# Architecture & Product Decisions

Append-only log of every real choice about stack, architecture, data model, process or scope.
**Never delete an entry** — supersede it, or note an amendment in its Status line.

Entries are deliberately terse: the decision, what lost and why, and what follows. Implementation
detail lives in the backlog; current state lives in `tech_stack.md` and `project_requirements.md`.

**Template:** `## ADR-0XX: <title>` · **Date / Status** · **Context** (why this was forced) ·
**Decision** · **Rejected** (option — reason) · **Consequences** (traps, accepted risks, work created).

---

## ADR-001: Branching strategy for the redesign

- **Date / Status:** 2026-07-16 · **Superseded by ADR-010** (`main` no longer mirrors production).
  The **branch-naming convention** below still stands and is referenced by `roadmap.md`.
- **Context:** Modernizing a live app in phases, without one long-running rewrite branch going stale.
- **Decision:** `main` stays deployable and is what runs in production. One branch per plan —
  `phase-N-<slug>`, `feature-<slug>`, `gdpr-<slug>`, `stack-<slug>` — mapping 1:1 to a plan agreed in
  Plan Mode before implementation. Each opens as a PR immediately and merges before the next starts
  from an updated `main`; no stacking. No direct commits or force-pushes to `main`. Squash-merge.
  Tag at the end of each phase as a rollback point.
- **Rejected:** **A single long-lived `redesign` branch** — too high a merge-conflict blast radius.
  **Trunk-based with feature flags** — too heavyweight before basic tests/CI exist.
- **Consequences:** Requires branch protection. Each session states its target branch before coding.

## ADR-002: AI insights service built on Apache Spark + Databricks

- **Date / Status:** 2026-07-16 · **Accepted** — was `Proposed` until confirmed by **ADR-036**, which
  also **amends the delivery shape**: not event-triggered, and it does not read the app's database.
- **Context:** New requirement for AI-derived operational insights — margin alerts, an analytics
  dashboard — scoped as an external service rather than built into Django.
- **Decision:** A separate batch component on **Apache Spark, run on Databricks**, returning results
  to the app.
- **Rejected:** Nothing, at the time — a plain-Python batch job (pandas/DuckDB) or a scheduled task was
  explicitly **not** compared against Spark for a dataset this size. That gap became ADR-024's null
  hypothesis and ADR-036 closed it.
- **Consequences:** Databricks runs on its own cloud, independent of where Django and Postgres are
  hosted. Community Edition is notebook-only with no job scheduling, so a paid workspace is required,
  billed separately from app hosting.

## ADR-003: Narrow hosting candidates to Railway, Render, DigitalOcean App Platform

- **Date / Status:** 2026-07-21 · Accepted — the final pick is ADR-013.
- **Context:** Eight candidates was too wide a field to finish deciding on.
- **Decision:** Only **Railway, Render and DigitalOcean App Platform** stay active. This narrows; it
  does not choose.
- **Rejected:** **Fly.io, Sevalla, Koyeb, Hetzner+Coolify** — set aside (comparison retained in
  `tech_stack.md`). **Oracle Cloud Always Free** — the front-runner on pure cost, lost on operational
  model: own reverse proxy/TLS, own firewall, no native GitHub deploy, traded for a managed PaaS.
- **Consequences:** Tooling, storage and CI/CD design target "works on any of the three".

## ADR-004: Deploy via the custom Dockerfile, not each platform's buildpack

- **Date / Status:** 2026-07-21 · Accepted
- **Context:** Each candidate supports a custom `Dockerfile` or its own buildpack; with the host
  unpicked, the build strategy had to behave identically across all three.
- **Decision:** Keep and harden the existing `Dockerfile` as the deployment artifact.
- **Rejected:** **Native buildpacks** — each makes its own choices about base image, Python patch
  version and build steps, so the app would need separate verification per host; all three prioritize
  a root `Dockerfile` anyway, so nothing is lost; and their own docs recommend buildpacks mainly for
  simple apps, whereas this one will add a PostgreSQL driver and image processing.
- **Consequences:** One Dockerfile is the single source of truth across dev, Compose and every host.
  Requires keeping it well-maintained rather than outsourcing that. Becomes rule 1 of ADR-015.

## ADR-005: Store user-uploaded media in S3-compatible object storage

- **Date / Status:** 2026-07-21 · Accepted
- **Context:** Product photos and profile pictures are coming, and no candidate host guarantees
  persistent shared local disk across redeploys or instances.
- **Decision:** **Cloudflare R2** via `django-storages`, decoupled from app hosting — zero egress, a
  10 GB/1M-write/10M-read free tier, and provider-agnostic, so storage need not move if the host does.
- **Rejected:** **Local disk** — not durable or shared on any candidate. **AWS S3** — egress fees and
  a free tier expiring after 12 months. **DigitalOcean Spaces** — a fallback only if DigitalOcean won
  compute. **Oracle Object Storage** — a weaker fit once Oracle stopped being a hosting candidate; a
  fourth provider relationship for no benefit.
- **Consequences:** Adds `django-storages[s3]`, `boto3`, `Pillow` in Epic 13. Bucket keys are secrets
  (2.5). Adds a processor. The backup bucket is later kept **separate** from media (ADR-031, 3.71).

## ADR-006: Multi-tenant SaaS architecture confirmed

- **Date / Status:** 2026-07-21 · Accepted
- **Context:** One bakery or many was open, and it blocked Epic 3 — it determines whether every model
  needs a tenant scope from the start.
- **Decision:** **Multi-tenant SaaS.** Each bakery is a tenant; one deployment serves many.
- **Rejected:** **Single-tenant (one deployment per bakery)** — doesn't match the intended direction of
  a shared database with per-tenant export as a differentiator.
- **Consequences:** Every business model needs a `Bakery` FK. Changes the GDPR model:
  **Bakery-the-product is Processor, each tenant is Controller.** Roles become per-tenant (ADR-020).
  Triggers a DPIA reassessment (11.7).

## ADR-007: App and database always run as separate services

- **Date / Status:** 2026-07-21 · Accepted
- **Context:** Whether to ever bundle Django and PostgreSQL into one deployable unit.
- **Decision:** **Always separate containers/services**, never one image. Matches current practice and
  how all three candidates offer Postgres — as a distinct managed add-on.
- **Rejected:** **Bundling Postgres into the app image** — breaks independent backups, breaks the
  "app container is stateless and disposable" property ADR-004 depends on, and isn't offered anyway.
- **Consequences:** Formalizes existing practice so it isn't re-litigated. Later the reason Railway's
  one-service Free plan is unusable.

## ADR-008: Shared multi-tenant database, with a tenant-scoped full data export

- **Date / Status:** 2026-07-21 · Accepted — export *format* fixed by **ADR-035**.
- **Context:** Given ADR-006: one shared database vs. a database per bakery. And separately, whether a
  departing bakery can get a full export usable outside the app.
- **Decision:** **A single shared database with row-level tenant isolation** — a `Bakery` model plus a
  tenant FK on every tenant-scoped table, enforced **at the query layer**, not at the database-instance
  level. Plus **a tenant-scoped full export** in a format that does not depend on this app's Postgres
  schema/version to reload.
- **Rejected:** **Database-per-tenant** — every candidate prices managed Postgres per instance
  (~$5–20+/mo each), so N bakeries means N bills; it would make "hand the tenant their DB" trivial, but
  that doesn't offset running N separately-migrated databases for a small dataset. **Handing over a raw
  `pg_dump`** — assumes the recipient runs a compatible Postgres.
- **Consequences:** FK migrations across nearly every table — a bigger schema change than scoped. New
  export tooling as its own feature (Epic 14). **Query-layer scoping becomes correctness-critical — a
  missed filter is a cross-tenant data leak** — hence dedicated isolation tests (6.9).

## ADR-009: A dedicated GDPR personal-data export alongside the bulk CSV exports

- **Date / Status:** 2026-07-21 · Accepted
- **Context:** The current CSV export is a bulk admin export of whole tables, not subject-scoped, so it
  doesn't satisfy Article 20. CSV as a *format* is fine; *scope* is the gap.
- **Decision:** Keep the bulk exports as an admin feature, **not** a compliance mechanism. Add a second
  **subject-scoped export** — one person's data across models. Distinct from both the bulk export and
  ADR-008's tenant-wide one.
- **Rejected:** **Retrofitting the bulk export with a subject filter** — the two shapes differ enough
  that conflating them risks over-exposing business data in a personal-data request, or under-scoping a
  real admin export.
- **Consequences:** A new export view/service (Epic 15), gated to the requester's own data or an admin
  acting on their behalf.

## ADR-010: `main` as dev/test integration, `production` as the deploy branch, tagged releases

- **Date / Status:** 2026-07-21 · Accepted — **supersedes ADR-001**; the **persistent-staging clause is
  amended by ADR-014**. The branch model itself is unchanged.
- **Context:** ADR-001 assumed `main` mirrors production. Before CI/CD exists, a pre-production
  integration branch, an explicit promotion step and named rollback points are wanted — and the model
  must work on whichever host is chosen. All three were checked and can run it.
- **Decision:** `main` is the **integration/dev-test branch**, not what users hit. ~~Every merge
  auto-deploys to persistent staging~~ — **amended by ADR-014**: that tier runs locally. A
  **`production` branch holds what's live**; promotion is a deliberate PR from `main`. Every merge to
  `production` is **tagged semver** and published as a GitHub Release. Both branches protected: PR
  only, no force-pushes; required status checks once Epic 6 exists; 0 approvals while solo.
- **Rejected:** **Keeping `main` as the deployed branch** — no safe integration point before users see
  changes. **Full GitFlow** — more ceremony than needed; two branches get the same safety.
  **Mandatory per-PR previews as a third tier** — cost (Render gates it behind a paid tier); left as a
  per-host option, which ADR-014 later takes up for the release PR only.
- **Consequences:** Requires creating `production` and configuring protection on both. Originally
  implied a second always-on environment — a real cost factor in the hosting pick, and what ADR-014
  removed.

## ADR-011: Minimal CI in Phase 1; Phase 6 becomes the full CI/CD build-out

- **Date / Status:** 2026-07-21 · Accepted — full pipeline shape fixed by **ADR-031**.
- **Context:** Branch protection means every change goes through a PR, but all CI/CD was scheduled for
  Phase 6 — five phases of PRs merging on manual review alone. Full CI/CD can't move earlier: it needs
  a test suite that doesn't exist yet and a host that isn't picked.
- **Decision:** Two touchpoints. **Phase 1** gets `manage.py check`, a migrations check, `docker build`
  validation and a basic lint pass on every PR. **Phase 6 extends that workflow rather than replacing
  it.** Deploy automation waits for an actual host.
- **Rejected:** **Moving all of Phase 6 forward** — its prerequisites don't exist; it would run against
  nothing or need redoing. **Leaving CI/CD entirely in Phase 6** — not defensible once protection is live.
- **Consequences:** Phase 1 gains 1.11 and 1.13. Phase 6's CI section says "extend", not "create".

## ADR-012: The plan becomes a task backlog; undecided material lives in `docs/`

- **Date / Status:** 2026-07-28 · Accepted
- **Context:** The plan had become a hybrid of actionable work, undecided recommendations, rationale and
  sequencing. Nothing was individually trackable, and it repeated — sometimes drifted from — `docs/`.
  Several `Accepted` ADRs had consequences spread through prose with no guarantee they became work.
