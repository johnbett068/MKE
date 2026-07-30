# project/urls.py

from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from core.views import HealthView

urlpatterns = [
    path('health/', HealthView.as_view(), name='health'),
    path('admin/', admin.site.urls),
    path('operations/', include('core.operations_urls')),
    path('api/v1/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/v1/accounts/', include('accounts.urls')),
    path('api/v1/locations/', include('core.urls')),
    path('api/v1/drivers/', include('drivers.urls')),
    path('api/v1/trips/', include('rides.urls')),
    path('api/v1/wallets/', include('wallets.urls')),
    path('api/v1/payments/', include('payments.urls')),
    path('api/v1/ratings/', include('ratings.urls')),
    path('api/v1/verification/', include('verification.urls')),
    path('api/v1/notifications/', include('notifications.urls')),
]
