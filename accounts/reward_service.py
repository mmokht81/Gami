from dataclasses import dataclass, field

from django.db import transaction
from django.db.models import F

from .models import (
    User,
    Badge,
    UserBadge,
    UserMission,
    Level,
    BadgeRule,
)


@dataclass
class LevelUpResult:
    from_level: int
    to_level: int


@dataclass
class RewardResult:
    points: int
    level_up: LevelUpResult | None = None
    badges: list = field(default_factory=list)


class LevelService:
    """
    Central service for dynamic level calculation.

    Level thresholds are stored in the database and can be
    configured by the admin.

    Current default configuration:
        Level 1 -> 0 points
        Level 2 -> 100 points
        Level 3 -> 200 points
        ...
    """

    @staticmethod
    def calculate_level(points, current_level=None):
        """
        Calculate the highest active level the user has reached
        based on the configured required_points values.
        """

        level = (
            Level.objects
            .filter(
                is_active=True,
                required_points__lte=points,
            )
            .order_by("-required_points")
            .first()
        )

        if level is None:
            return current_level or 1

        return level.level

    @staticmethod
    def update_level(user):
        """
        Recalculate and persist the user's level.

        Returns:
            {
                "old_level": int,
                "new_level": int,
                "level_up": bool,
            }
        """

        old_level = user.level

        new_level = LevelService.calculate_level(
            points=user.points,
            current_level=old_level,
        )

        if new_level != old_level:
            user.level = new_level
            user.save(update_fields=["level"])

        return {
            "old_level": old_level,
            "new_level": new_level,
            "level_up": new_level > old_level,
        }


class RewardService:

    @staticmethod
    @transaction.atomic
    def award_points(
        user,
        points,
        sync_automatic_missions=True,
    ):
        if points < 0:
            raise ValueError("points cannot be negative.")

        if points > 0:
            user.points = F("points") + points
            user.save(update_fields=["points"])
            user.refresh_from_db(
                fields=["points", "level"]
            )

        level_result = LevelService.update_level(user)

        if (
            level_result["level_up"]
            and level_result["new_level"] == 1
        ):
            from .services import OnboardingService

            OnboardingService.ensure_for_level_one_user(user)

        automatic_rewards = []

        if sync_automatic_missions:
            from .automatic_mission_service import (
                AutomaticMissionService,
            )

            completed_missions = (
                AutomaticMissionService.sync_all_for_user(user)
            )

            for user_mission in completed_missions:
                mission = user_mission.mission

                automatic_reward = RewardService.award_points(
                    user=user,
                    points=mission.points,
                    sync_automatic_missions=False,
                )

                automatic_rewards.append(
                    {
                        "mission": mission.name,
                        "points": automatic_reward["points"],
                        "level_up": automatic_reward["level_up"],
                    }
                )

        level_up = None

        if level_result["level_up"]:
            level_up = LevelUpResult(
                from_level=level_result["old_level"],
                to_level=level_result["new_level"],
            )

        return {
            "points": user.points,
            "level_up": level_up,
            "automatic_rewards": automatic_rewards,
        }


class BadgeRewardService:

    @staticmethod
    def assign_badge(user, badge, reason):
        """
        Assign a badge to a user only once.

        Returns:
            (UserBadge, created)
        """

        user_badge, created = UserBadge.objects.get_or_create(
            user=user,
            badge=badge,
            defaults={
                "reason": reason,
            },
        )

        return user_badge, created

    @staticmethod
    def check_automatic_badges(user):
        """
        Check active automatic badge rules.

        Currently supported rule:
            MISSION_COUNT

        Only newly awarded badges are returned.
        """

        newly_awarded = []

        completed_missions = UserMission.objects.filter(
            user=user,
            status="COMPLETED",
        ).count()

        rules = (
            BadgeRule.objects
            .filter(
                is_active=True,
                badge__is_active=True,
            )
            .select_related("badge")
        )

        for rule in rules:

            if rule.rule_type != "MISSIONS_COMPLETED":
                continue

            if completed_missions < rule.value:
                continue

            user_badge, created = (
                BadgeRewardService.assign_badge(
                    user=user,
                    badge=rule.badge,
                    reason=(
                        f"تکمیل حداقل "
                        f"{rule.value} ماموریت"
                    ),
                )
            )

            if created:
                newly_awarded.append(user_badge)

        return newly_awarded


class RewardResponseBuilder:

    @staticmethod
    def build(user, level_up=None, badges=None):
        """
        Build the standardized reward payload used by completion APIs.
        """

        if badges is None:
            badges = []

        return {
            "points": user.points,
            "rewards": {
                "level_up": (
                    {
                        "from": level_up.from_level,
                        "to": level_up.to_level,
                    }
                    if level_up
                    else None
                ),
                "badges": [
                    {
                        "id": badge.badge.name,
                        "name": badge.badge.label,
                        "description": badge.badge.description,
                        "icon": badge.badge.icon,
                    }
                    for badge in badges
                ],
            },
        }