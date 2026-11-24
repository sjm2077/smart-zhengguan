
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('api', '0003_achievement_subject'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='research_direction',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='研究方向'),
        ),
        migrations.AddField(
            model_name='project',
            name='region',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='研究区域'),
        ),
        migrations.AddField(
            model_name='project',
            name='country_or_region',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='国家或地区'),
        ),
        migrations.AddField(
            model_name='project',
            name='keywords',
            field=models.CharField(blank=True, max_length=500, null=True, verbose_name='分析关键词'),
        ),
        migrations.AddField(
            model_name='achievement',
            name='research_direction',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='研究方向'),
        ),
        migrations.AddField(
            model_name='achievement',
            name='region',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='研究区域'),
        ),
        migrations.AddField(
            model_name='achievement',
            name='country_or_region',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='国家或地区'),
        ),
        migrations.AddField(
            model_name='achievement',
            name='keywords',
            field=models.CharField(blank=True, max_length=500, null=True, verbose_name='分析关键词'),
        ),
    ]
