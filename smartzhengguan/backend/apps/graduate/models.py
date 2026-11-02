from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class DegreeType(models.TextChoices):
    ACADEMIC_MASTER = "academic_master", "Academic Master"
    PROFESSIONAL_MASTER = "professional_master", "Professional Master"
    DOCTORAL = "doctoral", "Doctoral"


class EnrollmentType(models.TextChoices):
    MASTER = "master", "Master"
    DOCTORAL = "doctoral", "Doctoral"
    INTERNATIONAL = "international", "International Student"


class StudentStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    SUSPENDED = "suspended", "Suspended"
    WITHDRAWN = "withdrawn", "Withdrawn"
    EXTENDED = "extended", "Extended Graduation"
    OTHER = "other", "Other"


class WorkflowStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PENDING = "pending", "Pending Review"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"
    IN_PROGRESS = "in_progress", "In Progress"
    COMPLETED = "completed", "Completed"


class RiskLevel(models.TextChoices):
    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"
    ALERT = "alert", "Alert"


class ModuleCode(models.TextChoices):
    HOME = "home", "Home"
    ADMISSION = "admission", "Admission"
    ACADEMIC_STATUS = "academic_status", "Academic Status"
    ACADEMIC_CHANGE = "academic_change", "Academic Change"
    TRAINING = "training", "Training"
    TRAINING_COURSE = "training_course", "Training Course"
    DEGREE = "degree", "Degree"
    DEGREE_DEFENSE = "degree_defense", "Degree Defense"
    SCHOLARSHIP = "scholarship", "Scholarship"
    EMPLOYMENT = "employment", "Employment"
    INTELLIGENT_PREDICTION = "intelligent_prediction", "Intelligent Prediction"


class Student(TimestampedModel):
    student_id = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=100)
    gender = models.CharField(max_length=20, blank=True)
    college = models.CharField(max_length=150, blank=True)
    major = models.CharField(max_length=150)
    grade = models.CharField(max_length=20)
    degree_type = models.CharField(max_length=32, choices=DegreeType.choices)
    enrollment_type = models.CharField(
        max_length=32,
        choices=EnrollmentType.choices,
        default=EnrollmentType.MASTER,
    )
    source_region = models.CharField(max_length=100, blank=True)
    advisor_name = models.CharField(max_length=100, blank=True)
    current_status = models.CharField(
        max_length=32,
        choices=StudentStatus.choices,
        default=StudentStatus.ACTIVE,
    )
    is_international = models.BooleanField(default=False)
    expected_graduation_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["student_id"]

    def __str__(self) -> str:
        return f"{self.student_id} {self.name}"


class HomeAnnualSummary(TimestampedModel):
    year = models.PositiveIntegerField(unique=True)
    total_students = models.PositiveIntegerField(default=0)
    master_count = models.PositiveIntegerField(default=0)
    doctor_count = models.PositiveIntegerField(default=0)
    international_count = models.PositiveIntegerField(default=0)
    annual_graduates = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["year"]

    def __str__(self) -> str:
        return str(self.year)


class HomeGradeMajorSummary(TimestampedModel):
    grade = models.CharField(max_length=20)
    major = models.CharField(max_length=150)
    total_count = models.PositiveIntegerField(default=0)
    male_count = models.PositiveIntegerField(default=0)
    female_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["grade", "major"]

    def __str__(self) -> str:
        return f"{self.grade} {self.major}"


class HomeSourceRegionSummary(TimestampedModel):
    region = models.CharField(max_length=100, unique=True)
    student_count = models.PositiveIntegerField(default=0)
    percent_text = models.CharField(max_length=20, blank=True)

    class Meta:
        ordering = ["-student_count", "region"]

    def __str__(self) -> str:
        return self.region


class ModuleNotice(TimestampedModel):
    module = models.CharField(max_length=40, choices=ModuleCode.choices)
    title = models.CharField(max_length=255)
    notice_date = models.DateField()
    is_read = models.BooleanField(default=False)
    content = models.TextField(blank=True)
    url = models.URLField(max_length=500, blank=True, default="")

    class Meta:
        ordering = ["-notice_date", "-id"]

    def __str__(self) -> str:
        return self.title


