# Roadmap / Phase Tracker

This is the single list of every phase or feature branch in flight or planned, across all of it —
engineering hardening, new features and GDPR work (`project_requirements.md`, `gdpr.md`), and stack
migrations (`tech_stack.md`). It answers "what's next, what's it called, and how far did it get" —
decisions go in `decisions.md`, requirements go in `project_requirements.md`, the task-level
breakdown goes in [`PRODUCTION_UPDATE_PLAN.md`](../PRODUCTION_UPDATE_PLAN.md), and this file just
tracks sequencing and status.

**Every row here is an Epic in the backlog**, with the same number and branch name. This file owns
epic-level status; the backlog owns task-level status.

## How to use this file

- One row per phase/branch/epic. Branch names follow ADR-001 in [decisions.md](decisions.md)
  (`phase-N-<slug>` for hardening phases, `feature-<slug>` / `gdpr-<slug>` / `stack-<slug>` for
  everything else). Every branch still targets `main`; promoting validated work from `main` to the
  `production` branch (and tagging a release) is a separate step per ADR-010.
- Update **Status** as work moves — don't leave a merged phase marked `In progress`.
- A phase should have an approved plan (Plan Mode, discussed with Claude) before its Status moves
  past `Not started`.
- Statuses: `Not started` → `Planned` (plan agreed, branch not opened yet) → `In progress` →
  `In review` (PR open) → `Done` (merged to `main`) → or `Blocked` (note what it's blocked on).
- When a phase finishes, note the merge commit/tag and any follow-up it created.
- Adding a new phase/feature here means adding the matching epic to the backlog in the same session.

## Engineering hardening (Epics 1–8)

| # | Phase | Branch | Status | Scope summary | Notes / links |
|---|---|---|---|---|---|
| 1 | Stabilize the repository | `phase-1-repo-cleanup` | Not started | Remove generated artifacts from VCS, settings package split, dead code cleanup, **`production` branch + branch protection + release tagging (ADR-010)**, **minimal CI pipeline (lint/check/Docker build validation) on every PR**, local dev-env refresh script (ADR-014) | See [decisions.md](decisions.md) ADR-010, ADR-011, ADR-014 |
| 2 | Security & configuration hardening | `phase-2-security-hardening` | Not started | Secrets to env vars, `DEBUG=False` outside dev, auth/authorization on all views, stop logging plaintext passwords | See [gdpr.md](gdpr.md) §6 — overlaps with GDPR Article 32 |
| 3 | Database redesign & data governance | `phase-3-db-redesign` | Not started | Schema fixes (Supplier PK, quantity types, naming), **multi-tenancy (`Bakery` model + tenant FK across all business tables, per ADR-006/ADR-008)**, migration strategy, retention practices, tenant full-data export + GDPR personal-data export tooling | See [tech_stack.md](tech_stack.md) DB row and [decisions.md](decisions.md) ADR-006/007/008/009 |
| 4 | Backend modernization | `phase-4-backend-modernization` | Not started | Services layer for costing/margin logic, real ModelForms, query performance | |
| 5 | Frontend modernization | `phase-5-frontend-modernization` | Not started | Shared `base.html`, asset pipeline, accessibility, real search/filter | See [tech_stack.md](tech_stack.md) Frontend section |
| 6 | Testing & quality gates | `phase-6-testing-ci` | Not started | Unit/integration tests, ruff/black, **extending** the Phase 1 minimal CI into the full pipeline (tests + security checks + deploy gating) | Builds on [decisions.md](decisions.md) ADR-011's Phase 1 foundation |
| 7 | Observability & operations | `phase-7-observability` | Not started | Structured logging, error tracking, health checks, deployment hardening | |
| 8 | Documentation & team readiness | `phase-8-docs` | Not started | README rewrite, architecture docs, runbooks | |

## Discovery work (Epics 9–11 — must land before dependent phases start)

| # | Phase | Branch | Status | Scope summary | Notes / links |
|---|---|---|---|---|---|
| 9 | Tech stack decisions | `stack-decisions` | Not started | Resolve every `Open` row in [tech_stack.md](tech_stack.md); log each as an ADR | Blocks Phases 3–5 above and the hosting migration below |
| 10 | Requirements discovery | `requirements-discovery` | Not started | Resolve personas, functional/non-functional requirements, business data semantics, and feature backlog priority in [project_requirements.md](project_requirements.md) | Blocks Phase 2's role model, Phase 3's schema semantics, and the new-feature phases below. Multi-tenancy already resolved (ADR-006) |
| 11 | GDPR data inventory & policy | `gdpr-data-inventory` | Not started | Complete the data inventory and policy sections in [gdpr.md](gdpr.md) | Blocks any consent/erasure/audit-log implementation, and the profile-picture feature |

## New features (Epics 12–16 — add rows as they're prioritized in `project_requirements.md`)

| # | Feature | Branch | Status | Scope summary | Notes / links |
|---|---|---|---|---|---|
| 12 | Hosting migration (off home server) | `stack-hosting-migration` | Not started | Move Django app + PostgreSQL off the self-hosted home server/Portainer setup to **Railway (Hobby, EU West)** per ADR-013, deployed via the existing Dockerfile rather than Railpack (ADR-004). Production only — the dev/test tier stays local per ADR-014 | Host now chosen (12.1 done); remaining work is provisioning, EU-region volume verification, backups, and the data migration. See [tech_stack.md](tech_stack.md) "Hosting candidates" |
| 13 | Media storage for user uploads (product photos, profile pictures) | `feature-media-storage` | Not started | Add `Product`/profile image fields, integrate S3-compatible object storage (Cloudflare R2 lead candidate) via `django-storages`, decoupled from app hosting | See ADR-005 in [decisions.md](decisions.md), [tech_stack.md](tech_stack.md) "Static & media file storage", and [gdpr.md](gdpr.md) — profile pictures are personal data and the legal basis must be resolved before implementation |
| 14 | Tenant full data export (portable/DBMS-importable) | `feature-tenant-data-export` | Not started | Given a tenant, export all of its rows across every tenant-scoped table as portable SQL or a CSV bundle + manifest, importable into another DBMS | See ADR-008 in [decisions.md](decisions.md) and [tech_stack.md](tech_stack.md) "Tenant data export tooling". Depends on Phase 3's `Bakery` tenant model existing first |
| 15 | GDPR personal-data export (subject-scoped) | `feature-gdpr-data-export` | Not started | Second, separate export scoped to one data subject's personal data across models — the actual Article 20 portability fix, distinct from the bulk admin CSV export and the tenant-wide export above | See ADR-009 in [decisions.md](decisions.md) and [gdpr.md](gdpr.md) §3 Portability |
| 16 | AI insights & alerts service (Spark/Databricks) | `feature-ai-insights-service` | Not started | External batch-processing service (Apache Spark on Databricks) triggered by app events (e.g. price/margin change), reads app DB, returns margin alerts and real-time analytics data back to the app | See ADR-002 in [decisions.md](decisions.md) and [tech_stack.md](tech_stack.md) "AI insights / batch analytics service"; needs the API contract + data-scope decision (GDPR §7) resolved before implementation starts |

## Suggested execution order

Sequencing only — the task-level detail is in [`PRODUCTION_UPDATE_PLAN.md`](../PRODUCTION_UPDATE_PLAN.md).

1. **Epics 9–11 (discovery) run first or in parallel with Epic 1** — they unblock most of what
   follows, and none of them require code changes.
2. Epic 1 — repository cleanup, branch/release setup, minimal CI.
3. Epic 2 — security fixes and permissions hardening (the plaintext-password logging fix should not
   wait for the rest of the epic).
4. Epic 9's dependency/runtime decisions, then the upgrade itself.
5. Epic 3 — database redesign, multi-tenancy, and safe migrations.
6. Epic 4 — backend refactor: services layer, real forms.
7. Epic 5 — frontend template consolidation and asset modernization.
8. Epic 6 — test suite and the full CI gate.
9. Epic 12 → Epic 7 — pick and provision the host, then observability and deployment hardening.
10. Epic 8 — documentation and runbooks, once the things being documented are stable.

Feature epics 13–16 slot in after their prerequisites (noted per epic), prioritized by the MoSCoW
pass in [project_requirements.md](project_requirements.md).

## Milestone: first production release scope

The first production-focused release prioritizes risk reduction over feature expansion. It is
considered shippable when these are done (task IDs from the backlog):

- Secrets removed from source (2.1) and `DEBUG = False` outside dev (2.2)
- Settings split by environment (1.5)
- Plaintext-password logging removed (2.10)
- Authentication and authorization enforced in views (2.6, 2.7)
- Known functional defects fixed, including the user-delete flow (6.7)
- Repository artifacts cleaned up (1.1, 1.2)
- Basic automated tests for core flows (6.8)
- Deployment configuration normalized (7.7, 7.8, 7.9)
- Dependency upgrade path prepared with lock files (9.8)

## Completed

_(move finished rows here with their merge date/tag, so the tables above stay focused on what's
still ahead)_

None yet.
