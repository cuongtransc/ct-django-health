"""The contract: /livez public and content-free; /readyz internal or staff only."""

import pytest
from django.contrib.auth import get_user_model

from ct_django_health import readiness

EDGE = {'REMOTE_ADDR': '10.20.30.40', 'HTTP_X_FORWARDED_FOR': '8.8.8.8'}


def ok():
    return 'ok'


def warn():
    return 'warn'


def boom():
    raise RuntimeError('connection to server at "10.1.2.3", user "app" failed')


@pytest.fixture
def checks(settings):
    def use(*names):
        settings.CT_HEALTH_CHECKS = [f'tests.test_probes.{n}' for n in names]

    return use


# /livez


def test_livez_is_ok_from_anywhere_without_host_or_https(client):
    # first in the chain: no ALLOWED_HOSTS check, no HTTPS redirect
    resp = client.get('/livez', HTTP_HOST='203.0.113.7:8000', **EDGE)
    assert resp.status_code == 200
    assert resp.content == b'ok'
    assert resp['Content-Type'].startswith('text/plain')


def test_livez_touches_no_check(client, checks):
    checks('boom')
    assert client.get('/livez').status_code == 200


# /readyz: who may ask


@pytest.mark.parametrize('addr', ['127.0.0.1', '::1', '172.18.0.5', '192.168.1.10'])
def test_readyz_answers_internal_callers_without_host_or_https(client, checks, addr):
    checks('ok')
    resp = client.get('/readyz', REMOTE_ADDR=addr, HTTP_HOST='127.0.0.1:8000')
    assert resp.status_code == 200
    assert resp.json() == {'status': 'ok'}


@pytest.mark.django_db
def test_readyz_through_the_edge_is_404(client, checks):
    checks('ok')
    assert client.get('/readyz', secure=True, **EDGE).status_code == 404


@pytest.mark.django_db
def test_readyz_from_a_public_peer_is_404(client, checks):
    checks('ok')
    resp = client.get('/readyz', secure=True, REMOTE_ADDR='8.8.8.8')
    assert resp.status_code == 404


@pytest.mark.django_db
def test_forged_proxy_header_does_not_make_a_caller_internal(client, checks):
    checks('ok')
    resp = client.get(
        '/readyz', secure=True, REMOTE_ADDR='8.8.8.8', HTTP_X_FORWARDED_FOR='127.0.0.1'
    )
    assert resp.status_code == 404


@pytest.mark.django_db
def test_signed_in_non_staff_through_the_edge_is_404(client, checks):
    checks('ok')
    client.force_login(get_user_model().objects.create_user('m', password='x'))
    assert client.get('/readyz', secure=True, **EDGE).status_code == 404


@pytest.mark.django_db
def test_staff_through_the_edge_gets_readiness(client, checks):
    checks('ok')
    staff = get_user_model().objects.create_user('ops', password='x', is_staff=True)
    client.force_login(staff)
    resp = client.get('/readyz', secure=True, **EDGE)
    assert resp.status_code == 200
    assert resp.json() == {'status': 'ok'}


# /readyz: what it says


def test_failed_check_is_503(client, checks):
    checks('ok', 'boom')
    resp = client.get('/readyz')
    assert resp.status_code == 503
    assert resp.json() == {'status': 'fail'}


def test_warn_stays_200(client, checks):
    checks('ok', 'warn')
    resp = client.get('/readyz')
    assert resp.status_code == 200
    assert resp.json() == {'status': 'warn'}


def test_verbose_lists_components_without_messages(client, checks):
    checks('ok', 'warn', 'boom')
    resp = client.get('/readyz?verbose')
    assert resp.status_code == 503
    assert resp.json()['components'] == [
        {'name': 'ok', 'status': 'ok'},
        {'name': 'warn', 'status': 'warn'},
        {'name': 'boom', 'status': 'fail'},
    ]
    assert b'10.1.2.3' not in resp.content


def test_no_checks_configured_is_not_ready(client, settings):
    settings.CT_HEALTH_CHECKS = []
    assert client.get('/readyz').status_code == 503


def test_a_check_returning_garbage_fails(client, checks, settings):
    settings.CT_HEALTH_CHECKS = ['tests.test_probes.EDGE']  # not callable
    assert client.get('/readyz').status_code == 503


def test_failure_detail_goes_to_the_log_only(caplog):
    with caplog.at_level('WARNING', logger='ct_django_health'):
        message = readiness.failure_message('db', RuntimeError('host 10.1.2.3'))
    assert message == 'RuntimeError'
    assert '10.1.2.3' in caplog.text


def test_other_paths_pass_through(client):
    # the middleware owns two paths only
    assert client.get('/livez/', secure=True).status_code == 404
    assert client.get('/elsewhere', secure=True).status_code == 404
