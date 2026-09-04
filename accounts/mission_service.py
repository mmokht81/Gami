from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Mission, UserMission
from .reward_service import (
    RewardService,
    BadgeRewardService,
)


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
    @transaction.atomic
    def assign_mission(user, mission):

        if not mission.is_active:
            raise ValidationError(
                "این ماموریت فعال نیست."
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
    @transaction.atomic
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
        # Idempotency guard
        # --------------------------------------------------
        #
        # Because the row is locked with select_for_update(),
        # concurrent completion requests cannot both process
        # the reward.
        #
        # The first request completes the mission and awards
        # the reward.
        #
        # Any later request sees COMPLETED and returns without
        # awarding points, levels or badges again.
        # --------------------------------------------------

        if user_mission.status == "COMPLETED":
            return user_mission, None

        if user_mission.status == "PENDING":
            raise ValidationError(
                "ابتدا باید ماموریت را شروع کنید."
            )

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

        badges = (
            BadgeRewardService.check_automatic_badges(
                user=user
            )
        )

        return {
            "points": point_result["points"],
            "level_up": point_result["level_up"],
            "badges": badges,
        }