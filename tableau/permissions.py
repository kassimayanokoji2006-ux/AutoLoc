from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def personnel_requis(vue):
    @login_required
    @wraps(vue)
    def verifier(request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        return vue(request, *args, **kwargs)

    return verifier
