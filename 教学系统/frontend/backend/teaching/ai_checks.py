"""智能分析与预警：基于真实教务数据的只读统计和确定性规则。

预警仅代表需要人工核查的登记异常，不判定教学质量或学生正式学业风险。
规则完整检测与页面预览分开：页面最多返回 160 条，但同步不会只保存前 160 条。
"""
from collections import defaultdict
from datetime import datetime, timedelta
from django.utils import timezone
from .models import Semester, Course, TeachingClass, Exam, Grade
from .ai_grade_stats import summarize_grades
from .demo_history_logic import HISTORY, NORMALIZED, DEMO_NOTE
from django.db.models import Q
from .ai_operation_stats import summarize_operations

MAX_PREVIEW = 160
MAX_SCAN_ROWS = 5000
MAX_RULES = 50000


def current_semester():
    """遵循学期档案：先 is_current，再实际起止日期；不猜测学年的开学时间。"""
    marked = Semester.objects.filter(is_current=True).order_by("-start_date", "-id").first()
    if marked:
        return marked
    today = timezone.localdate()
    return Semester.objects.filter(start_date__lte=today, end_date__gte=today).order_by("-start_date", "-id").first()


def _local_datetime(value):
    if value is None:
        return None
    return timezone.localtime(value) if timezone.is_aware(value) else value


