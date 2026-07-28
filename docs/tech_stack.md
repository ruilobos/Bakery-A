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
| Python | 3.8 (`runtime.txt`), Dockerfile uses 3.9-slim | 3.12 as the primary target, with a follow-up validation pass on 3.13 once all dependencies and the chosen host confirm support | — | Open |
| Django | 3.2 | Current supported LTS — 5.2 LTS directly if hosting and package support allow, otherwise staged 3.2 → 4.2 LTS → current LTS | — | Open |
| Database | PostgreSQL (version unpinned) | PostgreSQL, pin a version | — | Open |
| DB topology (app vs. DB process) | Self-hosted: separate Postgres container from the app | Always separate services (app and DB never bundled in one image), on every hosting candidate | Separate always | Decided (see ADR-007) |
| Multi-tenancy model | None — single-bakery schema | Single shared database, row-level tenant isolation via a `Bakery` FK on every business table (not database-per-tenant) | Shared DB, tenant-scoped rows | Decided (see ADR-006/ADR-008) |
| WSGI/ASGI server | gunicorn 20.1.0 (WSGI) | current gunicorn; ASGI only if a real need shows up | — | Open |

## Dependencies

| Package | Current | Candidate | Decision | Status |
|---|---|---|---|---|
| `psycopg2-binary` | 2.9.6 | `psycopg[binary]` (v3) | — | Open |
| `whitenoise` | 5.2.0 | latest compatible with chosen Django | — | Open |
| `django-environ` | 0.4.5 | latest | — | Open |
| `Pillow` | 10.4.0 | latest | — | Open |
| `django-mathfilters` | 1.0.0 | keep only if template math stays; drop if costing moves to a service layer | — | Open |
| `asgiref` / `sqlparse` / `tzdata`/`pytz` | pinned to Django 3.2's requirements | align with whatever Django release is chosen above | — | Open |
| Dependency management | single UTF-16LE `requirements.txt` | split `requirements/base.txt` + `dev.txt` + `prod.txt`, pinned via `pip-tools` or an equivalent lock workflow for deterministic builds | — | Open |
| Dependency hygiene | unreviewed — some packages may be unused | every dependency has a named owner and a stated purpose; anything else is removed | — | Open |
| Media storage | none | `django-storages[s3]` + `boto3`, for S3-compatible object storage (see ADR-005) | Cloudflare R2 | Decided |

**Dependency strategy (direction, pending the rows above):** replace the current ad hoc dependency
state with pinned, reviewed, production-safe dependencies; normalize the file encoding to UTF-8;
split by environment; generate pinned requirements from a lock workflow rather than hand-editing.
The `psycopg2-binary` → `psycopg[binary]` swap should be settled after the deployment review, since
the driver choice interacts with the chosen host's build environment.

## Backend architecture

| Topic | Current | Candidate | Decision | Status |
|---|---|---|---|---|
| Settings layout | `bakery/settings/base.py` (dev defaults) + `heroku.py` (prod overrides) | `settings/base.py` + `local.py` + `test.py` + `production.py` | — | Open |
| Business logic location | inline in `control/views.py`, duplicated across views and model `@property` methods | dedicated services/domain module | — | Open |
| API layer | none | Django REST Framework, only if an external integration/API consumer is actually needed | — | Open |
| Auth/permissions | mix of no auth, `staff_member_required`, ad hoc template checks | consistent `LoginRequiredMixin` + real role-based permissions | — | Open |
| Caching | none | cache expensive dashboard/costing aggregates — only if measurements show it's needed | — | Open |
| Connection pooling | none | `CONN_MAX_AGE` tuning or a pooler (e.g. PgBouncer) — only if traffic/deployment topology requires it | — | Open |

### Data model — structural open questions (feed Phase 3 / Epic 3)

These are shape-of-the-schema questions, distinct from the business-meaning questions in
[project_requirements.md](project_requirements.md) ("Business rules & data semantics"). Both sets
must be answered before the Phase 3 migrations are written.

| Topic | Current | Candidate | Decision | Status |
|---|---|---|---|---|
| Ingredient line model | two parallel through-style models (`Bs_Ingredients` for base recipes, `Recipe_Ingredients` for products) | keep them separate if the business workflows genuinely differ; otherwise a single shared ingredient-line model with a typed parent reference | — | Open |
| Units & categories | free-text `CharField`s (`unit`, `categorie`) | controlled enums if the value set is stable, or lookup/reference tables if the values are business-managed | — | Open |
| Calculated values | recomputed inline per request, in `float()` | store as derived/read-only data only, never as editable business fields | — | Open |
| Deletion semantics | hard deletes everywhere | soft delete / archive for entities whose history must stay visible — which entities is a business call (see `project_requirements.md`) | — | Open |
| Money & quantity types | mixed (`CharField` quantity, `float()` math in views) | `Decimal` end-to-end, in the schema and the service layer | — | Open |

## Frontend

| Topic | Current | Candidate | Decision | Status |
|---|---|---|---|---|
| Templating | Django templates, `APP_DIRS=True`, no shared `base.html` | Django templates + shared `base.html` + partials | — | Open |
| CSS framework | Bootstrap (vendored, bundled in `bakery/static`) | current stable Bootstrap, or reconsider entirely | — | Open |
| Asset pipeline | none (hand-copied static files) | Vite for SCSS/JS bundling + cache busting | — | Open |
| Interactivity | plain JS per page, several empty JS files | vanilla JS modules, optionally HTMX for server-driven interactivity | — | Open |
| Is a full SPA needed? | n/a | leaning no — server-rendered is enough per current scope | — | Open |
| Template/CSS/JS linting | none | add where practical, alongside the Python tooling below | — | Open |

