# Architecture & Product Decisions

This is an append-only decision log (lightweight ADRs). Every time a real choice gets made about
stack, architecture, data model, process, or scope — write it down here instead of only in chat.
Never delete an entry: if a decision changes later, add a new entry and mark the old one
**Superseded by ADR-00X**.

## How to add a decision

Copy this block, give it the next sequential number, and fill it in:

```
## ADR-00X: <short title>

- **Date:** YYYY-MM-DD
- **Status:** Proposed | Accepted | Superseded by ADR-00Y
- **Context:** What problem/question forced this decision?
- **Decision:** What was actually decided.
- **Alternatives considered:** What else was on the table, and why it lost.
- **Consequences:** What this makes easier, harder, or forecloses. Follow-up work it creates.
```

Keep entries short — a paragraph or two per section is usually enough. Link related entries and
other docs with normal markdown links (e.g. `[tech stack](tech_stack.md)`).

---

## ADR-001: Branching strategy for the redesign

- **Date:** 2026-07-16
- **Status:** Proposed
- **Context:** The app has real production usage history and is being modernized in phases
  (see `PRODUCTION_UPDATE_PLAN.md`) while requirements/stack/GDPR scope are still being decided
  (see [project_requirements.md](project_requirements.md), [tech_stack.md](tech_stack.md),
  [gdpr.md](gdpr.md)). We need a branch model that lets each phase ship independently without
  one giant long-running rewrite branch going stale.
- **Decision (proposed):**
  - `main` stays deployable at all times; it's what's actually running in production.
  - One feature/phase branch per plan — e.g. `phase-1-repo-cleanup`, `phase-2-security-hardening`,
    `gdpr-data-inventory`, `feature-supplier-price-comparison`. Branch names map 1:1 to a
    plan discussed with Claude in Plan Mode before implementation starts.
  - Each phase branch is opened as a PR against `main` as soon as it exists (draft PR is fine),
    reviewed, and merged before the next phase branch is started from an updated `main` —
    avoid stacking unmerged phase branches on top of each other.
  - No direct commits to `main`; no force-push to `main`.
  - Squash-merge per PR so `main` history reads as one entry per phase/feature.
  - Tag `main` at the end of each phase (e.g. `v0-phase1`) so there's a rollback point.
- **Alternatives considered:** Single long-lived `redesign` branch merged once at the end —
  rejected, too high risk/merge-conflict blast radius for a prototype-to-production rewrite.
  Trunk-based development with feature flags — reconsider later once CI/CD exists (Phase 6/7
  of the update plan); too heavyweight to introduce before basic tests/CI exist.
- **Consequences:** Requires GitHub branch protection on `main` (require PR + review) once
  more than one person touches the repo. Each plan/session should state which phase branch it
  targets before writing code.

---

## ADR-002: AI insights/batch analytics service built on Apache Spark + Databricks

- **Date:** 2026-07-16
- **Status:** Proposed
- **Context:** New requirement to surface AI-derived operational insights — e.g. alerts when a
  product's margin drops below expectation, a real-time analytics dashboard — computed from app
  events and the existing PostgreSQL data. This is being scoped as a new external service, not
  built into the Django app.
- **Decision:** The new service is a separate batch-processing component built on Apache Spark,
  run on Databricks, invoked via API when specific app events fire (e.g. a price/margin change),
  reading from the app's database and returning computed results back to the app.
