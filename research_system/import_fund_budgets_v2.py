import argparse
import os
import sys
from decimal import Decimal, InvalidOperation

import django
from django.db import transaction


def setup_django():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "research_system.settings")
    django.setup()


def parse_args():
    parser = argparse.ArgumentParser(
        description="科研经费年度预算 Excel 导入工具 v2（空白预算自动跳过；默认仅检查）"
    )
    parser.add_argument(
        "--file",
        required=True,
        help="预算 Excel 文件路径，例如 .\\科研经费年度预算待填写.xlsx",
    )
    parser.add_argument(
        "--sheet",
        default="年度预算导入",
        help="工作表名称，默认：年度预算导入",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="正式写入数据库；不加此参数时仅执行 dry-run 检查",
    )
    return parser.parse_args()


def normalize_year(value):
    if value is None or value == "":
        raise ValueError("预算年度为空")

    if isinstance(value, float):
        if not value.is_integer():
            raise ValueError(
                f"预算年度不是整数：{value}"
            )
        value = int(value)

    try:
        year = int(str(value).strip())
    except Exception:
        raise ValueError(
            f"预算年度格式无效：{value}"
        )

    if year < 1900 or year > 2200:
        raise ValueError(
            f"预算年度超出合理范围：{year}"
        )

    return year


def normalize_amount(value):
    if value is None or value == "":
        return None

    try:
        amount = Decimal(
            str(value).strip()
        )
    except (InvalidOperation, ValueError):
        raise ValueError(
            f"年度预算金额格式无效：{value}"
        )

    if amount <= 0:
        raise ValueError(
            f"年度预算金额必须大于 0：{amount}"
        )

    return amount.quantize(
        Decimal("0.01")
    )


