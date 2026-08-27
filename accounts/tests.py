from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .mission_service import MissionService
from .models import (
    User,
    Mission,
    UserMission,
    Badge,
    UserBadge,
    BadgeRule,
    Level,
)


class MissionServiceTests(TestCase):

    def setUp(self):
        # Test Levels
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

        Level.objects.create(
            level=3,
            required_points=200,
            is_active=True,
        )

        Level.objects.create(
            level=4,
            required_points=300,
            is_active=True,
        )

        # Test User
        self.user = User.objects.create_user(
            phone_number="09120000001",
            password="testpass123",
        )

        # User model currently starts at:
        # points = 10
        # level = 0

        # Test Mission
        self.mission = Mission.objects.create(
            name="Test Mission",
            description="Test mission",
            type="USER",
            points=10,
            is_active=True,
        )

    # UPDATE PROGRESS
    def test_update_progress(self):
        user_mission, reward = MissionService.update_progress(
            user=self.user,
            mission=self.mission,
            progress=50,
        )

        self.assertEqual(
            user_mission.progress,
            50,
        )

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

        self.assertEqual(
            user_mission.progress,
            0,
        )

        self.assertEqual(
            user_mission.status,
            "PENDING",
        )

        self.assertIsNone(reward)

    # COMPLETE MISSION
    def test_complete_mission(self):
        user_mission, reward = MissionService.complete_mission(
            user=self.user,
            mission=self.mission,
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

        # Initial points = 10
        # Mission points = 10
        # Final points = 20
        self.assertEqual(
            self.user.points,
            20,
        )

        # Reward
        self.assertIsNotNone(reward)

        self.assertEqual(
            reward["points"],
            20,
        )

        # 20 points reaches Level 1.
        # User starts at Level 0.
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

        self.assertEqual(
            reward["badges"],
            [],
        )

    # COMPLETED MISSION CANNOT MOVE BACKWARDS
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

    # COMPLETE MISSION TWICE
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

    # AUTOMATIC BADGE
    def test_completion_returns_new_badge(self):

        badge = Badge.objects.create(
            name="hero",
            label="Hero",
            description="Completed 5 missions",
            icon="🏆",
            is_active=True,
        )

        BadgeRule.objects.create(
            badge=badge,
            rule_type="MISSIONS_COMPLETED",
            value=5,
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

    def test_automatic_badge_rule(self):
        badge = Badge.objects.create(
            name="mission_hero_auto",
            label="پادشاه ماموریت‌ها",
            description="۵ ماموریت را تکمیل کرده است",
            icon="👑",
            is_active=True,
        )

        BadgeRule.objects.create(
            badge=badge,
            rule_type="MISSIONS_COMPLETED",
            value=5,
            is_active=True,
        )

        for i in range(4):
            mission = Mission.objects.create(
                name=f"Auto Mission {i}",
                description="Automatic badge test",
                type="USER",
                points=10,
                is_active=True,
            )

            MissionService.complete_mission(
                user=self.user,
                mission=mission,
            )

        self.assertFalse(
            UserBadge.objects.filter(
                user=self.user,
                badge=badge,
            ).exists()
        )

        mission = Mission.objects.create(
            name="Auto Mission 5",
            description="Automatic badge test",
            type="USER",
            points=10,
            is_active=True,
        )

        MissionService.complete_mission(
            user=self.user,
            mission=mission,
        )

        self.assertTrue(
            UserBadge.objects.filter(
                user=self.user,
                badge=badge,
            ).exists()
        )

        self.assertEqual(
            UserBadge.objects.filter(
                user=self.user,
                badge=badge,
            ).count(),
            1,
        )


class MissionAPITests(APITestCase):

    def setUp(self):

        # ---------------------------------------------------------
        # Test Levels
        # ---------------------------------------------------------

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

        Level.objects.create(
            level=3,
            required_points=200,
            is_active=True,
        )

        Level.objects.create(
            level=4,
            required_points=300,
            is_active=True,
        )

        # ---------------------------------------------------------
        # Test User
        # ---------------------------------------------------------

        self.user = User.objects.create_user(
            phone_number="09120000002",
            password="testpassword123",
        )

        # ---------------------------------------------------------
        # Test Mission
        # ---------------------------------------------------------

        self.mission = Mission.objects.create(
            name="API Mission",
            description="API mission description",
            type="USER",
            points=100,
            is_active=True,
        )

        # ---------------------------------------------------------
        # JWT Authentication
        # ---------------------------------------------------------

        refresh = RefreshToken.for_user(
            self.user
        )

        self.client.credentials(
            HTTP_AUTHORIZATION=(
                f"Bearer {refresh.access_token}"
            )
        )

    # ============================================================
    # START MISSION
    # ============================================================

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

    # ============================================================
    # UPDATE MISSION PROGRESS
    # ============================================================

    def test_update_progress_api(self):

        url = reverse(
            "api_mission_progress",
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

    # ============================================================
    # COMPLETE MISSION API
    # ============================================================

    def test_complete_mission_api(self):

        url = reverse(
            "api_mission_complete",
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

        # ---------------------------------------------------------
        # Basic response
        # ---------------------------------------------------------

        self.assertTrue(
            response.data["ok"]
        )

        self.assertEqual(
            response.data["progress"],
            100,
        )

        # User starts with 10 points.
        # Mission awards 100 points.
        # Final points = 110.
        self.assertEqual(
            response.data["points"],
            110,
        )

        # ---------------------------------------------------------
        # Rewards object
        # ---------------------------------------------------------

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

        # 110 points reaches Level 2.
        # User starts at Level 0.
        self.assertIsNotNone(
            response.data["rewards"]["level_up"]
        )

        self.assertEqual(
            response.data["rewards"]["level_up"]["from"],
            0,
        )

        self.assertEqual(
            response.data["rewards"]["level_up"]["to"],
            2,
        )

        self.assertEqual(
            response.data["rewards"]["badges"],
            [],
        )

    # ============================================================
    # INVALID PROGRESS
    # ============================================================

    def test_invalid_progress_api(self):

        response = self.client.patch(
            f"/api/missions/{self.mission.id}/progress/",
            {
                "progress": 150,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    # ============================================================
    # UNAUTHENTICATED USER
    # ============================================================

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

        # ---------------------------------------------------------
        # Test User
        # ---------------------------------------------------------

        self.user = User.objects.create_user(
            phone_number="09120000003",
            password="testpassword123",
            role="USER",
        )

        # ---------------------------------------------------------
        # Test Mission
        # ---------------------------------------------------------

        self.mission = Mission.objects.create(
            name="Permission Mission",
            description="Permission test",
            type="USER",
            points=50,
        )

        # ---------------------------------------------------------
        # JWT Authentication
        # ---------------------------------------------------------

        refresh = RefreshToken.for_user(
            self.user
        )

        self.client.credentials(
            HTTP_AUTHORIZATION=(
                f"Bearer {refresh.access_token}"
            )
        )

    # ============================================================
    # MISSION CREATION PERMISSION
    # ============================================================

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