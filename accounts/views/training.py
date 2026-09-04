from django.core.exceptions import ValidationError

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema

from ..models import (
    TrainingCourse,
    TrainingSection,
)
from ..serializers import (
    TrainingCourseSerializer,
    UserTrainingSerializer,
)
from ..training_service import TrainingService


class TrainingListAPIView(generics.ListAPIView):
    """
    List all active training courses.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = TrainingCourseSerializer

    def get_queryset(self):
        return (
            TrainingCourse.objects
            .filter(
                is_active=True,
            )
            .prefetch_related(
                "sections",
            )
            .order_by(
                "-created_at"
            )
        )

    @extend_schema(
        summary="List training courses",
        description="Return all active training courses.",
        responses=TrainingCourseSerializer(many=True),
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class TrainingDetailAPIView(generics.RetrieveAPIView):
    """
    Return details of one active training course.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = TrainingCourseSerializer

    lookup_url_kwarg = "training_id"

    def get_queryset(self):
        return (
            TrainingCourse.objects
            .filter(
                is_active=True,
            )
            .prefetch_related(
                "sections",
            )
        )

    @extend_schema(
        summary="Training course detail",
        description="Return details of an active training course.",
        responses=TrainingCourseSerializer,
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class TrainingEnrollAPIView(generics.GenericAPIView):
    """
    Enroll the authenticated user in a training course.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = UserTrainingSerializer

    @extend_schema(
        summary="Enroll in training course",
        description=(
            "Enroll the authenticated user in an active "
            "training course."
        ),
        responses={
            201: UserTrainingSerializer,
            400: None,
        },
    )
    def post(self, request, training_id):

        try:
            course = TrainingCourse.objects.get(
                id=training_id,
                is_active=True,
            )

        except TrainingCourse.DoesNotExist:
            return Response(
                {
                    "detail": "دوره مورد نظر پیدا نشد."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            user_training, created = (
                TrainingService.enroll_user(
                    user=request.user,
                    course=course,
                )
            )

        except ValidationError as exc:
            return Response(
                {
                    "detail": str(exc)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            UserTrainingSerializer(
                user_training
            ).data,
            status=(
                status.HTTP_201_CREATED
                if created
                else status.HTTP_200_OK
            ),
        )


class TrainingSectionStartAPIView(generics.GenericAPIView):
    """
    Start a training section.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = UserTrainingSerializer

    @extend_schema(
        summary="Start training section",
        description=(
            "Start a section of an enrolled training course. "
            "Starting a section automatically updates progress."
        ),
        responses={
            200: UserTrainingSerializer,
            201: UserTrainingSerializer,
            400: None,
        },
    )
    def post(
        self,
        request,
        training_id,
        section_id,
    ):

        try:
            course = TrainingCourse.objects.get(
                id=training_id,
                is_active=True,
            )

        except TrainingCourse.DoesNotExist:
            return Response(
                {
                    "detail": "دوره مورد نظر پیدا نشد."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            section = TrainingSection.objects.get(
                id=section_id,
                course=course,
            )

        except TrainingSection.DoesNotExist:
            return Response(
                {
                    "detail": "بخش مورد نظر پیدا نشد."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            user_training, reward, created = (
                TrainingService.start_section(
                    user=request.user,
                    course=course,
                    section=section,
                )
            )

        except ValidationError as exc:
            return Response(
                {
                    "detail": str(exc)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        response_data = UserTrainingSerializer(
            user_training
        ).data

        if reward is not None:
            response_data["rewards"] = {
                "points": reward["points"],
                "level_up": (
                    {
                        "from": reward["level_up"].from_level,
                        "to": reward["level_up"].to_level,
                    }
                    if reward["level_up"]
                    else None
                ),
                "badges": [],
            }

        return Response(
            response_data,
            status=status.HTTP_200_OK,
        )


class MyTrainingListAPIView(generics.ListAPIView):

    permission_classes = [IsAuthenticated]
    serializer_class = UserTrainingSerializer

    def get_queryset(self):
        return TrainingService.get_user_trainings(
            self.request.user
        )

    @extend_schema(
        summary="My trainings",
        description=(
            "Return all training courses in which "
            "the authenticated user is enrolled."
        ),
        responses=UserTrainingSerializer(many=True),
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class MyTrainingDetailAPIView(generics.GenericAPIView):
    """
    Return the authenticated user's progress in one course.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = UserTrainingSerializer

    @extend_schema(
        summary="My training detail",
        description=(
            "Return the authenticated user's enrollment "
            "and progress for a specific training course."
        ),
        responses=UserTrainingSerializer,
    )
    def get(self, request, training_id):

        try:
            course = TrainingCourse.objects.get(
                id=training_id,
            )

        except TrainingCourse.DoesNotExist:
            return Response(
                {
                    "detail": "دوره مورد نظر پیدا نشد."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            user_training = (
                TrainingService.get_user_training(
                    user=request.user,
                    course=course,
                )
            )

        except ValidationError as exc:
            return Response(
                {
                    "detail": str(exc)
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            UserTrainingSerializer(
                user_training
            ).data,
            status=status.HTTP_200_OK,
        )