class AdmissionCycle(TimestampedModel):
    year = models.PositiveIntegerField()
    enrollment_type = models.CharField(max_length=32, choices=EnrollmentType.choices)
    direction = models.CharField(max_length=150)
    source_category = models.CharField(max_length=100, blank=True)
    applicant_count = models.PositiveIntegerField(default=0)
    initial_review_pass_count = models.PositiveIntegerField(default=0)
    retest_count = models.PositiveIntegerField(default=0)
    proposed_admission_count = models.PositiveIntegerField(default=0)
    actual_admission_count = models.PositiveIntegerField(default=0)
    admission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        ordering = ["-year", "direction"]

    def __str__(self) -> str:
        return f"{self.year} {self.direction}"


class AdmissionStageProgress(TimestampedModel):
    cycle = models.ForeignKey(
        AdmissionCycle,
        related_name="stages",
        on_delete=models.CASCADE,
    )
    stage_name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=32, choices=WorkflowStatus.choices)
    completion_percent = models.PositiveSmallIntegerField(default=0)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["cycle", "sort_order", "id"]

    def __str__(self) -> str:
        return f"{self.cycle} {self.stage_name}"


class AcademicStatusEvent(TimestampedModel):
    external_id = models.CharField(max_length=32, unique=True)
    student = models.ForeignKey(
        Student,
        related_name="academic_status_events",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    student_name = models.CharField(max_length=100)
    change_type = models.CharField(max_length=100)
    handler_name = models.CharField(max_length=100, blank=True)
    reason = models.CharField(max_length=255, blank=True)
    occurred_on = models.DateField()
    status = models.CharField(max_length=32, choices=WorkflowStatus.choices)
    status_tag = models.CharField(max_length=20, blank=True)

    class Meta:
        ordering = ["-occurred_on", "-id"]

    def __str__(self) -> str:
        return self.external_id


class AcademicChangeRequest(TimestampedModel):
    student = models.ForeignKey(
        Student,
        related_name="academic_change_requests",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    student_name = models.CharField(max_length=100)
    change_type = models.CharField(max_length=100)
    current_step = models.CharField(max_length=100)
    status = models.CharField(max_length=32, choices=WorkflowStatus.choices)
    status_type = models.CharField(max_length=20, blank=True)
    submitted_at = models.DateTimeField()
    reviewed_at = models.DateTimeField(null=True, blank=True)
    remark = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-submitted_at", "-id"]

    def __str__(self) -> str:
        return f"{self.student_name} {self.change_type}"


class TrainingPlan(TimestampedModel):
    student = models.ForeignKey(
        Student,
        related_name="training_plans",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    student_name = models.CharField(max_length=100)
    grade = models.CharField(max_length=20)
    major = models.CharField(max_length=150)
    degree_type = models.CharField(max_length=32, choices=DegreeType.choices)
    stage = models.CharField(max_length=100)
    advisor_name = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=32, choices=WorkflowStatus.choices)
    status_tag = models.CharField(max_length=20, blank=True)
    completion_percent = models.PositiveSmallIntegerField(default=0)
    business_updated_at = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["grade", "student_name"]

    def __str__(self) -> str:
        return f"{self.student_name} training plan"


class CourseOffering(TimestampedModel):
    course_name = models.CharField(max_length=150)
    teacher_name = models.CharField(max_length=100)
    major = models.CharField(max_length=150)
    schedule_text = models.CharField(max_length=150)
    status = models.CharField(max_length=32, choices=WorkflowStatus.choices)
    status_type = models.CharField(max_length=20, blank=True)
    term = models.CharField(max_length=50, blank=True)

    class Meta:
        ordering = ["major", "course_name"]

    def __str__(self) -> str:
        return self.course_name


class DegreeApplication(TimestampedModel):
    student = models.ForeignKey(
        Student,
        related_name="degree_applications",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    student_name = models.CharField(max_length=100, blank=True)
    application_year = models.PositiveIntegerField()
    application_type = models.CharField(max_length=50)
    discipline = models.CharField(max_length=150)
    paper_submitted_at = models.DateField(null=True, blank=True)
    paper_review_result = models.CharField(max_length=50, blank=True)
    defense_result = models.CharField(max_length=50, blank=True)
    award_status = models.CharField(max_length=32, choices=WorkflowStatus.choices)
    awarded_at = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-application_year", "discipline"]

    def __str__(self) -> str:
        return f"{self.application_year} {self.application_type}"


class DefenseSession(TimestampedModel):
    session_name = models.CharField(max_length=150)
    chair_name = models.CharField(max_length=100)
    room = models.CharField(max_length=100)
    student_count = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=32, choices=WorkflowStatus.choices)
    status_type = models.CharField(max_length=20, blank=True)
    scheduled_at = models.DateTimeField()

    class Meta:
        ordering = ["scheduled_at", "session_name"]

    def __str__(self) -> str:
        return self.session_name


class ScholarshipAward(TimestampedModel):
    student = models.ForeignKey(
        Student,
        related_name="scholarship_awards",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    student_name = models.CharField(max_length=100, blank=True)
    award_year = models.PositiveIntegerField()
    grade = models.CharField(max_length=20)
    major = models.CharField(max_length=150)
    award_category = models.CharField(max_length=30)
    award_type = models.CharField(max_length=100)
    award_name = models.CharField(max_length=150)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    awarded_on = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-award_year", "award_type", "student_name"]

    def __str__(self) -> str:
        return self.award_name


class EmploymentRecord(TimestampedModel):
    student = models.ForeignKey(
        Student,
        related_name="employment_records",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    student_name = models.CharField(max_length=100, blank=True)
    graduation_year = models.PositiveIntegerField()
    destination_type = models.CharField(max_length=100)
    unit_nature = models.CharField(max_length=100, blank=True)
    industry = models.CharField(max_length=100, blank=True)
    province = models.CharField(max_length=100, blank=True)
    employer_name = models.CharField(max_length=150, blank=True)
    is_signed = models.BooleanField(default=False)
    is_further_study = models.BooleanField(default=False)
    status = models.CharField(max_length=32, choices=WorkflowStatus.choices)

    class Meta:
        ordering = ["-graduation_year", "student_name"]

    def __str__(self) -> str:
        return f"{self.graduation_year} {self.student_name}"


class PredictionIndicatorDefinition(TimestampedModel):
    name = models.CharField(max_length=100, unique=True)
    max_score = models.PositiveIntegerField(default=100)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self) -> str:
        return self.name


class PredictionSnapshot(TimestampedModel):
    student = models.ForeignKey(
        Student,
        related_name="prediction_snapshots",
        on_delete=models.CASCADE,
    )
    sample_range = models.CharField(max_length=50, blank=True)
    risk_level = models.CharField(max_length=16, choices=RiskLevel.choices)
    risk_type = models.CharField(max_length=50, blank=True)
    risk_field = models.CharField(max_length=150, blank=True)
    suggestion = models.CharField(max_length=255, blank=True)
    course_average = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    credit_completion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    attendance_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    research_task_completion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    research_output_count = models.PositiveIntegerField(default=0)
    project_participation_count = models.PositiveIntegerField(default=0)
    activity_hours = models.PositiveIntegerField(default=0)
    activity_count = models.PositiveIntegerField(default=0)
    practice_hours = models.PositiveIntegerField(default=0)
    practice_report_count = models.PositiveIntegerField(default=0)
    advisor_evaluation_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    advisor_meeting_count_60d = models.PositiveIntegerField(default=0)
    advisor_avg_response_days = models.PositiveIntegerField(default=0)
    missed_checkins = models.PositiveIntegerField(default=0)
    wellbeing_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    training_plan_completion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    graduation_progress_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    overdue_tasks_count = models.PositiveIntegerField(default=0)
    captured_at = models.DateTimeField()

    class Meta:
        ordering = ["-captured_at", "student__student_id"]

    def __str__(self) -> str:
        return f"{self.student} prediction snapshot"


class PredictionMonthlyMetric(TimestampedModel):
    snapshot = models.ForeignKey(
        PredictionSnapshot,
        related_name="monthly_metrics",
        on_delete=models.CASCADE,
    )
    month = models.CharField(max_length=7)
    course_average = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    credit_completion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    attendance_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    research_task_completion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    activity_hours = models.PositiveIntegerField(default=0)
    practice_hours = models.PositiveIntegerField(default=0)
    advisor_meeting_count = models.PositiveIntegerField(default=0)
    advisor_evaluation_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    wellbeing_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        ordering = ["snapshot", "month"]
        unique_together = ("snapshot", "month")

    def __str__(self) -> str:
        return f"{self.snapshot.student.student_id} {self.month}"


# ============================================================
# R05: Data Upload, Recognition & Import Models
# ============================================================

class ImportBatchStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PARSING = "parsing", "Parsing"
    MAPPING = "mapping", "Mapping"
    VALIDATING = "validating", "Validating"
    PREVIEWING = "previewing", "Previewing"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"
    CANCELLED = "cancelled", "Cancelled"


class ImportBatch(TimestampedModel):
    batch_id = models.CharField(max_length=64, unique=True)
    file_name = models.CharField(max_length=255)
    file_hash = models.CharField(max_length=64)
    status = models.CharField(
        max_length=32,
        choices=ImportBatchStatus.choices,
        default=ImportBatchStatus.DRAFT,
    )
    operator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="import_batches",
    )
    total_rows = models.PositiveIntegerField(default=0)
    new_count = models.PositiveIntegerField(default=0)
    update_count = models.PositiveIntegerField(default=0)
    unchanged_count = models.PositiveIntegerField(default=0)
    error_count = models.PositiveIntegerField(default=0)
    skipped_count = models.PositiveIntegerField(default=0)
    error_summary = models.TextField(blank=True)
    source_module = models.CharField(max_length=40, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.batch_id} - {self.file_name}"


class ImportRecordAction(models.TextChoices):
    CREATE = "create", "Create"
    UPDATE = "update", "Update"
    SKIP = "skip", "Skip"
    ERROR = "error", "Error"


class ImportBatchRecord(TimestampedModel):
    batch = models.ForeignKey(
        ImportBatch,
        related_name="records",
        on_delete=models.CASCADE,
    )
    row_index = models.PositiveIntegerField()
    action = models.CharField(
        max_length=16,
        choices=ImportRecordAction.choices,
    )
    target_model = models.CharField(max_length=100)
    target_id = models.CharField(max_length=64, blank=True)
    before_value = models.JSONField(default=dict)
    after_value = models.JSONField(default=dict)
    errors = models.JSONField(default=list)
    is_reverted = models.BooleanField(default=False)

    class Meta:
        ordering = ["batch", "row_index"]

    def __str__(self) -> str:
        return f"{self.batch.batch_id} - Row {self.row_index}"


class ImportMappingTemplate(TimestampedModel):
    name = models.CharField(max_length=100)
    target_module = models.CharField(max_length=40)
    sheet_name = models.CharField(max_length=100, blank=True)
    header_signature = models.JSONField(default=list)
    mapping = models.JSONField(default=dict)
    is_public = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="import_templates",
    )
    version = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.name} (v{self.version})"


