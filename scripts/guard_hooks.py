"""
Guard hooks for Claude Code sessions (task 1.15, ADR-038; the rename guard, ADR-039).

`.claude/settings.json` runs this before every Bash, PowerShell, Edit and Write call
Claude makes here. It reads the hook event on stdin and blocks the call, by exiting 2
with the reason on stderr, when the call would:

- push to `main` or `production`, which take changes only through a PR (ADR-037);
- respell `categorie`, `Bs_Ingredients` or `Recipe_Ingredients`, which stay misspelled
  on purpose until the task that deletes each one, 3.74 or 3.73 (ADR-039);
- commit on a task branch while that task's status in PRODUCTION_UPDATE_PLAN.md still
  reads what it read on `main`.

It sees only Claude's own tool calls, so it makes a mistake fail sooner and is never
the enforcement: branch protection (1.9) and CI (1.11) are. For the same reason a
guard that breaks exits 1, which Claude Code reports without blocking the call.

    echo '{"tool_name": "Bash", "tool_input": {"command": "git push"}}' | python scripts/guard_hooks.py

Standard library only, so whichever `python` Claude Code finds can run it.
"""

import fnmatch
import json
import os
import re
import shlex
import subprocess
import sys
from collections import namedtuple

PLAN = "PRODUCTION_UPDATE_PLAN.md"
PROTECTED_BRANCHES = ("main", "production")

Identifier = namedtuple("Identifier", "name spelling respellings owner")

# Each identifier ADR-039 leaves misspelled, the spellings a well-meant fix would give
# it, and the task that deletes it. `categorie(?!s)` leaves out `categories`, a
# different word: the `products_categories` and `rw_categories` URL names.
IDENTIFIERS = (
    Identifier(
        "categorie",
        re.compile(r"categorie(?!s)"),
        re.compile(r"category", re.IGNORECASE),
        "3.74",
    ),
    Identifier(
        "Bs_Ingredients",
        re.compile(r"Bs_Ingredients"),
        re.compile(
            r"bs_?ingredient|base_?recipe_?ingredient|recipe_?line", re.IGNORECASE
        ),
        "3.73",
    ),
    Identifier(
        "Recipe_Ingredients",
        re.compile(r"Recipe_Ingredients"),
        re.compile(r"recipe_?ingredient|recipe_?line", re.IGNORECASE),
        "3.73",
    ),
)

GitCall = namedtuple("GitCall", "location subcommand args")

# Git's own options that take the next word as their value. Only `-C` is kept, as the
# directory the call runs in.
GIT_OPTIONS_WITH_VALUE = {
    "-C",
    "-c",
    "--git-dir",
    "--work-tree",
    "--namespace",
    "--config-env",
}
PUSH_OPTIONS_WITH_VALUE = {"--repo", "-o", "--push-option", "--receive-pack", "--exec"}
COMMIT_OPTIONS_WITH_VALUE = {
    "-m",
    "--message",
    "-F",
    "--file",
    "-C",
    "--reuse-message",
    "-c",
    "--reedit-message",
    "--author",
    "--date",
    "-t",
    "--template",
    "--fixup",
    "--squash",
    "--cleanup",
    "--trailer",
}
DIFF = ("--no-color", "--no-ext-diff", "-U0")

# A token made only of these ends one command and starts the next: && || ; | & ( ) and
# a newline, in Bash and PowerShell alike.
SEPARATORS = ";&|()\n"
SEPARATOR = re.compile(r"[;&|()\n]+")

EPIC_ROW = re.compile(
    r"^\| \[?(\d+)\]?(?:\([^)]*\))? \| [^|]* \| `([^`]+)` \|", re.MULTILINE
)
TASK_BRANCH = re.compile(r"(.+)-(\d+)\.(\d+)")
CELL = re.compile(r"(?<!\\)\|")


def git_calls(command):
    """Each `git <subcommand>` in a shell command, in order, as a GitCall."""
    calls = []
    for segment in _segments(_tokens(command)):
        for i, word in enumerate(segment):
            if os.path.basename(word).lower() not in ("git", "git.exe"):
                continue
            j, location = i + 1, []
            while j < len(segment) and segment[j].startswith("-"):
                if segment[j] in GIT_OPTIONS_WITH_VALUE and j + 1 < len(segment):
                    if segment[j] == "-C":
                        location += segment[j : j + 2]
                    j += 1
                j += 1
            if j < len(segment):
                calls.append(GitCall(location, segment[j], segment[j + 1 :]))
            break
    return calls


def _tokens(command):
    try:
        return _lex(command)
    except (
        ValueError
    ):  # an unbalanced quote: a heredoc body or a PowerShell here-string
        tokens = []
        for line in command.splitlines():
            try:
                tokens += _lex(line)
            except ValueError:
                tokens += line.split()
            tokens.append("\n")
        return tokens


def _lex(text):
    lexer = shlex.shlex(text, posix=True, punctuation_chars=SEPARATORS)
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    return list(lexer)


