from django.conf import settings
from django.core.checks import Error, Warning, register
from django.urls import Resolver404, resolve
from django.utils.module_loading import import_string

MIDDLEWARE = 'ct_django_health.middleware.HealthMiddleware'


@register('ct_health')
def check_install(app_configs, **kwargs):
    errors = []
    middleware = list(getattr(settings, 'MIDDLEWARE', []))
    if not middleware or middleware[0] != MIDDLEWARE:
        errors.append(
            Error(
                f'{MIDDLEWARE} must be first in MIDDLEWARE.',
                hint='Later, the Host check and the HTTPS redirect answer the '
                'container healthcheck before the probe does.',
                id='ct_health.E001',
            )
        )

    paths = getattr(settings, 'CT_HEALTH_CHECKS', None)
    if not paths:
        errors.append(
            Error(
                'CT_HEALTH_CHECKS must list the readiness checks.',
                hint="e.g. ['ct_django_health.checks.database', "
                "'ct_django_health.checks.migrations']",
                id='ct_health.E002',
            )
        )
    else:
        for path in paths:
            try:
                ok = callable(import_string(path))
            except ImportError:
                ok = False
            if not ok:
                errors.append(
                    Error(
                        f'CT_HEALTH_CHECKS: {path!r} is not a callable.',
                        id='ct_health.E002',
                    )
                )

    try:
        match = resolve('/readyz')
        routed = match.func.__module__ == 'ct_django_health.views'
    except Resolver404:
        routed = False
    if not routed:
        errors.append(
            Warning(
                '/readyz is not routed to ct_django_health.views.readyz: staff '
                'cannot read readiness from outside.',
                hint="path('', include('ct_django_health.urls')) in ROOT_URLCONF",
                id='ct_health.W001',
            )
        )
    return errors
