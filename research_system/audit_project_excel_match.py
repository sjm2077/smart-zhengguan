from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd
from api.models import Project


def norm(value):
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass

    return " ".join(str(value).strip().split()).casefold()


def leader_values(user):
    """读取负责人对象中可能用于姓名匹配的字段，只读。"""
    values = set()

    if user is None:
        return values

    meta = getattr(user, "_meta", None)

    if meta:
        for field in meta.concrete_fields:
            field_name = field.name.lower()

            if any(
                key in field_name
                for key in ("name", "username", "real", "teacher")
            ):
                value = norm(getattr(user, field.name, ""))
                if value:
                    values.add(value)

    for attr in (
        "name",
        "username",
        "real_name",
        "full_name",
        "first_name",
        "display_name",
        "teacher_name",
        "user_name",
    ):
        value = norm(getattr(user, attr, ""))
        if value:
            values.add(value)

    get_full_name = getattr(user, "get_full_name", None)
    if callable(get_full_name):
        value = norm(get_full_name())
        if value:
            values.add(value)

    value = norm(str(user))
    if value:
        values.add(value)

    return values


path = Path("projects.xlsx")

if not path.exists():
    raise FileNotFoundError(f"找不到文件：{path.resolve()}")

df = pd.read_excel(path)

required = {"project_name", "leader_name"}
missing = required - set(df.columns)

if missing:
    raise ValueError(f"Excel 缺少必要字段：{sorted(missing)}")

projects = list(
    Project.objects.select_related("leader").order_by("id")
)

by_name = defaultdict(list)

for project in projects:
    name = norm(project.project_name)
    if name:
        by_name[name].append(project)

blank_projects = [
    p for p in projects if not norm(p.project_no)
]

source_pairs = Counter()
source_names = Counter()

for _, row in df.iterrows():
    name = norm(row["project_name"])
    leader = norm(row["leader_name"])

    if name:
        source_names[name] += 1

    if name and leader:
        source_pairs[(name, leader)] += 1

exact_rows = 0
exact_db_ids = set()
exact_blank_ids = set()
name_only_rows = 0
name_only_db_ids = set()
unmatched_rows = 0
missing_source_fields = 0
unmatched_samples = []

for excel_index, row in df.iterrows():
    name = norm(row["project_name"])
    leader = norm(row["leader_name"])

    if not name or not leader:
        missing_source_fields += 1
        continue

    candidates = by_name.get(name, [])

    matches = [
        p for p in candidates
        if leader in leader_values(p.leader)
    ]

    if matches:
        exact_rows += 1

        for p in matches:
            exact_db_ids.add(p.pk)

            if not norm(p.project_no):
                exact_blank_ids.add(p.pk)

    elif candidates:
        name_only_rows += 1

        for p in candidates:
            name_only_db_ids.add(p.pk)

        if len(unmatched_samples) < 10:
            unmatched_samples.append(
                (
                    excel_index + 2,
                    row["project_name"],
                    row["leader_name"],
                    [p.pk for p in candidates],
                )
            )

    else:
        unmatched_rows += 1

        if len(unmatched_samples) < 10:
            unmatched_samples.append(
                (
                    excel_index + 2,
                    row["project_name"],
                    row["leader_name"],
                    [],
                )
            )

duplicate_pair_groups = sum(
    count > 1 for count in source_pairs.values()
)

duplicate_name_groups = sum(
    count > 1 for count in source_names.values()
)

existing_numbers = [
    norm(p.project_no)
    for p in projects
    if norm(p.project_no)
]

duplicate_numbers = [
    number
    for number, count in Counter(existing_numbers).items()
    if count > 1
]

print("=" * 68)
print("项目 Excel 与数据库对应关系核查（只读）")
print("=" * 68)

print(f"Excel 数据行数：{len(df)}")
print(f"数据库项目总数：{len(projects)}")
print(f"数据库缺失编号：{len(blank_projects)}")
print(f"数据库已有编号：{len(projects) - len(blank_projects)}")

print("\n[名称 + 负责人精确匹配]")
print(f"Excel 成功匹配的行数：{exact_rows}")
print(f"对应的数据库项目数：{len(exact_db_ids)}")
print(f"其中缺失编号的项目数：{len(exact_blank_ids)}")

print("\n[其他匹配情况]")
print(f"仅名称匹配、负责人未精确匹配：{name_only_rows} 行")
print(f"项目名称未匹配：{unmatched_rows} 行")
print(f"Excel 缺少名称或负责人：{missing_source_fields} 行")
print(f"Excel 重复名称组数：{duplicate_name_groups}")
print(f"Excel 重复名称+负责人组数：{duplicate_pair_groups}")
print(f"数据库重复项目编号组数：{len(duplicate_numbers)}")

print("\n[已有编号样本]")
for p in projects:
    if norm(p.project_no):
        print(
            f"id={p.pk}, "
            f"project_no={p.project_no}, "
            f"name={p.project_name}"
        )
        if sum(1 for x in projects[:p.pk] if norm(x.project_no)) >= 9:
            break

print("\n[未精确匹配样本，最多 10 条]")
for excel_row, name, leader, candidate_ids in unmatched_samples:
    print(
        f"Excel行={excel_row}, "
        f"项目={name}, "
        f"负责人={leader}, "
        f"同名数据库ID={candidate_ids}"
    )

print("\n核查完成：没有创建、更新或删除任何数据库记录。")
