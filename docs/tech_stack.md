# Tech Stack

**Current** is factual — don't change it without checking the code. **Decision** is the outcome in a
line; **the reasoning lives in the ADR named beside it**, not here. Never write code against a
`Proposed`/`Open` row as if it were final.

**No `Open` rows remain as of 2026-08-26** — Epic 9 is closed ([roadmap.md](roadmap.md)). A new stack
question goes back in as an `Open` row here *and* as a new Epic 9 task; it does not get answered in
passing. Once a row is Decided it must also appear as a task in
[`PRODUCTION_UPDATE_PLAN.md`](../PRODUCTION_UPDATE_PLAN.md).

## Runtime

| Layer | Current | Decision | ADR |
|---|---|---|---|
| Python | 3.8 (`runtime.txt`), Dockerfile uses 3.9-slim — **both EOL** (Oct 2024 / Oct 2025) | **3.13** — spans Django 5.2 and 6.2, so the whole planned path needs no Python change. `python:3.13-slim` is the single source; `runtime.txt` is deleted | [025](decisions.md) |
| Django | 3.2 — **EOL since April 2024** | **5.2 LTS, direct from 3.2** (no 4.2 stop). Supported to April 2028 — a longer runway than current stable 6.1 (Dec 2027). Next hop **6.2 LTS**, H2 2027 | [025](decisions.md) |
| Database | PostgreSQL, version unpinned; `docker-compose.yaml` has no Postgres service at all | **PostgreSQL 17**, pinned identically local and production. Majors must match; a bump is deliberate and restore-tested, never drift | [026](decisions.md) |
| DB topology | Self-hosted: separate Postgres container from the app | **Always separate services** — never bundled in one image | [007](decisions.md) |
| Multi-tenancy | None — single-bakery schema | **Shared database, row-level tenant isolation** via a `Bakery` FK on every business table | [006](decisions.md)/[008](decisions.md) |
| WSGI/ASGI server | gunicorn 20.1.0 (WSGI) | **gunicorn, WSGI, sync workers**, latest pinned at lock time. Revisit only if the insights dashboard needs SSE/WebSocket push (7.14) | [036](decisions.md) |

## Dependencies

**Strategy:** pinned, reviewed, production-safe dependencies; UTF-8 encoding; split by environment;
generated from a lock workflow, never hand-edited. [ADR-025](decisions.md) fixes the **constraint** —
latest release compatible with Django 5.2 on Python 3.13 — and [ADR-029](decisions.md) the mechanism.
Exact pins live only in the generated lock files, never here or in the append-only ADR log, and the
constraint is re-evaluated at **every** recompile.

| Package | Current | Decision | ADR |
|---|---|---|---|
| `psycopg2-binary` | 2.9.6 | → **`psycopg[binary]` 3** (native in Django since 4.2; psycopg2 is maintenance-only) | [025](decisions.md) |
| `whitenoise` | 5.2.0 | Latest compatible at lock time (6.12.0 confirmed 2026-08-10) | [025](decisions.md) |
| `django-environ` | 0.4.5 | Latest compatible (0.14.0 confirmed 2026-08-10). **Stays** — it owns `env.db()`, the `DATABASE_URL` contract | [025](decisions.md) |
| `Pillow` | 10.4.0 | **Removed until Epic 13**, then latest compatible (12.3.0 confirmed 2026-08-10). No `ImageField` and no import exists (verified 2026-08-16); returns via 13.1 | [025](decisions.md)/[029](decisions.md) |
| `django-mathfilters` | 1.0.0 | **Dropped** — last released Feb 2020, classifiers stop at Django 3.x, so it blocks the upgrade outright. Its two templates do cost math ADR-018 ruled wrong (19.5) | [025](decisions.md) |
| `asgiref` / `sqlparse` / `pytz` | pinned to Django 3.2's requirements | **Removed from the hand-written file.** The first two are Django's own transitive deps and belong in the lock file; `pytz` goes entirely (dropped in Django 5.0, `zoneinfo` replaces it, nothing imports it) | [025](decisions.md) |
| `environ` 1.0 / `dj-database-url` 0.5.0 | both in `requirements.txt` | **Both removed.** `environ` is an unrelated package whose top-level module collides with `django-environ`'s — an install slip and a live hazard. `dj-database-url` is imported nowhere and duplicates `env.db()` | [025](decisions.md) |
| `sentry-sdk[django]` | none | **Added** to `base.in` with an owner comment | [031](decisions.md) |
| Media storage | none | `django-storages[s3]` + `boto3` against **Cloudflare R2**, entering in Epic 13 | [005](decisions.md) |
| Dependency management | single UTF-16LE `requirements.txt` | **`uv pip compile` over `requirements/{base,dev,prod}.in` → pinned, hashed `.txt`.** Requirements-file mode, **not** `pyproject.toml` — the format the `Dockerfile`, Railway and every fallback host already consume. `--generate-hashes` + `--require-hashes`, `--python-version 3.13`, and `dev`/`prod` compiled against `-c base.txt`. `uv` is pinned build tooling, never an app dependency (19.12, 19.16) | [029](decisions.md) |
| Dependency hygiene | reviewed 2026-08-10 — six of twelve entries removed with a named reason each | **The `.in` file is the register:** every line carries a comment naming its purpose and owning task; a line without one is removed at the next recompile. Transitive deps live only in the generated `.txt`. Recompile on `.in` change, on a security advisory, otherwise monthly | [029](decisions.md) |

