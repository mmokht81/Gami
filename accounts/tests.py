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
    JobPosition,
    Question,
    JobApplication,
    ApplicationQuestion,
    TrainingCourse,
    TrainingSection,
    UserTraining,
    UserTrainingSection,
)

from .serializers import JobApplicationSerializer
from .training_service import TrainingService

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

        self.assertTrue(
            response.data["ok"]
        )

        self.assertEqual(
            response.data["progress"],
            100,
        )

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

    def test_normal_user_cannot_assign_mission(self):

        response = self.client.post(
            f"/api/mission-management/{self.mission.id}/assign/",
            {
                "user_id": self.user.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            403,
        )


class ApplicationTests(APITestCase):

    def setUp(self):

        self.user = User.objects.create_user(
            phone_number="09121111111",
            password="testpassword123",
        )

        self.hr = User.objects.create_user(
            phone_number="09122222222",
            password="testpassword123",
        )

        self.hr.role = "ADMIN"
        self.hr.is_staff = True
        self.hr.save()

        self.job_position = JobPosition.objects.create(
            title="Backend Developer",
            description="Django Backend Developer",
            tags=["Django", "Python"],
            is_active=True,
        )

        self.question_1 = Question.objects.create(
            job_position=self.job_position,
            type="CUSTOM",
            text="چند سال سابقه برنامه نویسی دارید؟",
            order=1,
            is_active=True,
        )

        self.question_2 = Question.objects.create(
            job_position=self.job_position,
            type="CUSTOM",
            text="با Django کار کرده‌اید؟",
            order=2,
            is_active=True,
        )

        self.authenticate_user()

    def authenticate_user(self):

        refresh = RefreshToken.for_user(
            self.user
        )

        self.client.credentials(
            HTTP_AUTHORIZATION=(
                f"Bearer {refresh.access_token}"
            )
        )

    def authenticate_hr(self):

        refresh = RefreshToken.for_user(
            self.hr
        )

        self.client.credentials(
            HTTP_AUTHORIZATION=(
                f"Bearer {refresh.access_token}"
            )
        )

    def test_user_can_create_application(self):

        url = "/api/applications/create/"

        data = {
            "job_position": self.job_position.id,
            "answers": [
                {
                    "question_id": self.question_1.id,
                    "answer": "2 سال",
                },
                {
                    "question_id": self.question_2.id,
                    "answer": "بله",
                },
            ],
        }

        response = self.client.post(
            url,
            data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertEqual(
            JobApplication.objects.count(),
            1,
        )

        application = JobApplication.objects.get(
            user=self.user
        )

        self.assertEqual(
            application.job_position,
            self.job_position,
        )

        self.assertEqual(
            application.status,
            "PENDING_REVIEW",
        )

        self.assertEqual(
            len(application.answers),
            2,
        )

    def test_user_cannot_apply_twice(self):

        JobApplication.objects.create(
            user=self.user,
            job_position=self.job_position,
            answers=[],
        )

        url = "/api/applications/create/"

        data = {
            "job_position": self.job_position.id,
            "answers": [],
        }

        response = self.client.post(
            url,
            data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertEqual(
            JobApplication.objects.filter(
                user=self.user,
                job_position=self.job_position,
            ).count(),
            1,
        )

    def test_user_cannot_apply_to_inactive_job(self):

        self.job_position.is_active = False
        self.job_position.save()

        url = "/api/applications/create/"

        data = {
            "job_position": self.job_position.id,
            "answers": [],
        }

        response = self.client.post(
            url,
            data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertFalse(
            JobApplication.objects.filter(
                user=self.user,
                job_position=self.job_position,
            ).exists()
        )

    def test_invalid_question_is_rejected(self):

        other_job = JobPosition.objects.create(
            title="Frontend Developer",
            description="Frontend Developer",
            is_active=True,
        )

        other_question = Question.objects.create(
            job_position=other_job,
            type="CUSTOM",
            text="سوال دیگر",
            order=1,
            is_active=True,
        )

        url = "/api/applications/create/"

        data = {
            "job_position": self.job_position.id,
            "answers": [
                {
                    "question_id": other_question.id,
                    "answer": "Invalid",
                },
            ],
        }

        response = self.client.post(
            url,
            data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertFalse(
            JobApplication.objects.filter(
                user=self.user,
                job_position=self.job_position,
            ).exists()
        )

    def test_user_can_view_own_applications(self):

        application = JobApplication.objects.create(
            user=self.user,
            job_position=self.job_position,
            answers=[
                {
                    "question_id": self.question_1.id,
                    "question": self.question_1.text,
                    "answer": "2 سال",
                }
            ],
        )

        response = self.client.get(
            "/api/applications/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        results = response.data["results"]

        self.assertGreaterEqual(
            len(results),
            1,
        )

        self.assertTrue(
            any(
                item["id"] == application.id
                for item in results
            )
        )

    def test_user_can_view_job_questions(self):

        url = (
            f"/api/job-positions/"
            f"{self.job_position.id}/questions/"
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            200,
        )

        results = response.data["results"]

        self.assertGreaterEqual(
            len(results),
            2,
        )

        self.assertTrue(
            any(
                item["id"] == self.question_1.id
                for item in results
            )
        )

    def test_hr_can_create_question(self):

        self.authenticate_hr()

        url = "/api/questions/create/"

        data = {
            "job_position": self.job_position.id,
            "type": "CUSTOM",
            "text": "چرا باید شما را استخدام کنیم؟",
            "order": 3,
            "is_active": True,
        }

        response = self.client.post(
            url,
            data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertTrue(
            Question.objects.filter(
                job_position=self.job_position,
                text="چرا باید شما را استخدام کنیم؟",
            ).exists()
        )

    def test_user_cannot_create_question(self):

        url = "/api/questions/create/"

        data = {
            "job_position": self.job_position.id,
            "type": "CUSTOM",
            "text": "Unauthorized question",
            "order": 3,
            "is_active": True,
        }

        response = self.client.post(
            url,
            data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_hr_can_update_question(self):

        self.authenticate_hr()

        url = (
            f"/api/questions/"
            f"{self.question_1.id}/"
        )

        data = {
            "text": "متن سوال ویرایش شده",
        }

        response = self.client.patch(
            url,
            data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.question_1.refresh_from_db()

        self.assertEqual(
            self.question_1.text,
            "متن سوال ویرایش شده",
        )

    def test_hr_can_delete_question(self):

        self.authenticate_hr()

        url = (
            f"/api/questions/"
            f"{self.question_2.id}/"
        )

        response = self.client.delete(url)

        self.assertEqual(
            response.status_code,
            204,
        )

        self.assertFalse(
            Question.objects.filter(
                id=self.question_2.id
            ).exists()
        )

    def test_hr_can_view_all_applications(self):

        application = JobApplication.objects.create(
            user=self.user,
            job_position=self.job_position,
            answers=[
                {
                    "question_id": self.question_1.id,
                    "question": self.question_1.text,
                    "answer": "2 سال",
                }
            ],
        )

        self.authenticate_hr()

        response = self.client.get(
            "/api/applications/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        results = response.data["results"]

        self.assertGreaterEqual(
            len(results),
            1,
        )

        application_data = next(
            item
            for item in results
            if item["id"] == application.id
        )

        self.assertIn(
            "user",
            application_data,
        )

        self.assertIn(
            "job_position",
            application_data,
        )

        self.assertIn(
            "answers",
            application_data,
        )

    def test_hr_can_view_application_detail(self):

        application = JobApplication.objects.create(
            user=self.user,
            job_position=self.job_position,
            answers=[
                {
                    "question_id": self.question_1.id,
                    "question": self.question_1.text,
                    "answer": "2 سال",
                }
            ],
        )

        self.authenticate_hr()

        url = (
            f"/api/applications/"
            f"{application.id}/"
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["id"],
            application.id,
        )

        self.assertIn(
            "user",
            response.data,
        )

        self.assertIn(
            "job_position",
            response.data,
        )

        self.assertIn(
            "answers",
            response.data,
        )

    def test_hr_can_change_application_status(self):

        application = JobApplication.objects.create(
            user=self.user,
            job_position=self.job_position,
            status="PENDING_REVIEW",
            answers=[],
        )

        self.authenticate_hr()

        url = (
            f"/api/applications/"
            f"{application.id}/status/"
        )

        response = self.client.patch(
            url,
            {
                "status": "HR_REVIEW",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        application.refresh_from_db()

        self.assertEqual(
            application.status,
            "HR_REVIEW",
        )

        self.assertEqual(
            response.data["status"],
            "HR_REVIEW",
        )

    def test_user_cannot_change_application_status(self):

        application = JobApplication.objects.create(
            user=self.user,
            job_position=self.job_position,
            status="PENDING_REVIEW",
            answers=[],
        )

        url = (
            f"/api/applications/"
            f"{application.id}/status/"
        )

        response = self.client.patch(
            url,
            {
                "status": "ACCEPTED",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        application.refresh_from_db()

        self.assertEqual(
            application.status,
            "PENDING_REVIEW",
        )

    def test_all_application_statuses_are_valid(self):

        application = JobApplication.objects.create(
            user=self.user,
            job_position=self.job_position,
            status="PENDING_REVIEW",
            answers=[],
        )

        self.authenticate_hr()

        statuses = [
            "PENDING_REVIEW",
            "HR_REVIEW",
            "WAITING_FOR_USER",
            "MANAGEMENT_REVIEW",
            "ACCEPTED",
            "REJECTED",
        ]

        url = (
            f"/api/applications/"
            f"{application.id}/status/"
        )

        for status in statuses:

            response = self.client.patch(
                url,
                {
                    "status": status,
                },
                format="json",
            )

            self.assertEqual(
                response.status_code,
                200,
                msg=f"Status failed: {status}",
            )

            application.refresh_from_db()

            self.assertEqual(
                application.status,
                status,
            )

    def test_hr_can_create_application_custom_question(self):

        application = JobApplication.objects.create(
            user=self.user,
            job_position=self.job_position,
            answers=[],
        )

        self.authenticate_hr()

        url = (
            f"/api/applications/"
            f"{application.id}/questions/"
        )

        response = self.client.post(
            url,
            {
                "text": "چرا فکر می‌کنید برای این موقعیت مناسب هستید؟",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertTrue(
            ApplicationQuestion.objects.filter(
                application=application,
                text="چرا فکر می‌کنید برای این موقعیت مناسب هستید؟",
            ).exists()
        )

    def test_user_can_view_own_application_custom_questions(self):

        application = JobApplication.objects.create(
            user=self.user,
            job_position=self.job_position,
            answers=[],
        )

        question = ApplicationQuestion.objects.create(
            application=application,
            text="تجربه کاری خود را توضیح دهید.",
        )

        url = (
            f"/api/applications/"
            f"{application.id}/questions/"
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            200,
        )

        results = response.data["results"]

        self.assertTrue(
            any(
                item["id"] == question.id
                for item in results
            )
        )

    def test_user_can_answer_application_custom_question(self):

        application = JobApplication.objects.create(
            user=self.user,
            job_position=self.job_position,
            answers=[],
        )

        question = ApplicationQuestion.objects.create(
            application=application,
            text="چرا باید شما را استخدام کنیم؟",
        )

        url = (
            f"/api/application-questions/"
            f"{question.id}/answer/"
        )

        response = self.client.patch(
            url,
            {
                "answer": "چون تجربه خوبی در Django دارم.",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        question.refresh_from_db()

        self.assertEqual(
            question.answer,
            "چون تجربه خوبی در Django دارم.",
        )

        self.assertTrue(
            question.is_answered,
        )

        self.assertIsNotNone(
            question.answered_at,
        )

    def test_user_cannot_create_application_custom_question(self):

        application = JobApplication.objects.create(
            user=self.user,
            job_position=self.job_position,
            answers=[],
        )

        url = (
            f"/api/applications/"
            f"{application.id}/questions/"
        )

        response = self.client.post(
            url,
            {
                "text": "Unauthorized question",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.assertFalse(
            ApplicationQuestion.objects.filter(
                application=application,
            ).exists()
        )

    def test_user_cannot_view_another_users_application_questions(self):

        other_user = User.objects.create_user(
            phone_number="09129999999",
            password="testpassword123",
        )

        application = JobApplication.objects.create(
            user=other_user,
            job_position=self.job_position,
            answers=[],
        )

        ApplicationQuestion.objects.create(
            application=application,
            text="Private HR question",
        )

        url = (
            f"/api/applications/"
            f"{application.id}/questions/"
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_user_cannot_answer_another_users_application_question(self):

        other_user = User.objects.create_user(
            phone_number="09128888888",
            password="testpassword123",
        )

        application = JobApplication.objects.create(
            user=other_user,
            job_position=self.job_position,
            answers=[],
        )

        question = ApplicationQuestion.objects.create(
            application=application,
            text="Private question",
        )

        url = (
            f"/api/application-questions/"
            f"{question.id}/answer/"
        )

        response = self.client.patch(
            url,
            {
                "answer": "Should not work",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        question.refresh_from_db()

        self.assertFalse(
            question.is_answered,
        )

    def test_empty_custom_question_answer_is_rejected(self):

        application = JobApplication.objects.create(
            user=self.user,
            job_position=self.job_position,
            answers=[],
        )

        question = ApplicationQuestion.objects.create(
            application=application,
            text="Test question",
        )

        url = (
            f"/api/application-questions/"
            f"{question.id}/answer/"
        )

        response = self.client.patch(
            url,
            {
                "answer": "   ",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        question.refresh_from_db()

        self.assertFalse(
            question.is_answered,
        )


class JobApplicationValidationTests(APITestCase):

    def setUp(self):

        self.user = User.objects.create_user(
            phone_number="09121111111",
            password="testpassword123",
        )

        self.other_user = User.objects.create_user(
            phone_number="09122222222",
            password="testpassword123",
        )

        self.frontend = JobPosition.objects.create(
            title="Frontend Developer",
            description="Frontend Developer position",
            is_active=True,
        )

        self.backend = JobPosition.objects.create(
            title="Backend Developer",
            description="Backend Developer position",
            is_active=True,
        )

        self.question_1 = Question.objects.create(
            job_position=self.frontend,
            type="TEXT",
            text="What is React?",
            order=1,
            is_active=True,
        )

        self.question_2 = Question.objects.create(
            job_position=self.frontend,
            type="TEXT",
            text="What is JavaScript?",
            order=2,
            is_active=True,
        )

        self.backend_question = Question.objects.create(
            job_position=self.backend,
            type="TEXT",
            text="What is Django?",
            order=1,
            is_active=True,
        )

        refresh = RefreshToken.for_user(
            self.user
        )

        self.client.credentials(
            HTTP_AUTHORIZATION=(
                f"Bearer {refresh.access_token}"
            )
        )

    # --------------------------------------------------
    # Helper
    # --------------------------------------------------

    def build_application_data(
        self,
        question_1_id,
        question_2_id,
    ):

        return {
            "job_position": self.frontend.id,
            "answers": [
                {
                    "question_id": question_1_id,
                    "answer": "React is a JavaScript library.",
                },
                {
                    "question_id": question_2_id,
                    "answer": "JavaScript is a programming language.",
                },
            ],
        }

    # --------------------------------------------------
    # 1. Integer question IDs
    # --------------------------------------------------

    def test_application_accepts_integer_question_ids(self):

        data = self.build_application_data(
            self.question_1.id,
            self.question_2.id,
        )

        serializer = JobApplicationSerializer(
            data=data,
            context={
                "request": self.client,
            },
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

        self.assertEqual(
            serializer.validated_data["answers"][0][
                "question_id"
            ],
            self.question_1.id,
        )

    # --------------------------------------------------
    # 2. String question IDs
    # --------------------------------------------------

    def test_application_accepts_string_question_ids(self):

        data = self.build_application_data(
            str(self.question_1.id),
            str(self.question_2.id),
        )

        serializer = JobApplicationSerializer(
            data=data,
            context={
                "request": self.client,
            },
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

        self.assertEqual(
            serializer.validated_data["answers"][0][
                "question_id"
            ],
            self.question_1.id,
        )

        self.assertIsInstance(
            serializer.validated_data["answers"][0][
                "question_id"
            ],
            int,
        )

    # --------------------------------------------------
    # 3. Question from another job position
    # --------------------------------------------------

    def test_question_from_another_job_position_is_rejected(self):

        data = {
            "job_position": self.frontend.id,
            "answers": [
                {
                    "question_id": self.question_1.id,
                    "answer": "React",
                },
                {
                    "question_id": self.backend_question.id,
                    "answer": "Django",
                },
            ],
        }

        serializer = JobApplicationSerializer(
            data=data,
            context={
                "request": self.client,
            },
        )

        self.assertFalse(
            serializer.is_valid()
        )

        self.assertIn(
            "answers",
            serializer.errors,
        )

        self.assertIn(
            str(self.backend_question.id),
            str(serializer.errors["answers"]),
        )

    # --------------------------------------------------
    # 4. Inactive question
    # --------------------------------------------------

    def test_inactive_question_is_rejected(self):

        inactive_question = Question.objects.create(
            job_position=self.frontend,
            type="TEXT",
            text="Inactive question",
            order=3,
            is_active=False,
        )

        data = {
            "job_position": self.frontend.id,
            "answers": [
                {
                    "question_id": self.question_1.id,
                    "answer": "React",
                },
                {
                    "question_id": self.question_2.id,
                    "answer": "JavaScript",
                },
                {
                    "question_id": inactive_question.id,
                    "answer": "Should fail",
                },
            ],
        }

        serializer = JobApplicationSerializer(
            data=data,
            context={
                "request": self.client,
            },
        )

        self.assertFalse(
            serializer.is_valid()
        )

        self.assertIn(
            "answers",
            serializer.errors,
        )

    # --------------------------------------------------
    # 5. Empty answer
    # --------------------------------------------------

    def test_empty_answer_is_rejected(self):

        data = {
            "job_position": self.frontend.id,
            "answers": [
                {
                    "question_id": self.question_1.id,
                    "answer": "",
                },
                {
                    "question_id": self.question_2.id,
                    "answer": "JavaScript",
                },
            ],
        }

        serializer = JobApplicationSerializer(
            data=data,
            context={
                "request": self.client,
            },
        )

        self.assertFalse(
            serializer.is_valid()
        )

        self.assertIn(
            "answers",
            serializer.errors,
        )

    # --------------------------------------------------
    # 6. Missing answer
    # --------------------------------------------------

    def test_missing_answer_is_rejected(self):

        data = {
            "job_position": self.frontend.id,
            "answers": [
                {
                    "question_id": self.question_1.id,
                    "answer": "React",
                },
            ],
        }

        serializer = JobApplicationSerializer(
            data=data,
            context={
                "request": self.client,
            },
        )

        self.assertFalse(
            serializer.is_valid()
        )

        self.assertIn(
            "answers",
            serializer.errors,
        )

        self.assertIn(
            str(self.question_2.id),
            str(serializer.errors["answers"]),
        )

    # --------------------------------------------------
    # 7. Duplicate question
    # --------------------------------------------------

    def test_duplicate_question_is_rejected(self):

        data = {
            "job_position": self.frontend.id,
            "answers": [
                {
                    "question_id": self.question_1.id,
                    "answer": "First answer",
                },
                {
                    "question_id": self.question_1.id,
                    "answer": "Second answer",
                },
                {
                    "question_id": self.question_2.id,
                    "answer": "JavaScript",
                },
            ],
        }

        serializer = JobApplicationSerializer(
            data=data,
            context={
                "request": self.client,
            },
        )

        self.assertFalse(
            serializer.is_valid()
        )

        self.assertIn(
            "answers",
            serializer.errors,
        )

    # --------------------------------------------------
    # 8. All questions answered
    # --------------------------------------------------

    def test_all_active_questions_can_be_answered(self):

        data = self.build_application_data(
            self.question_1.id,
            self.question_2.id,
        )

        serializer = JobApplicationSerializer(
            data=data,
            context={
                "request": self.client,
            },
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

        normalized_answers = (
            serializer.validated_data["answers"]
        )

        self.assertEqual(
            len(normalized_answers),
            2,
        )

        self.assertEqual(
            normalized_answers[0]["question_id"],
            self.question_1.id,
        )

        self.assertEqual(
            normalized_answers[0]["question"],
            self.question_1.text,
        )

    # --------------------------------------------------
    # 9. No questions for job position
    # --------------------------------------------------

    def test_empty_answers_are_allowed_when_job_has_no_questions(self):

        empty_job = JobPosition.objects.create(
            title="UI Designer",
            description="UI Designer position",
            is_active=True,
        )

        data = {
            "job_position": empty_job.id,
            "answers": [],
        }

        serializer = JobApplicationSerializer(
            data=data,
            context={
                "request": self.client,
            },
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

    # --------------------------------------------------
    # 10. Non-numeric question ID
    # --------------------------------------------------

    def test_non_numeric_question_id_is_rejected(self):

        data = {
            "job_position": self.frontend.id,
            "answers": [
                {
                    "question_id": "abc",
                    "answer": "React",
                },
                {
                    "question_id": self.question_2.id,
                    "answer": "JavaScript",
                },
            ],
        }

        serializer = JobApplicationSerializer(
            data=data,
            context={
                "request": self.client,
            },
        )

        self.assertFalse(
            serializer.is_valid()
        )

        self.assertIn(
            "answers",
            serializer.errors,
        )


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
            phone_number="09123333333",
            password="testpassword123",
        )

        self.course = TrainingCourse.objects.create(
            delivery_type="ONLINE",
            structure="MULTI",
            name="Python Basics",
            description="Python training course",
            instructor_name="Test Instructor",
            duration="2 hours",
            sessions_count=2,
            points=50,
            event_link="https://example.com/python",
            capacity=10,
            is_active=True,
        )

        self.section_1 = TrainingSection.objects.create(
            course=self.course,
            title="Introduction",
            description="Introduction to Python",
            content_url="https://example.com/part-1",
            order=1,
        )

        self.section_2 = TrainingSection.objects.create(
            course=self.course,
            title="Variables",
            description="Python variables",
            content_url="https://example.com/part-2",
            order=2,
        )

    def test_user_can_enroll_in_training(self):

        user_training, created = TrainingService.enroll_user(
            user=self.user,
            course=self.course,
        )

        self.assertTrue(
            created
        )

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

        with self.assertRaises(Exception):
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

    def test_user_cannot_enroll_in_inactive_course(self):

        self.course.is_active = False
        self.course.save()

        with self.assertRaises(Exception):
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

    def test_user_cannot_enroll_when_course_is_full(self):

        self.course.capacity = 1
        self.course.save()

        another_user = User.objects.create_user(
            phone_number="09124444444",
            password="testpassword123",
        )

        TrainingService.enroll_user(
            user=self.user,
            course=self.course,
        )

        with self.assertRaises(Exception):
            TrainingService.enroll_user(
                user=another_user,
                course=self.course,
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

        self.assertTrue(
            created
        )

        self.assertEqual(
            user_training.progress,
            50,
        )

        self.assertEqual(
            user_training.status,
            "IN_PROGRESS",
        )

        self.assertIsNone(
            reward
        )

        self.assertTrue(
            UserTrainingSection.objects.filter(
                user_training=user_training,
                section=self.section_1,
            ).exists()
        )

    def test_start_last_section_completes_training_and_awards_points(self):

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

        self.assertTrue(
            created
        )

        self.assertEqual(
            user_training.progress,
            100,
        )

        self.assertEqual(
            user_training.status,
            "COMPLETED",
        )

        self.assertIsNotNone(
            user_training.completed_at
        )

        self.user.refresh_from_db()

        # Initial points = 10
        # Training points = 50
        # Final points = 60

        self.assertEqual(
            self.user.points,
            60,
        )

        self.assertIsNotNone(
            reward
        )

        self.assertEqual(
            reward["points"],
            60,
        )

        self.assertEqual(
            reward["badges"],
            [],
        )

    def test_start_same_section_twice_does_not_award_duplicate_progress_or_points(self):

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

        self.assertTrue(
            first_created
        )

        self.assertFalse(
            second_created
        )

        self.assertEqual(
            second_training.progress,
            50,
        )

        self.user.refresh_from_db()

        self.assertEqual(
            self.user.points,
            points_after_first_start,
        )

        self.assertIsNone(
            second_reward
        )

        self.assertEqual(
            UserTrainingSection.objects.filter(
                user_training=first_training,
                section=self.section_1,
            ).count(),
            1,
        )

    def test_completed_training_does_not_award_points_again(self):

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

        points_after_completion = self.user.points

        user_training, reward, created = (
            TrainingService.start_section(
                user=self.user,
                course=self.course,
                section=self.section_2,
            )
        )

        self.assertFalse(
            created
        )

        self.assertEqual(
            user_training.progress,
            100,
        )

        self.assertEqual(
            user_training.status,
            "COMPLETED",
        )

        self.assertIsNone(
            reward
        )

        self.user.refresh_from_db()

        self.assertEqual(
            self.user.points,
            points_after_completion,
        )

    def test_user_cannot_start_section_without_enrollment(self):

        with self.assertRaises(Exception):
            TrainingService.start_section(
                user=self.user,
                course=self.course,
                section=self.section_1,
            )

        self.assertFalse(
            UserTrainingSection.objects.filter(
                section=self.section_1,
            ).exists()
        )


class TrainingAPITests(APITestCase):

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
            phone_number="09125555555",
            password="testpassword123",
        )

        self.admin = User.objects.create_user(
            phone_number="09126666666",
            password="testpassword123",
            role="ADMIN",
        )

        self.course = TrainingCourse.objects.create(
            delivery_type="ONLINE",
            structure="MULTI",
            name="Django Basics",
            description="Django training course",
            instructor_name="Test Instructor",
            duration="3 hours",
            sessions_count=2,
            points=100,
            event_link="https://example.com/django",
            capacity=10,
            is_active=True,
        )

        self.section_1 = TrainingSection.objects.create(
            course=self.course,
            title="Introduction",
            description="Django introduction",
            content_url="https://example.com/django-1",
            order=1,
        )

        self.section_2 = TrainingSection.objects.create(
            course=self.course,
            title="Views",
            description="Django views",
            content_url="https://example.com/django-2",
            order=2,
        )

        self.authenticate_user()

    def authenticate_user(self):

        refresh = RefreshToken.for_user(
            self.user
        )

        self.client.credentials(
            HTTP_AUTHORIZATION=(
                f"Bearer {refresh.access_token}"
            )
        )

    def authenticate_admin(self):

        refresh = RefreshToken.for_user(
            self.admin
        )

        self.client.credentials(
            HTTP_AUTHORIZATION=(
                f"Bearer {refresh.access_token}"
            )
        )

    def test_user_can_list_training_courses(self):

        response = self.client.get(
            "/api/trainings/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        results = response.data["results"]

        self.assertTrue(
            any(
                item["id"] == self.course.id
                for item in results
            )
        )

    def test_user_can_view_training_detail(self):

        response = self.client.get(
            f"/api/trainings/{self.course.id}/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["id"],
            self.course.id,
        )

        self.assertEqual(
            response.data["name"],
            "Django Basics",
        )

        self.assertIn(
            "sections",
            response.data,
        )

        self.assertEqual(
            len(response.data["sections"]),
            2,
        )

    def test_user_can_enroll_in_training_api(self):

        response = self.client.post(
            f"/api/trainings/{self.course.id}/enroll/",
            {},
            format="json",
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
            "ENROLLED",
        )

        self.assertTrue(
            UserTraining.objects.filter(
                user=self.user,
                course=self.course,
            ).exists()
        )

    def test_user_cannot_enroll_twice_api(self):

        self.client.post(
            f"/api/trainings/{self.course.id}/enroll/",
            {},
            format="json",
        )

        response = self.client.post(
            f"/api/trainings/{self.course.id}/enroll/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertEqual(
            UserTraining.objects.filter(
                user=self.user,
                course=self.course,
            ).count(),
            1,
        )

    def test_user_can_start_training_section_api(self):

        enroll_response = self.client.post(
            f"/api/trainings/{self.course.id}/enroll/",
            {},
            format="json",
        )

        self.assertEqual(
            enroll_response.status_code,
            201,
        )

        response = self.client.post(
            f"/api/trainings/{self.course.id}/sections/"
            f"{self.section_1.id}/start/",
            {},
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

    def test_completing_training_api_awards_points(self):

        self.client.post(
            f"/api/trainings/{self.course.id}/enroll/",
            {},
            format="json",
        )

        first_response = self.client.post(
            f"/api/trainings/{self.course.id}/sections/"
            f"{self.section_1.id}/start/",
            {},
            format="json",
        )

        self.assertEqual(
            first_response.status_code,
            200,
        )

        second_response = self.client.post(
            f"/api/trainings/{self.course.id}/sections/"
            f"{self.section_2.id}/start/",
            {},
            format="json",
        )

        self.assertEqual(
            second_response.status_code,
            200,
        )

        self.assertEqual(
            second_response.data["progress"],
            100,
        )

        self.assertEqual(
            second_response.data["status"],
            "COMPLETED",
        )

        self.assertIn(
            "rewards",
            second_response.data,
        )

        self.assertEqual(
            second_response.data["rewards"]["points"],
            110,
        )

        self.assertIsNotNone(
            second_response.data["rewards"]["level_up"]
        )

        self.assertEqual(
            second_response.data["rewards"]["level_up"]["from"],
            0,
        )

        self.assertEqual(
            second_response.data["rewards"]["level_up"]["to"],
            2,
        )

        self.assertEqual(
            second_response.data["rewards"]["badges"],
            [],
        )

        self.user.refresh_from_db()

        self.assertEqual(
            self.user.points,
            110,
        )

    def test_user_cannot_start_section_without_enrollment_api(self):

        response = self.client.post(
            f"/api/trainings/{self.course.id}/sections/"
            f"{self.section_1.id}/start/",
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

    def test_unauthenticated_user_cannot_access_training_api(self):

        self.client.credentials()

        response = self.client.get(
            "/api/trainings/"
        )

        self.assertEqual(
            response.status_code,
            401,
        )

    def test_admin_can_create_training_course(self):

        self.authenticate_admin()

        data = {
            "delivery_type": "IN_PERSON",
            "structure": "SINGLE",
            "name": "Advanced Django",
            "description": "Advanced Django course",
            "instructor_name": "Admin Instructor",
            "duration": "4 hours",
            "sessions_count": 1,
            "points": 150,
            "event_link": "",
            "location": "Tehran Training Center",
            "capacity": 20,
            "is_active": True,
        }

        response = self.client.post(
            "/api/trainings/manage/",
            data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertTrue(
            TrainingCourse.objects.filter(
                name="Advanced Django",
            ).exists()
        )

    def test_normal_user_cannot_create_training_course(self):

        data = {
            "delivery_type": "ONLINE",
            "structure": "SINGLE",
            "name": "Unauthorized Course",
            "description": "Should fail",
            "instructor_name": "Test Instructor",
            "duration": "1 hour",
            "sessions_count": 1,
            "points": 50,
            "event_link": "https://example.com/course",
            "location": "",
            "capacity": 10,
            "is_active": True,
        }

        response = self.client.post(
            "/api/trainings/manage/",
            data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_admin_can_create_training_section(self):

        self.authenticate_admin()

        data = {
            "title": "Advanced Views",
            "description": "Advanced Django views",
            "content_url": "https://example.com/advanced-views",
            "order": 3,
        }

        response = self.client.post(
            f"/api/trainings/manage/{self.course.id}/sections/",
            data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertTrue(
            TrainingSection.objects.filter(
                course=self.course,
                title="Advanced Views",
            ).exists()
        )


