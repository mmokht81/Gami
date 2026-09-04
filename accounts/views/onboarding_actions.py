from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import (
    Onboarding,
    OnboardingChecklistItem,
)
from ..serializers import (
    OnboardingSerializer,
    OnboardingChecklistCompleteSerializer,
)
from ..services import OnboardingService


class OnboardingChecklistCompleteAPIView(
    generics.GenericAPIView
):

    permission_classes = [
        IsAuthenticated
    ]

    serializer_class = (
        OnboardingChecklistCompleteSerializer
    )

    def post(self, request):

        onboarding = (
            Onboarding.objects
            .select_related(
                "job_position",
                "team",
            )
            .filter(
                user=request.user
            )
            .first()
        )

        if onboarding is None:

            return Response(
                {
                    "detail": (
                        "برای این کاربر Onboarding وجود ندارد."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.get_serializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        checklist_item_id = serializer.validated_data[
            "checklist_item_id"
        ]

        checklist_item = (
            OnboardingChecklistItem.objects
            .filter(
                id=checklist_item_id,
                is_active=True,
            )
            .first()
        )

        if checklist_item is None:

            return Response(
                {
                    "detail": (
                        "آیتم Checklist پیدا نشد."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:

            onboarding = (
                OnboardingService.complete_checklist_item(
                    onboarding=onboarding,
                    checklist_item=checklist_item,
                )
            )

        except ValueError as exc:

            return Response(
                {
                    "detail": str(exc)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            OnboardingSerializer(
                onboarding
            ).data,
            status=status.HTTP_200_OK,
        )