- **Alternatives considered:** Not yet evaluated in this log — see the open cost/scale question
  below before treating this as final. A plain-Python batch job (pandas/DuckDB) or a small
  scheduled task was not compared against Spark/Databricks for a dataset this size (single
  bakery's raw materials/products/recipes).
- **Consequences:** Databricks is a managed service that runs on its own cloud infrastructure
  (AWS/Azure/GCP) independent of wherever the Django app/Postgres end up hosted — "same host" as
  the app isn't realistic, "connected via API" is. Databricks Community Edition (free) does not
  support the API-triggered job workflow described here (notebook-only, no job-scheduling API),
  so a paid workspace is likely required, billed separately from app hosting. **Open follow-up:**
  confirm Spark/Databricks is still the right choice once real data volume and budget are clearer
  — see [tech_stack.md](tech_stack.md) "AI insights / batch analytics service" section.

## ADR-003: Narrow hosting candidates to Railway, Render, and DigitalOcean App Platform

- **Date:** 2026-07-21
- **Status:** Accepted
- **Context:** The broader hosting survey in [tech_stack.md](tech_stack.md) "Hosting candidates"
  compared eight options (Railway, Render, DigitalOcean App Platform, Fly.io, Sevalla, Koyeb,
  Hetzner+Coolify, Oracle Cloud "Always Free"). That's too wide a set to finish deciding on; a
  shortlist is needed to actually pick one.
- **Decision:** Only Railway, Render, and DigitalOcean App Platform remain active candidates. The
  final pick among these three is still open — this ADR narrows the field, it doesn't choose.
- **Alternatives considered:** Fly.io, Sevalla, Koyeb, Hetzner+Coolify (self-managed), and Oracle
  Cloud's Always Free VM were all evaluated (see the full comparison retained in
  [tech_stack.md](tech_stack.md) for reference) but are set aside for now — Oracle in particular
  was the front-runner on pure cost before this narrowing, but the self-managed operational model
  (own reverse proxy/TLS, own firewall config, no native GitHub deploy) was traded for the
  simplicity of a fully managed PaaS.
- **Consequences:** Deployment tooling, static/media storage, and CI/CD design should target
  "works on any of these three" rather than being tuned to one host's quirks — see ADR-004 for how
  that shapes the Docker-vs-buildpack decision.

## ADR-004: Deploy via the existing custom Dockerfile, not each platform's native buildpack

- **Date:** 2026-07-21
- **Status:** Proposed
- **Context:** Railway, Render, and DigitalOcean App Platform (ADR-003) each support two build
  paths: a custom `Dockerfile` (already present in this repo) or the platform's own native
  buildpack (Railway: Railpack, replacing Nixpacks; Render: Cloud Native Buildpacks; DigitalOcean:
  the Heroku-derived Python buildpack). Since the host isn't picked yet, the build strategy needs
  to work identically across all three candidates.
- **Decision:** Keep and harden the existing `Dockerfile` as the deployment artifact on whichever
  host is chosen, rather than relying on that platform's native buildpack.
- **Alternatives considered:** Native buildpacks on each platform — rejected as the default because
  (a) each platform's buildpack makes its own decisions about base image, Python patch version, and
  build steps, so the app would need separate verification per host and could subtly behave
  differently across them; (b) all three platforms explicitly prioritize a root-level `Dockerfile`
  over their buildpack when one is present, so there's no loss of feature support by using it; (c)
  buildpacks are recommended by these platforms' own docs mainly for simple apps with no unusual
  system dependencies — reasonable today, but this app's update plan (Phase 1/3) will add system-
  level dependencies (e.g. a PostgreSQL driver, image processing for uploads) where Docker's
  explicit control is worth the small upfront cost.
- **Consequences:** One Dockerfile is the single source of truth for the runtime across dev,
  Docker Compose, and all three hosting candidates — reducing "works on my machine" drift. Requires
  keeping the Dockerfile itself well-maintained (multi-stage build, slim final image) rather than
  outsourcing that to a buildpack. See `PRODUCTION_UPDATE_PLAN.md` Phase 7 for the concrete
  Dockerfile hardening tasks.

## ADR-005: Store user-uploaded media (product photos, profile pictures) in S3-compatible object storage

- **Date:** 2026-07-21
- **Status:** Proposed
- **Context:** The redesign adds two user-upload features — product photos and user profile
  pictures (see [project_requirements.md](project_requirements.md) feature backlog and
  [gdpr.md](gdpr.md), since profile pictures are personal data). None of the three hosting
  candidates (ADR-003) guarantee persistent, shared local disk across redeploys or multiple
  instances, so local `MEDIA_ROOT` storage isn't viable in production.
- **Decision:** Store uploaded media in S3-compatible object storage via `django-storages`,
  decoupled from wherever the app is hosted. Cloudflare R2 is the leading candidate — zero egress
  fees, a 10GB/1M-write/10M-read free tier, and provider-agnostic (storage doesn't have to move if
  the app host changes later). Oracle Object Storage was also considered (Always-Free 10GB) but is
  a weaker fit now that Oracle is no longer a hosting candidate (ADR-003) — it would add a fourth
  provider relationship for no clear benefit.
