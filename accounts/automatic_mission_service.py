from django.db import transaction

from .models import Mission, UserMission


class AutomaticMissionService:

    @staticmethod
    def get_user_job_position(user):
        try:
            onboarding = user.onboarding
            if onboarding and onboarding.job_position.is_active:
                return onboarding.job_position
        except Exception:
            return None

        return None

    @staticmethod
    def matches_user(mission, user):
        if mission.type != "AUTOMATIC":
            return False

        if not mission.is_active:
            return False

        if mission.job_position_id:
            user_job_position = (
                AutomaticMissionService.get_user_job_position(user)
            )

            if not user_job_position:
                return False

            if user_job_position.id != mission.job_position_id:
                return False

        return True

    @staticmethod
    def calculate_progress(mission, user):
        if mission.target_level is not None:
            target = mission.target_level

            if user.level >= target:
                return 100

            if target <= 0:
                return 100

            progress = round(
                (user.level / target) * 100
            )

            return min(max(progress, 0), 99)

        if mission.target_points is not None:
            target = mission.target_points

            if user.points >= target:
                return 100

            if target <= 0:
                return 100

            progress = round(
                (user.points / target) * 100
            )

            return min(max(progress, 0), 99)

        return 0

    @staticmethod
    @transaction.atomic
    def sync_mission(user, mission):
        if not AutomaticMissionService.matches_user(
            mission,
            user,
        ):
            return None, None

        user_mission, created = UserMission.objects.get_or_create(
            user=user,
            mission=mission,
            defaults={
                "progress": 0,
                "status": "PENDING",
            },
        )

        if user_mission.status == "COMPLETED":
            return user_mission, None

        progress = AutomaticMissionService.calculate_progress(
            mission,
            user,
        )

        user_mission.progress = progress

        if progress >= 100:
            user_mission.progress = 100
            user_mission.status = "COMPLETED"
            user_mission.save(
                update_fields=[
                    "progress",
                    "status",
                    "updated_at",
                ]
            )

            return user_mission, True

        if progress == 0:
            user_mission.status = "PENDING"
        else:
            user_mission.status = "IN_PROGRESS"

        user_mission.save(
            update_fields=[
                "progress",
                "status",
                "updated_at",
            ]
        )

        return user_mission, False

    @staticmethod
    @transaction.atomic
    def sync_all_for_user(user):
        missions = Mission.objects.filter(
            type="AUTOMATIC",
            is_active=True,
        ).select_related("job_position")

        completed = []

        for mission in missions:
            user_mission, should_reward = (
                AutomaticMissionService.sync_mission(
                    user,
                    mission,
                )
            )

            if should_reward:
                completed.append(user_mission)

        return completed