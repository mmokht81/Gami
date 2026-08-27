from django.core.exceptions import ValidationError
from django.test import TestCase
from .mission_service import MissionService
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from django.urls import reverse
from .models import (
    User,
    Mission,
    UserMission,
    Badge,
    UserBadge,
)

class MissionServiceTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            phone_number="09120000001",
            password="testpass123",
        )

        self.mission = Mission.objects.create(
            name="Test Mission",
            description="Test mission",
            type="USER",
            points=10,
            is_active=True,
        )

    def test_update_progress(self):
        user_mission, reward = MissionService.update_progress(
            user=self.user,
            mission=self.mission,
            progress=50,
        )

        self.assertEqual(user_mission.progress, 50)
        self.assertEqual(
            user_mission.status,
            "IN_PROGRESS",
        )
        self.assertIsNone(reward)

    def test_zero_progress_is_pending(self):
        user_mission, reward = MissionService.update_progress(
            user=self.user,
            mission=self.mission,
            progress=0,
        )

        self.assertEqual(user_mission.progress, 0)
        self.assertEqual(
            user_mission.status,
            "PENDING",
        )
        self.assertIsNone(reward)

    def test_complete_mission(self):
        user_mission, reward = MissionService.complete_mission(
            user=self.user,
            mission=self.mission,
        )

        self.assertEqual(user_mission.progress, 100)
        self.assertEqual(
            user_mission.status,
            "COMPLETED",
        )

        self.user.refresh_from_db()

        self.assertEqual(
            self.user.points,
            20,
        )

        self.assertIsNotNone(reward)

        self.assertEqual(
            reward["points"],
            20,
        )

        self.assertIsNone(
            reward["level_up"]
        )

        self.assertEqual(
            reward["badges"],
            [],
        )

    def test_completed_mission_cannot_move_backwards(self):
        user_mission, reward = MissionService.complete_mission(
            user=self.user,
            mission=self.mission,
        )

        self.user.refresh_from_db()

        points_after_completion = self.user.points

        user_mission, second_reward = (
            MissionService.update_progress(
                user=self.user,
                mission=self.mission,
                progress=50,
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

        self.user.refresh_from_db()

        self.assertEqual(
            self.user.points,
            points_after_completion,
        )

        self.assertIsNone(second_reward)

    def test_complete_mission_twice_does_not_award_points_twice(self):
        MissionService.complete_mission(
            user=self.user,
            mission=self.mission,
        )

        self.user.refresh_from_db()

        first_points = self.user.points

        user_mission, reward = MissionService.complete_mission(
            user=self.user,
            mission=self.mission,
        )

        self.user.refresh_from_db()

        self.assertEqual(
            self.user.points,
            first_points,
        )

        self.assertIsNone(reward)

        self.assertEqual(
            user_mission.progress,
            100,
        )

        self.assertEqual(
            user_mission.status,
            "COMPLETED",
        )

    def test_completion_returns_new_badge(self):
        badge = Badge.objects.create(
            name="hero",
            label="Hero",
            description="Completed 5 missions",
            icon="🏆",
            is_active=True,
        )

        for i in range(4):
            mission = Mission.objects.create(
                name=f"Mission {i}",
                description="Test",
                type="USER",
                points=10,
                is_active=True,
            )

            MissionService.complete_mission(
                user=self.user,
                mission=mission,
            )

        last_mission = Mission.objects.create(
            name="Mission 5",
            description="Test",
            type="USER",
            points=10,
            is_active=True,
        )

        user_mission, reward = MissionService.complete_mission(
            user=self.user,
            mission=last_mission,
        )

        self.assertEqual(
            len(reward["badges"]),
            1,
        )

        self.assertEqual(
            reward["badges"][0].badge,
            badge,
        )


class MissionAPITests(APITestCase):

    def setUp(self):

        self.user = User.objects.create_user(
            phone_number="09120000002",
            password="testpassword123",
        )

        self.mission = Mission.objects.create(
            name="API Mission",
            description="API mission description",
            type="USER",
            points=100,
            is_active=True,
        )

        refresh = RefreshToken.for_user(
            self.user
        )

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}"
        )

    def test_start_mission_api(self):

        response = self.client.post(
            f"/api/missions/{self.mission.id}/start/"
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertEqual(
            response.data["progress"],
            0,
        )

        self.assertEqual(
            response.data["status"],
            "IN_PROGRESS",
        )

    def test_update_progress_api(self):
        url = reverse(
            "mission-progress",
            kwargs={
                "mission_id": self.mission.id,
            },
        )

        response = self.client.patch(
            url,
            {
                "progress": 50,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["progress"],
            50,
        )

        self.assertEqual(
            response.data["status"],
            "IN_PROGRESS",
        )

    def test_complete_mission_api(self):
        url = reverse(
            "mission-complete",
            kwargs={
                "mission_id": self.mission.id,
            },
        )

        response = self.client.post(
            url,
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTrue(
            response.data["ok"]
        )

        self.assertEqual(
            response.data["progress"],
            100,
        )

        self.assertEqual(
            response.data["points"],
            20,
        )

        self.assertIn(
            "rewards",
            response.data,
        )

        self.assertIn(
            "level_up",
            response.data["rewards"],
        )

        self.assertIn(
            "badges",
            response.data["rewards"],
        )

        self.assertIsNone(
            response.data["rewards"]["level_up"]
        )

        self.assertEqual(
            response.data["rewards"]["badges"],
            [],
        )

    def test_invalid_progress_api(self):

        response = self.client.patch(
            f"/api/missions/{self.mission.id}/progress/",
            {
                "progress": 150
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    def test_unauthenticated_user_cannot_start_mission(self):

        self.client.credentials()

        response = self.client.post(
            f"/api/missions/{self.mission.id}/start/"
        )

        self.assertEqual(
            response.status_code,
            401,
        )


class MissionPermissionTests(APITestCase):

    def setUp(self):

        self.user = User.objects.create_user(
            phone_number="09120000003",
            password="testpassword123",
            role="USER",
        )

        self.mission = Mission.objects.create(
            name="Permission Mission",
            description="Permission test",
            type="USER",
            points=50,
        )

        refresh = RefreshToken.for_user(
            self.user
        )

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}"
        )

    def test_normal_user_cannot_create_mission(self):

        response = self.client.post(
            "/api/missions/create/",
            {
                "name": "Unauthorized Mission",
                "description": "Should fail",
                "type": "USER",
                "points": 100,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            403,
        )

