from django.urls import path

from .views import (
    InitiateStkPushView,
    MpesaB2CResultView,
    MpesaC2BConfirmationView,
    MpesaC2BValidationView,
    MpesaStkCallbackView,
    PaymentIntentDetailView,
)


urlpatterns = [
    path("mpesa/stk/", InitiateStkPushView.as_view()),
    path("intents/<uuid:public_id>/", PaymentIntentDetailView.as_view()),
    path("webhooks/mpesa/stk/", MpesaStkCallbackView.as_view()),
    path("webhooks/mpesa/c2b/validation/", MpesaC2BValidationView.as_view()),
    path("webhooks/mpesa/c2b/confirmation/", MpesaC2BConfirmationView.as_view()),
    path("webhooks/mpesa/b2c/result/", MpesaB2CResultView.as_view()),
]
