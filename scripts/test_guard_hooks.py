"""Tests for the guard hooks (task 1.15, ADR-038; the rename guard, ADR-039)."""

import io
import json
import os
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest

from scripts.guard_hooks import (
    check,
    git_calls,
    main,
    pushed_branches,
    respelled,
    task_of,
    task_status,
)

GUARD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "guard_hooks.py")

# The shape of PRODUCTION_UPDATE_PLAN.md that the guard reads: the glance table that
# names each epic's branch, and task rows whose third cell is the status. 1.15's task
# cell carries an escaped pipe, which must not shift the cells.
PLAN = """\
# Plan

## Backlog at a glance

| Epic | Name | Branch | Status | Tasks | Blocked by |
|---|---|---|---|---|---|
| [1](#epic-1) | Stabilize the repository | `phase-1-repo-cleanup` | In progress | 2 | - |
| 3 | Database redesign | `phase-3-db-redesign` | Not started | 1 | Epic 19 |

## Epic 1

| ID | Task | Status | Notes |
|---|---|---|---|
| 1.1 | Something already done | **Done** 2026-09-01 | ADR-001 |
| 1.15 | Guard hooks: `a \\| b` | Not started | ADR-038 |

## Epic 3

| ID | Task | Status | Notes |
|---|---|---|---|
| 3.74 | Build `Category`, drop `categorie` | Not started | ADR-032 |
"""

FIELD = 'categorie = models.CharField("Category", max_length=30)\n'
RESPELLED = 'category = models.CharField("Category", max_length=30)\n'


class GitCallsTests(unittest.TestCase):
    def subcommands(self, command):
        return [call.subcommand for call in git_calls(command)]

    def test_each_command_in_a_chain_is_found(self):
        self.assertEqual(
            self.subcommands("git add -A && git commit -m x; git push | cat"),
            ["add", "commit", "push"],
        )

    def test_a_quoted_message_is_one_word(self):
        self.assertEqual(
            self.subcommands('git commit -m "then git push origin main"'), ["commit"]
        )

    def test_powershell_separators(self):
        self.assertEqual(
            self.subcommands("git push origin main; if ($?) { git status }"),
            ["push", "status"],
        )

    def test_each_line_is_its_own_command(self):
        self.assertEqual(
            self.subcommands("git status\ngit push origin main"), ["status", "push"]
        )

    def test_an_unbalanced_quote_falls_back_line_by_line(self):
        command = "git commit -F - <<'EOF'\nIt's done\nEOF\ngit push"
        self.assertEqual(self.subcommands(command), ["commit", "push"])

    def test_git_options_come_before_the_subcommand(self):
        (call,) = git_calls("git -C ../other -c core.pager=cat push origin main")
        self.assertEqual(call.location, ["-C", "../other"])
        self.assertEqual(call.subcommand, "push")
        self.assertEqual(call.args, ["origin", "main"])

    def test_no_git_no_calls(self):
        self.assertEqual(git_calls("gh pr view; echo digit"), [])


class PushedBranchesTests(unittest.TestCase):
    def test_destinations(self):
        task = "phase-1-repo-cleanup-1.15"
        cases = [
            ([], "main", {"main"}),
            (["origin"], task, {task}),
            (["-u", "origin", task], "main", {task}),
            (["--repo", "origin"], "main", {"main"}),
            (["origin", "HEAD"], "main", {"main"}),
            (["origin", "HEAD:production"], task, {"production"}),
            (["origin", "+main"], task, {"main"}),
            (["origin", ":main"], task, {"main"}),
            (["origin", "--delete", "main"], task, {"main"}),
            (["origin", "feature:refs/heads/main"], task, {"main"}),
            (["origin", "main:feature"], task, {"feature"}),
            (["-o", "ci.skip", "origin", task], "main", {task}),
            (["--all", "origin"], task, {"*"}),
            (["--mirror"], task, {"*"}),
            (["--dry-run", "origin", "main"], task, set()),
            (["--tags"], "main", set()),
            (["origin"], "", set()),
        ]
        for args, current, expected in cases:
            with self.subTest(args=args, current=current):
                self.assertEqual(pushed_branches(args, current), expected)


