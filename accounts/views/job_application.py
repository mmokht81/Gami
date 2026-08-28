from rest_framework import generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema

from ..models import JobApplication
from ..serializers import (
    JobApplicationSerializer,
    JobApplicationAdminSerializer,
    JobApplicationStatusSerializer,
)
from ..permissions import IsAdminOrSuperAdmin


class JobApplicationListAPIView(generics.ListAPIView):
    """
    API for retrieving job applications.

    USER:
    Returns only applications belonging to the authenticated user.

    ADMIN / SUPERADMIN:
    Returns all job applications.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get job applications",
        description="""
        Returns job applications based on user role.

        USER:
        - Only own applications.

        ADMIN / SUPERADMIN:
        - All users' applications.
        - User information.
        - Job position information.
        - Application answers.
        - Application status.
        - Submission and update dates.
        """,
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_serializer_class(self):

        if self.request.user.role in (
            "ADMIN",
            "SUPERADMIN",
        ):
            return JobApplicationAdminSerializer

        return JobApplicationSerializer

    def get_queryset(self):

        user = self.request.user

        if user.role in (
            "ADMIN",
            "SUPERADMIN",
        ):
            return (
                JobApplication.objects
                .select_related(
                    "user",
                    "job_position",
                )
                .order_by(
                    "-submitted_at"
                )
            )

        return (
            JobApplication.objects
            .filter(
                user=user
            )
            .select_related(
                "job_position"
            )
            .order_by(
                "-submitted_at"
            )
        )

class JobApplicationCreateAPIView(generics.CreateAPIView):
    """
    API for creating a new job application.
    """

    serializer_class = JobApplicationSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Create job application",
        description="""
        Creates a new job application for the authenticated user.

        User is automatically assigned from
        the authenticated account.

        Required field:
        - job_position
        """,
        request=JobApplicationSerializer,
        responses=JobApplicationSerializer,
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(
            user=self.request.user
        )

class JobApplicationDetailAPIView(generics.RetrieveAPIView):
    """
    API for retrieving a single job application.

    USER:
    Can only retrieve own applications.

    ADMIN / SUPERADMIN:
    Can retrieve any application.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get job application detail",
        description="""
        Returns details of a specific job application.

        USER:
        - Only own application.

        ADMIN / SUPERADMIN:
        - Any user's application.
        - User information.
        - Job position information.
        - Application answers.
        """,
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_serializer_class(self):

        if self.request.user.role in (
            "ADMIN",
            "SUPERADMIN",
        ):
            return JobApplicationAdminSerializer

        return JobApplicationSerializer

    def get_queryset(self):

        user = self.request.user

        if user.role in (
            "ADMIN",
            "SUPERADMIN",
        ):
            return (
                JobApplication.objects
                .select_related(
                    "user",
                    "job_position",
                )
            )

        return (
            JobApplication.objects
            .filter(
                user=user
            )
            .select_related(
                "job_position"
            )
        )

class JobApplicationStatusUpdateAPIView(
    generics.UpdateAPIView
):
    """
    API for updating job application status.

    Only ADMIN and SUPERADMIN can change
    application status.
    """

    serializer_class = JobApplicationStatusSerializer

    permission_classes = [
        IsAdminOrSuperAdmin
    ]

    queryset = JobApplication.objects.select_related(
        "user",
        "job_position",
    )

    @extend_schema(
        summary="Update application status",
        description="""
        Allows HR/Admin to update the status
        of a job application.

        Valid statuses:

        - PENDING_REVIEW
        - HR_REVIEW
        - WAITING_FOR_USER
        - MANAGEMENT_REVIEW
        - ACCEPTED
        - REJECTED
        """,
        request=JobApplicationStatusSerializer,
        responses=JobApplicationAdminSerializer,
    )
    def patch(self, request, *args, **kwargs):

        application = self.get_object()

        serializer = self.get_serializer(
            application,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True
        )

        serializer.save()

        return_serializer = (
            JobApplicationAdminSerializer(
                application
            )
        )

        return Response(
            return_serializer.data
        )

