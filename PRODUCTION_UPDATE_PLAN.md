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
| [17](#epic-17--batch--lot-traceability) | Batch & lot traceability | `feature-traceability` | Epics 3, 9, 10 |
| [18](#epic-18--allergen-data) | Allergen data | `feature-allergen-data` | Epics 3, 17 |

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
| 2.8 | Implement role-based permissions for **Owner / Staff / Read-only**, scoped **per tenant** rather than globally | **Unblocked** | [ADR-020](docs/decisions.md) — three roles, not four; Manager deferred. Role lives on the membership record from 3.58. Capability matrix in [project_requirements.md](docs/project_requirements.md) |
| 2.9 | Add audit logging for user management and destructive actions | Not started | Extended by 11.10 (logging who viewed/exported personal data) |

### Input and data protection

| ID | Task | Status | Notes / source |
|---|---|---|---|
| 2.10 | Replace the `print()` login diagnostics in `accounts/views.py` with structured logging that never records passwords | Not started | **Highest-priority security defect** — [gdpr.md](docs/gdpr.md) §6 |
| 2.11 | Validate and sanitize all form input server-side | Not started | Form-level business validation is 4.7 |
| 2.12 | Add server-side authorization to every export endpoint | Not started | |
| 2.13 | Remove the broken leftover `MEDIA_ROOT` path (`bluebiulding/media`) | Not started | Real media handling is Epic 13 |
| 2.14 | Confirm encryption in transit (HTTPS enforced end-to-end) once the settings work lands | Not started | GDPR Art. 32 — [gdpr.md](docs/gdpr.md) §6 |
| 2.15 | Restrict the Django admin to superusers, keep it out of all tenant-facing navigation, and log its access to personal data | Not started | [ADR-019](docs/decisions.md) — it is deliberately a **cross-tenant** support surface, which is what makes it useful and what makes it dangerous. `ModelAdmin` does **not** apply the tenant-scoped managers from 3.3/3.55. Feeds 11.10 |
| 2.16 | Express every permission check as a named capability (`can_manage_users`, `can_edit_pricing`, `can_record_receipt`), never as `role == "owner"` | Not started | [ADR-020](docs/decisions.md). Costs nothing with three roles and is what keeps adding Manager a table row instead of a rewrite |

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
| 3.4 | Scope user roles/permissions per tenant in the data model | Not started | Pairs with 2.8. Concrete shape decided by [ADR-020](docs/decisions.md): a membership record (user × bakery × role) — built in 3.58 |

### Supplier

| ID | Task | Status | Notes / source |
|---|---|---|---|
| 3.5 | Replace supplier name as primary key with a generated numeric or UUID primary key | Not started | |
| 3.6 | Enforce supplier name unique **per tenant**, over non-archived rows only, via a partial unique index | **Unblocked** | [ADR-019](docs/decisions.md). Not globally unique — two bakeries may both buy from "Odlums". Partial index because a plain composite constraint would let an archived row block that name forever. **Sequenced after 3.2** (needs the tenant FK) |
| 3.7 | Change phone number from `IntegerField` to a string field | Not started | |
| 3.8 | Add optional address, tax/business identifier, active flag, and timestamps | Not started | |

### Raw material

| ID | Task | Status | Notes / source |
|---|---|---|---|
| 3.9 | Change `quantity` from `CharField` to `DecimalField` | Not started | |
| 3.10 | Implement the agreed price semantics: `purchase_price` + `pack_quantity` + `purchase_unit`, as the invoice states them — cost per canonical unit derived at cost time, never persisted | **Unblocked** | [ADR-018](docs/decisions.md). Derived-not-stored is 3.17. The same three fields are what an ADR-017 goods-receipt line records, so 17.1 and this task must agree |
| 3.11 | Add normalized unit handling for cost calculations: convert any purchase unit to its canonical unit (kg / l / each) via the conversion factor in the unit reference table | **Unblocked** | [ADR-018](docs/decisions.md). Depends on 3.10 and the unit table in 3.52 |
| 3.12 | Add SKU/code uniqueness rules where appropriate | Not started | |
| 3.13 | Add active/inactive status instead of hard deletes where business history matters | Not started | No longer a judgment call for `RawMaterial`: anything referenced by a traceability record can never be hard-deleted ([ADR-017](docs/decisions.md)) — enforced in 17.6 |

### Base recipe and product

| ID | Task | Status | Notes / source |
|---|---|---|---|
| 3.14 | Standardize yield, unit, and cost fields across base recipes and products | Not started | |
| 3.15 | Make VAT representation consistent: all stored money is **net (ex-VAT)**; the product references a VAT rate **code**, not a percentage; VAT is applied only at display/sale | **Unblocked** | [ADR-018](docs/decisions.md). The rate table itself is 3.53; which rate a product gets is a tax question — 10.13 |
| 3.16 | Version sale pricing history: dated `ProductPrice` rows (product, net price, `valid_from`), current price = latest row whose `valid_from` has passed | **Unblocked** | [ADR-018](docs/decisions.md). **Input** price history is *not* built here — it comes free from ADR-017 goods receipts (17.12) |
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
| 3.22 | Add soft delete / archive to `Supplier`, `RawMaterial`, `Product`, and `Base_recipes`; leave ingredient lines hard-deletable | **Unblocked** | [ADR-019](docs/decisions.md) — the rule is "anything referenced by a record that outlives it": traceability for the first two, outbound records + dated prices for `Product`, production runs for `Base_recipes`. Ingredient lines are meaningful only inside their parent |
| 3.23 | Add `db_index=True` or explicit indexes on common filter/join paths | Not started | |
| 3.24 | Add unique and check constraints wherever a business rule exists | Not started | |
| 3.25 | Use `Decimal` consistently for money and quantities (schema and application code) | Not started | Removes the `float()` math currently in `control/views.py` — pairs with 4.1 |
| 3.26 | Standardize units and categories via controlled enums or lookup/reference tables | Partly unblocked | **Units: decided** — a lookup table, because a conversion factor is data an enum cannot carry ([ADR-018](docs/decisions.md)); built in 3.52. **Categories: still `Open`** — 9.18 |

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
| 3.34 | Define the canonical units used for costing | **Done (decided)** | 2026-08-06 — **kilogram / litre / each**, one per dimension ([ADR-018](docs/decisions.md)). Implementation is 3.11/3.52 |
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

### Money, units, and price history (ADR-018)

| ID | Task | Status | Notes / source |
|---|---|---|---|
| 3.50 | Set the decimal precision for quantities and money in the schema: quantities at least `Decimal(12,4)` (`12,6` safer), money carried beyond 2 dp internally | Not started | [ADR-018](docs/decisions.md). **This is the price of kg/l canonical units** — 7 g of yeast is `0.007 kg`, a pinch of spice `0.0005 kg`. Too little scale silently truncates small-ingredient cost to zero |
| 3.51 | Define, document, and test the rounding rule: which direction, and at which boundary — rounding to 2 dp happens **only at presentation**, never in stored data or intermediate math | Not started | [ADR-018](docs/decisions.md). Must not be inherited from Python's default behaviour by accident. Tested in 6.16 |
| 3.52 | Build the unit reference table: canonical unit per dimension plus a conversion factor per purchase unit, so adding "sack" or "dozen" is data entry rather than a migration | Not started | [ADR-018](docs/decisions.md). Resolves the units half of 3.26/9.18. Seed data feeds 3.37 and 10.10 |
| 3.53 | Build the dated VAT-rate reference table (`code`, `percent`, `valid_from`, `valid_to`) and reference it by code from products | Not started | [ADR-018](docs/decisions.md). Dated so a statutory rate change doesn't retroactively rewrite historical margins |
| 3.54 | Backfill existing `RawMaterial` prices into the purchase-price/pack-quantity/purchase-unit model — a per-row human-judgment exercise, **not** an automatic migration | Not started | [ADR-018](docs/decisions.md). Today's values mean whatever the person typing them assumed. Must complete before the legacy fields are dropped in 3.32 |

### Deletion, identity, and roles in the schema (ADR-019, ADR-020)

| ID | Task | Status | Notes / source |
|---|---|---|---|
| 3.55 | Combine tenant scoping and archived-state filtering into a **single** base manager, applied by default — not two filters applied ad hoc per query | Not started | [ADR-019](docs/decisions.md). Two orthogonal correctness-critical filters now exist: a query missing the archived filter resurrects deleted data, one missing the tenant filter leaks across tenants. Extends 3.3; tested in 6.18 |
| 3.56 | Give archived records a way back: an un-archive path and a way to see archived rows | Not started | [ADR-019](docs/decisions.md). A soft delete with no un-delete is just a confusing delete. Pairs with 5.x — the UI must say *archive* where it archives |
| 3.57 | Assign a role to every existing user as part of the membership migration — a human decision per user, not a default | Not started | [ADR-020](docs/decisions.md). Nobody in the current database has a role |
| 3.58 | Add the tenant membership model (user × bakery × role) as the home of role assignment | Not started | [ADR-020](docs/decisions.md). Django's global `Group` cannot express "Owner of bakery A". Implements 3.4 |

### Recipe composition and cost provenance (ADR-022)

| ID | Task | Status | Notes / source |
|---|---|---|---|
| 3.59 | Let an ingredient line reference **either** a raw material or a base recipe, and reject cycles at save time — a base recipe must not contain itself directly or transitively | Not started | [ADR-022](docs/decisions.md). **Cycle prevention is the critical part**: nothing in the current schema stops it, and a cycle makes costing loop forever. Depth guard in the service layer is 4.16; the test is 6.20 |
| 3.60 | Make `recipe_yeld` a real numeric quantity with a unit from the 3.52 unit table | Not started | [ADR-022](docs/decisions.md). Cost *per unit of yield* is what a parent recipe consumes, so a loose yield field can no longer work. Extends 3.14 |
| 3.61 | Derive a raw material's current cost from its latest goods receipt — most recent by **receipt date**, ties broken by creation time — with a manual price retained as a labelled estimate | Not started | [ADR-022](docs/decisions.md). Receipt-date ordering (not entry date) is what makes a late-entered back-dated delivery behave correctly. Needs 17.1 |
| 3.62 | Model cost **provenance** (receipt-derived vs. estimated) as data the service layer returns alongside the figure, not as a UI afterthought | Not started | [ADR-022](docs/decisions.md). Retrofitting provenance into a bare `Decimal` later is painful. Surfaced by 4.17 and in exports |
| 3.63 | Stop treating `RawMaterial`'s supplier FK as the definition of who supplies a material: the real supply relationship lives on the goods receipt, so the FK becomes at most an optional *preferred supplier* | Not started | [ADR-024](docs/decisions.md) — required by supplier price comparison being a **Must**. With a single FK, a comparison view has exactly one row per material and shows nothing. Pairs with 17.1; view is 5.21 |

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
| 4.16 | Implement recursive costing through base-recipe ingredient lines, with an explicit depth guard | Not started | [ADR-022](docs/decisions.md). The schema-level cycle rejection is 3.59; the depth guard is defence in depth for data that predates it. Tested in 6.20 |
| 4.17 | Return cost **provenance** with every costing result, so callers can distinguish a receipt-derived figure from an estimate | Not started | [ADR-022](docs/decisions.md), backed by 3.62. Consumed by the dashboard (5.18) and the exports |
| 4.18 | Implement the "stale price" rule once its threshold is set, as a service-layer concern rather than a template condition | Blocked | Threshold `Open` — 10.16. [ADR-023](docs/decisions.md) |

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
| 5.9 | Build real search/filter flows across raw materials, suppliers and products | **Unblocked** | [ADR-024](docs/decisions.md) rates this a **Must**, so this resolves to *build it*, not *remove the inputs*. Dead inputs that look functional are worse than no inputs |
| 5.10 | Improve forms, validation errors, empty states, and destructive-action confirmations | Not started | |
| 5.11 | Add image upload/preview UI with a clear empty-state placeholder | Not started | Owned by 13.8 |
| 5.12 | Meet **WCAG 2.2 Level A**: alt text, real `<label>` on every input, no keyboard traps, nothing conveyed by colour alone | **Unblocked** | [ADR-021](docs/decisions.md). Level A is the agreed target; semantic HTML and real labels here keep the remaining distance to AA small if the 10.15 revisit trigger fires |
| 5.13 | Make data tables usable on mobile and tablet — a deliberate strategy (horizontal scroll containers or card layouts), not overflow | Not started | [ADR-021](docs/decisions.md). Costing/margin tables are inherently wide; goods receipts (Epic 17) get recorded on a phone at the delivery door |
| 5.14 | Record the agreed performance budget (p95 < 500 ms pages, < 2 s dashboard, ~10 concurrent users/tenant) as a documented target, and verify it once monitoring exists | Not started | [ADR-021](docs/decisions.md). Deliberately **not** a CI gate — Railway Hobby shares CPU. Verifiable via 7.1/3.43 |
| 5.15 | Route all display text through Django's translation machinery (`gettext` / `{% translate %}`) during the rewrite | Not started | [ADR-021](docs/decisions.md). Ships English only, but makes the ADR-016 expansion trigger a locale file rather than a template audit |
| 5.16 | Remove every hardcoded `€` and format all money through a single currency formatter | Not started | [ADR-021](docs/decisions.md). Pairs with the presentation-boundary rounding rule in 3.51 — both belong in the same formatter |
| 5.17 | Verify against the agreed browser matrix: current and previous major version of Chrome, Firefox, Safari, Edge | Not started | [ADR-021](docs/decisions.md). No IE11, no legacy Edge |
| 5.18 | Rebuild the dashboard as an overview page: summary strip (product count, average margin, materials with no/stale pricing), worst-margin products, recent input price movements — moving the full product list to its own page | Not started | [ADR-023](docs/decisions.md). **Depends on Epic 3, not just this epic** — price movements and staleness need ADR-018's dated prices and ADR-022's receipts to exist. Runs against the p95 < 2 s budget in [ADR-021](docs/decisions.md) |
| 5.19 | Build the tenant self-administration settings area: user invite/remove and role assignment, bakery details, reference data, exports — Owner-writable, Read-only limited to exports | Not started | [ADR-023](docs/decisions.md). **Replaces** the broken user-delete view rather than patching it. Needs the roles from 2.8/3.58 and email from 9.22 |
| 5.20 | Show cost provenance in the UI: mark estimated figures distinctly from receipt-derived ones | Not started | [ADR-022](docs/decisions.md), backed by 4.17. A margin from a guess and one from an invoice are not the same claim |
| 5.21 | Build the supplier price comparison view for a given raw material — who supplied it, at what price per canonical unit, and when | Not started | [ADR-024](docs/decisions.md) rates it a **Must**. Reads goods-receipt data (Epic 17) and needs 3.63; sparse until receipts accumulate across more than one supplier, which is expected rather than a defect |

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
| 6.16 | Test unit conversion, decimal precision, and the rounding rule end to end: a gram-scale ingredient must not cost zero, and a known basket must produce an exactly-specified cost and margin | Not started | [ADR-018](docs/decisions.md), covering 3.11, 3.50, 3.51. With kg/l canonical units, precision loss on small ingredients is the realistic failure mode — assert on exact `Decimal` values, never on floats |
| 6.17 | Test that VAT is applied only at presentation, and that changing a VAT rate's `valid_from` does not alter historical figures | Not started | [ADR-018](docs/decisions.md), covering 3.15, 3.53 |
| 6.18 | Test the tenant + archived filter pair together: an archived row never appears in normal queries, and no query returns another tenant's rows — including archived ones | Not started | [ADR-019](docs/decisions.md), covering 3.55. The two filters are independent failure modes; test both, and their combination |
| 6.19 | Test the three-role capability matrix: Read-only cannot write anything, Staff cannot manage users or pricing, Owner cannot reach another tenant | Not started | [ADR-020](docs/decisions.md), covering 2.8, 2.16. Extends 6.4 |
| 6.20 | Test recursive costing: a product costing through a base recipe returns the right figure, and a self-referencing or transitively cyclic recipe is **rejected** rather than looping | Not started | [ADR-022](docs/decisions.md), covering 3.59 and 4.16. The cycle case is the one that hangs a request if it's missed |
| 6.21 | Test cost provenance: a receipt-derived figure and an estimated one are distinguishable, and recording a back-dated receipt updates the current cost correctly by receipt date | Not started | [ADR-022](docs/decisions.md), covering 3.61, 3.62, 4.17 |

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
| 9.18 | Decide the outstanding data-model questions: ingredient-line model shape, categories as enums vs. lookup tables, dashboard caching, connection pooling | Not started | Unblocks 3.19, 3.26, 3.42, 4.14. **Narrowed twice:** units are a lookup table ([ADR-018](docs/decisions.md)); and since [ADR-022](docs/decisions.md) gives both line models a typed *component* reference as well as a typed parent, they become structurally identical — a single shared ingredient-line model is now strongly indicated. Dashboard caching gained urgency from the [ADR-023](docs/decisions.md) overview page |
| 9.19 | Decide the tenant export format and generation mechanism | Not started | Direction fixed by [ADR-008](docs/decisions.md); tool choice open. Unblocks 14.1 |
| 9.20 | Re-confirm Spark/Databricks against a plain-Python batch alternative at this data scale, and confirm the workspace cost model | Not started | Open follow-up on [ADR-002](docs/decisions.md). Unblocks Epic 16 |
| 9.21 | Decide the traceability data-model shape: goods-receipt/batch/production-run entities and their relationships, internal lot-code generation strategy, and whether stock/quantity-on-hand comes along as a derived by-product or is deliberately excluded | Not started | [ADR-017](docs/decisions.md) fixes the direction; the entity shape is open. **Unblocks 17.1–17.4.** Review against 9.18's ingredient-line decision — both touch the same tables. **Stock is settled as a `Could`** ([ADR-024](docs/decisions.md)): design the entities so quantity-on-hand *could* be derived later, without the app claiming to track stock now |
| 9.22 | Choose an email provider and integration approach — required before user invitations can ship | Not started | Created by [ADR-023](docs/decisions.md): the app sends no email today, and the settings area's invite flow needs it. Credentials from environment variables (2.1); DPA via 11.6; turns the hypothetical email row in [gdpr.md](docs/gdpr.md) §7 into a real one |

---

## Epic 10 — Requirements discovery

**Branch:** `requirements-discovery` · **Depends on:** — · **Blocks:** Epics 2, 3, 5, and the feature epics

Each task fills in [project_requirements.md](docs/project_requirements.md) and logs an ADR where a
real choice is made.

| ID | Task | Status | Notes / source |
|---|---|---|---|
| 10.1 | Define the personas and a per-tenant role capability matrix (who can do what, who cannot) | **Done** | 2026-08-06 — **three** roles, not four: Owner / Staff / Read-only, on a membership record ([ADR-020](docs/decisions.md)). Manager deferred. Matrix in [project_requirements.md](docs/project_requirements.md). Unblocked 2.8, 3.4 |
| 10.2 | Fill in keep/change/remove and new requirements per area: dashboard, raw materials, suppliers, base recipes, products, settings/users/export | **Done** | 2026-08-06 — all six areas filled in via [ADR-022](docs/decisions.md) (receipts drive raw-material cost; ingredient lines accept base recipes) and [ADR-023](docs/decisions.md) (dashboard overview; tenant self-administration). Created 3.59–3.62, 4.16–4.18, 5.18–5.20, 6.20, 6.21, 9.22, 10.16, 10.17 |
| 10.3 | Prioritize the feature backlog with MoSCoW | **Done** | 2026-08-06 — full pass logged as [ADR-024](docs/decisions.md). **Must:** multi-tenancy, traceability, search, supplier comparison, user/role management (merged into 5.19/2.8/3.58/9.22). **Should:** both exports, trend reporting, allergen data (**new Epic 18**). **Could:** product photos, stock levels, AI insights (re-scope first). **Won't this round:** profile pictures, self-service registration, billing. Unblocked 5.9; created 3.63, 5.21, Epic 18 |
| 10.4 | Set non-functional targets: performance, accessibility (WCAG level), device support, browser support, localization/currency | **Done** | 2026-08-06 — [ADR-021](docs/decisions.md): p95 500 ms/2 s, **WCAG 2.2 Level A**, responsive + evergreen browsers, English/€ but translation-ready. Unblocked 5.12; created 5.14–5.17 and the 10.15 revisit trigger |
| 10.5 | Resolve the business data-semantics questions: raw-material price basis, canonical costing units, VAT representation, pricing-history versioning, which entities need soft delete/history, supplier-name uniqueness, and whether the Django admin and the in-app settings area should expose the same operations | **Done** | 2026-08-06 — all seven closed: four by [ADR-018](docs/decisions.md) (price basis, canonical units, VAT, price history), three by [ADR-019](docs/decisions.md) (soft-delete scope, per-tenant supplier uniqueness, admin surface). Unblocked 3.6, 3.10, 3.11, 3.15, 3.16, 3.22, 3.34 |
| 10.6 | Write the explicit out-of-scope list for this round | **Done** | 2026-08-06 — table in [project_requirements.md](docs/project_requirements.md) "Out of scope", completed once the MoSCoW pass (10.3) landed. Covers billing, plan gating, profile pictures, self-service registration, stock tracking, HACCP/temperature logs/recall workflows/mass-balance, and hosted staging |
| 10.7 | Identify the first real users, the deployment jurisdiction(s), any regulatory requirements beyond GDPR, and timeline pressure | **Done** | 2026-08-06 — one Irish pilot bakery, free pilot, no deadline ([ADR-016](docs/decisions.md)); jurisdiction Ireland/EU (already settled by [ADR-013](docs/decisions.md)); regulatory: batch/lot traceability in scope ([ADR-017](docs/decisions.md)). Feeds 11.1, 11.12, and Epic 17 |
| 10.8 | Confirm the traceability regulatory floor against FSAI guidance for a bakery: what one-step-back/one-step-forward actually requires in practice, and what granularity of outbound record is expected for direct-to-consumer sales | Not started | [ADR-017](docs/decisions.md). **Blocks Epic 17** — the scope is set in principle but not verified against the regulator's own guidance |
| 10.9 | Decide the food-law retention floor for traceability records, and reconcile it with the GDPR retention policy where a record names a supplier contact | Not started | [ADR-017](docs/decisions.md). Pairs with 11.4; feeds [gdpr.md](docs/gdpr.md) §5 and 17.9 |
| 10.10 | Decide tenant onboarding mechanics: self-service signup vs. manual provisioning, who creates the first admin user, what seed/reference data a new tenant starts with | Mostly resolved | [ADR-024](docs/decisions.md): **manual provisioning by the project owner**, first Owner created with the tenant, staff via Owner invitations ([ADR-023](docs/decisions.md)); public signup is `Won't (this round)`. What's left is the **seed/reference data** a new tenant starts with — pairs with 3.37, 3.52, 3.53, 10.17 and 12.10 |
| 10.11 | Decide which EU countries follow Ireland and on what trigger, then re-run the localization, currency, and hosting-residency questions | Not started | Left `Open` by [ADR-016](docs/decisions.md). Pairs with 10.4 (localization) and 11.14 (residency) |
| 10.12 | Confirm the allergen scope against FSAI/FIC guidance — the 14 declarable allergens, and what a costing tool records vs. what belongs on a label | **In scope, priority set** | [ADR-024](docs/decisions.md) rates allergen data a **Should** — now **Epic 18**. What remains here is the regulatory scope check that unblocks 18.1/18.2/18.4 |
| 10.13 | Determine which Irish VAT rate applies to which product category (bread vs. flour confectionery vs. other), and seed the rate table accordingly | Not started | A **tax** question, not an engineering one — [ADR-018](docs/decisions.md). The schema must let a tenant set it per product; do **not** ship guessed assignments. Feeds 3.53 |
| 10.14 | Decide whether one person may hold memberships in several tenants in the product UI (e.g. an accountant serving three bakeries) | Not started | Left `Open` by [ADR-020](docs/decisions.md) — the membership model already supports it; whether it is *offered* is a product choice, and it changes login/tenant-switching UX |
| 10.15 | Re-evaluate the accessibility target (Level A → AA) before EU expansion, or on the first tenant/buyer who needs it | Not started | [ADR-021](docs/decisions.md) — Level A excludes AA's contrast ratios, focus visibility, consistent navigation and error suggestions, which is what procurement and the European Accessibility Act point at. Same trigger point as 10.11 and 11.14 |
| 10.16 | Define what makes a price "stale" — how old a raw-material price must be before the dashboard flags it | Not started | [ADR-023](docs/decisions.md). Shipping a warning badge on an arbitrary threshold trains users to ignore it. Unblocks 4.18 |
| 10.17 | Decide which reference data a tenant may edit: VAT rates and categories are safe, **unit conversion factors are not** — a wrong factor silently corrupts every dependent cost figure with no error surfaced | Not started | [ADR-023](docs/decisions.md). Likely system-managed units with a tenant-selectable subset, but that is a decision, not an assumption. Feeds 3.52 and 5.19 |

---

## Epic 11 — GDPR data inventory & policy

**Branch:** `gdpr-data-inventory` · **Depends on:** — · **Blocks:** Epics 13, 15, and any consent/erasure/audit-log code

Discovery first: the inventory and policy must exist before compliance code is written against them.
This work is not legal advice — a real legal/DPO review is a prerequisite to relying on it.

| ID | Task | Status | Notes / source |
|---|---|---|---|
| 11.1 | Complete the personal-data inventory: every category, storage location, data subject, and status | Not started | [gdpr.md](docs/gdpr.md) §1 |
| 11.2 | Document the legal basis for each inventory row, with the reasoning | Not started | §2 |
| 11.3 | Decide and document the legal basis for profile pictures | Not started | §1 — **no longer on the critical path**: [ADR-024](docs/decisions.md) defers profile pictures out of this round. Still required before that feature ever ships |
| 11.4 | Define the retention and deletion policy per data category, with deletion triggers | Not started | §5. Unblocks 3.38. **Must be written per *field* for traceability data** — the food-law floor from 10.9 is not ours to choose, so the lot code and quantities are retained by law while the supplier contact's name may not need to be ([ADR-017](docs/decisions.md)) |
| 11.5 | Produce a DPA template usable per tenant, with Bakery-the-product as processor and each bakery as controller | Not started | §0/§7 — [ADR-006](docs/decisions.md) |
| 11.6 | Put DPAs in place with each third-party processor: hosting provider, Databricks, object storage, email provider | Blocked | Hosting provider resolved (12.1 ✅ Railway — execute via 12.7); Databricks blocked on 9.20; **email provider now a real processor, not hypothetical** — [ADR-023](docs/decisions.md), choice in 9.22 |
| 11.7 | Scope and carry out the DPIA now that multi-tenant SaaS is confirmed | Not started | §9 — reassessment was explicitly triggered by [ADR-006](docs/decisions.md). Include [ADR-017](docs/decisions.md)'s new angle: production runs record *which staff member* ran which batch, retained for years by legal obligation — that is employee activity data, and should be assessed deliberately rather than waved through as "just traceability" |
| 11.8 | Define the breach notification process (who, how fast, how — 72-hour supervisory authority deadline) | Not started | §8. Feeds 8.7 |
| 11.9 | Close the data-subject-rights gaps: restriction of processing, objection, and a real erasure/anonymization strategy — including deleting the stored object from object storage, not just the DB row | Not started | §3. Access/portability is Epic 15. **Erasure now has a hard limit:** a traceability record inside its retention window cannot be deleted — the strategy must cover anonymizing personal fields while keeping the trace intact, plus a documented refusal-with-reason path. Settle this **before** Epic 17 ships, not during a request |
| 11.10 | Add access logging for who viewed or exported personal data | Not started | §6. Extends 2.9 |
| 11.11 | Confirm no tracking/analytics cookies exist; define the consent path if that changes | Not started | §4 |
| 11.12 | Name the point of contact for data subject requests | Not started | 10.7 ✅ narrowed it: phase 1 has one tenant, so the controller-side contact is the pilot bakery and the processor-side contact is the project owner ([ADR-016](docs/decisions.md)). Still needs naming for real |
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
| 13.10 | Do not ship profile pictures until their legal basis is decided | **Deferred out of this round** | [ADR-024](docs/decisions.md) rates profile pictures **Won't (this round)** — deferred, not rejected. This takes 11.3 off the critical path. 13.5 and 13.9's profile-picture half go with it; Epic 13 narrows to **product photos only** |

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
| 16.1 | Confirm the processing engine and workspace cost model before any spend | Blocked | 9.20 — Community Edition does not support API-triggered jobs. **The bar has moved:** [ADR-024](docs/decisions.md) makes a scheduled query over [ADR-018](docs/decisions.md)'s dated prices the null hypothesis Spark has to beat, not the fallback |
| 16.2 | Define the API contract: which app events trigger the service, what it reads, what it returns | Not started | [tech_stack.md](docs/tech_stack.md) marks the exact contract `Open` |
| 16.3 | Define and enforce the data scope shared with the service — limited to product/pricing/recipe data, excluding user accounts and supplier contact personal data unless proven necessary | Not started | [gdpr.md](docs/gdpr.md) §7 |
| 16.4 | Put a DPA in place with the analytics provider before any real data flows | Blocked | Feeds 11.6 |
| 16.5 | Define the margin-alert rules and how alerts reach users | Not started | Needs 10.3 prioritization |
| 16.6 | Surface the analytics dashboard in the app | Not started | |
| 16.7 | Ensure everything the service reads or writes is tenant-scoped | Not started | [ADR-008](docs/decisions.md) |

---

## Epic 17 — Batch & lot traceability

**Branch:** `feature-traceability` · **Depends on:** Epics 3, 9 (9.21), 10 (10.8, 10.9)

Give the bakery the record-keeping EU Reg. 178/2002 Art. 18 requires of it: **one step back** (which
supplier lot went into what) and **one step forward** (where a finished batch went), per
[ADR-017](docs/decisions.md). This adds a temporal/event layer to a schema that is otherwise a pure
current-state catalogue — which is why it is its own epic rather than part of Epic 3.

**A partial implementation is worse than none if it looks complete.** The pilot bakery is a real food
business operator; nothing here should present itself as a compliance record until 17.7 and 17.10 make
the trace path whole.

| ID | Task | Status | Notes / source |
|---|---|---|---|
| 17.1 | Model goods receipts: what actually arrived — supplier lot code, receipt date, quantity, best-before, price paid — as lines distinct from the `RawMaterial` catalogue row | Blocked | Entity shape `Open` — 9.21. **A lot is an event, not an attribute** ([ADR-017](docs/decisions.md)); do not add a `lot` field to `RawMaterial` |
| 17.2 | Model production runs: which receipt lots were consumed, in what quantity, when, and by whom, producing an output batch | Blocked | 9.21 |
| 17.3 | Assign an internal lot code to each produced batch, with the code format decided rather than improvised | Blocked | 9.21 |
| 17.4 | Model outbound records at the granularity the regulator actually expects — sufficient for one-step-forward | Blocked | Granularity `Open` — 10.8. Direct-to-consumer sales are treated differently from wholesale |
| 17.5 | Make traceability records append-only: no hard delete, no silent retroactive edit — corrections are new records with an audit trail | Not started | The strongest integrity requirement in the schema. Pairs with 2.9 and 11.10 |
| 17.6 | Prevent hard-deletion of any `Supplier` or `RawMaterial` referenced by a traceability record | Not started | This is what turns 3.13/3.22's soft delete from a judgment call into a requirement |
| 17.7 | Build the trace query: given any lot, return one step back and one step forward, through multi-level recipes (base recipe → product) | Not started | The actual deliverable — everything above is scaffolding for it |
| 17.8 | Tenant-scope every traceability model with a `Bakery` FK, like every other business table | Not started | [ADR-008](docs/decisions.md). Needs 3.1/3.2 |
| 17.9 | Enforce the food-law retention floor on traceability records, overriding ordinary retention where the two conflict | Blocked | Floor undecided — 10.9. Pairs with 11.4 |
| 17.10 | Produce an authority-ready trace report/export for a given lot, usable in an FSAI request | Not started | Distinct from the tenant export (Epic 14) and the GDPR export (Epic 15) |
| 17.11 | Test the trace end to end: across a multi-level recipe, and proving no record from another tenant is ever reachable | Not started | Pairs with 6.9 |
| 17.12 | Record the price paid per goods receipt, and confirm whether it becomes the source of truth for input price history | Not started | [ADR-017](docs/decisions.md) — a receipt line naturally dates its own price, which may answer 10.5's price-history question outright. Decide together, not separately |

---

## Epic 18 — Allergen data

**Branch:** `feature-allergen-data` · **Depends on:** Epics 3, 17 (for the recursion and the receipt
data) · **Priority:** Should ([ADR-024](docs/decisions.md))

Allergen information on raw materials, aggregated up through base recipes to finished products under
EU FIC 1169/2011. Deliberately **outside** Epic 17 so the Article 18 traceability core isn't delayed
by scope growing around it — but it reuses [ADR-022](docs/decisions.md)'s recipe recursion directly:
aggregating allergens up the tree is the same traversal as aggregating cost.

| ID | Task | Status | Notes / source |
|---|---|---|---|
| 18.1 | Confirm the allergen scope against FSAI/FIC guidance: the 14 declarable allergens, and what a costing tool is expected to record vs. what belongs on a label | Blocked | 10.12 — scope confirmation. Same shape as 10.8 did for traceability |
| 18.2 | Add allergen attributes to `RawMaterial`, sourced from the supplier's specification rather than guessed | Blocked | 18.1 |
| 18.3 | Aggregate allergens up the recipe tree (raw material → base recipe → product), reusing the 4.16 recursion | Not started | [ADR-022](docs/decisions.md)/[ADR-024](docs/decisions.md). Same traversal as costing — build once, use twice |
| 18.4 | Model "may contain" / cross-contamination separately from "contains" — they are different claims | Blocked | 18.1 |
| 18.5 | Mark any product whose allergen data is **incomplete** as incomplete, rather than showing an empty allergen list as if it meant "none" | Not started | **The safety-critical one.** An unknown presented as an absence is how an allergen system hurts someone. Mirrors 17.7/17.10's "partial is worse than none" |
| 18.6 | Tenant-scope allergen data and cover it in the isolation tests | Not started | [ADR-008](docs/decisions.md); pairs with 6.9 |

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
| [ADR-016](docs/decisions.md) — one free pilot bakery, no deadline, flat per-bakery pricing later | 10.7 ✅, 10.6, 10.10, 10.11, plus a **negative** constraint on 3.1 (no plan/tier fields) and 2.8/3.4 (no plan-based gating) |
| [ADR-017](docs/decisions.md) — batch/lot traceability in scope, as its own epic | 9.21, 10.8, 10.9, 10.12, 17.1–17.12, and the forced soft-delete in 3.13/3.22 |
| [ADR-018](docs/decisions.md) — costing & money semantics (purchase-unit prices, kg/l/each, net-of-VAT with a dated rate table, dual-source price history) | 3.10, 3.11, 3.15, 3.16, 3.34 ✅, 3.50–3.54, 3.26 (units half), 6.16, 6.17, 10.13, 17.12, plus the deletion of inline `float()` costing in 4.1 |
| [ADR-019](docs/decisions.md) — soft-delete scope, per-tenant supplier uniqueness, Django admin as superuser-only support tooling | 3.6, 3.22, 3.55, 3.56, 2.15, 6.18 |
| [ADR-020](docs/decisions.md) — three per-tenant roles (Owner/Staff/Read-only) on a membership record | 2.8, 2.16, 3.4, 3.57, 3.58, 6.19, 10.14 |
| [ADR-021](docs/decisions.md) — non-functional targets (perf budget, WCAG 2.2 Level A, responsive/evergreen, English-€ but translation-ready) | 5.12, 5.13, 5.14–5.17, 10.15 |
| [ADR-022](docs/decisions.md) — receipts drive raw-material cost; ingredient lines accept a raw material or a base recipe | 3.59–3.62, 4.16, 4.17, 5.20, 6.20, 6.21, 17.1, and the narrowing of 9.18 |
| [ADR-023](docs/decisions.md) — dashboard overview page; settings as tenant self-administration | 5.18, 5.19, 4.18, 9.22, 10.16, 10.17, and the replacement of the broken user-delete view (6.7) |
| [ADR-024](docs/decisions.md) — MoSCoW pass on the feature backlog (10.3) | 5.9 (Must → build), 5.21 + 3.63 (supplier comparison as Must), **Epic 18** (allergen data as Should), Epic 13 narrowed to product photos, 16.1 re-scoped, 10.10 mostly resolved, 11.3 off the critical path |

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
| A half-built traceability feature that *looks* like a compliance record to a real food business operator | 17.7, 17.10, plus the 10.8 regulator check before Epic 17 starts |
| Schema redesigned in Epic 3 without accounting for Epic 17's event layer, forcing a second redesign | 9.21 decided before 3.19/3.22 are implemented |
| A cyclic base recipe hanging every costing request once recipes can nest | 3.59 (reject at save), 4.16 (depth guard), 6.20 (test) |
| Cost figures presented with equal confidence whether they came from an invoice or a guess | 3.62, 4.17, 5.20 |

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
