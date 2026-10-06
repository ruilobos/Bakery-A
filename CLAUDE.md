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

### Docs state intent; the code states fact

These documents are authoritative for **what to do, why, and in what order**. They are *not*
authoritative for **what the code currently contains** — every such claim was measured once, by
hand, and has been drifting since.

So before a number, a supersession or a technical constraint is allowed to set a task's scope,
**re-derive it from the code** via the `codecheck` subagent (ADR-040). Three have already been
wrong: a site count that matched a substring (`categorie` inside `categories`), a task believed
to absorb a rename it never performs, and a migration constraint guarding a deployment that does
not exist.

A claim that fails is a **defect to repair in the doc** — its own ADR and its own PR. It is never
something to quietly work around, and never a reason to widen the task in hand.

### Workflow this repo follows

Per ADR-010 (supersedes ADR-001), as amended by ADR-037: `main` is the integration/dev-test
branch, not what's deployed to real users — a separate `production` branch holds what's live.

**One task is one feature is one PR** (ADR-037). Each backlog task gets its own branch named
`<epic-branch>-<task-id>` (e.g. `phase-1-repo-cleanup-1.1`), branched from an updated `main`,
planned in Plan Mode before implementation starts, and squash-merged before the next begins.
**An epic groups and sequences tasks; it is not a branch.** No stacking, no direct commits.
Promote validated work from `main` to `production` via its own release PR, titled `Release vX.Y.Z`
(ADR-042) and merged with a merge commit, never squashed (ADR-041); on merge,
`.github/workflows/release.yml` tags it and publishes the GitHub Release. Don't start broad,
undiscussed work across multiple phases/areas in one session — confirm which task a change belongs
to first.

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

`ruff` lints and formats (6.10, ADR-034), configured in `pyproject.toml`'s `[tool.ruff]`, and the app suite is two smoke tests in `core/tests.py`. The runner is `pytest` (6.23, ADR-034), configured in `pyproject.toml` and installed from `requirements-dev.txt`; it also collects the `scripts/` tooling's `unittest` tests, which CI runs on their own as its `Tooling tests` check, `python -m unittest discover -s scripts -t .` (1.21). CI runs no `pytest` yet (6.12, 6.24). Two workflows: `.github/workflows/ci.yml` runs tasks 1.11's, 1.21's and 6.10's checks on every PR into `main`/`production`, and `.github/workflows/release.yml` tags releases. The commands below are what the current tooling supports.

```bash
# Environment (repo already has a .venv; recreate with your own Python if needed)
pip install -r requirements.txt   # UTF-8 since task 1.4; keep it out of Word, which re-encodes it
pip install -r requirements-dev.txt   # pytest and other dev tooling; never in the image (ADR-046)

# Local environment (ADR-014, task 1.12): pull main, rebuild, migrate, then launch on :8000
# beside postgres:17. The web image is production (DEBUG=False), so relaunch to see a change.
python scripts/launch_local.py              # --no-pull launches the checkout as it is, e.g. a feature branch

# Quick host-side dev server against that postgres (needs a hosts entry `127.0.0.1 postgres`, or
# DATABASE_URL pointing at localhost). manage.py defaults to bakery.settings.base, which IS
# production (ADR-028) and runs DEBUG=False — so ask for the local module:
DJANGO_SETTINGS_MODULE=bakery.settings.local python manage.py runserver   # bash
$env:DJANGO_SETTINGS_MODULE="bakery.settings.local"; python manage.py runserver  # PowerShell

# Migrations
python manage.py makemigrations
python manage.py migrate

# Django's test runner, once tests exist
python manage.py test                    # all apps
python manage.py test control            # single app
python manage.py test control.tests.SomeTestCase.test_method   # single test

# Lint and format (6.10), with ruff from requirements-dev.txt; CI runs check and format --check
ruff check .                # --fix applies the safe fixes
ruff format .               # --check reports without rewriting

# Static files (required before Docker/Heroku deploy — whitenoise serves from bakery/staticfiles)
python manage.py collectstatic --noinput

# Docker
docker compose up --build   # app on :8000 + postgres:17. The web image is production (DEBUG=False), so rebuild after changes
```

