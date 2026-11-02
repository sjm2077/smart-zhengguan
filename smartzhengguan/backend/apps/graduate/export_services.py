"""
R06: Export Services
导出学生名单和汇总表服务
"""
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import openpyxl
from openpyxl.styles import Font, Alignment
from django.conf import settings
from django.db.models import QuerySet
from django.utils import timezone

from .models import (
    FieldCatalog,
    Student,
    ExportRecord,
    ExportRecordStatus,
    ExportType,
)


def get_exportable_fields() -> list[dict]:
    """
    获取可导出字段列表

    Returns:
        按模块分组的字段列表
    """
    fields = FieldCatalog.objects.filter(is_exportable=True, is_active=True).values(
        'module', 'field_code', 'field_name_cn', 'data_granularity', 'is_sensitive'
    )

    # 按模块分组
    grouped = {}
    for field in fields:
        module = field['module']
        if module not in grouped:
            grouped[module] = []
        grouped[module].append(field)

    return [{'module': k, 'fields': v} for k, v in grouped.items()]


def build_student_queryset(filters: dict, user) -> QuerySet:
    """
    构建学生查询集，应用筛选条件和权限过滤

    Args:
        filters: 筛选条件
        user: 当前用户

    Returns:
        过滤后的 Student QuerySet
    """
    queryset = Student.objects.all()

    # 应用筛选条件
    if filters.get('grade'):
        queryset = queryset.filter(grade=filters['grade'])

    if filters.get('college'):
        queryset = queryset.filter(college=filters['college'])

    if filters.get('major'):
        queryset = queryset.filter(major=filters['major'])

    if filters.get('degree_type'):
        queryset = queryset.filter(degree_type=filters['degree_type'])

    if filters.get('current_status'):
        queryset = queryset.filter(current_status=filters['current_status'])

    if filters.get('advisor_name'):
        queryset = queryset.filter(advisor_name=filters['advisor_name'])

    # 应用权限过滤
    if hasattr(user, 'role'):
        if user.role == 'teacher':
            # 教师只能看到自己指导的学生
            queryset = queryset.filter(advisor_name=user.username)
        elif user.role == 'student':
            # 学生只能看到自己
            queryset = queryset.filter(student_id=user.username)

    return queryset


def resolve_one_to_many(student, field_code: str, strategy: str) -> Any:
    """
    处理一对多关系字段

    Args:
        student: Student 实例
        field_code: 字段编码
        strategy: 处理策略

    Returns:
        处理后的值
    """
    if field_code.startswith('scholarship.'):
        scholarships = student.scholarship_awards.all()

        if strategy == 'latest':
            latest = scholarships.order_by('-award_year').first()
            if latest and field_code == 'scholarship.award_name':
                return latest.award_name
            elif latest and field_code == 'scholarship.amount':
                return float(latest.amount)

        elif strategy == 'aggregate_count':
            return scholarships.count()

        elif strategy == 'aggregate_sum' and field_code == 'scholarship.amount':
            return sum(s.amount for s in scholarships)

        elif strategy == 'merge_text' and field_code == 'scholarship.award_name':
            return ', '.join(s.award_name for s in scholarships)

        elif strategy == 'expand_rows':
            return [getattr(s, field_code.split('.')[1], '') for s in scholarships]

    elif field_code.startswith('employment.'):
        employments = student.employment_records.all()

        if strategy == 'latest':
            latest = employments.order_by('-graduation_year').first()
            if latest:
                field_name = field_code.split('.')[1]
                return getattr(latest, field_name, '')

        elif strategy == 'aggregate_count':
            return employments.count()

    return None


def apply_sensitivity_rules(value: Any, field_code: str, user) -> str:
    """
    应用敏感字段脱敏规则

    Args:
        value: 原始值
        field_code: 字段编码
        user: 当前用户

    Returns:
        脱敏后的值
    """
    # 检查是否是敏感字段
    field = FieldCatalog.objects.filter(field_code=field_code, is_sensitive=True).first()

    if not field:
        return str(value)

    # 管理员可见完整值
    if hasattr(user, 'role') and user.role == 'admin':
        return str(value)

    # 其他角色进行脱敏
    value_str = str(value)
    if len(value_str) > 4:
        # 中间脱敏
        return value_str[:2] + '***' + value_str[-2:]
    else:
        return '***'


