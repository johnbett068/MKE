from django.urls import path
from .views import MyWalletsView, WalletTransactionsView

urlpatterns = [
    path('my-wallets/', MyWalletsView.as_view()),
    path('wallets/<int:wallet_id>/transactions/', WalletTransactionsView.as_view()),
]
