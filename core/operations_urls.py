from django.urls import path

from .operations_views import dashboard


urlpatterns = [
    path("", dashboard, name="operations-dashboard"),
]
