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

        self.user = User.objects.create_user(
            phone_number="09120000001",
            password="testpass123",
        )

        # User starts with:
        # points = 10
        # level = 0

        self.mission = Mission.objects.create(
            name="Test Mission",
            description="Test mission",
            type="USER",
            points=10,
            is_active=True,
        )

        UserMission.objects.create(
            user=self.user,
            mission=self.mission,
            progress=0,
            status="PENDING",
        )

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

        self.assertIsNone(
            reward
        )

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

        self.assertIsNone(
            reward
        )

    def test_complete_mission(self):

        # Mission must be started first.
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

        self.user.refresh_from_db()

        # Initial points = 10
        # Mission points = 10
        # Final points = 20

        self.assertEqual(
            self.user.points,
            20,
        )

        # Reward must exist.

        self.assertIsNotNone(
            reward
        )

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


    def test_completed_mission_cannot_move_backwards(self):

        # Start mission first.

        MissionService.start_mission(
            user=self.user,
            mission=self.mission,
        )

        # Complete mission.

        user_mission, reward = (
            MissionService.complete_mission(
                user=self.user,
                mission=self.mission,
            )
        )

        self.user.refresh_from_db()

        points_after_completion = self.user.points

        # Try to move progress backwards.

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

        # Points must not increase.

        self.assertEqual(
            self.user.points,
            points_after_completion,
        )

        self.assertIsNone(
            second_reward
        )

    def test_complete_mission_twice_does_not_award_points_twice(self):

        # Start mission first.

        MissionService.start_mission(
            user=self.user,
            mission=self.mission,
        )

        # First completion.

        MissionService.complete_mission(
            user=self.user,
            mission=self.mission,
        )

        self.user.refresh_from_db()

        first_points = self.user.points

        # Second completion.

        user_mission, reward = (
            MissionService.complete_mission(
                user=self.user,
                mission=self.mission,
            )
        )

        self.user.refresh_from_db()

        # Points must remain unchanged.

        self.assertEqual(
            self.user.points,
            first_points,
        )

        # No second reward.

        self.assertIsNone(
            reward
        )

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

        BadgeRule.objects.create(
            badge=badge,
            rule_type="MISSIONS_COMPLETED",
            value=5,
            is_active=True,
        )

        # Complete first 4 missions.

        for i in range(4):

            mission = Mission.objects.create(
                name=f"Mission {i}",
                description="Test",
                type="USER",
                points=10,
                is_active=True,
            )

            UserMission.objects.create(
                user=self.user,
                mission=mission,
                progress=0,
                status="PENDING",
            )

            MissionService.start_mission(
                user=self.user,
                mission=mission,
            )

            MissionService.complete_mission(
                user=self.user,
                mission=mission,
            )

        # Fifth mission should trigger badge.

        last_mission = Mission.objects.create(
            name="Mission 5",
            description="Test",
            type="USER",
            points=10,
            is_active=True,
        )

        UserMission.objects.create(
            user=self.user,
            mission=last_mission,
            progress=0,
            status="PENDING",
        )

        MissionService.start_mission(
            user=self.user,
            mission=last_mission,
        )

        user_mission, reward = (
            MissionService.complete_mission(
                user=self.user,
                mission=last_mission,
            )
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

        # Complete first 4 missions.

        for i in range(4):

            mission = Mission.objects.create(
                name=f"Auto Mission {i}",
                description="Automatic badge test",
                type="USER",
                points=10,
                is_active=True,
            )

            UserMission.objects.create(
                user=self.user,
                mission=mission,
                progress=0,
                status="PENDING",
            )

            MissionService.start_mission(
                user=self.user,
                mission=mission,
            )

            MissionService.complete_mission(
                user=self.user,
                mission=mission,
            )

        # Badge must not exist yet.

        self.assertFalse(
            UserBadge.objects.filter(
                user=self.user,
                badge=badge,
            ).exists()
        )

        # Fifth mission.

        mission = Mission.objects.create(
            name="Auto Mission 5",
            description="Automatic badge test",
            type="USER",
            points=10,
            is_active=True,
        )

        UserMission.objects.create(
            user=self.user,
            mission=mission,
            progress=0,
            status="PENDING",
        )

        MissionService.start_mission(
            user=self.user,
            mission=mission,
        )

        MissionService.complete_mission(
            user=self.user,
            mission=mission,
        )

        # Badge must now exist.

        self.assertTrue(
            UserBadge.objects.filter(
                user=self.user,
                badge=badge,
            ).exists()
        )

        # Badge must only be assigned once.

        self.assertEqual(
            UserBadge.objects.filter(
                user=self.user,
                badge=badge,
            ).count(),
            1,
        )


class MissionAPITests(APITestCase):

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

        UserMission.objects.create(
            user=self.user,
            mission=self.mission,
            progress=0,
            status="PENDING",
        )

        refresh = RefreshToken.for_user(
            self.user
        )

        self.client.credentials(
            HTTP_AUTHORIZATION=(
                f"Bearer {refresh.access_token}"
            )
        )

    def test_start_mission_api(self):

        response = self.client.post(
            f"/api/missions/{self.mission.id}/start/"
        )

        self.assertEqual(
            response.status_code,
            200,
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

        # Start mission first.

        start_response = self.client.post(
            f"/api/missions/{self.mission.id}/start/"
        )

        self.assertIn(
            start_response.status_code,
            [200, 201],
        )

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

    def test_complete_mission_api(self):

        # ---------------------------------------------------------
        # Make sure the mission is assigned and pending
        # ---------------------------------------------------------

        user_mission, created = (
            UserMission.objects.update_or_create(
                user=self.user,
                mission=self.mission,
                defaults={
                    "progress": 0,
                    "status": "PENDING",
                },
            )
        )

        self.assertEqual(
            user_mission.progress,
            0,
        )

        self.assertEqual(
            user_mission.status,
            "PENDING",
        )

        # ---------------------------------------------------------
        # Start mission
        # ---------------------------------------------------------

        start_url = reverse(
            "api_mission_start",
            kwargs={
                "mission_id": self.mission.id,
            },
        )

        start_response = self.client.post(
            start_url,
            {},
            format="json",
        )

        self.assertIn(
            start_response.status_code,
            [200, 201],
        )

        self.assertEqual(
            start_response.data["progress"],
            0,
        )

        self.assertEqual(
            start_response.data["status"],
            "IN_PROGRESS",
        )

        # ---------------------------------------------------------
        # Complete mission
        # ---------------------------------------------------------

        complete_url = reverse(
            "api_mission_complete",
            kwargs={
                "mission_id": self.mission.id,
            },
        )

        response = self.client.post(
            complete_url,
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

        # ---------------------------------------------------------
        # Points
        # ---------------------------------------------------------

        print("RESPONSE:", response.data)

        db_user_mission = UserMission.objects.get(
            user=self.user,
            mission=self.mission,
        )

        self.user.refresh_from_db()

        print("DB USER POINTS:", self.user.points)
        print("DB USER MISSION STATUS:", db_user_mission.status)
        print("DB USER MISSION PROGRESS:", db_user_mission.progress)

        # User starts with 10 points.
        # Mission awards 100 points.
        # Final points = 110.

        self.assertEqual(
            response.data["points"],
            110,
        )
        # ---------------------------------------------------------
        # Rewards
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

        # ---------------------------------------------------------
        # Level up
        # ---------------------------------------------------------

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

        # ---------------------------------------------------------
        # Badges
        # ---------------------------------------------------------

        self.assertEqual(
            response.data["rewards"]["badges"],
            [],
        )


    def test_invalid_progress_api(self):

        # Mission is assigned but not started.
        # The request should still fail because
        # progress cannot be updated before starting.

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
            HTTP_AUTHORIZATION=(
                f"Bearer {refresh.access_token}"
            )
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

