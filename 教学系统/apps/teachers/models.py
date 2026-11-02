from django.db import models


class Teacher(models.Model):
    """教师信息"""

    class TitleChoices(models.TextChoices):
        PROFESSOR = "professor", "教授"
        ASSOCIATE_PROFESSOR = "associate_professor", "副教授"
        ASSISTANT_PROFESSOR = "assistant_professor", "助理教授"
        LECTURER = "lecturer", "讲师"
        TEACHING_ASSISTANT = "teaching_assistant", "助教"
        RESEARCHER = "researcher", "研究员"
        SENIOR_ENGINEER = "senior_engineer", "高级工程师"

    class StatusChoices(models.TextChoices):
        ACTIVE = "active", "在职"
        ON_LEAVE = "on_leave", "休假"
        SECONDED = "seconded", "借调"
        RESIGNED = "resigned", "离职"
        RETIRED = "retired", "退休"

    # ============ 基本信息 ============
    name = models.CharField(
        max_length=64,
        verbose_name="姓名",
    )
    gender = models.CharField(
        max_length=8,
        choices=[("male", "男"), ("female", "女")],
        blank=True,
        default="",
        verbose_name="性别",
    )
    avatar = models.URLField(
        max_length=512,
        blank=True,
        default="",
        verbose_name="头像地址",
    )
    title = models.CharField(
        max_length=32,
        choices=TitleChoices.choices,
        verbose_name="职称",
    )
    college = models.ForeignKey(
        "colleges.College",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="teachers",
        verbose_name="所属学院",
    )
    email = models.EmailField(
        max_length=128,
        blank=True,
        default="",
        verbose_name="邮箱",
    )
    phone = models.CharField(
        max_length=32,
        blank=True,
        default="",
        verbose_name="电话",
    )
    office_location = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="办公地点",
    )
    research_areas = models.TextField(
        blank=True,
        default="",
        verbose_name="研究方向",
    )
    bio = models.TextField(
        blank=True,
        default="",
        verbose_name="个人简介",
    )
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.00,
        verbose_name="平均评教分",
    )
    status = models.CharField(
        max_length=32,
        choices=StatusChoices.choices,
        default=StatusChoices.ACTIVE,
        verbose_name="状态",
    )

    # ============ 关联账户 ============
    user = models.OneToOneField(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="teacher_profile",
        verbose_name="关联登录账户",
        help_text="与 users.User 一对一绑定，仅 role=teacher 时有值",
    )

    # ============ 时间戳 ============
    hire_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="入职日期",
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
        db_table = "teachers"
        verbose_name = "教师"
        verbose_name_plural = verbose_name
        ordering = ["college__name", "name"]
        indexes = [
            models.Index(fields=["college_id"], name="idx_teacher_college_id"),
            models.Index(fields=["title"], name="idx_teacher_title"),
            models.Index(fields=["status"], name="idx_teacher_status"),
            models.Index(fields=["user_id"], name="idx_teacher_user_id"),
            models.Index(fields=["email"], name="idx_teacher_email"),
            models.Index(fields=["name"], name="idx_teacher_name"),
        ]

    def __str__(self):
        college_name = self.college.name if self.college else "未分配学院"
        return f"{self.name} ({self.get_title_display()}) — {college_name}"


