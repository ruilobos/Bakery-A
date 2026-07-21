# Bakery Production Update Plan

## Objective

Turn Bakery from a prototype Django application into a secure, maintainable, tested, observable, and deployable production web application.

## Desired End State

- Modern supported Python and Django stack
- Clean, reproducible dependency management
- Secure configuration and secrets handling
- Production-grade PostgreSQL schema and migrations
- Strong authentication, authorization, and auditability
- Reusable, maintainable frontend architecture
- Automated quality gates: formatting, linting, tests, CI/CD
- Reliable deployment, monitoring, backup, and rollback procedures

## Current High-Risk Issues to Address First

1. Hardcoded `SECRET_KEY`, database credentials, and `DEBUG = True`
2. Weak access control enforced mostly in templates instead of views
3. Inconsistent deployment/runtime configuration across Docker, Heroku, and local setup
4. Generated files committed to the repository (`staticfiles`, `__pycache__`, IDE folders)
5. Model, template, and view bugs that can break core flows
6. Minimal test coverage and no real quality gate before deployment
7. Database model inconsistencies and missing production data practices

## Recommended Target Stack

### Python and Django

- Upgrade Python to **3.12** as the primary target runtime
- Plan a follow-up validation path for **3.13** once all dependencies and hosting support are confirmed
- Upgrade Django to the **current supported LTS release** for the project roadmap
- If the hosting environment and package support allow it, target **Django 5.2 LTS**
- Otherwise upgrade in stages: `3.2 -> 4.2 LTS -> current LTS`

### Dependency Strategy

- Replace the current ad hoc dependency state with pinned, reviewed, production-safe dependencies
- Normalize `requirements.txt` encoding to UTF-8
- Split dependencies into:
  - `requirements/base.txt`
  - `requirements/dev.txt`
  - `requirements/prod.txt`
- Use `pip-tools` or an equivalent lock workflow to generate deterministic pinned requirements
- Remove unused packages and confirm every dependency has an owner and purpose

### Candidate Dependency Refresh

- Django -> current supported LTS
- `whitenoise` -> current stable version compatible with chosen Django version
- `gunicorn` -> current stable version
- `psycopg2-binary` -> replace with `psycopg[binary]` or production-approved PostgreSQL driver strategy after deployment review
- `Pillow` -> current stable version
- `django-environ` -> current stable version
- `asgiref`, `sqlparse`, `tzdata`/`pytz` -> align with selected Django release requirements
- Review whether `mathfilters` is still needed; remove if calculations move to views/services
- Add `django-storages[s3]` + `boto3` once user-uploaded media (product photos, profile pictures) moves to S3-compatible object storage — see Phase 2/3/7 below and `docs/decisions.md` ADR-005

## Phase 1 - Stabilize the Repository

### Source Control Cleanup

- Remove generated and local-only artifacts from version control:
  - `__pycache__/`
  - `bakery/staticfiles/`
  - `.idea/`
  - `.venv/`
  - OS/editor temporary files
- Expand `.gitignore` to cover Python, Django, environment, build, and IDE artifacts
- Keep only source assets in `bakery/static/`

### Project Structure Cleanup

- Standardize settings into a package such as:
  - `settings/base.py`
  - `settings/local.py`
  - `settings/test.py`
  - `settings/production.py`
- Remove dead code, duplicate assets, and unused views/forms
- Replace inconsistent naming over time:
  - `categorie` -> `category`
  - `recipe_yeld` -> `recipe_yield`
  - `Base_recipes` -> `BaseRecipe`
  - `Bs_Ingredients` -> `BaseRecipeIngredient`
  - `Recipe_Ingredients` -> `ProductIngredient`
- Use transitional migrations and compatibility layers instead of risky big-bang renames

## Phase 2 - Security and Configuration Hardening

### Configuration

