import secrets

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from .models import (
    OTP,
    User,
    Badge,
    UserBadge,
    BadgeRule,
    UserMission,
    Onboarding,
    OnboardingChecklistItem,
    OnboardingChecklistProgress,
    JobPosition,
)

class OTPService:
    OTP_LENGTH = 6
    MAX_ATTEMPTS = 5
    RESEND_TIMEOUT = 120

    @staticmethod
    def generate_code():
        return "".join(
            secrets.choice("0123456789")
            for _ in range(OTPService.OTP_LENGTH)
        )

    @staticmethod
    def create_otp(phone_number):
        OTP.objects.filter(
            phone_number=phone_number,
            is_used=False,
        ).update(is_used=True)

        otp = OTP.objects.create(
            phone_number=phone_number,
            code=OTPService.generate_code(),
        )

        return otp

    @staticmethod
    def can_request_new_otp(phone_number):
        otp = (
            OTP.objects.filter(
                phone_number=phone_number,
                is_used=False,
            )
            .order_by("-created_at")
            .first()
        )

        if otp is None:
            return True

        return otp.is_expired()

    @staticmethod
    def verify_otp(phone_number, code):

        otp = (
            OTP.objects.filter(
                phone_number=phone_number,
                is_used=False,
            )
            .order_by("-created_at")
            .first()
        )

        if otp is None:
            return {
                "success": False,
                "error": "not_found",
            }

        if otp.is_expired():
            otp.is_used = True
            otp.save(update_fields=["is_used"])

            return {
                "success": False,
                "error": "expired",
            }

        if otp.code != code:
            otp.attempts += 1

            if otp.attempts >= OTPService.MAX_ATTEMPTS:
                otp.is_used = True
                otp.save(update_fields=["attempts", "is_used"])

                return {
                    "success": False,
                    "error": "max_attempts",
                }

            otp.save(update_fields=["attempts"])

            return {
                "success": False,
                "error": "invalid_code",
                "remaining_attempts": OTPService.MAX_ATTEMPTS - otp.attempts,
            }

        otp.is_used = True
        otp.save(update_fields=["is_used"])

        user = User.objects.filter(
            phone_number=phone_number
        ).first()

        if not user:
            return {
                "success": False,
                "error": "user_not_found",
            }

        user.is_phone_verified = True
        user.save(update_fields=["is_phone_verified"])

        return {
            "success": True,
            "user": user,
        }

class PointService:

    @staticmethod
    @transaction.atomic
    def award_points(user, points):
        if points <= 0:
            return user

        user.points = F("points") + points
        user.save(update_fields=["points"])
        user.refresh_from_db(fields=["points"])

        return user

class BadgeService:

    @staticmethod
    def check_automatic_badges(user):
        """
        Check all active badge rules and award
        badges whose conditions are satisfied.
        """

        badges = Badge.objects.filter(
            is_active=True,
            rule__is_active=True,
        ).select_related("rule")

        for badge in badges:

            rule = badge.rule

            if rule.rule_type == "MISSIONS_COMPLETED":

                completed_missions = UserMission.objects.filter(
                    user=user,
                    status="COMPLETED",
                ).count()

                if completed_missions >= rule.value:

                    UserBadge.objects.get_or_create(
                        user=user,
                        badge=badge,
                    )

class OnboardingService:

    @staticmethod
    @transaction.atomic
    def create_for_user(user, job_position):

        onboarding, created = Onboarding.objects.get_or_create(
            user=user,
            defaults={
                "job_position": job_position,
            },
        )

        if not created and onboarding.job_position_id != job_position.id:
            onboarding.job_position = job_position
            onboarding.save()

        checklist_items = (
            OnboardingChecklistItem.objects
            .filter(
                job_position=job_position,
                is_active=True,
            )
            .order_by("order", "id")
        )

        for item in checklist_items:

            OnboardingChecklistProgress.objects.get_or_create(
                onboarding=onboarding,
                checklist_item=item,
            )

        OnboardingService.update_checklist_progress(
            onboarding
        )

        return onboarding

    @staticmethod
    def update_checklist_progress(onboarding):

        items = (
            onboarding.checklist_progress_items
            .filter(
                checklist_item__is_active=True,
            )
        )

        total = items.count()

        if total == 0:
            onboarding.checklist_progress = 0
        else:
            completed = items.filter(
                is_completed=True
            ).count()

            onboarding.checklist_progress = round(
                completed * 100 / total
            )

        onboarding.save(
            update_fields=[
                "checklist_progress",
                "progress",
                "updated_at",
            ]
        )

        return onboarding

    @staticmethod
    def complete_checklist_item(
        onboarding,
        checklist_item,
    ):

        progress = (
            OnboardingChecklistProgress.objects.get(
                onboarding=onboarding,
                checklist_item=checklist_item,
            )
        )

        progress.is_completed = True
        progress.completed_at = timezone.now()
        progress.save(
            update_fields=[
                "is_completed",
                "completed_at",
            ]
        )

        return OnboardingService.update_checklist_progress(
            onboarding
        )

    @staticmethod
    def set_hr_progress(onboarding, value):

        if not 0 <= value <= 100:
            raise ValueError(
                "HR progress must be between 0 and 100."
            )

        onboarding.hr_progress = value

        onboarding.save(
            update_fields=[
                "hr_progress",
                "progress",
                "updated_at",
            ]
        )

        return onboarding

