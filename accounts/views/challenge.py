from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema

from ..models import (
    Challenge,
    ChallengeParticipant,
)
from ..serializers import (
    ChallengeSerializer,
    ChallengeParticipantSerializer,
    ChallengeWinnerSerializer,
    ChallengeRegisterSerializer,
    ChallengeWinnerInputSerializer,
)
from ..services import ChallengeService
from ..permissions import IsAdminOrSuperAdmin


class ChallengeListAPIView(generics.ListAPIView):
    """
    List all challenges and competitions.
    """

    serializer_class = ChallengeSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List challenges and competitions",
        description="""
Returns all challenges and competitions.
""",
        responses=ChallengeSerializer(many=True),
    )
    def get_queryset(self):

        return (
            Challenge.objects
            .all()
            .order_by("-start_time")
        )


class ChallengeDetailAPIView(generics.RetrieveAPIView):
    """
    Retrieve a single challenge or competition.
    """

    serializer_class = ChallengeSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get challenge or competition detail",
        responses=ChallengeSerializer,
    )
    def get_queryset(self):

        return Challenge.objects.all()


class ChallengeManagementListAPIView(
    generics.ListCreateAPIView
):
    """
    Admin API for listing and creating challenges.
    """

    serializer_class = ChallengeSerializer
    permission_classes = [IsAdminOrSuperAdmin]

    @extend_schema(
        summary="List and create challenges",
        responses=ChallengeSerializer(many=True),
    )
    def get_queryset(self):

        return Challenge.objects.all()


class ChallengeManagementDetailAPIView(
    generics.RetrieveUpdateDestroyAPIView
):
    """
    Admin API for updating and deleting challenges.
    """

    serializer_class = ChallengeSerializer
    permission_classes = [IsAdminOrSuperAdmin]

    @extend_schema(
        summary="Get, update or delete challenge",
        responses=ChallengeSerializer,
    )
    def get_queryset(self):

        return Challenge.objects.all()


class ChallengeRegisterAPIView(
    generics.CreateAPIView
):
    """
    Register authenticated user for a challenge.
    """
    serializer_class = ChallengeRegisterSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Register for challenge",
        responses=ChallengeParticipantSerializer,
    )
    def post(self, request, *args, **kwargs):

        challenge = generics.get_object_or_404(
            Challenge,
            pk=kwargs["pk"],
        )

        try:

            participant = ChallengeService.register_user(
                challenge=challenge,
                user=request.user,
            )

        except ValueError as exc:

            return Response(
                {
                    "ok": False,
                    "error": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "ok": True,
                "message": "ثبت نام با موفقیت انجام شد.",
                "participant": ChallengeParticipantSerializer(
                    participant
                ).data,
            },
            status=status.HTTP_201_CREATED,
        )


class ChallengeCancelAPIView(generics.GenericAPIView):

    serializer_class = ChallengeRegisterSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):

        challenge = generics.get_object_or_404(
            Challenge,
            pk=kwargs["pk"],
        )

        try:
            participant = ChallengeService.cancel_registration(
                challenge=challenge,
                user=request.user,
            )

        except ValueError as exc:
            return Response(
                {
                    "ok": False,
                    "error": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "ok": True,
                "message": "لغو ثبت نام با موفقیت انجام شد.",
                "participant": ChallengeParticipantSerializer(
                    participant
                ).data,
            },
            status=status.HTTP_200_OK,
        )


class ChallengeParticipantsAPIView(
    generics.ListAPIView
):
    """
    Admin API for viewing challenge participants.
    """

    serializer_class = ChallengeParticipantSerializer
    permission_classes = [IsAdminOrSuperAdmin]

    @extend_schema(
        summary="List challenge participants",
        responses=ChallengeParticipantSerializer(
            many=True
        ),
    )
    def get_queryset(self):

        challenge = generics.get_object_or_404(
            Challenge,
            pk=self.kwargs["pk"],
        )

        return ChallengeService.get_participants(
            challenge
        )


class ChallengeWinnersAPIView(
    generics.ListAPIView
):
    """
    List winners of a challenge or competition.
    """

    serializer_class = ChallengeWinnerSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List challenge winners",
        responses=ChallengeWinnerSerializer(
            many=True
        ),
    )
    def get_queryset(self):

        challenge = generics.get_object_or_404(
            Challenge,
            pk=self.kwargs["pk"],
        )

        return ChallengeService.get_winners(
            challenge
        )


class ChallengeAddWinnerAPIView(
    generics.CreateAPIView
):
    """
    Admin API for manually adding a winner.
    """

    serializer_class = ChallengeWinnerInputSerializer
    permission_classes = [IsAdminOrSuperAdmin]

    @extend_schema(
        summary="Add challenge or competition winner",
        request=ChallengeWinnerInputSerializer,
        responses=ChallengeWinnerSerializer,
    )
    def post(self, request, *args, **kwargs):

        challenge = generics.get_object_or_404(
            Challenge,
            pk=kwargs["pk"],
        )

        serializer = self.get_serializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        user_id = serializer.validated_data[
            "user_id"
        ]

        from ..models import User

        user = generics.get_object_or_404(
            User,
            pk=user_id,
        )

        try:

            winner = ChallengeService.add_winner(
                challenge=challenge,
                user=user,
                rank=serializer.validated_data.get(
                    "rank"
                ),
                points=serializer.validated_data.get(
                    "points"
                ),
                prize=serializer.validated_data.get(
                    "prize",
                    "",
                ),
            )

        except ValueError as exc:

            return Response(
                {
                    "ok": False,
                    "error": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "ok": True,
                "winner": ChallengeWinnerSerializer(
                    winner
                ).data,
            },
            status=status.HTTP_201_CREATED,
        )




