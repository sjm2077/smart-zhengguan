from datetime import date,timedelta
from unittest import TestCase
from .ai_prediction_data import build_examples,cutoff_for,HISTORY

START=date(2025,9,1); END=date(2026,1,15); CUT=cutoff_for(START,END)

def row(kind,score,day=None,cid=1,sid=1):
    return dict(student_id=sid,course_id=cid,semester_id=1,exam_type=kind,score=score,
        exam_date=day or (CUT+timedelta(days=10) if kind=='期末' else CUT-timedelta(days=10)),remark=HISTORY,exam_id=None)

class PredictionDataTests(TestCase):
    def test_label_never_in_features(self):
        a=[row('平时',70),row('期中',80),row('期末',59)]
        x,_,_=build_examples(a,START,END); a[-1]['score']=90
        y,_,_=build_examples(a,START,END)
        self.assertEqual(x[0][2],y[0][2]); self.assertNotEqual(x[0][3],y[0][3])
    def test_future_midterm_excluded(self):
        a=[row('平时',70),row('期中',80,CUT+timedelta(days=1)),row('期末',59)]
        x,c,_=build_examples(a,START,END); self.assertEqual(x,[]); self.assertEqual(c['early_after_cutoff'],1)
    def test_other_course_final_excluded_and_missing_final_kept(self):
        a=[row('平时',70),row('期中',80),row('期末',59),row('平时',50,cid=2)]
        x,_,_=build_examples(a,START,END); self.assertEqual(x[0][2][3:5],[50,1])
        a.append(row('期末',100,cid=2)); y,_,_=build_examples(a,START,END); self.assertEqual(x,y)
    def test_non_demo_blocked(self):
        a=row('平时',80); a['remark']='real'
        with self.assertRaises(ValueError): build_examples([a],START,END)
    def test_early_final_not_label(self):
        x,c,_=build_examples([row('平时',70),row('期中',80),row('期末',59,CUT)],START,END)
        self.assertFalse(x); self.assertEqual(c['final_not_after_cutoff'],1)
    def test_bad_exam_link(self):
        a=row('期末',50); a.update(exam_id=1,exam__course_id=2)
        x,c,_=build_examples([a],START,END); self.assertFalse(x); self.assertEqual(c['invalid_exam_link'],1)
    def test_no_other_student_leakage(self):
        a=[row('平时',70),row('期中',80),row('期末',60),row('平时',10,sid=2,cid=2)]
        x,_,_=build_examples(a,START,END); self.assertEqual(x[0][2][3],75); self.assertEqual(x[0][3],0)
