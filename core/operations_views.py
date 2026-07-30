from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum
from django.shortcuts import render

from drivers.models import Driver, DriverApplication, DriverDocument
from rides.models import Trip


@staff_member_required
def dashboard(request):
    active_trips = (
        Trip.objects.filter(status__in=["requested", "accepted", "in_progress"])
        .select_related("customer", "driver", "origin", "destination")
        .order_by("-created_at")[:20]
    )
    completed = Trip.objects.filter(status="completed")
    context = {
        "active_trips": active_trips,
        "online_drivers": Driver.objects.filter(is_online=True).count(),
        "available_drivers": Driver.objects.filter(
            is_online=True,
            is_available=True,
        ).count(),
        "pending_applications": DriverApplication.objects.filter(
            status="submitted"
        ).count(),
        "pending_documents": DriverDocument.objects.filter(
            status="pending"
        ).count(),
        "completed_trips": completed.count(),
        "gross_bookings": completed.aggregate(total=Sum("fare"))["total"] or 0,
    }
    return render(request, "operations/dashboard.html", context)
