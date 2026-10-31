# CLAUDE.md

Bakery is a Django app (originally an MSc prototype) that tracks a bakery's raw materials,
suppliers and products, and computes per-product cost and margin from recipe ingredients. It is
being hardened to production quality, and redesigned (features, GDPR, stack) along the way.

## Where things live

- **`PRODUCTION_UPDATE_PLAN.md`** — the task backlog: Epics 1–19, tasks `3.12` = Epic 3 task 12,
  the run order. The source of truth for planned work; reference task IDs in plans, commits, PRs.
- **`docs/`** — requirements, tech stack, the ADR log, open questions. Read
  [`docs/README.md`](docs/README.md) before any *planning* work.
- **Never read those files whole. Look up the piece you need** ([ADR-051](docs/decisions.md)):

```bash
python -m scripts.docs_lookup next              # the next task in the run order
python -m scripts.docs_lookup task 2.1          # a task row, verbatim, with its branch
python -m scripts.docs_lookup adr 37 41         # ADR entries in full
python -m scripts.docs_lookup roadmap 11.1      # an open question
python -m scripts.docs_lookup req "User roles"  # a requirements section (`stack <heading>` for tech_stack.md)
```

- A `Blocked` task waits on an open question in `docs/roadmap.md`: make and log the ADR first,
  never implement it. Settled questions are not re-opened; check an ADR's **Rejected** first.
- Docs state intent; the **code states fact**. Re-measure any number or constraint from a doc
  before it sets a task's scope (ADR-040).

## Workflow

- **`/next-task` executes a task** (ADR-038, ADR-051): first open run-order entry, one task = one
  branch `<epic-branch>-<task-id>` from updated `main` = one PR (ADR-037), squash-merged by the
  human. Plan Mode approval only for risky tasks (models/migrations, auth/security, >~5 files).
  It never merges or promotes. Confirm which task a change belongs to before broad work.
- `main` integrates; `production` is what's deployed (ADR-010). A release is its own PR from
  `main`, titled `Release vX.Y.Z` (ADR-042), merged with a merge commit (ADR-041);
  `.github/workflows/release.yml` tags it. Until 12.5, a `0.y.z` release PR records local
  verification of the `main` it promotes (ADR-050).
- `.claude/` holds procedure and pointers only, never the *why* (cite the ADR). Guard hooks:
  `.claude/settings.json` runs `scripts/guard_hooks.py` (task 1.15).
- Run `/clear` between tasks.

## Commands

```bash
pip install -r requirements.txt       # UTF-8; keep it out of Word, which re-encodes it
pip install -r requirements-dev.txt   # pytest, ruff; never in the image (ADR-046)
cp .env.example .env                  # then fill it in: secrets come only from the environment (2.1)

python scripts/launch_local.py        # pull main, rebuild, migrate, serve :8000 beside postgres:17
                                      # --no-pull launches the checkout as it is
# Host-side dev server (reaches compose's postgres through .env's localhost DATABASE_URL):
DJANGO_SETTINGS_MODULE=bakery.settings.local python manage.py runserver            # bash
$env:DJANGO_SETTINGS_MODULE="bakery.settings.local"; python manage.py runserver    # PowerShell

python manage.py makemigrations && python manage.py migrate
pytest                                         # app tests, under bakery.settings.test; django_db needs postgres
python -m unittest discover -s scripts -t .    # scripts/ tooling tests (CI: "Tooling tests")
ruff check . && ruff format --check .          # lint + format (CI runs both)
python -m scripts.check_static_refs            # every template static path resolves (CI: Django checks)
python manage.py collectstatic --noinput
docker compose up --build                      # production image (DEBUG=False): rebuild after changes
```

CI: `.github/workflows/ci.yml` on every PR into `main`/`production` (no `pytest` yet: 6.12, 6.24);
`release.yml` tags releases.

## Settings (ADR-028)

- `bakery/settings/base.py` **is production** and the default for `manage.py`, `wsgi.py`, `asgi.py`
  and the `Dockerfile`. Values come from the environment via `django-environ`; **`DEBUG` defaults
  to `False`**. There is no `production.py`.
- `local.py` — `DEBUG = True`; must be requested via `DJANGO_SETTINGS_MODULE`.
- `test.py` — fast hasher, plain static storage; `pytest` uses it (`pyproject.toml`).
- `SECRET_KEY` and `DATABASE_URL` have **no default** (2.1): locally they come from `.env`; CI and
  the image build use public placeholders. `ALLOWED_HOSTS`/`DEBUG` keep fallbacks until 2.19.
  `collectstatic` runs at image build on placeholders set **inline on the `Dockerfile`'s `RUN`
  line, never `ENV`** (ADR-049).
- `base.py` is **HTTPS-only** (2.4): it redirects plain HTTP and sets Secure cookies and HSTS.
  `local.py` and `test.py` turn the redirect off; compose's `web` alone sets `INSECURE_LOCAL_HTTP`.
- Database: PostgreSQL 17 (compose `postgres` service, published on `127.0.0.1` only).

## Code map and known quirks

- Apps: `core` (landing page), `accounts` (a custom `user_login` that **logs submitted passwords via
  `print()`** — a tracked issue, not a pattern), `control` (everything else, all in one
  `control/views.py`, routed under `/control/`).
- Model chain: `Supplier` (PK = `name`) → `RawMaterial` → `Bs_Ingredients` (→ `BaseRecipe`) and
  `Recipe_Ingredients` (→ `Product`).
- Cost math lives in model `@property`s **and** is re-implemented inline with `float()` in
  `Dashboard`, `Base_recipe`, `Product_List`; margins exist only in the views. Change both until
  Epic 4's service layer consolidates them.
- **Deliberate quirks, don't fix as a drive-by** (the guard hook blocks it): `categorie`,
  `Bs_Ingredients`, `Recipe_Ingredients` stay until 3.73/3.74 delete them (ADR-039);
  `Supplier.phone` is an `IntegerField`, `RawMaterial.quantity` a `CharField`.
- Views are generic CBVs with `fields = '__all__'`, no ModelForms; CSV exports are hand-built in
  views. **No `control` view requires login**, and `User_Create`/`User_Update` expose
  `is_superuser` — owned by 2.17, 2.7, 4.7; don't patch as a drive-by.
- Templates per app (`APP_DIRS = True`); shared static in `bakery/static/`, no bundler.
