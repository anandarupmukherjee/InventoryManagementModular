# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import F
from .forms import (
    WithdrawalForm,
    ProductForm,
    PurchaseOrderForm,
    UserCreateForm,
    UserUpdateForm,
    ProductItemForm,
    PurchaseOrderCompletionForm,
)
from services.data_storage.models import Product, Withdrawal, PurchaseOrder, ProductItem, PurchaseOrderCompletionLog, Location, StockRegistrationLog
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
from django.db.models import Sum, Count, Exists, OuterRef, Max
from django.db.models import Prefetch
from inventory.access_control import group_required





# ✅ Function to check if the user is an admin
def is_admin(user):
    return user.is_authenticated and is_admin_user(user)

@group_required(["Admin"])
def manage_inventory(request):
    return render(request, "manage_inventory.html")

@group_required(["Admin", "Staff", "User", "Supplier"])
def view_dashboard(request):
    return render(request, "dashboard.html")

# ✅ Admin-only view to list all users
@login_required
@user_passes_test(is_admin, login_url='inventory:dashboard')
def manage_users(request):
    ensure_role_groups()
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            role_key = form.cleaned_data['role']
            set_user_role(user, role_key)
            messages.success(request, f"User '{user.username}' created successfully.")
            return redirect('inventory:manage_users')
    else:
        form = UserCreateForm(initial={'role': ROLE_KEY_USER})

    users = User.objects.all().order_by('username')
    user_rows = []
    for user in users:
        role_key = get_user_role(user)
        user_rows.append({
            'instance': user,
            'name': user.first_name,
            'organisation': user.last_name,
            'email': user.email,
            'role_key': role_key,
            'role_label': ROLE_LABELS.get(role_key, '—'),
        })

    return render(request, 'registration/manage_users.html', {
        'form': form,
        'users': user_rows,
        'role_labels': ROLE_LABELS,
    })

# ✅ Admin-only view to register a new user
@login_required
@user_passes_test(is_admin, login_url='inventory:dashboard')
def register_user(request):
    messages.info(request, "User registration is now handled from the Manage Users page.")
    return redirect('inventory:manage_users')

# ✅ Admin-only view to edit a user
@login_required
@user_passes_test(is_admin, login_url='inventory:dashboard')
def edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    ensure_role_groups()
    role_initial = get_user_role(user) or ROLE_KEY_USER
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=user, role_initial=role_initial)
        if form.is_valid():
            updated_user = form.save()
            role_key = form.cleaned_data['role']
            set_user_role(updated_user, role_key)
            messages.success(request, f"User '{updated_user.username}' updated.")
            return redirect('inventory:manage_users')
    else:
        form = UserUpdateForm(instance=user, role_initial=role_initial)
        form.fields['role'].initial = role_initial
    return render(request, 'registration/edit_user.html', {'form': form, 'user_obj': user})

# ✅ Admin-only view to delete a user
@login_required
@user_passes_test(is_admin, login_url='inventory:dashboard')
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if user == request.user:
        messages.error(request, "You cannot delete your own account.")
        return redirect('inventory:manage_users')
    if request.method == "POST":
        user.delete()
        messages.success(request, "User deleted.")
        return redirect('inventory:manage_users')
    return render(request, 'registration/delete_user.html', {'user_obj': user})


@login_required
@user_passes_test(is_admin, login_url='inventory:dashboard')
def user_activity_overview(request):
    raw_active_entries = get_active_user_sessions()

    active_rows = []
    for entry in raw_active_entries:
        user = entry['user']
        role_key = get_user_role(user)
        active_rows.append({
            'user': user,
            'role_label': ROLE_LABELS.get(role_key, '—'),
            'last_login': entry['last_login'],
            'session_expiry': entry['session_expiry'],
        })

    all_users_queryset = User.objects.all().prefetch_related('groups').order_by('-last_login', 'username')
    all_users_list = list(all_users_queryset)
    all_user_rows = []
    for user in all_users_list:
        role_key = get_user_role(user)
        all_user_rows.append({
            'user': user,
            'role_label': ROLE_LABELS.get(role_key, '—'),
        })

    context = {
        'active_entries': active_rows,
        'active_user_total': len(active_rows),
        'total_users': len(all_users_list),
        'all_users': all_user_rows,
    }
    return render(request, 'registration/user_activity.html', context)