def _segments(tokens):
    segment = []
    for token in tokens:
        if SEPARATOR.fullmatch(token):
            if segment:
                yield segment
            segment = []
        else:
            segment.append(token)
    if segment:
        yield segment


def pushed_branches(args, current):
    """
    The remote branches a `git push` with these arguments would update.

    `current` is the checked-out branch, which a push with no refspec and a `HEAD`
    refspec both mean. `*` stands for every branch (`--all`, `--mirror`).
    """
    words = iter(args)
    positional, tags = [], False
    for word in words:
        if word == "--":
            positional += words
        elif word in ("-n", "--dry-run"):
            return set()
        elif word in ("--all", "--mirror", "--branches"):
            return {"*"}
        elif word == "--tags":
            tags = True
        elif word in PUSH_OPTIONS_WITH_VALUE:
            next(words, None)
        elif not word.startswith("-"):
            positional.append(word)
    refspecs = positional[1:]
    if not refspecs:
        return set() if tags or not current else {current}
    branches = set()
    for refspec in refspecs:
        source, colon, destination = refspec.lstrip("+").partition(":")
        if not colon:
            destination = source
        if destination in ("HEAD", "@"):
            destination = current
        if destination:
            branches.add(destination.removeprefix("refs/heads/"))
    return branches


def respelled(removed, added, task=None):
    """
    The identifiers a change from `removed` to `added` respells.

    The exact spelling has to occur fewer times and a fixed one more times, so moving,
    deleting or editing around one passes, and only a respelling trips it. The task
    that deletes an identifier may respell it.
    """
    found = []
    for identifier in IDENTIFIERS:
        if identifier.owner == task:
            continue
        spelling = identifier.spelling
        dropped = len(spelling.findall(removed)) - len(spelling.findall(added))
        gained = _respellings(identifier, added) - _respellings(identifier, removed)
        if dropped > 0 and gained > 0:
            found.append(identifier)
    return found


def _respellings(identifier, text):
    # Masked first, so `Bs_Ingredients` is not also counted as `bs_?ingredient`.
    masked = identifier.spelling.sub(" ", text)
    return len(identifier.respellings.findall(masked))


def task_of(branch, plan):
    """The task a branch is named for (`<epic-branch>-<task-id>`, ADR-037), or None."""
    match = TASK_BRANCH.fullmatch(branch or "")
    if not match:
        return None
    prefix, epic, number = match.groups()
    glance = plan.partition("## Backlog at a glance")[2].partition("\n## ")[0]
    epic_branches = dict(EPIC_ROW.findall(glance))
    return f"{epic}.{number}" if epic_branches.get(epic) == prefix else None


def task_status(plan, task):
    """The Status cell of a task's row in the plan, or None if it has no row."""
    for line in plan.splitlines():
        if line.startswith(f"| {task} |"):
            cells = CELL.split(line)
            return cells[3].strip() if len(cells) > 4 else None
    return None


def check(event):
    """The reasons to block this tool call, or an empty list to let it through."""
    tool = event.get("tool_name")
    tool_input = event.get("tool_input") or {}
    cwd = event.get("cwd") or os.getcwd()
    if tool in ("Edit", "Write"):
        return _check_edit(tool, tool_input, cwd)
    command = tool_input.get("command") or ""
    if tool not in ("Bash", "PowerShell") or "git" not in command:
        return []
    reasons, earlier = [], []
    for call in git_calls(command):
        if call.subcommand == "push":
            reasons += _check_push(call, cwd)
        elif call.subcommand == "commit":
            reasons += _check_commit(call, earlier, cwd)
        earlier.append(call)
    return reasons


def _check_push(call, cwd):
    current = _current_branch(cwd, call.location)
    destinations = pushed_branches(call.args, current)
    hit = [
        branch
        for branch in PROTECTED_BRANCHES
        if any(fnmatch.fnmatchcase(branch, pattern) for pattern in destinations)
    ]
    if not hit:
        return []
    return [
        (
            f"Blocked by the task 1.15 guard: this push would update "
            f"{' and '.join(hit)} directly. main and production take changes only "
            "through a PR (ADR-037): push the task branch and open a PR into main."
        )
    ]


def _check_commit(call, earlier, cwd):
    location = call.location
    everything, paths = _staged_by(earlier, call)
    # What is staged already, plus what this command stages from the working tree; the
    # counts are net, so they add up across the two diffs.
    diffs = [_git(cwd, location, "diff", "--cached", *DIFF)]
    if everything or paths:
        pathspec = [] if everything else paths
        diffs.append(_git(cwd, location, "diff", *DIFF, "--", *pathspec))
    removed, added = _changed_lines("".join(diff or "" for diff in diffs))

    if everything or (paths and _names(cwd, location, paths, PLAN)):
        plan = _worktree_plan(cwd, location)
    else:
        plan = _git(cwd, location, "show", f":{PLAN}") or ""
    task = task_of(_current_branch(cwd, location), plan)

    reasons = _respelling_reasons(removed, added, task)
    if task:
        base = _git(cwd, location, "merge-base", "HEAD", "main") or _git(
            cwd, location, "merge-base", "HEAD", "origin/main"
        )
        before = base and _git(cwd, location, "show", f"{base.strip()}:{PLAN}")
        status = task_status(plan, task)
        if before and status is not None and status == task_status(before, task):
            reasons.append(
                f"Blocked by the task 1.15 guard: task {task}'s status in {PLAN} "
                f'still reads "{status}", as it does on main. Set its status and record '
                "what was done in its Notes (/next-task step 10), stage the file, then "
                "commit."
            )
    return reasons


