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
- **Status:** Accepted — re-confirmed against the plain-query alternative, and given its cloud,
  region, data-handover, trigger and cost model, by [ADR-036](decisions.md) (9.20)
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
- **Status:** Accepted — the supplier-name uniqueness clause is **amended by
  [ADR-027](decisions.md)**: normalized (case-insensitive) uniqueness, declined below purely because
  it "needs a normalized column or a functional index", is adopted after all, since Django 4.0's
  functional unique constraints remove that cost. Every other clause stands unchanged
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

## ADR-027: Adopt the platform capabilities the Django 5.2 / Python 3.13 / PostgreSQL 17 upgrade unlocks (amends ADR-019)

- **Date:** 2026-08-11
- **Status:** Accepted — amends [ADR-019](decisions.md)'s supplier-name uniqueness clause
- **Context:** [ADR-025](decisions.md) and [ADR-026](decisions.md) settled *which* versions to move to.
  This entry answers the follow-up: the app jumps across four Django feature releases at once, and
  several of them provide, as framework or database features, things this project had planned to
  hand-build — or had **deferred specifically because hand-building them was too expensive**. Decided
  now rather than during implementation, because three of these change how Epics 2, 3 and 5 are built
  rather than being optimisations applied afterwards. Release notes were verified 2026-08-11 against
  the Django 4.0/4.1/4.2/5.0/5.1 release notes and the PostgreSQL 17 release notes.
- **Decision:** Adopt the following. Each has a task in the backlog; nothing here is aspirational.

  **Access control**
  1. **`LoginRequiredMiddleware` (Django 5.1) becomes the default posture**, with `@login_not_required`
     on the deliberate exceptions (the `core` cover page, the login view). Authentication stops being
     something each view opts into and becomes something a view must explicitly opt out of. This
     changes the shape of 2.6/2.7 — the mixin remains correct but is no longer the mechanism.
  2. **`SECRET_KEY_FALLBACKS` (Django 4.1)** makes secret-key rotation possible without invalidating
     every active session, which is what turns 8.6's runbook into a procedure someone would actually
     run.

  **Data correctness**
  3. **Supplier-name uniqueness becomes case-insensitive** — `UniqueConstraint(Lower("name"),
     "bakery", condition=<not archived>)`. This **amends [ADR-019](decisions.md)**, which declined
     normalized uniqueness with a single stated reason: that it "needs a normalized column or a
     functional index". Functional unique constraints (Django 4.0) make it one declaration with no
     extra column and no hand-written SQL, so the only argument against it no longer exists. The
     consequence ADR-019 was protecting against — a duplicate silently splitting one supplier's price
     history across two rows — is unchanged and is the reason to take this now.
  4. **Database constraints are validated in the model/form layer** via `Model.full_clean()` /
     `validate_constraints()` (Django 4.1), with `violation_error_message` supplying human wording.
     Without this, every rule Epic 3 adds — per-tenant supplier uniqueness, [ADR-022](decisions.md)'s
     cycle rejection — reaches the user as an `IntegrityError` 500 instead of a field error.
  5. **`db_comment` / `db_table_comment` (Django 4.2) document the schema in the database itself.**
     The redesigned schema carries meaning that is not visible from a column name — money stored net
     of VAT, quantities in canonical kg/l/each, `purchase_price` versus derived cost. Held in the
     database, that explanation is visible from `psql` and from the [ADR-019](decisions.md) admin
     support surface, and cannot drift away from the table it describes.
  6. **`db_default` (Django 5.0)** for the non-null columns Epic 3 adds to populated tables, removing
     a separate data-migration step per column.

  **Interface**
  7. **Django's own accessible form rendering** — `as_field_group()` (5.0) over the div-based
     templates (4.1) — is the default rendering path in the Epic 5 rewrite. It emits real label
     association, `aria-describedby`, `aria-invalid`, and `<fieldset>`/`<legend>` grouping, which is a
     material share of [ADR-021](decisions.md)'s WCAG 2.2 Level A target arriving from the framework
     instead of from hand-written markup.
  8. **`{% querystring %}` (Django 5.1)** for filter-preserving pagination in 5.9's search/filter work.

  **Operations**
  9. **Native psycopg connection pooling (Django 5.1)**, configured in `DATABASES["OPTIONS"]["pool"]`,
     together with `CONN_HEALTH_CHECKS` (4.1). This **closes the connection-pooling half of 9.18**: the
     question was "`CONN_MAX_AGE` tuning or a separate pooler such as PgBouncer", and the answer is now
     neither — it is in-process, needs no additional service, and no additional service means one less
     thing to run, monitor and keep patched.
  10. **PostgreSQL 17's `pg_stat_statements` improvements** (split shared/local block I/O timing,
      `stats_since`) are the measurement basis for [ADR-021](decisions.md)'s p95 budgets, which nothing
      currently measures (3.43, 7.1).
  11. **`COPY ... ON_ERROR ignore` (PostgreSQL 17)** for 3.54's price backfill — a per-row human
      judgement exercise, where one bad row aborting the whole import is a genuine obstacle.
  12. **`pg_restore --transaction-size` and parallel large-object restore (PostgreSQL 17)** in the
      3.48 restore drill, whose value depends entirely on it being fast enough to keep running weekly.

  **Also required, not optional:** `STATICFILES_STORAGE` and `DEFAULT_FILE_STORAGE` were deprecated in
  4.2 and **removed in 5.1**. `settings/base.py` currently sets `STATICFILES_STORAGE` for whitenoise,
  so the `STORAGES` dict is a **prerequisite of the upgrade itself** (19.14), not an Epic 13 nicety.
  Its two keys — `"default"` and `"staticfiles"` — happen to be exactly [ADR-005](decisions.md)'s split
  of R2 for media and whitenoise for static (13.11).

- **Alternatives considered:**
  - **Adopt nothing and keep the planned hand-built equivalents** — rejected. For items 1, 3, 4 and 7
    the hand-built version is strictly worse code that must then be maintained, and item 3 was
    *already* judged worth having and rejected only on cost.
  - **Adopt everything the four releases offer** — rejected; the list below was declined on merit.
  - **`GeneratedField` (Django 5.0) for cost and margin** — the most attractive-looking option here and
    **rejected on a technical constraint, not on preference.** It promises database-computed values
    that cannot drift from their inputs, which reads as a direct answer to
    [ADR-018](decisions.md)'s "derived, never persisted". It cannot work: PostgreSQL supports only
    `STORED` generated columns through version 17, and a generated expression must be immutable and
    reference **only columns of the same row** — no joins, no subqueries. Every derivation in this
    schema crosses rows: cost per canonical unit needs the unit-conversion table, gross price needs the
    dated VAT table, product cost recurses through ingredient lines ([ADR-022](decisions.md)). Recorded
    explicitly so it is not re-proposed by the next person who reads the 5.0 release notes.
  - **PostgreSQL 17 incremental backup (`pg_basebackup --incremental`)** — rejected as unusable here;
    it needs filesystem access to the data directory and `summarize_wal` on the server, which a managed
    Railway database does not offer. It does **not** close [ADR-013](decisions.md)'s PITR gap, and 9.16
    is unaffected. The portable logical dump ([ADR-015](decisions.md) rule 5) remains the mechanism.
  - **Redis cache backend (Django 4.0)** — **not decided either way.** The caching row stays `Open` in
    9.18. It is deliberately recorded as undecided rather than rejected: the correct trigger is
    [ADR-023](decisions.md)'s overview dashboard being measured against the p95 < 2 s budget, and if it
    misses, Redis is a reasonable answer whose hosting cost is minor next to a dashboard nobody waits
    for. Decide it on 7.1's measurements, not in advance.
  - **Async views / async ORM (Django 4.1)** — rejected; nothing in the decided scope needs them, which
    also reinforces leaving 9.4 (WSGI/ASGI) pointed at gunicorn.
  - **`CompositePrimaryKey` (Django 5.2) for the membership record** — rejected despite being the
    theoretically correct shape for user × bakery: it cannot be the target of a ForeignKey and has
    limited admin support. A surrogate key plus `UniqueConstraint(user, bakery)` costs nothing and
    stays boring (3.58).
