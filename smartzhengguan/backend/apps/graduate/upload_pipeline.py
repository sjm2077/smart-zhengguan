"""Read saved per-sheet mappings for both preview and confirmed import."""
import csv
import hashlib
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

import openpyxl
from django.conf import settings
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Student, ScholarshipAward, EmploymentRecord, ImportBatchRecord, ImportBatch


FIELDS = {
    'student': {'student_id': ['学号', '学生学号'], 'name': ['姓名', '学生姓名'],
                'gender': ['性别'], 'grade': ['年级'], 'major': ['专业'],
                'college': ['学院'], 'advisor_name': ['导师', '导师姓名'],
                'degree_type': ['学位类型', '培养层次'], 'current_status': ['学籍状态']},
    'scholarship': {'award_name': ['奖学金名称', '奖项名称'], 'amount': ['金额', '奖学金金额'],
                    'award_year': ['年度', '获奖年度'], 'award_type': ['奖项类型'], 'award_category': ['奖项类别']},
    'employment': {'employer_name': ['就业单位', '单位名称'], 'destination_type': ['去向类型', '就业类型'],
                   'province': ['省份', '就业省份'], 'graduation_year': ['毕业年份', '毕业年度'],
                   'industry': ['行业'], 'unit_nature': ['单位性质']},
    'course_grade': {'course_name': ['课程名称'], 'score': ['成绩'], 'credits': ['学分']},
}
MODELS = {'student': Student, 'scholarship': ScholarshipAward, 'employment': EmploymentRecord}
STRATEGIES = {'create_only', 'update_empty', 'overwrite', 'validate_only'}


def upload_path(batch):
    root = (Path(settings.BASE_DIR) / 'tmp' / 'uploads').resolve()
    path = (root / f'{batch.batch_id}_{batch.file_name}').resolve()
    if path.parent != root or not path.is_file():
        raise ValueError('上传文件不存在，请重新上传')
    return path


def plan_path(batch):
    return upload_path(batch).with_suffix('.mapping.json')


def read_sheets(batch):
    path = upload_path(batch)
    if path.suffix.lower() == '.csv':
        with path.open(encoding='utf-8-sig', newline='') as source:
            return {'Sheet1': list(csv.reader(source))}
    workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        return {sheet.title: list(sheet.values) for sheet in workbook}
    finally:
        workbook.close()


def field_options(module):
    result = [{'field_code': 'student.student_id', 'field_name_cn': '学号'}]
    for key, aliases in FIELDS.get(module, {}).items():
        code = f'{module}.{key}'
        if code != 'student.student_id':
            result.append({'field_code': code, 'field_name_cn': aliases[0]})
    return result


def load_plan(batch):
    path = plan_path(batch)
    if path.exists():
        return json.loads(path.read_text(encoding='utf-8'))
    sheets = []
    for name, rows in read_sheets(batch).items():
        headers = [str(value).strip() if value is not None else '' for value in rows[0]] if rows else []
        header_set = set(headers)
        module = ('course_grade' if '课程名称' in header_set and '成绩' in header_set else
                  'scholarship' if header_set.intersection(FIELDS['scholarship']['award_name']) else
                  'employment' if header_set.intersection(FIELDS['employment']['employer_name']) else
                  'student' if {'学号', '姓名'}.issubset(header_set) else 'unsupported')
        mapping = {}
        for header in headers:
            if header in ('学号', '学生学号'):
                mapping[header] = 'student.student_id'
            for field, aliases in FIELDS.get(module, {}).items():
                if header in aliases:
                    mapping[header] = f'{module}.{field}'
        samples = next((row for row in rows[1:] if any(value is not None and value != '' for value in row)), [])
        sheets.append({'sheet_name': name, 'module': module, 'mapping': mapping,
                       'headers': headers, 'sample_values': [str(value) if value is not None else '' for value in samples],
                       'row_count': sum(any(value is not None and value != '' for value in row) for row in rows[1:]),
                       'fields': field_options(module)})
    return {'sheets': sheets}


def save_plan(batch, plan):
    plan_path(batch).write_text(json.dumps(plan, ensure_ascii=False), encoding='utf-8')


