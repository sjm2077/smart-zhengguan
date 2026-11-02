import json
import re
import subprocess
from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.graduate.models import (
    AcademicChangeRequest,
    AcademicStatusEvent,
    AdmissionCycle,
    AdmissionStageProgress,
    CourseOffering,
    DefenseSession,
    DegreeApplication,
    DegreeType,
    EmploymentRecord,
    EnrollmentType,
    ModuleCode,
    ModuleNotice,
    PredictionIndicatorDefinition,
    PredictionMonthlyMetric,
    PredictionSnapshot,
    RiskLevel,
    ScholarshipAward,
    Student,
    StudentStatus,
    TrainingPlan,
    WorkflowStatus,
)


class Command(BaseCommand):
    help = "Load graduate business demo data from src/mock/graduateManagementMock.js"

    def add_arguments(self, parser):
        parser.add_argument(
            "--keep-existing",
            action="store_true",
            help="Append data instead of clearing existing graduate business data first.",
        )

    def handle(self, *args, **options):
        payload = load_mock_payload()

        with transaction.atomic():
            if not options["keep_existing"]:
                clear_existing_data()

            context = SeedContext(payload)
            context.seed_all()

        self.stdout.write(self.style.SUCCESS("Graduate mock data imported successfully."))
        for label, count in context.summary_lines():
            self.stdout.write(f"{label}: {count}")


