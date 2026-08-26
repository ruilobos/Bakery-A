# Tech Stack

How to use this file: the **Current** column is factual — don't change it without checking the
code. The **Decision** column stays `Open` until a choice is actually made; once it's made, write
it here **and** log the reasoning as an ADR in [decisions.md](decisions.md), then flip Status to
Decided. Claude should never write code against a `Proposed`/`Open` row as if it were final.

Once a row is Decided, it must also appear as a task in an epic in
[`PRODUCTION_UPDATE_PLAN.md`](../PRODUCTION_UPDATE_PLAN.md) — that file is the backlog, this one is
where the choice gets argued out. Epic 9 (`stack-decisions`) is the backlog counterpart of this
file: one task per `Open` row below.

**Status as of 2026-08-26: no `Open` rows remain.** The last six closed together
([ADR-032](decisions.md)–[ADR-036](decisions.md)) — the ingredient-line and category shapes, the
traceability entities, lot codes and stock, Python lint/test tooling, the tenant export format, and
the insights engine with its cost and data-handover model, which also released the WSGI/ASGI row
that had been held for it. Epic 9 is **closed**. A new question goes back in as an `Open` row here
*and* as a new Epic 9 task — it does not get answered in passing.

## Runtime

| Layer | Current | Candidate | Decision | Status |
|---|---|---|---|---|
| Python | 3.8 (`runtime.txt`), Dockerfile uses 3.9-slim — **both EOL** (Oct 2024 / Oct 2025) | 3.12 as the primary target, with a follow-up validation pass on 3.13 once all dependencies and the chosen host confirm support | **Python 3.13** — supported by both Django 5.2 (3.10–3.14) and 6.2 (3.12–3.14), so the whole planned path needs no Python change. `python:3.13-slim` in the `Dockerfile` is the single source of the version; `runtime.txt` is deleted, not updated. The old 3.12 candidate aged out — 3.12 has been security-only since Oct 2025 | Decided ([ADR-025](decisions.md)) |
| Django | 3.2 — **EOL since April 2024** | Current supported LTS — 5.2 LTS directly if hosting and package support allow, otherwise staged 3.2 → 4.2 LTS → current LTS | **Django 5.2 LTS, upgraded directly from 3.2** (no 4.2 stop). The LTS has the *longer* runway than current stable: 5.2 → April 2028 vs. 6.1 → Dec 2027, and 6.0 left mainstream support 2026-08-04. Next hop **6.2 LTS**, H2 2027 | Decided ([ADR-025](decisions.md)) |
| Database | PostgreSQL (version unpinned; `docker-compose.yaml` has no Postgres service at all) | PostgreSQL, pin a version | **PostgreSQL 17**, pinned identically local and production. Major versions must match across environments; a bump is deliberate and restore-tested (3.47), never drift | Decided ([ADR-026](decisions.md)) |
| DB topology (app vs. DB process) | Self-hosted: separate Postgres container from the app | Always separate services (app and DB never bundled in one image), on every hosting candidate | Separate always | Decided (see ADR-007) |
| Multi-tenancy model | None — single-bakery schema | Single shared database, row-level tenant isolation via a `Bakery` FK on every business table (not database-per-tenant) | Shared DB, tenant-scoped rows | Decided (see ADR-006/ADR-008) |
| WSGI/ASGI server | gunicorn 20.1.0 (WSGI) | current gunicorn; ASGI only if a real need shows up | **gunicorn, WSGI, sync workers**, latest version pinned at lock time ([ADR-029](decisions.md)). Nothing in the decided scope is async: [ADR-023](decisions.md)'s dashboard is server-rendered aggregates, and [ADR-036](decisions.md)'s insights service is a nightly extract plus a short callback POST. Adopting ASGI would impose the sync-ORM constraint on every view from day one for a `Could`-rated feature. **One revisit trigger:** the insights dashboard needing *push* updates (SSE/WebSocket) rather than polling (7.14) | Decided ([ADR-036](decisions.md)) |

## Dependencies

| Package | Current | Candidate | Decision | Status |
|---|---|---|---|---|
| `psycopg2-binary` | 2.9.6 | `psycopg[binary]` (v3) | **`psycopg[binary]` 3** — natively supported by Django since 4.2; psycopg2 is maintenance-only upstream | Decided ([ADR-025](decisions.md)) |
| `whitenoise` | 5.2.0 | latest compatible with chosen Django | **Latest compatible with Django 5.2 / Python 3.13** at lock time. 6.12.0 confirmed compatible 2026-08-10 | Decided ([ADR-025](decisions.md)) |
| `django-environ` | 0.4.5 | latest | **Latest compatible** at lock time; 0.14.0 confirmed 2026-08-10. Stays — it owns `env.db()`, the `DATABASE_URL` contract in [ADR-015](decisions.md) rule 2 | Decided ([ADR-025](decisions.md)) |
| `Pillow` | 10.4.0 | latest | **Removed until Epic 13**, then **latest compatible** at lock time (12.3.0 confirmed 2026-08-10). It has no consumer today — no `ImageField`, no `Pillow` import (verified 2026-08-16) — and its owner is 13.4/13.5, so it re-enters via 13.1 | Decided ([ADR-025](decisions.md), amended by [ADR-029](decisions.md)) |
| `django-mathfilters` | 1.0.0 | keep only if template math stays; drop if costing moves to a service layer | **Dropped.** Latest release is 1.0.0 (Feb 2020), classifiers stop at Django 3.x — a hard blocker for the upgrade, not a preference. Loaded in `base_recipe.html` and `products.html`, both doing template-side cost math that [ADR-018](decisions.md) already ruled wrong (19.6) | Decided ([ADR-025](decisions.md)) |
| `asgiref` / `sqlparse` / `tzdata`/`pytz` | pinned to Django 3.2's requirements | align with whatever Django release is chosen above | **Removed from the hand-written file.** `asgiref`/`sqlparse` are Django's own transitive deps and belong in the lock file; `pytz` goes entirely (Django dropped pytz support in 5.0, stdlib `zoneinfo` replaces it, no app code imports it) | Decided ([ADR-025](decisions.md)) |
| `environ` 1.0 / `dj-database-url` 0.5.0 (not previously listed) | both present in `requirements.txt` | — | **Both removed.** `environ` is an unrelated PyPI package whose top-level `environ` module collides with `django-environ`'s — an install slip and a live hazard. `dj-database-url` is imported nowhere in app code and duplicates `env.db()` | Decided ([ADR-025](decisions.md)) |
| Dependency management | single UTF-16LE `requirements.txt` | split `requirements/base.txt` + `dev.txt` + `prod.txt`, pinned via `pip-tools` or an equivalent lock workflow for deterministic builds | **`uv pip compile` over `requirements/{base,dev,prod}.in` → pinned, hashed `.txt`.** Requirements-file mode, **not** `pyproject.toml`/`uv sync` — the format the `Dockerfile`, Railway and every fallback host already consume, so determinism costs no change to the install path. `--generate-hashes` + `--require-hashes` at install, `--python-version 3.13` so resolution matches the image, and `dev`/`prod` compiled against `-c base.txt` so a shared package cannot resolve twice. `uv` itself is pinned build-time tooling, never an app dependency (19.12, 19.16) | Decided ([ADR-029](decisions.md)) |
| Dependency hygiene | **reviewed** 2026-08-10 by [ADR-025](decisions.md) — six of twelve entries removed with a named reason each | every dependency has a named owner and a stated purpose; anything else is removed | **The `.in` file is the register:** every line carries a trailing comment naming its purpose and the owning epic/task, and a line without one is removed at the next recompile rather than researched later. Transitive deps live only in the generated `.txt`, which is never hand-edited. First application of the rule: **`Pillow` is removed** — no `ImageField` and no `Pillow` import exists anywhere (verified 2026-08-16); it returns in 13.1 with the rest of the media stack, amending [ADR-025](decisions.md) | Decided ([ADR-029](decisions.md)) |
| Media storage | none | `django-storages[s3]` + `boto3`, for S3-compatible object storage (see ADR-005) | Cloudflare R2 | Decided |

