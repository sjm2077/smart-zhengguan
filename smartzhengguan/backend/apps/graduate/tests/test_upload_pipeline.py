import shutil
import tempfile
from pathlib import Path

from django.conf import settings
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.graduate.models import ImportBatch, Student, ScholarshipAward
from apps.graduate import upload_pipeline, upload_services


FIXTURE = Path(settings.BASE_DIR).parent / '测试数据_多Sheet综合.xlsx'


class WorkbookImportTests(TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.override = override_settings(BASE_DIR=Path(self.tmp.name))
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.batch = ImportBatch.objects.create(batch_id='test-upload', file_name=FIXTURE.name, file_hash='fixture')
        root = Path(self.tmp.name) / 'tmp' / 'uploads'
        root.mkdir(parents=True)
        shutil.copyfile(FIXTURE, root / f'{self.batch.batch_id}_{FIXTURE.name}')
        self.client = APIClient()

    def post(self, endpoint, **data):
        response = self.client.post(f'/api/v1/upload/{endpoint}/', {'batch_id': self.batch.batch_id, **data}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        return response.data

    def test_real_headers_and_per_sheet_mapping_are_saved(self):
        result = self.post('identify')
        self.assertEqual([row['row_count'] for row in result['identification_results']], [10, 5, 15])
        plan = upload_pipeline.load_plan(self.batch)
        self.assertEqual([row['module'] for row in plan['sheets']], ['student', 'scholarship', 'course_grade'])
        self.assertEqual(plan['sheets'][0]['sample_values'][1], '学生1')
        for sheet in plan['sheets']:
            self.post('mapping', sheet_name=sheet['sheet_name'], mapping=sheet['mapping'])
        self.assertEqual(upload_pipeline.load_plan(self.batch)['sheets'][1]['mapping']['年度'], 'scholarship.award_year')

    def test_preview_reads_30_rows_and_never_writes_business_data(self):
        result = self.post('validate-preview', strategy='create_only')
        self.assertEqual(result['preview']['total_rows'], 30)
        self.assertEqual(result['preview']['new_count'], 15)
        self.assertEqual(result['preview']['skipped_count'], 15)
        self.assertEqual(result['preview']['error_count'], 0)
        self.assertIn('课程成绩', result['validation']['warnings'][0]['message'])
        self.assertEqual(Student.objects.count(), 0)
        self.assertEqual(ScholarshipAward.objects.count(), 0)

    def test_confirm_imports_same_rows_and_blocks_repeat(self):
        preview = self.post('validate-preview', strategy='create_only')['preview']
        result = self.post('confirm', strategy='create_only')
        self.assertEqual(result['summary'], preview)
        self.assertEqual(Student.objects.count(), 10)
        self.assertEqual(ScholarshipAward.objects.count(), 5)
        self.assertEqual(Student.objects.get(student_id='2023001').name, '学生1')
        response = self.client.post('/api/v1/upload/confirm/', {'batch_id': self.batch.batch_id, 'strategy': 'create_only'}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(ScholarshipAward.objects.count(), 5)

    def test_validate_only_does_not_create_any_student_or_award(self):
        result = self.post('validate-preview', strategy='validate_only')
        self.assertEqual(result['preview']['new_count'], 0)
        self.assertEqual(result['preview']['skipped_count'], 30)
        self.post('confirm', strategy='validate_only')
        self.assertFalse(Student.objects.exists())
        self.assertFalse(ScholarshipAward.objects.exists())

    def test_missing_required_mapping_is_a_row_error_and_can_be_fixed(self):
        plan = upload_pipeline.load_plan(self.batch)
        mapping = plan['sheets'][0]['mapping']
        name = mapping.pop('姓名')
        self.post('mapping', sheet_name='学生信息', mapping=mapping)
        result = self.post('validate-preview', strategy='create_only')
        self.assertEqual(result['preview']['error_count'], 15)
        self.assertEqual(result['validation']['errors'][0]['sheet'], '学生信息')
        mapping['姓名'] = name
        self.post('mapping', sheet_name='学生信息', mapping=mapping)
        result = self.post('validate-preview', strategy='create_only')
        self.assertEqual(result['preview']['error_count'], 0)

    def test_update_empty_preserves_existing_values_and_fills_blank_fields(self):
        Student.objects.create(student_id='2023001', name='保留原姓名', grade='2022级', major='原专业', degree_type='academic_master')
        result = self.post('validate-preview', strategy='update_empty')
        self.assertEqual(result['preview']['update_count'], 1)
        self.post('confirm', strategy='update_empty')
        student = Student.objects.get(student_id='2023001')
        self.assertEqual(student.name, '保留原姓名')
        self.assertEqual(student.gender, '女')

    def test_revert_understands_each_target_model(self):
        self.post('validate-preview', strategy='create_only')
        self.post('confirm', strategy='create_only')
        result = upload_services.revert_batch(self.batch.batch_id)
        self.assertEqual(result['reverted_count'], 15)
        self.assertFalse(Student.objects.exists())
        self.assertFalse(ScholarshipAward.objects.exists())

    def test_preview_counts_all_records_not_only_first_20(self):
        self.batch.file_name = 'many.csv'
        self.batch.save()
        path = Path(self.tmp.name) / 'tmp' / 'uploads' / f'{self.batch.batch_id}_many.csv'
        path.write_text('学号,姓名,年级,专业\n' + '\n'.join(f'{i},姓名{i},2023级,专业' for i in range(30)), encoding='utf-8-sig')
        result = self.post('validate-preview', strategy='create_only')
        self.assertEqual(result['preview']['new_count'], 30)
        self.assertEqual(len(result['preview']['sample_changes']), 20)

    def test_unchanged_decimal_amount_does_not_count_as_update(self):
        self.post('validate-preview', strategy='create_only')
        self.post('confirm', strategy='create_only')
        result = upload_pipeline.prepare_import(self.batch, 'overwrite')
        self.assertEqual(result['preview']['update_count'], 0)
        self.assertEqual(result['preview']['unchanged_count'], 15)

    def test_changing_strategy_requires_another_preview(self):
        self.post('validate-preview', strategy='create_only')
        response = self.client.post('/api/v1/upload/confirm/', {'batch_id': self.batch.batch_id, 'strategy': 'overwrite'}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Student.objects.exists())
