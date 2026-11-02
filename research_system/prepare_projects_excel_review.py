# -*- coding: utf-8 -*-
"""
将 projects.xlsx 中已确认需要人工复核的冲突项目单独存档。

本脚本：
1. 不连接 Django，不访问数据库；
2. 不修改原始 projects.xlsx；
3. 生成 projects_import_ready.xlsx（排除指定的冲突行）；
4. 生成 projects_manual_review.xlsx（仅包含冲突行及已知数据库记录对照信息）。

运行位置建议：D:\\research_system
运行命令：python prepare_projects_excel_review.py
可选：python prepare_projects_excel_review.py --source .\\projects.xlsx
"""

from __future__ import annotations

import argparse
import shutil
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter


TARGET = {
    "project_name": "社会保障的创新研究",
    "leader_name": "胡志伟",
    "dept_name": "科学社会主义系",
    "fund_amount": Decimal("472.01"),
    "start_date": "2023-07-21",
    "end_date": "2025-08-13",
    "project_type": "国家级",
    "status": "在研",
    "subject": "社会保障",
    "actual_progress": 13,
}

DATABASE_RECORD = {
    "数据库项目ID": 348,
    "数据库项目编号": "TMP-2023-000348",
    "数据库经费": "256.17",
    "数据库开始日期": "2023-09-09",
    "数据库结束日期": "2025-03-05",
    "数据库状态": "立项",
    "数据库主题": "国际关系",
    "数据库进度": 85,
    "核查说明": (
        "同名同负责人，但项目属性与数据库记录不同；按保守原则暂不导入，"
        "保留数据库现有记录，等待人工确认 Excel 行是否为独立项目。"
    ),
}

REQUIRED_COLUMNS = {
    "project_name",
    "leader_name",
    "dept_name",
    "fund_amount",
    "start_date",
    "end_date",
    "project_type",
    "status",
    "subject",
    "actual_progress",
}


