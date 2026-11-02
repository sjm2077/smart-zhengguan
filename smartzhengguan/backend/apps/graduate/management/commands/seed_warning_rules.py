"""
管理命令：初始化预警规则
"""
from django.core.management.base import BaseCommand

from apps.graduate.models import WarningRule


class Command(BaseCommand):
    help = "Seed warning rules with default configurations"

    def handle(self, *args, **options):
        rules = [
            {
                'name': '欠学分预警',
                'code': 'CREDIT_LOW',
                'description': '学分完成率低于60%时触发预警',
                'target_module': 'training',
                'indicator_field': 'credit_completion_rate',
                'operator': '<',
                'threshold_value': 60,
                'risk_level': 'medium',
                'time_window_days': 0,
            },
            {
                'name': '成绩下降预警',
                'code': 'GRADE_DROP',
                'description': '课程平均成绩低于70分时触发预警',
                'target_module': 'training',
                'indicator_field': 'course_average',
                'operator': '<',
                'threshold_value': 70,
                'risk_level': 'medium',
                'time_window_days': 0,
            },
            {
                'name': '低出勤预警',
                'code': 'ATTENDANCE_LOW',
                'description': '出勤率低于70%时触发预警',
                'target_module': 'training',
                'indicator_field': 'attendance_rate',
                'operator': '<',
                'threshold_value': 70,
                'risk_level': 'high',
                'time_window_days': 0,
            },
            {
                'name': '培养节点逾期预警',
                'code': 'TASK_OVERDUE',
                'description': '存在逾期任务时触发预警',
                'target_module': 'training',
                'indicator_field': 'overdue_tasks_count',
                'operator': '>',
                'threshold_value': 0,
                'risk_level': 'medium',
                'time_window_days': 0,
            },
            {
                'name': '培养进度滞后预警',
                'code': 'PROGRESS_SLOW',
                'description': '培养计划完成率低于30%时触发预警（针对高年级学生）',
                'target_module': 'training',
                'indicator_field': 'training_plan_completion_rate',
                'operator': '<',
                'threshold_value': 30,
                'risk_level': 'high',
                'time_window_days': 0,
            },
        ]

        created_count = 0
        updated_count = 0

        for rule_data in rules:
            code = rule_data['code']
            obj, created = WarningRule.objects.update_or_create(
                code=code,
                defaults=rule_data
            )

            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Warning rules seeded: {created_count} created, {updated_count} updated'
            )
        )
