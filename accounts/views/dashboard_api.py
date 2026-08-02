from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from ..models import UserMission, JobApplication
from drf_spectacular.utils import extend_schema

class DashboardAPIView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    @extend_schema(
        summary="Get dashboard",
        description="""
        Returns dashboard statistics for the authenticated user.

        Includes:
        - User information
        - Mission statistics
        - Job application statistics
        """
    )

    def get(self, request):

        user = request.user

        missions = UserMission.objects.filter(
            user=user
        )

        applications = JobApplication.objects.filter(
            user=user
        )

        return Response({

            "user": {
                "id": user.id,
                "full_name": user.full_name,
                "points": user.points,
                "level": user.level,
                "status": user.status,
            },

            "missions": {
                "total": missions.count(),
                "completed": missions.filter(
                    status="COMPLETED"
                ).count(),
                "active": missions.filter(
                    status="IN_PROGRESS"
                ).count(),
            },

            "applications": {
                "total": applications.count(),
                "pending": applications.filter(
                    status="PENDING"
                ).count(),
            }
        }
    )