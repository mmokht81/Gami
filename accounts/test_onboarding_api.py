from django.test import TestCase
from rest_framework.test import APIClient

from .models import (
    User,
    Level,
    JobPosition,
    JobApplication,
    Onboarding,
    OnboardingChecklistItem,
    Team,
)
from .services import OnboardingService


class OnboardingAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()

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
            phone_number="09122222222",
            password="testpass123",
        )

        self.admin = User.objects.create_user(
            phone_number="09123333333",
            password="adminpass123",
            role="ADMIN",
        )

        self.job_position = JobPosition.objects.create(
            title="Backend Developer",
            description="Django backend developer",
            is_active=True,
        )

        self.other_job_position = JobPosition.objects.create(
            title="Frontend Developer",
            description="React frontend developer",
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
            title="Attend meeting",
            type="MEETING",
            points=20,
            order=2,
            is_active=True,
        )

        self.other_item = OnboardingChecklistItem.objects.create(
            job_position=self.other_job_position,
            title="Frontend setup",
            type="TECHNICAL",
            points=30,
            order=1,
            is_active=True,
        )

        self.application = JobApplication.objects.create(
            user=self.user,
            job_position=self.job_position,
            status="ACCEPTED",
        )

        self.user.level = 1
        self.user.save(update_fields=["level"])

        self.onboarding = OnboardingService.ensure_for_level_one_user(
            self.user
        )

        self.team = Team.objects.create(
            name="Backend Team",
            is_active=True,
        )

        self.inactive_team = Team.objects.create(
            name="Inactive Team",
            is_active=False,
        )

    # --------------------------------------------------
    # GET MY ONBOARDING
    # --------------------------------------------------

    def test_user_can_get_own_onboarding(self):
        self.user.level = 1
        self.user.save(update_fields=["level"])

        self.client.force_authenticate(
            user=self.user
        )

        response = self.client.get(
            "/api/onboarding/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["user"],
            self.user.id,
        )

        self.assertEqual(
            response.data["job_position"]["id"],
            self.job_position.id,
        )

        self.assertEqual(
            response.data["checklist_progress"],
            0,
        )

        self.assertEqual(
            response.data["hr_progress"],
            0,
        )

        self.assertEqual(
            response.data["progress"],
            0,
        )

    def test_unauthenticated_user_cannot_get_onboarding(self):
        self.client.force_authenticate(
            user=None
        )

        response = self.client.get(
            "/api/onboarding/"
        )

        self.assertEqual(
            response.status_code,
            401,
        )

    # --------------------------------------------------
    # COMPLETE CHECKLIST
    # --------------------------------------------------

    def test_user_can_complete_checklist_item(self):
        self.client.force_authenticate(
            user=self.user
        )

        response = self.client.post(
            "/api/onboarding/checklist/complete/",
            {
                "checklist_item_id": self.item_1.id
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.onboarding.refresh_from_db()

        self.assertEqual(
            self.onboarding.checklist_progress,
            50,
        )

        self.assertEqual(
            self.onboarding.progress,
            35,
        )

    def test_user_cannot_complete_item_from_other_job_position(self):
        self.client.force_authenticate(
            user=self.user
        )

        response = self.client.post(
            "/api/onboarding/checklist/complete/",
            {
                "checklist_item_id": self.other_item.id
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    def test_user_cannot_complete_inactive_checklist_item(self):
        self.item_1.is_active = False
        self.item_1.save(update_fields=["is_active"])

        self.client.force_authenticate(
            user=self.user
        )

        response = self.client.post(
            "/api/onboarding/checklist/complete/",
            {
                "checklist_item_id": self.item_1.id
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    # --------------------------------------------------
    # HR PROGRESS
    # --------------------------------------------------

    def test_admin_can_update_hr_progress(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.patch(
            f"/api/onboarding/users/{self.user.id}/hr-progress/",
            {
                "hr_progress": 50
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.onboarding.refresh_from_db()

        self.assertEqual(
            self.onboarding.hr_progress,
            50,
        )

        self.assertEqual(
            self.onboarding.progress,
            15,
        )

    def test_admin_cannot_set_invalid_hr_progress(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.patch(
            f"/api/onboarding/users/{self.user.id}/hr-progress/",
            {
                "hr_progress": 101
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    def test_normal_user_cannot_update_hr_progress(self):
        self.client.force_authenticate(
            user=self.user
        )

        response = self.client.patch(
            f"/api/onboarding/users/{self.user.id}/hr-progress/",
            {
                "hr_progress": 50
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    # --------------------------------------------------
    # TEAM ASSIGNMENT
    # --------------------------------------------------

    def test_admin_can_assign_team(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.patch(
            f"/api/onboarding/users/{self.user.id}/team/",
            {
                "team_id": self.team.id
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.onboarding.refresh_from_db()

        self.assertEqual(
            self.onboarding.team_id,
            self.team.id,
        )

    def test_admin_cannot_assign_inactive_team(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.patch(
            f"/api/onboarding/users/{self.user.id}/team/",
            {
                "team_id": self.inactive_team.id
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_normal_user_cannot_assign_team(self):
        self.client.force_authenticate(
            user=self.user
        )

        response = self.client.patch(
            f"/api/onboarding/users/{self.user.id}/team/",
            {
                "team_id": self.team.id
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    # --------------------------------------------------
    # ADMIN VIEW
    # --------------------------------------------------

    def test_admin_can_view_user_onboarding(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.get(
            f"/api/onboarding/users/{self.user.id}/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["user"],
            self.user.id,
        )

    def test_normal_user_cannot_view_other_user_onboarding(self):
        self.client.force_authenticate(
            user=self.user
        )

        response = self.client.get(
            f"/api/onboarding/users/{self.admin.id}/"
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_level_one_user_without_existing_onboarding_gets_onboarding_automatically(self):

        # Delete the existing onboarding
        Onboarding.objects.filter(
            user=self.user
        ).delete()

        self.client.force_authenticate(
            user=self.user
        )

        response = self.client.get(
            "/api/onboarding/"
        )

        self.assertEqual(
            response.status_code,
            200,
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
            onboarding.user,
            self.user,
        )

        self.assertEqual(
            onboarding.job_position,
            self.job_position,
        )
    def test_admin_can_assign_team_even_if_onboarding_does_not_exist(self):

        Onboarding.objects.filter(
            user=self.user
        ).delete()

        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.patch(
            f"/api/onboarding/users/{self.user.id}/team/",
            {
                "team_id": self.team.id
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        onboarding = Onboarding.objects.get(
            user=self.user
        )

        self.assertEqual(
            onboarding.team_id,
            self.team.id,
        )