**Dependency strategy:** replace the current ad hoc dependency state with pinned, reviewed,
production-safe dependencies; normalize the file encoding to UTF-8; split by environment; generate
pinned requirements from a lock workflow rather than hand-editing. Per [ADR-025](decisions.md), this
table fixes the **constraint** — latest release compatible with Django 5.2 on Python 3.13 — and the
lock workflow ([ADR-029](decisions.md), 9.8 ✅) fixes the exact versions. Exact patch pins are
deliberately not recorded here or in the ADR log, since both are append-only and the pins are not.
The constraint is re-evaluated at **every** recompile, not frozen at the first one.

The rewritten dependency set drops from twelve entries to **five** direct runtime dependencies in
`requirements/base.in` — Django, `psycopg[binary]`, `whitenoise`, `django-environ`, `gunicorn` —
with `Pillow` returning in Epic 13 and `django-storages[s3]`/`boto3` alongside it. Version facts above were
verified 2026-08-10 against the [Django release page](https://www.djangoproject.com/download/), the
[Django install FAQ](https://docs.djangoproject.com/en/dev/faq/install/), the
[Python version status page](https://devguide.python.org/versions/), and each package's PyPI
metadata.

## Backend architecture

| Topic | Current | Candidate | Decision | Status |
|---|---|---|---|---|
| Settings layout | `bakery/settings/base.py` (dev defaults) + `heroku.py` (prod overrides) | `settings/base.py` + `local.py` + `test.py` + `production.py` | **`base.py` + `local.py` + `test.py` — deliberately no `production.py`.** `base.py` *is* the production configuration: every value from the environment, production-safe defaults, and **no default at all** for `SECRET_KEY`/`ALLOWED_HOSTS`/`DEBUG`, so a missing variable fails at boot instead of silently running insecure. `local.py` and `test.py` are the only overlays and each opts *into* the unsafe or convenient behaviour, so forgetting `DJANGO_SETTINGS_MODULE` lands on the **safe** module — the inverse of today (1.5, 2.19) | Decided ([ADR-028](decisions.md)) |
| Business logic location | inline in `control/views.py`, duplicated across views and model `@property` methods | dedicated services/domain module | **`control/services/` — plain functions, frozen dataclass returns, batch-first.** `cost_products(queryset, …)` is the primary API; single-object costing wraps it. Models keep fields, constraints and managers and lose costing entirely — the `@property` methods are deleted, not delegated. Forced by [ADR-023](decisions.md)'s dashboard costing every product at once against [ADR-021](decisions.md)'s budget (a per-instance property structurally cannot batch) and by [ADR-018](decisions.md)'s provenance, which is a value object, not a `Decimal`. The inline `float()` costing is **definitively wrong**, not merely duplicated — it cannot express unit conversion, net-of-VAT storage, or dated prices — so it is deleted, not patched (4.1, 4.19, 4.20) | Decided ([ADR-028](decisions.md)) |
| API layer | none | Django REST Framework, only if an external integration/API consumer is actually needed | **No API layer, and no framework pre-selected for later.** Every candidate consumer is already excluded: [ADR-021](decisions.md)'s device matrix rules out a native app, the frontend is server-rendered (HTMX consumes HTML fragments, not JSON), the insights service has Django as the *client* not the server, and exports are files. The health endpoint and any future callback are plain `JsonResponse` views — two endpoints do not justify serializers, routers, and a second permission system beside [ADR-020](decisions.md)'s. Revisit trigger in [ADR-028](decisions.md); the tool gets chosen when it fires (4.15 cancelled) | Decided ([ADR-028](decisions.md)) |
| Auth/permissions | mix of no auth, `staff_member_required`, ad hoc template checks | consistent `LoginRequiredMixin` + real role-based permissions | Role **model** decided ([ADR-020](decisions.md)); **posture** decided ([ADR-027](decisions.md)): `LoginRequiredMiddleware` makes login the default, with `@login_not_required` on the cover page and login view (2.17). **Now closed** ([ADR-028](decisions.md)): Django's built-in auth views are the only auth surface — `accounts.views.user_login` is **unreachable** (`accounts.urls` is never included in `bakery/urls.py`) and is deleted outright (4.5). Capabilities are Django permission codenames resolved by a **custom authentication backend** against the request's active membership, so `PermissionRequiredMixin`, `@permission_required` and `{% if perms.… %}` keep working — one permission vocabulary, not two (2.20, 2.21) | Decided ([ADR-020](decisions.md)/[ADR-027](decisions.md)/[ADR-028](decisions.md)) |
| Caching | none | cache expensive dashboard/costing aggregates — only if measurements show it's needed | **No cache in the first release.** Query design is the lever instead: batch costing (4.19), `select_related`/`prefetch_related`, and [ADR-027](decisions.md)'s connection pool. Two reasons, and the second is decisive — the pilot is *one* bakery ([ADR-016](decisions.md)), whose whole ingredient graph costs in milliseconds once batched; and this is a **costing** app, where a stale margin is not a slow page but a wrong number someone prices against, over an invalidation surface spanning receipts, cascading base recipes, VAT rows and price rows. Escalation ladder and measurement trigger (7.20 against [ADR-021](decisions.md)) in [ADR-028](decisions.md); the batch API carries a per-tenant version stamp from day one so caching bolts on at that seam without redesign (4.20) | Decided ([ADR-028](decisions.md)) — closes the caching half of 9.18 |
| Email | none — the app sends no mail | a transactional email provider, configured from environment variables | **Brevo over SMTP**, via Django's built-in `smtp.EmailBackend` — no dependency, and the provider stays a pure environment-variable concern ([ADR-015](decisions.md) rule 2). French-owned, data centres in France/Belgium/Germany, ISO 27001:2022, DPA included by default, 300/day free against an expected volume under 100/month (verified 2026-08-13). Resend rejected on a **fact, not a preference**: EU data residency is Pro-only at $20–35/mo, over 3× the entire infrastructure budget. Scope is wider than [ADR-023](decisions.md)'s invitations — adopting Django's built-in auth views makes **password reset** email-only too (7.21, 7.22, 5.24, 11.16) | Decided ([ADR-028](decisions.md)) |
| Connection pooling | none | `CONN_MAX_AGE` tuning or a pooler (e.g. PgBouncer) — only if traffic/deployment topology requires it | **Django's native psycopg connection pool** (`DATABASES["OPTIONS"]["pool"]`, Django 5.1) plus `CONN_HEALTH_CHECKS`. Neither branch of the candidate: in-process, no PgBouncer, no extra service to run, monitor or patch (7.19) | Decided ([ADR-027](decisions.md)) — closes the pooling half of 9.18 |

### Data model — structural open questions (feed Phase 3 / Epic 3)

These are shape-of-the-schema questions, distinct from the business-meaning questions in
[project_requirements.md](project_requirements.md) ("Business rules & data semantics"). Both sets
must be answered before the Phase 3 migrations are written.

| Topic | Current | Candidate | Decision | Status |
|---|---|---|---|---|
| Ingredient line model | two parallel through-style models (`Bs_Ingredients` for base recipes, `Recipe_Ingredients` for products) | keep them separate if the business workflows genuinely differ; otherwise a single shared ingredient-line model with a typed parent reference | **One shared `RecipeLine`** — typed parent (`parent_product` XOR `parent_base_recipe`) and typed component (`component_material` XOR `component_recipe`), both XORs enforced by database `CHECK` constraints rather than by `clean()`, which does not run on `bulk_create`. `Product` and `Base_recipes` themselves stay separate models — this collapses the *lines*, not the recipes ([ADR-022](decisions.md)'s `is_sellable` merge remains declined, but gets cheaper). Costing recursion, the 17.7 trace and 18.3's allergen aggregation become one traversal over one table (3.19, 3.73) | Decided ([ADR-032](decisions.md)) |
| Recipe nesting & cycles | products reference raw materials only; base recipes reach nothing | a product's line may reference a base recipe, with costing recursing into it | Nesting **decided** ([ADR-022](decisions.md)). Cycles must be **rejected at save time** plus depth-guarded in the service layer — nothing in the current schema prevents a recipe containing itself | Decided (3.59, 4.16) |
| Cost provenance | none — a cost is a bare number | distinguish receipt-derived cost from a manual estimate, in the data not just the UI | **Decided** — the latest goods receipt by *receipt date* sets current cost; a manual price survives as a labelled estimate; the service layer returns provenance with the figure | Decided ([ADR-022](decisions.md)) |
| Units & categories | free-text `CharField`s (`unit`, `categorie`) | controlled enums if the value set is stable, or lookup/reference tables if the values are business-managed | **Both lookup tables, with different edit rights.** Units: a conversion factor is data an enum cannot carry ([ADR-018](decisions.md)), and units are **not** tenant-editable — editing a factor silently rewrites every derived cost. Categories: one tenant-scoped `Category` table with a `kind` discriminator (`material`/`product`), archivable, unique on `(bakery, kind, name)` — tenant-editable per 10.17, since a category carries no arithmetic. Existing free-text values are backfilled per tenant, then the column is dropped (3.74) | Decided ([ADR-018](decisions.md)/[ADR-032](decisions.md)) |
| Calculated values | recomputed inline per request, in `float()` | store as derived/read-only data only, never as editable business fields | Derived, never persisted — reinforced by [ADR-018](decisions.md) | Decided |
| Deletion semantics | hard deletes everywhere | soft delete / archive for entities whose history must stay visible | **Soft delete:** `Supplier`, `RawMaterial`, `Product`, `Base_recipes` — the rule is "anything referenced by a record that outlives it". **Hard delete:** ingredient lines. Tenant scope and archived state must be combined in **one** base manager, not applied ad hoc (3.55) | Decided ([ADR-019](decisions.md)) |
| Auth/permissions model | mix of no auth, `staff_member_required`, ad hoc template checks | consistent `LoginRequiredMixin` + real role-based permissions | **Three per-tenant roles** — Owner / Staff / Read-only — held on a **membership record** (user × bakery × role), since Django's global `Group` cannot express "Owner of bakery A". Checks are capability-named, never `role == "owner"` | Decided ([ADR-020](decisions.md)) |
| Administration surfaces | Django admin and the in-app settings area overlap | narrow one of them | **Two audiences, not the same operations.** In-app settings = tenant surface (tenant-scoped, role-checked, audited). Django admin = **superuser-only** support tooling, deliberately cross-tenant, never linked from the tenant UI. `ModelAdmin` does not apply tenant-scoped managers — do not rely on it to | Decided ([ADR-019](decisions.md)) |
| Money & quantity types | mixed (`CharField` quantity, `float()` math in views) | `Decimal` end-to-end, in the schema and the service layer | **`Decimal` end-to-end.** Quantities ≥ `Decimal(12,4)` (`12,6` safer), money carried beyond 2 dp internally, rounded to 2 dp **only at presentation** with an explicit, tested rounding rule | Decided ([ADR-018](decisions.md)) |
| Price basis | `RawMaterial.price` with implicit meaning | store the invoice as written; derive per-canonical-unit cost at cost time | `purchase_price` + `pack_quantity` + `purchase_unit`; derived cost never persisted | Decided ([ADR-018](decisions.md)) |
| Canonical costing units | none | one canonical unit per dimension, with a conversion factor per purchase unit | **kilogram / litre / each**. Trade-off accepted: larger canonical units mean gram-scale ingredients are small fractions, so decimal scale is load-bearing (3.50, 3.51, 6.16) | Decided ([ADR-018](decisions.md)) |
| VAT | inconsistent between products and dashboard math | net storage, VAT applied at the presentation boundary | All stored money **net (ex-VAT)**; dated VAT-rate reference table (`code`, `percent`, `valid_from`, `valid_to`); product references a rate **code** | Decided ([ADR-018](decisions.md)) |
| Price history | none — prices overwritten in place | version both input and sale prices | **Two sources:** input prices from ADR-017 goods receipts (free by-product); sale prices as dated `ProductPrice` rows | Decided ([ADR-018](decisions.md)) |
| Traceability entities (new — ADR-017) | none; the schema is a pure current-state catalogue with no delivery, batch, or production-run concept | Goods-receipt lines (supplier lot, date, quantity, best-before, price paid) distinct from the `RawMaterial` row; production runs consuming specific receipt lots and emitting an output batch; outbound records. **A lot is an event, not an attribute** — do not add a `lot` field to `RawMaterial` | **Header + lines, full event chain.** `GoodsReceipt` (supplier, receipt date, doc ref) → `GoodsReceiptLine` (material, supplier lot, qty, unit, best-before, price in [ADR-018](decisions.md)'s purchase-price shape); `ProductionRun` → `Consumption` (FK to a receipt line, quantity consumed) → output `Batch` → `OutboundRecord`. A delivery note is one record with many lines, so it is modelled as one. Receipts-only was rejected on [ADR-017](decisions.md)'s own "partial is worse than none" (17.1, 17.2) | Decided ([ADR-033](decisions.md)) |
| Internal lot code generation | n/a | Decided format (sequence? date-prefixed? per-tenant?) rather than improvised per install | **`YYYYMMDD-NNN`**, sequence resetting daily, unique on `(bakery, lot_code)`, allocated **server-side inside the transaction that creates the batch** — never client-side, never by counting rows. The date earns its place: a lot code is read off a label and quoted on a phone call. Gaps after a rollback are acceptable; collisions are not (17.13) | Decided ([ADR-033](decisions.md)) |
| Stock / quantity-on-hand | none | Nearly free once receipts and production runs exist, but a different product promise with different accuracy expectations — include deliberately or exclude deliberately | **Derivable, deliberately not surfaced.** `Consumption.quantity_consumed` makes on-hand computable as `Σ received − Σ consumed`, which is the whole content of [ADR-024](decisions.md)'s "design so it *could* be derived later" — but there is no stock field, no stock page and no low-stock alert this round. Showing the figure was rejected: it ignores waste, spillage and unrecorded use, so it would be wrong in normal operation, not in an edge case (17.14) | Decided ([ADR-033](decisions.md)) |

**Note on sequencing:** the three rows above were answered ([ADR-033](decisions.md), 2026-08-26)
**before** Epic 3's schema work starts, which was the point. Traceability adds a temporal/event layer
to tables Epic 3 is about to restructure (`RawMaterial`, the ingredient lines, deletion semantics), so
deciding them separately would have meant redesigning the same tables twice. Epic 3 must now build
`RawMaterial` knowing these tables are coming: **no `lot` field, no `stock` field**, and numeric
`quantity` with a unit FK so a receipt line can be reconciled against the catalogue row. See
[roadmap.md](roadmap.md), Epic 17.

## Frontend

| Topic | Current | Candidate | Decision | Status |
|---|---|---|---|---|
| Templating | Django templates, `APP_DIRS=True`, no shared `base.html` — measured 2026-08-16: **32 templates, 4,277 lines, zero `{% extends %}`, zero `{% include %}`**, 31 with full `<!DOCTYPE>` boilerplate, navbar duplicated 32× | Django templates + shared `base.html` + partials | **Shared `base.html` + `{% include %}` partials** in `<app>/templates/partials/`. `django-template-partials` **not** adopted — a dependency for ~4 fragments; revisit if HTMX fragments proliferate (5.1, 5.2) | Decided ([ADR-030](decisions.md)) |
| CSS framework | Bootstrap **5.0.0** vendored in `bakery/static` (released May 2021) | current stable Bootstrap, or reconsider entirely | **Bootstrap 5.3.x** — same major, so the classes across 32 templates stay largely valid: an upgrade, not a restyle. Keeps Epic 5 on structure rather than appearance, and its component semantics serve the WCAG 2.2 A target (5.4) | Decided ([ADR-030](decisions.md)) |
| Asset pipeline | none (hand-copied static files) | Vite for SCSS/JS bundling + cache busting | **None — the Vite candidate is rejected.** It would add Node to the `Dockerfile`, a second lockfile beside [ADR-029](decisions.md)'s, and CI steps, to bundle **zero bytes of JS** and 922 lines of CSS, duplicating the hashing/compression 19.14's whitenoise already does. Instead: consolidate the 16 CSS files, native custom properties + nesting, whitenoise for cache-busting. **Revisit:** custom JS past a few hundred lines, or SCSS-variable-level Bootstrap customization (5.6) | Decided ([ADR-030](decisions.md)) |
| Interactivity | **7 custom JS files, all 0 bytes** — there is no JavaScript in the project | vanilla JS modules, optionally HTMX for server-driven interactivity | **HTMX**, vendored at a pinned version, plus small vanilla modules. One ~14KB script, no bundler, server returns HTML fragments — what [ADR-028](decisions.md) already assumed when it rejected an API layer. Built as **progressive enhancement**: forms and links work with JS disabled. Alpine.js rejected — Bootstrap's JS bundle already covers dropdowns/modals/toasts (5.7, 5.25) | Decided ([ADR-030](decisions.md)) |
| Is a full SPA needed? | n/a | leaning no — server-rendered is enough per current scope | **No** — a ratification, not a new decision: [ADR-028](decisions.md) rejected the API layer and [ADR-021](decisions.md)'s device matrix rejected a native app, which between them already foreclosed it | Decided ([ADR-030](decisions.md)) |
| Template/CSS/JS linting | none | add where practical, alongside the Python tooling below | **`djlint`** for templates — a pip package, so it becomes the first real occupant of [ADR-029](decisions.md)'s `requirements/dev.in`, with no Node in dev. Standalone CSS/JS linting (`stylelint`/`prettier`) deferred to 9.17 on the same grounds as the pipeline row (5.8) | Decided ([ADR-030](decisions.md)) — closes the template half of 9.17 |
| Accessibility target | none stated | a named WCAG conformance level to build against | **WCAG 2.2 Level A** — with a revisit trigger to AA before EU expansion (10.15). **Django's own form rendering supplies a material share of it** (`as_field_group()`, div-based templates): real label association, `aria-describedby`, `aria-invalid`, `<fieldset>`/`<legend>` grouping — framework output rather than hand-written markup (5.22, [ADR-027](decisions.md)) | Decided ([ADR-021](decisions.md)) |
| Device / browser matrix | responsive, matrix unstated | one responsive UI across a named browser set | Phone→desktop; current **and previous** major Chrome/Firefox/Safari/Edge. No IE11, no native app | Decided ([ADR-021](decisions.md)) |
| Localization | English only, `€` hardcoded in templates | translation-ready even while shipping one locale | Ship `en-IE`/EUR; **`gettext` on display text and one currency formatter from day one** — no hardcoded `€` (5.15, 5.16) | Decided ([ADR-021](decisions.md)) |
| Performance budget | none | a target specific enough to detect a regression | p95 < 500 ms pages, < 2 s dashboard aggregate, ~10 concurrent users/tenant. Documented budget, **not** a CI gate — Railway Hobby shares CPU | Decided ([ADR-021](decisions.md)) |

**Frontend direction (decided — [ADR-030](decisions.md)):** a modern server-rendered Django frontend,
with progressive enhancement over a client-side framework. Keep Django templates, add a shared
`base.html` plus partials, upgrade Bootstrap in place, add HTMX for server-driven interactivity — and
**no build step**. The Vite candidate this paragraph used to carry was rejected on measurement: with
0 bytes of custom JavaScript and 922 lines of CSS, a bundler would add Node, a second lockfile and CI
steps to duplicate work whitenoise's manifest storage already does.

Two consequences of "no pipeline" are worth carrying forward, because they shift risk rather than
remove it:

- **5.3 becomes load-bearing.** Whitenoise is now the *only* cache-busting mechanism, and it does
  nothing for the 23 templates that hardcode `/static/...`. 5.3 + 19.14 + 1.13 are the whole story on
  asset versioning; done partially, the site silently serves stale CSS.
- **Vendored assets need their own register.** Bootstrap and HTMX are dependencies that
  `requirements/*.in` cannot see, so [ADR-029](decisions.md)'s owner/purpose rule is extended to them
  by hand (5.25). Skipping it reproduces exactly the state this decision found: a four-year-old
  vendored library nobody had noticed.

## Infrastructure / operations

| Topic | Current | Candidate | Decision | Status |
|---|---|---|---|---|
| Hosting | Self-hosted: home server running Docker via Portainer; PostgreSQL in a separate container on the same machine. (Moved off Heroku after Heroku discontinued its free dyno/Postgres tier.) | Railway, Render, or DigitalOcean App Platform — narrowed per ADR-003; see "Hosting candidates" below | **Railway, Hobby plan, EU West (Amsterdam)** — ~$6/mo (see ADR-013) | Decided |
| Dev/test environment | Runs on the developer's machine ad hoc | Local `docker-compose` (same Dockerfile as production, app and DB as separate containers) — no persistent hosted staging environment | Local Docker Compose (see ADR-014) | Decided |
| Containerization | `Dockerfile` + `docker-compose.yaml` (expects external `bakery_simple` network) | Keep the custom Dockerfile as the deploy artifact on whichever host is chosen, rather than that platform's native buildpack — see ADR-004 and "Deployment method" below | Custom Dockerfile | Decided |
| Host portability | Partially there by accident: `heroku.py` already reads `DATABASE_URL`, whitenoise serves static, media is S3-compatible. Undermined by a hardcoded port, `migrate` inside the container `CMD`, a host-named settings module, and no portable database dump | Any Docker + PostgreSQL host must be reachable with configuration changes only, never code changes — see "Host portability rules" below | Standing constraint (see ADR-015) | Decided |
| Static/media storage | whitenoise for static assets; local `MEDIA_ROOT` config exists but points to a broken leftover path (`bluebiulding/media`) and nothing uses it yet | Keep whitenoise for static assets. For user-uploaded media (new: product photos, profile pictures), use S3-compatible object storage — see "Static & media file storage" below | Cloudflare R2 (see ADR-005) | Decided |
| CI/CD | none | pipeline: install → lint → test → security scan → build | **GitHub Actions, extending the Epic 1 workflow ([ADR-011](decisions.md)) rather than replacing it, with a 70% repo-wide coverage floor.** Merge gate: the test suite, `ruff` + `djlint`, the migration/`collectstatic`/`docker build` checks already in 1.11/1.13, and `pip-audit` against [ADR-029](decisions.md)'s hashed lock, with Dependabot raising dependency PRs. **No SAST or image scanning** in the first release — revisit trigger in [ADR-031](decisions.md) | Decided ([ADR-031](decisions.md)) |
| Deploy trigger | manual, on the home server | CI-driven or platform-native | **Railway git-watch on `production`**, with `migrate` as Railway's **pre-deploy command** — which satisfies [ADR-015](decisions.md) rule 4 (migrations out of `CMD`) without a bespoke pipeline. 6.14 ("block a bad deploy") is therefore satisfied by **branch protection**, not by a second gate: failing checks block the merge, and only a merge deploys | Decided ([ADR-031](decisions.md)) |
| Error tracking / monitoring | none | Sentry or equivalent | **Sentry SaaS, free Developer tier, EU region (`de.sentry.io`)** — the region is fixed at organisation creation and **cannot be changed afterwards**, making it the one setup step that must not be got wrong. `sentry-sdk[django]` enters `requirements/base.in` with an owner comment ([ADR-029](decisions.md)); `send_default_pii` stays **off** and a `before_send` scrubber is mandatory, since a traceback here can carry supplier contacts, staff emails and costing data. New processor → DPA + subprocessor entry ([gdpr.md](gdpr.md) §7, 11.6) | Decided ([ADR-031](decisions.md)) |
| Uptime monitoring / alerting | none | external uptime check + alerting against the app health endpoint | **UptimeRobot free tier** — 5-minute HTTPS **keyword** check against 7.4's health endpoint, email alerting, public status page, $0. Keyword rather than status-code only, so a health endpoint reporting a dead database fails the check instead of passing on its HTTP 200. Deliberately **external to Railway**: a monitor hosted on the thing it monitors proves nothing when that thing is down | Decided ([ADR-031](decisions.md)) |
| Backups | unknown/undocumented | documented PostgreSQL backup + restore + PITR strategy, with a drilled restore. Note the host constraint (ADR-013): Railway backups are **not automatic** — daily (6-day retention), weekly (1 month), and monthly (3 months) schedules are configurable and combinable, billed incrementally (copy-on-write), and there is **no PITR**. A PITR requirement would need tooling beyond Railway's built-in backups. | **Two tracks, deliberately unequal.** (a) Railway's native daily/weekly/monthly snapshots — fast same-host rollback only (12.9). (b) The load-bearing one: a **nightly GitHub Actions job** runs `pg_dump -Fc --no-owner --no-privileges`, encrypts it **client-side with `age`**, and uploads to Cloudflare R2 under a 7-daily / 4-weekly / 12-monthly lifecycle rule — outside Railway by design ([ADR-015](decisions.md) rule 5). Weekly automated restore drill into a throwaway PostgreSQL 17 with 3.47's verification (3.48). **PITR rejected** — RPO of up to 24 h accepted, with a named revisit trigger | Decided ([ADR-031](decisions.md)) — closes 9.16 |

### Operations tooling and the two backup tracks (per ADR-031)

The four rows above are one decision: what runs around the app once it is live. All of it lands at
**$0/mo** on free tiers, which is what keeps [ADR-013](decisions.md)'s ~$6/mo budget intact — the
only new recurring cost is R2 storage, and a few hundred MB of dumps sits inside R2's 10 GB free
tier alongside [ADR-005](decisions.md)'s media.

The backup split is the part worth stating explicitly, because the two tracks answer different
questions and only one of them is portable:

| Track | Mechanism | Answers | Restorable elsewhere? |
|---|---|---|---|
| Same-host rollback | Railway daily/weekly/monthly volume snapshots (12.9) | "The release an hour ago corrupted data — put it back" | **No.** Copy-on-write volume snapshots, Railway-only |
| Host-independent archive | Nightly `pg_dump -Fc --no-owner --no-privileges`, `age`-encrypted, in R2 (3.70) | "Railway is gone / we are moving host / that row was wrong three months ago" | **Yes** — this is the one [ADR-015](decisions.md) rule 5 requires |

Three consequences that shape the tasks rather than just the tooling:

- **The dump job lives outside the host it backs up.** Running it in GitHub Actions rather than as a
  Railway cron keeps the escape hatch independent of the platform being escaped. The cost is that CI
  needs database credentials and reaches Postgres over Railway's public TCP proxy — so those
  credentials are backup-scoped and rotatable (3.41), not the app's.
- **Client-side `age` encryption makes key custody a real task.** Cloudflare holds ciphertext it
  cannot read, which is a clean answer for [gdpr.md](gdpr.md) §6 and 11.13 — but a lost private key
  means *proven*-lost backups, not suspected-lost. 3.72 owns the key, and 3.48's weekly drill is
  what proves the key still works.
- **Backup retention is a separate clock from record retention.** The 7/4/12 schedule here is backup
  lifetime; GDPR record retention stays `Open` in [gdpr.md](gdpr.md) §5 (11.4) and the food-law floor
  in 10.9. What the schedule *does* fix is the erasure-request answer: personal data in backups is
  gone within a year at the outside, and within five weeks for all but the monthlies.

### Hosting candidates (for the Django app + PostgreSQL)

**Resolved: Railway (Hobby) — see ADR-013.** Kept below for reference and as fallback options; not
being re-evaluated unless Railway's Hobby limits or lack of SLA become a problem.

Per ADR-003 in [decisions.md](decisions.md), the field was narrowed to these three. Cost estimates
assume this app's actual scope (single bakery, handful of concurrent users, small dataset); sourced
via web search 2026-07-21, with Railway's figures re-confirmed 2026-08-03.

| Option | App compute | Database | Est. total/mo | GitHub auto-deploy | Notes |
|---|---|---|---|---|---|
| **Railway** ✅ **chosen** | Hobby plan, $5/mo base includes $5 usage credit, billed per-second beyond that | ~$2/mo on light workloads, same usage pool | **~$6/mo** (re-confirmed 2026-08-03) | Native, low setup effort | Cheapest of the three; no cold starts. Free options rejected — see ADR-013 |
| **Render** | Starter $7/mo (always-on) or free tier (sleeps after ~15 min idle) | Free Postgres is deleted after 30–90 days depending on source — not viable long-term; paid Postgres from ~$15/mo | ~$22/mo paid, or $0 short-term on free tier | Native, deploy on push/release | Simplest DX, but the free database's expiry makes the free tier a trial, not a real option |
| **DigitalOcean App Platform** | $5/mo | Managed Postgres from $15/mo (HA doubles it to $60/mo); a non-HA "dev" database is ~$7/mo/512MB | ~$12–20/mo | Native | Priciest baseline here but closest to "professional" — managed backups/monitoring bundled |

#### Railway cost basis (verified 2026-08-03)

Railway bills **actual** per-second usage, not allocated capacity. Converted to a 730-hour month:
~**$10.14/GB-month** RAM, ~**$20.29/vCPU-month**, ~**$0.16/GB-month** volume, **$0.05/GB** egress.

| Item | Assumed usage | Cost/mo |
|---|---|---|
| App service (gunicorn) | ~0.3 GB RAM | $3.04 |
| PostgreSQL service | ~0.2 GB RAM | $2.03 |
| CPU, both services | ~0.02 vCPU avg | $0.41 |
| Volume (Postgres data) | 2 GB | $0.32 |
| Egress | <1 GB | ~$0.05 |
| **Total** | | **~$5.85/mo** |

Hobby's $5 base includes $5 of usage, so the effective bill is ~$6/mo. Plan limits (48 GB RAM,
48 vCPU, 6 replicas per service) are far above anything this app needs and aren't a deciding factor.

**Free tiers are not viable here** (the reason ADR-013 commits to paid Hobby): the 30-day trial
grants $5 once and **deletes stateful volumes** 30 days after credits expire; the Free plan's $1/mo
credit and 0.5 GB RAM / one service cannot run an app *and* a database, which ADR-007 requires.

<details>
<summary>Considered and set aside (per ADR-003) — kept for reference, not being re-evaluated</summary>

| Option | Cost | GitHub auto-deploy | Notes |
|---|---|---|---|
| Fly.io | ~$8–15/mo (app + Postgres machine) | Not literally git-push — a GitHub Actions step running `flyctl deploy` | Global edge network; steeper learning curve (`flyctl`), free tier no longer exists |
| Sevalla (Kinsta) | ~$25–35/mo est. (compute from $18/mo + separate DB pricing) | Native (Docker/buildpacks/Nixpacks) | Newer entrant; has a "hibernation" feature to cut cost on non-production apps |
| Koyeb | $0 on free tier (1 web service + 1 Postgres DB, no card) | Native | Fits this app's scope for free, but paid plans jump straight to $79/mo — steep cliff if outgrown |
| Hetzner VPS + Coolify (self-managed) | ~$6/mo (CX23 ≈ €5.49/mo runs app+DB on one box) | Not native — GitHub Actions SSH step, or self-host [Coolify](https://coolify.io) for git-push deploys | Cheapest overall; keeps you as the one patching the VM |
| Oracle Cloud "Always Free" VM | $0 forever (4 ARM cores/24GB RAM) | Not native — same GitHub Actions SSH approach as Hetzner | Was the front-runner on cost; set aside in favor of a fully managed PaaS (ADR-003) — see that ADR for the trade-off (own reverse proxy/TLS/firewall, no native GitHub deploy) |

</details>

### Deployment method: Docker vs. each platform's native buildpack

Verified 2026-07-21 (see ADR-004): all three candidates support a custom `Dockerfile` and all
three prioritize it over their native buildpack when one is present at the repo root.

| Platform | Native buildpack | Docker support | Platform's own guidance |
|---|---|---|---|
| Railway | Railpack (replaced Nixpacks, March 2026) | Full — Dockerfile takes priority if present | Fine for a quick start; recommends a custom Dockerfile once heading toward production or deploying anywhere else |
| Render | Cloud Native Buildpacks, auto-detects Python | Full — Dockerfile takes priority if present | Native buildpack is faster to start with for simple apps; Dockerfile recommended for control over system-level dependencies or a minimal final image |
| DigitalOcean App Platform | Heroku-derived Python buildpack | Full — Dockerfile takes priority if present | Recommends bringing your own Dockerfile over buildpacks for production — buildpacks are described as too "magical" for easy debugging |

**Verdict: keep the existing `Dockerfile`.** Beyond matching each platform's own production
guidance, it's the only approach that behaves identically across all three candidates while the
final host is still undecided — a buildpack makes its own choices per platform (base image, Python
patch version, build steps), so relying on it would mean re-verifying behavior separately on
whichever host gets picked.

### Dev/staging/preview environment support (per ADR-010)

Verified 2026-07-21 — relevant to the branch strategy in ADR-010 (`main` = staging/dev,
`production` = deployed branch).

| Platform | Persistent staging | Per-PR ephemeral preview | Notes |
|---|---|---|---|
| Railway | Native "Environments" — clone the project into a second environment tracking `main`, a separate one tracking `production`; each gets its own isolated database automatically | Native "PR Environments" — auto-created when a PR opens, auto-deleted on merge/close, no plan-tier gate | Cleanest native fit for a full PR-preview → staging → production flow at no extra plan cost |
| Render | Two persistent services, each tracking its own branch | "Preview Environments" per PR at a unique URL — requires the Pro workspace plan ($19/user/month) | Persistent staging works on any plan; per-PR previews add real monthly cost on top |
| DigitalOcean App Platform | Two Apps, each tracking a different branch with auto-deploy; "Environment Support" (via Projects) groups them as Dev/Staging/Production | `deploy_pr_review` App Spec setting enables an ephemeral per-PR preview app | Both available without a plan-tier gate, but as separate App/database resources — roughly doubles the single-app cost estimate above once staging is added |

None of this ruled out any of the three — all can run the `main` (integration) / `production` (live)
two-branch model from ADR-010.

**Resolved (ADR-014): the staging tier is local, not hosted.** Rather than paying for a persistent
staging environment on Railway (which would roughly double the bill to ~$12/mo for something a solo
developer leaves idle), the chosen model is:

| Tier | Where it runs | Lifetime | Cost |
|---|---|---|---|
| Dev / integration test | Developer's machine, `docker-compose` | Always, during development | $0 |
| Release preview | Railway PR environment, on the `main` → `production` PR **only** | While that PR is open (a day or two) | <$1/mo |
| Production | Railway, tracking `production` | Always-on | ~$6/mo |

Railway not gating PR environments behind a plan tier is what makes the middle row affordable — on
Render the equivalent would require the Pro workspace at $19/user/mo. The preview is scoped to the
release PR because local Docker already covers feature-branch verification; what it *can't* cover is
whether the merged code runs **on Railway**, which is exactly what the release preview checks.

### Host portability rules (per ADR-015)

The app and database must stay deployable on **any host that runs a Docker image and a PostgreSQL
service**, with configuration changes only. This exists because ADR-013 deferred the EU-owned hosts
and set a revisit trigger before EU expansion (11.14) — that option is only real if moving stays
cheap.

| # | Rule | Current state | Task |
|---|---|---|---|
| 1 | The `Dockerfile` is the only build artifact — no platform buildpack | ✅ Already true (ADR-004) | 7.6 |
| 2 | All config from environment variables; no host-named settings module | ⚠️ `settings/heroku.py` still exists | 1.5, 7.9 |
| 3 | Bind to `$PORT` with a local fallback | ❌ Hardcoded `:8000` in the `Dockerfile` `CMD` | 7.17 |
| 4 | Migrations are a release step, not part of the container start command | ❌ `migrate &&` is inside `CMD` and the compose command | 7.11 |
| 5 | A host-independent logical dump (`pg_dump`), restore-tested on a *different* instance | ❌ Backups are "unknown/undocumented" | 3.44, 9.16 |
| 6 | Core PostgreSQL and widely-available extensions only | ✅ True today; needs to stay true | 3.45, 9.3 |
| 7 | Persistent state only in PostgreSQL and object storage, never container disk | ⚠️ Broken `MEDIA_ROOT` leftover points at local disk | 2.13, 7.18 |
| 8 | Every environment variable documented in a committed `.env.example` | ❌ Doesn't exist | 7.13 |

`DATABASE_URL` is the database contract — every candidate host (Railway, Render, DigitalOcean, Fly,
Clever Cloud, Scaleway) provides it, and `heroku.py` already consumes it via `django-environ`'s
`env.db()`. That part of the existing code is worth preserving through the settings split.

**Accepted lock-in:** Railway's git-watch deploy automation (7.15) and the release-PR preview
environment (ADR-014, 12.5). Workflow conveniences, no data involved, roughly a day to rebuild
elsewhere. Railway's native volume snapshots (12.9) are fine to use *alongside* rule 5's portable
dump — they're for fast same-host rollback, not for moving.

**Portability is tested continuously and for free.** The local `docker-compose` environment (ADR-014)
runs the same image on plain Docker with no platform involved, so a break in portability shows up as
a broken local environment rather than as a discovery mid-migration.

#### Making database migration as routine as app migration

App migration is low-risk because **every deploy rehearses it**. The database restore path, left
alone, runs for the first time on the day it matters. Closing that gap is mostly about exercising the
path, plus four traps worth naming:

| Trap | Why it bites | Task |
|---|---|---|
| `pg_dump` default flags | Emits `OWNER`/`GRANT` referencing roles that don't exist on the target — the most common cross-host restore failure | 3.46 |
| Collation differences | Text index ordering depends on the host's glibc/ICU version; indexes can be subtly wrong after a cross-host restore while everything looks fine. `REINDEX` after restore | 3.47 |
| Unverified restores | "It restored without errors" is not "the data is complete" — needs row counts, constraint validation, sequence positions | 3.47 |
| Schema drift | If production has manual DDL that the migrations don't produce, the schema can't be rebuilt anywhere — also breaks PR-environment seeding (12.10) | 3.49 |

The one that changes the risk profile is **3.48: an automated restore drill on a schedule.** Restoring
the latest dump into a throwaway PostgreSQL every week, with 3.47's checks, converts migration from a
novel procedure into one that has already run fifty times.

**Two things that make this easier than it sounds at this scale:**

- **The dataset is small** (one bakery's raw materials, recipes, products — megabytes, not gigabytes).
  A dump/restore completes in seconds, so a short maintenance window is entirely adequate. Logical
  replication for near-zero-downtime cutover is available in PostgreSQL but is unnecessary complexity
  here — revisit only if the data grows by orders of magnitude.
- **Object storage doesn't move.** Media lives in Cloudflare R2, independent of the app host by design
  (ADR-005). A host migration moves compute and database only — the uploaded files stay exactly where
  they are, with no re-upload and no URL changes.

### Static & media file storage (product photos, profile pictures)

New requirement: users can upload product photos and profile pictures (see
[project_requirements.md](project_requirements.md) backlog). Profile pictures are personal data —
see [gdpr.md](gdpr.md) §1 data inventory.

| Topic | Current | Candidate | Decision | Status |
|---|---|---|---|---|
| Static assets (CSS/JS/bundled images) | whitenoise via `STATICFILES_STORAGE`; **every project template hardcodes `/static/...`**, so manifest hashing has never actually applied | whitenoise, unchanged — this decision only affects user uploads | No change to whitenoise itself, but **the setting that configures it no longer exists**: `STATICFILES_STORAGE`/`DEFAULT_FILE_STORAGE` were deprecated in Django 4.2 and **removed in 5.1**, so the `STORAGES` dict is required by the upgrade (19.14). Removed settings are ignored, not rejected — the failure is silent loss of compression and cache-busting. The **loud** failure waits for 5.3, when `{% static %}` first activates manifest storage and a missing asset becomes a render-time 500 (mitigated by 1.3 + 1.13) | Decided ([ADR-027](decisions.md)) |
| User-uploaded media | `MEDIA_ROOT` set to a broken leftover local path, not implemented | S3-compatible object storage via `django-storages` — Cloudflare R2 is the lead candidate (zero egress, 10GB/1M-write/10M-read free tier, provider-agnostic) | Cloudflare R2, configured under the `STORAGES` dict's `"default"` key while whitenoise keeps `"staticfiles"` — the two-key split matches this decision exactly (13.11) | Decided (see ADR-005, [ADR-027](decisions.md)) |
| Why not local disk | n/a | None of Railway/Render/DigitalOcean guarantee persistent shared disk across redeploys or multiple instances | — | Decided (ruled out) |
| Why not Oracle Object Storage | n/a | Was a reasonable pairing while Oracle was a hosting candidate; weaker fit now that Oracle is set aside (ADR-003) — would add a 4th provider relationship | — | Decided (ruled out) |
| New dependencies | none | `django-storages[s3]`, `boto3` | — | Decided |

Implementation shape once confirmed: add `ImageField`s to `Product` and a new user-profile model,
configure `django-storages` against the R2 endpoint with credentials from environment variables,
validate upload type/size in a real `ModelForm`, and provision the bucket + optional custom
domain/CDN as part of deployment. All of that is broken into tasks under Epic 13
(`feature-media-storage`) in [`PRODUCTION_UPDATE_PLAN.md`](../PRODUCTION_UPDATE_PLAN.md), with the
cross-references to Epics 2/3/4/7 noted per task.

### AI insights / batch analytics service (new)

Per the new "AI-driven insights" feature (margin alerts, real-time dashboard analytics — see
[project_requirements.md](project_requirements.md) and [roadmap.md](roadmap.md)):

| Topic | Current | Decision | Status |
|---|---|---|---|
| Processing engine | n/a (new service) | **Apache Spark on Databricks — confirmed.** Re-tested against [ADR-024](decisions.md)'s null hypothesis (a scheduled query over [ADR-018](decisions.md)'s dated prices) and kept as a deliberate bet on headroom for analytics and ML beyond margin alerts, with the cost and processor consequences accepted rather than discovered | Decided ([ADR-002](decisions.md), confirmed by [ADR-036](decisions.md)) |
| Where does it run relative to the app? | n/a | **Databricks Serverless Jobs on AWS, EU (Ireland) `eu-west-1`.** Serverless job compute only — no all-purpose or interactive cluster, and no cluster lifecycle for the app to start, idle or forget to stop. Both ends stay in the EEA (Railway is EU West per [ADR-013](decisions.md)), so the data needs no Chapter V transfer mechanism; Databricks Inc. being US-headquartered is a **subprocessor/DPA** question, not a data-location one (16.8, 11.17) | Decided ([ADR-036](decisions.md)) |
| Data handover | n/a | **Django pushes a scoped extract to R2; Databricks never touches PostgreSQL.** A nightly job writes a **personal-data-free** costing extract (product, date, cost, price, margin, tenant) to a dedicated Cloudflare R2 prefix ([ADR-005](decisions.md)) and the Spark job reads only that. Direct JDBC to Railway's public proxy was rejected — it exposes the production database to a third-party network and drags supplier contacts and user accounts into GDPR transfer scope (16.9, 16.3) | Decided ([ADR-036](decisions.md)) |
| Trigger mechanism | n/a | **Nightly Databricks schedule; results POSTed back** to a plain `JsonResponse` callback ([ADR-028](decisions.md)'s two-endpoint exception) authenticated with a shared secret. No event triggering from the request path — a margin alert is a daily concern, and event runs would need debounce, retry and deduplication in the app for no user-visible gain. The callback is the app's only internet-facing unauthenticated write path, so shared secret + tenant scoping + rate limiting are requirements, and it is the one route besides the cover and login pages exempt from `LoginRequiredMiddleware` (16.10, 16.11) | Decided ([ADR-036](decisions.md)) |
| Cost model | n/a | **Serverless job compute only, hard ceiling ~$15/mo**, spend alert configured before the first production run (16.12). Total infrastructure goes ~$6/mo → ~$21/mo — a 3.5× rise against [ADR-016](decisions.md)'s zero revenue, treated as a funded bet. **The DBU rate is deliberately not recorded here**: serverless pricing is region- and tier-dependent and changes, so 16.8 measures one real run at provisioning instead. Community Edition remains unusable for this (notebook-only, no job scheduling) | Decided ([ADR-036](decisions.md)) |
| Extract schema contract | n/a | **Versioned.** The Django job and the Databricks notebook live in different repositories and evolve on different schedules; the extract manifest carries a version and the notebook rejects an unknown one, so a schema change fails loudly instead of producing quietly wrong insights (16.13) | Decided ([ADR-036](decisions.md)) |

### Tenant data export tooling (new)

Per ADR-008/ADR-009 in [decisions.md](decisions.md): two distinct export mechanisms need to be
built, beyond the existing bulk admin CSV export.

| Topic | Current | Candidate | Decision | Status |
|---|---|---|---|---|
| Tenant full data export format | none | Portable, DBMS-agnostic format — plain ANSI-compatible SQL (`CREATE TABLE`/`INSERT`, not a Postgres-specific `pg_dump` custom format) or a per-table CSV bundle + relationship manifest | **A ZIP of one CSV per tenant-scoped table plus a `manifest.json`** carrying the export timestamp, schema version, and per table its columns, types, primary key and FK map. It serves both audiences [ADR-008](decisions.md) named — a spreadsheet for the owner, a loadable bundle for whoever they hire. Hand-generated ANSI SQL was rejected as a type-map and quoting burden that only serves a developer; `dumpdata` JSON was rejected as a *Django* format, which is the dependency ADR-008 existed to avoid. **The manifest is the deliverable** — CSV loses types, null-vs-empty and every relationship (14.1, 14.3) | Decided ([ADR-035](decisions.md)) |
| Tenant full data export mechanism | none | A management command / service that, given a tenant, walks every tenant-scoped table and emits the portable export — likely built on Django's `dumpdata`/serializers or hand-rolled SQL generation | **One service function, exposed twice:** an Owner-only download in the settings area ([ADR-023](decisions.md)'s tenant self-administration surface, gated by an [ADR-020](decisions.md) capability name) and a management command for support. Synchronous is adequate at [ADR-013](decisions.md)'s scale but is re-checked in 14.6, since a tenant with years of goods receipts is not today's catalogue. Money and quantities are written at **full stored precision**, never [ADR-018](decisions.md)'s 2-dp presentation rounding (14.6) | Decided ([ADR-035](decisions.md)) |
| GDPR personal-data export | Bulk CSV export exists but isn't subject-scoped | A second, separate export scoped to one data subject's personal data across models | Direction decided (separate from bulk export, [ADR-009](decisions.md)) — implementation Open, tracked in Epic 15. It **may** reuse [ADR-035](decisions.md)'s bundle shape scoped to one subject; that is 15.2's call, not a stack decision | Proposed — Epic 15 |

## Quality tooling

| Topic | Current | Candidate | Decision | Status |
|---|---|---|---|---|
| Formatting/linting | none | `ruff` (+ `black` if not fully covered by ruff, + `isort` if not covered either) | **`ruff` does both** — `ruff check` and `ruff format`. No `black`, no `isort`, no `flake8`: `ruff format` is a deliberate reimplementation of black's style, so running both spends a dependency and a CI step to reach the same output (6.10) | Decided ([ADR-034](decisions.md)) |
| Template linting | none | an HTML/Django template linter, if template consistency is wanted | **`djlint`** — adopted, a pip package so no Node enters dev. The work itself is 5.8; 6.11 wires it into the CI gate. Standalone CSS/JS linting (`stylelint`/`prettier`) stays deferred on the same no-Node grounds as the asset pipeline | Decided ([ADR-030](decisions.md)) |
| Testing | empty `tests.py` stubs in every app, no coverage | unit tests (models, costing, permissions, exports) + integration tests for CRUD flows + dedicated cross-tenant isolation tests (ADR-008) | **`pytest` + `pytest-django` + `pytest-cov`**, replacing `manage.py test`. Django's own runner was close and consistent with this project's "use the framework's rails" streak — it lost on the shape of *this* suite: costing is table-driven across unit conversions × VAT boundaries × rounding × recursion depth (`parametrize`), and [ADR-008](decisions.md)'s isolation tests want composable fixtures. Little lock-in — `pytest-django` wraps Django's test-database machinery rather than replacing it. `--cov-fail-under=70` is where [ADR-031](decisions.md)'s floor is enforced (6.23, 6.22) | Decided ([ADR-034](decisions.md)) |
| Tool configuration | none | — | **A `pyproject.toml` holding only `[tool.*]` sections.** Not a packaging file, declares no dependencies, and must never grow `[project]` or `[build-system]` — [ADR-029](decisions.md)'s requirements-file model is untouched. `ruff`, `pytest`, `pytest-django` and `pytest-cov` join `djlint` in `requirements/dev.in` with the owner comments [ADR-029](decisions.md) requires | Decided ([ADR-034](decisions.md)) |

## Open questions

- ~~Is Heroku actually still the deployment target, or has that changed?~~ Resolved: no — currently
  self-hosted, moving to Railway (EU West) per [ADR-013](decisions.md). `settings/heroku.py` is a
  leftover to be removed (1.5, 7.9).
- ~~Any hosting/budget constraints that rule out a candidate?~~ Resolved in practice: phase 1 is a
  **free pilot with one tenant** ([ADR-016](decisions.md)), so there is no revenue to fund
  infrastructure — ~$6/mo is the working budget, which is what ADR-013 and ADR-014 were sized against.
- Any org/team constraints (existing infra, required cloud provider, compliance requirements)
  that should narrow these choices before Phase 3+ of `PRODUCTION_UPDATE_PLAN.md` starts? Partly
  answered: the compliance constraint is now explicit — EU data residency (ADR-013) plus food-law
  traceability records with a legal retention floor ([ADR-017](decisions.md), 10.9), which raises the
  cost of losing the database and so raises the bar on 9.16's backup strategy.
