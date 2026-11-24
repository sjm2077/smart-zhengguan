"""本轮回归：python manage.py test teaching.test_ai_warning_workflow -v 2

Django 使用独立测试数据库，不应在正式数据库中手工造测试记录。
"""
from datetime import date, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from .ai_checks import collect_overview
from .ai_models import AIWarningCase
from .models import College, Semester, Course, Teacher, TeachingClass, Exam


class AIWarningWorkflowTests(TestCase):
    def setUp(self):
        self.college = College.objects.create(name="测试学院")
        self.semester = Semester.objects.create(
            name="2030—2031学年第一学期", academic_year="2030-2031", term="first",
            is_current=True, start_date=date(2030, 9, 2), end_date=date(2031, 1, 20),
        )
        self.teacher = Teacher.objects.create(teacher_no="AI-TEST-001", name="测试教师", college=self.college)
        self.course = Course.objects.create(code="AI-TEST-COURSE", name="测试课程", college=self.college,
                                            semester=self.semester)
        user = get_user_model().objects.create_user(username="ai-warning-admin", password="test-password")
        user.is_superuser = True
        user.save(update_fields=["is_superuser"])
        self.client = APIClient()
        self.client.force_authenticate(user=user)

    def make_class(self, name, schedule="", capacity=60, enrolled=30):
        return TeachingClass.objects.create(
            course=self.course, semester=self.semester, teacher=self.teacher, class_name=name,
            schedule=schedule, capacity=capacity, enrolled_count=enrolled,
        )

    def make_exam(self, name, start, location="A-101", duration=60):
        return Exam.objects.create(
            name=name, course=self.course, semester=self.semester,
            exam_date=start, duration=duration, location=location,
        )

    def test_current_semester_uses_business_flag_not_fixed_2026(self):
        Semester.objects.create(name="2026—2027学年第一学期", academic_year="2026-2027", term="first")
        response = self.client.get("/api/ai/overview/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["semester"]["id"], self.semester.id)
        self.assertEqual(response.data["analyses"]["teaching"]["week18_exams"], 0)

    def test_full_sync_is_not_limited_by_160_preview(self):
        for i in range(171):
            self.make_class(f"教学班{i:03}")
        overview = self.client.get("/api/ai/overview/").data
        self.assertTrue(overview["rules_complete"])
        self.assertEqual(len(overview["rule_preview"]), 160)
        self.assertEqual(overview["rule_total"], 171)
        result = self.client.post("/api/ai/warnings/sync/", {}, format="json")
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.data["created"], 171)
        self.assertEqual(AIWarningCase.objects.count(), 171)
        self.assertEqual(self.client.post("/api/ai/warnings/sync/", {}, format="json").data["created"], 0)
        first = self.client.get("/api/ai/warnings/?limit=100").data
        second = self.client.get("/api/ai/warnings/?limit=100&offset=100").data
        self.assertEqual(first["count"], 171)
        self.assertEqual(len(first["results"]), 100)
        self.assertEqual(first["next_offset"], 100)
        self.assertEqual(len(second["results"]), 71)
        self.assertIsNone(second["next_offset"])

    def test_source_disappears_and_reappears_without_erasing_manual_status(self):
        row = self.make_class("A")
        self.assertEqual(self.client.post("/api/ai/warnings/sync/", {}, format="json").data["created"], 1)
        case = AIWarningCase.objects.get()
        reply = self.client.patch(f"/api/ai/warnings/{case.id}/", {
            "status": "resolved", "handler": "教务处", "resolution_note": "已联系排课负责人核查。"
        }, format="json")
        self.assertEqual(reply.status_code, 200)
        row.schedule = "周二 09:00—10:40"
        row.save(update_fields=["schedule"])
        response = self.client.post("/api/ai/warnings/sync/", {}, format="json")
        self.assertEqual(response.data["cleared"], 1)
        case.refresh_from_db()
        self.assertFalse(case.source_active)
        self.assertIsNotNone(case.source_cleared_at)
        self.assertEqual(case.status, "resolved")
        self.assertEqual(case.handler, "教务处")
        row.schedule = ""
        row.save(update_fields=["schedule"])
        response = self.client.post("/api/ai/warnings/sync/", {}, format="json")
        self.assertEqual(response.data["reappeared"], 1)
        case.refresh_from_db()
        self.assertTrue(case.source_active)
        self.assertIsNotNone(case.source_reappeared_at)
        self.assertEqual(case.status, "resolved")
        self.assertEqual(case.resolution_note, "已联系排课负责人核查。")

    def test_capacity_and_exam_collision_respect_time_boundaries(self):
        self.make_class("人数异常", schedule="周三", capacity=20, enrolled=25)
        start = timezone.now().replace(microsecond=0)
        self.make_exam("考试甲", start, duration=60)
        self.make_exam("考试乙", start + timedelta(minutes=30), duration=60)
        self.make_exam("考试丙", start + timedelta(minutes=90), duration=60)  # 恰好相接，不算重叠
        response = self.client.get("/api/ai/overview/")
        self.assertEqual(response.status_code, 200)
        teaching = response.data["analyses"]["teaching"]
        self.assertEqual(teaching["over_capacity"], 1)
        self.assertEqual(teaching["venue_collisions"], 1)
        self.assertEqual(response.data["rule_total"], 2)

    def test_incomplete_scan_blocks_sync(self):
        self.make_class("A")
        self.make_class("B")
        with patch("teaching.ai_checks.MAX_SCAN_ROWS", 1):
            self.assertFalse(collect_overview()["rules_complete"])
            response = self.client.post("/api/ai/warnings/sync/", {}, format="json")
        self.assertEqual(response.status_code, 409)
        self.assertEqual(AIWarningCase.objects.count(), 0)

    def test_non_management_role_denied(self):
        teacher_user = get_user_model().objects.create_user(username="ai-teacher", password="test")
        from .models import UserProfile
        UserProfile.objects.create(user=teacher_user, role="teacher")
        self.client.force_authenticate(user=teacher_user)
        self.assertEqual(self.client.get("/api/ai/overview/").status_code, 403)
        self.assertEqual(self.client.post("/api/ai/warnings/sync/", {}, format="json").status_code, 403)
