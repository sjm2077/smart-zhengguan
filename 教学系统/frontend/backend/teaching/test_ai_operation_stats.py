from datetime import datetime, timezone, timedelta
from types import SimpleNamespace as NS
import json
import unittest
from .ai_operation_stats import summarize_operations, operation_facts


def cls(teacher=1, course=1, capacity=50, enrolled=40, schedule='周一第1-2节'):
    return NS(teacher_id=teacher, teacher=NS(name='PRIVATE_TEACHER_'+str(teacher)), course_id=course,
              capacity=capacity, enrolled_count=enrolled, schedule=schedule)


def exam(date, room):
    return NS(exam_date=date, location=room)


class OperationStatsTests(unittest.TestCase):
    def test_capacity_weighted_and_no_netting(self):
        data = summarize_operations([cls(capacity=50,enrolled=30), cls(capacity=10,enrolled=15),
                                     cls(capacity=10,enrolled=10), cls(capacity=0,enrolled=12)], [])
        c = data['capacity']
        self.assertEqual(data['enrolled_total'], 67)
        self.assertEqual((c['seats'], c['enrolled'], c['known_classes'], c['unknown_classes']), (70,55,3,1))
        self.assertEqual(c['utilization'],78.57)
        self.assertEqual((c['spare'],c['excess'],c['full_classes'],c['over_classes']), (20,5,1,1))

    def test_teacher_tasks_deduplicate_courses_and_people(self):
        data = summarize_operations([cls(), cls(), cls(teacher=2,course=2)], [])
        self.assertEqual((data['active_classes'], data['active_courses'], data['teachers']), (3,2,2))
        self.assertEqual(data['teacher_average_classes'],1.5)
        self.assertEqual(data['teacher_preview'][0]['courses'],1)
        self.assertEqual(data['teacher_max_classes'],2)

    def test_schedule_unknown_not_missing(self):
        data = summarize_operations([cls(schedule=x) for x in ['周一第1-2节','星期天第3节','周一至周五','周二、周四','', '待定']], [])
        s = data['schedule']
        self.assertEqual((s['parsed'], s['unparsed'], s['missing']), (2,3,1))
        self.assertEqual(s['weekdays'][0]['count'],1)
        self.assertEqual(s['weekdays'][-1]['count'],1)

    def test_exam_local_day_and_room(self):
        t = datetime(2030,1,1,17,tzinfo=timezone.utc)
        rows = [exam(t,' SECRET_ROOM '), exam(t+timedelta(hours=1),'SECRET_ROOM'), exam(t+timedelta(days=1),'')]
        data = summarize_operations([],rows,lambda x:x.astimezone(timezone(timedelta(hours=8))))
        e = data['exams']
        self.assertEqual(e['busiest_days'][0],{'date':'2030-01-02','count':2})
        self.assertEqual((e['days'], e['venues'],e['located'],e['peak_venue']), (2,1,2,2))
        self.assertNotIn('SECRET_ROOM', json.dumps(operation_facts(data)))

    def test_empty_and_over_capacity(self):
        data = summarize_operations([],[])
        self.assertIsNone(data['capacity']['utilization'])
        self.assertIsNone(data['teacher_average_classes'])
        self.assertIsNone(data['exams']['peak_daily'])
        self.assertEqual(summarize_operations([cls(capacity=10,enrolled=12)],[])['capacity']['utilization'],120)
        self.assertIn('说明',operation_facts(None))

    def test_external_aggregates_exclude_teacher_names(self):
        data = summarize_operations([cls()],[])
        text = json.dumps(operation_facts(data),ensure_ascii=False)
        self.assertNotIn('PRIVATE_TEACHER',text)
        self.assertNotIn('teacher_preview',text)
        self.assertIn('选课登记人次',text)