- Move all secrets to environment variables or a secret manager
- Remove all hardcoded credentials from source code
- Set `DEBUG = False` outside local development
- Define environment-specific `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, and cookie settings
- Add secure defaults:
  - `SECURE_SSL_REDIRECT`
  - `SESSION_COOKIE_SECURE`
  - `CSRF_COOKIE_SECURE`
  - `SECURE_HSTS_SECONDS`
  - `SECURE_HSTS_INCLUDE_SUBDOMAINS`
  - `SECURE_HSTS_PRELOAD`
  - `X_FRAME_OPTIONS`

### Authentication and Authorization

- Protect all business views with `LoginRequiredMixin`
- Protect admin-only operations with explicit permission classes or mixins
- Stop relying on template-only `is_staff` checks for security
- Introduce role-based permissions:
  - admin/owner
  - manager
  - staff/operator
  - read-only/auditor
- Review whether the Django admin and app settings area should expose the same operations
- Add audit logging for user management and destructive actions

### Input and Data Protection

- Replace unsafe `print()` login diagnostics with structured logging that never records passwords
- Validate and sanitize all form input
- Add server-side protection for export endpoints
- Implement media handling properly instead of leaving it half-configured: remove the broken
  leftover `MEDIA_ROOT` path and move user-uploaded media (product photos, profile pictures — see
  Phase 3) to S3-compatible object storage, with credentials held as environment variables, never
  hardcoded (Cloudflare R2 is the lead candidate — see `docs/tech_stack.md` and ADR-005)

## Phase 3 - Database Redesign and Data Governance

## Database Goals

- Make the schema consistent, normalized, and migration-safe
- Preserve historical business data
- Improve query performance and data integrity
- Prepare for backups, restore drills, and controlled schema evolution
- Introduce multi-tenancy: one shared database, tenant-scoped rows, per `docs/decisions.md`
  ADR-006/ADR-008 — the app is confirmed multi-tenant SaaS, not single-bakery

### Multi-Tenancy (new, per ADR-006/ADR-008)

- Add a `Bakery` model (the tenant) as the root of the tenant hierarchy
- Add a tenant FK to every business table that currently has none: `Supplier`, `RawMaterial`,
  `Base_recipes`, `Bs_Ingredients`, `Product`, `Recipe_Ingredients`, and the future `Profile` model
- Enforce tenant scoping at the query layer everywhere (managers/service layer that always filter
  by the current tenant) — this is a correctness- and security-critical convention, not optional;
  see Phase 6 for dedicated cross-tenant isolation tests
- Scope user roles/permissions (Phase 2) per tenant, not globally — a bakery's admin/owner
  administers only their own tenant's data
- Database topology stays as-is: app and database remain separate services/containers regardless
  of tenancy model (ADR-007) — multi-tenancy is a schema/row-scoping decision, not an infra one

### Schema Review and Refactor

- Redesign the current domain model with explicit naming and constraints

#### Supplier

- Replace supplier name as primary key with a generated numeric or UUID primary key
- Keep supplier name unique if business rules require it
- Change phone number from integer to string
- Add optional fields for address, tax/business identifier, active flag, and timestamps

#### Raw Material

- Change `quantity` from `CharField` to `DecimalField`
- Clarify whether price means:
  - price per purchase unit
  - price per normalized base unit
- Add normalized unit handling for cost calculations
- Add SKU/code uniqueness rules where appropriate
- Add active/inactive status instead of hard deletes where business history matters

#### Base Recipe and Product

- Standardize yield, unit, and cost fields
- Ensure VAT representation is consistent and documented
- Decide whether product pricing history must be versioned
- Consider storing calculated values as derived data only, not editable business data
- Add a `photo` field on `Product` for a product image, stored in object storage rather than local
  disk (see "Media & User Profiles" below and `docs/tech_stack.md`)

#### Ingredient Relations

- Keep separate through tables for recipe ingredients if business workflows differ
- Otherwise evaluate a shared ingredient line model with a typed parent reference
- Add uniqueness constraints to avoid duplicate ingredient lines for the same parent/item/unit combination

#### Media & User Profiles

- Add a profile picture field for app users — likely a `Profile` model with a one-to-one to
  Django's `User` rather than a custom user model, to avoid a disruptive auth migration
- Both this and the `Product.photo` field above store only a reference (object storage key/URL) in
  Postgres; the binary file itself lives in object storage, never in the database
- Treat profile pictures as personal data from day one — see `docs/gdpr.md` data inventory and data
  subject rights (an account deletion must also delete the stored photo, not just the DB row)

### Database Best Practices

- Add `created_at` and `updated_at` fields to all core business tables
- Add soft delete or archive patterns for entities that should remain historically visible
- Add `db_index=True` or explicit indexes on common filter/join paths
- Add unique constraints and check constraints where business rules exist
- Use `Decimal` consistently for money and quantities
- Standardize units and categories using one of these approaches:
  - controlled enums if values are stable
  - lookup/reference tables if values are business-managed

### Migration Strategy

1. Document current schema and data quality issues
2. Create a full database backup
3. Introduce additive fields first
4. Backfill data with safe migrations or management commands
5. Switch application code to new fields
6. Remove legacy fields only after validation and deployment stability

### Data Quality and Governance

- Define canonical units for costing
- Add data validation rules for prices, VAT, yields, and quantities
- Create import/export contracts and field definitions
- Add seed/reference data strategy for categories and units
- Create backup, restore, and retention procedures
- Add migration rollback guidance for every schema change release
- Build a tenant-scoped **full data export** (ADR-008): given a tenant, export all of that
  tenant's rows across every tenant-scoped table in a portable, DBMS-agnostic format (plain SQL
  `CREATE TABLE`/`INSERT` statements, or a per-table CSV bundle + relationship manifest) — not a
  Postgres-specific `pg_dump`, so a departing tenant can import it elsewhere
- Build a dedicated **GDPR personal-data export** (ADR-009), separate from both the above and the
  existing bulk admin CSV export: scoped to one data subject, containing only that subject's
  personal data across models — see `docs/gdpr.md` §3 Portability

### Database Operations for Production

- Use managed PostgreSQL or a well-maintained dedicated PostgreSQL service
- Enable automated backups and point-in-time recovery when available
- Separate application and database credentials by environment
- Add connection pooling if traffic or deployment topology requires it
- Monitor slow queries and add indexes based on observed workload

## Phase 4 - Backend Modernization

### Django Application Architecture

- Move business calculations out of large views into dedicated services/domain modules
- Keep views thin: query, validate, delegate, render
- Use class-based views consistently or function-based views consistently, not a mix without reason
- Replace broad and ineffective exception patterns with correct query handling
- Remove dead custom auth code if Django auth views are the chosen standard

### Forms and Validation

- Replace `fields = "__all__"` on sensitive create/update flows with explicit forms
- Add model forms with business validation for:
  - quantities
  - units
  - VAT
  - price ranges
  - uniqueness constraints
  - uploaded file type and size for product photos and profile pictures
- Use form widgets and help text for clearer operator workflows

### Query and Performance Review

- Use `select_related` and `prefetch_related` on supplier/product/ingredient listings
- Avoid repeated cost calculations inside nested loops in views
- Add service-layer aggregate calculations for dashboard and product costing
- Cache expensive dashboard summaries if needed

### API and Integration Readiness

- Decide whether the production roadmap needs a JSON API
- If yes, introduce Django REST Framework or a small read-only API surface for reporting/export/integrations
- Version any public API from the start

## Phase 5 - Frontend Modernization

### Frontend Technology Direction

The project does not need a full SPA to become production-ready. A modern server-rendered Django frontend is enough.

### Recommended Frontend Updates

- Keep Django templates for page rendering
- Introduce a shared `base.html` layout
- Replace duplicated navbar/footer/page scaffolding with reusable template blocks and partials
- Replace hardcoded static paths with `{% load static %}` and `{% static %}`
- Update Bootstrap to a current stable version
- Remove unused empty JavaScript files or replace them with purposeful modules

### Suggested Tooling

- Use a modern frontend asset pipeline such as **Vite** for:
  - SCSS/CSS bundling
  - small JavaScript modules
  - cache-busted asset builds
- For dynamic interactions, prefer lightweight progressive enhancement:
  - vanilla JavaScript modules
  - optionally HTMX for server-driven interactivity
- Add linting/formatting for templates, CSS, and JS where practical

### Frontend UX Improvements

- Build real search/filter flows or remove fake search inputs
- Improve forms, validation errors, empty states, and destructive action confirmations
- Add image upload/preview UI for product photos and user profile pictures, with a clear empty-state placeholder when no photo is set
- Improve accessibility:
  - semantic HTML
  - form labels
  - focus states
  - keyboard navigation
  - color contrast review
- Make data tables more usable on mobile and tablet

## Phase 6 - Testing and Quality Gates

### Test Coverage

- Add unit tests for:
  - model validation
  - costing logic
  - margin logic
  - permissions
  - exports
- Add integration tests for critical CRUD workflows
- Add regression tests for currently known broken areas
- Add smoke tests for login, dashboard, raw materials, suppliers, recipes, products, and settings

### Tooling

- Add formatting and linting tools:
  - `ruff`
  - `black`
  - optional `isort` if not covered by `ruff`
- Add template linting if the team wants HTML consistency
- Add test execution to CI

### CI/CD

- Create a pipeline that runs:
  - install
  - lint
  - tests
  - security checks
  - build
- Block deployments when checks fail

## Phase 7 - Observability and Operations

### Logging and Monitoring

- Add structured application logging
- Add error tracking (for example Sentry)
- Log security-relevant events, admin actions, and failed operations without leaking secrets
- Add health checks for app and database connectivity

### Deployment and Infrastructure

- Replace legacy Heroku assumptions with a documented deployment target — narrowed to Railway,
  Render, or DigitalOcean App Platform (see `docs/decisions.md` ADR-003)
- Standardize Docker for local development and production builds — deploy via the existing
  Dockerfile on whichever host is chosen rather than that platform's native buildpack, so behavior
  stays identical across all three candidates (see ADR-004)
- Fix `docker-compose.yaml` so it defines all required services correctly
- Separate local compose from production deployment definitions
- Provision an S3-compatible object storage bucket (Cloudflare R2 — see ADR-005) for user-uploaded
  media, decoupled from app compute so it's unaffected by which of the three hosts is picked;
  optionally front it with a custom domain/CDN
- Add:
  - static asset build step
  - migration release step
  - rollback procedure
  - environment documentation

### Production Runtime

- Run with Gunicorn or another supported process manager appropriate to the hosting platform
- Serve static files via CDN/object storage or a production-grade static strategy
- Define media storage properly if uploads are introduced
- Add uptime monitoring and alerting

## Phase 8 - Documentation and Team Readiness

- Rewrite `README.md` for production-oriented setup and development workflows
- Add architecture documentation:
  - app modules
  - data model
  - deployment overview
  - permissions model
- Add runbooks for:
  - deploy
  - rollback
  - backup/restore
  - rotating secrets
  - incident response

## Suggested Execution Order

1. Repository cleanup and settings refactor
2. Security fixes and permissions hardening
3. Dependency and runtime upgrade path
4. Database redesign and safe migrations
5. Backend refactor for business logic and forms
6. Frontend template consolidation and asset modernization
7. Test suite and CI/CD rollout
8. Observability, deployment hardening, and documentation

## Immediate First Release Scope

The first production-focused release should prioritize risk reduction over feature expansion.

- Remove secrets from code
- Split settings by environment
- Fix broken user delete flow and similar obvious defects
- Enforce authentication and authorization in views
- Clean repository artifacts
- Add basic automated tests for core flows
- Normalize deployment configuration
- Prepare dependency upgrade path with lock files

## Follow-Up Product Improvements

- Supplier price comparison workflows
- Search and filtering across operational data
- Historical cost snapshots and pricing trend reporting
- Better user and role management
- Reporting dashboards with optimized queries and caching

## Definition of "Production Ready" for Bakery

Bakery should only be considered production-ready when it meets all of the following:

- No secrets in source control
- Supported Python and Django versions
- Reproducible builds and pinned dependencies
- Full environment separation
- Protected business actions with real permissions
- Safe and tested database migrations
- Backup and restore strategy documented and tested
- Automated tests and CI/CD in place
- Logging, monitoring, and error tracking enabled
- Deployment and rollback documented and repeatable
