# Architecture & Product Decisions

Append-only log of every real choice about stack, architecture, data model, process or scope. **Its
only job is to stop settled questions being re-opened by accident.** Never delete an entry —
supersede it, or note the amendment on its Status line.

- **Read the index first**, then only the entries you need.
- Entries are terse by design. Work lives in [`PRODUCTION_UPDATE_PLAN.md`](../PRODUCTION_UPDATE_PLAN.md),
  current state in [tech_stack.md](tech_stack.md) and
  [project_requirements.md](project_requirements.md), and anything **still open** in
  [roadmap.md](roadmap.md) — never here.
- **Rejected is the load-bearing section** — an option plus the one reason it lost. That is what makes
  re-litigating visible. Nothing longer belongs here.
- A superseded entry keeps no live rules — surviving clauses move into the superseding ADR.
- **Template:** `## ADR-0XX: <title>` · **Date / Status** · **Decision** · **Rejected** · **Traps**
  (accepted risks and hazards with no other home; never a task list).

## Index

| # | Title | Status | Decision |
|---|---|---|---|
| [001](#adr-001-branching-strategy-for-the-redesign) | Branching strategy | **Superseded by 010** | — |
| [002](#adr-002-ai-insights-service-on-apache-spark--databricks) | AI insights on Spark/Databricks | Accepted (confirmed + reshaped by 036) | A separate batch component, not built into Django |
| [003](#adr-003-narrow-hosting-candidates-to-railway-render-digitalocean) | Narrow hosting candidates | Accepted (final pick 013) | Railway, Render, DigitalOcean only |
| [004](#adr-004-deploy-via-the-custom-dockerfile-not-a-buildpack) | Docker, not buildpack | Accepted | The repo's `Dockerfile` is the deploy artifact everywhere |
| [005](#adr-005-store-user-uploaded-media-in-s3-compatible-object-storage) | Media in object storage | Accepted | Cloudflare R2 via `django-storages`, decoupled from hosting |
| [006](#adr-006-multi-tenant-saas-architecture-confirmed) | Multi-tenant SaaS | Accepted | One deployment, many bakeries; each bakery is a tenant |
| [007](#adr-007-app-and-database-always-run-as-separate-services) | App and DB separate | Accepted | Never one image |
| [008](#adr-008-shared-multi-tenant-database-with-a-tenant-scoped-full-export) | Shared DB + tenant export | Accepted (format in 035) | One database, row-level tenant isolation at the query layer |
| [009](#adr-009-a-dedicated-gdpr-personal-data-export) | GDPR personal-data export | Accepted | A second, subject-scoped export beside the bulk CSVs |
| [010](#adr-010-main-as-integration-production-as-the-deploy-branch) | Branch model | Accepted (supersedes 001; amended by 014) | `main` integrates, `production` deploys, releases tagged |
| [011](#adr-011-minimal-ci-in-epic-1-epic-6-extends-it) | CI in two steps | Accepted (shape in 031) | Minimal CI in Epic 1; Epic 6 extends rather than replaces |
| [012](#adr-012-the-plan-becomes-a-task-backlog) | Plan → task backlog | Accepted | Epics of numbered, stable-ID tasks; undecided material outside it |
| [013](#adr-013-railway-hobby-plan-as-the-hosting-platform) | Railway (Hobby) | Accepted | ~$6/mo, EU West (Amsterdam), app + Postgres as two services |
| [014](#adr-014-local-docker-compose-is-the-devtest-environment) | Local dev/test only | Accepted (amends 010) | No persistent hosted staging; a PR environment on the release PR only |
| [015](#adr-015-host-portability-is-a-standing-design-constraint) | Host portability | Accepted | Eight standing rules; configuration changes only, never code |
| [016](#adr-016-phase-1-go-to-market) | Go-to-market | Accepted | One Irish pilot, free, no deadline, no billing epic |
| [017](#adr-017-batchlot-food-traceability-is-in-scope-as-its-own-epic) | Traceability in scope | Accepted (entities in 033) | EU Reg. 178/2002 Art. 18, built as Epic 17 |
| [018](#adr-018-costing-and-money-semantics) | Costing & money semantics | Accepted | Invoice-shaped prices, canonical kg/l/each, net-of-VAT, versioned history |
| [019](#adr-019-deletion-semantics-supplier-identity-administration-surfaces) | Deletion, identity, admin surfaces | Accepted (uniqueness amended by 027) | Soft delete where records outlive; supplier name unique per tenant |
| [020](#adr-020-three-per-tenant-roles-on-a-membership-record) | Three per-tenant roles | Accepted (enforcement in 027/028) | Owner / Staff / Read-only on a membership record |
| [021](#adr-021-non-functional-targets) | Non-functional targets | Accepted | p95 500 ms / 2 s, WCAG 2.2 **Level A**, responsive, `en-IE`/EUR translation-ready |
| [022](#adr-022-goods-receipts-drive-cost-lines-accept-a-material-or-a-base-recipe) | Receipts drive cost; nested recipes | Accepted | Latest receipt sets cost, with provenance; lines may reference a base recipe |
| [023](#adr-023-dashboard-becomes-an-overview-settings-becomes-self-administration) | Overview + self-administration | Accepted | Dashboard becomes an overview; settings becomes the tenant surface |
| [024](#adr-024-feature-backlog-prioritization-moscow) | MoSCoW prioritization | Accepted | Must/Should/Could/Won't across the whole feature backlog |
| [025](#adr-025-runtime-baseline--django-52-lts-on-python-313) | Runtime baseline | Accepted (amended by 029) | Django 5.2 LTS on Python 3.13, direct from 3.2; creates Epic 19 |
| [026](#adr-026-pin-postgresql-17-across-every-environment) | PostgreSQL 17 | Accepted | Pinned identically everywhere; majors must match |
| [027](#adr-027-adopt-the-capabilities-the-upgrade-unlocks) | Adopt unlocked capabilities | Accepted (amends 019) | Twelve Django 5.2 / PG 17 features adopted instead of hand-built |
| [028](#adr-028-backend-architecture) | Backend architecture | Accepted | Three settings modules, batch-first services, no API, no cache, Brevo |
| [029](#adr-029-dependency-management) | Dependency management | Accepted (amends 025) | `uv pip compile` over `requirements/{base,dev,prod}.in` |
| [030](#adr-030-frontend) | Frontend | Accepted | Shared `base.html`, Bootstrap 5.3, HTMX, **no Node build step** |
| [031](#adr-031-operations) | Operations | Accepted | Coverage-gated CI, git-watch deploys, Sentry EU, UptimeRobot, two backup tracks |
| [032](#adr-032-one-shared-recipeline-and-categories-as-a-lookup-table) | `RecipeLine` + categories | Accepted | One line table with `CHECK`-enforced XORs; one tenant-scoped `Category` |
| [033](#adr-033-traceability-entities) | Traceability entities | Accepted | Receipt headers with lines; runs → batches; `YYYYMMDD-NNN` lot codes |
| [034](#adr-034-ruff-for-lint-and-format-pytest-django-as-the-runner) | Lint, format, test tooling | Accepted | `ruff` for both; `pytest-django`; `[tool.*]`-only `pyproject.toml` |
| [035](#adr-035-tenant-full-data-export-format) | Tenant export format | Accepted | ZIP of per-table CSVs + `manifest.json` |
| [036](#adr-036-ai-insights-on-databricks-serverless-and-gunicorn-stands) | Databricks Serverless; gunicorn | Accepted (confirms 002) | Nightly job on AWS EU Ireland fed by an R2 extract; WSGI stands |

---

## ADR-001: Branching strategy for the redesign

**2026-07-16 · Superseded by [010](#adr-010-main-as-integration-production-as-the-deploy-branch).** It
assumed `main` mirrors production. The branch-naming convention and PR discipline it introduced
survive and now live in ADR-010; nothing else here is in force.

## ADR-002: AI insights service on Apache Spark + Databricks

- **2026-07-16 · Accepted** — was `Proposed` until confirmed by [036](#adr-036-ai-insights-on-databricks-serverless-and-gunicorn-stands), which also amends the delivery shape: not event-triggered, and it does not read the app's database.
- **Decision:** AI-derived operational insights (margin alerts, an analytics dashboard) are a separate batch component on **Apache Spark, run on Databricks**, returning results to the app — not built into Django.
- **Rejected:** Nothing, at the time — a plain-Python batch job was **not** compared against Spark for a dataset this size. That gap became ADR-024's null hypothesis and ADR-036 closed it.
- **Traps:** Community Edition is notebook-only with no job scheduling, so a paid workspace is required, billed separately from app hosting.

## ADR-003: Narrow hosting candidates to Railway, Render, DigitalOcean

- **2026-07-21 · Accepted** — final pick is [013](#adr-013-railway-hobby-plan-as-the-hosting-platform).
- **Decision:** Only **Railway, Render and DigitalOcean App Platform** stay active. Tooling, storage and CI/CD target "works on any of the three". This narrows; it does not choose.
- **Rejected:** **Fly.io, Sevalla, Hetzner+Coolify** — set aside. **Koyeb** — free tier fits, but paid plans jump to $79/mo. **Oracle Cloud Always Free** — front-runner on cost, lost on operational model: own reverse proxy, TLS and firewall, no native GitHub deploy.

## ADR-004: Deploy via the custom Dockerfile, not a buildpack

- **2026-07-21 · Accepted**
- **Decision:** Keep and harden the existing `Dockerfile` as **the** deployment artifact — one source of truth across dev, Compose and every host. Becomes rule 1 of [015](#adr-015-host-portability-is-a-standing-design-constraint).
- **Rejected:** **Native buildpacks** — each picks its own base image and build steps, so the app needs separate verification per host; all three candidates prioritize a root `Dockerfile` anyway.
- **Traps:** The cost is maintaining the Dockerfile rather than outsourcing that.

## ADR-005: Store user-uploaded media in S3-compatible object storage

- **2026-07-21 · Accepted**
- **Decision:** **Cloudflare R2** via `django-storages`, decoupled from app hosting — zero egress, a 10 GB free tier, provider-agnostic, so storage need not move if the host does.
- **Rejected:** **Local disk** — not durable or shared on any candidate. **AWS S3** — egress fees, free tier expires after 12 months. **DigitalOcean Spaces** — a fallback only if DigitalOcean won compute. **Oracle Object Storage** — a fourth provider relationship for no benefit.
- **Traps:** The **backup bucket is kept separate from media** ([031](#adr-031-operations)), so media credentials can never read or delete backups.

## ADR-006: Multi-tenant SaaS architecture confirmed

- **2026-07-21 · Accepted**
- **Decision:** **Multi-tenant SaaS.** Each bakery is a tenant; one deployment serves many. Every business model needs a `Bakery` FK.
- **Rejected:** **Single-tenant (one deployment per bakery)** — doesn't match the intended direction of a shared database with per-tenant export as a differentiator.
- **Traps:** Changes the GDPR model — **Bakery-the-product is Processor, each tenant is Controller** — and triggers a DPIA reassessment.

## ADR-007: App and database always run as separate services

- **2026-07-21 · Accepted**
- **Decision:** **Always separate containers/services**, never one image.
- **Rejected:** **Bundling Postgres into the app image** — breaks independent backups and the "app container is stateless and disposable" property ADR-004 depends on; no candidate offers it anyway.
- **Traps:** Later the reason Railway's one-service Free plan is unusable.

## ADR-008: Shared multi-tenant database, with a tenant-scoped full export

- **2026-07-21 · Accepted** — export *format* fixed by [035](#adr-035-tenant-full-data-export-format).
- **Decision:** **A single shared database with row-level tenant isolation** — a `Bakery` model plus a tenant FK on every tenant-scoped table, enforced **at the query layer**, not at the database-instance level. Plus a **tenant-scoped full export** in a format that does not depend on this app's Postgres schema or version to reload.
- **Rejected:** **Database-per-tenant** — every candidate prices managed Postgres per instance, so N bakeries means N bills for a small dataset. **Handing over a raw `pg_dump`** — assumes the recipient runs a compatible Postgres.
- **Traps:** **Query-layer scoping is correctness-critical — a missed filter is a cross-tenant data leak.** FK migrations touch nearly every table.

## ADR-009: A dedicated GDPR personal-data export

- **2026-07-21 · Accepted**
- **Decision:** Keep the bulk CSV exports as an **admin feature, not a compliance mechanism**. Add a second **subject-scoped export** — one person's data across models — gated to the requester's own data or an admin acting for them. Distinct from ADR-008's tenant-wide export.
- **Rejected:** **Retrofitting the bulk export with a subject filter** — conflating the two shapes risks over-exposing business data in a personal-data request, or under-scoping a real admin export.

## ADR-010: `main` as integration, `production` as the deploy branch

- **2026-07-21 · Accepted** — **supersedes [001](#adr-001-branching-strategy-for-the-redesign)**; the persistent-staging clause is **amended by [014](#adr-014-local-docker-compose-is-the-devtest-environment)**.
- **Decision:** `main` is the **integration/dev-test branch**, not what users hit. A **`production` branch holds what's live**; promotion is a deliberate PR from `main`, and every merge to `production` is **tagged semver** and published as a GitHub Release. Both branches protected: PR only, no force-pushes, required status checks once Epic 6 exists, 0 approvals while solo. **Branch discipline, carried over from ADR-001:** one branch per agreed plan, named `phase-N-<slug>` / `feature-<slug>` / `gdpr-<slug>` / `stack-<slug>`, opened as a PR immediately and merged before the next starts from an updated `main`. No stacking, no direct commits. Squash-merge.
- **Rejected:** **Keeping `main` as the deployed branch** — no safe integration point before users see changes. **Full GitFlow** — two branches get the same safety with less ceremony. **A single long-lived `redesign` branch** (ADR-001) — too high a merge-conflict blast radius. **Trunk-based with feature flags** (ADR-001) — too heavyweight before tests or CI exist. **Mandatory per-PR previews as a third tier** — cost; ADR-014 takes it up for the release PR only.
- **Traps:** Each session states its target branch before coding.

## ADR-011: Minimal CI in Epic 1; Epic 6 extends it

- **2026-07-21 · Accepted** — full pipeline shape fixed by [031](#adr-031-operations).
- **Decision:** Two touchpoints. **Epic 1** gets `manage.py check`, a migrations check, `docker build` validation and a basic lint pass on every PR. **Epic 6 extends that workflow rather than replacing it.** Deploy automation waits for an actual host.
- **Rejected:** **Moving all of Epic 6 forward** — it needs a test suite that doesn't exist and a host that isn't picked. **Leaving CI entirely in Epic 6** — five epics of PRs merging on manual review alone, once branch protection is live.

## ADR-012: The plan becomes a task backlog

- **2026-07-28 · Accepted**
- **Decision:** The plan is a **backlog** of **Epics** holding numbered tasks (`3.12` = Epic 3, task 12). **Task IDs are stable and never renumbered.** Epics 1–8 keep the original phase numbers so "Phase N" references still resolve. **Undecided material does not live in the backlog**; **every decision becomes a task**, tracked in a coverage table, and a task blocked on an open question is `Blocked` with a pointer — so an undecided question can no longer be implemented by accident.
- **Rejected:** **A separate issue tracker** — better tooling, but it splits working context away from the repo and the sessions where planning happens; revisit if more people join. **Prose plus phase-level tracking** — far too coarse for hundreds of pieces of work.
- **Traps:** Every future ADR gains a step: add its tasks and a coverage row **in the same session**.

## ADR-013: Railway (Hobby plan) as the hosting platform

- **2026-08-03 · Accepted**
- **Decision:** **Railway, Hobby** ($5/mo including $5 usage credit), app and Postgres as separate services, built from the repo's `Dockerfile`, in **EU West (Amsterdam)**. Expected **~$6/mo**. **Railway's free options are explicitly rejected:** the 30-day trial deletes stateful volumes 30 days after credits expire, and the Free plan (0.5 GB RAM, one service) cannot run an app *and* a database, which ADR-007 requires.
- **Rejected:** **Render** — per-PR previews need the Pro workspace and paid Postgres starts ~$15/mo, a realistic ~$22/mo. **DigitalOcean App Platform** — ~$12–20/mo, closest to a professional baseline, but 2–3× Railway for a single-bakery workload needing nothing it adds. Both stay viable fallbacks.
- **Traps:**
  - **The region must be set before any service is created.** Railway's default is US West and the personal data is in the *database* — an app in Amsterdam with a default-region Postgres puts the data in California. Moving a volume later forces a migration **with downtime**.
  - **Backups are not automatic** and there is **no PITR**. **No uptime SLA, no HA Postgres** on Hobby.
  - **Vendor ownership is an accepted risk, not a solved one.** Storage location is satisfied, but Railway is US-incorporated, so US law can reach the parent even for EU-held data. Accepted because the market is Ireland, where US-owned cloud is the norm, the exposure is shared by nearly every business on AWS/Azure/GCP, and SCCs remain a fallback. Revisit before expanding beyond Ireland — [roadmap.md](roadmap.md) 11.14, 11.15.

## ADR-014: Local Docker Compose is the dev/test environment

- **2026-08-03 · Accepted** — **amends [010](#adr-010-main-as-integration-production-as-the-deploy-branch)'s persistent-staging clause**.
- **Decision:** The dev/test environment is **local `docker-compose`**, using the same `Dockerfile` Railway deploys. **No persistent hosted staging.** Testing splits by branch: feature branch → automated unit tests locally and in CI; `main` → manual integration verification of the *merged* result locally; `main` → `production` PR → the release gate. Because local verification never exercises Railway, a **Railway PR environment runs on the release PR only** — auto-created on open, destroyed on merge, well under $1/mo, deliberately **not** on feature PRs.
- **Rejected:** **Persistent hosted staging** — roughly doubles the bill for an environment one developer leaves idle almost always; it becomes necessary the moment `main` must be verifiable by someone other than its author. **PR environments on every feature PR** — redundant with local testing, and it multiplies the seeding problem. **A self-hosted runner refreshing the local machine** — disproportionate, and only works while that machine is on.
- **Traps:** **Makes the local Docker setup load-bearing** — it is the only integration-test environment, so drift from production is a correctness problem. PR environments clone services but **not volume data**, so the release environment starts empty and needs migrations plus seed data. **`main` need not be green at every moment** (nothing deploys from it); the binding rule is local verification before a release PR merges.

## ADR-015: Host portability is a standing design constraint

- **2026-08-03 · Accepted**
- **Decision:** The app and database stay deployable on **any host running a Docker image and a PostgreSQL service**, with **configuration changes only, never code changes**. Eight rules, tabulated with their owning tasks in [tech_stack.md](tech_stack.md): Dockerfile is the only build artifact; all config from environment variables with `DATABASE_URL` as the database contract; bind to `$PORT`; migrations are a release step, never in `CMD`; a host-independent logical dump maintained *in addition to* native snapshots; core PostgreSQL only; persistent state only in Postgres and object storage; every variable in a committed `.env.example`.
- **Rejected:** **Accepting lock-in for convenience** — it would silently foreclose the residency revisit, the decision most likely to need reversing. **A full infrastructure abstraction** (Kubernetes, Terraform) — wildly disproportionate for a two-service app.
- **Traps:** Baking `migrate` into `CMD` makes every replica race to migrate on boot. Snapshots are for fast same-host rollback; **the dump is what makes the host replaceable.** Accepted lock-in: git-watch deploys and the release-PR preview — no data, ~a day to rebuild. The ongoing cost is discipline: a future ADR wanting a host-specific feature must argue against this one.

## ADR-016: Phase 1 go-to-market

- **2026-08-06 · Accepted**
- **Decision:** **First user:** one friendly Irish bakery, a real food business operator with real data. **Timeline:** no committed date. **Phase 1:** a **free pilot** — no payment provider, subscription state, billing tables or invoicing. **Eventual pricing:** a **flat per-bakery monthly subscription**, all features, unlimited users — recorded not because it is being built but so nothing contradicts it: **no feature gating by plan, no per-seat counting.**
- **Rejected:** **Paid beta / paid from day one** — one pilot tenant doesn't justify a payment integration, and it would put subscription state in the schema before the redesign. **Tiered pricing** — requires feature gating inside the permission layer, permanently complicating Epics 2 and 4 for revenue that doesn't exist. **Per-seat pricing** — makes seat counting a product concern and couples pricing to the role matrix.
- **Traps:** **No billing epic exists, and none should be added** — proposing one needs a superseding ADR. Multi-tenancy stays required even with one tenant, and this does **not** downgrade the isolation tests, which must exist *before* a second tenant. **The pilot is a real controller**, so the per-tenant DPA applies — "it's only a pilot" is not a GDPR exemption.

## ADR-017: Batch/lot food traceability is in scope, as its own epic

- **2026-08-06 · Accepted** — entity shape settled by [033](#adr-033-traceability-entities); the allergen question it left open is answered by [024](#adr-024-feature-backlog-prioritization-moscow).
- **Decision:** **EU Reg. 178/2002 Art. 18** requires a food business operator to identify **one step back** and **one step forward**, producing records to the **FSAI** on demand; the app is a pure current-state catalogue and cannot. Traceability is **in-scope**, built as **Epic 17** rather than folded into Epic 3. **Floor:** one-step-back/forward — full internal mass-balance is a **Should**. **Depends on Epic 3**, because a record without a trustworthy quantity isn't worth writing. **Not in scope:** HACCP, temperature/cleaning logs, recall workflows.
- **Rejected:** **Leaving it as the bakery's paper problem** — it is a legal obligation on them and the pilot needs it. **Bolting `lot` fields onto existing models** — **a lot is an event over time, not an attribute of a catalogue item**, and this app already suffers that conflation (`RawMaterial.price` has no time dimension), so repeating it would make the schema actively wrong rather than merely incomplete. **A third-party traceability system** — not evaluated; revisit only if Epic 17 proves much larger than scoped.
- **Traps:**
  - **Pre-answers deletion semantics:** anything referenced by a traceability record can never be hard-deleted, so soft delete stops being a judgment call.
  - **Retention gains a legal floor GDPR minimization cannot override** — a *minimum*, commonly five years. Where such a record names a supplier contact, floor and policy must be **reconciled**, not chosen freely.
  - **Records must be append-only** — no hard delete, no silent retroactive edit.
  - **A partial implementation is worse than none if it looks complete** — nothing may present itself as a compliance record until the trace path is whole.

## ADR-018: Costing and money semantics

- **2026-08-06 · Accepted**
- **Decision:** Four questions decided as **one**, because what a price *means* determines the unit, which determines where VAT applies, which determines what a price-history row contains.
  1. **Price basis** — `RawMaterial` stores what the invoice says: purchase price, pack quantity, purchase unit (€12.50 / 25 / kg). Cost per canonical unit is derived at cost time and **never persisted**. Exactly what a goods-receipt line records, so the two agree by construction.
  2. **Canonical units — kilogram, litre, each**, one per dimension; purchase units convert through a **factor in a reference table**, so adding "sack" is data entry, not a migration.
  3. **VAT — all stored money is net (ex-VAT)**, applied only at display or sale. Rates in a **dated table**; a product references a **code**, not a number.
  4. **Price history — versioned, from two sources.** Input prices come free from ADR-017's receipts; sale prices get dated `ProductPrice` rows — one price is an observed fact, the other a decision the bakery makes.
- **Rejected:** **Storing €/canonical-unit directly** — discards the invoice figure and makes the user do arithmetic on every price change. **Persisting the derived unit price** — two fields that can disagree. **Gram/millilitre canonical units** — considered; the precision cost below is the price of not choosing them. **A plain VAT-rate field** — a statutory change would recompute past margins at today's rate. **Gross storage** — every margin calculation begins with a division, and the repeating decimals propagate. **Current-price-only** — makes "why did this margin drop in March?" unanswerable, which is what Epic 16's alerts are for.
- **Traps:**
  - **Precision and rounding are load-bearing, because the canonical units are large.** 7 g of yeast is `0.007`. Quantities need ≥ `Decimal(12,4)` (`12,6` safer), money is carried beyond 2 dp internally, and rounding to 2 dp happens **only at presentation** — written down and tested, not inherited from whatever Python does.
  - **Existing data has no recorded basis** — today's values mean whatever the person typing them assumed, so backfilling is a per-row human-judgment exercise, not an automatic migration.
  - **The inline `float()` costing is now definitively wrong**, not merely duplicated — it cannot express any of the four decisions. Deleted, not patched.

## ADR-019: Deletion semantics, supplier identity, administration surfaces

- **2026-08-06 · Accepted** — the **uniqueness clause is amended by [027](#adr-027-adopt-the-capabilities-the-upgrade-unlocks)**: case-insensitive uniqueness, declined below purely on implementation cost, is adopted once functional unique constraints remove that cost. Every other clause stands.
- **Decision:**
  1. **Soft delete for anything referenced by a record that outlives it** — `Supplier`, `RawMaterial`, `Product`, `Base_recipes`. **Ingredient lines stay hard-deletable**, being meaningful only inside their parent.
  2. **Supplier name is unique per tenant, not globally** — two bakeries may both buy from "Odlums"; within one tenant a duplicate is almost always a data-entry error.
  3. **Uniqueness applies among non-archived rows only** — a partial unique index, since a plain composite constraint would let archiving "Odlums" block that name forever.
  4. **Two administration surfaces, two audiences.** In-app settings is the tenant's — scoped, role-checked, audited. The **Django admin is superuser-only support tooling**, never linked from the tenant UI.
- **Rejected:** **Soft delete everywhere** — an archived filter on every query forever, where a missed filter resurrects deleted data. **Soft delete only on the forced set** — deleting a `Product` would orphan its price history, needing a delete block anyway, which is soft delete with worse ergonomics. **No uniqueness, warn only** — duplicates silently split a supplier's cost history across two unlinked rows. **Disabling the Django admin in production** — leaves `psql` against production as the data-repair tool: a worse risk. **Both surfaces with identical operations** — every rule enforced twice.
- **Traps:**
  - **Two orthogonal, correctness-critical filters now exist:** tenant scope and archived state. They must combine in **one** base manager and be tested together — filtering tenant but not archived is a bug; archived but not tenant is a data leak.
  - **"Delete" now means two different things** depending on the model; the UI must say *archive* where it archives, and archived rows need a way back.
  - **The Django admin is a deliberate cross-tenant surface** — `ModelAdmin` does **not** apply tenant-scoped managers by default.

## ADR-020: Three per-tenant roles on a membership record

- **2026-08-06 · Accepted** — enforcement completed by [027](#adr-027-adopt-the-capabilities-the-upgrade-unlocks) and [028](#adr-028-backend-architecture).
- **Decision:** **Three roles per tenant** — **Owner** (full administration of their own bakery), **Staff** (daily work; no user management or tenant settings), **Read-only** (view and export, the accountant seat). **The role lives on a membership record** (user × bakery × role), not on the user: Django's global `Group` cannot express "Owner of bakery A", and a membership means a user *could* belong to several tenants without a schema change. **"Manager" is deliberately deferred**, not rejected.
- **Rejected:** **Four roles including Manager** — the pilot can't articulate it, and a role whose permissions are guessed is worse than one that doesn't exist; adding it later is a table row *provided* checks are capability-based. **Two roles (Admin/Staff)** — with no read-only tier an accountant gets either write access or a shared login, and shared logins destroy the audit trail Epics 11 and 17 depend on. **Django groups plus per-tenant editable permissions** — makes "who can do what" per-tenant configuration that can't be reasoned about or tested centrally.
- **Traps:** **Checks must be capability-named, not role-named** — this is what keeps Manager cheap to add, and it costs nothing now. **Read-only can export**, deliberately — every export is audit-logged, and **that logging is what makes it acceptable, not the role restriction.** Traceability writes are Staff-level but append-only, so a mistaken entry is corrected by a new record. Every existing user has no role; assigning one is a migration with a human decision in it.

## ADR-021: Non-functional targets

- **2026-08-06 · Accepted.** Decided *before* Epic 5's rewrite, since accessibility and localization are far more expensive to retrofit.
- **Decision:** **Performance** — p95 < ~500 ms normal pages, < ~2 s dashboard costing aggregate, ~10 concurrent users/tenant, on thousands of rows. **Accessibility — WCAG 2.2 Level A.** **Devices** — one responsive UI, phone→desktop, current and previous major Chrome/Firefox/Safari/Edge; no IE11, no native app. **Localization** — English and euro only, but translation-ready: `gettext` on display text, one currency formatter, **no hardcoded `€`**.
- **Rejected:** **No numeric performance target** — leaves "is this a regression?" a judgment call every time. **Sub-200 ms enforced in CI** — Railway Hobby shares CPU, making it partly unenforceable. **WCAG 2.2 AA** — the recommended option and not chosen; see below. **Desktop-first** — goods receipts get recorded at the delivery door on a phone. **Mobile-first** — costing views are inherently wide tables. **Hardcoded English/€** — makes the expansion trigger expensive exactly when it fires. **Multi-language/currency now** — the next countries are undecided, and multi-currency touches every money column.
- **Traps:** **Level A is below what procurement typically asks for** — it excludes AA's contrast ratios, visible focus indicators, consistent navigation and error suggestions ([roadmap.md](roadmap.md) 10.15). **Performance targets need something to measure them** — a documented budget now, an observed one once Epic 7 exists, never a CI gate. **Translation-readiness is a discipline, not a feature** — Epic 5 must not introduce a single hardcoded `€`, including in existing templates it touches.

## ADR-022: Goods receipts drive cost; lines accept a material or a base recipe

- **2026-08-06 · Accepted**
- **Decision:**
  1. **The latest goods receipt sets current cost** — most recent by **receipt date** (not entry date), ties by creation time, so a late-entered back-dated delivery behaves correctly.
  2. **A manual price stays possible, labelled an estimate** — a material never received must still be costable.
  3. **Every cost figure carries its provenance** — a margin from a guess and one from an invoice are not the same claim.
  4. **A line references either a raw material or a base recipe**, and costing recurses.
- **Rejected:** **Receipts as traceability only, price by hand** — the same figure entered twice with nothing detecting divergence. **Receipt price as the *only* price** — a material with no receipt couldn't be costed at all. **Keeping base recipes and products disconnected** — one dough used in six products would be restated six times, and a flour price change means editing six products. **Merging both into one model with an `is_sellable` flag** — genuinely cleaner and not chosen: a larger migration, and it collapses a distinction the bakery may think in.
- **Traps:**
  - **Recursive costing introduces a cycle risk that must be prevented, not merely avoided** — a recipe containing itself loops forever, and **nothing in the current schema prevents it.**
  - **`recipe_yeld` becomes load-bearing** — cost must be expressible per unit of yield, so the yield needs a real numeric value and a unit.
  - **Provenance has to be modelled, not just displayed** — retrofitting it into a bare `Decimal` is painful.
  - Epic 17's trace and this recursion are the same traversal in opposite directions; allergen aggregation is a third.

## ADR-023: Dashboard becomes an overview; settings becomes self-administration

- **2026-08-06 · Accepted**
- **Decision:** **The dashboard becomes a genuine overview** — summary strip (product count, average margin, materials with no or stale pricing), worst-margin products, recent input price movements; the full product list moves to its own page. **The settings area becomes the tenant's self-administration surface**, owned by Owner: invite/remove users and set roles, edit bakery details, manage reference data, run exports; Read-only reaches exports and nothing else writable. This is the surface the Django admin deliberately is **not**.
- **Rejected:** **Keeping the dashboard as the cost/margin list** with better sorting — lower-risk, but the overview is where price history pays off. **Fixing only the math** — too little given Epic 5 is rewriting templates anyway. **Keeping reference data in the Django admin** — every unit or VAT change becomes a support request. **Superuser-side user management only** — leaves Owner with nothing to administer and makes onboarding tenant #2 manual.
- **Traps:** **The dashboard depends on Epic 3, not just Epic 5** — price movements and staleness need dated prices and receipts. **Inviting users requires email, which the app does not send** — a hypothetical processor becomes a required one. **Tenant-editable reference data is not uniformly safe** — VAT rates and categories are fine; unit conversion factors are not ([roadmap.md](roadmap.md) 10.17). **This replaces the broken user-delete view rather than patching it.**

## ADR-024: Feature backlog prioritization (MoSCoW)

- **2026-08-06 · Accepted** — the AI-insights "re-scope before spending" is **discharged by [036](#adr-036-ai-insights-on-databricks-serverless-and-gunicorn-stands)**.
- **Decision:** **Must** — traceability · multi-tenancy · real search/filter · supplier price comparison · user & role management (**merged**, not separate — it *is* ADR-023's settings area assigning ADR-020's roles). **Should** — tenant export · GDPR export · trend reporting · allergen data (**new Epic 18**). **Could** — product photos · stock/quantity-on-hand (not an epic) · AI insights. **Won't this round** — profile pictures · self-service registration · billing.
- **Rejected:** **Search as Should** — dead inputs in a freshly rewritten UI are indefensible, and the fix is cheap while templates are open. **Reporting as Must** — charts over one week of data aren't persuasive. **Media as Should** — it would put the profile-picture legal basis on the critical path. **Supplier comparison as Could** — the cautious call, rejected since the user rates it core value. **Profile pictures at all this round** — personal data with an undecided legal basis, a storage DPA and erasure obligations, for no operational value at a one-tenant pilot. **Self-service registration** — open signup with no billing gate produces spam tenants and abandoned accounts holding personal data you must then retain and delete.
- **Traps:**
  - **Supplier comparison as a Must forces a schema change beyond Epic 3's scope.** `RawMaterial` has a **single** supplier FK, so a comparison view would show one row; the real relationship belongs on the **goods receipt**, so the FK becomes at most an optional *preferred supplier*. **This makes the feature depend on Epic 17.**
  - **ADR-023's overview is the whole of the reporting story for the first release** — said plainly so it isn't quietly expanded.
  - **Allergen data gets the same care as traceability:** information that looks authoritative but is incomplete is worse than none, because a consumer-facing claim depends on it.
  - **Stock stays excluded**, but the traceability entities must be designed so on-hand *could* later be derived.

## ADR-025: Runtime baseline — Django 5.2 LTS on Python 3.13

- **2026-08-10 · Accepted** — package list **amended by [029](#adr-029-dependency-management)** (`Pillow`); unlocked capabilities adopted in [027](#adr-027-adopt-the-capabilities-the-upgrade-unlocks).
- **Decision:** Everything the app runs on is past end of life, so one decision covers the whole chain — the Django version determines the Python range, which determines the driver and the pin set.
  1. **Django 5.2 LTS — not current stable.** Verified 2026-08-10: 5.2 is supported to **April 2028**; stable 6.1 only to Dec 2027; 6.0 left mainstream support six days before this decision. The older LTS has the longer runway. Next hop **6.2 LTS**.
  2. **Python 3.13** — supported by *both* ends of the path (5.2 takes 3.10–3.14, 6.2 takes 3.12–3.14), so the 6.2 upgrade needs no Python change. `python:3.13-slim` is the **single** place the version lives; `runtime.txt` is deleted.
  3. **Upgrade directly, 3.2 → 5.2** — no staged stop at 4.2.
  4. **Its own epic (19)**, after Epic 2 and before Epic 3.
  5. **`psycopg[binary]` 3** replaces `psycopg2-binary` — native since Django 4.2, and a new build is the cheapest moment to switch drivers.
  6. **The dependency set is a rule, not pins in this ADR:** latest release compatible with 5.2/3.13 *at lock time*. Four removed outright — `asgiref`/`sqlparse` (Django's own transitive deps), `pytz` (dropped in 5.0), `environ==1.0` (an unrelated package whose module collides with `django-environ`'s), `dj-database-url` (imported nowhere).
  7. **`django-mathfilters` dropped** — classifiers stop at Django 3.x: a hard blocker. Its two templates do cost arithmetic **in the template**, which ADR-018 ruled wrong.
- **Rejected:** **Django 6.1** — a *shorter* window than the older LTS, and it puts a solo developer on the 8-month feature treadmill. **Staged 3.2 → 4.2 → 5.2** — the conventional advice, rejected because staging exists so a test suite catches each release's removals and every `tests.py` here is an empty stub, and because **most of the code that would break is already scheduled for deletion**: migrating it carefully through 4.2 preserves a corpse. **Python 3.12** — security-fixes-only since Oct 2025. **Python 3.14** — needs 5.2.8+, and 3.13 covers the whole path through 6.2. **Keeping `psycopg2-binary`** — maintenance-only upstream, and deferring means switching later against a schema holding real tenant data. **Pinning exact patch versions here** — stale within weeks in an append-only log. **The ADR fixes the constraint; the lock file fixes the versions.**
- **Traps:**
  - **The safeguard replacing the staged upgrade is a deprecation sweep on 3.2 first** — checks under `-Wall`, clearing every `RemovedInDjango*Warning`. It is **not** equivalent to having tests, and saying so plainly is part of accepting this route. **Verification is a manual pass over every screen** — the largest accepted risk in the epic.
  - **April 2028 is a real deadline.** Django 6.x also drops Python 3.10/3.11 — irrelevant at 3.13, but noted so any future "pin Python back for package X" is recognised as closing the door on 6.2.

## ADR-026: Pin PostgreSQL 17 across every environment

- **2026-08-10 · Accepted**
- **Decision:** **PostgreSQL 17**, pinned identically everywhere — explicit `postgres:17` locally and 17 on Railway. Local and production **majors must match**; a bump is deliberate and restore-tested, never drift.
- **Rejected:** **`postgres:latest`** — turns a major bump into something that happens on a `docker pull`, against a production database that cannot follow. **Staying on 15/16** — no feature need, and it shortens the runway. **Leaving it unpinned** — makes the dump/restore drill untrustworthy, since `pg_dump` must match the server.
- **Traps:** The local compose file needs a Postgres service it lacks — and is broken as written anyway (`web` joins `my_network`; the file defines `bakery_simple`), so this is a fix, not new scope. The pilot's data must be restored from the home server's version into 17 during Epic 12 — **a cross-major restore**.

## ADR-027: Adopt the capabilities the upgrade unlocks

- **2026-08-11 · Accepted** — **amends [019](#adr-019-deletion-semantics-supplier-identity-administration-surfaces)'s uniqueness clause.** Release notes verified 2026-08-11.
- **Decision — adopt twelve, each with a task:** `LoginRequiredMiddleware` (5.1) as the default posture with `@login_not_required` on exceptions · `SECRET_KEY_FALLBACKS` (4.1) for rotation without invalidating sessions · **case-insensitive supplier uniqueness** via `UniqueConstraint(Lower("name"), "bakery", condition=…)` · constraint validation in the model/form layer via `full_clean()`/`validate_constraints()` with `violation_error_message` · `db_comment`/`db_table_comment` (4.2) · `db_default` (5.0) · `as_field_group()` (5.0) as Epic 5's default rendering · `{% querystring %}` (5.1) · **native psycopg pooling** (5.1) + `CONN_HEALTH_CHECKS` · PostgreSQL 17 `pg_stat_statements` as the p95 measurement basis · `COPY … ON_ERROR ignore` for the backfill · `pg_restore --transaction-size` for the restore drill. **Also required, not optional:** `STATICFILES_STORAGE`/`DEFAULT_FILE_STORAGE` were removed in 5.1, so the `STORAGES` dict is a **prerequisite of the upgrade itself**.
- **Rejected:** **Adopting nothing** — for the middleware, uniqueness, constraint validation and form rendering the hand-built version is strictly worse code that must then be maintained. **`GeneratedField` (5.0) for cost and margin** — the most attractive-looking option here, **rejected on a technical constraint, not preference:** PostgreSQL supports only `STORED` generated columns through 17, and the expression must be immutable and reference **only columns of the same row** — no joins, no subqueries — while every derivation here crosses rows. **Recorded explicitly so it is not re-proposed by the next person reading the 5.0 release notes.** **PG 17 incremental backup** — needs filesystem access to the data directory, which managed Railway does not offer; it does **not** close the PITR gap. **Redis cache backend (4.0)** — deliberately recorded as undecided rather than rejected *(ADR-028 then decided it)*. **Async views / async ORM (4.1)** — nothing in scope needs them. **`CompositePrimaryKey` (5.2) for the membership record** — theoretically the right shape, but it cannot be a ForeignKey target and has limited admin support.
- **Traps:** **Three of these change how downstream epics are built**, and they are only available **if Epic 19 lands first** — an independent argument for ADR-025's sequencing. **`STORAGES` is required by the upgrade, and the failure is quiet:** a removed setting is ignored, so the site keeps working while compression and cache-busting silently stop.

## ADR-028: Backend architecture

- **2026-08-13 · Accepted** — completes [020](#adr-020-three-per-tenant-roles-on-a-membership-record)/[027](#adr-027-adopt-the-capabilities-the-upgrade-unlocks) on auth, closes the caching question. Provider facts verified 2026-08-13.
- **Decision:** Six rows decided together because they are not independent — the service layer is where caching would attach, the permission mechanism determines whether that layer takes a user or a membership, and adopting Django's auth views is what makes email a first-release requirement.
  1. **Settings — `base.py` + `local.py` + `test.py`, no `production.py`.** `base.py` *is* production: all config from the environment, **no default at all** for `SECRET_KEY`/`ALLOWED_HOSTS`/`DEBUG`, so a missing variable raises `ImproperlyConfigured` at boot. Overlays opt *into* unsafe or convenient behaviour, so **the accident lands on the safe side** — the inverse of today, where a forgotten `DJANGO_SETTINGS_MODULE` yields hardcoded secrets and `DEBUG = True`.
  2. **Business logic — `control/services/`, plain functions, batch-first.** Explicit arguments, frozen dataclass returns carrying amount, canonical unit, provenance and as-of date together. **The batch entrypoint is the primary API**; single-object costing wraps it. Models lose costing entirely — the `@property` methods are **deleted, not left as delegators**.
  3. **API layer — none, no framework pre-selected.** Machine-readable endpoints are plain `JsonResponse` views. **Revisit trigger,** any of: a second non-first-party consumer; a native app or SPA committed to; or machine endpoints exceeding roughly six.
  4. **Auth — Django's auth views; capabilities as Django permission codenames.** `accounts/views.py` and `accounts/urls.py` deleted. Middleware resolves the active bakery and membership onto the request; a **custom authentication backend** implements `has_perm()` by mapping role → static capability set, so everything downstream stays stock Django.
  5. **Caching — none in the first release.** Query design is the lever. **Escalation ladder, in order,** only once the dashboard is measured over p95 < 2 s on realistic data: (a) fix the queries, (b) per-view cache with a short TTL keyed by a per-tenant version stamp, (c) Redis **only** if (b) needs cross-worker coherence. The batch API takes the version stamp from day one.
  6. **Email — Brevo over SMTP**, Django's built-in backend, credentials from env vars; console in `local.py`, locmem in `test.py`.
- **Rejected:** **Four settings modules including `production.py`** — makes `base.py` a module never loaded and therefore never tested. **A single env-driven `settings.py`** — test-only settings become `if` branches in the one file hardest to test. **Fat models, corrected in place** — the conventional answer, rejected on structure not taste: the dashboard costs every product in one request, and a per-instance `@property` recursing through nested recipes issues queries per node and cannot memoise across the walk, so meeting the budget means growing a second parallel batch path anyway; separately, provenance means the answer is a value object a `Decimal`-returning property cannot express. **An ORM-decoupled `domain/` package** — buys database portability nobody asked for. **DRF now, read-only** — a second authentication, permission and tenant-scoping surface to keep synchronised, for a consumer that does not exist. **Pre-selecting a framework for later** — ADR-025 had just shown that failure mode. **Name the trigger, not the tool.** **`django-rules`** — a good fit, rejected on proportion against three static roles. **A hand-rolled capability module** — templates lose `{% if perms %}`, Django admin keeps its own system regardless, and the result is two vocabularies for "is this allowed". **A thin `LoginView` subclass** — its one motivation is a multi-membership landing tenant, which doesn't exist yet. **Redis now** — the real cost is not ~$2–3/mo but that the invalidation matrix must be correct on day one across receipts, recipe edits, cascading base-recipe edits, VAT rows and price rows. **`LocMemCache`** — per-worker, so two users can be served figures cached at different moments: acceptable for a blog, not for the number a product is priced against. **Resend** — best DX of four evaluated, **rejected on a verified fact**: EU residency is Pro-only at $20–35/mo, over three times the entire infrastructure budget. **Mailjet** and **Scaleway TEM** — both viable; Brevo won on EU ownership *and* hosting aligning, a DPA by default, and the largest free headroom. **`django-anymail`** — worth it at volume, not under 100 emails a month.
- **Traps:**
  - **The password-logging `print()` in `accounts/views.py` is dead code, not a live leak** — `bakery/urls.py` never includes `accounts.urls`, so `user_login` is unreachable and even renders a template that does not exist. Recorded because "it never executed" is the fact worth having on file.
  - **Email is now a first-release blocker** — Django's auth views bring email-only password reset, so email gates the recovery path for every user.
  - **Two endpoints are carved out of the p95 < 500 ms budget** — invitation and password-reset POSTs send SMTP inline ([roadmap.md](roadmap.md) 10.18).
  - **A permission-cache watch item** — Django caches permissions on the user object, so it must be invalidated whenever the active tenant changes, or a two-membership user carries bakery A's capabilities into bakery B.

## ADR-029: Dependency management

- **2026-08-16 · Accepted** — **amends [025](#adr-025-runtime-baseline--django-52-lts-on-python-313)** on `Pillow`.
- **Decision:**
  1. **`uv`, in `pip compile` mode** — hand-edited `.in` → fully-pinned `.txt` in ordinary requirements format. Deliberately **not** `uv sync`/`pyproject.toml`: the requirements format is what the `Dockerfile`, Railway and every fallback host already consume, so this adds determinism **without changing the install path anywhere.** `uv` is build tooling at a **pinned** version, never an app dependency.
  2. **Three sources, three locks** — `base.in`, `dev.in` (`-r base.in` + tooling never in the image), `prod.in` (`-r base.in` + production-only). The root file is deleted. `prod.in` starts as nothing but `-r base.in`, deliberately: the value is **a named artifact the `Dockerfile` points at** that structurally cannot pick up dev tooling.
  3. **Determinism** — `--generate-hashes` at compile, `--require-hashes` at install, so a substituted artifact fails the build instead of shipping; `--python-version 3.13`; `dev`/`prod` compiled with `-c base.txt`.
  4. **The `.in` file *is* the register** — every line carries a comment naming its purpose and owning task, and **a dependency without one is removed at the next recompile rather than researched later.** Transitive deps exist only in the generated `.txt`, which is never hand-edited.
  5. **Refresh** on `.in` change, on a security advisory naming a pinned package, otherwise monthly, with ADR-025's "latest compatible" re-evaluated **each** time.
  6. **`Pillow` removed until Epic 13** — no `ImageField` and no import exists (verified 2026-08-16). Applying rule 4 to the package that prompted it is the point.
- **Rejected:** **`pip-tools`** — the closest call, with identical layout and near-identical output; lost on trajectory, since `uv` resolves an order of magnitude faster on per-second-billed build time and is where active development has moved. Migration back is one command line. **Poetry/PDM** — a project-layout migration bolted onto a framework upgrade with no test suite. **`pip freeze`** — pins with no record of what was asked for, so rule 4 is unenforceable; roughly the current state, which is how `environ==1.0` survived unnoticed. **Skipping hashes** — considered seriously, kept because pins alone don't deliver determinism against a mutated artifact.
- **Traps:** **CI needs a drift check**, or the generated files are only as current as the last person who remembered. **A monthly recompile is a standing chore with no owner but the solo developer** — named rather than pretended away. The rule extends **by hand** to vendored frontend assets, which `requirements/*.in` cannot see.

## ADR-030: Frontend

- **2026-08-16 · Accepted** — **rejects `tech_stack.md`'s own Vite candidate.** Decided against a frontend that was **measured**, not assumed (2026-08-16): 32 templates, 4,277 lines, **zero `{% extends %}`, zero `{% include %}`, zero `{% static %}`**, Bootstrap **5.0.0** vendored, **7 custom JS files all 0 bytes**, no Node tooling. **The interactivity layer is not thin, it is absent** — which is what moves this decision.
- **Decision:**
  1. **Shared `base.html` plus `{% include %}` partials.** No competing option was in play; the measurement is the argument. `django-template-partials` **not** adopted — a dependency for ~4 fragments.
  2. **Stay on Bootstrap, 5.0.0 → 5.3.x.** Same major, so classes stay largely valid: an upgrade, not a restyle.
  3. **No asset pipeline — this rejects Vite.** Instead: consolidate the CSS, native custom properties and nesting, whitenoise for hashing. **Revisit** past a few hundred lines of custom JS, or SCSS-variable-level Bootstrap customization.
  4. **HTMX**, vendored at a pinned version, plus small vanilla modules — one ~14KB script, no bundler, server returns HTML fragments. Built as **progressive enhancement**: every form and link must work with JavaScript disabled, which Level A requires anyway.
  5. **No SPA** — a ratification; the API-layer and device-matrix decisions had already foreclosed it.
  6. **`djlint`** for templates — a pip package, so no Node in dev either.
- **Rejected:** **Vite** — it would add Node, a second lockfile and CI steps **to bundle zero bytes of JavaScript** while duplicating what whitenoise already provides; the right tool for a frontend this project does not have, reversible in a day if the trigger fires. **`django-compressor`/libsass** — adds a compile step overlapping whitenoise's job, and libsass lags dart-sass. **Tailwind** — rewrites markup in all 32 templates and forces Node back in regardless. **Hand-written modern CSS, no framework** — hands a solo developer ownership of responsive tables, form styling, modals and the whole accessibility surface, against a WCAG target. **Vanilla JS only** — hand-writing fetch, DOM swapping, URL/history sync and error handling for exactly the patterns search and pagination need.
- **Traps:** **Switching to `{% static %}` stops being tidying and becomes load-bearing** — whitenoise is now the *only* cache-busting mechanism and does nothing for 23 hardcoded templates; done partially, the site silently serves stale CSS. **Bootstrap ships un-tree-shaken** (~230KB minified, compressed and cached) — accepted explicitly against the p95 budget. **Vendored assets need the ADR-029 treatment**, or the repo repeats what this ADR found: a four-year-old library nobody noticed.

## ADR-031: Operations

- **2026-08-18 · Accepted.** Two facts set the bar: **there is no test suite at all**, so any coverage gate is a target to reach rather than a floor to hold; and **backups are literally "unknown/undocumented"** — the risk is not a slow restore but an unrecoverable one, over data ADR-017 gives a **legal** retention floor.
- **Decision:**
  1. **CI merge gate** — extend the Epic 1 workflow with the test suite, `ruff` + `djlint`, the existing check/migrations/`collectstatic`/`docker build` steps, and `pip-audit` against the hashed lock. Dependabot raises dependency PRs through the same gate. Coverage is **70% repo-wide**, one number.
  2. **No SAST or container scanning this release.** **Revisit:** repo goes public, first non-pilot tenant, or payment data.
  3. **Deploys — Railway git-watch on `production`, `migrate` as the pre-deploy command.** The hook is what makes git-watch sufficient: migrations complete **before** the new version takes traffic, satisfying ADR-015 rule 4 without a release script or a Railway token in GitHub secrets. The deploy gate is therefore **branch protection**, leaving no place for CI and the platform to disagree about what is live.
  4. **Sentry SaaS, free tier, EU region** (`de.sentry.io`) — **irreversible after creation.** `send_default_pii` stays **off** and a `before_send` scrubber is part of the decision, not tuning.
  5. **UptimeRobot free tier**, 5-minute HTTPS **keyword** check against the health endpoint — keyword rather than HTTP 200, so an endpoint reporting a failed database check fails the monitor instead of passing it. Hosted away from Railway deliberately: **a monitor that shares fate with what it monitors is decorative.**
  6. **Backups — two unequal tracks, no PITR.** *Fast rollback:* Railway's native schedules, enabled explicitly since they are **off by default**; same-host only. *The real backup:* a nightly GitHub Actions `pg_dump -Fc --no-owner --no-privileges`, encrypted **client-side with `age`** before leaving CI, into an R2 bucket **separate from media**, on a **7 daily / 4 weekly / 12 monthly** lifecycle — outside Railway on purpose, because **an escape hatch that depends on the platform it escapes is not one.** *Proof:* a weekly drill that decrypts, restores into a throwaway PG 17, verifies and alerts on failure. *PITR rejected*, accepting **RPO up to 24 hours**.
- **Rejected:** **Coverage scoped to `control/services/` at 90%, or a ratchet** — better aimed, but one repo-wide number is what a solo developer keeps honest and scoping invites arguing which module counts. **80%+** — against zero tests, **a gate that cannot be met is a gate that gets disabled.** **CodeQL/Trivy** — the realistic threat is a known CVE in a dependency, which `pip-audit` and Dependabot cover, not a novel taint-flow bug in ~2,000 lines of views. **GitHub Actions owning the deploy via the Railway CLI** — buys ordering the pre-deploy hook already provides, in exchange for a long-lived token in secrets. **Manual deploy approval** — right once there are tenants who didn't agree to be pilots; today its only reviewer wrote the change. **GlitchTip self-hosted** — attractive on EU ownership, but needs a container **and its own PostgreSQL**, roughly doubling the bill; same SDK, so switching stays a configuration change. **Logs plus `AdminEmailHandler`** — no grouping, so one bad loop floods the inbox exactly when signal matters. **Better Stack / Sentry uptime** — using Sentry would let one outage take the alerting with it. **The dump job as a Railway cron** — the stronger *security* answer, rejected narrowly on portability and mitigated by backup-scoped rotatable credentials; worth reopening if the public-proxy exposure proves uncomfortable, since the job body is identical. **Snapshots plus manual pre-release dumps** — fails rule 5, and "manual, when I remember" is what the drill exists to eliminate. **PITR via `pgBackRest`/`wal-g`** — a self-managed component with its own failure modes, protecting a megabyte-scale dataset re-enterable from paper. **R2 server-side encryption or SSE-C** — SSE leaves Cloudflare holding usable keys; SSE-C must be passed correctly on every dump *and* restore, with no recovery if it drifts. **Client-side `age` gives the strongest statement — the processor stores ciphertext — for one extra command.**
- **Traps:** **70% from zero is the largest piece of work this ADR creates**, and it gates every merge once on, so it is turned on **at the end of Epic 6** — enabling it first blocks the PRs that write the tests. **Key custody becomes an operational responsibility with no software fallback** — the `age` private key lives outside CI; lose it and every backup is unrecoverable. **CI now needs database credentials**, which the repo has never held — backup-scoped, reaching Postgres over the public TCP proxy: an exposure that did not exist before and the accepted cost of clause 6's independence. **Alerting arrives after the thing it protects** — Sentry and UptimeRobot are Epic 7, which depends on Epic 12, so until then the pilot runs unmonitored. **The RPO is a stated product position, not an oversight** — up to 24 hours of receipts and price rows can be lost, and the pilot bakery must have seen it.

## ADR-032: One shared `RecipeLine`, and categories as a lookup table

- **2026-08-26 · Accepted**
- **Decision:**
  1. **One `RecipeLine` replaces both line tables** — typed parent (`parent_product` **XOR** `parent_base_recipe`), typed component (`component_material` **XOR** `component_recipe`), each pair enforced by a database `CHECK` constraint, plus `quantity` and a `unit` FK.
  2. **`Product` and `Base_recipes` stay separate** — this collapses the *lines*, not the recipes.
  3. **One tenant-scoped `Category` table** with a `kind` discriminator (`material`/`product`), an `archived` flag, and uniqueness on `(bakery, kind, name)` — one table, not two, since the kinds differ only in which model points at them.
  4. **Categories are tenant-editable; units are not.** A `Category` carries no arithmetic; a `Unit` carries a conversion factor, so editing one silently rewrites every cost derived from it.
- **Rejected:** **Two tables behind an abstract base** — the costing service still branches on type, and every later line-level feature gets built and tested twice. **Merging `Product` and `Base_recipes`** — consistent with ADR-022, and this decision makes that migration *cheaper* later. **`TextChoices` for categories** — a migration and deploy every time a bakery names a category, and every tenant sharing one vocabulary. **Two category tables** — duplicated CRUD, admin, settings UI and tests for tables differing by one column.
- **Traps:** **The `CHECK` constraints are the decision** — a nullable-FK pair with no constraint is a *worse* schema than two tables, because it permits a line with two parents or none. Both are database constraints in the same migration as the model, **not** `clean()`, which does not run on `bulk_create` — exactly how an import writes these rows. **The migration is a merge, not a rename.** **`kind` must be validated against the referencing model**, or a product can be filed under a flour category — the FK cannot express that.

## ADR-033: Traceability entities

- **2026-08-26 · Accepted.** The last decision Epic 3 was waiting on — these touch tables Epic 3 is about to restructure, so deciding them afterwards means restructuring twice.
- **Decision:**
  1. **Goods receipts are a header with lines** — `GoodsReceipt` (supplier, receipt date, document reference) → `GoodsReceiptLine` (material, supplier lot, quantity, unit, best-before, price in ADR-018's shape). A delivery note is one record with many lines, which makes "show me that delivery" a lookup rather than a group-by.
  2. **Production runs consume specific receipt lines and emit a batch** — `ProductionRun` → `Consumption` (FK to a line, quantity consumed in canonical units) → output `Batch` carrying the internal lot code, with `OutboundRecord` hanging off `Batch`.
  3. **Lot codes are `YYYYMMDD-NNN`**, resetting daily, unique per `(bakery, lot_code)`, allocated **server-side inside the batch-creating transaction** — never client-side, never by counting rows.
  4. **Quantity-on-hand is derivable but not surfaced** — `Σ received − Σ consumed` is computable, never stored, and **not displayed anywhere this round**.
- **Rejected:** **Flat receipt lines carrying supplier and date per row** — loses the delivery note as a document, which is the unit an FSAI inspector and a supplier query both work in. **Receipts first, production runs later** — receipts alone give one step *back* and nothing forward, while presenting a "Traceability" section to a real food business operator. **An opaque sequence (`B-000123`)** — a lot code's job is to be read off a label, quoted on a phone call and sorted on paper; the date earns its place. **User-entered lot codes** — a format the app cannot guarantee is a format the trace query cannot rely on; revisit if the pilot has an established scheme. **A full stock ledger** — a different product promise with accuracy expectations this app cannot meet. **Showing the derived figure read-only** — the closest call: a number on screen is trusted regardless of its caveat, and "received minus consumed" ignores waste, spillage and unrecorded use, so **it would be wrong in normal operation, not in an edge case.**
- **Traps:** **`Consumption.quantity_consumed` is load-bearing beyond traceability** — the single field keeping stock derivable later without a schema change. **Lot-code allocation needs a concurrency-safe implementation, not a helper function** — the unique constraint is the backstop, transactional allocation the mechanism, gaps after rollback acceptable. **Receipt lines are append-only**, the first tables where soft delete is not enough. **The pilot will ask for stock** — the answer is deliberate and should be given as one: the data is being recorded, the feature is not being claimed until it can be trusted.

## ADR-034: `ruff` for lint and format; `pytest-django` as the runner

- **2026-08-26 · Accepted**
- **Decision:** **`ruff` does both** (`check` and `format`) — no `black`, no `isort`, no `flake8`. **`pytest` + `pytest-django` + `pytest-cov`** replace `manage.py test`. **Tool config in a `pyproject.toml` holding only `[tool.*]` sections** — not a packaging file, declares no dependencies, and **must never grow a `[project]` or `[build-system]` table.**
- **Rejected:** **Django's own runner with `coverage.py`** — genuinely close, and consistent with rejecting DRF and Vite; it lost on the shape of *this* suite, where costing tests are table-driven across unit conversions × VAT boundaries × rounding × recursion depth and the isolation tests want composable fixtures. **`ruff` plus `black`** — `ruff format` is a deliberate reimplementation of black's style. **`mypy`** — out of scope for a codebase with no annotations; revisit when the service layer exists, since typed `Decimal` boundaries are where it would pay.
- **Traps:** **The documented test command changes in three places** — `CLAUDE.md`, the README and CI; the stale one is always the one someone follows. `pytest-django` wraps rather than replaces Django's test-database machinery, which is why the choice carries little lock-in.

## ADR-035: Tenant full data export format

- **2026-08-26 · Accepted**
- **Decision:** A **ZIP of one CSV per tenant-scoped table plus a `manifest.json`** carrying the export timestamp, a schema version, and per table its columns, types, primary key and FK map — so relationships survive a format that cannot express them. Generated by a **single service function**, exposed twice: an Owner-only settings download and a management command.
- **Rejected:** **Portable ANSI SQL** — ADR-008's first-named option; hand-generating correct portable DDL means maintaining a type map and quoting rules against every future model change, and the output serves only a developer, whereas the CSV bundle serves **both** audiences ADR-008 named. **`dumpdata` JSON** — nearly free, but a *Django serialization* format, precisely the dependency ADR-008 set out to avoid. **A tenant-scoped `pg_dump`** — already rejected by ADR-008.
- **Traps:** **The manifest is the deliverable, not the CSVs** — CSV loses types, nulls-versus-empty-strings and every relationship. **Synchronous download is adequate and should be re-checked, not assumed.** **Every export is a bulk disclosure of one tenant's business data**, so gating and audit logging are part of the feature. **Decimal fidelity in CSV is a real trap** — full stored precision, never 2-dp presentation rounding: **an export that rounds is an export that silently loses data.**

## ADR-036: AI insights on Databricks Serverless, and gunicorn stands

- **2026-08-26 · Accepted** — moves [002](#adr-002-ai-insights-service-on-apache-spark--databricks) `Proposed` → `Accepted` and amends its delivery shape. Closed the last two open stack questions, and with them all of Epic 9.
- **Decision:**
  1. **Spark on Databricks is confirmed** — ADR-002's engine choice stands.
  2. **Serverless Jobs on AWS, EU (Ireland) `eu-west-1`** — job compute only. This is what makes per-use billing real: there is no machine to start, idle, or forget to stop.
  3. **Django hands over an extract; Databricks never touches PostgreSQL** — a nightly job writes a **personal-data-free** costing extract (product, date, cost, price, margin, tenant) to a dedicated R2 prefix.
  4. **Nightly schedule, results POSTed back** to a plain `JsonResponse` callback authenticated with a shared secret. No event triggering.
  5. **Hard cost ceiling ~$15/mo**, spend alert before the first production run.
  6. **gunicorn, WSGI, sync workers.** **Revisit trigger, and only this one:** the insights dashboard needing **push** updates rather than polling.
- **Rejected:** **A scheduled query inside Django** (ADR-024's null hypothesis) — **not adopted, but not wrong.** It would have been cheaper and added no processor, and it remains the correct answer if the scope never grows past margin alerts; keeping Spark is a deliberate bet on headroom, made with the consequences stated rather than discovered. **Databricks reading Railway PostgreSQL directly** (ADR-002's literal shape) — exposes the production database to a third-party network and drags supplier contacts and user accounts into GDPR transfer scope, where the R2 handoff costs one nightly job and removes both problems. **Passing data in the Jobs API payload** — no persistence means no history, and trend analysis is most of the point. **Event-triggered runs** — the objection is debounce, retry and deduplication logic in the app, not latency: **a margin alert is a daily concern — a price change at 14:03 does not need a 14:04 alert.** **An all-purpose cluster** — the shape that generates surprise bills. **ASGI now** — the service layer is sync throughout, so an async view would raise `SynchronousOnlyOperation` against the ORM, imposing that constraint from day one for a `Could` feature.
- **Traps:** **The first recurring cost increase since ADR-013** — ~$6 → ~$21/mo at the ceiling, a 3.5× rise against zero revenue, so a real run must be measured before production spend. **The DBU rate is not recorded here on purpose** — serverless pricing is region- and tier-dependent and changes; **an unverified number in an append-only log is worse than no number.** **Two new processors** (Databricks Inc., AWS), both needing DPAs before real data flows; both sit in the EEA and the extract carries no personal data, so **Databricks being US-headquartered is a subprocessor/DPA question, not a data-location one** — stated so it isn't re-litigated. **The extract schema is a published contract** — job and notebook evolve in different repositories, so the manifest carries a version and the notebook rejects an unknown one. **A silent job failure is the real operational risk** — insights that stop arriving look identical to "no alerts this week". **The callback is the app's only unauthenticated-by-session, internet-facing write path.**

## ADR-037: &lt;next decision goes here&gt;

- **Date / Status:**
- **Decision:**
- **Rejected:**
- **Traps:**
