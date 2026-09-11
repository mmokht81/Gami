from rest_framework import generics

from ..models import Team
from ..permissions import (
    IsAdminOrSuperAdmin,
    IsTeamManagerOrSuperAdmin,
)
from ..serializers import TeamSerializer


class TeamListCreateAPIView(
    generics.ListCreateAPIView
):

    serializer_class = TeamSerializer

    permission_classes = [
        IsAdminOrSuperAdmin
    ]

    def get_queryset(self):

        user = self.request.user

        if user.role == "SUPERADMIN":
            return (
                Team.objects
                .select_related("manager")
                .prefetch_related(
                    "onboardings__user"
                )
                .all()
            )

        return (
            Team.objects
            .select_related("manager")
            .prefetch_related(
                "onboardings__user"
            )
            .filter(
                manager=user
            )
        )


class TeamDetailUpdateDeleteAPIView(
    generics.RetrieveUpdateDestroyAPIView
):

    serializer_class = TeamSerializer

    permission_classes = [
        IsTeamManagerOrSuperAdmin
    ]

    def get_queryset(self):

        user = self.request.user

        if user.role == "SUPERADMIN":
            return (
                Team.objects
                .select_related("manager")
                .prefetch_related(
                    "onboardings__user"
                )
                .all()
            )

        return (
            Team.objects
            .select_related("manager")
            .prefetch_related(
                "onboardings__user"
            )
            .filter(
                manager=user
            )
        )