# Bakery Production Backlog

The **task backlog** — 308 tasks across 19 epics. Every phase, discovery workstream and feature is an
**Epic**; every epic holds numbered tasks that can be picked up, tracked and closed. This file owns
**epic and task status and sequencing**.

**It holds work, not planning.** One home per kind of thing:

| If it is… | It lives in… |
|---|---|
| A question with no answer yet — stack, product, or data protection | [docs/roadmap.md](docs/roadmap.md) |
| A decision that *has* been made, with its reasoning | [docs/decisions.md](docs/decisions.md) |
| What the app should do, and its GDPR obligations | [docs/project_requirements.md](docs/project_requirements.md) |
| What it is built with | [docs/tech_stack.md](docs/tech_stack.md) |

The flow is one-directional: **open question → decided → ADR → tasks here.** Every `Accepted` entry in
`decisions.md` maps to at least one task (see [Decision → task coverage](#decision--task-coverage)).

## How to use this backlog

- **Task IDs are stable** (`3.12` = Epic 3, task 12). Reference them in commits, PRs and plans. Never
  renumber — append new tasks at the end of their section.
- **Task status:** `Not started` → `In progress` → `Done`, or `Blocked` (Notes says what on).
  A task is `Done` when its own PR is merged to `main` ([ADR-037](docs/decisions.md)).
  **Epic status** is the table below: `Not started` → `Planned` (plan agreed, no task branch opened)
  → `In progress` → `In review` (its last task PRs are open) → `Done` (all its tasks merged to `main`).
- **A `Blocked` task must not be implemented.** Its blocker is an open decision in
  [roadmap.md](docs/roadmap.md); make and log the ADR first.
- **Task = branch**, named per [ADR-037](docs/decisions.md): `<epic-branch>-<task-id>`, e.g.
  `phase-1-repo-cleanup-1.1`. The epic name is still `phase-N-<slug>` for hardening phases,
  `feature-` / `gdpr-` / `stack-<slug>` otherwise — it now *prefixes* the task branch rather than
  being one. **An epic groups and sequences; it does not branch.** Every branch targets `main`;
  promoting `main` → `production` with a release tag is a separate step. A task needs an approved
  plan before moving past `Not started`. `/next-task` executes one ([ADR-038](docs/decisions.md)).
- **New work starts as a task here**, not as a paragraph. If it needs a decision first, add the
  question to [roadmap.md](docs/roadmap.md) instead.
- **Notes cite the governing ADR and the trap worth knowing — not the argument.** The reasoning is in
  `decisions.md` by design; don't copy it back.

## Backlog at a glance

| Epic | Name | Branch | Status | Tasks | Blocked by |
|---|---|---|---|---|---|
| [1](#epic-1--stabilize-the-repository) | Stabilize the repository | `phase-1-repo-cleanup` | Not started | 16 | — |
| [2](#epic-2--security--configuration-hardening) | Security & configuration hardening | `phase-2-security-hardening` | Not started | 23 | Epic 1 |
| [3](#epic-3--database-redesign--data-governance) | Database redesign & data governance | `phase-3-db-redesign` | Not started | 74 | Epic 19 |
| [4](#epic-4--backend-modernization) | Backend modernization | `phase-4-backend-modernization` | Not started | 20 | Epic 3 |
| [5](#epic-5--frontend-modernization) | Frontend modernization | `phase-5-frontend-modernization` | Not started | 25 | Epics 3, 19 |
| [6](#epic-6--testing--quality-gates) | Testing & quality gates | `phase-6-testing-ci` | Not started | 24 | Epics 1–5 |
| [7](#epic-7--observability--operations) | Observability & operations | `phase-7-observability` | Not started | 23 | Epic 12 |
| [8](#epic-8--documentation--team-readiness) | Documentation & team readiness | `phase-8-docs` | Not started | 9 | Epics 1–7 |
| 9 | Tech stack decisions | `stack-decisions` | **Done** 2026-08-26 | — | Closed by ADR-025 → ADR-036 |
| 10 | Requirements discovery | `requirements-discovery` | In progress | — | Its questions live in [roadmap.md](docs/roadmap.md) `10.x` |
| [11](#epic-11--gdpr-data-inventory--policy) | GDPR data inventory & policy | `gdpr-data-inventory` | Not started | 10 | Judgments live in [roadmap.md](docs/roadmap.md) `11.x` |
| [12](#epic-12--hosting-migration) | Hosting migration | `stack-hosting-migration` | Not started | 11 | — |
| [13](#epic-13--media-storage-for-user-uploads) | Media storage for user uploads | `feature-media-storage` | Not started | 11 | Epics 3, 19 |
| [14](#epic-14--tenant-full-data-export) | Tenant full data export | `feature-tenant-data-export` | Not started | 6 | Epic 3 |
| [15](#epic-15--gdpr-personal-data-export) | GDPR personal-data export | `feature-gdpr-data-export` | Not started | 6 | Epic 11 |
| [16](#epic-16--ai-insights--alerts-service) | AI insights & alerts service | `feature-ai-insights-service` | Not started | 13 | Epic 11 |
| [17](#epic-17--batch--lot-traceability) | Batch & lot traceability | `feature-traceability` | Not started | 14 | Epic 3, roadmap 10.8 |
| [18](#epic-18--allergen-data) | Allergen data | `feature-allergen-data` | Not started | 6 | Epics 3, 17, roadmap 10.12 |
| [19](#epic-19--runtime--dependency-upgrade) | Runtime & dependency upgrade | `stack-runtime-upgrade` | Not started | 17 | Epic 2 |

## Execution order

Driven by risk and dependencies — **no date pressure** (one Irish pilot, no committed launch date,
[ADR-016](docs/decisions.md)). Feature epics 13–18 slot in after their prerequisites, ordered by
ADR-024's MoSCoW pass.

1. **Epic 11 (discovery) runs first or alongside Epic 1** — it needs no code changes and unblocks
   Epics 13, 15 and 16.
2. Epic 1 — repository cleanup, branch/release setup, minimal CI.
3. Epic 2 — security fixes and permissions hardening.
4. **Epic 19 — the runtime upgrade.** Must land **before** Epic 3, so Epic 3's migrations are written
   once, against the target version. Numbered 19 because task IDs are never renumbered.
5. Epic 3 — database redesign, multi-tenancy, safe migrations.
6. Epic 4 — services layer, real forms.
7. Epic 5 — template consolidation and asset modernization.
8. Epic 6 — test suite and the full CI gate.
9. Epic 12 → Epic 7 — provision the host, then observability and deployment hardening.
10. Epic 8 — documentation and runbooks, once what they document is stable.

**Two Epic 6 tasks run early, straight after 1.11: [6.23](#epic-6--testing--quality-gates)** (`pytest`
+ `pytest-django` + `pytest-cov`) **and [6.10](#epic-6--testing--quality-gates)** (`ruff`). Both are
already decided by [ADR-034](docs/decisions.md) and 6.10 is already `Unblocked`; they sit in Epic 6
only by grouping. Until they land there is no way for a task to ship with a test, and
[ADR-038](docs/decisions.md)'s loop requires exactly that. **Their IDs do not change and they remain
Epic 6 tasks** — this is sequencing, not renumbering. **6.22's coverage gate is explicitly *not*
pulled forward**: switching it on before the tests exist blocks the PRs that write them.

**Epic 17 is the exception to "features last"** — traceability is a Must ([ADR-017](docs/decisions.md))
and its data model had to be settled before Epic 3's schema work, or Epic 3 gets redesigned twice.
Supplier price comparison is likewise a Must that **depends on Epic 17**, since goods receipts are the
data it compares.

## Milestone: first production release scope

Risk reduction over feature expansion. Shippable when these are done:

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
- Dependency upgrade path prepared with lock files (19.12, 19.16, 19.17)

---

## Epic 1 — Stabilize the repository

**Branch:** `phase-1-repo-cleanup` · **Depends on:** —

Get the repository, its history and its branch/CI plumbing into a state where every later epic can
ship safely through a PR.

### Source control cleanup

| ID | Task | Status | Notes |
|---|---|---|---|
| 1.1 | Remove generated and local-only artifacts from version control (`__pycache__/`, `bakery/staticfiles/`, `.idea/`, `.venv/`, OS/editor temp files) | Not started | |
| 1.2 | Expand `.gitignore` to cover Python, Django, environment, build and IDE artifacts | Not started | |
| 1.3 | Keep only source assets in `bakery/static/`; confirm nothing depends on the committed `staticfiles/` output | Not started | **Prerequisite for 5.3** — a committed stale manifest is the classic "worked locally, 500 in production". ADR-027 |
| 1.4 | Re-save `requirements.txt` as UTF-8 (currently UTF-16LE) | Not started | Blocks tooling that reads it. Absorbed into 19.2 if Epic 19 lands first |
| 1.5 | Split settings into `settings/base.py` + `local.py` + `test.py`; retire the Heroku module | Not started | ADR-028: **three** modules, not four — `base.py` *is* production. `manage.py` and the `Dockerfile` both default to `base`. Pairs with 2.1, 2.19; deletes `settings/heroku.py` (7.9) and `runtime.txt` |
| 1.6 | Remove dead code, duplicate assets and unused views/forms (e.g. `control/forms.py: Raw_Material_Form`, wired into nothing) | Not started | |
| 1.7 | Rename prototype identifiers: `categorie`→`category`, `recipe_yeld`→`recipe_yield`, `Base_recipes`→`BaseRecipe`, `Bs_Ingredients`→`BaseRecipeIngredient`, `Recipe_Ingredients`→`ProductIngredient` | Not started | Transitional migrations + compatibility layers, never a big-bang rename; sequence with Epic 3 |

### Branch, release and CI plumbing

| ID | Task | Status | Notes |
|---|---|---|---|
| 1.8 | Create the `production` branch as the deploy branch, with `main` as integration/dev-test | Not started | ADR-010 |
| 1.9 | Branch protection on `main` and `production`: PR-only, no direct pushes, no force-pushes (0 required approvals while solo) | Not started | ADR-010 |
| 1.10 | Define the release step: every merge to `production` is tagged semver and published as a GitHub Release with auto-generated notes | Not started | ADR-010 |
| 1.11 | Minimal GitHub Actions workflow on every PR against `main`/`production`: `manage.py check`, `makemigrations --check --dry-run`, `docker build`, basic lint | Not started | ADR-011. No test run (none exist) and no deploy step (no host yet) — verification only; extended by 6.12 |
| 1.12 | Script that refreshes and launches the local dev environment in one command — pull `main`, rebuild containers, run migrations | Not started | ADR-014. Run **manually**; GitHub cannot trigger a local machine. Missing the migration step is the usual cause of a confusing local failure |
| 1.13 | Add `collectstatic --noinput` to CI, so a referenced-but-missing static asset fails the PR, not the deploy | Not started | Extends 1.11; load-bearing at 5.3, where `ManifestStaticFilesStorage` turns a missing file into a render-time `ValueError`. ADR-027 |
| 1.14 | Agent workflow scaffolding: `.claude/settings.json` permissions, the five task subagents, and the `/next-task` skill | Not started | ADR-038. Procedure and pointers only — **no architectural facts under `.claude/`**. The subagents exist to keep the backlog and ADR log out of main context, not to parallelize |
| 1.15 | Guard hooks: block direct pushes to `main`/`production`, block a drive-by rename of the prototype identifiers, block a commit that leaves this file's task status stale | Not started | ADR-038. Local only, so they are a fast failure and never the real enforcement — that stays 1.9 and 1.11. The rename guard exists because `categorie` alone is 137 sites across 58 files (1.7) |
| 1.16 | PR template carrying the task ID and the verification checklist | Not started | ADR-037. One PR per task makes the task ID the thing a reviewer needs first |

---

## Epic 2 — Security & configuration hardening

**Branch:** `phase-2-security-hardening` · **Depends on:** Epic 1

### Configuration

| ID | Task | Status | Notes |
|---|---|---|---|
| 2.1 | Move all secrets to environment variables or a secret manager; remove the hardcoded `SECRET_KEY` and database credentials from source | Not started | |
| 2.2 | Set `DEBUG = False` everywhere outside local development | Not started | |
| 2.3 | Environment-specific `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` and cookie settings | Not started | |
| 2.4 | Secure defaults: `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_HSTS_SECONDS`, `SECURE_HSTS_INCLUDE_SUBDOMAINS`, `SECURE_HSTS_PRELOAD`, `X_FRAME_OPTIONS` | Not started | |
| 2.5 | Hold object-storage (R2) access keys as environment variables — never hardcoded | Not started | ADR-005; pairs with 13.3 |
| 2.19 | Make `settings/base.py` fail loudly at boot when `SECRET_KEY`, `ALLOWED_HOSTS` or `DEBUG` is unset — no defaults for any of the three — and test it | Not started | ADR-028. Retires today's inversion: `base.py` ships a real `SECRET_KEY`/`DEBUG = True` and `heroku.py:11` defaults `DEBUG` to `True` in the *production* module. Pairs with 1.5, 2.1 |

### Authentication and authorization

| ID | Task | Status | Notes |
|---|---|---|---|
| 2.6 | Protect all business views with `LoginRequiredMixin` | Not started | **Reshaped by 2.17** — the middleware becomes the mechanism; this becomes a belt-and-braces pass. Do 2.17 first |
| 2.7 | Protect admin-only operations with explicit permission classes/mixins; stop relying on template-only `is_staff` checks | Not started | **Reshaped by 2.20** — these become stock Django mixins over capability codenames |
| 2.8 | Role-based permissions for **Owner / Staff / Read-only**, scoped **per tenant** | **Unblocked** | ADR-020. Role lives on the membership record (3.58). Matrix in [project_requirements.md](docs/project_requirements.md) |
| 2.9 | Audit logging for user management and destructive actions | Not started | Extended by 11.10 |
| 2.15 | Restrict the Django admin to superusers, keep it out of tenant-facing navigation, log its access to personal data | Not started | ADR-019 — a deliberate **cross-tenant** surface. `ModelAdmin` does **not** apply the tenant-scoped managers from 3.3/3.55. Feeds 11.10 |
| 2.16 | Express every permission check as a named capability (`can_manage_users`, `can_edit_pricing`, `can_record_receipt`), never `role == "owner"` | Not started | ADR-020. Costs nothing with three roles; keeps adding Manager a table row rather than a rewrite |
| 2.17 | Enable `LoginRequiredMiddleware`; mark deliberate exceptions with `@login_not_required` (the `core` cover page, the login view, 16.10's callback) | Not started | ADR-027, Django 5.1 — **needs Epic 19**. Inverts the default so a forgotten view fails closed. The real fix for "access control enforced in templates" |
| 2.18 | Configure `SECRET_KEY_FALLBACKS` so the signing key rotates without invalidating active sessions | Not started | ADR-027, Django 4.1 — **needs Epic 19**. Pairs with 2.1; makes 8.6's runbook something someone would actually run |
| 2.20 | Define the capability set per role as permission codenames; implement the custom auth backend resolving `has_perm()` against the active membership | Not started | ADR-028. Keeps `PermissionRequiredMixin`, `@permission_required` and `{% if perms.… %}` working — **one** permission vocabulary. Needs 3.58 |
| 2.21 | Middleware resolving the active bakery + membership onto the request, invalidating Django's cached permissions whenever the active tenant changes | Not started | ADR-028. The invalidation half is a **cross-tenant leak** if missed — a two-membership user would carry bakery A's capabilities into bakery B. Test it (6.9) |

### Input and data protection

| ID | Task | Status | Notes |
|---|---|---|---|
| 2.10 | ~~Replace the `print()` login diagnostics in `accounts/views.py` with structured logging~~ | **Superseded** by 4.5 + 2.23 | Verified 2026-08-13 (ADR-028): `accounts.urls` is never included and no template reverses `user_login`, so the password-logging `print()` is **unreachable dead code, not a live leak**. Deleted by 4.5; the real requirement is 2.23. Recorded in [project_requirements.md](docs/project_requirements.md) "Personal data inventory"/§6 |
| 2.11 | Validate and sanitize all form input server-side | Not started | Business-rule validation is 4.8 |
| 2.12 | Server-side authorization on every export endpoint | Not started | |
| 2.13 | Remove the broken leftover `MEDIA_ROOT` path (`bluebiulding/media`) | Not started | Real media handling is Epic 13; cleaned up under `STORAGES` in 19.14 |
| 2.14 | Confirm encryption in transit (HTTPS enforced end-to-end) once the settings work lands | Not started | Art. 32 — [project_requirements.md](docs/project_requirements.md) "Security measures" |
| 2.22 | Brute-force protection on the login endpoint (attempt throttling with lockout/backoff) | Not started | **Gap surfaced by ADR-028** — no epic covered it. Django's auth views ship no rate limiting, and 4.5 makes this the single credential entry point for every tenant |
| 2.23 | Structured audit events for failed and successful logins that record the attempt but **never** the submitted credentials | Not started | **Replaces 2.10.** [project_requirements.md](docs/project_requirements.md) "Security measures". Pairs with 2.22 (throttling needs the record); feeds 11.7, since login history is personal data with its own retention question |

---

## Epic 3 — Database redesign & data governance

**Branch:** `phase-3-db-redesign` · **Depends on:** Epic 19 (so the migrations are written once,
against the target version)

Make the schema consistent, normalized, migration-safe and tenant-scoped, while preserving
historical business data. **No longer blocked by Epics 9/10/11** — ADR-032 and ADR-033 settled the
ingredient line, categories and traceability entities before these migrations get written.

### Multi-tenancy

| ID | Task | Status | Notes |
|---|---|---|---|
| 3.1 | Add a `Bakery` model as the tenant root | Not started | ADR-006. **No plan/tier/subscription fields** (ADR-016) |
| 3.2 | Tenant FK on every business table: `Supplier`, `RawMaterial`, `Base_recipes`, `Product`, `RecipeLine`, future `Profile` | Not started | ADR-008 |
| 3.3 | Enforce tenant scoping at the query layer (managers/service layer always filter by current tenant) | Not started | A missed filter is a cross-tenant leak. Tested in 6.9 |
| 3.4 | Scope user roles/permissions per tenant in the data model | Not started | Pairs with 2.8; implemented as the membership record in 3.58 |

### Supplier

| ID | Task | Status | Notes |
|---|---|---|---|
| 3.5 | Replace supplier name as primary key with a generated numeric or UUID PK | Not started | |
| 3.6 | Supplier name unique **per tenant**, over non-archived rows only, via a partial unique index | **Unblocked** | ADR-019. Not global — two bakeries may both buy from "Odlums". Partial, because a plain composite constraint would let an archived row block that name forever. **Sequenced after 3.2** |
| 3.7 | Change phone from `IntegerField` to a string field | Not started | |
| 3.8 | Add optional address, tax/business identifier, active flag, timestamps | Not started | |

### Raw material

| ID | Task | Status | Notes |
|---|---|---|---|
| 3.9 | Change `quantity` from `CharField` to `DecimalField` | Not started | |
| 3.10 | Price semantics: `purchase_price` + `pack_quantity` + `purchase_unit` as the invoice states them — cost per canonical unit derived at cost time, never persisted | **Unblocked** | ADR-018. Same three fields a goods-receipt line records, so 17.1 must agree. **No `lot` field, no `stock` field** (ADR-033) |
| 3.11 | Normalized unit handling: convert any purchase unit to its canonical unit (kg / l / each) via the conversion factor | **Unblocked** | ADR-018. Depends on 3.10 and the unit table (3.52) |
| 3.12 | SKU/code uniqueness rules where appropriate | Not started | |
| 3.13 | Active/inactive status instead of hard deletes where business history matters | Not started | Not a judgment call: anything referenced by a traceability record can never be hard-deleted (ADR-017) — enforced in 17.6 |

### Base recipe and product

| ID | Task | Status | Notes |
|---|---|---|---|
| 3.14 | Standardize yield, unit and cost fields across base recipes and products | Not started | **No `stock` field** (ADR-033) |
| 3.15 | VAT consistency: all stored money **net (ex-VAT)**; product references a VAT rate **code**, not a percentage; VAT applied only at display/sale | **Unblocked** | ADR-018. Rate table is 3.53; which rate a product gets is a tax question (10.13) |
| 3.16 | Version sale pricing: dated `ProductPrice` rows (product, net price, `valid_from`); current price = latest row whose `valid_from` has passed | **Unblocked** | ADR-018. **Input** price history is not built here — it comes free from receipts (17.12) |
| 3.17 | Store calculated values as derived data only, never as editable business data | Not started | Pairs with 4.1 |
| 3.18 | Add the `Product.photo` field | Not started | Owned by 13.4 — this row exists so the schema work is sequenced with it |

### Ingredient relations

| ID | Task | Status | Notes |
|---|---|---|---|
| 3.19 | Build the shared `RecipeLine` model — typed parent (`parent_product` XOR `parent_base_recipe`), typed component (`component_material` XOR `component_recipe`), `quantity` + unit FK — replacing both `Bs_Ingredients` and `Recipe_Ingredients` | **Unblocked** | ADR-032. Both XORs are database `CHECK` constraints in the same migration, **not** `clean()` — `clean()` does not run on `bulk_create`, which is how an import writes these rows. Merge migration is 3.73 |
| 3.20 | Uniqueness constraints preventing duplicate ingredient lines for the same parent/item/unit | Not started | |

### Database best practices

| ID | Task | Status | Notes |
|---|---|---|---|
| 3.21 | `created_at` / `updated_at` on all core business tables | Not started | |
| 3.22 | Soft delete / archive on `Supplier`, `RawMaterial`, `Product`, `Base_recipes`; ingredient lines stay hard-deletable | **Unblocked** | ADR-019 — "anything referenced by a record that outlives it" |
| 3.23 | `db_index=True` or explicit indexes on common filter/join paths | Not started | |
| 3.24 | Unique and check constraints wherever a business rule exists | Not started | |
| 3.25 | `Decimal` consistently for money and quantities (schema and application code) | Not started | Removes the `float()` math in `control/views.py` — pairs with 4.1 |
| 3.26 | Standardize units and categories via lookup/reference tables | **Unblocked** | Units (ADR-018) in 3.52; categories (ADR-032) in 3.74. The difference that matters: categories are tenant-editable, units are not |

### Migration strategy

| ID | Task | Status | Notes |
|---|---|---|---|
| 3.27 | Document the current schema and its data-quality issues before changing anything | Not started | |
| 3.28 | Full, verified database backup before the first migration | Not started | |
| 3.29 | Introduce additive fields first (no destructive changes in the same release) | Not started | |
| 3.30 | Backfill data with safe migrations or management commands | Not started | |
| 3.31 | Switch application code over to the new fields | Not started | |
| 3.32 | Remove legacy fields only after validation and deployment stability | Not started | 3.54's price backfill must complete first |
| 3.33 | Migration rollback guidance for every schema-change release | Not started | |

### Data quality and governance

| ID | Task | Status | Notes |
|---|---|---|---|
| 3.34 | Define the canonical costing units | **Done (decided)** | 2026-08-06 — **kilogram / litre / each**, one per dimension (ADR-018). Implementation is 3.11/3.52 |
| 3.35 | Data validation rules for prices, VAT, yields and quantities | Not started | |
| 3.36 | Import/export contracts and field definitions | Not started | Feeds Epics 14 and 15 |
| 3.37 | Seed/reference data strategy for categories and units | Blocked | Depends on 3.26; pairs with 10.10 |
| 3.38 | Backup, restore and retention procedures, including a tested restore drill | Not started | **Unblocked** by ADR-031: *backup* retention is 7 daily / 4 weekly / 12 monthly — a **different clock** from GDPR *record* retention (11.4) and the food-law floor (10.9). Executed by 3.70–3.72, 3.44–3.48; written up in 8.5 |

### Database operations for production

| ID | Task | Status | Notes |
|---|---|---|---|
| 3.39 | Run on managed PostgreSQL as a service separate from the app | Not started | ADR-007; provisioned in 12.2 |
| 3.40 | Enable automated backups; **PITR deliberately not adopted** | Not started | ADR-031. **RPO up to 24 h is an accepted, stated position** — record it in 8.5 so the pilot bakery has seen it. Executed by 12.9 + 3.70 |
| 3.41 | Separate application and database credentials per environment | Not started | Includes the **backup-scoped, rotatable** credentials 3.70 needs in CI |
| 3.42 | ~~Add connection pooling if traffic requires it~~ | **Superseded by 7.19** | Closed by ADR-027 — Django 5.1's native psycopg pool, no separate pooler service |
| 3.43 | Monitor slow queries and add indexes based on observed workload | Not started | Needs 7.1/7.20 to observe |
| 3.44 | Maintain a **host-independent logical backup** (`pg_dump`) alongside the host's native snapshot, and prove it by restoring onto a *different* instance | Not started | ADR-015 rule 5. **This is what makes the host replaceable** — a Railway volume snapshot cannot be restored onto Clever Cloud or Scaleway |
| 3.45 | Restrict the schema to core PostgreSQL and widely-available extensions; host-specific features need their own ADR | Not started | ADR-015 rule 6 |
| 3.46 | Commit the exact dump and restore commands as scripts, flags settled — not prose in a runbook | Not started | ADR-015 rule 5. Settle `--no-owner --no-privileges` (plus explicit re-granting) and the dump format now, not during a migration |
| 3.47 | Post-restore verification: per-table row counts against source, constraint/FK validation, sequence positions, `REINDEX` | Not started | What "proven restore" in 3.44 means. `REINDEX` matters because text index ordering depends on OS collation (glibc/ICU) — a cross-host restore can leave indexes subtly wrong while everything *looks* fine |
| 3.48 | Automate the restore drill **weekly** — decrypt the latest dump, restore into a throwaway PostgreSQL 17, run 3.47's checks, alert on failure | Not started | **The key one.** ADR-031. The **only** recurring proof that 3.72's `age` key still works, so it must decrypt rather than restore a plaintext copy. Alerting on a *missed* run matters as much as on a failed one |
| 3.49 | Verify `migrate` from empty reproduces the production schema exactly; forbid manual DDL outside migrations | Not started | Drift quietly breaks both host migration and 12.10's PR-environment seeding |

### Money, units and price history (ADR-018)

| ID | Task | Status | Notes |
|---|---|---|---|
| 3.50 | Decimal precision: quantities at least `Decimal(12,4)` (`12,6` safer), money carried beyond 2 dp internally | Not started | **The price of kg/l canonical units** — 7 g of yeast is `0.007 kg`. Too little scale silently truncates small-ingredient cost to zero |
| 3.51 | Define, document and test the rounding rule — direction and boundary; rounding to 2 dp happens **only at presentation** | Not started | Must not be inherited from Python's default by accident. Tested in 6.16; lives in 5.16's formatter |
| 3.52 | Unit reference table: canonical unit per dimension plus a conversion factor per purchase unit, so adding "sack" or "dozen" is data entry | Not started | Resolves the units half of 3.26. **Not tenant-editable** (10.17). Seed data feeds 3.37, 10.10 |
| 3.53 | Dated VAT-rate reference table (`code`, `percent`, `valid_from`, `valid_to`), referenced by code from products | Not started | Dated so a statutory rate change doesn't retroactively rewrite historical margins |
| 3.54 | Backfill existing `RawMaterial` prices into the purchase-price/pack-quantity/purchase-unit model — a per-row human-judgment exercise, **not** an automatic migration | Not started | Today's values mean whatever the person typing them assumed. Must complete before 3.32. Load with 3.68's `ON_ERROR ignore` |

### Deletion, identity and roles in the schema (ADR-019, ADR-020)

| ID | Task | Status | Notes |
|---|---|---|---|
| 3.55 | Combine tenant scoping and archived-state filtering into a **single** base manager applied by default | Not started | Two orthogonal correctness-critical filters: missing the archived filter resurrects deleted data; missing the tenant filter leaks across tenants. Extends 3.3; tested in 6.18 |
| 3.56 | Give archived records a way back: an un-archive path and a way to see archived rows | Not started | A soft delete with no un-delete is just a confusing delete. The UI must say *archive* where it archives |
| 3.57 | Assign a role to every existing user as part of the membership migration — a human decision per user, not a default | Not started | Nobody in the current database has a role |
| 3.58 | Tenant membership model (user × bakery × role) as the home of role assignment | Not started | Django's global `Group` cannot express "Owner of bakery A". Surrogate key + `UniqueConstraint(user, bakery)` — **not** `CompositePrimaryKey`, which cannot be an FK target (ADR-027). Implements 3.4 |

### Recipe composition and cost provenance (ADR-022)

| ID | Task | Status | Notes |
|---|---|---|---|
| 3.59 | Let an ingredient line reference **either** a raw material or a base recipe, and reject cycles at save time | Not started | **Cycle prevention is the critical part**: nothing in the current schema stops it, and a cycle makes costing loop forever. Depth guard is 4.16; test is 6.20 |
| 3.60 | Make `recipe_yeld` a real numeric quantity with a unit from 3.52 | Not started | Cost *per unit of yield* is what a parent consumes, so a loose yield field can no longer work. Extends 3.14 |
| 3.61 | Derive a raw material's current cost from its latest goods receipt — most recent by **receipt date**, ties by creation time — keeping a manual price as a labelled estimate | Not started | Receipt-date ordering (not entry date) is what makes a late-entered back-dated delivery behave correctly. Needs 17.1 |
| 3.62 | Model cost **provenance** (receipt-derived vs. estimated) as data the service layer returns alongside the figure | Not started | Retrofitting provenance into a bare `Decimal` later is painful. Surfaced by 4.17 and in exports |
| 3.63 | Stop treating `RawMaterial`'s supplier FK as the definition of who supplies a material — it becomes at most an optional *preferred supplier* | Not started | ADR-024, required by supplier price comparison being a **Must**: with a single FK, a comparison view has one row and shows nothing. Pairs with 17.1; view is 5.21 |

### Platform capabilities unlocked by the upgrade (ADR-027)

All need Epic 19 landed. Each replaces something this epic would otherwise hand-build.

| ID | Task | Status | Notes |
|---|---|---|---|
| 3.64 | Supplier-name uniqueness **case-insensitive**: `UniqueConstraint(Lower("name"), "bakery", condition=<not archived>)` | Not started | Django 4.0 functional unique constraints. **Extends 3.6, doesn't replace it.** Prevents "Odlums"/"odlums" silently splitting one supplier's price history |
| 3.65 | Validate `Meta.constraints` via `full_clean()` / `validate_constraints()`, with `violation_error_message` on each | Not started | Django 4.1. Without it, 3.6/3.64 uniqueness and 3.59's cycle rejection reach the user as an `IntegrityError` 500 instead of a field error |
| 3.66 | `db_comment` on columns whose meaning isn't visible from the name, `db_table_comment` on tables | Not started | Django 4.2. Aimed at the non-obvious: money stored **net of VAT**, quantities in canonical kg/l/each, `purchase_price` vs. derived cost, `archived_at` semantics. Cannot drift from the table it describes |
| 3.67 | `db_default` for the non-null columns this epic adds to populated tables | Not started | Django 5.0. Removes a separate data-migration step per column |
| 3.68 | Load 3.54's backfill with `COPY ... ON_ERROR ignore` + `LOG_VERBOSITY` so a bad row is reported, not fatal | Not started | PostgreSQL 17. An all-or-nothing import is the wrong tool for a per-row judgment exercise |
| 3.69 | Use `pg_restore --transaction-size` and parallel large-object restore in the drill | Not started | PostgreSQL 17. 3.48 only has value if it stays fast enough to keep running |
| 3.70 | Nightly backup job as a scheduled GitHub Actions workflow: `pg_dump -Fc --no-owner --no-privileges` → `age` encrypt → upload to R2 | Not started | ADR-031. Uses 3.46's scripts. **Runs outside Railway on purpose.** Needs backup-scoped DB credentials (3.41) over Railway's public TCP proxy, and write-only R2 credentials. Must fail loudly — a silently skipped nightly job is indistinguishable from a working one until it matters |
| 3.71 | Provision the backup R2 bucket — **separate from the media bucket** — with a 7 daily / 4 weekly / 12 monthly lifecycle rule | Not started | Separate so media credentials can never read or delete backups. Fits R2's 10 GB free tier. The 12 monthlies are the outer bound on how long deleted personal data survives in restorable form — feeds [project_requirements.md](docs/project_requirements.md) "Retention & deletion" and 11.4 |
| 3.72 | Generate the `age` key pair, publish the **public** key to CI, store the private key outside CI with a documented recovery path | Not started | CI only ever needs the public key, so a compromised runner cannot read any backup. **The private key has no software fallback** — lose it and every dump is unrecoverable, which is why 3.48 must decrypt. Custody goes in the 8.5 and 8.6 runbooks |
| 3.73 | Migrate `Bs_Ingredients` + `Recipe_Ingredients` into `RecipeLine`, add both XOR `CHECK` constraints, drop the old tables only after row counts reconcile | Not started | ADR-032. A merge, not a rename. Constraints ship in the same migration as the model (3.19) |
| 3.74 | Build the tenant-scoped `Category` table (`kind` discriminator, `archived`, unique on `(bakery, kind, name)`), backfill distinct `categorie` values per tenant, drop the column | Not started | ADR-032. Mirrors 3.52. **`kind` must be validated against the referencing model** — the FK cannot stop a product being filed under a flour category, so the form and service layer must |

---

## Epic 4 — Backend modernization

**Branch:** `phase-4-backend-modernization` · **Depends on:** Epic 3

### Application architecture

| ID | Task | Status | Notes |
|---|---|---|---|
| 4.1 | Move costing/margin into `control/services/`, one implementation — deleting both the model `@property` methods and the inline `float()` loops in `control/views.py` | Not started | ADR-028. Properties are **deleted, not delegated**; the `float()` math is deleted rather than ported. Build 4.19 first |
| 4.2 | Make views thin: query, validate, delegate, render | Not started | |
| 4.3 | Use class-based or function-based views consistently | Not started | |
| 4.4 | Replace broad/ineffective exception patterns with correct query handling | Not started | |
| 4.5 | Delete the dead custom auth code — `accounts/views.py` and `accounts/urls.py` — leaving Django's auth views as the only auth surface | Not started | ADR-028. `bakery/urls.py` **never includes `accounts.urls`**, so `user_login` is unreachable and renders a template path that doesn't exist. A pure deletion. **Keep `accounts/templates/registration/`** |
| 4.6 | Make every service-layer query tenant-scoped by construction | Not started | ADR-008. Tested in 6.9 |
| 4.19 | Build the `control/services/` skeleton: `cost_products(queryset, …)` as the **primary batch entrypoint** loading the whole ingredient graph in a bounded number of queries, single-object costing as a thin wrapper, and a frozen `CostBreakdown` dataclass carrying amount, canonical unit, provenance and as-of date | Not started | ADR-028. Batch-first is not a preference — 5.18 costs every product per request against the p95 < 2 s budget, and it is **why no cache is needed**. Carries ADR-022's recursion, cycle guard and depth limit. Prerequisite for 4.1 |
| 4.20 | Give the batch signature a per-tenant version-stamp parameter, bumped by writes to costing inputs, so a cache can later attach at that seam | Not started | ADR-028. Inputs that must bump it: goods receipts, recipe edits, cascading base-recipe edits, VAT rows, `ProductPrice` rows |

### Forms and validation

| ID | Task | Status | Notes |
|---|---|---|---|
| 4.7 | Replace `fields = "__all__"` with explicit ModelForms on all create/update flows | Not started | |
| 4.8 | Business validation on those forms: quantities, units, VAT, price ranges, uniqueness | Not started | Backed by 3.65, so a rule surfaces as a field error rather than a 500 |
| 4.9 | Validate uploaded file type and size for product photos | Not started | Pairs with 13.7 |
| 4.10 | Form widgets and help text for clearer operator workflows | Not started | |

### Query and performance

| ID | Task | Status | Notes |
|---|---|---|---|
| 4.11 | `select_related`/`prefetch_related` on supplier/product/ingredient listings | Not started | |
| 4.12 | Remove repeated cost calculations from nested loops in views | Not started | Follows from 4.1 |
| 4.13 | Service-layer aggregate calculations for the dashboard and product costing | Not started | |
| 4.14 | ~~Cache expensive dashboard summaries~~ | **Cancelled** | ADR-028 — **no cache in the first release**. Escalation ladder gated on 7.20; version-stamp seam built into 4.20 |

### Costing and API readiness

| ID | Task | Status | Notes |
|---|---|---|---|
| 4.15 | ~~Build the agreed API surface (DRF or a small read-only reporting/export API)~~ | **Cancelled** (2026-08-13) | **No API layer** — ADR-028. Health/callback endpoints are plain `JsonResponse` views. Cancelled rather than deferred; the ADR carries the revisit trigger |
| 4.16 | Recursive costing through base-recipe ingredient lines, with an explicit depth guard | Not started | ADR-022. Schema-level cycle rejection is 3.59; the depth guard is defence in depth for data that predates it. Tested in 6.20 |
| 4.17 | Return cost **provenance** with every costing result | Not started | ADR-022, backed by 3.62. Consumed by 5.18/5.20 and the exports |
| 4.18 | Implement the "stale price" rule as a service-layer concern rather than a template condition | Blocked | ADR-023. Blocked on [roadmap.md](docs/roadmap.md) 10.16 — the staleness threshold |

---

## Epic 5 — Frontend modernization

**Branch:** `phase-5-frontend-modernization` · **Depends on:** Epic 19 (5.22, 5.23) and Epic 3
(5.18, 5.20, 5.21)

| ID | Task | Status | Notes |
|---|---|---|---|
| 5.1 | Introduce a shared `base.html` layout | Not started | ADR-030. **31 of 32 templates carry their own full `<!DOCTYPE>` boilerplate** and there is not one `{% extends %}` in the repo — the highest-leverage task in the epic |
| 5.2 | Replace duplicated navbar/footer/page scaffolding with blocks and partials in `<app>/templates/partials/` | Not started | The navbar is duplicated across **all 32** templates. Plain `{% include %}` — `django-template-partials` not adopted unless HTMX fragments outgrow a handful |
| 5.3 | Replace hardcoded static paths with `{% load static %}` / `{% static %}` | Not started | **Bigger than it looks; sequence after 1.3.** Every template hardcodes `/static/...`, so manifest hashing has never done anything here. Switching activates it, and `ManifestStaticFilesStorage` **raises `ValueError` at render time** for any file missing from the manifest — a missing asset becomes a 500. With no build step, 5.3 + 19.14 + 1.13 are the whole story on asset versioning; done partially, the site silently serves stale CSS |
| 5.4 | Update the vendored Bootstrap from 5.0.0 to current 5.3.x | **Unblocked** | ADR-030. Same major, so an upgrade rather than a restyle — but verify the components in use (navbar, tables, forms, buttons) render unchanged. The vendored set also includes an RTL build and `.map` files nothing references; leave or drop as judgment, not scope |
| 5.5 | Delete the seven empty JavaScript files and the `<script>` tags referencing them | Not started | Verified 2026-08-16: **all seven are 0 bytes** — a deletion, not a rewrite |
| 5.6 | **Rescoped — no build step.** Consolidate the 16 CSS files (922 lines, four byte-identical) into a small set on CSS custom properties, relying on whitenoise for hashing and compression | **Unblocked** | ADR-030 **rejects the Vite candidate**. Native nesting/custom properties are safe on the evergreen matrix. Revisit trigger in the ADR |
| 5.7 | Add HTMX as the progressive-enhancement layer; settle the fragment convention (on `HX-Request`, render the partial directly) | **Unblocked** | ADR-030. **Every form and link must still work with JS disabled** — WCAG 2.2 A requires it regardless. Settle the convention *before* 5.9 is built |
| 5.8 | Add `djlint` for template linting/formatting | **Unblocked** | ADR-030/ADR-034. A pip package in `requirements/dev.in`, no Node in dev. `stylelint`/`prettier` stay **deferred**. CI wiring is 6.11 |
| 5.9 | Build real search/filter flows across raw materials, suppliers and products | **Unblocked** | ADR-024 rates this a **Must** — *build it*, not remove the inputs. Dead inputs that look functional are worse than none. Use 5.23 for filter-preserving pagination |
| 5.10 | Improve forms, validation errors, empty states and destructive-action confirmations | Not started | **Reduced** by 5.22 |
| 5.11 | Image upload/preview UI with an empty-state placeholder | Not started | Owned by 13.8 |
| 5.12 | Meet **WCAG 2.2 Level A**: alt text, real `<label>` on every input, no keyboard traps, nothing conveyed by colour alone | **Unblocked** | ADR-021. Keeps the remaining distance to AA small if 10.15 fires. **Reduced** by 5.22 |
| 5.13 | Make data tables usable on mobile and tablet — a deliberate strategy (scroll containers or card layouts), not overflow | Not started | Costing tables are inherently wide; goods receipts get recorded on a phone at the delivery door |
| 5.14 | Record the performance budget (p95 < 500 ms pages, < 2 s dashboard, ~10 concurrent users/tenant) and verify once monitoring exists | Not started | Deliberately **not** a CI gate — Railway Hobby shares CPU. Verify via 7.20/3.43. Carve-outs in 10.18 |
| 5.15 | Route all display text through `gettext` / `{% translate %}` during the rewrite | Not started | Ships English only, but makes expansion a locale file rather than a template audit |
| 5.16 | Remove every hardcoded `€`; format all money through a single currency formatter | Not started | Pairs with 3.51's rounding rule — both belong in the same formatter |
| 5.17 | Verify against the browser matrix: current and previous major Chrome, Firefox, Safari, Edge | Not started | No IE11, no legacy Edge |
| 5.18 | Rebuild the dashboard as an overview page: summary strip (product count, average margin, materials with no/stale pricing), worst-margin products, recent input price movements — moving the full product list to its own page | Not started | ADR-023. **Depends on Epic 3** — price movements and staleness need dated prices and receipts. Runs against the p95 < 2 s budget |
| 5.19 | Build the tenant self-administration settings area: user invite/remove and role assignment, bakery details, reference data, exports — Owner-writable, Read-only limited to exports | Not started | ADR-023. **Replaces** the broken user-delete view rather than patching it. Needs roles (2.8/3.58) and email (7.21) |
| 5.20 | Show cost provenance in the UI: mark estimated figures distinctly from receipt-derived ones | Not started | ADR-022, backed by 4.17 |
| 5.21 | Supplier price comparison view for a given raw material — who supplied it, at what price per canonical unit, and when | Not started | ADR-024 rates it a **Must**. Reads receipts (Epic 17) and needs 3.63; sparse until receipts accumulate across more than one supplier, which is expected rather than a defect |
| 5.22 | Render forms through `as_field_group()` over the div-based renderer as the default path, rather than hand-writing label/error/help markup | Not started | ADR-027, Django 5.0/4.1 — **needs Epic 19**. Supplies label association, `aria-describedby`, `aria-invalid`, `<fieldset>`/`<legend>` — a material share of 5.12 from the framework |
| 5.23 | Use `{% querystring %}` for pagination and filter links so the current search survives paging | Not started | ADR-027, Django 5.1 — **needs Epic 19**. The fiddly half of 5.9 |
| 5.24 | Wire up and template Django's password-reset flow (four `registration/password_reset_*` templates plus two email bodies) | Not started | ADR-028 — a direct consequence of adopting Django's auth views: password reset is email-only, so this is the account-recovery path for every user. Needs 7.21; use 5.22's rendering and 5.15's `gettext` |
| 5.25 | Record every vendored frontend asset — Bootstrap and HTMX — with exact version, source URL and purpose, checked on the dependency-recompile cadence | Not started | ADR-030 extends ADR-029's owner/purpose rule to assets `requirements/*.in` cannot see. Without it the repo reproduces what this decision found: **Bootstrap 5.0.0 from May 2021, unnoticed** |

---

## Epic 6 — Testing & quality gates

**Branch:** `phase-6-testing-ci` · **Depends on:** Epics 1–5

### Test coverage

| ID | Task | Status | Notes |
|---|---|---|---|
| 6.1 | Unit tests for model validation and constraints | Not started | 3.65 makes these reachable from form tests, not only DB-level integration tests |
| 6.2 | Unit tests for costing logic | Not started | Against the 4.1/4.19 service layer |
| 6.3 | Unit tests for margin logic | Not started | |
| 6.4 | Unit tests for permissions and role enforcement | Not started | Covers 2.6–2.8 |
| 6.5 | Unit tests for the export views | Not started | Covers Epics 14/15 too |
| 6.6 | Integration tests for critical CRUD workflows | Not started | |
| 6.7 | Regression tests for known-broken areas (e.g. the user-delete view that deletes `RawMaterial`) | Not started | The fix itself is 5.19's rebuilt surface, not a patch |
| 6.8 | Smoke tests for login, dashboard, raw materials, suppliers, recipes, products, settings | Not started | Start from 19.8's recorded manual pass rather than from nothing |
| 6.9 | Dedicated cross-tenant isolation tests — prove tenant A can never read or write tenant B's rows | Not started | ADR-008; covers 3.3, 4.6 and 2.21's permission-cache invalidation |
| 6.16 | Test unit conversion, decimal precision and the rounding rule end to end: a gram-scale ingredient must not cost zero, and a known basket must produce an exactly-specified cost and margin | Not started | Covers 3.11, 3.50, 3.51. Assert on exact `Decimal` values, never floats |
| 6.17 | Test that VAT is applied only at presentation, and that changing a rate's `valid_from` does not alter historical figures | Not started | Covers 3.15, 3.53 |
| 6.18 | Test the tenant + archived filter pair together, including archived rows of another tenant | Not started | Covers 3.55. Two independent failure modes; test both and their combination |
| 6.19 | Test the three-role capability matrix: Read-only cannot write, Staff cannot manage users or pricing, Owner cannot reach another tenant | Not started | Covers 2.8, 2.16. Extends 6.4 |
| 6.20 | Test recursive costing: costing through a base recipe returns the right figure, and a self-referencing or transitively cyclic recipe is **rejected** rather than looping | Not started | Covers 3.59, 4.16. The cycle case hangs a request if missed |
| 6.21 | Test cost provenance: receipt-derived and estimated figures are distinguishable, and a back-dated receipt updates current cost correctly by receipt date | Not started | Covers 3.61, 3.62, 4.17 |
| 6.22 | Add coverage measurement to CI, then enable `--fail-under=70` as a required check | Not started | ADR-031. **Enable the gate last** — switching it on first blocks the PRs that write the tests. Measure and report from the start so the number is visible while it climbs. Repo-wide, one number |

### Tooling

| ID | Task | Status | Notes |
|---|---|---|---|
| 6.10 | Add and configure the agreed formatter/linter across the codebase | **Unblocked** | **`ruff check` + `ruff format`** — ADR-034. No `black`, no `isort`. Config in `[tool.ruff]` of the tool-only `pyproject.toml` |
| 6.11 | Wire template linting into the CI gate | **Unblocked** | **`djlint`** (ADR-030/ADR-034). The tooling work itself is 5.8 |
| 6.23 | Adopt `pytest` + `pytest-django` + `pytest-cov`, with `[tool.pytest.ini_options]` in the tool-only `pyproject.toml` | Not started | ADR-034. `--cov-fail-under=70` is where the floor is enforced, keeping 6.22 a one-line change. `pytest-django` wraps Django's test-database machinery rather than replacing it |
| 6.24 | Update the documented test command from `manage.py test` to `pytest` in `CLAUDE.md`, the README (8.1) and CI | Not started | ADR-034. Three places, and the stale one is always the one someone follows |

### CI/CD

| ID | Task | Status | Notes |
|---|---|---|---|
| 6.12 | Extend the Epic 1 workflow (don't replace it) with: install from the hashed lock, the real test suite, `ruff` + `djlint`, `pip-audit` | Not started | ADR-011, shape fixed by ADR-031. **No CodeQL/Trivy** this release. Coverage is 6.22, deliberately separate |
| 6.13 | Enable required status checks on `main` and `production`, blocking merge when checks fail | Not started | ADR-010. **This is also the deploy gate** — see 6.14 |
| 6.14 | Block deployments when checks fail | Not started | **Satisfied by 6.13, not a second mechanism** — ADR-031. `production` only advances by merge and Railway deploys only what lands there. The work is *verifying* that chain end to end (attempt a failing merge, confirm no deploy fires) |
| 6.15 | Run the unit suite on every PR into `main` as the feature-branch gate | Not started | ADR-014 — the automated half of the test split; integration verification of merged `main` stays manual against `docker-compose`. Part of 6.12 |

---

## Epic 7 — Observability & operations

**Branch:** `phase-7-observability` · **Depends on:** Epic 12 (a provisioned host)

### Logging and monitoring

| ID | Task | Status | Notes |
|---|---|---|---|
| 7.1 | Structured application logging | Not started | |
| 7.2 | Error tracking: create the Sentry organisation **in the EU region**, add `sentry-sdk[django]` to `base.in` with its owner comment, wire the DSN from the environment | Not started | ADR-031. **The region is chosen at org creation and cannot be changed** — the fix is a new organisation. Tag environment and release so pilot noise stays separable. PII handling is 7.23 and is **not optional** |
| 7.3 | Log security-relevant events, admin actions and failed operations without leaking secrets | Not started | Pairs with 2.9, 2.23 |
| 7.4 | Health checks for application and database connectivity | Not started | Must return something 7.5's keyword check can assert on |
| 7.5 | Uptime monitoring: a 5-minute UptimeRobot **keyword** check against 7.4's endpoint, email alerting | Not started | ADR-031. Keyword on the body, **not** HTTP 200 alone — otherwise a health endpoint correctly reporting a dead database still passes. Hosted away from Railway on purpose |

### Deployment and infrastructure

| ID | Task | Status | Notes |
|---|---|---|---|
| 7.6 | Harden the `Dockerfile` as the single deploy artifact (multi-stage, slim final image, pinned base) | Not started | ADR-004 |
| 7.7 | Fix `docker-compose.yaml` so it defines all required services correctly, app and DB separate | Not started | ADR-007; drop the external `bakery_simple` network assumption. Overlaps 19.10 |
| 7.8 | Separate the local compose definition from the production deployment definition | Not started | |
| 7.9 | Remove legacy Heroku assumptions (`settings/heroku.py`, `runtime.txt`, `Procfile`) | Not started | Pairs with 1.5 + Epic 12 |
| 7.10 | Add a static asset build step to the release process | Not started | `collectstatic` currently runs at image build time. After 1.5, ensure it does **not** require `DATABASE_URL`/`SECRET_KEY` at build — a settings module that raises on missing env vars would break the image build |
| 7.11 | Add a migration release step and **remove `migrate` from the container start command** in both the `Dockerfile` `CMD` and `docker-compose.yaml` | Not started | ADR-015 rule 4. Migrating on boot makes every replica race and ties the schema change to container start. **Pairs with 12.11** — do both in one pass or migrations run twice |
| 7.12 | Write and test the rollback procedure, using 1.10's release tags | Not started | |
| 7.13 | Document every environment variable per environment as a committed `.env.example` (names and example values only — never real secrets) | Not started | ADR-015 rule 8 — this file is the migration checklist; if it lives only in a host's dashboard, moving host becomes archaeology |
| 7.14 | Run the app under Gunicorn in production | **Unblocked** | **gunicorn, WSGI, sync workers**, latest pinned at lock time — ADR-036. Binds `$PORT` per 7.17. Revisit only if the insights dashboard needs SSE/WebSocket push |
| 7.15 | Automate deploys: Railway git-watch on `production` only | Not started | ADR-010, narrowed by ADR-014, settled by ADR-031. Platform-native git-watch, **not** a GitHub Actions deploy job — that would need a long-lived Railway token in CI and a release script to maintain. Migrations are 12.11 |
| 7.16 | Keep serving static assets via whitenoise; confirm it still fits once object storage is in play | Not started | Decided "no change" — a verification task |
| 7.17 | Bind Gunicorn to `$PORT` with a local fallback (`--bind 0.0.0.0:${PORT:-8000}`) instead of the hardcoded `:8000` | Not started | ADR-015 rule 3. Railway, Render, Fly, DigitalOcean, Clever Cloud and Heroku all inject the port they expect |
| 7.18 | Confirm no persistent state is written to the app container's local disk | Not started | ADR-015 rule 7. Pairs with 2.13 and Epic 13 |
| 7.19 | Enable Django's native psycopg pool (`DATABASES["OPTIONS"]["pool"]`) and `CONN_HEALTH_CHECKS`; tune `min_size`/`max_size` against Railway's connection limit | Not started | ADR-027, Django 5.1 — **needs Epic 19**. In-process, so no PgBouncer to run, monitor or patch. Health checks matter on a platform that recycles connections. Supersedes 3.42 |
| 7.20 | Enable `pg_stat_statements` and check the ADR-021 budgets against it (p95 < 500 ms pages, < 2 s dashboard) | Not started | ADR-027, PostgreSQL 17. Nothing currently measures those budgets. Feeds 3.43, 5.14. **The named trigger** for ADR-028's caching ladder: fix the queries, then a version-keyed per-view cache (4.20), then Redis only for cross-worker coherence |
| 7.21 | Configure email from environment variables: `smtp.EmailBackend` against Brevo in `base.py`, console in `local.py`, locmem in `test.py`, `DEFAULT_FROM_EMAIL` set | Not started | ADR-028. No dependency — the provider stays swappable by configuration alone. Variables go in 7.13's `.env.example`; credentials follow 2.1. **Blocks 5.19 and 5.24** |
| 7.22 | Create the Brevo account, verify the sending domain, publish SPF, DKIM and DMARC records | Not started | ADR-028. The half that is not code, and the usual cause of "the invitation never arrived" — unauthenticated mail from a new domain lands in spam regardless of the application being correct. Do before 5.19 ships to a real pilot user |
| 7.23 | Configure Sentry PII handling: `send_default_pii=False` plus a `before_send` scrubber stripping request bodies, headers, cookies and local variables | Not started | ADR-031. **The GDPR-load-bearing half of 7.2.** Test it — trigger a deliberate exception on a view handling personal data and inspect what actually arrived |

---

## Epic 8 — Documentation & team readiness

**Branch:** `phase-8-docs` · **Depends on:** Epics 1–7

| ID | Task | Status | Notes |
|---|---|---|---|
| 8.1 | Rewrite `README.md` for production-oriented setup and development workflows | Not started | Includes the `pytest` command change (6.24) |
| 8.2 | Document the architecture: app modules, data model, deployment overview, permissions model | Not started | |
| 8.3 | Deploy runbook | Not started | |
| 8.4 | Rollback runbook | Not started | Follows 7.12 |
| 8.5 | Backup/restore runbook | Not started | Follows 3.38. Must record the **accepted 24 h RPO** (3.40), the `age` key custody and recovery path (3.72), and what happens if a restore reintroduces personal data erased after the dump ([project_requirements.md](docs/project_requirements.md) "Retention & deletion") |
| 8.6 | Secret-rotation runbook | Not started | Build it around `SECRET_KEY_FALLBACKS` (2.18) — without that, rotating logs out every active session, which is why rotation runbooks go unused |
| 8.7 | Incident-response runbook | Not started | Must align with the GDPR breach process (11.8) |
| 8.8 | Document the branch/promotion/release process for contributors | Not started | ADR-010 |
| 8.9 | Host-migration runbook: provision elsewhere, restore the logical dump, move env vars, verify (3.47), cut DNS over, decommission | Not started | ADR-015 — the executable form of 11.14's revisit option; derive it from the Railway setup while fresh. Must cover: a maintenance window timed against Irish bakery business hours, lowering DNS TTL beforehand, keeping the old database **read-only but alive** until verification passes (12.6), and the rollback trigger. Object storage does **not** move |

---

## Epic 11 — GDPR data inventory & policy

**Branch:** `gdpr-data-inventory` · **Depends on:** — · **Blocks:** Epics 13, 15, 16, and any
consent/erasure/audit-log code

The executional half of data protection: build the inventory, execute the agreements, wire the
logging. **The judgments — legal basis, retention policy, erasure strategy, the DPIA, transfer
safeguards — are open decisions in [roadmap.md](docs/roadmap.md) (`11.2`, `11.3`, `11.4`, `11.7`,
`11.9`, `11.14`, `11.15`) and must not be answered here.** Not legal advice; a real legal/DPO review
is a prerequisite to relying on any of it.

| ID | Task | Status | Notes |
|---|---|---|---|
| 11.1 | Complete the personal-data inventory | Not started | [project_requirements.md](docs/project_requirements.md) "Personal data inventory". **Blocks 15.1** — you cannot scope a subject export without knowing which fields are personal data. Feeds roadmap 11.2 |
| 11.5 | DPA template usable per tenant, Bakery-the-product as processor | Not started | ADR-006. Applies to the free pilot too |
| 11.6 | Execute DPAs with each third-party processor: Railway, Cloudflare R2, Brevo, Sentry (Databricks/AWS are 11.17) | Blocked | Railway resolved as host (12.1 ✅) — execute via 12.7. Sentry by design receives whatever a traceback contains, which is why 7.23's scrubbing is part of the DPA story |
| 11.8 | Define the breach notification process (72-hour supervisory-authority deadline) | Not started | The authority (Irish DPC) and the processor→controller path are settled inputs. Feeds runbook 8.7 |
| 11.10 | Access logging for who viewed or exported personal data | Not started | Extends 2.9. Covers both the Read-only export path and the Django admin's cross-tenant access (2.15) |
| 11.11 | Confirm no tracking/analytics cookies exist; define the consent path if that changes | Not started | |
| 11.12 | Name the point of contact for data subject requests | Not started | Narrowed: one tenant, so controller-side is the pilot bakery and processor-side is the project owner. Still needs naming for real |
| 11.13 | Confirm backups are encrypted at rest — **client-side `age` before upload** | Not started | ADR-031. A verification task: confirms 3.70/3.72 do what the ADR says. R2's server-side encryption is a second layer, not the answer relied on |
| 11.16 | Add Brevo to the processor table — EU hosting, ISO 27001:2022, DPA reference, and what personal data reaches it | Not started | ADR-028. Narrow but real: recipient email, display name, reset/invite token. **No transfer safeguard needed** — EU-owned and EU-hosted |
| 11.17 | Add Databricks Inc. and AWS (EU Ireland) to the subprocessor list, with DPAs, and confirm the extract carries no personal data | Not started | ADR-036. Both in the EEA, so the **data** needs no Chapter V mechanism; Databricks being US-headquartered is a subprocessor/DPA question. Pairs with 16.3, 16.4, 16.9 |

---

## Epic 12 — Hosting migration

**Branch:** `stack-hosting-migration` · **Depends on:** — · **Blocks:** Epic 7

Move the Django app and PostgreSQL off the self-hosted home server onto **Railway (Hobby, EU West)**
(ADR-013). Only production is hosted — dev/test is local Docker Compose (ADR-014).

| ID | Task | Status | Notes |
|---|---|---|---|
| 12.1 | Pick the host among the three candidates, re-confirming pricing and the cost of a second environment; log it as an ADR | **Done** | Railway (Hobby), 2026-08-03 — ADR-013. Staging cost is what drove ADR-014 |
| 12.2 | Provision app compute and managed PostgreSQL as separate services | Not started | ADR-007. Pin Postgres to **17** here (19.11) |
| 12.3 | Configure the deployment to build from the repo's `Dockerfile`, not Railpack | Not started | ADR-004; pairs with 7.6 |
| 12.4 | Single Railway environment tracking `production`; do **not** provision persistent hosted staging | Not started | ADR-014 amends ADR-010 — the `main` tier runs locally |
| 12.5 | Enable a Railway PR environment on the `main` → `production` release PR only | Not started | ADR-014. No plan-tier gate; <$1/mo at a few releases a month |
| 12.6 | Migrate production data off the home server, with a verified restore on the new host | Not started | A **cross-major** restore (home-server version → 17) — exactly what 3.46/3.47's traps are about. Do not decommission the old host until verified |
| 12.7 | Execute the DPA with Railway and add it as a subprocessor | Not started | Feeds 11.6/11.15. Railway is a US company — the EU region covers storage location, not processor access |
| 12.8 | Set the region to **EU West (Amsterdam)** *before* creating any service | Not started | ADR-013. **Railway's default is US West** — the personal data lives in the database, so a default-region Postgres puts it in California. Volumes follow their service's region, and EU-West Metal supports volumes on Hobby (since 2025-03-14), so this is purely sequencing. Moving a volume later forces a migration **with downtime**. Confirm on both services after provisioning |
| 12.9 | Configure Railway's automated backup schedules — for fast same-host rollback, **not** the portable backup | Not started | ADR-013/ADR-031 — **off by default**. Enable all three (daily/weekly/monthly); no PITR. Copy-on-write volume snapshots are **not restorable on another host** — 3.44/3.70 covers that |
| 12.10 | Provide migrations + seed data for the release-PR environment, which comes up empty | Not started | ADR-014 — PR environments clone services and config but not volume data, so without this the preview is an unusable login page. Pairs with 3.37/10.10 |
| 12.11 | Set `manage.py migrate` as Railway's **pre-deploy command**, so it completes before the new version takes traffic | Not started | ADR-031. What makes platform-native git-watch sufficient and satisfies ADR-015 rule 4 without a release script. **Pairs with 7.11** — `migrate &&` must come out of the `Dockerfile` `CMD` and the compose command in the same pass, or migrations run twice and every replica races |

---

## Epic 13 — Media storage for user uploads

**Branch:** `feature-media-storage` · **Depends on:** Epics 3, 19 · **Priority:** Could (ADR-024)

**Product photos only this round**, in Cloudflare R2 via `django-storages`, decoupled from app
hosting (ADR-005). Profile pictures are deferred (13.10).

| ID | Task | Status | Notes |
|---|---|---|---|
| 13.1 | Add `django-storages[s3]`, `boto3` **and `Pillow`** to `requirements/base.in` with owner comments, then recompile | Not started | ADR-005. `Pillow` re-enters here: ADR-029 removed it in 19.2 because nothing imported it, and 13.4 makes it load-bearing — `ImageField` will not validate without it |
| 13.2 | Provision the R2 media bucket, optionally fronted by a custom domain/CDN | Not started | **Separate from 3.71's backup bucket** |
| 13.3 | Configure `django-storages` against the R2 endpoint, credentials from environment variables | Not started | Pairs with 2.5 |
| 13.4 | Add a `photo` field to `Product` | Not started | Schema change — sequence with 3.18 |
| 13.5 | Add a `Profile` model with a one-to-one to `User` and a photo field, avoiding a custom-user-model migration | **Deferred with 13.10** | Needs the tenant FK from 3.2 when it returns |
| 13.6 | Store only the object key/URL in PostgreSQL — the binary never goes in the database | Not started | |
| 13.7 | Validate uploaded file type and size in a real ModelForm | Not started | Pairs with 4.9 |
| 13.8 | Upload/preview UI with an empty-state placeholder | Not started | Pairs with 5.11 |
| 13.9 | Delete the stored object from the bucket on account deletion or an erasure request | Not started | [project_requirements.md](docs/project_requirements.md) "Data subject rights" — a DB-row delete alone is not compliance. The profile-picture half defers with 13.10 |
| 13.10 | Do not ship profile pictures until their legal basis is decided | **Deferred out of this round** | ADR-024 rates them **Won't (this round)** — deferred, not rejected. Takes 11.3 off the critical path. 13.5 and part of 13.9 go with it |
| 13.11 | Configure R2 under the `STORAGES` dict's `"default"` key, whitenoise on `"staticfiles"` | Not started | ADR-027, Django 4.2 — **needs Epic 19** and builds on 19.14. `DEFAULT_FILE_STORAGE` no longer exists on the target version, so any older `django-storages` recipe found online will be wrong |

---

## Epic 14 — Tenant full data export

**Branch:** `feature-tenant-data-export` · **Depends on:** Epic 3 · **Priority:** Should

All of one tenant's rows across every tenant-scoped table, in a portable DBMS-agnostic format, so a
departing bakery can take its data elsewhere (ADR-008). A product feature, **not** the GDPR
portability mechanism (Epic 15).

| ID | Task | Status | Notes |
|---|---|---|---|
| 14.1 | Implement the export format — a ZIP of one CSV per tenant-scoped table plus a `manifest.json` (timestamp, schema version, columns, types, PK, FK map) | **Unblocked** | ADR-035. Explicitly **not** `pg_dump`, not hand-generated ANSI SQL, not `dumpdata`. Money and quantities at **full stored precision**, never 2-dp presentation rounding — an export that rounds silently loses data |
| 14.2 | Build the service that walks every tenant-scoped table for a given tenant | Not started | Needs 3.1/3.2 |
| 14.3 | Include the relationship manifest and import instructions so the export is usable without this app | Not started | **The manifest is the deliverable** — CSV loses types, null-vs-empty and every relationship, so this is a correctness task, not documentation |
| 14.4 | Gate who can trigger an export; audit-log every run | Not started | Every export is a bulk disclosure of one tenant's business data. Pairs with 2.9/11.10 |
| 14.5 | Test that an export contains every one of that tenant's rows and none of any other tenant's | Not started | Pairs with 6.9 |
| 14.6 | Expose the export twice from one service function: an Owner-only settings download, and a management command | Not started | ADR-035/ADR-023, gated by an ADR-020 capability name rather than a role comparison. Synchronous is adequate today — **re-check here**, since a tenant with years of receipts is not today's catalogue |

---

## Epic 15 — GDPR personal-data export

**Branch:** `feature-gdpr-data-export` · **Depends on:** Epic 11 · **Priority:** Should

A second export scoped to **one data subject's** personal data — the Article 20 portability fix,
distinct from both the bulk admin CSV export and the tenant-wide export (ADR-009).

| ID | Task | Status | Notes |
|---|---|---|---|
| 15.1 | Define exactly which fields across which models constitute one data subject's personal data | Blocked | Needs the completed inventory — 11.1 |
| 15.2 | Build the subject-scoped export as its own view/service | Not started | May reuse ADR-035's bundle shape scoped to one subject — this task's call, not a stack decision |
| 15.3 | Gate it to the requesting user's own data, or an admin acting on a subject's behalf | Not started | |
| 15.4 | Audit-log every personal-data export | Not started | Pairs with 11.10 |
| 15.5 | Leave the per-entity bulk CSV exports unchanged as an admin/operational feature | Not started | ADR-009 — explicitly not the compliance mechanism |
| 15.6 | Update [project_requirements.md](docs/project_requirements.md) "Data subject rights" — mark Portability implemented when this ships | Not started | ADR-009 already records the direction; this closes the gap between decided and built |

---

## Epic 16 — AI insights & alerts service

**Branch:** `feature-ai-insights-service` · **Depends on:** Epic 11 · **Priority:** Could

An external batch service reading a nightly extract and returning margin alerts and analytics
(ADR-002, confirmed and scoped by ADR-036). **Databricks Serverless Jobs on AWS, EU (Ireland).**
Django pushes a personal-data-free costing extract to R2 and the Spark job reads only that — it never
reaches PostgreSQL. Results come back to a shared-secret callback. Hard ceiling **~$15/mo**, taking
total infrastructure from ~$6 to ~$21/mo against zero revenue.

| ID | Task | Status | Notes |
|---|---|---|---|
| 16.1 | Confirm the processing engine and workspace cost model before any spend | **Done** (2026-08-26) | **Spark on Databricks confirmed** — ADR-002 `Proposed` → `Accepted`, detailed by ADR-036. The *measured* cost is still owed (16.8) |
| 16.2 | Define the payload shape of the returned insights | **Rescoped** | ADR-036: **no event triggering**. The contract is a nightly R2 extract in (16.9, 16.13) and a POST out (16.10); what remains is the payload itself |
| 16.3 | Define and enforce the data scope shared with the service | **Settled in principle** | ADR-036: the extract carries **product, date, cost, price, margin, tenant — and no personal data**, and Databricks never reaches PostgreSQL. Enforced by what the extract job writes (16.9), not by a read-role grant that could widen later |
| 16.4 | Put a DPA in place with the analytics provider before any real data flows | Blocked | Feeds 11.6/11.17 — Databricks Inc. *and* AWS EU (Ireland) |
| 16.5 | Define the margin-alert rules and how alerts reach users | Not started | Email path is 7.21's configuration |
| 16.6 | Surface the analytics dashboard in the app | Not started | Polling, not push — push would reopen ADR-036’s WSGI decision |
| 16.7 | Ensure everything the service reads or writes is tenant-scoped | Not started | ADR-008 |
| 16.8 | Provision the Databricks workspace — **Serverless Jobs, AWS, EU (Ireland) `eu-west-1`** — and record the **measured** DBU + cloud cost of one real run before any production spend | Not started | ADR-036. The DBU rate is deliberately absent from the ADR: serverless pricing is region- and tier-dependent and changes |
| 16.9 | Build the nightly extract job: a management command writing a **personal-data-free** costing extract to a dedicated R2 prefix | Not started | ADR-036/ADR-005. This job **is** the data-scope enforcement for 16.3. Reuses 4.19's batch costing |
| 16.10 | Build the results callback: a plain `JsonResponse` endpoint authenticated by shared secret, tenant-scoped and rate-limited | Not started | ADR-036/ADR-028. **The app's only internet-facing unauthenticated write path** — and the one route besides the cover and login pages exempt from `LoginRequiredMiddleware` (2.17) |
| 16.11 | Alert on Databricks job failure | Not started | **The real operational risk:** insights that stop arriving look exactly like "no alerts this week". Part of this feature, not Epic 7's monitoring |
| 16.12 | Configure the spend alert at the ~$15/mo ceiling, and define what happens when it trips | Not started | ADR-036. The control that keeps the ~$6 → ~$21/mo rise a decision rather than a surprise |
| 16.13 | Version the extract schema as a published contract; make the notebook reject an unknown version | Not started | ADR-036. The Django job and the Spark notebook live in different repositories; an unversioned format fails silently into wrong insights |

---

## Epic 17 — Batch & lot traceability

**Branch:** `feature-traceability` · **Depends on:** Epic 3, plus 10.8 and 10.9 · **Priority:** Must

The record-keeping EU Reg. 178/2002 Art. 18 requires: **one step back** (which supplier lot went into
what) and **one step forward** (where a finished batch went) — ADR-017. It adds a temporal/event
layer to a schema that is otherwise a pure current-state catalogue, which is why it is its own epic.

**A partial implementation is worse than none if it looks complete.** The pilot bakery is a real food
business operator; nothing here should present itself as a compliance record until 17.7 and 17.10
make the trace path whole.

| ID | Task | Status | Notes |
|---|---|---|---|
| 17.1 | Model goods receipts as `GoodsReceipt` (supplier, receipt date, doc ref) + `GoodsReceiptLine` (material, supplier lot, quantity, unit, best-before, price paid), distinct from the `RawMaterial` catalogue row | **Unblocked** | ADR-033. Header + lines because a delivery note is one record with many lines. Price fields use ADR-018's shape — same definition as 3.10. **A lot is an event, not an attribute** |
| 17.2 | Model production runs: `ProductionRun` → `Consumption` (FK to a `GoodsReceiptLine`, quantity consumed in canonical units) → output `Batch`, with `OutboundRecord` off `Batch` | **Unblocked** | ADR-033. `Consumption.quantity_consumed` is load-bearing beyond traceability — the single field keeping on-hand derivable later without a schema change (17.14) |
| 17.3 | Assign an internal lot code to each produced batch, format decided rather than improvised | **Unblocked** | **`YYYYMMDD-NNN`**, resetting daily, unique on `(bakery, lot_code)` — ADR-033. Implementation is 17.13 |
| 17.4 | Model outbound records at the granularity the regulator expects | Blocked | Blocked on [roadmap.md](docs/roadmap.md) 10.8 — direct-to-consumer sales are treated differently from wholesale |
| 17.5 | Make traceability records append-only: no hard delete, no silent retroactive edit — corrections are new records with an audit trail | Not started | The strongest integrity requirement in the schema — stronger than ADR-019's soft delete. Pairs with 2.9, 11.10 |
| 17.6 | Prevent hard-deletion of any `Supplier` or `RawMaterial` referenced by a traceability record | Not started | Turns 3.13/3.22's soft delete from a judgment call into a requirement |
| 17.7 | Build the trace query: given any lot, return one step back and one step forward, through multi-level recipes | Not started | The actual deliverable — everything above is scaffolding. The same traversal as 4.16's costing recursion, in the opposite direction, over the one `RecipeLine` table |
| 17.8 | Tenant-scope every traceability model with a `Bakery` FK | Not started | ADR-008. Needs 3.1/3.2 |
| 17.9 | Enforce the food-law retention floor, overriding ordinary retention where the two conflict | Blocked | Floor undecided — 10.9. Pairs with 11.4 |
| 17.10 | Produce an authority-ready trace report/export for a given lot, usable in an FSAI request | Not started | Distinct from Epic 14's and Epic 15's exports |
| 17.11 | Test the trace end to end: across a multi-level recipe, and proving no record from another tenant is reachable | Not started | Pairs with 6.9 |
| 17.12 | Record the price paid per goods receipt; confirm it becomes the source of truth for input price history | Not started | ADR-017/ADR-033 — a receipt line dates its own price. Feeds 3.61 |
| 17.13 | Implement the lot-code generator: `YYYYMMDD-NNN`, per tenant, allocated inside the batch-creating transaction, with `unique_together (bakery, lot_code)` as the backstop | Not started | ADR-033. Two runs finishing in the same second must not collide. **Never** allocate by counting existing rows; gaps after a rollback are acceptable, duplicates are not |
| 17.14 | Record `quantity_consumed` on every `Consumption` row in canonical units so quantity-on-hand stays derivable — and deliberately surface **no** stock figure this round | Not started | ADR-033/ADR-024. The whole content of "design so it *could* be derived later". The pilot will ask for stock: the data is being recorded, the feature is not being claimed until it can be trusted |

---

## Epic 18 — Allergen data

**Branch:** `feature-allergen-data` · **Depends on:** Epic 3, Epic 17, and 10.12 · **Priority:**
Should (ADR-024)

Allergen information on raw materials, aggregated through base recipes to products under EU FIC
1169/2011. Deliberately **outside** Epic 17 so the Art. 18 core isn't delayed — but it reuses
ADR-022's recipe recursion directly: aggregating allergens up the tree is the same traversal as cost.

| ID | Task | Status | Notes |
|---|---|---|---|
| 18.1 | Confirm allergen scope against FSAI/FIC guidance: the 14 declarable allergens, and what a costing tool records vs. what belongs on a label | Blocked | 10.12 — same shape as 10.8 did for traceability |
| 18.2 | Add allergen attributes to `RawMaterial`, sourced from the supplier's specification rather than guessed | Blocked | 18.1 |
| 18.3 | Aggregate allergens up the recipe tree, reusing 4.16's recursion over the shared `RecipeLine` table | Not started | ADR-022/ADR-032. Same traversal as costing — build once, use twice |
| 18.4 | Model "may contain" / cross-contamination separately from "contains" | Blocked | 18.1. They are different claims |
| 18.5 | Mark any product whose allergen data is **incomplete** as incomplete, rather than showing an empty list as if it meant "none" | Not started | **The safety-critical one.** An unknown presented as an absence is how an allergen system hurts someone. Mirrors 17.7/17.10's "partial is worse than none" |
| 18.6 | Tenant-scope allergen data and cover it in the isolation tests | Not started | ADR-008; pairs with 6.9 |

---

## Epic 19 — Runtime & dependency upgrade

**Branch:** `stack-runtime-upgrade` · **Depends on:** Epic 2 · **Blocks:** Epic 3

Python 3.8/3.9 + Django 3.2 (all end-of-life) → **Python 3.13 + Django 5.2 LTS** in one direct hop,
with the dependency set rebuilt (ADR-025, ADR-026).

**Runs before Epic 3, not after** — Epic 3 writes a large migration set, and written against 3.2 then
upgraded afterwards, every migration needs re-verifying on 5.2.

**The standing risk:** no tests until Epic 6, so verification here is a deprecation sweep plus a
manual pass over every screen. Accepted deliberately; 19.1 is what makes it defensible.

| ID | Task | Status | Notes |
|---|---|---|---|
| 19.1 | **Before upgrading anything**, run the app's checks under `-Wall` on Django 3.2 and clear every `RemovedInDjango*Warning` | Not started | ADR-025. The safeguard standing in for a staged upgrade, and the only pre-flight signal available without tests. Do not skip it because the jump "worked" |
| 19.2 | Rewrite `requirements.txt`: Django 5.2 LTS, `psycopg[binary]` 3, current `whitenoise`/`django-environ`, `gunicorn`; remove `asgiref`, `sqlparse`, `pytz`, `environ`, `dj-database-url`, `django-mathfilters` **and `Pillow`** | Not started | ADR-025 amended by ADR-029 — **seven** removals, not six. Re-save as UTF-8 in the same pass, closing 1.4. 19.12 then converts this into the `requirements/` split |
| 19.3 | Change the `Dockerfile` base image to `python:3.13-slim`; delete `runtime.txt` rather than updating it | Not started | ADR-025, ADR-015 rule 1 — the Dockerfile becomes the single source of the Python version. Overlaps 7.9. Do in one pass with 19.16 |
| 19.4 | Upgrade Django 3.2 → 5.2; get `manage.py check` and `makemigrations --check --dry-run` clean | Not started | The core of the epic. Expect fallout in `control/views.py`, `bakery/urls.py` and settings. Do 19.14 in the same commit |
| 19.5 | Remove `mathfilters` from `INSTALLED_APPS` and the two templates that load it (`control/templates/base_recipe.html`, `products.html`), moving their arithmetic into the view | Not started | ADR-025. A down payment on 4.1/5.x — the values move again when the service layer lands |
| 19.6 | Switch the driver to `psycopg` 3; confirm connection, migrations and `DATABASE_URL` parsing still work | Not started | ADR-025. `env.db()` must still produce a working config (ADR-015 rule 2) |
| 19.7 | Confirm `zoneinfo` handling after the `pytz` removal | Not started | ADR-025 — `USE_TZ = True` and `TIME_ZONE = 'UTC'` are already explicit, so Django 5.0's default flip is a non-event. Verify, record, move on |
| 19.8 | Manual verification pass over every screen — dashboard, raw materials, suppliers, base recipes, products, settings/export, login | Not started | **The only functional check that exists** until Epic 6. Write down what was exercised, so 6.8 starts from that list |
| 19.9 | Update the Epic 1 CI workflow to run on Python 3.13 | Not started | 1.11, ADR-011. An edit if Epic 1 landed first; otherwise 1.11 is written against 3.13 |
| 19.10 | Add an explicit `postgres:17` service to `docker-compose.yaml` and fix the network mismatch (`web` joins `my_network`; the file defines `bakery_simple`) | Not started | ADR-026. The compose file cannot run as written, and ADR-014 makes it the **only** integration-test environment — load-bearing, not tidying. Pairs with 1.12, 7.7 |
| 19.11 | Confirm the Railway Postgres service is pinned to 17 when provisioned | Not started | ADR-026; executed inside 12.2 — listed here so the pin isn't lost between epics |
| 19.12 | Convert `requirements.txt` into `requirements/{base,dev,prod}.in` and generate pinned, hashed `.txt` files with `uv pip compile`; delete the root file | Not started | **Unblocked 2026-08-16** by 9.8 ✅ / ADR-029. Compile `base` first, then `dev`/`prod` with `-c requirements/base.txt`; `--generate-hashes --python-version 3.13` throughout. Every `.in` line gets an owner/purpose comment. `prod.in` is just `-r base.in` for now — the intended shape, not an omission. `dev.in` holds `ruff`, `pytest`, `pytest-django`, `pytest-cov`, `djlint` (ADR-034) plus `pip-audit` and `coverage` (ADR-031). First-release milestone item |
| 19.13 | Diary the Django 6.2 LTS upgrade for H2 2027 | Not started | ADR-025. 5.2's extended support ends **April 2028** — scheduled work, not optional. Python 3.13 already spans it, so it is a Django-only move; evaluate 3.14 then |
| 19.14 | Replace `STATICFILES_STORAGE` with a `STORAGES` dict defining **both** `"default"` and `"staticfiles"`, keeping whitenoise's `CompressedManifestStaticFilesStorage` on the latter | Not started | **Required, low-risk** — same commit as 19.4, since `STORAGES` doesn't exist before 4.2 and `STATICFILES_STORAGE` is what 3.2 reads. Removed in 5.1, so on the target version it is **silently ignored**: the site keeps its CSS while compression and cache-busting quietly stop. Define `"default"` too — where 13.11 plugs R2 in and where 2.13's broken path gets cleaned up. **Verify:** `collectstatic` emits `staticfiles.json` plus hashed/compressed variants, then load a page with `DEBUG=False` and confirm assets return 200 |
| 19.15 | Confirm the ADR-027 capabilities are actually available and working on the upgraded stack | Not started | A short verification: middleware, functional constraints, constraint validation, `as_field_group`, `{% querystring %}`, connection pool, `pg_stat_statements`. Cheap here, expensive to discover missing halfway through Epic 3 or 5 |
| 19.16 | Change the `Dockerfile` to install a **pinned** `uv`, then `uv pip install --system --require-hashes -r requirements/prod.txt` | Not started | ADR-029. Same lines 19.3 touches. `--require-hashes` is what turns pins into an integrity check; `uv` is build tooling and never enters `base.in` |
| 19.17 | Add a lock-drift check to CI: recompile the `.in` files and fail the PR if the committed `.txt` files differ | Not started | ADR-029. Extends 1.11 (or 6.12). Without it the generated files are only as fresh as the last person who remembered |

---

## Decision → task coverage

Every `Accepted` ADR maps to at least one task. Add a row when a new ADR lands, in the same session.
Tasks only — the reasoning is in [decisions.md](docs/decisions.md), and `10.x`/`11.x` references that
are not in this file are open decisions in [roadmap.md](docs/roadmap.md).

| ADR | Tasks |
|---|---|
| 002 / 036 — Spark on Databricks Serverless, R2 extract, gunicorn stands | 7.14, 16.1–16.13, 11.17 |
| 003 / 013 — Hosting narrowed, then Railway (Hobby, EU West) | 12.1 ✅, 12.2, 12.3, 12.6–12.9 |
| 004 — Deploy via the custom Dockerfile | 1.11, 7.6, 12.3 |
| 005 — Media in Cloudflare R2 | 2.5, 2.13, 3.18, 4.9, 5.11, 13.1–13.11, 16.9 |
| 006 — Multi-tenant SaaS | 2.8, 3.1–3.4, 11.5 |
| 007 — App and database always separate | 3.39, 7.7, 12.2 |
| 008 — Shared DB, row-level isolation + tenant export | 3.2, 3.3, 4.6, 6.9, 14.1–14.6, 16.7, 17.8, 18.6 |
| 009 — Dedicated GDPR personal-data export | 15.1–15.6 |
| 010 — `main` integration / `production` deploy, tagged releases | 1.8, 1.9, 1.10, 6.13, 7.12, 7.15, 8.8, 12.4 |
| 011 — Minimal CI in Epic 1, full pipeline in Epic 6 | 1.11, 1.13, 6.12, 19.9 |
| 014 — Local Docker dev/test, release-PR preview | 1.12, 6.15, 12.4, 12.5, 12.10, 19.10 |
| 015 — Host portability | 1.5, 3.44–3.49, 3.70, 7.6, 7.7, 7.9–7.11, 7.13, 7.17, 7.18, 8.9, 12.11 |
| 016 — One free pilot, no deadline, flat pricing later | **Negative** constraints only: no plan/tier fields on 3.1, no plan gating in 2.8/3.4 |
| 017 — Traceability in scope as its own epic | 17.1–17.14, plus the forced soft delete in 3.13/3.22 |
| 018 — Costing & money semantics | 3.10, 3.11, 3.15, 3.16, 3.26, 3.34 ✅, 3.50–3.54, 5.16, 6.16, 6.17, 17.12, and deleting the inline `float()` costing in 4.1 |
| 019 — Soft delete, per-tenant supplier uniqueness, admin as support tooling | 2.15, 3.6, 3.22, 3.55, 3.56, 6.18 |
| 020 — Three per-tenant roles on a membership record | 2.8, 2.16, 3.4, 3.57, 3.58, 6.19, 14.6 |
| 021 — Non-functional targets | 5.12–5.17, 7.20 |
| 022 — Receipts drive cost; lines accept a material or a base recipe | 3.59–3.62, 4.16, 4.17, 5.20, 6.20, 6.21, 17.1, 18.3 |
| 023 — Dashboard overview; settings as self-administration | 4.18, 5.18, 5.19, 14.6, and replacing the broken user-delete view (6.7) |
| 024 — MoSCoW pass | 5.9, 5.21 + 3.63, Epic 18, 13.10, 17.14 |
| 025 — Django 5.2 LTS on Python 3.13 | 19.1–19.9, 19.12, 19.13; 1.4 absorbed into 19.2; `runtime.txt` removal shared with 7.9 |
| 026 — PostgreSQL 17 pinned everywhere | 19.10, 19.11, and the version constraint on 3.44–3.48 |
| 027 — Adopt the capabilities the upgrade unlocks | 2.17, 2.18, 3.58, 3.64–3.69, 5.22, 5.23, 7.19, 7.20, 13.11, 19.14, 19.15; **reshapes** 2.6/2.7, **reduces** 5.10/5.12 |
| 028 — Backend architecture | 2.19–2.23, 4.19, 4.20, 5.24, 7.21, 7.22, 11.16; **rescopes** 1.5 and 4.1, **cancels** 4.15, **supersedes** 2.10 by 4.5 + 2.23 |
| 029 — `uv pip compile`; the `.in` file is the register | 19.12, 19.16, 19.17, the `Pillow` removal in 19.2 and its return in 13.1, and 5.25 |
| 030 — Frontend: partials, Bootstrap 5.3, HTMX, no build step | 5.1–5.8, 5.25, 6.11 |
| 031 — Operations: coverage-gated CI, git-watch deploys, Sentry EU, two backup tracks | 3.38, 3.40, 3.70–3.72, 6.12, 6.14, 6.22, 7.2, 7.5, 7.15, 7.23, 11.13, 12.9, 12.11 |
| 032 — One shared `RecipeLine`; tenant-scoped categories | 3.19, 3.26, 3.73, 3.74, 18.3; **corrects** 3.42 and 4.14 |
| 033 — Traceability entities and lot codes | 17.1–17.3, 17.12–17.14; **negative** constraint on 3.10/3.14 |
| 034 — `ruff` for lint *and* format; `pytest-django` | 6.10, 6.11, 6.23, 6.24; feeds 6.12, 6.22, 19.12 |
| 035 — Tenant export as a CSV bundle + JSON manifest | 14.1, 14.3, 14.4, 14.6 |
| 037 — One task = one feature = one PR | 1.16, and the branch naming enforced by 1.9 and 1.15 |
| 038 — Agent-assisted task loop | 1.14, 1.15 |
| [project_requirements.md](docs/project_requirements.md) — Ireland first, then wider EU | 11.8, 12.8 |
| [project_requirements.md](docs/project_requirements.md) — bulk CSV exports stay an admin feature | 15.5 |
| [tech_stack.md](docs/tech_stack.md) — static assets stay on whitenoise | 7.16 |

## Highest-risk items

The reasons for the current epic ordering. Each is already a task — this table exists so the risk
isn't lost among 352 of them.

| Risk | Fixed by |
|---|---|
| Running an end-of-life runtime **and** framework — Django 3.2 (EOL April 2024) on Python 3.8/3.9 (EOL Oct 2024/Oct 2025), so no security patches reach any layer | Epic 19 |
| A framework upgrade verified only by hand, because no test suite exists yet | 19.1, 19.8, then Epic 6 |
| Hardcoded `SECRET_KEY`, DB credentials and `DEBUG = True`, with `heroku.py` defaulting `DEBUG` to `True` in the *production* module | 2.1, 2.2, 2.19 |
| Access control enforced in templates instead of views | 2.17 (the real fix), then 2.6, 2.7, 2.20 |
| No brute-force protection on the single credential entry point for every tenant | 2.22, with 2.23 supplying the attempt record |
| No tenant isolation in a confirmed multi-tenant product | 3.3, 3.55, 4.6, 6.9, 6.18 — plus 2.21, where a missed permission-cache invalidation is itself a cross-tenant leak |
| Backups that have never been restored — the restore path runs for the first time on the day it matters, over records food law requires to be kept | 3.70, 3.48, 3.72 |
| Switching templates to `{% static %}` activates manifest storage for the first time, turning any missing asset into a render-time 500 | 1.3 before 5.3, plus 1.13 |
| Generated files committed to the repository | 1.1, 1.2 |
| Known functional defects (e.g. user delete removes the wrong model) | 6.7, with the actual fix in 5.19 |
| No automated quality gate before merge or deploy | 1.11, 6.12, 6.13 |
| Inconsistent runtime configuration across Docker, Heroku and local | 1.5, 7.7, 7.8, 7.9, 19.10 |
| A half-built traceability feature that *looks* like a compliance record to a real food business operator | 17.7, 17.10, plus 10.8 before Epic 17 starts |
| Allergen data presented as authoritative while incomplete — the same failure mode, with a consumer-safety consequence | 18.5, gated on 10.12/18.1 |
| Schema redesigned in Epic 3 without accounting for Epic 17's event layer, forcing a second redesign | **9.21 ✅ 2026-08-26** (ADR-033), before 3.19/3.22 are implemented |
| A cyclic base recipe hanging every costing request once recipes can nest | 3.59, 4.16, 6.20 |
| Cost figures presented with equal confidence whether they came from an invoice or a guess | 3.62, 4.17, 5.20 |
| A traceback shipping supplier contacts, staff emails or tenant costing data to a processor by accident | 7.23, and it is not optional |

## Definition of "production ready"

- [ ] No secrets in source control; all configuration from the environment, and a missing variable
      fails at boot rather than falling back to a dev default
- [ ] Supported Python and Django versions, with pinned, hashed, reproducible dependencies (Epic 19)
- [ ] Environment separation as decided: `base.py` (production) + `local.py` + `test.py`, dev/test
      local — **no hosted staging** (ADR-014/ADR-028)
- [ ] Every business action protected by real authentication and per-tenant authorization
- [ ] Tenant isolation enforced at the query layer and proven by tests
- [ ] Safe, reversible, tested database migrations
- [ ] Backup and restore strategy documented **and** drilled, with the accepted 24 h RPO stated
- [ ] Automated tests and CI/CD gating every merge and deploy
- [ ] Logging, monitoring and error tracking enabled, with PII scrubbing verified
- [ ] Deployment and rollback documented and repeatable
- [ ] GDPR obligations met for the personal data actually held (inventory, legal basis, retention,
      subject rights)
