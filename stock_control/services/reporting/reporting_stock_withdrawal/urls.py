from django.urls import path

from .views import track_withdrawals

app_name = 'reporting_stock_withdrawal'

urlpatterns = [
    path('', track_withdrawals, name='track_withdrawals'),
]