@login_required
@user_passes_test(is_admin, login_url='inventory:dashboard')
def role_assignment(request):
    ensure_role_groups()
    users = User.objects.all().order_by('username')

    if request.method == 'POST':
        updates = 0
        for user in users:
            field_name = f"role_{user.id}"
            role_key = request.POST.get(field_name)
            if role_key and role_key in ROLE_LABELS:
                if get_user_role(user) != role_key:
                    set_user_role(user, role_key)
                    updates += 1
        if updates:
            messages.success(request, f"Roles updated for {updates} user(s).")
        else:
            messages.info(request, "No changes were made to role assignments.")
        return redirect('inventory:role_assignment')

    user_rows = []
    for user in users:
        role_key = get_user_role(user) or ROLE_KEY_USER
        user_rows.append({
            'instance': user,
            'role_key': role_key,
            'role_label': ROLE_LABELS.get(role_key, '—'),
        })

    return render(request, 'registration/role_assignment.html', {
        'users': user_rows,
        'role_choices': ROLE_CHOICES,
        'role_features': ROLE_FEATURE_SUMMARY,
    })


##################### MODULARITY EXPERIMENTAL ##########################

from services.analysis.analysis import inventory_analysis_forecasting as _inventory_analysis_forecasting
from services.reporting.reporting import download_report as _download_report
from services.data_collection.data_collection import (
    parse_barcode as _parse_barcode,
    get_product_by_barcode as _get_product_by_barcode,
    get_product_by_id as _get_product_by_id,
    parse_barcode_data,
)
from services.data_collection_1.stock_admin import stock_admin as _stock_admin, delete_lot as _delete_lot
from services.analysis.analysis import get_dashboard_data
# from services.data_collection.data_collection import parse_barcode_data
from services.data_collection_2.create_withdrawal import create_withdrawal as _create_withdrawal

from services.data_storage.models import Product, ProductItem, PurchaseOrder
from django.contrib.auth.models import User
from collections import Counter, defaultdict
from .constants import (
    ROLE_CHOICES,
    ROLE_LABELS,
    ROLE_FEATURE_SUMMARY,
    ROLE_KEY_ADMIN,
    ROLE_KEY_STAFF,
    ROLE_KEY_USER,
    ROLE_KEY_SUPPLIER,
)
from .utils import (
    ensure_role_groups,
    set_user_role,
    get_user_role,
    is_admin_user,
    get_active_user_sessions,
)
from django.urls import reverse, NoReverseMatch

@login_required
@group_required(["Admin", "Staff", "User", "Supplier"])
def inventory_dashboard(request):
    role_key = get_user_role(request.user)
    if role_key == ROLE_KEY_SUPPLIER:
        return redirect('inventory:low_stock_lots')

    context = get_dashboard_data()

    # 1. Low stock alerts
    low_stock_alerts = []
    for product in Product.objects.prefetch_related("items").all():
        total_stock = sum(item.current_stock for item in product.items.all())
        if total_stock < product.threshold:
            has_pending_po = PurchaseOrder.objects.filter(
                product_code=product.product_code,
                status__in=["Ordered", "Delayed"],
            ).exists()
            if not has_pending_po:
                low_stock_alerts.append(product)
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

    # 7. Lots testing summary and locations mapping
    eligible_lots = ProductItem.objects.all().filter(current_stock__gt=0)
    tested_exists = LotAcceptanceTest.objects.filter(product_item=OuterRef('pk'), tested=True)
    failed_exists = LotAcceptanceTest.objects.filter(product_item=OuterRef('pk'), tested=True, passed=False)

    lots_not_tested_count = eligible_lots.annotate(has_tested=Exists(tested_exists)).filter(has_tested=False).count()
    failed_lots_count = eligible_lots.annotate(has_failed=Exists(failed_exists)).filter(has_failed=True).count()

    total_lots_count = ProductItem.objects.count()
    locations_mapped_count = ProductItem.objects.filter(location__isnull=False).count()
    unmapped_lots_count = total_lots_count - locations_mapped_count
    # Number of locations excluding the default
    locations_count = Location.objects.filter(is_default=False).count()

    context.update({
        "has_low_stock_alerts": has_low_stock_alerts,
        "has_expired_lot_alerts": has_expired_lot_alerts,
        "has_delayed_delivery_alerts": has_delayed_delivery_alerts,
        "has_missing_thresholds": has_missing_thresholds,
        "duplicate_product_names": duplicate_product_names,
        "total_users": total_users,
        "lots_not_tested_count": lots_not_tested_count,
        "failed_lots_count": failed_lots_count,
        "locations_mapped_count": locations_mapped_count,
        "total_lots_count": total_lots_count,
        "unmapped_lots_count": unmapped_lots_count,
        "locations_count": locations_count,
    })

    return render(request, "inventory/dashboard.html", context)



