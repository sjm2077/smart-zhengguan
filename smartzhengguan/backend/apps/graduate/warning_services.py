"""
R07: Warning Rule Engine Services
预警规则引擎服务
"""
import hashlib
from datetime import datetime, timedelta
from typing import Optional

from django.db import transaction
from django.utils import timezone

from .models import (
    WarningRule,
    WarningRuleVersion,
    WarningInstance,
    WarningInstanceStatus,
    WarningTreatmentLog,
    Student,
    PredictionSnapshot,
)


def evaluate_rule(rule: WarningRule, student: Student) -> Optional[dict]:
    """
    评估规则是否命中

    Args:
        rule: 预警规则
        student: 学生实例

    Returns:
        命中时返回 {indicator_value, threshold, data_time, evidence}
        未命中返回 None
    """
    # 获取学生最新的预测快照
    snapshot = student.prediction_snapshots.order_by('-captured_at').first()

    if not snapshot:
        return None

    # 获取指标值
    indicator_field = rule.indicator_field
    indicator_value = None

    if hasattr(snapshot, indicator_field):
        indicator_value = getattr(snapshot, indicator_field)
    else:
        return None

    # 判断是否命中
    operator = rule.operator
    threshold = rule.threshold_value

    hit = False

    if operator == '<':
        hit = float(indicator_value) < float(threshold)
    elif operator == '<=':
        hit = float(indicator_value) <= float(threshold)
    elif operator == '>':
        hit = float(indicator_value) > float(threshold)
    elif operator == '>=':
        hit = float(indicator_value) >= float(threshold)
    elif operator == '==':
        hit = str(indicator_value) == str(threshold)
    elif operator == '!=':
        hit = str(indicator_value) != str(threshold)
    elif operator == 'between':
        if isinstance(threshold, list) and len(threshold) == 2:
            hit = float(threshold[0]) <= float(indicator_value) <= float(threshold[1])
    elif operator == 'in':
        if isinstance(threshold, list):
            hit = str(indicator_value) in [str(v) for v in threshold]

    if hit:
        return {
            'indicator_value': indicator_value,
            'threshold': threshold,
            'data_time': snapshot.captured_at,
            'evidence': {
                'snapshot_id': snapshot.id,
                'student_id': student.student_id,
                'student_name': student.name,
                'indicator_field': indicator_field,
            }
        }

    return None


def run_scan(rule_ids: Optional[list] = None, dry_run: bool = False) -> dict:
    """
    运行预警扫描

    Args:
        rule_ids: 规则ID列表，None表示扫描所有激活的规则
        dry_run: True表示只预估不写入

    Returns:
        {
            'total_rules': int,
            'total_students_scanned': int,
            'hits': list,
            'new_count': int,
            'duplicate_count': int
        }
    """
    # 获取要扫描的规则
    rules = WarningRule.objects.filter(is_active=True)

    if rule_ids:
        rules = rules.filter(id__in=rule_ids)

    # 获取所有学生
    students = Student.objects.all()

    hits = []
    new_count = 0
    duplicate_count = 0

    for rule in rules:
        for student in students:
            result = evaluate_rule(rule, student)

            if result:
                # 生成去重键
                dedup_key = generate_dedup_key(
                    student.student_id,
                    rule.code,
                    rule.time_window_days
                )

                # 检查是否已存在
                existing = WarningInstance.objects.filter(dedup_key=dedup_key).first()

                if existing:
                    duplicate_count += 1
                else:
                    hits.append({
                        'rule': rule,
                        'student': student,
                        'indicator_value': result['indicator_value'],
                        'threshold': result['threshold'],
                        'data_time': result['data_time'],
                        'evidence': result['evidence']
                    })

                    if not dry_run:
                        # 创建预警实例
                        create_warning_instance(rule, student, result)
                        new_count += 1

    return {
        'total_rules': rules.count(),
        'total_students_scanned': students.count(),
        'hits': hits if dry_run else [],
        'new_count': new_count,
        'duplicate_count': duplicate_count
    }


def create_warning_instance(
    rule: WarningRule,
    student: Student,
    eval_result: dict
) -> WarningInstance:
    """
    创建预警实例

    Args:
        rule: 预警规则
        student: 学生实例
        eval_result: 评估结果

    Returns:
        创建的预警实例
    """
    # 获取或创建规则版本快照
    rule_version = get_or_create_rule_version(rule)

    # 生成去重键
    dedup_key = generate_dedup_key(
        student.student_id,
        rule.code,
        rule.time_window_days
    )

    # 创建预警实例
    warning = WarningInstance.objects.create(
        rule=rule,
        rule_version=rule_version,
        student=student,
        indicator_value={'value': eval_result['indicator_value']},
        threshold_at_hit={'value': eval_result['threshold']},
        data_time=eval_result['data_time'],
        dedup_key=dedup_key
    )

    return warning


