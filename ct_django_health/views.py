from django.http import Http404
from django.views.decorators.http import require_GET

from . import readiness


@require_GET
def readyz(request):
    """Readiness for a signed-in staff member; 404 for everyone else.

    Internal callers never get here: HealthMiddleware answers them first.
    """
    user = getattr(request, 'user', None)
    if not (user is not None and user.is_staff):
        raise Http404
    return readiness.response(request)
