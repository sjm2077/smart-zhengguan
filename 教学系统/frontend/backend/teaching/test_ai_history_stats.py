from datetime import date
from unittest import TestCase
from .ai_history_stats import date_quality, build_course_series, history_facts


def course(cid, students=5, name='同名课程'):
    return {'course_id':cid,'course_name':name,'student_count':students,'records':10,
            'average_score':75,'pass_rate':80,'excellent_rate':20}


def term(tid):
    return {'id':tid,'name':str(tid),'period':'closed'}


class HistoryStatsTests(TestCase):
    def test_date_boundaries_and_missing(self):
        start,end = date(2026,8,31),date(2027,1,31)
        self.assertEqual(date_quality([start,end,None,date(2026,7,26),date(2027,2,1)],start,end),
                         {'outside':2,'missing':1,'dated':4})

    def test_unknown_or_reversed_bounds_not_zero(self):
        a,b = date(2026,8,31),date(2027,1,31)
        for start,end in [(None,b),(a,None),(b,a)]:
            self.assertIsNone(date_quality([a],start,end)['outside'])

    def test_same_course_id_only_and_missing_term_not_filled(self):
        result=build_course_series([(term(1),[course(1),course(2)]),(term(2),[]),(term(3),[course(1),course(3)])])
        self.assertEqual([c['course_id'] for c in result],[1])
        self.assertEqual([t['semester_id'] for t in result[0]['terms']],[1,3])

    def test_no_comparison_for_one_term(self):
        self.assertEqual(build_course_series([(term(1),[course(1)])]),[])

    def test_external_course_small_group_excluded(self):
        courses=build_course_series([(term(1),[course(1,4,'PRIVATE'),course(2,5,'OK')]),(term(2),[course(1,5,'PRIVATE'),course(2,5,'OK')])])
        result=history_facts({'terms':[],'courses':courses,'note':'note','total_archives':2,'excluded_archives':0,'observed_terms':2,'grade_terms':2})
        self.assertEqual([x['课程'] for x in result['同课程样本']],['OK'])
        self.assertNotIn('course_id',str(result))

    def test_empty_history_facts(self):
        self.assertIn('说明',history_facts(None))
