from django.test import TestCase

from .models import (
    JobApplication,
    JobPosition,
    Level,
    Onboarding,
    OnboardingChecklistItem,
    OnboardingChecklistProgress,
    User,
)
from .services import OnboardingService
from .reward_service import RewardService


class OnboardingServiceTests(TestCase):

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
            phone_number="09121111111",
            password="testpass123",
        )

        self.job_position = JobPosition.objects.create(
            title="Backend Developer",
            description="Django backend developer",
            is_active=True,
        )

        self.item_1 = OnboardingChecklistItem.objects.create(
            job_position=self.job_position,
            title="Complete profile",
            type="PROFILE",
            points=10,
            order=1,
            is_active=True,
        )

        self.item_2 = OnboardingChecklistItem.objects.create(
            job_position=self.job_position,
            title="Attend introduction meeting",
            type="MEETING",
            points=20,
            order=2,
            is_active=True,
        )

        self.application = JobApplication.objects.create(
            user=self.user,
            job_position=self.job_position,
            status="ACCEPTED",
        )

    def test_level_one_accepted_user_gets_onboarding(self):
        self.user.level = 1
        self.user.save(update_fields=["level"])

        onboarding = OnboardingService.ensure_for_level_one_user(
            self.user
        )

        self.assertIsNotNone(onboarding)
        self.assertEqual(onboarding.user, self.user)
        self.assertEqual(
            onboarding.job_position,
            self.job_position,
        )

        self.assertEqual(
            onboarding.checklist_progress,
            0,
        )

        self.assertEqual(
            onboarding.hr_progress,
            0,
        )

        self.assertEqual(
            onboarding.progress,
            0,
        )

        self.assertEqual(
            OnboardingChecklistProgress.objects.filter(
                onboarding=onboarding,
            ).count(),
            2,
        )

    def test_accepted_user_gets_onboarding_when_reaching_level_one(self):
        self.assertEqual(
            self.user.level,
            0,
        )

        self.assertFalse(
            Onboarding.objects.filter(
                user=self.user
            ).exists()
        )

        RewardService.award_points(
            user=self.user,
            points=10,
        )

        self.user.refresh_from_db()

        self.assertEqual(
            self.user.level,
            1,
        )

        self.assertTrue(
            Onboarding.objects.filter(
                user=self.user
            ).exists()
        )

        onboarding = Onboarding.objects.get(
            user=self.user
        )

        self.assertEqual(
            onboarding.job_position,
            self.job_position,
        )

    def test_onboarding_is_created_only_once(self):
        self.user.level = 1
        self.user.save(update_fields=["level"])

        first = OnboardingService.ensure_for_level_one_user(
            self.user
        )

        second = OnboardingService.ensure_for_level_one_user(
            self.user
        )

        self.assertEqual(
            first.pk,
            second.pk,
        )

        self.assertEqual(
            Onboarding.objects.filter(
                user=self.user
            ).count(),
            1,
        )

    def test_checklist_progress_is_70_percent_of_total_progress(self):
        self.user.level = 1
        self.user.save(update_fields=["level"])

        onboarding = OnboardingService.ensure_for_level_one_user(
            self.user
        )

        OnboardingService.complete_checklist_item(
            onboarding=onboarding,
            checklist_item=self.item_1,
        )

        onboarding.refresh_from_db()

        self.assertEqual(
            onboarding.checklist_progress,
            50,
        )

        self.assertEqual(
            onboarding.hr_progress,
            0,
        )

        self.assertEqual(
            onboarding.progress,
            35,
        )

        OnboardingService.complete_checklist_item(
            onboarding=onboarding,
            checklist_item=self.item_2,
        )

        onboarding.refresh_from_db()

        self.assertEqual(
            onboarding.checklist_progress,
            100,
        )

        self.assertEqual(
            onboarding.progress,
            70,
        )

    def test_hr_progress_contributes_30_percent(self):
        self.user.level = 1
        self.user.save(update_fields=["level"])

        onboarding = OnboardingService.ensure_for_level_one_user(
            self.user
        )

        OnboardingService.set_hr_progress(
            onboarding=onboarding,
            value=50,
        )

        onboarding.refresh_from_db()

        self.assertEqual(
            onboarding.checklist_progress,
            0,
        )

        self.assertEqual(
            onboarding.hr_progress,
            50,
        )

        self.assertEqual(
            onboarding.progress,
            15,
        )

    def test_completed_onboarding_requires_both_parts(self):
        self.user.level = 1
        self.user.save(update_fields=["level"])

        onboarding = OnboardingService.ensure_for_level_one_user(
            self.user
        )

        OnboardingService.complete_checklist_item(
            onboarding=onboarding,
            checklist_item=self.item_1,
        )

        OnboardingService.complete_checklist_item(
            onboarding=onboarding,
            checklist_item=self.item_2,
        )

        OnboardingService.set_hr_progress(
            onboarding=onboarding,
            value=100,
        )

        onboarding.refresh_from_db()

        self.assertEqual(
            onboarding.checklist_progress,
            100,
        )

        self.assertEqual(
            onboarding.hr_progress,
            100,
        )

        self.assertEqual(
            onboarding.progress,
            100,
        )

        self.assertTrue(
            OnboardingService.is_completed(
                onboarding
            )
        )