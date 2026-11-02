from unittest import mock

from django.test import SimpleTestCase

from apps.graduate import services
from apps.graduate.agent import build_stream_answer_preview
from apps.graduate.models import Student, PredictionSnapshot, DegreeType
from apps.graduate.prediction_cohort import is_cohort_question, build_cohort_chat


def snapshot(student_id, name, risk='high', grade='2021级', major='行政管理', virtual=False):
    student = Student(student_id=student_id, name=name, grade=grade, major=major,
                      degree_type=DegreeType.values[0])
    result = PredictionSnapshot(student=student, risk_level=risk, overdue_tasks_count=2,
                                training_plan_completion_rate=80, advisor_meeting_count_60d=1)
    result.is_virtual = virtual
    return result


class CohortChatTests(SimpleTestCase):
    def test_stream_preview_shows_completed_sections_before_json_finishes(self):
        self.assertEqual(build_stream_answer_preview('{"directAnswer":"未完成'), '')
        partial = '{"directAnswer":"先核实记录","reasoning":["逾期2次","尚未写完'
        self.assertEqual(build_stream_answer_preview(partial), '先核实记录\n\n判断依据：逾期2次')

    def setUp(self):
        self.rows = [snapshot('001', '张浩然', 'low'), snapshot('002', '李明', 'high'),
                     snapshot('003', '王宁', 'alert', grade='2022级'),
                     snapshot('004', '学生0001'), snapshot('005', '虚拟同学', virtual=True)]
        self.patch = mock.patch.object(services, 'build_prediction_sources', return_value=self.rows)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def test_group_intent_does_not_capture_personal_or_policy_questions(self):
        for question in ('哪些学生需要优先干预？', '找出最需要干预的学生', '全院高风险名单', '导师沟通不足的学生Top3'):
            self.assertTrue(is_cohort_question(question), question)
        for question in ('他为什么高风险？', '张浩然需要干预吗？', '哪些学生符合奖学金条件？'):
            self.assertFalse(is_cohort_question(question), question)

    def test_ranking_uses_whole_measured_cohort_and_names(self):
        result = build_cohort_chat('哪些学生需要优先干预？')
        self.assertEqual(result['scope']['studentCount'], 3)
        self.assertEqual([row['name'] for row in result['students']], ['李明', '王宁', '张浩然'])
        self.assertIn('风险分', result['answer']['directAnswer'])
        self.assertNotIn('学生0001', result['answer']['directAnswer'])

    def test_explicit_scope_and_empty_scope(self):
        result = build_cohort_chat('2022级行政管理哪些学生需要优先干预？')
        self.assertEqual([row['name'] for row in result['students']], ['王宁'])
        result = build_cohort_chat('2025级哪些学生需要优先干预？')
        self.assertEqual(result['students'], [])
        self.assertEqual(result['scope']['studentCount'], 0)

    def test_communication_ranks_by_meeting_count_and_excludes_sufficient(self):
        self.rows[0].advisor_meeting_count_60d = 0
        self.rows[1].advisor_meeting_count_60d = 3
        result = build_cohort_chat('哪些学生导师沟通不足？')
        self.assertEqual([row['name'] for row in result['students']], ['张浩然', '王宁'])

    def test_stream_and_sync_ignore_selected_student_and_do_not_call_model(self):
        with mock.patch.object(services, 'get_intelligent_prediction_context', side_effect=AssertionError('个人上下文不应被读取')):
            sync = services.get_intelligent_prediction_chat('001', '哪些学生需要优先干预？')
            events = list(services.stream_intelligent_prediction_chat('999', '哪些学生需要优先干预？'))
        self.assertEqual(events[-1]['payload']['students'], sync['students'])
        self.assertFalse(sync['trace']['llmUsed'])

    def test_followup_keeps_explicit_cohort_scope(self):
        history = [{'role': 'user', 'content': '2022级行政管理哪些学生需要干预？'}]
        self.assertTrue(is_cohort_question('那只看前1名', history))
        result = build_cohort_chat('那只看前1名', history)
        self.assertEqual([row['name'] for row in result['students']], ['王宁'])
