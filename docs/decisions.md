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

## ADR-016: Phase 1 go-to-market — one pilot bakery, free, no deadline; flat per-bakery subscription as the eventual pricing shape

- **Date:** 2026-08-06
- **Status:** Accepted
- **Context:** [project_requirements.md](project_requirements.md) carried five linked `Open` commercial
  and context questions — who the first real users are, what timeline pressure exists, whether phase 1
  is a paid beta or a free pilot, what the pricing/plan structure looks like, and how tenants are
  onboarded. Together they determine whether billing work ever enters the backlog, what fields the
  `Bakery` tenant model needs (3.1), and whether the permission layer has to gate features by plan.
- **Decision:**
  - **First user:** a single friendly Irish bakery, running a pilot. It is a real food business
    operator with real data, not a test tenant.
  - **Timeline:** no committed launch date. Epic sequencing is driven by readiness and risk, not by an
    external deadline — the first-release milestone in [roadmap.md](roadmap.md) stays scoped by risk.
  - **Commercial model for phase 1:** a **free pilot**. No payment provider, no subscription state, no
    billing tables, no invoicing, no dunning. Billing is explicitly out of scope for this round.
  - **Eventual pricing shape:** a **flat per-bakery monthly subscription** — all features, unlimited
    users per tenant. Recorded now not because it is being built, but so nothing gets built that
    contradicts it: no feature gating by plan, no per-seat counting.
  - **Still Open:** tenant onboarding mechanics (10.10) and which EU countries follow Ireland (10.11).
- **Alternatives considered:** **Paid beta or paid from day one** — rejected for phase 1; a single
  pilot tenant does not justify a payment integration, and adding one now would put subscription state
  into the schema before the schema redesign (Epic 3) has even happened. **Tiered (Free/Pro/Business)
  pricing** — rejected as the target shape: tiering requires feature gating inside the permission
  layer, permanently complicating Epics 2 and 4 for revenue that does not exist. **Per-user seat
  pricing** — rejected; it makes seat counting a product concern and couples pricing to the role matrix
  (10.1), which should be driven by what people need to do, not by what they cost.
- **Consequences:**
  - **No billing epic exists, and none should be added this round.** If billing is proposed, it needs
    an ADR superseding this one.
  - The `Bakery` tenant model (3.1) needs **no** plan/tier/subscription fields — identity, contact, and
    an active flag are enough. Adding a plan field later is a small additive migration.
  - Role and permission work (10.1, 2.8, 3.4) is constrained by capability only, never by plan.
  - Multi-tenancy stays architecturally required ([ADR-006](decisions.md)) even with one tenant. Tenant
    #2 is not imminent, which buys time — but it does **not** downgrade the cross-tenant isolation
    tests (6.9), which must be in place *before* a second tenant exists, not after.
  - A single, known, forgiving pilot user makes the local-only dev/test model ([ADR-014](decisions.md))
    comfortable for longer than it otherwise would be. Revisit that ADR — and this one — before
    onboarding a second tenant or charging anyone.
  - The pilot bakery is a real data controller under [ADR-006](decisions.md), so the per-tenant DPA
    (11.5) is needed for the pilot too — "it's only a pilot" is not a GDPR exemption.

## ADR-017: Batch/lot food traceability is in scope, as its own epic

- **Date:** 2026-08-06
- **Status:** Accepted
- **Context:** [project_requirements.md](project_requirements.md) asked whether any regulation beyond
  GDPR applies. It does: a bakery is a food business operator, and EU Regulation 178/2002 Article 18
  requires every food business operator to be able to identify **one step back** (which supplier
  supplied which input) and **one step forward** (who a given output went to), with records produced to
  the competent authority on demand — the FSAI in Ireland. Bakery today models suppliers, raw
  materials, recipes, and products as a pure current-state catalogue: there is no notion of a delivery,
  a batch, a lot code, or a production run, so it cannot support that record-keeping at all.
- **Decision:** Batch/lot traceability is an **in-scope product capability**, built as its own epic
  (Epic 17, `feature-traceability`) rather than folded into the Epic 3 schema redesign.
  - **Model shape (direction, detail in 9.21):** goods-receipt lines record what actually arrived —
    supplier lot code, receipt date, quantity, best-before — distinct from the `RawMaterial` catalogue
    row. Production runs consume specific receipt lots and emit an output batch carrying its own
    internal lot code. Outbound records capture where a finished batch went.
  - **Regulatory floor:** one-step-back and one-step-forward. Full internal mass-balance (reconciling
    every gram in against every gram out) is a **Should**, not a **Must**.
  - **Sequencing:** depends on Epic 3 — tenant scoping, numeric quantities, and canonical units must
    land first, because a traceability record without a trustworthy quantity is not worth writing.
  - **Explicitly not in scope:** HACCP plans, temperature/cleaning logs, allergen labelling as such
    (a separate question, still Open), and automated recall workflows.
- **Alternatives considered:** **Treating traceability as the bakery's own paper problem and staying
  GDPR-only** — rejected; the pilot user needs it and it is a legal obligation on them, not an optional
  feature. **Bolting lot fields onto the existing models** (e.g. a `lot` `CharField` on `RawMaterial`)
  — rejected: a lot is an *event over time*, not an attribute of a catalogue item. This app already
  suffers from exactly that conflation (`RawMaterial.price` has no time dimension, which is why the
  price-basis and price-history questions in 10.5 are hard), and repeating it would make the schema
  actively wrong rather than merely incomplete. **Integrating a dedicated third-party traceability
  system** — not evaluated; revisit only if Epic 17 proves substantially larger than scoped.
