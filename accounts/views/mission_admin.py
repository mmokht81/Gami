from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema

from ..models import Mission
from ..serializers import MissionSerializer


class MissionCreateAPIView(generics.CreateAPIView):

    serializer_class = MissionSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Create mission",
        request=MissionSerializer,
        responses=MissionSerializer,
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class MissionDetailUpdateDeleteAPIView(
    generics.RetrieveUpdateDestroyAPIView
):

    serializer_class = MissionSerializer
    permission_classes = [IsAuthenticated]

    queryset = Mission.objects.all()

    @extend_schema(
        summary="Get mission",
        responses=MissionSerializer,
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Update mission",
        request=MissionSerializer,
        responses=MissionSerializer,
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @extend_schema(
        summary="Partial update mission",
        request=MissionSerializer,
        responses=MissionSerializer,
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @extend_schema(
        summary="Delete mission",
        responses=None,
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)