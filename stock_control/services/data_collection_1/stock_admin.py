from decimal import Decimal

from django.shortcuts import render, get_object_or_404
from django.utils.timezone import now
from django.db.models import F
import datetime
from django.utils import timezone
from services.data_collection.data_collection import parse_barcode_data
from services.data_storage.models import Product, ProductItem, Withdrawal
from inventory.forms import ProductForm, ProductItemForm
from django.shortcuts import redirect


def stock_admin(request, product_id=None):
    raw_barcode = request.GET.get("raw", None)
    barcode_parsed_code, parsed_lot, parsed_expiry = None, None, None
    editing_product, editing_lot_item = None, None

    if raw_barcode:
        barcode_data = parse_barcode_data(raw_barcode)
        if barcode_data:
            barcode_parsed_code = barcode_data.get("product_code")
            parsed_lot = barcode_data.get("lot_number")
            parsed_expiry = barcode_data.get("expiry_date")

            if barcode_parsed_code:
                editing_product = Product.objects.filter(product_code=barcode_parsed_code.lstrip("0")).first()
                if editing_product:
                    product_id = editing_product.id
                    if parsed_lot:
                        editing_lot_item = ProductItem.objects.filter(product=editing_product, lot_number=parsed_lot).first()

    products = Product.objects.all().prefetch_related('items').order_by('name')
    product = get_object_or_404(Product, pk=product_id) if product_id else None

    if request.method == "POST":
        product_form = ProductForm(request.POST, instance=product)
        product_item_form = ProductItemForm(request.POST, instance=editing_lot_item)

        if product_form.is_valid() and product_item_form.is_valid():
            saved_product = product_form.save()
            product_item = product_item_form.save(commit=False)
            product_item.product = saved_product
            product_item.save()
            return redirect('data_collection_1:stock_admin')


    else:
        product_form = ProductForm(instance=editing_product) if editing_product else ProductForm()
        product_item_form = ProductItemForm(instance=editing_lot_item)

        if parsed_lot and not editing_lot_item:
            product_item_form.fields['lot_number'].initial = parsed_lot
        if parsed_expiry and not editing_lot_item:
            try:
                product_item_form.fields['expiry_date'].initial = datetime.datetime.strptime(parsed_expiry, "%d.%m.%Y").date()
            except ValueError:
                pass

    today = timezone.localdate() if hasattr(timezone, 'localdate') else timezone.now().date()
    attention_lots = []
    low_stock_products = []

    for product_entry in products:
        items = list(product_entry.items.all())
        total_stock = Decimal('0')
        for item in items:
            if item.current_stock is not None:
                total_stock += item.current_stock
        try:
            threshold_value = Decimal(product_entry.threshold)
        except Exception:
            threshold_value = Decimal('0')

        is_low_stock = total_stock < threshold_value if threshold_value else False
        if is_low_stock:
            low_stock_products.append(product_entry)

        for item in items:
            expiry_date = item.expiry_date
            is_expired = bool(expiry_date and expiry_date <= today)
            if not is_expired and not is_low_stock:
                continue
            attention_lots.append({
                'product': product_entry,
                'item': item,
                'is_expired': is_expired,
                'is_low_stock': is_low_stock,
            })

    attention_lots.sort(
        key=lambda entry: (
            not entry['is_expired'],  # expired lots first
            entry['product'].name.lower(),
            entry['item'].lot_number,
        )
    )

    context = {
        'products': products,
        'product_form': product_form,
        'product_item_form': product_item_form,
        'editing_product': editing_product,
        'low_stock': low_stock_products,
        'attention_lots': attention_lots,
        'now': now(),
    }
    return render(request, 'inventory/stock_admin.html', context)



def delete_lot(request, item_id):
    item = get_object_or_404(ProductItem, id=item_id)
    if request.method == "POST":
        Withdrawal.objects.create(
            product_item=item,
            quantity=item.current_stock,
            withdrawal_type='lot_discard',
            timestamp=timezone.now(),
            user=request.user,
            barcode=None,
            parts_withdrawn=0,
            product_code=item.product.product_code,
            product_name=item.product.name,
            lot_number=item.lot_number,
            expiry_date=item.expiry_date,
        )
        item.delete()
        return redirect('data_collection_1:stock_admin')
