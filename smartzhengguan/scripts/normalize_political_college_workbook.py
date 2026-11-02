from pathlib import Path

from openpyxl import load_workbook


TARGET_COLLEGE = "政治学与公共管理学院"
WORKBOOK_SUFFIX = "2021-2026.xlsx"


def ensure_college_column(worksheet, insert_after_header):
    headers = [cell.value for cell in worksheet[1]]
    if "学院" in headers:
        college_index = headers.index("学院") + 1
    else:
        anchor_index = headers.index(insert_after_header) + 1
        worksheet.insert_cols(anchor_index + 1)
        college_index = anchor_index + 1
        worksheet.cell(row=1, column=college_index, value="学院")

    for row_index in range(2, worksheet.max_row + 1):
        worksheet.cell(row=row_index, column=college_index, value=TARGET_COLLEGE)

    return college_index


def main():
    root = Path(__file__).resolve().parents[1]
    workbook_path = next((path for path in root.glob("*.xlsx") if path.name.endswith(WORKBOOK_SUFFIX)), None)
    if workbook_path is None:
        raise SystemExit(f"Workbook not found under {root}")

    workbook = load_workbook(workbook_path)

    grade_major_sheet = workbook["首页总览-年级专业"]
    prediction_sheet = workbook["智能预测-学生数据"]

    ensure_college_column(grade_major_sheet, "专业")
    ensure_college_column(prediction_sheet, "专业")

    workbook.save(workbook_path)
    print(f"Workbook normalized: {workbook_path}")


if __name__ == "__main__":
    main()
