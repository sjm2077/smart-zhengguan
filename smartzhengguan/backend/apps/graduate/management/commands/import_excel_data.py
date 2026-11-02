from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from openpyxl import load_workbook
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.graduate.constants import REAL_MAJORS
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
    HomeAnnualSummary,
    HomeGradeMajorSummary,
    HomeSourceRegionSummary,
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


TARGET_COLLEGE_NAME = "政治学与公共管理学院"
DEFAULT_WORKBOOK_FILES = ["研究生数据_2021-2026.xlsx"]


ADVISOR_NAMES = [
    "王教授",
    "李教授",
    "张教授",
    "刘教授",
    "陈教授",
    "赵教授",
    "周教授",
    "吴教授",
]

COURSE_NAMES = [
    "马克思主义经典著作选读",
    "中国化马克思主义专题研究",
    "公共政策分析",
    "国际关系前沿问题",
    "政治学理论方法",
    "社会调查与数据分析",
    "学术规范与论文写作",
    "国家治理现代化专题",
    "比较政治制度研究",
    "应急管理案例分析",
]

COURSE_TEACHERS = ["王敏", "李娜", "张强", "刘洋", "陈晨", "赵磊", "周静", "吴昊"]
DEFENSE_CHAIRS = ["王教授", "李教授", "张教授", "刘教授", "陈教授", "赵教授"]
DEFENSE_ROOMS = ["文科楼201", "文科楼203", "学术报告厅A", "学术报告厅B", "综合楼501"]
INDUSTRIES = ["教育", "公共管理", "科研服务", "信息服务", "金融", "制造业"]
UNIT_NATURES = ["党政机关", "事业单位", "国有企业", "高校", "科研院所", "民营企业"]
ACADEMIC_CHANGE_TYPES = ["休学", "复学", "退学", "延期毕业", "其他异动"]
TRAINING_STAGES = ["培养计划", "开题阶段", "中期考核", "答辩阶段"]


