from django.contrib import admin
from .models import Rating


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = (
        'rater',
        'rated_account',
        'score',
        'service',
        'reference_id',
        'created_at',
    )
    list_filter = ('score', 'service')
    search_fields = (
        'rater__email',
        'rated_account__email',
        'reference_id',
    )
