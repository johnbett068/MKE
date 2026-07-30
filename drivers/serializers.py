from datetime import date

from rest_framework import serializers

from rides.models import Vehicle
from .models import Driver, DriverApplication, DriverDocument


class DriverApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverApplication
        fields = [
            "id", "national_id_number", "driving_license_number",
            "vehicle_type", "vehicle_make", "vehicle_model", "vehicle_year",
            "vehicle_color", "license_plate", "status", "submitted_at",
            "reviewed_at", "review_comment",
        ]
        read_only_fields = [
            "status", "submitted_at", "reviewed_at", "review_comment"
        ]

    def validate_vehicle_year(self, value):
        if value < 1990 or value > date.today().year + 1:
            raise serializers.ValidationError("Enter a valid vehicle year.")
        return value


class DriverDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverDocument
        fields = [
            "id", "document_type", "document_number", "file", "expires_at",
            "status", "reviewed_at", "review_comment", "created_at",
        ]
        read_only_fields = [
            "status", "reviewed_at", "review_comment", "created_at"
        ]

    def validate_expires_at(self, value):
        if value and value < date.today():
            raise serializers.ValidationError("Document is already expired.")
        return value


class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = [
            "id", "type", "make", "model", "year", "license_plate",
            "color", "capacity", "is_active",
        ]
        read_only_fields = ["license_plate"]


class DriverPresenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields = [
            "is_online", "is_available", "current_latitude",
            "current_longitude", "last_seen",
        ]
        read_only_fields = fields


class CoordinatesSerializer(serializers.Serializer):
    latitude = serializers.FloatField(min_value=-90, max_value=90)
    longitude = serializers.FloatField(min_value=-180, max_value=180)


class ReviewSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["approved", "rejected"])
    comment = serializers.CharField(required=False, allow_blank=True)
