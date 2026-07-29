from django.urls import path

from .views import (
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

urlpatterns = [
    path("", phone_view, name="phone"),
    path("register/", register_view, name="register"),
    path("login/", login_view, name="login"),
    path("verify/", verify_view, name="verify"),
    path("resend/", resend_otp_view, name="resend_otp"),
    path("dashboard/", dashboard_view, name="dashboard"),
    path("logout/", logout_view, name="logout"),
    path(
    "forgot-password/",
    forgot_password_view,
    name="forgot_password",
    ),

    path(
        "reset-password/",
        reset_password_view,
        name="reset_password",
    ),
]