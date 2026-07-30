from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from wallets.models import Wallet

from .models import Trip, TripOffer
from .serializers import (
    CancelTripSerializer,
    CompleteTripSerializer,
    FareQuoteRequestSerializer,
    FareQuoteSerializer,
    StartTripSerializer,
    TripOfferSerializer,
    TripSerializer,
)
from .services import DispatchService, RideService, is_approved_driver


def participant_trip(user, trip_id):
    return get_object_or_404(
        Trip.objects.select_related(
            "customer", "driver", "origin", "destination", "ride_details"
        ).filter(Q(customer=user) | Q(driver=user)),
        pk=trip_id,
    )


class FareQuoteCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = FareQuoteRequestSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        try:
            quote = serializer.save()
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        return Response(FareQuoteSerializer(quote).data, status=201)


class TripListCreateView(generics.ListCreateAPIView):
    serializer_class = TripSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Trip.objects.filter(
                Q(customer=self.request.user) | Q(driver=self.request.user)
            )
            .select_related("origin", "destination", "ride_details")
            .order_by("-created_at")
        )

    def perform_create(self, serializer):
        serializer.save(customer=self.request.user)


class TripDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, trip_id):
        trip = participant_trip(request.user, trip_id)
        return Response(TripSerializer(trip, context={"request": request}).data)


class DriverOfferListView(generics.ListAPIView):
    serializer_class = TripOfferSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if not is_approved_driver(self.request.user):
            raise PermissionDenied("An approved driver role is required.")
        TripOffer.objects.filter(
            driver=self.request.user,
            status="pending",
            expires_at__lte=timezone.now(),
        ).update(status="expired")
        return (
            TripOffer.objects.filter(
                driver=self.request.user,
                status="pending",
                expires_at__gt=timezone.now(),
            )
            .select_related(
                "trip", "trip__origin", "trip__destination", "trip__ride_details"
            )
            .order_by("expires_at")
        )


class OfferCommandView(APIView):
    permission_classes = [IsAuthenticated]
    command = None

    def post(self, request, offer_id):
        try:
            if self.command == "accept":
                trip = DispatchService.accept_offer(offer_id, request.user)
                return Response(
                    TripSerializer(trip, context={"request": request}).data
                )
            offer = get_object_or_404(
                TripOffer,
                pk=offer_id,
                driver=request.user,
            )
            DispatchService.reject_offer(offer, request.user)
            return Response(TripOfferSerializer(offer).data)
        except TripOffer.DoesNotExist:
            return Response(
                {"detail": "Offer not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except PermissionError as exc:
            raise PermissionDenied(str(exc)) from exc
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)}) from exc


class AcceptOfferView(OfferCommandView):
    command = "accept"


class RejectOfferView(OfferCommandView):
    command = "reject"


class TripCommandView(APIView):
    permission_classes = [IsAuthenticated]
    command = None

    def post(self, request, trip_id):
        try:
            if self.command == "start":
                payload = StartTripSerializer(data=request.data)
                payload.is_valid(raise_exception=True)
                trip = RideService.start_trip(
                    trip_id,
                    request.user,
                    payload.validated_data["pin"],
                )
            elif self.command == "arrived":
                trip = RideService.mark_arrived(trip_id, request.user)
            elif self.command == "complete":
                payload = CompleteTripSerializer(data=request.data)
                payload.is_valid(raise_exception=True)
                trip = RideService.complete_trip(
                    trip_id,
                    request.user,
                    payload.validated_data["distance_km"],
                    payload.validated_data["duration_minutes"],
                )
            elif self.command == "cancel":
                payload = CancelTripSerializer(data=request.data)
                payload.is_valid(raise_exception=True)
                trip = RideService.cancel_trip(
                    trip_id,
                    request.user,
                    payload.validated_data.get("reason", ""),
                )
            else:
                raise RuntimeError("Unsupported trip command.")
        except Trip.DoesNotExist:
            return Response(
                {"detail": "Trip not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except PermissionError as exc:
            raise PermissionDenied(str(exc)) from exc
        except (ValueError, Wallet.DoesNotExist) as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        return Response(TripSerializer(trip, context={"request": request}).data)


class StartTripView(TripCommandView):
    command = "start"


class ArrivedTripView(TripCommandView):
    command = "arrived"


class CompleteTripView(TripCommandView):
    command = "complete"


class CancelTripView(TripCommandView):
    command = "cancel"
