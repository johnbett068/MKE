from rest_framework import serializers
from .models import Verification


class VerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Verification
        fields = [
            'id',
            'verification_type',
            'document_number',
            'document_image',
            'status',
            'admin_comment',
            'submitted_at',
            'reviewed_at',
        ]


class CreateVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Verification
        fields = [
            'verification_type',
            'document_number',
            'document_image',
        ]
