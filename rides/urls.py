# rides/urls.py
from django.urls import path
from .views import (
    request_trip,
    available_trips,
    accept_trip,
    update_trip_status,
    trip_details
)

urlpatterns = [
    path('request/', request_trip, name='request-trip'),
    path('available/', available_trips, name='available-trips'),
    path('<int:trip_id>/accept/', accept_trip, name='accept-trip'),
    path('<int:trip_id>/status/', update_trip_status, name='update-trip-status'),
    path('<int:trip_id>/', trip_details, name='trip-details'),
]
