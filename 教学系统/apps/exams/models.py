from django.db import models


class Exam(models.Model):
    """考试安排"""

    class TypeChoices(models.TextChoices):
        FINAL = "final", "期末考试"
        MIDTERM = "midterm", "期中考试"
        MAKEUP = "makeup", "补考"
        RETAKE = "retake", "重修考试"
        ORAL = "oral", "口试"
        PRACTICAL = "practical", "实操考试"

    class ModeChoices(models.TextChoices):
        OFFLINE = "offline", "线下笔试"
        ONLINE = "online", "线上考试"
        COMPUTER = "computer", "上机考试"
        OPEN_BOOK = "open_book", "开卷考试"
        ORAL = "oral", "口试"
        PRACTICAL = "practical", "实操"

    class StatusChoices(models.TextChoices):
        DRAFT = "draft", "草稿"
        SCHEDULED = "scheduled", "已安排"
        IN_PROGRESS = "in_progress", "进行中"
        FINISHED = "finished", "已结束"
        CANCELED = "canceled", "已取消"

    # ============ 关联 ============
    course_offering = models.ForeignKey(
        "courses.CourseOffering",
        on_delete=models.CASCADE,
        related_name="exams",
        verbose_name="开课记录",
    )
    teacher = models.ForeignKey(
        "teachers.Teacher",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="exams",
        verbose_name="主考教师",
    )
    semester = models.CharField(
        max_length=32,
        verbose_name="学期",
        help_text="例如 2024-2025-2",
    )

    # ============ 基本信息 ============
    name = models.CharField(
        max_length=255,
        verbose_name="考试名称",
    )
    exam_type = models.CharField(
        max_length=16,
        choices=TypeChoices.choices,
        default=TypeChoices.FINAL,
        verbose_name="考试类型",
    )
    mode = models.CharField(
        max_length=16,
        choices=ModeChoices.choices,
        default=ModeChoices.OFFLINE,
        verbose_name="考试方式",
    )
    status = models.CharField(
        max_length=16,
        choices=StatusChoices.choices,
        default=StatusChoices.DRAFT,
        verbose_name="状态",
    )

    # ============ 时间安排 ============
    exam_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="考试日期",
    )
    start_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name="开始时间",
    )
    end_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name="结束时间",
    )
    duration_minutes = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="考试时长(分钟)",
    )

    # ============ 其他 ============
    total_students = models.IntegerField(
        default=0,
        verbose_name="应考人数",
    )
    notes = models.TextField(
        blank=True,
        default="",
        verbose_name="备注",
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
        db_table = "exams"
        verbose_name = "考试安排"
        verbose_name_plural = verbose_name
        ordering = ["-exam_date", "start_time"]
        indexes = [
            models.Index(fields=["course_offering_id"], name="idx_exam_offering_id"),
            models.Index(fields=["teacher_id"], name="idx_exam_teacher_id"),
            models.Index(fields=["semester"], name="idx_exam_semester"),
            models.Index(fields=["exam_type"], name="idx_exam_type"),
            models.Index(fields=["status"], name="idx_exam_status"),
            models.Index(fields=["exam_date"], name="idx_exam_date"),
            models.Index(fields=["course_offering_id", "semester"], name="idx_exam_off_semester"),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_exam_type_display()}) — {self.exam_date}"


