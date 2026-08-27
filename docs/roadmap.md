# Roadmap / Phase Tracker

One row per epic — engineering hardening, discovery, and new features alike. This file owns
**sequencing and epic-level status**. Task-level status lives in
[`PRODUCTION_UPDATE_PLAN.md`](../PRODUCTION_UPDATE_PLAN.md), reasoning in
[decisions.md](decisions.md), requirements in [project_requirements.md](project_requirements.md),
stack choices in [tech_stack.md](tech_stack.md). Epic numbers and branch names match the backlog
exactly.

## How to use this file

- **Branch naming** (ADR-001): `phase-N-<slug>` for hardening phases, `feature-` / `gdpr-` /
  `stack-<slug>` otherwise. Every branch targets `main`; promoting `main` → `production` with a
  release tag is a separate step (ADR-010).
- **Status:** `Not started` → `Planned` (plan agreed, branch not opened) → `In progress` →
  `In review` (PR open) → `Done` (merged to `main`) → or `Blocked` (say what on).
- A phase needs an approved plan (Plan Mode) before moving past `Not started`.
- On finish, note the merge commit/tag and any follow-up, then move the row to **Completed**.
- Adding an epic here means adding it to the backlog in the same session.

## Engineering hardening (Epics 1–8, 19)

| # | Epic | Branch | Status | Scope · notes |
|---|---|---|---|---|
| 1 | Stabilize the repository | `phase-1-repo-cleanup` | Not started | Generated artifacts out of VCS, settings package split, dead-code cleanup, **`production` branch + branch protection + release tagging**, **minimal CI (check / migrations / `docker build` / lint) on every PR**, one-command local dev refresh. ADR-010, ADR-011, ADR-014 |
| 2 | Security & configuration hardening | `phase-2-security-hardening` | Not started | Secrets to env vars, `DEBUG=False` outside dev, **login required by default via `LoginRequiredMiddleware`** rather than per-view opt-in, **three per-tenant roles (Owner/Staff/Read-only) with capability-named checks**, Django admin restricted to superusers, rotatable secret key, login throttling + credential-free login auditing. Overlaps [project_requirements.md](project_requirements.md) "Security measures" (Art. 32). Roles ADR-020, admin surface ADR-019. **2.17/2.18 need Epic 19 first** (ADR-027) |
| 3 | Database redesign & data governance | `phase-3-db-redesign` | Not started | Schema fixes (Supplier PK, quantity types, naming), **multi-tenancy (`Bakery` + tenant FK everywhere)**, the **ADR-018 money/unit model**, migration strategy, retention practices, export tooling. ADR-006/007/008/009/018. **No longer blocked** — ADR-032 settles the ingredient line and categories and ADR-033 the traceability entities *before* these migrations are written, which is what stops the same tables being redesigned twice. Build `RawMaterial` accordingly: **no `lot` field, no `stock` field**, numeric quantity with a unit FK |
| 4 | Backend modernization | `phase-4-backend-modernization` | Not started | `control/services/` for costing/margin (**batch-first, recursive through nested base recipes, depth-guarded, provenance returned with every figure**), real ModelForms, query performance. ADR-022, ADR-028. The inline `float()` costing in `control/views.py` is **deleted, not patched** — it cannot express unit conversion, net-of-VAT storage, dated prices or recursion |
| 5 | Frontend modernization | `phase-5-frontend-modernization` | Not started | Shared `base.html` + partials, Bootstrap 5.3.x, **HTMX**, **no build step**, **WCAG 2.2 Level A**, responsive tables, **`gettext` + one currency formatter (no hardcoded `€`)**, real search/filter. ADR-030 (9.13 ✅), decided against a measured baseline: zero `{% extends %}`/`{% include %}` across 4,277 template lines, zero `{% static %}`, 0 bytes of custom JS. Accessibility and translation-readiness are **build-in, not retrofit** (ADR-021). Django's own form rendering (5.22) supplies a share of Level A, so 5.10/5.12 shrink |
| 6 | Testing & quality gates | `phase-6-testing-ci` | Not started | Unit/integration tests, `ruff`/`djlint`, `pip-audit`, **extending** the Phase 1 CI into the full pipeline behind a **70% repo-wide coverage floor**. ADR-011 + ADR-031 (9.14 ✅). The gate switches on at the **end** of the epic (6.22) — enabling it first blocks the PRs that write the tests. No SAST/container scanning this round |
| 7 | Observability & operations | `phase-7-observability` | Not started | Structured logging, **Sentry (EU region) with mandatory PII scrubbing**, health checks, **UptimeRobot**, deployment hardening. ADR-031 (9.15 ✅), both free tiers. Depends on Epic 12 provisioning the host, so the pilot runs unmonitored until then |
| 8 | Documentation & team readiness | `phase-8-docs` | Not started | README rewrite, architecture docs, runbooks |
| 19 | Runtime & dependency upgrade | `stack-runtime-upgrade` | Not started | Python 3.8/3.9 → **3.13**, Django 3.2 → **5.2 LTS** in one direct hop, `psycopg2-binary` → **`psycopg` 3**, PostgreSQL pinned to **17**, dependency set rebuilt, `STATICFILES_STORAGE` → `STORAGES` (removed in Django 5.1 — silently ignored, so whitenoise's compression and cache-busting stop without an error), local compose gets a real Postgres service. ADR-025/ADR-026, with ADR-027 adopting the capabilities it unlocks (those tasks live in Epics 2/3/5/7/13 and are only available once this lands). Numbered 19 because task IDs are never renumbered — it runs at **step 4**, between Epic 2 and Epic 3. Everything currently running is end-of-life and there are no tests, so 19.1's deprecation sweep and 19.8's recorded manual pass are the whole safety net |

## Discovery work (Epics 10–11 — land before dependent phases start)

Epic 9 (tech stack decisions) is **Done** — see [Completed](#completed).

| # | Epic | Branch | Status | Scope · notes |
|---|---|---|---|---|
| 10 | Requirements discovery | `requirements-discovery` | In progress | Resolve personas, functional/non-functional requirements, data semantics and backlog priority in [project_requirements.md](project_requirements.md). **10.1–10.7 done** (2026-08-06, ADR-016 → ADR-024) — **no longer blocks Epic 2, Epic 3's schema semantics, or Epic 5.** Remaining follow-ups: 10.8/10.9 (traceability regulator check + retention floor), 10.10 (tenant seed data), 10.11 (next EU countries), 10.12 (allergen scope → Epic 18), 10.13 (VAT rate assignment), 10.14 (multi-tenant users), 10.15 (WCAG revisit), 10.16 (stale-price threshold), 10.17 (tenant-editable reference data), 10.18 (email-endpoint budget carve-out) |
| 11 | GDPR data inventory & policy | `gdpr-data-inventory` | Not started | Complete the inventory and policy sections in [project_requirements.md](project_requirements.md) Part 2. Blocks any consent/erasure/audit-log implementation |

## New features (Epics 12–18 — add rows as they're prioritized)

| # | Feature | Branch | Status | Scope · notes |
|---|---|---|---|---|
| 12 | Hosting migration (off home server) | `stack-hosting-migration` | Not started | Django app + PostgreSQL off the self-hosted Portainer setup onto **Railway (Hobby, EU West)** (ADR-013), deployed via the repo's Dockerfile rather than Railpack (ADR-004). Production only — the dev/test tier stays local (ADR-014). Host chosen (12.1 ✅); what remains is provisioning, EU-region volume verification, backups and the data migration |
| 13 | Media storage for user uploads (**product photos only** this round) | `feature-media-storage` | Not started | `Product` image field + S3-compatible object storage (Cloudflare R2) via `django-storages`, decoupled from app hosting. ADR-005. **Profile pictures deferred** — ADR-024 rates them `Won't (this round)`, which takes 11.3 (their legal basis) off the critical path. Product photos are a **Could**, so this epic sits behind the Musts and Shoulds |
| 14 | Tenant full data export | `feature-tenant-data-export` | Not started | Every row of one tenant across every tenant-scoped table as a **ZIP of per-table CSVs + `manifest.json`** (ADR-008, format fixed by ADR-035), importable elsewhere. Depends on Epic 3's `Bakery` model |
| 15 | GDPR personal-data export (subject-scoped) | `feature-gdpr-data-export` | Not started | A second export scoped to **one data subject** — the actual Article 20 portability fix, distinct from the bulk admin CSV export and from Epic 14. ADR-009, [project_requirements.md](project_requirements.md) Part 2 §3 |
| 16 | AI insights & alerts service | `feature-ai-insights-service` | Not started | Margin alerts and analytics from a nightly extract, returned to the app. **Engine confirmed** (ADR-036, 9.20 ✅): **Databricks Serverless Jobs, AWS EU (Ireland)** — ADR-002 moves `Proposed` → `Accepted`, chosen over ADR-024's scheduled-query null hypothesis as a deliberate bet on headroom. Django pushes a **personal-data-free** costing extract to R2; Databricks never touches PostgreSQL. Nightly schedule, results POSTed to a shared-secret callback — **no event triggering**. Still a **Could**, and now a **cost decision**: ~$6 → ~$21/mo against zero revenue, so 16.8 measures a real run before production spend. Two new processors need DPAs (11.17, 16.4) |
| 17 | Batch & lot traceability | `feature-traceability` | Not started | Goods receipts with supplier lot codes, production runs consuming specific lots, internal batch lot codes, outbound records, and a one-step-back/one-step-forward trace query. Append-only. **A legal obligation on the user** (EU Reg. 178/2002 Art. 18, FSAI-enforced), not a nice-to-have — ADR-017. **Entity shape decided** (ADR-033, 9.21 ✅): `GoodsReceipt`→`GoodsReceiptLine`, `ProductionRun`→`Consumption`→`Batch`→`OutboundRecord`, `YYYYMMDD-NNN` per-tenant lot codes, stock derivable but deliberately not surfaced. Receipts-only was rejected on ADR-017's own "partial is worse than none". Depends on Epic 3 and 10.8 |
| 18 | Allergen data | `feature-allergen-data` | Not started | Allergen attributes on raw materials, aggregated through base recipes to products (EU FIC 1169/2011), with incomplete data marked incomplete rather than shown as "none". **Should** per ADR-024. Deliberately outside Epic 17 so the Art. 18 core isn't delayed — but it reuses ADR-022's recipe recursion directly, so it is much cheaper built *after* Epic 17. Scope check is 10.12/18.1 |

## Suggested execution order

Sequencing only — task detail is in the [backlog](../PRODUCTION_UPDATE_PLAN.md).

1. **Epics 10–11 (discovery) run first or alongside Epic 1** — they unblock most of what follows and
   need no code changes.
2. Epic 1 — repository cleanup, branch/release setup, minimal CI.
3. Epic 2 — security fixes and permissions hardening.
4. **Epic 19 — the runtime upgrade** (Django 5.2 LTS, Python 3.13, PostgreSQL 17). Decisions are
   made; this is execution, and it must land **before** Epic 3 so Epic 3's migrations are written
   once, against the target version.
5. Epic 3 — database redesign, multi-tenancy, safe migrations.
6. Epic 4 — services layer, real forms.
7. Epic 5 — template consolidation and asset modernization.
8. Epic 6 — test suite and the full CI gate.
9. Epic 12 → Epic 7 — provision the host, then observability and deployment hardening.
10. Epic 8 — documentation and runbooks, once what they document is stable.

Feature epics 13–18 slot in after their prerequisites, ordered by ADR-024's MoSCoW pass:

| Priority | Epics / features |
|---|---|
| **Must** | Multi-tenancy (Epic 3), batch/lot traceability (Epic 17), real search/filter (5.9), supplier price comparison (5.21 + 3.63), user & role management (merged into 5.19/2.8/3.58/9.22) |
| **Should** | Tenant data export (Epic 14), GDPR personal-data export (Epic 15), allergen data (Epic 18), trend reporting |
| **Could** | Product photos (Epic 13, narrowed), stock levels (a 9.21 design constraint, not an epic), AI insights (Epic 16) |
| **Won't (this round)** | Profile pictures, self-service registration, billing/subscriptions |

**Epic 17 is the exception to "prioritize later"** — traceability is a Must (ADR-017), and its data
model had to be settled (9.21 ✅) *before* Epic 3's schema work is implemented, or Epic 3 gets
redesigned twice. Supplier price comparison is likewise a Must that **depends on Epic 17**, since
goods receipts are the data it compares.

**No date pressure.** One friendly Irish pilot bakery, no committed launch date (ADR-016), so this
order is driven by risk and dependencies.

## Milestone: first production release scope

Risk reduction over feature expansion. Shippable when these are done (task IDs from the backlog):

- Secrets removed from source (2.1) and `DEBUG = False` outside dev (2.2)
- Settings split by environment (1.5)
- Authentication and authorization enforced in views (2.6, 2.7, 2.17)
- Credential-free login auditing in place (2.23)
- Known functional defects fixed, including the user-delete flow (6.7)
- Repository artifacts cleaned up (1.1, 1.2)
- Basic automated tests for core flows (6.8)
- Deployment configuration normalized (7.7, 7.8, 7.9)
- **Supported runtime: Django 5.2 LTS on Python 3.13, PostgreSQL 17 (Epic 19)** — shipping a real
  pilot bakery onto a framework that stopped receiving security patches in April 2024 is not a
  defensible first release, so this is scope, not a follow-up
- Dependency upgrade path prepared with lock files — `uv pip compile`, hashed pins, three-file split
  (ADR-029; 9.8 ✅ → 19.12, 19.16, 19.17)

## Completed

| # | Epic | Branch | Finished | Outcome |
|---|---|---|---|---|
| 9 | Tech stack decisions | `stack-decisions` | **2026-08-26** | All 22 tasks closed; [tech_stack.md](tech_stack.md) has no `Open` rows left. Runtime block closed 2026-08-10 (ADR-025/ADR-026, creating Epic 19), backend architecture 2026-08-13 (ADR-028), dependencies and frontend 2026-08-16 (ADR-029/ADR-030), operations 2026-08-18 (ADR-031), and the final six on 2026-08-26 (ADR-032–ADR-036): one shared `RecipeLine` + tenant-scoped `Category` (9.18), traceability entities/lot codes/stock (9.21), `ruff` + `pytest-django` (9.17), tenant export as CSV bundle + manifest (9.19), and Databricks Serverless confirmed on AWS EU (Ireland) under a ~$15/mo ceiling (9.20) — which released 9.4 (gunicorn, WSGI). **Epics 3, 4, 5, 6 and 12 are no longer blocked by it.** A new stack question re-opens the epic with a new task *and* an `Open` row in `tech_stack.md`; it does not get answered in passing |
