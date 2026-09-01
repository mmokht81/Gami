from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from ..models import Onboarding
from ..permissions import IsAdminOrSuperAdmin
from ..serializers import OnboardingSerializer


class MyOnboardingAPIView(generics.RetrieveAPIView):
    """
    Return the complete onboarding dashboard
    for the authenticated user.
    """

    serializer_class = OnboardingSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):

        return Onboarding.objects.select_related(
            "user",
            "job_position",
            "user__team",
        ).prefetch_related(
            "checklist_progress_items__checklist_item",
            "user__badges__badge",
        ).get(
            user=self.request.user
        )


class UserOnboardingAPIView(generics.RetrieveAPIView):

    serializer_class = OnboardingSerializer
    permission_classes = [IsAdminOrSuperAdmin]

    lookup_url_kwarg = "user_id"

    def get_queryset(self):

        return (
            Onboarding.objects
            .select_related(
                "user",
                "job_position",
                "user__team",
            )
            .prefetch_related(
                "checklist_progress_items__checklist_item",
                "user__badges__badge",
            )
        )