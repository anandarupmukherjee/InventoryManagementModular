from django.contrib import admin
from django.urls import path, include
from .module_loader import load_enabled_modules

# Load enabled module flags from config/module_config.yaml
enabled = load_enabled_modules()

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
]

# User Interface (Inventory pages)
if "enable_user_interface" in enabled:
    urlpatterns.append(path("", include("inventory.urls")))

# Data Collection v2 (user withdrawals etc.)
if "enable_data_collection_2" in enabled:
    urlpatterns.append(path('data2/', include('services.data_collection_2.urls', namespace='data_collection_2')))

# Data Collection v3 (lots/acceptance)
if "enable_data_collection_3" in enabled:
    urlpatterns.append(path("", include("services.data_collection_3.urls", namespace="data_collection_3")))

# Data Collection v4 (product code registration)
if "enable_data_collection_4" in enabled:
    urlpatterns.append(path("", include("services.data_collection_4.urls", namespace="data_collection_4")))

# Analysis module
if "enable_analysis" in enabled:
    from services.analysis import urls as analysis_urls
    urlpatterns.append(path("analysis/", include((analysis_urls, "analysis"))))

# Data API module (barcode parsing, etc.)
if "enable_data_collection" in enabled:
    from services.data_collection import urls as data_urls
    urlpatterns.append(path("data/", include((data_urls, "data"), namespace='data')))

# Reporting module
if "enable_reporting" in enabled:
    from services.reporting import urls as reporting_urls
    urlpatterns.append(path("reporting/", include((reporting_urls, "reporting"))))

# Stock Admin (product + lots CRUD tools)
if "enable_stock_admin" in enabled:
    from services.data_collection_1 import urls as stock_admin_urls
    urlpatterns.append(path("stock/", include((stock_admin_urls, 'data_collection_1'))))