def identify_sheets(batch, overrides=None):
    plan = load_plan(batch)
    for sheet in plan['sheets']:
        module = overrides.get(sheet['sheet_name']) if isinstance(overrides, dict) else overrides
        if module:
            if module not in FIELDS and module != 'unsupported':
                raise ValueError('无法识别目标模块')
            sheet['module'] = module
            sheet['fields'] = field_options(module)
            allowed = {field['field_code'] for field in sheet['fields']}
            sheet['mapping'] = {key: value for key, value in sheet['mapping'].items() if value in allowed}
    save_plan(batch, plan)
    return [{'sheet_name': sheet['sheet_name'], 'best_match': sheet['module'],
             'confidence': 1 if sheet['module'] != 'unsupported' else 0,
             'candidate_modules': [], 'row_count': sheet['row_count']} for sheet in plan['sheets']]


def save_mapping(batch, sheet_name, mapping):
    plan = load_plan(batch)
    sheet = next((sheet for sheet in plan['sheets'] if sheet['sheet_name'] == sheet_name), None)
    if sheet is None:
        raise ValueError('请选择实际的 Sheet 名称')
    allowed = {field['field_code'] for field in sheet['fields']}
    if any(key not in sheet['headers'] or value not in allowed for key, value in mapping.items()):
        raise ValueError('映射包含不属于当前 Sheet 的列或字段')
    if len(set(mapping.values())) != len(mapping):
        raise ValueError('同一系统字段不能映射多个文件列')
    sheet['mapping'] = mapping
    save_plan(batch, plan)


def preview_signature(batch, strategy):
    plan = load_plan(batch)
    data = upload_path(batch).read_bytes() + json.dumps(plan['sheets'], sort_keys=True, ensure_ascii=False).encode('utf-8')
    return hashlib.sha256(data + strategy.encode('utf-8')).hexdigest()


def remember_preview(batch, strategy):
    plan = load_plan(batch)
    plan['preview_signature'] = preview_signature(batch, strategy)
    save_plan(batch, plan)


def prepare_import(batch, strategy):
    if strategy not in STRATEGIES:
        raise ValueError('不支持的更新策略')
    plan = load_plan(batch)
    sources = read_sheets(batch)
    errors, warnings, operations, summaries = [], [], [], []
    known_students = {item.student_id: item for item in Student.objects.all()}
    incoming_students = {}
    # Student data may be in a later Sheet than awards.
    for sheet in plan['sheets']:
        if sheet['module'] == 'student':
            for row in sources[sheet['sheet_name']][1:]:
                record = mapped_row(sheet, row)
                if all(record.get(f'student.{key}') for key in ('student_id', 'name', 'major', 'grade')):
                    incoming_students[str(record['student.student_id'])] = record
    for sheet in plan['sheets']:
        name, module = sheet['sheet_name'], sheet['module']
        counts = dict(new_count=0, update_count=0, unchanged_count=0, error_count=0, skipped_count=0)
        seen = set()
        for index, row in enumerate(sources[name][1:], 2):
            if not any(value is not None and value != '' for value in row):
                continue
            if module not in MODELS:
                counts['skipped_count'] += 1
                continue
            record = mapped_row(sheet, row)
            try:
                sid = str(record.get('student.student_id') or '').strip()
                if not sid:
                    raise ValueError('缺少学号，请检查字段映射')
                student = known_students.get(sid)
                profile = incoming_students.get(sid, {})
                values = {key.split('.', 1)[1]: value for key, value in record.items() if key.startswith(module + '.')}
                if module == 'student':
                    for required in ('student_id', 'name', 'major', 'grade'):
                        if not values.get(required):
                            raise ValueError(f'缺少必填字段：{required}')
                    existing = student
                    key = (sid,)
                else:
                    if not student and not profile:
                        raise ValueError(f'学号 {sid} 不存在，文件中也没有可用的学生基本信息')
                    if module == 'scholarship':
                        if not values.get('award_name') or not values.get('award_year'):
                            raise ValueError('缺少奖学金名称或年度')
                        values['award_year'] = int(values['award_year'])
                        amount = Decimal(str(values.get('amount', '')))
                        if not amount.is_finite() or amount < 0:
                            raise ValueError('奖学金金额必须为非负数')
                        values['amount'] = str(amount)
                        key = (sid, values['award_name'], values['award_year'])
                        existing = ScholarshipAward.objects.filter(student=student, award_name=key[1], award_year=key[2]).first() if student else None
                    else:
                        if not values.get('employer_name') or not values.get('graduation_year') or not values.get('destination_type'):
                            raise ValueError('缺少就业单位、毕业年度或去向类型')
                        values['graduation_year'] = int(values['graduation_year'])
                        key = (sid, values['graduation_year'])
                        existing = EmploymentRecord.objects.filter(student=student, graduation_year=key[1]).first() if student else None
                if key in seen:
                    raise ValueError('同一 Sheet 中记录业务键重复')
                seen.add(key)
                for field, value in values.items():
                    definition = MODELS[module]._meta.get_field(field)
                    normalized = definition.to_python(value)
                    definition.validate(normalized, existing)
                    definition.run_validators(normalized)
                    values[field] = normalized
                changes = {field: value for field, value in values.items()
                           if existing is None or (getattr(existing, field) != value
                           and (strategy != 'update_empty' or getattr(existing, field) in (None, '')))}
                action = ('skip' if strategy == 'validate_only' or existing and strategy == 'create_only' else
                          'create' if not existing else 'update' if changes else 'unchanged')
                counts[{'skip': 'skipped_count', 'create': 'new_count', 'update': 'update_count', 'unchanged': 'unchanged_count'}[action]] += 1
                operations.append({'sheet': name, 'row': index, 'module': module, 'student_id': sid,
                                   'existing': existing, 'values': values, 'changes': changes, 'action': action})
            except (ValueError, TypeError, InvalidOperation, ValidationError) as exc:
                counts['error_count'] += 1
                errors.append({'sheet': name, 'row': index, 'field': '', 'message': str(exc)})
        if module not in MODELS:
            warnings.append({'sheet': name, 'message': f'“{name}”共 {counts["skipped_count"]} 行暂不支持导入；当前系统没有学生课程成绩明细表。' if module == 'course_grade' else f'“{name}”尚未识别到支持的模块，已跳过。'})
        summaries.append({'sheet_name': name, 'module': module, 'row_count': sheet['row_count'], **counts})
    totals = {key: sum(sheet[key] for sheet in summaries) for key in ('new_count', 'update_count', 'unchanged_count', 'error_count', 'skipped_count')}
    preview = {**totals, 'total_rows': sum(sum(sheet[key] for key in totals) for sheet in summaries), 'sheets': summaries,
               'sample_changes': [{key: operation[key] for key in ('sheet', 'row', 'student_id', 'action')} for operation in operations[:20]]}
    return {'validation': {'errors': errors, 'warnings': warnings}, 'preview': preview, '_operations': operations}


