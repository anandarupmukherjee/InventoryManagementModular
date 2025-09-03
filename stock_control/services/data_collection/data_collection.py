import re
from django.http import JsonResponse
from services.data_storage.models import Product, ProductItem
from django.db.models import Q
import string

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

    if not raw:
        return None

    # Normalize common scanner variations
    # - Remove ASCII GS (Group Separator, 0x1D) which often appears between AIs
    # - Remove whitespace and other non-alnum (keep parentheses for bracketed parse)
    gs_char = "\x1D"
    # Remove GS control char but otherwise keep original content for bracketed parse
    raw_no_gs = raw.replace(gs_char, "")
    raw_keep_paren = raw_no_gs
    # Fully flattened (no parentheses) for the unbracketed pass
    # Flattened string with only A-Z, a-z, 0-9 kept
    raw_flat = re.sub(r"[^A-Za-z0-9]+", "", raw_no_gs.replace("(", "").replace(")", ""))

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
        product_code = re.search(r"\(01\)(\d{14})", raw_keep_paren)
        expiry = re.search(r"\(17\)(\d{6})", raw_keep_paren)
        lot = re.search(r"\(10\)([^\(\)]+)", raw_keep_paren)

        if product_code:
            result["product_code"] = product_code.group(1)
            if expiry:
                result["expiry_date"] = _format_gs1_date(expiry.group(1))
            if lot:
                result["lot_number"] = lot.group(1)
            result["format"] = "GS1"
            return result
        # If no product_code in bracketed form, fall through to flattened parsing
    except Exception:
        pass

    # Case 3: Flattened GS1
    try:
        s = raw_flat
        # Must start with AI 01 and have 14 digits after
        m01 = re.search(r"01(\d{14})", s)
        if not m01:
            raise ValueError("Missing AI 01")
        result["product_code"] = m01.group(1)

        # Search for expiry AI 17 (fixed length 6) anywhere after the GTIN
        after01 = s[m01.end():]
        m17 = re.search(r"17(\d{6})", after01)
        if m17:
            result["expiry_date"] = _format_gs1_date(m17.group(1))

        # Search for lot AI 10 (variable length). Prefer to stop at next AI (two digits) if present
        # Capture lot (AI 10) until next known AI or end. Allow common lot punctuation
        m10 = re.search(r"10([A-Za-z0-9\-_.\/]+?)(?=(?:01|17|21|15|11|30|37)\d|$)", after01)
        if m10:
            result["lot_number"] = m10.group(1)

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
        # Provide a normalized product code (strip leading zeros for numeric codes)
        p = result.get("product_code") or ""
        if p.isdigit():
            normalized = p.lstrip("0") or "0"
        else:
            normalized = p
        result["normalized_product_code"] = normalized
        # Back-compat: also expose as 'code'
        result["code"] = normalized
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


# 🌐 Typeahead search for products by name/code/supplier
def search_products(request):
    q = (request.GET.get("q", "") or "").strip()
    limit = int(request.GET.get("limit", 10) or 10)
    if not q:
        return JsonResponse({"results": []}, status=200)

    qs = (Product.objects
          .filter(Q(name__icontains=q) | Q(product_code__icontains=q) | Q(supplier__icontains=q))
          .order_by('name')[:limit])
    results = [{
        "id": p.id,
        "name": p.name,
        "product_code": p.product_code,
        "supplier": p.get_supplier_display() if hasattr(p, 'get_supplier_display') else p.supplier,
    } for p in qs]
    return JsonResponse({"results": results}, status=200)
