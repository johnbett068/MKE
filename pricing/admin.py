# pricing/admin.py

from django.contrib import admin
from .models import PricingRule, Zone, SurgePricing


@admin.register(PricingRule)
class PricingRuleAdmin(admin.ModelAdmin):
    list_display = (
        'city',
        'service_type',
        'base_fare',
        'per_km_rate',
        'per_minute_rate',
        'active',
    )
    list_filter = ('city', 'service_type', 'active')


@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'extra_fee', 'active')
    list_filter = ('city', 'active')


@admin.register(SurgePricing)
class SurgePricingAdmin(admin.ModelAdmin):
    list_display = (
        'city',
        'multiplier',
        'start_time',
        'end_time',
        'active',
    )
    list_filter = ('city', 'active')
