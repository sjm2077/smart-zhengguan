from django.db import models


class TeachingKPI(models.Model):
    """教学KPI指标快照（每次快照一条记录，含全部6个指标值）"""

    class PeriodChoices(models.TextChoices):
        SEMESTER = "semester", "学期"
        YEAR = "year", "学年"
        ALL = "all", "全部"

    semester = models.CharField(
        max_length=32,
        verbose_name="统计学期",
        help_text="例如 2024-2025-2",
    )
    period = models.CharField(
        max_length=16,
        choices=PeriodChoices.choices,
        default=PeriodChoices.SEMESTER,
        verbose_name="统计周期",
    )
    college = models.ForeignKey(
        "colleges.College",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="teaching_kpis",
        verbose_name="学院",
        help_text="若为空则为全院汇总",
    )

    # ============ 6 大 KPI 指标 ============
    quality_index = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="教学质量指数",
        help_text="0.00 ~ 100.00",
    )
    quality_index_change = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0.00,
        verbose_name="教学质量指数环比变化(%)",
    )

    satisfaction_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="学生满意度(%)",
    )
    satisfaction_rate_change = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0.00,
        verbose_name="学生满意度环比变化(%)",
    )

    course_pass_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="课程达标率(%)",
    )
    course_pass_rate_change = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0.00,
        verbose_name="课程达标率环比变化(%)",
    )

    seminar_participation = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="研讨参与指数",
    )
    seminar_participation_change = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0.00,
        verbose_name="研讨参与指数环比变化(%)",
    )

    resource_utilization = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="教学资源利用率(%)",
    )
    resource_utilization_change = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0.00,
        verbose_name="教学资源利用率环比变化(%)",
    )

    warning_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="学业预警率(%)",
    )
    warning_rate_change = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0.00,
        verbose_name="学业预警率环比变化(%)",
    )

    # ============ 驾驶舱指标 (cockpit) ============
    total_courses = models.IntegerField(
        default=0,
        verbose_name="开设课程数",
    )
    active_teachers = models.IntegerField(
        default=0,
        verbose_name="在授教师数",
    )
    avg_weekly_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        verbose_name="人均课时(时/周)",
    )
    supervisor_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        verbose_name="督导评分",
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
        db_table = "teaching_kpis"
        verbose_name = "教学KPI指标"
        verbose_name_plural = verbose_name
        ordering = ["-semester", "college__name"]
        indexes = [
            models.Index(fields=["semester"], name="idx_kpi_semester"),
            models.Index(fields=["college_id"], name="idx_kpi_college_id"),
            models.Index(fields=["period"], name="idx_kpi_period"),
            models.Index(fields=["college_id", "semester"], name="idx_kpi_col_semester"),
        ]
        unique_together = [
            ["semester", "period", "college"],
        ]

    def __str__(self):
        college_str = self.college.name if self.college else "全院"
        return f"{college_str} — {self.semester} 质量指数: {self.quality_index}"


