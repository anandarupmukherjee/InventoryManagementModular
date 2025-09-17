from stock_control.module_loader import load_enabled_modules

from .utils import get_active_user_count

def module_flags(request):
    enabled = load_enabled_modules()
    return {
        "flags": {module: True for module in enabled}
    }


def active_user_stats(request):
    return {
        "active_user_count": get_active_user_count(),
    }
