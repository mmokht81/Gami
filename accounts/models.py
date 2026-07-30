from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
)

from .managers import UserManager

ROLE_CHOICES = (
    ("USER", "User"),
    ("ADMIN", "Admin"),
    ("SUPERADMIN", "Super Admin"),
)
STATUS_CHOICES = (
    ("جویای کار", "جویای کار"),
    ("استخدام شده", "استخدام شده"),
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

    mission = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    mission_completed = models.BooleanField(
        default=False,
    )

    job_positions = models.ManyToManyField(
        "accounts.JobPosition",
        blank=True,
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

    objects = UserManager()

    USERNAME_FIELD = "phone_number"

    REQUIRED_FIELDS = []

    def __str__(self):
        return self.phone_number

from django.utils import timezone
from datetime import timedelta


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

    def __str__(self):
        return self.title