class FieldCatalog(TimestampedModel):
    module = models.CharField(max_length=40)
    field_code = models.CharField(max_length=100, unique=True)
    field_name_cn = models.CharField(max_length=100)
    data_type = models.CharField(max_length=20)
    data_granularity = models.CharField(max_length=20)
    is_sensitive = models.BooleanField(default=False)
    is_filterable = models.BooleanField(default=False)
    is_exportable = models.BooleanField(default=True)
    is_aggregatable = models.BooleanField(default=False)
    dict_items = models.JSONField(default=list)
    format_hint = models.CharField(max_length=100, blank=True)
    example = models.CharField(max_length=200, blank=True)
    aliases = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["module", "field_code"]

    def __str__(self) -> str:
        return f"{self.field_code} - {self.field_name_cn}"


# ============================================================
# R06: Export Models
# ============================================================

class ExportTemplate(TimestampedModel):
    name = models.CharField(max_length=100)
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="export_templates",
    )
    is_public = models.BooleanField(default=False)
    version = models.PositiveIntegerField(default=1)
    fields = models.JSONField(default=list)
    filters = models.JSONField(default=dict)
    field_aliases = models.JSONField(default=dict)
    one_to_many_strategy = models.JSONField(default=dict)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.name} (v{self.version})"


class ExportRecordStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"
    EXPIRED = "expired", "Expired"


