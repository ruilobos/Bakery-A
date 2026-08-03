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
- **Status:** Superseded by ADR-010 (`main` no longer mirrors production; a separate `production` branch does)
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
- **Status:** Accepted — the final pick among the three is closed by ADR-013 (Railway)
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
- **Status:** Accepted
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
- **Status:** Accepted
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

## ADR-010: Revise branch/environment strategy — `main` as dev/test integration, `production` as the deploy branch, with tagged releases (supersedes ADR-001)

- **Date:** 2026-07-21
- **Status:** Accepted — the persistent-staging-environment clause is amended by ADR-014 (the dev/test
  environment is local Docker Compose, not a hosted staging environment). The branch model itself
  (`main` integration → `production` deploy, tagged releases, branch protection) is unchanged.
- **Context:** ADR-001 assumed `main` mirrors what's live in production. Revisiting before CI/CD
  (Phase 6/7) is built: a dedicated pre-production integration/testing branch, an explicit
  promotion step to production, and named release points for rollback are wanted — and the model
  needs to work with whichever of Railway/Render/DigitalOcean (ADR-003) is eventually chosen. Each
  candidate's dev/staging/preview support was checked 2026-07-21 — see
  [tech_stack.md](tech_stack.md) "Dev/staging/preview environment support" — and all three can run
  the model below regardless of which is finally picked.
- **Decision:**
  - `main` becomes the **integration/dev-test branch**, not what real users hit. Phase/feature
    branches (naming unchanged from ADR-001 — `phase-N-slug`, `feature-slug`, `gdpr-slug`,
    `stack-slug`) branch off `main` and merge back via PR.
  - Every merge to `main` auto-deploys to a persistent staging/dev environment on the chosen
    platform (a second Railway environment / Render service / DigitalOcean App tracking `main`).
  - A new `production` branch holds what's actually live. Promotion is a deliberate, separate
    step: open a PR from `main` → `production` once the staged build is validated; merging it
    triggers the platform's production deployment.
  - Every merge to `production` is tagged with a semantic version (e.g. `v0.3.0`) and published as
    a GitHub Release (auto-generated notes from PR titles) — a named, referenceable rollback
    point.
  - Both `main` and `production` are protected: no direct pushes, no force-pushes, changes only
    via PR. Required-status-check enforcement is added once Phase 6 stands up real CI (nothing to
    check against yet). `production` gets a required-approval rule once more than one person
    touches the repo (0 required approvals for now, since this is currently a solo project — raise
    it later).
- **Alternatives considered:** Keeping `main` as the deployed branch (original ADR-001) —
  rejected, no safe integration point to validate changes before real users see them. Full
  GitFlow (`develop` + `main` + release + hotfix branches) — rejected as more ceremony than this
  project needs; two branches (`main` for integration, `production` for deploy) gets the same
  safety with less overhead. Mandatory per-PR ephemeral previews as a third tier — not required
  yet given cost/complexity (Render gates it behind a paid tier); left as an optional per-host
  enhancement, most naturally available on Railway.
- **Consequences:** Requires a second environment/app resource on whichever host is picked — a
  real cost factor to weigh in the final hosting pick. Requires creating the `production` branch
  and configuring branch protection on both `main` and `production` in GitHub.
  `docs/roadmap.md` branch naming is unaffected; only the destination of the final promotion step
  changes.

## ADR-011: Move a minimal CI check into Phase 1; Phase 6 becomes the full CI/CD build-out

- **Date:** 2026-07-21
- **Status:** Accepted
- **Context:** Branch protection on `main`/`production` (ADR-010) now requires every change to go
  through a PR, but the original plan put all CI/CD in Phase 6 — meaning five phases of PRs would
  merge on manual review alone, with zero automated verification, before any pipeline exists. Full
  CI/CD (comprehensive tests, coverage gates, security scanning, deploy automation) can't fully
  move earlier: it depends on a test suite that doesn't exist until Phase 6 writes it, and on a
  hosting platform that hasn't been picked yet (see [tech_stack.md](tech_stack.md) "Hosting
  candidates").
