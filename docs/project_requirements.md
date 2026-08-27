# Project Requirements

**What the app should do, and what data-protection obligations come with it.** Broad view only —
schema shape is in [tech_stack.md](tech_stack.md), reasoning in [decisions.md](decisions.md), work in
[`PRODUCTION_UPDATE_PLAN.md`](../PRODUCTION_UPDATE_PLAN.md), and anything still undecided in
[roadmap.md](roadmap.md). Every row below is **decided**; the ADR named on it holds the argument.

[Part 1 — Product](#part-1--product) · [Part 2 — Data protection](#part-2--data-protection-gdpr)

---

# Part 1 — Product

## Vision

Bakery is moving from a single-bakery back office (raw materials, suppliers, product costs and
margins) to a **multi-tenant SaaS product** — one deployment, one shared database, many bakeries'
data, every row scoped to its tenant ([ADR-006](decisions.md), [ADR-008](decisions.md)).

## Go-to-market ([ADR-016](decisions.md))

| | |
|---|---|
| First users | **One friendly Irish bakery** — a real food business operator with real data, not a test tenant |
| Timeline | **None committed.** Sequencing is driven by readiness and risk |
| Commercial model | **Free pilot** — no payment provider, subscription state, billing tables or invoicing |
| Eventual pricing | **Flat per-bakery monthly subscription**, all features, unlimited users. **No feature gating by plan, no per-seat counting** |
| Onboarding | **Manual provisioning**; first Owner created with the tenant, staff via Owner invitations |
| Market | **Phase 1 Ireland**, phase 2 wider EU |

Consequences: `Bakery` (3.1) needs no plan/tier fields; roles are capability-driven, never
plan-driven; the pilot is a real controller, so the per-tenant DPA (11.5) applies to it too; Irish
tenants make the **DPC** the supervisory authority and put every tenant in GDPR scope from day one.

## Regulatory scope beyond GDPR

**Batch/lot traceability — EU Reg. 178/2002 Art. 18** ([ADR-017](decisions.md)). A bakery is a food
business operator and must identify **one step back** (which supplier supplied which input) and **one
step forward** (who a given output went to), producing records to the **FSAI** on demand. The app is
a pure current-state catalogue today, so it cannot support that at all. Built as **Epic 17**.

| Aspect | Position |
|---|---|
| Floor | One-step-back and one-step-forward. Full internal mass-balance is a **Should**, not a Must |
| Prerequisite | Epic 3 — tenant scoping, numeric quantities, canonical units. A record with an untrustworthy quantity isn't worth writing |
| Integrity | Append-only — no hard delete, no silent retroactive edit (17.5) |
| Retention | Food law sets a **minimum** GDPR minimization cannot override |
| Not in scope | HACCP plans, temperature/cleaning logs, automated recall workflows |

**Allergen declaration — EU FIC 1169/2011** ([ADR-024](decisions.md)). A separate obligation, rated
**Should**, built as **Epic 18** — deliberately outside Epic 17 so the Art. 18 core isn't delayed,
but reusing [ADR-022](decisions.md)'s recipe recursion, since allergens aggregate up the tree exactly
like cost.

## User roles ([ADR-020](decisions.md))

Three roles, scoped per tenant, held on a **membership record** (user × bakery × role) rather than on
the user, because Django's global `Group` cannot express "Owner of bakery A".

| Role | Real-world | Can | Cannot |
|---|---|---|---|
| **Owner** | Whoever runs the business side | Everything Staff can, plus invite/remove users and set roles, change tenant settings and pricing, archive records, run exports | Touch another tenant's data; hard-delete anything under [ADR-019](decisions.md)'s archive rule; edit a traceability record after the fact |
| **Staff** | Bakers and counter staff | Create and edit raw materials, suppliers, base recipes, products; record goods receipts and production runs | Manage users, change tenant settings or pricing, archive records |
| **Read-only** | The accountant or auditor | View everything in the tenant; run exports | Write anything |
| ~~Manager~~ | — | **Deferred, not rejected** — a real distinction in a larger bakery, but the pilot can't yet articulate it, and a guessed permission set is worse than no role | |

Two rules keep this cheap to extend: checks are **capability-named** (`can_manage_users`), never
`role == "owner"` (2.16); and **Read-only can export**, which is deliberate — every export is
audit-logged (11.10, 14.4, 15.4), and *that* is what makes it acceptable, not a role restriction.

## Functional requirements by area

| Area | Current | Change |
|---|---|---|
| **Dashboard** | Lists all products with computed unit cost / net price / margin % | A real **overview page** — summary strip (product count, average margin, materials with no or stale pricing), worst-margin products, recent input price movements; the full product list moves to its own page ([ADR-023](decisions.md), 5.18). **Depends on Epic 3**, since price movements need dated prices and receipts to exist |
| **Raw materials** | CRUD per category, one supplier each | The **latest goods receipt sets current cost** — most recent by *receipt date*, ties by creation time. A manual price stays possible for materials never received, labelled an **estimate**. Every cost figure carries its **provenance**: a margin from a guess and one from an invoice are not the same claim. The single supplier FK becomes at most an optional *preferred supplier* — the real supply relationship lives on the receipt ([ADR-022](decisions.md)/[ADR-024](decisions.md); 3.61–3.63) |
| **Suppliers** | CRUD, name is the primary key | Surrogate PK; name unique **per tenant, case-insensitively**, among non-archived rows; archive instead of delete; phone becomes a string ([ADR-019](decisions.md)/[ADR-027](decisions.md)) |
| **Base recipes** | Name + yield + ingredient lines, **disconnected from products** — a base recipe's cost never reaches anything sold. Half a feature | A **product's ingredient line may reference a base recipe**, with costing recursing into it. `recipe_yeld` becomes load-bearing, and cycle prevention becomes a validation rule plus a depth guard, not a convention ([ADR-022](decisions.md); 3.59, 3.60, 4.16) |
| **Products** | Category + yield + price + VAT + ingredient lines | Lines accept raw materials **or** base recipes; prices net-of-VAT with dated history and a VAT rate *code*; archive replaces delete. Product photo is a **Could** (Epic 13) |
| **Settings / users / export** | CSV export per entity; ad hoc user CRUD, whose delete view has a known bug — it deletes `RawMaterial` | Rebuilt as the tenant's **self-administration surface** ([ADR-023](decisions.md), 5.19): Owner invites/removes users and sets roles, edits bakery details, manages reference data, runs exports; Read-only reaches exports and nothing else. This **replaces** the broken delete view rather than patching it. Bulk CSV exports stay an admin feature; two new exports arrive as Epics 14 and 15. Invitations need email, which makes password reset email-only too |

## Feature backlog ([ADR-024](decisions.md), MoSCoW)

| Priority | Features |
|---|---|
| **Must** | Multi-tenancy (Epic 3) · batch/lot traceability (Epic 17) · real search/filter (5.9 — the current inputs exist and do nothing, which is worse than absent) · supplier price comparison (5.21 + 3.63; **depends on Epic 17**, since receipts are what it compares) · user & role management (**merged**, not separate — it *is* ADR-023's settings area assigning ADR-020's roles: 5.19, 2.8, 3.58) |
| **Should** | Tenant full data export (Epic 14) · GDPR personal-data export (Epic 15) · allergen data (Epic 18) · trend reporting (deferred because trends need months of data that won't exist at launch) · reporting dashboards beyond the per-product view — ADR-023's overview is **the whole reporting story for the first release** |
| **Could** | Product photos (Epic 13) · stock levels (**not an epic** — [ADR-033](decisions.md) keeps on-hand derivable without surfacing it) · AI insights (Epic 16) |
| **Won't (this round)** | Profile pictures (**deferred, not rejected** — personal data with an undecided legal basis, a storage DPA and erasure obligations, for no operational value at a one-tenant pilot) · self-service registration (open signup with no billing gate produces spam tenants and abandoned accounts holding personal data) · billing/subscriptions — proposing one needs a superseding ADR |

## Business rules & data semantics

What the numbers *mean*; the structural counterparts are in [tech_stack.md](tech_stack.md).

| Question | Decision | ADR |
|---|---|---|
| What does `RawMaterial.price` mean? | **Purchase price + pack quantity + purchase unit**, as the invoice states it (€12.50 / 25 / kg); cost per canonical unit derived at cost time, never persisted | [018](decisions.md) |
| Canonical costing units, and conversion? | **Kilogram / litre / each**, one per dimension; purchase units convert via a factor in a reference table, so new units are data, not code | [018](decisions.md) |
| How is VAT represented and applied? | All stored money **net (ex-VAT)**; VAT only at display or sale; rates dated and referenced **by code** | [018](decisions.md) |
| Must pricing history be versioned? | **Yes, from two sources** — input prices free from goods receipts; sale prices as dated `ProductPrice` rows | [018](decisions.md) |
| Which entities survive "deletion"? | **Soft delete** for anything referenced by a record that outlives it: `Supplier`, `RawMaterial`, `Product`, `Base_recipes`. Ingredient lines stay hard-deletable | [019](decisions.md) |
| Is supplier name unique? | **Per tenant**, among non-archived rows only, and **case-insensitive** — not globally, since two bakeries may both buy from "Odlums" | [019](decisions.md)/[027](decisions.md) |
| Django admin vs. in-app settings? | **Different audiences.** In-app settings is the tenant surface (scoped, role-checked, audited); Django admin is **superuser-only** support tooling, never linked from the tenant UI | [019](decisions.md) |

**The consequence worth keeping visible:** kilogram/litre canonical units make small ingredients small
fractions — 7 g of yeast is `0.007 kg`, a pinch of spice `0.0005 kg`. Quantities need at least
`Decimal(12,4)`, money is carried beyond 2 dp internally, and rounding to 2 dp happens **only at
presentation**, with the rule written down and tested (3.50, 3.51, 6.16).

## Non-functional requirements ([ADR-021](decisions.md))

Decided deliberately *before* Epic 5's rewrite, since accessibility and localization are far cheaper
to build in than to retrofit.

| Area | Requirement |
|---|---|
| Performance | p95 **< 500 ms** normal pages, **< 2 s** dashboard costing aggregate, ~10 concurrent users/tenant, on thousands of rows. A documented budget, **not** a CI gate; verifiable once Epic 7's monitoring exists. Carve-out pending in 10.18 |
| Accessibility | **WCAG 2.2 Level A** — alt text, real form labels, no keyboard traps, nothing conveyed by colour alone |
| Device support | One **responsive** UI, phone through desktop. Recording a goods receipt at the delivery door on a phone is a real use case |
| Localization | **English (`en-IE`) and euro only**, but translation-ready: `gettext` on display text, **one** currency formatter, **no hardcoded `€`** |
| Browser support | Current **and previous** major Chrome, Firefox, Safari, Edge. No IE11, no legacy Edge, no native app |
| Security | Epic 2 |
| Data protection | [Part 2](#part-2--data-protection-gdpr) |

## Out of scope this round

Billing, payments, subscriptions and plan-tier gating ([ADR-016](decisions.md)) · HACCP plans,
temperature and cleaning logs, recall workflows, full mass-balance ([ADR-017](decisions.md)) ·
persistent hosted staging ([ADR-014](decisions.md)) · a JSON API layer and any caching including Redis
([ADR-028](decisions.md)) · profile pictures, self-service registration, and stock tracking as a
product promise ([ADR-024](decisions.md)).

---

# Part 2 — Data protection (GDPR)

**This is not legal advice** — a real legal/DPO review is a prerequisite to relying on it. This part
must describe *what personal data exists and why* **before** any GDPR-related code is written. Epic 11
carries the executional work; the judgments still open are [roadmap.md](roadmap.md) 11.2, 11.3, 11.4,
11.7, 11.9, 11.14 and 11.15.

## Controller / processor model ([ADR-006](decisions.md))

**Bakery-the-product is the data Processor; each bakery tenant is the data Controller** for its own
staff and supplier-contact personal data. **Supervisory authority: the Irish Data Protection
Commission (DPC)**, since phase-1 tenants are all Irish. Three obligations follow:

- A **DPA between Bakery-the-product and each tenant** (11.5) — not just with the infrastructure
  processors. The pilot bakery is a controller regardless of whether money changes hands.
- **Cross-tenant access must be technically impossible, not merely policy** — the query-layer scoping
  of [ADR-008](decisions.md) (3.3, 3.55, 4.6, 6.9, 6.18). A missed filter is both a security bug and a
  processor-obligation breach.
- A **DPIA reassessment**, triggered by this decision.

## Personal data inventory

Every place personal data is stored or processed. Personal data = anything identifying or capable of
identifying a living person, **including B2B contacts** — a supplier's named contact counts.
Completing this table is **11.1**; the legal-basis and retention columns are provisional until
roadmap 11.2 and 11.4 land.

| Category | Examples | Where | Data subject | Legal basis (provisional) |
|---|---|---|---|---|
| App user accounts | username, email, password hash | Django `auth_user` | Staff/employee | Contract / legitimate interest |
| Supplier contact info | `contact` name, `phone`, `email` | `control.Supplier` | Third party (supplier's employee) | Legitimate interest |
| Session data | Django session cookie | `django_session` | Staff/employee (indirectly) | Contract; retention is Django's session expiry |
| Login attempt records | username, timestamp, outcome — **never the submitted password** | Structured audit log (2.23) | Staff/employee | Legitimate interest (security) |
| CSV exports | full supplier / raw material / product / user tables | Generated on demand, not persisted | Mixed | Same as source data |
| Traceability records *(Epic 17, not built)* | goods receipts, production runs, outbound records; may name the supplier's contact and the staff member who ran a batch | Epic 17 models, tenant-scoped | Supplier contact, staff/employee | **Legal obligation** (EU Reg. 178/2002 Art. 18) for the record; contract/legitimate interest for the staff attribution. Retention is a legal *minimum*, not ours to set |
| Insights extract *(Epic 16, not built)* | product, date, cost, price, margin, tenant | Cloudflare R2 prefix, read by Databricks | — | **Deliberately contains no personal data** ([ADR-036](decisions.md)); confirm in 16.9/11.17 |
| User profile pictures | uploaded photo on a `Profile` model | R2, referenced from Postgres | Staff/employee (self-uploaded) | **Deferred out of this round** ([ADR-024](decisions.md)); 11.3 must resolve before it ever ships |

The historical `print()` of a submitted password in `accounts/views.py` was verified **unreachable
dead code** — `accounts.urls` is never included ([ADR-028](decisions.md)). The file is deleted by 4.5
and replaced by 2.23. Recorded because "it never executed" is the fact worth having on file.

## Data subject rights

| Right | Position |
|---|---|
| **Access** | Epic 15. The existing CSV export is an admin bulk export, not scoped to "my data only" |
| **Rectification** | **Covered** by existing CRUD/update views |
| **Erasure** | Strategy pending (roadmap 11.9). Delete views exist per model but there is no cascading or anonymization strategy, and the user-delete view has a known bug |
| **Restriction** | Pending (roadmap 11.9); [ADR-019](decisions.md)'s archive mechanism is the natural place to build it |
| **Portability** | **Decided, not built** — keep the bulk CSV export as an admin feature and add a dedicated subject-scoped export ([ADR-009](decisions.md), Epic 15), separate from the tenant-wide export (Epic 14), which is a "take all my bakery's data" feature rather than the portability mechanism |
| **Objection** | Pending (roadmap 11.9) |

## Retention & deletion

No policy exists today and data appears to be kept indefinitely; writing it is roadmap 11.4. **One
constraint is not ours to choose:** food law imposes a **minimum** retention on traceability records
([ADR-017](decisions.md)), and where such a record names a supplier's contact or the staff member who
ran a batch, that floor and GDPR's storage-limitation principle must be **reconciled, not traded
off** — the obligation to retain wins for the fields it covers, and the answer for the rest is to keep
the record while minimizing the personal data inside it.

**Backup lifetime is a separate clock, and it is fixed.** [ADR-031](decisions.md) sets 7 daily / 4
weekly / 12 monthly — how long a *dump* survives, not how long a *record* is kept. It matters because
an erasure request cannot reach into backups, so the honest answer to "when is this really gone?" is
bounded by that schedule: **within five weeks** for everything but the monthly archives, and **within
one year** at the outside. That bound must appear in the erasure response, and the restore runbook
(8.5) must say what happens if a restore reintroduces data erased after the dump was taken.

## Consent & cookies

Only a Django session cookie for authentication — no analytics, tracking or marketing cookies in the
codebase. If that changes, a cookie banner plus a consent record becomes necessary and the decision
gets logged. 11.11 confirms no tracking has arrived via a later integration.

## Security measures

Article 32 overlaps heavily with Epic 2 — don't duplicate that work here. The GDPR-specific items:

- **Credential-free login auditing** (2.23) plus brute-force throttling (2.22).
- Confirm encryption in transit once Epic 2 lands (2.14).
- Confirm backups are encrypted at rest — **client-side `age` before upload**, so the storage
  processor holds only ciphertext (11.13). The key lives outside CI, so key loss is data loss (3.72),
  and 3.48's weekly drill is what proves the key still works.
- Confirm Sentry's `before_send` scrubber strips personal data before it leaves the app (7.23). Error
  tracking is the one processor that receives **whatever a traceback happens to contain** rather than
  a defined field set, so `send_default_pii=False` plus scrubbing is a control, not a preference.
- **Access logging for who viewed or exported personal data** (2.15, 11.10) — covering both
  Read-only's deliberate export permission and the Django admin's deliberate cross-tenant access.

Processors, their DPA status and the residency position live in [tech_stack.md](tech_stack.md)
"Processors & data residency".

## Breach notification

GDPR requires notifying the supervisory authority within **72 hours** of becoming aware of a breach,
and affected individuals "without undue delay" where there is high risk to them. Defining the process
is 11.8, feeding runbook 8.7. Two settled inputs: the authority is the **Irish DPC**; and as
**processor**, Bakery-the-product's first obligation on becoming aware is to notify the **affected
tenant (the controller) without undue delay**, the tenant then notifying the DPC. The per-tenant DPA
must state this, and **the 72-hour clock is the controller's** — so the notification path to tenants
has to be fast enough not to consume it.

## DPIA

Required where processing is likely to result in high risk to individuals. The baseline changed from a
single bakery to confirmed multi-tenant SaaS with many bakeries' data in one shared database, which
was explicitly the trigger for reassessment — so a DPIA is **scoped rather than deferred again**.
Scope and the high-risk judgment are roadmap 11.7.
