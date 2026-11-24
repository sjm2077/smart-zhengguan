
from django.conf import settings
from django.db import models


class College(models.Model):
    name = models.CharField("学院/教研单位名称", max_length=120, unique=True)
    code = models.CharField("单位代码", max_length=30, blank=True)
    description = models.TextField("说明", blank=True)
    is_active = models.BooleanField("启用", default=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "学院/教研单位"
        verbose_name_plural = "学院/教研单位"

    def __str__(self):
        return self.name


class Semester(models.Model):
    TERM_CHOICES = [
        ("", "未设置"),
        ("first", "第一学期"),
        ("second", "第二学期"),
    ]

    name = models.CharField("学期名称", max_length=50, unique=True)
    academic_year = models.CharField(
        "学年", max_length=20, blank=True, default=""
    )
    term = models.CharField(
        "学期类型",
        max_length=10,
        choices=TERM_CHOICES,
        blank=True,
        default="",
    )
    start_date = models.DateField("开始日期", null=True, blank=True)
    end_date = models.DateField("结束日期", null=True, blank=True)
    is_current = models.BooleanField("当前学期", default=False)

    class Meta:
        ordering = ["-start_date", "name"]
        verbose_name = "学期"
        verbose_name_plural = "学期"

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ("admin", "系统管理员"),
        ("academic", "教务管理人员"),
        ("teacher", "教师"),
        ("student", "学生"),
        ("viewer", "只读用户"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="teaching_profile",
    )
    role = models.CharField(
        "角色", max_length=20, choices=ROLE_CHOICES, default="viewer"
    )
    college = models.ForeignKey(
        College,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
    )
    student = models.OneToOneField(
        "Student",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="user_profile",
        verbose_name="关联学生",
    )
    teacher = models.OneToOneField(
        "Teacher",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="user_profile",
        verbose_name="关联教师",
    )
    avatar = models.URLField("头像地址", blank=True)

    class Meta:
        verbose_name = "用户教学权限"
        verbose_name_plural = "用户教学权限"

    def __str__(self):
        return f"{self.user.username} ({self.role})"


class Teacher(models.Model):
    GENDER_CHOICES = [
        ("男", "男"),
        ("女", "女"),
        ("未说明", "未说明"),
    ]

    teacher_no = models.CharField("工号", max_length=40, unique=True)
    name = models.CharField("姓名", max_length=80)
    gender = models.CharField(
        "性别", max_length=10, choices=GENDER_CHOICES, default="未说明"
    )
    college = models.ForeignKey(
        College, on_delete=models.PROTECT, related_name="teachers"
    )
    title = models.CharField("职称", max_length=50, blank=True)
    phone = models.CharField("联系电话", max_length=30, blank=True)
    email = models.EmailField("电子邮箱", blank=True)
    description = models.TextField("简介", blank=True)
    is_active = models.BooleanField("在职", default=True)

    class Meta:
        ordering = ["teacher_no"]
        verbose_name = "教师"
        verbose_name_plural = "教师"

    def __str__(self):
        return f"{self.teacher_no} {self.name}"


class Student(models.Model):
    GENDER_CHOICES = [
        ("男", "男"),
        ("女", "女"),
        ("未说明", "未说明"),
    ]

    student_no = models.CharField("学号", max_length=40, unique=True)
    name = models.CharField("姓名", max_length=80)
    gender = models.CharField(
        "性别", max_length=10, choices=GENDER_CHOICES, default="未说明"
    )
    college = models.ForeignKey(
        College, on_delete=models.PROTECT, related_name="students"
    )
    major = models.CharField("专业", max_length=100)
    grade = models.CharField("年级", max_length=20)
    class_name = models.CharField("班级", max_length=60, blank=True)
    email = models.EmailField("电子邮箱", blank=True)
    phone = models.CharField("联系电话", max_length=30, blank=True)
    enrollment_year = models.PositiveSmallIntegerField("入学年份")
    is_active = models.BooleanField("在籍", default=True)

    class Meta:
        ordering = ["student_no"]
        indexes = [
            models.Index(fields=["grade", "major"]),
            models.Index(fields=["college", "grade"]),
        ]
        verbose_name = "学生"
        verbose_name_plural = "学生"

    def __str__(self):
        return f"{self.student_no} {self.name}"


class Course(models.Model):
    TYPE_CHOICES = [
        ("必修", "必修"),
        ("公共课", "公共课"),
        ("选修", "选修"),
        ("实践", "实践"),
        ("其他", "其他"),
    ]

    code = models.CharField("课程代码", max_length=40, unique=True)
    name = models.CharField("课程名称", max_length=150)
    credit = models.DecimalField(
        "学分", max_digits=4, decimal_places=1, default=0
    )
    hours = models.PositiveSmallIntegerField("总学时", default=0)
    college = models.ForeignKey(
        College, on_delete=models.PROTECT, related_name="courses"
    )
    semester = models.ForeignKey(
        Semester,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="courses",
    )
    course_type = models.CharField(
        "课程类型",
        max_length=20,
        choices=TYPE_CHOICES,
        default="必修",
    )
    description = models.TextField("课程简介", blank=True)
    is_active = models.BooleanField("启用", default=True)

    class Meta:
        ordering = ["code"]
        verbose_name = "课程"
        verbose_name_plural = "课程"

    def __str__(self):
        return f"{self.code} {self.name}"


class TeachingClass(models.Model):
    course = models.ForeignKey(
        Course, on_delete=models.PROTECT, related_name="teaching_classes"
    )
    semester = models.ForeignKey(
        Semester, on_delete=models.PROTECT, related_name="teaching_classes"
    )
    teacher = models.ForeignKey(
        Teacher, on_delete=models.PROTECT, related_name="teaching_classes"
    )
    class_name = models.CharField("教学班名称", max_length=100)
    capacity = models.PositiveSmallIntegerField("计划人数", default=0)
    enrolled_count = models.PositiveSmallIntegerField("选课人数", default=0)
    schedule = models.CharField("上课时间", max_length=160, blank=True)
    classroom = models.CharField("教室", max_length=100, blank=True)
    status = models.CharField("状态", max_length=20, default="开课中")

    class Meta:
        ordering = ["semester", "course__code", "class_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["course", "semester", "class_name"],
                name="uniq_teaching_class_course_semester_name",
            )
        ]
        verbose_name = "教学班"
        verbose_name_plural = "教学班"

    def __str__(self):
        return f"{self.course.name} - {self.class_name}"


