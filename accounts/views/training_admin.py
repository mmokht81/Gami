from django.core.exceptions import ValidationError

from rest_framework import generics, status
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema

from ..permissions import IsAdminOrSuperAdmin
from ..models import TrainingCourse, TrainingSection
from ..serializers import (
    TrainingCourseSerializer,
    TrainingSectionSerializer,
)


class TrainingManagementListCreateAPIView(
    generics.ListCreateAPIView
):
    """
    List and create training courses.

    Only ADMIN and SUPERADMIN users can access this endpoint.
    """

    permission_classes = [IsAdminOrSuperAdmin]
    serializer_class = TrainingCourseSerializer

    queryset = (
        TrainingCourse.objects
        .prefetch_related("sections")
        .all()
    )

    @extend_schema(
        summary="List training courses for management",
        responses=TrainingCourseSerializer(many=True),
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Create training course",
        request=TrainingCourseSerializer,
        responses=TrainingCourseSerializer,
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class TrainingManagementDetailAPIView(
    generics.RetrieveUpdateDestroyAPIView
):
    """
    Retrieve, update or delete a training course.
    """

    permission_classes = [IsAdminOrSuperAdmin]
    serializer_class = TrainingCourseSerializer

    queryset = (
        TrainingCourse.objects
        .prefetch_related("sections")
        .all()
    )

    @extend_schema(
        summary="Get training course",
        responses=TrainingCourseSerializer,
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Update training course",
        request=TrainingCourseSerializer,
        responses=TrainingCourseSerializer,
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @extend_schema(
        summary="Partial update training course",
        request=TrainingCourseSerializer,
        responses=TrainingCourseSerializer,
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @extend_schema(
        summary="Delete training course",
        responses=None,
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


class TrainingSectionListCreateAPIView(
    generics.ListCreateAPIView
):
    """
    List and create sections for a training course.
    """

    permission_classes = [IsAdminOrSuperAdmin]
    serializer_class = TrainingSectionSerializer

    def get_queryset(self):
        return (
            TrainingSection.objects
            .filter(
                course_id=self.kwargs["training_id"]
            )
            .select_related("course")
            .order_by("order", "id")
        )

    def perform_create(self, serializer):
        training_id = self.kwargs["training_id"]

        try:
            course = TrainingCourse.objects.get(
                id=training_id
            )
        except TrainingCourse.DoesNotExist:
            raise ValidationError(
                "دوره مورد نظر پیدا نشد."
            )

        serializer.save(course=course)

    @extend_schema(
        summary="List training sections",
        responses=TrainingSectionSerializer(many=True),
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Create training section",
        request=TrainingSectionSerializer,
        responses=TrainingSectionSerializer,
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class TrainingSectionDetailAPIView(
    generics.RetrieveUpdateDestroyAPIView
):
    """
    Retrieve, update or delete one training section.
    """

    permission_classes = [IsAdminOrSuperAdmin]
    serializer_class = TrainingSectionSerializer

    def get_queryset(self):
        return (
            TrainingSection.objects
            .filter(
                course_id=self.kwargs["training_id"]
            )
            .select_related("course")
        )

    @extend_schema(
        summary="Get training section",
        responses=TrainingSectionSerializer,
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Update training section",
        request=TrainingSectionSerializer,
        responses=TrainingSectionSerializer,
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @extend_schema(
        summary="Partial update training section",
        request=TrainingSectionSerializer,
        responses=TrainingSectionSerializer,
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @extend_schema(
        summary="Delete training section",
        responses=None,
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)