- **Alternatives considered:** Local disk on the app host — rejected, not durable/shared across
  redeploys or instances on any of the three candidates. AWS S3 — rejected as default due to
  standard egress fees and a free tier that expires after 12 months. DigitalOcean Spaces — a
  reasonable fallback specifically if DigitalOcean is chosen as the compute host (same-provider
  billing), but R2's zero-egress and provider-agnostic properties make it the better default
  regardless of which of the three compute hosts wins.
- **Consequences:** Adds `django-storages[s3]` + `boto3` as dependencies (tracked in
  `PRODUCTION_UPDATE_PLAN.md`). Requires the bucket's access keys to be handled as secrets (Phase 2
  hardening — never hardcoded). Requires a new GDPR entry for the storage provider as a third-party
  processor once a bucket is provisioned (see [gdpr.md](gdpr.md) §7).

## ADR-006: Multi-tenant SaaS architecture confirmed

- **Date:** 2026-07-21
- **Status:** Accepted
- **Context:** [project_requirements.md](project_requirements.md) and [gdpr.md](gdpr.md) both carried
  an open question on whether Bakery supports a single bakery or many (multi-tenant SaaS). This was
  blocking the Phase 3 schema redesign, since it determines whether every business model needs a
  tenant scope from the start.
- **Decision:** Bakery is a multi-tenant SaaS product. Each bakery is a tenant; the product serves
  multiple bakeries' data concurrently, not one bakery per deployment.
- **Alternatives considered:** Single-tenant (one deployment per bakery) — rejected; doesn't match
  the direction discussed (a shared database across tenants, with per-tenant data export as a
  product differentiator — see ADR-008/ADR-009).
- **Consequences:** Every business model (`Supplier`, `RawMaterial`, `Base_recipes`,
  `Bs_Ingredients`, `Product`, `Recipe_Ingredients`, and the future `Profile` model) needs an
  explicit tenant scope (a `Bakery` FK) — now a required part of the Phase 3 schema redesign, not
  optional. Changes the GDPR data-controller model: Bakery-the-product likely acts as a data
  **Processor**, with each bakery tenant as the data **Controller** for its own staff/supplier data
  — see the `gdpr.md` update below. User roles (admin/manager/staff/auditor, per
  `PRODUCTION_UPDATE_PLAN.md` Phase 2) are now scoped per-tenant, not global.

## ADR-007: Database topology — app and database always run as separate services

- **Date:** 2026-07-21
- **Status:** Accepted
- **Context:** Confirming whether any point in the Phase 3 redesign or the eventual hosting
  migration ([tech_stack.md](tech_stack.md) "Hosting candidates") should combine the Django app and
  PostgreSQL into a single deployable unit/image, or keep them permanently separate.
- **Decision:** Database and application always run as separate containers/services — never
  bundled into one image. This matches current self-hosted practice (Postgres already runs in its
  own container) and how all three hosting candidates from ADR-003 offer Postgres — as a distinct
  managed add-on, not something a single app image can encapsulate.
- **Alternatives considered:** Bundling Postgres into the app image for simplicity — rejected: it
  breaks independent backups/PITR, breaks the "app container is stateless and disposable" property
  the Dockerfile strategy (ADR-004) depends on, and isn't actually offered as an option by any of
  the three hosting candidates.
- **Consequences:** No implementation change required — this formalizes existing practice so it
  isn't re-litigated later. Reinforces that `docker-compose.yaml` and the Phase 7 hosting migration
  work should keep DB and app as distinct services/connection strings.

## ADR-008: Shared multi-tenant database (not database-per-tenant), with a tenant-scoped full data export capability

- **Date:** 2026-07-21
- **Status:** Accepted
- **Context:** Given ADR-006 (multi-tenant), the Phase 3 schema redesign needs to choose between one
  shared PostgreSQL database with tenant-scoped rows vs. a separate database per bakery. Separately,
  if a bakery stops using the app, can they get a full export of their data in a format usable
  outside this app — raised as a potential product differentiator, not just a compliance question.
