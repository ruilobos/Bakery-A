---
name: next-task
description: Execute one backlog task from PRODUCTION_UPDATE_PLAN.md end to end — select, plan, branch, implement with tests, review, verify, commit, open the PR, then stop. Use when asked to start the next task, work a specific task ID, or continue the backlog.
---

# Execute one backlog task

The sanctioned way to execute a task ([ADR-038](../../../docs/decisions.md), as amended by
[ADR-051](../../../docs/decisions.md)). Scope is **exactly one task = one feature = one PR**
([ADR-037](../../../docs/decisions.md)).

**The PR review is the gate that always applies; plan approval applies only to risky tasks
(step 5).** You own the work in between. You never merge to `main` and never promote to
`production`.

**Never load a planning doc whole.** Every lookup is one command, well under a second:

```bash
python -m scripts.docs_lookup next            # the first Run-order entry not Done, with its row
python -m scripts.docs_lookup task 2.1        # a task's row verbatim, with its branch name
python -m scripts.docs_lookup adr 37 41       # ADRs in full, following supersession
python -m scripts.docs_lookup roadmap 11.1    # an open question
python -m scripts.docs_lookup req "User roles"   # a project_requirements.md section
python -m scripts.docs_lookup stack Runtime      # a tech_stack.md section
```

## 1 · Sync and confirm a clean base

```bash
git switch main && git pull --prune
git status --short          # must be empty
gh pr list --state open     # note anything that touches the same files
```

A task branches from an **updated `main`**. No stacking — if an open PR already edits the file
this task needs, finish that one first or pick a different task.

## 2 · Select the task

`docs_lookup next`, or `task <id>` for a task the human names. It prints the task text, status,
branch name and **Notes verbatim**, and flags the two stops below.

**The run order is the sequence** ([ADR-048](../../../docs/decisions.md)): take its first entry
not `Done`. Never pick by ADR number, by the ADR just merged, or by size or risk. A task the human
names may run out of order; say so in the plan.

Refuse and stop if:

- **The current step has no written run order** (`next` says so) — writing one is a backlog PR,
  not part of a task.
- **Status is `Blocked`** — confirm the blocker with `docs_lookup roadmap <id>` and report it. The
  way forward is a human decision → ADR → tasks, never an implementation.
- **The Notes cite no ADR** — that is a defect in the backlog, not a task to start.

## 3 · Read only what the Notes cite

`docs_lookup adr …` for every ADR the Notes cite, plus `req` / `stack` sections they name. Read
the **Rejected** part of each ADR: it is what stops a dead option coming back.

## 4 · Verify the task's premises — **before planning**

Notes and ADRs record what was *believed* when written ([ADR-040](../../../docs/decisions.md)).
Re-derive the claims that decide scope from the code:

| Claim | What to verify |
|---|---|
| **A number** — "137 sites", "16 CSS files" | Re-measure it with `git grep -w` (word boundaries, exclusions stated) and keep the command. For a wide, multi-layer count, ask the **`codecheck`** agent |
| **"Superseded by / absorbed into task N"** | Search for the *target* state, not the current one — if the target appears nowhere, no task delivers it |
| **A constraint** — "never X", "must use Y" | It must cite an ADR **and** the condition it guards must exist in this repo today |
| **The task's purpose** | The outcome is still something `project_requirements.md` or an ADR wants |

**A failed premise is handled by its size** ([ADR-051](../../../docs/decisions.md)):

- **Small** — a wrong count or a stale sentence that does not change what the task does: correct
  the doc line **in this task's PR** and name the correction in the PR body. Carry on.
- **Scope-changing** — the task would do something different, more, or nothing: **stop and
  report**. The repair is an ADR on its own PR, never a widened task.

## 5 · Plan — gate only when risky

**Enter Plan Mode and wait for approval** when the task touches any of:

- `models.py` or a migration;
- authentication, permissions, or security settings;
- more than about five files — when unsure, take the gate.

Otherwise, state the plan in a few lines in the session and proceed.

## 6 · Branch

```bash
git switch -c <epic-branch>-<task-id>     # e.g. phase-1-repo-cleanup-1.1
```

`docs_lookup` prints the branch name. **An epic groups and sequences; it is not a branch.**

## 7 · Implement, with its tests

Write the task **and its tests** together. Follow the surrounding code's conventions.

Do not fix unrelated things you notice on the way. The prototype's naming and typing quirks are
enumerated in CLAUDE.md and owned by Epic 3, whose 3.73 and 3.74 delete the three misspellings
1.7 left ([ADR-039](../../../docs/decisions.md)) — a drive-by rename is a defect here, not a
courtesy. File anything else you find as a new task instead.

## 8 · Review the diff

Read `git diff` against the ADRs fetched in step 3 — does it contradict one, or re-introduce
something it `Rejected`? — and against the requirement section it claims to satisfy. Fetch more
with `docs_lookup` if the diff reaches past them.

## 9 · Run the verification gates

The gates are the jobs in [`.github/workflows/ci.yml`](../../../.github/workflows/ci.yml). Run the
same commands locally before committing; the PR's own run is the one that counts. Plus whatever
the task itself can be proven by — run the thing, don't assume it.

## 10 · Update the task's status

In `PRODUCTION_UPDATE_PLAN.md`, edit only the task's row (find its line with
`grep -n "^| <id> |"`). Set the status and make the Notes **its ADRs and its PR**:
`**Done** YYYY-MM-DD` · `ADR-0NN · PR #N`. The PR number is known once the PR exists; set it in a
follow-up commit on the same branch. If part of the task was deferred, say `In progress` and name
the task that now owns the remainder. The narrative — what changed, what was deferred, how it was
verified — goes in the PR body, not the row.

Keep the *Backlog at a glance* counts consistent with the rows.

## 11 · Commit

Reference the task ID. Say what changed, and why, including anything deliberately left out.

```
<Summary referencing the task ID>

<What changed, what was deferred and to which task, how it was verified.>

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```

## 12 · Open the PR

```bash
git push -u origin <branch>
gh pr create --base main --title "<task-id>: <summary>" --body-file <scratchpad>/pr-body.md
```

The body fills in [`.github/pull_request_template.md`](../../../.github/pull_request_template.md)'s
sections and checklist. Write it to the scratchpad first: `--body` and `--body-file` skip the
template, so it never fills itself in.

## 13 · Stop — **the PR review is the human gate**

**Do not merge. Do not promote to `production`.** Report the PR URL and stop. Tell the human to
`/clear` before the next task, so it does not carry this one's context.

Merging is the human's call; ADR-037 squash-merges task PRs to `main`, and promotion to
`production` is its own tagged release.

## Notes

- Guard hooks ([1.15](../../../PRODUCTION_UPDATE_PLAN.md)) are local and invisible to anyone not
  using this tooling. Branch protection (1.9) and CI (1.11) are the enforcement that binds.
- This file holds **procedure and pointers only**. If you find yourself explaining *why* a rule
  exists, cite the ADR instead — restating architecture here is a defect.
