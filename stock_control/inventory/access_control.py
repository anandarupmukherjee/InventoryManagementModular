from django.http import HttpResponseForbidden
from functools import wraps

from .utils import is_admin_user
from .constants import LEGACY_ROLE_GROUPS, GROUP_NAME_TO_ROLE_KEY


def has_access(user, allowed_groups=None):
    if user.is_authenticated:
        if is_admin_user(user):
            return True
        if allowed_groups:
            if user.groups.filter(name__in=allowed_groups).exists():
                return True
            legacy_targets = []
            for group in allowed_groups:
                role_key = GROUP_NAME_TO_ROLE_KEY.get(group)
                if not role_key:
                    continue
                legacy_targets.extend([
                    legacy_name
                    for legacy_name, legacy_role in LEGACY_ROLE_GROUPS.items()
                    if legacy_role == role_key
                ])
            if legacy_targets and user.groups.filter(name__in=legacy_targets).exists():
                return True
    return False

def group_required(allowed_groups):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if has_access(request.user, allowed_groups):
                return view_func(request, *args, **kwargs)
            return HttpResponseForbidden("You do not have permission to access this page.")
        return _wrapped_view
    return decorator
