from django.db import models


class College(models.Model):
    """学院"""

    code = models.CharField(
        max_length=32,
        unique=True,
        verbose_name="学院代码",
        help_text="如 CS / MATH / PHYS",
    )
    name = models.CharField(
        max_length=128,
        unique=True,
        verbose_name="学院名称",
        help_text="如 计算机科学与技术学院",
    )
    short_name = models.CharField(
        max_length=64,
        blank=True,
        default="",
        verbose_name="简称",
        help_text="如 计科院",
    )
    sort_order = models.IntegerField(
        default=0,
        verbose_name="排序权重",
        help_text="数值越小越靠前",
    )
    logo_url = models.URLField(
        max_length=512,
        blank=True,
        default="",
        verbose_name="Logo 链接",
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

    class Meta:
        db_table = "colleges"
        verbose_name = "学院"
        verbose_name_plural = verbose_name
        ordering = ["sort_order", "code"]
        indexes = [
            models.Index(fields=["code"], name="idx_col_code"),
            models.Index(fields=["is_active"], name="idx_col_active"),
            models.Index(fields=["sort_order"], name="idx_col_sort"),
        ]

    def __str__(self):
        return self.name