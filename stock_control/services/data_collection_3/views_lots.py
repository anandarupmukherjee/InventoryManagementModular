from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone

from services.data_storage.models import ProductItem
from services.data_storage.models_acceptance import LotAcceptanceTest
from .lot_queries import lots_for_product, lot_rollup_for_product, _get_product_by_code


# add this helper near the top
def _pcode(product):
    # Prefer "code"; fall back to "product_code"; finally pk
    return getattr(product, "code", None) or getattr(product, "product_code", None) or str(product.pk)


def product_lots_instances(request, code):
    product, items = lots_for_product(code)
    return render(request, "inventory/lots_instances.html", {
        "product": product,
        "product_code": _pcode(product),   # ✅ add this
        "items": items,
    })

def product_lots_rollup(request, code):
    product, rows = lot_rollup_for_product(code)
    return render(request, "inventory/lots_rollup.html", {
        "product": product,
        "product_code": _pcode(product),   # ✅ add this
        "rows": rows,
    })

# C) Create acceptance record (simple form)
# services/data_collection_3/views_lots.py

def create_acceptance_test(request, item_id):
    item = get_object_or_404(ProductItem, pk=item_id)
    pcode = _pcode(item.product)  # ✅ resolve safely

    if request.method == "POST":
        tested = request.POST.get("tested") == "on"
        passed = request.POST.get("passed") == "on"
        signed_off_by = request.POST.get("signed_off_by") or None
        signed_off_at = request.POST.get("signed_off_at") or None
        test_reference = request.POST.get("test_reference") or None

        LotAcceptanceTest.objects.create(
            product_item=item,
            tested=tested,
            passed=passed,
            signed_off_by=signed_off_by,
            signed_off_at=signed_off_at or None,
            test_reference=test_reference,
        )
        # 🔁 use the resolved pcode
        return redirect(reverse("data_collection_3:product-lots-instances", kwargs={"code": pcode}))

    # 🔁 pass it to the template so links don't guess field names
    return render(request, "inventory/acceptance_form.html", {"item": item, "product_code": pcode})


def create_lot_instance_form(request, code):
    if request.method == "POST":
        lot_number = request.POST.get("lot_number")
        expiry_date = request.POST.get("expiry_date") or None
        stock_units = request.POST.get("stock_units") or 0  # from form
        # received_at not in your model; omit it

        from services.data_storage.models import ProductItem
        product = _get_product_by_code(code)

        ProductItem.objects.create(
            product=product,
            lot_number=lot_number,
            expiry_date=expiry_date,
            current_stock=stock_units,   # ✅ map to your field
            # units_per_quantity if you want to set it too:
            # units_per_quantity=request.POST.get("units_per_quantity") or item_default
        )
        return redirect(reverse("data_collection_3:product-lots-instances", kwargs={"code": code}))

    return render(request, "inventory/create_lot_instance.html", {"code": code})
