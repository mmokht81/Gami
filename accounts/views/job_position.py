from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema

from ..models import JobPosition
from ..serializers import JobPositionSerializer


class JobPositionListAPIView(generics.ListAPIView):
    """
    API for retrieving available job positions.
    """

    serializer_class = JobPositionSerializer
    permission_classes = [IsAuthenticated]


    @extend_schema(
        summary="Get available job positions",
        description="""
        Returns all active job positions.

        Includes:
        - Job position title
        - Description
        - Active status
        """,
        responses=JobPositionSerializer(many=True),
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


    def get_queryset(self):
        return JobPosition.objects.filter(
            is_active=True
        )



class JobPositionDetailAPIView(generics.RetrieveAPIView):
    """
    API for retrieving a specific job position.
    """

    serializer_class = JobPositionSerializer
    permission_classes = [IsAuthenticated]


    @extend_schema(
        summary="Get job position detail",
        description="""
        Returns details of a specific active job position.

        Includes:
        - Title
        - Description
        - Active status
        """,
        responses=JobPositionSerializer,
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


    def get_queryset(self):
        return JobPosition.objects.filter(
            is_active=True
        )