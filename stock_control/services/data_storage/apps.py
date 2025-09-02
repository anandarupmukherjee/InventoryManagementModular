from django.apps import AppConfig

class DataStorageConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'services.data_storage'
    label = 'data_storage'

    # def ready(self):
    #     # Ensure acceptance models are registered at startup (so makemigrations sees them)
    #     from . import models_acceptance