class SeedContext:
    def __init__(self, payload: dict):
        self.payload = payload
        self.students_by_student_id: dict[str, Student] = {}
        self.students_by_name: dict[str, Student] = {}
        self.created_counts = {
            "students": 0,
            "notices": 0,
            "admission_cycles": 0,
            "admission_stages": 0,
            "academic_status_events": 0,
            "academic_change_requests": 0,
            "training_plans": 0,
            "course_offerings": 0,
            "degree_applications": 0,
            "defense_sessions": 0,
            "scholarship_awards": 0,
            "employment_records": 0,
            "prediction_indicators": 0,
            "prediction_snapshots": 0,
            "prediction_monthly_metrics": 0,
        }

    def seed_all(self):
        self.seed_students()
        self.seed_notices()
        self.seed_admission()
        self.seed_academic_status()
        self.seed_academic_change()
        self.seed_training()
        self.seed_training_courses()
        self.seed_degree()
        self.seed_degree_defense()
        self.seed_scholarships()
        self.seed_employment()
        self.seed_predictions()

    def summary_lines(self):
        return [
            ("students", self.created_counts["students"]),
            ("notices", self.created_counts["notices"]),
            ("admission cycles", self.created_counts["admission_cycles"]),
            ("admission stages", self.created_counts["admission_stages"]),
            ("academic status events", self.created_counts["academic_status_events"]),
            ("academic change requests", self.created_counts["academic_change_requests"]),
            ("training plans", self.created_counts["training_plans"]),
            ("course offerings", self.created_counts["course_offerings"]),
            ("degree applications", self.created_counts["degree_applications"]),
            ("defense sessions", self.created_counts["defense_sessions"]),
            ("scholarship awards", self.created_counts["scholarship_awards"]),
            ("employment records", self.created_counts["employment_records"]),
            ("prediction indicators", self.created_counts["prediction_indicators"]),
            ("prediction snapshots", self.created_counts["prediction_snapshots"]),
            ("prediction monthly metrics", self.created_counts["prediction_monthly_metrics"]),
        ]

    def seed_students(self):
        training = self.payload["training"]
        for plan in training["plans"]:
            student = self.upsert_student(
                student_id=plan["studentId"],
                name=plan["name"],
                major=plan["major"],
                grade=plan["grade"],
                degree_type=map_degree_type(plan.get("degreeType")),
                advisor_name=plan.get("advisor") or "",
                enrollment_type=map_enrollment_type(plan.get("degreeType")),
            )
            self.students_by_student_id[student.student_id] = student
            self.students_by_name[student.name] = student

        prediction = self.payload["intelligentPrediction"]
        for item in prediction["students"]:
            student = self.upsert_student(
                student_id=item["studentId"],
                name=item["name"],
                major=item["major"],
                grade=item["grade"],
                degree_type=map_degree_type(item.get("degreeType")),
                college=item.get("college") or "",
                enrollment_type=map_enrollment_type(item.get("degreeType")),
            )
            self.students_by_student_id[student.student_id] = student
            self.students_by_name[student.name] = student

        for row in self.payload["academicChange"]["tableCard"]["rows"]:
            self.upsert_student(
                student_id=row["studentId"],
                name=row["name"],
                major="待补充专业",
                grade=grade_from_student_id(row["studentId"]),
                degree_type=DegreeType.ACADEMIC_MASTER,
            )

        self.enrich_students()

    def enrich_students(self):
        students = list(Student.objects.order_by("student_id"))
        if not students:
            return

        source_regions = [item["name"] for item in self.payload["home"]["charts"]["sourceRegions"]]
        active_count = max(len(students) - 3, 1)

        for index, student in enumerate(students):
            student.gender = "男" if index % 5 in (0, 1, 2) else "女"
            student.source_region = source_regions[index % len(source_regions)] if source_regions else ""
            if index < active_count:
                student.current_status = StudentStatus.ACTIVE
            elif index == active_count:
                student.current_status = StudentStatus.SUSPENDED
            elif index == active_count + 1:
                student.current_status = StudentStatus.WITHDRAWN
            else:
                student.current_status = StudentStatus.OTHER
            student.save(update_fields=["gender", "source_region", "current_status"])

    def seed_notices(self):
        module_to_items = {
            ModuleCode.HOME: self.payload["home"].get("notices", []),
            ModuleCode.ADMISSION: self.payload["admission"].get("notices", []),
            ModuleCode.TRAINING: self.payload["training"].get("notices", []),
            ModuleCode.DEGREE: self.payload["degree"].get("notices", []),
            ModuleCode.SCHOLARSHIP: self.payload["scholarship"].get("notices", []),
            ModuleCode.ACADEMIC_CHANGE: self.payload["academicChange"]["noticeCard"]["items"],
            ModuleCode.TRAINING_COURSE: self.payload["trainingCourse"]["noticeCard"]["items"],
            ModuleCode.DEGREE_DEFENSE: self.payload["degreeDefense"]["noticeCard"]["items"],
            ModuleCode.INTELLIGENT_PREDICTION: self.payload["intelligentPrediction"]["noticeCard"]["items"],
        }

        for module_code, items in module_to_items.items():
            for item in items:
                ModuleNotice.objects.create(
                    module=module_code,
                    title=item["title"],
                    notice_date=parse_date(
                        item["date"],
                        fallback_year=infer_year_from_payload(self.payload, module_code),
                        fallback_date=infer_date_from_payload(self.payload, module_code),
                    ),
                    is_read=bool(item.get("read", False)),
                    content="",
                    url=item.get("url", ""),
                )
                self.created_counts["notices"] += 1

    def seed_admission(self):
        admission = self.payload["admission"]
        defaults = admission["filters"]["default"]
        major_top = admission["charts"]["majorTop"]
        apply_trend = admission["charts"]["applyTrend"]
        source_names = [item["name"] for item in admission["charts"]["sourceDistribution"]]
        total_weight = sum(item["value"] for item in major_top) or 1

        progress_cycle = None
        for year_item in apply_trend:
            year = int(year_item["year"])
            yearly_total = to_int(year_item["value"])
            assigned = 0

            for index, major_item in enumerate(major_top):
                weight = major_item["value"] / total_weight
                applicant_count = max(1, round(yearly_total * weight))
                assigned += applicant_count
                if index == len(major_top) - 1:
                    applicant_count += yearly_total - assigned

                initial_review = max(1, round(applicant_count * 0.65))
                retest_count = max(1, round(applicant_count * 0.26))
                proposed_count = max(1, round(applicant_count * 0.18))
                actual_count = max(1, round(proposed_count * 0.92))

                cycle = AdmissionCycle.objects.create(
                    year=year,
                    enrollment_type=map_enrollment_type(defaults["type"]),
                    direction=major_item["name"],
                    source_category=source_names[index % len(source_names)] if source_names else defaults["source"],
                    applicant_count=applicant_count,
                    initial_review_pass_count=initial_review,
                    retest_count=retest_count,
                    proposed_admission_count=proposed_count,
                    actual_admission_count=actual_count,
                    admission_rate=Decimal(actual_count * 100 / applicant_count).quantize(Decimal("0.01")),
                )
                self.created_counts["admission_cycles"] += 1
                if year == int(defaults["year"]) and index == 0:
                    progress_cycle = cycle

        if progress_cycle is not None:
            for index, stage in enumerate(admission["progress"], start=1):
                stage_obj = AdmissionStageProgress.objects.create(
                    cycle=progress_cycle,
                    stage_name=stage["stage"],
                    start_date=parse_date(stage["startTime"]),
                    end_date=parse_date(stage["endTime"]),
                    status=map_workflow_status(stage.get("status"), completion_percent=stage.get("completionPercent", 0)),
                    completion_percent=to_int(stage.get("completionPercent", 0)),
                    sort_order=index,
                )
                set_timestamps(stage_obj, parse_datetime(f"{stage['startTime']} 09:00"))
                self.created_counts["admission_stages"] += 1

    def seed_academic_status(self):
        payload_records = self.payload["academicStatus"]["records"]
        created_by_year = Counter()
        for record in payload_records:
            AcademicStatusEvent.objects.create(
                external_id=record["id"],
                student=self.students_by_name.get(record["name"]),
                student_name=record["name"],
                change_type=record["changeType"],
                handler_name=record.get("handler") or "",
                reason=record.get("reason") or "",
                occurred_on=parse_date(record["date"]),
                status=map_workflow_status(record.get("status"), status_type=record.get("tagType")),
                status_tag=record.get("tagType", ""),
            )
            created_by_year[str(parse_date(record["date"]).year)] += 1
            self.created_counts["academic_status_events"] += 1

        students = list(Student.objects.order_by("student_id"))
        template_records = payload_records or []
        for trend in self.payload["academicStatus"]["charts"]["changeTrend"]:
            year = str(trend["year"])
            target_count = to_int(trend["count"])
            existing = created_by_year.get(year, 0)
            for index in range(existing, target_count):
                student = students[index % len(students)] if students else None
                template = template_records[index % len(template_records)] if template_records else {}
                event = AcademicStatusEvent.objects.create(
                    external_id=f"{year}{index + 1:04d}",
                    student=student,
                    student_name=student.name if student else template.get("name", f"学生{index + 1}"),
                    change_type=template.get("changeType", "学籍异动"),
                    handler_name=template.get("handler", "教务老师"),
                    reason=template.get("reason", "业务演示数据补充"),
                    occurred_on=date(int(year), (index % 12) + 1, min(28, (index % 20) + 1)),
                    status=WorkflowStatus.COMPLETED if index % 3 else WorkflowStatus.IN_PROGRESS,
                    status_tag="success" if index % 3 else "warning",
                )
                set_timestamps(event, make_aware_noon(event.occurred_on))
                self.created_counts["academic_status_events"] += 1

    def seed_academic_change(self):
        default_year = infer_year_from_payload(self.payload, ModuleCode.ACADEMIC_CHANGE)
        anchor_date = infer_date_from_payload(self.payload, ModuleCode.ACADEMIC_CHANGE)
        base_rows = self.payload["academicChange"]["tableCard"]["rows"]
        labels = self.payload["academicChange"]["trendChart"]["labels"]
        students = list(Student.objects.order_by("student_id"))

        for index, label in enumerate(labels):
            row = base_rows[index % len(base_rows)]
            submitted_at = parse_month_label(
                label,
                day=10,
                fallback_year=default_year,
                anchor_date=anchor_date,
                hour=9,
            )
            request = AcademicChangeRequest.objects.create(
                student=self.students_by_student_id.get(row["studentId"]) or students[index % len(students)],
                student_name=row["name"],
                change_type=row["changeType"],
                current_step=row["currentStep"],
                status=map_workflow_status(row.get("status"), status_type=row.get("statusType")),
                status_type=row.get("statusType", ""),
                submitted_at=submitted_at,
                reviewed_at=None,
                remark="",
            )
            set_timestamps(request, submitted_at)
            self.created_counts["academic_change_requests"] += 1

    def seed_training(self):
        for plan in self.payload["training"]["plans"]:
            TrainingPlan.objects.create(
                student=self.students_by_student_id.get(plan["studentId"]),
                student_name=plan["name"],
                grade=plan["grade"],
                major=plan["major"],
                degree_type=map_degree_type(plan.get("degreeType")),
                stage=plan["stage"],
                advisor_name=plan.get("advisor") or "",
                status=map_workflow_status(plan.get("status"), status_type=plan.get("tagType")),
                status_tag=plan.get("tagType", ""),
                completion_percent=to_int(plan.get("completion", 0)),
                business_updated_at=parse_date(plan["updatedAt"]),
            )
            self.created_counts["training_plans"] += 1

    def seed_training_courses(self):
        default_term = self.payload["trainingCourse"].get("updatedAt", "")[:4] + " Spring"
        anchor_date = infer_date_from_payload(self.payload, ModuleCode.TRAINING_COURSE)
        labels = self.payload["trainingCourse"]["trendChart"]["labels"]
        rows = self.payload["trainingCourse"]["tableCard"]["rows"]
        for index, label in enumerate(labels):
            row = rows[index % len(rows)]
            course = CourseOffering.objects.create(
                course_name=row["courseName"],
                teacher_name=row["teacher"],
                major=row["major"],
                schedule_text=row["schedule"],
                status=map_workflow_status(row.get("status"), status_type=row.get("statusType")),
                status_type=row.get("statusType", ""),
                term=default_term,
            )
            set_timestamps(
                course,
                parse_month_label(label, day=12, fallback_year=extract_year(default_term), anchor_date=anchor_date),
            )
            self.created_counts["course_offerings"] += 1

    def seed_degree(self):
        degree = self.payload["degree"]
        application_types = [item["name"] for item in degree["charts"]["applicationTypes"]]
        disciplines = degree["charts"]["disciplineDistribution"]
        paper_results = [item["name"] for item in degree["charts"]["paperReview"]]
        defense_results = [item["name"] for item in degree["charts"]["defenseResults"]]
        students = list(self.students_by_student_id.values()) or list(Student.objects.all())
        application_trend = degree["charts"]["applicationTrend"]

        for year_index, trend in enumerate(application_trend):
            year = int(trend["year"])
            count = max(2, round(to_int(trend["count"]) / 25))
            for index in range(count):
                student = students[(year_index + index) % len(students)] if students else None
                discipline = disciplines[(year_index + index) % len(disciplines)]["name"]
                application = DegreeApplication.objects.create(
                    student=student,
                    student_name=student.name if student else "",
                    application_year=year,
                    application_type=application_types[(year_index + index) % len(application_types)],
                    discipline=discipline,
                    paper_submitted_at=date(year, 5, min(28, 10 + index)),
                    paper_review_result=paper_results[(year_index + index) % len(paper_results)],
                    defense_result=defense_results[(year_index + index) % len(defense_results)],
                    award_status=WorkflowStatus.COMPLETED if index % 4 else WorkflowStatus.PENDING,
                    awarded_at=date(year, 6, min(28, 5 + index)),
                )
                set_timestamps(application, make_aware_noon(date(year, 6, min(28, 5 + index))))
                self.created_counts["degree_applications"] += 1

    def seed_degree_defense(self):
        default_year = infer_year_from_payload(self.payload, ModuleCode.DEGREE_DEFENSE)
        anchor_date = infer_date_from_payload(self.payload, ModuleCode.DEGREE_DEFENSE)
        labels = self.payload["degreeDefense"]["trendChart"]["labels"]
        rows = self.payload["degreeDefense"]["tableCard"]["rows"]
        for index, label in enumerate(labels):
            row = rows[index % len(rows)]
            row_time = parse_datetime(row["time"], fallback_year=default_year)
            scheduled_at = parse_month_label(
                label,
                day=18,
                fallback_year=default_year,
                anchor_date=anchor_date,
                hour=timezone.localtime(row_time).hour,
                minute=timezone.localtime(row_time).minute,
            )
            session = DefenseSession.objects.create(
                session_name=row["sessionName"],
                chair_name=row["chair"],
                room=row["room"],
                student_count=to_int(row["students"]),
                status=map_workflow_status(row.get("status"), status_type=row.get("statusType")),
                status_type=row.get("statusType", ""),
                scheduled_at=scheduled_at,
            )
            set_timestamps(session, scheduled_at)
            self.created_counts["defense_sessions"] += 1

    def seed_scholarships(self):
        scholarship = self.payload["scholarship"]
        award_names = [item["name"] for item in scholarship["charts"]["scholarshipTypes"]]
        aid_names = [item["name"] for item in scholarship["charts"]["aidTypes"]]
        students = list(self.students_by_student_id.values()) or list(Student.objects.all())
        years = [int(item["year"]) for item in scholarship["charts"]["fundTrend"]]
        grades = [item["grade"] for item in scholarship["charts"]["gradeAwards"]]
        students_by_grade = defaultdict(list)
        for student in students:
            students_by_grade[student.grade].append(student)

        for year_index, award_year in enumerate(years):
            for grade_index, grade in enumerate(grades):
                grade_students = students_by_grade.get(grade) or students
                for type_index, raw_name in enumerate(award_names):
                    student = grade_students[(year_index + type_index) % len(grade_students)]
                    award = ScholarshipAward.objects.create(
                        student=student,
                        student_name=student.name,
                        award_year=award_year,
                        grade=grade,
                        major=student.major,
                        award_category="scholarship",
                        award_type=raw_name,
                        award_name=f"{raw_name}示范记录",
                        amount=Decimal("6000.00") + Decimal((year_index + grade_index + type_index) * 800),
                        awarded_on=date(award_year, 10, min(28, 3 + grade_index + type_index)),
                    )
                    set_timestamps(award, make_aware_noon(award.awarded_on))
                    self.created_counts["scholarship_awards"] += 1

                aid_student = grade_students[(year_index + grade_index) % len(grade_students)]
                aid_name = aid_names[(year_index + grade_index) % len(aid_names)]
                aid_award = ScholarshipAward.objects.create(
                    student=aid_student,
                    student_name=aid_student.name,
                    award_year=award_year,
                    grade=grade,
                    major=aid_student.major,
                    award_category="aid",
                    award_type=aid_name,
                    award_name=f"{aid_name}示范记录",
                    amount=Decimal("3000.00") + Decimal((year_index + grade_index) * 400),
                    awarded_on=date(award_year, 11, min(28, 5 + grade_index)),
                )
                set_timestamps(aid_award, make_aware_noon(aid_award.awarded_on))
                self.created_counts["scholarship_awards"] += 1

    def seed_employment(self):
        employment = self.payload["employment"]
        destination_types = [item["type"] for item in employment["charts"]["destinationStats"]]
        unit_natures = [item["name"] for item in employment["charts"]["unitNature"]]
        industries = [item["name"] for item in employment["charts"]["industryTop"]]
        provinces = [item["name"] for item in employment["charts"]["provinceDistribution"]]
        students = list(self.students_by_student_id.values()) or list(Student.objects.all())
        years = [int(item["year"]) for item in employment["metrics"][0]["series"]]

        for year_index, graduation_year in enumerate(years):
            for index, student in enumerate(students[:8], start=1):
                destination = destination_types[(year_index + index - 1) % len(destination_types)]
                record = EmploymentRecord.objects.create(
                    student=student,
                    student_name=student.name,
                    graduation_year=graduation_year,
                    destination_type=destination,
                    unit_nature=unit_natures[(year_index + index - 1) % len(unit_natures)],
                    industry=industries[(year_index + index - 1) % len(industries)],
                    province=provinces[(year_index + index - 1) % len(provinces)],
                    employer_name=f"示范单位{graduation_year}-{index}",
                    is_signed="签" in destination or "就业" in destination,
                    is_further_study="升学" in destination or "深造" in destination,
                    status=WorkflowStatus.COMPLETED,
                )
                set_timestamps(record, make_aware_noon(date(graduation_year, 6, min(28, 3 + index))))
                self.created_counts["employment_records"] += 1

    def seed_predictions(self):
        prediction = self.payload["intelligentPrediction"]
        risk_rows = {row["studentId"]: row for row in prediction["tableCard"]["rows"]}

        for index, indicator in enumerate(prediction["radarIndicators"], start=1):
            PredictionIndicatorDefinition.objects.create(
                name=indicator["name"],
                max_score=to_int(indicator.get("max", 100)),
                sort_order=index,
            )
            self.created_counts["prediction_indicators"] += 1

        captured_at = parse_datetime(prediction["updatedAt"])
        default_range = prediction["filters"]["default"]["range"]
        for item in prediction["students"]:
            student = self.students_by_student_id[item["studentId"]]
            risk_row = risk_rows.get(item["studentId"], {})
            snapshot = item["currentSnapshot"]
            prediction_snapshot = PredictionSnapshot.objects.create(
                student=student,
                sample_range=default_range,
                risk_level=map_risk_level(risk_row.get("riskLevel")),
                risk_type=risk_row.get("riskType", ""),
                risk_field=risk_row.get("riskField", ""),
                suggestion=risk_row.get("suggestion", ""),
                course_average=to_decimal(snapshot["courseAverage"]),
                credit_completion_rate=to_decimal(snapshot["creditCompletionRate"]),
                attendance_rate=to_decimal(snapshot["attendanceRate"]),
                research_task_completion_rate=to_decimal(snapshot["researchTaskCompletionRate"]),
                research_output_count=to_int(snapshot["researchOutputCount"]),
                project_participation_count=to_int(snapshot["projectParticipationCount"]),
                activity_hours=to_int(snapshot["activityHours"]),
                activity_count=to_int(snapshot["activityCount"]),
                practice_hours=to_int(snapshot["practiceHours"]),
                practice_report_count=to_int(snapshot["practiceReportCount"]),
                advisor_evaluation_score=to_decimal(snapshot["advisorEvaluationScore"]),
                advisor_meeting_count_60d=to_int(snapshot["advisorMeetingCount60d"]),
                advisor_avg_response_days=to_int(snapshot["advisorAvgResponseDays"]),
                missed_checkins=to_int(snapshot["missedCheckins"]),
                wellbeing_score=to_decimal(snapshot["wellbeingScore"]),
                training_plan_completion_rate=to_decimal(snapshot["trainingPlanCompletionRate"]),
                graduation_progress_rate=to_decimal(snapshot["graduationProgressRate"]),
                overdue_tasks_count=to_int(snapshot["overdueTasksCount"]),
                captured_at=captured_at,
            )
            self.created_counts["prediction_snapshots"] += 1

            metrics = item["monthlyMetrics"]
            for month_index, month in enumerate(metrics["months"]):
                PredictionMonthlyMetric.objects.create(
                    snapshot=prediction_snapshot,
                    month=month,
                    course_average=to_decimal(metrics["courseAverage"][month_index]),
                    credit_completion_rate=to_decimal(metrics["creditCompletionRate"][month_index]),
                    attendance_rate=to_decimal(metrics["attendanceRate"][month_index]),
                    research_task_completion_rate=to_decimal(metrics["researchTaskCompletionRate"][month_index]),
                    activity_hours=to_int(metrics["activityHours"][month_index]),
                    practice_hours=to_int(metrics["practiceHours"][month_index]),
                    advisor_meeting_count=to_int(metrics["advisorMeetingCount"][month_index]),
                    advisor_evaluation_score=to_decimal(metrics["advisorEvaluationScore"][month_index]),
                    wellbeing_score=to_decimal(metrics["wellbeingScore"][month_index]),
                )
                self.created_counts["prediction_monthly_metrics"] += 1

    def upsert_student(
        self,
        *,
        student_id: str,
        name: str,
        major: str,
        grade: str,
        degree_type: str,
        college: str = "",
        advisor_name: str = "",
        enrollment_type: str = EnrollmentType.MASTER,
    ) -> Student:
        defaults = {
            "name": name,
            "major": major,
            "grade": grade,
            "degree_type": degree_type,
            "college": college,
            "advisor_name": advisor_name,
            "enrollment_type": enrollment_type,
            "current_status": StudentStatus.ACTIVE,
            "gender": "",
            "source_region": "",
            "is_international": enrollment_type == EnrollmentType.INTERNATIONAL,
        }
        student, created = Student.objects.update_or_create(student_id=student_id, defaults=defaults)
        if created:
            self.created_counts["students"] += 1
        self.students_by_student_id[student.student_id] = student
        self.students_by_name[student.name] = student
        return student


