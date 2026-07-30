from rest_framework import serializers

from .models import Location


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = [
            "id", "country", "county", "town", "zone", "latitude", "longitude"
        ]


class ResolveLocationSerializer(serializers.Serializer):
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6)
