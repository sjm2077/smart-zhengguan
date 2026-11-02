from django.db import models


class Notification(models.Model):
    """通知消息模板"""

    class TypeChoices(models.TextChoices):
        SYSTEM = "system", "系统通知"
        COURSE = "course", "课程通知"
        EXAM = "exam", "考试通知"
        GRADE = "grade", "成绩通知"
        RISK = "risk", "风险预警"
        AI = "ai", "AI 建议"
        ANNOUNCEMENT = "announcement", "公告"
        OTHER = "other", "其他"

    class PriorityChoices(models.TextChoices):
        LOW = "low", "低"
        NORMAL = "normal", "普通"
        HIGH = "high", "高"
        URGENT = "urgent", "紧急"

    title = models.CharField(
        max_length=255,
        verbose_name="通知标题",
    )
    content = models.TextField(
        verbose_name="通知内容",
    )
    notification_type = models.CharField(
        max_length=32,
        choices=TypeChoices.choices,
        default=TypeChoices.SYSTEM,
        verbose_name="通知类型",
    )
    priority = models.CharField(
        max_length=16,
        choices=PriorityChoices.choices,
        default=PriorityChoices.NORMAL,
        verbose_name="优先级",
    )

    # ============ 发送者 ============
    sender = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_notifications",
        verbose_name="发送者",
        help_text="系统通知时可为空",
    )

    # ============ 关联目标（Generic Foreign Key，可选） ============
    target_type = models.CharField(
        max_length=64,
        blank=True,
        default="",
        verbose_name="关联目标类型",
        help_text="如 course_offering / exam / grade / risk_event 等的模型名或标识",
    )
    target_id = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="关联目标ID",
    )
    target_url = models.CharField(
        max_length=512,
        blank=True,
        default="",
        verbose_name="跳转链接",
        help_text="点击通知后跳转的前端路由",
    )

    # ============ 发布控制 ============
    is_published = models.BooleanField(
        default=True,
        verbose_name="是否发布",
        help_text="草稿状态可设为 False",
    )
    publish_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="发布时间",
        help_text="定时发布用，为空则立即发布",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="创建时间",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="更新时间",
    )

    class Meta:
        db_table = "notifications"
        verbose_name = "通知消息"
        verbose_name_plural = verbose_name
        ordering = ["-publish_at", "-created_at"]
        indexes = [
            models.Index(fields=["notification_type"], name="idx_notif_type"),
            models.Index(fields=["priority"], name="idx_notif_priority"),
            models.Index(fields=["sender_id"], name="idx_notif_sender_id"),
            models.Index(fields=["is_published"], name="idx_notif_published"),
            models.Index(fields=["publish_at"], name="idx_notif_publish_at"),
            models.Index(fields=["target_type", "target_id"], name="idx_notif_target"),
            models.Index(fields=["notification_type", "priority"], name="idx_notif_type_pri"),
        ]

    def __str__(self):
        return f"[{self.get_notification_type_display()}] {self.title}"


class UserNotification(models.Model):
    """用户通知关系 — 记录每个用户对每条通知的已读/未读 & 置顶状态"""

    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name="user_notifications",
        verbose_name="通知",
    )
    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="received_notifications",
        verbose_name="接收用户",
    )

    # ============ 已读/未读状态 ============
    is_read = models.BooleanField(
        default=False,
        verbose_name="是否已读",
    )
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="阅读时间",
    )

    # ============ 用户级置顶 ============
    is_pinned = models.BooleanField(
        default=False,
        verbose_name="是否置顶",
        help_text="用户可将重要通知置顶显示",
    )
    pinned_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="置顶时间",
    )

    # ============ 软删除 ============
    is_deleted = models.BooleanField(
        default=False,
        verbose_name="是否删除",
        help_text="用户删除通知后标记为 True，不物理删除",
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="删除时间",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="创建时间",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="更新时间",
    )

    class Meta:
        db_table = "user_notifications"
        verbose_name = "用户通知"
        verbose_name_plural = verbose_name
        ordering = ["-is_pinned", "-notification__publish_at", "-notification__created_at"]
        unique_together = [
            ["notification", "user"],
        ]
        indexes = [
            models.Index(fields=["user_id"], name="idx_un_user_id"),
            models.Index(fields=["notification_id"], name="idx_un_notif_id"),
            models.Index(fields=["is_read"], name="idx_un_is_read"),
            models.Index(fields=["is_pinned"], name="idx_un_is_pinned"),
            models.Index(fields=["is_deleted"], name="idx_un_is_deleted"),
            models.Index(fields=["user_id", "is_read"], name="idx_un_user_read"),
            models.Index(fields=["user_id", "is_pinned"], name="idx_un_user_pin"),
            models.Index(fields=["user_id", "is_deleted", "is_read"], name="idx_un_user_del_read"),
        ]

    def __str__(self):
        status = "✓" if self.is_read else "✗"
        pin = "📌" if self.is_pinned else ""
        return f"{pin}[{status}] {self.user.username} ← {self.notification.title}"