- **Consequences:**
  - **This is the largest single addition to the product scope so far.** It adds a temporal/event layer
    to a schema that is currently pure current-state. Epic 3's schema work should be reviewed with
    Epic 17 in mind so the redesign doesn't have to be redone.
  - **It partly pre-answers 10.5's deletion-semantics question.** A `Supplier` or `RawMaterial`
    referenced by a traceability record can never be hard-deleted, so soft delete/archive stops being
    a judgment call for those entities (3.13, 3.22, 17.6).
  - **It interacts with the price-basis and price-history questions (10.5).** A goods-receipt line
    naturally carries the price actually paid on that date — which would answer product/input price
    history as a side effect. Decide 10.5 with this in mind rather than independently.
  - **Retention gains a legal floor that GDPR minimization cannot override.** Food law imposes a
    *minimum* retention on traceability records (commonly five years, shorter for short-shelf-life
    products); where such a record names a supplier's contact person, that floor and the GDPR
    retention policy have to be reconciled rather than chosen freely — 10.9, feeding
    [gdpr.md](gdpr.md) §5 and 11.4.
  - **Traceability records must be append-only** — no hard delete, no silent retroactive edit. That is
    a stronger integrity requirement than anything else in the schema (17.5) and pairs with the audit
    logging in 2.9/11.10.
  - **A partial implementation is worse than none if it looks complete.** The pilot bakery is a real
    food business operator; whatever ships must not present itself as a compliance record until the
    one-step-back/one-step-forward path is actually whole (17.7, 17.10).
  - Adds structural data-model questions to [tech_stack.md](tech_stack.md) (batch/receipt entity shape,
    lot code generation, whether stock levels come along for the ride) — 9.21.

## ADR-018: Costing and money semantics — purchase-unit prices, kg/l/each canonical units, net-of-VAT storage with a dated rate table, and dual-source price history

- **Date:** 2026-08-06
- **Status:** Accepted
- **Context:** Four of the seven business data-semantics questions in
  [project_requirements.md](project_requirements.md) were blocking the Epic 3 schema redesign (tasks
  3.10, 3.11, 3.15, 3.16, 3.34). They are recorded as one decision because they only make sense
  together: what a price *means* determines what a unit must be, which determines where VAT can be
  applied, which determines what a price *history* row has to contain. Deciding them separately is how
  the current prototype ended up recomputing cost inline in `float()` in three different views.
- **Decision:**
  1. **Price basis — purchase unit + pack size, normalized at cost time.** `RawMaterial` stores what
     the invoice says: a purchase price, a pack quantity, and a purchase unit (€12.50 / 25 / kg). The
     service layer derives cost per canonical unit; nothing persists the derived figure (task 3.17
     stands). This is also exactly what an [ADR-017](decisions.md) goods-receipt line records, so the
     two features agree by construction rather than by convention.
  2. **Canonical units — kilogram, litre, each**, one per dimension (mass, volume, count). Any purchase
     unit converts to its canonical unit through a **conversion factor held in a reference table**, so
     adding "sack" or "dozen" is data entry, not a code change and not a migration.
  3. **VAT — all stored money is net (ex-VAT).** VAT is applied only at display/sale, never in stored
     data. Rates live in a **dated VAT-rate reference table** (`code`, `percent`, `valid_from`,
     `valid_to`) and a product references a rate code, not a number. This matches Irish reality, where
     different bakery products genuinely attract different rates, and it survives a statutory rate
     change without silently rewriting historical margins.
  4. **Price history — versioned, from two different sources.** Input prices are historised by the
     goods receipts that [ADR-017](decisions.md) already requires: each delivery dates the price
     actually paid, so input price history is a by-product rather than new machinery. Sale prices get
     their own dated rows (`ProductPrice`: product, net price, `valid_from`), with the current price
     being the latest row whose `valid_from` has passed. Two mechanisms, because the two prices have
     genuinely different origins — one is an observed fact, the other is a decision the bakery makes.
- **Alternatives considered:**
  - **Storing €/canonical-unit directly** — rejected; it discards the invoice figure and makes the user
    do the arithmetic on every price change, which is a silent-error generator in exactly the numbers
    this app exists to compute.
  - **Persisting the derived unit price as a column** — rejected; it creates two fields that can
    disagree and contradicts 3.17. Revisit only if profiling shows the derivation is actually a
    bottleneck, and then as an explicit cache with an invalidation story.
  - **Gram/millilitre canonical units** — considered and **not** chosen; see the precision consequence
    below, which is the price of that choice.
  - **A plain VAT-rate field on the product** — rejected; a statutory rate change would bulk-update
    every product and recompute past margins at today's rate.
  - **Gross (VAT-inclusive) storage** — rejected; every margin calculation would begin with a division,
    and the resulting repeating decimals propagate into the cost/margin figures.
  - **Current-price-only** — rejected; it makes "why did this product's margin drop in March?"
    unanswerable, which is precisely the question Epic 16's margin alerts are supposed to answer.
- **Consequences:**
  - **Precision and rounding are now load-bearing, because the canonical units are large.** With
    kilogram as the mass canonical, 7 g of yeast is `0.007` and a pinch of spice is `0.0005`.
    Quantities need at least `Decimal(12,4)` — `Decimal(12,6)` is the safer default — and money needs
    to be carried at more than two decimal places internally, rounding to 2 dp **only at
    presentation**. The rounding rule itself (half-up, and at which boundary) must be written down and
    tested rather than inherited from whatever Python does by default — new task 3.51, tested in 6.16.
    This is the direct cost of kg/l over g/ml, and it is manageable, but only if it is explicit.
  - **Units become a lookup table, not an enum.** This pre-answers half of 9.18: a conversion factor is
    data a unit must carry, which an enum cannot hold. Categories remain an open enum-vs-lookup
    question. Unblocks 3.26 for units only.
  - **Two new reference tables and their seed data:** unit conversions and VAT rates (3.52, 3.53), which
    feed the seed/reference-data strategy in 3.37 and the new-tenant onboarding question in 10.10.
  - **Which VAT rate applies to which product is a tax question, not an engineering one.** Irish VAT
    treatment of bakery goods is genuinely non-obvious (bread vs. flour confectionery), so the schema
    must let a tenant set it per product and must not ship with guessed assignments — 10.13.
  - **Existing data has no recorded basis.** Today's `RawMaterial.price` values mean whatever the person
    typing them assumed. Backfilling into the new model is a human-judgment, per-row data-quality
    exercise, not an automatic migration — 3.54, and it must happen before the old fields are dropped
    (3.32).
  - **Historical margin becomes reconstructible**, which turns the "historical cost/price snapshots &
    trend reporting" backlog item from speculative into cheap, and gives Epic 16's margin alerts an
    actual baseline to compare against.
  - **The inline `float()` costing in `control/views.py` is now definitively wrong**, not merely
    duplicated — it cannot express any of the four decisions above. It must be deleted in favour of the
    service layer (4.1, 3.25), not patched.
  - Closes four of the seven rows in the data-semantics table. Still open: which entities need soft
    delete (partly forced by [ADR-017](decisions.md)), supplier-name uniqueness, and the Django-admin
    vs. in-app-settings overlap.

