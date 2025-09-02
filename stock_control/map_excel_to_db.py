# import os
# import django
# import pandas as pd
# from decimal import Decimal
# from datetime import timedelta

# # 👇 Setup Django manually just like your previous working script
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stock_control.settings')  # ✅ adjust to match your project
# django.setup()

# from inventory.models import Product

# def extract_products(file_path, sheet_name, skip_rows, name_index, code_index, supplier_label):
#     xl = pd.ExcelFile(file_path)
#     df = xl.parse(sheet_name, skiprows=skip_rows, header=None)

#     df = df[[name_index, code_index]].dropna()
#     df.columns = ['name', 'product_code']
#     df = df[df['product_code'].astype(str).str.strip().str.lower() != 'undergoing optimisation']

#     for _, row in df.iterrows():
#         name = str(row['name']).strip()
#         code = str(row['product_code']).strip()

#         product, created = Product.objects.get_or_create(
#             product_code=code,
#             defaults={
#                 'name': name,
#                 'supplier': supplier_label,
#                 'threshold': 1,
#                 'lead_time': timedelta(days=2),
#                 'current_stock': Decimal('0.00'),
#                 'units_per_quantity': 1,
#                 'accumulated_partial': 0,
#                 'product_feature': 'unit'
#             }
#         )

#         print(f"{'✅ Created' if created else '➡️ Exists'}: {product.name} ({product.product_code})")


# if __name__ == "__main__":
#     file_path = "Addenbrookes-2025_master.xlsx"
#     extract_products(file_path, "Bond Reagents ", 4, 0, 1, "LEICA")
#     extract_products(file_path, "3rd Party Antibodies", 4, 0, 1, "THIRD_PARTY")

#     print("🎉 Excel import completed.")

import os
import django
import pandas as pd
from datetime import timedelta

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "stock_control.settings")  # replace with your project name
django.setup()

from services.data_storage.models import Product  # adjust if your app is not called 'inventory'

# Load Excel file
file_path = "Addenbrookes-2025_master.xlsx"  # replace with actual path
xl = pd.ExcelFile(file_path)

# Sheet-specific metadata
sheet_info = {
    "Bond Reagents": {"supplier": "LEICA", "lead_time": timedelta(days=2)},
    "3rd Party Antibodies": {"supplier": "THIRD_PARTY", "lead_time": timedelta(days=4)},
}

for sheet_name, info in sheet_info.items():
    df = xl.parse(sheet_name, skiprows=4, usecols=[0, 1])  # Skip to row 5, read first 2 cols
    df = df.dropna(subset=[df.columns[0], df.columns[1]])  # Drop rows with missing name or code

    for _, row in df.iterrows():
        name = str(row[df.columns[0]]).strip()
        product_code = str(row[df.columns[1]]).strip()

        # Create or update the product
        product, created = Product.objects.update_or_create(
            product_code=product_code,
            defaults={
                "name": name,
                "supplier": info["supplier"],
                "threshold": 0,
                "lead_time": info["lead_time"]
            }
        )
        print(f"{'Created' if created else 'Updated'}: {product}")
