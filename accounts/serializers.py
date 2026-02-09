from rest_framework import serializers
from .models import Account, Profile


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['avatar', 'address', 'verification_level']


class AccountSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = Account
        fields = [
            'id',
            'email',
            'phone_number',
            'first_name',
            'last_name',
            'profile',
        ]