- **Decision:** The plan is a **backlog** of **Epics** (1:1 with `roadmap.md`) holding numbered tasks
  (`3.12` = Epic 3, task 12). **Task IDs are stable and never renumbered.** Epics 1–8 keep the original
  phase numbers so "Phase N" references still resolve. **Undecided material does not live in the
  backlog.** **Every decision becomes a task**, tracked in the coverage table; a task blocked on an
  `Open` row is `Blocked` with a pointer to what unblocks it — so an undecided question can no longer be
  implemented by accident.
- **Rejected:** **A separate issue tracker** — better tooling, but it splits working context away from
  the repo and the sessions where planning happens; revisit if more people join. **Prose plus tracking
  in `roadmap.md`** — phase granularity is far too coarse for hundreds of pieces of work.
- **Consequences:** Work is referenceable by ID from commits and PRs. **Two files must stay in sync:**
  epic status in `roadmap.md`, task status in the backlog. Every future ADR gains a step: add its tasks
  and a coverage row in the same session. (Epics have since grown 16 → 19 and tasks to 352; the
  numbering rule is what makes that safe.)

## ADR-013: Railway (Hobby plan) as the hosting platform

- **Date / Status:** 2026-08-03 · Accepted
- **Context:** ADR-003 left the pick open; Epic 12 can't start without it and Epic 7 depends on Epic 12.
  Pricing re-confirmed 2026-08-03.
- **Decision:** **Railway, Hobby** ($5/mo including $5 usage credit), app and Postgres as separate
  services, built from the repo's `Dockerfile`, in **EU West (Amsterdam)**. **Expected ~$6/mo**;
  per-item basis in `tech_stack.md`. **Railway's free options are explicitly rejected:** the 30-day
  trial deletes stateful volumes 30 days after credits expire, and the Free plan (0.5 GB RAM, one
  service) cannot run an app *and* a database, which ADR-007 requires.
- **Rejected:** **Render** — per-PR previews need the Pro workspace ($19/user/mo) and paid Postgres
  starts ~$15/mo, a realistic ~$22/mo. **DigitalOcean App Platform** — ~$12–20/mo, bundling managed
  backups and monitoring and closest to a "professional" baseline, but 2–3× Railway's cost for a
  single-bakery workload with no capability needed today. Both stay viable fallbacks.
- **Consequences:**
  - **The region must be set before any service is created** (12.8). Railway's default is US West, and
    the personal data is in the *database* — an app in Amsterdam with a default-region Postgres puts the
    data in California. Volumes follow their service's region; EU-West Metal supports volumes on Hobby
    (since 2025-03-14). Moving a volume later forces a migration **with downtime**.
  - **Backups are not automatic** — daily (6-day retention), weekly (1 month), monthly (3 months) must be
    configured explicitly, billed incrementally. **No PITR.**
  - **No uptime SLA, no HA Postgres** on Hobby. Revisit at Pro ($20/mo per workspace) once real tenants
    are onboarded.
  - **Data residency vs. vendor ownership — the accepted risk.** Storage location is satisfied: GDPR
    treats the EU as one space (Art. 1(3)), so Amsterdam serves Irish customers as Dublin would. What it
    does *not* solve is that Railway is a US company, so US law can reach the parent even for EU-held
    data — a Chapter V question answered by SCCs / the EU-US Data Privacy Framework, whose predecessors
    Safe Harbour (2015) and Privacy Shield (2020) were **both annulled by the CJEU**. **Accepted, not
    dismissed**, on three grounds: the market is Ireland, where US-owned cloud is the norm; the exposure
    is shared by nearly every business on AWS/Azure/GCP; and SCCs remain a fallback. DPA required
    regardless (12.7 → 11.6, 11.15).
  - **Revisit before expanding beyond Ireland** (11.14). EU-owned alternatives (Clever Cloud ~€16–26/mo,
    Scaleway ~€16/mo) priced ~2.5–3× — about $150/yr, which is not what decides it. **What decides it is
    that continental buyers treat EU ownership as a purchasing criterion in a way Irish buyers generally
    do not.** Re-evaluate while migration is still annoying rather than a multi-tenant cutover.

## ADR-014: Local Docker Compose is the dev/test environment; no persistent hosted staging

- **Date / Status:** 2026-08-03 · Accepted — **amends ADR-010's persistent-staging clause**.
- **Context:** ADR-010's persistent staging means a second always-on app **and** Postgres on Railway,
  roughly doubling the bill to ~$12/mo — for an environment one developer leaves idle almost always.
- **Decision:** The dev/test environment is **local `docker-compose`**, using the same `Dockerfile`
  Railway deploys. **No persistent hosted staging** — Railway runs one environment, tracking
  `production`. Testing splits by branch: feature branch → automated unit tests locally and in CI;
  `main` → manual/integration verification of the *merged* result locally (catching interactions
  isolated branch testing cannot); `main` → `production` PR → the release gate. Because local
  verification never exercises Railway, enable a **Railway PR environment on the release PR only** —
  auto-created on open, destroyed on merge, well under $1/mo, and deliberately **not** on feature PRs.
  Refreshing the local environment is **manual** — GitHub cannot push to a developer's machine —
  reduced to one command by a repo script (1.12).
- **Rejected:** **Persistent hosted staging** — cost/benefit for a solo pre-launch project; it becomes
  necessary the moment `main` must be verifiable by someone other than its author. **PR environments on
  every feature PR** — redundant with local testing, and it multiplies the seeding problem. **A
  self-hosted runner auto-refreshing the local machine** — disproportionate, and only works while that
  machine is on.