def _staged_by(earlier, commit):
    """
    What this commit takes from the working tree beyond what is already staged:
    every tracked file (`-a`, `git add -A` or `-u`), or the given paths.
    """
    everything, paths = False, []
    for call in earlier:
        if call.subcommand == "add":
            add_all, add_paths = _add_arguments(call.args)
            everything = everything or add_all
            paths += add_paths
    commit_all, commit_paths = _commit_arguments(commit.args)
    return everything or commit_all, paths + commit_paths


def _add_arguments(args):
    words = iter(args)
    everything, paths = False, []
    for word in words:
        if word == "--":
            paths += words
        elif word in ("-A", "--all", "-u", "--update"):
            everything = True
        elif not word.startswith("-"):
            paths.append(word)
    return everything and not paths, paths


def _commit_arguments(args):
    words = iter(args)
    everything, paths = False, []
    for word in words:
        if word == "--":
            paths += words
        elif word in ("-a", "--all"):
            everything = True
        elif word in COMMIT_OPTIONS_WITH_VALUE:
            next(words, None)
        elif word.startswith("--"):
            continue
        elif word.startswith("-") and len(word) > 1:
            # a cluster of short options, such as `-am "message"`
            for position, letter in enumerate(word[1:], start=1):
                if letter == "a":
                    everything = True
                elif letter in "mFCct":
                    if position == len(word) - 1:
                        next(words, None)
                    break
        else:
            paths.append(word)
    return everything, paths


def _changed_lines(diff):
    """The removed and the added lines of a unified diff, each joined into one text."""
    removed, added, in_hunk = [], [], False
    for line in diff.splitlines():
        if line.startswith("diff --git "):
            in_hunk = False
        elif line.startswith("@@"):
            in_hunk = True
        elif in_hunk and line.startswith("-"):
            removed.append(line[1:])
        elif in_hunk and line.startswith("+"):
            added.append(line[1:])
    return "\n".join(removed), "\n".join(added)


def _check_edit(tool, tool_input, cwd):
    if tool == "Edit":
        removed = tool_input.get("old_string") or ""
        added = tool_input.get("new_string") or ""
    else:  # Write replaces the whole file
        removed = _read(os.path.join(cwd, tool_input.get("file_path") or ""))
        added = tool_input.get("content") or ""
    if not any(identifier.spelling.search(removed) for identifier in IDENTIFIERS):
        return []
    task = task_of(_current_branch(cwd, []), _worktree_plan(cwd, []))
    return _respelling_reasons(removed, added, task)


def _respelling_reasons(removed, added, task):
    return [
        f"Blocked by the task 1.15 guard: this respells `{identifier.name}`. ADR-039 "
        f"leaves it misspelled on purpose until task {identifier.owner} deletes it, so "
        "renaming it here is a drive-by fix. Keep the old spelling; if this is not a "
        "rename, stop and ask the user, who can make the change themselves."
        for identifier in respelled(removed, added, task)
    ]


def _names(cwd, location, paths, name):
    """Whether these pathspecs cover the tracked file `name` (relative to the root)."""
    listed = _git(cwd, location, "ls-files", "--full-name", "--", *paths) or ""
    return name in listed.splitlines()


def _current_branch(cwd, location):
    branch = _git(cwd, location, "symbolic-ref", "--short", "-q", "HEAD")
    return branch.strip() if branch else ""


def _worktree_plan(cwd, location):
    root = _git(cwd, location, "rev-parse", "--show-toplevel")
    return _read(os.path.join(root.strip(), PLAN)) if root else ""


def _read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as file:
            return file.read()
    except OSError:
        return ""


def _git(cwd, location, *args):
    """Run a read-only git command; its output, or None if it fails."""
    try:
        done = subprocess.run(
            ["git", *location, *args],
            cwd=cwd,
            capture_output=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout.decode("utf-8", "replace") if done.returncode == 0 else None


def main(stdin=None, stderr=None):
    stdin = stdin or sys.stdin.buffer
    stderr = stderr or sys.stderr
    # A broken guard must not stop work, so it exits 1, which never blocks: here for an
    # event it cannot read, and through the traceback for anything else.
    try:
        # Bytes, decoded here: on Windows the default would be the ANSI code page.
        reasons = check(json.loads(stdin.read().decode("utf-8")))
    except (ValueError, TypeError, AttributeError, LookupError) as error:
        print(f"guard_hooks: the call was not checked: {error!r}", file=stderr)
        return 1
    if reasons:
        print("\n\n".join(reasons), file=stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.stderr.reconfigure(encoding="utf-8")
    sys.exit(main())
