# Project Requirements

**What the app should do**, and **what data-protection obligations come with it** — separate from the
task backlog ([`PRODUCTION_UPDATE_PLAN.md`](../PRODUCTION_UPDATE_PLAN.md)) and from what it is built
with ([tech_stack.md](tech_stack.md)).

Two reading rules:

- **Decided rows are summaries.** The reasoning lives in the ADR named on the row — don't re-derive it
  and don't restate it here.
- **`Open` rows carry the detail deliberately**, because that detail is what the decision needs. An
  `Open` row is not permission to build against it.

Backlog counterparts: Epic 10 (`requirements-discovery`) for the product questions, Epic 11
(`gdpr-data-inventory`) for the data-protection ones.

---

# Part 1 — Product

## Vision

Bakery is moving from a single-bakery back office (raw materials, suppliers, product costs/margins)
to a **multi-tenant SaaS product** — one deployment, one shared database, many bakeries' data, each
row scoped to its tenant ([ADR-006](decisions.md), [ADR-008](decisions.md)).

## Go-to-market and market (Decided — [ADR-016](decisions.md))

| | |
|---|---|
| First users | **One friendly Irish bakery**, a real food business operator with real data — not a test tenant |
| Timeline | **None committed.** Sequencing is driven by readiness and risk |
| Commercial model | **Free pilot** — no payment provider, subscription state, billing tables or invoicing |
| Eventual pricing | **Flat per-bakery monthly subscription**, all features, unlimited users. Recorded so nothing contradicts it: **no feature gating by plan, no per-seat counting** |
| Onboarding | **Manual provisioning**; first Owner created with the tenant, staff via Owner invitations ([ADR-023](decisions.md)/[ADR-024](decisions.md)) |
| Market | **Phase 1 Ireland**, phase 2 wider EU |

Consequences kept visible: `Bakery` (3.1) needs no plan/tier fields; roles are capability-driven,
never plan-driven; the pilot is a real controller, so the per-tenant DPA (11.5) applies to it too;
Irish tenants make the **DPC** the supervisory authority and put every tenant in GDPR scope from day
one; hosting must store data in the EU/EEA, which Amsterdam satisfies ([ADR-013](decisions.md)).

## Regulatory scope beyond GDPR (Decided)

**Batch/lot traceability — EU Reg. 178/2002 Art. 18** ([ADR-017](decisions.md)). A bakery is a food
business operator and must identify **one step back** (which supplier supplied which input) and **one
step forward** (who a given output went to), producing records to the **FSAI** on demand. The app is
a pure current-state catalogue today — no delivery, lot code or production run — so it cannot support
that at all. Built as **Epic 17**, not folded into Epic 3.

