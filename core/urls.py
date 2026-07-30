from django.urls import path

from .views import LocationListView, ResolveLocationView


urlpatterns = [
    path("", LocationListView.as_view()),
    path("resolve/", ResolveLocationView.as_view()),
]
