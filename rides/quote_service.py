from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from pricing.services import PricingService

from .models import FareQuote
from .route_service import RouteService


class QuoteService:
    @staticmethod
    @transaction.atomic
    def create_quote(
        customer,
        origin,
        destination,
        service_type,
        pickup_latitude,
        pickup_longitude,
        dropoff_latitude,
        dropoff_longitude,
    ):
        route = RouteService.calculate(
            pickup_latitude,
            pickup_longitude,
            dropoff_latitude,
            dropoff_longitude,
        )
        fare = PricingService.calculate_fare(
            city=origin.town,
            service_type=service_type,
            distance_km=route.distance_km,
            duration_minutes=route.duration_minutes,
            pickup_zone=origin.zone,
            dropoff_zone=destination.zone,
        )
        return FareQuote.objects.create(
            customer=customer,
            origin=origin,
            destination=destination,
            service_type=service_type,
            pickup_latitude=pickup_latitude,
            pickup_longitude=pickup_longitude,
            dropoff_latitude=dropoff_latitude,
            dropoff_longitude=dropoff_longitude,
            distance_km=route.distance_km,
            duration_minutes=route.duration_minutes,
            fare=fare,
            route_source=route.source,
            expires_at=timezone.now() + timedelta(minutes=5),
        )
