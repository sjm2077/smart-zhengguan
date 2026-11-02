from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from openpyxl import load_workbook
from django.utils import timezone

from apps.graduate.management.commands.import_excel_data import Command
from apps.graduate.models import (
    DegreeType,
    EnrollmentType,
    PredictionMonthlyMetric,
    PredictionSnapshot,
    Student,
    StudentStatus,
)


WORKBOOK_NAME = "研究生数据_2021-2026.xlsx"
PREDICTION_SHEET = "智能预测-学生数据"
TARGET_COLLEGE = "政治学与公共管理学院"


def degree_type_from_label(label):
    text = str(label or "").strip()
    if text == "博士":
        return DegreeType.DOCTORAL, EnrollmentType.DOCTORAL
    return DegreeType.ACADEMIC_MASTER, EnrollmentType.MASTER


def graduation_status_text(text):
    return "已完成" if str(text or "").strip() == "已完成" else "进行中"


def numeric(row, key, default=0):
    value = row.get(key, default)
    if value in (None, ""):
        return default
    return value


def main():
    root = Path.cwd().parent
    workbook_path = root / WORKBOOK_NAME
    workbook = load_workbook(workbook_path, read_only=True, data_only=True)
    worksheet = workbook[PREDICTION_SHEET]
    iterator = worksheet.iter_rows(values_only=True)
    headers = next(iterator)
    rows = [dict(zip(headers, row)) for row in iterator if any(value not in (None, "") for value in row)]

    importer = Command()
    importer.ensure_prediction_indicators()

    PredictionMonthlyMetric.objects.all().delete()
    PredictionSnapshot.objects.all().delete()

    now = timezone.now()
    created_count = 0

    for index, row in enumerate(rows):
        degree_type, enrollment_type = degree_type_from_label(row.get("类别"))
        student, _ = Student.objects.update_or_create(
            student_id=str(row.get("学号") or "").strip(),
            defaults={
                "name": str(row.get("姓名") or "").strip(),
                "gender": "",
                "college": TARGET_COLLEGE,
                "major": str(row.get("专业") or "公开报道未注明").strip(),
                "grade": str(row.get("年级") or "").strip(),
                "degree_type": degree_type,
                "enrollment_type": enrollment_type,
                "source_region": "",
                "advisor_name": str(row.get("导师") or "").strip(),
                "current_status": StudentStatus.ACTIVE,
                "is_international": False,
            },
        )

        course_average = float(numeric(row, "课程成绩"))
        credit_completion_rate = float(numeric(row, "学分完成情况"))
        attendance_rate = float(numeric(row, "考勤情况"))
        training_rate = 100.0 if graduation_status_text(row.get("培养节点完成情况")) == "已完成" else 72.0
        overdue_tasks = int(numeric(row, "任务逾期次数"))
        missed_checkins = int(numeric(row, "未打卡记录次数"))
        wellbeing_score = float(numeric(row, "心理测评分数"))
        advisor_score = float(numeric(row, "导师评价分数"))
        risk_level, risk_type, risk_field, suggestion = importer.prediction_risk_fields(
            course_average,
            credit_completion_rate,
            attendance_rate,
            training_rate,
            overdue_tasks,
            missed_checkins,
            wellbeing_score,
        )

        snapshot = PredictionSnapshot.objects.create(
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
            research_output_count=int(numeric(row, "科研成果数量")),
            project_participation_count=int(numeric(row, "科研项目参与数量")),
            activity_hours=int(numeric(row, "活动时长")),
            activity_count=int(numeric(row, "活动参与次数")),
            practice_hours=int(numeric(row, "社会实践时长")),
            practice_report_count=int(numeric(row, "社会实践次数")),
            advisor_evaluation_score=Decimal(str(advisor_score)),
            advisor_meeting_count_60d=int(numeric(row, "导师沟通次数")),
            advisor_avg_response_days=max(1, 10 - int(numeric(row, "导师沟通次数")) // 2),
            missed_checkins=missed_checkins,
            wellbeing_score=Decimal(str(wellbeing_score)),
            training_plan_completion_rate=Decimal(str(training_rate)),
            graduation_progress_rate=Decimal(str(importer.graduation_progress_rate(student.grade, student.degree_type))),
            overdue_tasks_count=overdue_tasks,
            captured_at=now - timedelta(days=index),
        )

        for month_index in range(6):
            month_date = timezone.localdate() - timedelta(days=30 * (5 - month_index))
            decay = 5 - month_index
            PredictionMonthlyMetric.objects.create(
                snapshot=snapshot,
                month=month_date.strftime("%Y-%m"),
                course_average=Decimal(str(max(course_average - decay * 1.2, 60))),
                credit_completion_rate=Decimal(str(max(credit_completion_rate - decay, 50))),
                attendance_rate=Decimal(str(max(attendance_rate - decay * 0.8, 65))),
                research_task_completion_rate=Decimal(str(max(training_rate - decay * 1.5, 45))),
                activity_hours=max(int(numeric(row, "活动时长")) - decay * 2, 0),
                practice_hours=max(int(numeric(row, "社会实践时长")) - decay * 2, 0),
                advisor_meeting_count=max(1, 6 - decay),
                advisor_evaluation_score=Decimal(str(max(advisor_score - decay * 0.6, 60))),
                wellbeing_score=Decimal(str(max(wellbeing_score - decay * 0.7, 55))),
            )

        created_count += 1

    print(f"synced public prediction samples: {created_count}")


main()
