from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
from django.shortcuts import render

from services.data_storage.models import Location, StockRegistrationLog


def _is_admin(user):
    return user.is_authenticated and user.is_staff


@login_required
@user_passes_test(_is_admin, login_url='inventory:dashboard')
def track_stock_registries(request):
    location_id = request.GET.get('location_id') or ''
    user_id = request.GET.get('user_id') or ''
    registrations = (StockRegistrationLog.objects
                     .select_related('product_item', 'user', 'location', 'product_item__location')
                     .order_by('-timestamp'))
    if location_id:
        try:
            registrations = registrations.filter(location_id=int(location_id))
        except (TypeError, ValueError):
            pass

    if user_id:
        try:
            registrations = registrations.filter(user_id=int(user_id))
        except (TypeError, ValueError):
            pass

    locations = Location.objects.all().order_by('name')
    User = get_user_model()
    users = User.objects.filter(stockregistrationlog__isnull=False).distinct().order_by('username')
    return render(request, 'reporting/track_stock_registries.html', {
        'registrations': registrations,
        'locations': locations,
        'users': users,
        'selected_location_id': str(location_id),
        'selected_user_id': str(user_id),
    })
