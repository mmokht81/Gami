import secrets

from .models import OTP, User
# import requests
# from django.conf import settings

class OTPService:
    OTP_LENGTH = 6
    MAX_ATTEMPTS = 5
    RESEND_TIMEOUT = 120

    @staticmethod
    def generate_code():
        return "".join(
            secrets.choice("0123456789")
            for _ in range(OTPService.OTP_LENGTH)
        )

    @staticmethod
    def create_otp(phone_number):
        OTP.objects.filter(
            phone_number=phone_number,
            is_used=False,
        ).update(is_used=True)

        otp = OTP.objects.create(
            phone_number=phone_number,
            code=OTPService.generate_code(),
        )

        return otp

    @staticmethod
    def can_request_new_otp(phone_number):
        otp = (
            OTP.objects.filter(
                phone_number=phone_number,
                is_used=False,
            )
            .order_by("-created_at")
            .first()
        )

        if otp is None:
            return True

        return otp.is_expired()

    @staticmethod
    def verify_otp(phone_number, code):

        otp = (
            OTP.objects.filter(
                phone_number=phone_number,
                is_used=False,
            )
            .order_by("-created_at")
            .first()
        )

        if otp is None:
            return {
                "success": False,
                "error": "not_found",
            }

        if otp.is_expired():
            otp.is_used = True
            otp.save(update_fields=["is_used"])

            return {
                "success": False,
                "error": "expired",
            }

        if otp.code != code:
            otp.attempts += 1

            # اگر این تلاش، آخرین تلاش مجاز بود
            if otp.attempts >= OTPService.MAX_ATTEMPTS:
                otp.is_used = True
                otp.save(update_fields=["attempts", "is_used"])

                return {
                    "success": False,
                    "error": "max_attempts",
                }

            otp.save(update_fields=["attempts"])

            return {
                "success": False,
                "error": "invalid_code",
                "remaining_attempts": OTPService.MAX_ATTEMPTS - otp.attempts,
            }

        otp.is_used = True
        otp.save(update_fields=["is_used"])

        user = User.objects.filter(
            phone_number=phone_number
        ).first()

        if not user:
            return {
                "success": False,
                "error": "user_not_found",
            }

        user.is_phone_verified = True
        user.save(update_fields=["is_phone_verified"])

        return {
            "success": True,
            "user": user,
        }
    # @staticmethod
    # def send_sms(phone_number, code):
    #     url = "https://api.sms.ir/v1/send/bulk"

    #     headers = {
    #         "X-API-KEY": settings.SMS_IR_API_KEY,
    #         "Content-Type": "application/json",
    #         "Accept": "application/json",
    #     }

    #     payload = {
    #         "lineNumber": "",
    #         "messageText": [f"کد ورود شما: {code}"],
    #         "mobiles": [phone_number],
    #         "sendDateTime": None,
    #     }

    #     try:
    #         response = requests.post(
    #             url,
    #             json=payload,
    #             headers=headers,
    #             timeout=10,
    #         )

    #         print(response.status_code)
    #         print(response.text)

    #         return response.ok

    #     except Exception as e:
    #         print(e)
    #         return False