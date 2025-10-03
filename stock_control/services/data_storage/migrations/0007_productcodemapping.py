from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("data_storage", "0006_stockregistrationlog"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProductCodeMapping",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("new_product_code", models.CharField(blank=True, max_length=50)),
                ("old_product_code", models.CharField(blank=True, max_length=50)),
                ("barcode", models.CharField(blank=True, max_length=128)),
                ("notes", models.CharField(blank=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "product",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="code_mappings",
                        to="data_storage.product",
                    ),
                ),
            ],
            options={
                "ordering": ["-updated_at", "-created_at"],
            },
        ),
    ]
