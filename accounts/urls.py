from django.urls import path
from .views import (
    login_view,
    verify_view,
    dashboard_view,
    logout_view,
    resend_otp_view,
)

urlpatterns = [
    path("", login_view, name="login"),
    path("verify/", verify_view, name="verify"),
    path("dashboard/", dashboard_view, name="dashboard"),
    path("logout/", logout_view, name="logout"),
    path(
    "resend/",
    resend_otp_view,
    name="resend_otp",
    ),
]