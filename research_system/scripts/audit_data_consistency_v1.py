from pathlib import Path
import os
import sys
import django

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'research_system.settings')
django.setup()

from api.models import User, TeacherScore, Cooperation, FundBudget
from api.research_metrics import teacher_research_metrics

print('=' * 68)
print('科研系统统一数据口径审计 v1')
print('=' * 68)

print('\n[1] 数据库存量（只报告，不删除）')
print('演示 TeacherScore:', TeacherScore.objects.filter(is_demo=True).count())
print('正式 TeacherScore:', TeacherScore.objects.filter(is_demo=False).count())
print('演示 Cooperation:', Cooperation.objects.filter(is_demo=True).count())
print('正式 Cooperation:', Cooperation.objects.filter(is_demo=False).count())
print('演示 FundBudget:', FundBudget.objects.filter(is_demo=True).count())
print('正式 FundBudget:', FundBudget.objects.filter(is_demo=False).count())

print('\n[2] 教师统一指标抽查')
for teacher in User.objects.filter(role='teacher').select_related('dept').order_by('id')[:20]:
    m = teacher_research_metrics(teacher)
    print(
        f"{teacher.id:>4} | {teacher.real_name:<12} | "
        f"项目 {m['project_count']:>3} | 在研 {m['ongoing_projects']:>3} | "
        f"成果 {m['achievements_count']:>3} | 经费 {m['fund_total']:>10.2f} | "
        f"引用 {m['total_citation']:>4} | H {m['h_index']:>2} | "
        f"合作 {m['cooperation_count']:>3} | "
        f"综合得分 {m['comprehensive'] if m['comprehensive'] is not None else '暂无'}"
    )

print('\n[3] views.py 中仍需后续清理的模拟/fallback痕迹')
patterns = ('演示值', '演示数据', '模拟', 'demo_', 'math.sin', '随机')
path = BASE_DIR / 'api' / 'views.py'
lines = path.read_text(encoding='utf-8-sig').splitlines()
hits = []
for i, line in enumerate(lines, 1):
    if any(p in line for p in patterns):
        hits.append((i, line.strip()))

print(f'共 {len(hits)} 处')
for i, line in hits[:120]:
    print(f'  L{i}: {line[:180]}')

print('\n审计完成：本脚本只读，不修改任何业务数据。')
