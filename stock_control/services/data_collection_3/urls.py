from django.urls import path
from . import views_lots

app_name = 'data_collection_3'


urlpatterns = [
    # Lots pages (HTML)
    path("products/<str:code>/lots/", views_lots.product_lots_instances, name="product-lots-instances"),
    path("products/<str:code>/lots/rollup/", views_lots.product_lots_rollup, name="product-lots-rollup"),
    # path("lots/<uuid:item_id>/acceptance/new", views_lots.create_acceptance_test, name="create-acceptance-test"),
    path("lots/<str:item_id>/acceptance/new", views_lots.create_acceptance_test, name="create-acceptance-test"),

    # Optional: add-another-lot (parallel to your existing stock intake; no overwrite)
    path("products/<str:code>/lots/new", views_lots.create_lot_instance_form, name="create-lot-instance"),
]
