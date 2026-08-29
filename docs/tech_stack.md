# Tech Stack

**What this project is built with — decided facts only.** Nothing here is open or provisional. A
stack question that has no answer yet is an open decision and belongs in
[roadmap.md](roadmap.md); the *reasoning* behind every row below is in the ADR named beside it and is
deliberately not repeated here.

- **Current** is factual — don't change it without checking the code.
- **Decision** is the outcome in a line, plus the backlog task IDs that deliver it.
- Once a row is decided it must also exist as a task in
  [`PRODUCTION_UPDATE_PLAN.md`](../PRODUCTION_UPDATE_PLAN.md).

[Runtime](#runtime) · [Dependencies](#dependencies) · [Backend](#backend-architecture) ·
[Data model](#data-model) · [Frontend](#frontend) · [Infrastructure](#infrastructure--operations) ·
[Processors](#processors--data-residency) · [Portability](#host-portability-rules) ·
[Quality tooling](#quality-tooling)

## Runtime

| Layer | Current | Decision | ADR |
|---|---|---|---|
| Python | 3.8 (`runtime.txt`), Dockerfile 3.9-slim — **both EOL** | **3.13** — spans Django 5.2 and 6.2. `python:3.13-slim` is the single source; `runtime.txt` deleted | [025](decisions.md) |
| Django | 3.2 — **EOL since April 2024** | **5.2 LTS, direct from 3.2** (no 4.2 stop), supported to April 2028. Next hop 6.2 LTS, H2 2027 | [025](decisions.md) |
| Database | PostgreSQL, unpinned; no Postgres service in `docker-compose.yaml` | **PostgreSQL 17**, pinned identically local and production. Majors must match | [026](decisions.md) |
| DB topology | Separate Postgres container from the app | **Always separate services** — never bundled in one image | [007](decisions.md) |
| Multi-tenancy | None — single-bakery schema | **Shared database, row-level tenant isolation** via a `Bakery` FK on every business table | [006](decisions.md)/[008](decisions.md) |
| WSGI/ASGI server | gunicorn 20.1.0 (WSGI) | **gunicorn, WSGI, sync workers**, latest pinned at lock time (7.14) | [036](decisions.md) |

## Dependencies

Pinned, reviewed, UTF-8, split by environment, generated from a lock workflow and never hand-edited.
[ADR-025](decisions.md) fixes the constraint — latest release compatible with Django 5.2 on Python
3.13, re-evaluated at every recompile — and [ADR-029](decisions.md) the mechanism. **Exact pins live
only in the generated lock files**, never here.

| Package | Current | Decision | ADR |
|---|---|---|---|
| `psycopg2-binary` | 2.9.6 | → **`psycopg[binary]` 3** (19.6) | [025](decisions.md) |
| `whitenoise` | 5.2.0 | Latest compatible at lock time | [025](decisions.md) |
| `django-environ` | 0.4.5 | Latest compatible. **Stays** — it owns `env.db()`, the `DATABASE_URL` contract | [025](decisions.md) |
| `Pillow` | 10.4.0 | **Removed until Epic 13**, then latest compatible (13.1) | [025](decisions.md)/[029](decisions.md) |
| `django-mathfilters` | 1.0.0 | **Dropped** — classifiers stop at Django 3.x, a hard upgrade blocker (19.5) | [025](decisions.md) |
| `asgiref` / `sqlparse` / `pytz` | pinned to Django 3.2's requirements | **Removed from the hand-written file** — the first two are transitive; `pytz` goes entirely | [025](decisions.md) |
| `environ` 1.0 / `dj-database-url` 0.5.0 | both present | **Both removed** — a module-name collision and an unused duplicate of `env.db()` | [025](decisions.md) |
| `sentry-sdk[django]` | none | **Added** to `base.in` | [031](decisions.md) |
| Media storage | none | `django-storages[s3]` + `boto3` against Cloudflare R2, entering in Epic 13 | [005](decisions.md) |
| Management | single UTF-16LE `requirements.txt` | **`uv pip compile` over `requirements/{base,dev,prod}.in` → pinned, hashed `.txt`.** Requirements-file mode, not `pyproject.toml`. `--generate-hashes` + `--require-hashes`, `--python-version 3.13`; `dev`/`prod` compiled against `-c base.txt`. `uv` is build tooling, never an app dependency (19.12, 19.16) | [029](decisions.md) |
| Hygiene | none | **The `.in` file is the register:** every line carries a comment naming its purpose and owning task; a line without one is removed at the next recompile. Recompile on `.in` change, on a security advisory, otherwise monthly | [029](decisions.md) |

**The resulting set** — six direct runtime dependencies in `base.in`: Django, `psycopg[binary]`,
`whitenoise`, `django-environ`, `gunicorn`, `sentry-sdk[django]`, joined in Epic 13 by `Pillow`,
`django-storages[s3]` and `boto3`. `dev.in` holds `ruff`, `pytest`, `pytest-django`, `pytest-cov`,
`djlint`, `pip-audit`, `coverage`. `prod.in` is `-r base.in` only — intended, not an omission.
Version facts verified 2026-08-10.

## Backend architecture

| Topic | Current | Decision | ADR |
|---|---|---|---|
| Settings layout | `settings/base.py` (dev defaults) + `heroku.py` | **`base.py` + `local.py` + `test.py` — no `production.py`.** `base.py` *is* production: everything from the environment, **no default at all** for `SECRET_KEY`/`ALLOWED_HOSTS`/`DEBUG`, so a missing variable fails at boot and a forgotten `DJANGO_SETTINGS_MODULE` lands on the safe module (1.5, 2.19) | [028](decisions.md) |
| Business logic | inline in `control/views.py`, duplicated across views and model properties | **`control/services/` — plain functions, frozen dataclass returns, batch-first.** `cost_products(queryset, …)` is the primary API; single-object costing wraps it. Model costing properties and the inline `float()` math are **deleted, not ported** (4.1, 4.19, 4.20) | [028](decisions.md) |
| API layer | none | **None, and no framework pre-selected.** The health endpoint and the Epic 16 callback are plain `JsonResponse` views | [028](decisions.md) |
| Auth / permissions | mix of no auth, `staff_member_required`, ad hoc template checks | **Django's built-in auth views are the only auth surface**; `accounts.views.user_login` is deleted (4.5). `LoginRequiredMiddleware` makes login the default, with `@login_not_required` on the cover page, login view and Epic 16 callback (2.17). Capabilities are Django permission codenames resolved by a **custom authentication backend** against the active membership, so stock mixins, decorators and `{% if perms %}` keep working (2.20, 2.21) | [020](decisions.md)/[027](decisions.md)/[028](decisions.md) |
| Caching | none | **None in the first release.** Query design is the lever: batch costing (4.19), `select_related`/`prefetch_related`, the connection pool. The batch API carries a per-tenant version stamp from day one so a cache bolts on at that seam (4.20, trigger 7.20) | [028](decisions.md) |
| Email | none | **Brevo over SMTP** via Django's built-in `smtp.EmailBackend` — no dependency. Covers invitations **and** password reset, which becomes email-only (7.21, 7.22, 5.24, 11.16) | [028](decisions.md) |
| Connection pooling | none | **Django's native psycopg pool** (`DATABASES["OPTIONS"]["pool"]`) plus `CONN_HEALTH_CHECKS`. In-process — no PgBouncer (7.19) | [027](decisions.md) |

### Data model

Shape-of-the-schema decisions; the business-*meaning* ones are in
[project_requirements.md](project_requirements.md). All settled before Epic 3's migrations are
written.

| Topic | Current | Decision | ADR |
|---|---|---|---|
| Ingredient line | two parallel models (`Bs_Ingredients`, `Recipe_Ingredients`) | **One shared `RecipeLine`** — typed parent (`parent_product` XOR `parent_base_recipe`), typed component (`component_material` XOR `component_recipe`), both XORs as database `CHECK` constraints, **not** `clean()` (which does not run on `bulk_create`). `Product` and `Base_recipes` stay separate — this collapses the *lines* (3.19, 3.73) | [032](decisions.md) |
| Recipe nesting & cycles | products reference raw materials only | A product's line **may reference a base recipe**, costing recursing into it. Cycles rejected at save time plus depth-guarded in the service layer (3.59, 4.16) | [022](decisions.md) |
| Cost provenance | none — a cost is a bare number | Latest goods receipt by *receipt date* sets current cost; a manual price survives as a labelled estimate; the service layer returns **provenance** with every figure (3.62, 4.17) | [022](decisions.md) |
| Units & categories | free-text `CharField`s (`unit`, `categorie`) | **Both lookup tables, different edit rights.** Units carry a conversion factor and are **not** tenant-editable (3.52). Categories are one tenant-scoped `Category` with a `kind` discriminator, archivable, unique on `(bakery, kind, name)`, **tenant-editable** (3.74) | [018](decisions.md)/[032](decisions.md) |
| Calculated values | recomputed inline per request in `float()` | **Derived, never persisted** (3.17) | [018](decisions.md) |
| Deletion semantics | hard deletes everywhere | **Soft delete:** `Supplier`, `RawMaterial`, `Product`, `Base_recipes`. **Hard delete:** ingredient lines. Tenant scope and archived state combine in **one** base manager (3.55) | [019](decisions.md) |
| Roles | mix of no auth and ad hoc checks | **Three per-tenant roles** (Owner / Staff / Read-only) on a **membership record** (user × bakery × role); checks capability-named, never `role == "owner"` (3.58, 2.16) | [020](decisions.md) |
| Administration surfaces | Django admin and in-app settings overlap | **Two audiences.** In-app settings = tenant surface (scoped, role-checked, audited). Django admin = **superuser-only** support tooling, deliberately cross-tenant, never linked from the tenant UI. `ModelAdmin` does **not** apply tenant-scoped managers (2.15) | [019](decisions.md) |
| Money & quantity types | mixed (`CharField` quantity, `float()` math) | **`Decimal` end-to-end.** Quantities ≥ `Decimal(12,4)` (`12,6` safer), money beyond 2 dp internally, rounded to 2 dp **only at presentation** with an explicit tested rule (3.50, 3.51, 6.16) | [018](decisions.md) |
| Price basis | `RawMaterial.price`, implicit meaning | `purchase_price` + `pack_quantity` + `purchase_unit` as the invoice states it; derived cost never persisted (3.10) | [018](decisions.md) |
| Canonical costing units | none | **kilogram / litre / each**, one per dimension; purchase units convert via a factor in the reference table | [018](decisions.md) |
| VAT | inconsistent between products and dashboard math | All stored money **net (ex-VAT)**; dated rate table (`code`, `percent`, `valid_from`, `valid_to`); product references a rate **code** (3.15, 3.53) | [018](decisions.md) |
| Price history | none — prices overwritten in place | **Two sources:** input prices from goods receipts; sale prices as dated `ProductPrice` rows (3.16) | [018](decisions.md) |
| Traceability entities | none; a pure current-state catalogue | **Header + lines, full event chain.** `GoodsReceipt` → `GoodsReceiptLine` (material, supplier lot, qty, unit, best-before, price in ADR-018's shape); `ProductionRun` → `Consumption` → `Batch` → `OutboundRecord`. **A lot is an event, not an attribute** (17.1, 17.2) | [033](decisions.md) |
| Lot code generation | n/a | **`YYYYMMDD-NNN`**, resetting daily, unique on `(bakery, lot_code)`, allocated **server-side inside the batch-creating transaction** — never client-side, never by counting rows. Gaps after rollback acceptable; collisions not (17.13) | [033](decisions.md) |
| Stock / on-hand | none | **Derivable, deliberately not surfaced.** `Consumption.quantity_consumed` makes on-hand computable; no stock field, no stock page, no low-stock alert this round (17.14) | [033](decisions.md) |

**Constraint on Epic 3:** build `RawMaterial` knowing the event tables are coming — **no `lot` field,
no `stock` field**, numeric `quantity` with a unit FK.

## Frontend

Current column measured 2026-08-16.

| Topic | Current (measured) | Decision | ADR |
|---|---|---|---|
| Templating | 32 templates, 4,277 lines, **zero `{% extends %}`, zero `{% include %}`**; navbar duplicated 32× | **Shared `base.html` + `{% include %}` partials** in `<app>/templates/partials/`. `django-template-partials` not adopted (5.1, 5.2) | [030](decisions.md) |
| CSS framework | Bootstrap **5.0.0** vendored (May 2021) | **Bootstrap 5.3.x** — same major, so classes stay valid: an upgrade, not a restyle (5.4). Full stylesheet ships un-tree-shaken (~230KB minified), accepted as a cached static asset | [030](decisions.md) |
| Asset pipeline | none; 16 CSS files, 922 lines, four byte-identical; no `package.json` | **None — no Node, no bundler.** Consolidate the CSS, native custom properties + nesting, whitenoise for cache-busting. Revisit at a few hundred lines of custom JS or SCSS-level Bootstrap customization (5.6) | [030](decisions.md) |
| Interactivity | **7 custom JS files, all 0 bytes** | **HTMX**, vendored at a pinned version, plus small vanilla modules; server returns HTML fragments. Built as **progressive enhancement** — forms and links work with JS disabled (5.7, 5.25) | [030](decisions.md) |
| SPA? | n/a | **No** | [030](decisions.md) |
| Static references | **Zero `{% static %}`**; 23 templates hardcode `/static/...` | Switch to `{% static %}` (5.3). **Load-bearing:** whitenoise is the only cache-busting mechanism and does nothing for hardcoded paths, and `ManifestStaticFilesStorage` raises `ValueError` **at render time** for a file missing from the manifest — a missing asset becomes a 500, not a silent 404. Sequence after 1.3; lean on 1.13's CI `collectstatic` | [027](decisions.md)/[030](decisions.md) |
| Vendored assets | Bootstrap, HTMX — invisible to `requirements/*.in` | ADR-029's owner/purpose register extends to them **by hand** (5.25) | [030](decisions.md) |
| Template linting | none | **`djlint`** — a pip package, so no Node in dev (5.8, CI in 6.11) | [030](decisions.md)/[034](decisions.md) |
| Accessibility target | none stated | **WCAG 2.2 Level A** (revisit trigger 10.15). Django's own form rendering supplies a material share as framework output — real label association, `aria-describedby`, `aria-invalid`, `<fieldset>`/`<legend>` (5.22) | [021](decisions.md)/[027](decisions.md) |
| Device / browser matrix | responsive, matrix unstated | Phone→desktop; current **and previous** major Chrome/Firefox/Safari/Edge. No IE11, no native app (5.13, 5.17) | [021](decisions.md) |
| Localization | English only, `€` hardcoded | Ship `en-IE`/EUR; **`gettext` on display text and one currency formatter from day one** — no hardcoded `€` (5.15, 5.16) | [021](decisions.md) |
| Performance budget | none | p95 < 500 ms pages, < 2 s dashboard aggregate, ~10 concurrent users/tenant. A documented budget, **not** a CI gate (5.14) | [021](decisions.md) |

## Infrastructure / operations

| Topic | Current | Decision | ADR |
|---|---|---|---|
| Hosting | Self-hosted home server, Docker via Portainer; Postgres in a separate container | **Railway, Hobby plan, EU West (Amsterdam)** — ~$6/mo, billed on actual per-second usage | [013](decisions.md) |
| Dev/test environment | developer's machine, ad hoc | **Local `docker-compose`** — same Dockerfile as production, app and DB separate. **No persistent hosted staging** | [014](decisions.md) |
| Release preview | none | A **Railway PR environment on the `main` → `production` PR only**, open a day or two, <$1/mo. Local Docker covers feature branches; what it cannot cover is whether merged code runs on Railway (12.5) | [014](decisions.md) |
| Containerization | `Dockerfile` + `docker-compose.yaml` (expects an external `bakery_simple` network) | **Custom Dockerfile** as the deploy artifact, never the platform buildpack | [004](decisions.md) |
| Static storage | whitenoise | whitenoise unchanged, but configured through `STORAGES`' `"staticfiles"` key — `STATICFILES_STORAGE` was **removed in Django 5.1** and removed settings are *ignored, not rejected*, so compression and cache-busting fail silently (19.14) | [027](decisions.md) |
| Media storage | `MEDIA_ROOT` points at a broken leftover path nothing uses | **Cloudflare R2** via `django-storages` on `STORAGES`' `"default"` key — zero egress, 10 GB free tier, provider-agnostic. **Product photos only this round**; an `ImageField` on `Product`, credentials from env (2.5), type/size validated in a real `ModelForm` (4.9, 13.7, 13.11) | [005](decisions.md) |
| CI/CD | none | **GitHub Actions extending the Epic 1 workflow, behind a 70% repo-wide coverage floor.** Merge gate: test suite, `ruff` + `djlint`, the migration/`collectstatic`/`docker build` checks from 1.11/1.13, `pip-audit` against the hashed lock, Dependabot raising dependency PRs. **No SAST or image scanning** this release | [031](decisions.md) |
| Deploy trigger | manual, on the home server | **Railway git-watch on `production`**, `migrate` as the **pre-deploy command**. 6.14 is satisfied by **branch protection**: failing checks block the merge, and only a merge deploys | [031](decisions.md) |
| Error tracking | none | **Sentry SaaS, free Developer tier, EU region (`de.sentry.io`)** — the region is fixed at organisation creation and **cannot be changed afterwards**. `send_default_pii` stays off and a `before_send` scrubber is mandatory (7.2, 7.23, 11.6) | [031](decisions.md) |
| Uptime monitoring | none | **UptimeRobot free tier** — 5-minute HTTPS **keyword** check against 7.4's health endpoint, so a health endpoint reporting a dead database fails instead of passing on its HTTP 200. Deliberately external to Railway (7.5) | [031](decisions.md) |
| Backups | unknown/undocumented; Railway backups are **not automatic** and have **no PITR** | **Two unequal tracks** (below). PITR rejected; RPO up to 24 h accepted, revisit at the second paying tenant | [031](decisions.md) |

Everything above lands at **$0/mo** on free tiers; the only new recurring cost is R2 storage, and a
few hundred MB of dumps sits inside its 10 GB free tier alongside the media.

### The two backup tracks

| Track | Mechanism | Answers | Restorable elsewhere? |
|---|---|---|---|
| Same-host rollback | Railway daily/weekly/monthly volume snapshots (12.9) | "The release an hour ago corrupted data — put it back" | **No** — copy-on-write, Railway-only |
| Host-independent archive | Nightly GitHub Actions `pg_dump -Fc --no-owner --no-privileges`, `age`-encrypted client-side, into a **separate** R2 bucket on a 7-daily / 4-weekly / 12-monthly lifecycle (3.70, 3.71) | "Railway is gone / we are moving host / that row was wrong three months ago" | **Yes** — what rule 5 requires |

Three properties that shape the tasks: the dump job runs **outside the host it backs up**, so CI holds
backup-scoped, rotatable database credentials reaching Postgres over Railway's public proxy (3.41),
not the app's. Client-side `age` means Cloudflare holds ciphertext it cannot read, and **a lost
private key is proven data loss** — 3.72 owns the key and 3.48's weekly drill must **decrypt** to
prove it still works. And backup lifetime is a separate clock from record retention: the 7/4/12
schedule is what bounds the erasure answer at five weeks, one year at the outside.

### Processors & data residency

Every vendor is a GDPR **processor** needing a DPA and a subprocessor entry. Bakery-the-product is
itself a processor for each tenant — see
[project_requirements.md](project_requirements.md) "Controller / processor model".

| Processor | Purpose | Personal data involved | DPA |
|---|---|---|---|
| **Railway** ([013](decisions.md)) | Runs the app, stores the DB | Everything | Pending (12.7). US-incorporated, data in EU West (Amsterdam) |
| **Cloudflare R2** ([005](decisions.md)) | Media bucket, a **separate** backup bucket, the Epic 16 extract prefix | Product photos (not personal); backups are `age`-encrypted client-side, so ciphertext only; the extract is personal-data-free | Pending (11.6) |
| **Brevo** ([028](decisions.md)) | Transactional mail — invitations, password reset | Recipient email, display name, reset/invite token | Pending (11.6, 11.16). French-owned, EU data centres, ISO 27001:2022, DPA included by default. **No transfer safeguard needed** |
| **Sentry** ([031](decisions.md)) | Unhandled exceptions and their context | **Undefined by nature** — whatever a traceback carries. Mitigated at source by 7.23 | Pending (11.6). EU region (`de.sentry.io`), irreversible after creation. US-incorporated |
| **Databricks Inc.** ([036](decisions.md)) | Nightly Spark job computing margin alerts and analytics | **None by design** — reads only the personal-data-free R2 extract, never touches PostgreSQL | Pending (11.17, 16.4). US-headquartered — a subprocessor question, not a data-location one |
| **AWS** (EU Ireland `eu-west-1`) | Underlying cloud for Databricks Serverless job compute | None by design | Pending (11.17) |

**Storage location — satisfied.** GDPR Art. 1(3) bars restricting free movement of personal data
within the Union, so Irish tenants' data need not sit in Ireland and EU West (Amsterdam) qualifies.
**Both the app and the PostgreSQL service/volume must be in that region** — Railway's default is US
West, so it must be set before any service is created (12.8). Databricks and AWS sit in EU Ireland
and the extract carries no personal data, so the insights path needs no Chapter V mechanism.
Vendor-level transfer safeguards are still an open decision — [roadmap.md](roadmap.md) 11.15.

### Host portability rules

The app and database stay deployable on **any host that runs a Docker image and a PostgreSQL
service**, with configuration changes only — the option 11.14's residency revisit depends on. Eight
standing rules from [ADR-015](decisions.md); the tasks that close each gap are in the backlog.

1. The `Dockerfile` is the only build artifact — no platform buildpack (7.6).
2. All config from environment variables; no host-named settings module. `DATABASE_URL` is the database contract (1.5, 7.9).
3. Bind to `$PORT` with a local fallback (7.17).
4. Migrations are a release step, not part of the container start command (7.11, 12.11).
5. A host-independent logical dump (`pg_dump`), restore-tested on a *different* instance (3.44, 3.70).
6. Core PostgreSQL and widely-available extensions only (3.45).
7. Persistent state only in PostgreSQL and object storage, never container disk (2.13, 7.18).
8. Every environment variable documented in a committed `.env.example` (7.13).

**Accepted lock-in:** Railway's git-watch deploys (7.15) and the release-PR preview (12.5) — workflow
conveniences, no data involved. Native volume snapshots (12.9) are fine *alongside* rule 5's portable
dump. Portability is tested continuously and for free, because local `docker-compose` runs the same
image on plain Docker with no platform involved.

**Restore is the path that never rehearses itself**, unlike deploys — hence 3.46 (`pg_dump` flags
emitting `OWNER`/`GRANT` for roles absent on the target), 3.47 (collation-dependent index ordering,
and verifying row counts, constraints and sequence positions rather than trusting a clean exit),
3.49/12.10 (schema drift from manual DDL), and above all **3.48's automated weekly restore drill**,
which converts migration from a novel procedure into one that has already run fifty times. The
dataset is megabytes, so a short maintenance window is adequate and logical replication is
unnecessary; media lives in R2 and does not move.

### AI insights / batch analytics service

[ADR-002](decisions.md), scoped by [ADR-036](decisions.md). Epic 16.

| Topic | Decision |
|---|---|
| Engine and location | **Apache Spark on Databricks Serverless Jobs, AWS EU (Ireland) `eu-west-1`.** Serverless only — no cluster lifecycle to start, idle or forget to stop |
| Data handover | **Django pushes a scoped extract to R2; Databricks never touches PostgreSQL.** A nightly job writes a **personal-data-free** extract (product, date, cost, price, margin, tenant) to a dedicated R2 prefix (16.3, 16.9) |
| Trigger | **Nightly Databricks schedule; results POSTed back** to a plain `JsonResponse` callback authenticated with a shared secret. No event triggering. It is the app's only internet-facing unauthenticated write path — shared secret, tenant scoping and rate limiting are requirements (16.10, 16.11) |
| Cost model | **Hard ceiling ~$15/mo**, spend alert before the first production run; total infrastructure goes ~$6 → ~$21/mo. The DBU rate is deliberately not recorded — 16.8 measures one real run |
| Extract schema | **Versioned.** The manifest carries a version and the notebook rejects an unknown one, so a schema change fails loudly instead of producing quietly wrong insights (16.13) |

### Tenant data export tooling

| Topic | Decision | ADR |
|---|---|---|
| Tenant full export — format | **A ZIP of one CSV per tenant-scoped table plus a `manifest.json`** (timestamp, schema version, and per table its columns, types, primary key and FK map). **The manifest is the deliverable** — CSV alone loses types, null-vs-empty and every relationship (14.1, 14.3) | [035](decisions.md) |
| Tenant full export — mechanism | **One service function exposed twice:** an Owner-only settings download gated by a capability name, and a management command. Synchronous, re-checked in 14.6. Money and quantities written at **full stored precision**, never 2-dp presentation rounding | [035](decisions.md) |
| GDPR personal-data export | A separate, **subject-scoped** export — Epic 15, distinct from the bulk admin CSV export and from the tenant-wide export. Whether it reuses ADR-035's bundle shape is 15.2's call, not a stack decision | [009](decisions.md) |

## Quality tooling

| Topic | Current | Decision | ADR |
|---|---|---|---|
| Formatting / linting | none | **`ruff` does both** — `ruff check` and `ruff format`. No `black`, `isort` or `flake8` (6.10) | [034](decisions.md) |
| Template linting | none | **`djlint`** (5.8, 6.11) | [030](decisions.md)/[034](decisions.md) |
| Testing | empty `tests.py` stubs, no coverage | **`pytest` + `pytest-django` + `pytest-cov`**, replacing `manage.py test`. `--cov-fail-under=70` is where ADR-031's floor is enforced (6.22, 6.23) | [034](decisions.md) |
| Tool configuration | none | **A `pyproject.toml` holding only `[tool.*]` sections** — not a packaging file, declares no dependencies, must never grow `[project]` or `[build-system]` | [034](decisions.md) |