def mapped_row(sheet, row):
    return {sheet['mapping'][header]: row[index] for index, header in enumerate(sheet['headers'])
            if header in sheet['mapping'] and index < len(row) and row[index] is not None and row[index] != ''}


@transaction.atomic
def execute_batch(batch, strategy):
    batch = ImportBatch.objects.select_for_update().get(pk=batch.pk)
    if batch.status != 'previewing':
        raise ValueError('请先执行校验预览，请勿重复导入')
    if load_plan(batch).get('preview_signature') != preview_signature(batch, strategy):
        raise ValueError('文件、映射或更新策略已改变，请重新预览')
    # Re-read the same file and mappings; a preview never writes business records.
    result = prepare_import(batch, strategy)
    if result['validation']['errors']:
        raise ValueError('存在校验错误，请修正映射并重新预览')
    for op in sorted(result['_operations'], key=lambda item: item['module'] != 'student'):
        if op['action'] in ('skip', 'unchanged'):
            continue
        model = MODELS[op['module']]
        existing = op['existing']
        before = {field: str(getattr(existing, field)) for field in op['changes']} if existing else {}
        values = op['changes'] if existing else dict(op['values'])
        if existing:
            for field, value in values.items():
                setattr(existing, field, value)
            existing.full_clean()
            existing.save()
        else:
            if op['module'] == 'student':
                values.setdefault('degree_type', 'academic_master')
            else:
                student = Student.objects.get(student_id=op['student_id'])
                values.update(student=student, student_name=student.name)
                if op['module'] == 'scholarship':
                    values.update(grade=student.grade, major=student.major)
                    values.setdefault('award_type', values['award_name'])
                    values.setdefault('award_category', 'scholarship')
                else:
                    values.setdefault('status', 'completed')
            existing = model(**values)
            existing.full_clean()
            existing.save()
        existing.refresh_from_db()
        ImportBatchRecord.objects.create(batch=batch, row_index=op['row'], action=op['action'],
                                         target_model=model.__name__, target_id=str(existing.pk),
                                         before_value=before, after_value={'__fields': {field: str(getattr(existing, field)) for field in op['values']}, 'sheet': op['sheet']})
    for field in ('new_count', 'update_count', 'unchanged_count', 'error_count', 'skipped_count', 'total_rows'):
        setattr(batch, field, result['preview'][field])
    batch.status = 'completed'
    batch.completed_at = timezone.now()
    batch.save()
    return {'success': True, 'batch_id': batch.batch_id, 'summary': result['preview']}
