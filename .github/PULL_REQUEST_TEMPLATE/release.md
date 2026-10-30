<!--
Release PR template (task 6.26; ADR-042, ADR-050). A release PR merges `main` into `production`.
GitHub opens this file from a compare URL ending in `?template=release.md`. `gh pr create` skips
templates when given a body, so copy this file to the scratchpad, fill it in, and pass it:

  gh pr create --base production --head main --title "Release vX.Y.Z" --body-file <scratchpad>/release-body.md

Title: `Release vX.Y.Z`, the next patch, minor or major of the latest `v*` tag (ADR-042).
Merge with "Create a merge commit", never squash (ADR-041).
The repository is public: describe what was exercised, never data from it (ADR-050).
-->

**Release vX.Y.Z**: promotes `main` at `<short SHA>` to `production`. Previous release: `<vX.Y.Z, or none>`.

## Local verification (ADR-050)

Gates every `0.y.z` release until 12.5; `1.0.0` waits for the Railway release environment (ADR-014).

- **Commit verified:** `<full SHA>`. It must be this PR's head when it merges: if `main` moves
  after verification, verify again and update this line.
- **Launcher:** `python scripts/launch_local.py` on that commit → <built, migrated, serving :8000 — or what failed>
- **Screens exercised** (each loads with the data present, no server error):
  - [ ] Cover page `/`
  - [ ] Dashboard `/control/dashboard/`
  - [ ] Raw materials, by category `/control/rw_categories/`
  - [ ] Suppliers `/control/suppliers/`
  - [ ] Base recipes `/control/base_recipes/`
  - [ ] Products, by category `/control/products/`
  - [ ] Settings and CSV export `/control/settings/`, `/control/settings/export_to_csv`
  - [ ] Users `/control/settings/users/`
  - [ ] <anything this release changed that the list above does not reach>
- **Data used:** developer accounts and data seeded for the check, never production data.

## What this promotes

<!-- The PRs merged to main since the previous tag. `publish` generates the release notes from the same range, so every title here becomes public text (ADR-042). -->

-

### Checklist

- [ ] The title is `Release vX.Y.Z`, a successor of the latest tag, and `Validate release PR` passes (ADR-042)
- [ ] The commit verified above is this PR's head
- [ ] No PR title in the range carries production data
- [ ] Merge with **Create a merge commit**, never squash (ADR-041)
- [ ] After the merge, `publish` tagged the merge commit and created the Release; if it failed, the header of `.github/workflows/release.yml` says how to recover
