from django.http import HttpResponse

from . import readiness

LIVEZ_PATH = '/livez'
READYZ_PATH = '/readyz'


class HealthMiddleware:
    """First in MIDDLEWARE: answers before the Host check and the HTTPS redirect.

    /livez: always `ok`, no I/O, for anyone. /readyz: answered here for an
    internal caller (the container healthcheck sends neither the public Host
    nor X-Forwarded-Proto); anyone else goes on to the staff-only view.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == LIVEZ_PATH:
            return HttpResponse(b'ok', content_type='text/plain')
        if request.path == READYZ_PATH and readiness.is_internal(request):
            return readiness.response(request)
        return self.get_response(request)
