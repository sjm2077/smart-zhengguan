import unittest
from decimal import Decimal
from statistics import pstdev
from .ai_grade_stats import summarize_grades


class GradeStatisticsTests(unittest.TestCase):
    def test_boundaries_and_rates(self):
        scores = ['0', '59.99', '60', '69.99', '70', '79.99', '80', '89.99', '90', '100']
        data = summarize_grades((i, 1, 'A', Decimal(s), Decimal('100')) for i, s in enumerate(scores))
        self.assertEqual([x['count'] for x in data['distribution']], [2, 2, 2, 2, 2])
        self.assertEqual(data['pass_rate'], 80)
        self.assertEqual(data['below_pass_rate'], 20)
        self.assertEqual(data['excellent_rate'], 20)
        self.assertEqual(data['median_score'], 75)
        self.assertAlmostEqual(data['std_score'], round(pstdev(map(float, scores)), 2))
        self.assertEqual(data['average_score'], round(sum(map(float, scores))/10, 2))

    def test_student_dedup_and_course_totals(self):
        d = summarize_grades([(1, 1, 'A', 50, None), (1, 1, 'A', 55, 100),
                              (1, 2, 'B', 80, 100), (2, 2, 'B', 90, 100)])
        self.assertEqual(d['records'], 4)
        self.assertEqual(d['valid_students'], 2)
        self.assertEqual(d['below_pass_students'], 1)
        self.assertEqual([x['student_count'] for x in d['course_results']], [1, 2])
        self.assertEqual(sum(x['records'] for x in d['course_results']), 4)
        self.assertEqual(d['course_results'][1]['excellent_rate'], 50)

    def test_exclusions_and_empty(self):
        d = summarize_grades([(1, 1, 'A', -1, None), (2, 1, 'A', 101, 100),
                              (3, 1, 'A', 60, 120), (4, 1, 'A', None, None)])
        self.assertEqual(d['published_records'], 4)
        self.assertEqual(d['graded_students'], 4)
        self.assertEqual(d['excluded_records'], 4)
        self.assertEqual(d['non_hundred_exam_records'], 1)
        self.assertEqual(d['invalid_score_records'], 3)
        self.assertEqual(d['records'], 0)
        self.assertIsNone(d['average_score'])
        self.assertIsNone(d['pass_rate'])
        self.assertEqual(d['course_results'], [])
        self.assertIsNone(summarize_grades([])['median_score'])

    def test_all_courses_not_truncated(self):
        d = summarize_grades((i, i, f'C{i}', 60, 100) for i in range(90))
        self.assertEqual(len(d['course_results']), 90)
        self.assertEqual(d['pass_rate'], 100)
        self.assertEqual(d['std_score'], 0)

    def test_odd_and_even_median(self):
        rows = [(1, 1, 'A', 0, 100), (2, 1, 'A', 100, 100), (3, 1, 'A', 70, 100)]
        self.assertEqual(summarize_grades(rows)['median_score'], 70)
        self.assertEqual(summarize_grades(rows[:2])['median_score'], 50)
        self.assertEqual(summarize_grades(rows[:1])['std_score'], 0)
