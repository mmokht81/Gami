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
            password="testpassword123",
        )

        self.mission = Mission.objects.create(
            name="Test Mission",
            description="Test mission description",
            type="USER",
            points=100,
            is_active=True,
        )

    def test_start_mission(self):
        user_mission, created = MissionService.start_mission(
            user=self.user,
            mission=self.mission,
        )

        self.assertTrue(created)

        self.assertEqual(
            user_mission.progress,
            0,
        )

        self.assertEqual(
            user_mission.status,
            "IN_PROGRESS",
        )

    def test_start_mission_twice_does_not_create_duplicate(self):
        first, created_first = MissionService.start_mission(
            user=self.user,
            mission=self.mission,
        )

        second, created_second = MissionService.start_mission(
            user=self.user,
            mission=self.mission,
        )

        self.assertTrue(created_first)
        self.assertFalse(created_second)

        self.assertEqual(
            first.id,
            second.id,
        )

        self.assertEqual(
            UserMission.objects.count(),
            1,
        )

    def test_update_progress(self):
        user_mission = MissionService.update_progress(
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

    def test_zero_progress_is_pending(self):
        user_mission = MissionService.update_progress(
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

    def test_complete_mission(self):
        user_mission = MissionService.complete_mission(
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

    def test_complete_mission_awards_points(self):
        initial_points = self.user.points

        MissionService.complete_mission(
            user=self.user,
            mission=self.mission,
        )

        self.user.refresh_from_db()

        self.assertEqual(
            self.user.points,
            initial_points + 100,
        )

    def test_completed_mission_cannot_move_backwards(self):
        MissionService.complete_mission(
            user=self.user,
            mission=self.mission,
        )

        user_mission = MissionService.update_progress(
            user=self.user,
            mission=self.mission,
            progress=50,
        )

        self.assertEqual(
            user_mission.progress,
            100,
        )

        self.assertEqual(
            user_mission.status,
            "COMPLETED",
        )

    def test_invalid_progress_is_rejected(self):
        with self.assertRaises(ValidationError):
            MissionService.update_progress(
                user=self.user,
                mission=self.mission,
                progress=101,
            )

        with self.assertRaises(ValidationError):
            MissionService.update_progress(
                user=self.user,
                mission=self.mission,
                progress=-1,
            )

    def test_inactive_mission_cannot_start(self):
        self.mission.is_active = False
        self.mission.save()

        with self.assertRaises(ValidationError):
            MissionService.start_mission(
                user=self.user,
                mission=self.mission,
            )

    def test_inactive_mission_cannot_be_completed(self):
        self.mission.is_active = False
        self.mission.save()

        with self.assertRaises(ValidationError):
            MissionService.complete_mission(
                user=self.user,
                mission=self.mission,
            )

    def test_completed_mission_does_not_award_points_twice(self):
        initial_points = self.user.points

        MissionService.complete_mission(
            user=self.user,
            mission=self.mission,
        )

        MissionService.complete_mission(
            user=self.user,
            mission=self.mission,
        )

        self.user.refresh_from_db()

        self.assertEqual(
            self.user.points,
            initial_points + 100,
        )

        self.assertEqual(
            UserMission.objects.count(),
            1,
        )

    def test_completing_five_missions_awards_hero_badge(self):
        Badge.objects.create(
            name="hero",
            label="قهرمان",
            icon="🏆",
            description="تکمیل حداقل ۵ ماموریت",
            is_active=True,
        )

        for index in range(5):
            mission = Mission.objects.create(
                name=f"Mission {index}",
                description=f"Mission {index} description",
                type="USER",
                points=10,
                is_active=True,
            )

            MissionService.complete_mission(
                user=self.user,
                mission=mission,
            )

        self.assertEqual(
            UserMission.objects.filter(
                user=self.user,
                status="COMPLETED",
            ).count(),
            5,
        )

        self.assertEqual(
            UserBadge.objects.filter(
                user=self.user,
                badge__name="hero",
            ).count(),
            1,
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

        response = self.client.post(
            f"/api/missions/{self.mission.id}/start/"
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        response = self.client.patch(
            f"/api/missions/{self.mission.id}/progress/",
            {
                "progress": 60
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["progress"],
            60,
        )

        self.assertEqual(
            response.data["status"],
            "IN_PROGRESS",
        )

    def test_complete_mission_api(self):

        response = self.client.post(
            f"/api/missions/{self.mission.id}/complete/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["progress"],
            100,
        )

        self.assertEqual(
            response.data["status"],
            "COMPLETED",
        )

        self.user.refresh_from_db()

        self.assertEqual(
            self.user.points,
            110,
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