def clear_existing_data():
    PredictionMonthlyMetric.objects.all().delete()
    PredictionSnapshot.objects.all().delete()
    PredictionIndicatorDefinition.objects.all().delete()
    EmploymentRecord.objects.all().delete()
    ScholarshipAward.objects.all().delete()
    DefenseSession.objects.all().delete()
    DegreeApplication.objects.all().delete()
    CourseOffering.objects.all().delete()
    TrainingPlan.objects.all().delete()
    AcademicChangeRequest.objects.all().delete()
    AcademicStatusEvent.objects.all().delete()
    AdmissionStageProgress.objects.all().delete()
    AdmissionCycle.objects.all().delete()
    ModuleNotice.objects.all().delete()
    Student.objects.all().delete()


def load_mock_payload() -> dict:
    repo_root = Path(settings.BASE_DIR).parent
    mock_file = repo_root / "src" / "mock" / "graduateManagementMock.js"
    catalog_file = repo_root / "src" / "utils" / "graduateCatalog.js"
    if not mock_file.exists():
        raise CommandError(f"Mock data file not found: {mock_file}")
    if not catalog_file.exists():
        raise CommandError(f"Graduate catalog file not found: {catalog_file}")

    node_script = """
const fs = require('fs');
const vm = require('vm');

(() => {
  const mockPath = process.argv[1];
  const catalogPath = process.argv[2];

  let catalogCode = fs.readFileSync(catalogPath, 'utf8');
  catalogCode = catalogCode.replace(/export const\\s+(\\w+)\\s*=/g, 'const $1 =');
  catalogCode += '\\nmodule.exports = { REAL_GRADES, REAL_MAJORS };';
  const catalogSandbox = { module: { exports: {} }, exports: {} };
  vm.createContext(catalogSandbox);
  vm.runInContext(catalogCode, catalogSandbox, { filename: catalogPath });
  const { REAL_GRADES, REAL_MAJORS } = catalogSandbox.module.exports;

  let mockCode = fs.readFileSync(mockPath, 'utf8');
  mockCode = mockCode.replace(/import\\s+\\{\\s*REAL_GRADES\\s*,\\s*REAL_MAJORS\\s*\\}\\s+from\\s+['"][^'"]+['"];?/, '');
  mockCode = mockCode.replace(/export const\\s+(\\w+)\\s*=/g, 'const $1 =');
  mockCode = mockCode.replace(/export default\\s+graduateManagementMock\\s*;?/g, '');
  mockCode += '\\nmodule.exports = { homeMockData, admissionMockData, academicStatusMockData, academicChangeMockData, trainingMockData, trainingCourseMockData, degreeMockData, degreeDefenseMockData, scholarshipMockData, employmentMockData, intelligentPredictionMockData };';
  const mockSandbox = {
    module: { exports: {} },
    exports: {},
    REAL_GRADES,
    REAL_MAJORS,
  };
  vm.createContext(mockSandbox);
  vm.runInContext(mockCode, mockSandbox, { filename: mockPath });
  const mod = mockSandbox.module.exports;

  const payload = {
    home: mod.homeMockData,
    admission: mod.admissionMockData,
    academicStatus: mod.academicStatusMockData,
    academicChange: mod.academicChangeMockData,
    training: mod.trainingMockData,
    trainingCourse: mod.trainingCourseMockData,
    degree: mod.degreeMockData,
    degreeDefense: mod.degreeDefenseMockData,
    scholarship: mod.scholarshipMockData,
    employment: mod.employmentMockData,
    intelligentPrediction: mod.intelligentPredictionMockData
  };
  process.stdout.write(JSON.stringify(payload));
})()
"""

    try:
        result = subprocess.run(
            ["node", "-e", node_script, str(mock_file), str(catalog_file)],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            cwd=repo_root,
        )
    except FileNotFoundError as exc:
        raise CommandError("Node.js is required to load the existing frontend mock data.") from exc
    except subprocess.CalledProcessError as exc:
        raise CommandError(exc.stderr.strip() or "Failed to load mock data through Node.js.") from exc

    return json.loads(result.stdout)


