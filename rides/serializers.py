from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from .models import FareQuote, Ride, Trip, TripEvent, TripOffer
from .quote_service import QuoteService
from .security import hash_start_pin, start_pin_for_trip
from .services import DispatchService


class FareQuoteRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = FareQuote
        fields = [
            "origin", "destination", "service_type", "pickup_latitude",
            "pickup_longitude", "dropoff_latitude", "dropoff_longitude",
        ]

    def create(self, validated_data):
        return QuoteService.create_quote(
            customer=self.context["request"].user,
            **validated_data,
        )


class FareQuoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = FareQuote
        fields = [
            "id", "origin", "destination", "service_type",
            "pickup_latitude", "pickup_longitude", "dropoff_latitude",
            "dropoff_longitude", "distance_km", "duration_minutes", "fare",
            "route_source", "expires_at", "created_at",
        ]


class RideDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ride
        fields = [
            "pickup_latitude", "pickup_longitude", "dropoff_latitude",
            "dropoff_longitude", "total_fare", "commission_amount",
            "driver_payout",
        ]
        read_only_fields = fields


class TripSerializer(serializers.ModelSerializer):
    ride_details = RideDetailsSerializer(read_only=True)
    quote_id = serializers.IntegerField(write_only=True, required=True)
    start_pin = serializers.SerializerMethodField()

    class Meta:
        model = Trip
        fields = [
            "id", "customer", "driver", "vehicle", "trip_type", "status",
            "origin", "destination", "payment_method", "quoted_fare", "fare",
            "distance_km", "ride_details", "quote_id", "start_pin",
            "accepted_at", "started_at", "completed_at", "cancelled_at",
            "arrived_at",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "customer", "driver", "vehicle", "trip_type", "status", "origin",
            "destination", "quoted_fare", "fare", "distance_km",
            "accepted_at", "started_at", "completed_at", "cancelled_at",
            "arrived_at",
        ]

    def get_start_pin(self, trip):
        request = self.context.get("request")
        if (
            request
            and request.user.id == trip.customer_id
            and trip.status in {"requested", "accepted"}
        ):
            return start_pin_for_trip(trip.id)
        return None

    def validate_quote_id(self, value):
        request = self.context.get("request")
        quote = FareQuote.objects.filter(
            pk=value,
            customer=request.user,
        ).first()
        if not quote or not quote.is_usable:
            raise serializers.ValidationError(
                "This quote is invalid, expired, or already used."
            )
        return value

    @transaction.atomic
    def create(self, validated_data):
        quote_id = validated_data.pop("quote_id")
        customer = validated_data.pop("customer")
        quote = FareQuote.objects.select_for_update().get(
            pk=quote_id,
            customer=customer,
        )
        if not quote.is_usable:
            raise serializers.ValidationError(
                {"quote_id": "This quote is expired or already used."}
            )
        trip = Trip.objects.create(
            customer=customer,
            trip_type=quote.service_type,
            origin=quote.origin,
            destination=quote.destination,
            quoted_fare=quote.fare,
            distance_km=quote.distance_km,
            **validated_data,
        )
        pin = start_pin_for_trip(trip.id)
        Ride.objects.create(
            trip=trip,
            city=quote.origin.town,
            pickup_latitude=quote.pickup_latitude,
            pickup_longitude=quote.pickup_longitude,
            dropoff_latitude=quote.dropoff_latitude,
            dropoff_longitude=quote.dropoff_longitude,
            start_pin_hash=hash_start_pin(trip.id, pin),
        )
        quote.consumed_at = timezone.now()
        quote.save(update_fields=["consumed_at"])
        TripEvent.objects.create(trip=trip, status="requested")
        DispatchService.create_offers(trip)
        return trip


class StartTripSerializer(serializers.Serializer):
    pin = serializers.RegexField(r"^\d{4}$")


class CompleteTripSerializer(serializers.Serializer):
    distance_km = serializers.DecimalField(
        max_digits=8, decimal_places=2, min_value=0
    )
    duration_minutes = serializers.DecimalField(
        max_digits=8, decimal_places=2, min_value=0
    )


class CancelTripSerializer(serializers.Serializer):
    reason = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
    )


class TripOfferSerializer(serializers.ModelSerializer):
    trip = TripSerializer(read_only=True)
    expires_in_seconds = serializers.SerializerMethodField()

    class Meta:
        model = TripOffer
        fields = [
            "id", "trip", "distance_to_pickup_km", "status", "expires_at",
            "expires_in_seconds", "created_at",
        ]

    def get_expires_in_seconds(self, offer):
        return max(0, int((offer.expires_at - timezone.now()).total_seconds()))


class TripEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = TripEvent
        fields = ["id", "status", "timestamp", "note"]