def main():
    args = parse_args()

    try:
        from openpyxl import load_workbook
    except ImportError:
        print(
            "ERROR: 当前虚拟环境未安装 openpyxl。"
        )
        print(
            "请先运行：pip install openpyxl"
        )
        sys.exit(2)

    excel_path = os.path.abspath(
        args.file
    )

    if not os.path.exists(excel_path):
        print(
            f"ERROR: 找不到文件：{excel_path}"
        )
        sys.exit(2)

    setup_django()

    from api.models import Project, FundBudget

    wb = load_workbook(
        excel_path,
        data_only=True,
    )

    if args.sheet not in wb.sheetnames:
        print(
            f"ERROR: Excel 中不存在工作表：{args.sheet}"
        )
        print(
            f"现有工作表：{wb.sheetnames}"
        )
        sys.exit(2)

    ws = wb[args.sheet]

    # v2 使用列名定位，不依赖固定列序
    required_headers = [
        "项目编号*",
        "预算年度*",
        "年度预算金额（万元）*",
    ]

    header_map = {}

    for col in range(
        1,
        ws.max_column + 1,
    ):
        value = ws.cell(
            row=1,
            column=col,
        ).value

        if value is not None:
            header_map[
                str(value).strip()
            ] = col

    missing_headers = [
        h
        for h in required_headers
        if h not in header_map
    ]

    if missing_headers:
        print(
            "ERROR: Excel 缺少必要字段：",
            missing_headers,
        )
        sys.exit(2)

    project_name_col = header_map.get(
        "项目名称"
    )

    project_start_col = header_map.get(
        "项目起始年"
    )

    project_end_col = header_map.get(
        "项目结束年"
    )

    project_no_col = header_map[
        "项目编号*"
    ]
    year_col = header_map[
        "预算年度*"
    ]
    amount_col = header_map[
        "年度预算金额（万元）*"
    ]

    valid_rows = []
    errors = []
    warnings = []

    skipped_blank_budget = 0
    seen_keys = set()

    # 项目编号缓存，减少重复数据库查询
    project_cache = {}

    for row_no in range(
        2,
        ws.max_row + 1,
    ):
        raw_project_no = ws.cell(
            row=row_no,
            column=project_no_col,
        ).value

        raw_year = ws.cell(
            row=row_no,
            column=year_col,
        ).value

        raw_amount = ws.cell(
            row=row_no,
            column=amount_col,
        ).value

        # v2 核心规则：
        # 年度预算金额为空 -> 自动跳过，不报错
        if raw_amount in (None, ""):
            skipped_blank_budget += 1
            continue

        row_errors = []

        project_no = (
            str(raw_project_no).strip()
            if raw_project_no is not None
            else ""
        )

        if not project_no:
            row_errors.append(
                "项目编号为空"
            )

        try:
            year = normalize_year(
                raw_year
            )
        except ValueError as exc:
            year = None
            row_errors.append(
                str(exc)
            )

        try:
            amount = normalize_amount(
                raw_amount
            )
        except ValueError as exc:
            amount = None
            row_errors.append(
                str(exc)
            )

        project = None

        if project_no:
            if project_no not in project_cache:
                matches = list(
                    Project.objects.filter(
                        project_no=project_no
                    )[:2]
                )

                project_cache[
                    project_no
                ] = matches

            matches = project_cache[
                project_no
            ]

            if len(matches) == 0:
                row_errors.append(
                    f"系统中不存在项目编号：{project_no}"
                )
            elif len(matches) > 1:
                row_errors.append(
                    f"项目编号在系统中不唯一：{project_no}"
                )
            else:
                project = matches[0]

        # 项目名称仅核对，不作为匹配条件
        if (
            project is not None
            and project_name_col is not None
        ):
            raw_name = ws.cell(
                row=row_no,
                column=project_name_col,
            ).value

            if raw_name not in (None, ""):
                excel_name = str(
                    raw_name
                ).strip()

                if (
                    excel_name
                    != project.project_name
                ):
                    warnings.append(
                        f"第 {row_no} 行：项目名称与系统不一致；"
                        f"Excel='{excel_name}'；"
                        f"系统='{project.project_name}'"
                    )

        # 项目周期校验
        if (
            project is not None
            and year is not None
        ):
            if (
                year < project.start_date.year
                or year > project.end_date.year
            ):
                row_errors.append(
                    f"预算年度 {year} 不在项目周期 "
                    f"{project.start_date.year}-{project.end_date.year} 内；"
                    f"项目编号={project_no}"
                )

            key = (
                project.id,
                year,
            )

            if key in seen_keys:
                row_errors.append(
                    "Excel 内重复："
                    f"同一项目 + 同一年度重复出现（{project_no}, {year}）"
                )
            else:
                seen_keys.add(
                    key
                )

        # 自动模板里的起止年份若存在，则做一致性提示
        if (
            project is not None
            and project_start_col is not None
        ):
            raw_start = ws.cell(
                row=row_no,
                column=project_start_col,
            ).value

            if (
                raw_start not in (None, "")
                and int(raw_start)
                != project.start_date.year
            ):
                warnings.append(
                    f"第 {row_no} 行：Excel 项目起始年与数据库不一致。"
                )

        if (
            project is not None
            and project_end_col is not None
        ):
            raw_end = ws.cell(
                row=row_no,
                column=project_end_col,
            ).value

            if (
                raw_end not in (None, "")
                and int(raw_end)
                != project.end_date.year
            ):
                warnings.append(
                    f"第 {row_no} 行：Excel 项目结束年与数据库不一致。"
                )

        if row_errors:
            errors.append(
                f"第 {row_no} 行："
                + "；".join(row_errors)
            )
            continue

        existing = (
            FundBudget.objects.filter(
                project=project,
                year=year,
            ).first()
        )

        valid_rows.append({
            "row_no": row_no,
            "project": project,
            "year": year,
            "amount": amount,
            "action": (
                "UPDATE"
                if existing
                else "CREATE"
            ),
        })

    print("=" * 100)
    print(
        "FUND BUDGET IMPORT PREFLIGHT v2"
    )
    print("=" * 100)
    print(
        f"Excel 文件       : {excel_path}"
    )
    print(
        f"工作表           : {args.sheet}"
    )
    print(
        f"模式             : "
        f"{'EXECUTE' if args.execute else 'DRY-RUN / NO DATABASE WRITE'}"
    )
    print(
        f"空白预算跳过     : {skipped_blank_budget}"
    )
    print(
        f"有效记录         : {len(valid_rows)}"
    )
    print(
        f"错误             : {len(errors)}"
    )
    print(
        f"警告             : {len(warnings)}"
    )
    print()

    if warnings:
        print("[WARNINGS]")

        for item in warnings:
            print(" -", item)

        print()

    if errors:
        print("[ERRORS]")

        for item in errors:
            print(" -", item)

        print()
        print(
            "RESULT: FAILED / NO DATABASE WRITE"
        )
        sys.exit(1)

    create_count = sum(
        1
        for row in valid_rows
        if row["action"] == "CREATE"
    )

    update_count = sum(
        1
        for row in valid_rows
        if row["action"] == "UPDATE"
    )

    print("[PLAN]")
    print(
        f"  CREATE : {create_count}"
    )
    print(
        f"  UPDATE : {update_count}"
    )

    if not valid_rows:
        print()
        print(
            "RESULT: PASS / "
            "当前没有填写任何年度预算，数据库未修改"
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
            "如确认无误，请追加 --execute 正式写入。"
        )
        return

    created = 0
    updated = 0

    with transaction.atomic():
        for row in valid_rows:
            _, was_created = (
                FundBudget.objects.update_or_create(
                    project=row["project"],
                    year=row["year"],
                    defaults={
                        "budget_amount": row["amount"],
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
        "  Total FundBudget rows now : "
        f"{FundBudget.objects.count()}"
    )
    print()
    print("RESULT: COMPLETE")


if __name__ == "__main__":
    main()