def infer_year_from_payload(payload: dict, module_code: str) -> int:
    reference_date = infer_date_from_payload(payload, module_code)
    if reference_date is not None:
        return reference_date.year

    mapping = {
        ModuleCode.HOME: payload["home"].get("updatedAt"),
        ModuleCode.ADMISSION: payload["admission"].get("updatedAt"),
        ModuleCode.TRAINING: payload["training"]["notices"][0]["date"],
        ModuleCode.DEGREE: payload["degree"].get("updatedAt"),
        ModuleCode.SCHOLARSHIP: payload["scholarship"].get("updatedAt"),
        ModuleCode.ACADEMIC_CHANGE: payload["academicChange"].get("updatedAt"),
        ModuleCode.TRAINING_COURSE: payload["trainingCourse"].get("updatedAt"),
        ModuleCode.DEGREE_DEFENSE: payload["degreeDefense"].get("updatedAt"),
        ModuleCode.INTELLIGENT_PREDICTION: payload["intelligentPrediction"].get("updatedAt"),
    }
    return extract_year(mapping.get(module_code)) or timezone.localdate().year


def infer_date_from_payload(payload: dict, module_code: str) -> date | None:
    mapping = {
        ModuleCode.HOME: payload["home"].get("updatedAt"),
        ModuleCode.ADMISSION: payload["admission"].get("updatedAt"),
        ModuleCode.TRAINING: payload["training"].get("updatedAt"),
        ModuleCode.DEGREE: payload["degree"].get("updatedAt"),
        ModuleCode.SCHOLARSHIP: payload["scholarship"].get("updatedAt"),
        ModuleCode.ACADEMIC_CHANGE: payload["academicChange"].get("updatedAt"),
        ModuleCode.TRAINING_COURSE: payload["trainingCourse"].get("updatedAt"),
        ModuleCode.DEGREE_DEFENSE: payload["degreeDefense"].get("updatedAt"),
        ModuleCode.INTELLIGENT_PREDICTION: payload["intelligentPrediction"].get("updatedAt"),
    }
    raw_value = mapping.get(module_code)
    if not raw_value:
        return None

    text = str(raw_value).strip()
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def extract_year(value) -> int | None:
    if value is None:
        return None
    text = str(value)
    if len(text) >= 4 and text[:4].isdigit():
        return int(text[:4])
    return None


