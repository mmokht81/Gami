from rest_framework import serializers
from .models import JobApplication
from .models import (
    User,
    Mission,
    UserMission,
    JobPosition,
    Question,
    JobApplication,
    ApplicationAnswer,
)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "phone_number",
            "first_name",
            "last_name",
            "full_name",
            "points",
            "level",
            "role",
            "status",
            "is_phone_verified",
        )
        read_only_fields = (
            "id",
            "phone_number",
            "points",
            "level",
            "role",
            "is_phone_verified",
        )

class LeaderboardSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    rank = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "rank",
            "full_name",
            "points",
            "level",
        )

    def get_rank(self, obj):
        queryset = (
            User.objects.filter(
                is_active=True,
            )
            .order_by(
                "-points",
                "-level",
                "date_joined",
            )
        )

        ids = list(
            queryset.values_list(
                "id",
                flat=True,
            )
        )

        return ids.index(obj.id) + 1

class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
        )

class MissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mission
        fields = "__all__"

class UserMissionSerializer(serializers.ModelSerializer):
    mission = MissionSerializer(read_only=True)

    class Meta:
        model = UserMission
        fields = (
            "id",
            "mission",
            "progress",
            "status",
            "created_at",
            "updated_at",
        )

class JobPositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobPosition
        fields = "__all__"

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = "__all__"

class JobApplicationSerializer(serializers.ModelSerializer):

    class Meta:
        model = JobApplication
        fields = (
            "id",
            "job_position",
            "status",
            "submitted_at",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "status",
            "submitted_at",
            "updated_at",
        )

    def validate_job_position(self, value):
        user = self.context["request"].user

        if JobApplication.objects.filter(
            user=user,
            job_position=value
        ).exists():
            raise serializers.ValidationError(
                "شما قبلاً برای این موقعیت شغلی درخواست ثبت کرده‌اید."
            )

        return value

class ApplicationAnswerSerializer(serializers.ModelSerializer):

    class Meta:
        model = ApplicationAnswer

        fields = (
            "id",
            "question",
            "answer",
            "application",
        )

        read_only_fields = (
            "id",
            "application",
        )

class RegisterSerializer(serializers.ModelSerializer):

    password = serializers.CharField(
        write_only=True,
        min_length=6,
    )

    class Meta:
        model = User
        fields = (
            "phone_number",
            "password",
        )

    def create(self, validated_data):

        user = User.objects.create_user(
            phone_number=validated_data["phone_number"],
            password=validated_data["password"],
        )

        return user

class VerifyOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(
        max_length=11
    )

    code = serializers.CharField(
        max_length=6,
        min_length=6
    )