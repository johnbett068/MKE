from django.urls import path
from .views import (
    MyNotificationsView,
    MarkNotificationReadView
)

urlpatterns = [
    path('my/', MyNotificationsView.as_view()),
    path('<int:notification_id>/read/', MarkNotificationReadView.as_view()),
]