- **Consequences:** Cuts hosting from ~$12 to ~$6/mo. **Makes the local Docker setup load-bearing** — it
  is the only integration-test environment, so drift from production is a correctness problem (hence
  19.10's broken compose file matters). PR environments clone services but **not volume data**, so the
  release environment starts empty and needs migrations plus seed data (12.10). **`main` need not be
  green at every moment** (nothing deploys from it); the binding rule is local verification before a
  release PR merges. Revisit at a second developer or the first real tenant.

## ADR-015: Host portability is a standing design constraint

- **Date / Status:** 2026-08-03 · Accepted
- **Context:** ADR-013 deferred the EU-owned alternatives and set a revisit trigger (11.14). **That
  deferral is only honest if moving stays cheap.** Left unmanaged, platform-specific behaviour
  accumulates until "we can migrate later" is false without anyone deciding it.
- **Decision:** The app and database stay deployable on **any host running a Docker image and a
  PostgreSQL service**, with **configuration changes only, never code changes**:
  1. **The `Dockerfile` is the only build artifact** — no buildpack, no platform-specific build config.
  2. **All configuration from environment variables**; no host-named settings module
     (`settings/heroku.py` is exactly the anti-pattern). **`DATABASE_URL` is the database contract.**
  3. **Bind to `$PORT`** with a local fallback, never a hardcoded port.
  4. **Migrations are an explicit release step**, never in the container start command — baking them
     into `CMD` makes every replica race to migrate on boot.
  5. **The database must be restorable from a host-independent logical dump**, maintained *in addition
     to* the host's native snapshot. Snapshots are for fast same-host rollback; the dump is what makes
     the host replaceable.
  6. **Core PostgreSQL and widely-available extensions only.**
  7. **Persistent state only in PostgreSQL and object storage**, never the app container's disk.
  8. **Every environment variable in a committed `.env.example`** — that file is the migration checklist.
- **Accepted lock-in, not fought:** Railway git-watch deploys (7.15) and the release-PR preview (12.5) —
  workflow conveniences, no data, ~a day to rebuild. Native volume snapshots (12.9) are fine *provided*
  rule 5's dump exists alongside.
- **Rejected:** **Accepting lock-in for convenience** — it would silently foreclose the residency
  revisit, the decision most likely to need reversing. **A full infrastructure abstraction** (Kubernetes,
  Terraform) — wildly disproportionate for a two-service app.
- **Consequences:** Small constraints on several tasks. **Portability is verified continuously and for
  free** — ADR-014's local Compose runs the same image with no platform involved, so a break shows up as
  a broken local environment rather than a discovery mid-migration. Ongoing cost is discipline: a future
  ADR wanting a host-specific feature must argue against this one.

## ADR-016: Phase 1 go-to-market — one pilot bakery, free, no deadline

- **Date / Status:** 2026-08-06 · Accepted
- **Context:** Five linked commercial questions determining whether billing ever enters the backlog,
  what fields `Bakery` needs, and whether permissions must gate features by plan.
- **Decision:** **First user:** one friendly Irish bakery, a real food business operator with real data.
  **Timeline:** no committed date. **Phase 1:** a **free pilot** — no payment provider, subscription
  state, billing tables or invoicing. **Eventual pricing:** a **flat per-bakery monthly subscription**,
  all features, unlimited users — recorded not because it is being built but so nothing contradicts it:
  **no feature gating by plan, no per-seat counting.**
- **Rejected:** **Paid beta / paid from day one** — one pilot tenant doesn't justify a payment
  integration, and it would put subscription state in the schema before the redesign. **Tiered pricing**
  — tiering requires feature gating inside the permission layer, permanently complicating Epics 2 and 4
  for revenue that doesn't exist. **Per-seat pricing** — makes seat counting a product concern and
  couples pricing to the role matrix, which should be driven by what people need to do.
- **Consequences:** **No billing epic exists, and none should be added** — proposing one needs a
  superseding ADR. `Bakery` (3.1) needs **no** plan/tier fields. Roles are capability-constrained, never
  plan-constrained. Multi-tenancy stays required even with one tenant, and this does **not** downgrade
  the isolation tests (6.9), which must exist *before* a second tenant. A forgiving pilot user makes
  ADR-014's local-only model comfortable for longer. **The pilot is a real controller**, so the
  per-tenant DPA (11.5) applies — "it's only a pilot" is not a GDPR exemption.

## ADR-017: Batch/lot food traceability is in scope, as its own epic

- **Date / Status:** 2026-08-06 · Accepted — entity shape settled by **ADR-033**; the allergen question
  it left open is answered by **ADR-024** (in scope, Epic 18).
- **Context:** **EU Reg. 178/2002 Art. 18** requires a food business operator to identify **one step
  back** and **one step forward**, producing records to the **FSAI** on demand. Bakery is a pure
  current-state catalogue — no delivery, batch, lot code or production run — so it cannot support that.
- **Decision:** Traceability is **in-scope**, built as **Epic 17** rather than folded into Epic 3.
  Goods-receipt lines record what arrived (supplier lot, receipt date, quantity, best-before), distinct
  from the catalogue row; production runs consume specific lots and emit a batch with its own internal
  lot code; outbound records capture where it went. **Floor:** one-step-back/forward — full internal
  mass-balance is a **Should**. **Sequencing:** depends on Epic 3, because a record without a
  trustworthy quantity isn't worth writing. **Not in scope:** HACCP, temperature/cleaning logs, allergen
  labelling as such (then open), recall workflows.
- **Rejected:** **Leaving it as the bakery's paper problem** — the pilot needs it and it is a legal
  obligation on them. **Bolting `lot` fields onto existing models** — **a lot is an event over time, not
  an attribute of a catalogue item.** This app already suffers that conflation (`RawMaterial.price` has
  no time dimension, which is why the price questions were hard); repeating it would make the schema
  actively wrong rather than merely incomplete. **A third-party traceability system** — not evaluated;
  revisit only if Epic 17 proves much larger than scoped.
- **Consequences:**
  - **The largest single addition to product scope so far** — a temporal/event layer over a current-state
    schema, so Epic 3's design had to be reviewed against it (ADR-033 did that, before Epic 3 starts).
  - **Pre-answers deletion semantics:** anything referenced by a traceability record can never be
    hard-deleted, so soft delete stops being a judgment call (3.13, 3.22, 17.6).
  - **Answers input price history as a side effect** — a receipt line carries the price paid on that date
    (17.12), which ADR-018 took up.
  - **Retention gains a legal floor GDPR minimization cannot override** — a *minimum*, commonly five
    years. Where such a record names a supplier contact, floor and policy must be **reconciled**, not
    chosen freely (10.9, 11.4).
  - **Records must be append-only** — no hard delete, no silent retroactive edit; a stronger integrity
    requirement than anything else in the schema (17.5).
  - **A partial implementation is worse than none if it looks complete** — nothing may present itself as
    a compliance record until the trace path is whole (17.7, 17.10).

## ADR-018: Costing and money semantics

- **Date / Status:** 2026-08-06 · Accepted
- **Context:** Four data-semantics questions blocking Epic 3, recorded as **one** decision because they
  only make sense together: what a price *means* determines the unit, which determines where VAT
  applies, which determines what a price-history row contains. Deciding them separately is how the
  prototype ended up recomputing cost inline in `float()` across three views.
- **Decision:**
  1. **Price basis** — `RawMaterial` stores what the invoice says: purchase price, pack quantity,
     purchase unit (€12.50 / 25 / kg). Cost per canonical unit is derived at cost time and **never
     persisted**. This is also exactly what a goods-receipt line records, so the two agree by
     construction rather than convention.
  2. **Canonical units — kilogram, litre, each**, one per dimension. Purchase units convert through a
     **factor in a reference table**, so adding "sack" or "dozen" is data entry, not a migration.
  3. **VAT — all stored money is net (ex-VAT)**, applied only at display/sale. Rates in a **dated table**
     (`code`, `percent`, `valid_from`, `valid_to`); a product references a **code**, not a number. Matches
     Irish reality, where bakery products genuinely attract different rates, and survives a statutory
     change without rewriting historical margins.
  4. **Price history — versioned, from two sources.** Input prices come free from ADR-017's receipts;
     sale prices get dated `ProductPrice` rows. Two mechanisms, because one price is an observed fact and
     the other a decision the bakery makes.
- **Rejected:** **Storing €/canonical-unit directly** — discards the invoice figure and makes the user do
  the arithmetic on every price change: a silent-error generator in the very numbers this app computes.
  **Persisting the derived unit price** — two fields that can disagree. **Gram/millilitre canonical
  units** — considered; the precision cost below is the price of not choosing them. **A plain VAT-rate
  field** — a statutory change would bulk-update every product and recompute past margins at today's
  rate. **Gross storage** — every margin calculation begins with a division, and the repeating decimals
  propagate. **Current-price-only** — makes "why did this margin drop in March?" unanswerable, which is
  exactly what Epic 16's alerts are for.
- **Consequences:**
  - **Precision and rounding are load-bearing, because the canonical units are large.** 7 g of yeast is
    `0.007`; a pinch of spice `0.0005`. Quantities need ≥ `Decimal(12,4)` (`12,6` safer), money is carried
    beyond 2 dp internally, and rounding to 2 dp happens **only at presentation** — with the rule written
    down and tested (3.50, 3.51, 6.16), not inherited from whatever Python does.
  - **Units become a lookup table, not an enum** — a conversion factor is data an enum cannot hold.
  - **Two new reference tables and their seed data** (3.52, 3.53).
  - **Which VAT rate applies to which product is a tax question** — Irish treatment of bakery goods is
    genuinely non-obvious, so the schema must let a tenant set it per product and **must not ship guessed
    assignments** (10.13).
  - **Existing data has no recorded basis** — today's values mean whatever the person typing them assumed.
    Backfilling is a per-row human-judgment exercise, not an automatic migration (3.54), before old fields
    drop (3.32).
  - **Historical margin becomes reconstructible**, turning trend reporting from speculative into cheap.
  - **The inline `float()` costing is now definitively wrong**, not merely duplicated — it cannot express
    any of the four decisions. Deleted, not patched.

## ADR-019: Deletion semantics, supplier identity, and the two administration surfaces

- **Date / Status:** 2026-08-06 · Accepted — the **uniqueness clause is amended by ADR-027**:
  case-insensitive uniqueness, declined below purely on implementation cost, is adopted once Django 4.0's
  functional unique constraints remove that cost. Every other clause stands.
- **Context:** The last three data-semantics questions, all blocking Epic 3, and the second only
  answerable now that multi-tenancy and traceability are settled.
- **Decision:**
  1. **Soft delete for anything referenced by a record that outlives it** — `Supplier`, `RawMaterial`
     (forced by traceability), `Product` (outbound records and dated prices point at it) and
     `Base_recipes` (production runs reference the recipe followed). **Ingredient lines stay
     hard-deletable** — meaningful only inside their parent.
  2. **Supplier name is unique per tenant, not globally** — two bakeries may both buy from "Odlums";
     within one tenant a duplicate is almost always a data-entry error worth blocking.
  3. **Uniqueness applies among non-archived rows only** — a partial unique index. Falls out of combining
     (1) and (2): a plain composite constraint would let archiving "Odlums" block that name forever.
  4. **Two administration surfaces, two audiences.** In-app settings is the tenant's — scoped,
     role-checked, audited. The **Django admin is superuser-only support tooling**: data repair and
     diagnosis, never linked from the tenant UI.
- **Rejected:** **Soft delete everywhere** — an archived filter on every query forever, where a missed
  filter resurrects deleted data; doubling the correctness-critical filters doubles the chance of it.
  **Soft delete only on the forced set** — deleting a `Product` would orphan its price history and
  outbound records, needing a delete block anyway, which is soft delete with worse ergonomics. **No
  uniqueness, warn only** — duplicates silently split a supplier's cost history across two unlinked rows.
  **Case/whitespace-normalized uniqueness** — a better constraint, deliberately not adopted *at the time*
  because it needed a normalized column or functional index. **Disabling the Django admin in production**
  — removes the fastest tool for repairing a pilot tenant's data, leaving `psql` against production: a
  worse risk. **Both surfaces with identical operations** — every rule enforced twice, and Django admin
  bypasses tenant-scoped managers by default.
- **Consequences:**
  - **Two orthogonal, correctness-critical filters now exist:** tenant scope and archived state. They must
    combine in **one** base manager and be tested together — filtering tenant but not archived is a bug;
    archived but not tenant is a data leak (3.55, 6.18).
  - **"Delete" now means two different things** depending on the model. The UI must say *archive* where it
    archives, and archived rows need a way back (3.56).
  - The per-tenant constraint **depends on the tenant FK first**, so 3.6 follows 3.2.
  - **The Django admin is a deliberate cross-tenant surface** — what makes it useful for support and what
    makes it dangerous. Superuser-gated (2.15), excluded from tenant navigation, access logged (11.10). Do
    **not** rely on `ModelAdmin` for tenant scoping — it does not, by default.

## ADR-020: Three per-tenant roles — Owner, Staff, Read-only — on a membership record

- **Date / Status:** 2026-08-06 · Accepted — enforcement completed by **ADR-027** (posture) and
  **ADR-028** (permission codenames on a custom auth backend).
- **Context:** Four roles were originally proposed and the capability matrix was open; 2.8 can't be
  implemented until the roles exist. Access control today is partly in templates, partly absent.
- **Decision:** **Three roles per tenant** — **Owner** (full administration of their own bakery),
  **Staff** (daily work: materials, recipes, products, receipts, production runs; no user management or
  tenant settings), **Read-only** (view and export, no writes — the accountant/auditor seat). **The role
  lives on a membership record** (user × bakery × role), not on the user: Django's global `Group` cannot
  express "Owner of bakery A", and the membership model means a user *could* belong to several tenants
  without a schema change. **"Manager" is deliberately deferred**, not rejected — a real distinction in a
  larger bakery, but the pilot can't articulate it, and a role whose permissions are guessed is worse than
  one that doesn't exist.
- **Rejected:** **Four roles including Manager** — adding it later is a table row, not a reshape,
  *provided* checks are capability-based. **Two roles (Admin/Staff)** — with no read-only tier an
  accountant gets either write access or a shared login, and shared logins destroy the audit trail Epics
  11 and 17 depend on. **Django groups plus granular per-tenant editable permissions** — makes "who can do
  what" per-tenant configuration that can't be reasoned about or tested centrally, and the test matrix
  becomes combinations rather than three roles.
- **Consequences:** **Checks must be capability-named, not role-named** — this is what keeps Manager cheap
  to add, and it costs nothing now (2.16). **Read-only can export**, deliberately — so every export is
  audit-logged, and **that logging is what makes it acceptable, not the role restriction.** **Traceability
  writes are Staff-level**, but those records are append-only, so a mistaken entry is corrected by a new
  record — the role model and integrity model must be implemented together. Every existing user has no
  role; assigning one is a migration with a human decision in it (3.57).

## ADR-021: Non-functional targets

- **Date / Status:** 2026-08-06 · Accepted
- **Context:** The whole NFR table was open, blocking 5.12 and leaving Epic 5's rewrite with no target.
  Cheapest to decide *before* templates are rewritten, since accessibility and localization are far more
  expensive to retrofit.
- **Decision:** **Performance** — p95 < ~500 ms normal pages, < ~2 s dashboard costing aggregate, ~10
  concurrent users/tenant, on thousands of rows. **Accessibility — WCAG 2.2 Level A.** **Devices** — one
  responsive UI, phone→desktop, current and previous major Chrome/Firefox/Safari/Edge; no IE11, no native
  app. **Localization** — English and euro only, but translation-ready: `gettext` on display text, one
  currency formatter, **no hardcoded `€`**.
- **Rejected:** **No numeric performance target** — leaves nothing to check against, so "is this a
  regression?" becomes a judgment call every time. **Sub-200 ms enforced in CI** — Railway Hobby shares
  CPU, making it partly unenforceable, and the machinery is disproportionate. **WCAG 2.2 AA** — the
  recommended option and not chosen; see below. **No accessibility target** — Level A is cheap during a
  rewrite and makes it a requirement rather than a future bug report. **Desktop-first** — goods receipts
  get recorded at the delivery door on a phone. **Mobile-first** — costing views are inherently wide
  tables. **Hardcoded English/€** — makes the expansion trigger expensive exactly when it fires.
  **Multi-language/currency now** — the next countries are undecided, and multi-currency touches every
  money column and the whole costing service.
- **Consequences:**
  - **Level A is below what procurement typically asks for** — it excludes AA's contrast ratios (4.5:1),
    visible focus indicators, consistent navigation and error suggestions. Fine for a pilot with known
    users, and worth naming: the gap becomes real the first time a tenant has a staff member who needs it,
    or a buyer asks for a conformance statement — likeliest at EU expansion, where public procurement and
    the European Accessibility Act point at AA. **Revisit trigger 10.15.** Semantic HTML and real labels
    keep the remaining distance small.
  - **Performance targets need something to measure them** — unverifiable until Epic 7 exists, so a
    documented budget now and an observed one later, not a CI gate (5.14, 7.20).
  - **Translation-readiness is a discipline, not a feature** — Epic 5 must not introduce a single hardcoded
    `€`, including in existing templates it touches (5.15, 5.16).
  - Wide costing tables need a deliberate small-screen strategy, not overflow (5.13).

## ADR-022: Goods receipts drive raw-material cost; lines accept a material **or** a base recipe

- **Date / Status:** 2026-08-06 · Accepted
- **Context:** Two questions that turned out to be domain-model ones. Once receipts exist, the price
  paid is recorded twice — receipt and `RawMaterial` — so which one costing believes must be settled.
  And `Base_recipes` and `Product` are parallel and **disconnected**: a base recipe's cost can never
  reach a product, so base recipes are a calculator nothing consumes. Half a feature.
- **Decision:**
  1. **The latest goods receipt sets current cost** — most recent by **receipt date** (not entry date),
     ties by creation time, so a late-entered back-dated delivery behaves correctly.
  2. **A manual price stays possible, labelled an estimate** — a material never received must still be
     costable, otherwise planning before the first purchase is impossible.
  3. **Every cost figure carries its provenance** — a margin from a guess and one from an invoice are
     not the same claim.
  4. **A line references either a raw material or a base recipe**, and costing recurses.
- **Rejected:** **Receipts as traceability only, price by hand** — the same figure entered twice with
  nothing detecting divergence: the exact failure ADR-018 removes. **Receipt price as the *only* price**
  — a material with no receipt couldn't be costed at all. **Keeping the two disconnected** — one dough
  used in six products would be restated six times, and a flour price change means editing six products.
  **Merging both into one model with an `is_sellable` flag** — genuinely cleaner and not chosen: a larger
  migration, and it collapses a distinction the bakery may think in. (Decision 4 makes the two line
  models identical, so this gets easier later — ADR-032 collapses the *lines* and keeps the parents.)
- **Consequences:**
  - **Recursive costing introduces a cycle risk that must be prevented, not merely avoided.** A recipe
    containing itself, directly or transitively, loops forever. Needs save-time validation plus a depth
    guard (3.59, 4.16) and a test (6.20). **The most important consequence here** — nothing in the
    current schema prevents it.
  - **`recipe_yeld` becomes load-bearing** — cost must be expressible per unit of yield, so the yield
    needs a real numeric value and a unit (3.60).
  - **Substantially answers the ingredient-line question** — both models now need a typed *component*
    reference as well as a typed parent, making them identical (settled by ADR-032).
  - **Provenance has to be modelled, not just displayed** (3.62, 4.17) — retrofitting it into a bare
    `Decimal` is painful.
  - **Receipt and material share one price shape**, so 3.10 and 17.1 must use the same definition.
  - **Point-in-time costing becomes possible but is out of scope** — deferred to trend reporting.
  - Epic 17's trace (17.7) and this recursion are the same traversal in opposite directions; allergen
    aggregation (18.3) is a third.

## ADR-023: Dashboard becomes an overview; settings becomes tenant self-administration

- **Date / Status:** 2026-08-06 · Accepted
- **Context:** The last two "requirements by area" questions, now that tenants and roles exist and the
  Django admin is narrowed to superuser support tooling.
- **Decision:** **The dashboard becomes a genuine overview** — summary strip (product count, average
  margin, materials with no or stale pricing), worst-margin products, recent input price movements; the
  full product list moves to its own page. **The settings area becomes the tenant's self-administration
  surface**, owned by Owner: invite/remove users and set roles, edit bakery details, manage reference
  data, run exports; Read-only reaches exports and nothing else writable. This is the surface the Django
  admin deliberately is **not**.
- **Rejected:** **Keeping the dashboard as the cost/margin list** with better sorting — lower-risk, but
  the overview is where price history pays off. **Fixing only the math** — too little given Epic 5 is
  rewriting templates anyway. **Keeping reference data in the Django admin** — every unit or VAT change
  becomes a support request. **Superuser-side user management only** — leaves Owner with nothing to
  administer and makes onboarding tenant #2 manual.
- **Consequences:**
  - **The dashboard depends on Epic 3, not just Epic 5** — price movements and staleness need dated
    prices and receipts, so it is sequenced after Epic 3 despite being frontend work (5.18).
  - **"Stale" needs a definition** (10.16) — a badge on an arbitrary threshold trains users to ignore it.
  - **Inviting users requires email, which the app does not send** — turning a hypothetical processor row
    into a required one: a provider chosen (9.22), configured from env vars, DPA'd (11.6) before
    invitations ship. A new external dependency created by this decision.
  - **Tenant-editable reference data is not uniformly safe.** VAT rates and categories are fine; **unit
    conversion factors are not** — a wrong factor silently corrupts every dependent cost with no error
    anywhere (10.17).
  - **This replaces the broken user-delete view rather than patching it** — 6.7's regression test still
    applies, but the fix is the rebuilt surface (5.19).
  - The overview's aggregates run against the p95 < 2 s budget — the reason ADR-028's service layer is
    batch-first.

## ADR-024: Feature backlog prioritization (MoSCoW pass)

- **Date / Status:** 2026-08-06 · Accepted — the AI-insights "re-scope before spending" is **discharged
  by ADR-036**.
- **Context:** The backlog had no priorities, leaving epic sequencing (13–18) and several Epic 5 tasks
  without a basis for ordering.
- **Decision:** **Must** — traceability (legal obligation) · multi-tenancy (architectural foundation) ·
  real search/filter (the current inputs exist and do nothing, which is worse than absent) · supplier
  price comparison (core buying-decision value) · user & role management (**merged**, not separate — it
  *is* ADR-023's settings area assigning ADR-020's roles). **Should** — tenant export (differentiator) ·
  GDPR export (the Article 20 fix) · trend reporting (the data foundation is free from ADR-018/022, but
  full trends need months of data that won't exist at launch) · allergen data (a legal obligation riding
  on ADR-022's recursion — aggregating allergens up a tree is the same traversal as cost; **new Epic
  18**). **Could** — product photos (cosmetic for a costing tool) · stock/quantity-on-hand (receipts
  *imply* it, but claiming stock figures are accurate is a materially bigger promise than claiming a cost
  is; not an epic) · AI insights. **Won't this round** — profile pictures (personal data with an
  undecided legal basis, a storage DPA and erasure obligations, for no operational value at a one-tenant
  pilot) · self-service registration (open signup with no billing gate produces spam tenants and
  abandoned accounts holding personal data you must then retain and delete) · billing.
