from rest_framework import serializers
from .models import JobApplication
from .models import (
    User,
    Mission,
    UserMission,
    JobPosition,
    Question,
    JobApplication,
    Badge,
    UserBadge,
    BadgeRule
)
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer
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

class AssignMissionSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()

    def validate_user_id(self, value):
        try:
            user = User.objects.get(
                id=value,
                is_active=True,
            )
        except User.DoesNotExist:
            raise serializers.ValidationError(
                "کاربر مورد نظر پیدا نشد."
            )

        return user

class JobPositionSerializer(serializers.ModelSerializer):

    class Meta:
        model = JobPosition
        fields = "__all__"

    def validate_tags(self, value):

        if not isinstance(value, list):
            raise serializers.ValidationError(
                "tags باید یک آرایه باشد."
            )

        for tag in value:

            if not isinstance(tag, str):
                raise serializers.ValidationError(
                    "تمام tag ها باید از نوع string باشند."
                )

            if not tag.strip():
                raise serializers.ValidationError(
                    "tag نمی‌تواند خالی باشد."
                )

        return [
            tag.strip()
            for tag in value
        ]

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
            "answers",
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

    def validate_answers(self, value):

        if not isinstance(value, list):
            raise serializers.ValidationError(
                "answers باید یک آرایه باشد."
            )

        question_ids = []

        for item in value:

            if not isinstance(item, dict):
                raise serializers.ValidationError(
                    "هر پاسخ باید یک object باشد."
                )

            if "question_id" not in item:
                raise serializers.ValidationError(
                    "question_id برای هر پاسخ الزامی است."
                )

            if "answer" not in item:
                raise serializers.ValidationError(
                    "answer برای هر سوال الزامی است."
                )

            question_id = item["question_id"]

            if question_id in question_ids:
                raise serializers.ValidationError(
                    "یک سوال نمی‌تواند بیشتر از یک پاسخ داشته باشد."
                )

            question_ids.append(question_id)

        return value

    def validate(self, attrs):

        job_position = attrs.get("job_position")
        answers = attrs.get("answers", [])

        question_ids = [
            item["question_id"]
            for item in answers
        ]

        questions = Question.objects.filter(
            id__in=question_ids,
            job_position=job_position,
            is_active=True,
        )

        valid_question_ids = set(
            questions.values_list(
                "id",
                flat=True
            )
        )

        for question_id in question_ids:

            if question_id not in valid_question_ids:

                raise serializers.ValidationError({
                    "answers": (
                        f"سوال {question_id} مربوط به "
                        "این موقعیت شغلی نیست."
                    )
                })

        question_map = {
            question.id: question
            for question in questions
        }

        normalized_answers = []

        for item in answers:

            question = question_map[item["question_id"]]

            normalized_answers.append({
                "question_id": question.id,
                "question": question.text,
                "answer": item["answer"],
            })

        attrs["answers"] = normalized_answers

        return attrs

class JobApplicationAdminSerializer(serializers.ModelSerializer):

    user = UserSerializer(read_only=True)
    job_position = JobPositionSerializer(read_only=True)

    class Meta:
        model = JobApplication
        fields = (
            "id",
            "user",
            "job_position",
            "status",
            "answers",
            "submitted_at",
            "updated_at",
        )

        read_only_fields = fields

class PhoneAPISerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=11)

class RegisterAPISerializer(serializers.ModelSerializer):
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
        return User.objects.create_user(
            phone_number=validated_data["phone_number"],
            password=validated_data["password"],
        )

class VerifyOTPAPISerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=11)

    code = serializers.CharField(
        max_length=6,
        min_length=6,
    )

class ForgotPasswordAPISerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=11)

class ResetPasswordAPISerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=11)

    password = serializers.CharField(
        write_only=True,
        min_length=6,
    )

class GamiTokenObtainPairSerializer(
    TokenObtainPairSerializer
):

    def validate(self, attrs):

        data = super().validate(attrs)

        if not self.user.is_active:
            raise serializers.ValidationError(
                "حساب کاربری شما غیرفعال شده است. "
                "لطفاً با واحد HR تماس بگیرید."
            )

        return data

class UserAdminSerializer(serializers.ModelSerializer):

    password = serializers.CharField(
        write_only=True,
        required=False,
        min_length=6,
    )

    points = serializers.IntegerField(
        required=False,
        min_value=0,
        default=10,
        help_text="User points. Example: 100",
    )

    level = serializers.IntegerField(
        required=False,
        min_value=0,
        default=0,
        help_text="User level. Example: 1",
    )

    class Meta:
        model = User

        fields = (
            "id",
            "phone_number",
            "password",
            "first_name",
            "last_name",
            "full_name",
            "points",
            "level",
            "role",
            "status",
            "is_phone_verified",
            "is_active",
        )

        read_only_fields = (
            "id",
            "full_name",
            "is_phone_verified",
        )

    def create(self, validated_data):

        password = validated_data.pop(
            "password",
            None
        )

        user = User.objects.create_user(
            password=password,
            **validated_data
        )

        return user

    def update(self, instance, validated_data):

        password = validated_data.pop(
            "password",
            None
        )

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()

        return instance

class BadgeRuleSerializer(serializers.ModelSerializer):

    class Meta:
        model = BadgeRule

        fields = (
            "id",
            "rule_type",
            "value",
            "is_active",
        )

        read_only_fields = (
            "id",
        )

    def validate_value(self, value):

        if value <= 0:
            raise serializers.ValidationError(
                "value باید بزرگ‌تر از صفر باشد."
            )

        return value

class BadgeSerializer(serializers.ModelSerializer):
    rule = BadgeRuleSerializer(
        required=False
    )

    class Meta:
        model = Badge

        fields = (
            "id",
            "name",
            "label",
            "icon",
            "description",
            "is_active",
            "rule",
        )

        read_only_fields = (
            "id",
        )

    def create(self, validated_data):
        rule_data = validated_data.pop(
            "rule",
            None
        )

        badge = Badge.objects.create(
            **validated_data
        )

        if rule_data:
            BadgeRule.objects.create(
                badge=badge,
                **rule_data
            )

        return badge

    def update(self, instance, validated_data):
        rule_data = validated_data.pop(
            "rule",
            None
        )

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        if rule_data is not None:
            rule, created = BadgeRule.objects.get_or_create(
                badge=instance
            )

            for attr, value in rule_data.items():
                setattr(rule, attr, value)

            rule.save()

        return instance

class UserBadgeSerializer(serializers.ModelSerializer):
    badge = BadgeSerializer(
        read_only=True
    )

    class Meta:
        model = UserBadge

        fields = (
            "id",
            "badge",
            "reason",
            "assigned_at",
        )

        read_only_fields = (
            "id",
            "badge",
            "reason",
            "assigned_at",
        )

class AssignBadgeSerializer(serializers.Serializer):
    reason = serializers.CharField(
        required=False,
        allow_blank=True,
        default="Assigned manually by admin",
    )