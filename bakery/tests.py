import importlib.util
import logging
import os
import re
import sys
from pathlib import Path
from unittest import mock

import environ
import pytest
from django.core.exceptions import ImproperlyConfigured

ROOT = Path(__file__).resolve().parent.parent
SETTINGS = ROOT / "bakery" / "settings"
BASE = SETTINGS / "base.py"
SECRETS = {
    "SECRET_KEY": "test-only-key",
    "DATABASE_URL": "postgres://user:pass@db.invalid:5432/name",
}
# Every variable base.py reads with no default: the secrets (task 2.1), then the
# two whose fallbacks task 2.19 deleted.
REQUIRED = {**SECRETS, "ALLOWED_HOSTS": "app.invalid", "DEBUG": "false"}
# What a host serving the app on its own domain would set (task 2.3).
HOST = {
    "ALLOWED_HOSTS": "bakery.example.com",
    "CSRF_TRUSTED_ORIGINS": "bakery.example.com,.example.org",
    "SESSION_COOKIE_DOMAIN": ".example.com",
    "CSRF_COOKIE_DOMAIN": ".example.com",
}
# The switch only compose's `web` sets (task 2.4).
PLAIN_HTTP = {"INSECURE_LOCAL_HTTP": "true"}


def load_base(environment):
    # A fresh copy of base.py under its own name, so the settings this run already
    # loaded stay untouched. read_env is patched out: a developer's .env must not
    # supply the very variable a test removes.
    spec = importlib.util.spec_from_file_location("base_under_test", BASE)
    module = importlib.util.module_from_spec(spec)
    no_dotenv = mock.patch.object(environ.Env, "read_env")
    only_these = mock.patch.dict(os.environ, environment, clear=True)
    with no_dotenv, only_these:
        spec.loader.exec_module(module)
    return module


def load_overlay(name, environment):
    # An overlay's `from bakery.settings.base import *` takes whatever sys.modules
    # holds, so handing it a base.py loaded under this environment is enough.
    base = load_base(environment)
    spec = importlib.util.spec_from_file_location(
        f"{name}_under_test", SETTINGS / f"{name}.py"
    )
    module = importlib.util.module_from_spec(spec)
    with mock.patch.dict(sys.modules, {"bakery.settings.base": base}):
        spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("missing", sorted(REQUIRED))
def test_base_fails_loudly_without_a_required_variable(missing):
    # Tasks 2.1 and 2.19 deleted their fallbacks: production must not boot on a
    # default (ADR-028).
    environment = {k: v for k, v in REQUIRED.items() if k != missing}
    with pytest.raises(ImproperlyConfigured, match=missing):
        load_base(environment)


def test_base_reads_both_secrets_from_the_environment():
    settings = load_base(REQUIRED)
    assert settings.SECRET_KEY == "test-only-key"
    assert settings.DATABASES["default"]["HOST"] == "db.invalid"
    assert settings.DATABASES["default"]["NAME"] == "name"


def test_base_reads_hosts_and_debug_from_the_environment():
    hosts = {"ALLOWED_HOSTS": "a.example.com,b.example.com", "DEBUG": "true"}
    settings = load_base({**REQUIRED, **hosts})
    assert settings.ALLOWED_HOSTS == ["a.example.com", "b.example.com"]
    assert settings.DEBUG is True


@pytest.mark.parametrize("value", ["", "0", "bogus"])
def test_only_a_true_debug_turns_it_on(value):
    # A blank or mistyped value must land on the safe side.
    assert load_base({**REQUIRED, "DEBUG": value}).DEBUG is False


def test_base_trusts_nothing_extra_by_default():
    # Task 2.3 kept Django's defaults for these, the restrictive ones.
    settings = load_base(REQUIRED)
    assert settings.CSRF_TRUSTED_ORIGINS == []
    assert settings.SESSION_COOKIE_DOMAIN is None
    assert settings.CSRF_COOKIE_DOMAIN is None


def test_base_reads_the_host_settings_from_the_environment():
    settings = load_base({**REQUIRED, **HOST})
    assert settings.CSRF_TRUSTED_ORIGINS == ["bakery.example.com", ".example.org"]
    assert settings.SESSION_COOKIE_DOMAIN == ".example.com"
    assert settings.CSRF_COOKIE_DOMAIN == ".example.com"