def get_or_create_rule_version(rule: WarningRule) -> WarningRuleVersion:
    """
    获取或创建规则版本快照
    """
    # 查找当前版本
    current_version = rule.versions.filter(
        version=rule.version
    ).first()

    if current_version:
        return current_version

    # 创建新版本快照
    snapshot = {
        'name': rule.name,
        'code': rule.code,
        'indicator_field': rule.indicator_field,
        'operator': rule.operator,
        'threshold_value': rule.threshold_value,
        'risk_level': rule.risk_level,
        'description': rule.description,
    }

    rule_version = WarningRuleVersion.objects.create(
        rule=rule,
        version=rule.version,
        snapshot=snapshot,
        effective_from=rule.effective_from or timezone.now().date()
    )

    return rule_version


def generate_dedup_key(student_id: str, rule_code: str, time_window_days: int) -> str:
    """
    生成去重键

    Args:
        student_id: 学号
        rule_code: 规则编码
        time_window_days: 时间窗口（天）

    Returns:
        去重键
    """
    if time_window_days > 0:
        # 使用时间窗口
        window_start = datetime.now() - timedelta(days=time_window_days)
        window_key = window_start.strftime('%Y%m%d')
    else:
        # 使用当前日期
        window_key = datetime.now().strftime('%Y%m%d')

    raw_key = f"{student_id}_{rule_code}_{window_key}"
    return hashlib.md5(raw_key.encode()).hexdigest()


def auto_resolve_warnings(student: Student, rule: WarningRule) -> None:
    """
    自动解除预警（指标恢复后）

    Args:
        student: 学生实例
        rule: 预警规则
    """
    # 检查规则是否还命中
    result = evaluate_rule(rule, student)

    if result is None:
        # 规则不再命中，解除该学生的相关预警
        warnings = WarningInstance.objects.filter(
            student=student,
            rule=rule,
            status__in=[WarningInstanceStatus.PENDING, WarningInstanceStatus.PROCESSING]
        )

        for warning in warnings:
            warning.status = WarningInstanceStatus.RESOLVED
            warning.resolution_note = "指标已恢复正常，系统自动解除"
            warning.resolved_at = timezone.now()
            warning.save()

            # 记录日志
            WarningTreatmentLog.objects.create(
                warning=warning,
                operator=None,
                action='auto_resolve',
                note='指标已恢复正常，系统自动解除'
            )


def generate_explanation(warning_instance: WarningInstance) -> dict:
    """
    生成确定性解释（不使用 LLM）

    Args:
        warning_instance: 预警实例

    Returns:
        {
            'rule_name': str,
            'rule_description': str,
            'indicator_field': str,
            'indicator_value': Any,
            'threshold': Any,
            'operator': str,
            'data_time': str,
            'evidence': dict,
            'explanation_text': str
        }
    """
    rule_snapshot = warning_instance.rule_version.snapshot
    student = warning_instance.student

    operator_text_map = {
        '<': '低于',
        '<=': '不高于',
        '>': '高于',
        '>=': '不低于',
        '==': '等于',
        '!=': '不等于',
        'between': '在...之间',
        'in': '在...之中',
    }

    operator = rule_snapshot['operator']
    operator_text = operator_text_map.get(operator, operator)

    indicator_value = warning_instance.indicator_value.get('value')
    threshold = warning_instance.threshold_at_hit.get('value')

    explanation_text = (
        f"学生 {student.name}（学号：{student.student_id}）的"
        f"{rule_snapshot['indicator_field']} "
        f"为 {indicator_value}，"
        f"{operator_text} 阈值 {threshold}，"
        f"命中规则「{rule_snapshot['name']}」，"
        f"风险等级：{rule_snapshot['risk_level']}"
    )

    return {
        'rule_name': rule_snapshot['name'],
        'rule_description': rule_snapshot.get('description', ''),
        'indicator_field': rule_snapshot['indicator_field'],
        'indicator_value': indicator_value,
        'threshold': threshold,
        'operator': operator,
        'data_time': warning_instance.data_time.isoformat(),
        'evidence': warning_instance.indicator_value,
        'explanation_text': explanation_text
    }


def generate_llm_explanation(warning_instance: WarningInstance) -> str:
    """
    生成 LLM 解释（可选）

    Args:
        warning_instance: 预警实例

    Returns:
        LLM 生成的解释文本
    """
    # 获取确定性解释
    base_explanation = generate_explanation(warning_instance)

    # TODO: 调用 LLM API 生成更通俗的解释或建议
    # 这里返回确定性解释 + 提示
    return (
        base_explanation['explanation_text'] +
        "\n\n（建议内容不代替人工判断，请结合实际情况进行处理）"
    )
