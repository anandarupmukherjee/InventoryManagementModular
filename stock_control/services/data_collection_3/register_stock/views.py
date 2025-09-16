from __future__ import annotations

from datetime import datetime, date
from decimal import Decimal
from typing import Any, Dict, Optional

from django.contrib.auth.decorators import login_required
from django.db.models import F
from django.shortcuts import redirect, render
from django.utils import timezone

from services.data_collection.data_collection import parse_barcode_data
from services.data_storage.models import Product, ProductItem, StockRegistrationLog, Location

SESSION_HISTORY_KEY = "register_stock_history"
SESSION_FEEDBACK_KEY = "register_stock_feedback"
SESSION_FORM_STATE_KEY = "register_stock_form_state"
HISTORY_LIMIT = 10


def _normalize_product_code(raw: str) -> str:
    code = (raw or "").strip()
    if not code:
        return ""
    return code.lstrip("0") or "0" if code.isdigit() else code


def _parse_expiry_date(raw: Optional[str]) -> Optional[date]:
    if not raw:
        return None
    value = raw.strip()
    if not value:
        return None

    for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%y%m%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def _parse_delivery_datetime(raw: Optional[str]) -> Optional[datetime]:
    if not raw:
        return None
    value = raw.strip()
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if timezone.is_naive(parsed):
        return timezone.make_aware(parsed, timezone.get_current_timezone())
    return timezone.localtime(parsed)


def _format_datetime_for_display(value: datetime) -> str:
    return timezone.localtime(value).strftime("%Y-%m-%d %H:%M")


def _format_datetime_for_input(value: datetime) -> str:
    return timezone.localtime(value).strftime("%Y-%m-%dT%H:%M")


def _store_form_state(request, use_now: bool, delivery_dt: Optional[datetime], raw_value: str = "", location_id: str = "") -> None:
    if use_now:
        state = {"use_now": True, "delivery_datetime": "", "location_id": location_id or ""}
    else:
        formatted = ""
        if delivery_dt:
            formatted = _format_datetime_for_input(delivery_dt)
        elif raw_value:
            formatted = raw_value
        state = {"use_now": False, "delivery_datetime": formatted, "location_id": location_id or ""}
    request.session[SESSION_FORM_STATE_KEY] = state
    request.session.modified = True


def _prepare_history_entry(item: ProductItem, barcode: str, delivery_dt: Optional[datetime], location=None) -> Dict[str, Any]:
    scan_time = timezone.localtime()
    product = item.product
    return {
        "timestamp": scan_time.strftime("%Y-%m-%d %H:%M:%S"),
        "barcode": barcode,
        "product_code": product.product_code,
        "product_name": product.name,
        "lot_number": item.lot_number,
        "expiry_date": item.expiry_date.isoformat(),
        "current_stock": str(item.current_stock),
        "delivery_datetime": _format_datetime_for_display(delivery_dt) if delivery_dt else "",
        "location_name": getattr(location, "name", None) or getattr(item.location, "name", ""),
    }


def _record_feedback(request, level: str, message: str, details: Optional[Dict[str, Any]] = None) -> None:
    request.session[SESSION_FEEDBACK_KEY] = {
        "level": level,
        "message": message,
        "details": details or {},
    }
    request.session.modified = True


def _append_history(request, entry: Dict[str, Any]) -> None:
    history = request.session.get(SESSION_HISTORY_KEY, [])
    history.insert(0, entry)
    request.session[SESSION_HISTORY_KEY] = history[:HISTORY_LIMIT]
    request.session.modified = True


