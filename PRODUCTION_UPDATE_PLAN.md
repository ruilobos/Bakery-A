# Bakery Production Backlog

This file is the **task backlog**. Every phase, discovery workstream, and new feature is an
**Epic**; every epic holds a numbered list of tasks that can be picked up, tracked, and closed.

**It holds work, not planning.** Anything still being decided, proposed, compared, or awaiting
approval lives in `docs/` — not here:

| If it is… | It lives in… |
|---|---|
| A choice not yet made (stack, versions, tooling, hosting) | [docs/tech_stack.md](docs/tech_stack.md) |
| A product/business question (personas, roles, features, data semantics) | [docs/project_requirements.md](docs/project_requirements.md) |
| A privacy/compliance question (legal basis, retention, DPAs, DPIA) | [docs/gdpr.md](docs/gdpr.md) |
| A decision that *has* been made, with its reasoning | [docs/decisions.md](docs/decisions.md) (ADR log) |
| Sequencing, branch status, release milestones | [docs/roadmap.md](docs/roadmap.md) |

The flow is one-directional: **a decision lands in `docs/decisions.md` → it becomes one or more
tasks in an epic here.** Every `Accepted`/`Decided` entry in `docs/` must be represented by at
least one task below (see the [Decision → task coverage](#decision--task-coverage) map).

## How to use this backlog

- **Epic = phase/branch.** Epic numbers and branch names map 1:1 to the rows in
  [docs/roadmap.md](docs/roadmap.md). Epic-level status is tracked there; task-level status here.
- **Task IDs are stable** (`3.12` = Epic 3, task 12). Reference them in commits, PRs, and plans.
  Never renumber a task — append new ones at the end of their section.
- **Task statuses:** `Not started` → `In progress` → `Done`, or `Blocked` (the Notes column must
  say what it's blocked on — usually an `Open` row in a `docs/` file).
- **A `Blocked` task must not be implemented.** If a task is blocked on an open decision, the
  decision gets made and logged as an ADR first; then the task unblocks.
- **New work starts as a task here**, not as a paragraph. If it needs a decision first, add the
  question to the right `docs/` file and add the "decide X and log an ADR" task to Epic 9/10/11.

## Backlog at a glance

| Epic | Name | Branch | Blocked by |
|---|---|---|---|
| [1](#epic-1--stabilize-the-repository) | Stabilize the repository | `phase-1-repo-cleanup` | — |
| [2](#epic-2--security--configuration-hardening) | Security & configuration hardening | `phase-2-security-hardening` | Epic 1 |
| [3](#epic-3--database-redesign--data-governance) | Database redesign & data governance | `phase-3-db-redesign` | Epics 9, 10, 11 |
| [4](#epic-4--backend-modernization) | Backend modernization | `phase-4-backend-modernization` | Epics 3, 9 |
| [5](#epic-5--frontend-modernization) | Frontend modernization | `phase-5-frontend-modernization` | Epic 9 |
| [6](#epic-6--testing--quality-gates) | Testing & quality gates | `phase-6-testing-ci` | Epics 1–5 |
| [7](#epic-7--observability--operations) | Observability & operations | `phase-7-observability` | Epic 12 |
| [8](#epic-8--documentation--team-readiness) | Documentation & team readiness | `phase-8-docs` | Epics 1–7 |
| [9](#epic-9--tech-stack-decisions-discovery) | Tech stack decisions (discovery) | `stack-decisions` | — |
| [10](#epic-10--requirements-discovery) | Requirements discovery | `requirements-discovery` | — |
| [11](#epic-11--gdpr-data-inventory--policy) | GDPR data inventory & policy | `gdpr-data-inventory` | — |
| [12](#epic-12--hosting-migration) | Hosting migration | `stack-hosting-migration` | Epic 9 |
| [13](#epic-13--media-storage-for-user-uploads) | Media storage for user uploads | `feature-media-storage` | Epics 3, 11 |
| [14](#epic-14--tenant-full-data-export) | Tenant full data export | `feature-tenant-data-export` | Epic 3 |
| [15](#epic-15--gdpr-personal-data-export) | GDPR personal-data export | `feature-gdpr-data-export` | Epic 11 |
| [16](#epic-16--ai-insights--alerts-service) | AI insights & alerts service | `feature-ai-insights-service` | Epics 9, 11 |

Epic-level status lives in [docs/roadmap.md](docs/roadmap.md) — update it there when an epic moves.

---

## Epic 1 — Stabilize the repository

**Branch:** `phase-1-repo-cleanup` · **Depends on:** —

Get the repository, its history, and its branch/CI plumbing into a state where every later epic can
ship safely through a PR.

### Source control cleanup

| ID | Task | Status | Notes / source |
|---|---|---|---|
| 1.1 | Remove generated and local-only artifacts from version control (`__pycache__/`, `bakery/staticfiles/`, `.idea/`, `.venv/`, OS/editor temp files) | Not started | |
| 1.2 | Expand `.gitignore` to cover Python, Django, environment, build, and IDE artifacts | Not started | |
| 1.3 | Keep only source assets in `bakery/static/`; confirm nothing depends on the committed `staticfiles/` output | Not started | `collectstatic` must regenerate it |
| 1.4 | Re-save `requirements.txt` as UTF-8 (currently UTF-16LE) | Not started | Blocks any tooling that reads it |

### Project structure cleanup

| ID | Task | Status | Notes / source |
|---|---|---|---|
| 1.5 | Split settings into `settings/base.py` + `local.py` + `test.py` + `production.py`; retire the Heroku-specific module | Blocked | Settings-layout row is `Open` in [tech_stack.md](docs/tech_stack.md) — resolve in 9.9 first |
| 1.6 | Remove dead code, duplicate assets, and unused views/forms (e.g. `control/forms.py: Raw_Material_Form`, wired into nothing) | Not started | |
| 1.7 | Rename prototype identifiers: `categorie`→`category`, `recipe_yeld`→`recipe_yield`, `Base_recipes`→`BaseRecipe`, `Bs_Ingredients`→`BaseRecipeIngredient`, `Recipe_Ingredients`→`ProductIngredient` | Not started | Use transitional migrations + compatibility layers, never a big-bang rename; sequence with Epic 3 |

### Branch, release, and CI plumbing (ADR-010, ADR-011)

| ID | Task | Status | Notes / source |
|---|---|---|---|
| 1.8 | Create the `production` branch as the deploy branch, with `main` as the integration/dev-test branch | Not started | [ADR-010](docs/decisions.md) |
| 1.9 | Configure branch protection on both `main` and `production`: PR-only, no direct pushes, no force-pushes (0 required approvals while solo) | Not started | [ADR-010](docs/decisions.md) |
| 1.10 | Define the release step: every merge to `production` is tagged with a semantic version and published as a GitHub Release with auto-generated notes | Not started | [ADR-010](docs/decisions.md) |
| 1.11 | Add a minimal GitHub Actions workflow on every PR against `main`/`production`: `python manage.py check`, `python manage.py makemigrations --check --dry-run`, `docker build` validation, basic lint pass | Not started | [ADR-011](docs/decisions.md). No test run (none exist yet) and no deploy step (no host yet) — verification only; extended in 6.12 |
| 1.12 | Add a script that refreshes and launches the local dev environment in one command — pull `main`, rebuild the containers, run migrations — so the post-merge integration check is a single step | Not started | [ADR-014](docs/decisions.md). Run **manually** by the developer; GitHub cannot trigger a local machine. Missing the migration step is the most common cause of a confusing local failure |

---

## Epic 2 — Security & configuration hardening

**Branch:** `phase-2-security-hardening` · **Depends on:** Epic 1

### Configuration

| ID | Task | Status | Notes / source |
|---|---|---|---|
| 2.1 | Move all secrets to environment variables or a secret manager; remove the hardcoded `SECRET_KEY` and database credentials from source | Not started | |
| 2.2 | Set `DEBUG = False` everywhere outside local development | Not started | |
| 2.3 | Define environment-specific `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, and cookie settings | Not started | |
| 2.4 | Add secure defaults: `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_HSTS_SECONDS`, `SECURE_HSTS_INCLUDE_SUBDOMAINS`, `SECURE_HSTS_PRELOAD`, `X_FRAME_OPTIONS` | Not started | |
| 2.5 | Hold object-storage (R2) access keys as environment variables — never hardcoded | Not started | [ADR-005](docs/decisions.md); pairs with 13.3 |

### Authentication and authorization

| ID | Task | Status | Notes / source |
|---|---|---|---|
| 2.6 | Protect all business views with `LoginRequiredMixin` | Not started | |
| 2.7 | Protect admin-only operations with explicit permission classes/mixins; stop relying on template-only `is_staff` checks for security | Not started | |
| 2.8 | Implement role-based permissions (admin/owner, manager, staff/operator, read-only/auditor), scoped **per tenant** rather than globally | Blocked | Role capabilities are `Open` in [project_requirements.md](docs/project_requirements.md) — resolve in 10.1. Per-tenant scoping per [ADR-006](docs/decisions.md) |
| 2.9 | Add audit logging for user management and destructive actions | Not started | Extended by 11.10 (logging who viewed/exported personal data) |

### Input and data protection

| ID | Task | Status | Notes / source |
|---|---|---|---|
| 2.10 | Replace the `print()` login diagnostics in `accounts/views.py` with structured logging that never records passwords | Not started | **Highest-priority security defect** — [gdpr.md](docs/gdpr.md) §6 |
| 2.11 | Validate and sanitize all form input server-side | Not started | Form-level business validation is 4.7 |
| 2.12 | Add server-side authorization to every export endpoint | Not started | |
| 2.13 | Remove the broken leftover `MEDIA_ROOT` path (`bluebiulding/media`) | Not started | Real media handling is Epic 13 |
| 2.14 | Confirm encryption in transit (HTTPS enforced end-to-end) once the settings work lands | Not started | GDPR Art. 32 — [gdpr.md](docs/gdpr.md) §6 |

---

## Epic 3 — Database redesign & data governance

**Branch:** `phase-3-db-redesign` · **Depends on:** Epics 9 (stack), 10 (data semantics), 11 (retention)

Make the schema consistent, normalized, migration-safe, and tenant-scoped, while preserving
historical business data.

### Multi-tenancy (ADR-006 / ADR-008)

| ID | Task | Status | Notes / source |
|---|---|---|---|
| 3.1 | Add a `Bakery` model as the tenant root | Not started | [ADR-006](docs/decisions.md) |
| 3.2 | Add a tenant FK to every business table: `Supplier`, `RawMaterial`, `Base_recipes`, `Bs_Ingredients`, `Product`, `Recipe_Ingredients`, and the future `Profile` | Not started | [ADR-008](docs/decisions.md) |
| 3.3 | Enforce tenant scoping at the query layer (managers/service layer that always filter by the current tenant) | Not started | Correctness- and security-critical; a missed filter is a cross-tenant leak. Tested in 6.9 |
| 3.4 | Scope user roles/permissions per tenant in the data model | Not started | Pairs with 2.8 |

### Supplier

| ID | Task | Status | Notes / source |
|---|---|---|---|
| 3.5 | Replace supplier name as primary key with a generated numeric or UUID primary key | Not started | |
| 3.6 | Keep supplier name unique if business rules require it | Blocked | Business rule `Open` — 10.5 |
| 3.7 | Change phone number from `IntegerField` to a string field | Not started | |
| 3.8 | Add optional address, tax/business identifier, active flag, and timestamps | Not started | |

### Raw material

| ID | Task | Status | Notes / source |
|---|---|---|---|
| 3.9 | Change `quantity` from `CharField` to `DecimalField` | Not started | |
| 3.10 | Implement the agreed price semantics (per purchase unit vs. per normalized base unit) | Blocked | Semantics `Open` — 10.5 |
| 3.11 | Add normalized unit handling for cost calculations | Blocked | Depends on 3.10 and canonical units (3.24) |
| 3.12 | Add SKU/code uniqueness rules where appropriate | Not started | |
| 3.13 | Add active/inactive status instead of hard deletes where business history matters | Not started | |

### Base recipe and product

| ID | Task | Status | Notes / source |
|---|---|---|---|
| 3.14 | Standardize yield, unit, and cost fields across base recipes and products | Not started | |
| 3.15 | Make VAT representation consistent and documented | Not started | |
| 3.16 | Version product pricing history if required | Blocked | Requirement `Open` — 10.5 |
| 3.17 | Store calculated values as derived data only, never as editable business data | Not started | Pairs with the service layer in 4.1 |
| 3.18 | Add the `Product.photo` field | Not started | Owned by 13.4 — this row exists so the schema work is sequenced with it |

### Ingredient relations

| ID | Task | Status | Notes / source |
|---|---|---|---|
| 3.19 | Implement the agreed ingredient-line shape: keep separate through tables, or move to a shared ingredient line model with a typed parent reference | Blocked | Model shape `Open` — 9.18 |
| 3.20 | Add uniqueness constraints preventing duplicate ingredient lines for the same parent/item/unit combination | Not started | |

### Database best practices

| ID | Task | Status | Notes / source |
|---|---|---|---|
| 3.21 | Add `created_at` and `updated_at` to all core business tables | Not started | |
| 3.22 | Add soft delete / archive patterns for entities that must stay historically visible | Blocked | Which entities need history is `Open` — 10.5 |
| 3.23 | Add `db_index=True` or explicit indexes on common filter/join paths | Not started | |
| 3.24 | Add unique and check constraints wherever a business rule exists | Not started | |
| 3.25 | Use `Decimal` consistently for money and quantities (schema and application code) | Not started | Removes the `float()` math currently in `control/views.py` — pairs with 4.1 |
| 3.26 | Standardize units and categories via controlled enums or lookup/reference tables | Blocked | Enum-vs-lookup choice `Open` — 9.18 |

### Migration strategy

| ID | Task | Status | Notes / source |
|---|---|---|---|
| 3.27 | Document the current schema and its data-quality issues before changing anything | Not started | |
| 3.28 | Take a full, verified database backup before the first migration | Not started | |
| 3.29 | Introduce additive fields first (no destructive changes in the same release) | Not started | |
| 3.30 | Backfill data with safe migrations or management commands | Not started | |
| 3.31 | Switch application code over to the new fields | Not started | |
| 3.32 | Remove legacy fields only after validation and deployment stability | Not started | |
| 3.33 | Write migration rollback guidance for every schema-change release | Not started | |

### Data quality and governance

| ID | Task | Status | Notes / source |
|---|---|---|---|
| 3.34 | Define the canonical units used for costing | Blocked | Business decision — 10.5 |
| 3.35 | Add data validation rules for prices, VAT, yields, and quantities | Not started | |
| 3.36 | Define import/export contracts and field definitions | Not started | Feeds Epics 14 and 15 |
| 3.37 | Define the seed/reference data strategy for categories and units | Blocked | Depends on 3.26 |
| 3.38 | Create backup, restore, and retention procedures — including a tested restore drill | Blocked | Retention periods are `Open` in [gdpr.md](docs/gdpr.md) §5 — 11.4 |

### Database operations for production

| ID | Task | Status | Notes / source |
|---|---|---|---|
| 3.39 | Run on managed PostgreSQL (or a well-maintained dedicated service), as a service separate from the app | Not started | [ADR-007](docs/decisions.md); provisioned in 12.2 |
| 3.40 | Enable automated backups and point-in-time recovery where available | Not started | |
| 3.41 | Separate application and database credentials per environment | Not started | |
| 3.42 | Add connection pooling if traffic or deployment topology requires it | Blocked | Need/approach `Open` — 9.18 |
| 3.43 | Monitor slow queries and add indexes based on observed workload | Not started | Needs 7.1/7.2 in place to observe |
| 3.44 | Maintain a **host-independent logical backup** (`pg_dump`) alongside whatever native snapshot the host provides, and prove it by restoring onto a *different* PostgreSQL instance — not the one it came from | Not started | [ADR-015](docs/decisions.md) rule 5. **This is what actually makes the host replaceable** — a Railway volume snapshot cannot be restored onto Clever Cloud or Scaleway. Extends 3.38/3.40; the restore drill is the part that counts |
| 3.45 | Restrict the schema to core PostgreSQL and widely-available extensions; any host-specific feature needs its own ADR | Not started | [ADR-015](docs/decisions.md) rule 6. Pairs with the version pin in 9.3 — pin to a version every candidate host actually offers |
| 3.46 | Commit the exact dump and restore commands as scripts in the repo, with the flags settled — not prose in a runbook | Not started | [ADR-015](docs/decisions.md) rule 5. `pg_dump` defaults emit `OWNER`/`GRANT` statements referencing roles that don't exist on the new host — the single most common cross-host restore failure. Settle `--no-owner --no-privileges` (plus explicit re-granting) and the dump format now, not during a migration |
| 3.47 | Define the post-restore verification: per-table row counts against source, constraint/FK validation, sequence positions, and a `REINDEX` pass | Not started | This is what "proven restore" in 3.44 actually means. `REINDEX` matters because text index ordering depends on the OS collation (glibc/ICU version) — a cross-host restore can leave indexes subtly wrong while everything *looks* fine |
| 3.48 | Automate the restore drill on a schedule — restore the latest dump into a throwaway PostgreSQL and run 3.47's checks, reporting failures | Not started | **The key one.** App migration is low-risk because deploys rehearse it constantly; a database restore path that runs once a year is where the surprises live. A drill that runs weekly makes migration day routine rather than novel |
| 3.49 | Verify that `migrate` from an empty database reproduces the production schema exactly, and forbid manual DDL outside Django migrations | Not started | If production has drifted from what the migrations produce, the schema is no longer reproducible anywhere — this quietly breaks both host migration and 12.10's PR-environment seeding |

---

## Epic 4 — Backend modernization

**Branch:** `phase-4-backend-modernization` · **Depends on:** Epics 3, 9

### Application architecture

| ID | Task | Status | Notes / source |
|---|---|---|---|
| 4.1 | Move costing/margin calculations into a dedicated services/domain module, with one implementation — removing the duplication between model `@property` methods and the inline `float()` loops in `control/views.py` | Not started | |
| 4.2 | Make views thin: query, validate, delegate, render | Not started | |
| 4.3 | Use class-based or function-based views consistently, not a mix without reason | Not started | |
| 4.4 | Replace broad/ineffective exception patterns with correct query handling | Not started | |
| 4.5 | Remove the dead custom auth code (`accounts.views.user_login`) once Django's auth views are the standard | Blocked | Auth approach `Open` — 9.12. Depends on 2.10 landing first |
| 4.6 | Make every service-layer query tenant-scoped by construction | Not started | [ADR-008](docs/decisions.md); a missed filter is a data leak. Tested in 6.9 |

### Forms and validation

| ID | Task | Status | Notes / source |
|---|---|---|---|
| 4.7 | Replace `fields = "__all__"` with explicit ModelForms on all create/update flows | Not started | |
| 4.8 | Add business validation to those forms: quantities, units, VAT, price ranges, uniqueness constraints | Not started | |
| 4.9 | Validate uploaded file type and size for product photos and profile pictures | Not started | Pairs with 13.7 |
| 4.10 | Add form widgets and help text for clearer operator workflows | Not started | |

### Query and performance

| ID | Task | Status | Notes / source |
|---|---|---|---|
| 4.11 | Add `select_related`/`prefetch_related` to supplier/product/ingredient listings | Not started | |
| 4.12 | Remove repeated cost calculations from nested loops in views | Not started | Follows from 4.1 |
| 4.13 | Add service-layer aggregate calculations for the dashboard and product costing | Not started | |
| 4.14 | Cache expensive dashboard summaries | Blocked | Whether/how to cache is `Open` — 9.18 |

### API readiness

| ID | Task | Status | Notes / source |
|---|---|---|---|
| 4.15 | Build the agreed API surface (DRF or a small read-only reporting/export API), versioned from the first endpoint | Blocked | Whether an API is needed at all is `Open` — 9.11 |

---

## Epic 5 — Frontend modernization

**Branch:** `phase-5-frontend-modernization` · **Depends on:** Epic 9

| ID | Task | Status | Notes / source |
|---|---|---|---|
| 5.1 | Introduce a shared `base.html` layout | Not started | |
| 5.2 | Replace duplicated navbar/footer/page scaffolding with reusable template blocks and partials | Not started | |
| 5.3 | Replace hardcoded static paths with `{% load static %}` / `{% static %}` | Not started | |
| 5.4 | Update Bootstrap to the agreed version | Blocked | CSS framework/version `Open` — 9.13 |
| 5.5 | Remove unused empty JavaScript files or replace them with purposeful modules | Not started | |
| 5.6 | Introduce the agreed asset pipeline (SCSS/CSS bundling, JS modules, cache-busted builds) | Blocked | Pipeline choice `Open` — 9.13 |
| 5.7 | Add the agreed progressive-enhancement layer for dynamic interactions | Blocked | Vanilla JS vs. HTMX `Open` — 9.13 |
| 5.8 | Add linting/formatting for templates, CSS, and JS | Blocked | Tooling `Open` — 9.17 |
| 5.9 | Build real search/filter flows, or remove the non-functional search inputs | Blocked | Feature priority `Open` — 10.3 |
| 5.10 | Improve forms, validation errors, empty states, and destructive-action confirmations | Not started | |
| 5.11 | Add image upload/preview UI with a clear empty-state placeholder | Not started | Owned by 13.8 |
| 5.12 | Improve accessibility: semantic HTML, form labels, focus states, keyboard navigation, colour contrast | Blocked | Target WCAG level `Open` — 10.4 |
| 5.13 | Make data tables usable on mobile and tablet | Not started | |

---

## Epic 6 — Testing & quality gates

**Branch:** `phase-6-testing-ci` · **Depends on:** Epics 1–5

### Test coverage

| ID | Task | Status | Notes / source |
|---|---|---|---|
| 6.1 | Unit tests for model validation and constraints | Not started | |
| 6.2 | Unit tests for costing logic | Not started | Against the 4.1 service layer |
| 6.3 | Unit tests for margin logic | Not started | |
| 6.4 | Unit tests for permissions and role enforcement | Not started | Covers 2.6–2.8 |
| 6.5 | Unit tests for the export views | Not started | Covers Epics 14/15 too |
| 6.6 | Integration tests for critical CRUD workflows | Not started | |
| 6.7 | Regression tests for known-broken areas (e.g. the user-delete view that deletes `RawMaterial`) | Not started | |
| 6.8 | Smoke tests for login, dashboard, raw materials, suppliers, recipes, products, and settings | Not started | |
| 6.9 | Dedicated cross-tenant isolation tests — prove tenant A can never read or write tenant B's rows | Not started | [ADR-008](docs/decisions.md); covers 3.3 and 4.6 |

### Tooling

| ID | Task | Status | Notes / source |
|---|---|---|---|
| 6.10 | Add and configure the agreed formatter/linter across the codebase | Blocked | `ruff`/`black`/`isort` choice `Open` — 9.17 |
| 6.11 | Add template linting | Blocked | Whether to adopt it is `Open` — 9.17 |

### CI/CD

| ID | Task | Status | Notes / source |
|---|---|---|---|
| 6.12 | Extend the Epic 1 workflow (do not replace it) with: dependency install, full lint/format enforcement, the real test suite, and security checks | Not started | [ADR-011](docs/decisions.md) |
| 6.13 | Enable required status checks on `main` and `production`, blocking merge when checks fail | Not started | [ADR-010](docs/decisions.md) |
| 6.14 | Block deployments when checks fail | Not started | Deploy automation itself is 7.15 |
| 6.15 | Run the unit test suite on every PR into `main` as the feature-branch quality gate | Not started | [ADR-014](docs/decisions.md) — the automated half of the test split. Integration verification of merged `main` stays manual, run locally against `docker-compose`. Part of 6.12's extended workflow |

---

## Epic 7 — Observability & operations

**Branch:** `phase-7-observability` · **Depends on:** Epic 12 (a chosen host)

### Logging and monitoring

| ID | Task | Status | Notes / source |
|---|---|---|---|
| 7.1 | Add structured application logging | Not started | |
| 7.2 | Add error tracking | Blocked | Vendor `Open` — 9.15 |
| 7.3 | Log security-relevant events, admin actions, and failed operations without leaking secrets | Not started | Pairs with 2.9, 2.10 |
| 7.4 | Add health checks for application and database connectivity | Not started | |
| 7.5 | Add uptime monitoring and alerting | Blocked | Tooling `Open` — 9.15 |

### Deployment and infrastructure

| ID | Task | Status | Notes / source |
|---|---|---|---|
| 7.6 | Harden the existing `Dockerfile` as the single deploy artifact (multi-stage build, slim final image, pinned base) | Not started | [ADR-004](docs/decisions.md) |
| 7.7 | Fix `docker-compose.yaml` so it defines all required services correctly, with app and database as separate services | Not started | [ADR-007](docs/decisions.md); drop the external `bakery_simple` network assumption |
| 7.8 | Separate the local compose definition from the production deployment definition | Not started | |
| 7.9 | Remove legacy Heroku assumptions from the repo (`settings/heroku.py`, `runtime.txt`, Procfile) | Not started | Superseded by 1.5 + Epic 12 |
| 7.10 | Add a static asset build step to the release process | Not started | `collectstatic` currently runs at image build time. After the 1.5 settings split, make sure it does **not** require `DATABASE_URL`/`SECRET_KEY` to be present at build — a production settings module that raises on missing env vars will break the image build |
| 7.11 | Add a migration release step, and **remove `migrate` from the container start command** in both the `Dockerfile` `CMD` and `docker-compose.yaml` | Not started | [ADR-015](docs/decisions.md) rule 4. Migrating on boot makes every replica race to migrate, and ties the schema change to container start rather than to the release |
| 7.12 | Write and test the rollback procedure, using the release tags from 1.10 | Not started | |
| 7.13 | Document every environment variable the app requires, per environment, as a committed `.env.example` (names and example values only — never real secrets) | Not started | [ADR-015](docs/decisions.md) rule 8 — this file is the migration checklist; if it's only in a host's dashboard, moving host becomes archaeology |
| 7.14 | Run the app under Gunicorn (or the process manager appropriate to the chosen host) in production | Blocked | Server/version `Open` — 9.4 |
| 7.15 | Automate deploys: merge to `main` → staging environment, merge to `production` → production environment | Blocked | Needs the host chosen in 12.1 — [ADR-010](docs/decisions.md) |
| 7.16 | Keep serving static assets via whitenoise; confirm it still fits once a CDN/object storage is in play | Not started | Decided "no change" in [tech_stack.md](docs/tech_stack.md) — this is a verification task |
| 7.17 | Bind Gunicorn to `$PORT` with a local fallback (`--bind 0.0.0.0:${PORT:-8000}`) instead of the hardcoded `:8000` in the `Dockerfile` `CMD` | Not started | [ADR-015](docs/decisions.md) rule 3. Railway, Render, Fly, DigitalOcean, Clever Cloud and Heroku all inject the port they expect the container to listen on; a hardcoded port needs per-host workarounds |
| 7.18 | Confirm no persistent state is written to the app container's local disk — only PostgreSQL and object storage | Not started | [ADR-015](docs/decisions.md) rule 7. Pairs with 2.13 (the broken `MEDIA_ROOT`) and Epic 13 |

---

## Epic 8 — Documentation & team readiness

**Branch:** `phase-8-docs` · **Depends on:** Epics 1–7

| ID | Task | Status | Notes / source |
|---|---|---|---|
| 8.1 | Rewrite `README.md` for production-oriented setup and development workflows | Not started | |
| 8.2 | Document the architecture: app modules, data model, deployment overview, permissions model | Not started | |
| 8.3 | Write the deploy runbook | Not started | |
| 8.4 | Write the rollback runbook | Not started | Follows 7.12 |
| 8.5 | Write the backup/restore runbook | Not started | Follows 3.38 |
| 8.6 | Write the secret-rotation runbook | Not started | |
| 8.7 | Write the incident-response runbook | Not started | Must align with the GDPR breach process (11.8) |
| 8.8 | Document the branch/promotion/release process for contributors | Not started | [ADR-010](docs/decisions.md) |
| 8.9 | Write the host-migration runbook: provision elsewhere, restore the logical dump, move env vars, verify (3.47), cut DNS over, decommission | Not started | [ADR-015](docs/decisions.md). Derive it from the actual Railway setup while it's fresh; it's the executable form of 11.14's revisit option. Must cover: a maintenance window timed against Irish bakery business hours (tenants share one timezone in phase 1), lowering DNS TTL beforehand, keeping the old database **read-only but alive** until verification passes (12.6), and the rollback trigger. Object storage does **not** move — R2 is independent of the app host per [ADR-005](docs/decisions.md) |

---

## Epic 9 — Tech stack decisions (discovery)

**Branch:** `stack-decisions` · **Depends on:** — · **Blocks:** Epics 3, 4, 5, 6, 12

Every task here is "make the call, write it into [tech_stack.md](docs/tech_stack.md), and log an ADR
in [decisions.md](docs/decisions.md)". No implementation happens in this epic.

| ID | Task | Status | Notes / source |
|---|---|---|---|
| 9.1 | Decide the target Python version, and whether a follow-up validation pass on the next minor release is in scope | Not started | Currently 3.8 in `runtime.txt`, 3.9-slim in the Dockerfile |
| 9.2 | Decide the target Django version and the upgrade route (direct to current LTS vs. staged) | Not started | Currently 3.2 |
| 9.3 | Decide the pinned PostgreSQL version | Not started | [ADR-015](docs/decisions.md) rule 6 — pick a version every candidate host actually offers, so a logical dump restores cleanly elsewhere. Feeds 3.45 |
| 9.4 | Decide the WSGI/ASGI server and version | Not started | Unblocks 7.14 |
| 9.5 | Decide the PostgreSQL driver strategy (`psycopg2-binary` vs. `psycopg[binary]` v3) | Not started | |
| 9.6 | Decide target versions for `whitenoise`, `django-environ`, `Pillow`, and the `asgiref`/`sqlparse`/`tzdata` set | Not started | Must align with 9.2 |
| 9.7 | Decide whether `django-mathfilters` stays or goes | Not started | Goes if costing moves to the service layer (4.1) |
| 9.8 | Decide the dependency management approach (requirements split + lock workflow), and confirm every remaining dependency has an owner and purpose | Not started | Unblocks reproducible builds |
| 9.9 | Decide the settings module layout | Not started | Unblocks 1.5 |
| 9.10 | Decide where business logic lives (services/domain module shape) | Not started | Unblocks 4.1 |
| 9.11 | Decide whether a JSON API is needed at all, and if so which framework | Not started | Unblocks 4.15 |
| 9.12 | Decide the auth/permissions approach (Django auth views as standard, permission model shape) | Not started | Unblocks 4.5; pairs with 10.1 |
| 9.13 | Decide the frontend stack: templating approach, CSS framework/version, asset pipeline, interactivity layer, and whether an SPA is needed | Not started | Unblocks 5.4, 5.6, 5.7 |
| 9.14 | Decide the CI/CD pipeline shape beyond the Epic 1 minimum | Not started | Unblocks 6.12 |
| 9.15 | Decide error tracking and uptime monitoring tooling | Not started | Unblocks 7.2, 7.5 |
| 9.16 | Decide the backup/restore/PITR strategy — must cover **both** the host's native snapshots (fast rollback) and a portable logical dump (host replaceability) | Not started | Unblocks 3.38, 3.40, 3.44. [ADR-015](docs/decisions.md) rule 5. Note Railway offers no PITR — a PITR requirement needs tooling beyond the platform |
| 9.17 | Decide formatting/linting and testing tooling (including template linting) | Not started | Unblocks 5.8, 6.10, 6.11 |
| 9.18 | Decide the outstanding data-model questions: ingredient-line model shape, units/categories as enums vs. lookup tables, dashboard caching, connection pooling | Not started | Unblocks 3.19, 3.26, 3.42, 4.14 |
| 9.19 | Decide the tenant export format and generation mechanism | Not started | Direction fixed by [ADR-008](docs/decisions.md); tool choice open. Unblocks 14.1 |
| 9.20 | Re-confirm Spark/Databricks against a plain-Python batch alternative at this data scale, and confirm the workspace cost model | Not started | Open follow-up on [ADR-002](docs/decisions.md). Unblocks Epic 16 |

---

## Epic 10 — Requirements discovery

**Branch:** `requirements-discovery` · **Depends on:** — · **Blocks:** Epics 2, 3, 5, and the feature epics

Each task fills in [project_requirements.md](docs/project_requirements.md) and logs an ADR where a
real choice is made.

| ID | Task | Status | Notes / source |
|---|---|---|---|
| 10.1 | Define the four personas and a per-tenant role capability matrix (who can do what, who cannot) | Not started | Unblocks 2.8 |
| 10.2 | Fill in keep/change/remove and new requirements per area: dashboard, raw materials, suppliers, base recipes, products, settings/users/export | Not started | |
| 10.3 | Prioritize the feature backlog with MoSCoW | Not started | Unblocks 5.9 and feature epic sequencing |
| 10.4 | Set non-functional targets: performance, accessibility (WCAG level), device support, browser support, localization/currency | Not started | Unblocks 5.12 |
| 10.5 | Resolve the business data-semantics questions: raw-material price basis, canonical costing units, VAT representation, pricing-history versioning, which entities need soft delete/history, supplier-name uniqueness, and whether the Django admin and the in-app settings area should expose the same operations | Not started | Unblocks 3.6, 3.10, 3.16, 3.22, 3.34 |
| 10.6 | Write the explicit out-of-scope list for this round | Not started | |
| 10.7 | Identify the first real users, the deployment jurisdiction(s), any regulatory requirements beyond GDPR, and timeline pressure | Not started | Feeds 11.1 and 11.12 |

---

## Epic 11 — GDPR data inventory & policy

**Branch:** `gdpr-data-inventory` · **Depends on:** — · **Blocks:** Epics 13, 15, and any consent/erasure/audit-log code

Discovery first: the inventory and policy must exist before compliance code is written against them.
This work is not legal advice — a real legal/DPO review is a prerequisite to relying on it.

| ID | Task | Status | Notes / source |
|---|---|---|---|
| 11.1 | Complete the personal-data inventory: every category, storage location, data subject, and status | Not started | [gdpr.md](docs/gdpr.md) §1 |
| 11.2 | Document the legal basis for each inventory row, with the reasoning | Not started | §2 |
| 11.3 | Decide and document the legal basis for profile pictures | Not started | §1 — **must be resolved before Epic 13 is implemented** |
| 11.4 | Define the retention and deletion policy per data category, with deletion triggers | Not started | §5. Unblocks 3.38 |
| 11.5 | Produce a DPA template usable per tenant, with Bakery-the-product as processor and each bakery as controller | Not started | §0/§7 — [ADR-006](docs/decisions.md) |
| 11.6 | Put DPAs in place with each third-party processor: hosting provider, Databricks, object storage, email provider | Blocked | Hosting provider unknown until 12.1; Databricks until 9.20 |
| 11.7 | Scope and carry out the DPIA now that multi-tenant SaaS is confirmed | Not started | §9 — reassessment was explicitly triggered by [ADR-006](docs/decisions.md) |
| 11.8 | Define the breach notification process (who, how fast, how — 72-hour supervisory authority deadline) | Not started | §8. Feeds 8.7 |
| 11.9 | Close the data-subject-rights gaps: restriction of processing, objection, and a real erasure/anonymization strategy — including deleting the stored object from object storage, not just the DB row | Not started | §3. Access/portability is Epic 15 |
| 11.10 | Add access logging for who viewed or exported personal data | Not started | §6. Extends 2.9 |
| 11.11 | Confirm no tracking/analytics cookies exist; define the consent path if that changes | Not started | §4 |
| 11.12 | Name the point of contact for data subject requests | Not started | Depends on 10.7 |
| 11.13 | Confirm backups are encrypted at rest once a backup strategy exists | Not started | §6. Depends on 9.16 |
| 11.14 | Re-evaluate hosting residency and vendor ownership **before onboarding any tenant outside Ireland** | Not started | [ADR-013](docs/decisions.md) §7.1. The accepted US-parent transfer risk was weighed against an Irish-only market; continental EU buyers weigh EU ownership differently. EU-owned alternatives priced ~2.5–3× at decision time (Clever Cloud, Scaleway). Migration stays cheap only while ADR-004/ADR-007 hold |
| 11.15 | Confirm Railway's transfer-safeguard position (DPF certification and/or SCCs) and record it in [gdpr.md](docs/gdpr.md) §7.1 | Not started | Part of the DPA work in 12.7. §7.1 is `Open` until this lands |

---

## Epic 12 — Hosting migration

**Branch:** `stack-hosting-migration` · **Depends on:** Epic 9 · **Blocks:** Epic 7

Move the Django app and PostgreSQL off the self-hosted home server (Docker/Portainer) onto
**Railway (Hobby plan, EU West)**, chosen per [ADR-013](docs/decisions.md) from the ADR-003
shortlist. Only production is hosted — the dev/test environment is local Docker Compose
([ADR-014](docs/decisions.md)).

| ID | Task | Status | Notes / source |
|---|---|---|---|
| 12.1 | Pick the host among the three candidates — re-confirm current pricing and include the cost of a second (staging) environment — and log it as an ADR | **Done** | Railway (Hobby), 2026-08-03 — [ADR-013](docs/decisions.md). Staging cost is what drove [ADR-014](docs/decisions.md)'s local-dev decision |
| 12.2 | Provision app compute and managed PostgreSQL as separate services | Not started | [ADR-007](docs/decisions.md) |
| 12.3 | Configure the deployment to build from the repo's `Dockerfile`, not Railpack | Not started | [ADR-004](docs/decisions.md); pairs with 7.6 |
| 12.4 | Set up a single Railway environment tracking `production`; do **not** provision a persistent hosted staging environment | Not started | [ADR-014](docs/decisions.md) amends [ADR-010](docs/decisions.md) — the `main` tier runs locally instead |
| 12.5 | Enable a Railway PR environment on the `main` → `production` release PR only — not on feature PRs | Not started | [ADR-014](docs/decisions.md). No plan-tier gate on Railway; <$1/mo at a few releases a month |
| 12.6 | Migrate production data off the home server, with a verified restore on the new host | Not started | Do not decommission the old host until verified |
| 12.7 | Execute the DPA with Railway and add it as a subprocessor | Not started | Feeds 11.6. Railway is a US company — the EU region covers storage location, not processor access |
| 12.8 | Set the deployment region to **EU West (Amsterdam)** *before* creating any service, so both the app and the Postgres volume are provisioned in the EU | Not started | [ADR-013](docs/decisions.md). **Railway's default is US West** — the personal data lives in the database, so a default-region Postgres puts it in California. Volumes follow their service's region, and EU-West Metal supports volumes on Hobby (since 2025-03-14), so this is purely a sequencing requirement. Moving a volume later forces a migration **with downtime**. Confirm the region on both services after provisioning. Feeds 11.6 |
| 12.9 | Configure automated PostgreSQL backup schedules on Railway — for fast same-host rollback, **not** as the portable backup | Not started | [ADR-013](docs/decisions.md) — **not** enabled by default. Daily/weekly/monthly, combinable, no PITR. Railway's snapshots are copy-on-write volume snapshots and are **not restorable on another host** — the portable `pg_dump` in 3.44 is what covers that. Executes whatever 9.16 decides |
| 12.10 | Provide migrations + seed data for the release-PR environment, which comes up with an empty database | Not started | [ADR-014](docs/decisions.md) — Railway PR environments clone services and config but not volume data, so without this the preview is an unusable login page |

---

## Epic 13 — Media storage for user uploads

**Branch:** `feature-media-storage` · **Depends on:** Epics 3, 11

Product photos and user profile pictures, stored in S3-compatible object storage (Cloudflare R2) via
`django-storages` — decoupled from wherever the app is hosted, per [ADR-005](docs/decisions.md).

| ID | Task | Status | Notes / source |
|---|---|---|---|
| 13.1 | Add `django-storages[s3]` and `boto3` to the dependency set | Not started | [ADR-005](docs/decisions.md) |
| 13.2 | Provision the R2 bucket, optionally fronted by a custom domain/CDN | Not started | |
| 13.3 | Configure `django-storages` against the R2 endpoint, with credentials from environment variables | Not started | Pairs with 2.5 |
| 13.4 | Add a `photo` field to `Product` | Not started | Schema change — sequence with 3.18 |
| 13.5 | Add a `Profile` model with a one-to-one to Django's `User` and a photo field, avoiding a custom-user-model migration | Not started | Needs the tenant FK from 3.2 |
| 13.6 | Store only the object key/URL in PostgreSQL — the binary never goes in the database | Not started | |
| 13.7 | Validate uploaded file type and size in a real ModelForm | Not started | Pairs with 4.9 |
| 13.8 | Build the upload/preview UI with an empty-state placeholder | Not started | Pairs with 5.11 |
| 13.9 | Delete the stored object from the bucket on account deletion or an erasure request | Not started | [gdpr.md](docs/gdpr.md) §3 — a DB-row delete alone is not compliance |
| 13.10 | Do not ship profile pictures until their legal basis is decided | Blocked | 11.3 must land first; R2 processor entry via 11.6 |

---

## Epic 14 — Tenant full data export

**Branch:** `feature-tenant-data-export` · **Depends on:** Epic 3

Given a tenant, export all of that tenant's rows across every tenant-scoped table in a portable,
DBMS-agnostic format, so a departing bakery can take its data elsewhere ([ADR-008](docs/decisions.md)).
This is a product feature, not the GDPR portability mechanism (that's Epic 15).

| ID | Task | Status | Notes / source |
|---|---|---|---|
| 14.1 | Implement the agreed export format — portable ANSI SQL (`CREATE TABLE`/`INSERT`) or a per-table CSV bundle — explicitly **not** a Postgres-specific `pg_dump` | Blocked | Format/tool choice `Open` — 9.19 |
| 14.2 | Build the management command/service that walks every tenant-scoped table for a given tenant | Not started | Needs 3.1/3.2 |
| 14.3 | Include a relationship manifest and import instructions so the export is usable without this app | Not started | |
| 14.4 | Gate who can trigger an export, and audit-log every export run | Not started | Pairs with 2.9 |
| 14.5 | Test that an export contains every one of that tenant's rows and none of any other tenant's | Not started | Pairs with 6.9 |

---

## Epic 15 — GDPR personal-data export

**Branch:** `feature-gdpr-data-export` · **Depends on:** Epic 11

A second, separate export scoped to **one data subject's** personal data across models — the actual
Article 20 portability fix, distinct from both the bulk admin CSV export and the tenant-wide export
([ADR-009](docs/decisions.md)).

| ID | Task | Status | Notes / source |
|---|---|---|---|
| 15.1 | Define exactly which fields across which models constitute one data subject's personal data | Blocked | Needs the completed inventory — 11.1 |
| 15.2 | Build the subject-scoped export (CSV or a small CSV bundle) as its own view/service | Not started | |
| 15.3 | Gate it to the requesting user's own data, or to an admin acting on a data subject's behalf | Not started | |
| 15.4 | Audit-log every personal-data export | Not started | Pairs with 11.10 |
| 15.5 | Leave the existing per-entity bulk CSV exports unchanged as an admin/operational feature | Not started | [ADR-009](docs/decisions.md) — explicitly not the compliance mechanism |
| 15.6 | Update [gdpr.md](docs/gdpr.md) §3 Portability from `Open` to implemented when this ships | Not started | |

---

## Epic 16 — AI insights & alerts service

**Branch:** `feature-ai-insights-service` · **Depends on:** Epics 9, 11

An external batch-processing service, triggered by app events, that reads app data and returns margin
alerts and analytics ([ADR-002](docs/decisions.md) — direction proposed, cost/scale still open).

| ID | Task | Status | Notes / source |
|---|---|---|---|
| 16.1 | Confirm the processing engine and workspace cost model before any spend | Blocked | 9.20 — Community Edition does not support API-triggered jobs |
| 16.2 | Define the API contract: which app events trigger the service, what it reads, what it returns | Not started | [tech_stack.md](docs/tech_stack.md) marks the exact contract `Open` |
| 16.3 | Define and enforce the data scope shared with the service — limited to product/pricing/recipe data, excluding user accounts and supplier contact personal data unless proven necessary | Not started | [gdpr.md](docs/gdpr.md) §7 |
| 16.4 | Put a DPA in place with the analytics provider before any real data flows | Blocked | Feeds 11.6 |
| 16.5 | Define the margin-alert rules and how alerts reach users | Not started | Needs 10.3 prioritization |
| 16.6 | Surface the analytics dashboard in the app | Not started | |
| 16.7 | Ensure everything the service reads or writes is tenant-scoped | Not started | [ADR-008](docs/decisions.md) |

---

## Decision → task coverage

Every `Accepted`/`Decided` entry in `docs/` must map to at least one task above. Add a row here when
a new ADR lands, along with the tasks it creates.

| Decision | Tasks implementing it |
|---|---|
| [ADR-002](docs/decisions.md) — Spark/Databricks insights service (Proposed, cost open) | 9.20, 16.1–16.7 |
| [ADR-003](docs/decisions.md) — Hosting narrowed to Railway/Render/DigitalOcean | 12.1 |
| [ADR-004](docs/decisions.md) — Deploy via the custom Dockerfile, not a buildpack | 1.11, 7.6, 12.3 |
| [ADR-005](docs/decisions.md) — Media in S3-compatible object storage (Cloudflare R2) | 2.5, 2.13, 3.18, 4.9, 5.11, 13.1–13.10 |
| [ADR-006](docs/decisions.md) — Multi-tenant SaaS | 2.8, 3.1–3.4, 11.5, 11.7 |
| [ADR-007](docs/decisions.md) — App and database always separate services | 3.39, 7.7, 12.2 |
| [ADR-008](docs/decisions.md) — Shared DB with row-level tenant isolation + tenant export | 3.2, 3.3, 4.6, 6.9, 14.1–14.5, 16.7 |
| [ADR-009](docs/decisions.md) — Dedicated GDPR personal-data export | 15.1–15.6 |
| [ADR-010](docs/decisions.md) — `main` integration / `production` deploy, tagged releases | 1.8, 1.9, 1.10, 6.13, 7.12, 7.15, 8.8, 12.4 |
| [ADR-011](docs/decisions.md) — Minimal CI in Epic 1, full pipeline in Epic 6 | 1.11, 6.12 |
| [ADR-013](docs/decisions.md) — Railway (Hobby, EU West) as the hosting platform | 12.1 ✅, 12.2, 12.3, 12.6, 12.7, 12.8, 12.9, 11.14, 11.15 |
| [project_requirements.md](docs/project_requirements.md) — Ireland-first market, then wider EU | 11.8, 11.14, 12.8 |
| [ADR-015](docs/decisions.md) — Host portability as a standing design constraint | 1.5, 3.44–3.49, 7.6, 7.7, 7.9, 7.10, 7.11, 7.13, 7.17, 7.18, 8.9, 9.3, 9.16 |
| [ADR-014](docs/decisions.md) — Local Docker dev/test env, no hosted staging, release-PR preview | 1.12, 6.15, 12.4, 12.5, 12.10 |
| [tech_stack.md](docs/tech_stack.md) — static assets stay on whitenoise (no change) | 7.16 |
| [project_requirements.md](docs/project_requirements.md) — bulk CSV exports stay an admin feature | 15.5 |

## Highest-risk items

These are the reasons for the current epic ordering. Each one is already a task — this table exists
so the risk isn't lost among the ~140 tasks above.

| Risk | Fixed by |
|---|---|
| Plaintext passwords printed to logs on failed login | 2.10 |
| Hardcoded `SECRET_KEY`, DB credentials, and `DEBUG = True` | 2.1, 2.2 |
| Access control enforced in templates instead of views | 2.6, 2.7, 2.8 |
| No tenant isolation in a confirmed multi-tenant product | 3.3, 4.6, 6.9 |
| Generated files committed to the repository | 1.1, 1.2 |
| Known functional defects (e.g. user delete removes the wrong model) | 6.7, plus the Epic 4 view rework |
| No automated quality gate before merge or deploy | 1.11, 6.12, 6.13 |
| Inconsistent runtime configuration across Docker, Heroku, and local | 1.5, 7.7, 7.8, 7.9 |

## Definition of "production ready"

The exit criteria for this backlog. Bakery is production-ready only when all of these hold:

- [ ] No secrets in source control; all configuration comes from the environment
- [ ] Supported Python and Django versions, with pinned, reproducible dependencies
- [ ] Full environment separation (local / test / staging / production)
- [ ] Every business action protected by real authentication and per-tenant authorization
- [ ] Tenant isolation enforced at the query layer and proven by tests
- [ ] Safe, reversible, tested database migrations
- [ ] Backup and restore strategy documented **and** drilled
- [ ] Automated tests and CI/CD gating every merge and deploy
- [ ] Logging, monitoring, and error tracking enabled
- [ ] Deployment and rollback documented and repeatable
- [ ] GDPR obligations met for the personal data actually held (inventory, legal basis, retention, subject rights)
