from dataclasses import dataclass, field

from django.db import transaction
from django.db.models import F

from .models import User, Badge, UserBadge, UserMission, Level


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
    def award_points(user, points):
        """
        Award points and update level.

        Returns a RewardResult containing:
        - current points
        - level-up information
        """

        if points < 0:
            raise ValueError("points cannot be negative.")

        if points > 0:
            user.points = F("points") + points
            user.save(update_fields=["points"])
            user.refresh_from_db(fields=["points", "level"])

        level_result = LevelService.update_level(user)

        level_up = None

        if level_result["level_up"]:
            level_up = LevelUpResult(
                from_level=level_result["old_level"],
                to_level=level_result["new_level"],
            )

        return {
            "points": user.points,
            "level_up": level_up,
        }


class BadgeRewardService:

    HERO_BADGE_NAME = "hero"

    @staticmethod
    def assign_badge(user, badge, reason):
        """
        Assign a badge only once.

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
        Check automatic badge rules.

        Returns only badges newly awarded during this operation.
        """

        newly_awarded = []

        completed_missions = UserMission.objects.filter(
            user=user,
            status="COMPLETED",
        ).count()

        if completed_missions >= 5:

            try:
                badge = Badge.objects.get(
                    name=BadgeRewardService.HERO_BADGE_NAME,
                    is_active=True,
                )
            except Badge.DoesNotExist:
                return newly_awarded

            user_badge, created = (
                BadgeRewardService.assign_badge(
                    user=user,
                    badge=badge,
                    reason="تکمیل حداقل ۵ ماموریت",
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