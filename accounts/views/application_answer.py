from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema

from ..models import (
    Question,
    ApplicationAnswer,
    JobApplication,
)
from ..serializers import (
    QuestionSerializer,
    ApplicationAnswerSerializer,
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


class ApplicationAnswerListCreateAPIView(generics.ListCreateAPIView):
    """
    API for managing application answers.
    """

    serializer_class = ApplicationAnswerSerializer
    permission_classes = [IsAuthenticated]


    @extend_schema(
        summary="Get application answers",
        description="""
        Returns all answers submitted for a specific
        job application.

        Only answers belonging to the authenticated
        user's application are accessible.
        """,
        responses=ApplicationAnswerSerializer(many=True),
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)



    @extend_schema(
        summary="Create application answer",
        description="""
        Creates an answer for a question in a job application.

        Required fields:
        - question
        - answer

        Application is automatically assigned
        from URL parameter.
        """,
        request=ApplicationAnswerSerializer,
        responses=ApplicationAnswerSerializer,
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)



    def get_queryset(self):
        application_id = self.kwargs.get(
            "application_id"
        )

        return (
            ApplicationAnswer.objects
            .filter(
                application__id=application_id,
                application__user=self.request.user,
            )
        )

    def perform_create(self, serializer):
        application_id = self.kwargs.get(
            "application_id"
        )

        application = JobApplication.objects.get(
            id=application_id,
            user=self.request.user,
        )

        serializer.save(
            application=application
        )