from django.db import models


class CourseCategory(models.Model):
    """课程分类树"""

    name = models.CharField(
        max_length=64,
        verbose_name="分类名称",
    )
    color = models.CharField(
        max_length=16,
        default="#1677ff",
        verbose_name="分类颜色",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
        db_index=False,
        verbose_name="上级分类",
    )
    sort_order = models.IntegerField(
        default=0,
        verbose_name="排序序号",
    )
    icon = models.CharField(
        max_length=64,
        blank=True,
        default="",
        verbose_name="图标",
    )
    description = models.TextField(
        blank=True,
        default="",
        verbose_name="分类描述",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="创建时间",
    )

    class Meta:
        db_table = "course_categories"
        verbose_name = "课程分类"
        verbose_name_plural = verbose_name
        ordering = ["sort_order", "id"]
        indexes = [
            models.Index(fields=["parent_id"], name="idx_parent_id"),
        ]
        unique_together = [
            ["name", "parent"],
        ]

    def __str__(self):
        return self.name


class Course(models.Model):
    """课程库"""

    class CourseTypeChoices(models.TextChoices):
        REQUIRED = "required", "必修"
        ELECTIVE = "elective", "选修"
        GENERAL = "general", "通识"

    class CourseStatusChoices(models.TextChoices):
        ACTIVE = "active", "启用"
        INACTIVE = "inactive", "停用"

    code = models.CharField(
        max_length=32,
        unique=True,
        verbose_name="课程代码",
    )
    name = models.CharField(
        max_length=128,
        verbose_name="课程名称",
    )
    credit = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        verbose_name="学分",
    )
    hours = models.IntegerField(
        verbose_name="总学时",
    )
    category = models.ForeignKey(
        CourseCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="courses",
        verbose_name="课程分类",
    )
    college = models.ForeignKey(
        "colleges.College",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="courses",
        verbose_name="开课学院",
    )
    type = models.CharField(
        max_length=16,
        choices=CourseTypeChoices.choices,
        verbose_name="课程类型",
    )
    campus = models.CharField(
        max_length=64,
        blank=True,
        default="",
        verbose_name="开课校区",
    )
    description = models.TextField(
        blank=True,
        default="",
        verbose_name="课程简介",
    )
    cover_color = models.CharField(
        max_length=32,
        blank=True,
        default="",
        verbose_name="封面主色",
    )
    cover_gradient = models.CharField(
        max_length=64,
        blank=True,
        default="",
        verbose_name="封面渐变色",
    )
    cover_icon = models.CharField(
        max_length=64,
        blank=True,
        default="",
        verbose_name="封面图标类型",
    )
    status = models.CharField(
        max_length=16,
        choices=CourseStatusChoices.choices,
        default=CourseStatusChoices.ACTIVE,
        verbose_name="状态",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="创建时间",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="更新时间",
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="删除时间",
    )

    class Meta:
        db_table = "courses"
        verbose_name = "课程"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["category_id"], name="idx_category_id"),
            models.Index(fields=["college_id"], name="idx_college_id"),
            models.Index(fields=["type"], name="idx_type"),
            models.Index(fields=["status"], name="idx_status"),
        ]

    def __str__(self):
        return f"{self.code} {self.name}"


class CourseOffering(models.Model):
    """每学期实际开课"""

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="offerings",
        verbose_name="课程",
    )
    teacher = models.ForeignKey(
        "teachers.Teacher",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="offerings",
        verbose_name="授课教师",
    )
    semester = models.CharField(
        max_length=32,
        verbose_name="学期",
    )
    class_name = models.CharField(
        max_length=128,
        verbose_name="教学班名称",
    )
    student_count = models.IntegerField(
        default=0,
        verbose_name="选课人数",
    )
    class_location = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="上课地点",
    )
    class_time = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="上课时间描述",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="创建时间",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="更新时间",
    )

    class Meta:
        db_table = "course_offerings"
        verbose_name = "开课记录"
        verbose_name_plural = verbose_name
        ordering = ["semester", "course"]
        indexes = [
            models.Index(fields=["course_id"], name="idx_course_id"),
            models.Index(fields=["teacher_id"], name="idx_teacher_id"),
            models.Index(fields=["semester"], name="idx_semester"),
        ]
        unique_together = [
            ["course", "teacher", "semester"],
        ]

    def __str__(self):
        return f"{self.course.name} - {self.class_name} ({self.semester})"


class CourseHotScore(models.Model):
    """课程热度排行（每学期）"""

    course_offering = models.ForeignKey(
        CourseOffering,
        on_delete=models.CASCADE,
        related_name="hot_scores",
        verbose_name="开课记录",
    )
    semester = models.CharField(
        max_length=32,
        verbose_name="学期",
    )
    hot_score = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        verbose_name="热度评分",
    )
    ranking = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="排名",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="创建时间",
    )

    class Meta:
        db_table = "course_hot_scores"
        verbose_name = "课程热度排行"
        verbose_name_plural = verbose_name
        ordering = ["-hot_score"]
        indexes = [
            models.Index(fields=["course_offering_id"], name="idx_offering_id"),
            models.Index(fields=["semester"], name="idx_semester"),
            models.Index(fields=["-hot_score"], name="idx_hot_score"),
        ]
        unique_together = [
            ["course_offering", "semester"],
        ]

    def __str__(self):
        return f"{self.course_offering.course.name} hot={self.hot_score} ({self.semester})"