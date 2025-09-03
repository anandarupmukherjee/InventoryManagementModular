# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import F
from .forms import WithdrawalForm, ProductForm, PurchaseOrderForm, AdminUserCreationForm, AdminUserEditForm, ProductItemForm, PurchaseOrderCompletionForm
from services.data_storage.models import Product, Withdrawal, PurchaseOrder, ProductItem, PurchaseOrderCompletionLog, Location
from services.data_storage.models_acceptance import LotAcceptanceTest
from django.contrib.auth.forms import UserCreationForm
from io import BytesIO
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponse
import datetime
from datetime import timedelta
from django.utils import timezone
from django.utils.timezone import now
import openpyxl
from openpyxl.styles import Font
from django.db.models import Sum 
import json
import re
import csv
import io
from django.db.models import Q
from django.contrib import messages
from django.apps import apps
from django.utils.dateparse import parse_date
import numpy as np  # ✅ Import NumPy for calculations
import pandas as pd  # ✅ Import Pandas for time series processing
from statsmodels.tsa.holtwinters import ExponentialSmoothing  # ✅ Exponential Smoothing for Forecasting
from django.views.decorators.http import require_GET
from django.utils.timezone import make_aware
from django.db.models import Sum, Count
from django.db.models import Prefetch
from inventory.access_control import group_required





# ✅ Function to check if the user is an admin
def is_admin(user):
    return user.is_authenticated and user.is_staff

@group_required(["Inventory Manager"])
def manage_inventory(request):
    return render(request, "manage_inventory.html")

@group_required(["Inventory Manager", "Leica Staff"])
def view_dashboard(request):
    return render(request, "dashboard.html")

# ✅ Admin-only view to list all users
@login_required
@user_passes_test(is_admin, login_url='inventory:dashboard')
def manage_users(request):
    users = User.objects.all()
    return render(request, 'registration/manage_users.html', {'users': users})

# ✅ Admin-only view to register a new user
@login_required
@user_passes_test(is_admin, login_url='inventory:dashboard')
def register_user(request):
    if request.method == 'POST':
        form = AdminUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('inventory:manage_users')
    else:
        form = AdminUserCreationForm()
    return render(request, 'registration/register_user.html', {'form': form})

# ✅ Admin-only view to edit a user
@login_required
@user_passes_test(is_admin, login_url='inventory:dashboard')
def edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = AdminUserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('inventory:manage_users')
    else:
        form = AdminUserEditForm(instance=user)
    return render(request, 'registration/edit_user.html', {'form': form, 'user_obj': user})

# ✅ Admin-only view to delete a user
@login_required
@user_passes_test(is_admin, login_url='inventory:dashboard')
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == "POST":
        user.delete()
        return redirect('inventory:manage_users')
    return render(request, 'registration/delete_user.html', {'user_obj': user})


##################### MODULARITY EXPERIMENTAL ##########################

from services.analysis.analysis import inventory_analysis_forecasting as _inventory_analysis_forecasting
from services.reporting.reporting import download_report as _download_report
from services.data_collection.data_collection import (
    parse_barcode as _parse_barcode,
    get_product_by_barcode as _get_product_by_barcode,
    get_product_by_id as _get_product_by_id
)
from services.data_collection_1.stock_admin import stock_admin as _stock_admin, delete_lot as _delete_lot
from services.analysis.analysis import get_dashboard_data
# from services.data_collection.data_collection import parse_barcode_data
from services.data_collection_2.create_withdrawal import create_withdrawal as _create_withdrawal

from services.data_storage.models import Product, ProductItem, PurchaseOrder
from django.contrib.auth.models import User
from collections import Counter, defaultdict

