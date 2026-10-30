"""
Print one excerpt of the planning docs, so a session never loads them whole (ADR-051).

The task loop used to fetch these excerpts through LLM subagents, which took from
minutes to hours a lookup and could stall on their own. This reads the files directly.

    python -m scripts.docs_lookup next              # the first Run-order entry not Done
    python -m scripts.docs_lookup task 2.1 6.26     # task rows, verbatim, with their branch
    python -m scripts.docs_lookup adr 37 41         # ADR entries in full, following supersession
    python -m scripts.docs_lookup roadmap 11.1      # open-question rows
    python -m scripts.docs_lookup req "User roles"  # a section of project_requirements.md
    python -m scripts.docs_lookup stack Runtime     # a section of tech_stack.md

A task that is `Blocked`, or whose Notes cite no ADR, is flagged: `/next-task` stops at
both (ADR-038, ADR-048). The docs' claims about the code are printed as written, never
re-measured; that is `codecheck`'s job (ADR-040).

Standard library only, like the guard hooks whose backlog parsing it shares.
"""

import argparse
import os
import re
import sys

from scripts.guard_hooks import PLAN, epic_branches, row_cells

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DECISIONS = "docs/decisions.md"
ROADMAP = "docs/roadmap.md"
REQUIREMENTS = "docs/project_requirements.md"
TECH_STACK = "docs/tech_stack.md"

RUN_ORDER_ROW = re.compile(r"^\| \d+ \| (\d+\.\d+) \|(.*)\|\s*$", re.MULTILINE)
ADR_CITATION = re.compile(r"ADR-\d+")
SUPERSEDED_BY = re.compile(r"Superseded by (\d{3})")
ADR_NUMBER = re.compile(r"\b\d{3}\b")
HEADING = re.compile(r"^(#{2,6}) (.*)$", re.MULTILINE)


class NotFound(LookupError):
    pass


def read(name, root=ROOT):
    with open(os.path.join(root, name), encoding="utf-8") as file:
        return file.read()


def is_done(status):
    return status.replace("*", "").strip().startswith("Done")


def task(plan, task_id):
    """A task's row, verbatim, with its branch and the flags `/next-task` stops at."""
    cells = row_cells(plan, task_id)
    if not cells or len(cells) < 4:
        raise NotFound(f"no task {task_id} in {PLAN}")
    _, text, status, notes = cells[:4]
    epic = task_id.split(".")[0]
    branch = epic_branches(plan).get(epic)
    lines = [
        f"Task {task_id} · branch {branch}-{task_id}"
        if branch
        else f"Task {task_id} · epic {epic} has no branch in the glance table",
        f"Task:   {text}",
        f"Status: {status}",
        f"Notes:  {notes}",
    ]
    if "Blocked" in status:
        lines.append(
            "! Blocked: do not implement. Its Notes name the roadmap question; "
            "check it with `roadmap <id>` and report it."
        )
    if not is_done(status) and not ADR_CITATION.search(notes):
        lines.append("! Its Notes cite no ADR: a backlog defect, not a task to start.")
    return "\n".join(lines)


def run_order(plan):
    """The Run order's entries, in order, as (task ID, why-here) pairs."""
    section = plan.partition("### Run order")[2].partition("\n## ")[0]
    return [(task_id, why.strip()) for task_id, why in RUN_ORDER_ROW.findall(section)]


def next_task(plan):
    """The first Run-order entry not Done (ADR-048), never skipping one."""
    for task_id, why in run_order(plan):
        status = row_cells(plan, task_id)
        if status and len(status) > 2 and is_done(status[2]):
            continue
        reason = f"Run order: {why}\n" if why else ""
        return reason + task(plan, task_id)
    raise NotFound(
        "every Run-order entry is Done: the next step owes its run order, written in a "
        "backlog PR (ADR-048). Stop."
    )


def adr(decisions, number, seen=None):
    """An ADR entry in full, then each one that supersedes it, and its related ADRs."""
    seen = set() if seen is None else seen
    label = f"{int(number):03d}"
    match = re.search(
        rf"^## ADR-{label}:.*?(?=^## |\Z)", decisions, re.MULTILINE | re.DOTALL
    )
    if not match:
        raise NotFound(f"no ADR-{label} in {DECISIONS}")
    seen.add(label)
    parts = [match.group(0).rstrip()]
    status = _index_status(decisions, label)
    for successor in SUPERSEDED_BY.findall(status):
        if successor not in seen:
            parts.append(f"--- ADR-{label} is superseded by ADR-{successor}:")
            parts.append(adr(decisions, successor, seen))
    related = [n for n in dict.fromkeys(ADR_NUMBER.findall(status)) if n not in seen]
    if related:
        parts.append(
            f"--- ADR-{label}'s index status: {status}\n"
            f"Related: {', '.join(related)} (read with `adr {' '.join(related)}`)"
        )
    return "\n\n".join(parts)


def _index_status(decisions, label):
    index = decisions.partition("## Index")[2].partition("\n## ")[0]
    for line in index.splitlines():
        if line.startswith(f"| [{label}]"):
            cells = line.split(" | ")
            return cells[2].strip() if len(cells) > 2 else ""
    return ""


def roadmap(text, question):
    cells = row_cells(text, question)
    if not cells:
        raise NotFound(f"no open question {question} in {ROADMAP}; it may be answered")
    return " | ".join(cells)


def section(text, query, name):
    """Every section whose heading contains `query`, each up to its next sibling."""
    headings = list(HEADING.finditer(text))
    found = []
    for i, heading in enumerate(headings):
        if query.lower() not in heading.group(2).lower():
            continue
        level = len(heading.group(1))
        end = len(text)
        for later in headings[i + 1 :]:
            if len(later.group(1)) <= level:
                end = later.start()
                break
        found.append(text[heading.start() : end].rstrip())
    if not found:
        titles = "\n".join(f"  {h.group(0)}" for h in headings)
        raise NotFound(f"no heading in {name} contains {query!r}. Headings:\n{titles}")
    return "\n\n".join(found)


def lookup(command, args, root=None):
    root = root or ROOT
    if command == "next":
        return next_task(read(PLAN, root))
    if command == "task":
        plan = read(PLAN, root)
        return "\n\n".join(task(plan, task_id) for task_id in args)
    if command == "adr":
        decisions = read(DECISIONS, root)
        return "\n\n".join(adr(decisions, number) for number in args)
    if command == "roadmap":
        text = read(ROADMAP, root)
        return "\n".join(roadmap(text, question) for question in args)
    name = {"req": REQUIREMENTS, "stack": TECH_STACK}[command]
    return section(read(name, root), " ".join(args), name)


def main(argv=None, stdout=None, stderr=None):
    stdout = stdout or sys.stdout
    stderr = stderr or sys.stderr
    parser = argparse.ArgumentParser(prog="python -m scripts.docs_lookup")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("next", help="the first Run-order entry not Done")
    commands.add_parser("task", help="task rows by ID").add_argument("ids", nargs="+")
    commands.add_parser("adr", help="ADR entries by number").add_argument(
        "ids", nargs="+", type=int
    )
    commands.add_parser("roadmap", help="open questions by ID").add_argument(
        "ids", nargs="+"
    )
    commands.add_parser("req", help="a project_requirements.md section").add_argument(
        "ids", nargs="+"
    )
    commands.add_parser("stack", help="a tech_stack.md section").add_argument(
        "ids", nargs="+"
    )
    options = parser.parse_args(argv)
    try:
        print(lookup(options.command, getattr(options, "ids", [])), file=stdout)
    except NotFound as error:
        print(f"docs_lookup: {error}", file=stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    sys.exit(main())
