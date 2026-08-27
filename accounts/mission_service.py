from django.db import transaction
from django.core.exceptions import ValidationError

from .models import Mission, UserMission
from .services import PointService, BadgeService


class MissionService:

    @staticmethod
    @transaction.atomic
    def start_mission(user, mission):
        """
        Start a mission for a user.

        If the mission is already assigned to the user,
        the existing UserMission will be returned.
        """

        if not mission.is_active:
            raise ValidationError(
                "این ماموریت فعال نیست."
            )

        user_mission, created = UserMission.objects.get_or_create(
            user=user,
            mission=mission,
            defaults={
                "progress": 0,
                "status": "IN_PROGRESS",
            },
        )

        return user_mission, created

    @staticmethod
    @transaction.atomic
    def update_progress(user, mission, progress):
        """
        Update mission progress.

        Progress must be between 0 and 100.
        """

        if not mission.is_active:
            raise ValidationError(
                "این ماموریت فعال نیست."
            )

        if not 0 <= progress <= 100:
            raise ValidationError(
                "درصد پیشرفت باید بین 0 تا 100 باشد."
            )

        user_mission, created = UserMission.objects.get_or_create(
            user=user,
            mission=mission,
            defaults={
                "progress": 0,
                "status": "PENDING",
            },
        )

        # Completed missions must not be moved backwards.
        if user_mission.status == "COMPLETED":
            return user_mission

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

        if user_mission.status == "COMPLETED":
            MissionService._handle_completion(
                user_mission
            )

        return user_mission

    @staticmethod
    @transaction.atomic
    def complete_mission(user, mission):
        """
        Complete a mission for a user.

        This method is idempotent:
        completing the same mission twice will not
        award points twice.
        """

        if not mission.is_active:
            raise ValidationError(
                "این ماموریت فعال نیست."
            )

        user_mission, created = UserMission.objects.get_or_create(
            user=user,
            mission=mission,
            defaults={
                "progress": 100,
                "status": "COMPLETED",
            },
        )

        if not created:

            # Already completed.
            if user_mission.status == "COMPLETED":
                return user_mission

            user_mission.progress = 100
            user_mission.status = "COMPLETED"

            user_mission.save(
                update_fields=[
                    "progress",
                    "status",
                    "updated_at",
                ]
            )

            MissionService._handle_completion(
                user_mission
            )

        else:
            MissionService._handle_completion(
                user_mission
            )

        return user_mission

    @staticmethod
    def _handle_completion(user_mission):
        """
        Handle all business logic that should happen
        after a mission is completed.
        """

        user = user_mission.user
        mission = user_mission.mission

        # Award mission points.
        PointService.award_points(
            user=user,
            points=mission.points,
        )

        # Check automatic badges.
        BadgeService.check_automatic_badges(
            user=user
        )