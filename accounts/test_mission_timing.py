from datetime import timedelta
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from .models import (
    Mission,
    User,
    UserMission,
)
from .mission_service import MissionService


class MissionTimingTests(TestCase):

    def setUp(self):

        self.user = User.objects.create_user(
            phone_number="09121111111",
            password="testpassword123",
        )

        now = timezone.now()

        self.mission = Mission.objects.create(
            name="Timed Mission",
            description="Mission with schedule",
            type="USER",
            points=50,
            is_active=True,
            start_time=now - timedelta(days=1),
            end_time=now + timedelta(days=1),
        )

        UserMission.objects.create(
            user=self.user,
            mission=self.mission,
            progress=0,
            status="PENDING",
        )

    def test_mission_is_active_inside_schedule(self):

        self.assertTrue(
            self.mission.is_time_active
        )

        self.assertFalse(
            self.mission.is_upcoming
        )

        self.assertFalse(
            self.mission.is_expired
        )

    def test_mission_is_upcoming_before_start(self):

        now = timezone.now()

        self.mission.start_time = (
            now + timedelta(days=1)
        )

        self.mission.end_time = (
            now + timedelta(days=2)
        )

        self.mission.save()

        self.assertTrue(
            self.mission.is_upcoming
        )

        self.assertFalse(
            self.mission.is_time_active
        )

    def test_mission_is_expired_after_deadline(self):

        now = timezone.now()

        self.mission.start_time = (
            now - timedelta(days=2)
        )

        self.mission.end_time = (
            now - timedelta(days=1)
        )

        self.mission.save()

        self.assertTrue(
            self.mission.is_expired
        )

        self.assertFalse(
            self.mission.is_time_active
        )

    def test_start_before_start_time_is_rejected(self):

        now = timezone.now()

        self.mission.start_time = (
            now + timedelta(hours=1)
        )

        self.mission.end_time = (
            now + timedelta(days=1)
        )

        self.mission.save()

        with self.assertRaises(ValidationError):

            MissionService.start_mission(
                user=self.user,
                mission=self.mission,
            )

    def test_start_inside_schedule_is_allowed(self):

        user_mission, created = (
            MissionService.start_mission(
                user=self.user,
                mission=self.mission,
            )
        )

        self.assertFalse(created)

        self.assertEqual(
            user_mission.status,
            "IN_PROGRESS",
        )

    def test_start_after_deadline_is_rejected(self):

        now = timezone.now()

        self.mission.start_time = (
            now - timedelta(days=2)
        )

        self.mission.end_time = (
            now - timedelta(hours=1)
        )

        self.mission.save()

        with self.assertRaises(ValidationError):

            MissionService.start_mission(
                user=self.user,
                mission=self.mission,
            )

    def test_progress_after_deadline_is_rejected(self):

        now = timezone.now()

        self.mission.start_time = (
            now - timedelta(days=2)
        )

        self.mission.end_time = (
            now - timedelta(hours=1)
        )

        self.mission.save()

        with self.assertRaises(ValidationError):

            MissionService.update_progress(
                user=self.user,
                mission=self.mission,
                progress=50,
            )

    def test_completion_after_deadline_is_rejected(self):

        now = timezone.now()

        self.mission.start_time = (
            now - timedelta(days=2)
        )

        self.mission.end_time = (
            now - timedelta(hours=1)
        )

        self.mission.save()

        user_mission = UserMission.objects.get(
            user=self.user,
            mission=self.mission,
        )

        user_mission.status = "IN_PROGRESS"
        user_mission.progress = 50
        user_mission.save()

        with self.assertRaises(ValidationError):

            MissionService.complete_mission(
                user=self.user,
                mission=self.mission,
            )

        user_mission.refresh_from_db()

        self.assertEqual(
            user_mission.status,
            "EXPIRED",
        )

    def test_progress_inside_schedule_is_allowed(self):

        MissionService.start_mission(
            user=self.user,
            mission=self.mission,
        )

        user_mission, reward = (
            MissionService.update_progress(
                user=self.user,
                mission=self.mission,
                progress=50,
            )
        )

        self.assertEqual(
            user_mission.progress,
            50,
        )

        self.assertEqual(
            user_mission.status,
            "IN_PROGRESS",
        )

        self.assertIsNone(
            reward
        )

    def test_completion_inside_schedule_awards_reward(self):

        MissionService.start_mission(
            user=self.user,
            mission=self.mission,
        )

        user_mission, reward = (
            MissionService.complete_mission(
                user=self.user,
                mission=self.mission,
            )
        )

        self.assertEqual(
            user_mission.progress,
            100,
        )

        self.assertEqual(
            user_mission.status,
            "COMPLETED",
        )

        self.assertIsNotNone(
            reward
        )

    def test_assign_after_deadline_is_rejected(self):

        now = timezone.now()

        self.mission.start_time = (
            now - timedelta(days=2)
        )

        self.mission.end_time = (
            now - timedelta(hours=1)
        )

        self.mission.save()

        with self.assertRaises(ValidationError):

            MissionService.assign_mission(
                user=self.user,
                mission=self.mission,
            )

    def test_assign_before_start_is_allowed(self):

        now = timezone.now()

        self.mission.start_time = (
            now + timedelta(days=1)
        )

        self.mission.end_time = (
            now + timedelta(days=2)
        )

        self.mission.save()

        UserMission.objects.filter(
            user=self.user,
            mission=self.mission,
        ).delete()

        user_mission, created = (
            MissionService.assign_mission(
                user=self.user,
                mission=self.mission,
            )
        )

        self.assertTrue(created)

        self.assertEqual(
            user_mission.status,
            "PENDING",
        )

    def test_start_must_be_before_end(self):

        now = timezone.now()

        self.mission.start_time = (
            now + timedelta(days=2)
        )

        self.mission.end_time = (
            now + timedelta(days=1)
        )

        with self.assertRaises(ValidationError):

            self.mission.full_clean()

