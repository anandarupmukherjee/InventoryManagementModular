from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
from datetime import date, timedelta
from django.utils import timezone
from django.utils.timezone import now
from .models_acceptance import LotAcceptanceTest

class Location(models.Model):
    name = models.CharField(max_length=100, unique=True)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    @classmethod
    def get_default(cls):
        obj, _ = cls.objects.get_or_create(name="Central", defaults={"is_default": True})
        return obj

class Supplier(models.Model):
    name = models.CharField(max_length=100)
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    SUPPLIER_CHOICES = [
        ('LEICA', 'Leica'),
        ('THIRD_PARTY', 'Third Party'),
    ]
    product_code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    supplier = models.CharField(max_length=20, choices=SUPPLIER_CHOICES, default='LEICA')
    threshold = models.PositiveIntegerField()
    lead_time = models.DurationField(default=timedelta(days=1), help_text="Lead time (e.g., 1 day, 2 hours)")

    def __str__(self):
        return f"{self.product_code} - {self.name}"

    def get_full_items_in_stock(self):
        return int(sum(item.current_stock for item in self.items.all()))

    def get_remaining_parts(self):
        return sum(item.accumulated_partial for item in self.items.all())


class ProductCodeMapping(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="code_mappings",
    )
    new_product_code = models.CharField(max_length=50, blank=True)
    old_product_code = models.CharField(max_length=50, blank=True)
    barcode = models.CharField(max_length=128, blank=True)
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at", "-created_at"]

    def __str__(self):
        identifier = self.new_product_code or self.old_product_code or self.barcode or "Unmapped"
        product_label = self.product.name if self.product else "No Product"
        return f"{identifier} → {product_label}"


class ProductItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="items")
    lot_number = models.CharField(max_length=50, default="LOT000")
    expiry_date = models.DateField(default=date.today)
    current_stock = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00'),
        help_text="Stock available for this lot"
    )
    units_per_quantity = models.PositiveIntegerField(default=1)
    accumulated_partial = models.PositiveIntegerField(default=0)

    PRODUCT_FEATURE_CHOICES = [
        ('unit', 'Unit'),
        ('volume', 'Volume'),
    ]
    product_feature = models.CharField(max_length=10, choices=PRODUCT_FEATURE_CHOICES, default='unit')
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True, related_name="items")

    def __str__(self):
        return f"{self.product.name} (Lot {self.lot_number})"

    def get_full_items_in_stock(self):
        """Total full items across all lots."""
        return int(sum(item.current_stock for item in self.items.all()))

    def get_remaining_parts(self):
        """Total partial units (leftover parts across all lots)."""
        return sum(item.accumulated_partial for item in self.items.all())

    def save(self, *args, **kwargs):
        # Ensure a default location is set
        if self.location is None:
            try:
                self.location = Location.get_default()
            except Exception:
                pass
        super().save(*args, **kwargs)



