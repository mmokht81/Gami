from rest_framework import generics

from ..models import OnboardingChecklistItem
from ..permissions import IsAdminOrSuperAdmin
from ..serializers import (
    OnboardingChecklistItemManagementSerializer,
)


class OnboardingChecklistListCreateAPIView(
    generics.ListCreateAPIView
):

    serializer_class = (
        OnboardingChecklistItemManagementSerializer
    )

    permission_classes = [
        IsAdminOrSuperAdmin
    ]

    def get_queryset(self):

        queryset = (
            OnboardingChecklistItem.objects
            .select_related(
                "job_position"
            )
            .order_by(
                "job_position_id",
                "order",
                "id",
            )
        )

        job_position_id = self.request.query_params.get(
            "job_position"
        )

        if job_position_id:

            queryset = queryset.filter(
                job_position_id=job_position_id
            )

        return queryset


class OnboardingChecklistDetailUpdateDeleteAPIView(
    generics.RetrieveUpdateDestroyAPIView
):

    queryset = OnboardingChecklistItem.objects.all()

    serializer_class = (
        OnboardingChecklistItemManagementSerializer
    )

    permission_classes = [
        IsAdminOrSuperAdmin
    ]



