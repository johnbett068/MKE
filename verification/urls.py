from django.urls import path
from .views import (
    SubmitVerificationView,
    MyVerificationsView,
    AdminReviewVerificationView,
)

urlpatterns = [
    path('submit/', SubmitVerificationView.as_view()),
    path('my/', MyVerificationsView.as_view()),
    path('review/<int:verification_id>/', AdminReviewVerificationView.as_view()),
]
