from rest_framework import serializers
from .models import Vehicle, Trip, TripEvent

class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ['id', 'driver', 'type', 'license_plate', 'color', 'is_active']


class TripSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trip
        fields = [
            'id', 'customer', 'driver', 'vehicle',
            'trip_type', 'status', 'origin', 'destination',
            'fare', 'distance_km', 'created_at', 'updated_at'
        ]


class TripEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = TripEvent
        fields = ['id', 'trip', 'status', 'timestamp', 'note']
