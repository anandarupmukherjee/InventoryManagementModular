from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render

from services.data_storage.models import Withdrawal, Location


def _is_admin(user):
    return user.is_authenticated and user.is_staff


@login_required
@user_passes_test(_is_admin, login_url='inventory:dashboard')
def track_withdrawals(request):
    location_id = request.GET.get('location_id') or ''
    withdrawals = (Withdrawal.objects
                   .select_related('product_item', 'user', 'product_item__location')
                   .order_by('-timestamp'))
    if location_id:
        try:
            withdrawals = withdrawals.filter(product_item__location_id=int(location_id))
        except (TypeError, ValueError):
            pass

    for withdrawal in withdrawals:
        withdrawal.full_items = withdrawal.get_full_items_withdrawn()
        withdrawal.partial_items = withdrawal.get_partial_items_withdrawn()

    locations = Location.objects.all().order_by('name')
    return render(request, 'reporting/track_withdrawals.html', {
        'withdrawals': withdrawals,
        'locations': locations,
        'selected_location_id': str(location_id),
    })
