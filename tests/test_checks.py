"""The built-in readiness checks, against a real (sqlite) database."""

import pytest
import redis
from django.core.checks import run_checks

from ct_django_health import checks


@pytest.mark.django_db
def test_database_ok():
    assert checks.database() == 'ok'


@pytest.mark.django_db
def test_migrations_applied_is_ok():
    assert checks.migrations() == 'ok'


def test_redis_without_url_fails(settings):
    settings.CT_HEALTH_REDIS_URL = ''
    with pytest.raises(ValueError):
        checks.redis()


def test_redis_unreachable_raises(settings):
    settings.CT_HEALTH_REDIS_URL = 'redis://127.0.0.1:1/0'
    with pytest.raises(redis.ConnectionError):
        checks.redis()


# Django system checks: a wrong install fails `manage.py check`


def _ids(**_):
    return {e.id for e in run_checks(tags=['ct_health'])}


def test_installed_as_documented_has_no_errors():
    assert _ids() == set()


def test_middleware_not_first_is_an_error(settings):
    settings.MIDDLEWARE = [*settings.MIDDLEWARE[1:], settings.MIDDLEWARE[0]]
    assert 'ct_health.E001' in _ids()


def test_missing_checks_setting_is_an_error(settings):
    del settings.CT_HEALTH_CHECKS
    assert 'ct_health.E002' in _ids()


def test_unimportable_check_is_an_error(settings):
    settings.CT_HEALTH_CHECKS = ['nope.missing']
    assert 'ct_health.E002' in _ids()


def test_readyz_view_not_routed_is_a_warning(settings):
    settings.ROOT_URLCONF = 'tests.urls_empty'
    assert 'ct_health.W001' in _ids()
