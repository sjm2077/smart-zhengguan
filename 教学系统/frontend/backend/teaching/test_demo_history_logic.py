from datetime import date
from unittest import TestCase
from .demo_history_logic import assessment_dates, select_roster, synthetic_score

class DemoHistoryLogicTests(TestCase):
    def test_date_sequence(self):
        a,b=date(2025,9,1),date(2026,1,15)
        d=assessment_dates(a,b)
        self.assertTrue(a<d['平时']<d['期中']<d['期末']<b)
    def test_short_period_rejected(self):
        with self.assertRaises(ValueError): assessment_dates(date(2025,9,1),date(2025,9,15))
    def test_enrollment_eligibility_capacity_determinism(self):
        students=[(i,2025 if i<=20 else 2026) for i in range(1,31)]
        a=select_roster(students,1,2,date(2026,2,20),12,42)
        self.assertEqual(a,select_roster(students,1,2,date(2026,2,20),12,42))
        self.assertEqual(len(a),12); self.assertTrue(all(i<=20 for i in a)); self.assertEqual(len(set(a)),12)
    def test_synthetic_scores_bounded_and_reproducible(self):
        scores=[synthetic_score(42,i,1,2,0,'期末') for i in range(1,300)]
        self.assertTrue(all(0<=x<=100 for x in scores)); self.assertGreater(len(set(scores)),200)
        self.assertEqual(scores[0],synthetic_score(42,1,1,2,0,'期末'))
    def test_shared_student_signal_without_current_grade_inputs(self):
        a=[float(synthetic_score(42,i,1,2,0,'期中')) for i in range(1,300)]
        b=[float(synthetic_score(42,i,2,3,1,'期末')) for i in range(1,300)]
        ma,mb=sum(a)/len(a),sum(b)/len(b)
        self.assertGreater(sum((x-ma)*(y-mb) for x,y in zip(a,b)),0)
