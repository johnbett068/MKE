from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from rides.models import Vehicle
from .models import DriverApplication, DriverDocument
from .serializers import (
    CoordinatesSerializer,
    DriverApplicationSerializer,
    DriverDocumentSerializer,
    DriverPresenceSerializer,
    ReviewSerializer,
    VehicleSerializer,
)
from .services import DriverOnboardingService, DriverPresenceService


class DriverApplicationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        application = get_object_or_404(DriverApplication, user=request.user)
        return Response(DriverApplicationSerializer(application).data)

    def post(self, request):
        if request.user.profile.verification_level < 1:
            raise PermissionDenied("Phone verification is required.")
        existing = DriverApplication.objects.filter(user=request.user).first()
        if existing and existing.status in {"submitted", "approved"}:
            raise ValidationError(
                {"detail": "An active driver application already exists."}
            )
        serializer = DriverApplicationSerializer(
            existing,
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user, status="submitted")
        return Response(serializer.data, status=201)


class DriverDocumentListCreateView(generics.ListCreateAPIView):
    serializer_class = DriverDocumentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return DriverDocument.objects.filter(account=self.request.user)

    def perform_create(self, serializer):
        if not DriverApplication.objects.filter(user=self.request.user).exists():
            raise PermissionDenied("Submit a driver application first.")
        document_type = serializer.validated_data["document_type"]
        existing = DriverDocument.objects.filter(
            account=self.request.user,
            document_type=document_type,
        ).first()
        if existing:
            if existing.status == "approved":
                raise ValidationError(
                    {"document_type": "An approved document already exists."}
                )
            existing.delete()
        serializer.save(account=self.request.user)


class VehicleListUpdateView(generics.ListAPIView):
    serializer_class = VehicleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Vehicle.objects.filter(driver=self.request.user)


class VehicleDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = VehicleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Vehicle.objects.filter(driver=self.request.user)


class PresenceCommandView(APIView):
    permission_classes = [IsAuthenticated]
    command = None

    def post(self, request):
        try:
            if self.command in {"online", "heartbeat"}:
                serializer = CoordinatesSerializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                coordinates = serializer.validated_data
                if self.command == "online":
                    driver = DriverPresenceService.go_online(
                        request.user,
                        coordinates["latitude"],
                        coordinates["longitude"],
                    )
                else:
                    driver = DriverPresenceService.heartbeat(
                        request.user,
                        coordinates["latitude"],
                        coordinates["longitude"],
                    )
            else:
                driver = DriverPresenceService.go_offline(request.user)
        except AttributeError as exc:
            raise PermissionDenied("An approved driver profile is required.") from exc
        except PermissionError as exc:
            raise PermissionDenied(str(exc)) from exc
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        return Response(DriverPresenceSerializer(driver).data)


class DriverOnlineView(PresenceCommandView):
    command = "online"


class DriverOfflineView(PresenceCommandView):
    command = "offline"


class DriverHeartbeatView(PresenceCommandView):
    command = "heartbeat"


class AdminReviewApplicationView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, application_id):
        application = get_object_or_404(
            DriverApplication,
            pk=application_id,
            status="submitted",
        )
        serializer = ReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            DriverOnboardingService.review_application(
                application,
                request.user,
                serializer.validated_data["status"],
                serializer.validated_data.get("comment", ""),
            )
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        return Response(DriverApplicationSerializer(application).data)


class AdminReviewDocumentView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, document_id):
        document = get_object_or_404(
            DriverDocument,
            pk=document_id,
            status="pending",
        )
        serializer = ReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        DriverOnboardingService.review_document(
            document,
            request.user,
            serializer.validated_data["status"],
            serializer.validated_data.get("comment", ""),
        )
        return Response(DriverDocumentSerializer(document).data)