@login_required
def register_stock(request):
    if request.method == "POST":
        barcode = (request.POST.get("barcode") or "").strip()
        use_now_selected = bool(request.POST.get("use_now"))
        delivery_raw = request.POST.get("delivery_datetime") or ""
        delivery_dt = timezone.localtime() if use_now_selected else _parse_delivery_datetime(delivery_raw)

        location_id = (request.POST.get("location_id") or "").strip()
        selected_location = None
        if location_id:
            try:
                selected_location = Location.objects.get(pk=int(location_id))
            except (Location.DoesNotExist, TypeError, ValueError):
                selected_location = None
                location_id = ""

        _store_form_state(request, use_now_selected, delivery_dt, delivery_raw, location_id)

        if not barcode:
            _record_feedback(request, "error", "Please scan a barcode before submitting.")
            return redirect("data_collection_3:register-stock")

        if not use_now_selected and delivery_dt is None:
            _record_feedback(request, "error", "Enter a valid delivery date or select \"Use current date & time\".")
            return redirect("data_collection_3:register-stock")

        if delivery_dt is None:
            delivery_dt = timezone.localtime()

        parsed = parse_barcode_data(barcode)
        product = None
        lot_number = None
        expiry_date = None

        if parsed:
            product_code = parsed.get("product_code") or ""
            lot_number = parsed.get("lot_number") or None
            expiry_date = _parse_expiry_date(parsed.get("expiry_date"))

            normalized = _normalize_product_code(product_code)
            if normalized:
                product = Product.objects.filter(product_code__iexact=normalized).first()
            if not product and product_code:
                product = Product.objects.filter(product_code__iexact=product_code).first()
        else:
            normalized = _normalize_product_code(barcode)
            if normalized:
                product = Product.objects.filter(product_code__iexact=normalized).first()
            if not product:
                product = Product.objects.filter(product_code__iexact=barcode).first()

        if not product:
            _record_feedback(request, "error", "No product found for the scanned barcode.")
            return redirect("data_collection_3:register-stock")

        item_qs = ProductItem.objects.filter(product=product)
        if selected_location:
            item_qs = item_qs.filter(location=selected_location)
        if lot_number:
            item_qs = item_qs.filter(lot_number__iexact=lot_number)
        if expiry_date:
            item_qs = item_qs.filter(expiry_date=expiry_date)

        item = item_qs.order_by("expiry_date").first()
        if not item:
            item = product.items.order_by("expiry_date").first()
            if item and not selected_location:
                selected_location = getattr(item, 'location', None)
        elif not selected_location:
            selected_location = getattr(item, 'location', None)

        if not item:
            _record_feedback(request, "error", "The product has no lot available to update.")
            return redirect("data_collection_3:register-stock")

        ProductItem.objects.filter(pk=item.pk).update(current_stock=F("current_stock") + Decimal("1"))
        item.refresh_from_db(fields=["current_stock"])

        log_location = selected_location or getattr(item, 'location', None)
        StockRegistrationLog.objects.create(
            product_item=item,
            quantity=Decimal('1.00'),
            user=request.user if request.user.is_authenticated else None,
            barcode=barcode,
            delivery_datetime=delivery_dt,
            location=log_location,
        )

        location_id = str(log_location.id) if log_location else ""
        _store_form_state(request, use_now_selected, delivery_dt, delivery_raw, location_id)

        entry = _prepare_history_entry(item, barcode, delivery_dt, log_location)
        _append_history(request, entry)
        _record_feedback(
            request,
            "success",
            f"Registered 1 unit for {item.product.name}.",
            details=entry,
        )
        return redirect("data_collection_3:register-stock")

    feedback = request.session.pop(SESSION_FEEDBACK_KEY, None)
    history = request.session.get(SESSION_HISTORY_KEY, [])
    form_state = request.session.get(SESSION_FORM_STATE_KEY, {}) or {}
    initial_use_now = form_state.get("use_now")
    if initial_use_now is None:
        initial_use_now = True
    if initial_use_now:
        default_input_value = form_state.get("delivery_datetime") or _format_datetime_for_input(timezone.localtime())
    else:
        default_input_value = form_state.get("delivery_datetime") or ""

    initial_location_id = form_state.get("location_id") or ""
    locations = Location.objects.all().order_by('name')

    return render(
        request,
        "inventory/register_stock.html",
        {
            "feedback": feedback,
            "recent_scans": history,
            "initial_delivery": default_input_value,
            "initial_use_now": initial_use_now,
            "locations": locations,
            "initial_location_id": initial_location_id,
        },
    )

