from django.urls import path

from .views import track_stock_registries

app_name = 'reporting_stock_input'

urlpatterns = [
    path('', track_stock_registries, name='track_stock_registries'),
]
