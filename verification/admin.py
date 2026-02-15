from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Verification


@admin.register(Verification)
class VerificationAdmin(admin.ModelAdmin):
    list_display = (
        'account',
        'verification_type',
        'status',
        'submitted_at',
        'reviewed_at',
    )
    list_filter = ('verification_type', 'status')
    search_fields = ('account__email', 'document_number')