- **Rejected:** **Search as Should** — dead inputs in a freshly rewritten UI are indefensible, and the fix
  is cheap while templates are open. **Reporting as Must** — charts over one week of data aren't
  persuasive. **Media as Should** — it would put the profile-picture legal basis on the critical path.
  **Supplier comparison as Could** — the cautious call, rejected since the user rates it core value.
- **Consequences:**
  - **Supplier comparison as a Must forces a schema change beyond Epic 3's scope.** `RawMaterial` has a
    **single** supplier FK, so a comparison view would show one row. The fix follows from ADR-022: the
    real relationship belongs on the **goods receipt**, so the FK becomes at most an optional *preferred
    supplier* (3.63, view in 5.21). **This makes the feature depend on Epic 17**, not merely Epic 3.
    Sparse until receipts accumulate across suppliers — expected, not a defect.
  - **Epic 13 narrows to product photos only**, taking 11.3 off the critical path.
  - **Search moves into Epic 5 proper** — 5.9 resolves to *build it*.
  - **ADR-023's overview is the whole of the reporting story for the first release** — said plainly so it
    isn't quietly expanded.
  - **Allergen data becomes Epic 18**, reversing ADR-017's "still open" — deliberately outside Epic 17 so
    the Art. 18 core isn't delayed. **Same care as traceability:** allergen information that looks
    authoritative but is incomplete is worse than none, because a consumer-facing claim depends on it
    (18.5).
  - **Stock stays excluded**, but the traceability entities must be designed so on-hand *could* later be
    derived (ADR-033 discharges this with `Consumption.quantity_consumed`).
  - **Tenant onboarding answered in practice** — manual provisioning, staff via Owner invitations; public
    signup not built. Revisit at tenant #2 or when billing exists to gate it.

## ADR-025: Runtime baseline — Django 5.2 LTS on Python 3.13, direct from 3.2

- **Date / Status:** 2026-08-10 · Accepted — package list **amended by ADR-029** (`Pillow`); unlocked
  capabilities adopted in **ADR-027**.