def text_value(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def date_value(value) -> str:
    if value is None or text_value(value) == "":
        return ""
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    # 兼容 Excel 中以字符串保存的日期，如 2023-07-21 00:00:00
    raw = text_value(value)
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        return raw[:10]


def decimal_value(value):
    if value is None or text_value(value) == "":
        return None
    try:
        return Decimal(str(value).replace(",", "")).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        return None


def int_value(value):
    if value is None or text_value(value) == "":
        return None
    try:
        return int(Decimal(str(value)))
    except (InvalidOperation, ValueError):
        return None


def row_matches(row_values, col_index) -> bool:
    def get(field):
        return row_values[col_index[field] - 1]

    return (
        text_value(get("project_name")) == TARGET["project_name"]
        and text_value(get("leader_name")) == TARGET["leader_name"]
        and text_value(get("dept_name")) == TARGET["dept_name"]
        and decimal_value(get("fund_amount")) == TARGET["fund_amount"]
        and date_value(get("start_date")) == TARGET["start_date"]
        and date_value(get("end_date")) == TARGET["end_date"]
        and text_value(get("project_type")) == TARGET["project_type"]
        and text_value(get("status")) == TARGET["status"]
        and text_value(get("subject")) == TARGET["subject"]
        and int_value(get("actual_progress")) == TARGET["actual_progress"]
    )


def count_project_rows(ws, col_index) -> int:
    project_col = col_index["project_name"]
    count = 0
    for row_num in range(2, ws.max_row + 1):
        if text_value(ws.cell(row_num, project_col).value):
            count += 1
    return count


def main():
    parser = argparse.ArgumentParser(
        description="将指定的冲突项目从导入副本中移出，并生成待人工复核文件。"
    )
    parser.add_argument(
        "--source",
        default="projects.xlsx",
        help="原始 Excel 路径，默认是当前目录下的 projects.xlsx",
    )
    args = parser.parse_args()

    source_path = Path(args.source).expanduser().resolve()
    if not source_path.is_file():
        raise SystemExit(f"错误：找不到源文件：{source_path}")

    if source_path.name.lower() in {
        "projects_import_ready.xlsx",
        "projects_manual_review.xlsx",
    }:
        raise SystemExit("错误：源文件不能是本脚本生成的输出文件。请指定原始 projects.xlsx。")

    ready_path = source_path.with_name("projects_import_ready.xlsx")
    review_path = source_path.with_name("projects_manual_review.xlsx")

    # 只读取第一个工作表，与 pandas.read_excel() 默认读取首个工作表的行为一致。
    wb = load_workbook(source_path, data_only=False)
    ws = wb.worksheets[0]

    headers = [text_value(ws.cell(1, col).value) for col in range(1, ws.max_column + 1)]
    col_index = {
        header: idx
        for idx, header in enumerate(headers, start=1)
        if header
    }

    missing = REQUIRED_COLUMNS - set(col_index)
    if missing:
        raise SystemExit(
            "错误：源 Excel 缺少必要列，未生成任何输出文件："
            + "、".join(sorted(missing))
        )

    source_rows = count_project_rows(ws, col_index)
    matched_rows = []
    for row_num in range(2, ws.max_row + 1):
        values = [ws.cell(row_num, col).value for col in range(1, ws.max_column + 1)]
        if text_value(values[col_index["project_name"] - 1]) and row_matches(values, col_index):
            matched_rows.append(row_num)

    # 必须精确命中一行，否则停止，避免误移除其他项目。
    if len(matched_rows) != 1:
        raise SystemExit(
            f"安全检查未通过：目标冲突行应精确匹配 1 条，实际匹配 {len(matched_rows)} 条。"
            "\n未生成输出文件；请核对项目名称、负责人及属性后再运行。"
        )

    target_row_num = matched_rows[0]
    target_values = [
        ws.cell(target_row_num, col).value
        for col in range(1, ws.max_column + 1)
    ]

    # 输出一：复制原工作簿，再从副本中删除唯一匹配的冲突行。
    # 原始文件始终不被修改。
    shutil.copy2(source_path, ready_path)
    ready_wb = load_workbook(ready_path)
    ready_ws = ready_wb.worksheets[0]
    ready_ws.delete_rows(target_row_num, 1)
    ready_wb.save(ready_path)
    ready_wb.close()

    # 输出二：单独创建人工复核工作簿，包含原 Excel 冲突行和已知数据库记录信息。
    review_wb = Workbook()
    review_ws = review_wb.active
    review_ws.title = "待人工复核"

    review_headers = headers + list(DATABASE_RECORD.keys())
    review_ws.append(review_headers)
    review_ws.append(target_values + list(DATABASE_RECORD.values()))

    review_ws.freeze_panes = "A2"
    review_ws.auto_filter.ref = review_ws.dimensions

    header_fill = PatternFill(fill_type="solid", fgColor="D9EAF7")
    for cell in review_ws[1]:
        cell.font = Font(bold=True)
        cell.fill = header_fill
        cell.alignment = Alignment(vertical="center", wrap_text=True)

    for column_cells in review_ws.columns:
        col_letter = get_column_letter(column_cells[0].column)
        max_len = max(
            len(str(cell.value)) if cell.value is not None else 0
            for cell in column_cells
        )
        review_ws.column_dimensions[col_letter].width = min(max(max_len + 2, 12), 42)

    review_ws.row_dimensions[1].height = 32
    review_wb.save(review_path)
    review_wb.close()

    # 重新打开输出文件核验行数和目标行是否已被排除。
    verify_ready_wb = load_workbook(ready_path, read_only=True, data_only=True)
    verify_ready_ws = verify_ready_wb.worksheets[0]
    verify_headers = [text_value(verify_ready_ws.cell(1, col).value)
                      for col in range(1, verify_ready_ws.max_column + 1)]
    verify_col_index = {
        header: idx
        for idx, header in enumerate(verify_headers, start=1)
        if header
    }
    ready_rows = count_project_rows(verify_ready_ws, verify_col_index)
    remaining_target_count = 0
    for row_num in range(2, verify_ready_ws.max_row + 1):
        values = [
            verify_ready_ws.cell(row_num, col).value
            for col in range(1, verify_ready_ws.max_column + 1)
        ]
        if text_value(values[verify_col_index["project_name"] - 1]) and row_matches(
            values, verify_col_index
        ):
            remaining_target_count += 1
    verify_ready_wb.close()

    verify_review_wb = load_workbook(review_path, read_only=True, data_only=True)
    verify_review_ws = verify_review_wb["待人工复核"]
    review_data_rows = sum(
        1 for row_num in range(2, verify_review_ws.max_row + 1)
        if any(verify_review_ws.cell(row_num, col).value is not None
               for col in range(1, verify_review_ws.max_column + 1))
    )
    verify_review_wb.close()

    print("=" * 72)
    print("项目 Excel 冲突行分离完成（仅处理文件，未连接或修改数据库）")
    print("=" * 72)
    print(f"原始文件：{source_path}")
    print(f"原始项目行数：{source_rows}")
    print(f"精确识别的冲突行：第 {target_row_num} 行")
    print(f"导入准备文件：{ready_path}")
    print(f"导入准备文件项目行数：{ready_rows}")
    print(f"导入准备文件残留目标冲突行：{remaining_target_count}")
    print(f"人工复核文件：{review_path}")
    print(f"人工复核文件数据行数：{review_data_rows}")
    print("原始 projects.xlsx：未修改")
    print("数据库：未连接、未修改")

    if (
        ready_rows != source_rows - 1
        or remaining_target_count != 0
        or review_data_rows != 1
    ):
        raise SystemExit(
            "警告：输出文件核验未通过。请不要使用导入准备文件，先检查上述统计结果。"
        )

    print("结果核验：通过。请保留原始文件及人工复核文件。")


if __name__ == "__main__":
    main()
