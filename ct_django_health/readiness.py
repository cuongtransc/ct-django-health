"""Readiness: who may ask, what is checked, what the answer says."""

import ipaddress
import logging

from django.conf import settings
from django.http import JsonResponse
from django.utils.module_loading import import_string

logger = logging.getLogger('ct_django_health')

STATUSES = ('ok', 'warn', 'fail')


def is_internal(request) -> bool:
    """A caller on this host or its private network, not relayed by a proxy.

    The edge proxy always sets X-Forwarded-For and a client cannot strip it,
    so a request from the internet never passes, even though the proxy itself
    connects from a private address. A forged header only makes a caller
    look less internal, never more.
    """
    if 'HTTP_X_FORWARDED_FOR' in request.META:
        return False
    try:
        addr = ipaddress.ip_address(request.META.get('REMOTE_ADDR', ''))
    except ValueError:
        return False
    return addr.is_loopback or addr.is_private


def failure_message(name: str, exc: BaseException) -> str:
    """The exception class only; the detail goes to the server log.

    Driver errors hold hostnames, ports and DB users. Use this for anything
    a probe, status page or alert shows.
    """
    logger.warning('health check %s failed: %s', name, exc, exc_info=exc)
    return type(exc).__name__


def _run(path: str) -> dict:
    name = path.rsplit('.', 1)[-1]
    try:
        status = import_string(path)()
    except Exception as exc:  # noqa: BLE001  (any failure means not ready)
        failure_message(name, exc)
        status = 'fail'
    if status not in STATUSES:
        logger.warning('health check %s returned %r', name, status)
        status = 'fail'
    return {'name': name, 'status': status}


def response(request) -> JsonResponse:
    """503 when a check fails or none is configured; the body never has a message."""
    components = [_run(p) for p in getattr(settings, 'CT_HEALTH_CHECKS', [])]
    statuses = {c['status'] for c in components}
    if not components or 'fail' in statuses:
        overall = 'fail'
    elif 'warn' in statuses:
        overall = 'warn'
    else:
        overall = 'ok'
    body = {'status': overall}
    if 'verbose' in request.GET:
        body['components'] = components
    return JsonResponse(body, status=503 if overall == 'fail' else 200)