@login_required
@group_required(["Admin", "Staff", "User", "Supplier"])
def help_center(request):
    role_key = get_user_role(request.user) or ROLE_KEY_USER

    def safe_reverse(name):
        try:
            return reverse(name)
        except NoReverseMatch:
            return None

    sections_catalog = [
        {
            'key': 'getting_started',
            'title': 'Getting Started',
            'description': 'Begin at the dashboard to review alerts, then follow the guided tasks below.',
            'action_defs': [
                ('Open Dashboard', 'inventory:dashboard', [ROLE_KEY_ADMIN, ROLE_KEY_STAFF, ROLE_KEY_USER, ROLE_KEY_SUPPLIER]),
                ('View Profile & Change Password', 'password_change', [ROLE_KEY_ADMIN, ROLE_KEY_STAFF, ROLE_KEY_USER, ROLE_KEY_SUPPLIER]),
            ],
            'roles': [ROLE_KEY_ADMIN, ROLE_KEY_STAFF, ROLE_KEY_USER, ROLE_KEY_SUPPLIER],
        },
        {
            'key': 'withdrawals',
            'title': 'Withdraw Stock',
            'description': 'Scan a barcode or pick from the list to record items leaving inventory.',
            'action_defs': [
                ('Create Withdrawal', 'data_collection_2:create_withdrawal', [ROLE_KEY_ADMIN, ROLE_KEY_STAFF, ROLE_KEY_USER]),
            ],
            'roles': [ROLE_KEY_ADMIN, ROLE_KEY_STAFF, ROLE_KEY_USER],
        },
        {
            'key': 'product_overview',
            'title': 'Monitor Product Levels',
            'description': 'Review stock levels, low stock alerts, and expiring lots to plan replenishment.',
            'action_defs': [
                ('Current Product List', 'inventory:product_list', [ROLE_KEY_ADMIN, ROLE_KEY_STAFF, ROLE_KEY_USER]),
                ('Low Stock Lots', 'inventory:low_stock_lots', [ROLE_KEY_ADMIN, ROLE_KEY_STAFF, ROLE_KEY_USER, ROLE_KEY_SUPPLIER]),
                ('Expired Lots', 'inventory:expired_lots', [ROLE_KEY_ADMIN, ROLE_KEY_STAFF, ROLE_KEY_USER, ROLE_KEY_SUPPLIER]),
            ],
            'roles': [ROLE_KEY_ADMIN, ROLE_KEY_STAFF, ROLE_KEY_USER],
        },
        {
            'key': 'supplier_tools',
            'title': 'Supplier View',
            'description': 'Focus on lots requiring supplier attention: upcoming expiries and low quantities.',
            'action_defs': [
                ('Low Stock Lots', 'inventory:low_stock_lots', [ROLE_KEY_SUPPLIER]),
                ('Expired Lots', 'inventory:expired_lots', [ROLE_KEY_SUPPLIER]),
            ],
            'roles': [ROLE_KEY_SUPPLIER],
        },
        {
            'key': 'stock_management',
            'title': 'Manage Stock & Lots',
            'description': 'Register incoming stock, maintain lots, and capture acceptance testing.',
            'action_defs': [
                ('Stock Admin Tools', 'data_collection_1:stock_admin', [ROLE_KEY_ADMIN, ROLE_KEY_STAFF]),
                ('Register New Stock', 'data_collection_3:register-stock', [ROLE_KEY_ADMIN, ROLE_KEY_STAFF]),
                ('Lot QA Review', 'inventory:lot_quality_review', [ROLE_KEY_ADMIN, ROLE_KEY_STAFF]),
            ],
            'roles': [ROLE_KEY_ADMIN, ROLE_KEY_STAFF],
        },
        {
            'key': 'purchase_orders',
            'title': 'Purchase Orders',
            'description': 'Create, track, and complete purchase orders to replenish inventory.',
            'action_defs': [
                ('Record Purchase Order', 'inventory:record_purchase_order', [ROLE_KEY_ADMIN, ROLE_KEY_STAFF]),
                ('Track Purchase Orders', 'inventory:track_purchase_orders', [ROLE_KEY_ADMIN, ROLE_KEY_STAFF, ROLE_KEY_USER]),
            ],
            'roles': [ROLE_KEY_ADMIN, ROLE_KEY_STAFF, ROLE_KEY_USER],
        },
        {
            'key': 'reporting',
            'title': 'Reports & Insights',
            'description': 'Export data and explore trends to support forecasting and audits.',
            'action_defs': [
                ('Download Reports', 'reporting:download_report', [ROLE_KEY_ADMIN]),
                ('Inventory Analysis', 'analysis:inventory_analysis_forecasting', [ROLE_KEY_ADMIN]),
            ],
            'roles': [ROLE_KEY_ADMIN],
        },
        {
            'key': 'user_management',
            'title': 'Manage Users & Roles',
            'description': 'Add team members and adjust permissions to match responsibilities.',
            'action_defs': [
                ('Manage Users', 'inventory:manage_users', [ROLE_KEY_ADMIN]),
                ('Role Assignment', 'inventory:role_assignment', [ROLE_KEY_ADMIN]),
            ],
            'roles': [ROLE_KEY_ADMIN],
        },
    ]

    available_sections = []
    for section in sections_catalog:
        if role_key not in section['roles']:
            continue
        actions = []
        for label, route_name, roles in section['action_defs']:
            url = safe_reverse(route_name)
            if url and role_key in roles:
                actions.append({'label': label, 'url': url, 'roles': roles})
        available_sections.append({
            'title': section['title'],
            'description': section['description'],
            'actions': actions,
        })

    return render(request, 'inventory/help_center.html', {
        'sections': available_sections,
        'role_label': ROLE_LABELS.get(role_key, 'User'),
    })


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
@group_required(["Admin", "Staff"])
def stock_admin(request, product_id=None):
    response = _stock_admin(request, product_id=product_id)
    if isinstance(response, dict) and response.get("redirect"):
        return redirect('inventory:stock_admin')
    return response

