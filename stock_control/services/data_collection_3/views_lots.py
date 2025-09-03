from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone

from services.data_storage.models import ProductItem
from services.data_storage.models import Location
from services.data_storage.models_acceptance import LotAcceptanceTest
from .lot_queries import lots_for_product, lot_rollup_for_product, _get_product_by_code
from datetime import date as _date
from decimal import Decimal, InvalidOperation


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


def _parse_date_yyyy_mm_dd(value: str):
    if not value:
        return None
    try:
        return _date.fromisoformat(value)
    except Exception:
        # Fallback to strict format
        try:
            from datetime import datetime as _dt
            return _dt.strptime(value, "%Y-%m-%d").date()
        except Exception:
            return None


def create_lot_instance_form(request, code):
    if request.method == "POST":
        lot_number = (request.POST.get("lot_number") or "").strip()
        expiry_date_raw = (request.POST.get("expiry_date") or "").strip()
        stock_units_raw = (request.POST.get("stock_units") or "0").strip()

        errors = {}

        # Validate lot number
        if not lot_number:
            errors["lot_number"] = "Lot number is required."

        # Validate expiry date (optional but if provided must be valid)
        expiry_date_val = None
        if expiry_date_raw:
            expiry_date_val = _parse_date_yyyy_mm_dd(expiry_date_raw)
            if expiry_date_val is None:
                errors["expiry_date"] = "Enter a valid date in YYYY-MM-DD (e.g., 2025-09-30)."

        # Validate stock units
        stock_units_val = Decimal("0")
        try:
            stock_units_val = Decimal(stock_units_raw)
            if stock_units_val < 0:
                errors["stock_units"] = "Stock units must be zero or positive."
        except (InvalidOperation, ValueError):
            errors["stock_units"] = "Enter a valid number for stock units."

        if errors:
            # Re-render form with errors and sticky values
            context = {
                "code": code,
                "form_errors": errors,
                "form_values": {
                    "lot_number": lot_number,
                    "expiry_date": expiry_date_raw,
                    "stock_units": stock_units_raw,
                },
            }
            return render(request, "inventory/create_lot_instance.html", context)

        # Proceed to create record
        product = _get_product_by_code(code)
        ProductItem.objects.create(
            product=product,
            lot_number=lot_number,
            expiry_date=expiry_date_val or _date.today(),
            current_stock=stock_units_val,
            location=Location.get_default(),
        )
        return redirect(reverse("data_collection_3:product-lots-instances", kwargs={"code": code}))

    return render(request, "inventory/create_lot_instance.html", {"code": code})
