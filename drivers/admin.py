from django.contrib import admin

from .models import Driver, DriverApplication, DriverDocument


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = (
        "user", "license_plate", "is_online", "is_available", "last_seen"
    )
    list_filter = ("is_online", "is_available")
    search_fields = ("user__email", "user__phone_number", "license_plate")


@admin.register(DriverApplication)
class DriverApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "user", "license_plate", "status", "submitted_at", "reviewed_at"
    )
    list_filter = ("status", "vehicle_type")
    search_fields = (
        "user__email", "user__phone_number", "national_id_number",
        "driving_license_number", "license_plate",
    )
    readonly_fields = ("submitted_at", "reviewed_at", "reviewed_by")


@admin.register(DriverDocument)
class DriverDocumentAdmin(admin.ModelAdmin):
    list_display = (
        "account", "document_type", "status", "expires_at", "created_at"
    )
    list_filter = ("document_type", "status")
    search_fields = ("account__email", "document_number")
