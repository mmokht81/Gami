from django.contrib import admin
from .models import (
    User,
    OTP,
    Mission,
    UserMission,
    JobPosition,
    Question,
    JobApplication,
    ApplicationAnswer,
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "phone_number",
        "first_name",
        "last_name",
        "points",
        "level",
        "role",
        "status",
        "is_phone_verified",
    )

    search_fields = (
        "phone_number",
        "first_name",
        "last_name",
    )

    list_filter = (
        "role",
        "status",
        "is_phone_verified",
    )

    ordering = (
        "-date_joined",
    )


@admin.register(Mission)
class MissionAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "points",
        "is_active",
    )

    search_fields = (
        "name",
    )

    list_filter = (
        "is_active",
    )


@admin.register(UserMission)
class UserMissionAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "mission",
        "progress",
        "status",
    )

    list_filter = (
        "status",
    )

    search_fields = (
        "user__phone_number",
        "mission__name",
    )


@admin.register(JobPosition)
class JobPositionAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "is_active",
    )

    search_fields = (
        "title",
    )

    list_filter = (
        "is_active",
    )


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = (
        "job_position",
        "type",
        "order",
        "is_active",
    )

    list_filter = (
        "type",
        "is_active",
    )


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "job_position",
        "status",
        "submitted_at",
    )

    list_filter = (
        "status",
    )

    search_fields = (
        "user__phone_number",
    )

    ordering = (
        "-submitted_at",
    )


@admin.register(ApplicationAnswer)
class ApplicationAnswerAdmin(admin.ModelAdmin):
    list_display = (
        "application",
        "question",
        "answer",
    )


@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = (
        "phone_number",
        "code",
        "is_used",
        "created_at",
        "expires_at",
    )

    search_fields = (
        "phone_number",
    )