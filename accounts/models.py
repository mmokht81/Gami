from datetime import timedelta

from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
)
from django.core.validators import (
    MinValueValidator,
    MaxValueValidator,
)
from django.db import models
from django.utils import timezone

from .managers import UserManager


# Choices
ROLE_CHOICES = (
    ("USER", "User"),
    ("ADMIN", "Admin"),
    ("SUPERADMIN", "Super Admin"),
)
STATUS_CHOICES = (
    ("جویای کار", "جویای کار"),
    ("استخدام شده", "استخدام شده"),
)
APPLICATION_STATUS = (
    ("PENDING_REVIEW", "در انتظار بررسی"),
    ("HR_REVIEW", "در حال بررسی توسط HR"),
    ("WAITING_FOR_USER", "در انتظار پاسخ کاربر"),
    ("MANAGEMENT_REVIEW", "در حال بررسی توسط مدیریت"),
    ("ACCEPTED", "پذیرفته شده"),
    ("REJECTED", "رد شده"),
)
QUESTION_TYPES = (
    ("TEMPLATE", "Template"),
    ("CUSTOM", "Custom"),
)
MISSION_TYPE = (
    ("AUTOMATIC", "Automatic"),
    ("HR", "HR"),
    ("USER", "User"),
)
MISSION_STATUS = (
    ("PENDING", "Pending"),
    ("IN_PROGRESS", "In Progress"),
    ("COMPLETED", "Completed"),
)

# Team
class Team(models.Model):

    name = models.CharField(
        max_length=255,
        unique=True,
    )

    description = models.TextField(
        blank=True,
        default="",
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


# User
class User(AbstractBaseUser, PermissionsMixin):

    phone_number = models.CharField(
        max_length=11,
        unique=True,
    )

    first_name = models.CharField(
        max_length=100,
        blank=True,
    )

    last_name = models.CharField(
        max_length=100,
        blank=True,
    )

    points = models.PositiveIntegerField(
        default=10,
    )

    level = models.PositiveIntegerField(
        default=0,
    )

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default="USER",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="جویای کار",
    )

    is_phone_verified = models.BooleanField(
        default=False,
    )

    is_active = models.BooleanField(
        default=True,
    )

    is_staff = models.BooleanField(
        default=False,
    )

    date_joined = models.DateTimeField(
        auto_now_add=True,
    )

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    objects = UserManager()

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.phone_number


# OTP
class OTP(models.Model):

    phone_number = models.CharField(
        max_length=11,
        db_index=True,
    )

    code = models.CharField(
        max_length=6,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    expires_at = models.DateTimeField()

    is_used = models.BooleanField(
        default=False,
    )

    attempts = models.PositiveSmallIntegerField(
        default=0,
    )

    def save(self, *args, **kwargs):

        if not self.pk and not self.expires_at:
            self.expires_at = (
                timezone.now() + timedelta(minutes=2)
            )

        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"{self.phone_number} - {self.code}"


# Job Position
class JobPosition(models.Model):

    title = models.CharField(
        max_length=255,
        unique=True,
    )

    description = models.TextField()

    tags = models.JSONField(
        default=list,
        blank=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    def __str__(self):
        return self.title


# Onboarding Checklist Item
class OnboardingChecklistItem(models.Model):

    CHECKLIST_TYPE_CHOICES = (
        ("DOCUMENT", "Document"),
        ("TRAINING", "Training"),
        ("TASK", "Task"),
        ("MEETING", "Meeting"),
        ("PROFILE", "Profile"),
        ("OTHER", "Other"),
    )

    job_position = models.ForeignKey(
        JobPosition,
        on_delete=models.CASCADE,
        related_name="onboarding_checklist",
    )

    icon = models.CharField(
        max_length=100,
        blank=True,
        default="",
    )

    points = models.PositiveIntegerField(
        default=0,
    )

    title = models.CharField(
        max_length=255,
    )

    type = models.CharField(
        max_length=20,
        choices=CHECKLIST_TYPE_CHOICES,
        default="TASK",
    )

    description = models.TextField(
        blank=True,
        default="",
    )

    order = models.PositiveIntegerField(
        default=1,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.title


# Onboarding
class Onboarding(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="onboarding",
    )

    job_position = models.ForeignKey(
        JobPosition,
        on_delete=models.PROTECT,
        related_name="onboardings",
    )

    team = models.ForeignKey(
        Team,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="onboardings",
    )

    hr_progress = models.PositiveSmallIntegerField(
        default=0,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100),
        ],
    )

    checklist_progress = models.PositiveSmallIntegerField(
        default=0,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100),
        ],
    )

    progress = models.PositiveSmallIntegerField(
        default=0,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100),
        ],
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def calculate_progress(self):
        self.progress = round(
            (
                self.checklist_progress * 70
                + self.hr_progress * 30
            ) / 100
        )

        return self.progress

    def save(self, *args, **kwargs):
        self.calculate_progress()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Onboarding - {self.user}"


