from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Badge, UserBadge
from ..serializers import (
    BadgeSerializer,
    UserBadgeSerializer,
    AssignBadgeSerializer,
)
from ..permissions import IsAdminOrSuperAdmin

class BadgeListCreateAPIView(APIView):
    permission_classes = [IsAdminOrSuperAdmin]

    def get(self, request):
        badges = Badge.objects.all()
        serializer = BadgeSerializer(badges, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = BadgeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )


class BadgeDetailAPIView(APIView):
    permission_classes = [IsAdminOrSuperAdmin]

    def get_object(self, pk):
        return Badge.objects.get(pk=pk)

    def get(self, request, pk):
        try:
            badge = self.get_object(pk)
        except Badge.DoesNotExist:
            return Response(
                {"detail": "Badge پیدا نشد."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = BadgeSerializer(badge)
        return Response(serializer.data)

    def put(self, request, pk):
        try:
            badge = self.get_object(pk)
        except Badge.DoesNotExist:
            return Response(
                {"detail": "Badge پیدا نشد."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = BadgeSerializer(
            badge,
            data=request.data
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    def patch(self, request, pk):
        try:
            badge = self.get_object(pk)
        except Badge.DoesNotExist:
            return Response(
                {"detail": "Badge پیدا نشد."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = BadgeSerializer(
            badge,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    def delete(self, request, pk):
        try:
            badge = self.get_object(pk)
        except Badge.DoesNotExist:
            return Response(
                {"detail": "Badge پیدا نشد."},
                status=status.HTTP_404_NOT_FOUND
            )

        badge.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )


class AssignBadgeAPIView(APIView):
    permission_classes = [IsAdminOrSuperAdmin]

    def post(self, request):
        serializer = AssignBadgeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_badge = serializer.save()

        return Response(
            UserBadgeSerializer(user_badge).data,
            status=status.HTTP_201_CREATED
        )


class MyBadgesAPIView(APIView):
    def get(self, request):
        badges = UserBadge.objects.filter(
            user=request.user
        ).select_related("badge")

        serializer = UserBadgeSerializer(
            badges,
            many=True
        )

        return Response(serializer.data)


class UserBadgesAPIView(APIView):
    permission_classes = [IsAdminOrSuperAdmin]

    def get(self, request, user_id):
        badges = UserBadge.objects.filter(
            user_id=user_id
        ).select_related("badge")

        serializer = UserBadgeSerializer(
            badges,
            many=True
        )

        return Response(serializer.data)