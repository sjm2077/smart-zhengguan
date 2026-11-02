from collections import Counter
from datetime import date
from api.models import Project, RiskWarning

today = date.today()

projects = list(Project.objects.values(
    "id", "project_no", "status",
    "actual_progress", "start_date", "end_date"
))

warnings = list(RiskWarning.objects.values(
    "id", "project_id", "warning_date", "is_resolved",
    "project__status", "project__start_date", "project__end_date"
))

checks = {
    "项目总数保持377": len(projects) == 377,
    "预警总数保持17": len(warnings) == 17,
}

overdue_non_closed = [
    p for p in projects
    if p["end_date"] and p["end_date"] < today
    and p["status"] != "结题"
]

closed_not_100 = [
    p for p in projects
    if p["status"] == "结题"
    and p["actual_progress"] != 100
]

future_completed_not_review = [
    p for p in projects
    if p["actual_progress"] == 100
    and p["end_date"] and p["end_date"] > today
    and p["status"] not in ("审核中", "结题")
]

warning_after_end = [
    w for w in warnings
    if w["warning_date"] and w["project__end_date"]
    and w["warning_date"] > w["project__end_date"]
]

warning_before_start = [
    w for w in warnings
    if w["warning_date"] and w["project__start_date"]
    and w["warning_date"] < w["project__start_date"]
]

unresolved_on_closed = [
    w for w in warnings
    if not w["is_resolved"]
    and w["project__status"] == "结题"
]

checks.update({
    "无到期但未结题项目": len(overdue_non_closed) == 0,
    "结题项目进度均为100%": len(closed_not_100) == 0,
    "未来结束且进度100%的项目均为审核中":
        len(future_completed_not_review) == 0,
    "无预警日期晚于项目结束日期": len(warning_after_end) == 0,
    "无预警日期早于项目开始日期": len(warning_before_start) == 0,
    "无未解决的结题项目预警": len(unresolved_on_closed) == 0,
})

print("=" * 62)
print("科研系统修复后只读复核")
print("=" * 62)
print("审计日期：", today)
print("项目总数：", len(projects))
print("预警总数：", len(warnings))
print("项目状态分布：", dict(Counter(
    p["status"] for p in projects
)))
print("预警解决状态分布：", dict(Counter(
    "已解决" if w["is_resolved"] else "未解决"
    for w in warnings
)))
print("-" * 62)

for name, passed in checks.items():
    print(f"[{'PASS' if passed else 'CHECK'}] {name}")

details = {
    "到期未结题项目": overdue_non_closed,
    "结题但进度不为100%的项目": closed_not_100,
    "进度100但未来结束且状态不为审核中的项目":
        future_completed_not_review,
    "结束日期之后的预警": warning_after_end,
    "开始日期之前的预警": warning_before_start,
    "未解决的结题项目预警": unresolved_on_closed,
}

for name, rows in details.items():
    if rows:
        print(f"\n{name}：")
        for row in rows[:10]:
            print(row)

print("-" * 62)
print("复核结论：", "全部通过" if all(checks.values())
      else "存在待检查项")
print("本次检查未执行任何数据库写入。")
