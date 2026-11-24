# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from teaching.models import (
    College,
    Course,
    Exam,
    Student,
    Teacher,
    TeachingClass,
    UserProfile,
)

COLLEGE_NAME = "政治学与公共管理学院"
COLLEGE_CODE = "SPPA"

MAJORS = [
    "政治学与行政学",
    "行政管理",
    "国际政治",
    "科学社会主义",
]

COURSE_BLUEPRINT = [
    ("SPPA101", "政治学原理", "必修", "政治学基础理论与核心概念"),
    ("SPPA102", "公共管理学", "必修", "公共管理基本理论、组织与治理"),
    ("SPPA201", "行政管理学", "必修", "行政组织、行政运行与管理实践"),
    ("SPPA202", "国际政治学概论", "必修", "国际政治基本理论与国际关系分析"),
    ("SPPA203", "社会调查研究方法", "必修", "社会科学调查设计、资料收集与分析"),
    ("SPPA204", "中国政府与政治", "必修", "中国政府体系、制度与政治运行"),
    ("SPPA301", "公共政策分析", "必修", "公共政策过程、工具与分析方法"),
    ("SPPA302", "比较政治学", "选修", "比较政治制度、政治过程与治理模式"),
    ("SPPA303", "行政法与行政诉讼法", "选修", "行政法基础与行政救济制度"),
    ("SPPA304", "数字政府与治理", "选修", "数字政府建设、数据治理与公共服务创新"),
]

SCHEDULES = [
    ("周一第1-2节", "演示教室A-101"),
    ("周一第3-4节", "演示教室A-201"),
    ("周二第1-2节", "演示教室A-301"),
    ("周二第3-4节", "演示教室B-101"),
    ("周三第1-2节", "演示教室B-201"),
    ("周三第3-4节", "演示教室B-301"),
    ("周四第1-2节", "演示教室C-101"),
    ("周四第3-4节", "演示教室C-201"),
    ("周五第1-2节", "演示教室C-301"),
    ("周五第3-4节", "演示教室D-101"),
]


