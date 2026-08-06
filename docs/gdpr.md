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
| Traceability records (new feature — not built yet) | goods receipts, production runs, outbound records; may name the supplier's contact person and the staff member who ran a production batch | Epic 17 models, tenant-scoped (see [ADR-017](decisions.md)) | Third-party (supplier contact) and staff/employee | Yes, incidentally — the batch data itself isn't personal, but the names attached to it are | **Legal obligation** (EU Reg. 178/2002 Art. 18) for the record; contract/legitimate interest for the staff attribution | **Set by food law, not by us** — a legal *minimum*, see §5 | Open — 10.9, 11.4 |

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
| Erasure ("right to be forgotten") | Delete personal data on request | Partial — delete views exist per model, but no cascading/anonymization strategy, and the user-delete view has a known bug (deletes the wrong model). Once profile pictures exist, deletion must also remove the stored object from R2 (or whichever bucket), not just the DB row referencing it. **Traceability adds a hard limit:** records inside their food-law retention window cannot be deleted — the answer is anonymizing the personal fields, or a documented refusal-with-reason (see §5) | Open |
| Restriction of processing | Mark data as "don't use, don't delete yet" | Not implemented — but the archive/soft-delete mechanism from [ADR-019](decisions.md) is the natural place to build it, rather than a second parallel flag | Open |
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

**One constraint is no longer ours to choose.** Batch/lot traceability is in scope
([ADR-017](decisions.md)), and food law imposes a **minimum** retention on traceability records —
commonly five years, shorter for short-shelf-life products. Where such a record names a supplier's
contact person or the staff member who ran a batch, that floor and GDPR's storage-limitation principle
have to be **reconciled**, not traded off: the legal obligation to retain wins over minimization for
the fields the obligation actually covers, and the answer for the rest is to keep the record while
minimizing the personal data inside it. Two consequences for this section:

- The retention policy must be written **per field**, not per record, for traceability data — the lot
  code and quantities are retained by law; the contact's name may not need to be.
- An erasure request from a supplier contact **cannot** delete a traceability record within its
  retention window. The response is anonymization of the personal fields where the trace stays intact,
  and a documented refusal-with-reason where it doesn't. That has to be written into §3's erasure
  strategy before Epic 17 ships, not discovered during a request.

Tasks: 10.9 (establish the floor), 11.4 (write the policy), 17.9 (enforce it).

## 6. Security measures

Cross-reference with [`PRODUCTION_UPDATE_PLAN.md`](../PRODUCTION_UPDATE_PLAN.md) Epic 2 (secrets
management, HTTPS/HSTS, access control) — GDPR Article 32 requires "appropriate technical and
organizational measures," which overlaps heavily with that epic. Don't duplicate the security work
here; just track GDPR-specific gaps:

- [ ] Stop logging plaintext passwords on failed login (`accounts/views.py`) — highest priority.
- [ ] Confirm encryption in transit (HTTPS enforced) once Epic 2 lands.
- [ ] Confirm backups are encrypted at rest, if/when a backup strategy is defined.
- [ ] Access logging for who viewed/exported personal data (audit trail). Two cases now need naming
      explicitly: the **Read-only role can export** ([ADR-020](decisions.md)) — deliberate, and the
      audit log is what makes it acceptable rather than the role restriction; and the **Django admin
      is a deliberate cross-tenant surface** ([ADR-019](decisions.md)) whose access to personal data
      must be logged like any other (2.15, 11.10).

## 7. Third-party processors

Anyone outside the org who touches this data needs a Data Processing Agreement (DPA). Per §0, this
now also includes Bakery-the-product itself, acting as processor for each bakery tenant (the
controller) — not just infrastructure vendors below.

