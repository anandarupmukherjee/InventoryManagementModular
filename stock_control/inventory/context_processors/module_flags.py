from django.conf import settings
import json
import os

def module_flags(request):
    config_path = os.path.join(settings.BASE_DIR, "config", "module_config.json")
    try:
        with open(config_path, "r") as f:
            return {"module_flags": json.load(f)}
    except Exception:
        return {"module_flags": {}}