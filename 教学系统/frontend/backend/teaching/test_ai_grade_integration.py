from datetime import date
from decimal import Decimal
from unittest.mock import patch, MagicMock
import json
from django.test import TestCase
from .models import College, Course, Grade, Semester, Student
from .ai_checks import collect_overview
from .ai_views import call_deepseek


class GradeIntegrationTests(TestCase):
    def test_current_published_only_and_model_payload(self):
        c = College.objects.create(name='测试学院')
        sem = Semester.objects.create(name='2030-2031 第一学期', academic_year='2030-2031', term='first', is_current=True, start_date=date(2030,9,1), end_date=date(2031,1,20))
        old = Semester.objects.create(name='2029-2030 第一学期', academic_year='2029-2030', term='first')
        course = Course.objects.create(code='GRADE-TEST', name='测试课程', college=c, semester=sem)
        students = [Student.objects.create(student_no=f'PRIVATE-{i}', name=f'PRIVATE_NAME_{i}', college=c, major='测试专业', grade='2030', enrollment_year=2030) for i in range(5)]
        for i, score in enumerate([59,60,70,80,90]):
            Grade.objects.create(student=students[i], course=course, semester=sem, score=Decimal(score), is_published=True)
        Grade.objects.create(student=students[0], course=course, semester=sem, score=100, exam_type='期中', is_published=False)
        Grade.objects.create(student=students[0], course=course, semester=old, score=100, is_published=True)
        d = collect_overview()
        g = d['analyses']['grade']
        self.assertEqual(d['summary']['published_grades'], 5)
        self.assertEqual(g['records'], 5)
        self.assertEqual(g['pass_rate'], 80)
        self.assertEqual(g['median_score'], 70)
        self.assertEqual(g['below_pass_students'], 1)
        self.assertEqual(d['rule_total'], 0)
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps({'choices':[{'message':{'content':'OK'}}]}).encode()
        with patch.dict('os.environ', {'DEEPSEEK_API_KEY':'test-only'}), patch('teaching.ai_views.urlopen', return_value=response) as mocked:
            self.assertEqual(call_deepseek('成绩分布', [], d), ('OK', 'deepseek'))
            payload = json.loads(mocked.call_args.args[0].data)
            message = payload['messages'][0]['content']
            self.assertIn('分数段记录分布', message)
            self.assertIn('测试课程', message)
            self.assertNotIn('PRIVATE', message)
            self.assertNotIn('below_pass_students', message)
