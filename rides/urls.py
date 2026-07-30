from django.urls import path

from .views import (
    AcceptOfferView,
    ArrivedTripView,
    CancelTripView,
    CompleteTripView,
    DriverOfferListView,
    FareQuoteCreateView,
    RejectOfferView,
    StartTripView,
    TripDetailView,
    TripListCreateView,
)


urlpatterns = [
    path("", TripListCreateView.as_view(), name="trip-list-create"),
    path("quotes/", FareQuoteCreateView.as_view(), name="fare-quote-create"),
    path("offers/", DriverOfferListView.as_view(), name="driver-offers"),
    path(
        "offers/<int:offer_id>/accept/",
        AcceptOfferView.as_view(),
        name="offer-accept",
    ),
    path(
        "offers/<int:offer_id>/reject/",
        RejectOfferView.as_view(),
        name="offer-reject",
    ),
    path("<int:trip_id>/", TripDetailView.as_view(), name="trip-detail"),
    path("<int:trip_id>/arrived/", ArrivedTripView.as_view(), name="trip-arrived"),
    path("<int:trip_id>/start/", StartTripView.as_view(), name="trip-start"),
    path("<int:trip_id>/complete/", CompleteTripView.as_view(), name="trip-complete"),
    path("<int:trip_id>/cancel/", CancelTripView.as_view(), name="trip-cancel"),
]
