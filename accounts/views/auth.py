from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required

from ..forms import (
    PhoneForm,
    RegisterForm,
    LoginForm,
    VerifyOTPForm,
    ForgotPasswordForm,
    ResetPasswordForm,
)

from ..models import User
from ..services import OTPService


def phone_view(request):
    if request.method == "POST":
        form = PhoneForm(request.POST)

        if form.is_valid():
            phone = form.cleaned_data["phone_number"]

            request.session["phone_number"] = phone

            if User.objects.filter(phone_number=phone).exists():
                return redirect("login")

            return redirect("register")

    else:
        form = PhoneForm()

    return render(
        request,
        "accounts/phone.html",
        {
            "form": form,
        },
    )

def register_view(request):
    phone = request.session.get("phone_number")

    if not phone:
        return redirect("phone")

    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():

            user = User.objects.create_user(
                phone_number=phone,
                password=form.cleaned_data["password"],
            )

            otp = OTPService.create_otp(phone)

            print("=" * 50)
            print(f"REGISTER OTP : {otp.code}")
            print("=" * 50)

            return redirect("verify")

    else:
        form = RegisterForm(
            initial={
                "phone_number": phone,
            }
        )

    return render(
        request,
        "accounts/register.html",
        {
            "form": form,
            "phone_number": phone,
        },
    )

def login_view(request):
    phone = request.session.get("phone_number")

    if not phone:
        return redirect("phone")

    if request.method == "POST":
        form = LoginForm(request.POST)

        if form.is_valid():
            password = form.cleaned_data["password"]

            user = authenticate(
                request,
                phone_number=phone,
                password=password,
            )

            if user is None:
                form.add_error(
                    "password",
                    "رمز عبور اشتباه است."
                )

            elif not user.is_active:
                form.add_error(
                    None,
                    "حساب کاربری شما غیرفعال شده است. لطفاً با واحد HR تماس بگیرید."
                )

                # print(form.errors)

            elif not user.is_phone_verified:
                messages.error(
                    request,
                    "ابتدا شماره موبایل خود را تایید کنید."
                )
                return redirect("verify")

            else:
                login(request, user)
                request.session.pop("phone_number", None)
                return redirect("dashboard")

    else:
        form = LoginForm(
            initial={
                "phone_number": phone,
            }
        )

    return render(
        request,
        "accounts/login.html",
        {
            "form": form,
            "phone_number": phone,
        },
    )

def verify_view(request):
    phone = request.session.get("phone_number")

    if not phone:
        return redirect("phone")

    if request.method == "POST":
        form = VerifyOTPForm(request.POST)

        if form.is_valid():
            result = OTPService.verify_otp(
                phone,
                form.cleaned_data["code"],
            )

            if result["success"]:

                # اگر فرآیند بازیابی رمز عبور باشد،
                # فقط به صفحه تغییر رمز هدایت می‌شود.
                if request.session.get("reset_password"):
                    return redirect("reset_password")

                login(
                    request,
                    result["user"],
                    backend="accounts.backends.PhoneBackend",
                )

                request.session.pop("phone_number", None)

                return redirect("dashboard")

            error = result["error"]

            if error == "invalid_code":
                form.add_error(
                    "code",
                    f"کد اشتباه است. {result['remaining_attempts']} تلاش باقی مانده است."
                )

            elif error == "expired":
                form.add_error(
                    "code",
                    "زمان اعتبار کد به پایان رسیده است."
                )

            elif error == "max_attempts":
                form.add_error(
                    "code",
                    "کد باطل شد. دوباره درخواست کد بدهید."
                )

            elif error == "user_not_found":
                return redirect("phone")

    else:
        form = VerifyOTPForm()

    return render(
        request,
        "accounts/verify.html",
        {
            "form": form,
            "phone_number": phone,
        },
    )

def resend_otp_view(request):
    phone = request.session.get("phone_number")

    if not phone:
        return redirect("phone")

    if not OTPService.can_request_new_otp(phone):
        messages.error(
            request,
            "لطفا تا پایان اعتبار کد قبلی صبر کنید."
        )
        return redirect("verify")

    otp = OTPService.create_otp(phone)

    print("=" * 50)
    print(f"NEW OTP : {otp.code}")
    print("=" * 50)

    messages.success(
        request,
        "کد جدید ارسال شد."
    )

    return redirect("verify")

@login_required
def dashboard_view(request):
    return render(
        request,
        "accounts/dashboard.html",
    )

def logout_view(request):
    logout(request)
    return redirect("phone")

def forgot_password_view(request):

    if request.method == "POST":
        form = ForgotPasswordForm(request.POST)

        if form.is_valid():
            phone = form.cleaned_data["phone_number"]

            request.session["phone_number"] = phone
            request.session["reset_password"] = True

            otp = OTPService.create_otp(phone)

            print("=" * 50)
            print(f"RESET OTP : {otp.code}")
            print("=" * 50)

            return redirect("verify")

    else:
        form = ForgotPasswordForm()

    return render(
        request,
        "accounts/forgot_password.html",
        {
            "form": form,
        },
    )

def reset_password_view(request):

    phone = request.session.get("phone_number")

    if not phone:
        return redirect("phone")

    try:
        user = User.objects.get(phone_number=phone)
    except User.DoesNotExist:
        return redirect("phone")

    if request.method == "POST":
        form = ResetPasswordForm(request.POST)

        if form.is_valid():

            user.set_password(
                form.cleaned_data["password"]
            )

            user.save()

            login(
                request,
                user,
                backend="accounts.backends.PhoneBackend",
            )

            request.session.pop("phone_number", None)
            request.session.pop("reset_password", None)

            return redirect("dashboard")

    else:
        form = ResetPasswordForm()

    return render(
        request,
        "accounts/reset_password.html",
        {
            "form": form,
        },
    )