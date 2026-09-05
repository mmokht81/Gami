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

        user = self.request.user

        # Make sure eligible Level 1 users
        # have an onboarding record.
        onboarding = (
            OnboardingService
            .ensure_for_level_one_user(user)
        )

        if onboarding is None:

            raise Onboarding.DoesNotExist(
                "برای این کاربر Onboarding قابل ایجاد نیست. "
                "کاربر باید Level 1 باشد و یک درخواست استخدام "
                "پذیرفته‌شده داشته باشد."
            )

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
                user=user
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

    def get_object(self):

        user_id = self.kwargs[
            self.lookup_url_kwarg
        ]

        from ..models import User

        user = User.objects.get(
            id=user_id
        )

        onboarding = (
            OnboardingService
            .ensure_for_level_one_user(user)
        )

        if onboarding is None:

            raise Onboarding.DoesNotExist(
                "برای این کاربر Onboarding قابل ایجاد نیست. "
                "کاربر باید Level 1 باشد و یک درخواست استخدام "
                "پذیرفته‌شده داشته باشد."
            )

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
                user_id=user_id
            )
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

        from ..models import User

        try:

            user = User.objects.get(
                id=user_id,
                is_active=True,
            )

        except User.DoesNotExist:

            return Response(
                {
                    "detail": "کاربر پیدا نشد."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # Automatically create onboarding
        # for eligible Level 1 users.
        onboarding = (
            OnboardingService
            .ensure_for_level_one_user(user)
        )

        if onboarding is None:

            return Response(
                {
                    "detail": (
                        "برای این کاربر Onboarding قابل ایجاد نیست. "
                        "کاربر باید Level 1 باشد و یک درخواست استخدام "
                        "پذیرفته‌شده داشته باشد."
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
                    "detail": "Team پیدا نشد."
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

        from ..models import User

        try:

            user = User.objects.get(
                id=user_id,
                is_active=True,
            )

        except User.DoesNotExist:

            return Response(
                {
                    "detail": "کاربر پیدا نشد."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        onboarding = (
            OnboardingService
            .ensure_for_level_one_user(user)
        )

        if onboarding is None:

            return Response(
                {
                    "detail": (
                        "برای این کاربر Onboarding قابل ایجاد نیست. "
                        "کاربر باید Level 1 باشد و یک درخواست استخدام "
                        "پذیرفته‌شده داشته باشد."
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


