from datetime import timedelta

from django.db.models import Avg, Count, F, Q, Sum
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    College, Semester, Teacher, Student, Course, TeachingClass, Exam, Grade, Notice,
    GraduateEmploymentStat, TeachingActivityLog,
)
from .permissions import (
    FULL_READ_ROLES,
    TeachingRolePermission,
    get_linked_student_id,
    get_linked_teacher_id,
    get_teaching_role,
    scope_grade_queryset,
)
from .serializers import (
    CollegeSerializer, SemesterSerializer, TeacherSerializer, StudentSerializer,
    CourseSerializer, TeachingClassSerializer, ExamSerializer, GradeSerializer,
    NoticeSerializer, UserInfoSerializer,
)


class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        username = request.data.get("username", "").strip()
        password = request.data.get("password", "")
        if not username or not password:
            return Response(
                {"detail": "请输入账号和密码"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        from django.contrib.auth import authenticate
        user = authenticate(request, username=username, password=password)
        if user is None or not user.is_active:
            return Response(
                {"detail": "账号或密码错误"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        refresh = RefreshToken.for_user(user)
        return Response({
            "token": str(refresh.access_token),
            "refresh": str(refresh),
            "user": UserInfoSerializer(user).data,
        })


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserInfoSerializer(request.user).data)


class BaseTeachingViewSet(viewsets.ModelViewSet):
    permission_classes = [TeachingRolePermission]

    ACTIVITY_MODULES = {
        "teacher": "教师管理",
        "student": "学生管理",
        "course": "课程管理",
        "teachingclass": "教学班管理",
        "exam": "考务管理",
        "grade": "成绩管理",
        "notice": "通知公告",
    }

    def record_activity(self, action, instance):
        model_name = instance._meta.model_name
        module = self.ACTIVITY_MODULES.get(model_name, instance._meta.verbose_name)

        if isinstance(instance, Grade):
            label = f"{instance.course.name}（{instance.exam_type}）"
        else:
            label = (
                getattr(instance, "name", "")
                or getattr(instance, "title", "")
                or getattr(instance, "class_name", "")
                or getattr(instance, "code", "")
                or str(instance.pk)
            )

        action_label = dict(TeachingActivityLog.ACTION_CHOICES).get(action, action)
        TeachingActivityLog.objects.create(
            actor=self.request.user if self.request.user.is_authenticated else None,
            action=action,
            module=module,
            object_label=str(label)[:200],
            message=f"{action_label}{module}：{label}"[:255],
        )

    def perform_create(self, serializer):
        instance = serializer.save()
        self.record_activity("create", instance)

    def perform_update(self, serializer):
        instance = serializer.save()
        self.record_activity("update", instance)

    def perform_destroy(self, instance):
        self.record_activity("delete", instance)
        instance.delete()


class CollegeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = College.objects.filter(is_active=True)
    serializer_class = CollegeSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ["name", "code"]


class SemesterViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Semester.objects.all()
    serializer_class = SemesterSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ["name"]


class TeacherViewSet(BaseTeachingViewSet):
    queryset = Teacher.objects.select_related("college").all()
    serializer_class = TeacherSerializer
    search_fields = ["teacher_no", "name", "email", "college__name"]
    ordering_fields = ["teacher_no", "name", "title"]
    ordering = ["teacher_no"]

    def get_queryset(self):
        qs = super().get_queryset()
        role = get_teaching_role(self.request.user)

        if role == "teacher":
            teacher_id = get_linked_teacher_id(self.request.user)
            qs = qs.filter(pk=teacher_id) if teacher_id else qs.none()
        elif role not in FULL_READ_ROLES and role != "student":
            qs = qs.none()

        # Preserve the existing teacher-directory filters for authorized readers.
        college_id = self.request.query_params.get("college_id")
        if college_id:
            qs = qs.filter(college_id=college_id)

        active = self.request.query_params.get("is_active")
        if active in ("true", "false"):
            qs = qs.filter(is_active=(active == "true"))

        return qs


class StudentViewSet(BaseTeachingViewSet):
    queryset = Student.objects.select_related("college").all()
    serializer_class = StudentSerializer
    search_fields = ["student_no", "name", "major", "class_name", "college__name"]
    ordering_fields = ["student_no", "name", "grade", "enrollment_year"]
    ordering = ["student_no"]

    def get_queryset(self):
        qs = super().get_queryset()
        role = get_teaching_role(self.request.user)
        if role == "student":
            student_id = get_linked_student_id(self.request.user)
            qs = qs.filter(pk=student_id) if student_id else qs.none()
        elif role == "teacher":
            teacher_id = get_linked_teacher_id(self.request.user)
            if not teacher_id:
                qs = qs.none()
            else:
                qs = qs.filter(
                    grades__course__teaching_classes__teacher_id=teacher_id
                ).distinct()
        elif role not in FULL_READ_ROLES:
            qs = qs.none()

        college_id = self.request.query_params.get("college_id")
        grade = self.request.query_params.get("grade")
        if college_id:
            qs = qs.filter(college_id=college_id)
        if grade:
            qs = qs.filter(grade=grade)
        active = self.request.query_params.get("is_active")
        if active in ("true", "false"):
            qs = qs.filter(is_active=(active == "true"))
        return qs


class CourseViewSet(BaseTeachingViewSet):
    queryset = Course.objects.select_related("college", "semester").all()
    serializer_class = CourseSerializer
    search_fields = ["code", "name", "college__name", "description"]
    ordering_fields = ["code", "name", "credit", "hours"]
    ordering = ["code"]

    def get_queryset(self):
        qs = super().get_queryset()
        role = get_teaching_role(self.request.user)
        if role == "teacher":
            teacher_id = get_linked_teacher_id(self.request.user)
            qs = qs.filter(
                teaching_classes__teacher_id=teacher_id
            ).distinct() if teacher_id else qs.none()
        elif role not in FULL_READ_ROLES and role not in {"student"}:
            qs = qs.none()

        college_id = self.request.query_params.get("college_id")
        course_type = self.request.query_params.get("type")
        semester_id = self.request.query_params.get("semester_id")
        if college_id:
            qs = qs.filter(college_id=college_id)
        if course_type:
            qs = qs.filter(course_type=course_type)
        if semester_id:
            qs = qs.filter(semester_id=semester_id)
        active = self.request.query_params.get("is_active")
        if active in ("true", "false"):
            qs = qs.filter(is_active=(active == "true"))
        return qs


class TeachingClassViewSet(BaseTeachingViewSet):
    queryset = TeachingClass.objects.select_related(
        "course", "semester", "teacher"
    ).all()
    serializer_class = TeachingClassSerializer
    search_fields = ["class_name", "course__name", "teacher__name", "classroom"]
    ordering_fields = ["class_name", "capacity", "enrolled_count"]
    ordering = ["semester", "course__code"]

    def get_queryset(self):
        qs = super().get_queryset()
        role = get_teaching_role(self.request.user)
        if role == "teacher":
            teacher_id = get_linked_teacher_id(self.request.user)
            return qs.filter(teacher_id=teacher_id) if teacher_id else qs.none()
        if role == "student":
            student_id = get_linked_student_id(self.request.user)
            return qs.filter(
                course__grades__student_id=student_id,
                course__grades__is_published=True,
            ).distinct() if student_id else qs.none()
        if role not in FULL_READ_ROLES:
            return qs.none()
        return qs


class ExamViewSet(BaseTeachingViewSet):
    queryset = Exam.objects.select_related("course", "semester").all()
    serializer_class = ExamSerializer
    search_fields = ["name", "course__name", "course__code", "location"]
    ordering_fields = ["exam_date", "name", "status"]
    ordering = ["exam_date"]

    def get_queryset(self):
        qs = super().get_queryset()
        role = get_teaching_role(self.request.user)
        if role == "teacher":
            teacher_id = get_linked_teacher_id(self.request.user)
            qs = qs.filter(
                course__teaching_classes__teacher_id=teacher_id
            ).distinct() if teacher_id else qs.none()
        elif role == "student":
            student_id = get_linked_student_id(self.request.user)
            qs = qs.filter(
                course__grades__student_id=student_id,
                course__grades__is_published=True,
            ).distinct() if student_id else qs.none()
        elif role not in FULL_READ_ROLES:
            qs = qs.none()

        course_id = self.request.query_params.get("course_id")
        semester_id = self.request.query_params.get("semester_id")
        if course_id:
            qs = qs.filter(course_id=course_id)
        if semester_id:
            qs = qs.filter(semester_id=semester_id)
        return qs


class GradeViewSet(BaseTeachingViewSet):
    queryset = Grade.objects.select_related(
        "student", "course", "semester", "exam"
    ).all()
    serializer_class = GradeSerializer
    search_fields = [
        "student__student_no", "student__name", "course__name", "course__code"
    ]
    ordering_fields = ["score", "grade_point", "student__student_no"]
    ordering = ["student__student_no", "course__code"]

    def get_queryset(self):
        qs = scope_grade_queryset(super().get_queryset(), self.request.user)
        student_id = self.request.query_params.get("student_id")
        course_id = self.request.query_params.get("course_id")
        semester_id = self.request.query_params.get("semester_id")
        if student_id:
            if str(student_id).isdigit():
                qs = qs.filter(student_id=student_id)
            else:
                qs = qs.filter(student__student_no=student_id)
        if course_id:
            qs = qs.filter(course_id=course_id)
        if semester_id:
            qs = qs.filter(semester_id=semester_id)
        published = self.request.query_params.get("is_published")
        # Students cannot bypass publication restrictions via ?is_published=false.
        if get_teaching_role(self.request.user) != "student":
            if published in ("true", "false"):
                qs = qs.filter(is_published=(published == "true"))
        return qs

    @action(detail=False, methods=["get"], url_path="statistics")
    def statistics(self, request):
        qs = self.filter_queryset(self.get_queryset())
        semester_id = request.query_params.get("semester_id")
        college_id = request.query_params.get("college_id")
        if semester_id:
            qs = qs.filter(semester_id=semester_id)
        if college_id:
            qs = qs.filter(student__college_id=college_id)
        aggregate = qs.aggregate(avg_score=Avg("score"), total=Count("id"))
        total = aggregate["total"] or 0
        passed = qs.filter(score__gte=60).count()
        excellent = qs.filter(score__gte=90).count()
        distribution = {
            "0-59": qs.filter(score__lt=60).count(),
            "60-69": qs.filter(score__gte=60, score__lt=70).count(),
            "70-79": qs.filter(score__gte=70, score__lt=80).count(),
            "80-89": qs.filter(score__gte=80, score__lt=90).count(),
            "90-100": excellent,
        }
        return Response({
            "pass_rate": round(passed / total * 100, 2) if total else 0,
            "excellent_rate": round(excellent / total * 100, 2) if total else 0,
            "avg_score": round(float(aggregate["avg_score"] or 0), 2),
            "score_distribution": distribution,
        })


class NoticeViewSet(BaseTeachingViewSet):
    queryset = Notice.objects.select_related("publisher").all()
    serializer_class = NoticeSerializer
    search_fields = ["title", "content"]
    ordering_fields = ["created_at", "updated_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        qs = super().get_queryset()
        role = get_teaching_role(self.request.user)
        if role not in {"admin", "academic"}:
            qs = qs.filter(is_published=True)
        notice_type = self.request.query_params.get("notice_type")
        if notice_type:
            qs = qs.filter(notice_type=notice_type)
        return qs

    def perform_create(self, serializer):
        instance = serializer.save(publisher=self.request.user)
        self.record_activity("create", instance)



class DashboardSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        role = get_teaching_role(request.user)

        students = Student.objects.filter(is_active=True)
        teachers = Teacher.objects.filter(is_active=True)
        courses = Course.objects.filter(is_active=True)
        grades = Grade.objects.all()
        teaching_classes = TeachingClass.objects.all()

        # 学生只能统计自己的公开成绩、相关课程和教学班。
        if role == "student":
            student_id = get_linked_student_id(request.user)

            if student_id:
                students = students.filter(pk=student_id)
                grades = grades.filter(
                    student_id=student_id,
                    is_published=True,
                )

                course_ids = grades.values("course_id").distinct()

                courses = courses.filter(pk__in=course_ids)
                teaching_classes = teaching_classes.filter(
                    course_id__in=course_ids,
                )
                teachers = teachers.filter(
                    teaching_classes__course_id__in=course_ids,
                ).distinct()
            else:
                students = students.none()
                teachers = teachers.none()
                courses = courses.none()
                grades = grades.none()
                teaching_classes = teaching_classes.none()

        # 教师只能统计自己负责的教学班及其关联数据。
        elif role == "teacher":
            teacher_id = get_linked_teacher_id(request.user)

            if teacher_id:
                teaching_classes = teaching_classes.filter(
                    teacher_id=teacher_id,
                )
                course_ids = teaching_classes.values("course_id")

                teachers = teachers.filter(pk=teacher_id)
                courses = courses.filter(pk__in=course_ids)
                grades = grades.filter(course_id__in=course_ids)
                students = students.filter(
                    grades__course_id__in=course_ids,
                ).distinct()
            else:
                students = students.none()
                teachers = teachers.none()
                courses = courses.none()
                grades = grades.none()
                teaching_classes = teaching_classes.none()

        # 其他没有完整读取权限的角色不返回全校统计数据。
        elif role not in FULL_READ_ROLES:
            students = students.none()
            teachers = teachers.none()
            courses = courses.none()
            grades = grades.none()
            teaching_classes = teaching_classes.none()

        # 学院筛选。
        college_id = request.query_params.get("college_id")

        if college_id:
            students = students.filter(college_id=college_id)
            teachers = teachers.filter(college_id=college_id)
            courses = courses.filter(college_id=college_id)
            grades = grades.filter(
                student__college_id=college_id,
            )
            teaching_classes = teaching_classes.filter(
                course__college_id=college_id,
            )

        # 教学班默认统计当前学期；指定学期时按指定学期统计。
        semester_id = request.query_params.get("semester_id")

        if semester_id:
            grades = grades.filter(semester_id=semester_id)
            teaching_classes = teaching_classes.filter(
                semester_id=semester_id,
            )
        else:
            current_semester_id = (
                Semester.objects.filter(is_current=True)
                .values_list("id", flat=True)
                .first()
            )

            if current_semester_id:
                teaching_classes = teaching_classes.filter(
                    semester_id=current_semester_id,
                )

        # 成绩统计继续使用经过角色权限过滤后的成绩集合。
        total_grades = grades.count()
        passed = grades.filter(score__gte=60).count()
        average = grades.aggregate(value=Avg("score"))["value"] or 0

        return Response({
            "total_students": students.distinct().count(),
            "total_teachers": teachers.distinct().count(),
            "total_courses": courses.distinct().count(),
            "current_teaching_classes": (
                teaching_classes.distinct().count()
            ),
            "avg_score": round(float(average), 2),
            "exam_pass_rate": (
                round(passed / total_grades * 100, 2)
                if total_grades else 0
            ),
        })


def analytics_grade_queryset(request):
    qs = Grade.objects.all()
    return scope_grade_queryset(qs, request.user)


class ScoreDistributionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = analytics_grade_queryset(request)
        for key, field in [
            ("semester_id", "semester_id"),
            ("course_id", "course_id"),
            ("college_id", "student__college_id"),
        ]:
            if request.query_params.get(key):
                qs = qs.filter(**{field: request.query_params[key]})
        ranges = [
            ("0-59", Q(score__lt=60)),
            ("60-69", Q(score__gte=60, score__lt=70)),
            ("70-79", Q(score__gte=70, score__lt=80)),
            ("80-89", Q(score__gte=80, score__lt=90)),
            ("90-100", Q(score__gte=90, score__lte=100)),
        ]
        return Response({
            "distribution": [
                {"score_range": label, "count": qs.filter(condition).count()}
                for label, condition in ranges
            ]
        })


class CourseScoresView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = analytics_grade_queryset(request)
        for key, field in [
            ("semester_id", "semester_id"),
            ("college_id", "student__college_id"),
        ]:
            if request.query_params.get(key):
                qs = qs.filter(**{field: request.query_params[key]})
        rows = qs.values("course_id", "course__name").annotate(
            avg_score=Avg("score"), total=Count("id"),
        ).order_by("course__name")
        result = []
        for row in rows:
            subset = qs.filter(course_id=row["course_id"])
            total = row["total"] or 0
            result.append({
                "course_id": row["course_id"],
                "course_name": row["course__name"],
                "avg_score": round(float(row["avg_score"] or 0), 2),
                "pass_rate": round(
                    subset.filter(score__gte=60).count() / total * 100, 2
                ) if total else 0,
                "excellent_rate": round(
                    subset.filter(score__gte=90).count() / total * 100, 2
                ) if total else 0,
            })
        return Response({"course_stats": result})


class SemesterTrendView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = analytics_grade_queryset(request).select_related("semester").filter(
            semester__isnull=False
        )
        for key, field in [
            ("college_id", "student__college_id"),
            ("course_id", "course_id"),
        ]:
            if request.query_params.get(key):
                qs = qs.filter(**{field: request.query_params[key]})
        rows = qs.values("semester_id", "semester__name").annotate(
            avg_score=Avg("score"), total=Count("id"),
        ).order_by("semester_id")
        return Response([{
            "semester_id": row["semester_id"],
            "semester_name": row["semester__name"],
            "avg_score": round(float(row["avg_score"] or 0), 2),
            "pass_rate": round(
                qs.filter(
                    semester_id=row["semester_id"], score__gte=60
                ).count() / row["total"] * 100, 2
            ) if row["total"] else 0,
        } for row in rows])

class GradeTypeComparisonView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # 使用现有权限过滤，避免跨角色泄露成绩数据
        qs = analytics_grade_queryset(request).filter(
            semester__isnull=False
        )

        # 支持指定学期；未指定时，使用当前账号可查看的
        # 最新学期成绩，不虚构历史学期数据
        semester_id = request.query_params.get("semester_id")

        if semester_id:
            qs = qs.filter(semester_id=semester_id)
        else:
            latest_semester_id = (
                qs.order_by("-semester_id")
                .values_list("semester_id", flat=True)
                .first()
            )

            if latest_semester_id is None:
                return Response({
                    "semester_id": None,
                    "semester_name": "",
                    "grade_type_stats": [],
                })

            qs = qs.filter(semester_id=latest_semester_id)

        semester_info = qs.values(
            "semester_id",
            "semester__name",
        ).first()

        rows = (
            qs.values("exam_type")
            .annotate(
                total=Count("id"),
                avg_score=Avg("score"),
                pass_count=Count(
                    "id",
                    filter=Q(score__gte=60),
                ),
                excellent_count=Count(
                    "id",
                    filter=Q(score__gte=90),
                ),
            )
            .order_by("exam_type")
        )

        grade_type_stats = []

        for row in rows:
            total = row["total"]

            grade_type_stats.append({
                "exam_type": row["exam_type"],
                "count": total,
                "avg_score": round(
                    float(row["avg_score"] or 0), 2
                ),
                "pass_rate": round(
                    row["pass_count"] / total * 100, 2
                ) if total else 0,
                "excellent_rate": round(
                    row["excellent_count"] / total * 100, 2
                ) if total else 0,
            })

        return Response({
            "semester_id": (
                semester_info["semester_id"]
                if semester_info else None
            ),
            "semester_name": (
                semester_info["semester__name"]
                if semester_info else ""
            ),
            "grade_type_stats": grade_type_stats,
        })

class StudentRankingView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        role = get_teaching_role(request.user)
        if role == "student":
            raise PermissionDenied("学生账号无权查看全校学生排名。")
        if role not in FULL_READ_ROLES and role != "teacher":
            raise PermissionDenied("当前账号无权查看学生排名。")

        qs = Grade.objects.all()
        if role == "teacher":
            teacher_id = get_linked_teacher_id(request.user)
            if not teacher_id:
                qs = qs.none()
            else:
                qs = qs.filter(
                    course__teaching_classes__teacher_id=teacher_id
                ).distinct()

        semester_id = request.query_params.get("semester_id")
        college_id = request.query_params.get("college_id")
        if semester_id:
            qs = qs.filter(semester_id=semester_id)
        if college_id:
            qs = qs.filter(student__college_id=college_id)
        try:
            limit = min(max(int(request.query_params.get("limit", 10)), 1), 100)
        except (TypeError, ValueError):
            limit = 10

        rows = qs.values("student_id", "student__name").annotate(
            avg_score=Avg("score")
        ).order_by("-avg_score", "student_id")[:limit]
        return Response([{
            "student_id": row["student_id"],
            "student_name": row["student__name"],
            "avg_score": round(float(row["avg_score"] or 0), 2),
            "rank": index + 1,
        } for index, row in enumerate(rows)])

class GraduateEmploymentDashboardView(APIView):
    """毕业生就业汇总：GET 查询图表，POST 由教务管理员录入官方统计数。"""

    permission_classes = [IsAuthenticated]

    def scoped_queryset(self, request):
        qs = GraduateEmploymentStat.objects.select_related("college").all()
        role = get_teaching_role(request.user)

        if role in FULL_READ_ROLES:
            return qs
        if role == "teacher":
            teacher_id = get_linked_teacher_id(request.user)
            teacher = Teacher.objects.filter(pk=teacher_id).first() if teacher_id else None
            return qs.filter(college_id=teacher.college_id) if teacher else qs.none()
        if role == "student":
            student_id = get_linked_student_id(request.user)
            student = Student.objects.filter(pk=student_id).first() if student_id else None
            return qs.filter(college_id=student.college_id) if student else qs.none()
        return qs.none()

    def get(self, request):
        qs = self.scoped_queryset(request)
        college_id = request.query_params.get("college_id")
        if college_id:
            qs = qs.filter(college_id=college_id)

        year_param = request.query_params.get("year")
        if year_param:
            try:
                year = int(year_param)
            except (TypeError, ValueError):
                return Response({"detail": "year 必须为整数"}, status=status.HTTP_400_BAD_REQUEST)
            qs = qs.filter(graduation_year=year)
        else:
            year = qs.order_by("-graduation_year").values_list(
                "graduation_year", flat=True
            ).first()
            if year is None:
                return Response({"year": None, "total": 0, "data": []})
            qs = qs.filter(graduation_year=year)

        label_map = dict(GraduateEmploymentStat.DESTINATION_CHOICES)
        rows = qs.values("destination_type").annotate(
            value=Sum("graduate_count")
        ).order_by("destination_type")
        data = [
            {
                "name": label_map.get(row["destination_type"], row["destination_type"]),
                "value": int(row["value"] or 0),
            }
            for row in rows
            if int(row["value"] or 0) > 0
        ]
        return Response({
            "year": year,
            "total": sum(item["value"] for item in data),
            "data": data,
        })

    def post(self, request):
        role = get_teaching_role(request.user)
        if role not in {"admin", "academic"}:
            raise PermissionDenied("只有系统管理员或教务管理人员可以维护就业统计数据。")

        try:
            year = int(request.data.get("year"))
            college_id = int(request.data.get("college_id"))
            count = int(request.data.get("count"))
        except (TypeError, ValueError):
            return Response(
                {"detail": "year、college_id 和 count 均须为整数"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        destination_type = str(request.data.get("destination_type", "")).strip()
        allowed_types = {value for value, _ in GraduateEmploymentStat.DESTINATION_CHOICES}
        if year < 2000 or year > 2100:
            return Response({"detail": "毕业年份不在有效范围内"}, status=status.HTTP_400_BAD_REQUEST)
        if count < 0:
            return Response({"detail": "人数不能小于 0"}, status=status.HTTP_400_BAD_REQUEST)
        if destination_type not in allowed_types:
            return Response({"detail": "就业去向类别无效"}, status=status.HTTP_400_BAD_REQUEST)
        if not College.objects.filter(pk=college_id).exists():
            return Response({"detail": "学院不存在"}, status=status.HTTP_400_BAD_REQUEST)

        record, created = GraduateEmploymentStat.objects.update_or_create(
            college_id=college_id,
            graduation_year=year,
            destination_type=destination_type,
            defaults={"graduate_count": count},
        )
        category_label = record.get_destination_type_display()
        TeachingActivityLog.objects.create(
            actor=request.user,
            action="create" if created else "update",
            module="毕业生就业",
            object_label=f"{year}届-{category_label}"[:200],
            message=f"{'新增' if created else '更新'}{year}届毕业生就业去向：{category_label} {count}人"[:255],
        )
        return Response({
            "id": record.id,
            "year": record.graduation_year,
            "college_id": record.college_id,
            "destination_type": record.destination_type,
            "destination_label": category_label,
            "count": record.graduate_count,
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class DashboardAlertsView(APIView):
    """根据考试安排、教学班容量和已发布成绩动态计算预警。"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        role = get_teaching_role(request.user)
        exams = Exam.objects.select_related("course", "semester").all()
        classes = TeachingClass.objects.select_related("course", "semester", "teacher").all()
        grades = Grade.objects.filter(is_published=True).select_related("course", "semester")

        if role == "teacher":
            teacher_id = get_linked_teacher_id(request.user)
            if not teacher_id:
                return Response({"results": []})
            exams = exams.filter(course__teaching_classes__teacher_id=teacher_id).distinct()
            classes = classes.filter(teacher_id=teacher_id)
            grades = grades.filter(course__teaching_classes__teacher_id=teacher_id).distinct()
        elif role == "student":
            student_id = get_linked_student_id(request.user)
            if not student_id:
                return Response({"results": []})
            course_ids = Grade.objects.filter(student_id=student_id).values_list("course_id", flat=True)
            exams = exams.filter(course_id__in=course_ids)
            classes = classes.filter(course_id__in=course_ids)
            grades = grades.filter(student_id=student_id)
        elif role not in FULL_READ_ROLES:
            raise PermissionDenied("当前账号无权查看教学预警。")

        current_semester_id = Semester.objects.filter(is_current=True).values_list("id", flat=True).first()
        if current_semester_id:
            classes = classes.filter(semester_id=current_semester_id)
            grades = grades.filter(semester_id=current_semester_id)
        else:
            latest_grade_semester_id = grades.exclude(semester_id__isnull=True).order_by(
                "-semester_id"
            ).values_list("semester_id", flat=True).first()
            if latest_grade_semester_id is not None:
                grades = grades.filter(semester_id=latest_grade_semester_id)

        alerts = []
        now = timezone.now()
        upcoming_exams = exams.filter(
            exam_date__gte=now,
            exam_date__lte=now + timedelta(days=14),
        ).filter(
            Q(location__isnull=True) | Q(location__exact="") |
            Q(status__in=["待安排", "未安排", "待确认"])
        ).order_by("exam_date").distinct()[:5]

        for exam in upcoming_exams:
            exam_time = timezone.localtime(exam.exam_date).strftime("%m-%d %H:%M")
            detail = "未填写考场" if not (exam.location or "").strip() else f"当前状态：{exam.status}"
            alerts.append({
                "id": f"exam-{exam.id}",
                "level": "orange",
                "levelLabel": "提醒",
                "title": "考试安排待完善",
                "desc": f"{exam.course.name} · {exam_time} · {detail}",
            })

        overflow_classes = classes.filter(
            capacity__gt=0,
            enrolled_count__gt=F("capacity"),
        ).order_by("-enrolled_count")[:5]
        for teaching_class in overflow_classes:
            alerts.append({
                "id": f"class-{teaching_class.id}",
                "level": "red",
                "levelLabel": "异常",
                "title": "教学班人数超过容量",
                "desc": f"{teaching_class.course.name}：选课 {teaching_class.enrolled_count} 人，计划容量 {teaching_class.capacity} 人",
            })

        grade_rows = grades.values("course_id", "course__name").annotate(
            total=Count("id", distinct=True),
            failed=Count("id", filter=Q(score__lt=60), distinct=True),
        ).order_by("-failed")
        fail_alert_count = 0
        for row in grade_rows:
            total = int(row["total"] or 0)
            failed = int(row["failed"] or 0)
            rate = failed / total if total else 0
            if total >= 5 and rate >= 0.30:
                alerts.append({
                    "id": f"grade-{row['course_id']}",
                    "level": "yellow",
                    "levelLabel": "关注",
                    "title": "课程不及格率偏高",
                    "desc": f"{row['course__name']}：已发布成绩 {total} 条，不及格率 {rate * 100:.1f}%",
                })
                fail_alert_count += 1
                if fail_alert_count >= 5:
                    break

        return Response({"results": alerts[:10]})


class DashboardLiveFeedView(APIView):
    """返回真实业务操作日志，不生成演示动态。"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        role = get_teaching_role(request.user)
        qs = TeachingActivityLog.objects.select_related("actor").all()
        if role in FULL_READ_ROLES:
            pass
        elif role == "teacher":
            qs = qs.filter(actor=request.user)
        else:
            return Response({"results": []})

        try:
            limit = min(max(int(request.query_params.get("limit", 8)), 1), 20)
        except (TypeError, ValueError):
            limit = 8

        items = []
        for item in qs[:limit]:
            items.append({
                "id": item.id,
                "time": timezone.localtime(item.created_at).strftime("%m-%d %H:%M"),
                "text": item.message,
                "module": item.module,
                "action": item.get_action_display(),
                "actor": item.actor.get_username() if item.actor else "系统",
            })
        return Response({"results": items})