| Aspect | Position |
|---|---|
| Floor | One-step-back and one-step-forward. Full internal mass-balance is a **Should**, not a Must |
| Prerequisite | Epic 3 — tenant scoping, numeric quantities, canonical units. A record with an untrustworthy quantity isn't worth writing |
| Integrity | Append-only — no hard delete, no silent retroactive edit (17.5) |
| Retention | Food law sets a **minimum**, which GDPR minimization cannot override — see [Retention & deletion](#retention--deletion) |
| Not in scope | HACCP plans, temperature/cleaning logs, automated recall workflows |

**Allergen declaration — EU FIC 1169/2011** ([ADR-024](decisions.md)). A separate obligation, rated
**Should**, built as **Epic 18** — deliberately outside Epic 17 so the Art. 18 core isn't delayed,
but reusing [ADR-022](decisions.md)'s recipe recursion, since allergens aggregate up the tree exactly
like cost.

## User roles (Decided — [ADR-020](decisions.md))

Three roles, scoped per tenant, held on a **membership record** (user × bakery × role) rather than on
the user, because Django's global `Group` cannot express "Owner of bakery A".

| Role | Real-world | Can | Cannot |
|---|---|---|---|
| **Owner** | The owner or whoever runs the business side | Everything Staff can, plus invite/remove users and set roles, change tenant settings and pricing, archive records, run exports | Touch another tenant's data; hard-delete anything under [ADR-019](decisions.md)'s archive rule; edit a traceability record after the fact |
| **Staff** | Bakers and counter staff | Create and edit raw materials, suppliers, base recipes, products; record goods receipts and production runs | Manage users, change tenant settings or pricing, archive records |
| **Read-only** | The accountant or auditor | View everything in the tenant; run exports | Write anything |
| ~~Manager~~ | — | **Deferred, not rejected** — a real distinction in a larger bakery (pricing and suppliers without user administration), but the pilot can't yet articulate it, and a guessed permission set is worse than no role | |

Two rules keep this cheap to extend: checks are **capability-named** (`can_manage_users`), never
`role == "owner"` (2.16); and **Read-only can export**, which is deliberate — every export is
audit-logged (11.10, 14.4, 15.4), and *that* is what makes it acceptable, not the role restriction.

## Functional requirements by area

| Area | Current | Change |
|---|---|---|
| **Dashboard** | Lists all products with computed unit cost / net price / margin % | Becomes a real **overview page** — summary strip (product count, average margin, materials with no or stale pricing), worst-margin products, recent input price movements; the full product list moves to its own page ([ADR-023](decisions.md), 5.18). **Depends on Epic 3**, not just Epic 5 — price movements and staleness need dated prices and receipts to exist |
| **Raw materials** | CRUD per category, one supplier each | The **latest goods receipt sets current cost** — most recent by *receipt date*, ties by creation time, so back-dated entries behave correctly. A manual price stays possible for materials never received, labelled an **estimate**. Every cost figure carries its **provenance**: a margin from a guess and one from an invoice are not the same claim. The single supplier FK becomes at most an optional *preferred supplier* — the real supply relationship lives on the receipt ([ADR-022](decisions.md)/[ADR-024](decisions.md); 3.61–3.63) |
| **Suppliers** | CRUD, name is the primary key | Surrogate PK; name unique **per tenant, case-insensitively**, among non-archived rows; archive instead of delete; phone becomes a string ([ADR-019](decisions.md)/[ADR-027](decisions.md)) |
| **Base recipes** | Name + yield + ingredient lines — and **disconnected from products**, so a base recipe's cost never reaches anything sold. Half a feature | A **product's ingredient line may reference a base recipe**, with costing recursing into it. `recipe_yeld` becomes load-bearing (cost per unit of yield is what a parent consumes), and cycle prevention becomes a validation rule plus a depth guard, not a convention ([ADR-022](decisions.md); 3.59, 3.60, 4.16) |
| **Products** | Category + yield + price + VAT + ingredient lines | Lines accept raw materials **or** base recipes; prices net-of-VAT with dated history and a VAT rate *code*; archive replaces delete. Product photo is a **Could** (Epic 13) |
| **Settings / users / export** | CSV export per entity; ad hoc user CRUD (the delete view has a known bug — it deletes `RawMaterial`) | Rebuilt as the tenant's **self-administration surface** ([ADR-023](decisions.md), 5.19) — Owner invites/removes users and sets roles, edits bakery details, manages reference data, runs exports; Read-only reaches exports and nothing else writable. This **replaces** the broken delete view rather than patching it. Bulk CSV exports stay as an admin feature ([ADR-009](decisions.md)); two new exports arrive as Epics 14 and 15. Inviting users needs **email** — Brevo over SMTP (9.22 ✅), which also makes password reset email-only |

## Feature backlog (Decided — [ADR-024](decisions.md), MoSCoW pass)

| Priority | Features |
|---|---|
| **Must** | Multi-tenancy (Epic 3) · batch/lot traceability (Epic 17) · real search/filter (5.9 — the current inputs exist and do nothing, which is worse than absent) · supplier price comparison (5.21 + 3.63; **depends on Epic 17**, since receipts are what it compares) · user & role management (**merged**, not separate — it *is* ADR-023's settings area assigning ADR-020's roles: 5.19, 2.8, 3.58, 9.22) |
| **Should** | Tenant full data export (Epic 14) · GDPR personal-data export (Epic 15) · allergen data (Epic 18) · trend reporting (cheap rather than speculative — [ADR-018](decisions.md) versions both price sources as a by-product — but deferred because trends need months of data that won't exist at launch) · reporting dashboards beyond the per-product view (ADR-023's overview is **the whole of the reporting story for the first release**) |
| **Could** | Product photos (Epic 13) · stock levels (**not an epic** — [ADR-033](decisions.md) keeps on-hand derivable via `Consumption.quantity_consumed` without surfacing it) · AI insights (Epic 16; engine confirmed on Databricks Serverless by [ADR-036](decisions.md), and now a cost decision at ~$6 → ~$21/mo) |
| **Won't (this round)** | Profile pictures (**deferred, not rejected** — personal data with an undecided legal basis, a storage DPA and erasure obligations, for no operational value at a one-tenant pilot) · self-service registration (open signup with no billing gate produces spam tenants and abandoned accounts holding personal data you must then retain and delete) · billing/subscriptions ([ADR-016](decisions.md); proposing one needs a superseding ADR) |

## Business rules & data semantics (Decided)

What the numbers *mean*; the structural counterparts are in [tech_stack.md](tech_stack.md).
Four rows by [ADR-018](decisions.md) — decided as one model, because a price's meaning determines the
unit, which determines where VAT applies, which determines what a price-history row contains — and
three by [ADR-019](decisions.md).

| Question | Decision |
|---|---|
| What does `RawMaterial.price` mean? | **Purchase price + pack quantity + purchase unit**, as the invoice states it (€12.50 / 25 / kg); cost per canonical unit derived at cost time, never persisted |
| Canonical costing units, and conversion? | **Kilogram / litre / each**, one per dimension; purchase units convert via a factor in a reference table, so new units are data, not code |
| How is VAT represented and applied? | All stored money **net (ex-VAT)**; VAT only at display/sale; rates in a dated table (`code`, `percent`, `valid_from`, `valid_to`), referenced **by code** |
| Must pricing history be versioned? | **Yes, from two sources** — input prices free from goods receipts; sale prices as dated `ProductPrice` rows |
| Which entities survive "deletion"? | **Soft delete** for anything referenced by a record that outlives it: `Supplier`, `RawMaterial`, `Product`, `Base_recipes`. Ingredient lines stay hard-deletable |
| Is supplier name unique? | **Per tenant**, among non-archived rows only, and **case-insensitive** ([ADR-027](decisions.md)). Not globally — two bakeries may both buy from "Odlums" |
| Django admin vs. in-app settings? | **Different audiences.** In-app settings is the tenant surface (scoped, role-checked, audited); Django admin is **superuser-only** support tooling, never linked from the tenant UI |

**The consequence worth keeping visible:** kilogram/litre canonical units make small ingredients small
fractions — 7 g of yeast is `0.007 kg`, a pinch of spice `0.0005 kg`. Quantities need at least
`Decimal(12,4)` (`12,6` safer), money is carried beyond 2 dp internally, and rounding to 2 dp happens
**only at presentation**, with the rule written down and tested (3.50, 3.51, 6.16).

## Non-functional requirements (Decided — [ADR-021](decisions.md))

Decided deliberately *before* Epic 5's rewrite, since accessibility and localization are far cheaper
to build in than to retrofit.

| Area | Requirement |
|---|---|
| Performance | p95 **< 500 ms** normal pages, **< 2 s** dashboard costing aggregate, ~10 concurrent users/tenant, on thousands of rows. A documented budget, **not** a CI gate (Railway Hobby shares CPU); verifiable once Epic 7's monitoring exists. Two carve-outs: the invitation and password-reset POSTs send SMTP inline (10.18) |
| Accessibility | **WCAG 2.2 Level A** — alt text, real form labels, no keyboard traps, nothing conveyed by colour alone. Revisit trigger: 10.15 |
| Device support | One **responsive** UI, phone through desktop. Recording a goods receipt at the delivery door on a phone is a real use case |
| Localization | **English (`en-IE`) and euro only**, but translation-ready: `gettext` on display text, **one** currency formatter, **no hardcoded `€`** |
| Browser support | Current **and previous** major Chrome, Firefox, Safari, Edge. No IE11, no legacy Edge, no native app |
| Security | Epic 2 |
| Data protection | [Part 2](#part-2--data-protection-gdpr) |

## Out of scope this round (Decided)

Billing/payments/subscriptions and plan-tier gating ([ADR-016](decisions.md)) · HACCP plans,
temperature/cleaning logs, recall workflows, full mass-balance ([ADR-017](decisions.md)) · persistent
hosted staging ([ADR-014](decisions.md)) · a JSON API layer and any caching including Redis
([ADR-028](decisions.md)) · profile pictures, self-service registration, stock tracking as a product
promise ([ADR-024](decisions.md)).

---

# Part 2 — Data protection (GDPR)

**This is not legal advice** — a real legal/DPO review is a prerequisite to relying on it.

Before any GDPR-related code is written (consent flows, deletion endpoints, audit logs, export
changes), this part must already describe *what personal data exists and why*. That is discovery, not
coding: fill in the inventory, decide policy, log the decision in [decisions.md](decisions.md), then
implement. Epic 11 carries one task per open item; Epic 15 carries the portability fix.

## Controller / processor model (Decided — [ADR-006](decisions.md))

**Bakery-the-product is the data Processor; each bakery tenant is the data Controller** for its own
staff and supplier-contact personal data. Three obligations follow, all still Open:

- A **DPA between Bakery-the-product and each tenant** (11.5) — not just with the infrastructure
  processors. The pilot bakery is a controller regardless of whether money changes hands, so this
  applies to the free pilot too.
- **Cross-tenant access must be technically impossible, not merely policy** — the query-layer scoping
  of [ADR-008](decisions.md) (3.3, 3.55, 4.6, 6.9, 6.18). A missed filter is both a security bug and a
  processor-obligation breach.
- A **DPIA reassessment**, triggered by this decision — see [DPIA](#dpia).

**Supervisory authority: the Irish Data Protection Commission (DPC)**, since phase-1 tenants are all
Irish.

## Personal data inventory

Every place personal data is stored or processed. Personal data = anything identifying or capable of
identifying a living person, **including B2B contacts** — a supplier's named contact person counts.

| Category | Examples | Where | Data subject | Legal basis | Retention | Status |
|---|---|---|---|---|---|---|
| App user accounts | username, email, password hash | Django `auth_user` | Staff/employee | Contract / legitimate interest | Open | **Open** |
| Supplier contact info | `contact` name, `phone`, `email` | `control.Supplier` | Third party (supplier's employee) | Legitimate interest | Open | **Open** |
| Session data | Django session cookie | `django_session` | Staff/employee (indirectly) | Contract | Django default (session expiry) | **Open** |
| Login attempt records | username, timestamp, outcome — **never the submitted password** | Structured audit log (2.23) | Staff/employee | Legitimate interest (security) | Open — its own retention question, feeds the DPIA | **Open.** The historical `print()` of the submitted password in `accounts/views.py` was verified **unreachable dead code** (`accounts.urls` is never included — [ADR-028](decisions.md)); the file is deleted by 4.5 and replaced by 2.23. Recorded because "it never executed" is the fact worth having on file |
| CSV exports | full supplier / raw material / product / user tables | Generated on demand, not persisted | Mixed | Same as source data | n/a (not stored) | **Open** |
| Traceability records *(Epic 17, not built)* | goods receipts, production runs, outbound records; may name the supplier's contact and the staff member who ran a batch | Epic 17 models, tenant-scoped | Supplier contact and staff/employee | **Legal obligation** (EU Reg. 178/2002 Art. 18) for the record; contract/legitimate interest for the staff attribution | **Set by food law, not by us** — a legal *minimum* | **Open** — 10.9, 11.4 |
| Insights extract *(Epic 16, not built)* | product, date, cost, price, margin, tenant | Cloudflare R2 prefix, read by Databricks | — | **Deliberately contains no personal data** ([ADR-036](decisions.md)) | Tied to the nightly job's lifecycle | **Open** — confirm in 16.9/11.17 |
| User profile pictures | uploaded photo on a `Profile` model | R2, referenced from Postgres | Staff/employee (self-uploaded) | Likely consent — confirm before building | Delete on account deletion or on request | **Deferred out of this round** ([ADR-024](decisions.md)). 11.3 must still resolve before the feature ever ships |

Add rows as new personal data appears. Completing this inventory is **11.1**; documenting the legal
basis *with its reasoning* for each row is **11.2** — "we assumed legitimate interest" is not enough
once this matters for real users.

## Data subject rights

| Right | What it means here | State |
|---|---|---|
| **Access** | A user or supplier contact asks what data is held about them | **Open.** The CSV export exists but is an admin bulk export, not scoped to "my data only" |
| **Rectification** | Correct inaccurate data | **Mostly covered** by existing CRUD/update views |
| **Erasure** | Delete personal data on request | **Open.** Delete views exist per model but there is no cascading/anonymization strategy, and the user-delete view has a known bug. Once media exists, deletion must remove the stored object from R2, not just the DB row (13.9). **Traceability adds a hard limit** — see below |
| **Restriction** | Mark data "don't use, don't delete yet" | **Open.** [ADR-019](decisions.md)'s archive/soft-delete mechanism is the natural place to build it, rather than a second parallel flag |
| **Portability** | Provide data in a machine-readable format | **Decided, not built.** Keep the bulk CSV export as an admin feature and add a dedicated subject-scoped export ([ADR-009](decisions.md), Epic 15) — separate from the tenant-wide export (Epic 14), which is a "take all my bakery's data" feature, not the portability mechanism |
| **Objection** | Opt out of a given processing purpose | **Open** |

Closing the restriction/objection/erasure gaps is **11.9**; Access and Portability are **Epic 15**.

**The erasure limit is the part that needs deciding, not discovering.** A traceability record inside
its food-law retention window **cannot be deleted**. The strategy must cover: anonymizing the personal
fields where the trace stays intact, and a **documented refusal-with-reason** where it doesn't. That
has to be written into the erasure response **before Epic 17 ships**, not during a request.

## Retention & deletion

**Open** — no policy exists today and data appears to be kept indefinitely. Writing it is **11.4**.

**One constraint is not ours to choose.** Food law imposes a **minimum** retention on traceability
records ([ADR-017](decisions.md)) — commonly five years, shorter for short-shelf-life products. Where
such a record names a supplier's contact or the staff member who ran a batch, that floor and GDPR's
storage-limitation principle must be **reconciled, not traded off**: the obligation to retain wins for
the fields it actually covers, and the answer for the rest is to keep the record while minimizing the
personal data inside it. Two consequences:

- The policy must be written **per field**, not per record, for traceability data — the lot code and
  quantities are retained by law; the contact's name may not need to be.
- An erasure request from a supplier contact cannot delete such a record within its window (see
  above).

Establishing the food-law floor itself is **10.9**, and it is a regulatory question, not an
engineering one — it must be confirmed against guidance, not assumed.

**Backup lifetime is a separate clock, and it is already fixed.** [ADR-031](decisions.md) sets the
backup schedule at **7 daily / 4 weekly / 12 monthly** — how long a *dump* survives, not how long a
*record* is kept. It matters here because an erasure request cannot reach into backups, so the honest
answer to "when is this really gone?" is bounded by that schedule: within **five weeks** for
everything but the monthly archives, and within **one year** at the outside. That bound must appear in
the erasure response, and the restore runbook (8.5) must say what happens if a restore reintroduces
data erased after the dump was taken (11.13, 3.71).

## Consent & cookies

Only a Django session cookie for authentication today — no analytics, tracking or marketing cookies
observed in the codebase. If that changes, a cookie banner plus a consent record becomes necessary and
the decision gets logged.

**Status: Open** — 11.11 confirms no tracking has been added by a later integration.

## Security measures

Article 32 requires "appropriate technical and organizational measures", overlapping heavily with
Epic 2 — don't duplicate that work here. The GDPR-specific gaps:

- [ ] **Credential-free login auditing** (2.23) plus brute-force throttling (2.22).
- [ ] Confirm encryption in transit once Epic 2 lands (2.14).
- [ ] Confirm backups are encrypted at rest (11.13) — **client-side `age` before upload**, so the
      storage processor holds only ciphertext. The key lives outside CI, so key loss is data loss
      (3.72), and 3.48's weekly drill is what proves the key still works.
- [ ] Confirm the Sentry `before_send` scrubber actually strips personal data before it leaves the app
      (7.23). Error tracking is the one processor that receives **whatever a traceback happens to
      contain** — supplier contacts, staff emails, a tenant's costing data — rather than a defined
      field set, so `send_default_pii=False` plus scrubbing is a control, not a preference.
- [ ] **Access logging for who viewed or exported personal data** (2.15, 11.10). Two cases need naming:
      **Read-only can export** ([ADR-020](decisions.md)) — deliberate, with the audit log as what makes
      it acceptable; and the **Django admin is a deliberate cross-tenant surface**
      ([ADR-019](decisions.md)) whose access must be logged like any other.

Third-party processors, their DPA status, and the data-residency/international-transfer position live
in [tech_stack.md](tech_stack.md) "Processors & data residency", alongside the vendors themselves.

## Breach notification

GDPR requires notifying the supervisory authority within **72 hours** of becoming aware of a breach,
and affected individuals "without undue delay" where there is high risk to them.

**Open** — no process defined yet (11.8, feeding runbook 8.7). Two settled inputs to defining it:

- The authority is the **Irish DPC**.
- As **processor**, Bakery-the-product's first obligation on becoming aware is to notify the
  **affected tenant (the controller) without undue delay**; the tenant then notifies the DPC. The
  per-tenant DPA must state this, and **the 72-hour clock is the controller's** — so the notification
  path to tenants has to be fast enough not to consume it.

## DPIA

Required when processing is likely to result in high risk to individuals. The scope changed from the
original baseline (a single bakery) to confirmed multi-tenant SaaS with many bakeries' data in one
shared database — which was explicitly the trigger for reassessment, so a DPIA should now be **scoped
rather than deferred again** (11.7).

Likely still not "high risk" in the GDPR sense — B2B supplier contacts and staff accounts, no
large-scale sensitive/special-category data, no systematic monitoring — **but that judgment should be
made deliberately, not by default.** Two angles to include:

- [ADR-017](decisions.md)'s: production runs record *which staff member* ran which batch, retained for
  years by legal obligation. That is **employee activity data**, and should be assessed rather than
  waved through as "just traceability".
- The login-attempt records from 2.23, which are personal data with their own retention question.

**Status: Open.**

---

## Open questions

Each of these blocks work; none should be answered in passing.

| # | Question | Why it matters / what a good answer needs |
|---|---|---|
| 10.8 | What does the traceability floor actually require in practice, per FSAI guidance — and what granularity of outbound record is expected for **direct-to-consumer** sales? | **Blocks Epic 17.** The scope is set in principle but not verified against the regulator's own guidance, and direct-to-consumer is treated differently from wholesale. Getting this wrong means either over-building or shipping something that is not a compliance record |
| 10.9 | What is the food-law retention floor for traceability records, and how does it reconcile with GDPR retention where a record names a supplier contact? | Not ours to choose — it is a legal minimum. Pairs with 11.4 and drives 17.9. The answer must be **per field**, not per record |
| 10.10 | What seed/reference data does a new tenant start with? | Onboarding mechanics are otherwise resolved (manual provisioning). What remains is units, VAT rates and categories at tenant creation — pairs with 3.37, 3.52, 3.53, 10.17 and 12.10 (the PR environment comes up with an empty database) |
| 10.11 | Which EU countries follow Ireland, and on what trigger? | Left Open by [ADR-016](decisions.md). Re-runs the localization, currency **and** hosting-residency questions at once — pairs with 10.15 and 11.14, which share the same trigger point |
| 10.12 | What allergen scope applies — the 14 declarable allergens, and what a costing tool records vs. what belongs on a label? | Unblocks 18.1/18.2/18.4. Same shape as 10.8 did for traceability: a regulatory scope check, not a design choice |
| 10.13 | Which Irish VAT rate applies to which product category? | A **tax** question, not an engineering one — Irish treatment of bakery goods is genuinely non-obvious (bread vs. flour confectionery). The schema must let a tenant set it per product and **must not ship guessed assignments**. Feeds 3.53 |
| 10.14 | May one person hold memberships in several tenants in the product UI (e.g. an accountant serving three bakeries)? | The data model already supports it; whether it is *offered* is a product choice. It changes login and tenant-switching UX, and makes 2.21's permission-cache invalidation user-visible rather than theoretical |
| 10.15 | Should the accessibility target move from Level A to AA? | Level A excludes AA's contrast ratios (4.5:1), visible focus indicators, consistent navigation and error suggestions. **Revisit trigger:** EU expansion, or the first tenant/buyer who needs it — public procurement and the European Accessibility Act point at AA. Building semantic HTML and real labels during Epic 5 keeps the remaining distance small |
| 10.16 | What makes a raw-material price "stale"? | Unblocks 4.18. A warning badge on an arbitrary threshold trains users to ignore it, so the threshold needs a reason |
| 10.17 | Which reference data may a tenant edit? | VAT rates and categories are safe. **Unit conversion factors are not** — a wrong factor silently corrupts every dependent cost figure with no error surfaced anywhere. Likely system-managed units with a tenant-selectable subset, but that is a decision, not an assumption. Feeds 3.52 and 5.19 |
| 10.18 | Record the invitation and password-reset POSTs as explicit exclusions from the p95 < 500 ms budget | Both send SMTP inline; there is no task queue, and [ADR-028](decisions.md) declined Redis, so Celery for a few dozen emails a month would reintroduce it. A documented carve-out is the cheaper answer — but it must be written down, or 7.20 reports it as a regression |
| 11.1–11.2 | Complete the personal-data inventory and document each row's legal basis with reasoning | Everything else in Part 2 depends on it. **11.1 blocks 15.1** — you cannot scope a subject export without knowing which fields are personal data |
| 11.3 | What is the legal basis for profile pictures? | **No longer on the critical path** ([ADR-024](decisions.md) defers the feature), but still required before it ever ships |
| 11.4 | Retention and deletion policy per category, with deletion triggers | Unblocks 3.38. Must be **per field** for traceability data (see [Retention & deletion](#retention--deletion)) |
| 11.5 | A DPA template usable per tenant, Bakery-the-product as processor | Applies to the free pilot too |
| 11.7 | Scope and carry out the DPIA | See [DPIA](#dpia) — include the employee-activity-data angle and login history |
| 11.8 | Define the breach notification process | See [Breach notification](#breach-notification) — the authority and processor→controller path are settled inputs. Feeds 8.7 |
| 11.9 | Close the restriction, objection and erasure gaps | Including the traceability erasure limit and deleting stored objects from R2, not just DB rows |
| 11.11 | Confirm no tracking/analytics cookies exist; define the consent path if that changes | |
| 11.12 | Name the point of contact for data subject requests | Narrowed: phase 1 has one tenant, so controller-side is the pilot bakery and processor-side is the project owner. Still needs naming for real |
| — | Processor DPAs and transfer safeguards (11.6, 11.13–11.17, 12.7) | Tracked with the vendors in [tech_stack.md](tech_stack.md) "Processors & data residency" |