class TeachingQuality(models.Model):
    """教学质量分析 & 趋势预测数据点"""

    semester = models.CharField(
        max_length=32,
        verbose_name="学期",
        help_text="例如 2024-2025-2",
    )
    semester_label = models.CharField(
        max_length=32,
        verbose_name="学期标签",
        help_text="显示用标签，如 21秋 / 22春",
    )
    college = models.ForeignKey(
        "colleges.College",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="teaching_qualities",
        verbose_name="学院",
    )

    actual_score = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="实际质量分",
        help_text="0.00 ~ 5.00",
    )
    predicted_score = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="预测质量分",
        help_text="AI 预测值",
    )
    target_score = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=4.50,
        verbose_name="目标线",
    )

    # ============ 维度分解 ============
    teaching_content_score = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="教学内容分",
    )
    teaching_method_score = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="教学方法分",
    )
    interaction_score = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="师生互动分",
    )
    innovation_score = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="课程创新分",
    )
    research_output_score = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="科研产出分",
    )
    social_service_score = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="社会服务分",
    )

    is_prediction = models.BooleanField(
        default=False,
        verbose_name="是否为预测值",
        help_text="True 表示该条为 AI 预测数据",
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
        db_table = "teaching_quality"
        verbose_name = "教学质量趋势"
        verbose_name_plural = verbose_name
        ordering = ["semester", "college__name"]
        indexes = [
            models.Index(fields=["semester"], name="idx_tq_semester"),
            models.Index(fields=["college_id"], name="idx_tq_college_id"),
            models.Index(fields=["college_id", "semester"], name="idx_tq_col_semester"),
            models.Index(fields=["is_prediction"], name="idx_tq_is_pred"),
        ]
        unique_together = [
            ["semester", "college", "is_prediction"],
        ]

    def __str__(self):
        college_str = self.college.name if self.college else "全院"
        pred = "(预)" if self.is_prediction else ""
        return f"{college_str} — {self.semester_label}{pred} 质量分: {self.actual_score or self.predicted_score}"


class SatisfactionSurvey(models.Model):
    """教学满意度调查数据"""

    semester = models.CharField(
        max_length=32,
        verbose_name="学期",
    )
    college = models.ForeignKey(
        "colleges.College",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="satisfaction_surveys",
        verbose_name="学院",
    )

    # ============ 6 个调查维度 × 4 个满意度等级 ============
    dimension = models.CharField(
        max_length=64,
        verbose_name="调查维度",
        help_text="教学内容 / 教学方法 / 课堂氛围 / 课后辅导 / 考核方式 / 教材选用",
    )

    very_satisfied = models.IntegerField(
        default=0,
        verbose_name="非常满意人数",
    )
    satisfied = models.IntegerField(
        default=0,
        verbose_name="满意人数",
    )
    neutral = models.IntegerField(
        default=0,
        verbose_name="一般人数",
    )
    dissatisfied = models.IntegerField(
        default=0,
        verbose_name="不满意人数",
    )

    total_responses = models.IntegerField(
        default=0,
        verbose_name="总参与人数",
    )
    satisfaction_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="满意度综合得分",
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
        db_table = "satisfaction_surveys"
        verbose_name = "教学满意度调查"
        verbose_name_plural = verbose_name
        ordering = ["semester", "college__name", "dimension"]
        indexes = [
            models.Index(fields=["semester"], name="idx_sat_semester"),
            models.Index(fields=["college_id"], name="idx_sat_college_id"),
            models.Index(fields=["dimension"], name="idx_sat_dimension"),
            models.Index(fields=["college_id", "semester"], name="idx_sat_col_semester"),
        ]
        unique_together = [
            ["semester", "college", "dimension"],
        ]

    def __str__(self):
        college_str = self.college.name if self.college else "全院"
        return f"{college_str} — {self.semester} — {self.dimension}: {self.satisfaction_score}"


class RiskEvent(models.Model):
    """风险预警事件"""

    class LevelChoices(models.TextChoices):
        HIGH = "high", "高风险"
        MEDIUM = "medium", "中风险"
        LOW = "low", "低风险"

    class StatusChoices(models.TextChoices):
        ACTIVE = "active", "未处理"
        PROCESSING = "processing", "处理中"
        RESOLVED = "resolved", "已解决"
        DISMISSED = "dismissed", "已忽略"

    level = models.CharField(
        max_length=16,
        choices=LevelChoices.choices,
        verbose_name="风险等级",
    )
    status = models.CharField(
        max_length=16,
        choices=StatusChoices.choices,
        default=StatusChoices.ACTIVE,
        verbose_name="处理状态",
    )
    title = models.CharField(
        max_length=255,
        verbose_name="风险标题",
    )
    description = models.TextField(
        verbose_name="风险描述",
    )
    scope = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="影响范围",
        help_text="如：2个班级 · 68名学生",
    )
    suggested_action = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="建议措施",
        help_text="如：立即处理 / 教研室介入 / 资源采购",
    )

    # ============ 关联实体（可选） ============
    semester = models.CharField(
        max_length=32,
        blank=True,
        default="",
        verbose_name="关联学期",
    )
    college = models.ForeignKey(
        "colleges.College",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="risk_events",
        verbose_name="关联学院",
    )
    course_offering = models.ForeignKey(
        "courses.CourseOffering",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="risk_events",
        verbose_name="关联课程",
    )

    triggered_at = models.DateTimeField(
        verbose_name="触发时间",
        help_text="风险被系统检测到的时间",
    )
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="解决时间",
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
        db_table = "risk_events"
        verbose_name = "风险预警事件"
        verbose_name_plural = verbose_name
        ordering = ["-triggered_at"]
        indexes = [
            models.Index(fields=["level"], name="idx_risk_level"),
            models.Index(fields=["status"], name="idx_risk_status"),
            models.Index(fields=["college_id"], name="idx_risk_college_id"),
            models.Index(fields=["semester"], name="idx_risk_semester"),
            models.Index(fields=["triggered_at"], name="idx_risk_triggered"),
            models.Index(fields=["level", "status"], name="idx_risk_level_status"),
        ]

    @property
    def level_order(self):
        """用于排序：high=0, medium=1, low=2"""
        return {"high": 0, "medium": 1, "low": 2}.get(self.level, 3)

    def __str__(self):
        return f"[{self.get_level_display()}] {self.title}"


