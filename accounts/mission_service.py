from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import Mission, UserMission
from .reward_service import RewardService
from .services import BadgeService


class MissionService:
    """
    Central service for managing the complete mission lifecycle.

    Mission flow:

        Assign
          ↓
        Start
          ↓
        Progress
          ↓
        Complete
          ↓
        Points
          ↓
        Level
          ↓
        Automatic Badges
    """

    @staticmethod
    def _validate_mission_schedule(mission):
        now = timezone.now()

        if (
            mission.start_time is not None
            and now < mission.start_time
        ):
            raise ValidationError(
                "زمان شروع این ماموریت هنوز نرسیده است."
            )

        if (
            mission.end_time is not None
            and now >= mission.end_time
        ):
            raise ValidationError(
                "ددلاین این ماموریت به پایان رسیده است."
            )

    @staticmethod
    def _expire_user_mission_if_needed(user_mission):
        mission = user_mission.mission

        if (
            mission.end_time is not None
            and timezone.now() >= mission.end_time
            and user_mission.status != "COMPLETED"
        ):
            user_mission.status = "EXPIRED"

            user_mission.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

            return True

        return False

    @staticmethod
    @transaction.atomic
    def assign_mission(user, mission):

        if not mission.is_active:
            raise ValidationError(
                "این ماموریت فعال نیست."
            )

        if (
            mission.end_time is not None
            and timezone.now() >= mission.end_time
        ):
            raise ValidationError(
                "ددلاین این ماموریت به پایان رسیده است."
            )

        if not user.is_active:
            raise ValidationError(
                "این کاربر فعال نیست."
            )

        user_mission, created = (
            UserMission.objects.get_or_create(
                user=user,
                mission=mission,
                defaults={
                    "progress": 0,
                    "status": "PENDING",
                },
            )
        )

        return user_mission, created

    @staticmethod
    @transaction.atomic
    def start_mission(user, mission):

        if not mission.is_active:
            raise ValidationError(
                "این ماموریت فعال نیست."
            )

        try:
            user_mission = (
                UserMission.objects
                .select_for_update()
                .get(
                    user=user,
                    mission=mission,
                )
            )
        except UserMission.DoesNotExist:
            raise ValidationError(
                "این ماموریت به شما اختصاص داده نشده است."
            )

        if MissionService._expire_user_mission_if_needed(
            user_mission
        ):
            raise ValidationError(
                "ددلاین این ماموریت به پایان رسیده است."
            )

        MissionService._validate_mission_schedule(
            mission
        )

        if user_mission.status == "COMPLETED":
            return user_mission, False

        if user_mission.status == "PENDING":
            user_mission.status = "IN_PROGRESS"

            user_mission.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

        return user_mission, False

    @staticmethod
    @transaction.atomic
    def update_progress(user, mission, progress):

        if not mission.is_active:
            raise ValidationError(
                "این ماموریت فعال نیست."
            )

        if not 0 <= progress <= 100:
            raise ValidationError(
                "درصد پیشرفت باید بین 0 تا 100 باشد."
            )

        try:
            user_mission = (
                UserMission.objects
                .select_for_update()
                .get(
                    user=user,
                    mission=mission,
                )
            )
        except UserMission.DoesNotExist:
            raise ValidationError(
                "این ماموریت به شما اختصاص داده نشده است."
            )

        if MissionService._expire_user_mission_if_needed(
            user_mission
        ):
            raise ValidationError(
                "ددلاین این ماموریت به پایان رسیده است."
            )

        MissionService._validate_mission_schedule(
            mission
        )

        # A completed mission is immutable.
        # No progress update and no reward processing.
        if user_mission.status == "COMPLETED":
            return user_mission, None

        user_mission.progress = progress

        if progress == 0:
            user_mission.status = "PENDING"

        elif progress < 100:
            user_mission.status = "IN_PROGRESS"

        else:
            user_mission.status = "COMPLETED"

        user_mission.save(
            update_fields=[
                "progress",
                "status",
                "updated_at",
            ]
        )

        reward = None

        if user_mission.status == "COMPLETED":
            reward = MissionService._handle_completion(
                user_mission
            )

        return user_mission, reward

    @staticmethod
    def complete_mission(user, mission):

        if not mission.is_active:
            raise ValidationError(
                "این ماموریت فعال نیست."
            )

        try:
            user_mission = (
                UserMission.objects
                .select_for_update()
                .select_related(
                    "user",
                    "mission",
                )
                .get(
                    user=user,
                    mission=mission,
                )
            )
        except UserMission.DoesNotExist:
            raise ValidationError(
                "این ماموریت به شما اختصاص داده نشده است."
            )

        # --------------------------------------------------
        # Expire mission after deadline
        # --------------------------------------------------
        #
        # This must be committed before raising ValidationError.
        # Otherwise an outer atomic transaction would roll back
        # the EXPIRED status.
        # --------------------------------------------------

        if (
            mission.end_time is not None
            and timezone.now() >= mission.end_time
            and user_mission.status != "COMPLETED"
        ):
            user_mission.status = "EXPIRED"

            user_mission.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

            raise ValidationError(
                "ددلاین این ماموریت به پایان رسیده است."
            )

        MissionService._validate_mission_schedule(
            mission
        )

        # --------------------------------------------------
        # Idempotency guard
        # --------------------------------------------------
        #
        # select_for_update() prevents concurrent completion
        # requests from processing the reward twice.
        #
        # A completed mission remains immutable.
        # --------------------------------------------------

        if user_mission.status == "COMPLETED":
            return user_mission, None

        if user_mission.status == "PENDING":
            raise ValidationError(
                "ابتدا باید ماموریت را شروع کنید."
            )

        with transaction.atomic():

            user_mission.progress = 100
            user_mission.status = "COMPLETED"

            user_mission.save(
                update_fields=[
                    "progress",
                    "status",
                    "updated_at",
                ]
            )

            reward = MissionService._handle_completion(
                user_mission
            )

        return user_mission, reward

    @staticmethod
    @transaction.atomic
    def _handle_completion(user_mission):

        user = user_mission.user
        mission = user_mission.mission

        point_result = RewardService.award_points(
            user=user,
            points=mission.points,
        )

        badges = BadgeService.check_automatic_badges(
            user=user
        )

        return {
            "points": point_result["points"],
            "level_up": point_result["level_up"],
            "badges": badges,
        }