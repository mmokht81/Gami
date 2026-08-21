from rest_framework import serializers

from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer
)

class GamiTokenObtainPairSerializer(
    TokenObtainPairSerializer
):

    def validate(self, attrs):

        data = super().validate(attrs)

        if not self.user.is_active:
            raise serializers.ValidationError(
                "حساب کاربری شما غیرفعال است. "
                "لطفاً با مدیر HR تماس بگیرید."
            )

        return data