**Frontend direction (rationale, not yet decided):** the project does not need a full SPA to become
production-ready — a modern server-rendered Django frontend is enough. The candidate shape is: keep
Django templates for page rendering, add a shared `base.html` plus partials, move to a real asset
pipeline (Vite is the leading candidate) for SCSS/CSS bundling, small JS modules, and cache-busted
builds, and prefer lightweight progressive enhancement (vanilla JS modules, optionally HTMX for
server-driven interactivity) over a client-side framework.

## Infrastructure / operations

| Topic | Current | Candidate | Decision | Status |
|---|---|---|---|---|
| Hosting | Self-hosted: home server running Docker via Portainer; PostgreSQL in a separate container on the same machine. (Moved off Heroku after Heroku discontinued its free dyno/Postgres tier.) | Railway, Render, or DigitalOcean App Platform — narrowed per ADR-003; see "Hosting candidates" below | — | Open |
| Containerization | `Dockerfile` + `docker-compose.yaml` (expects external `bakery_simple` network) | Keep the custom Dockerfile as the deploy artifact on whichever host is chosen, rather than that platform's native buildpack — see ADR-004 and "Deployment method" below | Custom Dockerfile | Decided |
| Static/media storage | whitenoise for static assets; local `MEDIA_ROOT` config exists but points to a broken leftover path (`bluebiulding/media`) and nothing uses it yet | Keep whitenoise for static assets. For user-uploaded media (new: product photos, profile pictures), use S3-compatible object storage — see "Static & media file storage" below | Cloudflare R2 (see ADR-005) | Decided |
| CI/CD | none | pipeline: install → lint → test → security scan → build | — | Open |
| Error tracking / monitoring | none | Sentry or equivalent | — | Open |
| Uptime monitoring / alerting | none | external uptime check + alerting against the app health endpoint | — | Open |
| Backups | unknown/undocumented | documented PostgreSQL backup + restore + PITR strategy, with a drilled restore | — | Open |

### Hosting candidates (for the Django app + PostgreSQL)

Per ADR-003 in [decisions.md](decisions.md), the field is narrowed to these three — pick one and
log it as an ADR. Cost estimates assume this app's actual scope (single bakery, handful of
concurrent users, small dataset); sourced via web search 2026-07-21, confirm current pricing
before committing.

| Option | App compute | Database | Est. total/mo | GitHub auto-deploy | Notes |
|---|---|---|---|---|---|
| **Railway** | Hobby plan, $5/mo base includes $5 usage credit, billed per-second beyond that | ~$1–3/mo on light workloads, same usage pool | **~$5–10/mo** | Native, low setup effort | Cheapest of the three; no cold starts |
| **Render** | Starter $7/mo (always-on) or free tier (sleeps after ~15 min idle) | Free Postgres is deleted after 30–90 days depending on source — not viable long-term; paid Postgres from ~$15/mo | ~$22/mo paid, or $0 short-term on free tier | Native, deploy on push/release | Simplest DX, but the free database's expiry makes the free tier a trial, not a real option |
| **DigitalOcean App Platform** | $5/mo | Managed Postgres from $15/mo (HA doubles it to $60/mo); a non-HA "dev" database is ~$7/mo/512MB | ~$12–20/mo | Native | Priciest baseline here but closest to "professional" — managed backups/monitoring bundled |

None of the three is picked yet — resolve as an ADR in [decisions.md](decisions.md) once chosen.

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

None of this rules out any of the three — all can run the `main` (staging) / `production` (live)
two-branch model from ADR-010. Railway is the only one where a full 3-tier flow (PR preview +
staging + production) doesn't add plan-tier or per-resource cost; worth weighing if per-PR
previews end up mattering.

### Static & media file storage (product photos, profile pictures)

New requirement: users can upload product photos and profile pictures (see
[project_requirements.md](project_requirements.md) backlog). Profile pictures are personal data —
see [gdpr.md](gdpr.md) §1 data inventory.

| Topic | Current | Candidate | Decision | Status |
|---|---|---|---|---|
| Static assets (CSS/JS/bundled images) | whitenoise, unchanged | whitenoise, unchanged — this decision only affects user uploads | No change | Decided (no change needed) |
| User-uploaded media | `MEDIA_ROOT` set to a broken leftover local path, not implemented | S3-compatible object storage via `django-storages` — Cloudflare R2 is the lead candidate (zero egress, 10GB/1M-write/10M-read free tier, provider-agnostic) | Cloudflare R2 | Decided (see ADR-005) |
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
| Cost model | n/a | Databricks Community Edition is free but doesn't support external API-triggered jobs (notebook-only, no job-scheduling API) — a real triggered-batch-job workflow needs a paid workspace, billed on top of the underlying cloud compute. Worth re-confirming Spark/Databricks is still the right call at this data scale (a single bakery's dataset) vs. a much cheaper plain-Python batch job, before committing spend. | Open |

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

- Is Heroku actually still the deployment target, or has that changed?
- Any hosting/budget constraints that rule out a candidate (e.g. managed Postgres cost)?
- Any org/team constraints (existing infra, required cloud provider, compliance requirements)
  that should narrow these choices before Phase 3+ of `PRODUCTION_UPDATE_PLAN.md` starts?