- **Decision:** Split "CI/CD" into two touchpoints instead of one phase. A minimal CI pipeline
  moves into Phase 1 — `python manage.py check`, a migrations-check, a Docker build validation,
  and a basic lint pass, running on every PR against `main`/`production` via GitHub Actions.
  Phase 6 keeps the full pipeline (real test suite, complete formatting/lint enforcement, security
  scanning) and extends the Phase 1 workflow rather than replacing it; the deploy-automation half
  of CI/CD (auto-deploy to staging/production per ADR-010) is added once Phase 7 has an actual
  host chosen.
- **Alternatives considered:** Moving all of Phase 6 to now — rejected, most of its scope (the
  test suite itself, full lint/format enforcement, security scanning, deploy automation) has
  prerequisites that don't exist yet (tests, chosen host) and would either run against nothing or
  need to be redone once those prerequisites land. Leaving CI/CD entirely in Phase 6 as originally
  scoped — rejected now that branch protection is live; PRs would merge on manual review only for
  the first five phases.
- **Consequences:** Phase 1 gains a small new deliverable (a basic GitHub Actions workflow) that
  wasn't in its original scope. Phase 6's CI/CD section is reworded to "extend" rather than
  "create" the pipeline. No change to the overall phase count or execution order — this splits one
  phase's scope across two touchpoints rather than reordering phases.

## ADR-012: `PRODUCTION_UPDATE_PLAN.md` becomes a task backlog; all undecided material lives in `docs/`

- **Date:** 2026-07-28
- **Status:** Accepted
- **Context:** `PRODUCTION_UPDATE_PLAN.md` had grown into a hybrid: actionable work, stack
  recommendations that were never decided, rationale, sequencing, and release scoping all in one
  narrative document. Nothing in it was individually trackable, and it repeated (and sometimes
  drifted from) material that already lived in `docs/tech_stack.md`, `docs/project_requirements.md`,
  `docs/gdpr.md`, and `docs/roadmap.md`. Separately, several `Accepted` ADRs (005, 006, 008, 009,
  010, 011) had consequences spread across the plan's prose with no guarantee every one had been
  picked up as work.
- **Decision:**
  - `PRODUCTION_UPDATE_PLAN.md` is now a **backlog**. Each phase, discovery workstream, and feature
    is an **Epic** (numbered 1–16, mapping 1:1 to the branch rows in `docs/roadmap.md`), and each
    epic holds numbered tasks (`3.12` = Epic 3, task 12) with a status of
    `Not started` / `In progress` / `Blocked` / `Done`. Task IDs are stable and never renumbered.
  - Epics 1–8 keep the original phase numbers, so existing references to "Phase N" in this log and
    elsewhere still resolve — Phase N is Epic N.
  - **Undecided material does not live in the backlog.** Candidate stack choices, product/business
    questions, privacy questions, and sequencing/milestones were moved into `tech_stack.md`,
    `project_requirements.md`, `gdpr.md`, and `roadmap.md` respectively. The backlog references
    them; it does not restate them.
  - **Every decision becomes a task.** Any `Accepted` ADR or `Decided` row in `docs/` must be
    represented by at least one task in an epic, tracked in the backlog's "Decision → task coverage"
    table. A task blocked on an `Open` row is marked `Blocked` with a pointer to the decision task
    (Epics 9/10/11) that unblocks it — so an undecided question can no longer be implemented by
    accident.
- **Alternatives considered:** A separate issue tracker (GitHub Issues/Projects) — better tooling,
  but it splits the working context away from the repo and away from Claude Code sessions, which is
  where this project's planning actually happens; revisit if more people join. Leaving the plan as
  prose and tracking tasks only in `roadmap.md` — rejected, `roadmap.md` tracks branches at
  phase granularity, which is far too coarse for ~140 discrete pieces of work.