class Exam(models.Model):
    TYPE_CHOICES = [
        ("期末考试", "期末考试"),
        ("期中考试", "期中考试"),
        ("补考", "补考"),
        ("课程考核", "课程考核"),
    ]

    name = models.CharField("考试名称", max_length=160)
    course = models.ForeignKey(
        Course, on_delete=models.PROTECT, related_name="exams"
    )
    semester = models.ForeignKey(
        Semester, on_delete=models.PROTECT, related_name="exams"
    )
    exam_type = models.CharField(
        "考试类型",
        max_length=30,
        choices=TYPE_CHOICES,
        default="期末考试",
    )
    exam_date = models.DateTimeField("考试时间")
    duration = models.PositiveSmallIntegerField(
        "考试时长（分钟）", default=120
    )
    total_score = models.DecimalField(
        "满分", max_digits=5, decimal_places=1, default=100
    )
    location = models.CharField("考场", max_length=120, blank=True)
    status = models.CharField("状态", max_length=20, default="待安排")

    class Meta:
        ordering = ["exam_date", "course__code"]
        verbose_name = "考试安排"
        verbose_name_plural = "考试安排"

    def __str__(self):
        return f"{self.name} - {self.course.name}"


class Grade(models.Model):
    student = models.ForeignKey(
        Student, on_delete=models.PROTECT, related_name="grades"
    )
    course = models.ForeignKey(
        Course, on_delete=models.PROTECT, related_name="grades"
    )
    semester = models.ForeignKey(
        Semester,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="grades",
    )
    exam = models.ForeignKey(
        Exam,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="grades",
        verbose_name="关联考试",
    )
    score = models.DecimalField("成绩", max_digits=5, decimal_places=2)
    grade_point = models.DecimalField(
        "绩点",
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        default=None,
    )
    exam_type = models.CharField("考核类型", max_length=30, default="期末")
    exam_date = models.DateField("考核日期", null=True, blank=True)
    remark = models.CharField("备注", max_length=250, blank=True)
    is_published = models.BooleanField("已发布", default=False)

    class Meta:
        ordering = ["student__student_no", "course__code"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "course", "semester", "exam_type"],
                name="uniq_grade_student_course_semester_type",
            )
        ]
        verbose_name = "成绩"
        verbose_name_plural = "成绩"

    def __str__(self):
        return f"{self.student.student_no} - {self.course.name}: {self.score}"


