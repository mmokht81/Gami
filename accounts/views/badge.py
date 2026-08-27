from django.shortcuts import get_object_or_404

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import Badge, UserBadge, User
from ..permissions import IsAdminOrSuperAdmin
from ..serializers import (
    BadgeSerializer,
    UserBadgeSerializer,
    AssignBadgeSerializer,
)


class BadgeListCreateAPIView(generics.ListCreateAPIView):
    """
    GET:
        Return all active badges.

    POST:
        Create a new badge.
        Admin/SuperAdmin only.
    """

    serializer_class = BadgeSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdminOrSuperAdmin()]

        return [IsAuthenticated()]

    def get_queryset(self):
        return Badge.objects.filter(
            is_active=True
        ).order_by("id")


class BadgeDetailAPIView(
    generics.RetrieveUpdateDestroyAPIView
):
    """
    GET:
        Return badge details.

    PUT/PATCH/DELETE:
        Admin/SuperAdmin only.
    """

    queryset = Badge.objects.all()
    serializer_class = BadgeSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]

        return [IsAdminOrSuperAdmin()]


class MyBadgesAPIView(generics.ListAPIView):
    """
    Return badges belonging to the authenticated user.
    """

    serializer_class = UserBadgeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            UserBadge.objects
            .filter(user=self.request.user)
            .select_related("badge")
            .order_by("-assigned_at")
        )


class UserBadgesAPIView(generics.ListAPIView):
    """
    Return badges of a specific user.

    Admin/SuperAdmin only.
    """

    serializer_class = UserBadgeSerializer
    permission_classes = [IsAdminOrSuperAdmin]

    def get_queryset(self):
        user_id = self.kwargs["user_id"]

        return (
            UserBadge.objects
            .filter(user_id=user_id)
            .select_related("badge")
            .order_by("-assigned_at")
        )


class AssignBadgeAPIView(generics.GenericAPIView):
    """
    Assign a badge to a user.

    Admin/SuperAdmin only.
    """

    permission_classes = [IsAdminOrSuperAdmin]
    serializer_class = AssignBadgeSerializer

    def post(self, request, badge_id, user_id):

        badge = get_object_or_404(
            Badge,
            id=badge_id,
            is_active=True,
        )

        user = get_object_or_404(
            User,
            id=user_id,
            is_active=True,
        )

        serializer = self.get_serializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        reason = serializer.validated_data.get(
            "reason"
        )

        user_badge, created = (
            UserBadge.objects.get_or_create(
                user=user,
                badge=badge,
                defaults={
                    "reason": reason,
                },
            )
        )

        response_serializer = UserBadgeSerializer(
            user_badge
        )

        return Response(
            response_serializer.data,
            status=(
                status.HTTP_201_CREATED
                if created
                else status.HTTP_200_OK
            ),
        )