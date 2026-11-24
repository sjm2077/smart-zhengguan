from datetime import date
import json
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.utils import timezone
from .models import College, Semester, Course, Teacher, TeachingClass, Exam
from .ai_checks import collect_overview
from .ai_views import call_deepseek


class OperationIntegrationTests(TestCase):
    def test_current_active_operations_and_external_facts(self):
        college = College.objects.create(name='测试学院')
        sem = Semester.objects.create(name='2030-2031 第一学期', is_current=True, start_date=date(2030,9,1))
        old = Semester.objects.create(name='2029-2030 第一学期')
        course = Course.objects.create(code='OPS-1', name='测试课程', college=college, semester=sem)
        teacher = Teacher.objects.create(teacher_no='PRIVATE-001', name='PRIVATE_TEACHER', college=college)
        for name, term, status, enrolled in [('A',sem,'开课中',35),('B',sem,'停开',20),('C',old,'开课中',15)]:
            TeachingClass.objects.create(course=course,semester=term,teacher=teacher,class_name=name,
                                         status=status,capacity=40,enrolled_count=enrolled,schedule='周三第1-2节')
        Exam.objects.create(name='考试',course=course,semester=sem,exam_date=timezone.now(),location='PRIVATE_ROOM')
        d = collect_overview()
        o = d['analyses']['teaching']['operations']
        self.assertEqual(d['summary']['teaching_classes'],2)
        self.assertEqual(o['active_classes'],1)
        self.assertEqual(o['teachers'],1)
        self.assertEqual(o['enrolled_total'],35)
        self.assertEqual(o['capacity']['utilization'],87.5)
        self.assertEqual(o['schedule']['weekdays'][2]['count'],1)
        self.assertEqual(o['exams']['venues'],1)
        self.assertEqual(d['rule_total'],0)
        with patch('teaching.ai_checks.MAX_SCAN_ROWS',1):
            partial = collect_overview()
            self.assertIsNone(partial['analyses']['teaching']['operations'])
            self.assertFalse(partial['rules_complete'])
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps({'choices':[{'message':{'content':'OK'}}]}).encode()
        with patch.dict('os.environ', {'DEEPSEEK_API_KEY':'test-only'}), patch('teaching.ai_views.urlopen',return_value=response) as mocked:
            self.assertEqual(call_deepseek('教学运行',[],d),('OK','deepseek'))
            payload = json.loads(mocked.call_args.args[0].data)
            text = payload['messages'][0]['content']
            self.assertIn('教学运行综合统计',text)
            self.assertIn('87.5',text)
            self.assertNotIn('PRIVATE',text)
