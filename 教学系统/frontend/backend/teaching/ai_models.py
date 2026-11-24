"""智能分析与预警中心：人工核查流程持久化模型。

Django 会通过 teaching/models.py 末尾 `from .ai_models import AIWarningCase` 注册此模型。
使用 `python manage.py makemigrations teaching && python manage.py migrate` 生成并应用数据库迁移。
"""
from django.db import models


class AIWarningCase(models.Model):
    STATUS_PENDING = "pending"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_RESOLVED = "resolved"
    STATUS_DISMISSED = "dismissed"
    STATUS_CHOICES = [
        (STATUS_PENDING, "待核查"),
        (STATUS_IN_PROGRESS, "处理中"),
        (STATUS_RESOLVED, "已解决"),
        (STATUS_DISMISSED, "已排除"),
    ]

    event_key = models.CharField(max_length=200, unique=True, verbose_name="规则事件唯一标识")
    rule_code = models.CharField(max_length=64, verbose_name="识别规则")
    semester_key = models.CharField(max_length=80, blank=True, verbose_name="所属学期")
    category = models.CharField(max_length=32, verbose_name="风险类别")
    severity = models.CharField(max_length=16, verbose_name="风险等级")
    title = models.CharField(max_length=180, verbose_name="事项标题")
    description = models.TextField(verbose_name="检测说明")
    source = models.CharField(max_length=120, verbose_name="数据来源")
    route_path = models.CharField(max_length=120, default="/ai-warning", verbose_name="相关页面")
    evidence = models.JSONField(default=dict, blank=True, verbose_name="可核验依据")
    # 检测事实与人工处理状态分离：基础数据修复后不覆盖人工核查结论。
    source_active = models.BooleanField(default=True, verbose_name="当前仍被规则识别")
    source_cleared_at = models.DateTimeField(null=True, blank=True, verbose_name="规则不再命中的时间")
    source_reappeared_at = models.DateTimeField(null=True, blank=True, verbose_name="规则再次命中的时间")
    status = models.CharField(max_length=24, choices=STATUS_CHOICES, default=STATUS_PENDING)
    handler = models.CharField(max_length=80, blank=True, verbose_name="责任人")
    resolution_note = models.TextField(blank=True, verbose_name="核查与处理说明")
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at", "-id"]
        verbose_name = "智能预警处理记录"
        verbose_name_plural = verbose_name
        indexes = [models.Index(fields=["status", "-updated_at"])]

    def __str__(self):
        return f"{self.title} [{self.get_status_display()}]"
