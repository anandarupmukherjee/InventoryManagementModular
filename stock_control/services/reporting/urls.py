from django.urls import include, path
from services.reporting.reporting import download_report

app_name = 'reporting'

urlpatterns = [
    path('download_report/', download_report, name='download_report'),
    path('stock-withdrawals/', include(('services.reporting.reporting_stock_withdrawal.urls', 'reporting_stock_withdrawal'), namespace='reporting_stock_withdrawal')),
    path('stock-inputs/', include(('services.reporting.reporting_stock_input.urls', 'reporting_stock_input'), namespace='reporting_stock_input')),
]