class ExportType(models.TextChoices):
    STUDENT_LIST = "student_list", "Student List"
    SUMMARY_TABLE = "summary_table", "Summary Table"


class ExportRecord(TimestampedModel):
    record_id = models.CharField(max_length=64, unique=True)
    operator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="export_records",
    )
    export_type = models.CharField(
        max_length=32,
        choices=ExportType.choices,
        default=ExportType.STUDENT_LIST,
    )
    filters = models.JSONField(default=dict)
    fields = models.JSONField(default=list)
    row_count = models.PositiveIntegerField(default=0)
    file_path = models.CharField(max_length=500, blank=True)
    file_name = models.CharField(max_length=255)
    status = models.CharField(
        max_length=32,
        choices=ExportRecordStatus.choices,
        default=ExportRecordStatus.PENDING,
    )
    error_message = models.TextField(blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.record_id} - {self.file_name}"


# ============================================================
# R07: Warning Rule Engine Models
# ============================================================

class WarningRule(TimestampedModel):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=64, unique=True)
    description = models.TextField(blank=True)
    target_module = models.CharField(max_length=40)
    indicator_field = models.CharField(max_length=100)
    operator = models.CharField(max_length=10)  # <, <=, >, >=, ==, !=, between, in
    threshold_value = models.JSONField()
    time_window_days = models.PositiveIntegerField(default=0)
    risk_level = models.CharField(max_length=16, choices=RiskLevel.choices)
    responsible_role = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=False)
    version = models.PositiveIntegerField(default=1)
    effective_from = models.DateField(null=True, blank=True)
    effective_to = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="warning_rules",
    )

    class Meta:
        ordering = ["-is_active", "risk_level", "name"]

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"


