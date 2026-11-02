import argparse
import os
import sys
from collections import defaultdict
from decimal import Decimal

import django


def setup_django():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "research_system.settings")
    django.setup()


def parse_args():
    parser = argparse.ArgumentParser(
        description="根据当前数据库自动生成科研经费年度预算待填写 Excel"
    )
    parser.add_argument(
        "--output",
        default="科研经费年度预算待填写.xlsx",
        help="输出 Excel 文件名，默认：科研经费年度预算待填写.xlsx",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    try:
        from openpyxl import Workbook
        from openpyxl.styles import Alignment, Font, PatternFill
        from openpyxl.worksheet.datavalidation import DataValidation
    except ImportError:
        print("ERROR: 当前虚拟环境未安装 openpyxl。")
        print("请先运行：pip install openpyxl")
        sys.exit(2)

    setup_django()

    from django.db.models import Sum
    from api.models import Project, FundDetail, FundBudget

    # 系统实际存在的经费年份，例如 [2021, 2022, 2023, 2024, 2025]
    system_years = sorted(
        {
            int(y)
            for y in FundDetail.objects.values_list(
                "year",
                flat=True,
            ).distinct()
            if y is not None
        }
    )

    if not system_years:
        print("ERROR: FundDetail 中没有可用年份，无法生成模板。")
        sys.exit(1)

    projects = list(
        Project.objects.select_related(
            "dept",
            "leader",
        ).order_by(
            "project_no",
            "id",
        )
    )

    # 项目-年度实际经费，仅作为填写预算时的参考
    actual_map = defaultdict(Decimal)

    actual_rows = (
        FundDetail.objects.values(
            "project_id",
            "year",
        )
        .annotate(total=Sum("amount"))
    )

    for row in actual_rows:
        actual_map[
            (row["project_id"], int(row["year"]))
        ] = row["total"] or Decimal("0")

    # 如果已有预算，也一并回填，便于后续再次生成模板时继续维护
    budget_map = {
        (b.project_id, int(b.year)): b.budget_amount
        for b in FundBudget.objects.all()
    }

    wb = Workbook()

    ws = wb.active
    ws.title = "年度预算导入"

    headers = [
        "项目编号*",
        "项目名称",
        "学科/方向",
        "项目起始年",
        "项目结束年",
        "预算年度*",
        "项目总经费（万元）",
        "年度实际经费（万元，仅参考）",
        "年度预算金额（万元）*",
        "备注",
    ]

    ws.append(headers)

    row_count = 0

    for project in projects:
        project_start = project.start_date.year
        project_end = project.end_date.year

        # 只生成“项目周期 ∩ 系统真实经费年份”
        valid_years = [
            year
            for year in system_years
            if project_start <= year <= project_end
        ]

        for year in valid_years:
            existing_budget = budget_map.get(
                (project.id, year)
            )

            ws.append([
                project.project_no,
                project.project_name,
                project.subject or "",
                project_start,
                project_end,
                year,
                float(project.fund_amount or 0),
                float(
                    actual_map.get(
                        (project.id, year),
                        Decimal("0"),
                    )
                ),
                (
                    float(existing_budget)
                    if existing_budget is not None
                    else ""
                ),
                "",
            ])

            row_count += 1

    # 表头样式
    header_fill = PatternFill(
        "solid",
        fgColor="17365D",
    )
    header_font = Font(
        color="FFFFFF",
        bold=True,
    )

    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(
            horizontal="center",
            vertical="center",
        )

    # 列宽
    widths = {
        "A": 18,
        "B": 34,
        "C": 18,
        "D": 12,
        "E": 12,
        "F": 12,
        "G": 20,
        "H": 24,
        "I": 22,
        "J": 28,
    }

    for col, width in widths.items():
        ws.column_dimensions[col].width = width

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:J{max(ws.max_row, 1)}"

    # 内容样式
    for row in ws.iter_rows(
        min_row=2,
        max_row=ws.max_row,
    ):
        for cell in row:
            cell.alignment = Alignment(
                vertical="center",
                wrap_text=True,
            )

    # 金额格式
    for row in range(2, ws.max_row + 1):
        ws[f"G{row}"].number_format = "0.00"
        ws[f"H{row}"].number_format = "0.00"
        ws[f"I{row}"].number_format = "0.00"

    # 年度预算金额必须 > 0；空白允许存在，因为这是“待填写模板”
    if ws.max_row >= 2:
        dv_amount = DataValidation(
            type="decimal",
            operator="greaterThan",
            formula1="0",
            allow_blank=True,
        )
        dv_amount.error = "年度预算金额必须为大于 0 的数字。"
        dv_amount.errorTitle = "预算金额无效"
        ws.add_data_validation(dv_amount)
        dv_amount.add(f"I2:I{ws.max_row}")

    # 说明页
    info = wb.create_sheet("填写说明")
    info["A1"] = "科研经费年度预算待填写表说明"
    info["A1"].font = Font(
        bold=True,
        size=14,
        color="FFFFFF",
    )
    info["A1"].fill = header_fill
    info.merge_cells("A1:B1")

    instructions = [
        ("项目编号*", "系统自动生成，不要修改。导入时使用它匹配 Project.project_no。"),
        ("项目名称", "系统自动生成，仅用于核对。"),
        ("学科/方向", "系统自动生成，仅用于核对和筛选。"),
        ("项目起始年/结束年", "系统自动生成，用于确认预算年度处于项目周期内。"),
        ("预算年度*", "系统自动生成，为“项目周期 ∩ FundDetail 实际年份”的交集。"),
        ("项目总经费", "来自 Project.fund_amount，仅供参考，不作为年度预算自动推导依据。"),
        ("年度实际经费", "来自 FundDetail 当年汇总，仅供参考，不代表年度预算。"),
        ("年度预算金额*", "唯一需要重点填写的字段；留空行在导入时会自动跳过。"),
        ("备注", "可填写预算批复、调整原因、数据来源等。"),
        ("已有预算", "若 FundBudget 中已有该项目该年度预算，重新导出时会自动回填。"),
        ("导入原则", "先 dry-run，确认无错误后再使用 --execute 正式写入。"),
    ]

    info.append(["字段", "说明"])

    for field, desc in instructions:
        info.append([field, desc])

    info["A2"].font = Font(bold=True)
    info["B2"].font = Font(bold=True)
    info["A2"].fill = PatternFill(
        "solid",
        fgColor="D9EAF7",
    )
    info["B2"].fill = PatternFill(
        "solid",
        fgColor="D9EAF7",
    )

    info.column_dimensions["A"].width = 24
    info.column_dimensions["B"].width = 82

    for row in info.iter_rows():
        for cell in row:
            cell.alignment = Alignment(
                vertical="center",
                wrap_text=True,
            )

    output_path = os.path.abspath(args.output)
    wb.save(output_path)

    print("=" * 100)
    print("FUND BUDGET TEMPLATE EXPORT")
    print("=" * 100)
    print(f"系统年份           : {system_years}")
    print(f"项目总数           : {len(projects)}")
    print(f"生成待填写预算行数 : {row_count}")
    print(f"输出文件           : {output_path}")
    print()
    print("RESULT: COMPLETE")


if __name__ == "__main__":
    main()
