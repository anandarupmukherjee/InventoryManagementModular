import re
from django.http import JsonResponse
from services.data_storage.models import Product, ProductItem

# 🔧 Utility function to format GS1 expiry date
def _format_gs1_date(raw_date):
    try:
        yy, mm, dd = raw_date[:2], raw_date[2:4], raw_date[4:6]
        return f"{dd}.{mm}.20{yy}"
    except Exception:
        return ""

# 🔍 Reusable parser that works independently of Django
def parse_barcode_data(raw):
    result = {
        "product_code": "",
        "lot_number": "",
        "expiry_date": "",
        "format": None
    }

    # Case 1: 3PR barcode
    if "**" in raw and "3PR" in raw:
        try:
            parts = raw.split("**")
            product_code = re.search(r"3PR\d+", parts[0])
            result["product_code"] = product_code.group(0) if product_code else ""
            result["lot_number"] = parts[1] if len(parts) > 1 else ""
            result["expiry_date"] = parts[2] if len(parts) > 2 else ""
            result["format"] = "3PR"
            return result
        except Exception:
            return None

    # Case 2: Bracketed GS1
    try:
        product_code = re.search(r"\(01\)(\d{14})", raw)
        expiry = re.search(r"\(17\)(\d{6})", raw)
        lot = re.search(r"\(10\)([^\(]+)", raw)

        if product_code:
            result["product_code"] = product_code.group(1)
        if expiry:
            result["expiry_date"] = _format_gs1_date(expiry.group(1))
        if lot:
            result["lot_number"] = lot.group(1)
        result["format"] = "GS1"
        return result if product_code else None
    except Exception:
        pass

    # Case 3: Flattened GS1
    try:
        if raw.startswith("01") and len(raw) > 16:
            result["product_code"] = raw[2:16]
            i = 16

            if raw[i:i+2] == "17":
                expiry_raw = raw[i+2:i+8]
                result["expiry_date"] = _format_gs1_date(expiry_raw)
                i += 8

            if raw[i:i+2] == "10":
                result["lot_number"] = raw[i+2:]

            result["format"] = "GS1_flat"
            return result
    except Exception:
        pass

    return None

# 🌐 Django endpoint to use parse_barcode_data
def parse_barcode(request):
    raw = request.GET.get("raw", "")
    result = parse_barcode_data(raw)
    if result:
        return JsonResponse(result)
    return JsonResponse({"error": "Unrecognized barcode format"}, status=400)

# 🌐 Lookup by scanned barcode
def get_product_by_barcode(request):
    barcode = request.GET.get("barcode", "")
    if not barcode:
        return JsonResponse({"error": "No barcode provided"}, status=400)

    print(barcode)
    product = Product.objects.filter(product_code=barcode).first()

    if not product and barcode.isdigit():
        product = Product.objects.filter(product_code=barcode.lstrip("0")).first()

    if product:
        latest_item = product.items.order_by('-expiry_date').first()
        if latest_item:
            return JsonResponse({
                "name": product.name,
                "stock": str(latest_item.current_stock),
                "units_per_quantity": latest_item.units_per_quantity,
                "product_feature": latest_item.product_feature,
            }, status=200)
        else:
            return JsonResponse({
                "name": product.name,
                "stock": "0",
                "units_per_quantity": "",
                "product_feature": "",
                "warning": "No associated ProductItem found"
            }, status=200)

    return JsonResponse({"error": "Product not found"}, status=404)

# 🌐 Lookup by product ID
def get_product_by_id(request):
    product_id = request.GET.get("id", "")
    if not product_id.isdigit():
        return JsonResponse({"error": "Invalid or missing product ID"}, status=400)

    try:
        product = Product.objects.get(id=product_id)
        latest_item = product.items.order_by('-expiry_date').first()

        response_data = {
            "product_code": product.product_code.zfill(14),
            "name": product.name,
            "current_stock": str(latest_item.current_stock) if latest_item else "0.00",
            "units_per_quantity": latest_item.units_per_quantity if latest_item else 1,
            "product_feature": latest_item.product_feature if latest_item else "unit",
            "lot_number": latest_item.lot_number if latest_item else "",
            "expiry_date": latest_item.expiry_date.strftime('%Y-%m-%d') if latest_item and latest_item.expiry_date else "",
        }

        return JsonResponse(response_data, status=200)

    except Product.DoesNotExist:
        return JsonResponse({"error": "Product not found"}, status=404)
