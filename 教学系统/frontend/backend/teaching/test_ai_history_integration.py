from datetime import date, datetime
from unittest.mock import patch, MagicMock
import json
from django.test import TestCase
from django.utils import timezone
from .models import College, Semester, Course, Student, Teacher, TeachingClass, Exam, Grade
from .ai_checks import collect_overview
from .ai_history_stats import collect_history, history_facts
from .ai_views import call_deepseek, grounded_fallback, is_history_question


class HistoryIntegrationTests(TestCase):
    def test_registered_history_and_date_quality(self):
        college=College.objects.create(name='历史测试学院')
        old=Semester.objects.create(name='历史学期',start_date=date(2025,9,1),end_date=date(2026,1,31))
        empty=Semester.objects.create(name='空学期',start_date=date(2026,3,1),end_date=date(2026,7,31))
        current=Semester.objects.create(name='当前学期',start_date=date(2026,9,1),end_date=date(2027,1,31),is_current=True)
        Semester.objects.create(name='未知日期')
        Semester.objects.create(name='未来学期',start_date=date(2027,3,1),end_date=date(2027,7,31))
        course=Course.objects.create(code='H-1',name='历史测试课程',college=college,semester=current)
        teacher=Teacher.objects.create(teacher_no='PRIVATE_T',name='PRIVATE_TEACHER',college=college)
        for sem,status,name,capacity,enrolled in [(old,'已结课','A',20,15),(old,'停开','B',10,1),(current,'开课中','C',40,30)]:
            TeachingClass.objects.create(course=course,semester=sem,teacher=teacher,class_name=name,status=status,capacity=capacity,enrolled_count=enrolled,schedule='周一第1-2节')
        exam=Exam.objects.create(name='考试',course=course,semester=current,exam_date=timezone.make_aware(datetime(2026,7,20,10)),location='PRIVATE_ROOM')
        for i in range(5):
            student=Student.objects.create(student_no='PRIVATE_S'+str(i),name='PRIVATE_STUDENT',college=college,major='测试',grade='2025',enrollment_year=2025)
            Grade.objects.create(student=student,course=course,semester=old,exam=exam if i==0 else None,score=70,is_published=True,exam_date=date(2025,12,1))
            Grade.objects.create(student=student,course=course,semester=current,score=80,is_published=True,exam_date=None if i==0 else date(2026,10,1))
        Grade.objects.create(student=student,course=course,semester=current,score=0,is_published=False,exam_type='未发布')
        with patch('django.utils.timezone.localdate',return_value=date(2026,11,24)):
            h=collect_history(current.id)
        self.assertEqual([r['id'] for r in h['terms']],[old.id,empty.id,current.id])
        a,b,c=h['terms']
        self.assertEqual((h['total_archives'],h['observed_terms'],h['grade_terms'],h['excluded_archives']),(5,2,2,2))
        self.assertEqual((a['classes'],a['courses'],a['enrolled'],a['capacity_rate']),(1,1,15,75.0))
        self.assertFalse(b['has_data']); self.assertIsNone(b['average_score'])
        self.assertEqual(c['quality']['exams']['outside'],1)
        self.assertEqual(c['quality']['grades']['missing'],1)
        self.assertEqual(a['quality']['linked_exam_conflicts'],1)
        self.assertEqual((a['average_score'],c['average_score'],c['grade_records']),(70,80,5))
        self.assertEqual(len(h['courses']),1)
        d=collect_overview(); d['history_trend']=h
        self.assertEqual(d['rule_total'],0) # historical quality does not create warnings
        self.assertTrue(is_history_question('对比上学期成绩'))
        self.assertIn('2期有有效成绩',grounded_fallback('历史趋势',d))
        response=MagicMock(); response.__enter__.return_value.read.return_value=json.dumps({'choices':[{'message':{'content':'OK'}}]}).encode()
        with patch.dict('os.environ',{'DEEPSEEK_API_KEY':'test-only'}),patch('teaching.ai_views.urlopen',return_value=response) as mocked:
            self.assertEqual(call_deepseek('历史趋势',[],d),('OK','deepseek'))
            text=json.loads(mocked.call_args.args[0].data)['messages'][0]['content']
            self.assertIn('跨学期历史统计',text); self.assertIn('考试日期越界数',text); self.assertNotIn('PRIVATE',text)
        self.assertEqual(Exam.objects.get(pk=exam.pk).semester_id,current.id)
        self.assertEqual(Grade.objects.count(),11)
