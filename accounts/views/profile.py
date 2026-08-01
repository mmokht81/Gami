from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema

from ..serializers import UserSerializer


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
        return super().get(request, *args, **kwargs)



    @extend_schema(
        summary="Update user profile",
        description="""
        Update user profile information.

        Editable fields:
        - first name
        - last name
        - status
        """,
        request=UserSerializer,
        responses=UserSerializer,
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)



    def get_object(self):
        return self.request.user