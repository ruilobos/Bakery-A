import importlib.util
import os
from pathlib import Path
from unittest import mock

import environ
import pytest
from django.core.exceptions import ImproperlyConfigured

BASE = Path(__file__).resolve().parent / "settings" / "base.py"
SECRETS = {
    "SECRET_KEY": "test-only-key",
    "DATABASE_URL": "postgres://user:pass@db.invalid:5432/name",
}


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


@pytest.mark.parametrize("missing", sorted(SECRETS))
def test_base_fails_loudly_without_a_secret(missing):
    # Task 2.1 deleted their fallbacks: production must not boot on a default (ADR-028).
    environment = {k: v for k, v in SECRETS.items() if k != missing}
    with pytest.raises(ImproperlyConfigured, match=missing):
        load_base(environment)


def test_base_reads_both_secrets_from_the_environment():
    settings = load_base(SECRETS)
    assert settings.SECRET_KEY == "test-only-key"
    assert settings.DATABASES["default"]["HOST"] == "db.invalid"
    assert settings.DATABASES["default"]["NAME"] == "name"
