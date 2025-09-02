from stock_control.module_loader import load_enabled_modules

def module_flags(request):
    enabled = load_enabled_modules()
    return {
        "flags": {module: True for module in enabled}
    }