def generate_student_list_excel(
    fields: list[str],
    filters: dict,
    one_to_many_strategies: dict,
    field_aliases: dict,
    user
) -> dict:
    """
    生成学生名单 Excel 文件

    Args:
        fields: 要导出的字段列表
        filters: 筛选条件
        one_to_many_strategies: 一对多字段处理策略
        field_aliases: 字段别名
        user: 当前用户

    Returns:
        {
            'file_path': str,
            'file_name': str,
            'row_count': int,
            'record_id': str
        }
    """
    # 获取学生数据
    students = build_student_queryset(filters, user)

    # 创建工作簿
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "学生名单"

    # 获取字段信息
    field_info = {f.field_code: f for f in FieldCatalog.objects.filter(field_code__in=fields)}

    # 构建表头
    headers = []
    for field_code in fields:
        if field_code in field_aliases:
            headers.append(field_aliases[field_code])
        elif field_code in field_info:
            headers.append(field_info[field_code].field_name_cn)
        else:
            headers.append(field_code)

    # 写入表头
    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal='center')

    # 写入数据
    row_idx = 2
    for student in students:
        for col_idx, field_code in enumerate(fields, start=1):
            value = None

            # 获取字段值
            if field_code.startswith('student.'):
                field_name = field_code.split('.')[1]
                value = getattr(student, field_name, '')
            else:
                # 处理一对多字段
                strategy = one_to_many_strategies.get(field_code, 'latest')
                value = resolve_one_to_many(student, field_code, strategy)

            # 应用脱敏
            value = apply_sensitivity_rules(value, field_code, user)

            # 防止 Excel 公式注入
            if isinstance(value, str) and value and value[0] in ['=', '+', '-', '@']:
                value = "'" + value

            ws.cell(row=row_idx, column=col_idx, value=value)

        row_idx += 1

    # 创建"导出说明" Sheet
    ws_info = wb.create_sheet("导出说明")
    ws_info.cell(row=1, column=1, value="导出说明")
    ws_info.cell(row=2, column=1, value="筛选条件:")
    ws_info.cell(row=2, column=2, value=str(filters))
    ws_info.cell(row=3, column=1, value="导出字段:")
    ws_info.cell(row=3, column=2, value=', '.join(headers))
    ws_info.cell(row=4, column=1, value="数据截止时间:")
    ws_info.cell(row=4, column=2, value=datetime.now().isoformat())
    ws_info.cell(row=5, column=1, value="生成时间:")
    ws_info.cell(row=5, column=2, value=datetime.now().isoformat())
    ws_info.cell(row=6, column=1, value="操作人:")
    ws_info.cell(row=6, column=2, value=user.username if user else '')
    ws_info.cell(row=7, column=1, value="数据行数:")
    ws_info.cell(row=7, column=2, value=row_idx - 2)

    # 保存文件
    export_dir = Path(settings.BASE_DIR) / 'tmp' / 'exports'
    export_dir.mkdir(parents=True, exist_ok=True)

    record_id = str(uuid.uuid4())
    file_name = f"student_list_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    file_path = export_dir / f"{record_id}_{file_name}"

    wb.save(str(file_path))

    # 创建导出记录
    ExportRecord.objects.create(
        record_id=record_id,
        operator=user,
        export_type=ExportType.STUDENT_LIST,
        filters=filters,
        fields=fields,
        row_count=row_idx - 2,
        file_path=str(file_path),
        file_name=file_name,
        status=ExportRecordStatus.COMPLETED,
        expires_at=timezone.now() + timedelta(days=7)
    )

    return {
        'file_path': str(file_path),
        'file_name': file_name,
        'row_count': row_idx - 2,
        'record_id': record_id
    }


def generate_summary_table_excel(filters: dict, user) -> dict:
    """
    生成汇总表 Excel 文件

    Args:
        filters: 筛选条件
        user: 当前用户

    Returns:
        {
            'file_path': str,
            'file_name': str,
            'row_count': int,
            'record_id': str
        }
    """
    # 获取学生数据
    students = build_student_queryset(filters, user)

    # 按年级和专业统计
    from django.db.models import Count
    summary = students.values('grade', 'major').annotate(
        total=Count('id')
    ).order_by('grade', 'major')

    # 创建工作簿
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "汇总统计"

    # 写入表头
    headers = ['年级', '专业', '人数']
    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal='center')

    # 写入数据
    row_idx = 2
    for item in summary:
        ws.cell(row=row_idx, column=1, value=item['grade'])
        ws.cell(row=row_idx, column=2, value=item['major'])
        ws.cell(row=row_idx, column=3, value=item['total'])
        row_idx += 1

    # 创建"导出说明" Sheet
    ws_info = wb.create_sheet("导出说明")
    ws_info.cell(row=1, column=1, value="导出说明")
    ws_info.cell(row=2, column=1, value="导出类型:")
    ws_info.cell(row=2, column=2, value="汇总统计表")
    ws_info.cell(row=3, column=1, value="筛选条件:")
    ws_info.cell(row=3, column=2, value=str(filters))
    ws_info.cell(row=4, column=1, value="生成时间:")
    ws_info.cell(row=4, column=2, value=datetime.now().isoformat())
    ws_info.cell(row=5, column=1, value="操作人:")
    ws_info.cell(row=5, column=2, value=user.username if user else '')

    # 保存文件
    export_dir = Path(settings.BASE_DIR) / 'tmp' / 'exports'
    export_dir.mkdir(parents=True, exist_ok=True)

    record_id = str(uuid.uuid4())
    file_name = f"summary_table_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    file_path = export_dir / f"{record_id}_{file_name}"

    wb.save(str(file_path))

    # 创建导出记录
    ExportRecord.objects.create(
        record_id=record_id,
        operator=user,
        export_type=ExportType.SUMMARY_TABLE,
        filters=filters,
        fields=[],
        row_count=row_idx - 2,
        file_path=str(file_path),
        file_name=file_name,
        status=ExportRecordStatus.COMPLETED,
        expires_at=timezone.now() + timedelta(days=7)
    )

    return {
        'file_path': str(file_path),
        'file_name': file_name,
        'row_count': row_idx - 2,
        'record_id': record_id
    }