class TeachingTeam(models.Model):
    """教学团队 / 教研室"""

    name = models.CharField(
        max_length=128,
        verbose_name="团队名称",
    )
    code = models.CharField(
        max_length=32,
        unique=True,
        blank=True,
        default="",
        verbose_name="团队编号",
    )
    college = models.ForeignKey(
        "colleges.College",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="teaching_teams",
        verbose_name="所属学院",
    )
    leader = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="led_teams",
        verbose_name="团队负责人",
    )
    members = models.ManyToManyField(
        Teacher,
        blank=True,
        related_name="teaching_teams",
        verbose_name="团队成员",
    )
    description = models.TextField(
        blank=True,
        default="",
        verbose_name="团队描述",
    )
    established_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="成立日期",
    )
    sort_order = models.IntegerField(
        default=0,
        verbose_name="排序序号",
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
        db_table = "teaching_teams"
        verbose_name = "教学团队"
        verbose_name_plural = verbose_name
        ordering = ["sort_order", "id"]
        indexes = [
            models.Index(fields=["college_id"], name="idx_team_college_id"),
            models.Index(fields=["leader_id"], name="idx_team_leader_id"),
            models.Index(fields=["code"], name="idx_team_code"),
        ]

    def __str__(self):
        return f"{self.name}（负责人: {self.leader.name if self.leader else '未指定'}）"


class TeacherPublication(models.Model):
    """教师科研成果"""

    class PubTypeChoices(models.TextChoices):
        PAPER = "paper", "论文"
        BOOK = "book", "著作"
        PATENT = "patent", "专利"
        PROJECT = "project", "项目"
        AWARD = "award", "奖项"
        OTHER = "other", "其他"

    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name="publications",
        verbose_name="所属教师",
    )
    title = models.CharField(
        max_length=255,
        verbose_name="成果标题",
    )
    pub_type = models.CharField(
        max_length=16,
        choices=PubTypeChoices.choices,
        verbose_name="成果类型",
    )
    authors = models.TextField(
        blank=True,
        default="",
        verbose_name="作者列表",
    )
    journal_or_source = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="期刊/来源",
    )
    pub_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="发表日期",
    )
    doi_or_link = models.URLField(
        max_length=512,
        blank=True,
        default="",
        verbose_name="DOI / 链接",
    )
    abstract = models.TextField(
        blank=True,
        default="",
        verbose_name="摘要",
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
        db_table = "teacher_publications"
        verbose_name = "教师科研成果"
        verbose_name_plural = verbose_name
        ordering = ["-pub_date", "-created_at"]
        indexes = [
            models.Index(fields=["teacher_id"], name="idx_pub_teacher_id"),
            models.Index(fields=["pub_type"], name="idx_pub_type"),
            models.Index(fields=["-pub_date"], name="idx_pub_date"),
        ]

    def __str__(self):
        return f"[{self.get_pub_type_display()}] {self.title}"


class TeacherAward(models.Model):
    """教师荣誉与获奖"""

    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name="awards",
        verbose_name="所属教师",
    )
    name = models.CharField(
        max_length=255,
        verbose_name="奖项名称",
    )
    level = models.CharField(
        max_length=32,
        choices=[
            ("national", "国家级"),
            ("provincial", "省部级"),
            ("municipal", "市级"),
            ("school", "校级"),
            ("other", "其他"),
        ],
        verbose_name="获奖级别",
    )
    issuing_authority = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="颁发机构",
    )
    award_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="获奖日期",
    )
    description = models.TextField(
        blank=True,
        default="",
        verbose_name="奖项描述",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="创建时间",
    )

    class Meta:
        db_table = "teacher_awards"
        verbose_name = "教师荣誉获奖"
        verbose_name_plural = verbose_name
        ordering = ["-award_date"]
        indexes = [
            models.Index(fields=["teacher_id"], name="idx_award_teacher_id"),
            models.Index(fields=["level"], name="idx_award_level"),
        ]

    def __str__(self):
        return f"{self.name} — {self.get_level_display()}"


class TeacherCourseEvaluation(models.Model):
    """每学期教师课程评教结果"""

    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name="course_evaluations",
        verbose_name="教师",
    )
    course_offering = models.ForeignKey(
        "courses.CourseOffering",
        on_delete=models.CASCADE,
        related_name="teacher_evaluations",
        verbose_name="开课记录",
    )
    semester = models.CharField(
        max_length=32,
        verbose_name="学期",
    )
    teaching_score = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        verbose_name="教学评分",
    )
    content_score = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="内容评分",
    )
    method_score = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="方法评分",
    )
    interaction_score = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="互动评分",
    )
    rigor_score = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="严格度评分",
    )
    overall_score = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        verbose_name="综合评分",
    )
    participation_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        verbose_name="参评率(%)",
    )
    student_count = models.IntegerField(
        default=0,
        verbose_name="参评学生数",
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
        db_table = "teacher_course_evaluations"
        verbose_name = "教师课程评教"
        verbose_name_plural = verbose_name
        ordering = ["-semester", "-overall_score"]
        indexes = [
            models.Index(fields=["teacher_id"], name="idx_eval_teacher_id"),
            models.Index(fields=["course_offering_id"], name="idx_eval_offering_id"),
            models.Index(fields=["semester"], name="idx_eval_semester"),
            models.Index(fields=["teacher_id", "semester"], name="idx_eval_teacher_semester"),
        ]
        unique_together = [
            ["teacher", "course_offering", "semester"],
        ]

    def __str__(self):
        return f"{self.teacher.name} — {self.course_offering.course.name} ({self.semester}) 评分: {self.overall_score}"