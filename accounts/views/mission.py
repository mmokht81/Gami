from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema

from ..models import (
    UserMission,
    Mission,
)
from ..serializers import (
    UserMissionSerializer,
    MissionSerializer,
)
from ..permissions import IsAdminOrSuperAdmin
from ..automatic_mission_service import AutomaticMissionService

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
        AutomaticMissionService.sync_all_for_user(
            self.request.user
        )

        return UserMission.objects.filter(
            user=self.request.user
        ).select_related(
            "mission"
        ).order_by(
            "-created_at"
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

class MissionManagementListAPIView(
    generics.ListCreateAPIView
):
    """
    API for listing and creating missions.
    """

    serializer_class = MissionSerializer
    permission_classes = [IsAdminOrSuperAdmin]

    @extend_schema(
        summary="List and create missions",
        description="""
Returns all missions and allows creating a new mission.

Supported methods:
- GET
- POST
""",
        responses=MissionSerializer(many=True),
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return Mission.objects.all()

class MissionManagementDetailAPIView(
    generics.RetrieveUpdateDestroyAPIView
):
    serializer_class = MissionSerializer
    permission_classes = [IsAdminOrSuperAdmin]

    def get_queryset(self):
        return Mission.objects.all()

    def update(self, request, *args, **kwargs):
        mission = self.get_object()

        if mission.type == "AUTOMATIC":
            return Response(
                {
                    "detail": (
                        "ماموریت‌های خودکار قابل ویرایش نیستند."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        return super().update(
            request,
            *args,
            **kwargs,
        )

    def destroy(self, request, *args, **kwargs):
        mission = self.get_object()

        if mission.type == "AUTOMATIC":
            return Response(
                {
                    "detail": (
                        "ماموریت‌های خودکار قابل حذف نیستند."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        return super().destroy(
            request,
            *args,
            **kwargs,
        )