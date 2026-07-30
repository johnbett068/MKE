from django.contrib import admin
from .models import (
    CancellationConfig,
    FareQuote,
    Ride,
    Trip,
    TripCancellation,
    TripEvent,
    TripOffer,
    Vehicle,
)

admin.site.register(Vehicle)
admin.site.register(Trip)
admin.site.register(Ride)
admin.site.register(TripEvent)
admin.site.register(CancellationConfig)
admin.site.register(FareQuote)
admin.site.register(TripOffer)
admin.site.register(TripCancellation)
