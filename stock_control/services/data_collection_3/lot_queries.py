from django.core.exceptions import FieldError
from django.shortcuts import get_object_or_404
from django.db.models import OuterRef, Subquery, BooleanField, CharField, DateTimeField, Count, Min, Max, Sum
from services.data_storage.models import Product, ProductItem
from services.data_storage.models_acceptance import LotAcceptanceTest

def _get_product_by_code(value: str) -> Product:
    try:
        return get_object_or_404(Product, code=value)
    except FieldError:
        return get_object_or_404(Product, product_code=value)
    except Product.DoesNotExist:
        return get_object_or_404(Product, product_code=value)

def lots_for_product(product_code: str):
    product = _get_product_by_code(product_code)

    last_test_qs = (LotAcceptanceTest.objects
                    .filter(product_item=OuterRef("pk"))
                    .order_by("-created_at"))

    qs = (ProductItem.objects
          .filter(product=product)
          .annotate(
              last_tested=Subquery(last_test_qs.values("created_at")[:1], output_field=DateTimeField()),
              last_passed=Subquery(last_test_qs.values("passed")[:1], output_field=BooleanField()),
              last_ref=Subquery(last_test_qs.values("test_reference")[:1], output_field=CharField()),
              last_signed_by=Subquery(last_test_qs.values("signed_off_by")[:1], output_field=CharField()),
              last_signed_at=Subquery(last_test_qs.values("signed_off_at")[:1], output_field=DateTimeField()),
          )
          .order_by("-id"))  # ✅ newest first without received_at
    return product, qs

def lot_rollup_for_product(product_code: str):
    product = _get_product_by_code(product_code)
    agg = (ProductItem.objects
           .filter(product=product)
           .values("lot_number")
           .annotate(
               instances=Count("id"),
               total_units=Sum("current_stock"),   # ✅ use current_stock
               first_received=Min("id"),           # proxy; no received_at in schema
               last_received=Max("id"),
               earliest_expiry=Min("expiry_date"),
           )
           .order_by("lot_number"))
    return product, agg
