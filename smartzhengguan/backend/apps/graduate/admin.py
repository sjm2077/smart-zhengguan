from django.contrib import admin

from apps.graduate import models


@admin.register(models.Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("student_id", "name", "major", "grade", "degree_type", "current_status")
    search_fields = ("student_id", "name", "major")
    list_filter = ("grade", "degree_type", "current_status")


@admin.register(models.ModuleNotice)
class ModuleNoticeAdmin(admin.ModelAdmin):
    list_display = ("title", "module", "notice_date", "is_read")
    list_filter = ("module", "is_read")
    search_fields = ("title",)


@admin.register(models.AdmissionCycle)
class AdmissionCycleAdmin(admin.ModelAdmin):
    list_display = (
        "year",
        "enrollment_type",
        "direction",
        "applicant_count",
        "proposed_admission_count",
        "actual_admission_count",
    )
    list_filter = ("year", "enrollment_type")
    search_fields = ("direction", "source_category")


@admin.register(models.AdmissionStageProgress)
class AdmissionStageProgressAdmin(admin.ModelAdmin):
    list_display = ("cycle", "stage_name", "start_date", "end_date", "status", "completion_percent")
    list_filter = ("status",)
    search_fields = ("stage_name",)


@admin.register(models.AcademicStatusEvent)
class AcademicStatusEventAdmin(admin.ModelAdmin):
    list_display = ("external_id", "student_name", "change_type", "handler_name", "occurred_on", "status")
    list_filter = ("change_type", "status")
    search_fields = ("external_id", "student_name", "reason")


@admin.register(models.AcademicChangeRequest)
class AcademicChangeRequestAdmin(admin.ModelAdmin):
    list_display = ("student_name", "change_type", "current_step", "status", "submitted_at")
    list_filter = ("change_type", "status")
    search_fields = ("student_name", "remark")


@admin.register(models.TrainingPlan)
class TrainingPlanAdmin(admin.ModelAdmin):
    list_display = (
        "student_name",
        "grade",
        "major",
        "stage",
        "advisor_name",
        "status",
        "completion_percent",
    )
    list_filter = ("grade", "major", "stage", "status")
    search_fields = ("student_name", "student__student_id", "advisor_name")


@admin.register(models.CourseOffering)
class CourseOfferingAdmin(admin.ModelAdmin):
    list_display = ("course_name", "teacher_name", "major", "schedule_text", "status")
    list_filter = ("major", "status")
    search_fields = ("course_name", "teacher_name")


@admin.register(models.DegreeApplication)
class DegreeApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "application_year",
        "student_name",
        "application_type",
        "discipline",
        "paper_review_result",
        "defense_result",
        "award_status",
    )
    list_filter = ("application_year", "application_type", "award_status")
    search_fields = ("student_name", "discipline")


@admin.register(models.DefenseSession)
class DefenseSessionAdmin(admin.ModelAdmin):
    list_display = ("session_name", "chair_name", "room", "student_count", "status", "scheduled_at")
    list_filter = ("status",)
    search_fields = ("session_name", "chair_name", "room")


@admin.register(models.ScholarshipAward)
class ScholarshipAwardAdmin(admin.ModelAdmin):
    list_display = (
        "award_year",
        "student_name",
        "award_category",
        "award_type",
        "award_name",
        "amount",
    )
    list_filter = ("award_year", "award_category", "award_type")
    search_fields = ("student_name", "award_name", "major")


@admin.register(models.EmploymentRecord)
class EmploymentRecordAdmin(admin.ModelAdmin):
    list_display = (
        "graduation_year",
        "student_name",
        "destination_type",
        "unit_nature",
        "province",
        "is_signed",
        "is_further_study",
        "status",
    )
    list_filter = ("graduation_year", "destination_type", "is_signed", "is_further_study", "status")
    search_fields = ("student_name", "industry", "employer_name", "province")


@admin.register(models.PredictionIndicatorDefinition)
class PredictionIndicatorDefinitionAdmin(admin.ModelAdmin):
    list_display = ("name", "max_score", "sort_order")
    ordering = ("sort_order", "id")


class PredictionMonthlyMetricInline(admin.TabularInline):
    model = models.PredictionMonthlyMetric
    extra = 0


@admin.register(models.PredictionSnapshot)
class PredictionSnapshotAdmin(admin.ModelAdmin):
    list_display = ("student", "risk_level", "risk_type", "captured_at", "graduation_progress_rate")
    list_filter = ("risk_level", "risk_type")
    search_fields = ("student__student_id", "student__name", "risk_field", "suggestion")
    inlines = [PredictionMonthlyMetricInline]
