from rest_framework import generics

from ..models import Team
from ..permissions import IsAdminOrSuperAdmin
from ..serializers import TeamSerializer


class TeamListCreateAPIView(
    generics.ListCreateAPIView
):

    queryset = Team.objects.all()

    serializer_class = TeamSerializer

    permission_classes = [
        IsAdminOrSuperAdmin
    ]


class TeamDetailUpdateDeleteAPIView(
    generics.RetrieveUpdateDestroyAPIView
):

    queryset = Team.objects.all()

    serializer_class = TeamSerializer

    permission_classes = [
        IsAdminOrSuperAdmin
    ]