# Onboarding Checklist Progress
class OnboardingChecklistProgress(models.Model):

    onboarding = models.ForeignKey(
        Onboarding,
        on_delete=models.CASCADE,
        related_name="checklist_progress_items",
    )

    checklist_item = models.ForeignKey(
        OnboardingChecklistItem,
        on_delete=models.CASCADE,
        related_name="user_progress",
    )

    is_completed = models.BooleanField(
        default=False,
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "onboarding",
                    "checklist_item",
                ],
                name="unique_onboarding_checklist_item",
            )
        ]

    def __str__(self):
        return (
            f"{self.onboarding.user} - "
            f"{self.checklist_item.title}"
        )


# Mission
class Mission(models.Model):

    name = models.CharField(
        max_length=255,
    )

    description = models.TextField()

    type = models.CharField(
        max_length=20,
        choices=MISSION_TYPE,
        default="USER",
    )

    points = models.PositiveIntegerField(
        default=0,
    )

    is_active = models.BooleanField(
        default=True,
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


# Job Application
class JobApplication(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="applications",
    )

    job_position = models.ForeignKey(
        JobPosition,
        on_delete=models.CASCADE,
        related_name="applications",
    )

    status = models.CharField(
        max_length=30,
        choices=APPLICATION_STATUS,
        default="PENDING_REVIEW",
    )

    answers = models.JSONField(
        default=list,
        blank=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    submitted_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        unique_together = ("user", "job_position")

    def __str__(self):
        return f"{self.user} - {self.job_position}"


# Question
class Question(models.Model):

    job_position = models.ForeignKey(
        JobPosition,
        on_delete=models.CASCADE,
        related_name="questions",
    )

    type = models.CharField(
        max_length=20,
        choices=QUESTION_TYPES,
    )

    text = models.TextField()

    order = models.PositiveIntegerField(
        default=1,
    )

    is_active = models.BooleanField(
        default=True,
    )

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.text[:50]


# User Mission
class UserMission(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="user_missions",
    )

    mission = models.ForeignKey(
        Mission,
        on_delete=models.CASCADE,
        related_name="user_missions",
    )

    progress = models.PositiveSmallIntegerField(
        default=0,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100),
        ],
    )

    status = models.CharField(
        max_length=20,
        choices=MISSION_STATUS,
        default="PENDING",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        unique_together = ("user", "mission")

    def __str__(self):
        return f"{self.user.phone_number} - {self.mission.name}"


# Badge
class Badge(models.Model):

    name = models.CharField(
        max_length=100,
        unique=True,
    )

    label = models.CharField(
        max_length=100,
    )

    icon = models.CharField(
        max_length=10,
    )

    description = models.TextField()

    is_active = models.BooleanField(
        default=True,
    )

    def __str__(self):
        return self.name


# User Badge
class UserBadge(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="badges",
    )

    badge = models.ForeignKey(
        Badge,
        on_delete=models.CASCADE,
        related_name="user_badges",
    )

    reason = models.TextField()

    assigned_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "badge"],
                name="unique_user_badge",
            )
        ]
        ordering = ["-assigned_at"]

    def __str__(self):
        return f"{self.user} - {self.badge}"


# Badge Rule
class BadgeRule(models.Model):

    RULE_TYPE = (
        (
            "MISSIONS_COMPLETED",
            "Missions Completed",
        ),
    )

    badge = models.OneToOneField(
        Badge,
        on_delete=models.CASCADE,
        related_name="rule",
    )

    rule_type = models.CharField(
        max_length=50,
        choices=RULE_TYPE,
    )

    value = models.PositiveIntegerField(
        default=1,
    )

    is_active = models.BooleanField(
        default=True,
    )

    def __str__(self):
        return f"{self.badge.name} - {self.rule_type}"


# Level
class Level(models.Model):

    level = models.PositiveIntegerField(
        unique=True,
    )

    required_points = models.PositiveIntegerField(
        unique=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    class Meta:
        ordering = ["required_points"]

    def __str__(self):
        return f"Level {self.level}"