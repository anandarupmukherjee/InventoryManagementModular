from django.urls import path

from .views import register_stock

register_stock_urlpatterns = [
    path("register-stock/", register_stock, name="register-stock"),
]

