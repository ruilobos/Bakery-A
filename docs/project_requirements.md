# Project Requirements

How to use this file: this is the running source of truth for *what the app should do*, separate
from [`PRODUCTION_UPDATE_PLAN.md`](../PRODUCTION_UPDATE_PLAN.md) (the task backlog — epics and
tasks, no undecided material) and `tech_stack.md` (*what it's built with*). Fill in sections as you
decide them; leave `Status: Open` rows alone until you've actually made the call. When a requirement
changes scope meaningfully, log why in [decisions.md](decisions.md).

Once something here is decided, it must also appear as a task in an epic in the backlog. Epic 10
(`requirements-discovery`) is the backlog counterpart of this file: one task per group of `Open`
rows below.

## Vision

_What should Bakery be once this redesign is done? One paragraph — who uses it, for what, and
what "better" looks like. (Current baseline, from the old README: a single-bakery back office for
tracking raw materials, suppliers, and product costs/margins.)_

Multi-tenant confirmed (see [decisions.md](decisions.md) ADR-006): Bakery is moving from a
single-bakery back office to a multi-tenant SaaS product — one deployment, one shared database,
serving many bakeries' data concurrently, each scoped to its own tenant. Who the buyer/user personas
are beyond "a bakery" is still Open (see the role matrix below).

### Go-to-market, phase 1 (Decided — [ADR-016](decisions.md))

| Question | Decision |
|---|---|
| Who are the first real users? | **One friendly Irish bakery**, running a pilot. A real food business operator with real data — not a test tenant |
| Timeline pressure? | **None.** No committed launch date; sequencing is driven by readiness and risk, not by a date |
| Paid beta or free pilot? | **Free pilot.** No payment provider, no subscription state, no billing tables, no invoicing. Billing is out of scope this round |
| Pricing/plan structure? | **Flat per-bakery monthly subscription** when pricing arrives — all features, unlimited users per tenant. Recorded so nothing is built that contradicts it: **no feature gating by plan, no per-seat counting** |
| How are tenants onboarded? | Still **Open** — task 10.10 |

Consequences worth keeping visible: the `Bakery` tenant model (3.1) needs no plan/tier fields; the
role matrix below is driven by capability only, never by plan; and the pilot bakery is a real
controller under ADR-006, so the per-tenant DPA (11.5) applies to the pilot too.

### Target market (Decided)

**Phase 1: Ireland.** All initial tenants are Irish bakeries. **Phase 2: wider EU**, timing and
countries Open.

This is not only a sales matter — it drives several technical and compliance positions:

| Consequence | Where it lands |
|---|---|
| Irish Data Protection Commission is the supervisory authority (72-hour breach notification) | [gdpr.md](gdpr.md) §8 |
| All tenants are EU-based, so GDPR applies to every tenant from day one — no non-EU carve-out | [gdpr.md](gdpr.md) §0 |
| Hosting must store data in the EU/EEA; Amsterdam qualifies for Irish customers (Art. 1(3) free movement — data need not stay *in* Ireland) | [ADR-013](decisions.md), [gdpr.md](gdpr.md) §7 |
| EU-owned hosting is a weak differentiator in Ireland but a stronger one in continental Europe — hence the residency revisit trigger at expansion | [ADR-013](decisions.md), task 11.14 |
| Language/locale: English only for phase 1; multi-language and multi-currency become questions at EU expansion | Open — feeds the i18n question below |

Pricing structure, the free-pilot model, and the first-user question are now closed by
[ADR-016](decisions.md) above. Still Open: how tenants are onboarded (10.10), and which EU countries
come next (10.11).

## Regulatory scope beyond GDPR (Decided)

**Batch/lot food traceability is in scope** — see [ADR-017](decisions.md).

A bakery is a food business operator, and EU Regulation 178/2002 Article 18 obliges it to identify
**one step back** (which supplier supplied which input) and **one step forward** (who a given output
went to), producing those records to the competent authority on demand — the **FSAI** in Ireland.
The app today is a pure current-state catalogue with no notion of a delivery, a lot code, or a
production run, so it cannot support that record-keeping at all.

| Aspect | Position |
|---|---|
| Regulatory floor | One-step-back and one-step-forward. Full internal mass-balance is a **Should**, not a **Must** |
| Where it's built | **Epic 17** (`feature-traceability`) — its own epic, not folded into the Epic 3 schema redesign |
| Prerequisite | Epic 3: tenant scoping, numeric quantities, canonical units. A traceability record with an untrustworthy quantity isn't worth writing |
| Record integrity | Append-only — no hard delete, no silent retroactive edit (17.5) |
| Retention | Food law sets a **minimum** retention (commonly 5 years, shorter for short-shelf-life goods). Where a record names a supplier contact, that floor and GDPR retention must be reconciled, not chosen freely — 10.9 → [gdpr.md](gdpr.md) §5 |
| Not in scope | HACCP plans, temperature/cleaning logs, allergen labelling as such (separate, still Open), automated recall workflows |

Two knock-on effects on decisions still listed as Open below: entities referenced by a traceability
record can never be hard-deleted (so soft delete stops being a judgment call for `Supplier` and
`RawMaterial`), and a goods-receipt line naturally carries the price actually paid on that date —
which would answer input price history as a side effect. Decide the data-semantics questions with
that in mind rather than independently.

Allergen data (EU FIC 1169/2011) was **not** decided in this round — it is a plausible neighbour of
traceability but a separate obligation, and stays Open.

## User roles / personas

**Decided — three roles, scoped per tenant** ([ADR-020](decisions.md)). A bakery's Owner administers
only their own bakery's data, never another tenant's. The role lives on a **membership record**
(user × bakery × role), not on the user, because Django's global `Group` cannot express "Owner of
bakery A".

| Role | Who is this in real life? | Can do | Cannot do | Status |
|---|---|---|---|---|
| **Owner** | The bakery owner or whoever runs the business side | Everything Staff can, plus: invite/remove users and set their roles, change tenant settings, set and change pricing, archive records, run exports | Touch another tenant's data. Hard-delete anything covered by [ADR-019](decisions.md)'s archive rule. Edit a traceability record after the fact ([ADR-017](decisions.md)) | **Decided** |
| **Staff** | Bakers and counter staff doing daily work | Create and edit raw materials, suppliers, base recipes and products; record goods receipts and production runs | Manage users, change tenant settings, change pricing, archive records | **Decided** |
| **Read-only** | The accountant or auditor | View everything in the tenant; run exports | Write anything at all | **Decided** |
| ~~Manager~~ | — | — | — | **Deferred, not rejected** — a real distinction in a larger bakery (pricing and suppliers without user administration), but the pilot can't yet articulate it. A guessed permission set is worse than no role |

Two implementation rules that keep this cheap to extend: permission checks are **capability-named**
(`can_manage_users`), never `role == "owner"`, so adding Manager later is a table row rather than a
rewrite (2.16); and **Read-only can export**, which is deliberate — a read-only account can still
extract data in bulk, so every export is audit-logged (11.10, 14.4, 15.4). The logging is what makes
that acceptable, not the role.

Still open: whether one person may hold memberships in several tenants in the product UI — the data
model supports it, offering it is a product choice (10.14).

## Functional requirements by area

For each existing area: what should stay as-is, what should change, what's genuinely new.

### Dashboard
- Current: lists all products with computed unit cost / net price / margin %.
- **Change ([ADR-023](decisions.md)):** becomes a real **overview page** — a summary strip (product
  count, average margin, materials with no or stale pricing), the worst-margin products, and recent
  input price movements. The full product list moves to its own page.
- **Sequencing note:** this depends on **Epic 3**, not just Epic 5 — "recent price movements" and
  "stale pricing" need ADR-018's dated prices and ADR-022's receipts to exist first (5.18).
- Still Open: what counts as a **stale** price (10.16). An arbitrary threshold would train users to
  ignore the badge.

### Raw materials
- Current: CRUD per category, tied to one supplier each.
- **Change ([ADR-022](decisions.md)):** the **latest goods receipt sets the current cost** — most
  recent by *receipt date*, ties broken by creation time, so back-dated entries behave correctly. A
  manual price stays possible for materials never yet received (so a new product can be costed before
  the ingredient is first bought) and is labelled an **estimate**.
- **New requirement:** every cost figure carries its **provenance** — receipt-derived or estimated.
  A margin computed from a guess and one computed from an invoice are not the same claim, and the UI
  and exports must be able to say which it is.
- Still open as a priority call: supplier price comparison across raw materials (feature backlog).

### Suppliers
- Current: CRUD, name is the primary key.
- **Change:** surrogate primary key with name **unique per tenant** among non-archived rows, and
  archive instead of delete ([ADR-019](decisions.md)). Phone becomes a string field.
- New requirements: none beyond the schema work in Epic 3.

### Base recipes
- Current: name + yield + ingredient lines with per-line cost — and **disconnected from products**, so
  a base recipe's cost can never reach anything that's sold. Half a feature.
- **Change ([ADR-022](decisions.md)):** a **product's ingredient line may reference a base recipe**,
  and costing recurses into it. This is what base recipes were for.
- **Consequence:** `recipe_yeld` becomes load-bearing — cost per unit of yield is what a parent
  consumes, so the yield needs a real numeric value and a unit from the ADR-018 unit table (3.60).
- **Consequence:** a base recipe containing itself, directly or transitively, would make costing loop
  forever. Cycle prevention is a validation rule plus a depth guard, not a convention (3.59, 4.16).

### Products
- Current: category + yield + price + VAT + ingredient lines; cost/margin computed per product.
- **Change:** ingredient lines accept raw materials **or** base recipes ([ADR-022](decisions.md));
  prices are net-of-VAT with dated history and a VAT rate *code* ([ADR-018](decisions.md)); archive
  replaces delete ([ADR-019](decisions.md)).
- New requirements: product photo (Epic 13), subject to the MoSCoW pass.

### Settings / users / export
- Current: CSV export per entity, ad hoc user CRUD (note: user delete view has a known bug —
  it deletes `RawMaterial` instead of the user model).
- Keep / Change / Remove: Keep the existing per-entity bulk CSV exports as an admin/operational
  feature (see [decisions.md](decisions.md) ADR-009). **Rebuild the area as the tenant's
  self-administration surface** ([ADR-023](decisions.md)): the Owner invites and removes users and
  sets their roles, edits bakery details, manages reference data, and runs exports. Read-only users
  reach exports and nothing else writable. This **replaces** the broken user-delete view rather than
  patching it.
- New requirements: Two new exports, decided in ADR-008/ADR-009 — (1) a tenant-scoped full data
  export in a portable, DBMS-importable format (see backlog below); (2) a dedicated GDPR
  personal-data export, scoped to one data subject, separate from the bulk admin export.
- **New external dependency:** inviting users needs **email**, which the app does not send today. A
  provider must be chosen (9.22), configured from environment variables, and covered by a DPA (11.6)
  before invitations ship — this turns the hypothetical email-provider row in [gdpr.md](gdpr.md) §7
  into a real one.
- Still Open: **which reference data a tenant may edit.** VAT rates and categories are safe. **Unit
  conversion factors are not** — a wrong factor silently corrupts every cost figure depending on it,
  with no error surfaced anywhere. Likely system-managed units with a tenant-selectable subset, but
  that is a decision to make, not to assume (10.17).

## New feature backlog

Prioritize with MoSCoW (Must / Should / Could / Won't-this-round) once there's enough to sort.
Carried over from the old README/plan as candidates, not commitments:

| Feature | Priority | Notes | Status |
|---|---|---|---|
| Supplier price comparison for the same raw material | **Must** | Core buying-decision value. **Forces a schema change:** `RawMaterial` has a single supplier FK today, so a comparison view would show one row. The real supply relationship belongs on the goods receipt ([ADR-022](decisions.md)); the FK becomes at most an optional *preferred supplier* — 3.63, view in 5.21. Depends on Epic 17, since receipts are what it compares | **Decided** ([ADR-024](decisions.md)) |
| Real search/filter across raw materials, suppliers, products | **Must** | The current inputs exist and do nothing, which is worse than absent. Epic 5 is rewriting these templates anyway — 5.9 resolves to *build it*, not *remove it* | **Decided** ([ADR-024](decisions.md)) |
| Historical cost/price snapshots & trend reporting | **Should** | **Now cheap rather than speculative** — [ADR-018](decisions.md) versions both input prices (via ADR-017 goods receipts) and sale prices (dated `ProductPrice` rows), so the underlying history exists as a by-product. Deferred because trends need months of accumulated data that won't exist at launch. Gives Epic 16's margin alerts an actual baseline | **Decided** ([ADR-024](decisions.md)) |
| Self-service user registration | **Won't (this round)** | Open signup into a shared database with no billing gate produces spam tenants and abandoned accounts holding personal data you're then obliged to retain and delete. **Tenants are provisioned manually**; staff accounts come from Owner invitations ([ADR-023](decisions.md)). Revisit at tenant #2 or when billing exists to gate it | **Decided** ([ADR-024](decisions.md)) |
| Reporting dashboards beyond the current per-product view | **Should** | [ADR-023](decisions.md)'s overview dashboard delivers the first slice and is **the whole of the reporting story for the first release** — worth stating plainly so it isn't quietly expanded | **Decided** ([ADR-024](decisions.md)) |
| AI-driven insights service: margin alerts (notify when a product's margin drops below expectation), dynamic real-time analytics dashboard | **Could — re-scope before spending** | Keep the goal, revisit the engine. A margin alert over [ADR-018](decisions.md)'s dated prices is a **scheduled query, not a Spark cluster** — that is now the null hypothesis Spark has to beat (9.20), and it must be settled before any Databricks spend. See [tech_stack.md](tech_stack.md) and ADR-002 (still only `Proposed`) | **Decided** ([ADR-024](decisions.md)) |
| Product photo upload | **Could** | Cosmetic for a costing tool. New `photo` field on `Product`, stored in object storage — see [tech_stack.md](tech_stack.md) "Static & media file storage" and ADR-005 | **Decided** ([ADR-024](decisions.md)) |
| User profile picture upload | **Won't (this round)** | Personal data with an undecided legal basis (11.3), an object-storage DPA, and erasure obligations — real compliance cost for no operational value at a one-tenant pilot. Takes 11.3 off the critical path. Not rejected, deferred | **Decided** ([ADR-024](decisions.md)) |
| Multi-tenancy (`Bakery` model + tenant scoping across all business models) | | Confirmed direction — see [decisions.md](decisions.md) ADR-006/ADR-008. Required foundation for Phase 3; not optional | Decided (direction) |
| Tenant full data export, portable/DBMS-importable format | **Should** | Lets a departing tenant take their full dataset with them — see ADR-008. Potential product differentiator, not just a compliance mechanism. Depends on Epic 3 | Decided (direction + priority) |
| GDPR personal-data export (dedicated, subject-scoped) | **Should** | Second export alongside the bulk CSV export, scoped to one data subject — see ADR-009 and [gdpr.md](gdpr.md) §3 Portability | Decided (direction + priority) |
| Better user & role management (per-tenant role assignment, inviting/removing users, self-service tenant admin) | **Must — merged, no longer a separate feature** | This *is* [ADR-023](decisions.md)'s settings area assigning [ADR-020](decisions.md)'s roles. Fully covered by 5.19, 2.8, 3.58 and 9.22 — kept here as a pointer only, so the two don't drift | **Decided** ([ADR-024](decisions.md)) |
| Batch/lot traceability (goods receipts, production runs, one-step-back/one-step-forward trace) | **Must** | Legal obligation on the user, not a nice-to-have — EU Reg. 178/2002 Art. 18, see [ADR-017](decisions.md). Epic 17; depends on Epic 3 | Decided (in scope) |
| Allergen data on raw materials, aggregated to products (EU FIC 1169/2011) | **Should** | **In scope, as Epic 18** — a legal obligation on a bakery selling to consumers, and it reuses [ADR-022](decisions.md)'s recipe recursion directly (allergens aggregate up the tree exactly like cost). Kept **outside** Epic 17 so the Art. 18 traceability core isn't delayed by scope growing around it. Same warning as traceability: incomplete allergen data that looks authoritative is worse than none (18.5) | **Decided** ([ADR-024](decisions.md)) |
| Stock / inventory levels as a by-product of goods receipts and production runs | **Could** | Receipts and production runs *imply* quantity-on-hand, but claiming stock figures are accurate is a materially bigger promise than claiming a cost is. Not an epic — but 9.21 should design the traceability entities so stock **could** be derived later without the app claiming to track it now | **Decided** ([ADR-024](decisions.md)) |
| Billing / subscriptions | **Won't (this round)** | Phase 1 is a free pilot with a flat per-bakery price when it arrives — [ADR-016](decisions.md). No billing epic exists; proposing one needs an ADR superseding it | Decided (out of scope) |

## Business rules & data semantics

Open business questions that the Phase 3 schema redesign is blocked on. These are questions about
what the numbers *mean*, not about how to model them — the structural counterparts live in
[tech_stack.md](tech_stack.md) "Data model — structural open questions".

**This section is now fully decided** — four rows by [ADR-018](decisions.md) (decided as one model,
because a price's meaning determines the unit, which determines where VAT can be applied, which
determines what a price-history row must contain) and three by [ADR-019](decisions.md). The one
remaining `Open` row below is a tax question, not a modelling one.

| Question | Why it matters | Status |
|---|---|---|
| Does `RawMaterial.price` mean price per purchase unit, or price per normalized base unit? | Every cost/margin figure in the app depends on the answer; today it's implicit | **Decided** — purchase price + pack quantity + purchase unit, as the invoice states it (€12.50 / 25 / kg); cost per canonical unit is derived at cost time and never persisted ([ADR-018](decisions.md)) |
| What are the canonical units used for costing, and how are purchase units converted to them? | Needed before normalized unit handling can be implemented | **Decided** — **kilogram / litre / each**, one per dimension; purchase units convert via a factor held in a reference table, so new units are data, not code. Note the precision cost below |
| How should VAT be represented (rate vs. amount, inclusive vs. exclusive), and where is it applied? | Currently inconsistent between products and the dashboard math | **Decided** — all stored money is **net (ex-VAT)**; VAT applied only at display/sale; rates in a dated reference table (`code`, `percent`, `valid_from`, `valid_to`), referenced by the product |
| Must product pricing history be versioned, or is only the current price meaningful? | Determines whether Phase 3 adds price-history tables; also feeds the historical-trends feature above | **Decided** — yes, from **two sources**: input prices come free from ADR-017 goods receipts (each delivery dates the price paid); sale prices get dated `ProductPrice` rows |
| Which entities must remain historically visible after "deletion" (suppliers? raw materials? products?) | Determines where soft delete/archive replaces hard delete | **Decided** — soft delete for anything referenced by a record that outlives it: `Supplier`, `RawMaterial`, `Product` (outbound trace + dated prices), `Base_recipes` (production runs). Ingredient lines stay hard-deletable ([ADR-019](decisions.md)) |
| Is supplier name genuinely required to be unique, once it stops being the primary key? | Determines whether a unique constraint survives the PK change | **Decided** — unique **per tenant**, and only among non-archived rows (otherwise archiving a name would block it forever). Not globally unique: two bakeries may both buy from "Odlums" ([ADR-019](decisions.md)) |
| Should the Django admin and the in-app settings area expose the same operations, or should one be narrowed? | Two overlapping administration surfaces is a permissions and support risk | **Decided** — different audiences, not the same operations. In-app settings is the tenant surface (tenant-scoped, role-checked, audited); Django admin is **superuser-only support tooling** for the project owner, never linked from the tenant UI ([ADR-019](decisions.md)) |
| Which VAT rate applies to which product? | A **tax** question, not an engineering one — Irish VAT treatment of bakery goods is genuinely non-obvious (bread vs. flour confectionery). The schema must let a tenant set it per product and must not ship guessed assignments | Open — 10.13 |

**One consequence worth keeping visible.** Choosing kilogram/litre as canonical (rather than
gram/millilitre) means small ingredients become small fractions: 7 g of yeast is `0.007 kg`, a pinch
of spice `0.0005 kg`. Quantities therefore need at least `Decimal(12,4)` (`Decimal(12,6)` is safer),
money must be carried at more than two decimal places internally, and rounding to 2 dp happens **only
at presentation** — with the rounding rule written down and tested (3.51, 6.16) rather than inherited
from whatever Python happens to do. Manageable, but only because it's explicit.

## Non-functional requirements

All decided by [ADR-021](decisions.md) — deliberately before Epic 5's template rewrite, since
accessibility and localization are far cheaper to build in than to retrofit.

| Area | Requirement | Status |
|---|---|---|
| Security | see [`PRODUCTION_UPDATE_PLAN.md`](../PRODUCTION_UPDATE_PLAN.md) Epic 2 | Tracked elsewhere |
| GDPR / data protection | see [gdpr.md](gdpr.md) | Tracked elsewhere |
| Performance | p95 **< 500 ms** for normal pages, **< 2 s** for the dashboard costing aggregate, at ~10 concurrent users per tenant, on thousands of rows (not millions). Sized to what Railway Hobby actually holds | **Decided** — a documented budget, verifiable once Epic 7's monitoring exists (5.14) |
| Accessibility | **WCAG 2.2 Level A** — alt text, real form labels, no keyboard traps, nothing conveyed by colour alone | **Decided** — with an explicit revisit trigger, see below |
| Device support | One **responsive** UI, phone through desktop. Recording a goods receipt at the delivery door on a phone is a real use case | **Decided** |
| Localization | **English (`en-IE`) and euro only** — but translation-ready: display text through `gettext`, money through **one** formatter, **no hardcoded `€`** anywhere | **Decided** |
| Browser support | Current **and previous** major version of Chrome, Firefox, Safari, Edge. No IE11, no legacy Edge, no native mobile app | **Decided** |

**One thing worth naming about Level A.** It excludes AA's contrast ratios (4.5:1), visible focus
indicators, consistent navigation, and error-suggestion requirements. That is a reasonable call for a
pilot with a handful of known users. The gap becomes real the first time a tenant has a staff member
who needs it, or a buyer asks for a conformance statement — likeliest at EU expansion, where public
procurement and the European Accessibility Act point at AA. Recorded as a **revisit trigger (10.15)**,
tied to the same expansion point as 10.11 and 11.14. Building semantic HTML and real labels for Level
A during Epic 5 keeps the remaining distance to AA small.

## Out of scope (for now)

_Explicitly not building this round, so nobody re-litigates it mid-phase. Fill in as things get
deferred._

Confirmed out of scope so far (the full list is task 10.6):

| Not building | Why | Source |
|---|---|---|
| Billing, payments, subscriptions, dunning | Phase 1 is a free pilot with one tenant | [ADR-016](decisions.md) |
| Plan/tier feature gating and per-seat counting | Pricing shape is flat per-bakery; gating would permanently complicate Epics 2 and 4 for revenue that doesn't exist | [ADR-016](decisions.md) |
| HACCP plans, temperature/cleaning logs, automated recall workflows | Traceability is scoped to the Art. 18 one-step-back/one-step-forward floor | [ADR-017](decisions.md) |
| Full internal mass-balance reconciliation | A **Should**, not the regulatory floor — revisit after Epic 17 ships | [ADR-017](decisions.md) |
| Persistent hosted staging environment | Local Docker Compose is the dev/test tier | [ADR-014](decisions.md) |
| User profile pictures | Personal data with an undecided legal basis, a storage DPA and erasure obligations — real compliance cost, no operational value at a one-tenant pilot. **Deferred, not rejected** | [ADR-024](decisions.md) |
| Self-service user registration / public signup | Open signup into a shared database with no billing gate produces spam tenants and abandoned accounts holding personal data. Tenants are provisioned manually; staff come from Owner invitations | [ADR-024](decisions.md) |
| Stock / inventory tracking as a product promise | Receipts and production runs imply quantity-on-hand, but claiming it's accurate is a bigger promise than claiming a cost is. 9.21 keeps the door open in the schema | [ADR-024](decisions.md) |
| HACCP, temperature logs, recall workflows, mass-balance | Traceability is scoped to the Art. 18 floor | [ADR-017](decisions.md) |

## Open questions

- ~~How many bakeries/tenants does this need to support — one, or multi-tenant?~~ Resolved:
  multi-tenant, single shared database — see [decisions.md](decisions.md) ADR-006/ADR-008.
- ~~Any regulatory requirements beyond GDPR (e.g. food safety/traceability data)?~~ Resolved: yes —
  batch/lot traceability under EU Reg. 178/2002 Art. 18 is in scope, built as Epic 17. See
  [ADR-017](decisions.md) and "Regulatory scope beyond GDPR" above. Allergen labelling (EU FIC
  1169/2011) is a separate obligation and remains Open.
- ~~Who are the actual first users, and what's the timeline pressure (if any)?~~ Resolved: one
  friendly Irish bakery running a free pilot, no committed date — see [ADR-016](decisions.md) and
  "Go-to-market, phase 1" above.
- How are tenants onboarded — self-service signup, or manual provisioning by an operator? (10.10)
- Which EU countries follow Ireland, and on what trigger? (10.11 — pairs with the hosting-residency
  revisit in 11.14)
