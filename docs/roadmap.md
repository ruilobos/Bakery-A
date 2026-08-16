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

## Engineering hardening (Epics 1–8, 19)

| # | Phase | Branch | Status | Scope summary | Notes / links |
|---|---|---|---|---|---|
| 1 | Stabilize the repository | `phase-1-repo-cleanup` | Not started | Remove generated artifacts from VCS, settings package split, dead code cleanup, **`production` branch + branch protection + release tagging (ADR-010)**, **minimal CI pipeline (lint/check/Docker build validation) on every PR**, local dev-env refresh script (ADR-014) | See [decisions.md](decisions.md) ADR-010, ADR-011, ADR-014 |
| 2 | Security & configuration hardening | `phase-2-security-hardening` | Not started | Secrets to env vars, `DEBUG=False` outside dev, **login required by default via `LoginRequiredMiddleware`** rather than per-view opt-in, **three per-tenant roles (Owner/Staff/Read-only) with capability-named checks, Django admin restricted to superusers**, rotatable secret key, stop logging plaintext passwords | See [gdpr.md](gdpr.md) §6 — overlaps with GDPR Article 32. Role model decided in ADR-020, admin surface in ADR-019; 2.8 is no longer blocked. **2.17/2.18 need Epic 19 first** (ADR-027) |
| 3 | Database redesign & data governance | `phase-3-db-redesign` | Not started | Schema fixes (Supplier PK, quantity types, naming), **multi-tenancy (`Bakery` model + tenant FK across all business tables, per ADR-006/ADR-008)**, **the ADR-018 money/unit model (purchase-unit prices, kg/l/each conversion table, dated VAT-rate table, dated sale-price rows, decimal precision + rounding rule)**, migration strategy, retention practices, tenant full-data export + GDPR personal-data export tooling | See [tech_stack.md](tech_stack.md) DB row and [decisions.md](decisions.md) ADR-006/007/008/009/018. **Review the design against Epic 17 (traceability) before implementing** — it adds an event layer to the same tables |
| 4 | Backend modernization | `phase-4-backend-modernization` | Not started | Services layer for costing/margin logic (**including recursive costing through nested base recipes, with a depth guard, and cost provenance returned alongside every figure**), real ModelForms, query performance | See ADR-022. The inline `float()` costing in `control/views.py` is deleted, not patched — it cannot express unit conversion, net-of-VAT storage, dated prices, or recursion |
| 5 | Frontend modernization | `phase-5-frontend-modernization` | Not started | Shared `base.html` + partials, Bootstrap 5.3.x, **HTMX**, **no build step**, **WCAG 2.2 Level A**, responsive tables, **`gettext` + single currency formatter (no hardcoded `€`)**, real search/filter | Stack decided in **[ADR-030](decisions.md)** (9.13 ✅), against a measured baseline: zero `{% extends %}`/`{% include %}` across 4,277 template lines, zero `{% static %}`, and 0 bytes of custom JS. See [tech_stack.md](tech_stack.md) Frontend section and ADR-021. Accessibility and translation-readiness are **build-in, not retrofit** — they are the reason ADR-021 was decided before this epic starts. Per ADR-027, Django's own form rendering (5.22) supplies a share of Level A, so 5.10/5.12 shrink rather than grow |
| 6 | Testing & quality gates | `phase-6-testing-ci` | Not started | Unit/integration tests, ruff/black, **extending** the Phase 1 minimal CI into the full pipeline (tests + security checks + deploy gating) | Builds on [decisions.md](decisions.md) ADR-011's Phase 1 foundation |
| 7 | Observability & operations | `phase-7-observability` | Not started | Structured logging, error tracking, health checks, deployment hardening | |
| 8 | Documentation & team readiness | `phase-8-docs` | Not started | README rewrite, architecture docs, runbooks | |
| 19 | Runtime & dependency upgrade | `stack-runtime-upgrade` | Not started | Python 3.8/3.9 → **3.13**, Django 3.2 → **5.2 LTS** in one direct hop, `psycopg2-binary` → **`psycopg` 3**, PostgreSQL pinned to **17**, dependency set rebuilt (`pytz`/`environ`/`dj-database-url`/`django-mathfilters` removed), `STATICFILES_STORAGE` → `STORAGES` (removed in Django 5.1 — silently ignored, so whitenoise's compression and cache-busting stop without an error), local compose gets a real Postgres service | Decided in [decisions.md](decisions.md) **ADR-025/ADR-026**, with **ADR-027** adopting the capabilities it unlocks (those tasks live in Epics 2/3/5/7/13, and are only available once this lands). Numbered 19 because task IDs are never renumbered — it sits at **step 4** in the execution order, between Epic 2 and Epic 3. Everything currently running is end-of-life, and there are no tests yet, so 19.1's deprecation sweep and 19.8's recorded manual pass are the whole safety net |

## Discovery work (Epics 9–11 — must land before dependent phases start)

| # | Phase | Branch | Status | Scope summary | Notes / links |
|---|---|---|---|---|---|
| 9 | Tech stack decisions | `stack-decisions` | In progress | Resolve every `Open` row in [tech_stack.md](tech_stack.md); log each as an ADR | Blocks Phases 3–5 above and the hosting migration below. **The runtime block is done** (2026-08-10): 9.1, 9.2, 9.3, 9.5, 9.6, 9.7 closed by ADR-025/ADR-026 — Django 5.2 LTS on Python 3.13, PostgreSQL 17, `psycopg` 3 — creating **Epic 19** for the upgrade itself. **9.4 (WSGI/ASGI) is deliberately held** for 9.20. **The backend-architecture block is done** (2026-08-13): 9.9, 9.10, 9.11, 9.12, 9.22 and the caching half of 9.18 closed by [ADR-028](decisions.md) — three settings modules, a batch-first `control/services/` layer, no API, capabilities on Django's own permission API, no cache in the first release, and Brevo over SMTP. **The dependency block is done** (2026-08-16): 9.8 closed by [ADR-029](decisions.md) — `uv pip compile` over a three-file `requirements/` split, hashed pins, and the `.in` file as the dependency register — which unblocks 19.12, the last blocked task in Epic 19, and removes `Pillow` until Epic 13. **The frontend block is done** (2026-08-16): 9.13 and the template half of 9.17 closed by [ADR-030](decisions.md) — shared `base.html` + partials, Bootstrap 5.3.x, HTMX, no SPA, `djlint`, and **no build step** (the Vite candidate rejected on measurement: 0 bytes of custom JS, 922 lines of CSS). Unblocks 5.4, 5.6, 5.7, 5.8. Still open: 9.14–9.17 (CI/CD, monitoring, backups, Python linting + test runner), 9.18's ingredient-line and categories halves, 9.19 (export format), 9.20 (Spark re-confirm), 9.21 (traceability entities) |
| 10 | Requirements discovery | `requirements-discovery` | In progress | Resolve personas, functional/non-functional requirements, business data semantics, and feature backlog priority in [project_requirements.md](project_requirements.md) | **10.1–10.7 all done** (2026-08-06) via ADR-016 → ADR-024. **No longer blocks Epic 2, Epic 3's schema semantics, or Epic 5.** Remaining are follow-ups this pass created: 10.8/10.9 (traceability regulator check + retention floor), 10.10 (tenant seed data), 10.11 (next EU countries), 10.12 (allergen scope → Epic 18), 10.13 (VAT rate assignment), 10.14 (multi-tenant users), 10.15 (WCAG revisit), 10.16 (stale-price threshold), 10.17 (tenant-editable reference data) |
| 11 | GDPR data inventory & policy | `gdpr-data-inventory` | Not started | Complete the data inventory and policy sections in [gdpr.md](gdpr.md) | Blocks any consent/erasure/audit-log implementation, and the profile-picture feature |

## New features (Epics 12–18 — add rows as they're prioritized in `project_requirements.md`)

| # | Feature | Branch | Status | Scope summary | Notes / links |
|---|---|---|---|---|---|
| 12 | Hosting migration (off home server) | `stack-hosting-migration` | Not started | Move Django app + PostgreSQL off the self-hosted home server/Portainer setup to **Railway (Hobby, EU West)** per ADR-013, deployed via the existing Dockerfile rather than Railpack (ADR-004). Production only — the dev/test tier stays local per ADR-014 | Host now chosen (12.1 done); remaining work is provisioning, EU-region volume verification, backups, and the data migration. See [tech_stack.md](tech_stack.md) "Hosting candidates" |
| 13 | Media storage for user uploads (**product photos only** this round) | `feature-media-storage` | Not started | Add a `Product` image field and integrate S3-compatible object storage (Cloudflare R2) via `django-storages`, decoupled from app hosting. **Profile pictures deferred** — ADR-024 rates them `Won't (this round)` | See ADR-005 and **ADR-024** in [decisions.md](decisions.md). Priority: product photos are **Could**, so this epic sits behind the Musts and Shoulds. Deferring profile pictures takes 11.3 (their legal basis) off the critical path |
| 14 | Tenant full data export (portable/DBMS-importable) | `feature-tenant-data-export` | Not started | Given a tenant, export all of its rows across every tenant-scoped table as portable SQL or a CSV bundle + manifest, importable into another DBMS | See ADR-008 in [decisions.md](decisions.md) and [tech_stack.md](tech_stack.md) "Tenant data export tooling". Depends on Phase 3's `Bakery` tenant model existing first |
| 15 | GDPR personal-data export (subject-scoped) | `feature-gdpr-data-export` | Not started | Second, separate export scoped to one data subject's personal data across models — the actual Article 20 portability fix, distinct from the bulk admin CSV export and the tenant-wide export above | See ADR-009 in [decisions.md](decisions.md) and [gdpr.md](gdpr.md) §3 Portability |
| 16 | AI insights & alerts service | `feature-ai-insights-service` | Not started | Margin alerts (notify when a product's margin drops below expectation) and analytics, triggered by app events, returned to the app | **Could**, and **re-scope the engine before any spend** (ADR-024): a margin alert over ADR-018's dated prices is a scheduled query, which is now the null hypothesis Spark/Databricks has to beat (9.20). ADR-002 is still only `Proposed`. Also needs the API contract + data-scope decision (GDPR §7) before implementation |
| 17 | Batch & lot traceability | `feature-traceability` | Not started | Goods receipts with supplier lot codes, production runs consuming specific lots, internal batch lot codes, outbound records, and a one-step-back/one-step-forward trace query. Append-only records | **A legal obligation on the user** (EU Reg. 178/2002 Art. 18, FSAI-enforced), not a nice-to-have — see ADR-017 in [decisions.md](decisions.md). Depends on Epic 3 (tenant scoping, numeric quantities, canonical units), 9.21 (entity shape), and 10.8 (regulator check). Adds an event/temporal layer to a schema that is currently pure current-state — review Epic 3's design against it before implementing 3.19/3.22 |
| 18 | Allergen data | `feature-allergen-data` | Not started | Allergen attributes on raw materials, aggregated up through base recipes to products (EU FIC 1169/2011), with incomplete data marked as incomplete rather than shown as "none" | **Should** per ADR-024. Deliberately outside Epic 17 so the Art. 18 traceability core isn't delayed — but it reuses ADR-022's recipe recursion directly, so it is much cheaper built *after* Epic 17. Scope check is 10.12/18.1 |

## Suggested execution order

Sequencing only — the task-level detail is in [`PRODUCTION_UPDATE_PLAN.md`](../PRODUCTION_UPDATE_PLAN.md).

1. **Epics 9–11 (discovery) run first or in parallel with Epic 1** — they unblock most of what
   follows, and none of them require code changes.
2. Epic 1 — repository cleanup, branch/release setup, minimal CI.
3. Epic 2 — security fixes and permissions hardening (the plaintext-password logging fix should not
   wait for the rest of the epic).
4. **Epic 19 — the runtime upgrade itself** (Django 5.2 LTS on Python 3.13, PostgreSQL 17). Its
   decisions are made (ADR-025/ADR-026); this is now execution, and it must land **before** Epic 3 so
   Epic 3's migrations are written once, against the target version.
5. Epic 3 — database redesign, multi-tenancy, and safe migrations.
6. Epic 4 — backend refactor: services layer, real forms.
7. Epic 5 — frontend template consolidation and asset modernization.
8. Epic 6 — test suite and the full CI gate.
9. Epic 12 → Epic 7 — pick and provision the host, then observability and deployment hardening.
10. Epic 8 — documentation and runbooks, once the things being documented are stable.

Feature epics 13–17 slot in after their prerequisites (noted per epic), ordered by the MoSCoW pass in
[project_requirements.md](project_requirements.md) — logged as ADR-024:

| Priority | Epics / features |
|---|---|
| **Must** | Multi-tenancy (Epic 3), batch/lot traceability (Epic 17), real search/filter (5.9), supplier price comparison (5.21 + 3.63), user & role management (merged into 5.19/2.8/3.58/9.22) |
| **Should** | Tenant data export (Epic 14), GDPR personal-data export (Epic 15), allergen data (Epic 18), trend reporting |
| **Could** | Product photos (Epic 13, narrowed), stock levels (not an epic — a 9.21 design constraint), AI insights (Epic 16, **re-scope the engine first** via 9.20) |
| **Won't (this round)** | Profile pictures, self-service registration, billing/subscriptions |

**Epic 17 is the exception to "prioritize later"** — traceability is a **Must** (ADR-017), and its
data model must be settled (9.21) *before* Epic 3's schema work is implemented, or Epic 3 gets
redesigned twice. Supplier price comparison is likewise a Must that **depends on Epic 17**, since
goods receipts are the data it compares.

**No date pressure.** The first user is a single friendly Irish pilot bakery with no committed launch
date (ADR-016), so this order is driven by risk and dependencies, not by a deadline.

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
- **Supported runtime: Django 5.2 LTS on Python 3.13, PostgreSQL 17 (Epic 19)** — shipping a real
  pilot bakery onto a framework that stopped receiving security patches in April 2024 is not a
  defensible first release, so this is scope, not a follow-up
- Dependency upgrade path prepared with lock files — `uv pip compile`, hashed pins, three-file split
  ([ADR-029](decisions.md); 9.8 ✅ → 19.12, 19.16, 19.17)

## Completed

_(move finished rows here with their merge date/tag, so the tables above stay focused on what's
still ahead)_

None yet.
