# Planning documents

Read this before a **planning** session: proposing a feature, answering a roadmap question, or
logging a decision. A task session does not need it; `/next-task` and
`python -m scripts.docs_lookup` fetch what a task cites ([ADR-051](decisions.md)).

## One job each

| File | Its job |
|---|---|
| [`project_requirements.md`](project_requirements.md) | **What the app should do, at a broad level.** Part 1: product (go-to-market, regulatory scope, roles, per-area requirements, feature backlog, non-functional targets). Part 2: data protection (GDPR): controller/processor model, personal-data inventory, subject rights, retention, breach process, DPIA. The inventory must exist before consent, deletion or audit-log code is written against it |
| [`tech_stack.md`](tech_stack.md) | **What it's built with, decided facts only.** Current vs. decided per layer, plus the third-party processors and the data-residency position. Outcomes in a line; the reasoning is in the ADR named beside each row and is never repeated there |
| [`decisions.md`](decisions.md) | **Append-only ADR log; its only job is to stop settled questions being re-opened.** Index first, then Decision · Rejected · Traps per entry. **Rejected is the load-bearing part.** Never delete an entry; supersede it, and move any surviving clause into the superseding ADR |
| [`roadmap.md`](roadmap.md) | **The open-decisions register, and nothing else.** Every question still awaiting a judgment, with stable IDs (`10.x` product, `11.x` data protection, `9.x` stack) that `Blocked` backlog tasks cite. No tasks, no status, no sequencing |
| [`../PRODUCTION_UPDATE_PLAN.md`](../PRODUCTION_UPDATE_PLAN.md) | **The task backlog:** epics and tasks, their status, the run order and the release milestone |

**There are no `Open` rows anywhere but `roadmap.md`.** A question in `tech_stack.md`,
`project_requirements.md` or `decisions.md` is a bug — move it to `roadmap.md`.

## When a decision is made

The flow is one-directional: **open question → ADR → tasks**, all in the same session:

1. Add an ADR to `decisions.md`, and its index row.
2. Update the state doc it changes (`tech_stack.md` or `project_requirements.md`).
3. **Delete the question from `roadmap.md`.**
4. Turn the decision into task(s) in the right epic of the backlog, plus a row in its
   "Decision → task coverage" table.

ADRs record product, architecture, stack and gate decisions. Procedure inside the task loop
(`.claude/skills/`, `scripts/`, agent files) changes by PR without one, unless it changes a gate,
the branch, merge or release model, or a rule another ADR states ([ADR-051](decisions.md)).

## Docs state intent; the code states fact

These documents are authoritative for **what to do, why, and in what order**. They are *not*
authoritative for **what the code currently contains**: every such claim was measured once, by
hand, and has been drifting since. Before a number, a supersession or a technical constraint sets
a task's scope, **re-derive it from the code** ([ADR-040](decisions.md)). Three have already been
wrong: a site count that matched a substring (`categorie` inside `categories`), a task believed
to absorb a rename it never performs, and a migration constraint guarding a deployment that does
not exist.

A wrong claim found during a task is fixed in that task's PR when it is small. When it changes
the task's scope or purpose, it gets its own ADR and PR ([ADR-051](decisions.md)), and is never a
reason to widen the task in hand.