- **Decision:**
  - Use a single shared database with row-level tenant isolation: add a `Bakery` model and a tenant
    FK on every tenant-scoped table (`Supplier`, `RawMaterial`, `Base_recipes`, `Bs_Ingredients`,
    `Product`, `Recipe_Ingredients`, and the future `Profile` model). Enforce tenant scoping at the
    query layer (a service-layer/manager convention that always filters by the current tenant), not
    at the database-instance level.
  - Build a tenant-scoped **full data export** as an explicit Phase 3 deliverable: given a tenant,
    produce a complete export of that tenant's rows across all tenant-scoped tables, in a format
    that doesn't depend on this app's exact Postgres schema/version to reload — i.e. portable SQL
    (plain ANSI-compatible `CREATE TABLE`/`INSERT` statements, not a Postgres-specific `pg_dump`
    custom-format file) or an equivalent structured bundle (one CSV per table plus a manifest
    describing relationships), so a departing tenant can import it into a different DBMS or
    spreadsheet tooling of their choice.
- **Alternatives considered:**
  - Database-per-tenant — rejected primarily on cost: each of the three hosting candidates
    (ADR-003) prices managed Postgres per instance (~$5-20+/mo each), so N bakeries means N database
    bills — impractical at this app's scale. It would make "hand the tenant their DB" trivial, but
    that convenience doesn't offset the operational/cost overhead of running N separately-migrated
    databases for a small dataset.
  - Handing over a raw `pg_dump` of a tenant's rows — rejected as the default: even scoped to one
    tenant, a native Postgres dump format assumes the recipient runs a compatible Postgres version;
    a portable SQL/CSV bundle is usable far more broadly and doesn't lock the export to this app's
    specific DB engine.
- **Consequences:** Requires a `Bakery` tenant model and FK migrations across nearly every table in
  Phase 3 — a bigger schema change than originally scoped, since every existing model changes.
  Requires new tooling (a management command or service) to generate the portable per-tenant
  export — real, non-trivial engineering work, tracked as its own feature rather than a byproduct of
  the schema redesign. Query-layer tenant scoping becomes a correctness-critical convention across
  all of Phase 4's service-layer work (a missed filter is a cross-tenant data leak) — worth strong,
  dedicated test coverage in Phase 6 specifically for tenant isolation.

## ADR-009: Add a dedicated GDPR personal-data export alongside existing CSV exports

- **Date:** 2026-07-21
- **Status:** Accepted
- **Context:** `gdpr.md`'s data inventory flags that the current CSV export is a bulk admin export
  (whole tables), not scoped to a specific data subject, and doesn't satisfy Article 20 portability
  on its own — researched separately: CSV as a *format* is fine under GDPR, but *scope* (whole
  tables vs. one subject's data) is the actual gap.
- **Decision:** Keep the existing per-entity bulk CSV exports as-is — they remain an admin/
  operational feature, not a compliance mechanism. Add a second, separate export: a dedicated GDPR
  personal-data export, produced as its own CSV (or small CSV bundle) scoped to one data subject at
  a time, containing only that subject's personal data across models (e.g. their user account
  fields, profile picture reference, any supplier-contact rows where they're the named contact).
  This is what satisfies a "give me my data" / portability request, and is distinct from both the
  bulk admin export and the tenant-wide full-data export from ADR-008.
- **Alternatives considered:** Retrofitting the existing bulk export with a subject filter —
  rejected; the two export shapes are different enough (all business data for a whole bakery vs.
  one person's personal data across the schema) that conflating them risks either over-exposing
  business data in a personal-data request or under-scoping a real admin export.
- **Consequences:** Adds a new export view/service, gated to the requesting user's own data (or an
  admin acting on a data subject's behalf), tracked as a Phase 3/GDPR discovery deliverable. Should
  be cross-referenced from `gdpr.md` §3 (Portability) as the concrete fix for that row's "Open"
  status.

## ADR-010: <next decision goes here>

- **Date:**
- **Status:** Proposed
- **Context:**
- **Decision:**
- **Alternatives considered:**
- **Consequences:**
