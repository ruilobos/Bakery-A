# Tech Stack

How to use this file: the **Current** column is factual — don't change it without checking the
code. The **Decision** column stays `Open` until a choice is actually made; once it's made, write
it here **and** log the reasoning as an ADR in [decisions.md](decisions.md), then flip Status to
Decided. Claude should never write code against a `Proposed`/`Open` row as if it were final.

Once a row is Decided, it must also appear as a task in an epic in
[`PRODUCTION_UPDATE_PLAN.md`](../PRODUCTION_UPDATE_PLAN.md) — that file is the backlog, this one is
where the choice gets argued out. Epic 9 (`stack-decisions`) is the backlog counterpart of this
file: one task per `Open` row below.

## Runtime

| Layer | Current | Candidate | Decision | Status |
|---|---|---|---|---|
| Python | 3.8 (`runtime.txt`), Dockerfile uses 3.9-slim — **both EOL** (Oct 2024 / Oct 2025) | 3.12 as the primary target, with a follow-up validation pass on 3.13 once all dependencies and the chosen host confirm support | **Python 3.13** — supported by both Django 5.2 (3.10–3.14) and 6.2 (3.12–3.14), so the whole planned path needs no Python change. `python:3.13-slim` in the `Dockerfile` is the single source of the version; `runtime.txt` is deleted, not updated. The old 3.12 candidate aged out — 3.12 has been security-only since Oct 2025 | Decided ([ADR-025](decisions.md)) |
| Django | 3.2 — **EOL since April 2024** | Current supported LTS — 5.2 LTS directly if hosting and package support allow, otherwise staged 3.2 → 4.2 LTS → current LTS | **Django 5.2 LTS, upgraded directly from 3.2** (no 4.2 stop). The LTS has the *longer* runway than current stable: 5.2 → April 2028 vs. 6.1 → Dec 2027, and 6.0 left mainstream support 2026-08-04. Next hop **6.2 LTS**, H2 2027 | Decided ([ADR-025](decisions.md)) |
| Database | PostgreSQL (version unpinned; `docker-compose.yaml` has no Postgres service at all) | PostgreSQL, pin a version | **PostgreSQL 17**, pinned identically local and production. Major versions must match across environments; a bump is deliberate and restore-tested (3.47), never drift | Decided ([ADR-026](decisions.md)) |
| DB topology (app vs. DB process) | Self-hosted: separate Postgres container from the app | Always separate services (app and DB never bundled in one image), on every hosting candidate | Separate always | Decided (see ADR-007) |
| Multi-tenancy model | None — single-bakery schema | Single shared database, row-level tenant isolation via a `Bakery` FK on every business table (not database-per-tenant) | Shared DB, tenant-scoped rows | Decided (see ADR-006/ADR-008) |
| WSGI/ASGI server | gunicorn 20.1.0 (WSGI) | current gunicorn; ASGI only if a real need shows up | — | Open — 9.4. **Deliberately left open** while [ADR-025](decisions.md) closed the rest of the runtime: nothing in the decided scope needs async ([ADR-023](decisions.md)'s dashboard is server-rendered aggregates, and [ADR-024](decisions.md) reduced Epic 16's "real-time analytics" to a scheduled query), so the answer is very likely "current gunicorn, WSGI" — but the revisit trigger should be written against Epic 16's actual shape, which 9.20 settles |

## Dependencies