- **Consequences:** The plan file is longer but mechanically usable — work can be picked up, closed,
  and referenced by ID from commits/PRs. Two files must now be kept in sync: epic status in
  `roadmap.md`, task status in the backlog. Adding a phase means adding both a roadmap row and an
  epic. Every future ADR gains a step: add its tasks to the relevant epic and a row to the coverage
  table in the same session.

## ADR-013: Railway (Hobby plan) as the hosting platform

- **Date:** 2026-08-03
- **Status:** Accepted
- **Context:** ADR-003 narrowed hosting to Railway, Render, and DigitalOcean App Platform but
  deliberately left the final pick open. Epic 12 can't start without it, and Epic 7 (observability /
  deployment hardening) depends on Epic 12. Pricing and platform capabilities were re-confirmed
  against Railway's pricing page and docs on 2026-08-03.
- **Decision:** Host on **Railway, Hobby plan** ($5/mo, including $5 of usage credit), with the app
  and PostgreSQL as separate services ([ADR-007](decisions.md)), built from the repo's `Dockerfile`
  rather than Railpack ([ADR-004](decisions.md)), deployed to the **EU West (Amsterdam)** region for
  GDPR data residency.
  - **Expected cost ~$6/mo.** Railway bills actual per-second usage: ~$10.14/GB-month RAM,
    ~$20.29/vCPU-month, ~$0.16/GB-month volume, $0.05/GB egress. For this workload — app ~0.3 GB
    (~$3.04), Postgres ~0.2 GB (~$2.03), CPU ~$0.41, a 2 GB volume ~$0.32, negligible egress.
  - **Railway's free options are explicitly rejected.** The 30-day trial deletes stateful volumes 30
    days after credits expire, and the Free plan ($1/mo credit, 0.5 GB RAM, one service) cannot run
    an app and a database together — which ADR-007 requires.
- **Alternatives considered:** **Render** — persistent staging works on any plan, but per-PR previews
  are gated behind the Pro workspace ($19/user/mo) and paid Postgres starts at ~$15/mo, putting a
  realistic total near ~$22/mo. **DigitalOcean App Platform** — ~$12–20/mo, bundles managed backups
  and monitoring and is the closest of the three to a "professional" baseline, but is roughly 2–3×
  Railway's cost for a single-bakery workload with no capability this project needs today. Both stay
  viable fallbacks if Railway's Hobby limits or lack of SLA become a problem.
- **Consequences:**
  - Closes the open pick in ADR-003; unblocks Epic 12 and, through it, Epic 7.
  - **The region must be set before any service is created.** Railway's default region is US West,
    and the personal data lives in the *database* — an app in Amsterdam with a default-region Postgres
    stores the actual data in California. Volumes follow the region of the service they attach to, and
    EU-West Metal supports volumes on Hobby (since 2025-03-14, superseding the February 2025 launch
    limitation), so this is a sequencing requirement, not a capability gap. Moving a volume afterwards
    forces a migration **with downtime** (task 12.8).
  - **Backups are not automatic on Railway** — daily (6-day retention), weekly (1 month), or monthly
    (3 months) schedules must be configured explicitly, billed incrementally. No PITR. This partly
    answers the `Open` Backups row in [tech_stack.md](tech_stack.md), but the full strategy is still
    9.16's job.
  - **Hobby has no uptime SLA and no HA Postgres.** Acceptable while pre-launch and solo; revisit at
    Pro ($20/mo per workspace, not per seat) once real tenants are onboarded under
    [ADR-006](decisions.md).
  - **Data residency vs. vendor ownership — the accepted risk.** Storage location is satisfied:
    GDPR treats the EU as one space (Art. 1(3) free movement), so Amsterdam serves Irish customers
    exactly as Dublin would. What Amsterdam does *not* solve is that Railway is a US company, so US
    law can reach the parent even for data held in the EU. That leaves a Chapter V transfer question
    answered by contractual safeguards (SCCs / the EU-US Data Privacy Framework), whose two
    predecessors — Safe Harbour (2015) and Privacy Shield (2020) — were both annulled by the CJEU.
    This risk is **accepted, not dismissed**, on three grounds: the initial market is Ireland, where
    US-owned cloud is the norm and carries little commercial friction; the exposure is shared by
    nearly every business running on AWS/Azure/Google Cloud; and SCCs remain as a fallback if the
    current framework falls. A DPA and subprocessor entry are required regardless (12.7 → 11.6).
  - **Revisit trigger — before expanding beyond Ireland.** EU-owned alternatives (Clever Cloud
    ~€16–26/mo, Scaleway ~€16/mo, both France) were priced at roughly 2.5–3× Railway — about $150/yr
    in absolute terms, which is not what decides this. What decides it is the market: continental
    buyers (Germany/France especially) treat EU ownership as a purchasing criterion in a way Irish
    buyers generally do not. Re-evaluate residency **before onboarding tenants outside Ireland**,
    while migration is still merely annoying rather than a coordinated multi-tenant cutover. ADR-004
    (Docker) and ADR-007 (separate database) are what keep that option cheap — preserve both.

