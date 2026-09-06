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


class ApplicationQuestionDetailUpdateDeleteAPIView(
    generics.RetrieveUpdateDestroyAPIView
):
    """
    Custom question management for a specific job application.

    ADMIN / SUPERADMIN:
        GET    -> view question
        PUT    -> update question
        PATCH  -> partially update question
        DELETE -> delete question

    User:
        GET    -> view questions belonging to own application
        PUT/PATCH/DELETE -> forbidden
    """

    permission_classes = [IsAuthenticated]
    serializer_class = ApplicationQuestionSerializer

    def get_queryset(self):
        user = self.request.user

        if user.role in ("ADMIN", "SUPERADMIN"):
            return ApplicationQuestion.objects.select_related(
                "application",
                "application__user",
                "application__job_position",
            )

        return ApplicationQuestion.objects.filter(
            application__user=user,
        ).select_related(
            "application",
        )

    def check_admin_permission(self):
        if self.request.user.role not in (
            "ADMIN",
            "SUPERADMIN",
        ):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied(
                "Only HR/Admin users can modify application questions."
            )

    def put(self, request, *args, **kwargs):
        self.check_admin_permission()

        return super().put(
            request,
            *args,
            **kwargs,
        )

    def patch(self, request, *args, **kwargs):
        self.check_admin_permission()

        return super().patch(
            request,
            *args,
            **kwargs,
        )

    def delete(self, request, *args, **kwargs):
        self.check_admin_permission()

        return super().delete(
            request,
            *args,
            **kwargs,
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