def week_number(value, start_date):
    """起始日期所在的周一为教学第 1 周；未知开学日期时不计算。"""
    if value is None or start_date is None:
        return None
    day = value.date() if isinstance(value, datetime) else value
    first_monday = start_date - timedelta(days=start_date.weekday())
    return ((day - first_monday).days // 7) + 1


def _warning(key, rule, category, severity, title, description, source, route, evidence, term):
    return {
        "key": key[:200], "rule_code": rule, "semester_key": term,
        "category": category, "severity": severity, "title": title,
        "description": description, "source": source, "route_path": route,
        "evidence": evidence,
    }


def _empty_overview():
    return {
        "semester": None,
        "summary": {"courses": 0, "teaching_classes": 0, "exams": 0, "published_grades": 0, "graded_students": 0},
        "analyses": {
            "grade": {**summarize_grades([]), "explanation": "未找到当前学期档案，不能统计当前学期成绩。"},
            "teaching": {"missing_schedule": 0, "over_capacity": 0, "missing_exam_location": 0,
                         "venue_collisions": 0, "week18_exams": None, "week19_exams": None, "operations": None},
        },
        "rule_preview": [], "rule_total": 0, "rules_complete": False,
        "data_notes": ["未找到标记为当前学期或日期覆盖今天的学期记录。请在学期管理核实 is_current 或起止日期；不将过往学期冒充当前学期。"],
    }


def collect_overview(include_all_rules=False):
    """include_all_rules 仅供服务端同步使用，且必须检查 rules_complete。"""
    semester = current_semester()
    if not semester:
        return _empty_overview()

    term = str(semester.name)
    courses = Course.objects.filter(semester=semester)
    class_qs = TeachingClass.objects.filter(semester=semester).select_related("course", "teacher")
    exam_qs = Exam.objects.filter(semester=semester).select_related("course")
    classes_count = class_qs.count()
    exams_count = exam_qs.count()
    # 超限后仍可展示部分结果，但绝不在不完整的数据上执行源风险消失判断。
    classes = list(class_qs.order_by("id")[:MAX_SCAN_ROWS])
    exams = list(exam_qs.order_by("exam_date", "id")[:MAX_SCAN_ROWS])
    complete = classes_count <= MAX_SCAN_ROWS and exams_count <= MAX_SCAN_ROWS

    grades = Grade.objects.filter(semester=semester, is_published=True)
    grade_stats = summarize_grades(grades.order_by().values_list(
        "student_id", "course_id", "course__name", "score", "exam__total_score"
    ).iterator(chunk_size=2000))

    # 教师字段在真实数据模型中为非空外键，原先的 missing_teacher 检查在正常库中无法触发。
    # 这里采用可以由现有业务字段直接核实的上课时间缺漏、选课人数超容量两类检查。
    inactive_statuses = {"停开", "已停开", "已取消", "取消", "已结课", "已结束"}
    active_classes = [c for c in classes if str(c.status or "").strip() not in inactive_statuses]
    operations = (summarize_operations(active_classes, exams, _local_datetime)
                  if classes_count <= MAX_SCAN_ROWS and exams_count <= MAX_SCAN_ROWS else None)
    missing_schedule = [c for c in active_classes if not str(c.schedule or "").strip()]
    over_capacity = [c for c in active_classes if c.capacity > 0 and c.enrolled_count > c.capacity]
    missing_locations = [e for e in exams if not str(e.location or "").strip()]

    warnings = []
    def append_rule(*args):
        nonlocal complete
        if len(warnings) >= MAX_RULES:
            complete = False
            return
        warnings.append(_warning(*args))

    for row in missing_schedule:
        append_rule(
            f"TCHSCHED:{semester.id}:{row.id}", "missing_schedule", "教学运行", "medium",
            f"教学班尚未登记上课时间：{row.class_name}",
            f"关联课程：{row.course.name}。请核查该教学班是否尚未完成排课登记。",
            "TeachingClass.schedule", "/course", {"teaching_class_id": row.id, "course_id": row.course_id}, term,
        )
    for row in over_capacity:
        append_rule(
            f"TCHCAP:{semester.id}:{row.id}", "over_capacity", "教学运行", "medium",
            f"教学班选课人数超过登记容量：{row.class_name}",
            f"计划容量 {row.capacity} 人，已登记选课 {row.enrolled_count} 人，请核查容量与人数是否准确。",
            "TeachingClass.capacity/enrolled_count", "/course",
            {"teaching_class_id": row.id, "capacity": row.capacity, "enrolled_count": row.enrolled_count}, term,
        )
    for row in missing_locations:
        start = _local_datetime(row.exam_date)
        append_rule(
            f"EXMLOC:{semester.id}:{row.id}", "missing_exam_location", "考试安排", "medium",
            f"考试尚未登记地点：{row.name}",
            f"考试时间：{start.strftime('%Y-%m-%d %H:%M') if start else '待录入'}；请核查考场登记。",
            "Exam.location", "/exam", {"exam_id": row.id}, term,
        )

    rooms = defaultdict(list)
    collision_count = 0
    # exams 已按开始时间升序。只保留当前时刻尚未结束的同一考场考试，避免逐房间全历史 O(n²)。
    for row in exams:
        room = str(row.location or "").strip()
        start = _local_datetime(row.exam_date)
        if not room or start is None:
            continue
        end = start + timedelta(minutes=max(1, int(row.duration or 120)))
        active = [(prior, prior_end) for prior, prior_end in rooms[room] if prior_end > start]
        for prior, _ in active:
            collision_count += 1
            ids = sorted((prior.id, row.id))
            append_rule(
                f"EXMROOM:{semester.id}:{ids[0]}:{ids[1]}", "room_time_overlap", "考试安排", "high",
                f"同一考场考试时间重叠：{room}",
                f"“{prior.name}”与“{row.name}”在该考场的考试时间存在重叠。",
                "Exam.exam_date/duration/location", "/exam",
                {"exam_ids": ids, "location": room}, term,
            )
        active.append((row, end))
        rooms[room] = active

    week18 = week19 = None
    if semester.start_date is not None:
        weeks = [week_number(_local_datetime(e.exam_date), semester.start_date) for e in exams]
        week18 = sum(w == 18 for w in weeks)
        week19 = sum(w == 19 for w in weeks)

    demo_data = Grade.objects.filter(Q(remark__startswith=HISTORY) | Q(remark__startswith=NORMALIZED)).exists()
    notes = [
        "所有统计均来自本学期教务数据库。规则命中表示需要人工核查，不等于已经确认教学事故。",
        "成绩统计采用已发布的百分制考核记录，不是学生最终课程成绩；记录占比不等于学生占比。",
        "未配置学校认可的学业风险阈值，系统不会自动创建成绩类预警。",
        "页面最多预览 160 项，但同步使用完成扫描后的全部规则事项。",
    ]
    if demo_data:
        notes.insert(0, DEMO_NOTE)
    if semester.start_date is None:
        notes.append("学期未登记开始日期，因此不计算第18/19教学周；请在学期管理维护起始日期。")
    else:
        notes.append("教学周按照学期开始日期所在的周一推算，并非校方另行公布的考试周通知。")
    if not complete:
        notes.append("登记记录或规则数量超过单次扫描上限：页面可能只显示部分异常；为防止漏判，本次禁止同步台账。")

    data = {
        "semester": {"id": semester.id, "name": term},
        "summary": {"courses": courses.count(), "teaching_classes": classes_count, "exams": exams_count,
                    "published_grades": grade_stats["published_records"],
                    "graded_students": grade_stats["graded_students"]},
        "analyses": {
            "grade": grade_stats,
            "teaching": {"missing_schedule": len(missing_schedule), "over_capacity": len(over_capacity),
                         "active_classes_scanned": len(active_classes),
                         "missing_exam_location": len(missing_locations), "venue_collisions": collision_count,
                         "week18_exams": week18, "week19_exams": week19, "operations": operations},
        },
        "rule_preview": warnings[:MAX_PREVIEW], "rule_total": len(warnings),
        "rules_complete": complete, "data_notes": notes, "demo_data": demo_data,
    }
    if include_all_rules:
        data["_full_rules"] = warnings
    return data