## ADR-014: Local Docker Compose is the dev/test environment; no persistent hosted staging (amends ADR-010)

- **Date:** 2026-08-03
- **Status:** Accepted (amends ADR-010's persistent-staging clause)
- **Context:** ADR-010 requires every merge to `main` to auto-deploy to a persistent staging/dev
  environment on the chosen platform. On Railway ([ADR-013](decisions.md)) that means a second
  always-on app **and** Postgres, roughly doubling the bill to ~$12/mo — for an environment that a
  single developer leaves idle almost all of the time. The project currently has one developer and no
  live tenants.
- **Decision:**
  - The dev/test environment is **local**: `docker-compose` on the developer's machine, using the
    same `Dockerfile` Railway deploys ([ADR-004](decisions.md)) with app and Postgres as separate
    containers ([ADR-007](decisions.md)). It costs nothing and is already running during development.
  - **No persistent hosted staging environment.** Railway runs one environment, tracking `production`.
  - Testing responsibility splits by branch:
    - **Feature branch** — automated unit tests, run locally and in CI on the PR into `main`.
    - **`main`** — manual/integration verification of the *merged* result, run locally against
      `docker-compose` after pulling `main`. This catches interactions between separately-developed
      features, which isolated branch testing cannot.
    - **`main` → `production` PR** — the release gate; merging it deploys to Railway.
  - Because local verification never exercises Railway itself, enable a **Railway PR environment on
    the `main` → `production` release PR only** — a temporary full copy (app, its own Postgres, its
    own URL), auto-created when the release PR opens and auto-destroyed on merge. Railway does not
    gate PR environments behind a plan tier; at a few releases a month lasting a day or two each this
    costs well under $1/mo. It is deliberately **not** enabled on feature PRs, where it would mostly
    re-check what local testing already covered.
  - Refreshing the local environment is a **manual, developer-initiated step** — GitHub cannot push to
    a developer's machine — reduced to one command by a repo script (task 1.12).
- **Alternatives considered:** A persistent hosted staging environment, as ADR-010 originally
  specified — rejected on cost/benefit for a solo, pre-launch project; it becomes necessary the moment
  `main` needs to be verifiable by someone other than its author. PR environments on **every** feature
  PR — rejected as largely redundant with local testing, and it multiplies the database-seeding
  problem below. A self-hosted GitHub Actions runner auto-refreshing the local machine on merge —
  rejected as disproportionate machinery for a command the developer can run themselves, and it only
  works while that machine is on.
- **Consequences:**
  - Cuts expected hosting cost from ~$12/mo to ~$6/mo.
  - Makes the local Docker setup **load-bearing**: it is now the only integration-test environment, so
    drift between `docker-compose.yaml`/`Dockerfile` and production is a correctness problem, not just
    an inconvenience.
  - Railway PR environments clone services and configuration but **not volume data**, so the
    release-PR environment starts with an empty database and needs migrations plus seed data to be
    usable — new work that didn't previously exist (task 12.10).
  - `main` is **not** required to be green at every moment (nothing deploys from it); the binding rule
    is that it must be verified locally before a release PR is merged.
  - Revisit this ADR when a second developer joins or the first real tenant is onboarded.

## ADR-015: Host portability is a standing design constraint

- **Date:** 2026-08-03
- **Status:** Accepted
- **Context:** [ADR-013](decisions.md) picked Railway while explicitly deferring the EU-owned
  alternatives, and set a revisit trigger before expansion beyond Ireland (task 11.14). That deferral
  is only honest if moving hosts stays cheap. Left unmanaged, platform-specific behaviour accumulates
  quietly — a native backup format here, a platform env var there — until "we can migrate later" has
  become false without anyone deciding it. ADR-004 (Dockerfile) and ADR-007 (separate database)
  already point the right way but were decided for other reasons and don't cover the database,
  configuration, or state.
- **Decision:** The application and its database must remain deployable on **any host that can run a
  Docker image and a PostgreSQL service**, requiring configuration changes only — never code changes.
  Concretely:
  1. **The `Dockerfile` is the only build artifact** ([ADR-004](decisions.md)). No platform buildpack,
     no platform-specific build configuration committed to the repo.
  2. **All configuration comes from environment variables.** No settings module named after a host
     (the current `settings/heroku.py` is exactly the anti-pattern — 1.5, 7.9). `DATABASE_URL` is the
     database contract, since every candidate host provides it.
  3. **Bind to `$PORT` with a local fallback**, never a hardcoded port — most platforms inject the
     port they expect the container to listen on (7.17).
  4. **Migrations run as an explicit release/deploy step**, never inside the container start command
     (7.11) — baking them into `CMD` makes every replica race to migrate on boot.
  5. **The database must be restorable from a host-independent logical dump** (`pg_dump`), maintained
     *in addition to* whatever native snapshot the host offers (3.44). Native snapshots are for fast
     same-host rollback; the logical dump is what actually makes the host replaceable.
  6. **Core PostgreSQL and widely-available extensions only.** Anything host-specific requires its own
     ADR justifying the lock-in (3.45).
  7. **Persistent state lives only in PostgreSQL and S3-compatible object storage**
     ([ADR-005](decisions.md)) — never on the app container's local disk, which no platform
     guarantees across redeploys.
  8. **Every environment variable is documented in a committed `.env.example`** (7.13) — that file is
     the migration checklist.
- **Accepted lock-in, explicitly not fought:** Railway's git-watch deploy automation (7.15) and the
  release-PR preview environment ([ADR-014](decisions.md), 12.5). Both are workflow conveniences,
  neither touches data, and rebuilding them elsewhere is roughly a day's work. Native volume backups
  (12.9) are also fine to use — provided rule 5's portable dump exists alongside them.
- **Alternatives considered:** Accept platform lock-in for convenience — rejected; it would silently
  foreclose the residency revisit that ADR-013 depends on, which is the one decision most likely to
  need reversing. A full infrastructure abstraction (Kubernetes, Terraform, a provider-agnostic
  control plane) — rejected as wildly disproportionate for a two-service app; Docker plus environment
  variables plus a logical dump covers essentially the same ground at a fraction of the complexity.
- **Consequences:** Adds small constraints to several existing tasks and a handful of new ones (7.17,
  3.44, 3.45, 8.9), none large. **Portability is verified continuously and for free:** the local
  `docker-compose` environment from [ADR-014](decisions.md) runs the same image on plain Docker with
  no platform involved — if the app runs there, it runs anywhere, so a break in portability shows up
  as a broken local environment rather than as a nasty discovery during a migration. The main ongoing
  cost is discipline: a future ADR that wants a host-specific feature must argue against this one.

## ADR-016: <next decision goes here>

- **Date:**
- **Status:** Proposed
- **Context:**
- **Decision:**
- **Alternatives considered:**
- **Consequences:**
