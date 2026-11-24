
import os, sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'research_system.settings')

import django
django.setup()

from api.models import Project, Achievement
from api.research_analysis import infer_keywords, infer_direction, infer_geo

def pack(words):
    return '；'.join(words)

def update_project(obj):
    text = obj.project_name or ''
    dept_name = obj.dept.dept_name if obj.dept else ''
    changed = []
    keywords = pack(infer_keywords(text))
    direction = infer_direction(dept_name, text)
    country, region = infer_geo(text)

    for field, value in [
        ('keywords', keywords),
        ('research_direction', direction),
        ('country_or_region', country),
        ('region', region),
    ]:
        if value and not getattr(obj, field):
            setattr(obj, field, value)
            changed.append(field)
    if changed:
        obj.save(update_fields=changed)
    return bool(changed)

def update_achievement(obj):
    text = obj.title or ''
    dept_name = obj.dept.dept_name if obj.dept else ''
    changed = []
    keywords = pack(infer_keywords(text))
    direction = infer_direction(dept_name, text)
    country, region = infer_geo(text)

    for field, value in [
        ('keywords', keywords),
        ('research_direction', direction),
        ('country_or_region', country),
        ('region', region),
    ]:
        if value and not getattr(obj, field):
            setattr(obj, field, value)
            changed.append(field)
    if changed:
        obj.save(update_fields=changed)
    return bool(changed)

p_changed = 0
for obj in Project.objects.select_related('dept').all().iterator():
    p_changed += int(update_project(obj))

a_changed = 0
for obj in Achievement.objects.select_related('dept').all().iterator():
    a_changed += int(update_achievement(obj))

print(f'项目元数据回填：{p_changed}/{Project.objects.count()}')
print(f'成果元数据回填：{a_changed}/{Achievement.objects.count()}')
print('说明：仅依据现有项目名/成果名做确定性回填；未新增项目、成果或经费记录。')
