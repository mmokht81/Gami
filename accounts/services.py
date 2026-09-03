import secrets

from django.db import transaction
from django.db.models import F
from django.utils import timezone
from datetime import timedelta
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
    JobApplication,
    Challenge,
    ChallengeParticipant,
    ChallengeWinner,
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

                otp.save(
                    update_fields=[
                        "attempts",
                        "is_used",
                    ]
                )

                return {
                    "success": False,
                    "error": "max_attempts",
                }

            otp.save(
                update_fields=[
                    "attempts"
                ]
            )

            return {
                "success": False,
                "error": "invalid_code",
                "remaining_attempts": (
                    OTPService.MAX_ATTEMPTS
                    - otp.attempts
                ),
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

        user.save(
            update_fields=[
                "is_phone_verified"
            ]
        )

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

        user.save(
            update_fields=[
                "points"
            ]
        )

        user.refresh_from_db(
            fields=[
                "points"
            ]
        )

        return user


class BadgeService:
    
    @staticmethod
    def check_automatic_badges(user):
        badges = (
            Badge.objects
            .filter(
                is_active=True,
                rule__is_active=True,
            )
            .select_related("rule")
        )

        for badge in badges:

            rule = badge.rule

            if rule.rule_type == "MISSIONS_COMPLETED":

                completed_missions = (
                    UserMission.objects
                    .filter(
                        user=user,
                        status="COMPLETED",
                    )
                    .count()
                )

                if completed_missions >= rule.value:

                    UserBadge.objects.get_or_create(
                        user=user,
                        badge=badge,
                    )


class OnboardingService:

    @staticmethod
    @transaction.atomic
    def create_for_user(user, job_position):

        onboarding, created = (
            Onboarding.objects.get_or_create(
                user=user,
                defaults={
                    "job_position": job_position,
                },
            )
        )

        if (
            not created
            and onboarding.job_position_id
            != job_position.id
        ):

            onboarding.job_position = job_position

            onboarding.save()

        checklist_items = (
            OnboardingChecklistItem.objects
            .filter(
                job_position=job_position,
                is_active=True,
            )
            .order_by(
                "order",
                "id",
            )
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
    @transaction.atomic
    def ensure_for_level_one_user(user):

        """
        Create onboarding automatically when:

        1. User is Level 1
        2. User has an accepted job application

        OneToOneField guarantees that only one
        onboarding can exist for the user.
        """

        if user.level != 1:
            return None

        application = (
            JobApplication.objects
            .filter(
                user=user,
                status="ACCEPTED",
            )
            .select_related(
                "job_position"
            )
            .order_by("-updated_at")
            .first()
        )

        if application is None:
            return None

        return OnboardingService.create_for_user(
            user=user,
            job_position=application.job_position,
        )

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

            completed = (
                items
                .filter(
                    is_completed=True
                )
                .count()
            )

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
    @transaction.atomic
    def complete_checklist_item(
        onboarding,
        checklist_item,
    ):

        if (
            checklist_item.job_position_id
            != onboarding.job_position_id
        ):

            raise ValueError(
                "این آیتم مربوط به موقعیت شغلی این Onboarding نیست."
            )

        progress, created = (
            OnboardingChecklistProgress.objects
            .get_or_create(
                onboarding=onboarding,
                checklist_item=checklist_item,
            )
        )

        if not progress.is_completed:

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
    def set_hr_progress(
        onboarding,
        value,
    ):

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

    @staticmethod
    @transaction.atomic
    def assign_team(
        onboarding,
        team,
    ):

        onboarding.team = team

        onboarding.save(
            update_fields=[
                "team",
                "updated_at",
            ]
        )

        return onboarding

    @staticmethod
    def is_completed(onboarding):

        return onboarding.progress >= 100


class ChallengeService:

    REGISTRATION_CANCEL_MINUTES = 30

    @staticmethod
    def update_status(challenge):
        """
        Update challenge status according to current time.
        """

        if challenge.status == "CANCELLED":
            return challenge

        now = timezone.now()

        if now >= challenge.end_time:
            challenge.status = "FINISHED"

        elif now >= challenge.start_time:
            challenge.status = "ACTIVE"

        else:
            challenge.status = "UPCOMING"

        challenge.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        return challenge

    @staticmethod
    @transaction.atomic
    def register_user(challenge, user):

        ChallengeService.update_status(challenge)

        if not challenge.is_active:
            raise ValueError(
                "این چالش یا مسابقه فعال نیست."
            )

        if challenge.status in (
            "ACTIVE",
            "FINISHED",
            "CANCELLED",
        ):
            raise ValueError(
                "ثبت نام برای این چالش یا مسابقه امکان پذیر نیست."
            )

        now = timezone.now()

        if now >= challenge.start_time:
            raise ValueError(
                "زمان ثبت نام به پایان رسیده است."
            )

        participant = (
            ChallengeParticipant.objects
            .filter(
                challenge=challenge,
                user=user,
            )
            .first()
        )

        if participant:

            if not participant.is_cancelled:
                raise ValueError(
                    "شما قبلاً در این چالش یا مسابقه ثبت نام کرده‌اید."
                )

            participant.is_cancelled = False
            participant.cancelled_at = None
            participant.registered_at = now

            participant.save(
                update_fields=[
                    "is_cancelled",
                    "cancelled_at",
                    "registered_at",
                ]
            )

            return participant

        participant = ChallengeParticipant.objects.create(
            challenge=challenge,
            user=user,
        )

        return participant

    @staticmethod
    @transaction.atomic
    def cancel_registration(challenge, user):

        ChallengeService.update_status(challenge)

        participant = (
            ChallengeParticipant.objects
            .filter(
                challenge=challenge,
                user=user,
            )
            .first()
        )

        if participant is None:
            raise ValueError(
                "شما در این چالش یا مسابقه ثبت نام نکرده‌اید."
            )

        if participant.is_cancelled:
            raise ValueError(
                "ثبت نام شما قبلاً لغو شده است."
            )

        now = timezone.now()

        cancellation_deadline = (
            challenge.start_time
            - timedelta(
                minutes=ChallengeService.REGISTRATION_CANCEL_MINUTES
            )
        )

        if now > cancellation_deadline:
            raise ValueError(
                "لغو ثبت نام فقط تا ۳۰ دقیقه قبل از شروع امکان پذیر است."
            )

        if now >= challenge.start_time:
            raise ValueError(
                "این چالش یا مسابقه شروع شده است."
            )

        participant.is_cancelled = True
        participant.cancelled_at = now

        participant.save(
            update_fields=[
                "is_cancelled",
                "cancelled_at",
            ]
        )

        return participant

    @staticmethod
    def get_participants(challenge):

        return (
            ChallengeParticipant.objects
            .filter(
                challenge=challenge,
                is_cancelled=False,
            )
            .select_related("user")
            .order_by("registered_at")
        )

    @staticmethod
    def get_winners(challenge):

        return (
            ChallengeWinner.objects
            .filter(
                challenge=challenge,
            )
            .select_related("user")
            .order_by("rank", "id")
        )

    @staticmethod
    @transaction.atomic
    def add_winner(
        challenge,
        user,
        rank=None,
        points=None,
        prize="",
    ):

        ChallengeService.update_status(challenge)

        if challenge.status != "FINISHED":
            raise ValueError(
                "ثبت نتایج فقط بعد از پایان چالش یا مسابقه امکان پذیر است."
            )

        participant = (
            ChallengeParticipant.objects
            .filter(
                challenge=challenge,
                user=user,
                is_cancelled=False,
            )
            .first()
        )

        if participant is None:
            raise ValueError(
                "برنده باید در این چالش یا مسابقه ثبت نام کرده باشد."
            )

        if challenge.type == "COMPETITION":

            if rank is None:
                raise ValueError(
                    "برای مسابقه وارد کردن رتبه الزامی است."
                )

            if points is None:
                raise ValueError(
                    "برای مسابقه وارد کردن امتیاز الزامی است."
                )

            winner_points = points

        else:

            winner_points = challenge.points

        winner, created = (
            ChallengeWinner.objects.get_or_create(
                challenge=challenge,
                user=user,
                defaults={
                    "rank": rank,
                    "points": winner_points,
                    "prize": prize,
                },
            )
        )

        if not created:
            raise ValueError(
                "این کاربر قبلاً به عنوان برنده ثبت شده است."
            )

        if winner_points > 0:
            PointService.award_points(
                user,
                winner_points,
            )

        return winner

