"""
R05: Data Upload Services
上传、识别、校验和导入服务
"""
import csv
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any

import openpyxl
from django.db import transaction
from django.utils import timezone

from .models import (
    ImportBatch,
    ImportBatchRecord,
    ImportRecordAction,
    FieldCatalog,
    Student,
)


def calculate_file_hash(file_path: str) -> str:
    """计算文件 SHA256 哈希值"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def parse_workbook(file_path: str) -> dict:
    """
    解析 Excel 或 CSV 文件

    Returns:
        {
            'sheets': [
                {
                    'name': str,
                    'headers': list[str],
                    'sample_rows': list[list],  # 最多5行
                    'empty_count': int,
                    'merged_cells': list
                }
            ]
        }
    """
    file_path_obj = Path(file_path)
    extension = file_path_obj.suffix.lower()

    sheets_data = []

    if extension == '.csv':
        # 处理 CSV 文件
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            rows = list(reader)

            if not rows:
                return {'sheets': []}

            headers = rows[0] if rows else []
            sample_rows = rows[1:6] if len(rows) > 1 else []
            empty_count = sum(1 for row in rows if not any(row))

            sheets_data.append({
                'name': 'Sheet1',
                'headers': headers,
                'sample_rows': sample_rows,
                'empty_count': empty_count,
                'merged_cells': []
            })

    elif extension in ['.xlsx', '.xls']:
        # 处理 Excel 文件
        workbook = openpyxl.load_workbook(file_path, data_only=True)  # data_only=True 读取公式缓存值

        for sheet_name in workbook.sheetnames:
            sheet = workbook[sheet_name]

            # 读取表头（第一行）
            headers = []
            first_row = next(sheet.iter_rows(min_row=1, max_row=1, values_only=True), None)
            if first_row:
                headers = [str(cell) if cell is not None else '' for cell in first_row]

            # 读取样例数据（最多5行）
            sample_rows = []
            for row in sheet.iter_rows(min_row=2, max_row=6, values_only=True):
                sample_rows.append([str(cell) if cell is not None else '' for cell in row])

            # 统计空行数量
            empty_count = 0
            for row in sheet.iter_rows(min_row=2, values_only=True):
                if not any(row):
                    empty_count += 1

            # 获取合并单元格信息
            merged_cells = [str(merged_range) for merged_range in sheet.merged_cells.ranges]

            sheets_data.append({
                'name': sheet_name,
                'headers': headers,
                'sample_rows': sample_rows,
                'empty_count': empty_count,
                'merged_cells': merged_cells
            })

    return {'sheets': sheets_data}


def identify_module(sheet_info: dict, field_catalog: list[dict]) -> list[dict]:
    """
    识别 Sheet 对应的目标模块

    Args:
        sheet_info: parse_workbook 返回的 sheet 信息
        field_catalog: 字段目录列表

    Returns:
        [
            {
                'sheet_name': str,
                'candidate_modules': [
                    {
                        'module': str,
                        'score': float,
                        'matched_fields': list[str]
                    }
                ],
                'best_match': str,
                'confidence': float
            }
        ]
    """
    results = []

    for sheet in sheet_info.get('sheets', []):
        sheet_headers = [h.lower().strip() for h in sheet['headers'] if h]

        # 按模块分组字段
        module_fields = {}
        for field in field_catalog:
            module = field.get('module', '')
            if module not in module_fields:
                module_fields[module] = []
            module_fields[module].append(field)

        # 对每个模块计算匹配度
        candidate_modules = []
        for module, fields in module_fields.items():
            matched_fields = []
            total_weight = 0
            matched_weight = 0

            for field in fields:
                field_weight = 1.0
                total_weight += field_weight

                # 检查字段名和别名是否匹配
                field_names = [field.get('field_name_cn', '').lower()]
                field_names.extend([alias.lower() for alias in field.get('aliases', [])])

                for field_name in field_names:
                    if any(field_name in header for header in sheet_headers):
                        matched_fields.append(field.get('field_code', ''))
                        matched_weight += field_weight
                        break

            if total_weight > 0:
                score = matched_weight / total_weight
                if score > 0:  # 只保留有匹配的模块
                    candidate_modules.append({
                        'module': module,
                        'score': score,
                        'matched_fields': matched_fields
                    })

        # 按分数排序
        candidate_modules.sort(key=lambda x: x['score'], reverse=True)

        # 确定最佳匹配和置信度
        best_match = ''
        confidence = 0.0

        if candidate_modules:
            best_match = candidate_modules[0]['module']
            confidence = candidate_modules[0]['score']

            # 如果有多个候选且分数接近，降低置信度
            if len(candidate_modules) > 1:
                second_score = candidate_modules[1]['score']
                if confidence - second_score < 0.1:
                    confidence *= 0.8  # 降低置信度

        results.append({
            'sheet_name': sheet['name'],
            'candidate_modules': candidate_modules[:3],  # 只返回前3个候选
            'best_match': best_match,
            'confidence': confidence
        })

    return results


def validate_records(
    target_model: str,
    mapped_data: list[dict],
    field_catalog: list[dict]
) -> dict:
    """
    校验记录数据

    Returns:
        {
            'valid': [record],
            'warnings': [{'row': int, 'field': str, 'message': str}],
            'errors': [{'row': int, 'field': str, 'message': str}]
        }
    """
    valid = []
    warnings = []
    errors = []

    # 构建字段信息字典
    field_info = {f['field_code']: f for f in field_catalog}

    for idx, record in enumerate(mapped_data):
        row_num = idx + 2  # Excel 行号（从2开始，因为第1行是表头）
        record_errors = []
        record_warnings = []

        # 检查必填字段
        if target_model == 'Student':
            required_fields = ['student_id', 'name', 'major', 'grade']
            for field in required_fields:
                field_code = f'student.{field}'
                if not record.get(field_code):
                    record_errors.append({
                        'row': row_num,
                        'field': field,
                        'message': f'必填字段"{field}"缺失'
                    })

            # 检查学号格式（假设学号是数字）
            student_id = record.get('student.student_id', '')
            if student_id and not str(student_id).isdigit():
                record_warnings.append({
                    'row': row_num,
                    'field': 'student_id',
                    'message': '学号格式可能不正确'
                })

        # 检查枚举值
        for field_code, value in record.items():
            if field_code in field_info:
                field = field_info[field_code]
                dict_items = field.get('dict_items', [])

                if dict_items and value and value not in dict_items:
                    record_errors.append({
                        'row': row_num,
                        'field': field_code,
                        'message': f'值"{value}"不在允许的枚举值中: {dict_items}'
                    })

        # 如果有错误，记录到 errors；否则记录为 valid
        if record_errors:
            errors.extend(record_errors)
        else:
            valid.append(record)
            if record_warnings:
                warnings.extend(record_warnings)

    return {
        'valid': valid,
        'warnings': warnings,
        'errors': errors
    }


def preview_diff(
    target_model: str,
    validated_data: list[dict],
    strategy: str
) -> dict:
    """
    预览差异

    Args:
        target_model: 目标模型名称
        validated_data: 已校验的数据
        strategy: 更新策略 (create_only / update_empty / overwrite / validate_only)

    Returns:
        {
            'new_count': int,
            'update_count': int,
            'unchanged_count': int,
            'error_count': int,
            'skipped_count': int,
            'sample_changes': list[dict]  # 前20条
        }
    """
    new_count = 0
    update_count = 0
    unchanged_count = 0
    error_count = 0
    skipped_count = 0
    sample_changes = []

    if target_model == 'Student':
        for record in validated_data[:20]:  # 只预览前20条
            student_id = record.get('student.student_id')

            try:
                existing = Student.objects.get(student_id=student_id)

                if strategy == 'create_only':
                    unchanged_count += 1
                    sample_changes.append({
                        'action': 'skip',
                        'student_id': student_id,
                        'reason': '学生已存在，策略为仅新增'
                    })
                elif strategy == 'validate_only':
                    unchanged_count += 1
                    sample_changes.append({
                        'action': 'validate',
                        'student_id': student_id,
                        'reason': '仅校验模式'
                    })
                else:
                    # 判断是否需要更新
                    has_changes = False
                    changes = {}

                    field_mapping = {
                        'student.name': 'name',
                        'student.major': 'major',
                        'student.grade': 'grade',
                    }

                    for record_key, model_field in field_mapping.items():
                        new_value = record.get(record_key)
                        old_value = getattr(existing, model_field, None)

                        if new_value and str(new_value) != str(old_value):
                            if strategy == 'update_empty' and old_value:
                                continue  # 跳过非空字段
                            has_changes = True
                            changes[model_field] = {
                                'old': old_value,
                                'new': new_value
                            }

                    if has_changes:
                        update_count += 1
                        sample_changes.append({
                            'action': 'update',
                            'student_id': student_id,
                            'changes': changes
                        })
                    else:
                        unchanged_count += 1
                        sample_changes.append({
                            'action': 'unchanged',
                            'student_id': student_id
                        })

            except Student.DoesNotExist:
                new_count += 1
                sample_changes.append({
                    'action': 'create',
                    'student_id': student_id,
                    'data': record
                })

    return {
        'new_count': new_count,
        'update_count': update_count,
        'unchanged_count': unchanged_count,
        'error_count': error_count,
        'skipped_count': skipped_count,
        'sample_changes': sample_changes
    }


def execute_import(
    batch_id: str,
    target_model: str,
    validated_data: list[dict],
    strategy: str
) -> dict:
    """
    执行导入

    Returns:
        {
            'success': bool,
            'batch_id': str,
            'summary': dict
        }
    """
    try:
        batch = ImportBatch.objects.get(batch_id=batch_id)
    except ImportBatch.DoesNotExist:
        return {
            'success': False,
            'batch_id': batch_id,
            'summary': {'error': '批次不存在'}
        }

    new_count = 0
    update_count = 0
    unchanged_count = 0
    error_count = 0

    try:
        with transaction.atomic():
            if target_model == 'Student':
                for idx, record in enumerate(validated_data):
                    row_index = idx + 2
                    student_id = record.get('student.student_id')

                    try:
                        existing = Student.objects.filter(student_id=student_id).first()

                        if existing:
                            if strategy == 'create_only':
                                unchanged_count += 1
                                ImportBatchRecord.objects.create(
                                    batch=batch,
                                    row_index=row_index,
                                    action=ImportRecordAction.SKIP,
                                    target_model=target_model,
                                    target_id=student_id,
                                    before_value={},
                                    after_value=record
                                )
                            else:
                                # 记录修改前的值
                                before_value = {
                                    'name': existing.name,
                                    'major': existing.major,
                                    'grade': existing.grade,
                                }

                                # 更新字段
                                if record.get('student.name'):
                                    existing.name = record['student.name']
                                if record.get('student.major'):
                                    existing.major = record['student.major']
                                if record.get('student.grade'):
                                    existing.grade = record['student.grade']

                                existing.save()
                                update_count += 1

                                ImportBatchRecord.objects.create(
                                    batch=batch,
                                    row_index=row_index,
                                    action=ImportRecordAction.UPDATE,
                                    target_model=target_model,
                                    target_id=student_id,
                                    before_value=before_value,
                                    after_value=record
                                )
                        else:
                            # 创建新记录
                            new_student = Student.objects.create(
                                student_id=student_id,
                                name=record.get('student.name', ''),
                                major=record.get('student.major', ''),
                                grade=record.get('student.grade', ''),
                                degree_type='academic_master'  # 默认值
                            )
                            new_count += 1

                            ImportBatchRecord.objects.create(
                                batch=batch,
                                row_index=row_index,
                                action=ImportRecordAction.CREATE,
                                target_model=target_model,
                                target_id=student_id,
                                before_value={},
                                after_value=record
                            )

                    except Exception as e:
                        error_count += 1
                        ImportBatchRecord.objects.create(
                            batch=batch,
                            row_index=row_index,
                            action=ImportRecordAction.ERROR,
                            target_model=target_model,
                            target_id=student_id,
                            before_value={},
                            after_value=record,
                            errors=[str(e)]
                        )

            # 更新批次统计
            batch.new_count = new_count
            batch.update_count = update_count
            batch.unchanged_count = unchanged_count
            batch.error_count = error_count
            batch.completed_at = timezone.now()
            batch.save()

            return {
                'success': True,
                'batch_id': batch_id,
                'summary': {
                    'new_count': new_count,
                    'update_count': update_count,
                    'unchanged_count': unchanged_count,
                    'error_count': error_count
                }
            }

    except Exception as e:
        return {
            'success': False,
            'batch_id': batch_id,
            'summary': {'error': str(e)}
        }


def revert_batch(batch_id: str) -> dict:
    """
    撤销批次导入

    Returns:
        {
            'reverted_count': int,
            'conflict_count': int,
            'conflicts': list
        }
    """
    try:
        batch = ImportBatch.objects.get(batch_id=batch_id)
    except ImportBatch.DoesNotExist:
        return {
            'reverted_count': 0,
            'conflict_count': 0,
            'conflicts': [],
            'error': '批次不存在'
        }

    reverted_count = 0
    conflict_count = 0
    conflicts = []

    records = batch.records.filter(is_reverted=False).order_by('-created_at', '-pk')

    with transaction.atomic():
        for record in records:
            if '__fields' in record.after_value:
                from .upload_pipeline import MODELS
                model = next((model for model in MODELS.values() if model.__name__ == record.target_model), None)
                instance = model.objects.filter(pk=record.target_id).first() if model else None
                if instance is None or any(str(getattr(instance, field)) != value for field, value in record.after_value['__fields'].items()):
                    conflict_count += 1
                    conflicts.append({'target_id': record.target_id, 'reason': '记录已被删除或在批次后被修改'})
                    continue
                if record.action == ImportRecordAction.CREATE:
                    instance.delete()
                elif record.action == ImportRecordAction.UPDATE:
                    for field, value in record.before_value.items():
                        setattr(instance, field, value)
                    instance.save()
                record.is_reverted = True
                record.save()
                reverted_count += 1
                continue
            if record.action == ImportRecordAction.CREATE:
                # 删除创建的记录
                try:
                    Student.objects.filter(student_id=record.target_id).delete()
                    record.is_reverted = True
                    record.save()
                    reverted_count += 1
                except Exception:
                    pass

            elif record.action == ImportRecordAction.UPDATE:
                # 恢复修改前的值
                try:
                    student = Student.objects.get(student_id=record.target_id)

                    # 检查是否有冲突（当前值与 after_value 不一致）
                    current_value = {
                        'name': student.name,
                        'major': student.major,
                        'grade': student.grade,
                    }

                    has_conflict = False
                    for key in current_value:
                        if str(current_value[key]) != str(record.after_value.get(f'student.{key}', '')):
                            has_conflict = True
                            break

                    if has_conflict:
                        conflict_count += 1
                        conflicts.append({
                            'student_id': record.target_id,
                            'reason': '记录在批次后被修改，无法自动撤销'
                        })
                    else:
                        # 恢复原值
                        student.name = record.before_value.get('name', student.name)
                        student.major = record.before_value.get('major', student.major)
                        student.grade = record.before_value.get('grade', student.grade)
                        student.save()

                        record.is_reverted = True
                        record.save()
                        reverted_count += 1

                except Student.DoesNotExist:
                    conflict_count += 1
                    conflicts.append({
                        'student_id': record.target_id,
                        'reason': '记录已被删除'
                    })

    return {
        'reverted_count': reverted_count,
        'conflict_count': conflict_count,
        'conflicts': conflicts
    }


def check_duplicate(file_hash: str):
    """检查文件是否已上传"""
    return ImportBatch.objects.filter(file_hash=file_hash).first()