class RespelledTests(unittest.TestCase):
    def names(self, removed, added, task=None):
        return [identifier.name for identifier in respelled(removed, added, task)]

    def test_respellings_are_caught(self):
        cases = [
            (FIELD, RESPELLED, "categorie"),
            (
                "filter(categorie__icontains=q)",
                "filter(category__icontains=q)",
                "categorie",
            ),
            (
                "class Bs_Ingredients(models.Model):",
                "class BsIngredient(models.Model):",
                "Bs_Ingredients",
            ),
            (
                "Recipe_Ingredients.objects.filter(product=p)",
                "RecipeLine.objects.filter(product=p)",
                "Recipe_Ingredients",
            ),
            (
                "class Recipe_IngredientsAdmin(admin.ModelAdmin):",
                "class RecipeIngredientsAdmin(admin.ModelAdmin):",
                "Recipe_Ingredients",
            ),
        ]
        for removed, added, name in cases:
            with self.subTest(added=added):
                self.assertEqual(self.names(removed, added), [name])

    def test_changes_that_are_not_respellings_pass(self):
        cases = [
            # `categories` is another word: the URL names
            (
                "{% url 'control:products_categories' %}",
                "{% url 'control:products_category' %}",
            ),
            # deleted outright
            ("x = Recipe_Ingredients.objects.all()\n", ""),
            # moved
            (
                "a\nRecipe_Ingredients.objects.all()\n",
                "Recipe_Ingredients.objects.all()\na\n",
            ),
            # edited around, the name kept
            (FIELD, FIELD.replace("30", "50")),
            # `category` added, the field untouched
            (FIELD, FIELD + "# category is the label\n"),
        ]
        for removed, added in cases:
            with self.subTest(added=added):
                self.assertEqual(self.names(removed, added), [])

    def test_the_deleting_task_may_respell_its_own_identifier(self):
        self.assertEqual(self.names(FIELD, RESPELLED, task="3.74"), [])
        self.assertEqual(self.names(FIELD, RESPELLED, task="3.73"), ["categorie"])
        self.assertEqual(self.names("Bs_Ingredients", "RecipeLine", task="3.73"), [])


class TaskTests(unittest.TestCase):
    def test_task_branches(self):
        self.assertEqual(task_of("phase-1-repo-cleanup-1.15", PLAN), "1.15")
        self.assertEqual(task_of("phase-3-db-redesign-3.74", PLAN), "3.74")

    def test_other_branches_are_not_task_branches(self):
        for branch in (
            "main",
            "",
            "chore-backlog-1.15-notes",
            "chore-backlog-1.15",
            "phase-1-repo-cleanup-3.74",
            "phase-1-repo-cleanup",
        ):
            with self.subTest(branch=branch):
                self.assertIsNone(task_of(branch, PLAN))

    def test_status_is_the_third_cell(self):
        self.assertEqual(task_status(PLAN, "1.15"), "Not started")
        self.assertEqual(task_status(PLAN, "1.1"), "**Done** 2026-09-01")
        self.assertIsNone(task_status(PLAN, "9.9"))


def _remove_read_only(function, path, _):
    # git writes its objects read-only, which stops rmtree on Windows
    os.chmod(path, stat.S_IWRITE)
    function(path)