@login_required
@group_required(["Inventory Manager", "Leica Staff"])
def inventory_dashboard(request):
    context = get_dashboard_data()

    # 1. Low stock alerts
    low_stock_alerts = [
        p for p in Product.objects.prefetch_related("items").all()
        if sum(item.current_stock for item in p.items.all()) < p.threshold
    ]
    has_low_stock_alerts = len(low_stock_alerts) > 0

    # 2. Expired lots
    has_expired_lot_alerts = ProductItem.objects.filter(expiry_date__lte=now().date()).exists()

    # 3. Delayed deliveries
    has_delayed_delivery_alerts = PurchaseOrder.objects.filter(
        expected_delivery__lt=now()
    ).exclude(status="Delivered").exists()

    # 4. Products with missing threshold
    products_with_zero_threshold = Product.objects.filter(threshold=0)
    has_missing_thresholds = products_with_zero_threshold.exists()

    # 5. Duplicate product names
    # Normalize names: strip spaces and convert to lowercase
    raw_names = Product.objects.values_list("name", flat=True)
    normalized_name_map = defaultdict(list)

    for name in raw_names:
        normalized = name.strip().lower()
        normalized_name_map[normalized].append(name)

    # Only consider real duplicates (two or more different entries mapping to same normalized form)
    duplicate_product_names = [
        names[0] for names in normalized_name_map.values() if len(set(names)) > 1
    ]

    # 6. User count
    total_users = User.objects.count()

    context.update({
        "has_low_stock_alerts": has_low_stock_alerts,
        "has_expired_lot_alerts": has_expired_lot_alerts,
        "has_delayed_delivery_alerts": has_delayed_delivery_alerts,
        "has_missing_thresholds": has_missing_thresholds,
        "duplicate_product_names": duplicate_product_names,
        "total_users": total_users,
    })

    return render(request, "inventory/dashboard.html", context)



@login_required
@user_passes_test(is_admin, login_url='inventory:dashboard')
def inventory_analysis_forecasting(request):
    return _inventory_analysis_forecasting(request)


@login_required
@user_passes_test(is_admin, login_url='inventory:dashboard')
def download_report(request):
    return _download_report(request)


@login_required
def parse_barcode(request):
    return _parse_barcode(request)

@login_required
def get_product_by_barcode(request):
    return _get_product_by_barcode(request)

@login_required
def get_product_by_id(request):
    return _get_product_by_id(request)


@login_required
@user_passes_test(is_admin, login_url='inventory:dashboard')
def stock_admin(request, product_id=None):
    response = _stock_admin(request, product_id=product_id)
    if isinstance(response, dict) and response.get("redirect"):
        return redirect('inventory:stock_admin')
    return response

@login_required
@user_passes_test(is_admin, login_url='inventory:dashboard')
def delete_lot(request, item_id):
    response = _delete_lot(request, item_id)
    if isinstance(response, dict) and response.get("redirect"):
        return redirect('inventory:stock_admin')
    return response


@login_required
def create_withdrawal(request):
    return _create_withdrawal(request)

####################################





@login_required
@group_required(["Inventory Manager", "Leica Staff"])
def product_list(request):
    # Prefetch items and their acceptance tests for efficient per-product aggregation
    products = (
        Product.objects
        .prefetch_related(
            Prefetch(
                "items",
                queryset=ProductItem.objects.prefetch_related(
                    Prefetch("acceptance_tests", queryset=LotAcceptanceTest.objects.order_by("-created_at"))
                )
            )
        )
        .all()
    )
    for product in products:
        product.full_items = product.get_full_items_in_stock()
        product.remaining_parts = product.get_remaining_parts()
        product.total_stock = sum(item.current_stock for item in product.items.all())

        items = list(product.items.all())
        product.lot_instances = len(items)

        # Earliest expiry across all lots for this product (None if no items)
        product.earliest_expiry = None
        if items:
            expiries = [i.expiry_date for i in items if getattr(i, "expiry_date", None)]
            product.earliest_expiry = min(expiries) if expiries else None

        # Count latest acceptance status per lot instance
        passed = failed = untested = 0
        for item in items:
            tests = list(getattr(item, "acceptance_tests", []).all()) if hasattr(item, "acceptance_tests") else []
            last_test = tests[0] if tests else None
            if not last_test:
                untested += 1
            else:
                if getattr(last_test, "tested", False):
                    if getattr(last_test, "passed", False):
                        passed += 1
                    else:
                        failed += 1
                else:
                    untested += 1

        product.lot_passed = passed
        product.lot_failed = failed
        product.lot_untested = untested

    return render(request, 'inventory/product_list.html', {
        'products': products
    })


