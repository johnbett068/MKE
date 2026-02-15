from rest_framework import serializers
from .models import Rating


class RatingSerializer(serializers.ModelSerializer):
    rater = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Rating
        fields = [
            'id',
            'rater',
            'score',
            'comment',
            'service',
            'reference_id',
            'created_at',
        ]


class CreateRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = [
            'rated_account',
            'score',
            'comment',
            'service',
            'reference_id',
        ]

    def validate_score(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value
