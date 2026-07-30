from django.urls import path

from .views import (
    AdminReviewApplicationView,
    AdminReviewDocumentView,
    DriverApplicationView,
    DriverDocumentListCreateView,
    DriverHeartbeatView,
    DriverOfflineView,
    DriverOnlineView,
    VehicleListUpdateView,
    VehicleDetailView,
)


urlpatterns = [
    path("applications/", DriverApplicationView.as_view()),
    path("applications/me/", DriverApplicationView.as_view()),
    path("documents/", DriverDocumentListCreateView.as_view()),
    path("vehicles/", VehicleListUpdateView.as_view()),
    path("vehicles/<int:pk>/", VehicleDetailView.as_view()),
    path("presence/online/", DriverOnlineView.as_view()),
    path("presence/offline/", DriverOfflineView.as_view()),
    path("presence/heartbeat/", DriverHeartbeatView.as_view()),
    path(
        "admin/applications/<int:application_id>/review/",
        AdminReviewApplicationView.as_view(),
    ),
    path(
        "admin/documents/<int:document_id>/review/",
        AdminReviewDocumentView.as_view(),
    ),
]