| Package | Current | Candidate | Decision | Status |
|---|---|---|---|---|
| `psycopg2-binary` | 2.9.6 | `psycopg[binary]` (v3) | **`psycopg[binary]` 3** — natively supported by Django since 4.2; psycopg2 is maintenance-only upstream | Decided ([ADR-025](decisions.md)) |
| `whitenoise` | 5.2.0 | latest compatible with chosen Django | **Latest compatible with Django 5.2 / Python 3.13** at lock time. 6.12.0 confirmed compatible 2026-08-10 | Decided ([ADR-025](decisions.md)) |
| `django-environ` | 0.4.5 | latest | **Latest compatible** at lock time; 0.14.0 confirmed 2026-08-10. Stays — it owns `env.db()`, the `DATABASE_URL` contract in [ADR-015](decisions.md) rule 2 | Decided ([ADR-025](decisions.md)) |
| `Pillow` | 10.4.0 | latest | **Latest compatible** at lock time; 12.3.0 confirmed 2026-08-10 | Decided ([ADR-025](decisions.md)) |
| `django-mathfilters` | 1.0.0 | keep only if template math stays; drop if costing moves to a service layer | **Dropped.** Latest release is 1.0.0 (Feb 2020), classifiers stop at Django 3.x — a hard blocker for the upgrade, not a preference. Loaded in `base_recipe.html` and `products.html`, both doing template-side cost math that [ADR-018](decisions.md) already ruled wrong (19.6) | Decided ([ADR-025](decisions.md)) |
| `asgiref` / `sqlparse` / `tzdata`/`pytz` | pinned to Django 3.2's requirements | align with whatever Django release is chosen above | **Removed from the hand-written file.** `asgiref`/`sqlparse` are Django's own transitive deps and belong in the lock file; `pytz` goes entirely (Django dropped pytz support in 5.0, stdlib `zoneinfo` replaces it, no app code imports it) | Decided ([ADR-025](decisions.md)) |
| `environ` 1.0 / `dj-database-url` 0.5.0 (not previously listed) | both present in `requirements.txt` | — | **Both removed.** `environ` is an unrelated PyPI package whose top-level `environ` module collides with `django-environ`'s — an install slip and a live hazard. `dj-database-url` is imported nowhere in app code and duplicates `env.db()` | Decided ([ADR-025](decisions.md)) |
| Dependency management | single UTF-16LE `requirements.txt` | split `requirements/base.txt` + `dev.txt` + `prod.txt`, pinned via `pip-tools` or an equivalent lock workflow for deterministic builds | — | Open |
| Dependency hygiene | unreviewed — some packages may be unused | every dependency has a named owner and a stated purpose; anything else is removed | — | Open |
| Media storage | none | `django-storages[s3]` + `boto3`, for S3-compatible object storage (see ADR-005) | Cloudflare R2 | Decided |

**Dependency strategy:** replace the current ad hoc dependency state with pinned, reviewed,
production-safe dependencies; normalize the file encoding to UTF-8; split by environment; generate
pinned requirements from a lock workflow rather than hand-editing. Per [ADR-025](decisions.md), this
table fixes the **constraint** — latest release compatible with Django 5.2 on Python 3.13 — and the
lock workflow (9.8, still `Open`) fixes the exact versions. Exact patch pins are deliberately not
recorded here or in the ADR log, since both are append-only and the pins are not.

