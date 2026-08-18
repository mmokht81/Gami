from django import forms
from django.contrib.auth import get_user_model
import re

User = get_user_model()

class PhoneForm(forms.Form):
    phone_number = forms.CharField(
        label="شماره موبایل",
        max_length=11,
        widget=forms.TextInput(
            attrs={
                "class": "form-control form-control-lg",
                "placeholder": "09*********",
                "autocomplete": "off",
            }
        ),
    )

    def clean_phone_number(self):
        phone = self.cleaned_data["phone_number"].strip()

        if not re.fullmatch(r"09\d{9}", phone):
            raise forms.ValidationError("شماره موبایل معتبر نیست.")

        return phone

class RegisterForm(forms.Form):
    phone_number = forms.CharField(
        widget=forms.HiddenInput()
    )

    password = forms.CharField(
        label="رمز عبور",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control form-control-lg",
                "placeholder": "رمز عبور",
            }
        ),
        min_length=6,
    )

class LoginForm(forms.Form):
    phone_number = forms.CharField(
        widget=forms.HiddenInput()
    )

    password = forms.CharField(
        label="رمز عبور",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control form-control-lg",
                "placeholder": "رمز عبور",
            }
        ),
    )

class VerifyOTPForm(forms.Form):
    code = forms.CharField(
        label="کد تایید",
        max_length=6,
        min_length=6,
        widget=forms.TextInput(
            attrs={
                "class": "form-control form-control-lg text-center",
                "placeholder": "12**56",
                "autocomplete": "off",
                "maxlength": "6",
            }
        ),
    )

    def clean_code(self):
        code = self.cleaned_data["code"].strip()

        if not code.isdigit():
            raise forms.ValidationError("کد فقط باید شامل عدد باشد.")

        return code

class ForgotPasswordForm(forms.Form):
    phone_number = forms.CharField(
        label="شماره موبایل",
        max_length=11,
        widget=forms.TextInput(
            attrs={
                "class": "form-control form-control-lg",
                "placeholder": "09*********",
            }
        ),
    )

    def clean_phone_number(self):
        phone = self.cleaned_data["phone_number"].strip()

        if not re.fullmatch(r"09\d{9}", phone):
            raise forms.ValidationError("شماره موبایل معتبر نیست.")

        if not User.objects.filter(phone_number=phone).exists():
            raise forms.ValidationError("کاربری با این شماره وجود ندارد.")

        return phone


class ResetPasswordForm(forms.Form):
    password = forms.CharField(
        min_length=6,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control form-control-lg",
                "placeholder": "رمز جدید",
            }
        )
    )