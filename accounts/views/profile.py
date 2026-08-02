from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema

from ..serializers import (
    UserSerializer,
    ProfileUpdateSerializer,
)

class ProfileAPIView(generics.RetrieveUpdateAPIView):

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]


    @extend_schema(
        summary="Get user profile",
        description="""
        Returns authenticated user's profile information.

        Includes:
        - phone number
        - name
        - points
        - level
        - role
        - status
        """,
        responses=UserSerializer,
    )
    def get(self, request, *args, **kwargs):
        print("=" * 50)
        print(request.headers.get("Authorization"))
        print(request.user)
        print(request.user.is_authenticated)
        print("=" * 50)

        return super().get(request, *args, **kwargs)

    def get_serializer_class(self):

        if self.request.method in ["PUT", "PATCH"]:
            return ProfileUpdateSerializer

        return UserSerializer

    @extend_schema(
        summary="Update user profile",
        description="""
        Update user profile information.

        Editable fields:
        - first name
        - last name
        - status
        """,
        request=ProfileUpdateSerializer,
        responses=UserSerializer,
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)



    def get_object(self):
        return self.request.user