from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("teaching", "0004_aiwarningcase"),
    ]

    operations = [
        migrations.AddField(
            model_name="aiwarningcase", name="source_active",
            field=models.BooleanField(default=True, verbose_name="当前仍被规则识别"),
        ),
        migrations.AddField(
            model_name="aiwarningcase", name="source_cleared_at",
            field=models.DateTimeField(null=True, blank=True, verbose_name="规则不再命中的时间"),
        ),
        migrations.AddField(
            model_name="aiwarningcase", name="source_reappeared_at",
            field=models.DateTimeField(null=True, blank=True, verbose_name="规则再次命中的时间"),
        ),
    ]