# ✅ Updated view function
@login_required
@user_passes_test(is_admin, login_url='inventory:dashboard')
def record_purchase_order(request):
    initial = {}
    if request.method == "GET":
        product_code = request.GET.get('product_code')
        product_name = request.GET.get('product_name')
        if product_code:
            initial['product_code'] = product_code
        if product_name:
            initial['product_name'] = product_name

    if request.method == "POST":
        form = PurchaseOrderForm(request.POST)
        if form.is_valid():
            po = form.save(commit=False)
            po.ordered_by = request.user

            # 🧠 Logic to auto-select ProductItem from product_code if not provided
            if not po.product_item and form.cleaned_data.get("product_code"):
                product_code = form.cleaned_data["product_code"]
                product = Product.objects.filter(product_code=product_code).first()
                if product:
                    product_item = ProductItem.objects.filter(product=product).order_by('expiry_date').first()
                    if product_item:
                        po.product_item = product_item            
            print(po)
            po.save()

            if po.status == 'Delivered' and po.product_item:
                po.product_item.current_stock = F('current_stock') + po.quantity_ordered
                po.product_item.save()
                print(po)

            return redirect('inventory:record_purchase_order')
    else:
        form = PurchaseOrderForm(initial=initial)

    # 🧮 Recalculate low stock again, excluding products with an outstanding PO
    products = Product.objects.all()
    low_stock = []
    for p in products:
        total_stock = sum(item.current_stock for item in p.items.all())
        if total_stock < p.threshold:
            # Exclude if an order is already placed and pending (status Ordered/Delayed)
            has_pending_po = PurchaseOrder.objects.filter(
                product_code=p.product_code,
                status__in=["Ordered", "Delayed"],
            ).exists()
            if not has_pending_po:
                low_stock.append(p)

    return render(request, 'inventory/record_purchase_order.html', {
        'form': form,
        'low_stock': low_stock,
    })




@login_required
@user_passes_test(is_admin, login_url='inventory:dashboard')
def track_withdrawals(request):
    location_id = request.GET.get('location_id') or ''
    withdrawals = Withdrawal.objects.select_related('product_item', 'user', 'product_item__location').order_by('-timestamp')
    if location_id:
        try:
            withdrawals = withdrawals.filter(product_item__location_id=int(location_id))
        except (TypeError, ValueError):
            pass
    for w in withdrawals:
        w.full_items = w.get_full_items_withdrawn()
        w.partial_items = w.get_partial_items_withdrawn()
    locations = Location.objects.all().order_by('name')
    return render(request, 'inventory/track_withdrawals.html', {
        'withdrawals': withdrawals,
        'locations': locations,
        'selected_location_id': str(location_id)
    })



