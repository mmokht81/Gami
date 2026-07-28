from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required

from .forms import PhoneLoginForm, VerifyOTPForm
from .services import OTPService


def login_view(request):
    if request.method == "POST":
        form = PhoneLoginForm(request.POST)

        if form.is_valid():
            phone_number = form.cleaned_data["phone_number"]

            otp = OTPService.create_otp(phone_number)

            OTPService.send_sms(
                phone_number,
                otp.code,
            )

            request.session["phone_number"] = phone_number

            return redirect("verify")

    else:
        form = PhoneLoginForm()

    return render(
        request,
        "accounts/login.html",
        {
            "form": form,
        },
    )


def verify_view(request):
    phone_number = request.session.get("phone_number")

    if not phone_number:
        return redirect("login")

    if request.method == "POST":
        form = VerifyOTPForm(request.POST)

        if form.is_valid():
            code = form.cleaned_data["code"]

            result = OTPService.verify_otp(
                phone_number,
                code,
            )

            if result["success"]:
                login(request, result["user"])

                request.session.pop("phone_number", None)

                return redirect("dashboard")

            error = result["error"]

            if error == "invalid_code":
                form.add_error(
                    "code",
                    f"کد وارد شده اشتباه است. {result['remaining_attempts']} تلاش باقی مانده است."
                )

            elif error == "expired":
                form.add_error(
                    "code",
                    "زمان اعتبار کد به پایان رسیده است."
                )

            elif error == "max_attempts":
                form.add_error(
                    "code",
                    "۵ بار کد را اشتباه وارد کردید. این کد باطل شد. لطفاً کد جدید دریافت کنید."
                )

            else:
                form.add_error(
                    "code",
                    "کد معتبر یافت نشد."
                )

    else:
        form = VerifyOTPForm()

    return render(
        request,
        "accounts/verify.html",
        {
            "form": form,
        },
    )


@login_required
def dashboard_view(request):
    return render(
        request,
        "accounts/dashboard.html",
    )


def logout_view(request):
    logout(request)
    return redirect("login")


def resend_otp_view(request):
    phone_number = request.session.get("phone_number")

    if not phone_number:
        return redirect("login")

    if not OTPService.can_request_new_otp(phone_number):
        messages.error(
            request,
            "لطفاً تا پایان زمان اعتبار کد فعلی صبر کنید."
        )
        return redirect("verify")

    otp = OTPService.create_otp(phone_number)

    OTPService.send_sms(
        phone_number,
        otp.code,
    )

    messages.success(
        request,
        "کد جدید ارسال شد."
    )

    return redirect("verify")