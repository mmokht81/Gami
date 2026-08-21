from rest_framework import generics

from ..models import User
from ..serializers import UserAdminSerializer
from ..permissions import IsAdminOrSuperAdmin

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
)


@extend_schema_view(
    get=extend_schema(
        summary="List users",
        description="""
        Returns a list of all users.

        Only ADMIN and SUPERADMIN users can access this endpoint.
        """
    ),
    post=extend_schema(
        summary="Create user",
        description="""
        Creates a new user.

        Only ADMIN and SUPERADMIN users can perform this action.
        """
    ),
)
class UserAdminListCreateAPIView(
    generics.ListCreateAPIView
):

    queryset = User.objects.all().order_by("-date_joined")

    serializer_class = UserAdminSerializer

    permission_classes = [
        IsAdminOrSuperAdmin
    ]


@extend_schema_view(
    get=extend_schema(
        summary="Get user",
        description="""
        Returns details of a specific user.

        Only ADMIN and SUPERADMIN users can access this endpoint.
        """
    ),
    put=extend_schema(
        summary="Update user",
        description="""
        Updates all editable fields of a user.

        Only ADMIN and SUPERADMIN users can perform this action.
        """
    ),
    patch=extend_schema(
        summary="Partial update user",
        description="""
        Partially updates a user.

        Only ADMIN and SUPERADMIN users can perform this action.
        """
    ),
    delete=extend_schema(
        summary="Delete user",
        description="""
        Deletes a user.

        Only ADMIN and SUPERADMIN users can perform this action.
        """
    ),
)
class UserAdminDetailAPIView(
    generics.RetrieveUpdateDestroyAPIView
):

    queryset = User.objects.all()

    serializer_class = UserAdminSerializer

    permission_classes = [
        IsAdminOrSuperAdmin
    ]