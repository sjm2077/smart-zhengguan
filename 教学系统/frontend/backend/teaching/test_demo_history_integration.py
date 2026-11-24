from datetime import date, datetime
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from django.core.management import call_command, CommandError
from django.db import connection
from django.test import TestCase
from django.utils import timezone
from .models import College, Semester, Course, Teacher, Student, TeachingClass, Exam, Grade
from .ai_history_stats import collect_history
from .ai_checks import collect_overview
from .demo_history_logic import HISTORY, NORMALIZED

class DemoHistoryIntegrationTests(TestCase):
    def setUp(self):
        self.college=College.objects.create(code='SPPA',name='演示学院')
        self.old=Semester.objects.create(name='2025-2026 第一学期',start_date=date(2025,9,1),end_date=date(2026,1,15))
        self.old2=Semester.objects.create(name='2025-2026 第二学期',start_date=date(2026,2,20),end_date=date(2026,7,10))
        self.cur=Semester.objects.create(name='2026-2027 第一学期',start_date=date(2026,9,1),end_date=date(2027,1,15),is_current=True)
        self.course=Course.objects.create(code='SPPA101',name='测试课程',college=self.college,semester=self.cur)
        self.teacher=Teacher.objects.create(teacher_no='T001',name='测试教师',college=self.college)
        TeachingClass.objects.create(course=self.course,semester=self.cur,teacher=self.teacher,class_name='当前班',capacity=20,enrolled_count=12,schedule='周一第1-2节')
        self.exam=Exam.objects.create(name='原考试',course=self.course,semester=self.cur,exam_type='期末考试',exam_date=timezone.make_aware(datetime(2026,7,1,9)),location='A101')
        for i in range(12):
            st=Student.objects.create(student_no='S'+str(i),name='测试学生',college=self.college,major='测试',grade='2025',enrollment_year=2025 if i<10 else 2026)
            Grade.objects.create(student=st,course=self.course,semester=self.cur,exam=self.exam,exam_type='期末',exam_date=date(2026,7,1),score=76+i,is_published=True)
            Grade.objects.create(student=st,course=self.course,semester=self.cur,exam_type='平时',score=80,is_published=True)
        self.tmp=TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.confirm=str(connection.settings_dict['NAME'])
        self.day=date(2026,11,24)
    def invoke(self,*args):
        with patch('django.utils.timezone.localdate',return_value=self.day):
            call_command('build_demo_history',*args,stdout=StringIO())
    def execute(self):
        self.invoke('--normalize-current','--execute','--confirm-demo-db',self.confirm,'--backup-dir',self.tmp.name)
        return str(next(Path(self.tmp.name).glob('*.json')))
    def test_preview_no_write_and_wrong_confirmation(self):
        self.invoke('--normalize-current')
        self.assertEqual(Grade.objects.count(),24); self.assertEqual(TeachingClass.objects.count(),1)
        with self.assertRaises(CommandError): self.invoke('--execute','--confirm-demo-db','WRONG','--backup-dir',self.tmp.name)
        self.assertFalse(list(Path(self.tmp.name).glob('*.json')))
    def test_apply_history_normalize_and_rollback(self):
        initial=list(Grade.objects.order_by('pk').values_list('pk','score','exam_date','remark','exam_id'))
        original_exam=Exam.objects.get(pk=self.exam.pk).exam_date
        manifest=self.execute()
        self.assertEqual(TeachingClass.objects.count(),3); self.assertEqual(Exam.objects.count(),5)
        self.assertTrue(Grade.objects.filter(remark__startswith=HISTORY).exists())
        self.assertFalse(Grade.objects.filter(semester__in=[self.old,self.old2],student__enrollment_year=2026).exists())
        self.assertEqual(Grade.objects.filter(semester=self.cur,remark__startswith=NORMALIZED).count(),24)
        with patch('django.utils.timezone.localdate',return_value=self.day):
            h=collect_history(self.cur.pk); overview=collect_overview()
        self.assertTrue(overview['demo_data']); self.assertEqual(h['grade_terms'],3); self.assertEqual(len(h['courses']),1)
        for row in h['terms']:
            self.assertEqual(row['quality']['exams']['outside'],0); self.assertEqual(row['quality']['grades']['outside'],0)
            self.assertEqual(row['quality']['grades']['missing'],0); self.assertEqual(row['quality']['linked_exam_conflicts'],0)
        self.assertEqual(list(Grade.objects.filter(semester=self.cur).order_by('pk').values_list('pk','score')),[(x[0],x[1]) for x in initial])
        with self.assertRaises(CommandError): self.execute()
        self.invoke('--rollback',manifest)  # preview
        self.assertGreater(Grade.objects.count(),24)
        self.invoke('--rollback',manifest,'--execute','--confirm-demo-db',self.confirm)
        self.assertEqual(list(Grade.objects.order_by('pk').values_list('pk','score','exam_date','remark','exam_id')),initial)
        self.assertEqual(Exam.objects.get(pk=self.exam.pk).exam_date,original_exam)
        self.assertEqual(TeachingClass.objects.count(),1)
    def test_rollback_refuses_edited_generated_grade(self):
        manifest=self.execute(); g=Grade.objects.filter(remark__startswith=HISTORY).first(); g.score=1; g.save(update_fields=['score'])
        with self.assertRaises(CommandError): self.invoke('--rollback',manifest,'--execute','--confirm-demo-db',self.confirm)
        self.assertTrue(Grade.objects.filter(pk=g.pk,score=1).exists())
    def test_nonempty_history_refuses_overwrite(self):
        TeachingClass.objects.create(course=self.course,semester=self.old,teacher=self.teacher,class_name='已有历史',capacity=20)
        with self.assertRaises(CommandError): self.invoke('--normalize-current')
        self.assertEqual(TeachingClass.objects.count(),2)
