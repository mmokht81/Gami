from rest_framework import filters, generics
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema

from ..models import JobPosition
from ..serializers import JobPositionSerializer


class JobPositionListAPIView(generics.ListCreateAPIView):

    serializer_class = JobPositionSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = (
        filters.SearchFilter,
        filters.OrderingFilter,
    )

    search_fields = (
        "title",
        "description",
        "tags",
    )

    ordering_fields = (
        "title",
    )

    ordering = (
        "title",
    )

    @extend_schema(
        summary="List and create job positions",
        description="""
Returns all active job positions.

Supports:
- Search by title
- Search by description
- Search by tags
- Ordering by title

Also allows creating a new job position.
""",
        responses=JobPositionSerializer(many=True),
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return JobPosition.objects.filter(
            is_active=True
        )


class JobPositionDetailAPIView(
    generics.RetrieveUpdateDestroyAPIView
):

    serializer_class = JobPositionSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get, update or delete job position",
        description="""
Returns, updates or deletes a specific job position.

Supported methods:
- GET
- PUT
- PATCH
- DELETE
""",
        responses=JobPositionSerializer,
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return JobPosition.objects.filter(
            is_active=True
        )