class Withdrawal(models.Model):
    product_item = models.ForeignKey('ProductItem', on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="For unit-based: store integer (e.g., 1.00); for volume-based: store decimal (e.g., 0.5)"
    )
    withdrawal_type = models.CharField(
        max_length=10,
        choices=[
            ('unit', 'Full Item'),
            ('volume', 'Volume'),
            ('part', 'Partial Withdrawal'),
        ],
        default='unit'
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    barcode = models.CharField(max_length=128, blank=True, null=True)
    location = models.ForeignKey('Location', on_delete=models.SET_NULL, null=True, blank=True, related_name='withdrawals')

    parts_withdrawn = models.PositiveIntegerField(
        default=0,
        blank=True,
        help_text="Number of partial units withdrawn, if not a full item"
    )

    product_code = models.CharField(max_length=50, default="N/A")
    product_name = models.CharField(max_length=100, default="Unnamed Product")
    lot_number = models.CharField(max_length=50, default="UNKNOWN")
    expiry_date = models.DateField(default=date.today)

    def save(self, *args, **kwargs):
        if self.product_item:
            product = self.product_item.product
            self.product_code = product.product_code
            self.product_name = product.name
            self.lot_number = self.product_item.lot_number
            self.expiry_date = self.product_item.expiry_date
            if self.location is None:
                # default withdrawal location to the item's location if not provided
                self.location = getattr(self.product_item, 'location', None)
        super().save(*args, **kwargs)

    def get_full_items_withdrawn(self):
        return int(self.quantity)

    def get_partial_items_withdrawn(self):
        return self.parts_withdrawn

    def __str__(self):
        return f"{self.product_name} withdrawn on {self.timestamp}"


class StockRegistrationLog(models.Model):
    product_item = models.ForeignKey('ProductItem', on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('1.00'),
        help_text="Quantity registered from this scan"
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    barcode = models.CharField(max_length=128, blank=True, null=True)
    delivery_datetime = models.DateTimeField(null=True, blank=True)
    location = models.ForeignKey('Location', on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_registrations')

    product_code = models.CharField(max_length=50, default="N/A")
    product_name = models.CharField(max_length=100, default="Unnamed Product")
    lot_number = models.CharField(max_length=50, default="UNKNOWN")
    expiry_date = models.DateField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.product_item:
            product = self.product_item.product
            self.product_code = product.product_code
            self.product_name = product.name
            self.lot_number = self.product_item.lot_number
            self.expiry_date = self.product_item.expiry_date
            if self.location is None:
                self.location = getattr(self.product_item, 'location', None)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Registration for {self.product_name} on {self.timestamp}"



class PurchaseOrder(models.Model):
    product_item = models.ForeignKey('ProductItem', on_delete=models.SET_NULL, null=True, blank=True)
    quantity_ordered = models.PositiveIntegerField(default=1)
    ordered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    order_date = models.DateTimeField(auto_now_add=True)
    expected_delivery = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, default='Ordered')
    delivered_at = models.DateTimeField(null=True, blank=True)
    po_reference = models.CharField(max_length=100, blank=True, null=True, default="")

    product_code = models.CharField(max_length=50, default="N/A")
    product_name = models.CharField(max_length=100, default="Unnamed Product")
    lot_number = models.CharField(max_length=50, default="UNKNOWN")
    expiry_date = models.DateField(default=date.today)

    def save(self, *args, **kwargs):
        if self.product_item:
            product = self.product_item.product
            self.product_code = product.product_code
            self.product_name = product.name
            self.lot_number = self.product_item.lot_number
            self.expiry_date = self.product_item.expiry_date
        super().save(*args, **kwargs)

    def mark_as_delivered(self):
        if self.status != 'Delivered' and self.product_item:
            self.product_item.quantity += self.quantity_ordered
            self.product_item.save()
            self.status = 'Delivered'
            self.save()

    def __str__(self):
        ref = f" [{self.po_reference}]" if self.po_reference else ""
        return f"PO-{self.id}{ref} for {self.product_name} (Lot {self.lot_number})"




class PurchaseOrderCompletionLog(models.Model):
    # Link to the original PO (optional, for traceability)
    purchase_order = models.ForeignKey(
        'PurchaseOrder',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='completion_logs'
    )

    # Snapshot fields (copied from related models at the time of completion)
    product_code = models.CharField(max_length=50)
    product_name = models.CharField(max_length=100)
    lot_number = models.CharField(max_length=50)
    expiry_date = models.DateField()

    quantity_ordered = models.PositiveIntegerField()
    ordered_by = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='po_completions_created'
    )
    completed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='po_completions_completed'
    )

    order_date = models.DateTimeField()
    completed_at = models.DateTimeField(default=now)

    remarks = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Completed PO - {self.product_name} ({self.product_code}) on {self.completed_at.strftime('%Y-%m-%d %H:%M')}"
