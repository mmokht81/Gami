from django import forms
import re


class PhoneLoginForm(forms.Form):
    phone_number = forms.CharField(
        label="شماره موبایل",
        max_length=11,
        widget=forms.TextInput(
            attrs={
                "class": "form-control form-control-lg",
                "placeholder": "09123456789",
                "autocomplete": "off",
            }
        ),
    )

    def clean_phone_number(self):
        phone = self.cleaned_data["phone_number"].strip()

        if not re.fullmatch(r"09\d{9}", phone):
            raise forms.ValidationError(
                "شماره موبایل معتبر نیست."
            )

        return phone

class VerifyOTPForm(forms.Form):
    code = forms.CharField(
        label="کد تایید",
        max_length=6,
        min_length=6,
        widget=forms.TextInput(
            attrs={
                "class": "form-control form-control-lg text-center",
                "placeholder": "123456",
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