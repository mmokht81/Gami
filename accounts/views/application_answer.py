from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema

from ..models import Question
from ..serializers import (
    QuestionSerializer,
)


class JobQuestionListAPIView(generics.ListAPIView):
    """
    Returns questions related to a job position.
    """

    serializer_class = QuestionSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get job position questions",
        description="""
        Returns active questions for a specific job position.

        Includes:
        - Question type
        - Question text
        - Display order
        - Active status
        """,
        responses=QuestionSerializer(many=True),
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        job_position_id = self.kwargs.get(
            "job_position_id"
        )

        return (
            Question.objects
            .filter(
                job_position_id=job_position_id,
                is_active=True,
            )
            .order_by(
                "order"
            )
        )