from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APITestCase

from .models import (
    User,
    Challenge,
    ChallengeParticipant,
    ChallengeWinner,
)


class ChallengeAPITestCase(APITestCase):

    def setUp(self):

        self.user = User.objects.create_user(
            phone_number="09120000001",
            password="Test1234",
            first_name="Test",
            last_name="User",
        )

        self.user2 = User.objects.create_user(
            phone_number="09120000002",
            password="Test1234",
            first_name="Test",
            last_name="User2",
        )

        self.admin = User.objects.create_user(
            phone_number="09120000003",
            password="Test1234",
            first_name="Admin",
            last_name="User",
            role="ADMIN",
        )

        self.challenge = Challenge.objects.create(
            name="Python Challenge",
            description="Test challenge",
            tags=[
                "python",
                "backend",
            ],
            start_time=timezone.now() + timedelta(hours=2),
            end_time=timezone.now() + timedelta(hours=4),
            requirements=[
                "Solve the task",
                "Submit before deadline",
            ],
            points=100,
            type="CHALLENGE",
            event_link="https://example.com/challenge",
            is_active=True,
        )

    def authenticate(self, user):

        self.client.force_authenticate(
            user=user
        )

    # --------------------------------------------------
    # Challenge List
    # --------------------------------------------------

    def test_challenge_list(self):

        self.authenticate(self.user)

        response = self.client.get("/api/challenges/")

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            "results",
            response.data,
        )

        self.assertTrue(
            any(
                item["id"] == self.challenge.id
                for item in response.data["results"]
            )
        )

    # --------------------------------------------------
    # Challenge Detail
    # --------------------------------------------------

    def test_challenge_detail(self):

        self.authenticate(self.user)

        url = reverse(
            "challenge-detail",
            kwargs={
                "pk": self.challenge.id
            },
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["name"],
            "Python Challenge",
        )

        self.assertEqual(
            response.data["participants_count"],
            0,
        )

        self.assertEqual(
            response.data["winners"],
            [],
        )

    # --------------------------------------------------
    # Register
    # --------------------------------------------------

    def test_user_can_register(self):

        self.authenticate(self.user)

        url = reverse(
            "challenge-register",
            kwargs={
                "pk": self.challenge.id
            },
        )

        response = self.client.post(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertTrue(
            response.data["ok"]
        )

        self.assertEqual(
            ChallengeParticipant.objects.filter(
                challenge=self.challenge,
                user=self.user,
                is_cancelled=False,
            ).count(),
            1,
        )

    # --------------------------------------------------
    # Duplicate Register
    # --------------------------------------------------

    def test_user_cannot_register_twice(self):

        ChallengeParticipant.objects.create(
            challenge=self.challenge,
            user=self.user,
        )

        self.authenticate(self.user)

        url = reverse(
            "challenge-register",
            kwargs={
                "pk": self.challenge.id
            },
        )

        response = self.client.post(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    # --------------------------------------------------
    # Cancel Registration
    # --------------------------------------------------

    def test_user_can_cancel_registration(self):

        ChallengeParticipant.objects.create(
            challenge=self.challenge,
            user=self.user,
        )

        self.authenticate(self.user)

        url = reverse(
            "challenge-cancel",
            kwargs={
                "pk": self.challenge.id
            },
        )

        response = self.client.post(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        participant = ChallengeParticipant.objects.get(
            challenge=self.challenge,
            user=self.user,
        )

        self.assertTrue(
            participant.is_cancelled
        )

    # --------------------------------------------------
    # Cannot Cancel Within 30 Minutes
    # --------------------------------------------------

    def test_user_cannot_cancel_within_30_minutes(self):

        self.challenge.start_time = (
            timezone.now() + timedelta(minutes=20)
        )

        self.challenge.save()

        ChallengeParticipant.objects.create(
            challenge=self.challenge,
            user=self.user,
        )

        self.authenticate(self.user)

        url = reverse(
            "challenge-cancel",
            kwargs={
                "pk": self.challenge.id
            },
        )

        response = self.client.post(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    # --------------------------------------------------
    # Participants Count
    # --------------------------------------------------

    def test_participants_count(self):

        ChallengeParticipant.objects.create(
            challenge=self.challenge,
            user=self.user,
        )

        ChallengeParticipant.objects.create(
            challenge=self.challenge,
            user=self.user2,
        )

        self.authenticate(self.user)

        url = reverse(
            "challenge-detail",
            kwargs={
                "pk": self.challenge.id
            },
        )

        response = self.client.get(url)

        self.assertEqual(
            response.data["participants_count"],
            2,
        )

    # --------------------------------------------------
    # Cancelled User Not Counted
    # --------------------------------------------------

    def test_cancelled_user_not_counted(self):

        ChallengeParticipant.objects.create(
            challenge=self.challenge,
            user=self.user,
            is_cancelled=True,
            cancelled_at=timezone.now(),
        )

        self.authenticate(self.user)

        url = reverse(
            "challenge-detail",
            kwargs={
                "pk": self.challenge.id
            },
        )

        response = self.client.get(url)

        self.assertEqual(
            response.data["participants_count"],
            0,
        )

    # --------------------------------------------------
    # Admin Can Create Challenge
    # --------------------------------------------------

    def test_admin_can_create_challenge(self):

        self.authenticate(self.admin)

        url = reverse(
            "challenge-management-list"
        )

        data = {
            "name": "New Challenge",
            "description": "New test",
            "tags": [
                "django"
            ],
            "start_time": (
                timezone.now()
                + timedelta(days=1)
            ).isoformat(),
            "end_time": (
                timezone.now()
                + timedelta(days=1, hours=2)
            ).isoformat(),
            "requirements": [
                "Complete task"
            ],
            "points": 200,
            "type": "CHALLENGE",
            "event_link": "https://example.com",
            "is_active": True,
        }

        response = self.client.post(
            url,
            data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            Challenge.objects.count(),
            2,
        )

    # --------------------------------------------------
    # Normal User Cannot Create
    # --------------------------------------------------

    def test_normal_user_cannot_create_challenge(self):

        self.authenticate(self.user)

        url = reverse(
            "challenge-management-list"
        )

        response = self.client.post(
            url,
            {
                "name": "Unauthorized",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    # --------------------------------------------------
    # Winner Must Be Participant
    # --------------------------------------------------

    def test_winner_must_be_participant(self):

        self.challenge.start_time = (
            timezone.now() - timedelta(hours=4)
        )

        self.challenge.end_time = (
            timezone.now() - timedelta(hours=1)
        )

        self.challenge.save()

        self.authenticate(self.admin)

        url = reverse(
            "challenge-add-winner",
            kwargs={
                "pk": self.challenge.id
            },
        )

        response = self.client.post(
            url,
            {
                "user_id": self.user.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    # --------------------------------------------------
    # Challenge Winner Gets Fixed Points
    # --------------------------------------------------

    def test_challenge_winner_gets_fixed_points(self):

        self.challenge.start_time = (
            timezone.now() - timedelta(hours=4)
        )

        self.challenge.end_time = (
            timezone.now() - timedelta(hours=1)
        )

        self.challenge.save()

        ChallengeParticipant.objects.create(
            challenge=self.challenge,
            user=self.user,
        )

        initial_points = self.user.points

        self.authenticate(self.admin)

        url = reverse(
            "challenge-add-winner",
            kwargs={
                "pk": self.challenge.id
            },
        )

        response = self.client.post(
            url,
            {
                "user_id": self.user.id,
                "rank": 1,
                "points": 9999,
                "prize": "Prize",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.user.refresh_from_db()

        self.assertEqual(
            self.user.points,
            initial_points + self.challenge.points,
        )

        winner = ChallengeWinner.objects.get(
            challenge=self.challenge,
            user=self.user,
        )

        self.assertEqual(
            winner.points,
            self.challenge.points,
        )

    # --------------------------------------------------
    # Competition Winner Gets Submitted Points
    # --------------------------------------------------

    def test_competition_winner_gets_submitted_points(self):

        competition = Challenge.objects.create(
            name="Test Competition",
            description="Competition",
            tags=["competition"],
            start_time=(
                timezone.now()
                - timedelta(hours=4)
            ),
            end_time=(
                timezone.now()
                - timedelta(hours=1)
            ),
            requirements=[],
            points=0,
            type="COMPETITION",
            event_link="https://example.com",
            is_active=True,
        )

        ChallengeParticipant.objects.create(
            challenge=competition,
            user=self.user,
        )

        initial_points = self.user.points

        self.authenticate(self.admin)

        url = reverse(
            "challenge-add-winner",
            kwargs={
                "pk": competition.id
            },
        )

        response = self.client.post(
            url,
            {
                "user_id": self.user.id,
                "rank": 1,
                "points": 500,
                "prize": "First Prize",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.user.refresh_from_db()

        self.assertEqual(
            self.user.points,
            initial_points + 500,
        )

    # --------------------------------------------------
    # Winners List
    # --------------------------------------------------

    def test_winners_list(self):

        ChallengeParticipant.objects.create(
            challenge=self.challenge,
            user=self.user,
        )

        self.challenge.start_time = (
            timezone.now() - timedelta(hours=4)
        )

        self.challenge.end_time = (
            timezone.now() - timedelta(hours=1)
        )

        self.challenge.save()

        ChallengeWinner.objects.create(
            challenge=self.challenge,
            user=self.user,
            rank=1,
            points=100,
            prize="First Prize",
        )

        self.authenticate(self.user)

        response = self.client.get(
            f"/api/challenges/{self.challenge.id}/winners/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            "results",
            response.data,
        )

        self.assertTrue(
            any(
                item["user"]["id"] == self.user.id
                for item in response.data["results"]
            )
        )

    # --------------------------------------------------
    # Status Becomes Finished
    # --------------------------------------------------

    def test_challenge_becomes_finished(self):

        self.challenge.start_time = (
            timezone.now() - timedelta(hours=4)
        )

        self.challenge.end_time = (
            timezone.now() - timedelta(hours=1)
        )

        self.challenge.save()

        self.assertEqual(
            self.challenge.status,
            "FINISHED",
        )