## ADR-019: Deletion semantics, supplier identity, and the two administration surfaces

- **Date:** 2026-08-06
- **Status:** Accepted
- **Context:** The last three business data-semantics questions in
  [project_requirements.md](project_requirements.md) — which entities survive "deletion", whether
  supplier name stays unique once it is no longer the primary key, and whether the Django admin and
  the in-app settings area should expose the same operations. All three block Epic 3 (3.6, 3.22) and
  the second is only answerable now that multi-tenancy (ADR-006) and traceability (ADR-017) are
  settled.
- **Decision:**
  1. **Soft delete for anything referenced by a record that outlives it.** `Supplier` and
     `RawMaterial` (forced by traceability), plus `Product` — an outbound trace record and a dated
     `ProductPrice` row both point at it — and `Base_recipes`, since a production run references the
     recipe it followed. **Ingredient lines stay hard-deletable**: they are only meaningful inside
     their parent and nothing outside references them.
  2. **Supplier name is unique per tenant, not globally.** Two different bakeries may both buy from
     "Odlums"; global uniqueness would be actively wrong in a multi-tenant product. Within one tenant,
     a duplicate name is almost always a data-entry error worth blocking.
  3. **Uniqueness applies among non-archived rows only.** This falls directly out of combining (1) and
     (2): with a plain composite unique constraint, archiving "Odlums" would permanently block ever
     creating a supplier by that name again. Enforced as a partial unique index over live rows.
  4. **Two administration surfaces with two different audiences.** The in-app settings area is the
     tenant's surface — tenant-scoped, role-checked, audited. The **Django admin is superuser-only
     support tooling** for the project owner: data repair and diagnosis, never linked from the tenant
     UI, never offered to a tenant user.
