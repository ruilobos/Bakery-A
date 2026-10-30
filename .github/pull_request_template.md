<!--
Title: `<task-id>: <summary>`. The repository is public, so the title becomes release-note text:
keep production data out of it (ADR-042).
A release PR into `production` is titled `Release vX.Y.Z` (ADR-042) and uses
`.github/PULL_REQUEST_TEMPLATE/release.md` instead of this body (ADR-050).
A doc or ADR PR with no task names the ADR it logs in the lead line, and drops the checklist lines
that don't apply.
-->

**Task <task-id>** (Epic <n>): <task title>. Governing ADRs: <ADR-nnn>.

## What changed

-

## Not in this PR

<!-- What was deferred or deliberately left out, and the task that now owns it. "Nothing" is an answer. -->

-

## Found on the way, not fixed

<!-- Filed as a task or routed, never fixed in this PR. Delete the section if empty. -->

## Verification

<!-- The commands run and what they showed. The gates are the jobs in `.github/workflows/ci.yml`; the PR's own run is the one that counts. -->

-

### Checklist

- [ ] The title and the lead line carry the task ID
- [ ] The branch is `<epic-branch>-<task-id>` (ADR-037), cut from an updated `main` (ADR-010)
- [ ] The premise gate ran before planning; a small doc defect it found is corrected here and named above, and a scope-changing one was reported, not worked around (ADR-040, ADR-051)
- [ ] The diff was reviewed against the cited ADRs and requirement sections (ADR-038), and re-introduces no `Rejected` option
- [ ] The task's status in `PRODUCTION_UPDATE_PLAN.md` is set, its Notes are its ADRs and this PR (ADR-051), and anything deferred names the task that now owns it
- [ ] The jobs in `.github/workflows/ci.yml` were run locally
- [ ] No unrelated fixes (ADR-037), and no drive-by rename of the identifiers ADR-039 keeps