@pytest.mark.parametrize("name", ["SESSION_COOKIE_DOMAIN", "CSRF_COOKIE_DOMAIN"])
def test_an_empty_cookie_domain_means_unset(name):
    # A blank `.env` line yields "", which Django 3.2 would take as the domain,
    # failing every HTTPS form post on its CSRF check.
    settings = load_base({**REQUIRED, name: ""})
    assert getattr(settings, name) is None


@pytest.mark.parametrize("overlay", ["local", "test"])
def test_overlays_keep_their_own_host_settings(overlay):
    # base.py reads a developer's .env, so a host's values must stop at the overlays.
    settings = load_overlay(overlay, {**REQUIRED, **HOST})
    assert "bakery.example.com" not in settings.ALLOWED_HOSTS
    assert settings.CSRF_TRUSTED_ORIGINS == []
    assert settings.SESSION_COOKIE_DOMAIN is None
    assert settings.CSRF_COOKIE_DOMAIN is None


@pytest.mark.parametrize("value", ["true", "false"])
@pytest.mark.parametrize("overlay, expected", [("local", True), ("test", False)])
def test_overlays_fix_their_own_debug(overlay, expected, value):
    # Whatever `.env` says: runserver debugs, and the suite tests what ships.
    settings = load_overlay(overlay, {**REQUIRED, "DEBUG": value})
    assert settings.DEBUG is expected


def https_only(settings):
    return (
        settings.SECURE_SSL_REDIRECT,
        settings.SESSION_COOKIE_SECURE,
        settings.CSRF_COOKIE_SECURE,
        settings.SECURE_HSTS_SECONDS,
    )


def test_base_is_https_only_by_default():
    # Task 2.4: the secure values are base.py's, so a forgotten variable is safe.
    settings = load_base(REQUIRED)
    assert https_only(settings) == (True, True, True, 31536000)
    assert settings.SECURE_HSTS_INCLUDE_SUBDOMAINS is True
    assert settings.SECURE_HSTS_PRELOAD is True
    assert settings.X_FRAME_OPTIONS == "DENY"


def test_the_local_switch_serves_plain_http():
    settings = load_base({**REQUIRED, **PLAIN_HTTP})
    assert https_only(settings) == (False, False, False, 0)
    assert settings.X_FRAME_OPTIONS == "DENY"


@pytest.mark.parametrize("value", ["false", "0", ""])
def test_only_a_true_switch_relaxes_anything(value):
    # A blank or negative `.env` line must not open production up.
    settings = load_base({**REQUIRED, "INSECURE_LOCAL_HTTP": value})
    assert https_only(settings) == (True, True, True, 31536000)


@pytest.mark.parametrize("environment", [{}, PLAIN_HTTP], ids=["unset", "set"])
@pytest.mark.parametrize(
    "overlay, expected",
    [("local", (False, False, False, 0)), ("test", (False, True, True, 31536000))],
)
def test_overlays_fix_their_own_https_settings(overlay, expected, environment):
    # Whatever `.env` says: runserver and the test client both speak plain HTTP,
    # and the suite keeps production's cookie and HSTS values.
    settings = load_overlay(overlay, {**REQUIRED, **environment})
    assert https_only(settings) == expected


def dockerfile_instructions():
    # One string per instruction, with its `\` continuation lines joined.
    text = re.sub(r"\\\n", " ", (ROOT / "Dockerfile").read_text(encoding="utf-8"))
    lines = (line.strip() for line in text.splitlines())
    return [line for line in lines if line and not line.startswith("#")]


def test_the_image_build_sets_each_required_variable_on_its_run_line_only():
    # ADR-049: collectstatic gets placeholders inline. Through ENV or ARG they would
    # persist into the image, and a host that forgot a real value would boot on one
    # instead of failing. CI's Docker build would still pass.
    instructions = dockerfile_instructions()
    [collectstatic] = [i for i in instructions if "collectstatic" in i]
    persisted = " ".join(i for i in instructions if i.split()[0] in ("ENV", "ARG"))

    assert collectstatic.startswith("RUN ")
    assert [key for key in REQUIRED if f"{key}=" not in collectstatic] == []
    assert [key for key in REQUIRED if re.search(rf"\b{key}\b", persisted)] == []


def test_an_audit_event_is_one_bare_line_that_does_not_propagate():
    # ADR-052: the JSON object is the whole line, written once, by its own handler.
    logger = logging.getLogger("bakery.audit")
    [handler] = logger.handlers
    line = '{"action": "delete"}'
    record = logger.makeRecord(logger.name, logging.INFO, __file__, 0, line, None, None)

    assert isinstance(handler, logging.StreamHandler)
    assert handler.format(record) == line
    assert logger.propagate is False
