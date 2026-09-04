from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import (
    TrainingCourse,
    TrainingSection,
    UserTraining,
    UserTrainingSection,
)
from .reward_service import RewardService


class TrainingService:
    """
    Central service for managing the complete training lifecycle.

    Training flow:

        Course
          ↓
        Enrollment
          ↓
        Start Section
          ↓
        Progress
          ↓
        Complete Course
          ↓
        Points
          ↓
        Level
    """

    @staticmethod
    @transaction.atomic
    def enroll_user(user, course):
        """
        Enroll a user in an active training course.

        Rules:
        1. Course must be active.
        2. User must be active.
        3. User can enroll in multiple courses.
        4. Same user cannot enroll in the same course twice.
        5. Course capacity is respected when configured.

        Returns:
            (UserTraining, created)
        """

        if not course.is_active:
            raise ValidationError(
                "این دوره فعال نیست."
            )

        if not user.is_active:
            raise ValidationError(
                "این کاربر فعال نیست."
            )

        existing = (
            UserTraining.objects
            .filter(
                user=user,
                course=course,
            )
            .first()
        )

        if existing is not None:
            raise ValidationError(
                "شما قبلاً در این دوره ثبت نام کرده‌اید."
            )

        # Lock the course row to prevent capacity race conditions.
        course = (
            TrainingCourse.objects
            .select_for_update()
            .get(
                id=course.id
            )
        )

        if not course.is_active:
            raise ValidationError(
                "این دوره فعال نیست."
            )

        if course.is_full:
            raise ValidationError(
                "ظرفیت این دوره تکمیل شده است."
            )

        user_training = UserTraining.objects.create(
            user=user,
            course=course,
            progress=0,
            status="ENROLLED",
        )

        return user_training, True

    @staticmethod
    @transaction.atomic
    def start_section(user, course, section):
        """
        Start a training section for an enrolled user.

        Starting a section automatically updates course progress.

        For SINGLE courses:
            Opening the only section -> 100%

        For MULTI courses:
            Progress = started sections / total sections * 100

        When the final section is started:
            - progress becomes 100
            - course becomes COMPLETED
            - points are awarded once

        Returns:
            (UserTraining, reward, created)
        """

        if not course.is_active:
            raise ValidationError(
                "این دوره فعال نیست."
            )

        # Make sure the section belongs to this course.
        if section.course_id != course.id:
            raise ValidationError(
                "این بخش متعلق به این دوره نیست."
            )

        # Lock the user's enrollment row.
        try:
            user_training = (
                UserTraining.objects
                .select_for_update()
                .select_related(
                    "user",
                    "course",
                )
                .get(
                    user=user,
                    course=course,
                )
            )

        except UserTraining.DoesNotExist:
            raise ValidationError(
                "ابتدا باید در این دوره ثبت نام کنید."
            )

        # Completed courses remain completed.
        if user_training.status == "COMPLETED":
            return user_training, None, False

        # Create section progress only once.
        started_section, created = (
            UserTrainingSection.objects.get_or_create(
                user_training=user_training,
                section=section,
            )
        )

        # If this section was already started, do not
        # recalculate or award rewards again.
        if not created:
            return user_training, None, False

        total_sections = (
            TrainingSection.objects
            .filter(
                course=course,
            )
            .count()
        )

        if total_sections == 0:
            raise ValidationError(
                "این دوره هنوز هیچ بخشی ندارد."
            )

        started_sections = (
            UserTrainingSection.objects
            .filter(
                user_training=user_training,
            )
            .count()
        )

        progress = round(
            started_sections * 100 / total_sections
        )

        if progress > 100:
            progress = 100

        user_training.progress = progress

        reward = None

        if started_sections >= total_sections:
            user_training.progress = 100
            user_training.status = "COMPLETED"
            user_training.completed_at = timezone.now()

            user_training.save(
                update_fields=[
                    "progress",
                    "status",
                    "completed_at",
                ]
            )

            reward = TrainingService._handle_completion(
                user_training
            )

        else:
            user_training.status = "IN_PROGRESS"

            user_training.save(
                update_fields=[
                    "progress",
                    "status",
                ]
            )

        return user_training, reward, created

    @staticmethod
    @transaction.atomic
    def _handle_completion(user_training):
        """
        Handle rewards generated by training completion.

        Points are awarded exactly once because this method
        is called only when the UserTraining transitions
        from an incomplete state to COMPLETED.
        """

        user = user_training.user
        course = user_training.course

        point_result = RewardService.award_points(
            user=user,
            points=course.points,
        )

        return {
            "points": point_result["points"],
            "level_up": point_result["level_up"],
            "badges": [],
        }

    @staticmethod
    def get_user_trainings(user):
        """
        Return all courses in which the user is enrolled.
        """

        return (
            UserTraining.objects
            .filter(
                user=user,
            )
            .select_related(
                "course",
            )
            .prefetch_related(
                "started_sections__section",
                "course__sections",
            )
            .order_by(
                "-enrolled_at"
            )
        )

    @staticmethod
    def get_user_training(user, course):
        """
        Return a specific user's enrollment in a course.
        """

        try:
            return (
                UserTraining.objects
                .select_related(
                    "course",
                )
                .prefetch_related(
                    "started_sections__section",
                    "course__sections",
                )
                .get(
                    user=user,
                    course=course,
                )
            )

        except UserTraining.DoesNotExist:
            raise ValidationError(
                "شما در این دوره ثبت نام نکرده‌اید."
            )