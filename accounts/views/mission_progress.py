from django.core.exceptions import ValidationError

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema

from ..models import Mission
from ..mission_service import MissionService
from ..serializers import UserMissionSerializer


class MissionStartAPIView(generics.GenericAPIView):

    permission_classes = [IsAuthenticated]
    serializer_class = UserMissionSerializer

    @extend_schema(
        summary="Start mission",
        description="Start a mission assigned to the authenticated user.",
        responses=UserMissionSerializer,
    )
    def post(self, request, mission_id):

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

        try:
            user_mission, created = MissionService.start_mission(
                user=request.user,
                mission=mission,
            )
        except ValidationError as exc:
            return Response(
                {
                    "detail": str(exc)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            UserMissionSerializer(user_mission).data,
            status=(
                status.HTTP_201_CREATED
                if created
                else status.HTTP_200_OK
            ),
        )


class MissionProgressAPIView(generics.GenericAPIView):

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Update mission progress",
        description=(
            "Update progress of a mission for "
            "the authenticated user."
        ),
        request={
            "type": "object",
            "properties": {
                "progress": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 100,
                }
            },
            "required": ["progress"],
        },
        responses=UserMissionSerializer,
    )
    def patch(self, request, mission_id):

        progress = request.data.get("progress")

        if progress is None:
            return Response(
                {
                    "detail": "progress الزامی است."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            progress = int(progress)
        except (TypeError, ValueError):
            return Response(
                {
                    "detail": "progress باید عدد صحیح باشد."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

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

        try:
            user_mission = MissionService.update_progress(
                user=request.user,
                mission=mission,
                progress=progress,
            )
        except ValidationError as exc:
            return Response(
                {
                    "detail": str(exc)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            UserMissionSerializer(user_mission).data,
            status=status.HTTP_200_OK,
        )


class MissionCompleteAPIView(generics.GenericAPIView):

    permission_classes = [IsAuthenticated]
    serializer_class = UserMissionSerializer

    @extend_schema(
        summary="Complete mission",
        description=(
            "Complete a mission for the authenticated user. "
            "Points are awarded automatically."
        ),
        responses=UserMissionSerializer,
    )
    def post(self, request, mission_id):

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

        try:
            user_mission = MissionService.complete_mission(
                user=request.user,
                mission=mission,
            )
        except ValidationError as exc:
            return Response(
                {
                    "detail": str(exc)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            UserMissionSerializer(user_mission).data,
            status=status.HTTP_200_OK,
        )