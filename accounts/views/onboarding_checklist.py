from rest_framework import generics, status
from rest_framework.response import Response

from ..models import OnboardingChecklistItem
from ..permissions import IsAdminOrSuperAdmin
from ..serializers import (
    OnboardingChecklistItemManagementSerializer,
)
from ..services import OnboardingService


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

    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        checklist_item = serializer.save()

        OnboardingService.sync_checklist_item(
            checklist_item
        )

        headers = self.get_success_headers(
            serializer.data
        )

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

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



