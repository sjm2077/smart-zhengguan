from pathlib import Path

from openpyxl import load_workbook

from public_prediction_samples import (
    PUBLIC_PREDICTION_HEADERS,
    PUBLIC_PREDICTION_SAMPLES,
)


WORKBOOK_NAME = "研究生数据_2021-2026.xlsx"
PREDICTION_SHEET = "智能预测-学生数据"
SOURCE_SHEET = "智能预测-公开来源说明"


def write_prediction_sheet(workbook):
    worksheet = workbook[PREDICTION_SHEET]
    worksheet.delete_rows(1, worksheet.max_row)
    worksheet.append(PUBLIC_PREDICTION_HEADERS)
    for sample in PUBLIC_PREDICTION_SAMPLES:
        worksheet.append([sample.get(header, "") for header in PUBLIC_PREDICTION_HEADERS])


def write_source_sheet(workbook):
    if SOURCE_SHEET in workbook.sheetnames:
        worksheet = workbook[SOURCE_SHEET]
        worksheet.delete_rows(1, worksheet.max_row)
    else:
        worksheet = workbook.create_sheet(SOURCE_SHEET)

    rows = [
        ["字段", "说明"],
        ["数据范围", "山东大学政治学与公共管理学院研究生公开样本"],
        ["真实公开字段", "姓名、培养层次、年级、学院、公开报道中的研究主题/方向、来源标题、来源链接"],
        ["非公开字段处理", "学号使用系统公开样本编号；课程/考勤/心理等预测指标使用基于公开荣誉表现整理的治理演示值"],
        ["主要公开来源 1", "https://pspa.sdu.edu.cn/info/1056/10958.htm"],
        ["主要公开来源 2", "https://pspa.sdu.edu.cn/info/1056/8874.htm"],
        ["主要公开来源 3", "https://pspa.sdu.edu.cn/jytd/qzjs.htm"],
        ["主要公开来源 4", "https://www.yz.sdu.edu.cn/shandongdaxue2026nianshuoshiyanjiushengzhaoshengzhuanyemuludiaozhengtongkaozhaoshengjihua.pdf"],
    ]
    for row in rows:
        worksheet.append(row)


def main():
    root = Path(__file__).resolve().parents[1]
    workbook_path = root / WORKBOOK_NAME
    workbook = load_workbook(workbook_path)
    write_prediction_sheet(workbook)
    write_source_sheet(workbook)
    workbook.save(workbook_path)
    print(f"updated workbook: {workbook_path}")
    print(f"public samples: {len(PUBLIC_PREDICTION_SAMPLES)}")


if __name__ == "__main__":
    main()

