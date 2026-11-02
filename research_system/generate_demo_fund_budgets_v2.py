import argparse
import hashlib
import os
import sys
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP

import django
from django.db import transaction
from django.db.models import Sum


DEMO_SOURCE = "DEMO_BUDGET_V2"

# 课程展示用年度基准执行率，不代表真实财务数据。
BASE_RATES = {
    2021: Decimal("0.80"),
    2022: Decimal("0.83"),
    2023: Decimal("0.86"),
    2024: Decimal("0.88"),
    2025: Decimal("0.84"),
}

MIN_RATE = Decimal("0.72")
MAX_RATE = Decimal("0.95")
PERTURB_MIN = Decimal("-0.04")
PERTURB_MAX = Decimal("0.04")
MONEY_QUANT = Decimal("0.01")
RATE_QUANT = Decimal("0.0001")


def setup_django():
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE",
        "research_system.settings",
    )
    django.setup()


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "生成 DEMO_BUDGET_V2 演示年度预算。"
            "默认 DRY-RUN，仅计算和审计，不写数据库。"
        )
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="正式写入 FundBudget；不加该参数时仅 DRY-RUN。",
    )
    return parser.parse_args()


def money(value):
    return Decimal(value).quantize(
        MONEY_QUANT,
        rounding=ROUND_HALF_UP,
    )


