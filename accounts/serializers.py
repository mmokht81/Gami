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
    BadgeRule,
    APPLICATION_STATUS,
    Team,
    Onboarding,
    OnboardingChecklistItem,
    OnboardingChecklistProgress,
)
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer
)


class UserSerializer(serializers.ModelSerializer):

    # team = serializers.PrimaryKeyRelatedField(
    #     read_only=True
    # )
    
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

        fields = (
            "id",
            "job_position",
            "type",
            "text",
            "order",
            "is_active",
        )

        read_only_fields = (
            "id",
        )

    def validate_order(self, value):

        if value < 1:
            raise serializers.ValidationError(
                "order باید بزرگ‌تر از صفر باشد."
            )

        return value

    def validate_text(self, value):

        if not value.strip():
            raise serializers.ValidationError(
                "متن سوال نمی‌تواند خالی باشد."
            )

        return value.strip()

class ApplicationAnswerInputSerializer(serializers.Serializer):
    """
    Validates a single answer submitted for a job application.

    question_id accepts both:
        4
        "4"

    and normalizes both values to:
        4
    """

    question_id = serializers.IntegerField(
        min_value=1
    )

    answer = serializers.CharField(
        allow_blank=False,
        trim_whitespace=True,
    )

class JobApplicationSerializer(serializers.ModelSerializer):

    answers = ApplicationAnswerInputSerializer(
        many=True,
        allow_empty=True,
    )

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

        request = self.context.get("request")

        if request is not None:

            user = getattr(
                request,
                "user",
                None,
            )

            if user is not None and user.is_authenticated:

                if JobApplication.objects.filter(
                    user=user,
                    job_position=value,
                ).exists():

                    raise serializers.ValidationError(
                        "شما قبلاً برای این موقعیت شغلی "
                        "درخواست ثبت کرده‌اید."
                    )

        if not value.is_active:

            raise serializers.ValidationError(
                "این موقعیت شغلی فعال نیست."
            )

        return value

    def validate_answers(self, value):

        question_ids = [
            item["question_id"]
            for item in value
        ]

        # --------------------------------------------------
        # 1. Prevent duplicate answers
        # --------------------------------------------------

        if len(question_ids) != len(set(question_ids)):

            raise serializers.ValidationError(
                "یک سوال نمی‌تواند بیشتر از یک پاسخ داشته باشد."
            )

        return value

    def validate(self, attrs):

        job_position = attrs.get("job_position")
        answers = attrs.get("answers", [])

        if not job_position:

            raise serializers.ValidationError({
                "job_position": (
                    "موقعیت شغلی الزامی است."
                )
            })

        question_ids = [
            item["question_id"]
            for item in answers
        ]

        # --------------------------------------------------
        # 2. Get all active questions belonging to this job
        # --------------------------------------------------

        job_questions = Question.objects.filter(
            job_position=job_position,
            is_active=True,
        ).order_by("order")

        valid_question_ids = set(
            job_questions.values_list(
                "id",
                flat=True,
            )
        )

        submitted_question_ids = set(
            question_ids
        )

        # --------------------------------------------------
        # 3. Reject questions that don't belong to job
        # --------------------------------------------------

        invalid_question_ids = (
            submitted_question_ids
            - valid_question_ids
        )

        if invalid_question_ids:

            invalid_question_id = sorted(
                invalid_question_ids
            )[0]

            raise serializers.ValidationError({
                "answers": (
                    f"سوال {invalid_question_id} مربوط به "
                    "این موقعیت شغلی نیست."
                )
            })

        # --------------------------------------------------
        # 4. Make sure all active questions are answered
        # --------------------------------------------------

        missing_question_ids = (
            valid_question_ids
            - submitted_question_ids
        )

        if missing_question_ids:

            missing_question_id = sorted(
                missing_question_ids
            )[0]

            raise serializers.ValidationError({
                "answers": (
                    f"پاسخ سوال {missing_question_id} "
                    "الزامی است."
                )
            })

        # --------------------------------------------------
        # 5. Normalize and snapshot question information
        # --------------------------------------------------

        question_map = {
            question.id: question
            for question in job_questions
        }

        normalized_answers = []

        for item in answers:

            question = question_map[
                item["question_id"]
            ]

            normalized_answers.append({
                "question_id": question.id,
                "question": question.text,
                "answer": item["answer"].strip(),
            })

        attrs["answers"] = normalized_answers

        return attrs

