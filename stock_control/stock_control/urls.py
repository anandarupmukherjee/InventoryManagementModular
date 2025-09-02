from django.contrib import admin
from django.urls import path, include
from .module_loader import load_enabled_modules

enabled = load_enabled_modules()

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("inventory.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
    path('data2/', include('services.data_collection_2.urls', namespace='data_collection_2')),
]

if "enable_analysis" in enabled:
    from services.analysis import urls as analysis_urls
    urlpatterns.append(path("analysis/", include((analysis_urls, "analysis"))))

if "enable_data_collection" in enabled:
    from services.data_collection import urls as data_urls
    urlpatterns.append(path("data/", include((data_urls, "data"), namespace='data')))

if "enable_reporting" in enabled:
    from services.reporting import urls as reporting_urls
    urlpatterns.append(path("reporting/", include((reporting_urls, "reporting"))))

if "enable_stock_admin" in enabled:
    from services.data_collection_1 import urls as stock_admin_urls
    urlpatterns.append(path("stock/", include((stock_admin_urls, 'data_collection_1'))))

