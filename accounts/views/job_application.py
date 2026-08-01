from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema

from ..models import JobApplication
from ..serializers import JobApplicationSerializer


class JobApplicationListAPIView(generics.ListAPIView):
    """
    API for retrieving user's job applications.
    """

    serializer_class = JobApplicationSerializer
    permission_classes = [IsAuthenticated]


    @extend_schema(
        summary="Get user's job applications",
        description="""
        Returns all job applications created by the authenticated user.

        Includes:
        - Job position
        - Application status
        - Submission date
        - Last update date
        """,
        responses=JobApplicationSerializer(many=True),
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


    def get_queryset(self):
        return (
            JobApplication.objects
            .filter(
                user=self.request.user
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
    """

    serializer_class = JobApplicationSerializer
    permission_classes = [IsAuthenticated]


    @extend_schema(
        summary="Get job application detail",
        description="""
        Returns details of a specific job application.

        Only applications belonging to
        the authenticated user are accessible.
        """,
        responses=JobApplicationSerializer,
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


    def get_queryset(self):
        return JobApplication.objects.filter(
            user=self.request.user
        )