- **Alternatives considered:**
  - **Soft delete on every business table** — rejected; it puts an archived-row filter on every query
    forever, and a missed filter resurrects deleted data. That is the same failure mode as a missed
    tenant filter, and doubling the number of correctness-critical filters doubles the chance of it.
  - **Soft delete only on the forced set** (`Supplier`, `RawMaterial`) — rejected; deleting a `Product`
    would orphan its price history and any outbound trace record, so it would need a delete block
    anyway, which is soft delete with worse ergonomics.
  - **No supplier-name uniqueness, warn only** — rejected as the default; duplicates silently split a
    supplier's cost history across two rows with no link between them. Genuine "two branches of the
    same supplier" cases are served by distinct names, which is what a human would write anyway.
  - **Case/whitespace-normalized uniqueness** — a better constraint, and deliberately **not** adopted
    now: it needs a normalized column or a functional index, and the marginal duplicates it catches
    ("odlums" vs "Odlums") do not yet justify that. Reconsider if real duplicates appear.
  - **Disabling the Django admin in production** — rejected; it removes the fastest tool for repairing
    a pilot tenant's data, leaving management commands or `psql` against production, which is a worse
    risk than a superuser-gated admin.
  - **Keeping both surfaces with identical operations** (today's shape) — rejected; every permission
    rule would have to be enforced twice, and Django admin bypasses tenant-scoped managers by default.
- **Consequences:**
  - **Two orthogonal, correctness-critical query filters now exist:** tenant scope (ADR-008) and
    archived state. They must be combined in **one** base manager rather than applied ad hoc per
    query, and tested together — a query that filters tenant but not archived is a bug, and one that
    filters archived but not tenant is a data leak (3.55, tested in 6.18).
  - **"Delete" in the UI now means two different things** depending on the model, which users will
    notice. The interface has to say *archive* where it archives, and archived rows need a way back
    (3.56) — a soft delete with no un-delete path is just a confusing delete.
  - The per-tenant unique constraint **depends on the tenant FK existing first** (3.2), so 3.6 is
    sequenced after it, not alongside.
  - **The Django admin is now a deliberate cross-tenant surface.** That is exactly what makes it useful
    for support and exactly what makes it dangerous: it must be superuser-gated (2.15), excluded from
    tenant-facing navigation, and its access to personal data logged like any other (11.10). Do **not**
    rely on `ModelAdmin` to enforce tenant scoping — it does not, by default.
  - Closes the data-semantics section of [project_requirements.md](project_requirements.md) entirely.
    Together with [ADR-018](decisions.md), all seven questions are now answered and Epic 3's blocked
    tasks are unblocked.

## ADR-020: Three per-tenant roles — Owner, Staff, Read-only — held on a membership record

- **Date:** 2026-08-06
- **Status:** Accepted
- **Context:** `PRODUCTION_UPDATE_PLAN.md` originally proposed four roles (admin/owner, manager,
  staff/operator, read-only/auditor) and [project_requirements.md](project_requirements.md) carried
  the capability matrix as `Open`. [ADR-006](decisions.md) scoped roles per tenant, and task 2.8
  (real authorization in views) cannot be implemented until the roles actually exist. Today access
  control is enforced inconsistently — partly in templates, partly not at all.
- **Decision:**
  - **Three roles per tenant:**
    - **Owner** — full administration of their own bakery: users, settings, pricing, archiving,
      exports, and all daily work.
    - **Staff** — daily work: raw materials, recipes, products, goods receipts, production runs. No
      user management, no tenant settings.
    - **Read-only** — view and export, no writes at all. This is the accountant/auditor seat.
  - **The role lives on a membership record** (user × bakery × role), not on the user. Django's global
    `Group` model cannot express "Owner of bakery A" and the role must be per tenant per ADR-006. The
    membership model also means a user *could* belong to more than one tenant without a schema change.
  - **"Manager" is deliberately deferred**, not rejected. It is a real distinction in a larger bakery
    (pricing and suppliers without user administration), but the pilot cannot yet articulate it, and a
    role whose permissions are guessed is worse than one that does not exist.
- **Alternatives considered:** **Four roles including Manager** — rejected for now on the above
  grounds; adding it later is a new row in a role table, not a reshape, *provided* permissions are
  checked by capability rather than by `if role == "owner"` scattered through views. **Two roles
  (Admin/Staff)** — rejected; with no read-only tier an accountant either gets write access or a
  shared login, and shared logins destroy the audit trail that Epics 11 and 17 depend on. **Django
  groups plus granular per-tenant editable permissions** — rejected as premature: it makes "who can do
  what" per-tenant configuration that can no longer be reasoned about or tested centrally, and the
  test matrix becomes combinations rather than three roles.
- **Consequences:**
  - Unblocks 2.8 and 3.4, and gives 10.1's capability matrix its shape.
  - **Permission checks must be capability-named, not role-named** — `can_manage_users`, not
    `role == "owner"` — even though only three roles exist. This is what keeps Manager cheap to add
    later, and it costs nothing now (2.16).
  - **Read-only can export**, which is deliberate but means a read-only account can still extract data
    in bulk. Every export is audit-logged (14.4, 15.4, 11.10); that logging is what makes this
    acceptable rather than the role restriction.
  - **Traceability writes are Staff-level**, since recording a goods receipt is daily work. But
    traceability records are append-only ([ADR-017](decisions.md)), so a mistaken Staff entry is
    corrected by a new record, never by editing — the role model and the integrity model have to be
    implemented together (17.5).
  - **Still open:** whether one person may hold memberships in several tenants in the product UI. The
    membership model supports it; whether it is offered is a product question — 10.14.
  - Every existing user in the current database has no role. Assigning one per user is a migration
    with a human decision in it, not a default (3.57).

## ADR-021: Non-functional targets — modest explicit performance budgets, WCAG 2.2 Level A, responsive/evergreen-browser support, and translation-ready English/euro

- **Date:** 2026-08-06
- **Status:** Accepted
- **Context:** The non-functional requirements table in
  [project_requirements.md](project_requirements.md) was entirely `Open`, blocking task 5.12 and
  leaving Epic 5's frontend rewrite with no target to build against. These are cheapest to decide
  *before* the templates are rewritten, since accessibility and localization are far more expensive
  to retrofit than to build in.
- **Decision:**
  1. **Performance — modest but explicit.** p95 under ~500 ms for normal pages, under ~2 s for the
     dashboard's costing aggregate, at roughly ten concurrent users per tenant, on a dataset of
     thousands of rows rather than millions. Numbers the ~$6/mo Railway Hobby service can actually
     hold ([ADR-013](decisions.md)), and specific enough that a regression is detectable.
  2. **Accessibility — WCAG 2.2 Level A.** The minimum conformance level: alt text, real form labels,
     no keyboard traps, no information conveyed by colour alone.
  3. **Devices and browsers — one responsive UI**, phone through desktop, on the current and previous
     major version of Chrome, Firefox, Safari and Edge. No IE11, no legacy Edge, no native mobile app.
  4. **Localization — English and euro only, but translation-ready.** Ship `en-IE`/EUR, while routing
     display text through Django's translation machinery and all money through a single formatter from
     day one. No hardcoded `€` in templates.
- **Alternatives considered:**
  - **No numeric performance target** — rejected; it leaves nothing for review or CI to check against,
    and "is this a regression?" becomes a judgment call every time. **Strict sub-200 ms budgets
    enforced in CI** — rejected; Railway Hobby shares CPU, so the host itself makes that latency
    partly unenforceable, and the machinery is disproportionate for one pilot tenant.
  - **WCAG 2.2 Level AA** — the recommended option and **not** chosen; see the consequence below.
  - **No accessibility target at all** — rejected; Level A is cheap during a template rewrite and
    turns accessibility into a requirement rather than a future bug report.
  - **Desktop-first with best-effort mobile** — rejected; goods receipts under
    [ADR-017](decisions.md) get recorded at the delivery door, on a phone. **Mobile-first** — rejected
    as the primary frame; costing and margin views are inherently wide tables.
  - **Hardcoded English/€** (today's behaviour) — rejected; it makes the ADR-016 expansion trigger
    expensive precisely when it fires. **Multi-language and multi-currency now** — rejected; the next
    EU countries are undecided (10.11), and multi-currency touches every money column and the whole
    costing service.
- **Consequences:**
  - **Level A is below what procurement typically asks for.** It deliberately excludes AA's contrast
    ratios (4.5:1), visible focus indicators, consistent navigation, and error-suggestion
    requirements. That is a fine call for a pilot with a handful of known users, and it is worth
    naming what it means: the gap becomes real the first time a tenant has a staff member who needs
    it, or a buyer asks for a conformance statement — which is likelier at EU expansion, where public
    procurement and the European Accessibility Act point at AA. **Recorded as a revisit trigger
    (10.15), tied to the same expansion point as 10.11 and 11.14.** Building semantic HTML and real
    form labels for Level A during Epic 5 keeps most of the distance to AA small.
  - **Performance targets need something to measure them.** They are unverifiable until Epic 7's
    logging and slow-query monitoring exist (7.1, 3.43), so they are a documented budget now and an
    observed one later — not a CI gate (5.14).
  - **Translation-readiness is a discipline, not a feature.** `gettext` on display strings and one
    currency formatter cost almost nothing during the Epic 5 rewrite and are painful to add
    afterwards. This means Epic 5 must not introduce a single hardcoded `€` — including in the
    existing templates it touches (5.15, 5.16).
  - Wide costing/margin tables need a deliberate small-screen strategy — horizontal scroll containers
    or card layouts — rather than being left to overflow (5.13, already scoped).
  - Closes the entire non-functional section of [project_requirements.md](project_requirements.md) and
    unblocks 5.12.

## ADR-022: Goods receipts drive raw-material cost; ingredient lines accept a raw material **or** a base recipe

- **Date:** 2026-08-06
- **Status:** Accepted
- **Context:** Two functional questions from
  [project_requirements.md](project_requirements.md) "Functional requirements by area", both of which
  turned out to be domain-model questions rather than UI ones. First: once
  [ADR-017](decisions.md)'s goods receipts exist, the price actually paid for a material is recorded
  in two places — the receipt and `RawMaterial` — so which one costing believes has to be settled.
  Second: `Base_recipes` and `Product` are currently parallel and **disconnected** — a product's
  ingredient lines can only reference raw materials, so a base recipe's cost can never reach a
  product. Base recipes are therefore a standalone calculator that nothing consumes, which is half a
  feature.
- **Decision:**
  1. **The latest goods receipt sets a raw material's current cost**, with a manual override retained
     as a fallback. Cost becomes an observed fact rather than a number re-typed by hand. "Latest" means
     the most recent receipt by **receipt date** (not entry date), ties broken by creation time, so
     back-dating a late-entered delivery behaves correctly.
  2. **A manually-entered price remains possible and is labelled an estimate.** A material that has
     never been received — a new ingredient being costed for a product that doesn't exist yet — must
     still be costable, otherwise recipe planning is impossible before the first purchase.
  3. **Every cost figure carries its provenance.** The UI and any export must be able to say whether a
     figure came from a real receipt or from an estimate. A margin computed from a guess and one
     computed from an invoice are not the same claim.
  4. **An ingredient line references either a raw material or a base recipe.** Costing recurses: a
     product consuming "laminated dough" pulls that base recipe's cost per unit of its yield.
- **Alternatives considered:**
  - **Receipts as traceability records only, price maintained by hand** — rejected; the same figure
    would be entered twice with nothing detecting divergence, which is the exact failure mode
    [ADR-018](decisions.md) was written to remove.
  - **Receipt price as the *only* price** — rejected; a material with no receipt could not be costed
    at all, which blocks "what would this product cost?" planning entirely.
  - **Keeping base recipes and products parallel and disconnected** (today's shape) — rejected; a
    bakery making one dough used in six products would restate every dough ingredient six times, and a
    flour price change would mean editing six products.
  - **Merging both into one recipe model with a `is_sellable` flag** — genuinely cleaner and **not**
    chosen: it is a larger migration and it collapses a distinction the bakery may think in. Note that
    decision 4 makes the two ingredient-line models structurally identical, so this option gets
    materially easier later if it's ever wanted.
- **Consequences:**
  - **Recursive costing introduces a cycle risk that must be prevented, not merely avoided.** A base
    recipe that contains itself — directly, or transitively through two others — makes costing loop
    forever. This needs a validation rule at save time plus a depth guard in the costing service
    (3.59, 4.16), and a test that a cycle is rejected (6.20). This is the single most important
    consequence here; nothing in the current schema prevents it.
  - **`recipe_yeld` becomes load-bearing.** To use a base recipe as an ingredient, its cost must be
    expressible per unit of yield, so the yield needs a real numeric value and a unit from the
    [ADR-018](decisions.md) unit table — it can no longer be a loose field (3.60, extends 3.14).
  - **This substantially answers 9.18's ingredient-line question.** Both line models now need a typed
    *component* reference (raw material or base recipe) as well as a typed parent, which makes them
    structurally identical. A single shared ingredient-line model is now strongly indicated; formally
    it remains 9.18's call, but the alternative has lost most of its justification.
  - **Cost provenance has to be modelled, not just displayed** — a flag or a derivation the service
    layer returns alongside the figure (4.17). Retrofitting provenance into a bare `Decimal` later is
    painful.
  - **The receipt and the material now share one price shape** (`purchase_price` / `pack_quantity` /
    `purchase_unit`), which is why 3.10 and 17.1 must be implemented against the same definition.
  - **Point-in-time costing becomes possible but is not in scope.** With dated receipts and dated sale
    prices, "what was this product's margin in March?" is answerable — deferred to the trend-reporting
    feature rather than built into the costing service now.
  - Epic 17's multi-level trace (17.7) and this recursion are the same traversal in opposite
    directions; implementing one should inform the other.

## ADR-023: Dashboard becomes an overview page; the settings area becomes tenant self-administration

- **Date:** 2026-08-06
- **Status:** Accepted
- **Context:** The remaining two "Functional requirements by area" questions in
  [project_requirements.md](project_requirements.md) — what the dashboard should be, and what the
  settings/users/export area should contain now that tenants ([ADR-006](decisions.md)) and roles
  ([ADR-020](decisions.md)) exist and the Django admin has been narrowed to superuser support tooling
  ([ADR-019](decisions.md)).
- **Decision:**
  1. **The dashboard becomes a genuine overview**: a summary strip (product count, average margin,
     materials with no or stale pricing), the worst-margin products, and recent input price movements.
     The full product list moves to its own page rather than being the dashboard.
  2. **The settings area becomes the tenant's self-administration surface**, owned by the Owner role:
     invite and remove users and set their roles, edit bakery details, manage reference data, and run
     exports. Read-only users can reach exports; nothing else in there is writable by them.
  3. This is the surface the Django admin deliberately is **not** — it is tenant-scoped, role-checked,
     and audited, per [ADR-019](decisions.md).
- **Alternatives considered:** **Keeping the dashboard as the product cost/margin list** with better
  sorting/filtering — the lower-risk option, rejected because the overview is where price history
  (ADR-018) actually pays off. **Fixing only the underlying math with no UI change** — rejected as too
  little given Epic 5 is rewriting the templates anyway. **Keeping reference data in the Django admin**
  — rejected; every unit or VAT-rate change would become a support request. **Superuser-side user
  management only** — rejected; it leaves the Owner role with almost nothing to administer and makes
  onboarding tenant #2 a manual job.
- **Consequences:**
  - **The dashboard rework depends on Epic 3, not just Epic 5.** "Recent input price movements" and
    "stale pricing" require [ADR-018](decisions.md)'s dated prices and [ADR-022](decisions.md)'s
    receipts to exist. Built before that data lands, the overview has nothing to show — so it is
    sequenced after Epic 3 even though it is a frontend deliverable (5.18).
  - **"Stale" needs a definition.** How old a price must be before the dashboard flags it is a business
    rule nobody has set — 10.16. Shipping a warning badge with an arbitrary threshold would train users
    to ignore it.
  - **Inviting users requires email, which the app does not currently send.** This turns the "any email
    provider (if added)" row in [gdpr.md](gdpr.md) §7 from hypothetical into required: a provider must
    be chosen (9.22), configured from environment variables, and covered by a DPA (11.6) before
    invitations ship. It is a new external dependency created by this decision, not an incidental
    detail.
  - **Tenant-editable reference data is not uniformly safe.** VAT rates and categories are fine for a
    tenant to manage. **Unit conversion factors are not** — a wrong factor silently corrupts every cost
    figure that depends on it, with no error anywhere. The likely split is system-managed units with a
    tenant-selectable subset, but that is a real decision, not an assumption — 10.17.
  - **This replaces the broken user-delete view rather than patching it** (the one that deletes
    `RawMaterial`). 6.7's regression test still applies, but the fix is the rebuilt surface.
  - The overview's aggregates run against the p95 < 2 s dashboard budget from
    [ADR-021](decisions.md) — which is also the view most likely to need the caching that 9.18 leaves
    open.

## ADR-024: Feature backlog prioritization (MoSCoW pass, task 10.3)

- **Date:** 2026-08-06
- **Status:** Accepted
- **Context:** The feature backlog in [project_requirements.md](project_requirements.md) carried
  candidates with no priority column filled in, which left epic sequencing (13–17) and several Epic 5
  tasks without a basis for ordering. Task 10.3 is the MoSCoW pass.
- **Decision:**

  | Feature | Priority | Reasoning |
  |---|---|---|
  | Batch/lot traceability (Epic 17) | **Must** | A legal obligation on the user, decided in [ADR-017](decisions.md) |
  | Multi-tenancy (Epic 3) | **Must** | Architectural foundation, [ADR-006](decisions.md)/[ADR-008](decisions.md) |
  | Real search/filter across entities | **Must** | The current search inputs exist and do nothing, which is worse than absent. Epic 5 is rewriting these templates anyway |
  | Supplier price comparison for the same raw material | **Must** | Core buying-decision value — see the schema consequence below |
  | Tenant full data export (Epic 14) | **Should** | Product differentiator, [ADR-008](decisions.md); depends on Epic 3 |
  | GDPR personal-data export (Epic 15) | **Should** | The Article 20 fix, [ADR-009](decisions.md) |
  | Trend reporting / dashboards beyond the per-product view | **Should** | The data foundation is free from [ADR-018](decisions.md)/[ADR-022](decisions.md), and [ADR-023](decisions.md)'s overview delivers the first slice. Full trends need months of accumulated data that won't exist at launch |
  | Product photo upload | **Could** | Cosmetic for a costing tool |
  | User profile picture upload | **Won't (this round)** | Personal data with an undecided legal basis (11.3), an object-storage DPA, and erasure obligations — real compliance cost for no operational value at a one-tenant pilot |
  | Billing / subscriptions | **Won't (this round)** | [ADR-016](decisions.md) |
  | Better user & role management | **Must — merged, not a separate feature** | This *is* [ADR-023](decisions.md)'s settings area assigning [ADR-020](decisions.md)'s roles. Already scoped as 5.19, 2.8, 3.58, 9.22; the backlog row is folded in rather than tracked twice |
  | Allergen data on raw materials, aggregated to products | **Should** | A legal obligation on a bakery selling to consumers (EU FIC 1169/2011), and it rides on the recursion [ADR-022](decisions.md) just built — aggregating allergens up a recipe tree is the same traversal as cost. New Epic 18 |
  | Stock / quantity-on-hand | **Could** | Receipts and production runs *imply* it, but claiming stock figures are accurate is a materially bigger promise than claiming a cost is. Stays a 9.21 sub-question, not an epic |
  | AI insights & alerts service (Epic 16) | **Could — and re-scope before spending** | Keep the goal, revisit the engine. Margin alerts over [ADR-018](decisions.md)'s price history are a scheduled query, not a Spark cluster |
  | Self-service user registration | **Won't (this round)** | Open signup into a shared database with no billing gate produces spam tenants and abandoned accounts holding personal data you are then obliged to retain and delete |

- **Alternatives considered:** **Search as Should** — rejected; leaving dead inputs in a freshly
  rewritten UI is indefensible, and the fix is cheap while the templates are open. **Reporting as
  Must** — rejected; charts over one week of data are not persuasive, and the overview page already
  covers the immediate need. **Media as Should** — rejected; it would put the profile-picture legal
  basis on the critical path rather than resolving it when the feature is actually wanted. **Supplier
  comparison as Could** — rejected despite being the cautious call, since the user rates it core
  buying-decision value.
- **Consequences:**
  - **Supplier price comparison as a Must forces a schema change beyond what Epic 3 already had.**
    `RawMaterial` today has a **single** supplier FK, so a comparison view would have exactly one row
    per material and show nothing. The fix follows naturally from [ADR-022](decisions.md): the real
    supply relationship belongs on the **goods receipt** (this supplier, this material, this price,
    this date), so `RawMaterial`'s FK becomes at most an optional *preferred supplier* rather than the
    definition of who supplies it — 3.63, with the comparison view itself in 5.21.
  - **This makes the comparison feature dependent on Epic 17**, not merely on Epic 3 — the receipts
    are the data it compares. Until receipts accumulate across more than one supplier, the view will
    be sparse; that is expected, not a defect.
  - **Epic 13 narrows to product photos only.** Profile pictures leave this round, which takes 11.3
    (their legal basis) off the critical path and removes the profile-picture driver from the R2 DPA —
    though R2 is still needed for product photos if Epic 13 runs at all, and 11.6 still covers it.
  - **Search moves into Epic 5 proper** rather than being deferred: 5.9's "build it or remove the dead
    inputs" phrasing resolves to *build it*.
  - Reporting stays a post-launch epic, which means the ADR-023 overview dashboard is the whole of the
    reporting story for the first release — worth saying plainly so it isn't quietly expanded.
  - **Allergen data becomes Epic 18** (`feature-allergen-data`), reversing the "still Open" position
    [ADR-017](decisions.md) left it in. It is scoped as a *Should*, deliberately outside Epic 17 so
    the Article 18 traceability core is not delayed by scope growing around it — but it reuses
    [ADR-022](decisions.md)'s recipe recursion directly, so building it after Epic 17 costs far less
    than building it before. **The same care applies as with traceability:** allergen information that
    looks authoritative but is incomplete is worse than none, because a consumer-facing claim depends
    on it (18.5).
  - **Stock levels stay explicitly excluded from Epic 17's scope**, as a `Could`. This matters for
    9.21: the traceability entities should be designed so quantity-on-hand *could* later be derived
    from them, without the app claiming to track stock now.
  - **Epic 16's engine question moves ahead of its build.** Rating it `Could` while
    [ADR-002](decisions.md) is still only `Proposed` means 9.20 must resolve before any Databricks
    spend, and 16.4's DPA is not needed until then. A margin alert over dated prices is a scheduled
    job; that is now the null hypothesis Spark has to beat.
  - **Tenant onboarding is answered in practice** (10.10): tenants are provisioned manually by the
    project owner, and staff accounts come from Owner invitations ([ADR-023](decisions.md)). Public
    signup is not built. Revisit when tenant #2 arrives or when billing exists to gate it.
  - **"Better user & role management" leaves the feature backlog as a distinct item** — it is fully
    covered by existing tasks, and keeping a duplicate row would let the two drift.

## ADR-025: Runtime baseline — Django 5.2 LTS on Python 3.13, upgraded directly from 3.2, with the dependency set rebuilt around it

- **Date:** 2026-08-10
- **Status:** Accepted
- **Context:** Tasks 9.1, 9.2, 9.5, 9.6 and 9.7 — the runtime and dependency rows that
  [tech_stack.md](tech_stack.md) still carried as `Open`, and the last thing standing between Epic 2
  and Epic 3. Everything the app runs on is past end of life: Python 3.8 (`runtime.txt`) since
  October 2024, the Dockerfile's 3.9-slim since October 2025, and Django 3.2 since April 2024. The
  candidate text in `tech_stack.md` — "3.12 as the primary target, validate 3.13 later" — was written
  when 3.12 was the current release; 3.12 went security-fixes-only in October 2025, so the candidate
  had quietly aged into a recommendation to start a new build on an unsupported runtime. Release
  windows and every package's declared support were re-verified 2026-08-10 (sources in
  [tech_stack.md](tech_stack.md)). These are recorded as **one** decision because the Django version
  determines the Python range, which determines the database driver and the rest of the pin set —
  deciding them separately is how a mutually incompatible pin set gets assembled one line at a time.
- **Decision:**
  1. **Django 5.2 LTS — not the current stable.** Verified 2026-08-10: 5.2 LTS is supported to
     **April 2028**; the current stable 6.1 only to December 2027; and 6.0 left mainstream support on
     **4 August 2026**, six days before this decision. The older LTS has the longer runway. The next
     hop is **6.2 LTS** (releases April 2027, supported to April 2030), planned for H2 2027.
  2. **Python 3.13.** It is supported by *both* ends of the planned path — Django 5.2 takes 3.10–3.14,
     Django 6.2 takes 3.12–3.14 — so the 6.2 upgrade requires no Python change at all. The
     `python:3.13-slim` base image in the `Dockerfile` is the **single** place the version lives;
     `runtime.txt` is deleted rather than updated (1.5, 7.9), per [ADR-015](decisions.md) rule 1.
  3. **Upgrade directly, 3.2 → 5.2.** No staged stop at 4.2 LTS.
  4. **Sequenced after Epic 2 and before Epic 3**, as its own epic (Epic 19).
  5. **`psycopg[binary]` 3** replaces `psycopg2-binary` (closes 9.5) — natively supported by Django
     since 4.2, and a new build is the cheapest moment to switch drivers.
  6. **The dependency set is defined by a rule, not by pins in this ADR** (9.6): each package targets
     the latest release compatible with Django 5.2 and Python 3.13 *at the time the lock file is
     generated* (9.8). Confirmed available and compatible on 2026-08-10 — `whitenoise` 6.12.0,
     `django-environ` 0.14.0, `Pillow` 12.3.0. Four entries are **removed outright**:
     - `asgiref`, `sqlparse` — Django's own transitive dependencies; they belong in the lock file, not
       in a hand-maintained list where they can contradict Django's requirements.
     - `pytz` — Django removed pytz support in 5.0; the stdlib `zoneinfo` replaces it, and no app code
       imports it.
     - `environ==1.0` — an unrelated PyPI package whose top-level `environ` module collides with the
       one `django-environ` provides. Almost certainly an install slip, and a live hazard.
     - `dj-database-url` — imported nowhere in app code, and `django-environ`'s `env.db()` already
       parses `DATABASE_URL`, which [ADR-015](decisions.md) rule 2 names as the database contract.
  7. **`django-mathfilters` is dropped** (closes 9.7). Its latest release is 1.0.0 from February 2020
     and its classifiers stop at Django 3.x — it is a hard blocker for this upgrade, not a preference.
     It is loaded in `control/templates/base_recipe.html` and `products.html`, both of which do
     cost/margin arithmetic **in the template** — exactly what [ADR-018](decisions.md) ruled wrong. The
     values come from the view (and later the service layer) instead.
- **Alternatives considered:**
  - **Django 6.1, the current stable** — rejected. It has a *shorter* support window than the older
     LTS (December 2027 vs. April 2028) and puts a solo developer on the 8-month feature-release
     treadmill. Django 6.0 dropping out of mainstream support the week this was decided is the
     demonstration, not a hypothetical.
  - **Staged 3.2 → 4.2 LTS → 5.2** — the conventional advice, and rejected on two project-specific
    grounds. First, staging exists so a test suite can catch each release's removals, and every
    `tests.py` in this repo is an empty stub — staging without tests means running the app manually
    three times instead of once, and getting three chances to be wrong. Second, and more decisive:
    **most of the code that would break is code already scheduled for deletion** — the inline
    `float()` costing ([ADR-018](decisions.md)), the models Epic 3 restructures for tenancy, the
    templates Epic 5 rewrites. Migrating it carefully through 4.2 preserves a corpse.
  - **Python 3.12** (the previous candidate) — rejected; security-fixes-only since October 2025.
  - **Python 3.14** (the newest) — rejected as the target, not on stability but on span: it needs
    Django 5.2.8+, and 3.13 already covers the entire path through 6.2 with mature wheels everywhere.
    Re-evaluate it at the 6.2 LTS hop, as one upgrade event rather than two.
  - **Keeping `psycopg2-binary`** — rejected; psycopg2 is in maintenance-only upstream, and deferring
    the swap means doing it later against a schema that by then has real tenant data in it.
  - **Pinning exact patch versions in this ADR** — rejected; they would be stale within weeks and this
    log is append-only. The ADR fixes the *constraint*; the lock file (9.8) fixes the versions.
- **Consequences:**
  - **This creates a new epic — Epic 19, `stack-runtime-upgrade`.** The suggested execution order in
    [roadmap.md](roadmap.md) already said "then the upgrade itself" at step 4, but no epic held that
    work; Epic 9 is decisions-only and Epic 1 is repository hygiene. It is added rather than smuggled
    into Epic 1, so the upgrade has a branch and a PR of its own.
  - **It must run before Epic 3.** Epic 3 writes a large migration set; written against 3.2 and
    upgraded afterwards, every one of them needs re-verifying on 5.2.
  - **The `USE_TZ` default flip in Django 5.0 is a non-event here** — `bakery/settings/base.py`
    already sets `USE_TZ = True` and `TIME_ZONE = 'UTC'` explicitly. Verified and recorded so it is
    not re-investigated when the dated-price and receipt-date tables from
    [ADR-018](decisions.md)/[ADR-017](decisions.md) are built.
  - **The safeguard that replaces the staged upgrade is a deprecation sweep on 3.2 first** — run the
    app's checks under `-Wall` and clear every `RemovedInDjango*Warning` *before* jumping (19.1).
    That is what a staged upgrade would have surfaced; it is not equivalent to having tests, and
    saying so plainly is part of accepting this route.
  - **Verification is a manual pass over every screen**, because there are no tests until Epic 6.
    This is the largest accepted risk in the epic and the reason it is sequenced as its own step
    rather than folded into another epic's PR.
  - Epic 1's minimal CI (1.11) must run on Python 3.13 — if Epic 1 lands first, its workflow is
    updated by 19.9 rather than written twice.
  - `requirements.txt` drops from twelve entries to roughly six, and the UTF-8 re-encoding (1.4)
    happens in the same pass since the file is being rewritten anyway.
  - **April 2028 is now a real deadline.** 5.2's extended support ends then, so the 6.2 LTS hop is
    scheduled work, not an option — diary it for H2 2027. Django 6.x also drops Python 3.10/3.11,
    which is irrelevant at 3.13 but noted so that any future "pin Python back for package X" is
    recognised as closing the door on 6.2.
  - Closes five `Open` rows in [tech_stack.md](tech_stack.md) and leaves the WSGI/ASGI row (9.4)
    deliberately open — see the note on that row; it waits on 9.20's re-scope of Epic 16.

## ADR-026: Pin PostgreSQL 17 across every environment

- **Date:** 2026-08-10
- **Status:** Accepted
- **Context:** Task 9.3. [ADR-015](decisions.md) rule 6 requires core PostgreSQL at a version every
  candidate host actually offers, so a logical dump restores cleanly elsewhere. Today the version is
  pinned nowhere: `docker-compose.yaml` has **no Postgres service at all** (Postgres runs as a
  separate hand-managed container on the home server), so nothing in the repository records which
  major version the app is developed or deployed against.
- **Decision:** **PostgreSQL 17**, pinned identically in every environment — an explicit `postgres:17`
  service in the local `docker-compose.yaml`, and Postgres 17 on Railway, which offers it directly
  (and a version-selectable template if a specific major is ever needed). The local and production
  **major versions must match**; a major bump is a deliberate change accompanied by a restore test
  (3.47), never drift.
- **Alternatives considered:** **Tracking `postgres:latest`** — rejected; it turns a major version
  bump into something that happens on a `docker pull`, against a production database that cannot
  follow. **Staying on 15 or 16 for conservatism** — rejected; no feature need argues for it and it
  shortens the runway for no benefit (17 is supported into late 2029). **Leaving it unpinned, as
  today** — rejected; it is the state [ADR-015](decisions.md) rule 6 exists to prevent, and it makes
  the dump/restore drill (3.48) untrustworthy since `pg_dump`'s version has to match the server's.
- **Consequences:**
  - The local `docker-compose.yaml` needs a Postgres service it does not currently have (19.10).
    It is broken as written anyway — the `web` service joins a network named `my_network` while the
    file defines `bakery_simple` — so this is a fix, not new scope. [ADR-014](decisions.md) makes that
    file the only integration-test environment, so it has to actually run.
  - Feeds 3.45 (core-PostgreSQL-only constraint) and the portability work in 3.44 and 3.46–3.48:
    `pg_dump`/`pg_restore` must match the server major, which is only checkable once a major is named.
  - The pilot's existing data has to be dumped from whatever version the home server currently runs
    and restored into 17 during Epic 12 — a cross-major restore, which is precisely the case
    [ADR-015](decisions.md) rule 5 and the 3.46/3.47 traps are about.

## ADR-027: <next decision goes here>

- **Date:**
- **Status:** Proposed
- **Context:**
- **Decision:**
- **Alternatives considered:**
- **Consequences:**
