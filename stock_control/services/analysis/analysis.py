import json
import pandas as pd
from datetime import timedelta
from django.utils.timezone import now
from django.shortcuts import render
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import datetime
from django.db.models import Count, Sum, Value, CharField
from django.db.models.functions import Coalesce
from services.data_storage.models import Product, ProductItem, Withdrawal, PurchaseOrder

def get_dashboard_data():
    # 1. Stock Level Status
    products = Product.objects.all()
    heatmap_data = []
    for product in products:
        stock = product.get_full_items_in_stock()
        threshold = product.threshold or 1
        ratio = stock / threshold if threshold else 0
        heatmap_data.append({
            'label': product.name,
            'code': product.product_code,
            'stock': stock,
            'threshold': threshold,
            'ratio': round(ratio, 2),
        })

    # 2. Stock Distribution by Supplier
    supplier_data = Product.objects.values('supplier').annotate(count=Count('id'))
    supplier_labels = [item['supplier'] for item in supplier_data]
    supplier_values = [item['count'] for item in supplier_data]

    # 3. Recent Withdrawals Trend (last 30 days)
    today = now().date()
    start_date = today - datetime.timedelta(days=30)
    withdrawals = Withdrawal.objects.filter(timestamp__date__gte=start_date)
    withdrawal_by_day = withdrawals.extra({'day': "date(timestamp)"}).values('day').annotate(total=Count('id')).order_by('day')
    withdrawal_dates = [item['day'] for item in withdrawal_by_day]
    withdrawal_counts = [item['total'] for item in withdrawal_by_day]

    # 4. Top Withdrawn Products
    top_withdrawn = Withdrawal.objects.values('product_name').annotate(total=Sum('quantity')).order_by('-total')[:5]
    top_products_labels = [item['product_name'] for item in top_withdrawn]
    top_products_counts = [float(item['total']) for item in top_withdrawn]

    # 5. Purchase Orders Status
    po_status = PurchaseOrder.objects.values('status').annotate(count=Count('id'))
    po_status_labels = [item['status'] for item in po_status]
    po_status_counts = [item['count'] for item in po_status]

    # 6. Expiring Soon Table
    today_plus_15 = int((today + datetime.timedelta(days=15)).strftime("%s"))
    today_plus_30 = int((today + datetime.timedelta(days=30)).strftime("%s"))

    expiring_soon = ProductItem.objects.filter(
        expiry_date__range=[today, today + datetime.timedelta(days=60)]
    ).order_by('expiry_date')

    return {
        'stock_heatmap': heatmap_data,
        'supplier_labels': supplier_labels,
        'supplier_values': supplier_values,
        'withdrawal_dates': withdrawal_dates,
        'withdrawal_counts': withdrawal_counts,
        'top_products_labels': top_products_labels,
        'top_products_counts': top_products_counts,
        'po_status_labels': po_status_labels,
        'po_status_counts': po_status_counts,
        'expiring_soon': expiring_soon,
        'today_plus_15': today_plus_15,
        'today_plus_30': today_plus_30,
    }



# import json
# import pandas as pd
# from datetime import timedelta
# from django.utils.timezone import now
# from django.shortcuts import render
# from django.db.models import Sum

# from statsmodels.tsa.holtwinters import ExponentialSmoothing

# from .models import Product, Withdrawal