The rewritten `requirements.txt` drops from twelve entries to roughly six. Version facts above were
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
| Ingredient line model | two parallel through-style models (`Bs_Ingredients` for base recipes, `Recipe_Ingredients` for products) | keep them separate if the business workflows genuinely differ; otherwise a single shared ingredient-line model with a typed parent reference | Still 9.18's call, but **strongly narrowed**: [ADR-022](decisions.md) gives both models a typed *component* reference (raw material **or** base recipe) alongside the typed parent, making them structurally identical | Open — 9.18, narrowed |
| Recipe nesting & cycles | products reference raw materials only; base recipes reach nothing | a product's line may reference a base recipe, with costing recursing into it | Nesting **decided** ([ADR-022](decisions.md)). Cycles must be **rejected at save time** plus depth-guarded in the service layer — nothing in the current schema prevents a recipe containing itself | Decided (3.59, 4.16) |
| Cost provenance | none — a cost is a bare number | distinguish receipt-derived cost from a manual estimate, in the data not just the UI | **Decided** — the latest goods receipt by *receipt date* sets current cost; a manual price survives as a labelled estimate; the service layer returns provenance with the figure | Decided ([ADR-022](decisions.md)) |
| Units & categories | free-text `CharField`s (`unit`, `categorie`) | controlled enums if the value set is stable, or lookup/reference tables if the values are business-managed | **Units: lookup table** — a conversion factor is data an enum cannot carry ([ADR-018](decisions.md)). **Categories: still open** | Partly decided |
| Calculated values | recomputed inline per request, in `float()` | store as derived/read-only data only, never as editable business fields | Derived, never persisted — reinforced by [ADR-018](decisions.md) | Decided |
| Deletion semantics | hard deletes everywhere | soft delete / archive for entities whose history must stay visible | **Soft delete:** `Supplier`, `RawMaterial`, `Product`, `Base_recipes` — the rule is "anything referenced by a record that outlives it". **Hard delete:** ingredient lines. Tenant scope and archived state must be combined in **one** base manager, not applied ad hoc (3.55) | Decided ([ADR-019](decisions.md)) |
| Auth/permissions model | mix of no auth, `staff_member_required`, ad hoc template checks | consistent `LoginRequiredMixin` + real role-based permissions | **Three per-tenant roles** — Owner / Staff / Read-only — held on a **membership record** (user × bakery × role), since Django's global `Group` cannot express "Owner of bakery A". Checks are capability-named, never `role == "owner"` | Decided ([ADR-020](decisions.md)) |
| Administration surfaces | Django admin and the in-app settings area overlap | narrow one of them | **Two audiences, not the same operations.** In-app settings = tenant surface (tenant-scoped, role-checked, audited). Django admin = **superuser-only** support tooling, deliberately cross-tenant, never linked from the tenant UI. `ModelAdmin` does not apply tenant-scoped managers — do not rely on it to | Decided ([ADR-019](decisions.md)) |
| Money & quantity types | mixed (`CharField` quantity, `float()` math in views) | `Decimal` end-to-end, in the schema and the service layer | **`Decimal` end-to-end.** Quantities ≥ `Decimal(12,4)` (`12,6` safer), money carried beyond 2 dp internally, rounded to 2 dp **only at presentation** with an explicit, tested rounding rule | Decided ([ADR-018](decisions.md)) |
| Price basis | `RawMaterial.price` with implicit meaning | store the invoice as written; derive per-canonical-unit cost at cost time | `purchase_price` + `pack_quantity` + `purchase_unit`; derived cost never persisted | Decided ([ADR-018](decisions.md)) |
| Canonical costing units | none | one canonical unit per dimension, with a conversion factor per purchase unit | **kilogram / litre / each**. Trade-off accepted: larger canonical units mean gram-scale ingredients are small fractions, so decimal scale is load-bearing (3.50, 3.51, 6.16) | Decided ([ADR-018](decisions.md)) |
| VAT | inconsistent between products and dashboard math | net storage, VAT applied at the presentation boundary | All stored money **net (ex-VAT)**; dated VAT-rate reference table (`code`, `percent`, `valid_from`, `valid_to`); product references a rate **code** | Decided ([ADR-018](decisions.md)) |
| Price history | none — prices overwritten in place | version both input and sale prices | **Two sources:** input prices from ADR-017 goods receipts (free by-product); sale prices as dated `ProductPrice` rows | Decided ([ADR-018](decisions.md)) |
| Traceability entities (new — ADR-017) | none; the schema is a pure current-state catalogue with no delivery, batch, or production-run concept | Goods-receipt lines (supplier lot, date, quantity, best-before, price paid) distinct from the `RawMaterial` row; production runs consuming specific receipt lots and emitting an output batch; outbound records. **A lot is an event, not an attribute** — do not add a `lot` field to `RawMaterial` | Direction fixed by [ADR-017](decisions.md); entity shape Open | Open — 9.21 |
| Internal lot code generation | n/a | Decided format (sequence? date-prefixed? per-tenant?) rather than improvised per install | — | Open — 9.21 |
| Stock / quantity-on-hand | none | Nearly free once receipts and production runs exist, but a different product promise with different accuracy expectations — include deliberately or exclude deliberately | — | Open — 9.21 |

