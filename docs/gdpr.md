# GDPR / Data Protection

How to use this file: before any GDPR-related code gets written (consent flows, deletion
endpoints, audit logs, export changes), this file should already describe *what personal data
exists and why*. That's a discovery exercise, not a coding task — fill in the data inventory
first, decide policy, log the decision in [decisions.md](decisions.md), then implement. Don't
treat an `Open` row as permission to build against it.

This is not legal advice — get a real legal/DPO review before relying on this for compliance.

Backlog counterpart: Epic 11 (`gdpr-data-inventory`) in
[`PRODUCTION_UPDATE_PLAN.md`](../PRODUCTION_UPDATE_PLAN.md) carries one task per open item below;
Epic 15 (`feature-gdpr-data-export`) carries the §3 Portability fix. Decisions get made here, tasks
get tracked there.

## 0. Controller / processor model (multi-tenant)

Per [decisions.md](decisions.md) ADR-006, Bakery is now confirmed as a multi-tenant SaaS product —
each bakery is a tenant, sharing one database (row-scoped, see ADR-008). This resolves the
controller/processor question that was previously open: Bakery-the-product most likely acts as a
data **Processor**, and each bakery tenant is the data **Controller** for its own staff and
supplier-contact personal data. This has concrete follow-on obligations, still Open:

- A Data Processing Agreement (DPA) is needed between Bakery-the-product and each bakery tenant —
  not just with third-party infrastructure processors (see §7 below).
- Cross-tenant data access must be technically impossible, not just policy — ties directly to the
  query-layer tenant scoping decided in ADR-008 (a missed filter is both a security bug and a GDPR
  processor-obligation breach).
- Re-assess whether a DPIA is now required — see §9, status changed by this decision.

Status: Decided (multi-tenant confirmed) — DPA template and controller/processor contract terms
still Open.

## 1. Data inventory

List every place personal data is currently stored or processed. Personal data = anything that
identifies or could identify a living person, including B2B contacts (a supplier's named contact
person counts).