- **Consequences:**
  - **Three of these change how downstream epics are built, not what happens after them** — item 1
    reshapes 2.6/2.7, item 3 adds a constraint to Epic 3's schema work, item 7 sets Epic 5's default
    rendering path. They are only available to those epics **if Epic 19 lands first**, which is an
    independent argument for the sequencing [ADR-025](decisions.md) already chose.
  - **Amends [ADR-019](decisions.md)** on supplier-name uniqueness only. Everything else in ADR-019 —
    the soft-delete scope, per-tenant (not global) uniqueness, live-rows-only enforcement, the two
    administration surfaces — stands unchanged.
  - **Closes the connection-pooling sub-question of 9.18.** The ingredient-line, categories, and
    caching sub-questions remain open.
  - **`STORAGES` is required by the upgrade** (19.14), though the failure is quiet rather than loud:
    a removed setting is ignored, not rejected, so the site keeps working while whitenoise's
    compression and cache-busting silently stop. **The louder consequence lands in Epic 5.** Every
    template in this repo hardcodes `/static/...` — there is no `{% static %}` anywhere in the
    project's own templates — so manifest hashing has never actually done anything here. When 5.3
    switches to `{% static %}`, `ManifestStaticFilesStorage` starts raising `ValueError` at render
    time for any referenced file missing from the manifest, turning a missing asset from a silent 404
    into a 500. Mitigated by sequencing 5.3 with 1.3 (the committed `staticfiles/` output is removed,
    so a stale manifest can't be the source) and by 1.13 running `collectstatic` in CI.
  - Adds 13 tasks across Epics 2, 3, 5, 7, 13 and 19. None is large; several *reduce* the work already
    scoped, since the framework now supplies what those tasks were going to build by hand.
  - **Item 4 has a testing consequence:** validating constraints in `full_clean()` means the error
    paths are now reachable from form tests rather than only from database-level integration tests —
    worth using when 6.x writes the first tests, since they are cheap tests of expensive rules.

## ADR-028: Backend architecture — settings layout, a batch-first service layer, no API, permissions on Django's own rails, no cache, and Brevo over SMTP

- **Date:** 2026-08-13
- **Status:** Accepted — completes [ADR-020](decisions.md)/[ADR-027](decisions.md) on auth, closes the
  caching half of 9.18
- **Context:** The `Backend architecture` table in [tech_stack.md](tech_stack.md) was the last block of
  `Open` rows standing between the discovery epics and Epic 4's implementation, and five of the six
  rows blocked at least one task apiece (1.5, 4.1, 4.5, 4.15, 5.19). They are decided together because
  they are not independent: the service layer is where caching would attach, the permission mechanism
  determines whether the service layer takes a user or a membership, and adopting Django's built-in
  auth views is what makes email a first-release requirement rather than a feature-epic one. Provider
  facts were verified 2026-08-13; Django-version-specific claims rest on the 5.2 baseline fixed by
  [ADR-025](decisions.md).
- **Decision:**

  **1. Settings layout (9.9) — `base.py` + `local.py` + `test.py`, no `production.py`.**
  `base.py` *is* the production configuration rather than a shared parent that nothing runs: all
  config from the environment ([ADR-015](decisions.md) rule 2), production-safe defaults, and **no
  default at all** for `SECRET_KEY`, `ALLOWED_HOSTS` and `DEBUG` — a missing variable raises
  `ImproperlyConfigured` at boot. `local.py` and `test.py` are the only overlays and each opts *into*
  the unsafe or convenient behaviour. The property being bought is that **the accident lands on the
  safe side**: `manage.py` and the `Dockerfile` both default to `base`, so a forgotten
  `DJANGO_SETTINGS_MODULE` yields production settings. Today it yields the opposite — `base.py` ships
  a hardcoded `SECRET_KEY`, `DEBUG = True`, live database credentials, and `heroku.py:11` defaults
  `DEBUG` to `True` in the *production* module.

  **2. Business logic location (9.10) — `control/services/`, plain functions, batch-first.**
  Module-level functions grouped by concern (`costing`, `pricing`, `receipts`) taking explicit
  arguments and returning frozen dataclasses that carry amount, canonical unit, provenance and
  as-of date together. **The batch entrypoint is the primary API**; single-object costing is a thin
  wrapper over it. Models keep fields, constraints and managers (including
  [ADR-019](decisions.md)'s combined tenant + archived base manager) and lose costing entirely — the
  `@property` methods are deleted, not left as delegators.

  **3. API layer (9.11) — none, and no framework pre-selected.** Machine-readable endpoints (the
  health check, any future insights callback) are plain Django views returning `JsonResponse`.
  Revisit trigger, any one of: a second non-first-party consumer appears; a native app or SPA client
  is committed to (which would reverse [ADR-021](decisions.md)'s device matrix); or machine endpoints
  exceed roughly six.

  **4. Auth/permissions (9.12) — Django's auth views, capabilities on Django's permission API.**
  `accounts/views.py` and `accounts/urls.py` are deleted outright. Capabilities are Django permission
  codenames; middleware resolves the active bakery and membership onto the request, and a **custom
  authentication backend** implements `has_perm()` by mapping the membership role to a static
  capability set. Everything downstream stays stock Django — `PermissionRequiredMixin`,
  `@permission_required`, `{% if perms.control.edit_recipes %}`.

  **5. Caching (9.18, caching half) — none in the first release.** Query design is the performance
  lever: the batch costing service, `select_related`/`prefetch_related`, and
  [ADR-027](decisions.md)'s connection pool. Escalation ladder, in order, only once 7.20 measures the
  dashboard over ADR-021's p95 < 2 s on realistic pilot data: (a) fix the queries, (b) per-view cache
  with a short TTL keyed by a per-tenant version stamp, (c) a Redis backend **only** if step (b)
  needs cross-worker coherence. The batch API takes the version stamp in its signature from day one.

  **6. Email (9.22) — Brevo, over SMTP.** Django's built-in `smtp.EmailBackend` with host, port, user
  and password from environment variables; console backend in `local.py`, locmem in `test.py`. No
  dependency, and the provider stays swappable by configuration alone.

- **Alternatives considered:**
  - **Four settings modules including `production.py`** (the standing candidate) — rejected. It makes
    `base.py` a module that is never loaded and therefore never tested, and requires
    `DJANGO_SETTINGS_MODULE` to be right in three places, where being wrong silently loads that
    untested module. **A single env-var-driven `settings.py`** was also rejected: debug-toolbar apps
    and test-only settings become `if` branches inside settings, which is logic in the one file that
    is hardest to test.
  - **Fat models, corrected in place** — the conventional Django answer, and rejected on a structural
    point rather than taste. [ADR-023](decisions.md)'s dashboard costs every product in one request;
    a per-instance `@property` that recurses through [ADR-022](decisions.md)'s nested base recipes
    issues queries per node and cannot memoise across the walk, so meeting
    [ADR-021](decisions.md)'s budget would mean growing a second, parallel batch path — which is the
    service layer, arrived at by accident. Separately, [ADR-018](decisions.md)'s provenance means the
    answer is a value object, which a property returning a `Decimal` cannot express.
  - **A standalone ORM-decoupled `domain/` package with repositories** — rejected as overhead that
    buys database/framework portability nobody asked for. [ADR-015](decisions.md) requires *host*
    portability, which Docker plus `DATABASE_URL` already delivers.
  - **Adopt DRF now, read-only** — rejected. It would add a second authentication and permission
    surface to keep synchronised with [ADR-020](decisions.md)'s memberships and a second
    tenant-scoping path to test for cross-tenant leaks ([ADR-008](decisions.md)), for a consumer that
    does not exist. **Pre-selecting a framework for later** (django-ninja was the candidate) was also
    rejected: [ADR-025](decisions.md) had just demonstrated the failure mode when the Python 3.12
    candidate aged out before implementation. Name the trigger, not the tool.
  - **`django-rules` for permissions** — a genuinely good fit, rejected on proportion: it plugs into
    the same `has_perm` integration points the custom backend does, so it buys predicate composition
    and object-level ergonomics against a role matrix that is three static roles. One more dependency
    to carry across the 5.2 → 6.2 hop for that is not worth it. Reconsider if per-object rules
    ("can edit *this* recipe") multiply.
  - **A hand-rolled capability module with its own mixin** — rejected. Templates would lose
    `{% if perms %}` and need a custom tag, Django admin keeps its own permission system regardless,
    and the result is two vocabularies for "is this allowed" — which is precisely how the ad hoc
    template checks in the current code came about.
  - **Keeping a thin `LoginView` subclass** — rejected for now. The one real motivation is choosing a
    landing tenant for a user holding several memberships, which does not exist while
    [ADR-016](decisions.md) has one pilot bakery. Re-add the subclass when the second membership does.
  - **Provision Redis now** — rejected. The stated cost is ~$2–3/mo, which is not the real cost; the
    real cost is that the full invalidation matrix must be correct on day one across goods receipts,
    recipe edits, base-recipe edits cascading to every product containing them, VAT-rate rows and
    `ProductPrice` rows. **`LocMemCache` now** was rejected separately: it is per-gunicorn-worker, so
    two users can be served figures cached at different moments and a recipe edit is visible to
    neither — acceptable for a blog, not for the number a product is priced against.
  - **Resend for email** — the best developer experience of the four evaluated, and **rejected on a
    verified fact**: EU data residency is gated to Pro at $20–35/mo, with account data and logs
    remaining in the US on the free tier. That is over three times the entire ~$6/mo infrastructure
    budget, spent to meet a constraint Brevo, Mailjet and Scaleway TEM all meet for free.
    **Mailjet** (EU DCs, ISO 27701, 6,000/mo free) and **Scaleway TEM** (French, EU-only, €0.25/1,000)
    were both viable; Brevo won on EU ownership *and* EU hosting aligning, a DPA included by default,
    and the largest free headroom. **`django-anymail`** was rejected for now — bounce webhooks and
    delivery analytics are worth having at volume, not at under 100 emails a month; it is the
    escalation path if deliverability becomes a question.
- **Consequences:**
  - **Unblocks five tasks and cancels one.** 1.5 is unblocked but **rescoped** — three modules, not
    four. 4.1, 4.5 and 5.19 are unblocked. **4.15 is cancelled**, not deferred.
  - **4.5 is smaller and safer than recorded.** `bakery/urls.py` includes `django.contrib.auth.urls`
    but **never includes `accounts.urls`**, so `accounts.views.user_login` is unreachable — it even
    renders `'login.html'`, a path that does not exist (the real template is
    `accounts/templates/registration/login.html`, already serving Django's `LoginView`). The
    password-logging `print()` at `accounts/views.py:20-21` is therefore **dead code, not a live
    leak**, which lowers the severity recorded on 2.10 and removes 4.5's stated dependency on it.
    4.5 becomes a pure deletion with no behaviour to port.
  - **Email is now a first-release blocker, for a reason ADR-023 did not have.** Adopting Django's
    built-in auth views adopts its password-reset flow, which is email-only — so email gates the
    recovery path for every user, not just the invitation flow.
  - **Two endpoints are carved out of [ADR-021](decisions.md)'s p95 < 500 ms page budget**: the
    invitation POST and the password-reset POST send SMTP inline. There is no task queue, and
    decision 5 above declined Redis, so introducing Celery for a few dozen emails a month would drag
    it straight back in. The carve-out is deliberate and documented (10.18) rather than engineered
    around.
  - **A permission-cache watch item.** Django caches permissions on the user object, so the cache
    must be invalidated whenever the active tenant changes, or a user holding two memberships carries
    bakery A's capabilities into bakery B (2.21). This is a cross-tenant leak of exactly the kind
    [ADR-008](decisions.md) requires dedicated tests for.
  - **Two gaps surfaced that no epic covered**: brute-force protection on login (2.22) and
    GDPR-safe failed-login auditing that records the attempt without the credentials (2.23).
  - Adds 11 tasks across Epics 2, 4, 5, 7, 10 and 11, and leaves the ingredient-line and categories
    halves of 9.18 open, along with 9.21's traceability entities.

## ADR-029: Dependency management — `uv pip compile` over a three-file `requirements/` split, with a stated owner per direct dependency

- **Date:** 2026-08-16
- **Status:** Accepted — closes the last two `Open` rows in [tech_stack.md](tech_stack.md)'s
  `Dependencies` table (9.8); amends [ADR-025](decisions.md)'s package list on one entry (`Pillow`)
- **Context:** [ADR-025](decisions.md) decided *which* packages the app depends on and fixed the
  version **rule** — latest release compatible with Django 5.2 on Python 3.13 — while explicitly
  refusing to pin versions in an append-only log: *"The ADR fixes the constraint; the lock file (9.8)
  fixes the versions."* That left the mechanism undecided, and 19.12 `Blocked` behind it as the only
  blocked task in Epic 19 and a first-release milestone item. The two rows are decided together
  because they are one decision, not two: "every dependency has a named owner and a stated purpose"
  is a claim that has to live *somewhere*, and where it lives is a property of the file layout. The
  hygiene row's `Current` text ("unreviewed") is also already stale — [ADR-025](decisions.md)
  performed exactly that review and removed six of twelve entries with a named reason each. What
  remains is not an audit but a rule that keeps the audit true.
- **Decision:**

  **1. Tool — `uv`, in its `pip compile` mode.** `uv pip compile` reads hand-edited `.in` files and
  emits fully-pinned `.txt` files in ordinary requirements format. Deliberately **not** `uv sync` /
  `pyproject.toml` mode: the requirements-file format is what the `Dockerfile`, Railway, and every
  fallback host in [ADR-013](decisions.md) already consume, so this adds determinism without
  changing the install path anywhere. `uv` is a build-time tool — it is installed in the
  `Dockerfile` and in CI at a **pinned** version, and never appears in the application's dependency
  set.

  **2. Layout — three sources, three locks.**

  | File | Hand-edited? | Contents |
  |---|---|---|
  | `requirements/base.in` | yes | Runtime dependencies shared by every environment |
  | `requirements/dev.in` | yes | `-r base.in` plus tooling: linter, test runner, anything never installed in the image |
  | `requirements/prod.in` | yes | `-r base.in` plus production-only additions |
  | `requirements/*.txt` | **no — generated** | Fully pinned, hashed output of `uv pip compile` |

  The root `requirements.txt` is deleted once the split lands. `prod.in` starts as nothing but
  `-r base.in`, and that is deliberate: the value is a **named artifact the `Dockerfile` points at**
  that structurally cannot pick up dev tooling, not extra packages. It has a known future occupant
  (an error-tracking SDK, 9.15).

  **3. Determinism — hashes, a pinned resolution target, and a shared constraint.** Compile with
  `--generate-hashes`; the `Dockerfile` installs with `--require-hashes`, so a re-uploaded or
  substituted artifact fails the build instead of shipping. Compile with `--python-version 3.13` so
  resolution matches the image regardless of the developer's local interpreter. Compile `base` first
  and the other two against it with `-c requirements/base.txt`, so a package present in more than one
  file cannot resolve to two different versions.

  **4. Hygiene rule — the `.in` file *is* the register.** Every line in a `.in` file carries a
  trailing comment naming its purpose and the epic or task that owns it; a dependency with no such
  comment is removed at the next recompile rather than researched later. Transitive dependencies
  exist **only** in the generated `.txt` — this is what [ADR-025](decisions.md) was reaching for when
  it moved `asgiref` and `sqlparse` out of the hand-written file. The `.txt` files carry a
  generated-by header and are never hand-edited; the fix for a wrong pin is a recompile, never a
  keystroke.

  **5. Refresh trigger.** Recompile when a `.in` changes, when a security advisory names a pinned
  package, and otherwise on a monthly pass. [ADR-025](decisions.md)'s "latest compatible at lock
  time" rule is evaluated at each recompile, not frozen at the first one.

  **6. `Pillow` is removed from the dependency set until Epic 13** (amends
  [ADR-025](decisions.md) clause 6, which kept and re-pinned it). Verified 2026-08-16: there is no
  `ImageField` — and no `Pillow` import — anywhere in the codebase, because the fields that need it
  do not exist yet (13.4, 13.5). It is the first thing rule 4 catches, and applying the rule to the
  package that prompted it is the point. It returns in 13.1, alongside `django-storages[s3]` and
  `boto3`, with an owner comment.
- **Alternatives considered:**
  - **`pip-tools`** — the candidate [tech_stack.md](tech_stack.md) named, and the closest call here.
    Identical file layout and near-identical output, so nothing about this ADR's *structure* depends
    on the choice. Rejected on trajectory rather than capability: `uv` resolves and installs an order
    of magnitude faster (it is billed per-second Railway build time and CI minutes on a ~$6/mo
    budget), covers venv creation and installation with the same binary, and is where the ecosystem's
    active development has moved. The migration cost in the other direction is one command line, so
    this is a cheap bet either way.
  - **Poetry or PDM** — rejected. Both move dependency declaration into `pyproject.toml` with a
    bespoke lock format, which means changing the install path in the `Dockerfile`, in CI, and on the
    host, and abandoning the `requirements/` split this row specifies. That is a project-layout
    migration bolted onto an epic that is already a framework upgrade with no test suite
    ([ADR-025](decisions.md)) — the wrong thing to stack on top of 19.4.
  - **`pip freeze > requirements.txt`** — rejected. It produces pins with no record of *which*
    packages were actually asked for, so the direct/transitive distinction is lost and rule 4 becomes
    unenforceable. It is roughly the state the current twelve-line file is already in, which is how
    `environ==1.0` and `dj-database-url` survived in it unnoticed.
  - **Skipping `--generate-hashes`** — considered seriously; hashes add friction to ad hoc
    `pip install` in a local venv. Kept because "deterministic builds" is the row's stated goal and
    pins alone do not deliver it against a mutated artifact, and because `uv pip compile` makes
    regeneration fast enough that the friction resolves into one command.
  - **Leaving both rows open until the quality-tooling row (9.17) decides what goes in `dev.in`** —
    rejected. The *contents* of `dev.in` depend on 9.17; the layout, the lock workflow and the
    hygiene rule do not. An initially thin `dev.in` is the expected state, not a symptom.
- **Consequences:**
  - **Unblocks 19.12**, the last `Blocked` task in Epic 19 and a first-release milestone item, and
    closes 9.8 — leaving Epic 9's remaining open rows as 9.4, 9.13–9.17, 9.18 (two halves), 9.19,
    9.20 and 9.21.
  - **The `Dockerfile` changes twice in Epic 19**: 19.3 sets `python:3.13-slim`, and 19.16 switches
    the install to a pinned `uv` against `requirements/prod.txt` with `--require-hashes`. Both touch
    the same lines, so they belong in one pass.
  - **19.2 now removes seven entries, not six** — `Pillow` joins `asgiref`, `sqlparse`, `pytz`,
    `environ`, `dj-database-url` and `django-mathfilters`. `base.in` ends at **five** direct
    dependencies: Django, `psycopg[binary]`, `whitenoise`, `django-environ`, `gunicorn`.
  - **CI gains a drift check** (19.17): recompile and fail if the `.txt` files differ from what the
    `.in` files produce. Without it the generated files are only as current as the last person who
    remembered, which is the failure mode rule 4 exists to prevent.
  - **A monthly recompile is a standing chore with no owner but the solo developer.** Named here
    rather than pretended away; it folds into the 9.14/9.15 monitoring work if that produces a
    scheduled job.
  - The hygiene row's promise is now falsifiable: any `.in` line without an owner comment is a
    visible defect in review, rather than a claim in a planning document.

## ADR-030: Frontend stack — a shared template base, Bootstrap 5.3, HTMX, and deliberately no Node build step

- **Date:** 2026-08-16
- **Status:** Accepted — closes the `Frontend` table in [tech_stack.md](tech_stack.md) (9.13) and the
  template half of 9.17; **rejects** that file's own Vite candidate
- **Context:** Task 9.13, blocking 5.4, 5.6 and 5.7. Unlike the earlier stack rows, this one is
  decided against a frontend that was measured rather than assumed (2026-08-16):

  | Measured | Finding |
  |---|---|
  | Templates | 32 files, 4,277 lines, **zero `{% extends %}` and zero `{% include %}`** — 31 carry a full `<!DOCTYPE>` boilerplate and the navbar is duplicated 32 times |
  | Static references | **Zero `{% static %}`**; 23 templates hardcode `/static/...` |
  | Bootstrap | **5.0.0**, vendored (released May 2021); current is 5.3.x — the *same major* |
  | Custom JavaScript | 7 files, **all 0 bytes** |
  | Custom CSS | 16 files, 922 lines total; four are byte-identical 19-line files |
  | Node tooling | none — no `package.json`, no Node in the `Dockerfile` |

  The last two rows are what move this decision. [tech_stack.md](tech_stack.md) described the current
  state as "plain JS per page, several empty JS files"; the interactivity layer is not thin, it is
  **absent**. Much of the surrounding shape was also already fixed elsewhere:
  [ADR-021](decisions.md) set WCAG 2.2 A, an evergreen browser matrix, one responsive UI and an
  `en-IE`/EUR translation-ready target; [ADR-027](decisions.md) put form accessibility on Django's
  own `as_field_group()` and pagination on `{% querystring %}`; [ADR-024](decisions.md) made
  search/filter (5.9) and supplier price comparison (5.21) **Musts**; and [ADR-013](decisions.md)
  fixed the budget at one solo developer and ~$6/mo.
- **Decision:**

  **1. Templating (row 1) — shared `base.html` plus `{% include %}` partials.** Partials live in
  `<app>/templates/partials/`. No competing option was seriously in play; the measurement above is
  the argument. `django-template-partials` is **not** adopted — a dependency for roughly four
  fragments — with a revisit trigger if HTMX fragment templates proliferate past a handful.

  **2. CSS framework (row 2) — stay on Bootstrap, upgrade 5.0.0 → 5.3.x.** Same major version, so
  the classes across 32 templates stay largely valid: this is an upgrade, not a restyle. It buys four
  years of fixes and component semantics that serve the WCAG 2.2 A target, and it keeps Epic 5's
  effort on structure — `base.html`, partials, `{% static %}` — rather than on appearance.

  **3. Asset pipeline (row 3) — none. This rejects the Vite candidate recorded in
  [tech_stack.md](tech_stack.md).** Vite would add Node to the `Dockerfile`, a `package.json` and a
  second lockfile immediately after [ADR-029](decisions.md) standardized the Python one, and extra CI
  steps — in order to bundle **zero bytes of JavaScript** and 922 lines of CSS, while duplicating
  cache-busting and compression that 19.14's whitenoise `CompressedManifestStaticFilesStorage`
  already provides. Instead: consolidate the 16 CSS files into a small set, use native CSS custom
  properties and nesting (safe on [ADR-021](decisions.md)'s evergreen matrix), and let whitenoise do
  the hashing. **Revisit trigger:** custom JavaScript passing roughly a few hundred lines, or a need
  to customize Bootstrap at the SCSS-variable level rather than by overriding CSS.

  **4. Interactivity (row 4) — HTMX, vendored at a pinned version, plus small vanilla JS modules.**
  A single ~14KB script with no bundler, so it composes with clause 3. The server returns HTML
  fragments — exactly what [ADR-028](decisions.md) assumed when it rejected an API layer. It is built
  as **progressive enhancement**: every form and link must work with JavaScript disabled, which
  WCAG 2.2 A requires regardless. Alpine.js is rejected as a third overlapping layer — Bootstrap 5's
  JS bundle already ships dropdowns, modals, toasts and collapse.

  **5. SPA (row 5) — no, and this is a ratification rather than a new decision.**
  [ADR-028](decisions.md) rejected an API layer and [ADR-021](decisions.md)'s device matrix rejected
  a native app; between them an SPA was already foreclosed. Recorded so the row stops reading as
  open.

  **6. Linting (row 6) — `djlint` for templates; standalone CSS/JS linting deferred to 9.17.**
  `djlint` is a pip package, so it becomes the first real occupant of
  [ADR-029](decisions.md)'s `requirements/dev.in`, with no Node in dev either. `stylelint`/`prettier`
  are rejected for now on the same grounds as clause 3: they would pull in a `package.json` for 922
  lines of CSS and no JS.
- **Alternatives considered:**
  - **Vite** (the documented candidate) — rejected, see clause 3. It is the right tool for a frontend
    this project does not have; the decision is reversible in a day if the revisit trigger fires.
  - **`django-compressor`/libsass** — considered as the no-Node way to keep SCSS. Rejected: it adds a
    Python dependency and a compile step that overlap whitenoise's job, and the libsass bindings lag
    dart-sass upstream. It carries some of both options' downsides for little of either's benefit.
  - **Tailwind** — rejected. It rewrites the markup in all 32 templates and forces the Node pipeline
    back in regardless of clause 3, which is a large scope addition on top of a template rewrite that
    already carries plenty.
  - **Dropping the CSS framework for hand-written modern CSS** — rejected. 922 lines is genuinely
    small, but it would hand a solo developer ownership of responsive tables, form styling, modals
    and the whole accessibility surface, against a WCAG target — the opposite of the intent.
  - **Vanilla JS only, no HTMX** — rejected. It means hand-writing fetch, DOM swapping, URL/history
    sync and error handling for precisely the patterns 5.9 and 5.23 need, producing more custom
    JavaScript to maintain solo and more surface for the accessibility target to go wrong.
  - **Deferring the whole linting row to 9.17** — rejected narrowly; template linting directly serves
    this epic's `base.html`/partials rewrite, so it is decided where it is used. Python formatting and
    the test runner stay with 9.17.
- **Consequences:**
  - **5.3 stops being tidying and becomes load-bearing.** With no pipeline, whitenoise is now the
    *only* cache-busting mechanism, and it does nothing for the 23 templates that hardcode
    `/static/...`. 5.3 + 19.14 + 1.13 are the whole story on asset versioning — if 5.3 is done
    partially, the result is a site that silently serves stale CSS.
  - **Bootstrap's full stylesheet ships, un-tree-shaken** (~230KB minified, compressed by whitenoise
    and cached). Accepted explicitly against [ADR-021](decisions.md)'s p95 budget: it is a cached
    static asset at roughly ten concurrent users, not a per-request cost.
  - **Vendored frontend assets need the [ADR-029](decisions.md) treatment.** Bootstrap and HTMX are
    dependencies that `requirements/*.in` cannot see, so their versions and provenance get recorded
    explicitly (5.25) — otherwise the repo repeats exactly the situation this ADR opened with: a
    four-year-old vendored library nobody noticed.
  - **`requirements/dev.in` gains its first occupant** (`djlint`), which is why
    [ADR-029](decisions.md) treated an initially thin `dev.in` as expected rather than a gap.
  - **Views acquire a fragment-rendering path**: on `HX-Request`, render the partial directly rather
    than the full page. That is a small convention, but it must be settled before 5.9 is built, not
    discovered during it (5.7).
  - **Epic 5 still cannot start.** 5.22/5.23 need Django 5.2 (Epic 19) and 5.18/5.20/5.21 need
    Epic 3's dated prices and receipts. This decision removes the *decision* blocker on 5.4/5.6/5.7,
    not the sequencing one.
  - Closes 9.13; Epic 9's remaining open rows are 9.4, 9.14, 9.15, 9.16, 9.17 (less template
    linting), 9.18's two halves, 9.19, 9.20 and 9.21.

## ADR-031: Operations — a coverage-gated CI pipeline, Railway git-watch deploys, Sentry EU, UptimeRobot, and a two-track backup strategy

- **Date:** 2026-08-18
- **Status:** Accepted — closes the `Infrastructure / operations` table in [tech_stack.md](tech_stack.md)
  (9.14, 9.15, 9.16)
- **Context:** Tasks 9.14, 9.15 and 9.16, blocking 6.12, 7.2, 7.5, 3.38, 3.40 and 3.44. These were
  the last four `Open` rows in the infrastructure table, and they are decided together because they
  share one set of constraints already fixed elsewhere:

  | Constraint | Source |
  |---|---|
  | ~$6/mo total infrastructure, one solo developer, a free pilot with **one** tenant | [ADR-013](decisions.md), [ADR-016](decisions.md) |
  | EU data residency; every vendor is a GDPR **processor** needing a DPA and a subprocessor entry | [ADR-013](decisions.md), [gdpr.md](gdpr.md) §7 |
  | The app must stay movable to any Docker + PostgreSQL host with **configuration changes only** | [ADR-015](decisions.md), rule 5 in particular |
  | Railway offers **no PITR**; its snapshots are copy-on-write volume snapshots, not restorable elsewhere | [ADR-013](decisions.md) |
  | GitHub Actions is already the CI runner, with a minimal workflow in Epic 1 (1.11, 1.13) | [ADR-011](decisions.md) |
  | Cloudflare R2 is already provisioned for media, with zero egress and a 10 GB free tier | [ADR-005](decisions.md) |
  | Dependencies are pinned and hashed in `requirements/{base,dev,prod}.txt`; each direct dependency names an owner | [ADR-029](decisions.md) |

  Two facts about the current state set the bar. There is **no test suite at all**, so any coverage
  gate decided now is a target Epic 6 has to reach rather than a floor it has to hold. And backups
  are literally "unknown/undocumented" — the risk being managed is not a slow restore but an
  unrecoverable one, over data that [ADR-017](decisions.md) gives a **legal** retention floor.
- **Decision:**

  **1. CI merge gate (9.14) — extend the Epic 1 workflow with tests, lint, a dependency audit, and a
  70% repo-wide coverage floor.** The blocking set on every PR is: the Django test suite, `ruff`
  (Python) and `djlint` (templates, per [ADR-030](decisions.md)), the `manage.py check` /
  `makemigrations --check` / `collectstatic` / `docker build` checks already in 1.11 and 1.13, and
  `pip-audit` run against the hashed lock from [ADR-029](decisions.md). Dependabot raises dependency
  PRs, which then pass through the same gate. Coverage is **70% across the repository**, one number,
  enforced by `coverage report --fail-under=70`.

  **2. No SAST or container scanning in the first release.** CodeQL and Trivy are deliberately left
  out: this is a private repo (so CodeQL needs GitHub Advanced Security), and the realistic threat
  here is a known CVE in a dependency — which `pip-audit` and Dependabot already cover — not a novel
  taint-flow bug in ~2,000 lines of Django views. **Revisit trigger:** the repo going public, the
  first tenant outside the pilot, or any handling of payment data.

  **3. Deploys (9.14, second half) — Railway git-watch on `production`, with `migrate` as Railway's
  pre-deploy command.** [ADR-015](decisions.md) already accepted git-watch as tolerated lock-in;
  the pre-deploy hook is what makes it sufficient, because it runs migrations to completion **before**
  the new version takes traffic, satisfying rule 4 (migrations out of the container `CMD`) without a
  hand-maintained release script or a Railway token in GitHub secrets. Task 6.14 ("block deployments
  when checks fail") is therefore satisfied **by branch protection**: `production` only advances by
  merge, merges are blocked by 6.13's required checks, so an unverified commit cannot become a
  deploy. There is no second gate to build, and no place for CI and the platform to disagree about
  what is live.

  **4. Error tracking (9.15) — Sentry SaaS, free Developer tier, EU region.** The organisation is
  created in the EU region (`de.sentry.io`), which is **irreversible after creation** — the single
  setup step that must not be got wrong. `sentry-sdk[django]` joins `requirements/base.in` with an
  owner comment. Two configuration rules are part of this decision, not afterthoughts:
  `send_default_pii` stays **off**, and a `before_send` scrubber strips request bodies, headers and
  local variables — a traceback from this app can carry supplier contact details, staff emails and a
  tenant's costing data, and shipping those to a processor by accident is a personal-data disclosure
  that no DPA covers. Sentry environments and releases are tagged from the deploy so pilot noise is
  separable from real production errors.

  **5. Uptime (9.15, second half) — UptimeRobot free tier, keyword check, external to Railway.** A
  5-minute HTTPS check against 7.4's health endpoint, matching on a **keyword in the response body**
  rather than on HTTP 200, so a health endpoint that reports a failed database check fails the
  monitor instead of passing it. Email alerting; the public status page is available if the pilot
  ever wants one. It is hosted away from Railway deliberately — a monitor that shares fate with the
  thing it monitors is decorative.

  **6. Backups (9.16) — two tracks, deliberately unequal, and no PITR.**
  - *Fast rollback:* Railway's native daily / weekly / monthly schedules, enabled explicitly since
    they are **off by default** (12.9). Same-host only.
  - *The real backup:* a nightly GitHub Actions job running
    `pg_dump -Fc --no-owner --no-privileges` (flags per 3.46), encrypted **client-side with `age`**
    before it leaves CI, uploaded to a Cloudflare R2 bucket separate from the media bucket, under a
    lifecycle rule keeping **7 daily, 4 weekly, 12 monthly**. It runs outside Railway on purpose: an
    escape hatch that depends on the platform it escapes is not one.
  - *Proof:* 3.48's weekly automated restore drill — decrypt, restore into a throwaway PostgreSQL 17,
    run 3.47's verification (row counts, constraint/FK validation, sequence positions, `REINDEX`),
    and alert on failure. The drill is also the only thing that proves the `age` key still decrypts.
  - *PITR is rejected*, accepting an RPO of up to 24 hours. **Revisit trigger:** the second paying
    tenant, or the point where a day of lost goods receipts stops being re-enterable from paper
    invoices.
- **Alternatives considered:**
  - **Coverage scoped to `control/services/` at 90%, or a no-regression ratchet** — both were better
    aimed (the costing layer is where a wrong number becomes a mispriced product) but a single
    repo-wide number is what a solo developer will actually keep honest, and scoping invites
    arguing about which module counts. The blunt version is enforced in one CI line and is
    tightenable later without renegotiation.
  - **A coverage floor of 80%+** — rejected as a first target against a codebase with zero tests;
    a gate that cannot be met is a gate that gets disabled.
  - **GitHub Actions owning the deploy via the Railway CLI** — rejected. It buys explicit control of
    migrate/release ordering, which the pre-deploy command already provides, in exchange for a
    long-lived Railway token in GitHub secrets and a release script to maintain solo. It also swaps
    accepted lock-in for a bespoke one.
  - **Manual deploy approval on `production`** — rejected for now. A human checkpoint is right once
    there are tenants who did not agree to be pilots; with one pilot bakery and one developer it adds
    a step whose only reviewer is the person who wrote the change. Folds into the same revisit
    trigger as clause 2.
  - **GlitchTip self-hosted (Sentry-SDK-compatible)** — genuinely attractive on EU-ownership and
    removes a processor entirely, but it needs a container **and its own PostgreSQL**, roughly
    doubling the infrastructure bill and making the thing that watches the app another thing to
    patch and watch. Because it speaks the same SDK, the switch stays a configuration change if
    Sentry's free tier or ownership becomes a problem.
  - **Logs plus `AdminEmailHandler` over Brevo, no error-tracking vendor** — rejected. Free and
    processor-free, but with no grouping, deduplication or release correlation, one bad loop floods
    the inbox and the signal is lost exactly when it matters.
  - **Better Stack / Sentry's own uptime monitors** — both fine; UptimeRobot wins on being free
    without a plan tier and independent of the error-tracking vendor. Using Sentry for uptime would
    make one free tier the entire observability stack and let a Sentry outage take the alerting with
    it.
  - **The dump job as a Railway cron service** — the stronger *security* answer: it runs on the
    private network, so the database never needs Railway's public TCP proxy and no DB credentials sit
    in GitHub secrets. Rejected narrowly on the portability argument above, and mitigated instead by
    backup-scoped, rotatable credentials (3.41). Worth reopening if the public-proxy exposure ever
    proves uncomfortable — the job body is identical either way.
  - **Railway snapshots plus manual pre-release dumps** — rejected outright: it fails
    [ADR-015](decisions.md) rule 5, and "manual, when I remember" is precisely what 3.48 exists to
    eliminate.
  - **Real PITR via `pgBackRest`/`wal-g` shipping WAL to R2** — rejected for now. It is the only way
    to get minutes-level RPO on a host with no PITR, but it is a self-managed component with its own
    failure modes, added by a solo developer to protect a dataset measured in megabytes that is
    re-enterable from paper invoices. See the revisit trigger in clause 6.
  - **Relying on R2's default server-side encryption, or SSE-C** — SSE alone leaves Cloudflare
    holding keys it could use, which weakens the §6 answer for a vendor that is already the media
    processor; SSE-C keeps the key yours but must be passed correctly on every dump *and* every
    restore, with no recovery if it drifts. Client-side `age` gives the strongest statement — the
    processor stores ciphertext — for one extra command in the job.
- **Consequences:**
  - **Epic 6 acquires a hard number.** 70% coverage from zero is the largest single piece of work
    this ADR creates, and it gates every subsequent merge once enabled. It is therefore turned on
    **at the end of Epic 6**, not at its start (6.22) — enabling it first would block the very PRs
    that write the tests.
  - **`requirements/base.in` gains its sixth direct dependency** (`sentry-sdk[django]`), the first
    addition since [ADR-029](decisions.md) set the register rule. `pip-audit` and `coverage` go to
    `dev.in` alongside `djlint`.
  - **A third processor joins [gdpr.md](gdpr.md) §7** (Sentry, after Railway and Cloudflare R2, with
    Brevo from [ADR-028](decisions.md)). 11.6 grows to include it, and 11.13's "confirm backups are
    encrypted at rest" now has a concrete answer to confirm: client-side `age`, so the storage
    processor holds ciphertext.
  - **Key custody becomes an operational responsibility with no software fallback.** The `age`
    private key lives outside CI; if it is lost, every backup in R2 is unrecoverable. 3.72 owns it
    and 3.48 is the recurring proof it still works — this is the one place where the weekly drill is
    not merely good practice.
  - **CI now needs database credentials**, which the repo has never held. They are backup-scoped and
    separate from the app's (3.41), and reach Postgres over Railway's public TCP proxy — an exposure
    that did not exist before and is the accepted cost of clause 6's independence.
  - **Alerting arrives before the thing it protects.** Sentry and UptimeRobot both belong to Epic 7,
    which depends on Epic 12 provisioning the host — so until that lands, the pilot runs unmonitored
    on the home server. That is a sequencing fact, not a gap this ADR can close.
  - **The RPO is a stated product position, not an oversight.** Up to 24 hours of goods receipts and
    price rows can be lost. With [ADR-017](decisions.md)'s traceability records carrying a legal
    retention floor, this must be written into the backup runbook (8.5) so it is a decision the
    pilot bakery has seen rather than a surprise on the day.
  - Closes 9.14, 9.15 and 9.16. Epic 9's remaining open rows are **9.4** (held for 9.20), 9.17's
    Python half, 9.18's ingredient-line and categories halves, 9.19, 9.20 and 9.21.

## ADR-032: One shared `RecipeLine` model, and categories as a tenant-scoped lookup table

- **Date:** 2026-08-26
- **Status:** Accepted
- **Context:** The two remaining halves of 9.18. [ADR-022](decisions.md) gave both `Bs_Ingredients`
  and `Recipe_Ingredients` a typed *component* reference (raw material **or** base recipe) alongside
  their typed parent, which left the two tables structurally identical and reduced the choice between
  them to a formality — but a formality that Epic 3's migrations cannot be written without.
  Separately, `categorie` is a free-text `CharField` on `RawMaterial` and `Product`: unvalidated,
  untranslatable, and useless for the filtering 5.9 has to build. [ADR-018](decisions.md) already sent
  units to a lookup table, and 10.17 recorded that categories — unlike units — are reference data a
  tenant may safely edit.
- **Decision:**
  1. **One `RecipeLine` model replaces both line tables.** It carries a typed parent
     (`parent_product` **XOR** `parent_base_recipe`) and a typed component (`component_material`
     **XOR** `component_recipe`), each pair enforced by a database `CHECK` constraint rather than by
     convention, plus `quantity` and a `unit` FK per [ADR-018](decisions.md).
  2. **`Product` and `Base_recipes` stay separate models.** This collapses the *lines*, not the
     recipes. [ADR-022](decisions.md) considered and declined merging them behind an `is_sellable`
     flag; nothing here reopens that — the migration is larger and the distinction is one the bakery
     thinks in.
  3. **Categories become a single tenant-scoped `Category` table** with a `kind` discriminator
     (`material` / `product`), an `archived` flag per [ADR-019](decisions.md)'s soft-delete rule, and
     uniqueness on `(bakery, kind, name)`. One table, not two — the two kinds differ only in which
     model points at them.
  4. **Categories are tenant-editable; units are not.** A `Category` row carries no arithmetic, so a
     tenant inventing "Viennoiserie" breaks nothing. A `Unit` row carries a conversion factor, so
     editing one silently rewrites every cost derived from it — which is why 10.17 separates them and
     why this ADR does too.
- **Alternatives considered:**
  - **Keeping two line tables behind one abstract base** — rejected. It preserves the shape without
    the benefit: the costing service still branches on type, and every later line-level feature
    (allergen aggregation in 18.3, waste factors, per-line notes) gets built and tested twice.
  - **Merging `Product` and `Base_recipes` into one `Recipe` model** — rejected here, consistent with
    [ADR-022](decisions.md). Worth noting that this decision makes that migration *cheaper* later, not
    harder: with one line table, merging the parents becomes a change to two FK columns.
  - **`TextChoices` enum for categories** — rejected on 10.17. A fixed code-managed list means a
    migration and a deploy every time a bakery names a new category, and every tenant sharing one
    vocabulary, which the multi-tenant model in [ADR-006](decisions.md) does not support.
  - **Two separate category tables** — rejected as duplicated CRUD, admin registration, settings UI and
    tests for two tables that differ by one column.
- **Consequences:**
  - **The `CHECK` constraints are the decision.** A nullable-FK pair with no constraint is a worse
    schema than two tables, because it permits a line with two parents or none. Both XORs are database
    constraints written in the same migration as the model (3.73), not `clean()` methods — `clean()`
    does not run on `bulk_create`, which is exactly how an import will write these rows.
  - **The migration is a merge, not a rename.** Two tables of live prototype data fold into one with a
    discriminating parent column; the old tables are dropped only after row counts reconcile (3.73).
  - **It simplifies the two hardest traversals in the app at once.** [ADR-022](decisions.md)'s
    recursive costing and [ADR-017](decisions.md)/17.7's multi-level trace are the same walk in
    opposite directions over this one table — and 18.3's allergen aggregation is a third. One
    cycle-guard implementation (3.59, 4.16) now covers all of them.
  - **Free-text categories must be backfilled per tenant, not globally.** Today's values are one
    bakery's typing; migrating them means distinct-value extraction into `Category` rows scoped to the
    pilot tenant, with the free-text column dropped afterwards (3.74).
  - **`kind` must be validated against the referencing model**, or a product can be filed under a
    flour category. The FK cannot express that; the form and the service layer must (3.74).
  - Closes 9.18 completely. Unblocks 3.19 and the categories half of 3.26; creates 3.73, 3.74. Note
    that 3.42 and 4.14 still cite 9.18 as their blocker — both were already closed by
    [ADR-027](decisions.md) (pooling → 7.19) and [ADR-028](decisions.md) (no cache), and are corrected
    in the backlog by this pass.

## ADR-033: Traceability entity model — receipt headers with lines, production runs emitting batches, date-prefixed lot codes, and stock derivable but not surfaced

- **Date:** 2026-08-26
- **Status:** Accepted
- **Context:** 9.21, the last decision Epic 3 is waiting on. [ADR-017](decisions.md) fixed the
  direction — goods receipts, production runs, outbound records, and the rule that **a lot is an event,
  not an attribute** — but explicitly left the entity shape, the lot-code strategy, and the
  stock question open. All three touch tables Epic 3 is about to restructure, so deciding them
  afterwards means restructuring twice.
- **Decision:**
  1. **Goods receipts are a header with lines.** `GoodsReceipt` holds supplier, receipt date and
     document reference; `GoodsReceiptLine` holds raw material, supplier lot code, quantity, unit,
     best-before, and the price actually paid in [ADR-018](decisions.md)'s
     `purchase_price`/`pack_quantity`/`purchase_unit` shape. A delivery note is one record with many
     lines, and modelling it that way is what makes "show me that delivery" a lookup rather than a
     group-by.
  2. **Production runs consume specific receipt lines and emit a batch.** `ProductionRun` →
     `Consumption` (FK to `GoodsReceiptLine`, quantity consumed in canonical units) and an output
     `Batch` carrying the internal lot code. `OutboundRecord` hangs off `Batch`.
  3. **Internal lot codes are `YYYYMMDD-NNN`**, sequence resetting daily, unique per
     `(bakery, lot_code)`, allocated **server-side inside the transaction that creates the batch** —
     never client-side, never by counting existing rows.
  4. **Quantity-on-hand is derivable but not surfaced.** Because `Consumption` records the quantity
     taken from each receipt line, on-hand is `Σ received − Σ consumed` — computable, never stored,
     and **not displayed anywhere this round**: no stock field, no stock page, no low-stock alerts.
- **Alternatives considered:**
  - **Flat receipt lines carrying supplier and date on every row** — rejected. It denormalises the
    delivery note into its items and loses the document as a record, which is the unit an FSAI
    inspector and a supplier query both work in.
  - **Receipts first, production runs in a later slice** — rejected on [ADR-017](decisions.md)'s own
    warning: a partial traceability implementation that looks complete is worse than none. Receipts
    alone give one step *back* and nothing forward, while presenting a "Traceability" section to a real
    food business operator.
  - **Opaque per-tenant sequence (`B-000123`)** — rejected. It is simpler to generate, but a lot code's
    job is to be read off a label, quoted on a phone call, and sorted on paper; the date earns its
    place in the string.
  - **User-entered lot codes** — rejected as the default. Many bakeries print their own codes, but a
    format the app cannot guarantee is a format the trace query cannot rely on. Revisit if the pilot
    turns out to have an established scheme worth honouring.
  - **A full stock ledger with adjustments, waste and stock-takes** — rejected; it contradicts
    [ADR-024](decisions.md)'s `Could` rating and is a different product promise (inventory management)
    with accuracy expectations this app cannot meet.
  - **Showing the derived figure read-only** — rejected, and this was the closest call. A number on
    screen is trusted regardless of its caveat label; "received minus consumed" ignores waste,
    spillage and unrecorded use, so it would be wrong in a bakery's normal operation, not in an edge
    case.
- **Consequences:**
  - **`Consumption.quantity_consumed` is load-bearing beyond traceability.** It is the single field
    that keeps stock derivable later without a schema change (17.14) — the whole content of
    [ADR-024](decisions.md)'s "design so it *could* be derived".
  - **Lot-code allocation needs a concurrency-safe implementation, not a helper function.** Two runs
    finishing in the same second must not collide; the unique constraint is the backstop, the
    transactional allocation is the mechanism, and gaps after a rollback are acceptable (17.13).
  - **This is where [ADR-022](decisions.md)'s costing gets its data.** "Latest receipt by receipt date"
    now has a concrete table to query, and `GoodsReceiptLine` is the price-history source 17.12 asks
    about — which answers 10.5's input-price-history question as a by-product.
  - **Receipt lines are append-only** (17.5), which makes them the first tables in the schema where
    [ADR-019](decisions.md)'s soft-delete is not enough — corrections are new records, not edits.
  - **Epic 3 must build `RawMaterial` knowing these tables are coming.** Specifically: no `lot` field,
    no `stock` field, and `quantity` numeric with a unit FK (3.10, 3.14) so a receipt line can be
    reconciled against the catalogue row.
  - **The pilot will ask for stock.** The answer is deliberate and should be given as one: the data is
    being recorded, the feature is not being claimed until it can be trusted. Recorded here so it is a
    position rather than an omission.
  - Closes 9.21. Unblocks 17.1, 17.2, 17.3; creates 17.13, 17.14; confirms the direction of 17.12.

## ADR-034: Python quality tooling — `ruff` for both linting and formatting, `pytest-django` as the test runner

- **Date:** 2026-08-26
- **Status:** Accepted
- **Context:** The Python half of 9.17. [ADR-030](decisions.md) already closed templates (`djlint`)
  and deferred standalone CSS/JS linting; [ADR-031](decisions.md) already named `ruff` in the CI gate
  and set a 70% repo-wide coverage floor. What was left unstated is whether `ruff` also *formats*
  (or whether `black`/`isort` join it), and what actually runs the tests — a question with no legacy
  cost attached, since every `tests.py` in the repo is an empty stub.
- **Decision:**
  1. **`ruff` does both** — `ruff check` and `ruff format`. No `black`, no `isort`, no `flake8`.
  2. **`pytest` + `pytest-django` + `pytest-cov`** run the suite, replacing `manage.py test`.
  3. **Tool configuration lives in a `pyproject.toml` holding only `[tool.*]` sections.** It is not a
     packaging file and declares no dependencies — [ADR-029](decisions.md)'s requirements-file model is
     untouched, and this file must never grow a `[project]` or `[build-system]` table.
  4. `pytest`, `pytest-django`, `pytest-cov` and `ruff` all enter `requirements/dev.in` with the
     owner/purpose comment [ADR-029](decisions.md) requires, alongside `djlint`.
- **Alternatives considered:**
  - **Django's own test runner with `coverage.py`** — genuinely close, and consistent with how
    [ADR-028](decisions.md) rejected DRF and [ADR-030](decisions.md) rejected Vite. It lost on the
    specific shape of this suite: the costing tests are table-driven across unit conversions × VAT
    boundaries × rounding × recursion depth, which is what `parametrize` exists for, and
    [ADR-008](decisions.md)'s tenant-isolation tests want composable fixtures more than they want
    `setUp`. `subTest()` covers the first case; it reports failures worse.
  - **`ruff` for linting with `black` for formatting** — rejected. `ruff format` is a deliberate
    reimplementation of black's style; running both adds a dependency and a CI step to reach the same
    output, and [ADR-029](decisions.md)'s register would ask what it is for.
  - **Adding `mypy`** — not adopted and not rejected on merit; it is simply out of scope for a codebase
    with no annotations yet. Revisit when [ADR-028](decisions.md)'s service layer exists, since typed
    `Decimal` boundaries are where it would pay.
- **Consequences:**
  - **The documented test command changes**, and it is documented in three places — `CLAUDE.md`, the
    README rewrite (8.1), and the CI workflow. `python manage.py test` stops being the answer (6.24).
  - **`--cov-fail-under=70` is where [ADR-031](decisions.md)'s floor is actually enforced**, which
    keeps 6.22's "switch the gate on at the end of the epic" a one-line change rather than a rework.
  - **Django's test-database machinery still applies** — `pytest-django` wraps it rather than replacing
    it, so migrations, `--reuse-db` and transactional test cases behave as Django documents them. This
    is why the choice carries little lock-in: the tests are still Django tests.
  - **First real occupants of `requirements/dev.in`.** Together with `djlint` from
    [ADR-030](decisions.md), this is the file's actual content, and the first test of whether the
    owner-comment rule survives contact with a real dependency list.
  - Closes 9.17 completely. Unblocks 6.10 and 6.11; creates 6.23, 6.24; feeds 6.12 and 6.22.

## ADR-035: Tenant full data export — one CSV per table plus a JSON manifest, in a ZIP

- **Date:** 2026-08-26
- **Status:** Accepted
- **Context:** 9.19. [ADR-008](decisions.md) committed to a tenant-scoped full export in a format that
  does **not** assume the recipient runs a compatible PostgreSQL, and named two candidates — portable
  ANSI SQL, or a per-table CSV bundle with a relationship manifest — without choosing. Epic 14 is
  blocked on the choice.
- **Decision:** A **ZIP containing one CSV per tenant-scoped table plus a `manifest.json`**. The
  manifest carries the export timestamp, a schema version, and for each table its columns, types,
  primary key and foreign-key map, so relationships survive a format that cannot express them.
  Generated by a **single service function**, exposed two ways: an Owner-only download in the
  settings area ([ADR-023](decisions.md)'s tenant self-administration surface) and a management
  command for support use.
- **Alternatives considered:**
  - **Portable ANSI SQL (`CREATE TABLE`/`INSERT`)** — rejected, though it was ADR-008's first-named
    option. Hand-generating correct, portable DDL means maintaining a type map and quoting rules
    against every future model change, and the output serves only a developer. The CSV bundle serves
    both audiences ADR-008 named: it opens in a spreadsheet for the bakery owner and loads into any
    DBMS for whoever they hire.
  - **`manage.py dumpdata` JSON** — rejected. Nearly free to build, but it is a *Django serialization*
    format, not a DBMS-portable one, which is precisely the dependency ADR-008 set out to avoid.
  - **A tenant-scoped `pg_dump`** — already rejected by ADR-008; unchanged here.
- **Consequences:**
  - **The manifest is the deliverable, not the CSVs.** CSV loses types, nulls-versus-empty-strings, and
    every relationship; the manifest is what makes the bundle reconstructable, so 14.3 is a
    correctness task rather than a documentation nicety.
  - **Synchronous download is adequate and should be re-checked, not assumed.** One bakery's data is
    megabytes ([ADR-013](decisions.md)'s scale), so it fits [ADR-021](decisions.md)'s budget as a
    direct response — but the check belongs in 14.6, since a tenant with years of goods receipts is a
    different size than today's catalogue.
  - **Every export is a bulk disclosure of one tenant's business data**, so 14.4's gating and audit log
    are part of the feature, not a follow-up — and the Owner-only restriction uses
    [ADR-020](decisions.md)'s capability names, not a role comparison.
  - **The GDPR personal-data export (Epic 15) is still a separate mechanism** per
    [ADR-009](decisions.md). It can reuse this bundle *shape* scoped to one subject; whether it does is
    15.2's call, not this ADR's.
  - **Decimal fidelity in CSV is a real trap.** Money and quantities must be written at full stored
    precision, never at [ADR-018](decisions.md)'s 2-dp presentation rounding — an export that rounds is
    an export that silently loses data (14.1).
  - Closes 9.19. Unblocks 14.1; creates 14.6.

## ADR-036: AI insights confirmed on Databricks Serverless Jobs (AWS, EU Ireland), fed by an R2 extract on a nightly schedule — and gunicorn/WSGI stands

- **Date:** 2026-08-26
- **Status:** Accepted
- **Context:** 9.20 and 9.4. [ADR-002](decisions.md) proposed Spark on Databricks for the insights
  service but was never confirmed: its own "alternatives considered" recorded that a plain-Python or
  scheduled-query approach had not been compared, and [ADR-024](decisions.md) went further, making a
  scheduled query over [ADR-018](decisions.md)'s dated price rows the **null hypothesis** Spark had to
  beat. Left unsettled with it: the trigger contract, where the service runs relative to the app, the
  data it may see, and the cost model — plus 9.4, which [ADR-025](decisions.md) deliberately held back
  because a live analytics dashboard is the only thing in scope that could argue for ASGI.
- **Decision:**
  1. **Spark on Databricks is confirmed** — the engine choice in [ADR-002](decisions.md) stands, and
     that ADR moves from `Proposed` to `Accepted`.
  2. **Databricks Serverless Jobs on AWS, EU (Ireland) `eu-west-1`.** Serverless job compute only —
     no all-purpose or interactive cluster, and no cluster lifecycle for the app to manage. This is
     what makes per-use billing real: there is no machine to start, idle, or forget to stop.
  3. **Django hands over an extract; Databricks never touches PostgreSQL.** A nightly job writes a
     scoped, **personal-data-free** costing extract (product, date, cost, price, margin, tenant) to a
     dedicated Cloudflare R2 prefix ([ADR-005](decisions.md)); the Databricks job reads only that.
  4. **Nightly schedule, results POSTed back.** The job runs on Databricks' own schedule and returns
     results to a plain `JsonResponse` callback endpoint ([ADR-028](decisions.md)'s two-endpoint
     exception), authenticated with a shared secret. No event triggering, no Jobs API call from the
     request path.
  5. **Hard cost ceiling ~$15/mo**, with a spend alert configured before the first production run.
  6. **9.4: gunicorn, WSGI, sync workers**, latest version pinned at lock time
     ([ADR-029](decisions.md)). Revisit trigger, and only this one: the insights dashboard needing
     **push** updates (SSE/WebSocket) rather than polling.
- **Alternatives considered:**
  - **A scheduled query inside Django** ([ADR-024](decisions.md)'s null hypothesis) — not adopted. It
    would have been cheaper and added no processor, and it remains the correct answer if the insights
    scope never grows past margin alerts. The decision to keep Spark is a deliberate bet on headroom
    for the analytics and ML work Epic 16 is meant to grow into, made with the cost and compliance
    consequences below stated rather than discovered.
  - **Databricks reading Railway PostgreSQL directly over the public TCP proxy** (ADR-002's literal
    shape) — rejected. It exposes the production database to a third-party network and drags every
    readable table, including supplier contacts and user accounts, into GDPR transfer scope. The R2
    handoff costs one nightly job and removes both problems.
  - **Passing data in the Jobs API payload** — rejected; no persistence means no history, and trend
    analysis is most of the point.
  - **Event-triggered runs on price/receipt changes** — rejected for the first release. Serverless
    startup is seconds rather than minutes, so latency is not the objection; debounce, retry and
    deduplication logic in the app is. A margin alert is a daily concern — a price change at 14:03
    does not need a 14:04 alert. Revisit if a genuinely interactive insight appears.
  - **All-purpose/interactive Databricks cluster** — rejected as the shape that generates surprise
    bills, which is exactly what the ~$15/mo ceiling exists to prevent.
  - **ASGI now** (9.4) — rejected. [ADR-028](decisions.md)'s service layer is sync throughout, so an
    async view would raise `SynchronousOnlyOperation` against the ORM; adopting ASGI would impose that
    constraint from day one for a feature rated `Could`.
- **Consequences:**
  - **This is the first recurring cost increase since [ADR-013](decisions.md).** Total infrastructure
    goes from ~$6/mo to roughly $21/mo at the ceiling — a 3.5× rise against [ADR-016](decisions.md)'s
    zero revenue. It is a funded bet, not a free addition, and 16.8 must measure a real run before
    production spend rather than trusting the estimate.
  - **The DBU rate is not recorded here on purpose.** Databricks serverless pricing changes and is
    region- and tier-dependent; 16.8 records the *measured* cost of one real run at provisioning time.
    An unverified number in an append-only log is worse than no number.
  - **Two new processors join [gdpr.md](gdpr.md) §7** — Databricks Inc. and AWS — both requiring a DPA
    before real data flows (11.17, 16.4). The R2 extract is what keeps this manageable: with no
    personal data in the handover, the transfer is business data only, and both processors sit in the
    EEA (AWS `eu-west-1`; Railway is EU West per [ADR-013](decisions.md)), so no Chapter V transfer
    mechanism is needed for the data itself. **Databricks Inc. being US-headquartered is a
    subprocessor/DPA question, not a data-location one** — worth stating explicitly so the distinction
    is not re-litigated later.
  - **The extract schema is a published contract.** The Django job and the Databricks notebook evolve
    in different repositories on different schedules; an unversioned extract format is how that breaks
    silently, so the manifest carries a version and the notebook rejects an unknown one (16.13).
  - **A silent job failure is the real operational risk.** Insights that stop arriving look identical
    to "no alerts this week" — so job-failure alerting (16.11) is part of the feature, not part of
    Epic 7's monitoring.
  - **The callback endpoint is an unauthenticated-by-session, internet-facing write path** — the only
    one in the app. Shared secret, tenant scoping, and rate limiting are requirements on 16.10, and it
    is the one endpoint [ADR-027](decisions.md)'s `LoginRequiredMiddleware` must be exempted from
    besides the cover and login pages.
  - **9.4 closes with it.** Nothing in this shape is async: the extract job is a management command,
    the callback is a short POST. Unblocks 7.14.
  - Closes 9.20 and 9.4 — and with them, **every open row in
    [tech_stack.md](tech_stack.md) and all of Epic 9**. Creates 16.8–16.13, 11.17; unblocks 16.1, 16.2,
    16.3.

## ADR-037: <next decision goes here>

- **Date:**
- **Status:** Proposed
- **Context:**
- **Decision:**
- **Alternatives considered:**
- **Consequences:**
