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
serving many bakeries' data concurrently, each scoped to its own tenant. The rest of the vision
(who the buyer/user personas are beyond "a bakery", pricing/plan structure, go-to-market) is still
Open.

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

Still Open: pricing/plan structure, how tenants are onboarded, whether phase 1 is a paid beta or
free pilot, and which EU countries come next.

## User roles / personas

`PRODUCTION_UPDATE_PLAN.md` proposes: admin/owner, manager, staff/operator, read-only/auditor.
Now that multi-tenancy is confirmed (ADR-006), these roles are scoped **per tenant** (a bakery's
admin/owner only administers their own bakery's data, not other tenants') — confirm the rest:

| Role | Who is this in real life? | Can do | Cannot do | Status |
|---|---|---|---|---|
| Admin/owner | | | | Open |
| Manager | | | | Open |
| Staff/operator | | | | Open |
| Read-only/auditor | | | | Open |

## Functional requirements by area

For each existing area: what should stay as-is, what should change, what's genuinely new.

### Dashboard
- Current: lists all products with computed unit cost / net price / margin %.
- Keep / Change / Remove: Open
- New requirements: Open

### Raw materials
- Current: CRUD per category, tied to one supplier each.
- Keep / Change / Remove: Open
- New requirements: Open (e.g. supplier price comparison across raw materials — mentioned as a
  follow-up idea in `PRODUCTION_UPDATE_PLAN.md`)

### Suppliers
- Current: CRUD, name is the primary key.
- Keep / Change / Remove: Open
- New requirements: Open

### Base recipes
- Current: name + yield + ingredient lines with per-line cost.
- Keep / Change / Remove: Open
- New requirements: Open

### Products
- Current: category + yield + price + VAT + ingredient lines; cost/margin computed per product.
- Keep / Change / Remove: Open
- New requirements: Open

### Settings / users / export
- Current: CSV export per entity, ad hoc user CRUD (note: user delete view has a known bug —
  it deletes `RawMaterial` instead of the user model).
- Keep / Change / Remove: Keep the existing per-entity bulk CSV exports as an admin/operational
  feature (see [decisions.md](decisions.md) ADR-009).
- New requirements: Two new exports, decided in ADR-008/ADR-009 — (1) a tenant-scoped full data
  export in a portable, DBMS-importable format (see backlog below); (2) a dedicated GDPR
  personal-data export, scoped to one data subject, separate from the bulk admin export.

## New feature backlog

Prioritize with MoSCoW (Must / Should / Could / Won't-this-round) once there's enough to sort.
Carried over from the old README/plan as candidates, not commitments:

| Feature | Priority | Notes | Status |
|---|---|---|---|
| Supplier price comparison for the same raw material | | | Open |
| Real search/filter across raw materials, suppliers, products | | | Open |
| Historical cost/price snapshots & trend reporting | | | Open |
| Self-service user registration | | | Open |
| Reporting dashboards beyond the current per-product view | | | Open |
| AI-driven insights service: margin alerts (notify when a product's margin drops below expectation), dynamic real-time analytics dashboard | | External service, event-triggered, built on Apache Spark/Databricks — see [tech_stack.md](tech_stack.md) "AI insights / batch analytics service" and ADR-002 in [decisions.md](decisions.md). Needs an API contract between the Django app and this service before implementation. | Open |
| Product photo upload | | New `photo` field on `Product`, stored in object storage — see [tech_stack.md](tech_stack.md) "Static & media file storage" and ADR-005 | Open |
| User profile picture upload | | New profile model with a photo field, likely a `Profile` one-to-one to Django's `User`. Personal data — see [gdpr.md](gdpr.md) data inventory | Open |
| Multi-tenancy (`Bakery` model + tenant scoping across all business models) | | Confirmed direction — see [decisions.md](decisions.md) ADR-006/ADR-008. Required foundation for Phase 3; not optional | Decided (direction) |
| Tenant full data export, portable/DBMS-importable format | | Lets a departing tenant take their full dataset with them — see ADR-008. Potential product differentiator, not just a compliance mechanism | Decided (direction) |
| GDPR personal-data export (dedicated, subject-scoped) | | Second export alongside the bulk CSV export, scoped to one data subject — see ADR-009 and [gdpr.md](gdpr.md) §3 Portability | Decided (direction) |
| Better user & role management (per-tenant role assignment, inviting/removing users, self-service tenant admin) | | Beyond the security-hardening baseline in Epic 2 — this is the product-facing administration surface. Depends on the role matrix above | Open |

## Business rules & data semantics

Open business questions that the Phase 3 schema redesign is blocked on. These are questions about
what the numbers *mean*, not about how to model them — the structural counterparts live in
[tech_stack.md](tech_stack.md) "Data model — structural open questions".

| Question | Why it matters | Status |
|---|---|---|
| Does `RawMaterial.price` mean price per purchase unit, or price per normalized base unit? | Every cost/margin figure in the app depends on the answer; today it's implicit | Open |
| What are the canonical units used for costing, and how are purchase units converted to them? | Needed before normalized unit handling can be implemented | Open |
| How should VAT be represented (rate vs. amount, inclusive vs. exclusive), and where is it applied? | Currently inconsistent between products and the dashboard math | Open |
| Must product pricing history be versioned, or is only the current price meaningful? | Determines whether Phase 3 adds price-history tables; also feeds the historical-trends feature above | Open |
| Which entities must remain historically visible after "deletion" (suppliers? raw materials? products?) | Determines where soft delete/archive replaces hard delete | Open |
| Is supplier name genuinely required to be unique, once it stops being the primary key? | Determines whether a unique constraint survives the PK change | Open |
| Should the Django admin and the in-app settings area expose the same operations, or should one be narrowed? | Two overlapping administration surfaces is a permissions and support risk | Open |

## Non-functional requirements

| Area | Requirement | Status |
|---|---|---|
| Security | see [`PRODUCTION_UPDATE_PLAN.md`](../PRODUCTION_UPDATE_PLAN.md) Epic 2 | Tracked elsewhere |
| GDPR / data protection | see [gdpr.md](gdpr.md) | Tracked elsewhere |
| Performance | Open — any target (response time, concurrent users)? | Open |
| Accessibility | Open — target WCAG level? | Open |
| Device support | Current: responsive, works on mobile/tablet/desktop. Keep? | Open |
| Localization | Current: English only, `€` hardcoded. Need other languages/currencies? | Open |
| Browser support | Open | Open |

## Out of scope (for now)

_Explicitly not building this round, so nobody re-litigates it mid-phase. Fill in as things get
deferred._

Open.

## Open questions

- ~~How many bakeries/tenants does this need to support — one, or multi-tenant?~~ Resolved:
  multi-tenant, single shared database — see [decisions.md](decisions.md) ADR-006/ADR-008.
- Any regulatory requirements beyond GDPR (e.g. food safety/traceability data)?
- Who are the actual first users, and what's the timeline pressure (if any)?