class Command(BaseCommand):
    help = (
        "将当前纯开发/演示数据库统一规范为山东大学政治学与公共管理学院主题。"
        "默认只预览；添加 --execute 后才写入。"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--execute",
            action="store_true",
            help="真正执行数据库修改；不带该参数时仅 DRY-RUN。",
        )

    def handle(self, *args, **options):
        execute = options["execute"]

        students = list(Student.objects.select_related("college").order_by("id"))
        teachers = list(Teacher.objects.select_related("college").order_by("id"))
        courses = list(Course.objects.select_related("college").order_by("id"))
        classes = list(TeachingClass.objects.order_by("id"))
        exams = list(Exam.objects.order_by("id"))

        if len(courses) != len(COURSE_BLUEPRINT):
            raise CommandError(
                f"当前课程数为 {len(courses)}，而规范化脚本预期为 "
                f"{len(COURSE_BLUEPRINT)}。为避免错误映射，已停止。"
            )

        # 固定使用课程主键建立映射；教学班和考试名称不依赖缓存的旧课程对象。
        course_blueprint_by_id = {
            course.id: blueprint
            for course, blueprint in zip(courses, COURSE_BLUEPRINT)
        }

        self.stdout.write("=" * 88)
        self.stdout.write("山东大学政治学与公共管理学院 — 演示数据主题统一")
        self.stdout.write("=" * 88)
        self.stdout.write(f"模式            : {'EXECUTE' if execute else 'DRY-RUN'}")
        self.stdout.write(f"学生            : {len(students)}")
        self.stdout.write(f"教师            : {len(teachers)}")
        self.stdout.write(f"课程            : {len(courses)}")
        self.stdout.write(f"教学班          : {len(classes)}")
        self.stdout.write(f"考试            : {len(exams)}")
        self.stdout.write(f"当前学院记录    : {College.objects.count()}")
        self.stdout.write("")

        self.stdout.write("[课程映射预览]")
        for course in courses:
            new_code, new_name, new_type, _ = course_blueprint_by_id[course.id]
            self.stdout.write(
                f"  id={course.id:<3} {course.code} / {course.name}"
                f"  ->  {new_code} / {new_name} / {new_type}"
            )

        self.stdout.write("")
        self.stdout.write("[学生主题预览]")
        for index, student in enumerate(students[:8]):
            major = MAJORS[index % len(MAJORS)]
            class_no = (index // len(MAJORS)) % 2 + 1
            old_college = student.college.name if student.college else "未关联学院"
            self.stdout.write(
                f"  {student.student_no} {student.name}: "
                f"{old_college} / {student.major} / {student.class_name}"
                f"  ->  {COLLEGE_NAME} / {major} / {major}{class_no}班"
            )

        self.stdout.write("")
        self.stdout.write("[教学班/考试名称同步预览]")
        for teaching_class in classes[:5]:
            blueprint = course_blueprint_by_id.get(teaching_class.course_id)
            if blueprint:
                self.stdout.write(
                    f"  教学班 id={teaching_class.id}: "
                    f"{teaching_class.class_name} -> {blueprint[1]}教学班"
                )
        for exam in exams[:5]:
            blueprint = course_blueprint_by_id.get(exam.course_id)
            if blueprint:
                suffix = exam.exam_type or "课程考核"
                self.stdout.write(
                    f"  考试 id={exam.id}: {exam.name} -> {blueprint[1]}{suffix}"
                )

        if not execute:
            self.stdout.write("")
            self.stdout.write(
                self.style.WARNING(
                    "DRY-RUN 完成：数据库未修改。确认预览无误后再添加 --execute。"
                )
            )
            return

        with transaction.atomic():
            college, _ = College.objects.get_or_create(
                name=COLLEGE_NAME,
                defaults={
                    "code": COLLEGE_CODE,
                    "description": "山东大学政治学与公共管理学院教学系统演示单位",
                    "is_active": True,
                },
            )
            college.code = COLLEGE_CODE
            college.description = "山东大学政治学与公共管理学院教学系统演示单位"
            college.is_active = True
            college.save(update_fields=["code", "description", "is_active"])

            # 仅保留目标学院为活动状态；旧学院记录不删除，以便追溯和回滚。
            College.objects.exclude(pk=college.pk).update(is_active=False)

            Student.objects.update(college=college)
            Teacher.objects.update(college=college)
            Course.objects.update(college=college)
            UserProfile.objects.update(college=college)

            for index, student in enumerate(students):
                major = MAJORS[index % len(MAJORS)]
                class_no = (index // len(MAJORS)) % 2 + 1
                student.major = major
                student.class_name = f"{major}{class_no}班"
                student.save(update_fields=["major", "class_name"])

            # 分两步更新课程代码，规避唯一性约束冲突。
            for course in courses:
                course.code = f"TMP_SPPA_{course.id}"
                course.save(update_fields=["code"])

            for course in courses:
                new_code, new_name, new_type, description = course_blueprint_by_id[course.id]
                course.code = new_code
                course.name = new_name
                course.course_type = new_type
                course.description = description
                course.save(
                    update_fields=["code", "name", "course_type", "description"]
                )

            for index, teaching_class in enumerate(classes):
                blueprint = course_blueprint_by_id.get(teaching_class.course_id)
                if not blueprint:
                    raise CommandError(
                        f"教学班 id={teaching_class.id} 的 course_id="
                        f"{teaching_class.course_id} 不在课程映射中。"
                    )
                schedule, classroom = SCHEDULES[index % len(SCHEDULES)]
                teaching_class.class_name = f"{blueprint[1]}教学班"
                teaching_class.schedule = schedule
                teaching_class.classroom = classroom
                teaching_class.status = "开课中"
                teaching_class.save(
                    update_fields=["class_name", "schedule", "classroom", "status"]
                )

            for exam in exams:
                blueprint = course_blueprint_by_id.get(exam.course_id)
                if not blueprint:
                    raise CommandError(
                        f"考试 id={exam.id} 的 course_id={exam.course_id} "
                        "不在课程映射中。"
                    )
                suffix = exam.exam_type or "课程考核"
                exam.name = f"{blueprint[1]}{suffix}"
                exam.save(update_fields=["name"])

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "EXECUTE 完成：数据库主题已统一为政治学与公共管理学院。"
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"活动学院={College.objects.filter(is_active=True).count()}；"
                f"学生={Student.objects.count()}；教师={Teacher.objects.count()}；"
                f"课程={Course.objects.count()}；教学班={TeachingClass.objects.count()}；"
                f"考试={Exam.objects.count()}。"
            )
        )
