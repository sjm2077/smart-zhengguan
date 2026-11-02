"""
科研系统项目编号缺失来源核查（只读版）
不修改数据库，不生成或写入项目编号。

在 D:\\research_system（与 manage.py 同级）执行：
python manage.py shell -c "exec(open('audit_project_no_origin_v1.py', encoding='utf-8').read())"

输出：
project_no_origin_diagnostic.json
"""
import json
from collections import Counter, defaultdict
from pathlib import Path

from api.models import Project


def clean(value):
    return str(value or "").strip()


def as_text(value):
    if value is None:
        return None
    return str(value)


def related_label(obj, preferred_names):
    if obj is None:
        return ""
    for name in preferred_names:
        value = getattr(obj, name, None)
        if value not in (None, ""):
            return str(value)
    return str(obj)


def field_metadata():
    result = []
    for field in Project._meta.fields:
        result.append({
            "name": field.name,
            "attname": getattr(field, "attname", field.name),
            "type": field.get_internal_type(),
            "null": getattr(field, "null", None),
            "blank": getattr(field, "blank", None),
            "max_length": getattr(field, "max_length", None),
            "is_relation": bool(getattr(field, "is_relation", False)),
        })
    return result


def main():
    model_fields = {field.name for field in Project._meta.fields}
    relation_names = [
        name for name in ("leader", "dept")
        if name in model_fields
        and getattr(Project._meta.get_field(name), "is_relation", False)
    ]

    queryset = Project.objects.all().order_by(Project._meta.pk.name)
    if relation_names:
        queryset = queryset.select_related(*relation_names)
    projects = list(queryset)

    pk_name = Project._meta.pk.name
    pk_values = [getattr(p, pk_name) for p in projects]
    numeric_pks = [int(value) for value in pk_values if str(value).isdigit()]

    def row_dict(p):
        leader_obj = getattr(p, "leader", None)
        dept_obj = getattr(p, "dept", None)
        row = {
            "id": getattr(p, pk_name),
            "project_no": getattr(p, "project_no", None),
            "project_name": getattr(p, "project_name", None),
            "leader": related_label(leader_obj, ("real_name", "name", "username")),
            "department": related_label(dept_obj, ("dept_name", "name")),
            "project_type": getattr(p, "project_type", None),
            "status": getattr(p, "status", None),
            "start_date": as_text(getattr(p, "start_date", None)),
            "end_date": as_text(getattr(p, "end_date", None)),
        }

        # Only include timestamp/source-like fields when they actually exist.
        for field_name in (
            "created_at", "updated_at", "create_time", "update_time",
            "created", "modified", "source", "data_source", "is_demo",
        ):
            if field_name in model_fields:
                value = getattr(p, field_name, None)
                row[field_name] = as_text(value)
        return row

    rows = [row_dict(p) for p in projects]
    blank_rows = [r for r in rows if not clean(r.get("project_no"))]
    numbered_rows = [r for r in rows if clean(r.get("project_no"))]
    blank_ids = sorted(int(r["id"]) for r in blank_rows if str(r["id"]).isdigit())

    ranges = [
        ("pk_1_227", 1, 227),
        ("pk_228_526", 228, 526),
        ("pk_220_240_boundary", 220, 240),
        ("pk_515_526_tail", 515, 526),
    ]

    range_summaries = {}
    for label, low, high in ranges:
        subset = [r for r in rows if str(r["id"]).isdigit() and low <= int(r["id"]) <= high]
        range_summaries[label] = {
            "pk_min": min((int(r["id"]) for r in subset), default=None),
            "pk_max": max((int(r["id"]) for r in subset), default=None),
            "record_count": len(subset),
            "blank_project_no_count": sum(not clean(r.get("project_no")) for r in subset),
            "nonblank_project_no_count": sum(bool(clean(r.get("project_no"))) for r in subset),
            "project_type_counts": dict(Counter(str(r.get("project_type") or "") for r in subset)),
            "status_counts": dict(Counter(str(r.get("status") or "") for r in subset)),
            "department_counts": dict(Counter(str(r.get("department") or "") for r in subset)),
            "project_name_nonempty_count": sum(bool(clean(r.get("project_name"))) for r in subset),
            "leader_nonempty_count": sum(bool(clean(r.get("leader"))) for r in subset),
            "start_date_nonempty_count": sum(bool(clean(r.get("start_date"))) for r in subset),
            "end_date_nonempty_count": sum(bool(clean(r.get("end_date"))) for r in subset),
        }

    # Check whether blank project numbers form one contiguous PK block.
    blank_pk_contiguous = (
        bool(blank_ids)
        and blank_ids == list(range(blank_ids[0], blank_ids[-1] + 1))
    )
    first_blank_pk = min(blank_ids) if blank_ids else None
    all_numbered_before_blank_block = (
        bool(numbered_rows)
        and bool(blank_rows)
        and max(int(r["id"]) for r in numbered_rows if str(r["id"]).isdigit()) < first_blank_pk
    )

    title_suffixes = (
        "的对策研究", "的实践研究", "的评估研究", "的模式研究",
        "的机制研究", "的路径研究", "的演进研究", "的创新研究",
    )
    blank_name_counts = Counter(
        str(r.get("project_name") or "").strip()
        for r in blank_rows
        if str(r.get("project_name") or "").strip()
    )
    blank_title_suffix_counts = Counter()
    for r in blank_rows:
        title = str(r.get("project_name") or "").strip()
        for suffix in title_suffixes:
            if title.endswith(suffix):
                blank_title_suffix_counts[suffix] += 1
                break

    # Show a small boundary sample plus examples from numbered records.
    boundary_rows = [
        r for r in rows
        if str(r["id"]).isdigit()
        and (215 <= int(r["id"]) <= 240 or 515 <= int(r["id"]) <= 526)
    ]
    existing_number_samples = numbered_rows[:12]
    blank_samples = blank_rows[:12]

    timestamp_source_fields = [
        field["name"] for field in field_metadata()
        if any(token in field["name"].lower() for token in (
            "created", "updated", "create", "update", "source", "demo", "import"
        ))
    ]

    report = {
        "audit_type": "project_no_origin_diagnostic",
        "read_only": True,
        "database_write_performed": False,
        "model": f"{Project._meta.app_label}.{Project.__name__}",
        "database_table": Project._meta.db_table,
        "primary_key_field": pk_name,
        "project_total": len(rows),
        "project_pk_min": min(numeric_pks, default=None),
        "project_pk_max": max(numeric_pks, default=None),
        "project_no_blank_count": len(blank_rows),
        "project_no_nonblank_count": len(numbered_rows),
        "blank_project_no_pk_min": min(blank_ids, default=None),
        "blank_project_no_pk_max": max(blank_ids, default=None),
        "blank_project_no_pk_contiguous": blank_pk_contiguous,
        "all_numbered_records_have_pk_before_blank_block": all_numbered_before_blank_block,
        "project_no_existing_value_samples": [
            {
                "id": r["id"],
                "project_no": r.get("project_no"),
                "project_name": r.get("project_name"),
                "leader": r.get("leader"),
                "department": r.get("department"),
            }
            for r in existing_number_samples
        ],
        "blank_project_no_samples": blank_samples,
        "boundary_and_tail_samples": boundary_rows,
        "pk_range_summaries": range_summaries,
        "blank_project_title_suffix_counts": dict(blank_title_suffix_counts),
        "blank_project_duplicate_name_groups_count": sum(
            1 for count in blank_name_counts.values() if count > 1
        ),
        "blank_project_duplicate_name_records_count": sum(
            count for count in blank_name_counts.values() if count > 1
        ),
        "possible_timestamp_or_source_fields": timestamp_source_fields,
        "model_fields": field_metadata(),
        "interpretation_note": (
            "本报告只提供分布和字段证据。连续主键段集中缺失编号可能提示同批导入/生成，"
            "但不能单独证明记录是演示数据，也不能据此决定正式编号。"
        ),
    }

    output = Path("project_no_origin_diagnostic.json")
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )

    print("=" * 76)
    print("科研系统项目编号缺失来源核查（只读）")
    print("=" * 76)
    print("模型：", report["model"])
    print("数据表：", report["database_table"])
    print("项目总数：", report["project_total"])
    print("项目编号缺失：", report["project_no_blank_count"])
    print("项目编号已有：", report["project_no_nonblank_count"])
    print(
        "缺失编号主键范围：",
        report["blank_project_no_pk_min"],
        "—",
        report["blank_project_no_pk_max"],
    )
    print("缺失编号主键是否连续：", report["blank_project_no_pk_contiguous"])
    print(
        "所有已有编号记录是否都位于缺失区间之前：",
        report["all_numbered_records_have_pk_before_blank_block"],
    )
    print("\n分段统计：")
    for label, summary in range_summaries.items():
        print(
            f"  {label}: records={summary['record_count']}, "
            f"blank={summary['blank_project_no_count']}, "
            f"nonblank={summary['nonblank_project_no_count']}"
        )
    print("\n可能存在的创建时间/来源字段：", timestamp_source_fields or "未发现")
    print("本次数据库写入：否")
    print("完整报告：", output.resolve())
    print("\n请把终端输出和 project_no_origin_diagnostic.json 发回核对。")


main()
