# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Bakery is a Django web app (originally an MSc capstone prototype) that lets a bakery track raw materials, suppliers, and products, and computes per-product cost/margin from recipe ingredient data. It is currently being hardened from prototype to production quality — see `PRODUCTION_UPDATE_PLAN.md` for the authoritative, phased roadmap (security hardening, dependency/runtime upgrades, DB redesign, testing, CI/CD, observability). Treat that file as the source of truth for planned work; don't re-derive priorities from scratch.

This is also a broader redesign in progress — new features, GDPR compliance, and a possible tech
stack change are still being decided, not just the engineering hardening in
`PRODUCTION_UPDATE_PLAN.md`. That undecided material lives in `docs/`, not in this file.

## Planning & documentation (`docs/`)

Four living documents track decisions that aren't in the code yet. Read the relevant one(s)
before proposing anything in that area — don't re-derive a requirement or stack choice from
scratch if it's already marked `Open` or `Decided` there:

- `docs/project_requirements.md` — what the app should do: personas, per-area functional
  requirements, new feature backlog, non-functional requirements. Separate from engineering
  quality work (that's `PRODUCTION_UPDATE_PLAN.md`).
- `docs/tech_stack.md` — what it's built with: current vs. candidate vs. decided, per layer
  (runtime, dependencies, backend, frontend, infra, quality tooling).
- `docs/gdpr.md` — personal data inventory, legal basis, data subject rights, retention,
  breach process. Data-inventory work here is a discovery task, not a coding task — the
  inventory needs to exist before consent/deletion/audit-log code gets written against it.
- `docs/decisions.md` — append-only ADR log. Every real decision (stack, architecture, data
  model, process — including the branch strategy in ADR-001) gets logged here with context and
  alternatives considered, not just stated in chat. Never delete an entry; supersede it instead.
- `docs/roadmap.md` — the phase/branch tracker: every phase from `PRODUCTION_UPDATE_PLAN.md`
  plus new-feature/GDPR/stack-decision phases, each with a branch name, status, and scope
  summary. Check this before starting work to confirm which phase/branch a task belongs to, and
  update its status as work moves (`Not started` → `Planned` → `In progress` → `In review` →
  `Done`).

Rows/sections marked `Open` in these docs are not settled — don't write code as if they were
decided. When a decision is actually made (in conversation or otherwise), update the relevant doc
**and** add an ADR to `docs/decisions.md` in the same session.

### Workflow this repo follows

Per ADR-001 in `docs/decisions.md`: `main` stays deployable; each phase or feature gets its own
branch (e.g. `phase-1-repo-cleanup`, `gdpr-data-inventory`) opened as a PR against `main`, planned
in Plan Mode before implementation starts, and merged before the next phase branch begins. Don't
start broad, undiscussed work across multiple phases/areas in one session — confirm which
phase/branch a task belongs to first.

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