@login_required
@group_required(["Admin", "Staff"])
def delete_lot(request, item_id):
    response = _delete_lot(request, item_id)
    if isinstance(response, dict) and response.get("redirect"):
        return redirect('inventory:stock_admin')
    return response


@login_required
@group_required(["Admin", "Staff", "User"])
def create_withdrawal(request):
    return _create_withdrawal(request)

####################################






@login_required
@group_required(["Admin", "Staff", "User"])
def product_list(request):
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

    product_codes = [p.product_code for p in products]
    logs_by_product = {
        entry['product_code']: entry
        for entry in (
            StockRegistrationLog.objects
            .filter(product_code__in=product_codes)
            .values('product_code')
            .annotate(last_delivery=Max('delivery_datetime'), last_timestamp=Max('timestamp'))
        )
    }

    for product in products:
        product.full_items = product.get_full_items_in_stock()
        product.remaining_parts = product.get_remaining_parts()
        product.total_stock = sum(item.current_stock for item in product.items.all())

        items = list(product.items.all())
        product.lot_instances = len(items)

        product.earliest_expiry = None
        if items:
            expiries = [i.expiry_date for i in items if getattr(i, "expiry_date", None)]
            product.earliest_expiry = min(expiries) if expiries else None

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

        log_entry = logs_by_product.get(product.product_code)
        if log_entry:
            product.last_received = log_entry['last_delivery'] or log_entry['last_timestamp']
        else:
            product.last_received = None

    return render(request, 'inventory/product_list.html', {
        'products': products
    })


@login_required
@group_required(["Admin", "Staff", "User", "Supplier"])
def low_stock_lots(request):
    products = Product.objects.prefetch_related('items', 'items__location').all()
    rows = []

    for product in products:
        total_stock = sum(item.current_stock for item in product.items.all())
        if total_stock >= product.threshold:
            continue
        has_pending_po = PurchaseOrder.objects.filter(
            product_code=product.product_code,
            status__in=["Ordered", "Delayed"],
        ).exists()
        if has_pending_po:
            continue

        items = list(product.items.all())
        if items:
            for item in items:
                rows.append({
                    'product': product,
                    'lot_number': item.lot_number,
                    'lot_stock': item.current_stock,
                    'total_stock': total_stock,
                    'threshold': product.threshold,
                    'expiry_date': item.expiry_date,
                    'location': getattr(item, 'location', None),
                })
        else:
            rows.append({
                'product': product,
                'lot_number': '—',
                'lot_stock': 0,
                'total_stock': total_stock,
                'threshold': product.threshold,
                'expiry_date': None,
                'location': None,
            })

    rows.sort(key=lambda r: (r['product'].name, r['expiry_date'] or datetime.date.max))

    return render(request, 'inventory/low_stock_lots.html', {
        'rows': rows,
    })