class RepoTests(unittest.TestCase):
    """The guard against a real repository, on a task branch cut from `main`."""

    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root, onerror=_remove_read_only)
        self.git("init", "-q", "-b", "main")
        self.write("PRODUCTION_UPDATE_PLAN.md", PLAN)
        self.write("models.py", FIELD)
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "base")
        self.git("switch", "-q", "-c", "phase-1-repo-cleanup-1.15")

    def git(self, *args):
        identity = ["-c", "user.name=Guard", "-c", "user.email=guard@example.com"]
        subprocess.run(
            ["git", *identity, "-c", "commit.gpgsign=false", *args],
            cwd=self.root,
            check=True,
            capture_output=True,
        )

    def write(self, name, text):
        path = os.path.join(self.root, name)
        with open(path, "w", encoding="utf-8", newline="\n") as file:
            file.write(text)
        return path

    def set_status(self, task, status):
        row = next(line for line in PLAN.splitlines() if line.startswith(f"| {task} |"))
        self.write(
            "PRODUCTION_UPDATE_PLAN.md",
            PLAN.replace(row, row.replace("Not started", status)),
        )

    def bash(self, command, cwd=None):
        tool_input = {"command": command}
        return check(
            {"tool_name": "Bash", "tool_input": tool_input, "cwd": cwd or self.root}
        )

    def assertBlocked(self, reasons, *words):
        self.assertEqual(len(reasons), 1, reasons)
        for word in words:
            self.assertIn(word, reasons[0])

    # stale status

    def test_a_commit_with_the_status_unchanged_is_blocked(self):
        self.assertBlocked(self.bash("git commit -m work"), "1.15", '"Not started"')

    def test_a_staged_status_change_lets_the_commit_through(self):
        self.set_status("1.15", "**Done** 2026-10-09")
        self.git("add", "PRODUCTION_UPDATE_PLAN.md")
        self.assertEqual(self.bash("git commit -m work"), [])

    def test_a_status_change_staged_by_the_same_command_counts(self):
        self.set_status("1.15", "In progress")
        for command in (
            "git add -A && git commit -m work",
            "git add PRODUCTION_UPDATE_PLAN.md models.py && git commit -m work",
            "git add . && git commit -m work",
            "git commit -am work",
            "git commit -m work -- PRODUCTION_UPDATE_PLAN.md",
        ):
            with self.subTest(command=command):
                self.assertEqual(self.bash(command), [])

    def test_an_unstaged_status_change_does_not_count(self):
        self.set_status("1.15", "In progress")
        for command in (
            "git commit -m work",
            "git add models.py && git commit -m work",
        ):
            with self.subTest(command=command):
                self.assertBlocked(self.bash(command), "1.15")

    def test_later_commits_on_the_branch_pass(self):
        self.set_status("1.15", "In progress")
        self.git("commit", "-q", "-am", "status")
        self.assertEqual(self.bash("git commit -m 'review fixes'"), [])

    def test_branches_that_are_not_task_branches_are_not_checked(self):
        self.git("switch", "-q", "-c", "chore-backlog-1.15-notes")
        self.assertEqual(self.bash("git commit -m notes"), [])

    # respelling

    def test_a_staged_respelling_is_blocked(self):
        self.set_status("1.15", "In progress")
        self.write("models.py", RESPELLED)
        self.git("add", "-A")
        self.assertBlocked(self.bash("git commit -m work"), "`categorie`", "3.74")

    def test_a_respelling_staged_by_the_same_command_is_blocked(self):
        self.set_status("1.15", "In progress")
        self.write("models.py", RESPELLED)
        self.assertBlocked(self.bash("git add -A && git commit -m work"), "`categorie`")
        self.assertBlocked(self.bash("git commit -am work"), "`categorie`")

    def test_an_unstaged_respelling_is_not_in_the_commit(self):
        self.set_status("1.15", "In progress")
        self.git("add", "PRODUCTION_UPDATE_PLAN.md")
        self.write("models.py", RESPELLED)
        self.assertEqual(self.bash("git commit -m work"), [])

    def test_the_deleting_task_may_respell_on_its_own_branch(self):
        self.git("switch", "-q", "-c", "phase-3-db-redesign-3.74", "main")
        self.set_status("3.74", "In progress")
        self.write("models.py", RESPELLED)
        self.assertEqual(self.bash("git add -A && git commit -m category"), [])

    def test_an_edit_that_respells_is_blocked(self):
        path = os.path.join(self.root, "models.py")
        event = {
            "tool_name": "Edit",
            "tool_input": {
                "file_path": path,
                "old_string": FIELD,
                "new_string": RESPELLED,
            },
            "cwd": self.root,
        }
        self.assertBlocked(check(event), "`categorie`")
        event["tool_input"]["new_string"] = FIELD.replace("30", "50")
        self.assertEqual(check(event), [])

    def test_a_write_that_respells_is_blocked(self):
        path = os.path.join(self.root, "models.py")
        event = {
            "tool_name": "Write",
            "tool_input": {"file_path": path, "content": RESPELLED},
            "cwd": self.root,
        }
        self.assertBlocked(check(event), "`categorie`")
        event["tool_input"]["file_path"] = os.path.join(self.root, "new.py")
        self.assertEqual(check(event), [])

    # pushes

    def test_a_push_to_main_or_production_is_blocked(self):
        self.assertBlocked(self.bash("git push origin HEAD:production"), "production")
        self.git("switch", "-q", "main")
        self.assertBlocked(self.bash("git push"), "main")

    def test_a_push_of_the_task_branch_passes(self):
        self.assertEqual(self.bash("git push -u origin phase-1-repo-cleanup-1.15"), [])

    def test_git_dash_c_names_the_repository(self):
        self.git("switch", "-q", "main")
        command = f"git -C {shlex.quote(self.root.replace(os.sep, '/'))} push"
        self.assertBlocked(self.bash(command, cwd=tempfile.gettempdir()), "main")

    # the hook itself

    def test_main_blocks_with_exit_2_and_the_reason(self):
        event = {"tool_name": "Bash", "tool_input": {"command": "git commit -m x"}}
        event["cwd"] = self.root
        stderr = io.StringIO()
        status = main(io.BytesIO(json.dumps(event).encode("utf-8")), stderr)
        self.assertEqual(status, 2)
        self.assertIn("1.15", stderr.getvalue())

    def test_the_script_runs_as_claude_code_calls_it(self):
        event = {"tool_name": "Bash", "tool_input": {"command": "git push"}}
        event["cwd"] = self.root
        self.git("switch", "-q", "main")
        done = subprocess.run(
            [sys.executable, GUARD],
            input=json.dumps(event).encode("utf-8"),
            capture_output=True,
            check=False,
        )
        self.assertEqual(done.returncode, 2, done.stderr)
        self.assertIn(b"Blocked by the task 1.15 guard", done.stderr)


class FailOpenTests(unittest.TestCase):
    def test_a_call_that_is_not_blocked_exits_0(self):
        event = {"tool_name": "Bash", "tool_input": {"command": "ls"}}
        self.assertEqual(main(io.BytesIO(json.dumps(event).encode()), io.StringIO()), 0)

    def test_a_broken_event_exits_1_and_does_not_block(self):
        stderr = io.StringIO()
        self.assertEqual(main(io.BytesIO(b"not json"), stderr), 1)
        self.assertIn("not checked", stderr.getvalue())

    def test_outside_a_repository_nothing_is_blocked(self):
        with tempfile.TemporaryDirectory() as directory:
            for command in ("git push", "git commit -m x"):
                with self.subTest(command=command):
                    event = {"tool_name": "Bash", "tool_input": {"command": command}}
                    event["cwd"] = directory
                    self.assertEqual(check(event), [])


if __name__ == "__main__":
    unittest.main()
