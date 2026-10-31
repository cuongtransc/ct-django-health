"""Readiness checks: a callable returns 'ok' or 'warn', or raises.

List them in settings.CT_HEALTH_CHECKS. Only what a request cannot be
served without belongs here; data freshness and business thresholds are
alerts, not readiness.
"""

from django.conf import settings
from django.db import connection
from django.db.migrations.executor import MigrationExecutor


def database() -> str:
    with connection.cursor() as cur:
        cur.execute('SELECT 1')
        cur.fetchone()
    return 'ok'


def migrations() -> str:
    """'warn' while migrations are pending (a deploy in progress), not 'fail'."""
    executor = MigrationExecutor(connection)
    plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
    return 'warn' if plan else 'ok'


def redis() -> str:
    """PING settings.CT_HEALTH_REDIS_URL (needs the `redis` extra)."""
    from redis import from_url

    url = getattr(settings, 'CT_HEALTH_REDIS_URL', '')
    if not url:
        raise ValueError('CT_HEALTH_REDIS_URL is not set')
    client = from_url(url, socket_timeout=2, socket_connect_timeout=2)
    try:
        client.ping()
    finally:
        client.close()
    return 'ok'