def parse_date(value, fallback_year: int | None = None, fallback_date: date | None = None) -> date:
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue

    if len(text) == 5 and text[2] == "-":
        year = fallback_year or timezone.localdate().year
        return datetime.strptime(f"{year}-{text}", "%Y-%m-%d").date()

    if len(text) == 5 and text[2] == ":":
        if fallback_date is not None:
            return fallback_date
        today = timezone.localdate()
        return date(fallback_year or today.year, today.month, today.day)

    raise CommandError(f"Unsupported date format: {value}")


def parse_datetime(value, fallback_year: int | None = None) -> datetime:
    text = str(value).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S.%f"):
        try:
            return timezone.make_aware(datetime.strptime(text, fmt), timezone.get_current_timezone())
        except ValueError:
            continue

    if len(text) == 11 and text[2] == "-" and text[5] == " ":
        year = fallback_year or timezone.localdate().year
        parsed = datetime.strptime(f"{year}-{text}", "%Y-%m-%d %H:%M")
        return timezone.make_aware(parsed, timezone.get_current_timezone())

    try:
        parsed_date = parse_date(text, fallback_year=fallback_year)
        return timezone.make_aware(datetime.combine(parsed_date, time.min), timezone.get_current_timezone())
    except CommandError as exc:
        raise CommandError(f"Unsupported datetime format: {value}") from exc