- **Context:** Everything the app runs on is past end of life — Python 3.8 (Oct 2024), the Dockerfile's
  3.9-slim (Oct 2025), Django 3.2 (April 2024). The old candidate text ("3.12 primary, validate 3.13
  later") was written when 3.12 was current; **it had quietly aged into a recommendation to start a new
  build on an unsupported runtime.** Recorded as **one** decision because the Django version determines
  the Python range, which determines the driver and the rest of the pin set.
- **Decision:**
  1. **Django 5.2 LTS — not current stable.** Verified 2026-08-10: 5.2 is supported to **April 2028**;
     stable 6.1 only to Dec 2027; and 6.0 left mainstream support on **4 August 2026**, six days before
     this decision. The older LTS has the longer runway. Next hop **6.2 LTS** (April 2027 → April 2030).
  2. **Python 3.13** — supported by *both* ends of the path (5.2 takes 3.10–3.14, 6.2 takes 3.12–3.14),
     so the 6.2 upgrade needs no Python change. `python:3.13-slim` is the **single** place the version
     lives; `runtime.txt` is deleted, not updated.
  3. **Upgrade directly, 3.2 → 5.2** — no staged stop at 4.2.
  4. **Its own epic (19)**, after Epic 2 and before Epic 3.
  5. **`psycopg[binary]` 3** replaces `psycopg2-binary` — native since Django 4.2, and a new build is the
     cheapest moment to switch drivers.
  6. **The dependency set is a rule, not pins in this ADR:** latest release compatible with 5.2/3.13 *at
     lock time*. Confirmed 2026-08-10 — `whitenoise` 6.12.0, `django-environ` 0.14.0, `Pillow` 12.3.0.
     Four removed outright: **`asgiref`/`sqlparse`** (Django's own transitive deps — they belong in the
     lock file, not a hand-maintained list where they can contradict Django); **`pytz`** (dropped in 5.0,
     `zoneinfo` replaces it, nothing imports it); **`environ==1.0`** (an unrelated package whose
     top-level module collides with `django-environ`'s — an install slip and a live hazard); and
     **`dj-database-url`** (imported nowhere, duplicates `env.db()`).
  7. **`django-mathfilters` dropped** — last released Feb 2020, classifiers stop at Django 3.x: a hard
     blocker, not a preference. Its two templates do cost arithmetic **in the template**, which ADR-018
     ruled wrong.
- **Rejected:** **Django 6.1** — a *shorter* window than the older LTS, and it puts a solo developer on
  the 8-month feature treadmill; 6.0 dropping out of support that week is the demonstration. **Staged
  3.2 → 4.2 → 5.2** — the conventional advice, rejected on two grounds: staging exists so a test suite
  catches each release's removals, and every `tests.py` here is an empty stub, so it means running the app
  manually three times and getting three chances to be wrong; and **most of the code that would break is
  already scheduled for deletion** — the inline `float()` costing, the models Epic 3 restructures, the
  templates Epic 5 rewrites. **Migrating it carefully through 4.2 preserves a corpse.** **Python 3.12** —
  security-fixes-only since Oct 2025. **Python 3.14** — not on stability but on span: it needs 5.2.8+,
  and 3.13 covers the whole path through 6.2. **Keeping `psycopg2-binary`** — maintenance-only upstream,
  and deferring means switching later against a schema holding real tenant data. **Pinning exact patch
  versions here** — stale within weeks in an append-only log. **The ADR fixes the constraint; the lock
  file fixes the versions.**
- **Consequences:**
  - **Creates Epic 19** — the execution order already said "then the upgrade itself", but no epic held it.
    Added rather than smuggled into Epic 1, so it gets its own branch and PR.
  - **It must run before Epic 3**, which writes a large migration set that would otherwise need
    re-verifying on 5.2.
  - **Django 5.0's `USE_TZ` flip is a non-event here** — already set explicitly. Verified and recorded so
    it isn't re-investigated (19.7).
  - **The safeguard replacing the staged upgrade is a deprecation sweep on 3.2 first** (19.1) — checks
    under `-Wall`, clearing every `RemovedInDjango*Warning`. That is what staging would have surfaced. It
    is **not** equivalent to having tests, and saying so plainly is part of accepting this route.
  - **Verification is a manual pass over every screen** (19.8) — the largest accepted risk in the epic.
  - `requirements.txt` drops twelve → ~six *(five after ADR-029 removes `Pillow`; six again once ADR-031
    adds `sentry-sdk[django]`)*, with UTF-8 re-encoding in the same pass.
  - **April 2028 is a real deadline** — the 6.2 hop is scheduled work (19.13). Django 6.x also drops
    Python 3.10/3.11: irrelevant at 3.13, but noted so any future "pin Python back for package X" is
    recognised as closing the door on 6.2.
  - Leaves 9.4 (WSGI/ASGI) deliberately open, waiting on 9.20.

## ADR-026: Pin PostgreSQL 17 across every environment

- **Date / Status:** 2026-08-10 · Accepted
- **Context:** ADR-015 rule 6 requires a version every candidate host offers, so a logical dump restores
  cleanly. Today it is pinned nowhere — `docker-compose.yaml` has **no Postgres service at all**, so
  nothing records which major the app is developed or deployed against.
- **Decision:** **PostgreSQL 17**, pinned identically everywhere — explicit `postgres:17` locally, and 17
  on Railway. Local and production **majors must match**; a bump is deliberate and restore-tested, never
  drift.
- **Rejected:** **`postgres:latest`** — turns a major bump into something that happens on a `docker pull`,
  against a production database that cannot follow. **Staying on 15/16** — no feature need, and it
  shortens the runway (17 is supported into late 2029). **Leaving it unpinned** — the state rule 6 exists
  to prevent, and it makes the dump/restore drill untrustworthy since `pg_dump` must match the server.
- **Consequences:** The local compose file needs a Postgres service it lacks (19.10) — and it is broken as
  written anyway (`web` joins `my_network`; the file defines `bakery_simple`), so this is a fix, not new
  scope. ADR-014 makes that file the only integration-test environment, so it must actually run. The
  pilot's data must be restored from the home server's version into 17 during Epic 12 (12.6) — **a
  cross-major restore**, precisely what rule 5 and the 3.46/3.47 traps are about.

## ADR-027: Adopt the capabilities the Django 5.2 / PostgreSQL 17 upgrade unlocks

- **Date / Status:** 2026-08-11 · Accepted — **amends ADR-019**'s uniqueness clause.
- **Context:** The app jumps four Django feature releases at once, and several provide, as framework or
  database features, things this project planned to hand-build — or had **deferred specifically because
  hand-building them was too expensive.** Decided now because three of them change *how* Epics 2, 3 and 5
  are built. Release notes verified 2026-08-11.
- **Decision — adopt, each with a task:**

  | # | Capability | Why | Task |
  |---|---|---|---|
  | 1 | **`LoginRequiredMiddleware`** (5.1) as the default posture, `@login_not_required` on exceptions | Authentication stops being opt-in and becomes opt-out. Changes the shape of 2.6/2.7 — the mixin is still correct but no longer the mechanism | 2.17 |
  | 2 | **`SECRET_KEY_FALLBACKS`** (4.1) | Rotation without invalidating every session — what turns 8.6's runbook into a procedure someone would run | 2.18 |
  | 3 | **Case-insensitive supplier uniqueness** — `UniqueConstraint(Lower("name"), "bakery", condition=…)` | **Amends ADR-019**, which declined it for one stated reason: it "needs a normalized column or a functional index". Functional unique constraints (4.0) make it one declaration, so the only argument is gone. The failure it prevents — a duplicate splitting one supplier's price history — is unchanged | 3.64 |
  | 4 | **Constraint validation in the model/form layer** via `full_clean()`/`validate_constraints()` (4.1), with `violation_error_message` | Without it, every rule Epic 3 adds reaches the user as an `IntegrityError` 500 instead of a field error | 3.65 |
  | 5 | **`db_comment`/`db_table_comment`** (4.2) | The schema carries meaning invisible from a column name — money net of VAT, canonical kg/l/each, `purchase_price` vs. derived cost. Held in the database it is visible from `psql` and cannot drift from the table | 3.66 |
  | 6 | **`db_default`** (5.0) | Removes a separate data-migration step per column on populated tables | 3.67 |
  | 7 | **`as_field_group()`** (5.0) over div-based templates (4.1) as Epic 5's default rendering | Real label association, `aria-describedby`, `aria-invalid`, `<fieldset>`/`<legend>` — a material share of Level A from the framework rather than hand-written markup | 5.22 |
  | 8 | **`{% querystring %}`** (5.1) | Filter-preserving pagination for 5.9's search | 5.23 |
  | 9 | **Native psycopg pooling** (5.1) + `CONN_HEALTH_CHECKS` (4.1) | **Closes the pooling question**: the answer is neither `CONN_MAX_AGE` tuning nor PgBouncer — it is in-process, so one less service to run, monitor and patch | 7.19 |
  | 10 | **PostgreSQL 17 `pg_stat_statements`** (split shared/local block I/O timing, `stats_since`) | The measurement basis for the p95 budgets, which nothing currently measures | 7.20 |
  | 11 | **`COPY … ON_ERROR ignore`** (PG 17) | 3.54's backfill is a per-row judgement exercise, where one bad row aborting the import is a real obstacle | 3.68 |
  | 12 | **`pg_restore --transaction-size`** + parallel large-object restore (PG 17) | 3.48's drill only has value if it stays fast enough to keep running | 3.69 |

  **Also required, not optional:** `STATICFILES_STORAGE`/`DEFAULT_FILE_STORAGE` were deprecated in 4.2 and
  **removed in 5.1**, so the `STORAGES` dict is a **prerequisite of the upgrade itself** (19.14), not an
  Epic 13 nicety. Its two keys are exactly ADR-005's media/static split (13.11).
- **Rejected:**
  - **Adopting nothing** — for items 1, 3, 4 and 7 the hand-built version is strictly worse code that must
    then be maintained, and item 3 was *already* judged worth having and rejected only on cost.
  - **`GeneratedField` (5.0) for cost and margin** — the most attractive-looking option here and **rejected
    on a technical constraint, not preference.** PostgreSQL supports only `STORED` generated columns through
    17, and the expression must be immutable and reference **only columns of the same row** — no joins, no
    subqueries. Every derivation here crosses rows: cost per canonical unit needs the conversion table,
    gross price the dated VAT table, product cost recurses through lines. **Recorded explicitly so it is
    not re-proposed by the next person reading the 5.0 release notes.**
  - **PG 17 incremental backup** — needs filesystem access to the data directory and `summarize_wal`, which
    managed Railway does not offer. It does **not** close ADR-013's PITR gap.
  - **Redis cache backend (4.0)** — **not decided either way** here, deliberately recorded as undecided
    rather than rejected, with the trigger being the dashboard measured against p95 < 2 s. *(ADR-028 then
    decided it.)*
  - **Async views / async ORM (4.1)** — nothing in scope needs them, reinforcing gunicorn for 9.4.
  - **`CompositePrimaryKey` (5.2) for the membership record** — theoretically the correct shape for
    user × bakery, but it cannot be a ForeignKey target and has limited admin support. A surrogate key plus
    `UniqueConstraint(user, bakery)` costs nothing and stays boring (3.58).
- **Consequences:** **Three of these change how downstream epics are built** — item 1 reshapes 2.6/2.7,
  item 3 adds a constraint to Epic 3, item 7 sets Epic 5's rendering path — and they are only available
  **if Epic 19 lands first**, an independent argument for ADR-025's sequencing. **`STORAGES` is required by
  the upgrade**, though the failure is quiet: a removed setting is ignored, so the site keeps working while
  compression and cache-busting silently stop. **The louder consequence lands in Epic 5** — every template
  hardcodes `/static/...`, so manifest hashing has never done anything; when 5.3 switches to `{% static %}`
  it starts raising `ValueError` at render time for any missing file, turning a silent 404 into a 500
  (mitigated by sequencing 5.3 after 1.3, and 1.13's CI `collectstatic`). Adds 13 tasks; several *reduce*
  work already scoped. **Item 4 has a testing consequence** — error paths become reachable from form tests
  rather than only DB-level integration tests: cheap tests of expensive rules.

## ADR-028: Backend architecture — settings, a batch-first service layer, no API, no cache, Brevo

- **Date / Status:** 2026-08-13 · Accepted — completes ADR-020/ADR-027 on auth, closes the caching question.
- **Context:** The last block of open backend rows, five of six blocking a task. Decided together because
  they are not independent: the service layer is where caching would attach, the permission mechanism
  determines whether that layer takes a user or a membership, and adopting Django's auth views is what makes
  email a first-release requirement. Provider facts verified 2026-08-13.
- **Decision:**
  1. **Settings — `base.py` + `local.py` + `test.py`, no `production.py`.** `base.py` *is* production rather
     than a parent nothing runs: all config from the environment, and **no default at all** for
     `SECRET_KEY`/`ALLOWED_HOSTS`/`DEBUG`, so a missing variable raises `ImproperlyConfigured` at boot.
     Overlays opt *into* unsafe or convenient behaviour. The property bought is that **the accident lands on
     the safe side** — a forgotten `DJANGO_SETTINGS_MODULE` yields production settings. Today it yields the
     opposite: `base.py` ships a hardcoded `SECRET_KEY`, `DEBUG = True` and live credentials, and
     `heroku.py:11` defaults `DEBUG` to `True` in the *production* module.
  2. **Business logic — `control/services/`, plain functions, batch-first.** Module-level functions grouped
     by concern with explicit arguments, returning frozen dataclasses carrying amount, canonical unit,
     provenance and as-of date together. **The batch entrypoint is the primary API**; single-object costing
     wraps it. Models keep fields, constraints and managers and lose costing entirely — the `@property`
     methods are **deleted, not left as delegators**.
  3. **API layer — none, no framework pre-selected.** Machine-readable endpoints are plain `JsonResponse`
     views. **Revisit trigger,** any of: a second non-first-party consumer; a native app or SPA client
     committed to; or machine endpoints exceeding roughly six.
  4. **Auth — Django's auth views; capabilities as Django permission codenames.** `accounts/views.py` and
     `accounts/urls.py` deleted. Middleware resolves the active bakery and membership onto the request, and a
     **custom authentication backend** implements `has_perm()` by mapping role → static capability set.
     Everything downstream stays stock Django.
  5. **Caching — none in the first release.** Query design is the lever. **Escalation ladder, in order,** only
     once 7.20 measures the dashboard over p95 < 2 s on realistic data: (a) fix the queries, (b) per-view
     cache with a short TTL keyed by a per-tenant version stamp, (c) Redis **only** if (b) needs cross-worker
     coherence. The batch API takes the version stamp from day one (4.20).
  6. **Email — Brevo over SMTP**, Django's built-in backend, credentials from env vars; console in `local.py`,
     locmem in `test.py`. No dependency, provider swappable by configuration alone.
- **Rejected:**
  - **Four settings modules including `production.py`** — makes `base.py` a module never loaded and therefore
    never tested, and requires `DJANGO_SETTINGS_MODULE` to be right in three places where being wrong silently
    loads that untested module. **A single env-driven `settings.py`** — test-only settings become `if`
    branches in the one file hardest to test.
  - **Fat models, corrected in place** — the conventional answer, rejected on structure not taste: ADR-023's
    dashboard costs every product in one request, and a per-instance `@property` recursing through nested
    recipes issues queries per node and cannot memoise across the walk, so meeting the budget means growing a
    second parallel batch path — the service layer, arrived at by accident. Separately, provenance means the
    answer is a value object, which a property returning a `Decimal` cannot express.
  - **An ORM-decoupled `domain/` package with repositories** — buys database/framework portability nobody
    asked for; ADR-015 requires *host* portability, which Docker plus `DATABASE_URL` already delivers.
  - **DRF now, read-only** — a second authentication and permission surface to keep synchronised with
    memberships, and a second tenant-scoping path to test for leaks, for a consumer that does not exist.
    **Pre-selecting a framework for later** (django-ninja) — ADR-025 had just demonstrated the failure mode
    when the Python 3.12 candidate aged out before implementation. **Name the trigger, not the tool.**
  - **`django-rules`** — a good fit, rejected on proportion: it plugs into the same `has_perm` points the
    custom backend does, buying predicate composition against a matrix of three static roles. Reconsider if
    per-object rules multiply.
  - **A hand-rolled capability module with its own mixin** — templates lose `{% if perms %}` and need a custom
    tag, Django admin keeps its own system regardless, and the result is two vocabularies for "is this
    allowed" — precisely how the current ad hoc template checks came about.
  - **A thin `LoginView` subclass** — its one motivation is choosing a landing tenant for a multi-membership
    user, which doesn't exist yet. Re-add it when the second membership does.
  - **Redis now** — the stated ~$2–3/mo is not the real cost; the real cost is that the full invalidation
    matrix must be correct on day one across receipts, recipe edits, cascading base-recipe edits, VAT rows and
    price rows. **`LocMemCache`** — per-worker, so two users can be served figures cached at different moments
    and a recipe edit is visible to neither: acceptable for a blog, not for the number a product is priced
    against.
  - **Resend** — the best DX of four evaluated, **rejected on a verified fact**: EU residency is Pro-only at
    $20–35/mo, over three times the entire infrastructure budget, to meet a constraint Brevo, Mailjet and
    Scaleway TEM all meet free. **Mailjet** (EU DCs, ISO 27701, 6,000/mo free) and **Scaleway TEM** (French,
    EU-only, €0.25/1,000) were viable; Brevo won on EU ownership *and* hosting aligning, a DPA by default, and
    the largest free headroom (300/day vs. <100/month expected). **`django-anymail`** — bounce webhooks and
    analytics are worth having at volume, not under 100 emails a month; the escalation path if deliverability
    becomes a question.
- **Consequences:**
  - **Unblocks five tasks and cancels one** — 1.5 rescoped to three modules; 4.1, 4.5, 5.19 unblocked; **4.15
    cancelled**, not deferred.
  - **4.5 is smaller and safer than recorded.** `bakery/urls.py` includes `django.contrib.auth.urls` but
    **never includes `accounts.urls`**, so `user_login` is unreachable — it even renders `'login.html'`, a path
    that does not exist. **The password-logging `print()` at `accounts/views.py:20-21` is therefore dead code,
    not a live leak**, which lowers 2.10's severity and removes 4.5's dependency on it.
  - **Email is now a first-release blocker, for a reason ADR-023 did not have** — adopting Django's auth views
    adopts its email-only password reset, so email gates the recovery path for every user (5.24, 7.21, 7.22).
  - **Two endpoints are carved out of the p95 < 500 ms budget** — invitation and password-reset POSTs send SMTP
    inline. No task queue exists, and decision 5 declined Redis, so Celery for a few dozen emails a month would
    drag it back in. Deliberate and documented (10.18).
  - **A permission-cache watch item** — Django caches permissions on the user object, so it must be invalidated
    whenever the active tenant changes, or a two-membership user carries bakery A's capabilities into bakery B
    (2.21): a cross-tenant leak of exactly the kind ADR-008 requires tests for.
  - **Two gaps surfaced that no epic covered** — brute-force protection (2.22) and credential-free failed-login
    auditing (2.23).

## ADR-029: Dependency management — `uv pip compile` over a three-file `requirements/` split

- **Date / Status:** 2026-08-16 · Accepted — **amends ADR-025** on `Pillow`.
- **Context:** ADR-025 fixed the version **rule** while refusing to pin in an append-only log, leaving the
  mechanism undecided and 19.12 the only blocked task in Epic 19. The two rows are one decision: "every
  dependency has a named owner and a stated purpose" has to live *somewhere*, and where it lives is a property
  of the file layout. The hygiene row's "unreviewed" state was already stale — ADR-025 performed that review
  and removed six of twelve entries. **What remains is not an audit but a rule that keeps the audit true.**
- **Decision:**
  1. **`uv`, in `pip compile` mode** — hand-edited `.in` → fully-pinned `.txt` in ordinary requirements format.
     Deliberately **not** `uv sync`/`pyproject.toml`: the requirements format is what the `Dockerfile`, Railway
     and every fallback host already consume, so this adds determinism **without changing the install path
     anywhere.** `uv` is build tooling at a **pinned** version, never an app dependency.
  2. **Three sources, three locks** — `base.in` (shared runtime), `dev.in` (`-r base.in` + tooling never in the
     image), `prod.in` (`-r base.in` + production-only), and generated `*.txt`. The root file is deleted.
     `prod.in` starts as nothing but `-r base.in`, deliberately: the value is **a named artifact the
     `Dockerfile` points at** that structurally cannot pick up dev tooling.
  3. **Determinism** — `--generate-hashes` at compile, `--require-hashes` at install, so a re-uploaded or
     substituted artifact fails the build instead of shipping; `--python-version 3.13` so resolution matches
     the image; and `dev`/`prod` compiled with `-c base.txt` so a shared package cannot resolve twice.
  4. **The `.in` file *is* the register** — every line carries a comment naming its purpose and owning task, and
     **a dependency without one is removed at the next recompile rather than researched later.** Transitive deps
     exist only in the generated `.txt`, which is never hand-edited; the fix for a wrong pin is a recompile.
  5. **Refresh** on `.in` change, on a security advisory naming a pinned package, otherwise monthly. ADR-025's
     "latest compatible at lock time" is evaluated at **each** recompile.
  6. **`Pillow` removed until Epic 13** — no `ImageField` and no import exists (verified 2026-08-16). It is the
     first thing rule 4 catches, and applying the rule to the package that prompted it is the point.
- **Rejected:** **`pip-tools`** — the documented candidate and the closest call; identical layout and
  near-identical output, so nothing structural depends on the choice. Lost on trajectory: `uv` resolves an order
  of magnitude faster (billed per-second build time and CI minutes on a ~$6/mo budget) and is where active
  development has moved. Migration back is one command line. **Poetry/PDM** — move declaration into
  `pyproject.toml` with a bespoke lock format, changing the install path in the `Dockerfile`, CI and host, and
  abandoning the split: a project-layout migration bolted onto a framework upgrade with no test suite.
  **`pip freeze`** — pins with no record of what was actually asked for, so direct/transitive is lost and rule 4
  is unenforceable; roughly the current state, which is how `environ==1.0` survived unnoticed. **Skipping
  hashes** — considered seriously (friction for ad hoc local installs), kept because pins alone don't deliver
  determinism against a mutated artifact. **Waiting for 9.17 to decide `dev.in`'s contents** — the contents
  depend on 9.17; the layout and rules do not.
- **Consequences:** **Unblocks 19.12.** **The `Dockerfile` changes twice in Epic 19** (19.3 base image, 19.16
  install) — same lines, one pass. **19.2 removes seven entries, not six**; `base.in` ends at **five** direct
  dependencies *(six once ADR-031 adds Sentry)*. **CI gains a drift check** (19.17) — without it the generated
  files are only as current as the last person who remembered, the failure rule 4 exists to prevent. **A monthly
  recompile is a standing chore with no owner but the solo developer** — named rather than pretended away. The
  hygiene promise is now falsifiable: a line without an owner comment is a visible defect in review. *(ADR-030
  extends the rule to vendored frontend assets, which `requirements/*.in` cannot see.)*

## ADR-030: Frontend — a shared template base, Bootstrap 5.3, HTMX, and deliberately no Node build step

- **Date / Status:** 2026-08-16 · Accepted — closes the Frontend table and the template half of quality
  tooling; **rejects** that file's own Vite candidate.
- **Context:** Decided against a frontend that was **measured**, not assumed (2026-08-16): 32 templates, 4,277
  lines, **zero `{% extends %}` and zero `{% include %}`**, 31 with full `<!DOCTYPE>` boilerplate and the navbar
  duplicated 32×; **zero `{% static %}`** with 23 templates hardcoding `/static/...`; Bootstrap **5.0.0**
  vendored (May 2021) against a current 5.3.x — the *same major*; **7 custom JS files, all 0 bytes**; 16 CSS
  files, 922 lines, four byte-identical; and no Node tooling at all. **The interactivity layer is not thin, it
  is absent** — which is what moves this decision.
- **Decision:**
  1. **Shared `base.html` plus `{% include %}` partials.** No competing option was in play; the measurement is
     the argument. `django-template-partials` **not** adopted — a dependency for ~4 fragments.
  2. **Stay on Bootstrap, 5.0.0 → 5.3.x.** Same major, so the classes stay largely valid: an upgrade, not a
     restyle. Buys four years of fixes and component semantics serving the Level A target, and keeps Epic 5 on
     structure rather than appearance.
  3. **No asset pipeline — this rejects Vite.** It would add Node, a `package.json` and a second lockfile right
     after ADR-029 standardized the Python one, plus CI steps, **to bundle zero bytes of JavaScript** while
     duplicating cache-busting and compression whitenoise already provides. Instead: consolidate the CSS, native
     custom properties and nesting, whitenoise for hashing. **Revisit** past a few hundred lines of custom JS, or
     SCSS-variable-level Bootstrap customization.
  4. **HTMX**, vendored at a pinned version, plus small vanilla modules — one ~14KB script, no bundler, server
     returns HTML fragments (what ADR-028 assumed when rejecting an API layer). Built as **progressive
     enhancement**: every form and link must work with JavaScript disabled, which Level A requires anyway.
  5. **No SPA** — a ratification; the API-layer and device-matrix decisions had already foreclosed it.
  6. **`djlint`** for templates — a pip package, so no Node in dev either. `stylelint`/`prettier` deferred on the
     same grounds as clause 3.
- **Rejected:** **Vite** — the right tool for a frontend this project does not have; reversible in a day if the
  trigger fires. **`django-compressor`/libsass** — the no-Node way to keep SCSS, but it adds a Python dependency
  and a compile step overlapping whitenoise's job, and libsass lags dart-sass: some of both options' downsides
  for little of either's benefit. **Tailwind** — rewrites markup in all 32 templates and forces Node back in
  regardless. **Hand-written modern CSS, no framework** — 922 lines is small, but it hands a solo developer
  ownership of responsive tables, form styling, modals and the whole accessibility surface, against a WCAG
  target: the opposite of the intent. **Vanilla JS only** — hand-writing fetch, DOM swapping, URL/history sync
  and error handling for exactly the patterns 5.9 and 5.23 need. **Deferring linting to 9.17** — template linting
  serves this epic's rewrite, so it is decided where it is used.
- **Consequences:** **5.3 stops being tidying and becomes load-bearing** — whitenoise is now the *only*
  cache-busting mechanism, and it does nothing for 23 hardcoded templates; 5.3 + 19.14 + 1.13 are the whole story
  on asset versioning, and done partially the site silently serves stale CSS. **Bootstrap ships un-tree-shaken**
  (~230KB minified, compressed and cached) — accepted explicitly against the p95 budget as a cached asset, not a
  per-request cost. **Vendored assets need the ADR-029 treatment** (5.25), or the repo repeats exactly what this
  ADR found: a four-year-old library nobody noticed. **`dev.in` gains its first occupant.** **Views acquire a
  fragment-rendering path** — on `HX-Request`, render the partial directly; settle it before 5.9 is built, not
  during it. **Epic 5 still cannot start** — 5.22/5.23 need Django 5.2 and 5.18/5.20/5.21 need Epic 3's data;
  this removes the *decision* blocker, not the sequencing one.

## ADR-031: Operations — coverage-gated CI, git-watch deploys, Sentry EU, UptimeRobot, two-track backups

- **Date / Status:** 2026-08-18 · Accepted — closes the operations table.
- **Context:** Decided together because they share fixed constraints: ~$6/mo total, one solo developer, a free
  pilot with one tenant; EU residency with every vendor a processor needing a DPA; the app must stay movable with
  **configuration changes only**; Railway has **no PITR** and its snapshots aren't restorable elsewhere; GitHub
  Actions is already the runner; R2 is already provisioned. Two facts set the bar: **there is no test suite at
  all**, so any coverage gate is a target to reach rather than a floor to hold; and **backups are literally
  "unknown/undocumented"** — the risk is not a slow restore but an unrecoverable one, over data ADR-017 gives a
  **legal** retention floor.
- **Decision:**
  1. **CI merge gate** — extend the Epic 1 workflow with the test suite, `ruff` + `djlint`, the existing
     check/migrations/`collectstatic`/`docker build` steps, and `pip-audit` against the hashed lock. Dependabot
     raises dependency PRs through the same gate. Coverage is **70% repo-wide**, one number.
  2. **No SAST or container scanning this release.** CodeQL needs GitHub Advanced Security on a private repo, and
     the realistic threat is a known CVE in a dependency — which `pip-audit` and Dependabot cover — not a novel
     taint-flow bug in ~2,000 lines of views. **Revisit:** repo goes public, first non-pilot tenant, or payment
     data.
  3. **Deploys — Railway git-watch on `production`, `migrate` as the pre-deploy command.** The hook is what makes
     git-watch sufficient: migrations complete **before** the new version takes traffic, satisfying rule 4 without
     a release script or a Railway token in GitHub secrets. 6.14 is therefore satisfied **by branch protection** —
     `production` only advances by merge, and merges are blocked by required checks. No second gate, and no place
     for CI and the platform to disagree about what is live.
  4. **Sentry SaaS, free tier, EU region** (`de.sentry.io`) — **irreversible after creation**, the one setup step
     that must not be got wrong. `send_default_pii` stays **off** and a `before_send` scrubber is part of the
     decision, not tuning: a traceback here can carry supplier contacts, staff emails and costing data, and
     shipping those to a processor by accident is a disclosure no DPA covers. Environments and releases tagged from
     the deploy so pilot noise stays separable.
  5. **UptimeRobot free tier**, 5-minute HTTPS **keyword** check against the health endpoint — keyword rather than
     HTTP 200, so an endpoint reporting a failed database check fails the monitor instead of passing it. Hosted
     away from Railway deliberately: **a monitor that shares fate with what it monitors is decorative.**
  6. **Backups — two unequal tracks, no PITR.** *Fast rollback:* Railway's native schedules, enabled explicitly
     since they are **off by default**; same-host only. *The real backup:* a nightly GitHub Actions
     `pg_dump -Fc --no-owner --no-privileges`, encrypted **client-side with `age`** before leaving CI, into an R2
     bucket **separate from media**, on a **7 daily / 4 weekly / 12 monthly** lifecycle — outside Railway on
     purpose, because **an escape hatch that depends on the platform it escapes is not one.** *Proof:* 3.48's
     weekly drill — decrypt, restore into a throwaway PG 17, verify, alert on failure; also the only thing proving
     the key still decrypts. *PITR rejected*, accepting **RPO up to 24 hours**; revisit at the second paying
     tenant, or when a day of lost receipts stops being re-enterable from paper invoices.
- **Rejected:** **Coverage scoped to `control/services/` at 90%, or a ratchet** — better aimed (costing is where a
  wrong number becomes a mispriced product), but one repo-wide number is what a solo developer keeps honest, and
  scoping invites arguing which module counts. **80%+** — against zero tests, **a gate that cannot be met is a gate
  that gets disabled.** **GitHub Actions owning the deploy via the Railway CLI** — buys migrate/release ordering the
  pre-deploy hook already provides, in exchange for a long-lived token in secrets and a release script; it also
  swaps accepted lock-in for a bespoke one. **Manual deploy approval** — right once there are tenants who didn't
  agree to be pilots; today its only reviewer wrote the change. **GlitchTip self-hosted** — attractive on EU
  ownership and removes a processor, but needs a container **and its own PostgreSQL**, roughly doubling the bill and
  making the watcher another thing to patch; same SDK, so switching stays a configuration change. **Logs plus
  `AdminEmailHandler`** — free and processor-free, but with no grouping or deduplication one bad loop floods the
  inbox exactly when signal matters. **Better Stack / Sentry uptime** — fine, but UptimeRobot is free without a plan
  tier and independent of the error vendor; using Sentry would let one outage take the alerting with it. **The dump
  job as a Railway cron** — the stronger *security* answer (private network, no DB credentials in GitHub), rejected
  narrowly on portability and mitigated by backup-scoped rotatable credentials; worth reopening if the public-proxy
  exposure proves uncomfortable, since the job body is identical. **Snapshots plus manual pre-release dumps** —
  fails rule 5, and "manual, when I remember" is what 3.48 exists to eliminate. **PITR via `pgBackRest`/`wal-g`** —
  the only way to minutes-level RPO without host support, but a self-managed component with its own failure modes,
  added by a solo developer to protect a megabyte-scale dataset re-enterable from paper. **R2 server-side
  encryption or SSE-C** — SSE leaves Cloudflare holding usable keys, weakening the answer for a vendor already
  holding the media; SSE-C keeps the key yours but must be passed correctly on every dump *and* restore, with no
  recovery if it drifts. **Client-side `age` gives the strongest statement — the processor stores ciphertext — for
  one extra command.**
- **Consequences:** **Epic 6 acquires a hard number** — 70% from zero is the largest piece of work this ADR creates,
  and it gates every merge once on, so it is turned on **at the end of Epic 6** (6.22). **`base.in` gains its sixth
  direct dependency.** **A third processor joins the register.** **Key custody becomes an operational
  responsibility with no software fallback** — the `age` private key lives outside CI; lose it and every backup is
  unrecoverable (3.72), which is the one place where 3.48's drill is not merely good practice. **CI now needs
  database credentials**, which the repo has never held — backup-scoped, separate from the app's, reaching Postgres
  over the public TCP proxy: an exposure that did not exist before and the accepted cost of clause 6's
  independence. **Alerting arrives before the thing it protects** — Sentry and UptimeRobot are Epic 7, which depends
  on Epic 12, so until then the pilot runs unmonitored. **The RPO is a stated product position, not an oversight** —
  up to 24 hours of receipts and price rows can be lost, and with traceability carrying a legal retention floor this
  must be in the backup runbook (8.5) so the pilot bakery has seen it.

## ADR-032: One shared `RecipeLine`, and categories as a tenant-scoped lookup table

- **Date / Status:** 2026-08-26 · Accepted
- **Context:** ADR-022 gave both line models a typed *component* reference alongside their typed parent, leaving
  them structurally identical and reducing the choice to a formality — but one Epic 3's migrations can't be written
  without. Separately, `categorie` is free text: unvalidated, untranslatable, useless for the filtering 5.9 needs.
- **Decision:**
  1. **One `RecipeLine` replaces both line tables** — typed parent (`parent_product` **XOR**
     `parent_base_recipe`), typed component (`component_material` **XOR** `component_recipe`), each pair enforced
     by a database `CHECK` constraint, plus `quantity` and a `unit` FK.
  2. **`Product` and `Base_recipes` stay separate** — this collapses the *lines*, not the recipes.
  3. **One tenant-scoped `Category` table** with a `kind` discriminator (`material`/`product`), an `archived` flag,
     and uniqueness on `(bakery, kind, name)`. One table, not two — the kinds differ only in which model points at
     them.
  4. **Categories are tenant-editable; units are not.** A `Category` carries no arithmetic, so a tenant inventing
     "Viennoiserie" breaks nothing. A `Unit` carries a conversion factor, so editing one silently rewrites every
     cost derived from it.
- **Rejected:** **Two tables behind an abstract base** — preserves the shape without the benefit: the costing
  service still branches on type, and every later line-level feature (allergen aggregation, waste factors, per-line
  notes) gets built and tested twice. **Merging `Product` and `Base_recipes`** — consistent with ADR-022; note this
  decision makes that migration *cheaper* later, since with one line table merging the parents is a change to two FK
  columns. **`TextChoices` for categories** — a migration and deploy every time a bakery names a category, and every
  tenant sharing one vocabulary. **Two category tables** — duplicated CRUD, admin, settings UI and tests for tables
  differing by one column.
- **Consequences:** **The `CHECK` constraints are the decision** — a nullable-FK pair with no constraint is a
  *worse* schema than two tables, because it permits a line with two parents or none. Both are database constraints
  in the same migration as the model, **not** `clean()`, which does not run on `bulk_create` — exactly how an import
  writes these rows. **The migration is a merge, not a rename** — two tables of live data fold into one, dropped only
  after row counts reconcile (3.73). **It simplifies the two hardest traversals at once** — recursive costing and the
  multi-level trace are the same walk in opposite directions over this table, and allergen aggregation is a third, so
  one cycle-guard covers all three. **Free-text categories backfill per tenant, not globally** (3.74). **`kind` must
  be validated against the referencing model**, or a product can be filed under a flour category — the FK cannot
  express that; the form and service layer must. Also **corrects 3.42 and 4.14**, which still cited this question as
  their blocker though ADR-027 and ADR-028 had already closed them.

## ADR-033: Traceability entities — receipt headers with lines, runs emitting batches, dated lot codes, stock derivable but not surfaced

- **Date / Status:** 2026-08-26 · Accepted
- **Context:** The last decision Epic 3 was waiting on. ADR-017 fixed the direction and the rule that **a lot is an
  event, not an attribute**, but left the entity shape, lot-code strategy and stock question open — all touching
  tables Epic 3 is about to restructure, so deciding them afterwards means restructuring twice.
- **Decision:**
  1. **Goods receipts are a header with lines** — `GoodsReceipt` (supplier, receipt date, document reference) →
     `GoodsReceiptLine` (material, supplier lot, quantity, unit, best-before, price in ADR-018's shape). A delivery
     note is one record with many lines, and modelling it that way makes "show me that delivery" a lookup rather
     than a group-by.
  2. **Production runs consume specific receipt lines and emit a batch** — `ProductionRun` → `Consumption` (FK to a
     line, quantity consumed in canonical units) → output `Batch` carrying the internal lot code, with
     `OutboundRecord` hanging off `Batch`.
  3. **Lot codes are `YYYYMMDD-NNN`**, resetting daily, unique per `(bakery, lot_code)`, allocated **server-side
     inside the batch-creating transaction** — never client-side, never by counting rows.
  4. **Quantity-on-hand is derivable but not surfaced** — `Σ received − Σ consumed` is computable, never stored, and
     **not displayed anywhere this round**: no stock field, no stock page, no low-stock alerts.
- **Rejected:** **Flat receipt lines carrying supplier and date per row** — denormalises the delivery note into its
  items and loses the document as a record, which is the unit an FSAI inspector and a supplier query both work in.
  **Receipts first, production runs later** — rejected on ADR-017's own warning: receipts alone give one step *back*
  and nothing forward, while presenting a "Traceability" section to a real food business operator. **An opaque
  sequence (`B-000123`)** — simpler to generate, but a lot code's job is to be read off a label, quoted on a phone
  call and sorted on paper; the date earns its place. **User-entered lot codes** — a format the app cannot guarantee
  is a format the trace query cannot rely on; revisit if the pilot has an established scheme. **A full stock ledger**
  — a different product promise with accuracy expectations this app cannot meet. **Showing the derived figure
  read-only** — the closest call: a number on screen is trusted regardless of its caveat, and "received minus
  consumed" ignores waste, spillage and unrecorded use, so **it would be wrong in normal operation, not in an edge
  case.**
- **Consequences:** **`Consumption.quantity_consumed` is load-bearing beyond traceability** — the single field
  keeping stock derivable later without a schema change (17.14). **Lot-code allocation needs a concurrency-safe
  implementation, not a helper function** — two runs finishing in the same second must not collide; the unique
  constraint is the backstop, transactional allocation the mechanism, and gaps after rollback acceptable (17.13).
  **This is where ADR-022's costing gets its data** — "latest receipt by receipt date" now has a table, and the
  receipt line is the price-history source (17.12). **Receipt lines are append-only** (17.5), the first tables where
  soft delete is not enough. **Epic 3 must build `RawMaterial` knowing these are coming:** no `lot` field, no `stock`
  field, numeric `quantity` with a unit FK. **The pilot will ask for stock** — the answer is deliberate and should be
  given as one: the data is being recorded, the feature is not being claimed until it can be trusted.

## ADR-034: `ruff` for both linting and formatting; `pytest-django` as the test runner

- **Date / Status:** 2026-08-26 · Accepted
- **Context:** ADR-030 closed templates and ADR-031 named `ruff` in the CI gate, but whether `ruff` also *formats*
  and what runs the tests were unstated — a question with no legacy cost, since every `tests.py` is an empty stub.
- **Decision:** **`ruff` does both** (`check` and `format`) — no `black`, no `isort`, no `flake8`. **`pytest` +
  `pytest-django` + `pytest-cov`** replace `manage.py test`. **Tool config in a `pyproject.toml` holding only
  `[tool.*]` sections** — not a packaging file, declares no dependencies, and **must never grow a `[project]` or
  `[build-system]` table.** All four enter `dev.in` with owner comments.
- **Rejected:** **Django's own runner with `coverage.py`** — genuinely close, and consistent with rejecting DRF and
  Vite. It lost on the shape of *this* suite: costing tests are table-driven across unit conversions × VAT
  boundaries × rounding × recursion depth, which is what `parametrize` exists for, and the isolation tests want
  composable fixtures more than `setUp`. `subTest()` covers the first case but reports failures worse. **`ruff` plus
  `black`** — `ruff format` is a deliberate reimplementation of black's style, so running both spends a dependency
  and a CI step for the same output. **`mypy`** — not rejected on merit, just out of scope for a codebase with no
  annotations; revisit when the service layer exists, since typed `Decimal` boundaries are where it would pay.
- **Consequences:** **The documented test command changes in three places** — `CLAUDE.md`, the README, and CI; the
  stale one is always the one someone follows (6.24). **`--cov-fail-under=70` is where ADR-031's floor is actually
  enforced**, keeping 6.22 a one-line change. **Django's test-database machinery still applies** — `pytest-django`
  wraps rather than replaces it, which is why the choice carries little lock-in: the tests are still Django tests.

## ADR-035: Tenant full data export — one CSV per table plus a JSON manifest, in a ZIP

- **Date / Status:** 2026-08-26 · Accepted
- **Context:** ADR-008 committed to an export that does **not** assume the recipient runs a compatible PostgreSQL,
  and named two candidates without choosing. Epic 14 is blocked on it.
- **Decision:** A **ZIP of one CSV per tenant-scoped table plus a `manifest.json`** carrying the export timestamp, a
  schema version, and per table its columns, types, primary key and FK map — so relationships survive a format that
  cannot express them. Generated by a **single service function**, exposed twice: an Owner-only settings download and
  a management command.
- **Rejected:** **Portable ANSI SQL** — ADR-008's first-named option; hand-generating correct portable DDL means
  maintaining a type map and quoting rules against every future model change, and the output serves only a
  developer. The CSV bundle serves **both** audiences ADR-008 named: a spreadsheet for the owner, a loadable bundle
  for whoever they hire. **`dumpdata` JSON** — nearly free, but a *Django serialization* format, precisely the
  dependency ADR-008 set out to avoid. **A tenant-scoped `pg_dump`** — already rejected by ADR-008.
- **Consequences:** **The manifest is the deliverable, not the CSVs** — CSV loses types, nulls-versus-empty-strings
  and every relationship, so 14.3 is a correctness task rather than documentation. **Synchronous download is adequate
  and should be re-checked, not assumed** (14.6) — a tenant with years of receipts is a different size than today's
  catalogue. **Every export is a bulk disclosure of one tenant's business data**, so gating and audit logging are part
  of the feature, using capability names rather than a role comparison. **Epic 15 stays a separate mechanism**; it may
  reuse this *shape* scoped to one subject. **Decimal fidelity in CSV is a real trap** — full stored precision, never
  2-dp presentation rounding: **an export that rounds is an export that silently loses data.**

## ADR-036: AI insights on Databricks Serverless (AWS EU Ireland), fed by an R2 extract — and gunicorn stands

- **Date / Status:** 2026-08-26 · Accepted — moves **ADR-002** `Proposed` → `Accepted` and amends its delivery
  shape. Closes the last two open stack questions, and with them **every open row in `tech_stack.md` and all of
  Epic 9.**
- **Context:** ADR-002 was never confirmed — its own alternatives recorded that a plain-Python or scheduled-query
  approach had not been compared, and ADR-024 made a scheduled query over dated price rows the **null hypothesis**
  Spark had to beat. Left unsettled with it: the trigger contract, where the service runs, what data it may see, and
  the cost model — plus the WSGI/ASGI question, held back because a live analytics dashboard is the only thing in
  scope that could argue for ASGI.
- **Decision:**
  1. **Spark on Databricks is confirmed** — ADR-002's engine choice stands.
  2. **Serverless Jobs on AWS, EU (Ireland) `eu-west-1`** — job compute only, no all-purpose or interactive cluster
     and no lifecycle for the app to manage. This is what makes per-use billing real: there is no machine to start,
     idle, or forget to stop.
  3. **Django hands over an extract; Databricks never touches PostgreSQL** — a nightly job writes a
     **personal-data-free** costing extract (product, date, cost, price, margin, tenant) to a dedicated R2 prefix.
  4. **Nightly schedule, results POSTed back** to a plain `JsonResponse` callback authenticated with a shared secret.
     No event triggering, no Jobs API call from the request path.
  5. **Hard cost ceiling ~$15/mo**, spend alert before the first production run.
  6. **gunicorn, WSGI, sync workers.** **Revisit trigger, and only this one:** the insights dashboard needing
     **push** updates rather than polling.
- **Rejected:** **A scheduled query inside Django** (the null hypothesis) — **not adopted, but not wrong.** It would
  have been cheaper and added no processor, and it remains the correct answer if the scope never grows past margin
  alerts. Keeping Spark is a deliberate bet on headroom for the analytics and ML work Epic 16 is meant to grow into,
  made with the consequences stated rather than discovered. **Databricks reading Railway PostgreSQL directly**
  (ADR-002's literal shape) — exposes the production database to a third-party network and drags every readable
  table, including supplier contacts and user accounts, into GDPR transfer scope; the R2 handoff costs one nightly
  job and removes both problems. **Passing data in the Jobs API payload** — no persistence means no history, and
  trend analysis is most of the point. **Event-triggered runs** — serverless startup is seconds, so latency isn't the
  objection; debounce, retry and deduplication logic in the app is. **A margin alert is a daily concern — a price
  change at 14:03 does not need a 14:04 alert.** **An all-purpose cluster** — the shape that generates surprise
  bills, which the ceiling exists to prevent. **ASGI now** — the service layer is sync throughout, so an async view
  would raise `SynchronousOnlyOperation` against the ORM, imposing that constraint from day one for a `Could` feature.
- **Consequences:** **The first recurring cost increase since ADR-013** — ~$6 → ~$21/mo at the ceiling, a 3.5× rise
  against zero revenue. A funded bet, so 16.8 must measure a real run before production spend. **The DBU rate is not
  recorded here on purpose** — serverless pricing is region- and tier-dependent and changes; **an unverified number in
  an append-only log is worse than no number.** **Two new processors** (Databricks Inc., AWS), both needing DPAs
  before real data flows. The R2 extract keeps this manageable: no personal data in the handover, and both sit in the
  EEA, so no Chapter V mechanism is needed for the data itself — **Databricks being US-headquartered is a
  subprocessor/DPA question, not a data-location one**, stated so it isn't re-litigated. **The extract schema is a
  published contract** — the job and the notebook evolve in different repositories, so the manifest carries a version
  and the notebook rejects an unknown one (16.13). **A silent job failure is the real operational risk** — insights
  that stop arriving look identical to "no alerts this week", so failure alerting is part of the feature (16.11).
  **The callback is an unauthenticated-by-session, internet-facing write path** — the only one in the app; shared
  secret, tenant scoping and rate limiting are requirements, and it is the one endpoint besides the cover and login
  pages exempt from `LoginRequiredMiddleware`.

## ADR-037: &lt;next decision goes here&gt;

- **Date / Status:**
- **Context:**
- **Decision:**
- **Rejected:**
- **Consequences:**