**The resulting set:** six direct runtime dependencies in `base.in` — Django, `psycopg[binary]`,
`whitenoise`, `django-environ`, `gunicorn`, `sentry-sdk[django]` — with `Pillow`,
`django-storages[s3]` and `boto3` joining in Epic 13. `dev.in` holds `ruff`, `pytest`,
`pytest-django`, `pytest-cov`, `djlint`, `pip-audit`, `coverage`. `prod.in` is `-r base.in` only,
which is the intended shape rather than an omission. Version facts verified 2026-08-10 against the
[Django release page](https://www.djangoproject.com/download/), the
[Django install FAQ](https://docs.djangoproject.com/en/dev/faq/install/), the
[Python version status page](https://devguide.python.org/versions/), and each package's PyPI metadata.

## Backend architecture

| Topic | Current | Decision | ADR |
|---|---|---|---|
| Settings layout | `settings/base.py` (dev defaults) + `heroku.py` (prod overrides) | **`base.py` + `local.py` + `test.py` — no `production.py`.** `base.py` *is* production: everything from the environment, and **no default at all** for `SECRET_KEY`/`ALLOWED_HOSTS`/`DEBUG`, so a missing variable fails at boot and a forgotten `DJANGO_SETTINGS_MODULE` lands on the **safe** module — the inverse of today (1.5, 2.19) | [028](decisions.md) |
| Business logic | inline in `control/views.py`, duplicated across views and model `@property` methods | **`control/services/` — plain functions, frozen dataclass returns, batch-first.** `cost_products(queryset, …)` is the primary API; single-object costing wraps it. Models lose costing entirely — the properties are **deleted, not delegated**, and the inline `float()` math is deleted rather than ported (4.1, 4.19, 4.20) | [028](decisions.md) |
| API layer | none | **None, and no framework pre-selected.** The health endpoint and any future callback are plain `JsonResponse` views. Revisit trigger in the ADR (4.15 cancelled) | [028](decisions.md) |
| Auth / permissions | mix of no auth, `staff_member_required`, ad hoc template checks | **Django's built-in auth views are the only auth surface** — `accounts.views.user_login` is unreachable and is deleted (4.5). `LoginRequiredMiddleware` makes login the default, with `@login_not_required` on the cover page, login view and the Epic 16 callback (2.17). Capabilities are Django permission codenames resolved by a **custom authentication backend** against the active membership, so the stock mixins, decorator and `{% if perms %}` keep working (2.20, 2.21) | [020](decisions.md)/[027](decisions.md)/[028](decisions.md) |
| Caching | none | **None in the first release.** Query design is the lever: batch costing (4.19), `select_related`/`prefetch_related`, the connection pool. A stale margin is not a slow page but a wrong number someone prices against. Escalation ladder and measurement trigger (7.20) in the ADR; the batch API carries a per-tenant version stamp from day one so a cache bolts on at that seam (4.20) | [028](decisions.md) |
| Email | none — the app sends no mail | **Brevo over SMTP** via Django's built-in `smtp.EmailBackend` — no dependency, provider stays a pure environment-variable concern. Scope is wider than invitations: built-in auth views make **password reset** email-only too (7.21, 7.22, 5.24, 11.16) | [028](decisions.md) |
| Connection pooling | none | **Django's native psycopg pool** (`DATABASES["OPTIONS"]["pool"]`, 5.1) plus `CONN_HEALTH_CHECKS`. In-process — no PgBouncer, no extra service (7.19) | [027](decisions.md) |

### Data model

Shape-of-the-schema decisions, distinct from the business-meaning ones in
[project_requirements.md](project_requirements.md). All settled **before** Epic 3's migrations are
written — traceability adds a temporal/event layer to tables Epic 3 is about to restructure, so
deciding them separately would have meant redesigning the same tables twice.

| Topic | Current | Decision | ADR |
|---|---|---|---|
| Ingredient line model | two parallel through-style models (`Bs_Ingredients`, `Recipe_Ingredients`) | **One shared `RecipeLine`** — typed parent (`parent_product` XOR `parent_base_recipe`) and typed component (`component_material` XOR `component_recipe`), both XORs as database `CHECK` constraints rather than `clean()` (which does not run on `bulk_create`). `Product` and `Base_recipes` stay separate — this collapses the *lines*, not the recipes. Costing recursion, the 17.7 trace and 18.3's allergen aggregation become one traversal (3.19, 3.73) | [032](decisions.md) |
| Recipe nesting & cycles | products reference raw materials only; base recipes reach nothing | A product's line **may reference a base recipe**, with costing recursing into it. Cycles **rejected at save time** plus depth-guarded in the service layer — nothing in the current schema prevents a recipe containing itself (3.59, 4.16) | [022](decisions.md) |
| Cost provenance | none — a cost is a bare number | Latest goods receipt by *receipt date* sets current cost; a manual price survives as a labelled estimate; the service layer returns **provenance** with the figure (3.62, 4.17) | [022](decisions.md) |
| Units & categories | free-text `CharField`s (`unit`, `categorie`) | **Both lookup tables, different edit rights.** Units carry a conversion factor an enum cannot hold and are **not** tenant-editable — editing a factor silently rewrites every derived cost (3.52). Categories are one tenant-scoped `Category` table with a `kind` discriminator, archivable, unique on `(bakery, kind, name)`, **tenant-editable** since a category carries no arithmetic (3.74) | [018](decisions.md)/[032](decisions.md) |
| Calculated values | recomputed inline per request, in `float()` | **Derived, never persisted** (3.17) | [018](decisions.md) |
| Deletion semantics | hard deletes everywhere | **Soft delete:** `Supplier`, `RawMaterial`, `Product`, `Base_recipes` — "anything referenced by a record that outlives it". **Hard delete:** ingredient lines. Tenant scope and archived state combine in **one** base manager (3.55) | [019](decisions.md) |
| Roles | mix of no auth and ad hoc checks | **Three per-tenant roles** (Owner / Staff / Read-only) on a **membership record** (user × bakery × role). Checks are capability-named, never `role == "owner"` (3.58, 2.16) | [020](decisions.md) |
| Administration surfaces | Django admin and in-app settings overlap | **Two audiences, not the same operations.** In-app settings = tenant surface (scoped, role-checked, audited). Django admin = **superuser-only** support tooling, deliberately cross-tenant, never linked from the tenant UI. `ModelAdmin` does **not** apply tenant-scoped managers (2.15) | [019](decisions.md) |
| Money & quantity types | mixed (`CharField` quantity, `float()` math) | **`Decimal` end-to-end.** Quantities ≥ `Decimal(12,4)` (`12,6` safer), money beyond 2 dp internally, rounded to 2 dp **only at presentation** with an explicit tested rule (3.50, 3.51, 6.16) | [018](decisions.md) |
| Price basis | `RawMaterial.price` with implicit meaning | `purchase_price` + `pack_quantity` + `purchase_unit`, as the invoice states it; derived cost never persisted (3.10) | [018](decisions.md) |
| Canonical costing units | none | **kilogram / litre / each**, one per dimension. Trade-off accepted: larger units make gram-scale ingredients small fractions, so decimal scale is load-bearing | [018](decisions.md) |
| VAT | inconsistent between products and dashboard math | All stored money **net (ex-VAT)**; dated VAT-rate table (`code`, `percent`, `valid_from`, `valid_to`); product references a rate **code** (3.15, 3.53) | [018](decisions.md) |
| Price history | none — prices overwritten in place | **Two sources:** input prices from goods receipts (a free by-product); sale prices as dated `ProductPrice` rows (3.16) | [018](decisions.md) |
| Traceability entities | none; a pure current-state catalogue | **Header + lines, full event chain.** `GoodsReceipt` → `GoodsReceiptLine` (material, supplier lot, qty, unit, best-before, price in ADR-018's shape); `ProductionRun` → `Consumption` → `Batch` → `OutboundRecord`. A delivery note is one record with many lines. **A lot is an event, not an attribute** — no `lot` field on `RawMaterial` (17.1, 17.2) | [033](decisions.md) |
| Lot code generation | n/a | **`YYYYMMDD-NNN`**, resetting daily, unique on `(bakery, lot_code)`, allocated **server-side inside the batch-creating transaction** — never client-side, never by counting rows. Gaps after rollback acceptable; collisions not (17.13) | [033](decisions.md) |
| Stock / quantity-on-hand | none | **Derivable, deliberately not surfaced.** `Consumption.quantity_consumed` makes on-hand computable as `Σ received − Σ consumed`, but there is no stock field, no stock page, no low-stock alert this round (17.14) | [033](decisions.md) |

**Constraint on Epic 3:** build `RawMaterial` knowing the event tables are coming — **no `lot` field,
no `stock` field**, numeric `quantity` with a unit FK so a receipt line can be reconciled against the
catalogue row.

## Frontend

Measured 2026-08-16 — and the measurement is what decided the rows below it.

| Topic | Current (measured) | Decision | ADR |
|---|---|---|---|
| Templating | 32 templates, 4,277 lines, **zero `{% extends %}`, zero `{% include %}`**; 31 with full `<!DOCTYPE>` boilerplate, navbar duplicated 32× | **Shared `base.html` + `{% include %}` partials** in `<app>/templates/partials/`. `django-template-partials` **not** adopted — a dependency for ~4 fragments (5.1, 5.2) | [030](decisions.md) |
| CSS framework | Bootstrap **5.0.0** vendored (May 2021) | **Bootstrap 5.3.x** — same major, so the classes across 32 templates stay largely valid: an upgrade, not a restyle (5.4) | [030](decisions.md) |
| Asset pipeline | none; 16 CSS files, 922 lines, four byte-identical; no `package.json` | **None — the Vite candidate is rejected.** It would add Node, a second lockfile and CI steps to bundle **zero bytes of JS**, duplicating what whitenoise already does. Instead: consolidate the CSS, native custom properties + nesting, whitenoise for cache-busting. Revisit at a few hundred lines of custom JS, or SCSS-variable-level Bootstrap customization (5.6) | [030](decisions.md) |
| Interactivity | **7 custom JS files, all 0 bytes** — there is no JavaScript in the project | **HTMX**, vendored at a pinned version, plus small vanilla modules. One ~14KB script, no bundler, server returns HTML fragments. Built as **progressive enhancement** — forms and links work with JS disabled. Alpine.js rejected: Bootstrap's JS bundle already covers dropdowns/modals/toasts (5.7, 5.25) | [030](decisions.md) |
| SPA? | n/a | **No** — a ratification; the API layer and the device matrix had already foreclosed it | [030](decisions.md) |
| Static references | **Zero `{% static %}`**; 23 templates hardcode `/static/...` | Switch to `{% static %}` (5.3) — see the warning below | [027](decisions.md)/[030](decisions.md) |
| Template linting | none | **`djlint`** — a pip package, so no Node in dev; first occupant of `requirements/dev.in`. `stylelint`/`prettier` deferred on the same grounds (5.8, CI in 6.11) | [030](decisions.md)/[034](decisions.md) |
| Accessibility target | none stated | **WCAG 2.2 Level A**, with a revisit trigger to AA before EU expansion (10.15). **Django's own form rendering supplies a material share of it** — real label association, `aria-describedby`, `aria-invalid`, `<fieldset>`/`<legend>` grouping, as framework output rather than hand-written markup (5.22) | [021](decisions.md)/[027](decisions.md) |
| Device / browser matrix | responsive, matrix unstated | Phone→desktop; current **and previous** major Chrome/Firefox/Safari/Edge. No IE11, no native app (5.13, 5.17) | [021](decisions.md) |
| Localization | English only, `€` hardcoded in templates | Ship `en-IE`/EUR; **`gettext` on display text and one currency formatter from day one** — no hardcoded `€` (5.15, 5.16) | [021](decisions.md) |
| Performance budget | none | p95 < 500 ms pages, < 2 s dashboard aggregate, ~10 concurrent users/tenant. A documented budget, **not** a CI gate — Railway Hobby shares CPU (5.14) | [021](decisions.md) |

Two consequences of "no pipeline" shift risk rather than removing it:

- **5.3 is load-bearing.** Whitenoise is now the *only* cache-busting mechanism, and it does nothing
  for the 23 templates hardcoding `/static/...`. 5.3 + 19.14 + 1.13 are the whole story on asset
  versioning; done partially, the site silently serves stale CSS. Worse, switching to `{% static %}`
  activates manifest storage for the first time, and `ManifestStaticFilesStorage` raises `ValueError`
  **at render time** for any file missing from the manifest — a missing asset stops being a silent 404
  and becomes a 500. Sequence 5.3 after 1.3 and lean on 1.13's CI `collectstatic`.
- **Vendored assets need their own register.** Bootstrap and HTMX are dependencies
  `requirements/*.in` cannot see, so ADR-029's owner/purpose rule extends to them by hand (5.25).
  Skipping it reproduces the state this decision found: a four-year-old vendored library nobody noticed.

Bootstrap's full stylesheet ships un-tree-shaken (~230KB minified, compressed by whitenoise and
cached) — accepted against the p95 budget as a cached static asset, not a per-request cost.

## Infrastructure / operations

| Topic | Current | Decision | ADR |
|---|---|---|---|
| Hosting | Self-hosted: home server running Docker via Portainer; PostgreSQL in a separate container. (Moved off Heroku after the free dyno/Postgres tier ended) | **Railway, Hobby plan, EU West (Amsterdam)** — ~$6/mo | [013](decisions.md) |
| Dev/test environment | Runs on the developer's machine ad hoc | **Local `docker-compose`** — same Dockerfile as production, app and DB separate. No persistent hosted staging | [014](decisions.md) |
| Containerization | `Dockerfile` + `docker-compose.yaml` (expects an external `bakery_simple` network) | **Custom Dockerfile** as the deploy artifact, not the platform's buildpack | [004](decisions.md) |
| Host portability | Partly there by accident: `heroku.py` reads `DATABASE_URL`, whitenoise serves static, media is S3-compatible. Undermined by a hardcoded port, `migrate` in `CMD`, a host-named settings module, and no portable dump | **Standing constraint** — the eight rules are tabulated below | [015](decisions.md) |
| Static/media storage | whitenoise for static; `MEDIA_ROOT` points at a broken leftover path (`bluebiulding/media`) that nothing uses | whitenoise unchanged for static, **Cloudflare R2** for uploads — but the *setting* changes: `STATICFILES_STORAGE`/`DEFAULT_FILE_STORAGE` were deprecated in Django 4.2 and **removed in 5.1**, so the `STORAGES` dict is required by the upgrade (19.14). Removed settings are **ignored, not rejected** — the failure is the silent loss of compression and cache-busting. Its two keys are the media/static split: R2 on `"default"`, whitenoise on `"staticfiles"` (13.11) | [005](decisions.md)/[027](decisions.md) |
| CI/CD | none | **GitHub Actions, extending the Epic 1 workflow, with a 70% repo-wide coverage floor.** Merge gate: the test suite, `ruff` + `djlint`, the migration/`collectstatic`/`docker build` checks from 1.11/1.13, and `pip-audit` against the hashed lock, with Dependabot raising dependency PRs. **No SAST or image scanning** this release | [031](decisions.md) |
| Deploy trigger | manual, on the home server | **Railway git-watch on `production`**, with `migrate` as the **pre-deploy command** — satisfying ADR-015 rule 4 without a bespoke pipeline. 6.14 is therefore satisfied by **branch protection**: failing checks block the merge, and only a merge deploys | [031](decisions.md) |
| Error tracking | none | **Sentry SaaS, free Developer tier, EU region (`de.sentry.io`)** — the region is fixed at organisation creation and **cannot be changed afterwards**, the one setup step that must not be got wrong. `send_default_pii` stays **off** and a `before_send` scrubber is mandatory (7.2, 7.23, 11.6) | [031](decisions.md) |
| Uptime monitoring | none | **UptimeRobot free tier** — 5-minute HTTPS **keyword** check against 7.4's health endpoint, email alerting, $0. Keyword rather than status-code only, so a health endpoint reporting a dead database fails instead of passing on its HTTP 200. Deliberately **external to Railway** (7.5) | [031](decisions.md) |
| Backups | unknown/undocumented. Railway backups are **not automatic** — daily (6-day retention), weekly (1 month) and monthly (3 months) schedules are configurable and combinable, billed incrementally, and there is **no PITR** | **Two tracks, deliberately unequal** (below). **PITR rejected**; RPO of up to 24 h accepted, revisit at the second paying tenant | [031](decisions.md) |

Everything above lands at **$0/mo** on free tiers, keeping the ~$6/mo budget intact — the only new
recurring cost is R2 storage, and a few hundred MB of dumps sits inside R2's 10 GB free tier alongside
the media.

### The two backup tracks

| Track | Mechanism | Answers | Restorable elsewhere? |
|---|---|---|---|
| Same-host rollback | Railway daily/weekly/monthly volume snapshots (12.9) | "The release an hour ago corrupted data — put it back" | **No.** Copy-on-write volume snapshots, Railway-only |
| Host-independent archive | Nightly GitHub Actions `pg_dump -Fc --no-owner --no-privileges`, `age`-encrypted client-side, into a **separate** R2 bucket on a 7-daily / 4-weekly / 12-monthly lifecycle (3.70, 3.71) | "Railway is gone / we are moving host / that row was wrong three months ago" | **Yes** — the one ADR-015 rule 5 requires |

Three consequences that shape tasks rather than tooling:

- **The dump job lives outside the host it backs up.** Running it in GitHub Actions keeps the escape
  hatch independent of the platform being escaped. The cost: CI needs database credentials and reaches
  Postgres over Railway's public TCP proxy — so those credentials are backup-scoped and rotatable
  (3.41), not the app's.
- **Client-side `age` encryption makes key custody a real task.** Cloudflare holds ciphertext it
  cannot read — a clean answer for [project_requirements.md](project_requirements.md) "Security measures" — but a lost private key means *proven*-lost
  backups. 3.72 owns the key; 3.48's weekly drill proves it still works, which is why the drill must
  **decrypt** rather than restore a plaintext copy.
- **Backup retention is a separate clock from record retention.** The 7/4/12 schedule is backup
  lifetime; GDPR record retention stays `Open` ([project_requirements.md](project_requirements.md) "Retention & deletion", 11.4) and the food-law floor is
  10.9. What the schedule *does* fix is the erasure answer: personal data in backups is gone within a
  year at the outside, and within five weeks for all but the monthlies.

### Processors & data residency

Every vendor above is a GDPR **processor** and needs a DPA plus a subprocessor entry. Bakery-the-
product is itself a processor for each tenant — see
[project_requirements.md](project_requirements.md) "Controller / processor model".

| Processor | Purpose | Personal data involved | Status |
|---|---|---|---|
| **Railway** ([ADR-013](decisions.md)) — still self-hosted until Epic 12 executes | Runs the app, stores the DB | Everything | **Open** — DPA required (12.7). US-incorporated; data in EU West (Amsterdam). See transfers below |
| **Cloudflare R2** ([ADR-005](decisions.md)) | Media bucket, a **separate** backup bucket ([ADR-031](decisions.md)), and the Epic 16 extract prefix | Product photos (not personal); backups hold everything but are `age`-encrypted client-side, so Cloudflare holds only ciphertext; the insights extract is personal-data-free. Profile pictures only if that deferred feature ships | **Open** — DPA via 11.6 |
| **Brevo** ([ADR-028](decisions.md), 9.22 ✅) | Transactional mail: user invitations and password reset | Recipient email address, display name, and the reset/invite token | **Open** — DPA not yet executed (11.6, 11.16). French-owned, data centres in France/Belgium/Germany, ISO 27001:2022, DPA included by default. **No transfer safeguard needed** — EU-owned *and* EU-hosted |
| **Sentry** ([ADR-031](decisions.md), 9.15 ✅) | Receives unhandled exceptions and their context | **Undefined by nature** — whatever a traceback carries: potentially supplier contacts, staff emails, tenant costing data, request metadata | **Open** — DPA via 11.6. Free Developer tier, organisation in the **EU region** (`de.sentry.io`), irreversible after creation. Mitigated at source by 7.23. US-incorporated with EU storage — same transfer question as Railway |
| **Databricks Inc.** ([ADR-036](decisions.md)) | Runs the nightly Spark job computing margin alerts and analytics | **None by design** — it reads only the personal-data-free R2 extract and **never touches PostgreSQL** | **Open** — DPA via 11.17/16.4, before any real data flows. US-headquartered, which is a **subprocessor/DPA question, not a data-location one** |
| **AWS** (EU Ireland `eu-west-1`) | Underlying cloud for the Databricks Serverless job compute | Same — none by design | **Open** — subprocessor entry + DPA via 11.17 |

**Storage location — satisfied.** GDPR treats the EU as a single space: Art. 1(3) provides that free
movement of personal data within the Union may not be restricted for data-protection reasons. Irish
tenants' data therefore does **not** have to sit in Ireland, and Railway's EU West (Amsterdam) region
satisfies residency. Both the app **and** the PostgreSQL service/volume must be in that region — the
personal data is in the database, so an app in Amsterdam with a default-region (US West) database puts
the actual data in the US. Railway's default *is* US West, so the region must be set before any
service is created (12.8). Databricks and AWS sit in EU Ireland, and the extract carries no personal
data anyway, so the insights path needs no Chapter V mechanism for the data itself.

**Transfer safeguards — Open (11.15, via 12.7).** Railway and Sentry are US-incorporated, so US law
can reach the parent company even for data held in the EU. That is a Chapter V question answered by
contractual safeguards — SCCs and/or the EU-US Data Privacy Framework, whose predecessors Safe
Harbour (2015) and Privacy Shield (2020) were **both annulled by the CJEU**. To resolve: confirm each
vendor's current certification/SCC position and record it here. [ADR-013](decisions.md) documents why
this risk was accepted for the Ireland phase and sets the revisit trigger before EU expansion (11.14):
EU-owned alternatives were priced at roughly 2.5–3× Railway (Clever Cloud ~€16–26/mo, Scaleway
~€16/mo), which is not what decides it — **what decides it is that continental buyers treat EU
ownership as a purchasing criterion in a way Irish buyers generally do not.** Migration stays cheap
only while ADR-004, ADR-007 and ADR-015 hold.

### Hosting candidates

**Resolved: Railway (Hobby)** — [ADR-013](decisions.md). Kept as fallback reference; not being
re-evaluated unless Hobby's limits or lack of SLA become a problem. Field narrowed to three by
[ADR-003](decisions.md). Costs assume this app's actual scope (single bakery, a handful of concurrent
users, a small dataset); sourced 2026-07-21, Railway re-confirmed 2026-08-03.

| Option | App compute | Database | Est. total/mo | Notes |
|---|---|---|---|---|
| **Railway** ✅ chosen | Hobby, $5/mo base including $5 usage credit, per-second beyond | ~$2/mo light, same usage pool | **~$6/mo** | Cheapest of the three; no cold starts; native GitHub auto-deploy |
| Render | Starter $7/mo always-on, or free tier (sleeps after ~15 min idle) | Free Postgres deleted after 30–90 days — not viable long-term; paid from ~$15/mo | ~$22/mo paid | Simplest DX, but the free database's expiry makes the free tier a trial. Per-PR previews need the Pro workspace ($19/user/mo) |
| DigitalOcean App Platform | $5/mo | Managed Postgres from $15/mo (HA doubles to $60); non-HA "dev" DB ~$7/mo/512MB | ~$12–20/mo | Priciest baseline but closest to "professional" — managed backups/monitoring bundled |

**Railway cost basis** (verified 2026-08-03) — Railway bills **actual** per-second usage, not allocated
capacity. Per 730-hour month: ~**$10.14/GB** RAM, ~**$20.29/vCPU**, ~**$0.16/GB** volume, **$0.05/GB**
egress.

| Item | Assumed usage | Cost/mo |
|---|---|---|
| App service (gunicorn) | ~0.3 GB RAM | $3.04 |
| PostgreSQL service | ~0.2 GB RAM | $2.03 |
| CPU, both services | ~0.02 vCPU avg | $0.41 |
| Volume (Postgres data) | 2 GB | $0.32 |
| Egress | <1 GB | ~$0.05 |
| **Total** | | **~$5.85/mo** |

Hobby's $5 base includes $5 of usage, so the effective bill is ~$6/mo. Plan limits (48 GB RAM,
48 vCPU, 6 replicas per service) are far above anything this app needs. **Free tiers are not viable:**
the 30-day trial grants $5 once and **deletes stateful volumes** 30 days after credits expire, and the
Free plan's $1/mo credit and 0.5 GB RAM / one service cannot run an app *and* a database, which
[ADR-007](decisions.md) requires.

<details>
<summary>Considered and set aside per ADR-003 — reference only, not being re-evaluated</summary>

| Option | Cost | GitHub auto-deploy | Notes |
|---|---|---|---|
| Fly.io | ~$8–15/mo (app + Postgres machine) | Not literally git-push — a GitHub Actions step running `flyctl deploy` | Global edge network; steeper learning curve, free tier no longer exists |
| Sevalla (Kinsta) | ~$25–35/mo est. (compute from $18/mo + separate DB pricing) | Native (Docker/buildpacks/Nixpacks) | Newer entrant; "hibernation" cuts cost on non-production apps |
| Koyeb | $0 on free tier (1 web service + 1 Postgres DB, no card) | Native | Fits this app's scope for free, but paid plans jump to $79/mo — a steep cliff if outgrown |
| Hetzner VPS + Coolify (self-managed) | ~$6/mo (CX23 ≈ €5.49/mo runs app+DB on one box) | Not native — GitHub Actions SSH step, or self-host [Coolify](https://coolify.io) | Cheapest overall; keeps you as the one patching the VM |
| Oracle Cloud "Always Free" VM | $0 forever (4 ARM cores / 24 GB RAM) | Not native — same SSH approach | Was the front-runner on cost; set aside for a fully managed PaaS (own reverse proxy/TLS/firewall, no native GitHub deploy) |

</details>

### Deployment method: Docker vs. native buildpack

Verified 2026-07-21 ([ADR-004](decisions.md)): all three candidates support a custom `Dockerfile` and
all three **prioritize it over their native buildpack** when one is present at the repo root.

| Platform | Native buildpack | Platform's own guidance |
|---|---|---|
| Railway | Railpack (replaced Nixpacks, March 2026) | Fine for a quick start; recommends a custom Dockerfile once heading toward production or deploying anywhere else |
| Render | Cloud Native Buildpacks, auto-detects Python | Buildpack is faster for simple apps; Dockerfile recommended for control over system dependencies or a minimal final image |
| DigitalOcean App Platform | Heroku-derived Python buildpack | Recommends bringing your own Dockerfile for production — buildpacks are described as too "magical" for easy debugging |

### Dev / staging / preview environments

Verified 2026-07-21. None of this ruled out any candidate — all can run the `main` (integration) /
`production` (live) two-branch model.

| Platform | Persistent staging | Per-PR ephemeral preview |
|---|---|---|
| Railway | Native "Environments" — a second environment tracking `main`, each with its own isolated database | Native "PR Environments" — auto-created on PR open, auto-deleted on merge/close, **no plan-tier gate** |
| Render | Two persistent services, each tracking its own branch | "Preview Environments" per PR — requires the Pro workspace ($19/user/mo) |
| DigitalOcean App Platform | Two Apps auto-deploying different branches; "Environment Support" groups them Dev/Staging/Production | `deploy_pr_review` App Spec setting. No plan gate, but separate App/database resources roughly double the cost |

**Resolved ([ADR-014](decisions.md)): the staging tier is local, not hosted.** Railway not gating PR
environments behind a plan tier is what makes the middle row affordable. The preview is scoped to the
release PR because local Docker already covers feature-branch verification; what it *can't* cover is
whether the merged code runs **on Railway**.

| Tier | Where it runs | Lifetime | Cost |
|---|---|---|---|
| Dev / integration test | Developer's machine, `docker-compose` | Always, during development | $0 |
| Release preview | Railway PR environment, on the `main` → `production` PR **only** | While that PR is open (a day or two) | <$1/mo |
| Production | Railway, tracking `production` | Always-on | ~$6/mo |

### Host portability rules

Rules from [ADR-015](decisions.md); this table adds current state and owning task. The app and
database must stay deployable on **any host that runs a Docker image and a PostgreSQL service**, with
configuration changes only — the option ADR-013's residency revisit (11.14) depends on.

| # | Rule | Current state | Task |
|---|---|---|---|
| 1 | The `Dockerfile` is the only build artifact — no platform buildpack | ✅ Already true | 7.6 |
| 2 | All config from environment variables; no host-named settings module. `DATABASE_URL` is the database contract | ⚠️ `settings/heroku.py` still exists | 1.5, 7.9 |
| 3 | Bind to `$PORT` with a local fallback | ❌ Hardcoded `:8000` in the `Dockerfile` `CMD` | 7.17 |
| 4 | Migrations are a release step, not part of the container start command | ❌ `migrate &&` is inside `CMD` and the compose command | 7.11, 12.11 |
| 5 | A host-independent logical dump (`pg_dump`), restore-tested on a *different* instance | ❌ Backups are "unknown/undocumented" | 3.44, 3.70 |
| 6 | Core PostgreSQL and widely-available extensions only | ✅ True today; needs to stay true | 3.45 |
| 7 | Persistent state only in PostgreSQL and object storage, never container disk | ⚠️ Broken `MEDIA_ROOT` leftover points at local disk | 2.13, 7.18 |
| 8 | Every environment variable documented in a committed `.env.example` | ❌ Doesn't exist | 7.13 |

`DATABASE_URL` is provided by every candidate host (Railway, Render, DigitalOcean, Fly, Clever Cloud,
Scaleway), and `heroku.py` already consumes it via `env.db()` — worth preserving through the settings
split.

**Accepted lock-in:** Railway's git-watch deploys (7.15) and the release-PR preview (12.5) — workflow
conveniences, no data involved, roughly a day to rebuild elsewhere. Native volume snapshots (12.9) are
fine *alongside* rule 5's portable dump.

**Portability is tested continuously and for free.** The local `docker-compose` environment runs the
same image on plain Docker with no platform involved, so a break shows up as a broken local
environment rather than as a discovery mid-migration.

#### Making database migration as routine as app migration

App migration is low-risk because **every deploy rehearses it**. The database restore path, left
alone, runs for the first time on the day it matters. Four traps worth naming:

| Trap | Why it bites | Task |
|---|---|---|
| `pg_dump` default flags | Emits `OWNER`/`GRANT` referencing roles that don't exist on the target — the most common cross-host restore failure | 3.46 |
| Collation differences | Text index ordering depends on the host's glibc/ICU version; indexes can be subtly wrong after a cross-host restore while everything looks fine. `REINDEX` after restore | 3.47 |
| Unverified restores | "It restored without errors" is not "the data is complete" — needs row counts, constraint validation, sequence positions | 3.47 |
| Schema drift | If production has manual DDL the migrations don't produce, the schema can't be rebuilt anywhere — also breaks PR-environment seeding | 3.49, 12.10 |

The one that changes the risk profile is **3.48: an automated weekly restore drill**, which converts
migration from a novel procedure into one that has already run fifty times. Two things make this
easier at this scale: the **dataset is small** (megabytes, not gigabytes), so a dump/restore completes
in seconds and a short maintenance window is adequate — logical replication for near-zero-downtime
cutover is unnecessary complexity here. And **object storage doesn't move**: media lives in R2,
independent of the app host by design, so a host migration moves compute and database only.

### Static & media file storage

| Topic | Decision |
|---|---|
| Static assets | whitenoise, unchanged — but configured through `STORAGES`' `"staticfiles"` key (19.14), since `STATICFILES_STORAGE` no longer exists on Django 5.2 |
| User-uploaded media | **Cloudflare R2** via `django-storages`, under `STORAGES`' `"default"` key (13.11). Zero egress, 10 GB/1M-write/10M-read free tier, provider-agnostic |
| Why not local disk | No candidate host guarantees persistent shared disk across redeploys or instances — ruled out |
| Why not Oracle Object Storage | Reasonable while Oracle was a hosting candidate; a weaker fit now — it would add a fourth provider relationship — ruled out |
| New dependencies | `django-storages[s3]`, `boto3`, `Pillow` (13.1) |

**Scope this round: product photos only.** Profile pictures are deferred by
[ADR-024](decisions.md), which takes their legal basis (11.3) off the critical path. Implementation:
an `ImageField` on `Product`, `django-storages` against the R2 endpoint with credentials from
environment variables (2.5), upload type/size validated in a real `ModelForm` (4.9, 13.7), and the
bucket plus optional custom domain/CDN provisioned (13.2). The backup bucket is **separate** from the
media bucket (3.71) so media credentials can never read or delete backups.

### AI insights / batch analytics service

[ADR-002](decisions.md), confirmed and scoped by [ADR-036](decisions.md) (9.20 ✅). Epic 16.

| Topic | Decision |
|---|---|
| Processing engine | **Apache Spark on Databricks — confirmed.** Re-tested against ADR-024's null hypothesis (a scheduled query over dated prices) and kept as a deliberate bet on headroom, with the cost and processor consequences accepted rather than discovered |
| Where it runs | **Databricks Serverless Jobs on AWS, EU (Ireland) `eu-west-1`.** Serverless job compute only — no cluster lifecycle for the app to start, idle or forget to stop. Both ends stay in the EEA, so the data needs no Chapter V transfer mechanism; Databricks Inc. being US-headquartered is a **subprocessor/DPA** question, not a data-location one (16.8, 11.17) |
| Data handover | **Django pushes a scoped extract to R2; Databricks never touches PostgreSQL.** A nightly job writes a **personal-data-free** costing extract (product, date, cost, price, margin, tenant) to a dedicated R2 prefix. Direct JDBC to Railway's public proxy was rejected — it exposes the production database to a third-party network and drags supplier contacts and user accounts into GDPR transfer scope (16.9, 16.3) |
| Trigger mechanism | **Nightly Databricks schedule; results POSTed back** to a plain `JsonResponse` callback authenticated with a shared secret. No event triggering. The callback is the app's only internet-facing unauthenticated write path, so shared secret + tenant scoping + rate limiting are requirements, and it is the one route besides the cover and login pages exempt from `LoginRequiredMiddleware` (16.10, 16.11) |
| Cost model | **Hard ceiling ~$15/mo**, spend alert before the first production run (16.12). Total infrastructure goes ~$6 → ~$21/mo against zero revenue — a funded bet. **The DBU rate is deliberately not recorded**: serverless pricing is region- and tier-dependent and changes, so 16.8 measures one real run. Community Edition remains unusable (notebook-only, no job scheduling) |
| Extract schema contract | **Versioned.** The Django job and the notebook live in different repositories and evolve separately; the manifest carries a version and the notebook rejects an unknown one, so a schema change fails loudly instead of producing quietly wrong insights (16.13) |

### Tenant data export tooling

Two mechanisms beyond the existing bulk admin CSV export.

| Topic | Decision | ADR |
|---|---|---|
| Tenant full export format | **A ZIP of one CSV per tenant-scoped table plus a `manifest.json`** (timestamp, schema version, and per table its columns, types, primary key and FK map). Serves both audiences ADR-008 named — a spreadsheet for the owner, a loadable bundle for whoever they hire. **The manifest is the deliverable** — CSV loses types, null-vs-empty and every relationship (14.1, 14.3) | [035](decisions.md) |
| Tenant full export mechanism | **One service function, exposed twice:** an Owner-only settings download (gated by a capability name) and a management command. Synchronous is adequate today but re-checked in 14.6. Money and quantities written at **full stored precision**, never 2-dp presentation rounding | [035](decisions.md) |
| GDPR personal-data export | Direction decided — a separate, subject-scoped export; implementation Open, tracked in Epic 15. It **may** reuse ADR-035's bundle shape scoped to one subject; that is 15.2's call, not a stack decision | [009](decisions.md) |

## Quality tooling

| Topic | Current | Decision | ADR |
|---|---|---|---|
| Formatting / linting | none | **`ruff` does both** — `ruff check` and `ruff format`. No `black`, no `isort`, no `flake8`: `ruff format` is a deliberate reimplementation of black's style (6.10) | [034](decisions.md) |
| Template linting | none | **`djlint`** — see the Frontend table (5.8, 6.11) | [030](decisions.md)/[034](decisions.md) |
| Testing | empty `tests.py` stubs in every app, no coverage | **`pytest` + `pytest-django` + `pytest-cov`**, replacing `manage.py test`. Django's own runner was close and lost on this suite's shape: table-driven costing (`parametrize`) and composable tenant-isolation fixtures. Little lock-in — `pytest-django` wraps Django's test-database machinery. `--cov-fail-under=70` is where ADR-031's floor is enforced (6.22, 6.23) | [034](decisions.md) |
| Tool configuration | none | **A `pyproject.toml` holding only `[tool.*]` sections.** Not a packaging file, declares no dependencies, and must never grow `[project]` or `[build-system]` | [034](decisions.md) |

## Open questions

- Any org/team constraints (existing infra, required cloud provider, compliance requirements) that
  should narrow these choices further? Partly answered: the compliance constraint is explicit — EU
  data residency ([ADR-013](decisions.md)) plus food-law traceability records with a legal retention
  floor ([ADR-017](decisions.md), 10.9), which raises the cost of losing the database and so raised the
  bar on the backup strategy ADR-031 settled.
