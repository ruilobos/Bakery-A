# Open Decisions

**One job: everything on this page needs a decision.** Nothing here is a task, and nothing here is
settled. This is the only place open questions live — if one appears in
[project_requirements.md](project_requirements.md), [tech_stack.md](tech_stack.md) or
[decisions.md](decisions.md), that is a bug in those files.

The flow is one-directional: **question here → decided → [ADR](decisions.md) → task(s) in
[PRODUCTION_UPDATE_PLAN.md](../PRODUCTION_UPDATE_PLAN.md)**, and the row is deleted from here.

- **IDs are stable and referenced by `Blocked` rows in the backlog.** `10.x` product and
  requirements, `11.x` data protection, `9.x` stack. Never renumber, never reuse.
- **An open question is not permission to build against it.** A blocked task stays blocked until the
  ADR exists.
- **The detail here is deliberate.** These rows are longer than a backlog note because the detail is
  what the decision needs. Compress them when they are answered, not before.
- **Work that just needs doing is not a decision** — that belongs in the backlog. The test: is the
  answer a judgment nobody has made, or a clear path nobody has walked?

**No open stack questions (`9.x`).** Epic 9 closed 2026-08-26 with ADR-025 → ADR-036. A new stack
question is added here first and answered with an ADR — never in passing.

## Product & requirements (`10.x`)

| # | Question | Why it needs deciding |
|---|---|---|
| 10.8 | What does the traceability floor require in practice per FSAI guidance — and what granularity of outbound record is expected for **direct-to-consumer** sales? | **Blocks Epic 17.** Scope is set in principle ([ADR-017](decisions.md)) but never verified against the regulator's own guidance, and direct-to-consumer is treated differently from wholesale. Wrong either way: over-built, or not a compliance record |
| 10.9 | What is the food-law retention floor for traceability records, and how does it reconcile with GDPR retention where a record names a supplier contact? | Not ours to choose — a legal minimum GDPR minimization cannot override. The answer must be **per field**, not per record. Pairs with 11.4; feeds 17.9 |
| 10.10 | What seed and reference data does a new tenant start with? | Onboarding is otherwise resolved — manual provisioning ([ADR-024](decisions.md)). What remains is units, VAT rates and categories at tenant creation. Feeds 3.37, 3.52, 3.53; pairs with 10.17 and with 12.10, whose PR environment comes up with an empty database |
| 10.11 | Which EU countries follow Ireland, and on what trigger? | Left open by [ADR-016](decisions.md). Re-runs localization, currency **and** hosting residency at once — same trigger point as 10.15 and 11.14 |
| 10.12 | What allergen scope applies — the 14 declarable allergens, and what a costing tool records vs. what belongs on a label? | Unblocks 18.1, 18.2, 18.4. A regulatory scope check, not a design choice — the same shape 10.8 has for traceability |
| 10.13 | Which Irish VAT rate applies to which product category? | A **tax** question, not an engineering one. Irish treatment of bakery goods is genuinely non-obvious (bread vs. flour confectionery). The schema must let a tenant set it per product and **must not ship guessed assignments**. Feeds 3.53 |
| 10.14 | May one person hold memberships in several tenants in the product UI — an accountant serving three bakeries? | Left open by [ADR-020](decisions.md). The data model already supports it; whether it is *offered* is a product choice. Changes login and tenant-switching UX, and makes 2.21's permission-cache invalidation user-visible rather than theoretical |
| 10.15 | Should the accessibility target move from Level A to AA? | Level A excludes AA's contrast ratios (4.5:1), visible focus indicators, consistent navigation and error suggestions. **Trigger:** EU expansion, or the first tenant or buyer who needs it — public procurement and the European Accessibility Act point at AA. Semantic HTML and real labels in Epic 5 keep the remaining distance small |
| 10.16 | What makes a raw-material price "stale"? | Unblocks 4.18. A warning badge on an arbitrary threshold trains users to ignore it, so the threshold needs a reason |
| 10.17 | Which reference data may a tenant edit? | VAT rates and categories are safe. **Unit conversion factors are not** — a wrong factor silently corrupts every dependent cost figure with no error surfaced anywhere. Likely system-managed units with a tenant-selectable subset, but that is a decision, not an assumption. Feeds 3.52, 5.19 |
| 10.18 | Are the invitation and password-reset POSTs excluded from the p95 < 500 ms budget, and on what stated reason? | Both send SMTP inline; there is no task queue, and [ADR-028](decisions.md) declined Redis, so Celery for a few dozen emails a month would reintroduce it. A documented carve-out is the cheaper answer — but unwritten, 7.20 reports it as a regression |

## Data protection (`11.x`)

Executional GDPR work — completing the inventory, writing the DPA template, executing processor DPAs,
naming the contact — is **not** here; it is Epic 11 in the backlog. These are the judgments.

| # | Question | Why it needs deciding |
|---|---|---|
| 11.2 | What is the legal basis for each personal-data inventory row, and the reasoning behind it? | Everything else in Part 2 depends on it, and "we assumed legitimate interest" is not enough once real users are involved. Takes 11.1's inventory as its input |
| 11.3 | What is the legal basis for profile pictures? | **Not on the critical path** — [ADR-024](decisions.md) defers the feature — but required before it ever ships |
| 11.4 | What is the retention and deletion policy per data category, and what triggers deletion? | Unblocks 3.38. No policy exists today and data appears to be kept indefinitely. Must be written **per field** for traceability data, since 10.9's floor covers the lot code and quantities but may not cover a contact's name |
| 11.7 | What is the DPIA's scope, and is this processing "high risk"? | Triggered by [ADR-006](decisions.md) — the baseline changed from one bakery to many bakeries in one shared database. Likely *not* high risk (B2B contacts and staff accounts, no special-category data, no systematic monitoring), **but that judgment must be made deliberately rather than by default.** Two angles to include: production runs record *which staff member* ran which batch, retained for years by legal obligation, which is employee activity data; and 2.23's login-attempt records, which are personal data with their own retention question |
| 11.9 | What is the erasure, restriction and objection strategy? | Delete views exist per model but there is no cascading or anonymization strategy, and once media exists deletion must remove the stored object from R2, not just the DB row (13.9). [ADR-019](decisions.md)'s archive mechanism is the natural home for restriction rather than a second parallel flag. **The hard part is a limit, not a gap:** a traceability record inside its food-law window cannot be deleted, so the strategy needs anonymization where the trace survives it and a **documented refusal-with-reason** where it does not. Settle **before Epic 17 ships**, not during a request |
| 11.14 | Does hosting residency and vendor ownership still hold before onboarding any tenant outside Ireland? | [ADR-013](decisions.md) accepted US-incorporated vendors for the Ireland phase and set this as the revisit trigger. EU-owned alternatives priced ~2.5–3× at decision time (Clever Cloud ~€16–26/mo, Scaleway ~€16/mo) — but price is not what decides it: **continental buyers treat EU ownership as a purchasing criterion in a way Irish buyers generally do not.** Migration stays cheap only while ADR-004, ADR-007 and ADR-015 hold |
| 11.15 | What is each US-incorporated processor's Chapter V transfer-safeguard position — DPF certification, SCCs, or both? | Railway and Sentry are US-incorporated, so US law can reach the parent company even for data held in the EU. Safe Harbour (2015) and Privacy Shield (2020) were **both annulled by the CJEU**, so a current position must be confirmed per vendor, not assumed. Answered as part of 12.7; recorded in [tech_stack.md](tech_stack.md) once it lands |
