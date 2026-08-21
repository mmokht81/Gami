from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from drf_spectacular.utils import extend_schema

from ..permissions import IsAdminOrSuperAdmin
from ..models import Mission, UserMission
from ..serializers import (
    MissionSerializer,
    AssignMissionSerializer,
    UserMissionSerializer,
)

class MissionCreateAPIView(generics.CreateAPIView):

    serializer_class = MissionSerializer
    permission_classes = [IsAuthenticated]

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
    permission_classes = [IsAuthenticated]

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
        Assigns an existing mission to an active user.

        Only ADMIN and SUPERADMIN users can perform this action.
        """,
        request=AssignMissionSerializer,
        responses=UserMissionSerializer,
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

        if UserMission.objects.filter(
            user=user,
            mission=mission,
        ).exists():

            return Response(
                {
                    "detail": "این ماموریت قبلاً به این کاربر اختصاص داده شده است."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_mission = UserMission.objects.create(
            user=user,
            mission=mission,
            progress=0,
            status="PENDING",
        )

        response_serializer = UserMissionSerializer(
            user_mission
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )