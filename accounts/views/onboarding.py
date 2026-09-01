from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import (
    Onboarding,
    OnboardingChecklistItem,
    Team,
)
from ..permissions import IsAdminOrSuperAdmin
from ..serializers import (
    OnboardingSerializer,
    OnboardingTeamAssignSerializer,
    OnboardingHRProgressSerializer,
    OnboardingChecklistCompleteSerializer,
)
from ..services import OnboardingService


class MyOnboardingAPIView(
    generics.RetrieveAPIView
):

    serializer_class = OnboardingSerializer

    permission_classes = [
        IsAuthenticated
    ]

    def get_object(self):

        return (
            Onboarding.objects
            .select_related(
                "user",
                "job_position",
                "team",
            )
            .prefetch_related(
                "checklist_progress_items__checklist_item",
                "team__onboardings__user",
                "user__badges__badge",
            )
            .get(
                user=self.request.user
            )
        )


class UserOnboardingAPIView(
    generics.RetrieveAPIView
):

    serializer_class = OnboardingSerializer

    permission_classes = [
        IsAdminOrSuperAdmin
    ]

    lookup_url_kwarg = "user_id"

    def get_queryset(self):

        return (
            Onboarding.objects
            .select_related(
                "user",
                "job_position",
                "team",
            )
            .prefetch_related(
                "checklist_progress_items__checklist_item",
                "team__onboardings__user",
                "user__badges__badge",
            )
        )


class OnboardingChecklistCompleteAPIView(
    generics.GenericAPIView
):

    serializer_class = (
        OnboardingChecklistCompleteSerializer
    )

    permission_classes = [
        IsAuthenticated
    ]

    def post(self, request):

        serializer = self.get_serializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        checklist_item_id = serializer.validated_data[
            "checklist_item_id"
        ]

        try:
            onboarding = (
                Onboarding.objects
                .select_related(
                    "user",
                    "job_position",
                    "team",
                )
                .get(
                    user=request.user
                )
            )
        except Onboarding.DoesNotExist:
            return Response(
                {
                    "detail": (
                        "Onboarding برای این کاربر "
                        "وجود ندارد."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            checklist_item = (
                OnboardingChecklistItem.objects.get(
                    id=checklist_item_id,
                    is_active=True,
                )
            )
        except OnboardingChecklistItem.DoesNotExist:
            return Response(
                {
                    "detail": (
                        "Checklist item پیدا نشد."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if (
            checklist_item.job_position_id
            != onboarding.job_position_id
        ):
            return Response(
                {
                    "detail": (
                        "این Checklist مربوط به "
                        "موقعیت شغلی شما نیست."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        OnboardingService.complete_checklist_item(
            onboarding=onboarding,
            checklist_item=checklist_item,
        )

        onboarding.refresh_from_db()

        return Response(
            OnboardingSerializer(
                onboarding
            ).data
        )


class OnboardingTeamAssignAPIView(
    generics.GenericAPIView
):

    serializer_class = (
        OnboardingTeamAssignSerializer
    )

    permission_classes = [
        IsAdminOrSuperAdmin
    ]

    def patch(self, request, user_id):

        serializer = self.get_serializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        team_id = serializer.validated_data[
            "team_id"
        ]

        try:
            onboarding = (
                Onboarding.objects
                .get(
                    user_id=user_id
                )
            )
        except Onboarding.DoesNotExist:
            return Response(
                {
                    "detail": (
                        "Onboarding برای این کاربر "
                        "وجود ندارد."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            team = Team.objects.get(
                id=team_id,
                is_active=True,
            )
        except Team.DoesNotExist:
            return Response(
                {
                    "detail": (
                        "Team پیدا نشد."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        OnboardingService.assign_team(
            onboarding=onboarding,
            team=team,
        )

        onboarding.refresh_from_db()

        return Response(
            OnboardingSerializer(
                onboarding
            ).data
        )


class OnboardingHRProgressAPIView(
    generics.GenericAPIView
):

    serializer_class = (
        OnboardingHRProgressSerializer
    )

    permission_classes = [
        IsAdminOrSuperAdmin
    ]

    def patch(self, request, user_id):

        serializer = self.get_serializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        hr_progress = serializer.validated_data[
            "hr_progress"
        ]

        try:
            onboarding = (
                Onboarding.objects
                .get(
                    user_id=user_id
                )
            )
        except Onboarding.DoesNotExist:
            return Response(
                {
                    "detail": (
                        "Onboarding برای این کاربر "
                        "وجود ندارد."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        OnboardingService.set_hr_progress(
            onboarding=onboarding,
            value=hr_progress,
        )

        onboarding.refresh_from_db()

        return Response(
            OnboardingSerializer(
                onboarding
            ).data
        )




