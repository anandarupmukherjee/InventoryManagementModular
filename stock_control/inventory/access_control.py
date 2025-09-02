from django.http import HttpResponseForbidden
from functools import wraps

def has_access(user, allowed_groups=None):
    if user.is_authenticated:
        if getattr(user, 'is_admin', False):
            return True
        if allowed_groups:
            return user.groups.filter(name__in=allowed_groups).exists()
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