def pct(rate):
    return (
        Decimal(rate) * Decimal("100")
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


def stable_key(project, year):
    """
    使用项目主键 + 项目编号 + 年份构造稳定身份。
    即使 project_no 为空，不同项目也不会得到相同扰动。
    """
    project_no = (project.project_no or "").strip()
    return (
        f"{DEMO_SOURCE}|"
        f"project_id={project.id}|"
        f"project_no={project_no}|"
        f"year={year}"
    )


def deterministic_perturb(project, year):
    raw = stable_key(
        project,
        year,
    ).encode("utf-8")

    digest = hashlib.sha256(
        raw
    ).digest()

    integer = int.from_bytes(
        digest[:8],
        byteorder="big",
        signed=False,
    )

    max_int = (1 << 64) - 1
    unit = Decimal(integer) / Decimal(max_int)

    return (
        PERTURB_MIN
        + unit * (
            PERTURB_MAX
            - PERTURB_MIN
        )
    )


def get_demo_rate(project, year):
    base = BASE_RATES.get(
        int(year),
        Decimal("0.84"),
    )

    rate = (
        base
        + deterministic_perturb(
            project,
            year,
        )
    )

    rate = max(
        MIN_RATE,
        min(
            MAX_RATE,
            rate,
        ),
    )

    return rate.quantize(
        RATE_QUANT,
        rounding=ROUND_HALF_UP,
    )


def main():
    args = parse_args()

    setup_django()

    from api.models import (
        Project,
        FundDetail,
        FundBudget,
    )

    # 模型字段保护
    budget_fields = {
        field.name
        for field in FundBudget._meta.fields
    }

    required_fields = {
        "is_demo",
        "data_source",
    }

    missing_fields = (
        required_fields
        - budget_fields
    )

    if missing_fields:
        print("=" * 118)
        print(
            "DEMO FUND BUDGET GENERATOR — "
            "DEMO_BUDGET_V2"
        )
        print("=" * 118)
        print(
            "ERROR: FundBudget 缺少字段："
            + ", ".join(
                sorted(
                    missing_fields
                )
            )
        )
        print(
            "请先完成 models.py、makemigrations、migrate。"
        )
        sys.exit(2)

    # 与科研经费页面保持完全一致：
    # 按 FundDetail 中实际存在的“项目 + 年份”汇总，
    # 不再用 Project.start_date/end_date 过滤。
    actual_rows = list(
        FundDetail.objects
        .values(
            "project_id",
            "year",
        )
        .annotate(
            actual_total=Sum("amount")
        )
        .order_by(
            "year",
            "project_id",
        )
    )

    positive_rows = [
        row
        for row in actual_rows
        if (
            row["actual_total"] is not None
            and row["actual_total"] > 0
        )
    ]

    project_ids = {
        row["project_id"]
        for row in positive_rows
    }

    projects = Project.objects.in_bulk(
        project_ids
    )

    existing_budgets = {
        (obj.project_id, int(obj.year)): obj
        for obj in FundBudget.objects.filter(
            project_id__in=project_ids
        )
    }

    candidates = []
    skipped_real = []
    warnings = []

    lifecycle_mismatches = []
    blank_project_nos = []

    # 汇总同时包含：
    # 1) 本轮 DEMO 候选预算；
    # 2) 若未来已有真实预算，则保留真实预算。
    year_summary = defaultdict(
        lambda: {
            "actual": Decimal("0"),
            "budget": Decimal("0"),
            "rows": 0,
            "demo_rows": 0,
            "real_rows": 0,
            "min_demo_rate": None,
            "max_demo_rate": None,
        }
    )

    source_actual_by_year = defaultdict(
        lambda: Decimal("0")
    )

    for row in positive_rows:
        project = projects.get(
            row["project_id"]
        )

        if project is None:
            # 正常 FK 约束下不应发生。
            print(
                "ERROR: FundDetail 引用了不存在的 Project："
                f"{row['project_id']}"
            )
            sys.exit(1)

        year = int(
            row["year"]
        )
        actual = money(
            row["actual_total"]
        )

        source_actual_by_year[
            year
        ] += Decimal(
            row["actual_total"]
        )

        summary = year_summary[
            year
        ]
        summary["actual"] += Decimal(
            row["actual_total"]
        )
        summary["rows"] += 1

        project_no = (
            project.project_no
            or ""
        ).strip()

        if not project_no:
            blank_project_nos.append(
                (
                    project.id,
                    year,
                    project.project_name,
                )
            )

        # 项目周期不一致在当前历史/演示数据中只做数据质量警告，
        # 不再阻断预算生成。
        if (
            year < project.start_date.year
            or year > project.end_date.year
        ):
            lifecycle_mismatches.append(
                (
                    project_no
                    or f"[PROJECT_ID={project.id}]",
                    year,
                    (
                        f"{project.start_date.year}-"
                        f"{project.end_date.year}"
                    ),
                )
            )

        existing = existing_budgets.get(
            (
                project.id,
                year,
            )
        )

        # 真实/人工预算永不覆盖，直接纳入最终预算汇总。
        if (
            existing is not None
            and not existing.is_demo
        ):
            skipped_real.append(
                (
                    project_no
                    or f"[PROJECT_ID={project.id}]",
                    year,
                    existing.budget_amount,
                )
            )

            summary[
                "budget"
            ] += Decimal(
                existing.budget_amount
            )
            summary[
                "real_rows"
            ] += 1

            continue

        demo_rate = get_demo_rate(
            project,
            year,
        )

        budget = money(
            Decimal(actual)
            / demo_rate
        )

        realized_rate = (
            Decimal(actual)
            / budget
            if budget > 0
            else Decimal("0")
        )

        action = (
            "UPDATE"
            if existing is not None
            else "CREATE"
        )

        candidates.append({
            "project": project,
            "year": year,
            "actual": actual,
            "budget": budget,
            "target_rate": demo_rate,
            "realized_rate": realized_rate,
            "action": action,
        })

        summary[
            "budget"
        ] += budget
        summary[
            "demo_rows"
        ] += 1

        current_min = summary[
            "min_demo_rate"
        ]
        current_max = summary[
            "max_demo_rate"
        ]

        if (
            current_min is None
            or realized_rate < current_min
        ):
            summary[
                "min_demo_rate"
            ] = realized_rate

        if (
            current_max is None
            or realized_rate > current_max
        ):
            summary[
                "max_demo_rate"
            ] = realized_rate

    print("=" * 124)
    print(
        "DEMO FUND BUDGET GENERATOR — "
        "DEMO_BUDGET_V2"
    )
    print("=" * 124)
    print(
        "性质            : 演示预算数据 / 非真实财务预算"
    )
    print(
        "模式            : "
        + (
            "EXECUTE"
            if args.execute
            else "DRY-RUN / NO DATABASE WRITE"
        )
    )
    print(
        "统计口径        : 与科研经费页面一致，以 FundDetail 项目年度实际数据为准"
    )
    print(
        "项目周期异常    : 仅警告，不作为 DEMO 预算生成阻断条件"
    )
    print(
        "项目扰动        : SHA256(project_id + project_no + year + DEMO_BUDGET_V2)"
    )
    print(
        "执行率边界      : 72% ～ 95%"
    )
    print(
        "已有真实预算    : 永不覆盖"
    )
    print()

    print("[YEAR SUMMARY]")
    print(
        f"{'年度':<8}"
        f"{'项目年':>9}"
        f"{'DEMO':>9}"
        f"{'REAL':>9}"
        f"{'实际经费':>18}"
        f"{'最终预算':>18}"
        f"{'汇总执行率':>16}"
        f"{'DEMO最低':>14}"
        f"{'DEMO最高':>14}"
    )

    for year in sorted(
        year_summary
    ):
        summary = year_summary[
            year
        ]

        aggregate_rate = (
            summary["actual"]
            / summary["budget"]
            if summary["budget"] > 0
            else Decimal("0")
        )

        min_text = (
            f"{pct(summary['min_demo_rate'])}%"
            if summary["min_demo_rate"] is not None
            else "-"
        )
        max_text = (
            f"{pct(summary['max_demo_rate'])}%"
            if summary["max_demo_rate"] is not None
            else "-"
        )

        print(
            f"{year:<8}"
            f"{summary['rows']:>9}"
            f"{summary['demo_rows']:>9}"
            f"{summary['real_rows']:>9}"
            f"{money(summary['actual']):>18}"
            f"{money(summary['budget']):>18}"
            f"{str(pct(aggregate_rate)) + '%':>16}"
            f"{min_text:>14}"
            f"{max_text:>14}"
        )

    # 核心覆盖检查：必须与 FundDetail 页面统计口径完全一致。
    coverage_failures = []

    for year in sorted(
        source_actual_by_year
    ):
        source_total = money(
            source_actual_by_year[
                year
            ]
        )
        summary_total = money(
            year_summary[
                year
            ]["actual"]
        )
        diff = money(
            summary_total
            - source_total
        )

        if diff != Decimal("0.00"):
            coverage_failures.append(
                (
                    year,
                    source_total,
                    summary_total,
                    diff,
                )
            )

    print()
    print("[COVERAGE CHECK]")
    if coverage_failures:
        for item in coverage_failures:
            print(
                f"  FAIL {item[0]} | "
                f"FundDetail={item[1]} | "
                f"Generator={item[2]} | "
                f"Diff={item[3]}"
            )
    else:
        for year in sorted(
            source_actual_by_year
        ):
            print(
                f"  PASS {year} | "
                f"actual={money(source_actual_by_year[year])}"
            )

    create_count = sum(
        1
        for row in candidates
        if row["action"] == "CREATE"
    )
    update_count = sum(
        1
        for row in candidates
        if row["action"] == "UPDATE"
    )

    print()
    print("[PLAN]")
    print(
        f"  CREATE DEMO        : {create_count}"
    )
    print(
        f"  UPDATE DEMO        : {update_count}"
    )
    print(
        f"  SKIP REAL          : {len(skipped_real)}"
    )
    print(
        f"  LIFECYCLE WARNINGS : {len(lifecycle_mismatches)}"
    )
    print(
        f"  BLANK PROJECT NO   : {len(blank_project_nos)}"
    )

    if lifecycle_mismatches:
        print()
        print(
            "[LIFECYCLE WARNINGS — first 20]"
        )
        for item in lifecycle_mismatches[
            :20
        ]:
            print(
                f"  {item[0]} | "
                f"FundDetail year={item[1]} | "
                f"Project cycle={item[2]}"
            )

    if blank_project_nos:
        print()
        print(
            "[BLANK PROJECT NO — first 20]"
        )
        for item in blank_project_nos[
            :20
        ]:
            print(
                f"  project_id={item[0]} | "
                f"year={item[1]} | "
                f"name={item[2]}"
            )

    if skipped_real:
        print()
        print(
            "[SKIPPED REAL BUDGET — first 20]"
        )
        for item in skipped_real[
            :20
        ]:
            print(
                f"  {item[0]} | "
                f"{item[1]} | "
                f"budget={item[2]}"
            )

    print()
    print(
        "[SAMPLE — first 15 DEMO candidates]"
    )
    for row in candidates[
        :15
    ]:
        project_no = (
            row["project"].project_no
            or ""
        ).strip()

        identity = (
            project_no
            if project_no
            else (
                "[PROJECT_ID="
                f"{row['project'].id}]"
            )
        )

        print(
            "  "
            f"{identity} | "
            f"{row['year']} | "
            f"actual={row['actual']} | "
            f"budget={row['budget']} | "
            f"rate={pct(row['realized_rate'])}% | "
            f"{row['action']}"
        )

    if coverage_failures:
        print()
        print(
            "RESULT: FAILED / "
            "FundDetail 覆盖检查不一致 / "
            "未写数据库"
        )
        sys.exit(1)

    if not candidates:
        print()
        print(
            "RESULT: PASS / "
            "没有需要生成或更新的 DEMO 预算"
        )
        return

    if not args.execute:
        print()
        print(
            "RESULT: PASS / "
            "DRY-RUN COMPLETE / "
            "NO DATABASE WRITE"
        )
        print(
            "生命周期异常仅作为历史数据质量警告。"
        )
        print(
            "确认 YEAR SUMMARY 合理后，再追加 --execute。"
        )
        return

    created = 0
    updated = 0

    with transaction.atomic():
        for row in candidates:
            _, was_created = (
                FundBudget.objects.update_or_create(
                    project=row["project"],
                    year=row["year"],
                    defaults={
                        "budget_amount": row["budget"],
                        "is_demo": True,
                        "data_source": DEMO_SOURCE,
                    },
                )
            )

            if was_created:
                created += 1
            else:
                updated += 1

    print()
    print("[EXECUTION]")
    print(
        f"  Created : {created}"
    )
    print(
        f"  Updated : {updated}"
    )
    print(
        "  DEMO rows now : "
        f"{FundBudget.objects.filter(is_demo=True).count()}"
    )
    print(
        "  REAL rows now : "
        f"{FundBudget.objects.filter(is_demo=False).count()}"
    )
    print()
    print(
        "RESULT: COMPLETE / "
        "DEMO_BUDGET_V2 WRITTEN"
    )


if __name__ == "__main__":
    main()