def make_aware_noon(
    value: date,
    *,
    hour: int = 12,
    minute: int = 0,
) -> datetime:
    return timezone.make_aware(
        datetime.combine(value, time(hour=hour, minute=minute)),
        timezone.get_current_timezone(),
    )


def parse_month_label(
    label,
    *,
    day: int = 12,
    fallback_year: int | None = None,
    anchor_date: date | None = None,
    hour: int = 12,
    minute: int = 0,
) -> datetime:
    text = str(label or "").strip()
    anchor = anchor_date or timezone.localdate()
    year = fallback_year or anchor.year
    normalized = text.lower()
    digits = [int(item) for item in re.findall(r"\d+", text)]

    weekday_map = {
        "周一": 0,
        "周二": 1,
        "周三": 2,
        "周四": 3,
        "周五": 4,
        "周六": 5,
        "周日": 6,
        "周天": 6,
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }
    for token, weekday in weekday_map.items():
        if token in text or token in normalized:
            week_start = anchor - timedelta(days=anchor.weekday())
            return make_aware_noon(week_start + timedelta(days=weekday), hour=hour, minute=minute)

    if "周" in text or "week" in normalized:
        week_index = digits[0] if digits else 1
        week_start = anchor - timedelta(days=anchor.weekday())
        return make_aware_noon(
            week_start + timedelta(weeks=max(week_index - 1, 0)),
            hour=hour,
            minute=minute,
        )

    if "月" in text and digits:
        month = max(1, min(12, digits[0]))
        if anchor_date is not None and month > anchor.month:
            year -= 1
        return make_aware_noon(
            date(year, month, min(day, days_in_month(year, month))),
            hour=hour,
            minute=minute,
        )

    if digits:
        month = max(1, min(12, digits[0]))
        return make_aware_noon(
            date(year, month, min(day, days_in_month(year, month))),
            hour=hour,
            minute=minute,
        )

    return make_aware_noon(
        date(year, anchor.month, min(day, days_in_month(year, anchor.month))),
        hour=hour,
        minute=minute,
    )


