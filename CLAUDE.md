# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Bakery is a Django web app (originally an MSc capstone prototype) that lets a bakery track raw materials, suppliers, and products, and computes per-product cost/margin from recipe ingredient data. It is currently being hardened from prototype to production quality — see `PRODUCTION_UPDATE_PLAN.md`, the authoritative **task backlog**: every phase/workstream is an Epic (numbered 1–19, each with its own branch) holding numbered, individually-tracked tasks (`3.12` = Epic 3, task 12). Treat that file as the source of truth for planned work; don't re-derive priorities from scratch. Reference task IDs in plans, commits, and PRs. A task marked `Blocked` is blocked on an open decision in `docs/roadmap.md` — make and log the ADR first, don't implement it (see ADR-012).

This is also a broader redesign in progress — new features, GDPR compliance, and a possible tech
stack change are still being decided, not just the engineering hardening in
`PRODUCTION_UPDATE_PLAN.md`. That undecided material lives in `docs/`, not in this file.

## Planning & documentation (`docs/`)

Four documents, **one job each**. Read the relevant one before proposing anything in that area —
and read its **index/table of contents first**, then only the section you need, rather than loading
the whole file:

- `docs/project_requirements.md` — **what the app should do, at a broad level.** Part 1: product
  (go-to-market, regulatory scope, roles, per-area requirements, feature backlog, non-functional
  targets). Part 2: data protection (GDPR) — controller/processor model, personal data inventory,
  subject rights, retention, breach process, DPIA. Details belong in the other docs; the inventory
  must exist before consent/deletion/audit-log code is written against it.
- `docs/tech_stack.md` — **what it's built with, decided facts only.** Current vs. decided per
  layer (runtime, dependencies, backend, data model, frontend, infra, quality tooling), plus the
  third-party **processors and the data-residency position**, which live with the vendors. Outcomes
  in a line; the reasoning is in the ADR named beside each row and is never repeated here.
- `docs/decisions.md` — **append-only ADR log; its only job is to stop settled questions being
  re-opened.** Opens with an index table (number, title, status, one-line decision) — read that,
  then fetch only the entries you need. Each entry is Decision · Rejected · Traps; **Rejected is the
  load-bearing part.** Never delete an entry; supersede it, and move any surviving clause into the
  superseding ADR.
- `docs/roadmap.md` — **the open-decisions register, and nothing else.** Every question still
  awaiting a judgment, with stable IDs (`10.x` product/requirements, `11.x` data protection, `9.x`
  stack) that `Blocked` backlog tasks reference. It holds no tasks, no status tracking and no
  sequencing.

**There are no `Open` rows anywhere else.** If a question appears in `tech_stack.md`,
`project_requirements.md` or `decisions.md`, that's a bug — move it to `roadmap.md`. Epic and task
status, sequencing, the execution order and the release milestone all live in
`PRODUCTION_UPDATE_PLAN.md`.

When a decision is actually made (in conversation or otherwise): add an ADR to `docs/decisions.md`
(and its index row), update the relevant state doc, **delete the question from `roadmap.md`**, and
turn the decision into task(s) in the right epic in `PRODUCTION_UPDATE_PLAN.md` plus a row in its
"Decision → task coverage" table — all in the same session. The flow is one-directional:
**open question → ADR → tasks.**

### Workflow this repo follows

Per ADR-010 (supersedes ADR-001), as amended by ADR-037: `main` is the integration/dev-test
branch, not what's deployed to real users — a separate `production` branch holds what's live.

**One task is one feature is one PR** (ADR-037). Each backlog task gets its own branch named
`<epic-branch>-<task-id>` (e.g. `phase-1-repo-cleanup-1.1`), branched from an updated `main`,
planned in Plan Mode before implementation starts, and squash-merged before the next begins.
**An epic groups and sequences tasks; it is not a branch.** No stacking, no direct commits.
Promote validated work from `main` to `production` via its own PR, tagged as a GitHub Release on
merge. Don't start broad, undiscussed work across multiple phases/areas in one session — confirm
which task a change belongs to first.

**`/next-task` is the sanctioned way to execute a task** (ADR-038): it selects the next actionable
task (refusing anything `Blocked`), reads only the ADRs and requirement sections that task's Notes
cite, plans, branches, implements with tests, reviews the diff against both `docs/decisions.md` and
`docs/project_requirements.md`, runs the verification gates, updates the task's status, commits and
opens the PR — then stops. It never merges and never promotes.

### The `.claude/` execution layer

`docs/` says *what and why*; `PRODUCTION_UPDATE_PLAN.md` says *what's left*; `.claude/` says *how a
task gets done* — the `/next-task` skill, its subagents, and the guard hooks. **It holds procedure
and pointers only.** If a file under `.claude/` ever explains *why* something is built a certain
way, that's a bug in the same way an `Open` row outside `roadmap.md` is: it cites ADR-018, it never
restates it.

