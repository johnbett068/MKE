# project/urls.py

from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # JWT endpoints
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('api/accounts/', include('accounts.urls')),
    path('api/rides/', include('rides.urls')),
    path('api/wallets/', include('wallets.urls')),
    path('api/ratings/', include('ratings.urls')),
    path('api/verification/', include('verification.urls')),
    path('api/notifications/', include('notifications.urls')),
    #path('api/pricing/', include('pricing.urls')),
]
