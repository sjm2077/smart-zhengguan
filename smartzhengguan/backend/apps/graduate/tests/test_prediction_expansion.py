from collections import Counter
from unittest import mock

from django.test import SimpleTestCase, TestCase

from apps.graduate.models import DegreeType, Student
from apps.graduate.management.commands.expand_prediction_cohort import expand_rows
from apps.graduate.management.commands.import_excel_data import Command


class CohortExpansionTests(SimpleTestCase):
    def test_all_degree_grade_major_groups_and_original_values_are_preserved(self):
        original = ['测试姓名', '2021010001', '硕士', '2021级', '政治学理论',
                    '政治学与公共管理学院', '王教授', 90, 88, 95, '已完成',
                    2, 1, 8, 30, 3, 30, 8, 90, 0, 0, 90]
        rows = expand_rows([original])
        self.assertEqual(len(rows), 4200)
        counts = Counter((r[2], r[3], r[4]) for r in rows)
        self.assertEqual(len(counts), 120)
        self.assertEqual(set(counts.values()), {35})
        self.assertEqual(len({r[1] for r in rows}), 4200)
        self.assertEqual(rows[0][:2] + rows[0][3:], original[:2] + original[3:])
        self.assertTrue(any(r[17] < 2 for r in rows))
        self.assertEqual(expand_rows(rows), rows)


class ExplicitSampleImportTests(TestCase):
    def test_aggregate_quotas_do_not_drop_samples_or_override_explicit_degree(self):
        distribution = [{'年级': '2023级', '专业': '政治学理论', '总人数': 1, '男生人数': 1, '女生人数': 0}]
        samples = [
            {'年级': '2023级', '专业': '政治学理论', '姓名': '张三', '学号': '2023010001', '导师': '王教授', '类别': '专业型硕士'},
            {'年级': '2023级', '专业': '政治学理论', '姓名': '李四', '学号': '2023010002', '导师': '李教授', '类别': '学术型硕士'},
        ]
        command = Command()
        with mock.patch.object(command, 'sheet_rows', side_effect=lambda _wb, sheet: {
            '首页总览-年级专业': distribution, '智能预测-学生数据': samples,
        }.get(sheet, [])):
            command.import_students(None)
        self.assertEqual(Student.objects.count(), 2)
        self.assertEqual(Student.objects.get(student_id='2023010001').degree_type, DegreeType.PROFESSIONAL_MASTER)
        self.assertEqual(Student.objects.get(student_id='2023010002').degree_type, DegreeType.ACADEMIC_MASTER)
