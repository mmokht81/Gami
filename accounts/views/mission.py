from rest_framework import generics
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
    """
    API for retrieving, updating and deleting a mission.
    """

    serializer_class = MissionSerializer
    permission_classes = [IsAdminOrSuperAdmin]

    @extend_schema(
        summary="Get, update or delete mission",
        description="""
Returns, updates or deletes a specific mission.

Supported methods:
- GET
- PUT
- PATCH
- DELETE
""",
        responses=MissionSerializer,
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return Mission.objects.all()