## Commands

There is no test suite, linter, or CI configured yet (each app's `tests.py` is an empty stub). The commands below are what the current tooling supports.

```bash
# Environment (repo already has a .venv; recreate with your own Python if needed)
pip install -r requirements.txt   # NOTE: requirements.txt is UTF-16LE encoded — re-save as UTF-8 if your pip/tooling chokes on it

# Run dev server (uses bakery/settings/base.py, hardcoded DEBUG=True + dev secrets)
python manage.py runserver

# Migrations
python manage.py makemigrations
python manage.py migrate

# Django's test runner, once tests exist
python manage.py test                    # all apps
python manage.py test control            # single app
python manage.py test control.tests.SomeTestCase.test_method   # single test

# Static files (required before Docker/Heroku deploy — whitenoise serves from bakery/staticfiles)
python manage.py collectstatic --noinput

# Docker
docker-compose up   # uses docker-compose.yaml; expects an external `bakery_simple` network and DATABASE_URL env
```

Database is PostgreSQL. Local/base settings hardcode `postgres`/`simple` credentials; there is no separate local/test settings module — `manage.py` always loads `bakery.settings.base` via `DJANGO_SETTINGS_MODULE`.

## Architecture

### Settings split

- `bakery/settings/base.py` — the settings module actually used by `manage.py` and local/Docker runs. Contains hardcoded `SECRET_KEY`, hardcoded DB credentials, hardcoded `ALLOWED_HOSTS`, and `DEBUG = True`. There is no `local.py`/`test.py` yet — everything not on Heroku runs on these dev defaults.
- `bakery/settings/heroku.py` — production overrides, imports `from bakery.settings.base import *` then overrides `DEBUG`, `SECRET_KEY`, `ALLOWED_HOSTS`, and `DATABASES` from environment variables via `django-environ`. Nothing currently sets `DJANGO_SETTINGS_MODULE` to this file in-repo (Heroku config presumably sets it externally) — verify before assuming it's live.

### App layout

Three Django apps, routed from `bakery/urls.py`:

- `core` — just the public landing/cover page (`core.urls`, namespace `core`), essentially unused beyond `/`.
- `accounts` — a custom `user_login` view (`accounts.views.user_login`) alongside Django's built-in `django.contrib.auth.urls` mounted at `/accounts/`. The custom view duplicates what `django.contrib.auth` already provides and logs failed login attempts (including the submitted password) via `print()` — a known issue tracked in the update plan, not a pattern to copy.
- `control` — the actual application. Everything (dashboard, raw materials, suppliers, base recipes, products, settings/export/user management) lives in one `control/views.py` and is routed under `/control/` (namespace `control`).

### Domain model (`control/models.py`)

```
Supplier (PK = name, not a surrogate key)
   ↓ FK
RawMaterial (price, quantity, unit, categorie)
   ↓ FK (via through-style models)
Bs_Ingredients  → belongs to Base_recipes   (base recipe costing)
Recipe_Ingredients → belongs to Product     (sellable product costing)
```

`Base_recipes` and `Product` are separate, parallel concepts (a "base recipe" like a dough/batter vs. a sellable `Product`), each with its own ingredient-line model (`Bs_Ingredients` / `Recipe_Ingredients`) rather than a shared polymorphic ingredient line. Cost/margin math (`cost`, `net_price`, `margin_percent`, `margin_value`) is defined as `@property` methods on these models **and separately re-implemented inline** inside `control/views.py` (`Dashboard`, `Base_recipe`, `Product_List` all loop over querysets and recompute cost/margin by hand using `float()` instead of reusing the model properties or `Decimal`). When touching costing/margin logic, expect to update both places until this is consolidated into a service layer (planned in `PRODUCTION_UPDATE_PLAN.md` Phase 4).

Known naming/data quirks carried from the prototype (also listed in the update plan, don't "fix" incidentally as a drive-by — they're tracked for a deliberate migration): `categorie` (not `category`), `recipe_yeld` (not `recipe_yield`), `Supplier.phone` typed as `IntegerField`, `RawMaterial.quantity` typed as `CharField` instead of numeric, `Supplier.name` used as primary key.

### Views and templates

All `control` views live in a single `views.py` using Django generic `ListView`/`CreateView`/`UpdateView`/`DeleteView`, mostly with `fields = '__all__'` (no dedicated ModelForms except `control/forms.py: Raw_Material_Form`, which isn't actually wired into any view). Templates are per-app under `<app>/templates/`, `APP_DIRS = True`, with shared static assets in `bakery/static/` (Bootstrap, custom CSS/JS per page, no build pipeline/bundler). CSV export views (`export_suppliers`, `export_raw_materials`, etc.) build CSVs by hand with the `csv` module directly in the view.

Access control is enforced inconsistently: views don't consistently use `LoginRequiredMixin`, and staff-only intent is expressed ad hoc rather than via a real permission scheme.
