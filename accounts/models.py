from django.db import models
from .managers import UserManager
from django.utils import timezone
from datetime import timedelta
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
)

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
    ("PENDING", "Pending"),
    ("ACCEPTED", "Accepted"),
    ("REJECTED", "Rejected"),
)
QUESTION_TYPES = (
    ("TEMPLATE", "Template"),
    ("CUSTOM", "Custom"),
)
MISSION_STATUS = (
    ("PENDING", "Pending"),
    ("IN_PROGRESS", "In Progress"),
    ("COMPLETED", "Completed"),
)


class User(AbstractBaseUser, PermissionsMixin):

    phone_number = models.CharField(
        max_length=11,
        unique=True
    )

    first_name = models.CharField(
        max_length=100,
        blank=True
    )

    last_name = models.CharField(
        max_length=100,
        blank=True
    )

    points = models.PositiveIntegerField(
        default=10
    )

    level = models.PositiveIntegerField(
        default=0
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
        default=False
    )

    is_active = models.BooleanField(
        default=True
    )

    is_staff = models.BooleanField(
        default=False
    )

    date_joined = models.DateTimeField(
        auto_now_add=True
    )

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    objects = UserManager()

    USERNAME_FIELD = "phone_number"

    REQUIRED_FIELDS = []

    def __str__(self):
        return self.phone_number

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
            self.expires_at = timezone.now() + timedelta(minutes=2)

        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"{self.phone_number} - {self.code}"

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

class Mission(models.Model):

    name = models.CharField(
        max_length=255
    )

    description = models.TextField()

    points = models.PositiveIntegerField(
        default=0
    )

    is_active = models.BooleanField(
        default=True
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

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
        max_length=20,
        choices=APPLICATION_STATUS,
        default="PENDING",
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