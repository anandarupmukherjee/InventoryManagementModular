import json
from django.conf import settings
from django.http import HttpResponseNotFound
import os

CONFIG_PATH = os.path.join(settings.BASE_DIR, "config", "module_config.json")

with open(CONFIG_PATH, "r") as f:
    MODULE_CONFIG = json.load(f)

class ModuleToggleMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.module_config = MODULE_CONFIG
        return self.get_response(request)