@login_required
@group_required(["Admin", "Staff", "User", "Supplier"])
def expired_lots(request):
    today = timezone.localdate() if hasattr(timezone, 'localdate') else timezone.now().date()
    selected_range = request.GET.get('range', 'expired')
    range_definitions = {
        'expired': {
            'label': 'Already expired',
            'filter': {'expiry_date__lte': today},
            'description': f"Lots with an expiry date on or before {today.strftime('%Y-%m-%d')}.",
        },
        '7_days': {
            'label': 'Expiring in 7 days',
            'range_end': today + datetime.timedelta(days=7),
        },
        '1_month': {
            'label': 'Expiring in 1 month',
            'range_end': today + datetime.timedelta(days=30),
        },
    }

    if selected_range not in range_definitions:
        selected_range = 'expired'

    definition = range_definitions[selected_range]
    filters = {'expiry_date__isnull': False}

    if selected_range == 'expired':
        filters.update(definition['filter'])
    else:
        range_end = definition['range_end']
        filters.update({
            'expiry_date__gt': today,
            'expiry_date__lte': range_end,
        })
        definition['description'] = (
            f"Lots with an expiry date between {today.strftime('%Y-%m-%d')} and {range_end.strftime('%Y-%m-%d')}"
        )

    items = (ProductItem.objects
             .filter(**filters)
             .select_related('product', 'location')
             .order_by('expiry_date'))

    return render(request, 'inventory/expired_lots.html', {
        'items': items,
        'today': today,
        'selected_range': selected_range,
        'range_definitions': range_definitions,
        'subtitle': definition['description'],
    })



# ✅ Updated view function
@login_required
@group_required(["Admin", "Staff"])
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
@group_required(["Admin", "Staff", "User"])
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
@group_required(["Admin", "Staff"])
def mark_order_delivered(request, order_id):
    purchase_order = get_object_or_404(PurchaseOrder, id=order_id)
    if purchase_order.status != 'Delivered':
        if purchase_order.product_item:
            purchase_order.product_item.current_stock = F('current_stock') + purchase_order.quantity_ordered
            purchase_order.product_item.save()
        purchase_order.status = 'Delivered'
        purchase_order.save()
    return redirect('inventory:track_purchase_orders')


@login_required
@group_required(["Admin", "Staff"])
def lot_quality_review(request):
    search_query = (request.GET.get('search') or '').strip()
    barcode_query = (request.GET.get('barcode') or '').strip()

    products = Product.objects.prefetch_related(
        Prefetch(
            "items",
            queryset=ProductItem.objects.prefetch_related(
                Prefetch("acceptance_tests", queryset=LotAcceptanceTest.objects.order_by("-created_at"))
            )
        )
    )

    if barcode_query:
        parsed = parse_barcode_data(barcode_query)
        codes = []
        if parsed:
            code = parsed.get('product_code') or ''
            if code:
                codes.append(code)
                normalized = code.lstrip('0')
                if normalized and normalized != code:
                    codes.append(normalized)
        else:
            normalized = barcode_query.lstrip('0')
            codes = [barcode_query]
            if normalized and normalized != barcode_query:
                codes.append(normalized)
        if codes:
            products = products.filter(product_code__in=codes)
        else:
            products = products.none()

    if search_query:
        products = products.filter(
            Q(product_code__icontains=search_query) |
            Q(name__icontains=search_query) |
            Q(items__lot_number__icontains=search_query)
        ).distinct()

    products = products.order_by('name')

    product_codes = [p.product_code for p in products]
    logs_by_product = {
        entry['product_code']: entry
        for entry in (
            StockRegistrationLog.objects
            .filter(product_code__in=product_codes)
            .values('product_code')
            .annotate(last_delivery=Max('delivery_datetime'), last_timestamp=Max('timestamp'))
        )
    }

    rows = []
    for product in products:
        items = list(product.items.all())
        total_stock = sum(item.current_stock for item in items)
        passed = failed = untested = 0
        earliest_expiry = None

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

            if item.expiry_date:
                if earliest_expiry is None or item.expiry_date < earliest_expiry:
                    earliest_expiry = item.expiry_date

        log_entry = logs_by_product.get(product.product_code)
        last_received = None
        if log_entry:
            last_received = log_entry['last_delivery'] or log_entry['last_timestamp']

        rows.append({
            'product': product,
            'total_stock': total_stock,
            'threshold': product.threshold,
            'supplier': product.supplier,
            'passed': passed,
            'failed': failed,
            'untested': untested,
            'earliest_expiry': earliest_expiry,
            'last_received': last_received,
        })

    return render(request, 'inventory/lot_quality_review.html', {
        'rows': rows,
        'search_query': search_query,
        'barcode_query': barcode_query,
    })
