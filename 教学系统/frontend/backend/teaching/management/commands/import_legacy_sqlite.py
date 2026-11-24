from __future__ import annotations

import sqlite3
from collections import Counter, defaultdict
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlparse

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.utils import timezone

from teaching.models import (
    College, Semester, UserProfile, Teacher, Student, Course,
    TeachingClass, Exam, Grade, Notice,
)

SOURCE_COUNTS = {
    "auth_user": 61,
    "dashboard_college": 7,
    "dashboard_semester": 3,
    "course_info": 10,
    "teacher_info": 10,
    "student_info": 139,
    "exam_info": 10,
    "grade_info": 3621,
    "notice_info": 5,
}
TARGET_COUNTS = {
    "学院": (College, 6),
    "学期": (Semester, 3),
    "课程": (Course, 10),
    "教师": (Teacher, 10),
    "学生": (Student, 139),
    "教学班": (TeachingClass, 0),
    "考试": (Exam, 10),
    "成绩": (Grade, 3621),
    "通知": (Notice, 5),
    "用户档案": (UserProfile, 61),
}
COURSE_TYPES = {"required": "必修", "public": "公共课", "elective": "选修"}
GENDERS = {"male": "男", "female": "女", "男": "男", "女": "女", "": "未说明", None: "未说明"}
TITLES = {"professor": "教授", "associate_professor": "副教授", "lecturer": "讲师", "assistant": "助教"}
EXAM_TYPES = {"final": "期末考试", "midterm": "期中考试", "makeup": "补考", "course": "课程考核"}
GRADE_TYPES = {"final": "期末", "midterm": "期中", "usual": "平时"}
NOTICE_TYPES = {"info": "info", "warning": "warning", "success": "success"}
ROLES = {"admin": "admin", "teacher": "teacher", "student": "student"}


def norm(value):
    return str(value or "").strip().casefold()


def text(value):
    return str(value or "").strip()


def as_date(value):
    if not value:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    return date.fromisoformat(str(value)[:10])


def as_datetime(value):
    if not value:
        return None
    dt = value if isinstance(value, datetime) else datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())
    return dt


def dec(value, default="0"):
    return Decimal(str(default if value is None or value == "" else value))


def match_person(user, records):
    email = norm(user.get("email"))
    name = norm(text(user.get("first_name")) + text(user.get("last_name")))
    if not email or not name:
        return None
    by_email = [p for p in records if norm(p.get("email")) == email]
    by_name = [p for p in records if norm(p.get("name")) == name]
    if len(by_email) == len(by_name) == 1 and int(by_email[0]["id"]) == int(by_name[0]["id"]):
        return int(by_email[0]["id"])
    return None