class MissionTimingAPITests(APITestCase):

    def setUp(self):

        self.user = User.objects.create_user(
            phone_number="09122222222",
            password="testpassword123",
        )

        refresh = RefreshToken.for_user(
            self.user
        )

        self.client.credentials(
            HTTP_AUTHORIZATION=(
                f"Bearer {refresh.access_token}"
            )
        )

        now = timezone.now()

        self.mission = Mission.objects.create(
            name="API Timed Mission",
            description="API timing test",
            type="USER",
            points=50,
            is_active=True,
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(days=1),
        )

        UserMission.objects.create(
            user=self.user,
            mission=self.mission,
            status="PENDING",
            progress=0,
        )

    def test_user_cannot_start_mission_before_start_time(self):

        response = self.client.post(
            f"/api/missions/{self.mission.id}/start/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertIn(
            "detail",
            response.data,
        )

    def test_user_can_start_mission_inside_schedule(self):

        now = timezone.now()

        self.mission.start_time = (
            now - timedelta(minutes=1)
        )

        self.mission.end_time = (
            now + timedelta(days=1)
        )

        self.mission.save()

        response = self.client.post(
            f"/api/missions/{self.mission.id}/start/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["status"],
            "IN_PROGRESS",
        )

    def test_user_cannot_complete_mission_after_deadline(self):

        now = timezone.now()

        self.mission.start_time = (
            now - timedelta(days=2)
        )

        self.mission.end_time = (
            now - timedelta(minutes=1)
        )

        self.mission.save()

        user_mission = UserMission.objects.get(
            user=self.user,
            mission=self.mission,
        )

        user_mission.status = "IN_PROGRESS"
        user_mission.progress = 50
        user_mission.save()

        response = self.client.post(
            f"/api/missions/{self.mission.id}/complete/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        user_mission.refresh_from_db()

        self.assertEqual(
            user_mission.status,
            "EXPIRED",
        )
    def test_admin_must_provide_mission_schedule(self):

        admin = User.objects.create_user(
            phone_number="09123333333",
            password="testpassword123",
            role="ADMIN",
        )

        refresh = RefreshToken.for_user(
            admin
        )

        self.client.credentials(
            HTTP_AUTHORIZATION=(
                f"Bearer {refresh.access_token}"
            )
        )

        response = self.client.post(
            "/api/mission-management/",
            {
                "name": "Mission Without Schedule",
                "description": "Invalid mission",
                "type": "HR",
                "points": 100,
                "is_active": True,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertIn(
            "start_time",
            response.data,
        )

        self.assertIn(
            "end_time",
            response.data,
        )

    def test_admin_can_create_scheduled_mission(self):

        admin = User.objects.create_user(
            phone_number="09124444444",
            password="testpassword123",
            role="ADMIN",
        )

        refresh = RefreshToken.for_user(
            admin
        )

        self.client.credentials(
            HTTP_AUTHORIZATION=(
                f"Bearer {refresh.access_token}"
            )
        )

        now = timezone.now()

        response = self.client.post(
            "/api/mission-management/",
            {
                "name": "Scheduled HR Mission",
                "description": "Scheduled mission",
                "type": "HR",
                "points": 100,
                "is_active": True,
                "start_time": (
                    now + timedelta(days=1)
                ).isoformat(),
                "end_time": (
                    now + timedelta(days=30)
                ).isoformat(),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        mission = Mission.objects.get(
            name="Scheduled HR Mission"
        )

        self.assertIsNotNone(
            mission.start_time
        )

        self.assertIsNotNone(
            mission.end_time
        )


