from django.core.exceptions import ValidationError

from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status

from drf_spectacular.utils import extend_schema

from ..permissions import IsAdminOrSuperAdmin
from ..models import Mission, UserMission
from ..mission_service import MissionService
from ..serializers import (
    AssignMissionSerializer,
    UserMissionSerializer,
    MissionAssignmentSerializer,
    MissionAssignmentProgressSerializer,
)


class MissionAssignAPIView(generics.CreateAPIView):

    serializer_class = AssignMissionSerializer
    permission_classes = [IsAdminOrSuperAdmin]

    @extend_schema(
        summary="Assign mission to user",
        description="""
        Assigns an existing active mission to an active user.

        Only ADMIN and SUPERADMIN users can perform this action.

        A mission cannot be assigned to the same user twice.
        """,
        request=AssignMissionSerializer,
        responses={
            201: UserMissionSerializer,
            200: UserMissionSerializer,
            400: None,
            404: None,
        },
    )
    def post(self, request, *args, **kwargs):

        mission_id = kwargs.get("mission_id")

        try:
            mission = Mission.objects.get(
                id=mission_id,
                is_active=True,
            )
        except Mission.DoesNotExist:
            return Response(
                {
                    "detail": "ماموریت مورد نظر پیدا نشد."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.get_serializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        user = serializer.validated_data["user_id"]

        try:
            user_mission, created = (
                MissionService.assign_mission(
                    user=user,
                    mission=mission,
                )
            )

        except ValidationError as exc:
            return Response(
                {
                    "detail": str(exc)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        response_serializer = UserMissionSerializer(
            user_mission
        )

        return Response(
            response_serializer.data,
            status=(
                status.HTTP_201_CREATED
                if created
                else status.HTTP_200_OK
            ),
        )

class MissionAssignmentListAPIView(generics.ListAPIView):
    """
    API for listing HR-assigned missions.

    Only ADMIN and SUPERADMIN users can access this endpoint.
    """

    serializer_class = MissionAssignmentSerializer
    permission_classes = [IsAdminOrSuperAdmin]

    @extend_schema(
        summary="List HR mission assignments",
        description="""
        Returns all missions assigned by HR to users.

        Only HR/Admin users can access this endpoint.

        Includes:
        - User information
        - Mission information
        - Progress
        - Mission status
        - Creation and update dates
        """,
        responses=UserMissionSerializer(many=True),
    )
    def get_queryset(self):
        return (
            UserMission.objects
            .select_related(
                "user",
                "mission",
            )
            .order_by(
                "-created_at"
            )
        )

class MissionAssignmentProgressAPIView(
    generics.UpdateAPIView
):
    """
    API for updating the progress of
    a mission assigned to a user.

    Only ADMIN and SUPERADMIN users can
    update mission progress.
    """

    serializer_class = MissionAssignmentProgressSerializer
    permission_classes = [IsAdminOrSuperAdmin]

    http_method_names = ["patch"]

    @extend_schema(
        summary="Update assigned mission progress",
        description="""
        Updates the progress of a mission
        assigned to a user.

        Only ADMIN and SUPERADMIN users can
        perform this action.

        The mission status is automatically
        updated based on progress:

        - 0 -> PENDING
        - 1-99 -> IN_PROGRESS
        - 100 -> COMPLETED
        """,
        request=MissionAssignmentProgressSerializer,
        responses=MissionAssignmentSerializer,
    )
    def patch(self, request, *args, **kwargs):

        user_mission = self.get_object()

        serializer = self.get_serializer(
            user_mission,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True
        )

        progress = serializer.validated_data[
            "progress"
        ]

        try:
            updated_user_mission, reward = (
                MissionService.update_progress(
                    user=user_mission.user,
                    mission=user_mission.mission,
                    progress=progress,
                )
            )

        except ValidationError as exc:
            return Response(
                {
                    "detail": str(exc)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        response_serializer = (
            MissionAssignmentSerializer(
                updated_user_mission
            )
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK,
        )

    def get_queryset(self):

        return (
            UserMission.objects
            .select_related(
                "user",
                "mission",
            )
        )