def inventory_analysis_forecasting(request):
    # === Get Filter Parameters from GET ===
    selected_range = request.GET.get("range", "30")  # default: 1 month
    selected_limit = request.GET.get("limit", "all")  # default: all items

    try:
        days_back = int(selected_range)
    except ValueError:
        days_back = 30

    try:
        limit = None if selected_limit == "all" else int(selected_limit)
    except ValueError:
        limit = None

    # === Prepare Date Range ===
    today = now().date()
    start_date = today - timedelta(days=days_back)
    recent_dates = [start_date + timedelta(days=i) for i in range((today - start_date).days + 1)]

    # === Filtered Products ===
    products = Product.objects.prefetch_related('items').all()
    if limit:
        products = products[:limit]

    product_names = [p.name for p in products]
    product_codes = [p.product_code for p in products]
    current_stock = [float(sum(i.current_stock for i in p.items.all())) for p in products]
    stock_thresholds = [p.threshold for p in products]
    lead_times = [p.lead_time.days for p in products]

    # === Withdrawals over Date Range ===
    withdrawal_counts = [
        float(Withdrawal.objects.filter(timestamp__date=day).aggregate(total=Sum('quantity'))['total'] or 0)
        for day in recent_dates
    ]
    date_labels = [day.strftime("%b %d") for day in recent_dates]

    # === DataFrame for SMA & Forecast ===
    df = pd.DataFrame({"date": recent_dates, "withdrawals": withdrawal_counts}).set_index("date").asfreq("D", fill_value=0)
    df["withdrawals"] = pd.to_numeric(df["withdrawals"], errors="coerce").fillna(0)
    df["SMA_7"] = df["withdrawals"].rolling(window=7, min_periods=1).mean()
    df["SMA_14"] = df["withdrawals"].rolling(window=14, min_periods=1).mean()

    # === Exponential Smoothing Forecast ===
    forecast_values = [0] * 7
    if df["withdrawals"].sum() > 0:
        model = ExponentialSmoothing(df["withdrawals"], trend="add", seasonal=None, damped_trend=True)
        fitted = model.fit()
        forecast_values = [round(val, 2) for val in fitted.forecast(7).tolist()]

    forecast_dates = [(today + timedelta(days=i)).strftime("%b %d") for i in range(1, 8)]

    # === Run-Out & Reorder Estimates ===
    days_until_run_out = []
    days_until_reorder = []

    for idx, product in enumerate(products):
        total_withdrawn = Withdrawal.objects.filter(
            product_item__product=product,
            timestamp__gte=start_date
        ).aggregate(total=Sum('quantity'))['total'] or 0

        avg_daily = float(total_withdrawn) / max(days_back, 1)
        current = current_stock[idx]

        if avg_daily > 0 and current > 0:
            run_out = round(current / float(avg_daily), 2)
            # Clamp run-out to 400 days max for readability
            if run_out > 400:
                run_out = 400.0
            reorder = max(run_out - lead_times[idx], 0)
            if reorder > 400:
                reorder = 400.0
        else:
            run_out = 0
            reorder = 0

        days_until_run_out.append(run_out)
        days_until_reorder.append(reorder)

    # === Top Consumed Products ===
    top = (Withdrawal.objects
           .filter(timestamp__date__gte=start_date)
           .values('product_code', 'product_name')
           .annotate(total_quantity=Sum('quantity'))
           .order_by('-total_quantity'))

    if limit:
        top = top[:limit]

    top_consumed_names = [i['product_name'] for i in top]
    top_consumed_codes = [i.get('product_code') or '' for i in top]
    top_consumed_quantities = [float(i['total_quantity']) for i in top]

    # === Location-specific Withdrawal Totals (within range) ===
    loc_qs = (Withdrawal.objects
              .filter(timestamp__date__gte=start_date)
              .annotate(loc_name=Coalesce(Coalesce('location__name', 'product_item__location__name'), Value('Central', output_field=CharField())))
              .values('loc_name')
              .annotate(total_qty=Sum('quantity'))
              .order_by('-total_qty'))
    location_names = [row['loc_name'] for row in loc_qs]
    location_withdrawals = [float(row['total_qty'] or 0) for row in loc_qs]

    # === Delayed deliveries per day in chosen range ===
    delayed_counts = [
        PurchaseOrder.objects.filter(status='Delayed', expected_delivery__date=day).count()
        for day in recent_dates
    ]

    # === Top 10 deleted quantities by product (lot_discard) ===
    deleted_qs = (Withdrawal.objects
                  .filter(withdrawal_type='lot_discard', timestamp__date__gte=start_date)
                  .values('product_code', 'product_name')
                  .annotate(total_qty=Sum('quantity'))
                  .order_by('-total_qty')[:10])
    deleted_codes = [row['product_code'] or '' for row in deleted_qs]
    deleted_quantities = [float(row['total_qty'] or 0) for row in deleted_qs]
    deleted_names = [row['product_name'] or '' for row in deleted_qs]

    # === Top 10 upcoming expiring quantities by product code (next 30 days) among top-consumed items ===
    top_codes_10 = [c for c in top_consumed_codes[:10] if c]
    next_30 = today + timedelta(days=30)
    exp_qs = (ProductItem.objects
              .filter(product__product_code__in=top_codes_10, expiry_date__range=[today, next_30])
              .values('product__product_code', 'product__name')
              .annotate(total_units=Sum('current_stock'))
              .order_by('-total_units')[:10])
    upcoming_expiry_codes = [row['product__product_code'] for row in exp_qs]
    upcoming_expiry_quantities = [float(row['total_units'] or 0) for row in exp_qs]
    upcoming_expiry_names = [row['product__name'] or '' for row in exp_qs]

    # === Final Context ===
    context = {
        "product_names": json.dumps(product_names),
        "product_codes": json.dumps(product_codes),
        "current_stock": json.dumps(current_stock),
        "stock_thresholds": json.dumps(stock_thresholds),
        "date_labels": json.dumps(date_labels),
        "withdrawal_counts": json.dumps(withdrawal_counts),
        "sma_7": json.dumps(df["SMA_7"].fillna(0).tolist()),
        "sma_14": json.dumps(df["SMA_14"].fillna(0).tolist()),
        "forecast_dates": json.dumps(forecast_dates),
        "forecast_values": json.dumps(forecast_values),
        "lead_times": json.dumps(lead_times),
        "run_out_days": json.dumps(days_until_run_out),
        "reorder_days": json.dumps(days_until_reorder),
        "top_consumed_names": json.dumps(top_consumed_names),
        "top_consumed_codes": json.dumps(top_consumed_codes),
        "top_consumed_quantities": json.dumps(top_consumed_quantities),
        "location_names": json.dumps(location_names),
        "location_withdrawals": json.dumps(location_withdrawals),
        "delayed_counts": json.dumps([int(x) for x in delayed_counts]),
        "deleted_codes": json.dumps(deleted_codes),
        "deleted_quantities": json.dumps(deleted_quantities),
        "upcoming_expiry_codes": json.dumps(upcoming_expiry_codes),
        "upcoming_expiry_quantities": json.dumps(upcoming_expiry_quantities),
        "upcoming_expiry_names": json.dumps(upcoming_expiry_names),
        "deleted_names": json.dumps(deleted_names),
        "selected_range": selected_range,
        "selected_limit": selected_limit,
    }

    return render(request, 'inventory/inventory_analysis_forecasting.html', context)