**Note on sequencing:** the three rows above must be answered **before** Epic 3's schema work is
implemented, not after. Traceability adds a temporal/event layer to tables that Epic 3 is about to
restructure (`RawMaterial`, the ingredient lines, deletion semantics) — deciding them separately means
redesigning the same tables twice. See [roadmap.md](roadmap.md), Epic 17.

## Frontend

| Topic | Current | Candidate | Decision | Status |
|---|---|---|---|---|
| Templating | Django templates, `APP_DIRS=True`, no shared `base.html` | Django templates + shared `base.html` + partials | — | Open |
| CSS framework | Bootstrap (vendored, bundled in `bakery/static`) | current stable Bootstrap, or reconsider entirely | — | Open |
| Asset pipeline | none (hand-copied static files) | Vite for SCSS/JS bundling + cache busting | — | Open |
| Interactivity | plain JS per page, several empty JS files | vanilla JS modules, optionally HTMX for server-driven interactivity | — | Open |
| Is a full SPA needed? | n/a | leaning no — server-rendered is enough per current scope | — | Open |
| Template/CSS/JS linting | none | add where practical, alongside the Python tooling below | — | Open |
| Accessibility target | none stated | a named WCAG conformance level to build against | **WCAG 2.2 Level A** — with a revisit trigger to AA before EU expansion (10.15). **Django's own form rendering supplies a material share of it** (`as_field_group()`, div-based templates): real label association, `aria-describedby`, `aria-invalid`, `<fieldset>`/`<legend>` grouping — framework output rather than hand-written markup (5.22, [ADR-027](decisions.md)) | Decided ([ADR-021](decisions.md)) |
| Device / browser matrix | responsive, matrix unstated | one responsive UI across a named browser set | Phone→desktop; current **and previous** major Chrome/Firefox/Safari/Edge. No IE11, no native app | Decided ([ADR-021](decisions.md)) |
| Localization | English only, `€` hardcoded in templates | translation-ready even while shipping one locale | Ship `en-IE`/EUR; **`gettext` on display text and one currency formatter from day one** — no hardcoded `€` (5.15, 5.16) | Decided ([ADR-021](decisions.md)) |
| Performance budget | none | a target specific enough to detect a regression | p95 < 500 ms pages, < 2 s dashboard aggregate, ~10 concurrent users/tenant. Documented budget, **not** a CI gate — Railway Hobby shares CPU | Decided ([ADR-021](decisions.md)) |

**Frontend direction (rationale, not yet decided):** the project does not need a full SPA to become
production-ready — a modern server-rendered Django frontend is enough. The candidate shape is: keep
Django templates for page rendering, add a shared `base.html` plus partials, move to a real asset
pipeline (Vite is the leading candidate) for SCSS/CSS bundling, small JS modules, and cache-busted
builds, and prefer lightweight progressive enhancement (vanilla JS modules, optionally HTMX for
server-driven interactivity) over a client-side framework.

## Infrastructure / operations

