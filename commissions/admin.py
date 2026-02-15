# commissions/admin.py

from django.contrib import admin
from .models import CommissionRule


@admin.register(CommissionRule)
class CommissionRuleAdmin(admin.ModelAdmin):
    list_display = (
        'service_type',
        'role',
        'percentage',
        'flat_fee',
        'effective_from',
        'is_active',
    )
    list_filter = ('service_type', 'role', 'is_active')