Database is PostgreSQL 17, locally the compose `postgres` service. `base.py` falls back to the `postgres`/`simple` dev credentials when `DATABASE_URL` is unset (2.1 removes that), and `manage.py` defaults to `bakery.settings.base`, so host-side `runserver` names `bakery.settings.local` and CI names `bakery.settings.test`, as `pytest` does from `pyproject.toml`; its `django_db` tests need that `postgres` running. The launcher's containers run `base.py` itself: the `web` image is the production image (ADR-043).

## Architecture

### Settings split

Three modules per ADR-028, **no `production.py`** — `base.py` *is* production, and the overlays opt
*into* unsafe or convenient behaviour so the accident lands on the safe side.

- `bakery/settings/base.py` — production, and the default for `manage.py`, `wsgi.py`, `asgi.py` and the `Dockerfile`. Every environment-sensitive value (`SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DATABASE_URL`) is read from the environment via `django-environ`. **`DEBUG` defaults to `False` here.**
- `bakery/settings/local.py` — development: `DEBUG = True` and a local host list. Must be requested explicitly via `DJANGO_SETTINGS_MODULE`.
- `bakery/settings/test.py` — minimal: `DEBUG = False`, fast password hasher, plain static storage. `pytest` runs under it (6.23), which needed nothing added; extend it when a test does.

**The values are still in the repo as `default=` fallbacks**, so nothing yet fails when a variable is
unset. Task **2.1** removes the secret fallbacks; **2.19** removes them entirely so a missing
variable raises `ImproperlyConfigured` — 2.19 is `Blocked` on roadmap question **9.22**, because a
raising module would break `collectstatic` at image build.

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
Bs_Ingredients  → belongs to BaseRecipe     (base recipe costing)
Recipe_Ingredients → belongs to Product     (sellable product costing)
```

`BaseRecipe` and `Product` are separate, parallel concepts (a "base recipe" like a dough/batter vs. a sellable `Product`), each with its own ingredient-line model (`Bs_Ingredients` / `Recipe_Ingredients`) rather than a shared polymorphic ingredient line. Cost/margin math (`cost`, `net_price`, `margin_percent`, `margin_value`) is defined as `@property` methods on these models **and separately re-implemented inline** inside `control/views.py` (`Dashboard`, `Base_recipe`, `Product_List` all loop over querysets and recompute cost/margin by hand using `float()` instead of reusing the model properties or `Decimal`). When touching costing/margin logic, expect to update both places until this is consolidated into a service layer (planned in `PRODUCTION_UPDATE_PLAN.md` Phase 4).

Known naming/data quirks carried from the prototype (also listed in the update plan, don't "fix" incidentally as a drive-by — they're tracked for a deliberate migration): `categorie` (not `category`), `Bs_Ingredients` / `Recipe_Ingredients` as parallel line models, `Supplier.phone` typed as `IntegerField`, `RawMaterial.quantity` typed as `CharField` instead of numeric, `Supplier.name` used as primary key. **`Base_recipes` and `recipe_yeld` were renamed by task 1.7** (ADR-039); the remaining three naming quirks are deliberate until 3.73 and 3.74 delete those columns and tables outright — renaming them would be edits to something being dropped.

### Views and templates

All `control` views live in a single `views.py` using Django generic `ListView`/`CreateView`/`UpdateView`/`DeleteView`, mostly with `fields = '__all__'` (no dedicated ModelForms except `control/forms.py: Raw_Material_Form`, which isn't actually wired into any view). Templates are per-app under `<app>/templates/`, `APP_DIRS = True`, with shared static assets in `bakery/static/` (Bootstrap, custom CSS/JS per page, no build pipeline/bundler). CSV export views (`export_suppliers`, `export_raw_materials`, etc.) build CSVs by hand with the `csv` module directly in the view.

Access control is enforced inconsistently: views don't consistently use `LoginRequiredMixin`, and staff-only intent is expressed ad hoc rather than via a real permission scheme.