class Command(BaseCommand):
    help = "Read-only dry run by default. Add --execute to import the audited legacy SQLite data once."

    def add_arguments(self, parser):
        parser.add_argument("--source", required=True, help="Absolute path to the old db.sqlite3")
        parser.add_argument("--execute", action="store_true", help="Perform the import; without this flag nothing is written")

    def handle(self, *args, **opts):
        path = Path(opts["source"]).expanduser().resolve()
        if not path.is_file():
            raise CommandError(f"找不到旧 SQLite 数据库：{path}")
        if connection.settings_dict.get("ENGINE") != "django.db.backends.mysql":
            raise CommandError("当前目标数据库不是 MySQL，已停止。")
        if connection.settings_dict.get("NAME") != "college_teaching":
            raise CommandError("目标数据库名称不是 college_teaching，已停止，防止导入错误数据库。")

        source = self.read_source(path)
        self.validate_source(source)
        admin = self.validate_target()
        matches = self.resolve_accounts(source)
        outside = self.count_exam_date_outliers(source)
        nonfinal_links, final_mismatches = self.grade_exam_issues(source)
        if final_mismatches:
            raise CommandError(
                f"发现 {final_mismatches} 条期末成绩缺少有效的期末考试关联 "
                "（考试不存在、类型不符或课程不一致），已停止。"
            )

        self.stdout.write("\n" + "=" * 68)
        self.stdout.write("旧 SQLite -> Django/MySQL 数据迁移预演")
        self.stdout.write("=" * 68)
        self.stdout.write(f"旧数据库：{path}")
        self.stdout.write(f"目标数据库：{connection.settings_dict['NAME']} @ {connection.settings_dict['HOST']}:{connection.settings_dict['PORT']}")
        self.stdout.write(f"保留现有管理员：{admin.username}；不覆盖该账号的密码或资料")
        self.stdout.write("\n源数据行数：")
        for table, count in SOURCE_COUNTS.items():
            self.stdout.write(f"  {table}: {len(source[table])}")
        self.stdout.write("\n计划导入的目标记录：")
        for label, (_, count) in TARGET_COUNTS.items():
            self.stdout.write(f"  {label}: {count}")
        self.stdout.write("  用户账号: 61（旧管理员映射到现有管理员，不重复创建）")
        self.stdout.write("\n账号映射：")
        self.stdout.write(f"  教师唯一匹配：{len(matches['teacher'])}/10")
        self.stdout.write(f"  学生唯一匹配：{len(matches['student'])}/50；其余账号不猜测档案关联")
        self.stdout.write("\n异常保留策略：")
        self.stdout.write(f"  重名学院组：{len(self.duplicate_colleges(source))}；按名称合并，优先保留非空单位代码及引用较多的记录")
        self.stdout.write(f"  考试日期超出所属学期：{outside}/10；保留原日期和学期，状态标记为“待核实”")
        self.stdout.write(f"  期中/平时成绩错误关联到期末考试：{nonfinal_links} 条；解除考试外键并写入备注保留旧考试 ID")
        self.stdout.write(f"  GPA 为空的成绩：{sum(r.get('gpa') is None for r in source['grade_info'])}；保持为空")
        self.stdout.write("  旧库没有成绩发布字段；目标成绩统一设为未发布")
        self.stdout.write("  旧库没有教学班数据；不生成虚构教学班")

        if not opts["execute"]:
            self.stdout.write(self.style.WARNING("\nDRY RUN 完成：没有写入、修改或删除任何目标数据。"))
            self.stdout.write("确认预演结果后，再用相同命令追加 --execute。")
            return

        self.stdout.write(self.style.WARNING("\n检测到 --execute，开始执行单事务导入。"))
        with transaction.atomic():
            admin = self.validate_target()
            maps = self.import_business(source)
            user_map = self.import_users(source, admin)
            self.import_profiles(source, user_map, maps, matches)
            self.import_grades(source, maps)
            self.import_notices(source, user_map)

            problems = []
            for label, (model, expected) in TARGET_COUNTS.items():
                actual = model.objects.count()
                if actual != expected:
                    problems.append(f"{label}: 预期 {expected}，实际 {actual}")
            User = get_user_model()
            if User.objects.count() != 61:
                problems.append(f"用户账号: 预期 61，实际 {User.objects.count()}")
            expected_exam_links = sum(r["grade_type"] == "final" for r in source["grade_info"])
            if Grade.objects.filter(exam__isnull=False).count() != expected_exam_links:
                problems.append("成绩关联考试数量与期末成绩数量不一致")
            if UserProfile.objects.filter(role="teacher", teacher__isnull=False).count() != 10:
                problems.append("教师用户档案关联数不为 10")
            if UserProfile.objects.filter(role="student", student__isnull=False).count() != len(matches["student"]):
                problems.append("学生用户档案关联数与唯一匹配结果不一致")
            if problems:
                raise CommandError("导入后验证失败，事务将回滚：\n  " + "\n  ".join(problems))

        self.stdout.write(self.style.SUCCESS("\n迁移完成：目标记录数及关键账号/成绩关联检查均通过。"))
        self.stdout.write("考试日期与学期的冲突已保留，需业务核实后再单独修正。")

    def read_source(self, path):
        conn = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        try:
            integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
            if integrity != "ok":
                raise CommandError(f"SQLite 完整性检查失败：{integrity}")
            fk = list(conn.execute("PRAGMA foreign_key_check"))
            if fk:
                raise CommandError(f"旧库存在 {len(fk)} 条外键违规，已停止。")
            tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            missing = sorted(set(SOURCE_COUNTS) - tables)
            if missing:
                raise CommandError(f"旧库缺少必要表：{missing}")
            rows = {t: [dict(r) for r in conn.execute(f'SELECT * FROM "{t}"')] for t in SOURCE_COUNTS}
            return rows
        finally:
            conn.close()

    def validate_source(self, src):
        for table, expected in SOURCE_COUNTS.items():
            if len(src[table]) != expected:
                raise CommandError(f"{table} 当前 {len(src[table])} 条，与已审计基准 {expected} 条不同；停止迁移。")
        for table, field in [("auth_user", "username"), ("dashboard_semester", "name"), ("course_info", "code"), ("teacher_info", "teacher_no"), ("student_info", "student_no")]:
            vals = [r.get(field) for r in src[table]]
            if len(vals) != len(set(vals)):
                raise CommandError(f"{table}.{field} 存在重复值，与目标唯一约束冲突。")
        grade_keys = [(r["student_id"], r["course_id"], r["semester_id"], r["grade_type"]) for r in src["grade_info"]]
        if len(grade_keys) != len(set(grade_keys)):
            raise CommandError("旧成绩表存在重复的学生+课程+学期+类型组合。")
        roles = Counter(r.get("role") for r in src["auth_user"])
        if roles != Counter({"admin": 1, "teacher": 10, "student": 50}):
            raise CommandError(f"旧账号角色分布与已审计结果不同：{dict(roles)}")
        if any(
            r.get("role") != "admin" and (bool(r.get("is_staff")) or bool(r.get("is_superuser")))
            for r in src["auth_user"]
        ):
            raise CommandError("旧教师/学生账号中存在 staff/superuser 权限，需人工核实后再迁移。")
        if not any(
            r.get("role") == "admin" and bool(r.get("is_staff")) and bool(r.get("is_superuser"))
            for r in src["auth_user"]
        ):
            raise CommandError("旧库管理员账号未同时具备 staff/superuser 标志，需人工核实。")
        if any(not text(r.get("password")).startswith("pbkdf2_sha256$") for r in src["auth_user"]):
            raise CommandError("发现非 pbkdf2_sha256 密码摘要，停止以避免账号迁移后无法登录。")
        for r in src["course_info"]:
            if r.get("course_type") not in COURSE_TYPES:
                raise CommandError(f"未知课程类型 {r.get('course_type')!r}，课程 ID={r.get('id')}")
            credit = dec(r.get("credit"))
            if credit != credit.quantize(Decimal("0.1")):
                raise CommandError(f"课程 ID={r.get('id')} 的学分精度超过目标模型支持范围。")
        for r in src["student_info"] + src["teacher_info"]:
            if r.get("gender") not in GENDERS:
                raise CommandError(f"未知性别值 {r.get('gender')!r}，记录 ID={r.get('id')}")
        for r in src["exam_info"]:
            if r.get("exam_type") not in EXAM_TYPES:
                raise CommandError(f"未知考试类型 {r.get('exam_type')!r}，考试 ID={r.get('id')}")
        for r in src["grade_info"]:
            if r.get("grade_type") not in GRADE_TYPES:
                raise CommandError(f"未知成绩类型 {r.get('grade_type')!r}，成绩 ID={r.get('id')}")
            score = dec(r.get("score"))
            if score < 0 or score > 100:
                raise CommandError(f"成绩 ID={r.get('id')} 超出 0–100：{score}")
        for r in src["notice_info"]:
            if r.get("notice_type") not in NOTICE_TYPES:
                raise CommandError(f"未知通知类型 {r.get('notice_type')!r}，通知 ID={r.get('id')}")
        # Explicitly verify foreign keys as well as SQLite's own check.
        ids = {
            "college": {int(r["id"]) for r in src["dashboard_college"]},
            "semester": {int(r["id"]) for r in src["dashboard_semester"]},
            "course": {int(r["id"]) for r in src["course_info"]},
            "teacher": {int(r["id"]) for r in src["teacher_info"]},
            "student": {int(r["id"]) for r in src["student_info"]},
            "exam": {int(r["id"]) for r in src["exam_info"]},
            "user": {int(r["id"]) for r in src["auth_user"]},
        }
        checks = [
            ("course_info", "college_id", "college"), ("course_info", "semester_id", "semester"),
            ("teacher_info", "college_id", "college"), ("student_info", "college_id", "college"),
            ("exam_info", "course_id", "course"), ("exam_info", "semester_id", "semester"),
            ("grade_info", "student_id", "student"), ("grade_info", "course_id", "course"),
            ("grade_info", "semester_id", "semester"), ("grade_info", "exam_id", "exam"),
            ("notice_info", "publisher_id", "user"),
        ]
        for table, field, ref in checks:
            for r in src[table]:
                value = r.get(field)
                if value is not None and int(value) not in ids[ref]:
                    raise CommandError(f"外键不存在：{table}.{field}={value}，记录 ID={r.get('id')}")

    def validate_target(self):
        User = get_user_model()
        counts = {label: model.objects.count() for label, (model, _) in TARGET_COUNTS.items()}
        nonempty = {label: n for label, n in counts.items() if n != 0}
        if nonempty:
            raise CommandError(f"目标业务表不是空表，停止以防重复导入：{nonempty}")
        users = list(User.objects.all())
        admins = [u for u in users if u.is_staff and u.is_superuser]
        if len(users) != 1 or len(admins) != 1:
            raise CommandError(f"目标用户表必须恰好只有一个现有管理员；用户数={len(users)}，管理员数={len(admins)}")
        return admins[0]

    def resolve_accounts(self, src):
        User = get_user_model()
        target_names = set(User.objects.values_list("username", flat=True))
        collisions = [r["username"] for r in src["auth_user"] if r["role"] != "admin" and r["username"] in target_names]
        if collisions:
            raise CommandError(f"旧教师/学生用户名与目标账号冲突：{collisions}；不会覆盖任何账号。")
        teacher_users = [r for r in src["auth_user"] if r["role"] == "teacher"]
        student_users = [r for r in src["auth_user"] if r["role"] == "student"]
        teacher_matches = {int(u["id"]): pid for u in teacher_users if (pid := match_person(u, src["teacher_info"])) is not None}
        student_matches = {int(u["id"]): pid for u in student_users if (pid := match_person(u, src["student_info"])) is not None}
        if len(teacher_matches) != 10:
            raise CommandError(f"教师账号唯一匹配数为 {len(teacher_matches)}/10，与此前审计不一致。")
        if len(student_matches) != 1:
            raise CommandError(f"学生账号唯一匹配数为 {len(student_matches)}/50，与此前审计不一致。")
        return {"teacher": teacher_matches, "student": student_matches}

    @staticmethod
    def duplicate_colleges(src):
        groups = defaultdict(list)
        for r in src["dashboard_college"]:
            if not norm(r.get("name")):
                raise CommandError("旧学院存在空名称，无法安全合并。")
            groups[norm(r["name"])].append(r)
        return [g for g in groups.values() if len(g) > 1]

    def count_exam_date_outliers(self, src):
        semesters = {int(s["id"]): s for s in src["dashboard_semester"]}
        total = 0
        for e in src["exam_info"]:
            s = semesters[int(e["semester_id"])]
            day, start, end = as_date(e["exam_date"]), as_date(s["start_date"]), as_date(s["end_date"])
            if start and end and not (start <= day <= end):
                total += 1
        return total

    @staticmethod
    def grade_exam_issues(src):
        exams = {int(e["id"]): e for e in src["exam_info"]}
        nonfinal, final_mismatch = 0, 0

        for grade in src["grade_info"]:
            exam_id = grade.get("exam_id")
            exam = (
                exams.get(int(exam_id))
                if exam_id is not None
                else None
            )

            if (
                exam is not None
                and grade["grade_type"] != "final"
                and exam["exam_type"] == "final"
            ):
                nonfinal += 1

            if grade["grade_type"] == "final":
                if (
                    exam is None
                    or exam["exam_type"] != "final"
                    or int(exam["course_id"]) != int(grade["course_id"])
                ):
                    final_mismatch += 1

        return nonfinal, final_mismatch

    def import_business(self, src):
        college_map, semester_map, course_map, teacher_map, student_map, exam_map = {}, {}, {}, {}, {}, {}
        references = Counter()
        for table in ("course_info", "teacher_info", "student_info"):
            for r in src[table]:
                if r.get("college_id") is not None:
                    references[int(r["college_id"])] += 1
        groups = defaultdict(list)
        for r in src["dashboard_college"]:
            groups[norm(r["name"])].append(r)
        for group in groups.values():
            chosen = max(group, key=lambda r: (bool(text(r.get("code"))), references[int(r["id"])], -int(r["id"])))
            obj = College.objects.create(name=text(chosen["name"]), code=text(chosen.get("code")), description="", is_active=True)
            for r in group:
                college_map[int(r["id"])] = obj
        for r in sorted(src["dashboard_semester"], key=lambda x: int(x["id"])):
            semester_map[int(r["id"])] = Semester.objects.create(
                name=text(r["name"]), academic_year=text(r.get("academic_year")), term=text(r.get("term")),
                start_date=as_date(r.get("start_date")), end_date=as_date(r.get("end_date")), is_current=bool(r.get("is_current")),
            )
        for r in sorted(src["course_info"], key=lambda x: int(x["id"])):
            course_map[int(r["id"])] = Course.objects.create(
                code=text(r["code"]), name=text(r["name"]), credit=dec(r.get("credit")).quantize(Decimal("0.1")),
                hours=int(r.get("hours") or 0), college=college_map[int(r["college_id"])],
                semester=semester_map.get(int(r["semester_id"])) if r.get("semester_id") is not None else None,
                course_type=COURSE_TYPES[r["course_type"]], description=text(r.get("description")), is_active=True,
            )
        for r in sorted(src["teacher_info"], key=lambda x: int(x["id"])):
            title = text(r.get("title"))
            teacher_map[int(r["id"])] = Teacher.objects.create(
                teacher_no=text(r["teacher_no"]), name=text(r["name"]), gender=GENDERS[r.get("gender")],
                college=college_map[int(r["college_id"])], title=TITLES.get(title, title), phone=text(r.get("phone")),
                email=text(r.get("email")), description=text(r.get("description")), is_active=True,
            )
        for r in sorted(src["student_info"], key=lambda x: int(x["id"])):
            student_map[int(r["id"])] = Student.objects.create(
                student_no=text(r["student_no"]), name=text(r["name"]), gender=GENDERS[r.get("gender")],
                college=college_map[int(r["college_id"])], major=text(r.get("major")), grade=text(r.get("grade")),
                class_name=text(r.get("class_name")), email=text(r.get("email")), phone=text(r.get("phone")),
                enrollment_year=int(r["enrollment_year"]), is_active=True,
            )
        semesters_src = {int(s["id"]): s for s in src["dashboard_semester"]}
        for r in sorted(src["exam_info"], key=lambda x: int(x["id"])):
            s = semesters_src[int(r["semester_id"])]
            day, start, end = as_date(r["exam_date"]), as_date(s["start_date"]), as_date(s["end_date"])
            outside = bool(start and end and not (start <= day <= end))
            exam_map[int(r["id"])] = Exam.objects.create(
                name=text(r["name"]), course=course_map[int(r["course_id"])], semester=semester_map[int(r["semester_id"])],
                exam_type=EXAM_TYPES[r["exam_type"]], exam_date=as_datetime(r["exam_date"]),
                duration=int(r.get("duration") or 120), total_score=dec(r.get("total_score") or 100).quantize(Decimal("0.1")),
                location=text(r.get("location")), status="待核实" if outside else "待安排",
            )
        return {"college": college_map, "semester": semester_map, "course": course_map, "teacher": teacher_map, "student": student_map, "exam": exam_map}

    def import_users(self, src, target_admin):
        User = get_user_model()
        user_map = {}
        old_admins = [u for u in src["auth_user"] if u["role"] == "admin"]
        if len(old_admins) != 1:
            raise CommandError("旧库管理员账号不唯一，停止。")
        user_map[int(old_admins[0]["id"])] = target_admin
        for r in sorted(src["auth_user"], key=lambda x: int(x["id"])):
            if r["role"] == "admin":
                continue
            # Keep the original Django password hash; do not call set_password().
            user = User(
                username=text(r["username"]), password=text(r["password"]),
                first_name=text(r.get("first_name")), last_name=text(r.get("last_name")), email=text(r.get("email")),
                is_staff=bool(r.get("is_staff")), is_superuser=bool(r.get("is_superuser")), is_active=bool(r.get("is_active")),
                last_login=as_datetime(r.get("last_login")), date_joined=as_datetime(r.get("date_joined")) or timezone.now(),
            )
            user.save(force_insert=True)
            user_map[int(r["id"])] = user
        return user_map

    def import_profiles(self, src, user_map, maps, matches):
        for r in sorted(src["auth_user"], key=lambda x: int(x["id"])):
            role = ROLES[r["role"]]
            teacher = student = college = None
            if role == "teacher" and int(r["id"]) in matches["teacher"]:
                teacher = maps["teacher"][matches["teacher"][int(r["id"])]]
                college = teacher.college
            elif role == "student" and int(r["id"]) in matches["student"]:
                student = maps["student"][matches["student"][int(r["id"])]]
                college = student.college
            avatar = text(r.get("avatar"))
            parsed = urlparse(avatar)
            if not (parsed.scheme in {"http", "https"} and parsed.netloc):
                avatar = ""
            UserProfile.objects.create(user=user_map[int(r["id"])], role=role, college=college, teacher=teacher, student=student, avatar=avatar)

    def import_grades(self, src, maps):
        exams = {int(e["id"]): e for e in src["exam_info"]}
        for r in sorted(src["grade_info"], key=lambda x: int(x["id"])):
            old_exam = exams.get(int(r["exam_id"])) if r.get("exam_id") is not None else None
            linked_exam, exam_day, remark = None, None, ""
            if (
                r["grade_type"] == "final"
                and old_exam is not None
                and old_exam["exam_type"] == "final"
                and int(old_exam["course_id"]) == int(r["course_id"])
            ):
                linked_exam = maps["exam"][int(old_exam["id"])]
                exam_day = as_date(old_exam["exam_date"])
            elif old_exam:
                remark = (
                    f"迁移说明：旧系统考试ID={old_exam['id']}，原成绩类型={r['grade_type']}，"
                    f"原关联考试类型={old_exam.get('exam_type')}；为避免错误关联，未绑定该考试。"
                )
            Grade.objects.create(
                student=maps["student"][int(r["student_id"])], course=maps["course"][int(r["course_id"])],
                semester=maps["semester"].get(int(r["semester_id"])) if r.get("semester_id") is not None else None,
                exam=linked_exam, score=dec(r.get("score")).quantize(Decimal("0.01")),
                grade_point=dec(r.get("gpa")).quantize(Decimal("0.01")) if r.get("gpa") is not None else None,
                exam_type=GRADE_TYPES[r["grade_type"]], exam_date=exam_day, remark=remark,
                # The old schema has no publication field, so do not infer that grades were published.
                is_published=False,
            )

    def import_notices(self, src, user_map):
        for r in sorted(src["notice_info"], key=lambda x: int(x["id"])):
            created = as_datetime(r.get("created_at")) or timezone.now()
            updated = as_datetime(r.get("updated_at")) or created
            notice = Notice.objects.create(
                title=text(r["title"]), content=text(r["content"]), notice_type=NOTICE_TYPES[r["notice_type"]],
                publisher=user_map.get(int(r["publisher_id"])) if r.get("publisher_id") is not None else None,
                is_published=bool(r.get("is_published")),
            )
            # auto_now fields override values on save; QuerySet.update preserves source timestamps.
            Notice.objects.filter(pk=notice.pk).update(created_at=created, updated_at=updated)
