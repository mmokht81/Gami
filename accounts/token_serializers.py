from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from .models import User

class GamiTokenObtainPairSerializer(TokenObtainPairSerializer):

    def validate(self, attrs):

        phone_number = attrs.get(User.USERNAME_FIELD)

        user = User.objects.filter(
            phone_number=phone_number
        ).first()

        if user and not user.is_active:
            raise serializers.ValidationError(
                "حساب کاربری شما غیرفعال است. "
                "لطفاً با مدیر HR تماس بگیرید."
            )

        try:
            data = super().validate(attrs)

        except AuthenticationFailed:
            raise serializers.ValidationError(
                "شماره موبایل یا رمز عبور صحیح نیست."
            )

        return data