class WarningRuleVersion(TimestampedModel):
    rule = models.ForeignKey(
        WarningRule,
        related_name="versions",
        on_delete=models.CASCADE,
    )
    version = models.PositiveIntegerField()
    snapshot = models.JSONField()
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-version"]

    def __str__(self) -> str:
        return f"{self.rule.code} v{self.version}"


class WarningInstanceStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PROCESSING = "processing", "Processing"
    RESOLVED = "resolved", "Resolved"
    FALSE_ALARM = "false_alarm", "False Alarm"
    CLOSED = "closed", "Closed"


class WarningInstance(TimestampedModel):
    rule = models.ForeignKey(
        WarningRule,
        related_name="instances",
        on_delete=models.CASCADE,
    )
    rule_version = models.ForeignKey(
        WarningRuleVersion,
        related_name="instances",
        on_delete=models.CASCADE,
    )
    student = models.ForeignKey(
        Student,
        related_name="warnings",
        on_delete=models.CASCADE,
    )
    indicator_value = models.JSONField()
    threshold_at_hit = models.JSONField()
    data_time = models.DateTimeField()
    hit_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=32,
        choices=WarningInstanceStatus.choices,
        default=WarningInstanceStatus.PENDING,
    )
    assignee = models.ForeignKey(
        User,
        related_name="assigned_warnings",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    resolution_note = models.TextField(blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    attachments = models.JSONField(default=list)
    dedup_key = models.CharField(max_length=128, unique=True)

    class Meta:
        ordering = ["-hit_at"]

    def __str__(self) -> str:
        return f"{self.student.student_id} - {self.rule.name}"


class WarningTreatmentLog(TimestampedModel):
    warning = models.ForeignKey(
        WarningInstance,
        related_name="treatment_logs",
        on_delete=models.CASCADE,
    )
    operator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    action = models.CharField(max_length=50)  # assign / start / resolve / mark_false_alarm / close / reopen
    note = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.warning.id} - {self.action}"