@login_required
@group_required(["Inventory Manager", "Leica Staff"])
def track_purchase_orders(request):
    # Load POs, excluding delivered orders older than 7 days
    seven_days_ago = now() - timedelta(days=7)
    orders = (
        PurchaseOrder.objects
        .select_related('product_item', 'ordered_by')
        .filter(
            Q(status__in=["Ordered", "Delayed"]) |
            Q(status="Delivered", delivered_at__gte=seven_days_ago)
        )
        .order_by('-order_date')
    )
    for order in orders:
        if order.expected_delivery < now() and order.status == "Ordered":
            order.status = "Delayed"
            order.save()

    # Initialise form (prefilled by JS from table selection)
    initial = {}

    # Handle PO form submission
    if request.method == "POST":
        form = PurchaseOrderCompletionForm(request.POST)
        if form.is_valid():
            product_code = form.cleaned_data["product_code"]
            product_name = form.cleaned_data["product_name"]
            lot_number = form.cleaned_data.get("lot_number")
            expiry_date = form.cleaned_data.get("expiry_date")
            qty = form.cleaned_data.get("quantity_ordered") or 0
            lot_mode = request.POST.get("lot_mode", "single")

            # Validate product
            product = Product.objects.filter(product_code=product_code).first()
            if not product:
                form.add_error(None, "Product not found.")
                return render(request, "inventory/track_purchase_orders.html", {
                    "purchase_orders": orders,
                    "completion_form": form
                })

            total_received = 0
            touched_items = []
            if lot_mode == "multiple":
                lot_nums = request.POST.getlist("multi_lot_number[]")
                exp_dates = request.POST.getlist("multi_expiry_date[]")
                qtys = request.POST.getlist("multi_quantity[]")
                for ln, ed, q in zip(lot_nums, exp_dates, qtys):
                    if not ln or not q:
                        continue
                    try:
                        q_int = int(q)
                    except ValueError:
                        q_int = 0
                    ed_obj = None
                    if ed:
                        try:
                            ed_obj = datetime.datetime.strptime(ed, "%Y-%m-%d").date()
                        except ValueError:
                            ed_obj = None
                    item, _ = ProductItem.objects.get_or_create(
                        product=product,
                        lot_number=ln,
                        expiry_date=ed_obj,
                        defaults={"current_stock": 0}
                    )
                    item.current_stock = F("current_stock") + q_int
                    item.save()
                    item.refresh_from_db()
                    touched_items.append(item)
                    total_received += q_int
                # Server-side validation: totals must equal ordered qty (if provided)
                try:
                    ordered_qty = int(request.POST.get("quantity_ordered") or 0)
                except ValueError:
                    ordered_qty = 0
                if ordered_qty and total_received != ordered_qty:
                    error_msg = f"Total across lots ({total_received}) does not match ordered quantity ({ordered_qty})."
                    if request.headers.get("x-requested-with") == "XMLHttpRequest":
                        return JsonResponse({"error": error_msg}, status=400)
                    form.add_error(None, error_msg)
                    return render(request, "inventory/track_purchase_orders.html", {
                        "purchase_orders": orders,
                        "completion_form": form
                    })
            else:
                item, _ = ProductItem.objects.get_or_create(
                    product=product,
                    lot_number=lot_number or "",
                    expiry_date=expiry_date,
                    defaults={"current_stock": 0}
                )
                item.current_stock = F("current_stock") + int(qty or 0)
                item.save()
                item.refresh_from_db()
                touched_items.append(item)
                total_received = int(qty or 0)

            # Update matching PurchaseOrder (by product) to Delivered
            po = PurchaseOrder.objects.filter(
                Q(product_code=product_code),
                Q(status="Ordered") | Q(status="Delayed")
            ).order_by("-order_date").first()

            if po:
                po.status = "Delivered"
                po.delivered_at = timezone.now()
                po.save()
                first_item = touched_items[0]
                PurchaseOrderCompletionLog.objects.create(
                    purchase_order=po,
                    product_code=po.product_code,
                    product_name=po.product_name,
                    lot_number=first_item.lot_number,
                    expiry_date=first_item.expiry_date,
                    quantity_ordered=total_received or po.quantity_ordered,
                    order_date=po.order_date,
                    ordered_by=po.ordered_by,
                    completed_by=request.user,
                    remarks=("Multiple lots received" if lot_mode == "multiple" else "Completed via form")
                )

            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({
                    "success": True,
                    "product_code": product_code,
                    "status": "Delivered"
                })
            return redirect("inventory:track_purchase_orders")


        else:
            return render(request, "inventory/track_purchase_orders.html", {
                "purchase_orders": orders,
                "completion_form": form
            })

    # Initial form for GET request
    form = PurchaseOrderCompletionForm(initial=initial)
    return render(request, "inventory/track_purchase_orders.html", {
        "purchase_orders": orders,
        "completion_form": form
    })


@login_required
@user_passes_test(is_admin, login_url='inventory:dashboard')
def mark_order_delivered(request, order_id):
    purchase_order = get_object_or_404(PurchaseOrder, id=order_id)
    if purchase_order.status != 'Delivered':
        if purchase_order.product_item:
            purchase_order.product_item.current_stock = F('current_stock') + purchase_order.quantity_ordered
            purchase_order.product_item.save()
        purchase_order.status = 'Delivered'
        purchase_order.save()
    return redirect('inventory:track_purchase_orders')
