from django.conf import settings
from django.db import connection
from django.db import models
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from rides.utils import haversine_distance
from .models import Location
from .serializers import LocationSerializer, ResolveLocationSerializer


class HealthView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        checks = {"database": False, "redis": not bool(settings.REDIS_URL)}
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                checks["database"] = cursor.fetchone()[0] == 1
        except Exception:
            pass
        if settings.REDIS_URL:
            try:
                from redis import Redis

                checks["redis"] = bool(
                    Redis.from_url(settings.REDIS_URL).ping()
                )
            except Exception:
                pass
        healthy = all(checks.values())
        return Response(
            {"status": "ok" if healthy else "unavailable", "checks": checks},
            status=200 if healthy else 503,
        )


class LocationListView(generics.ListAPIView):
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Location.objects.all().order_by(
            "country", "county", "town", "zone"
        )
        query = self.request.query_params.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                models.Q(town__icontains=query)
                | models.Q(zone__icontains=query)
                | models.Q(county__icontains=query)
            )
        return queryset[:50]


class ResolveLocationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ResolveLocationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        latitude = serializer.validated_data["latitude"]
        longitude = serializer.validated_data["longitude"]
        candidates = Location.objects.exclude(
            latitude__isnull=True
        ).exclude(longitude__isnull=True)
        nearest = None
        nearest_distance = None
        for location in candidates:
            distance = haversine_distance(
                latitude,
                longitude,
                location.latitude,
                location.longitude,
            )
            if nearest_distance is None or distance < nearest_distance:
                nearest = location
                nearest_distance = distance
        if not nearest or nearest_distance > 25:
            raise ValidationError(
                {"detail": "This location is outside the current service area."}
            )
        return Response(
            {
                **LocationSerializer(nearest).data,
                "selected_latitude": str(latitude),
                "selected_longitude": str(longitude),
                "distance_to_zone_center_km": round(nearest_distance, 2),
            }
        )
