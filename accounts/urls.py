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
from .views.mission_progress import (
    MissionStartAPIView,
    MissionProgressAPIView,
    MissionCompleteAPIView,
)
from .views.job_position import (
    JobPositionListAPIView,
    JobPositionDetailAPIView,
)
from .views.question import (
    JobQuestionListAPIView,
    QuestionCreateAPIView,
    QuestionDetailUpdateDeleteAPIView,
)
from .views.job_application import (
    JobApplicationListAPIView,
    JobApplicationCreateAPIView,
    JobApplicationDetailAPIView,
    JobApplicationStatusUpdateAPIView,
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
from .views.badge import (
    BadgeListCreateAPIView,
    BadgeDetailAPIView,
    MyBadgesAPIView,
    UserBadgesAPIView,
    AssignBadgeAPIView,
)
from .views.onboarding import (
    MyOnboardingAPIView,
    UserOnboardingAPIView,
)
from .views.onboarding_actions import (
    OnboardingChecklistCompleteAPIView,
    OnboardingTeamAssignAPIView,
    OnboardingHRProgressAPIView,
)
from .views.onboarding_checklist import (
    OnboardingChecklistListCreateAPIView,
    OnboardingChecklistDetailUpdateDeleteAPIView,
)
from .views.team import (
    TeamListCreateAPIView,
    TeamDetailUpdateDeleteAPIView,
)
from .views.challenge import (
    ChallengeListAPIView,
    ChallengeDetailAPIView,
    ChallengeManagementListAPIView,
    ChallengeManagementDetailAPIView,
    ChallengeRegisterAPIView,
    ChallengeCancelAPIView,
    ChallengeParticipantsAPIView,
    ChallengeWinnersAPIView,
    ChallengeAddWinnerAPIView,
)
from .views.training import (
    TrainingListAPIView,
    TrainingDetailAPIView,
    TrainingEnrollAPIView,
    TrainingSectionStartAPIView,
    MyTrainingListAPIView,
    MyTrainingDetailAPIView,
)
from .views.training_admin import (
    TrainingManagementListCreateAPIView,
    TrainingManagementDetailAPIView,
    TrainingSectionListCreateAPIView,
    TrainingSectionDetailAPIView,
)

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
        "api/missions/<int:mission_id>/start/",
        MissionStartAPIView.as_view(),
        name="api_mission_start",
    ),

    path(
        "api/missions/<int:mission_id>/progress/",
        MissionProgressAPIView.as_view(),
        name="api_mission_progress",
    ),

    path(
        "api/missions/<int:mission_id>/complete/",
        MissionCompleteAPIView.as_view(),
        name="api_mission_complete",
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
        "api/applications/<int:pk>/status/",
        JobApplicationStatusUpdateAPIView.as_view(),
        name="api_application_status_update",
    ),

    path(
        "api/job-positions/<int:job_position_id>/questions/",
        JobQuestionListAPIView.as_view(),
        name="api_job_questions",
    ),

    path(
        "api/questions/create/",
        QuestionCreateAPIView.as_view(),
        name="api_question_create",
    ),

    path(
        "api/questions/<int:pk>/",
        QuestionDetailUpdateDeleteAPIView.as_view(),
        name="api_question_detail",
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

    path(
        "api/badges/",
        BadgeListCreateAPIView.as_view(),
        name="api_badge_list_create",
    ),

    path(
        "api/badges/my/",
        MyBadgesAPIView.as_view(),
        name="api_my_badges",
    ),

    path(
        "api/badges/users/<int:user_id>/",
        UserBadgesAPIView.as_view(),
        name="api_user_badges",
    ),

    path(
        "api/badges/<int:badge_id>/users/<int:user_id>/assign/",
        AssignBadgeAPIView.as_view(),
        name="api_badge_assign",
    ),

    path(
        "api/badges/<int:pk>/",
        BadgeDetailAPIView.as_view(),
        name="api_badge_detail",
    ),

    path(
        "api/onboarding/",
        MyOnboardingAPIView.as_view(),
        name="api_my_onboarding",
    ),

    path(
        "api/onboarding/users/<int:user_id>/",
        UserOnboardingAPIView.as_view(),
        name="api_user_onboarding",
    ),

    path(
        "api/teams/",
        TeamListCreateAPIView.as_view(),
        name="api_team_list_create",
    ),

    path(
        "api/teams/<int:pk>/",
        TeamDetailUpdateDeleteAPIView.as_view(),
        name="api_team_detail",
    ),

    path(
        "api/onboarding/checklist/",
        OnboardingChecklistListCreateAPIView.as_view(),
        name="api_onboarding_checklist_list_create",
    ),

    path(
        "api/onboarding/checklist/<int:pk>/",
        OnboardingChecklistDetailUpdateDeleteAPIView.as_view(),
        name="api_onboarding_checklist_detail",
    ),

    path(
        "api/onboarding/checklist/complete/",
        OnboardingChecklistCompleteAPIView.as_view(),
        name="api_onboarding_checklist_complete",
    ),

    path(
        "api/onboarding/users/<int:user_id>/team/",
        OnboardingTeamAssignAPIView.as_view(),
        name="api_onboarding_team_assign",
    ),

    path(
        "api/onboarding/users/<int:user_id>/hr-progress/",
        OnboardingHRProgressAPIView.as_view(),
        name="api_onboarding_hr_progress",
    ),

    path(
        "api/challenges/",
        ChallengeListAPIView.as_view(),
        name="challenge-list",
    ),

    path(
        "api/challenges/<int:pk>/",
        ChallengeDetailAPIView.as_view(),
        name="challenge-detail",
    ),

    path(
        "api/challenges/manage/",
        ChallengeManagementListAPIView.as_view(),
        name="challenge-management-list",
    ),

    path(
        "api/challenges/manage/<int:pk>/",
        ChallengeManagementDetailAPIView.as_view(),
        name="challenge-management-detail",
    ),

    path(
        "api/challenges/<int:pk>/register/",
        ChallengeRegisterAPIView.as_view(),
        name="challenge-register",
    ),

    path(
        "api/challenges/<int:pk>/cancel/",
        ChallengeCancelAPIView.as_view(),
        name="challenge-cancel",
    ),

    path(
        "api/challenges/<int:pk>/participants/",
        ChallengeParticipantsAPIView.as_view(),
        name="challenge-participants",
    ),

    path(
        "api/challenges/<int:pk>/winners/",
        ChallengeWinnersAPIView.as_view(),
        name="challenge-winners",
    ),

    path(
        "api/challenges/<int:pk>/winners/add/",
        ChallengeAddWinnerAPIView.as_view(),
        name="challenge-add-winner",
    ),

    path(
        "api/trainings/",
        TrainingListAPIView.as_view(),
        name="training-list",
    ),

    path(
        "api/trainings/my/",
        MyTrainingListAPIView.as_view(),
        name="my-training-list",
    ),

    path(
        "api/trainings/my/<int:training_id>/",
        MyTrainingDetailAPIView.as_view(),
        name="my-training-detail",
    ),

    path(
        "api/trainings/<int:training_id>/",
        TrainingDetailAPIView.as_view(),
        name="training-detail",
    ),

    path(
        "api/trainings/<int:training_id>/enroll/",
        TrainingEnrollAPIView.as_view(),
        name="training-enroll",
    ),

    path(
        "api/trainings/<int:training_id>/sections/<int:section_id>/start/",
        TrainingSectionStartAPIView.as_view(),
        name="training-section-start",
    ),

    path(
        "api/trainings/manage/",
        TrainingManagementListCreateAPIView.as_view(),
        name="training-management-list-create",
    ),

    path(
        "api/trainings/manage/<int:pk>/",
        TrainingManagementDetailAPIView.as_view(),
        name="training-management-detail",
    ),

    path(
        "api/trainings/manage/<int:training_id>/sections/",
        TrainingSectionListCreateAPIView.as_view(),
        name="training-section-list-create",
    ),

    path(
        "api/trainings/manage/<int:training_id>/sections/<int:pk>/",
        TrainingSectionDetailAPIView.as_view(),
        name="training-section-detail",
    ),
]