| Topic | Current | Candidate | Decision | Status |
|---|---|---|---|---|
| Hosting | Self-hosted: home server running Docker via Portainer; PostgreSQL in a separate container on the same machine. (Moved off Heroku after Heroku discontinued its free dyno/Postgres tier.) | Railway, Render, or DigitalOcean App Platform — narrowed per ADR-003; see "Hosting candidates" below | **Railway, Hobby plan, EU West (Amsterdam)** — ~$6/mo (see ADR-013) | Decided |
| Dev/test environment | Runs on the developer's machine ad hoc | Local `docker-compose` (same Dockerfile as production, app and DB as separate containers) — no persistent hosted staging environment | Local Docker Compose (see ADR-014) | Decided |
| Containerization | `Dockerfile` + `docker-compose.yaml` (expects external `bakery_simple` network) | Keep the custom Dockerfile as the deploy artifact on whichever host is chosen, rather than that platform's native buildpack — see ADR-004 and "Deployment method" below | Custom Dockerfile | Decided |
| Host portability | Partially there by accident: `heroku.py` already reads `DATABASE_URL`, whitenoise serves static, media is S3-compatible. Undermined by a hardcoded port, `migrate` inside the container `CMD`, a host-named settings module, and no portable database dump | Any Docker + PostgreSQL host must be reachable with configuration changes only, never code changes — see "Host portability rules" below | Standing constraint (see ADR-015) | Decided |
| Static/media storage | whitenoise for static assets; local `MEDIA_ROOT` config exists but points to a broken leftover path (`bluebiulding/media`) and nothing uses it yet | Keep whitenoise for static assets. For user-uploaded media (new: product photos, profile pictures), use S3-compatible object storage — see "Static & media file storage" below | Cloudflare R2 (see ADR-005) | Decided |
| CI/CD | none | pipeline: install → lint → test → security scan → build | — | Open |
| Error tracking / monitoring | none | Sentry or equivalent | — | Open |
| Uptime monitoring / alerting | none | external uptime check + alerting against the app health endpoint | — | Open |
| Backups | unknown/undocumented | documented PostgreSQL backup + restore + PITR strategy, with a drilled restore. Note the host constraint (ADR-013): Railway backups are **not automatic** — daily (6-day retention), weekly (1 month), and monthly (3 months) schedules are configurable and combinable, billed incrementally (copy-on-write), and there is **no PITR**. A PITR requirement would need tooling beyond Railway's built-in backups. | — | Open — 9.16 |

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
| Processing engine | n/a (new service) | Apache Spark, run on Databricks | Decided (see ADR-002) |
| Trigger mechanism | n/a | App events call the service via API; service reads app DB, returns computed insights | Decided (direction), Open (exact contract) |
| Where does it run relative to the app? | n/a | Databricks is a managed service — it runs on AWS/Azure/GCP infrastructure regardless of where the Django app/Postgres are hosted. "Same hosting" as the app isn't realistic; "API-connected, compatible" is the practical version of that goal. | Open |
| Cost model | n/a | Databricks Community Edition is free but doesn't support external API-triggered jobs (notebook-only, no job-scheduling API) — a real triggered-batch-job workflow needs a paid workspace, billed on top of the underlying cloud compute. **[ADR-024](decisions.md) moved the bar:** a margin alert over [ADR-018](decisions.md)'s dated price history is a scheduled query, and that is now the **null hypothesis Spark has to beat**, not the fallback. Settle in 9.20 before any spend. | Open — 9.20 |

### Tenant data export tooling (new)

Per ADR-008/ADR-009 in [decisions.md](decisions.md): two distinct export mechanisms need to be
built, beyond the existing bulk admin CSV export.

| Topic | Current | Candidate | Decision | Status |
|---|---|---|---|---|
| Tenant full data export format | none | Portable, DBMS-agnostic format — plain ANSI-compatible SQL (`CREATE TABLE`/`INSERT`, not a Postgres-specific `pg_dump` custom format) or a per-table CSV bundle + relationship manifest | Direction decided (portable SQL/CSV, not a native `pg_dump`) — exact tool choice Open | Proposed |
| Tenant full data export mechanism | none | A management command / service that, given a tenant, walks every tenant-scoped table and emits the portable export — likely built on Django's `dumpdata`/serializers or hand-rolled SQL generation | — | Open |
| GDPR personal-data export | Bulk CSV export exists but isn't subject-scoped | A second, separate export scoped to one data subject's personal data across models | Direction decided (separate from bulk export) — implementation Open | Proposed |

## Quality tooling

| Topic | Current | Candidate | Decision | Status |
|---|---|---|---|---|
| Formatting/linting | none | `ruff` (+ `black` if not fully covered by ruff, + `isort` if not covered either) | — | Open |
| Template linting | none | an HTML/Django template linter, if template consistency is wanted | — | Open |
| Testing | empty `tests.py` stubs in every app, no coverage | unit tests (models, costing, permissions, exports) + integration tests for CRUD flows + dedicated cross-tenant isolation tests (ADR-008) | — | Open |

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
