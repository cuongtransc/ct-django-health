# ct-django-health

Kubernetes-style health probes for Django apps behind a reverse proxy, one
contract for every app:

| Path | Who may call it | Checks | Body | On failure |
|---|---|---|---|---|
| `/livez` | anyone (external uptime checks) | nothing: the process answers | `ok` | — |
| `/readyz` | internal callers, or a signed-in staff member; everyone else 404 | `CT_HEALTH_CHECKS` | `{"status": "ok\|warn\|fail"}`; `?verbose` adds `components: [{name, status}]` | 503 |

- **Internal** = no `X-Forwarded-For` and a loopback or private peer: the container
  healthcheck, the host, the docker network, the LAN. The edge proxy always sets
  `X-Forwarded-For`, so a request from the internet is never internal. Also refuse
  `/readyz` at the proxy itself (e.g. a 403 rule), so a proxy misconfiguration cannot
  expose it.
- **No message ever leaves**: a failed check shows `fail`; the exception goes to the
  `ct_django_health` logger. Use `readiness.failure_message(name, exc)` in your own
  status pages and alerts too: driver errors hold hostnames, ports and DB users.
- **Readiness is not alerting.** Only what a request cannot be served without belongs
  in `CT_HEALTH_CHECKS` (database, migrations, redis). Crawl freshness, costs, queues
  are alerts on your own status page.

## Install

Pin by commit SHA:

```toml
dependencies = ["ct-django-health[redis] @ git+https://github.com/cuongtransc/ct-django-health@<sha>"]
```

```python
INSTALLED_APPS += ['ct_django_health']
MIDDLEWARE = ['ct_django_health.middleware.HealthMiddleware', *MIDDLEWARE]  # first
CT_HEALTH_CHECKS = [
    'ct_django_health.checks.database',
    'ct_django_health.checks.migrations',  # 'warn' while pending
    'ct_django_health.checks.redis',  # needs CT_HEALTH_REDIS_URL
]
CT_HEALTH_REDIS_URL = REDIS_URL

# urls.py
urlpatterns += [path('', include('ct_django_health.urls'))]  # staff /readyz
```

A check is any callable returning `'ok'` or `'warn'`, or raising. `manage.py check`
fails when the middleware is not first (`ct_health.E001`) or a check does not import
(`ct_health.E002`), and warns when `/readyz` is not routed (`ct_health.W001`).

Docker healthcheck: `python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/readyz', timeout=3)"`.

## Development

`mise run ci` (ruff, pytest, gitleaks).
