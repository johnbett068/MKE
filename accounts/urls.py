# accounts/urls.py

from django.urls import path
from .views import (
    ConfirmPasswordResetView,
    ConfirmPhoneLoginView,
    MeView,
    RegisterView,
    RequestPasswordResetView,
    RequestPhoneLoginView,
    RequestPhoneCodeView,
    VerifyPhoneView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='account-register'),
    path('me/', MeView.as_view(), name='account-me'),
    path(
        'phone/request-code/',
        RequestPhoneCodeView.as_view(),
        name='phone-request-code',
    ),
    path('phone/verify/', VerifyPhoneView.as_view(), name='phone-verify'),
    path(
        'password/request-reset/',
        RequestPasswordResetView.as_view(),
        name='password-request-reset',
    ),
    path(
        'password/confirm-reset/',
        ConfirmPasswordResetView.as_view(),
        name='password-confirm-reset',
    ),
    path('phone-login/request/', RequestPhoneLoginView.as_view()),
    path('phone-login/confirm/', ConfirmPhoneLoginView.as_view()),
]
