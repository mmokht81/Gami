from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from rest_framework_simplejwt.tokens import RefreshToken
from ..models import User
from ..serializers import (
    UserSerializer,
    PhoneAPISerializer,
    RegisterAPISerializer,
    VerifyOTPAPISerializer,
    ForgotPasswordAPISerializer,
    ResetPasswordAPISerializer,
)
from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
)
from ..services import OTPService


class PhoneAPIView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = PhoneAPISerializer

    @extend_schema(
        summary="Check phone number",
        description="""
    Checks whether a phone number already exists.

    Possible responses:

    - Existing user → Login
    - New user → Register
    """,
        request=PhoneAPISerializer,
        responses={
            200: OpenApiResponse(
                description="Phone checked successfully."
            ),
            400: OpenApiResponse(
                description="Validation error."
            ),
        },
    )

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone_number"]

        if User.objects.filter(phone_number=phone).exists():
            return Response(
                {
                    "message": "User exists. Please login."
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "message": "New user. Please register."
            },
            status=status.HTTP_200_OK,
        )

class RegisterAPIView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = RegisterAPISerializer

    @extend_schema(
        summary="Register user",
        description="""
    Creates a new user account and sends an OTP code.

    Required:

    - phone_number
    - password
    """,
        request=RegisterAPISerializer,
        responses={
            201: OpenApiResponse(
                description="User created successfully. OTP sent."
            ),
            400: OpenApiResponse(
                description="Validation error."
            ),
        },
    )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone_number"]

        if User.objects.filter(phone_number=phone).exists():
            return Response(
                {
                    "error": "User already exists"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer.save()

        otp = OTPService.create_otp(phone)

        print("=" * 50)
        print(f"REGISTER OTP : {otp.code}")
        print("=" * 50)

        return Response(
            {
                "message": "User created. OTP sent.",
                "phone_number": phone,
            },
            status=status.HTTP_201_CREATED,
        )

class VerifyOTPAPIView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = VerifyOTPAPISerializer

    @extend_schema(
        summary="Verify OTP",
        description="""
    Verifies the OTP code.

    If the code is correct:

    - phone number becomes verified
    - user is authenticated
    """,
        request=VerifyOTPAPISerializer,
        responses={
            200: OpenApiResponse(
                description="OTP verified successfully. JWT tokens returned."
            ),
            400: OpenApiResponse(
                description="Invalid or expired OTP."
            ),
        },
    )

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone_number"]
        code = serializer.validated_data["code"]

        result = OTPService.verify_otp(
            phone,
            code,
        )

        if not result["success"]:
            return Response(
                result,
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = result["user"]

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "message": "OTP verified successfully",

                "access": str(refresh.access_token),

                "refresh": str(refresh),

                "user": UserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )

class ForgotPasswordAPIView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = ForgotPasswordAPISerializer

    @extend_schema(
        summary="Forgot password",
        description="""
    Sends an OTP code for password recovery.
    """,
        request=ForgotPasswordAPISerializer,
        responses={
            200: OpenApiResponse(
                description="OTP sent."
            ),
            404: OpenApiResponse(
                description="User not found."
            ),
        },
    )

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone_number"]

        if not User.objects.filter(phone_number=phone).exists():
            return Response(
                {
                    "error": "User not found"
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        otp = OTPService.create_otp(phone)

        print("=" * 50)
        print(f"RESET OTP : {otp.code}")
        print("=" * 50)

        return Response(
            {
                "message": "OTP sent for password reset"
            },
            status=status.HTTP_200_OK,
        )

class ResetPasswordAPIView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = ResetPasswordAPISerializer

    @extend_schema(
        summary="Reset password",
        description="""
    Changes the user's password.
    """,
        request=ResetPasswordAPISerializer,
        responses={
            200: OpenApiResponse(
                description="Password changed."
            ),
        },
    )

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone_number"]
        password = serializer.validated_data["password"]

        try:
            user = User.objects.get(
                phone_number=phone,
            )
        except User.DoesNotExist:
            return Response(
                {
                    "error": "User not found"
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        user.set_password(password)
        user.save()

        return Response(
            {
                "message": "Password changed successfully"
            },
            status=status.HTTP_200_OK,
        )