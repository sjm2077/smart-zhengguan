from django.db import models


class User(models.Model):
    """系统登录账号 / 认证"""

    class RoleChoices(models.TextChoices):
        ADMIN = "admin", "管理员"
        TEACHER = "teacher", "教师"
        STUDENT = "student", "学生"

    username = models.CharField(
        max_length=64,
        unique=True,
        verbose_name="用户名",
    )
    password_hash = models.CharField(
        max_length=255,
        verbose_name="密码哈希",
    )
    role = models.CharField(
        max_length=16,
        choices=RoleChoices.choices,
        verbose_name="角色",
    )
    # 后续通过 OneToOneField 关联 Teacher / Student，此处先使用普通外键预留
    teacher_id = models.BigIntegerField(
        null=True,
        blank=True,
        verbose_name="关联教师ID",
        help_text="仅 role=teacher 时有值",
    )
    student_id = models.BigIntegerField(
        null=True,
        blank=True,
        verbose_name="关联学生ID",
        help_text="仅 role=student 时有值",
    )
    last_login_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="最后登录时间",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="是否启用",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="创建时间",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="更新时间",
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="删除时间",
    )

    class Meta:
        db_table = "users"
        verbose_name = "用户"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["role"], name="idx_role"),
            models.Index(fields=["teacher_id"], name="idx_teacher_id"),
            models.Index(fields=["student_id"], name="idx_student_id"),
        ]

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"