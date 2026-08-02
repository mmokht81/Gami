from rest_framework import filters, generics
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

    filter_backends = (
        filters.SearchFilter,
        filters.OrderingFilter,
    )

    search_fields = (
        "title",
        "description",
    )

    ordering_fields = (
        "title",
    )

    ordering = (
        "title",
    )

    @extend_schema(
        summary="Get available job positions",
        description="""
Returns all active job positions.

Supports:
- Search by title
- Search by description
- Ordering by title
""",
        responses=JobPositionSerializer(many=True),
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return (
            JobPosition.objects
            .filter(is_active=True)
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
""",
        responses=JobPositionSerializer,
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return (
            JobPosition.objects
            .filter(is_active=True)
        )