def set_timestamps(instance, when: datetime):
    instance.__class__.objects.filter(pk=instance.pk).update(created_at=when, updated_at=when)


def days_in_month(year: int, month: int) -> int:
    if month == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)
    return (next_month - timedelta(days=1)).day


def grade_from_student_id(student_id: str) -> str:
    digits = "".join(char for char in str(student_id) if char.isdigit())
    if len(digits) >= 4:
        return f"{digits[:4]}级"
    return "未知年级"


def to_decimal(value) -> Decimal:
    if isinstance(value, Decimal):
        return value
    text = str(value).strip().replace("%", "")
    return Decimal(text)


def to_int(value) -> int:
    if isinstance(value, int):
        return value
    return int(to_decimal(value))


def find_number_by_title(stat_cards: dict, keywords: list[str], default):
    for title, value in stat_cards.items():
        if all(keyword in title for keyword in keywords):
            return value
    return default


def map_degree_type(raw_value) -> str:
    text = str(raw_value or "")
    if "博士" in text:
        return DegreeType.DOCTORAL
    if "专业" in text:
        return DegreeType.PROFESSIONAL_MASTER
    return DegreeType.ACADEMIC_MASTER


def map_enrollment_type(raw_value) -> str:
    text = str(raw_value or "")
    if "国际" in text:
        return EnrollmentType.INTERNATIONAL
    if "博士" in text:
        return EnrollmentType.DOCTORAL
    return EnrollmentType.MASTER


