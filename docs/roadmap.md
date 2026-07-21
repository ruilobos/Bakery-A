# Roadmap / Phase Tracker

This is the single list of every phase or feature branch in flight or planned, across all of it —
engineering hardening (`PRODUCTION_UPDATE_PLAN.md`), new features and GDPR work
(`project_requirements.md`, `gdpr.md`), and stack migrations (`tech_stack.md`). It answers "what's
next, what's it called, and how far did it get" — decisions go in `decisions.md`, requirements go
in `project_requirements.md`, this file just tracks sequencing and status.

## How to use this file

- One row per phase/branch. Branch names follow ADR-001 in [decisions.md](decisions.md)
  (`phase-N-<slug>` for hardening phases, `feature-<slug>` / `gdpr-<slug>` / `stack-<slug>` for
  everything else).
- Update **Status** as work moves — don't leave a merged phase marked `In progress`.
- A phase should have an approved plan (Plan Mode, discussed with Claude) before its Status moves
  past `Not started`.
- Statuses: `Not started` → `Planned` (plan agreed, branch not opened yet) → `In progress` →
  `In review` (PR open) → `Done` (merged to `main`) → or `Blocked` (note what it's blocked on).
- When a phase finishes, note the merge commit/tag and any follow-up it created.

## Engineering hardening (from `PRODUCTION_UPDATE_PLAN.md`)

| # | Phase | Branch | Status | Scope summary | Notes / links |
|---|---|---|---|---|---|
| 1 | Stabilize the repository | `phase-1-repo-cleanup` | Not started | Remove generated artifacts from VCS, settings package split, dead code cleanup | |
| 2 | Security & configuration hardening | `phase-2-security-hardening` | Not started | Secrets to env vars, `DEBUG=False` outside dev, auth/authorization on all views, stop logging plaintext passwords | See [gdpr.md](gdpr.md) §6 — overlaps with GDPR Article 32 |
| 3 | Database redesign & data governance | `phase-3-db-redesign` | Not started | Schema fixes (Supplier PK, quantity types, naming), **multi-tenancy (`Bakery` model + tenant FK across all business tables, per ADR-006/ADR-008)**, migration strategy, retention practices, tenant full-data export + GDPR personal-data export tooling | See [tech_stack.md](tech_stack.md) DB row and [decisions.md](decisions.md) ADR-006/007/008/009 |
| 4 | Backend modernization | `phase-4-backend-modernization` | Not started | Services layer for costing/margin logic, real ModelForms, query performance | |
| 5 | Frontend modernization | `phase-5-frontend-modernization` | Not started | Shared `base.html`, asset pipeline, accessibility, real search/filter | See [tech_stack.md](tech_stack.md) Frontend section |
| 6 | Testing & quality gates | `phase-6-testing-ci` | Not started | Unit/integration tests, ruff/black, CI pipeline | |
| 7 | Observability & operations | `phase-7-observability` | Not started | Structured logging, error tracking, health checks, deployment hardening | |
| 8 | Documentation & team readiness | `phase-8-docs` | Not started | README rewrite, architecture docs, runbooks | |

## Discovery work (must land before dependent phases start)

| Phase | Branch | Status | Scope summary | Notes / links |
|---|---|---|---|---|
| Tech stack decisions | `stack-decisions` | Not started | Resolve every `Open` row in [tech_stack.md](tech_stack.md); log each as an ADR | Blocks Phase 3–5 above |
| Requirements discovery | `requirements-discovery` | Not started | Resolve personas, functional/non-functional requirements, feature backlog priority in [project_requirements.md](project_requirements.md) | Blocks new-feature phases below. Multi-tenancy question already resolved (ADR-006) — remaining Open items are personas, priority, timeline |
| GDPR data inventory | `gdpr-data-inventory` | Not started | Complete the data inventory and policy sections in [gdpr.md](gdpr.md) | Blocks any consent/erasure/audit-log implementation |

## New features (add rows as they're prioritized in `project_requirements.md`)

| Feature | Branch | Status | Scope summary | Notes / links |
|---|---|---|---|---|
| Hosting migration (off home server) | `stack-hosting-migration` | Not started | Move Django app + PostgreSQL off the self-hosted home server/Portainer setup to one of Railway, Render, or DigitalOcean App Platform (narrowed per ADR-003), deployed via the existing Dockerfile rather than a platform buildpack (ADR-004) | See [tech_stack.md](tech_stack.md) "Hosting candidates" and "Deployment method" — pick a host, log as an ADR, then execute |
| AI insights & alerts service (Spark/Databricks) | `feature-ai-insights-service` | Not started | External batch-processing service (Apache Spark on Databricks) triggered by app events (e.g. price/margin change), reads app DB, returns margin alerts and real-time analytics data back to the app | See ADR-002 in [decisions.md](decisions.md) and [tech_stack.md](tech_stack.md) "AI insights / batch analytics service"; needs the API contract + data-scope decision (GDPR §7) resolved before implementation starts |
| Media storage for user uploads (product photos, profile pictures) | `feature-media-storage` | Not started | Add `Product`/profile image fields, integrate S3-compatible object storage (Cloudflare R2 lead candidate) via `django-storages`, decoupled from app hosting | See ADR-005 in [decisions.md](decisions.md), [tech_stack.md](tech_stack.md) "Static & media file storage", and [gdpr.md](gdpr.md) — profile pictures are personal data and the legal basis must be resolved before implementation |
| Tenant full data export (portable/DBMS-importable) | `feature-tenant-data-export` | Not started | Given a tenant, export all of its rows across every tenant-scoped table as portable SQL or a CSV bundle + manifest, importable into another DBMS | See ADR-008 in [decisions.md](decisions.md) and [tech_stack.md](tech_stack.md) "Tenant data export tooling". Depends on Phase 3's `Bakery` tenant model existing first |
| GDPR personal-data export (subject-scoped) | `feature-gdpr-data-export` | Not started | Second, separate export scoped to one data subject's personal data across models — the actual Article 20 portability fix, distinct from the bulk admin CSV export and the tenant-wide export above | See ADR-009 in [decisions.md](decisions.md) and [gdpr.md](gdpr.md) §3 Portability |

## Completed

_(move finished rows here with their merge date/tag, so the tables above stay focused on what's
still ahead)_

None yet.