| Data category | Examples | Where stored (model/table) | Data subject | Personal data? | Legal basis | Retention | Status |
|---|---|---|---|---|---|---|---|
| App user accounts | username, email, password hash | Django `auth_user` | Staff/employee | Yes | Contract/legitimate interest | Open | Open |
| User profile pictures (new feature — not built yet) | uploaded photo, likely on a `Profile` model | Object storage (Cloudflare R2 — see `tech_stack.md` ADR-005), referenced from Postgres | Staff/employee (the user themselves uploads it) | Yes — a photo of a person | Likely consent (optional, user-initiated upload) — confirm before building | Delete on account deletion or on user request | Open — must be resolved before this feature is implemented, not after |
| Supplier contact info | `contact` name, `phone`, `email` | `control.Supplier` | Third-party (supplier's employee) | Yes | Legitimate interest | Open | Open |
| Failed login attempts | username + **plaintext password**, currently `print()`-ed to console/logs | `accounts/views.py: user_login` | Staff/employee | Yes — and currently a serious issue (secrets in logs) | n/a until fixed | n/a until fixed | **Needs remediation, not just documentation** |
| CSV exports | full supplier/raw material/product/user tables | Generated on demand, not persisted | Mixed | Yes (contains the above) | Same as source data | n/a (not stored) | Open |
| Session data | Django session cookie | `django_session` table | Staff/employee | Indirectly (session tied to a user) | Contract | Django default (session expiry) | Open |

Add rows as new personal data appears anywhere in the app (new features, new integrations).

## 2. Legal basis for processing

For each row above, pick one: consent, contract, legal obligation, vital interest, public task,
or legitimate interest. Document *why* that basis applies — "we assumed legitimate interest" isn't
enough on its own once this matters for real users.

Open.

## 3. Data subject rights — implementation status

| Right | What it means here | Currently implemented? | Status |
|---|---|---|---|
| Access | A user/supplier contact can ask what data is held about them | CSV export exists but isn't scoped to "my data only" — it's an admin bulk export | Open |
| Rectification | Correct inaccurate data | Yes, via existing CRUD/update views | Mostly covered |
| Erasure ("right to be forgotten") | Delete personal data on request | Partial — delete views exist per model, but no cascading/anonymization strategy, and the user-delete view has a known bug (deletes the wrong model). Once profile pictures exist, deletion must also remove the stored object from R2 (or whichever bucket), not just the DB row referencing it | Open |
| Restriction of processing | Mark data as "don't use, don't delete yet" | Not implemented | Open |
| Portability | Provide data in a machine-readable format | CSV export exists but not self-service or subject-scoped. Fix decided, not yet built: keep the bulk CSV export as an admin feature, and add a dedicated subject-scoped GDPR personal-data export (ADR-009) — separate from the tenant-wide full data export (ADR-008), which is a broader "take all my bakery's data" feature, not itself the portability mechanism | Decided (direction) — implementation Open |
| Objection | Opt out of a given processing purpose | Not implemented | Open |

## 4. Consent & cookies

- Current: only a Django session cookie for authentication — no analytics/tracking/marketing
  cookies observed in the codebase.
- If that changes (analytics, marketing tools), a cookie banner + consent record becomes
  necessary. Log the decision when/if that happens.

Status: Open (confirm no tracking has been added elsewhere, e.g. by a future integration).

## 5. Retention & deletion policy

For each data category in the inventory: how long is it kept, and what triggers deletion
(account closure, supplier relationship ends, N years of inactivity, etc.)?

Open — currently no retention policy exists; data appears to be kept indefinitely.

## 6. Security measures

Cross-reference with [`PRODUCTION_UPDATE_PLAN.md`](../PRODUCTION_UPDATE_PLAN.md) Epic 2 (secrets
management, HTTPS/HSTS, access control) — GDPR Article 32 requires "appropriate technical and
organizational measures," which overlaps heavily with that epic. Don't duplicate the security work
here; just track GDPR-specific gaps:

- [ ] Stop logging plaintext passwords on failed login (`accounts/views.py`) — highest priority.
- [ ] Confirm encryption in transit (HTTPS enforced) once Epic 2 lands.
- [ ] Confirm backups are encrypted at rest, if/when a backup strategy is defined.
- [ ] Access logging for who viewed/exported personal data (audit trail).

## 7. Third-party processors

Anyone outside the org who touches this data needs a Data Processing Agreement (DPA). Per §0, this
now also includes Bakery-the-product itself, acting as processor for each bakery tenant (the
controller) — not just infrastructure vendors below.

| Processor | Purpose | Data involved | DPA in place? | Status |
|---|---|---|---|---|
| Bakery-the-product (this app), re: each bakery tenant | Runs the multi-tenant app on the tenant's behalf | All personal data belonging to that tenant (staff accounts, supplier contacts, profile pictures once built) | Not yet — needs a DPA template usable per tenant | Open (new, see ADR-006) |
| Hosting — currently self-hosted (home server, Docker/Portainer); narrowed to Railway, Render, or DigitalOcean App Platform, see `tech_stack.md` ADR-003 | Runs the app, stores the DB | Everything | Open — needed once one of the three is chosen | Open |
| Databricks (new — AI insights/batch analytics service, ADR-002) | Reads app data to compute margin alerts / analytics | Whatever the batch job queries — confirm it's limited to product/pricing/recipe data and excludes user accounts or supplier contact personal data unless proven necessary | Needed once a paid Databricks workspace is set up | Open |
| Object storage for media (Cloudflare R2 — see `tech_stack.md` ADR-005) | Stores uploaded files, including profile pictures once that feature ships | Profile pictures (personal), product photos (not personal) | Needed before the profile-picture feature goes live | Open |
| Any email provider (if added) | Notifications | User emails | Open | Open |

## 8. Breach notification process

_Who gets notified, how fast, and how, if personal data is exposed?_ GDPR requires notifying the
relevant supervisory authority within 72 hours of becoming aware of a breach, and affected
individuals "without undue delay" if there's high risk to them.

Open — no process currently defined.

## 9. DPIA (Data Protection Impact Assessment)

Needed when processing is likely to result in high risk to individuals (large-scale sensitive
data, systematic monitoring, etc.). The scope has now changed from the original baseline (single
bakery) to confirmed multi-tenant SaaS with many bakeries' data in one shared database (ADR-006/
ADR-008) — this was explicitly the trigger noted below for reassessment, so a DPIA should actually
be scoped now rather than deferred again. Likely still not "high risk" in the GDPR sense (B2B
supplier contacts and staff accounts, no large-scale sensitive/special-category data or systematic
monitoring observed), but that judgment should be made deliberately, not by default.

Status: Open — reassess now that multi-tenant SaaS is confirmed (was previously deferred pending
exactly this change).

## Open questions

- Which jurisdiction(s) will this actually be deployed in / whose data protection law applies?
- ~~Is there a single data controller (the bakery owner) or could this become multi-tenant SaaS
  with Bakery-the-product as processor and each bakery as controller?~~ Resolved: multi-tenant
  SaaS confirmed, Bakery-the-product as processor / each bakery tenant as controller — see §0 above
  and [decisions.md](decisions.md) ADR-006. DPA terms and the exact controller/processor contract
  are still Open follow-up work.
- Who is the practical point of contact for data subject requests once this is live?
