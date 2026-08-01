from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from django.contrib.auth import login

from ..models import User
from ..services import OTPService
from ..serializers import (
    UserSerializer,
    RegisterSerializer,
    VerifyOTPSerializer,
)

class PhoneAPIView(generics.GenericAPIView):
    permission_classes = [AllowAny]

    def post(self, request):

        phone = request.data.get("phone_number")

        if not phone:
            return Response(
                {
                    "error": "phone_number is required"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if User.objects.filter(phone_number=phone).exists():

            return Response(
                {
                    "message": "User exists. Please login."
                },
                status=status.HTTP_200_OK
            )

        return Response(
            {
                "message": "New user. Please register."
            },
            status=status.HTTP_200_OK
        )



class RegisterAPIView(generics.CreateAPIView):

    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):

        phone = request.data.get("phone_number")
        password = request.data.get("password")


        if not phone or not password:
            return Response(
                {
                    "error": "phone_number and password are required"
                },
                status=status.HTTP_400_BAD_REQUEST
            )


        if User.objects.filter(phone_number=phone).exists():

            return Response(
                {
                    "error": "User already exists"
                },
                status=status.HTTP_400_BAD_REQUEST
            )


        user = User.objects.create_user(
            phone_number=phone,
            password=password,
        )


        otp = OTPService.create_otp(phone)


        print("=" * 50)
        print(f"REGISTER OTP : {otp.code}")
        print("=" * 50)


        return Response(
            {
                "message": "User created. OTP sent.",
                "phone_number": phone,
            },
            status=status.HTTP_201_CREATED
        )



class VerifyOTPAPIView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = VerifyOTPSerializer
    def post(self, request):

        serializer = self.get_serializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        phone = serializer.validated_data["phone_number"]
        code = serializer.validated_data["code"]

        if not phone or not code:

            return Response(
                {
                    "error": "phone_number and code are required"
                },
                status=status.HTTP_400_BAD_REQUEST
            )


        result = OTPService.verify_otp(
            phone,
            code,
        )


        if not result["success"]:

            return Response(
                result,
                status=status.HTTP_400_BAD_REQUEST
            )


        user = result["user"]

        login(
            request,
            user,
            backend="accounts.backends.PhoneBackend",
        )


        return Response(
            {
                "message": "OTP verified successfully",
                "user": UserSerializer(user).data
            },
            status=status.HTTP_200_OK
        )



class ForgotPasswordAPIView(generics.GenericAPIView):
    permission_classes = [AllowAny]


    def post(self, request):

        phone = request.data.get("phone_number")


        if not User.objects.filter(phone_number=phone).exists():

            return Response(
                {
                    "error": "User not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )


        otp = OTPService.create_otp(phone)


        print("=" * 50)
        print(f"RESET OTP : {otp.code}")
        print("=" * 50)


        return Response(
            {
                "message": "OTP sent for password reset"
            }
        )



class ResetPasswordAPIView(generics.GenericAPIView):
    permission_classes = [AllowAny]


    def post(self, request):

        phone = request.data.get("phone_number")
        password = request.data.get("password")


        try:
            user = User.objects.get(
                phone_number=phone
            )

        except User.DoesNotExist:

            return Response(
                {
                    "error": "User not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )


        user.set_password(password)
        user.save()


        return Response(
            {
                "message": "Password changed successfully"
            },
            status=status.HTTP_200_OK
        )