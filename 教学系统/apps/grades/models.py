from django.db import models


class Grade(models.Model):
    """学生成绩明细"""

    class GradeLevelChoices(models.TextChoices):
        A = "A", "优秀 (90-100)"
        B = "B", "良好 (80-89)"
        C = "C", "中等 (70-79)"
        D = "D", "及格 (60-69)"
        F = "F", "不及格 (0-59)"

    class ExamTypeChoices(models.TextChoices):
        FINAL = "final", "期末"
        MAKEUP = "makeup", "补考"
        RETAKE = "retake", "重修"

    class StatusChoices(models.TextChoices):
        NORMAL = "normal", "正常"
        WITHDRAWN = "withdrawn", "退课"
        INCOMPLETE = "incomplete", "缓考"

    # ============ 关联 ============
    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="grades",
        verbose_name="学生",
    )
    course_offering = models.ForeignKey(
        "courses.CourseOffering",
        on_delete=models.CASCADE,
        related_name="grades",
        verbose_name="开课记录",
    )
    semester = models.CharField(
        max_length=32,
        verbose_name="学期",
        help_text="例如 2024-2025-2",
    )

    # ============ 成绩数据 ============
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="总评成绩",
        help_text="0.00 ~ 100.00",
    )
    regular_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="平时成绩",
    )
    midterm_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="期中成绩",
    )
    final_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="期末成绩",
    )
    gpa = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="绩点(GPA)",
        help_text="4.0 制绩点",
    )
    grade_level = models.CharField(
        max_length=4,
        choices=GradeLevelChoices.choices,
        blank=True,
        default="",
        verbose_name="等级",
    )

    # ============ 状态 ============
    exam_type = models.CharField(
        max_length=16,
        choices=ExamTypeChoices.choices,
        default=ExamTypeChoices.FINAL,
        verbose_name="考试类型",
    )
    status = models.CharField(
        max_length=16,
        choices=StatusChoices.choices,
        default=StatusChoices.NORMAL,
        verbose_name="状态",
    )

    # ============ 时间戳 ============
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="创建时间",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="更新时间",
    )

    class Meta:
        db_table = "grades"
        verbose_name = "学生成绩"
        verbose_name_plural = verbose_name
        ordering = ["semester", "student__student_no"]
        indexes = [
            models.Index(fields=["student_id"], name="idx_grade_student_id"),
            models.Index(fields=["course_offering_id"], name="idx_grade_offering_id"),
            models.Index(fields=["semester"], name="idx_grade_semester"),
            models.Index(fields=["grade_level"], name="idx_grade_level"),
            models.Index(fields=["score"], name="idx_grade_score"),
            models.Index(fields=["student_id", "semester"], name="idx_grade_stu_semester"),
            models.Index(fields=["course_offering_id", "semester"], name="idx_grade_off_semester"),
        ]
        unique_together = [
            ["student", "course_offering", "semester", "exam_type"],
        ]

    def __str__(self):
        score_str = f"{self.score}" if self.score is not None else "未评分"
        return f"{self.student.name} — {self.course_offering.course.name} ({self.semester}): {score_str}"


class GPAStatistics(models.Model):
    """GPA 学期统计快照（每个学生每学期一条）"""

    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="gpa_statistics",
        verbose_name="学生",
    )
    semester = models.CharField(
        max_length=32,
        verbose_name="学期",
    )
    gpa = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        verbose_name="学期 GPA",
    )
    cumulative_gpa = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        verbose_name="累计 GPA",
    )
    total_credits = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=0.0,
        verbose_name="学期总学分",
    )
    cumulative_credits = models.DecimalField(
        max_digits=6,
        decimal_places=1,
        default=0.0,
        verbose_name="累计总学分",
    )
    course_count = models.IntegerField(
        default=0,
        verbose_name="课程门数",
    )
    weighted_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        verbose_name="加权平均分",
    )
    pass_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        verbose_name="通过率(%)",
    )
    rank_in_college = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="学院排名",
    )
    rank_in_major = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="专业排名",
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
        db_table = "gpa_statistics"
        verbose_name = "GPA学期统计"
        verbose_name_plural = verbose_name
        ordering = ["student", "-semester"]
        indexes = [
            models.Index(fields=["student_id"], name="idx_gpastat_student_id"),
            models.Index(fields=["semester"], name="idx_gpastat_semester"),
            models.Index(fields=["gpa"], name="idx_gpastat_gpa"),
            models.Index(fields=["student_id", "semester"], name="idx_gpastat_stu_semester"),
        ]
        unique_together = [
            ["student", "semester"],
        ]

    def __str__(self):
        return f"{self.student.name} — {self.semester} GPA: {self.gpa}"


class GradeTrend(models.Model):
    """成绩趋势聚合快照（每学期—学院级别统计）"""

    semester = models.CharField(
        max_length=32,
        verbose_name="学期",
    )
    college = models.ForeignKey(
        "colleges.College",
        on_delete=models.CASCADE,
        related_name="grade_trends",
        verbose_name="学院",
    )
    avg_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="平均分",
    )
    median_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="中位数分",
    )
    gpa_avg = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        verbose_name="平均 GPA",
    )
    pass_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="通过率(%)",
    )
    excellent_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="优秀率(%)",
        help_text="成绩 ≥ 90 比例",
    )
    fail_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        verbose_name="不及格率(%)",
        help_text="成绩 < 60 比例",
    )
    score_stddev = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="成绩标准差",
    )
    student_count = models.IntegerField(
        default=0,
        verbose_name="参评学生数",
    )
    course_count = models.IntegerField(
        default=0,
        verbose_name="课程数",
    )
    grade_count = models.IntegerField(
        default=0,
        verbose_name="成绩记录数",
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
        db_table = "grade_trends"
        verbose_name = "成绩趋势统计"
        verbose_name_plural = verbose_name
        ordering = ["semester", "college__name"]
        indexes = [
            models.Index(fields=["semester"], name="idx_trend_semester"),
            models.Index(fields=["college_id"], name="idx_trend_college_id"),
            models.Index(fields=["college_id", "semester"], name="idx_trend_col_semester"),
        ]
        unique_together = [
            ["semester", "college"],
        ]

    def __str__(self):
        return f"{self.college.name} — {self.semester} 均分: {self.avg_score}"