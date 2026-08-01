from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema

from ..models import UserMission
from ..serializers import UserMissionSerializer


class MissionListAPIView(generics.ListAPIView):
    """
    API for retrieving user's missions list.
    """

    serializer_class = UserMissionSerializer
    permission_classes = [IsAuthenticated]


    @extend_schema(
        summary="Get user missions",
        description="""
        Returns missions assigned to the authenticated user.

        Includes:
        - Mission information
        - Progress percentage
        - Mission status
        - Creation and update dates
        """,
        responses=UserMissionSerializer(many=True),
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


    def get_queryset(self):
        return (
            UserMission.objects
            .filter(
                user=self.request.user
            )
            .select_related(
                "mission"
            )
            .order_by(
                "-created_at"
            )
        )



class MissionDetailAPIView(generics.RetrieveAPIView):
    """
    API for retrieving a single user mission.
    """

    serializer_class = UserMissionSerializer
    permission_classes = [IsAuthenticated]


    @extend_schema(
        summary="Get mission detail",
        description="""
        Returns details of a specific mission
        assigned to the authenticated user.

        Includes:
        - Mission name
        - Description
        - Points
        - Progress
        - Status
        """,
        responses=UserMissionSerializer,
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


    def get_queryset(self):
        return (
            UserMission.objects
            .filter(
                user=self.request.user
            )
            .select_related(
                "mission"
            )
        )