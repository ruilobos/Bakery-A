---
name: next-task
description: Execute one backlog task from PRODUCTION_UPDATE_PLAN.md end to end — select, plan, branch, implement with tests, review, verify, commit, open the PR, then stop. Use when asked to start the next task, work a specific task ID, or continue the backlog.
---

# Execute one backlog task

The sanctioned way to execute a task ([ADR-038](../../../docs/decisions.md)). Scope is **exactly
one task = one feature = one PR** ([ADR-037](../../../docs/decisions.md)).

**Three human gates: the plan, each commit's diff, the merge.** You own the work between them.
You never merge to `main` and never promote to `production`.

## 1 · Sync and confirm a clean base

```bash
git switch main && git pull --prune
git status --short          # must be empty
gh pr list --state open     # note anything that touches the same files
```

A task branches from an **updated `main`**. No stacking — if an open PR already edits the file
this task needs, finish that one first or pick a different task.

## 2 · Select the task

Ask the **`backlog`** subagent for the next actionable task, or for the specific ID requested.
Take from it: the task text, its status, its branch name, and the **Notes column verbatim**.

Refuse and stop if:

- **Status is `Blocked`** — confirm the blocker with **`roadmap`** and report it. The way
  forward is a human decision → ADR → tasks, never an implementation.
- **The Notes cite no ADR** — that is a defect in the backlog, not a task to start. Fix the
  Notes first. *(ADR-038: the loop is only as good as the Notes column.)*

## 3 · Read only what the Notes cite

Fetch **only** the referenced material, via the subagent that owns each file:

| Need | Subagent |
|---|---|
| An ADR the Notes cite | `decisions` |
| A requirement or the personal-data inventory | `requirements` |
| A decided version, library or infra fact | `tech-stack` |
| What an open question is waiting on | `roadmap` |

They exist to keep the planning docs out of this session's context (ADR-038). Do not read a doc
directly when a subagent owns it.

## 4 · Plan — **human gate 1**

Enter **Plan Mode** and get the plan approved before writing anything.

**1.5 and 1.7 must always route through plan mode** — they are refactors, not mechanical edits.
See ADR-038's traps for the scale of 1.7.

## 5 · Branch

```bash
git switch -c <epic-branch>-<task-id>     # e.g. phase-1-repo-cleanup-1.1
```

The epic branch name comes from the *Backlog at a glance* table. **An epic groups and sequences;
it is not a branch.**

## 6 · Implement, with its tests

Write the task **and its tests** together. Follow the surrounding code's conventions.

Do not fix unrelated things you notice on the way. The prototype's naming and typing quirks are
enumerated in CLAUDE.md and owned by task 1.7, which migrates them deliberately — a drive-by
rename is a defect here, not a courtesy. File anything else you find as a new task instead.

## 7 · Review the diff

Read `git diff` against **both**:

- `decisions.md` — does this contradict a settled ADR, or re-introduce something `Rejected`?
- `project_requirements.md` — does it satisfy the requirement it claims to?

Use the `decisions` and `requirements` subagents. Re-introducing a rejected option is the single
failure the ADR log exists to prevent.

## 8 · Run the verification gates

Today's gates:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
```

Plus whatever the task itself can be proven by — run the thing, don't assume it.

**Task 1.11 owns the CI gate list and 6.23 the test runner.** When those land, they are the
source of truth; this file follows them rather than competing with them.

## 9 · Update the task's status

In `PRODUCTION_UPDATE_PLAN.md`, set the task's status and record what was done in its Notes.
A task is `Done` when its own PR merges. If part of it was deferred, say `In progress` and name
the task that now owns the remainder — a green checkmark over unfinished work is worse than an
honest status.

Keep the *Backlog at a glance* counts consistent with the rows.

## 10 · Commit — **human gate 2**

Reference the task ID. Say what changed, and why, including anything deliberately left out.

```
<Summary referencing the task ID>

<What changed, what was deferred and to which task, how it was verified.>

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
```

## 11 · Open the PR

```bash
git push -u origin <branch>
gh pr create --base main --title "<task-id>: <summary>" --body "..."
```

The body carries the task ID, what changed, what was deferred, and how it was verified.

## 12 · Stop — **human gate 3**

**Do not merge. Do not promote to `production`.** Report the PR URL and stop.

Merging is the human's call; ADR-037 squash-merges task PRs to `main`, and promotion to
`production` is its own tagged release.

## Notes

- Guard hooks ([1.15](../../../PRODUCTION_UPDATE_PLAN.md)) are local and invisible to anyone not
  using this tooling. Branch protection (1.9) and CI (1.11) are the enforcement that binds.
- This file holds **procedure and pointers only**. If you find yourself explaining *why* a rule
  exists, cite the ADR instead — restating architecture here is a defect.
