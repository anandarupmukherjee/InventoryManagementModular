from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from inventory.access_control import group_required
from services.data_storage.models import Product, ProductCodeMapping

from .forms import ProductCodeMappingForm


@login_required
@group_required(["Admin", "Staff"])
def register_product_codes(request):
    search_term = (request.GET.get("q") or "").strip()
    edit_instance = None
    form = None

    if request.method == "POST":
        if "delete_id" in request.POST:
            delete_id = request.POST.get("delete_id")
            mapping = get_object_or_404(ProductCodeMapping, pk=delete_id)
            mapping.delete()
            messages.success(request, "Mapping removed.")
            return redirect("data_collection_4:register-product-codes")

        mapping_id = request.POST.get("mapping_id")
        instance = None
        if mapping_id:
            instance = get_object_or_404(ProductCodeMapping, pk=mapping_id)

        form = ProductCodeMappingForm(request.POST, instance=instance)
        if form.is_valid():
            with transaction.atomic():
                mapping = form.save(commit=False)
                mode = form.cleaned_data.get("mode")
                product = None

                if mode == ProductCodeMappingForm.MODE_EXISTING:
                    product = form.cleaned_data.get("product")
                elif mode == ProductCodeMappingForm.MODE_NEW_PRODUCT:
                    new_code = form.cleaned_data.get("new_product_code")
                    new_name = form.cleaned_data.get("new_product_name")
                    supplier = form.cleaned_data.get("new_product_supplier")
                    threshold = form.cleaned_data.get("new_product_threshold") or 0
                    lead_time_days = form.cleaned_data.get("new_product_lead_time_days") or 1

                    product = Product.objects.create(
                        product_code=new_code,
                        name=new_name,
                        supplier=supplier,
                        threshold=threshold,
                        lead_time=timedelta(days=lead_time_days),
                    )
                mapping.product = product
                mapping.save()

            action = "updated" if instance else "created"
            if mode == ProductCodeMappingForm.MODE_NEW_PRODUCT and product:
                messages.success(
                    request,
                    f"Mapping {action} and new product '{product.name}' added successfully.",
                )
            else:
                messages.success(request, f"Mapping {action} successfully.")
            return redirect("data_collection_4:register-product-codes")
        else:
            barcode_value = (form.data.get("barcode") or "").strip()
            existing = None
            if barcode_value:
                existing = ProductCodeMapping.objects.filter(barcode__iexact=barcode_value).first()
            if existing:
                messages.info(
                    request,
                    "Mapping for this barcode already exists. Loaded it for editing instead.",
                )
                edit_instance = existing
                form = ProductCodeMappingForm(instance=existing)
            else:
                edit_instance = instance
    else:
        edit_id = request.GET.get("edit")
        if edit_id:
            edit_instance = get_object_or_404(ProductCodeMapping, pk=edit_id)
        form = ProductCodeMappingForm(instance=edit_instance)

    mappings_qs = ProductCodeMapping.objects.select_related("product").all()
    if search_term:
        mappings_qs = mappings_qs.filter(
            Q(new_product_code__icontains=search_term)
            | Q(old_product_code__icontains=search_term)
            | Q(barcode__icontains=search_term)
            | Q(notes__icontains=search_term)
            | Q(product__name__icontains=search_term)
        )
    mappings = mappings_qs.order_by("-updated_at", "-created_at")

    context = {
        "form": form,
        "mappings": mappings,
        "search_term": search_term,
        "editing_mapping": edit_instance,
    }
    return render(request, "inventory/register_product_codes.html", context)
