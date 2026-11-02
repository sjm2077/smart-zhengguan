import re

from rest_framework import serializers


STUDENT_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,39}$")
SUPPORTED_API_STYLES = {"responses", "chat_completions"}
SUPPORTED_TABS = {"trend", "risk", "governance"}
SUPPORTED_EXPERIMENT_KEYS = {"default", "prompt_v1_compact"}
SUPPORTED_THINKING_TYPES = {"", "enabled", "disabled"}
SUPPORTED_REASONING_EFFORTS = {"", "low", "medium", "high"}
GRADE_OR_MAJOR_PATTERN = re.compile(r"^[\w\u4e00-\u9fff()（）·\-\s]{0,40}$")


def validate_student_id(value):
    text = str(value or "").strip()
    if not text:
        raise serializers.ValidationError("studentId is required")
    if not STUDENT_ID_PATTERN.fullmatch(text):
        raise serializers.ValidationError("studentId format is invalid")
    return text


class PredictionRuntimeOptionsSerializer(serializers.Serializer):
    preferredModel = serializers.CharField(required=False, allow_blank=True, max_length=120)
    apiStyle = serializers.CharField(required=False, allow_blank=True, max_length=32)
    thinkingType = serializers.CharField(required=False, allow_blank=True, max_length=32)
    reasoningEffort = serializers.CharField(required=False, allow_blank=True, max_length=16)
    temperature = serializers.FloatField(required=False)
    useLlmWhenAvailable = serializers.BooleanField(required=False)
    # Agent 开关与预算。DRF 会丢弃未声明的字段，不在这里声明的话
    # useAgent 根本到不了 services 层（排查时会误以为开关失灵）。
    # 真正的权限收敛在 normalize_prediction_runtime_options 里做。
    useAgent = serializers.BooleanField(required=False)
    maxSteps = serializers.IntegerField(required=False, min_value=1, max_value=6)
    timeBudgetSeconds = serializers.IntegerField(required=False, min_value=15, max_value=300)

    def validate_apiStyle(self, value):
        text = str(value or "").strip().lower()
        if text and text not in SUPPORTED_API_STYLES:
            raise serializers.ValidationError("apiStyle is invalid")
        return text

    def validate_thinkingType(self, value):
        text = str(value or "").strip().lower()
        if text not in SUPPORTED_THINKING_TYPES:
            raise serializers.ValidationError("thinkingType is invalid")
        return text

    def validate_reasoningEffort(self, value):
        text = str(value or "").strip().lower()
        if text not in SUPPORTED_REASONING_EFFORTS:
            raise serializers.ValidationError("reasoningEffort is invalid")
        return text

    def validate_temperature(self, value):
        numeric = float(value)
        if numeric < 0 or numeric > 1:
            raise serializers.ValidationError("temperature must be between 0 and 1")
        return numeric


class PredictionContextQuerySerializer(serializers.Serializer):
    student_id = serializers.CharField(max_length=40)

    def validate_student_id(self, value):
        return validate_student_id(value)


class PredictionAnalyzeRequestSerializer(serializers.Serializer):
    studentId = serializers.CharField(max_length=40)
    tab = serializers.CharField(required=False, allow_blank=True, max_length=16, default="trend")
    experimentKey = serializers.CharField(required=False, allow_blank=True, max_length=32, default="default")
    runtimeOptions = PredictionRuntimeOptionsSerializer(required=False, default=dict)

    def validate_studentId(self, value):
        return validate_student_id(value)

    def validate_tab(self, value):
        text = str(value or "").strip().lower() or "trend"
        if text not in SUPPORTED_TABS:
            raise serializers.ValidationError("tab is invalid")
        return text

    def validate_experimentKey(self, value):
        text = str(value or "").strip() or "default"
        if text not in SUPPORTED_EXPERIMENT_KEYS:
            raise serializers.ValidationError("experimentKey is invalid")
        return text


class PredictionChatHistoryItemSerializer(serializers.Serializer):
    role = serializers.CharField(max_length=16)
    text = serializers.CharField(required=False, allow_blank=True, max_length=500)
    content = serializers.CharField(required=False, allow_blank=True, max_length=500)

    def validate_role(self, value):
        text = str(value or "").strip().lower()
        if text not in {"user", "assistant"}:
            raise serializers.ValidationError("role is invalid")
        return text

    def validate(self, attrs):
        text = str(attrs.get("text") or attrs.get("content") or "").strip()
        if not text:
            raise serializers.ValidationError("text is required")
        attrs["text"] = text
        attrs["content"] = text
        return attrs


class PredictionChatRequestSerializer(serializers.Serializer):
    studentId = serializers.CharField(max_length=40)
    question = serializers.CharField(max_length=500)
    chatHistory = PredictionChatHistoryItemSerializer(required=False, many=True, default=list)
    experimentKey = serializers.CharField(required=False, allow_blank=True, max_length=32, default="default")
    runtimeOptions = PredictionRuntimeOptionsSerializer(required=False, default=dict)

    def validate_studentId(self, value):
        return validate_student_id(value)

    def validate_question(self, value):
        text = str(value or "").strip()
        if not text:
            raise serializers.ValidationError("question is required")
        return text

    def validate_experimentKey(self, value):
        text = str(value or "").strip() or "default"
        if text not in SUPPORTED_EXPERIMENT_KEYS:
            raise serializers.ValidationError("experimentKey is invalid")
        return text

    def validate_chatHistory(self, value):
        items = list(value or [])
        if len(items) > 6:
            raise serializers.ValidationError("chatHistory cannot exceed 6 items")
        return items


class GlobalSearchQuerySerializer(serializers.Serializer):
    q = serializers.CharField(required=False, allow_blank=True, max_length=80, default="")

    def validate_q(self, value):
        return str(value or "").strip()


class CrossModuleQuerySerializer(serializers.Serializer):
    grade = serializers.CharField(required=False, allow_blank=True, max_length=40, default="")
    major = serializers.CharField(required=False, allow_blank=True, max_length=40, default="")

    def validate_grade(self, value):
        text = str(value or "").strip()
        if text and not GRADE_OR_MAJOR_PATTERN.fullmatch(text):
            raise serializers.ValidationError("grade format is invalid")
        return text

    def validate_major(self, value):
        text = str(value or "").strip()
        if text and not GRADE_OR_MAJOR_PATTERN.fullmatch(text):
            raise serializers.ValidationError("major format is invalid")
        return text