class Notice(models.Model):
    TYPE_CHOICES = [
        ("info", "通知"),
        ("warning", "提醒"),
        ("success", "完成"),
    ]

    title = models.CharField("标题", max_length=200)
    content = models.TextField("内容")
    notice_type = models.CharField(
        "类型", max_length=20, choices=TYPE_CHOICES, default="info"
    )
    publisher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="teaching_notices",
    )
    is_published = models.BooleanField("已发布", default=False)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "教学通知"
        verbose_name_plural = "教学通知"

    def __str__(self):
        return self.title

class GraduateEmploymentStat(models.Model):
    """按学院、毕业年份和去向类别保存的毕业生就业汇总数据。"""

    DESTINATION_CHOICES = [
        ("employment", "协议/合同就业"),
        ("further_study", "升学"),
        ("civil_service", "考公考编"),
        ("flexible", "灵活就业"),
        ("entrepreneurship", "自主创业"),
        ("unemployed", "待就业"),
        ("other", "其他"),
    ]

    college = models.ForeignKey(
        College,
        on_delete=models.PROTECT,
        related_name="graduate_employment_stats",
        verbose_name="所属学院",
    )
    graduation_year = models.PositiveSmallIntegerField("毕业年份")
    destination_type = models.CharField(
        "就业去向类别", max_length=30, choices=DESTINATION_CHOICES
    )
    graduate_count = models.PositiveIntegerField("毕业生人数", default=0)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        ordering = ["-graduation_year", "college__name", "destination_type"]
        constraints = [
            models.UniqueConstraint(
                fields=["college", "graduation_year", "destination_type"],
                name="uniq_grad_emp_stat",
            )
        ]
        verbose_name = "毕业生就业统计"
        verbose_name_plural = "毕业生就业统计"

    def __str__(self):
        return f"{self.college.name} - {self.graduation_year}届 - {self.get_destination_type_display()}"


class TeachingActivityLog(models.Model):
    """教务业务操作日志，用于首页最近动态展示。"""

    ACTION_CHOICES = [
        ("create", "新增"),
        ("update", "修改"),
        ("delete", "删除"),
    ]

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="teaching_activity_logs",
        verbose_name="操作人",
    )
    action = models.CharField("操作类型", max_length=10, choices=ACTION_CHOICES)
    module = models.CharField("业务模块", max_length=40)
    object_label = models.CharField("业务对象", max_length=200, blank=True)
    message = models.CharField("动态内容", max_length=255)
    created_at = models.DateTimeField("发生时间", auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "教务操作动态"
        verbose_name_plural = "教务操作动态"

    def __str__(self):
        return self.message

# 智能预警处理记录：与 teaching 原有模型共用 Django 应用。
from .ai_models import AIWarningCase
