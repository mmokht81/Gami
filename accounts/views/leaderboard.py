from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema

from ..models import User
from ..serializers import LeaderboardSerializer


class LeaderboardAPIView(generics.ListAPIView):
    """
    API for displaying users leaderboard
    based on points and level.
    """

    serializer_class = LeaderboardSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get leaderboard",
        description="""
        Returns active users leaderboard.

        Ranking is based on:
        - Higher points
        - Higher level
        - Earlier registration date
        """,
        responses=LeaderboardSerializer(many=True),
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return User.objects.filter(
            is_active=True,
        ).order_by(
            "-points",
            "-level",
            "date_joined",
        )