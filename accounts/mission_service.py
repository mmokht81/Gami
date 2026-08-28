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
        """
        Assign an active mission to an active user.

        Returns:
            (UserMission, created)

        The same mission cannot be assigned to the same
        user more than once.
        """

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
        """
        Start a mission that has already been assigned
        to the user.

        A user cannot start a mission that has not been
        assigned to them.

        Returns:
            (UserMission, created)

        created is always False because the UserMission
        must already exist before starting.
        """

        if not mission.is_active:
            raise ValidationError(
                "این ماموریت فعال نیست."
            )

        try:
            user_mission = UserMission.objects.get(
                user=user,
                mission=mission,
            )
        except UserMission.DoesNotExist:
            raise ValidationError(
                "این ماموریت به شما اختصاص داده نشده است."
            )

        # Already completed missions stay completed.
        if user_mission.status == "COMPLETED":
            return user_mission, False

        # Start pending mission.
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
        """
        Update the progress of an assigned mission.

        Progress must be between 0 and 100.

        If progress reaches 100, the mission is completed
        automatically and rewards are processed.
        """

        if not mission.is_active:
            raise ValidationError(
                "این ماموریت فعال نیست."
            )

        if not 0 <= progress <= 100:
            raise ValidationError(
                "درصد پیشرفت باید بین 0 تا 100 باشد."
            )

        try:
            user_mission = UserMission.objects.get(
                user=user,
                mission=mission,
            )
        except UserMission.DoesNotExist:
            raise ValidationError(
                "این ماموریت به شما اختصاص داده نشده است."
            )

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
        """
        Complete an assigned and started mission.

        Rules:

        1. Mission must be active.
        2. Mission must be assigned to the user.
        3. Mission must be started first.
        4. A completed mission cannot be completed again.
        5. Points and badges are awarded only once.

        Returns:
            (UserMission, reward)
        """

        if not mission.is_active:
            raise ValidationError(
                "این ماموریت فعال نیست."
            )

        try:
            user_mission = UserMission.objects.get(
                user=user,
                mission=mission,
            )
        except UserMission.DoesNotExist:
            raise ValidationError(
                "این ماموریت به شما اختصاص داده نشده است."
            )


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
        """
        Handle all rewards generated by mission completion.

        Flow:

            Mission Completion
                    ↓
                 Points
                    ↓
                  Level
                    ↓
            Automatic Badges
                    ↓
              Reward Result

        Returns a standardized reward dictionary:

            {
                "points": int,
                "level_up": LevelUpResult | None,
                "badges": list,
            }
        """

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