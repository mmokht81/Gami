from django.shortcuts import get_object_or_404

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema

from ..models import JobPosition, Question
from ..serializers import QuestionSerializer
from ..permissions import IsAdminOrSuperAdmin


class JobQuestionListAPIView(generics.ListAPIView):

    serializer_class = QuestionSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get job position questions",
        description="""
        Returns active questions for a specific job position.
        """,
        responses=QuestionSerializer(many=True),
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):

        job_position = get_object_or_404(
            JobPosition,
            id=self.kwargs["job_position_id"],
            is_active=True,
        )

        return Question.objects.filter(
            job_position=job_position,
            is_active=True,
        ).order_by("order")


class QuestionCreateAPIView(generics.CreateAPIView):

    serializer_class = QuestionSerializer
    permission_classes = [IsAdminOrSuperAdmin]

    @extend_schema(
        summary="Create application question",
        description="""
        Creates a question for a job position.

        Only ADMIN and SUPERADMIN can create questions.
        """,
        request=QuestionSerializer,
        responses=QuestionSerializer,
    )
    def perform_create(self, serializer):

        job_position = serializer.validated_data["job_position"]

        if not job_position.is_active:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({
                "job_position": (
                    "نمی‌توان برای موقعیت شغلی غیرفعال سوال ایجاد کرد."
                )
            })

        serializer.save()


class QuestionDetailUpdateDeleteAPIView(
    generics.RetrieveUpdateDestroyAPIView
):

    serializer_class = QuestionSerializer
    permission_classes = [IsAdminOrSuperAdmin]

    queryset = Question.objects.select_related(
        "job_position"
    ).all()

    @extend_schema(
        summary="Get application question",
        responses=QuestionSerializer,
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Update application question",
        request=QuestionSerializer,
        responses=QuestionSerializer,
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @extend_schema(
        summary="Partial update application question",
        request=QuestionSerializer,
        responses=QuestionSerializer,
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @extend_schema(
        summary="Delete application question",
        responses=None,
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)