| Processor | Purpose | Data involved | DPA in place? | Status |
|---|---|---|---|---|
| Bakery-the-product (this app), re: each bakery tenant | Runs the multi-tenant app on the tenant's behalf | All personal data belonging to that tenant (staff accounts, supplier contacts, profile pictures once built) | Not yet — needs a DPA template usable per tenant | Open (new, see ADR-006) |
| **Railway** (chosen host — ADR-013; currently still self-hosted on the home server until Epic 12 executes) | Runs the app, stores the DB | Everything | **Required** — task 12.7 | Open — DPA not yet executed. US-incorporated: data stored in EU West (Amsterdam), but see §7.1 below on transfer safeguards |
| Databricks (new — AI insights/batch analytics service, ADR-002) | Reads app data to compute margin alerts / analytics | Whatever the batch job queries — confirm it's limited to product/pricing/recipe data and excludes user accounts or supplier contact personal data unless proven necessary | Needed once a paid Databricks workspace is set up | Open |
| Object storage for media (Cloudflare R2 — see `tech_stack.md` ADR-005) | Stores uploaded files, including profile pictures once that feature ships | Profile pictures (personal), product photos (not personal) | Needed before the profile-picture feature goes live | Open |
| Email provider | Transactional mail — **user invitations** for the tenant self-administration area, plus any later notifications | Invitee email addresses and names | **Now required, not hypothetical** — [ADR-023](decisions.md)'s invite flow depends on it; provider choice is 9.22, DPA via 11.6 | Open |

### 7.1 Data residency and international transfers

All tenants are Irish in phase 1 (see [project_requirements.md](project_requirements.md) "Target
market"), so GDPR applies to every tenant from day one.

**Storage location — satisfied.** GDPR treats the EU as a single space: Article 1(3) provides that
free movement of personal data within the Union may not be restricted for data-protection reasons.
Irish tenants' data therefore does **not** have to be stored in Ireland, and Railway's EU West
(Amsterdam) region satisfies the residency obligation. Both the app **and** the PostgreSQL
service/volume must sit in that region — the personal data is in the database, so an app in
Amsterdam with a default-region (US West) database would place the actual data in the US. Railway's
default is US West, so the region must be set before any service is created (task 12.8).

**Transfer safeguards — Open.** Railway is US-incorporated, so US law can reach the parent company
even for data held in the EU. This is a Chapter V question answered by contractual safeguards
(SCCs and/or the EU-US Data Privacy Framework, whose predecessors Safe Harbour and Privacy Shield
were both annulled by the CJEU). To resolve: confirm Railway's current certification/SCC position
and record it here as part of the DPA work in task 12.7. [ADR-013](decisions.md) documents why this
risk was accepted for the Ireland phase, and sets a revisit trigger before EU expansion (task 11.14).

## 8. Breach notification process

_Who gets notified, how fast, and how, if personal data is exposed?_ GDPR requires notifying the
relevant supervisory authority within 72 hours of becoming aware of a breach, and affected
individuals "without undue delay" if there's high risk to them.

**Supervisory authority: the Irish Data Protection Commission (DPC)**, since phase-1 tenants are all
Irish. Note the processor position from §0 — as processor, Bakery-the-product's first obligation on
becoming aware of a breach is to notify the **affected tenant (the controller) without undue delay**;
the tenant then notifies the DPC. The per-tenant DPA must state this, and the 72-hour clock is the
controller's, which means the notification path to tenants has to be fast enough not to consume it.

Open — no process currently defined; the authority and the processor→controller path above are now
settled inputs to defining it (task 11.8).

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

- ~~Which jurisdiction(s) will this actually be deployed in / whose data protection law applies?~~
  Resolved: phase-1 tenants are all Irish, so Irish/EU law applies and the Irish DPC is the
  supervisory authority; data is stored in the EU (Amsterdam) per [ADR-013](decisions.md). See §7.1
  and §8 above. EU expansion beyond Ireland is a separate, still-Open question — see
  [project_requirements.md](project_requirements.md) "Target market".
- ~~Is there a single data controller (the bakery owner) or could this become multi-tenant SaaS
  with Bakery-the-product as processor and each bakery as controller?~~ Resolved: multi-tenant
  SaaS confirmed, Bakery-the-product as processor / each bakery tenant as controller — see §0 above
  and [decisions.md](decisions.md) ADR-006. DPA terms and the exact controller/processor contract
  are still Open follow-up work.
- Who is the practical point of contact for data subject requests once this is live? Narrowed by
  [ADR-016](decisions.md): phase 1 has exactly **one tenant** (a friendly Irish pilot bakery), so the
  controller-side contact is that bakery and the processor-side contact is the project owner. Still
  needs naming for real — task 11.12.
- Does a free pilot change any obligation? **No.** The pilot bakery is a data controller and
  Bakery-the-product is its processor regardless of whether money changes hands, so the per-tenant DPA
  (11.5) is required for the pilot too.
