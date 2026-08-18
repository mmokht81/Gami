from django.db.models import Q
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from ..models import JobPosition
from ..serializers import JobPositionSerializer


class JobPositionCreateAPIView(generics.CreateAPIView):

    serializer_class = JobPositionSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Create job position",
        request=JobPositionSerializer,
        responses=JobPositionSerializer,
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class JobPositionDetailUpdateDeleteAPIView(
    generics.RetrieveUpdateDestroyAPIView
):

    serializer_class = JobPositionSerializer
    permission_classes = [IsAuthenticated]

    queryset = JobPosition.objects.all()

    @extend_schema(
        summary="Get job position",
        responses=JobPositionSerializer,
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Update job position",
        request=JobPositionSerializer,
        responses=JobPositionSerializer,
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @extend_schema(
        summary="Partial update job position",
        request=JobPositionSerializer,
        responses=JobPositionSerializer,
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @extend_schema(
        summary="Delete job position",
        responses=None,
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)