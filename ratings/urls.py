from django.urls import path
from .views import CreateRatingView, MyRatingsView

urlpatterns = [
    path('rate/', CreateRatingView.as_view()),
    path('my-ratings/', MyRatingsView.as_view()),
]
