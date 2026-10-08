"""
Check that every static file a template names exists (task 1.13, ADR-045).

CI's `Docker build` job runs `collectstatic`, which never reads templates, so a
template pointing at a missing asset passes CI and breaks the page instead: today
as a 404, and once 5.3 moves the templates to `{% static %}`, as a render-time
`ValueError` from manifest storage, a 500.

This reads every template in the project's own apps and takes each `src` or `href`
value with a `static/` path segment and each literal `{% static '...' %}` argument.
It reports a prefix that is neither STATIC_URL nor `static/` behind zero or more
`../`, and a path the staticfiles finders cannot find.

    python -m scripts.check_static_refs

It proves the file exists, not that a relative URL reaches it from the page that
renders it (ADR-045's Traps); 5.3's `{% static %}` closes that. A `{% static %}`
whose argument is a variable cannot be checked, and is skipped.

CI runs it in the `Django checks` job, which installs the app's requirements. The
checking itself is standard library only, so `scripts/`'s tests still run on a bare
`python3`: Django is imported inside `main()`.
"""

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ATTRIBUTE = re.compile(r"""\b(?:src|href)\s*=\s*(["'])(.*?)\1""", re.IGNORECASE)
STATIC_TAG = re.compile(r"""\{%\s*static\s+(["'])(.*?)\1\s*%\}""")
# A scheme (https:, mailto:) or a protocol-relative //host.
EXTERNAL = re.compile(r"^(?:[a-z][a-z0-9+.-]*:|//)", re.IGNORECASE)


def references(text, static_url="/static/"):
    """
    Yield `(line, path, problem)` for each static reference in a template.

    `path` is relative to STATIC_URL, as the finders take it, or None when
    `problem` says why the reference cannot name a static file.
    """
    name = re.escape(static_url.strip("/"))
    segment = re.compile(r"(?:^|/)" + name + "/")
    accepted = re.compile(
        r"(?:" + re.escape(static_url) + r"|(?:\.\./)*" + name + "/)(.+)"
    )

    for match in ATTRIBUTE.finditer(text):
        value = match.group(2).strip()
        # Template-built values are checked through their {% static %} tag, if any.
        if EXTERNAL.match(value) or "{{" in value or "{%" in value:
            continue
        if not segment.search(value):
            continue
        line = _line(text, match.start(2))
        found = accepted.fullmatch(value)
        if found:
            yield line, _without_query(found.group(1)), None
        else:
            yield line, None, f"unrecognised static prefix in {value!r}"

    for match in STATIC_TAG.finditer(text):
        yield _line(text, match.start(2)), _without_query(match.group(2)), None


def check(templates, find, static_url="/static/"):
    """
    Check `(name, text)` templates against `find(path)`, which is truthy for a
    static file that exists. Return the number of references and the problems,
    each as `name:line: message`.
    """
    count, problems = 0, []
    for name, text in templates:
        for line, path, problem in references(text, static_url):
            count += 1
            if problem is None and not find(path):
                problem = f"no static file named {path!r}"
            if problem:
                problems.append(f"{name}:{line}: {problem}")
    return count, problems


def run(templates, find, static_url="/static/", out=None):
    """Check the templates, print the outcome and return the exit code."""
    out = out or sys.stdout
    templates = list(templates)
    if not templates:
        # Finding nothing to check is a broken check, not a passing one.
        print("No templates found, so nothing was checked.", file=out)
        return 1

    count, problems = check(templates, find, static_url)
    for problem in problems:
        print(problem, file=out)
    if problems:
        print(
            f"{len(problems)} of {count} static references in {len(templates)} "
            "templates do not resolve.",
            file=out,
        )
        return 1
    print(
        f"All {count} static references in {len(templates)} templates resolve.",
        file=out,
    )
    return 0


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bakery.settings.test")
    import django

    django.setup()

    from django.apps import apps
    from django.conf import settings
    from django.contrib.staticfiles import finders

    # The project's own apps sit at the repo root; Django's admin and anything
    # else from site-packages are not this check's business.
    directories = [
        Path(path) for engine in settings.TEMPLATES for path in engine["DIRS"]
    ]
    directories += [
        Path(config.path) / "templates"
        for config in apps.get_app_configs()
        if Path(config.path).resolve().parent == ROOT
    ]
    templates = [
        (path.resolve().relative_to(ROOT).as_posix(), path.read_text(encoding="utf-8"))
        for directory in directories
        if directory.is_dir()
        for path in sorted(directory.rglob("*.html"))
    ]
    return run(templates, finders.find, settings.STATIC_URL)


def _line(text, index):
    return text.count("\n", 0, index) + 1


def _without_query(path):
    return re.split(r"[?#]", path, maxsplit=1)[0]


if __name__ == "__main__":
    sys.exit(main())
