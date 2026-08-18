from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema

from ..models import JobPosition, Question
from ..serializers import QuestionSerializer


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