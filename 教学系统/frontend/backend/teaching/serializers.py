from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import (
    College, Semester, Teacher, Student, Course, TeachingClass, Exam, Grade,
    Notice, UserProfile,
)

User = get_user_model()


class CollegeSerializer(serializers.ModelSerializer):
    class Meta:
        model = College
        fields = ["id", "name", "code", "description", "is_active"]


class SemesterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Semester
        fields = [
            "id", "name", "academic_year", "term",
            "start_date", "end_date", "is_current",
        ]


class UserInfoSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "role", "avatar"]

    def get_role(self, obj):
        if obj.is_superuser or obj.is_staff:
            return "admin"
        try:
            return obj.teaching_profile.role
        except UserProfile.DoesNotExist:
            return "unassigned"

    def get_avatar(self, obj):
        try:
            return obj.teaching_profile.avatar or None
        except UserProfile.DoesNotExist:
            return None


class TeacherSerializer(serializers.ModelSerializer):
    college_name = serializers.CharField(source="college.name", read_only=True)

    class Meta:
        model = Teacher
        fields = [
            "id", "teacher_no", "name", "gender", "college", "college_name",
            "title", "phone", "email", "description", "is_active",
        ]


class StudentSerializer(serializers.ModelSerializer):
    college_name = serializers.CharField(source="college.name", read_only=True)

    class Meta:
        model = Student
        fields = [
            "id", "student_no", "name", "gender", "college", "college_name",
            "major", "grade", "class_name", "email", "phone", "enrollment_year",
            "is_active",
        ]


class CourseSerializer(serializers.ModelSerializer):
    college_name = serializers.CharField(source="college.name", read_only=True)
    semester_name = serializers.CharField(
        source="semester.name", read_only=True, allow_null=True
    )

    class Meta:
        model = Course
        fields = [
            "id", "code", "name", "credit", "hours", "college", "college_name",
            "semester", "semester_name", "course_type", "description", "is_active",
        ]


class TeachingClassSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source="course.name", read_only=True)
    teacher_name = serializers.CharField(source="teacher.name", read_only=True)
    semester_name = serializers.CharField(source="semester.name", read_only=True)

    class Meta:
        model = TeachingClass
        fields = [
            "id", "course", "course_name", "semester", "semester_name",
            "teacher", "teacher_name", "class_name", "capacity",
            "enrolled_count", "schedule", "classroom", "status",
        ]


class ExamSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source="course.name", read_only=True)
    course_code = serializers.CharField(source="course.code", read_only=True)
    semester_name = serializers.CharField(source="semester.name", read_only=True)

    class Meta:
        model = Exam
        fields = [
            "id", "name", "course", "course_name", "course_code", "semester",
            "semester_name", "exam_type", "exam_date", "duration", "total_score",
            "location", "status",
        ]


class GradeSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.name", read_only=True)
    student_id = serializers.CharField(
        source="student.student_no", read_only=True
    )
    course_name = serializers.CharField(source="course.name", read_only=True)
    semester_name = serializers.CharField(
        source="semester.name", read_only=True, allow_null=True
    )
    exam_name = serializers.CharField(
        source="exam.name", read_only=True, allow_null=True
    )

    class Meta:
        model = Grade
        fields = [
            "id", "student", "student_name", "student_id", "course", "course_name",
            "semester", "semester_name", "exam", "exam_name", "score",
            "grade_point", "exam_type", "exam_date", "remark", "is_published",
        ]


class NoticeSerializer(serializers.ModelSerializer):
    publisher_name = serializers.CharField(
        source="publisher.username", read_only=True, allow_null=True
    )

    class Meta:
        model = Notice
        fields = [
            "id", "title", "content", "notice_type", "publisher",
            "publisher_name", "is_published", "created_at", "updated_at",
        ]
        read_only_fields = ["publisher", "created_at", "updated_at"]
