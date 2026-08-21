from django.urls import path
from .views.profile import ProfileAPIView
from .views.dashboard_api import DashboardAPIView
from .views.leaderboard import LeaderboardAPIView

from rest_framework_simplejwt.views import (
    TokenRefreshView,
)
from .views.token import (
    GamiTokenObtainPairView,
)
from .views.auth import (
    phone_view,
    register_view,
    login_view,
    verify_view,
    resend_otp_view,
    dashboard_view,
    logout_view,
    forgot_password_view,
    reset_password_view,
)
from .views.auth_api import (
    PhoneAPIView,
    RegisterAPIView,
    VerifyOTPAPIView,
    ForgotPasswordAPIView,
    ResetPasswordAPIView,
)
from .views.mission import (
    MissionListAPIView,
    MissionDetailAPIView,
    MissionManagementListAPIView,
    MissionManagementDetailAPIView,
)
from .views.job_position import (
    JobPositionListAPIView,
    JobPositionDetailAPIView,
)
from .views.question import (
    JobQuestionListAPIView,
)
from .views.job_application import (
    JobApplicationListAPIView,
    JobApplicationCreateAPIView,
    JobApplicationDetailAPIView,
)
from .views.mission_admin import (
    MissionCreateAPIView,
    MissionDetailUpdateDeleteAPIView,
    MissionAssignAPIView,
)
from .views.job_position_admin import (
    JobPositionCreateAPIView,
    JobPositionDetailUpdateDeleteAPIView,
)
from .views.user_admin import (
    UserAdminListCreateAPIView,
    UserAdminDetailAPIView,
)
from .views.job_application_page import job_application_page

urlpatterns = [

    path(
        "job-positions/<int:pk>/apply/",
        job_application_page,
        name="job_application",
    ),

    # ATHENTICATION PAGES
    path("", phone_view, name="phone"),
    path("register/", register_view, name="register"),
    path("login/", login_view, name="login"),
    path("verify/", verify_view, name="verify"),
    path("resend/", resend_otp_view, name="resend_otp"),
    path("forgot-password/", forgot_password_view, name="forgot_password"),
    path("reset-password/", reset_password_view, name="reset_password"),
    path("logout/", logout_view, name="logout"),

    # WEBSITE PAGES
    path("dashboard/", dashboard_view, name="dashboard"),

    # REST API
    path("api/profile/",
        ProfileAPIView.as_view(),
        name="api_profile"
    ),

    path(
        "api/leaderboard/",
        LeaderboardAPIView.as_view(),
        name="api_leaderboard"
    ),

    path(
        "api/missions/",
        MissionListAPIView.as_view(),
        name="api_mission_list",
    ),

    path(
        "api/missions/<int:pk>/",
        MissionDetailAPIView.as_view(),
        name="api_mission_detail",
    ),

    path(
        "api/mission-management/",
        MissionManagementListAPIView.as_view(),
        name="mission-management-list",
    ),

    path(
        "api/mission-management/<int:pk>/",
        MissionManagementDetailAPIView.as_view(),
        name="mission-management-detail",
    ),

    path(
        "api/mission-management/<int:mission_id>/assign/",
        MissionAssignAPIView.as_view(),
        name="api_mission_assign",
    ),

    path(
        "api/job-positions/",
        JobPositionListAPIView.as_view(),
        name="api_job_position_list",
    ),

    path(
        "api/job-positions/<int:pk>/",
        JobPositionDetailAPIView.as_view(),
        name="api_job_position_detail",
    ),

    path(
        "api/applications/",
        JobApplicationListAPIView.as_view(),
        name="api_application_list",
    ),

    path(
        "api/applications/create/",
        JobApplicationCreateAPIView.as_view(),
        name="api_application_create",
    ),

    path(
        "api/applications/<int:pk>/",
        JobApplicationDetailAPIView.as_view(),
        name="api_application_detail",
    ),

    path(
        "api/job-positions/<int:job_position_id>/questions/",
        JobQuestionListAPIView.as_view(),
        name="api_job_questions",
    ),
    
    path(
        "api/auth/phone/",
        PhoneAPIView.as_view(),
        name="api_phone",
    ),

    path(
        "api/auth/register/",
        RegisterAPIView.as_view(),
        name="api_register",
    ),

    path(
        "api/auth/verify/",
        VerifyOTPAPIView.as_view(),
        name="api_verify",
    ),

    path(
        "api/auth/forgot-password/",
        ForgotPasswordAPIView.as_view(),
        name="api_forgot_password",
    ),

    path(
        "api/auth/reset-password/",
        ResetPasswordAPIView.as_view(),
        name="api_reset_password",
    ),

    path(
        "api/token/",
        GamiTokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),

    path(
        "api/token/refresh/",
        TokenRefreshView.as_view(),
        name="token_refresh",
    ),

    path(
        "api/dashboard/",
        DashboardAPIView.as_view(),
        name="dashboard-api",
    ),

    path(
        "api/missions/create/",
        MissionCreateAPIView.as_view(),
        name="api_mission_create",
    ),

    path(
        "api/missions/<int:pk>/manage/",
        MissionDetailUpdateDeleteAPIView.as_view(),
        name="api_mission_manage",
    ),

    path(
        "api/job-positions/create/",
        JobPositionCreateAPIView.as_view(),
        name="api_job_position_create",
    ),

    path(
        "api/job-positions/<int:pk>/manage/",
        JobPositionDetailUpdateDeleteAPIView.as_view(),
        name="api_job_position_manage",
    ),

    path(
        "api/user-management/",
        UserAdminListCreateAPIView.as_view(),
        name="user-management-list-create",
    ),

    path(
        "api/user-management/<int:pk>/",
        UserAdminDetailAPIView.as_view(),
        name="user-management-detail",
    ),
]