class AISuggestion(models.Model):
    """AI 分析建议"""

    class PriorityChoices(models.TextChoices):
        HIGH = "high", "高优先级"
        MEDIUM = "medium", "中优先级"
        LOW = "low", "低优先级"

    class StatusChoices(models.TextChoices):
        PENDING = "pending", "待审核"
        ACCEPTED = "accepted", "已采纳"
        REJECTED = "rejected", "已拒绝"
        IMPLEMENTED = "implemented", "已实施"

    priority = models.CharField(
        max_length=16,
        choices=PriorityChoices.choices,
        verbose_name="优先级",
    )
    status = models.CharField(
        max_length=16,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING,
        verbose_name="状态",
    )
    title = models.CharField(
        max_length=255,
        verbose_name="建议标题",
    )
    description = models.TextField(
        verbose_name="建议详述",
    )
    confidence = models.IntegerField(
        verbose_name="置信度(%)",
        help_text="0 ~ 100，AI 模型给出的置信度",
    )

    # ============ 关联 ============
    semester = models.CharField(
        max_length=32,
        blank=True,
        default="",
        verbose_name="关联学期",
    )
    college = models.ForeignKey(
        "colleges.College",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ai_suggestions",
        verbose_name="关联学院",
    )
    accepted_by = models.ForeignKey(
        "auth_app.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="accepted_suggestions",
        verbose_name="采纳人",
    )

    # ============ AI 元数据 ============
    model_name = models.CharField(
        max_length=64,
        blank=True,
        default="",
        verbose_name="AI 模型名称",
        help_text="如 Gemini-Pro / GPT-4o",
    )
    prompt_version = models.CharField(
        max_length=32,
        blank=True,
        default="",
        verbose_name="提示词版本",
    )
    source_data_snapshot = models.TextField(
        blank=True,
        default="",
        verbose_name="数据快照摘要",
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
        db_table = "ai_suggestions"
        verbose_name = "AI分析建议"
        verbose_name_plural = verbose_name
        ordering = ["-confidence"]
        indexes = [
            models.Index(fields=["priority"], name="idx_ai_priority"),
            models.Index(fields=["status"], name="idx_ai_status"),
            models.Index(fields=["college_id"], name="idx_ai_college_id"),
            models.Index(fields=["semester"], name="idx_ai_semester"),
            models.Index(fields=["confidence"], name="idx_ai_confidence"),
            models.Index(fields=["priority", "status"], name="idx_ai_pri_status"),
        ]

    @property
    def priority_order(self):
        """用于排序：high=0, medium=1, low=2"""
        return {"high": 0, "medium": 1, "low": 2}.get(self.priority, 3)

    def __str__(self):
        return f"[{self.get_priority_display()}] {self.title} (置信度: {self.confidence}%)"