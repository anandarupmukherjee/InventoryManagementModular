from django import forms
from services.data_storage.models import Product, ProductCodeMapping
from services.data_collection.data_collection import parse_barcode_data


class ProductCodeMappingForm(forms.ModelForm):
    MODE_EXISTING = "existing"
    MODE_NEW_PRODUCT = "new_product"
    MODE_CHOICES = [
        (MODE_EXISTING, "Update existing product codes"),
        (MODE_NEW_PRODUCT, "Add new product & mapping"),
    ]

    mode = forms.ChoiceField(
        label="Select workflow",
        choices=MODE_CHOICES,
        widget=forms.RadioSelect,
        initial=MODE_EXISTING,
    )
    new_product_name = forms.CharField(
        label="New product name",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Full product name"}),
    )
    new_product_supplier = forms.ChoiceField(
        label="Supplier",
        choices=Product.SUPPLIER_CHOICES,
        required=False,
        initial=Product.SUPPLIER_CHOICES[0][0] if Product.SUPPLIER_CHOICES else None,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    new_product_threshold = forms.IntegerField(
        label="Reorder threshold",
        min_value=0,
        initial=0,
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "0"}),
    )
    new_product_lead_time_days = forms.IntegerField(
        label="Lead time (days)",
        min_value=0,
        initial=1,
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "1"}),
    )
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["product"].queryset = Product.objects.order_by("name")
        self.fields["product"].required = False
        self.fields["new_product_code"].required = False
        self.fields["old_product_code"].required = False

        # Ensure initial workflow reflects the current instance state when editing.
        if self.is_bound:
            pass  # bound forms rely on submitted data
        else:
            instance_mode = self.MODE_EXISTING
            if getattr(self.instance, "pk", None) and not getattr(self.instance, "product", None):
                instance_mode = self.MODE_NEW_PRODUCT
            self.fields["mode"].initial = instance_mode

    class Meta:
        model = ProductCodeMapping
        fields = [
            "product",
            "new_product_code",
            "old_product_code",
            "barcode",
            "notes",
        ]
        widgets = {
            "product": forms.Select(attrs={"class": "form-control"}),
            "new_product_code": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. 3PR1234"}),
            "old_product_code": forms.TextInput(attrs={"class": "form-control", "placeholder": "Legacy code"}),
            "barcode": forms.TextInput(attrs={"class": "form-control", "placeholder": "Scan or paste barcode"}),
            "notes": forms.TextInput(attrs={"class": "form-control", "placeholder": "Optional notes"}),
        }
        labels = {
            "mode": "Workflow",
            "product": "Assign to Product",
            "new_product_code": "New Product Code",
            "old_product_code": "Old Product Code",
            "barcode": "Barcode",
            "notes": "Notes",
            "new_product_name": "New Product Name",
            "new_product_supplier": "Supplier",
            "new_product_threshold": "Reorder Threshold",
            "new_product_lead_time_days": "Lead Time (days)",
        }

    @staticmethod
    def _normalize_product_code(raw: str) -> str:
        code = (raw or "").strip()
        if not code:
            return ""
        return code.lstrip("0") or "0" if code.isdigit() else code

    def clean_new_product_code(self):
        value = (self.cleaned_data.get("new_product_code") or "").strip()
        return value.upper()

    def clean_old_product_code(self):
        value = (self.cleaned_data.get("old_product_code") or "").strip()
        return value.upper()

    def clean_barcode(self):
        value = (self.cleaned_data.get("barcode") or "").strip()
        # Remove spaces that scanners sometimes include
        value = value.replace(" ", "")
        return value.upper()

    def clean(self):
        cleaned_data = super().clean()
        mode = cleaned_data.get("mode") or self.MODE_EXISTING
        new_code = cleaned_data.get("new_product_code", "")
        old_code = cleaned_data.get("old_product_code", "")
        barcode = cleaned_data.get("barcode", "")
        product = cleaned_data.get("product")

        if not any([new_code, old_code, barcode]):
            raise forms.ValidationError("Provide at least one of barcode, new code, or old code.")

        # Ensure uniqueness constraints for non-empty identifiers
        instance_id = self.instance.pk if self.instance.pk else None

        if barcode:
            qs = ProductCodeMapping.objects.filter(barcode__iexact=barcode)
            if instance_id:
                qs = qs.exclude(pk=instance_id)
            if qs.exists():
                self.add_error("barcode", "A mapping for this barcode already exists.")

        if new_code:
            qs = ProductCodeMapping.objects.filter(new_product_code__iexact=new_code)
            if instance_id:
                qs = qs.exclude(pk=instance_id)
            if qs.exists():
                self.add_error("new_product_code", "A mapping for this new product code already exists.")

        if old_code:
            qs = ProductCodeMapping.objects.filter(old_product_code__iexact=old_code)
            if instance_id:
                qs = qs.exclude(pk=instance_id)
            if qs.exists():
                self.add_error("old_product_code", "A mapping for this old product code already exists.")

        if mode == self.MODE_EXISTING:
            if not product:
                self.add_error("product", "Select a product to update.")
        elif mode == self.MODE_NEW_PRODUCT:
            cleaned_data["product"] = None
            name = (cleaned_data.get("new_product_name") or "").strip()
            supplier = cleaned_data.get("new_product_supplier")
            threshold = cleaned_data.get("new_product_threshold")
            lead_time_days = cleaned_data.get("new_product_lead_time_days")
            if not barcode:
                self.add_error("barcode", "Scan or enter a barcode to extract the product code.")
            if not name:
                self.add_error("new_product_name", "Enter the product name.")
            if not supplier:
                self.add_error("new_product_supplier", "Select the supplier.")
            if threshold is None:
                cleaned_data["new_product_threshold"] = 0
            if lead_time_days is None:
                cleaned_data["new_product_lead_time_days"] = 1

            if barcode:
                parsed = parse_barcode_data(barcode)
                extracted_code = ""
                if parsed:
                    extracted_code = parsed.get("product_code") or ""
                if not extracted_code:
                    extracted_code = barcode
                cleaned_data["new_product_code"] = self._normalize_product_code(extracted_code.upper())
                new_code = cleaned_data["new_product_code"]

            # Avoid clobbering an existing product
            if new_code:
                product_qs = Product.objects.filter(product_code__iexact=new_code)
                if instance_id and self.instance.product and self.instance.product.product_code.upper() == new_code.upper():
                    product_qs = product_qs.exclude(pk=self.instance.product.pk)
                if product_qs.exists():
                    self.add_error(
                        "new_product_code",
                        "A product already exists with this code. Switch to \"Update existing product codes\".",
                    )

        return cleaned_data
