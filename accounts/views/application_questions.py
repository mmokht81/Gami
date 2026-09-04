from django.shortcuts import get_object_or_404

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import (
    ApplicationQuestion,
    JobApplication,
)
from ..serializers import (
    ApplicationQuestionSerializer,
    ApplicationQuestionAnswerSerializer,
)


class ApplicationQuestionListCreateAPIView(
    generics.ListCreateAPIView
):
    """
    HR:
        GET  -> view questions
        POST -> ask a new question

    User:
        GET  -> view questions of own application
        POST -> forbidden
    """

    permission_classes = [IsAuthenticated]

    def get_application(self):
        application = get_object_or_404(
            JobApplication.objects.select_related(
                "user",
                "job_position",
            ),
            pk=self.kwargs["application_id"],
        )

        user = self.request.user

        if user.role in ("ADMIN", "SUPERADMIN"):
            return application

        if application.user_id != user.id:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied(
                "You can only access your own application."
            )

        return application

    def get_queryset(self):
        application = self.get_application()

        return ApplicationQuestion.objects.filter(
            application=application
        ).order_by("created_at")

    def get_serializer_class(self):
        return ApplicationQuestionSerializer

    def create(self, request, *args, **kwargs):
        if request.user.role not in ("ADMIN", "SUPERADMIN"):
            return Response(
                {
                    "detail": (
                        "Only HR/Admin users can create "
                        "application questions."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        return super().create(
            request,
            *args,
            **kwargs,
        )

    def perform_create(self, serializer):
        application = self.get_application()

        serializer.save(
            application=application,
        )


class ApplicationQuestionAnswerAPIView(
    generics.UpdateAPIView
):
    """
    Authenticated user can answer a question
    belonging to their own application.

    ADMIN / SUPERADMIN:
        Cannot answer application questions.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = ApplicationQuestionAnswerSerializer

    http_method_names = ["patch"]

    def get_queryset(self):
        return ApplicationQuestion.objects.filter(
            application__user=self.request.user,
        ).select_related(
            "application",
        )

    def patch(self, request, *args, **kwargs):
        question = self.get_object()

        serializer = self.get_serializer(
            question,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True
        )

        question.answer = serializer.validated_data["answer"]
        question.is_answered = True

        from django.utils import timezone

        question.answered_at = timezone.now()

        question.save(
            update_fields=[
                "answer",
                "is_answered",
                "answered_at",
            ]
        )

        return Response(
            ApplicationQuestionSerializer(
                question
            ).data,
            status=status.HTTP_200_OK,
        )


