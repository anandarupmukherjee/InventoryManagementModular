from django.urls import path

from . import views

app_name = "data_collection_4"

urlpatterns = [
    path("register-product-codes/", views.register_product_codes, name="register-product-codes"),
]
