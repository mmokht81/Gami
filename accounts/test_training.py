from django.test import TestCase
from django.core.exceptions import ValidationError

from .models import (
    User,
    Level,
    TrainingCourse,
    TrainingSection,
    UserTraining,
    UserTrainingSection,
)
from .training_service import TrainingService


class TrainingServiceTests(TestCase):

    def setUp(self):
        Level.objects.create(
            level=1,
            required_points=0,
            is_active=True,
        )

        Level.objects.create(
            level=2,
            required_points=100,
            is_active=True,
        )

        self.user = User.objects.create_user(
            phone_number="09123334444",
            password="testpass123",
        )

        self.course = TrainingCourse.objects.create(
            delivery_type="ONLINE",
            structure="MULTI",
            name="Django Training",
            description="Django backend training",
            instructor_name="Test Instructor",
            duration="10 hours",
            sessions_count=2,
            points=50,
            is_active=True,
        )

        self.section_1 = TrainingSection.objects.create(
            course=self.course,
            title="Introduction",
            description="Introduction section",
            order=1,
        )

        self.section_2 = TrainingSection.objects.create(
            course=self.course,
            title="Django REST",
            description="DRF section",
            order=2,
        )

    def test_user_can_enroll_in_training(self):

        user_training, created = TrainingService.enroll_user(
            user=self.user,
            course=self.course,
        )

        self.assertTrue(created)

        self.assertEqual(
            user_training.user,
            self.user,
        )

        self.assertEqual(
            user_training.course,
            self.course,
        )

        self.assertEqual(
            user_training.progress,
            0,
        )

        self.assertEqual(
            user_training.status,
            "ENROLLED",
        )

    def test_user_cannot_enroll_twice(self):

        TrainingService.enroll_user(
            user=self.user,
            course=self.course,
        )

        with self.assertRaises(ValidationError):
            TrainingService.enroll_user(
                user=self.user,
                course=self.course,
            )

        self.assertEqual(
            UserTraining.objects.filter(
                user=self.user,
                course=self.course,
            ).count(),
            1,
        )

    def test_user_cannot_start_section_without_enrollment(self):

        with self.assertRaises(ValidationError):
            TrainingService.start_section(
                user=self.user,
                course=self.course,
                section=self.section_1,
            )

    def test_start_first_section_updates_progress(self):

        TrainingService.enroll_user(
            user=self.user,
            course=self.course,
        )

        user_training, reward, created = (
            TrainingService.start_section(
                user=self.user,
                course=self.course,
                section=self.section_1,
            )
        )

        self.assertTrue(created)

        self.assertEqual(
            user_training.progress,
            50,
        )

        self.assertEqual(
            user_training.status,
            "IN_PROGRESS",
        )

        self.assertIsNone(reward)

        self.assertEqual(
            UserTrainingSection.objects.filter(
                user_training=user_training,
            ).count(),
            1,
        )

    def test_start_same_section_twice_does_not_award_reward(self):

        TrainingService.enroll_user(
            user=self.user,
            course=self.course,
        )

        first_training, first_reward, first_created = (
            TrainingService.start_section(
                user=self.user,
                course=self.course,
                section=self.section_1,
            )
        )

        self.user.refresh_from_db()

        points_after_first_start = self.user.points

        second_training, second_reward, second_created = (
            TrainingService.start_section(
                user=self.user,
                course=self.course,
                section=self.section_1,
            )
        )

        self.user.refresh_from_db()

        self.assertFalse(second_created)

        self.assertIsNone(second_reward)

        self.assertEqual(
            self.user.points,
            points_after_first_start,
        )

        self.assertEqual(
            UserTrainingSection.objects.filter(
                user_training=first_training,
                section=self.section_1,
            ).count(),
            1,
        )

    def test_final_section_completes_training_and_awards_points(self):

        TrainingService.enroll_user(
            user=self.user,
            course=self.course,
        )

        TrainingService.start_section(
            user=self.user,
            course=self.course,
            section=self.section_1,
        )

        user_training, reward, created = (
            TrainingService.start_section(
                user=self.user,
                course=self.course,
                section=self.section_2,
            )
        )

        self.assertTrue(created)

        self.assertEqual(
            user_training.progress,
            100,
        )

        self.assertEqual(
            user_training.status,
            "COMPLETED",
        )

        self.assertIsNotNone(reward)

        self.user.refresh_from_db()

        self.assertEqual(
            self.user.points,
            60,
        )

        self.assertEqual(
            reward["points"],
            60,
        )

        self.assertIsNotNone(
            reward["level_up"]
        )

        self.assertEqual(
            reward["level_up"].from_level,
            0,
        )

        self.assertEqual(
            reward["level_up"].to_level,
            1,
        )

    def test_completed_training_cannot_award_points_again(self):

        TrainingService.enroll_user(
            user=self.user,
            course=self.course,
        )

        TrainingService.start_section(
            user=self.user,
            course=self.course,
            section=self.section_1,
        )

        TrainingService.start_section(
            user=self.user,
            course=self.course,
            section=self.section_2,
        )

        self.user.refresh_from_db()

        first_points = self.user.points

        user_training, reward, created = (
            TrainingService.start_section(
                user=self.user,
                course=self.course,
                section=self.section_2,
            )
        )

        self.user.refresh_from_db()

        self.assertEqual(
            self.user.points,
            first_points,
        )

        self.assertIsNone(reward)

        self.assertFalse(created)

        self.assertEqual(
            user_training.status,
            "COMPLETED",
        )

        self.assertEqual(
            user_training.progress,
            100,
        )

    def test_inactive_course_cannot_be_enrolled(self):

        self.course.is_active = False
        self.course.save(update_fields=["is_active"])

        with self.assertRaises(ValidationError):
            TrainingService.enroll_user(
                user=self.user,
                course=self.course,
            )

        self.assertFalse(
            UserTraining.objects.filter(
                user=self.user,
                course=self.course,
            ).exists()
        )

    def test_section_from_another_course_is_rejected(self):

        other_course = TrainingCourse.objects.create(
            delivery_type="ONLINE",
            structure="SINGLE",
            name="Other Training",
            instructor_name="Other Instructor",
            points=20,
            is_active=True,
        )

        other_section = TrainingSection.objects.create(
            course=other_course,
            title="Other Section",
            order=1,
        )

        TrainingService.enroll_user(
            user=self.user,
            course=self.course,
        )

        with self.assertRaises(ValidationError):
            TrainingService.start_section(
                user=self.user,
                course=self.course,
                section=other_section,
            )