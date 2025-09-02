from django.db import models

# Import your existing ProductItem
# from services.data_storage.models import ProductItem

class LotAcceptanceTest(models.Model):
    product_item = models.ForeignKey(
        "data_storage.ProductItem",   # 👈 app_label.ModelName (app label is "data_storage")
        on_delete=models.CASCADE,
        related_name="acceptance_tests",
    )
    tested = models.BooleanField(default=False)
    passed = models.BooleanField(default=False)
    signed_off_by = models.CharField(max_length=100, blank=True, null=True)
    signed_off_at = models.DateTimeField(blank=True, null=True)
    test_reference = models.CharField(max_length=200, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["product_item", "created_at"]),
            models.Index(fields=["product_item", "passed"]),
        ]