def map_workflow_status(raw_value, status_type: str | None = None, completion_percent: int | None = None) -> str:
    text = str(raw_value or "")
    tag = str(status_type or "")

    if completion_percent == 100:
        return WorkflowStatus.COMPLETED
    if completion_percent == 0 and "未" in text:
        return WorkflowStatus.DRAFT

    if any(keyword in text for keyword in ["未开始", "待发布", "待提交"]):
        return WorkflowStatus.DRAFT
    if any(keyword in text for keyword in ["待审核", "待确认", "待处理", "待审", "待提交"]):
        return WorkflowStatus.PENDING
    if any(keyword in text for keyword in ["进行中", "办理中", "审核中", "审批中"]):
        return WorkflowStatus.IN_PROGRESS
    if any(keyword in text for keyword in ["退回", "驳回", "不通过", "需修订", "修改后重提"]):
        return WorkflowStatus.REJECTED
    if any(keyword in text for keyword in ["已通过", "通过", "已结束", "完成", "成功", "已生效", "已发布"]):
        return WorkflowStatus.COMPLETED

    if tag == "success":
        return WorkflowStatus.COMPLETED
    if tag == "warning":
        return WorkflowStatus.PENDING
    if tag == "danger":
        return WorkflowStatus.REJECTED
    if tag == "info":
        return WorkflowStatus.IN_PROGRESS

    return WorkflowStatus.PENDING


def map_risk_level(raw_value) -> str:
    text = str(raw_value or "")
    if "高" in text:
        return RiskLevel.HIGH
    if "预警" in text or "警" in text:
        return RiskLevel.ALERT
    if "中" in text:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW
