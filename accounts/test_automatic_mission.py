from django.test import TestCase

from .models import User, Mission, UserMission
from .automatic_mission_service import AutomaticMissionService


class AutomaticMissionIdempotencyTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone_number="09129999999",
            password="testpass123",
        )

        self.mission = Mission.objects.create(
            name="Reach Level 1",
            description="Automatic level mission",
            type="AUTOMATIC",
            points=20,
            is_active=True,
            target_level=1,
        )

    def test_automatic_mission_completion_is_idempotent(self):
        self.user.level = 1
        self.user.save(update_fields=["level"])

        user_mission, first_reward = (
            AutomaticMissionService.sync_mission(
                self.user,
                self.mission,
            )
        )

        self.assertTrue(first_reward)
        self.assertEqual(user_mission.progress, 100)
        self.assertEqual(user_mission.status, "COMPLETED")

        second_user_mission, second_reward = (
            AutomaticMissionService.sync_mission(
                self.user,
                self.mission,
            )
        )

        self.assertEqual(
            second_user_mission.pk,
            user_mission.pk,
        )
        self.assertIsNone(second_reward)

        self.assertEqual(
            UserMission.objects.filter(
                user=self.user,
                mission=self.mission,
            ).count(),
            1,
        )