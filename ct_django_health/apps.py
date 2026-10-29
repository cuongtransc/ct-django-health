from django.apps import AppConfig


class CtDjangoHealthConfig(AppConfig):
    name = 'ct_django_health'
    verbose_name = 'Health probes'

    def ready(self):
        from . import system_checks  # noqa: F401  (registers the checks)