class ExamRoom(models.Model):
    """考场/教室分配"""

    class RoomTypeChoices(models.TextChoices):
        CLASSROOM = "classroom", "普通教室"
        LAB = "lab", "实验室"
        LECTURE_HALL = "lecture_hall", "阶梯教室"
        COMPUTER_ROOM = "computer_room", "机房"
        GYM = "gym", "体育馆"
        OTHER = "other", "其他"

    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name="rooms",
        verbose_name="考试",
    )
    name = models.CharField(
        max_length=128,
        verbose_name="考场名称",
    )
    building = models.CharField(
        max_length=128,
        blank=True,
        default="",
        verbose_name="教学楼",
    )
    floor = models.CharField(
        max_length=16,
        blank=True,
        default="",
        verbose_name="楼层",
    )
    room_type = models.CharField(
        max_length=32,
        choices=RoomTypeChoices.choices,
        default=RoomTypeChoices.CLASSROOM,
        verbose_name="教室类型",
    )
    capacity = models.IntegerField(
        default=0,
        verbose_name="容量",
    )
    assigned_count = models.IntegerField(
        default=0,
        verbose_name="已分配人数",
    )
    notes = models.TextField(
        blank=True,
        default="",
        verbose_name="备注",
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
        db_table = "exam_rooms"
        verbose_name = "考场分配"
        verbose_name_plural = verbose_name
        ordering = ["exam", "name"]
        indexes = [
            models.Index(fields=["exam_id"], name="idx_room_exam_id"),
            models.Index(fields=["building"], name="idx_room_building"),
        ]

    def __str__(self):
        return f"{self.name} — {self.exam.name}"


class ExamInvigilator(models.Model):
    """监考安排（多对多关联 Exam 与 Teacher，含额外信息）"""

    class RoleChoices(models.TextChoices):
        CHIEF = "chief", "主监考"
        INVIGILATOR = "invigilator", "监考员"
        ASSISTANT = "assistant", "助理监考"
        PATROL = "patrol", "巡考"

    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name="invigilators",
        verbose_name="考试",
    )
    teacher = models.ForeignKey(
        "teachers.Teacher",
        on_delete=models.CASCADE,
        related_name="exam_invigilations",
        verbose_name="监考教师",
    )
    room = models.ForeignKey(
        ExamRoom,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invigilators",
        verbose_name="负责考场",
    )
    role = models.CharField(
        max_length=16,
        choices=RoleChoices.choices,
        default=RoleChoices.INVIGILATOR,
        verbose_name="监考角色",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="创建时间",
    )

    class Meta:
        db_table = "exam_invigilators"
        verbose_name = "监考安排"
        verbose_name_plural = verbose_name
        ordering = ["exam", "teacher__name"]
        unique_together = [
            ["exam", "teacher"],
        ]
        indexes = [
            models.Index(fields=["exam_id"], name="idx_inv_exam_id"),
            models.Index(fields=["teacher_id"], name="idx_inv_teacher_id"),
            models.Index(fields=["room_id"], name="idx_inv_room_id"),
            models.Index(fields=["exam_id", "teacher_id"], name="idx_inv_exam_teacher"),
        ]

    def __str__(self):
        return f"{self.teacher.name} ({self.get_role_display()}) — {self.exam.name}"


class ExamConflict(models.Model):
    """考试冲突检测"""

    class ConflictTypeChoices(models.TextChoices):
        TIME = "time", "时间冲突"
        ROOM = "room", "考场冲突"
        TEACHER = "teacher", "教师冲突"
        STUDENT = "student", "学生冲突"

    class SeverityChoices(models.TextChoices):
        ERROR = "error", "严重冲突"
        WARNING = "warning", "一般冲突"
        INFO = "info", "提示冲突"

    class StatusChoices(models.TextChoices):
        ACTIVE = "active", "未处理"
        RESOLVED = "resolved", "已解决"
        IGNORED = "ignored", "已忽略"

    conflict_type = models.CharField(
        max_length=16,
        choices=ConflictTypeChoices.choices,
        verbose_name="冲突类型",
    )
    severity = models.CharField(
        max_length=16,
        choices=SeverityChoices.choices,
        default=SeverityChoices.WARNING,
        verbose_name="严重程度",
    )
    status = models.CharField(
        max_length=16,
        choices=StatusChoices.choices,
        default=StatusChoices.ACTIVE,
        verbose_name="状态",
    )
    exam_a = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name="conflicts_as_a",
        verbose_name="考试 A",
    )
    exam_b = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name="conflicts_as_b",
        verbose_name="考试 B",
    )
    description = models.TextField(
        blank=True,
        default="",
        verbose_name="冲突描述",
    )
    resolution_note = models.TextField(
        blank=True,
        default="",
        verbose_name="解决备注",
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
        db_table = "exam_conflicts"
        verbose_name = "考试冲突"
        verbose_name_plural = verbose_name
        ordering = ["-severity", "-created_at"]
        indexes = [
            models.Index(fields=["exam_a_id"], name="idx_conf_exam_a_id"),
            models.Index(fields=["exam_b_id"], name="idx_conf_exam_b_id"),
            models.Index(fields=["conflict_type"], name="idx_conf_type"),
            models.Index(fields=["severity"], name="idx_conf_severity"),
            models.Index(fields=["status"], name="idx_conf_status"),
        ]

    def __str__(self):
        return f"[{self.get_conflict_type_display()}] {self.exam_a.name} ↔ {self.exam_b.name}"