class Command(BaseCommand):
    help = "Import graduate data from Excel file"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            default=DEFAULT_WORKBOOK_FILES[0],
            help="Path to the Excel file",
        )
        parser.add_argument(
            "--keep-existing",
            action="store_true",
            help="Append data instead of clearing existing data first",
        )

    def handle(self, *args, **options):
        excel_path = self.resolve_excel_path(options["file"])

        try:
            workbook = load_workbook(excel_path, read_only=True)
            self.stdout.write(f"Excel file loaded: {excel_path}")
            self.stdout.write(f"Sheets: {workbook.sheetnames}")
        except Exception as exc:
            raise CommandError(f"Failed to load Excel file: {exc}") from exc

        with transaction.atomic():
            if not options["keep_existing"]:
                self.stdout.write("Clearing existing data...")
                self.clear_existing_data()

            self.import_homepage_summaries(workbook)
            student_context = self.import_students(workbook)
            self.import_academic_records(workbook, student_context)
            self.import_admission_data(workbook)
            self.import_training_plans(workbook, student_context)
            self.import_course_offerings(workbook)
            self.import_degree_applications(workbook, student_context)
            self.import_defense_sessions(workbook)
            self.import_scholarships(workbook, student_context)
            self.import_employment_records(workbook, student_context)
            self.ensure_prediction_indicators()
            self.import_predictions(workbook, student_context)

        self.stdout.write(self.style.SUCCESS("Excel data imported successfully!"))

    def resolve_excel_path(self, file_arg):
        file_candidates = [file_arg]
        if str(file_arg).strip() == DEFAULT_WORKBOOK_FILES[0]:
            file_candidates.extend(
                candidate for candidate in DEFAULT_WORKBOOK_FILES[1:]
                if candidate not in file_candidates
            )

        search_paths = []
        for raw_candidate in file_candidates:
            candidate = Path(raw_candidate).expanduser()
            if candidate.is_absolute():
                search_paths.append(candidate)
                continue

            search_paths.extend([
                Path.cwd() / candidate,
                settings.BASE_DIR / candidate,
                settings.BASE_DIR.parent / candidate,
            ])

        for path in search_paths:
            if path.exists():
                return path

        checked_paths = ", ".join(str(path) for path in search_paths)
        raise CommandError(f"Excel file not found: {file_arg}. Checked: {checked_paths}")

    def clear_existing_data(self):
        PredictionMonthlyMetric.objects.all().delete()
        PredictionSnapshot.objects.all().delete()
        AdmissionStageProgress.objects.all().delete()
        AcademicChangeRequest.objects.all().delete()
        AcademicStatusEvent.objects.all().delete()
        TrainingPlan.objects.all().delete()
        CourseOffering.objects.all().delete()
        DegreeApplication.objects.all().delete()
        DefenseSession.objects.all().delete()
        ScholarshipAward.objects.all().delete()
        EmploymentRecord.objects.all().delete()
        AdmissionCycle.objects.all().delete()
        HomeSourceRegionSummary.objects.all().delete()
        HomeGradeMajorSummary.objects.all().delete()
        HomeAnnualSummary.objects.all().delete()
        Student.objects.all().delete()

    def import_homepage_summaries(self, workbook):
        annual_rows = self.sheet_rows(workbook, "首页总览-年度数据")
        grade_major_rows = self.sheet_rows(workbook, "首页总览-年级专业")
        source_rows = self.sheet_rows(workbook, "首页总览-生源地")

        annual_objects = [
            HomeAnnualSummary(
                year=int(row["年份"]),
                total_students=int(row["在校学生总数"]),
                master_count=int(row["硕士生人数"]),
                doctor_count=int(row["博士生人数"]),
                international_count=int(row["国际学生人数"]),
                annual_graduates=int(row["毕业生人数"]),
            )
            for row in annual_rows
        ]
        grade_major_objects = [
            HomeGradeMajorSummary(
                grade=str(row["年级"]),
                major=str(row["专业"]),
                total_count=int(row["总人数"]),
                male_count=int(row["男生人数"]),
                female_count=int(row["女生人数"]),
            )
            for row in grade_major_rows
        ]
        source_objects = [
            HomeSourceRegionSummary(
                region=str(row["生源地"]),
                student_count=int(row["人数"]),
                percent_text=str(row["占比"]),
            )
            for row in source_rows
        ]

        HomeAnnualSummary.objects.bulk_create(annual_objects, batch_size=100)
        HomeGradeMajorSummary.objects.bulk_create(grade_major_objects, batch_size=200)
        HomeSourceRegionSummary.objects.bulk_create(source_objects, batch_size=100)
        self.stdout.write(f"Imported {len(annual_objects)} home annual summaries")
        self.stdout.write(f"Imported {len(grade_major_objects)} home grade-major summaries")
        self.stdout.write(f"Imported {len(source_objects)} home source-region summaries")

    def import_students(self, workbook):
        distribution_rows = self.sheet_rows(workbook, "首页总览-年级专业")
        source_rows = self.sheet_rows(workbook, "首页总览-生源地")
        annual_rows = self.sheet_rows(workbook, "首页总览-年度数据")
        status_rows = self.sheet_rows(workbook, "学籍管理")
        prediction_rows = self.sheet_rows(workbook, "智能预测-学生数据")

        if not distribution_rows:
            self.stdout.write("Student distribution sheet not found, skipped student import")
            return self.build_student_context()

        remaining = {}
        gender_quota = {}
        for row in distribution_rows:
            key = (str(row["年级"]), str(row["专业"]))
            remaining[key] = int(row["总人数"])
            gender_quota[key] = {
                "男": int(row["男生人数"] or 0),
                "女": int(row["女生人数"] or 0),
            }

        seed_rows = []
        used_prediction_rows = []
        for row in prediction_rows:
            key = (str(row["年级"]), str(row["专业"]))
            # Explicit prediction samples must not be dropped merely because
            # a historical aggregate sheet has a smaller population quota.
            remaining.setdefault(key, 0)
            gender_quota.setdefault(key, {"男": 0, "女": 0})
            gender = self.consume_gender(gender_quota[key])
            remaining[key] -= 1
            seed_rows.append(
                {
                    "student_id": str(row["学号"]),
                    "name": str(row["姓名"]),
                    "grade": str(row["年级"]),
                    "major": str(row["专业"]),
                    "advisor_name": str(row["导师"]),
                    "degree_label": str(row["类别"]),
                    "gender": gender,
                }
            )
            used_prediction_rows.append(str(row["学号"]))

        synthetic_counter = 1
        for row in distribution_rows:
            grade = str(row["年级"])
            major = str(row["专业"])
            key = (grade, major)
            for _ in range(max(remaining.get(key, 0), 0)):
                gender = self.consume_gender(gender_quota[key])
                seed_rows.append(
                    {
                        "student_id": f"AUTO{synthetic_counter:06d}",
                        "name": f"学生{synthetic_counter:04d}",
                        "grade": grade,
                        "major": major,
                        "advisor_name": ADVISOR_NAMES[(synthetic_counter - 1) % len(ADVISOR_NAMES)],
                        "degree_label": "",
                        "gender": gender,
                    }
                )
                synthetic_counter += 1

        total_students = len(seed_rows)
        latest_annual = annual_rows[-1] if annual_rows else {}
        latest_status = status_rows[-1] if status_rows else {}
        source_regions = self.expand_named_counts(
            [(str(row["生源地"]), int(row["人数"])) for row in source_rows],
            total_students,
        )

        doctoral_quota = self.scaled_count(
            int(latest_annual.get("博士生人数", 0)),
            int(latest_annual.get("在校学生总数", total_students or 1)),
            total_students,
        )
        international_quota = self.scaled_count(
            int(latest_annual.get("国际学生人数", 0)),
            int(latest_annual.get("在校学生总数", total_students or 1)),
            total_students,
        )
        status_scale_base = int(latest_status.get("在籍学生数", total_students or 1))
        suspended_quota = self.scaled_count(int(latest_status.get("休学人数", 0)), status_scale_base, total_students)
        withdrawn_quota = self.scaled_count(int(latest_status.get("退学人数", 0)), status_scale_base, total_students)
        extended_quota = self.scaled_count(int(latest_status.get("延毕人数", 0)), status_scale_base, total_students)
        other_quota = self.scaled_count(int(latest_status.get("其他异动人数", 0)), status_scale_base, total_students)

        doctoral_indexes = self.build_even_index_set(total_students, doctoral_quota, offset=1)
        international_indexes = self.build_even_index_set(total_students, international_quota, offset=2)
        suspended_indexes = self.build_even_index_set(total_students, suspended_quota, offset=3)
        withdrawn_indexes = self.build_even_index_set(total_students, withdrawn_quota, offset=4)
        extended_indexes = self.build_even_index_set(total_students, extended_quota, offset=5)
        other_indexes = self.build_even_index_set(total_students, other_quota, offset=6)

        students = []
        for index, row in enumerate(seed_rows):
            major = row["major"]
            grade = row["grade"]
            college = TARGET_COLLEGE_NAME
            if row["degree_label"] == "博士" or (not row["degree_label"] and index in doctoral_indexes):
                degree_type = DegreeType.DOCTORAL
                enrollment_type = EnrollmentType.DOCTORAL
            elif row["degree_label"] == "专业型硕士" or (row["degree_label"] != "学术型硕士" and "管理" in major):
                degree_type = DegreeType.PROFESSIONAL_MASTER
                enrollment_type = EnrollmentType.MASTER
            else:
                degree_type = DegreeType.ACADEMIC_MASTER
                enrollment_type = EnrollmentType.MASTER

            is_international = index in international_indexes
            if is_international:
                enrollment_type = EnrollmentType.INTERNATIONAL

            if index in withdrawn_indexes:
                current_status = StudentStatus.WITHDRAWN
            elif index in suspended_indexes:
                current_status = StudentStatus.SUSPENDED
            elif index in extended_indexes:
                current_status = StudentStatus.EXTENDED
            elif index in other_indexes:
                current_status = StudentStatus.OTHER
            else:
                current_status = StudentStatus.ACTIVE

            students.append(
                Student(
                    student_id=row["student_id"],
                    name=row["name"],
                    gender=row["gender"],
                    college=college,
                    major=major,
                    grade=grade,
                    degree_type=degree_type,
                    enrollment_type=enrollment_type,
                    source_region=source_regions[index] if index < len(source_regions) else "",
                    advisor_name=row["advisor_name"],
                    current_status=current_status,
                    is_international=is_international,
                    expected_graduation_date=self.expected_graduation_date(grade, degree_type),
                )
            )

        Student.objects.bulk_create(students, batch_size=500)
        self.stdout.write(f"Imported {len(students)} students")
        return self.build_student_context()

    def import_academic_records(self, workbook, student_context):
        rows = self.sheet_rows(workbook, "学籍管理")
        students = student_context["all"]
        if not rows or not students:
            self.stdout.write("Academic status sheets skipped")
            return

        events = []
        requests = []
        event_counter = 1
        request_counter = 1
        all_students = students

        for row in rows:
            year = int(row["年份"])
            changes = [
                ("休学", int(row["休学人数"]), WorkflowStatus.COMPLETED),
                ("复学", int(row["复学人数"]), WorkflowStatus.COMPLETED),
                ("退学", int(row["退学人数"]), WorkflowStatus.COMPLETED),
                ("延期毕业", int(row["延毕人数"]), WorkflowStatus.IN_PROGRESS),
                ("其他异动", int(row["其他异动人数"]), WorkflowStatus.PENDING),
            ]

            student_offset = year * 17
            for change_type, count, default_status in changes:
                for item_index in range(count):
                    student = all_students[(student_offset + item_index) % len(all_students)]
                    occurred_on = date(year, min(12, 1 + (item_index % 12)), 1 + (item_index % 27))
                    event_status = default_status
                    request_status = (
                        WorkflowStatus.PENDING
                        if item_index % 8 == 0 and default_status != WorkflowStatus.COMPLETED
                        else default_status
                    )
                    events.append(
                        AcademicStatusEvent(
                            external_id=f"AS{year}{event_counter:05d}",
                            student=student,
                            student_name=student.name,
                            change_type=change_type,
                            handler_name="研究生院学籍办",
                            reason=f"{change_type}业务导入记录",
                            occurred_on=occurred_on,
                            status=event_status,
                            status_tag=self.workflow_tag(event_status),
                        )
                    )
                    submitted_at = self.make_aware_datetime(
                        year,
                        min(12, 1 + (item_index % 12)),
                        2 + (item_index % 26),
                        10,
                    )
                    reviewed_at = submitted_at + timedelta(days=5) if request_status == WorkflowStatus.COMPLETED else None
                    requests.append(
                        AcademicChangeRequest(
                            student=student,
                            student_name=student.name,
                            change_type=change_type,
                            current_step=self.change_step(change_type, request_status),
                            status=request_status,
                            status_type=self.workflow_tag(request_status),
                            submitted_at=submitted_at,
                            reviewed_at=reviewed_at,
                            remark=f"Excel 导入生成的{change_type}申请",
                        )
                    )
                    event_counter += 1
                    request_counter += 1

        AcademicStatusEvent.objects.bulk_create(events, batch_size=500)
        AcademicChangeRequest.objects.bulk_create(requests, batch_size=500)
        self.stdout.write(f"Imported {len(events)} academic status events")
        self.stdout.write(f"Imported {len(requests)} academic change requests")

    def import_admission_data(self, workbook):
        rows = self.sheet_rows(workbook, "招生管理-年度汇总")
        if not rows:
            self.stdout.write("Admission sheet not found, skipped")
            return

        cycles = []
        for row in rows:
            year = int(row["年份"])
            cycle_rows = [
                (
                    EnrollmentType.MASTER,
                    "硕士研究生",
                    "统考招生",
                    int(row["硕士报名人数"]),
                    int(row["硕士复试人数"]),
                    int(row["硕士复试人数"]),
                    int(row["硕士拟录取人数"]),
                    int(row["硕士正式录取人数"]),
                ),
                (
                    EnrollmentType.DOCTORAL,
                    "博士研究生",
                    "申请考核",
                    int(row["博士报名人数"]),
                    int(row["博士复试人数"]),
                    int(row["博士复试人数"]),
                    int(row["博士拟录取人数"]),
                    int(row["博士正式录取人数"]),
                ),
                (
                    EnrollmentType.INTERNATIONAL,
                    "国际学生",
                    "来华留学",
                    int(row["国际学生报名人数"]),
                    int(row["国际学生录取人数"]),
                    int(row["国际学生录取人数"]),
                    int(row["国际学生录取人数"]),
                    int(row["国际学生录取人数"]),
                ),
            ]

            for enrollment_type, direction, source, applicants, initial_pass, retest, proposed, actual in cycle_rows:
                rate = round(actual * 100 / applicants, 2) if applicants else 0
                cycles.append(
                    AdmissionCycle(
                        year=year,
                        enrollment_type=enrollment_type,
                        direction=direction,
                        source_category=source,
                        applicant_count=applicants,
                        initial_review_pass_count=initial_pass,
                        retest_count=retest,
                        proposed_admission_count=proposed,
                        actual_admission_count=actual,
                        admission_rate=Decimal(str(rate)),
                    )
                )

        AdmissionCycle.objects.bulk_create(cycles, batch_size=200)
        self.stdout.write(f"Imported {len(cycles)} admission cycles")

        stage_objects = []
        for cycle in AdmissionCycle.objects.all().order_by("year", "direction"):
            stage_objects.extend(self.build_admission_stages(cycle))
        AdmissionStageProgress.objects.bulk_create(stage_objects, batch_size=500)
        self.stdout.write(f"Imported {len(stage_objects)} admission stages")

    def import_training_plans(self, workbook, student_context):
        rows = self.sheet_rows(workbook, "培养管理")
        students = student_context["all"]
        by_grade = student_context["by_grade"]
        if not rows or not students:
            self.stdout.write("Training sheet skipped")
            return

        plans = []
        for row in rows:
            year = int(row["年份"])
            total = int(row["培养计划总数"])
            submitted = int(row["已提交培养计划数量"])
            approved = int(row["已审核通过培养计划数量"])
            incomplete = int(row["未完成培养计划数量"])
            proposal_count = int(row["开题人数"])
            midterm_count = int(row["中期考核人数"])
            defense_count = int(row["答辩阶段人数"])

            draft_count = max(total - submitted, 0)
            rejected_count = min(incomplete, total)
            pending_count = max(submitted - approved - rejected_count, 0)
            completed_count = max(total - draft_count - rejected_count - pending_count, 0)

            grade_key = f"{year}级"
            student_pool = by_grade.get(grade_key) or students

            for index in range(total):
                student = student_pool[index % len(student_pool)]
                if index < completed_count:
                    status = WorkflowStatus.COMPLETED
                    completion = 92 + (index % 9)
                elif index < completed_count + pending_count:
                    status = WorkflowStatus.PENDING
                    completion = 65 + (index % 15)
                elif index < completed_count + pending_count + rejected_count:
                    status = WorkflowStatus.REJECTED
                    completion = 45 + (index % 15)
                else:
                    status = WorkflowStatus.DRAFT
                    completion = 20 + (index % 20)

                if index < defense_count:
                    stage = "答辩阶段"
                elif index < midterm_count:
                    stage = "中期考核"
                elif index < proposal_count:
                    stage = "开题阶段"
                else:
                    stage = "培养计划"

                plans.append(
                    TrainingPlan(
                        student=student,
                        student_name=student.name,
                        grade=student.grade,
                        major=student.major,
                        degree_type=student.degree_type,
                        stage=stage,
                        advisor_name=student.advisor_name,
                        status=status,
                        status_tag=self.workflow_tag(status),
                        completion_percent=min(completion, 100),
                        business_updated_at=date(year, min(12, 1 + (index % 12)), 1 + (index % 27)),
                    )
                )

        TrainingPlan.objects.bulk_create(plans, batch_size=500)
        self.stdout.write(f"Imported {len(plans)} training plans")

    def import_course_offerings(self, workbook):
        rows = self.sheet_rows(workbook, "课程与培养环节")
        if not rows:
            self.stdout.write("Course sheet not found, skipped")
            return

        offerings = []
        for row in rows:
            year = int(row["年份"])
            semester = str(row["学期"])
            open_count = int(row["开课数量"])
            for index in range(open_count):
                status = WorkflowStatus.COMPLETED if year < timezone.localdate().year else (
                    WorkflowStatus.IN_PROGRESS if semester == "春季" else WorkflowStatus.PENDING
                )
                offerings.append(
                    CourseOffering(
                        course_name=f"{COURSE_NAMES[index % len(COURSE_NAMES)]}-{year}{semester}-{index + 1}",
                        teacher_name=COURSE_TEACHERS[index % len(COURSE_TEACHERS)],
                        major=self.course_major(index),
                        schedule_text=self.course_schedule(semester, index),
                        status=status,
                        status_type=self.workflow_tag(status),
                        term=f"{year}{semester}",
                    )
                )

        CourseOffering.objects.bulk_create(offerings, batch_size=500)
        self.stdout.write(f"Imported {len(offerings)} course offerings")

    def import_degree_applications(self, workbook, student_context):
        rows = self.sheet_rows(workbook, "学位管理")
        students = student_context["all"]
        by_grade = student_context["by_grade"]
        if not rows or not students:
            self.stdout.write("Degree sheet skipped")
            return

        applications = []
        for row in rows:
            year = int(row["年份"])
            total = int(row["学位申请人数"])
            submitted_count = int(row["论文提交人数"])
            review_pass_count = int(row["论文评阅通过人数"])
            defense_pass_count = int(row["答辩通过人数"])
            academic_awarded = int(row["学术学位授予人数"])
            professional_awarded = int(row["专业学位授予人数"])
            awarded_count = academic_awarded + professional_awarded

            student_pool = by_grade.get(f"{year}级") or students
            academic_cutoff = min(academic_awarded, total)
            professional_cutoff = min(academic_awarded + professional_awarded, total)

            for index in range(total):
                student = student_pool[index % len(student_pool)]
                paper_submitted_at = date(year, 4, 1 + (index % 20)) if index < submitted_count else None
                if index < review_pass_count:
                    review_result = "通过"
                elif paper_submitted_at:
                    review_result = "待评阅"
                else:
                    review_result = ""

                if index < defense_pass_count:
                    defense_result = "通过"
                elif index < submitted_count:
                    defense_result = "待答辩"
                else:
                    defense_result = ""

                if index < awarded_count:
                    award_status = WorkflowStatus.COMPLETED
                    awarded_at = date(year, 7, 1 + (index % 20))
                elif paper_submitted_at:
                    award_status = WorkflowStatus.IN_PROGRESS
                    awarded_at = None
                else:
                    award_status = WorkflowStatus.PENDING
                    awarded_at = None

                if index < academic_cutoff:
                    application_type = "学术学位"
                elif index < professional_cutoff:
                    application_type = "专业学位"
                else:
                    application_type = "学位申请"

                applications.append(
                    DegreeApplication(
                        student=student,
                        student_name=student.name,
                        application_year=year,
                        application_type=application_type,
                        discipline=student.major,
                        paper_submitted_at=paper_submitted_at,
                        paper_review_result=review_result,
                        defense_result=defense_result,
                        award_status=award_status,
                        awarded_at=awarded_at,
                    )
                )

        DegreeApplication.objects.bulk_create(applications, batch_size=500)
        self.stdout.write(f"Imported {len(applications)} degree applications")

    def import_defense_sessions(self, workbook):
        rows = self.sheet_rows(workbook, "答辩管理")
        if not rows:
            self.stdout.write("Defense sheet not found, skipped")
            return

        sessions = []
        current_year = timezone.localdate().year
        for row in rows:
            year = int(row["年份"])
            session_count = int(row["答辩场次数量"])
            student_counts = self.split_integer(int(row["答辩学生人数"]), session_count)
            in_progress_cutoff = 2 if year == current_year else 0
            pending_cutoff = 4 if year == current_year else 0

            for index in range(session_count):
                if year < current_year or index < max(session_count - in_progress_cutoff - pending_cutoff, 0):
                    status = WorkflowStatus.COMPLETED
                elif index < session_count - pending_cutoff:
                    status = WorkflowStatus.IN_PROGRESS
                else:
                    status = WorkflowStatus.PENDING

                sessions.append(
                    DefenseSession(
                        session_name=f"{year}年第{index + 1}场研究生答辩",
                        chair_name=DEFENSE_CHAIRS[index % len(DEFENSE_CHAIRS)],
                        room=DEFENSE_ROOMS[index % len(DEFENSE_ROOMS)],
                        student_count=student_counts[index],
                        status=status,
                        status_type=self.workflow_tag(status),
                        scheduled_at=self.make_aware_datetime(year, min(12, 3 + (index % 6)), 1 + (index % 24), 9 + (index % 6)),
                    )
                )

        DefenseSession.objects.bulk_create(sessions, batch_size=300)
        self.stdout.write(f"Imported {len(sessions)} defense sessions")

    def import_scholarships(self, workbook, student_context):
        rows = self.sheet_rows(workbook, "奖助管理")
        students = student_context["all"]
        if not rows or not students:
            self.stdout.write("Scholarship sheet skipped")
            return

        awards = []
        student_offset = 0
        for row in rows:
            year = int(row["年份"])
            categories = [
                ("scholarship", "国家奖学金", int(row["国家奖学金人数"]), int(row["国家奖学金金额"])),
                ("scholarship", "学业奖学金", int(row["学业奖学金人数"]), int(row["学业奖学金金额"])),
                ("scholarship", "社会奖学金", int(row["社会奖学金人数"]), int(row["社会奖学金金额"])),
                ("aid", "助学金", int(row["助学金人数"]), int(row["助学金金额"])),
            ]

            for award_category, award_type, count, total_amount in categories:
                amounts = self.split_amount(total_amount, count)
                for index in range(count):
                    student = students[(student_offset + index) % len(students)]
                    awards.append(
                        ScholarshipAward(
                            student=student,
                            student_name=student.name,
                            award_year=year,
                            grade=student.grade,
                            major=student.major,
                            award_category=award_category,
                            award_type=award_type,
                            award_name=f"{year}{award_type}-{index + 1}",
                            amount=amounts[index],
                            awarded_on=date(year, 11 if award_category == "scholarship" else 10, 1 + (index % 27)),
                        )
                    )
                student_offset += count

        ScholarshipAward.objects.bulk_create(awards, batch_size=500)
        self.stdout.write(f"Imported {len(awards)} scholarship records")

    def import_employment_records(self, workbook, student_context):
        rows = self.sheet_rows(workbook, "就业管理")
        students = student_context["all"]
        if not rows or not students:
            self.stdout.write("Employment sheet skipped")
            return

        records = []
        current_year = timezone.localdate().year
        student_offset = 0
        for row in rows:
            year = int(row["年份"])
            total = int(row["毕业生总人数"])
            employed = int(row["已就业人数"])
            further = int(row["升学人数"])
            overseas = int(row["出国出境人数"])
            flexible = int(row["灵活就业人数"])
            signed = int(row["签约人数"])

            standard_employed = max(employed - further - overseas - flexible, 0)
            unresolved = max(total - employed, 0)
            category_specs = [
                ("单位就业", standard_employed, False),
                ("升学", further, True),
                ("出国出境", overseas, False),
                ("灵活就业", flexible, False),
                ("", unresolved, False),
            ]

            annual_records = []
            for destination_type, count, is_further_study in category_specs:
                for index in range(count):
                    student = students[(student_offset + len(annual_records)) % len(students)]
                    has_destination = bool(destination_type)
                    province = student.source_region or "山东"
                    status = WorkflowStatus.COMPLETED if has_destination else WorkflowStatus.PENDING
                    annual_records.append(
                        EmploymentRecord(
                            student=student,
                            student_name=student.name,
                            graduation_year=year,
                            destination_type=destination_type,
                            unit_nature=self.unit_nature_for_destination(destination_type),
                            industry=self.industry_for_destination(destination_type, index),
                            province=province,
                            employer_name=self.employer_name(destination_type, province, year, index),
                            is_signed=False,
                            is_further_study=is_further_study,
                            status=status if year <= current_year else WorkflowStatus.PENDING,
                        )
                    )

            signed_remaining = signed
            for record in annual_records:
                if not record.destination_type or signed_remaining <= 0:
                    continue
                record.is_signed = True
                signed_remaining -= 1

            records.extend(annual_records[:total])
            student_offset += total

        EmploymentRecord.objects.bulk_create(records, batch_size=500)
        self.stdout.write(f"Imported {len(records)} employment records")

    def ensure_prediction_indicators(self):
        indicators = [
            ("课程成绩", 100, 1),
            ("学分完成率", 100, 2),
            ("考勤率", 100, 3),
            ("培养节点进度", 100, 4),
            ("科研表现", 100, 5),
            ("导师反馈", 100, 6),
            ("心理健康", 100, 7),
        ]
        for name, max_score, sort_order in indicators:
            PredictionIndicatorDefinition.objects.get_or_create(
                name=name,
                defaults={"max_score": max_score, "sort_order": sort_order},
            )

    def import_predictions(self, workbook, student_context):
        rows = self.sheet_rows(workbook, "智能预测-学生数据")
        students_by_student_id = student_context["by_student_id"]
        if not rows:
            self.stdout.write("Prediction sheet not found, skipped")
            return

        snapshots = []
        snapshot_plan = []
        now = timezone.now()
        for index, row in enumerate(rows):
            student = students_by_student_id.get(str(row["学号"]))
            if student is None:
                continue

            course_average = float(row["课程成绩"])
            credit_completion_rate = float(row["学分完成情况"])
            attendance_rate = float(row["考勤情况"])
            training_status = str(row["培养节点完成情况"])
            training_rate = 100.0 if training_status == "已完成" else 72.0
            overdue_tasks = int(row["任务逾期次数"])
            missed_checkins = int(row["未打卡记录次数"])
            advisor_score = float(row["导师评价分数"])
            wellbeing_score = float(row["心理测评分数"])
            risk_level, risk_type, risk_field, suggestion = self.prediction_risk_fields(
                course_average,
                credit_completion_rate,
                attendance_rate,
                training_rate,
                overdue_tasks,
                missed_checkins,
                wellbeing_score,
            )

            snapshot = PredictionSnapshot(
                student=student,
                sample_range="近6个月",
                risk_level=risk_level,
                risk_type=risk_type,
                risk_field=risk_field,
                suggestion=suggestion,
                course_average=Decimal(str(course_average)),
                credit_completion_rate=Decimal(str(credit_completion_rate)),
                attendance_rate=Decimal(str(attendance_rate)),
                research_task_completion_rate=Decimal(str(training_rate)),
                research_output_count=int(row["科研成果数量"]),
                project_participation_count=int(row["科研项目参与数量"]),
                activity_hours=int(row["活动时长"]),
                activity_count=int(row["活动参与次数"]),
                practice_hours=int(row["社会实践时长"]),
                practice_report_count=int(row["社会实践次数"]),
                advisor_evaluation_score=Decimal(str(advisor_score)),
                advisor_meeting_count_60d=int(row["导师沟通次数"]),
                advisor_avg_response_days=max(1, 10 - int(row["导师沟通次数"]) // 2),
                missed_checkins=missed_checkins,
                wellbeing_score=Decimal(str(wellbeing_score)),
                training_plan_completion_rate=Decimal(str(training_rate)),
                graduation_progress_rate=Decimal(str(self.graduation_progress_rate(student.grade, student.degree_type))),
                overdue_tasks_count=overdue_tasks,
                captured_at=now - timedelta(days=index),
            )
            snapshots.append(snapshot)
            snapshot_plan.append(
                {
                    "student_id": student.student_id,
                    "course_average": course_average,
                    "credit_completion_rate": credit_completion_rate,
                    "attendance_rate": attendance_rate,
                    "training_rate": training_rate,
                    "activity_hours": int(row["活动时长"]),
                    "practice_hours": int(row["社会实践时长"]),
                    "advisor_score": advisor_score,
                    "wellbeing_score": wellbeing_score,
                }
            )

        PredictionSnapshot.objects.bulk_create(snapshots, batch_size=200)
        snapshot_lookup = {item.student.student_id: item for item in PredictionSnapshot.objects.select_related("student").all()}

        monthly_metrics = []
        for plan in snapshot_plan:
            snapshot = snapshot_lookup.get(plan["student_id"])
            if snapshot is None:
                continue
            for month_index in range(6):
                month_date = timezone.localdate() - timedelta(days=30 * (5 - month_index))
                decay = 5 - month_index
                monthly_metrics.append(
                    PredictionMonthlyMetric(
                        snapshot=snapshot,
                        month=month_date.strftime("%Y-%m"),
                        course_average=Decimal(str(max(plan["course_average"] - decay * 1.2, 60))),
                        credit_completion_rate=Decimal(str(max(plan["credit_completion_rate"] - decay, 50))),
                        attendance_rate=Decimal(str(max(plan["attendance_rate"] - decay * 0.8, 65))),
                        research_task_completion_rate=Decimal(str(max(plan["training_rate"] - decay * 1.5, 45))),
                        activity_hours=max(plan["activity_hours"] - decay * 2, 0),
                        practice_hours=max(plan["practice_hours"] - decay * 2, 0),
                        advisor_meeting_count=max(1, 6 - decay),
                        advisor_evaluation_score=Decimal(str(max(plan["advisor_score"] - decay * 0.6, 60))),
                        wellbeing_score=Decimal(str(max(plan["wellbeing_score"] - decay * 0.7, 55))),
                    )
                )

        PredictionMonthlyMetric.objects.bulk_create(monthly_metrics, batch_size=500)
        self.stdout.write(f"Imported {len(snapshots)} prediction snapshots")
        self.stdout.write(f"Imported {len(monthly_metrics)} prediction monthly metrics")

    def build_student_context(self):
        students = list(Student.objects.all().order_by("student_id"))
        by_grade = {}
        by_student_id = {}
        for student in students:
            by_grade.setdefault(student.grade, []).append(student)
            by_student_id[student.student_id] = student
        return {"all": students, "by_grade": by_grade, "by_student_id": by_student_id}

    def sheet_rows(self, workbook, sheet_name):
        if sheet_name not in workbook.sheetnames:
            return []
        worksheet = workbook[sheet_name]
        iterator = worksheet.iter_rows(values_only=True)
        headers = next(iterator, None)
        if not headers:
            return []

        rows = []
        for row in iterator:
            if not any(value not in (None, "") for value in row):
                continue
            rows.append(dict(zip(headers, row)))
        return rows

    def consume_gender(self, quota):
        if quota["男"] > quota["女"] and quota["男"] > 0:
            quota["男"] -= 1
            return "男"
        if quota["女"] > 0:
            quota["女"] -= 1
            return "女"
        if quota["男"] > 0:
            quota["男"] -= 1
            return "男"
        return "男"

    def expanded_count_pairs(self, named_counts, target_total):
        total = sum(count for _, count in named_counts) or 1
        scaled = []
        assigned = 0
        remainders = []
        for index, (name, count) in enumerate(named_counts):
            exact = target_total * count / total
            base = int(exact)
            scaled.append([name, base])
            assigned += base
            remainders.append((exact - base, index))
        for _, index in sorted(remainders, reverse=True)[: max(target_total - assigned, 0)]:
            scaled[index][1] += 1
        return [(name, count) for name, count in scaled]

    def expand_named_counts(self, named_counts, target_total):
        expanded = []
        for name, count in self.expanded_count_pairs(named_counts, target_total):
            expanded.extend([name] * count)
        if len(expanded) < target_total and named_counts:
            expanded.extend([named_counts[-1][0]] * (target_total - len(expanded)))
        return expanded[:target_total]

    def scaled_count(self, count, base_total, target_total):
        if base_total <= 0 or target_total <= 0 or count <= 0:
            return 0
        return round(target_total * count / base_total)

    def build_even_index_set(self, total, count, offset=0):
        if total <= 0 or count <= 0:
            return set()
        indexes = set()
        for index in range(count):
            candidate = int((index * total) / count)
            indexes.add((candidate + offset) % total)
        return indexes

    def expected_graduation_date(self, grade, degree_type):
        digits = "".join(ch for ch in str(grade) if ch.isdigit())
        if len(digits) < 4:
            return None
        start_year = int(digits[:4])
        duration = 4 if degree_type == DegreeType.DOCTORAL else 3
        return date(start_year + duration, 6, 30)

    def make_aware_datetime(self, year, month, day, hour=9, minute=0):
        naive = datetime(year, month, day, hour, minute)
        return timezone.make_aware(naive, timezone.get_current_timezone())

    def workflow_tag(self, status):
        return {
            WorkflowStatus.DRAFT: "info",
            WorkflowStatus.PENDING: "warning",
            WorkflowStatus.IN_PROGRESS: "primary",
            WorkflowStatus.COMPLETED: "success",
            WorkflowStatus.REJECTED: "danger",
        }.get(status, "info")

    def change_step(self, change_type, status):
        if status == WorkflowStatus.COMPLETED:
            return "归档完成"
        if status == WorkflowStatus.IN_PROGRESS:
            return f"{change_type}审批中"
        if status == WorkflowStatus.PENDING:
            return "待学院审核"
        return "待提交"

    def build_admission_stages(self, cycle):
        if cycle.enrollment_type == EnrollmentType.INTERNATIONAL:
            stage_names = ["材料受理", "资格审核", "面试评审", "录取审批", "报到注册"]
        else:
            stage_names = ["报名受理", "资格审核", "复试组织", "拟录取公示", "正式录取"]

        current_year = timezone.localdate().year
        stage_objects = []
        for index, stage_name in enumerate(stage_names, start=1):
            start_month = min(12, index * 2 - 1)
            start_date = date(cycle.year, start_month, 1)
            end_date = start_date + timedelta(days=24)

            if cycle.year < current_year:
                status = WorkflowStatus.COMPLETED
                completion = 100
            elif index <= 2:
                status = WorkflowStatus.COMPLETED
                completion = 100
            elif index == 3:
                status = WorkflowStatus.IN_PROGRESS
                completion = 68
            else:
                status = WorkflowStatus.PENDING
                completion = 0

            stage_objects.append(
                AdmissionStageProgress(
                    cycle=cycle,
                    stage_name=stage_name,
                    start_date=start_date,
                    end_date=end_date,
                    status=status,
                    completion_percent=completion,
                    sort_order=index,
                )
            )
        return stage_objects

    def course_major(self, index):
        return REAL_MAJORS[index % len(REAL_MAJORS)]

    def course_schedule(self, semester, index):
        weekday = ["周一", "周二", "周三", "周四", "周五"][index % 5]
        period = ["1-2节", "3-4节", "5-6节", "7-8节"][index % 4]
        return f"{semester}{weekday}{period}"

    def split_amount(self, total_amount, count):
        if count <= 0:
            return []
        base, remainder = divmod(int(total_amount), count)
        return [Decimal(base + (1 if index < remainder else 0)) for index in range(count)]

    def split_integer(self, total, count):
        if count <= 0:
            return []
        base, remainder = divmod(total, count)
        return [base + (1 if index < remainder else 0) for index in range(count)]

    def unit_nature_for_destination(self, destination_type):
        if destination_type == "升学":
            return "高校"
        if destination_type == "出国出境":
            return "境外高校"
        if destination_type == "灵活就业":
            return "灵活就业"
        if destination_type == "":
            return ""
        return UNIT_NATURES[0]

    def industry_for_destination(self, destination_type, index):
        if destination_type == "升学":
            return "教育"
        if destination_type == "出国出境":
            return "国际教育"
        if destination_type == "灵活就业":
            return "自由职业"
        if destination_type == "":
            return ""
        return INDUSTRIES[index % len(INDUSTRIES)]

    def employer_name(self, destination_type, province, year, index):
        if destination_type == "":
            return ""
        if destination_type == "升学":
            return f"{province}某高校"
        if destination_type == "出国出境":
            return "境外高校/机构"
        if destination_type == "灵活就业":
            return f"{province}灵活就业平台"
        return f"{province}{year}用人单位{index + 1}"

    def prediction_risk_fields(
        self,
        course_average,
        credit_completion_rate,
        attendance_rate,
        training_rate,
        overdue_tasks,
        missed_checkins,
        wellbeing_score,
    ):
        issues = []
        if course_average < 75:
            issues.append("课程学习")
        if credit_completion_rate < 70:
            issues.append("培养进度")
        if attendance_rate < 90:
            issues.append("课堂考勤")
        if training_rate < 80:
            issues.append("培养节点")
        if overdue_tasks >= 2:
            issues.append("任务执行")
        if missed_checkins >= 2:
            issues.append("日常管理")
        if wellbeing_score < 75:
            issues.append("心理健康")

        if len(issues) >= 4 or wellbeing_score < 65:
            return RiskLevel.HIGH, "综合风险", "、".join(issues[:3]), "建议立即开展导师面谈和专项跟踪"
        if len(issues) >= 2 or course_average < 80:
            return RiskLevel.ALERT, "发展预警", "、".join(issues[:3]), "建议纳入月度关注名单并补强薄弱环节"
        if issues:
            return RiskLevel.MEDIUM, "轻度关注", "、".join(issues[:2]), "建议持续观察并跟进学习状态"
        return RiskLevel.LOW, "常规跟踪", "学业表现稳定", "维持当前培养节奏并定期复核"

    def graduation_progress_rate(self, grade, degree_type):
        digits = "".join(ch for ch in str(grade) if ch.isdigit())
        if len(digits) < 4:
            return 75
        start_year = int(digits[:4])
        current_year = timezone.localdate().year
        duration = 4 if degree_type == DegreeType.DOCTORAL else 3
        elapsed = max(current_year - start_year + 1, 1)
        return min(round(elapsed * 100 / duration, 1), 100)
