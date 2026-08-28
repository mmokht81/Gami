from django.core.exceptions import ValidationError

from rest_framework import generics
# from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from drf_spectacular.utils import extend_schema

from ..permissions import IsAdminOrSuperAdmin
from ..models import Mission
from ..mission_service import MissionService
from ..serializers import (
    MissionSerializer,
    AssignMissionSerializer,
    UserMissionSerializer,
)

class MissionCreateAPIView(generics.CreateAPIView):

    serializer_class = MissionSerializer
    permission_classes = [IsAdminOrSuperAdmin]

    @extend_schema(
        summary="Create mission",
        request=MissionSerializer,
        responses=MissionSerializer,
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class MissionDetailUpdateDeleteAPIView(
    generics.RetrieveUpdateDestroyAPIView
):

    serializer_class = MissionSerializer
    permission_classes = [IsAdminOrSuperAdmin]

    queryset = Mission.objects.all()

    @extend_schema(
        summary="Get mission",
        responses=MissionSerializer,
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Update mission",
        request=MissionSerializer,
        responses=MissionSerializer,
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @extend_schema(
        summary="Partial update mission",
        request=MissionSerializer,
        responses=MissionSerializer,
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @extend_schema(
        summary="Delete mission",
        responses=None,
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


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