class JobApplicationAdminSerializer(serializers.ModelSerializer):

    user = UserSerializer(read_only=True)

    job_position = JobPositionSerializer(
        read_only=True
    )

    status_display = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )

    class Meta:
        model = JobApplication

        fields = (
            "id",
            "user",
            "job_position",
            "status",
            "status_display",
            "answers",
            "submitted_at",
            "updated_at",
        )

        read_only_fields = fields

class JobApplicationStatusSerializer(serializers.ModelSerializer):

    class Meta:
        model = JobApplication

        fields = (
            "status",
        )

    def validate_status(self, value):

        valid_statuses = {
            choice[0]
            for choice in APPLICATION_STATUS
        }

        if value not in valid_statuses:
            raise serializers.ValidationError(
                "وضعیت انتخاب‌شده معتبر نیست."
            )

        return value


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


class TeamSerializer(serializers.ModelSerializer):

    members = serializers.SerializerMethodField()

    class Meta:
        model = Team

        fields = (
            "id",
            "name",
            "description",
            "members",
            "is_active",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "members",
            "created_at",
            "updated_at",
        )

    def get_members(self, obj):
        onboardings = (
            obj.onboardings
            .select_related("user")
            .filter(
                user__is_active=True,
            )
        )

        return UserSerializer(
            [
                onboarding.user
                for onboarding in onboardings
            ],
            many=True,
        ).data


class OnboardingChecklistItemSerializer(
    serializers.ModelSerializer
):

    class Meta:
        model = OnboardingChecklistItem

        fields = (
            "id",
            "icon",
            "points",
            "title",
            "type",
            "description",
            "order",
            "is_active",
        )

        read_only_fields = (
            "id",
        )

class OnboardingChecklistProgressSerializer(
    serializers.ModelSerializer
):

    checklist_item = OnboardingChecklistItemSerializer(
        read_only=True
    )

    class Meta:
        model = OnboardingChecklistProgress

        fields = (
            "id",
            "checklist_item",
            "is_completed",
            "completed_at",
        )

        read_only_fields = (
            "id",
            "completed_at",
        )

class OnboardingTeamSerializer(
    serializers.ModelSerializer
):

    members = serializers.SerializerMethodField()

    class Meta:
        model = Team

        fields = (
            "id",
            "name",
            "description",
            "members",
        )

    def get_members(self, obj):

        onboardings = (
            obj.onboardings
            .select_related("user")
            .filter(
                user__is_active=True,
            )
        )

        return UserSerializer(
            [
                onboarding.user
                for onboarding in onboardings
            ],
            many=True,
        ).data

class OnboardingSerializer(
    serializers.ModelSerializer
):

    job_position = JobPositionSerializer(
        read_only=True
    )

    team = OnboardingTeamSerializer(
        read_only=True
    )

    checklist = serializers.SerializerMethodField()

    badges = serializers.SerializerMethodField()

    class Meta:
        model = Onboarding

        fields = (
            "id",
            "user",
            "job_position",
            "team",
            "checklist_progress",
            "hr_progress",
            "progress",
            "checklist",
            "badges",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "user",
            "job_position",
            "team",
            "checklist_progress",
            "progress",
            "checklist",
            "badges",
            "created_at",
            "updated_at",
        )

    def get_checklist(self, obj):

        return OnboardingChecklistProgressSerializer(
            obj.checklist_progress_items.all(),
            many=True,
        ).data

    def get_badges(self, obj):

        user_badges = (
            obj.user.badges
            .select_related("badge")
            .order_by("-assigned_at")
        )

        return UserBadgeSerializer(
            user_badges,
            many=True,
        ).data

class OnboardingChecklistItemManagementSerializer(
    serializers.ModelSerializer
):

    class Meta:
        model = OnboardingChecklistItem

        fields = (
            "id",
            "job_position",
            "icon",
            "points",
            "title",
            "type",
            "description",
            "order",
            "is_active",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
        )

    def validate_title(self, value):

        value = value.strip()

        if not value:

            raise serializers.ValidationError(
                "عنوان نمی‌تواند خالی باشد."
            )

        return value

    def validate_order(self, value):

        if value < 1:

            raise serializers.ValidationError(
                "order باید بزرگ‌تر از صفر باشد."
            )

        return value

class OnboardingChecklistCompleteSerializer(
    serializers.Serializer
):

    checklist_item_id = serializers.IntegerField(
        min_value=1
    )

class OnboardingHRProgressSerializer(
    serializers.Serializer
):

    hr_progress = serializers.IntegerField(
        min_value=0,
        max_value=100,
    )

class OnboardingTeamAssignSerializer(
    serializers.Serializer
):

    team_id = serializers.IntegerField(
        min_value=1
    )





