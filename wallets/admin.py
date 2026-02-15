from django.contrib import admin
from .models import Wallet, Transaction


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = (
        'account',
        'role',
        'available_balance',
        'pending_balance',
        'debt_balance',
        'is_active',
    )
    list_filter = ('role', 'is_active')
    search_fields = ('account__email',)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        'wallet',
        'transaction_type',
        'amount',
        'service',
        'reference_id',
        'created_at',
    )
    list_filter = ('transaction_type', 'service')
    search_fields = ('reference_id',)
