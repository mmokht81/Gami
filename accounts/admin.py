from django.contrib import admin
from .models import (
    User,
    OTP,
    Mission,
    UserMission,
    JobPosition,
    Question,
    JobApplication,
    Badge,
    UserBadge,
    Level,
    Team,
    Onboarding,
    OnboardingChecklistItem,
    OnboardingChecklistProgress,
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


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "label",
        "icon",
        "is_active",
    )
    list_filter = ("is_active",)
    search_fields = (
        "name",
        "label",
    )


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "badge",
        "assigned_at",
    )
    list_filter = ("badge",)
    search_fields = (
        "user__phone_number",
        "badge__name",
    )


@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = (
        "level",
        "required_points",
        "is_active",
    )

    list_filter = (
        "is_active",
    )

    ordering = (
        "level",
    )


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "is_active",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "name",
        "description",
    )

    list_filter = (
        "is_active",
    )

    ordering = (
        "name",
    )


@admin.register(Onboarding)
class OnboardingAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "job_position",
        "team",
        "checklist_progress",
        "hr_progress",
        "progress",
        "created_at",
    )

    search_fields = (
        "user__phone_number",
        "user__first_name",
        "user__last_name",
        "job_position__title",
        "team__name",
    )

    list_filter = (
        "job_position",
        "team",
    )

    ordering = (
        "-created_at",
    )

    autocomplete_fields = (
        "user",
        "job_position",
        "team",
    )


@admin.register(OnboardingChecklistItem)
class OnboardingChecklistItemAdmin(admin.ModelAdmin):

    list_display = (
        "title",
        "job_position",
        "type",
        "points",
        "order",
        "is_active",
    )

    search_fields = (
        "title",
        "description",
        "job_position__title",
    )

    list_filter = (
        "type",
        "is_active",
        "job_position",
    )

    ordering = (
        "job_position",
        "order",
        "id",
    )


@admin.register(OnboardingChecklistProgress)
class OnboardingChecklistProgressAdmin(admin.ModelAdmin):

    list_display = (
        "onboarding",
        "checklist_item",
        "is_completed",
        "completed_at",
    )

    search_fields = (
        "onboarding__user__phone_number",
        "checklist_item__title",
    )

    list_filter = (
        "is_completed",
    )

    ordering = (
        "-completed_at",
    )


