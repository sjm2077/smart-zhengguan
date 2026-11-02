from __future__ import annotations

import json
import subprocess
import zipfile
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parents[1]
MOCK_FILE = ROOT / "src" / "mock" / "graduateManagementMock.js"
OUTPUT_DIR = ROOT / "汇报材料"
DETAIL_FILE = OUTPUT_DIR / "研究生管理系统_模拟数据.xlsx"
MERGED_FILE = OUTPUT_DIR / "研究生管理系统_模拟数据_合并版.xlsx"


def load_mock_data() -> dict:
    node_script = f"""
const fs = require('fs');
const vm = require('vm');
const path = {json.dumps(str(MOCK_FILE))};
let code = fs.readFileSync(path, 'utf8');
code = code.replace(/export const\\s+(\\w+)\\s*=/g, 'const $1 =');
code = code.replace(/export default\\s+graduateManagementMock\\s*;?/g, '');
code += '\\nmodule.exports = {{ sharedOptions, homeMockData, admissionMockData, academicStatusMockData, trainingMockData, degreeMockData, scholarshipMockData, employmentMockData, messageMockData, smartPredictionMockData, graduateManagementMock }};';
const sandbox = {{ module: {{ exports: {{}} }}, exports: {{}} }};
vm.createContext(sandbox);
vm.runInContext(code, sandbox, {{ filename: path }});
process.stdout.write(JSON.stringify(sandbox.module.exports));
"""
    result = subprocess.run(
        ["node", "-e", node_script],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
        encoding="utf-8",
    )
    return json.loads(result.stdout)


def stringify(value):
    if value is None:
        return ""
    if isinstance(value, float):
        return round(value, 2)
    if isinstance(value, (int, str)):
        return value
    if isinstance(value, bool):
        return "是" if value else "否"
    return json.dumps(value, ensure_ascii=False)


def rows_from_mapping(mapping: dict, key_label="字段", value_label="值"):
    rows = [[key_label, value_label]]
    for key, value in mapping.items():
        rows.append([key, stringify(value)])
    return rows


def rows_from_records(records: list[dict]):
    if not records:
        return [["无数据"]]

    columns = []
    seen = set()
    for record in records:
        for key in record.keys():
            if key not in seen:
                seen.add(key)
                columns.append(key)

    rows = [columns]
    for record in records:
        rows.append([stringify(record.get(column, "")) for column in columns])
    return rows


def append_section(target_rows: list[list], title: str, rows: list[list]):
    if target_rows:
        target_rows.append([])
    target_rows.append([title])
    target_rows.extend(rows)


def xml_cell(value, row_idx: int, col_idx: int, style_id: int = 0):
    cell_ref = f"{column_letter(col_idx)}{row_idx}"
    style = f' s="{style_id}"' if style_id else ""

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return f'<c r="{cell_ref}"{style}><v>{value}</v></c>'

    text = escape(str(value))
    return f'<c r="{cell_ref}" t="inlineStr"{style}><is><t>{text}</t></is></c>'


def column_letter(index: int) -> str:
    letters = ""
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        letters = chr(65 + remainder) + letters
    return letters


def worksheet_xml(rows: list[list]):
    max_cols = max((len(row) for row in rows), default=1)
    max_rows = max(len(rows), 1)

    widths = []
    for col_idx in range(max_cols):
        max_len = 10
        for row in rows:
            if col_idx < len(row):
                max_len = max(max_len, len(str(row[col_idx])))
        widths.append(min(max_len + 2, 40))

    cols_xml = "".join(
        f'<col min="{idx}" max="{idx}" width="{width}" customWidth="1"/>'
        for idx, width in enumerate(widths, start=1)
    )

    sheet_rows = []
    for row_idx, row in enumerate(rows, start=1):
        cells = []
        is_section_title = len(row) == 1 and row[0] and row_idx != 1
        for col_idx, value in enumerate(row, start=1):
            style_id = 2 if is_section_title else 1 if row_idx == 1 else 0
            cells.append(xml_cell(value, row_idx, col_idx, style_id))
        sheet_rows.append(f'<row r="{row_idx}">{"".join(cells)}</row>')

    dimension = f"A1:{column_letter(max_cols)}{max_rows}"
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <dimension ref="{dimension}"/>
  <sheetViews>
    <sheetView workbookViewId="0">
      <pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/>
    </sheetView>
  </sheetViews>
  <sheetFormatPr defaultRowHeight="18"/>
  <cols>{cols_xml}</cols>
  <sheetData>{"".join(sheet_rows)}</sheetData>
</worksheet>
"""


def build_detail_sheets(data: dict):
    home = data["homeMockData"]
    admission = data["admissionMockData"]
    academic = data["academicStatusMockData"]
    training = data["trainingMockData"]
    degree = data["degreeMockData"]
    scholarship = data["scholarshipMockData"]
    employment = data["employmentMockData"]
    messages = data["messageMockData"]
    smart = data["smartPredictionMockData"]

    return [
        ("00_说明", [
            ["项目", "内容"],
            ["文件来源", "src/mock/graduateManagementMock.js"],
            ["生成时间", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            ["说明", "本工作簿为模拟数据明细版，适合逐页检查页面字段和数据结构。"],
        ]),
        ("01_共享选项", rows_from_mapping(data["sharedOptions"])),
        ("02_首页_统计卡", rows_from_records(home["statCards"])),
        ("03_首页_趋势", rows_from_records(home["charts"]["trend"])),
        ("04_首页_性别", rows_from_records(home["charts"]["gender"])),
        ("05_首页_年级", rows_from_records(home["charts"]["grades"])),
        ("06_首页_生源地", rows_from_records(home["charts"]["sourceRegions"])),
        ("07_首页_通知", rows_from_records(home["notices"])),
        ("08_首页_待办", rows_from_records(home["todos"])),
        ("09_招生_统计卡", rows_from_records(admission["statCards"])),
        ("10_招生_报名趋势", rows_from_records(admission["charts"]["applyTrend"])),
        ("11_招生_专业TOP", rows_from_records(admission["charts"]["majorTop"])),
        ("12_招生_生源分布", rows_from_records(admission["charts"]["sourceDistribution"])),
        ("13_招生_进度", rows_from_records(admission["progress"])),
        ("14_招生_通知", rows_from_records(admission["notices"])),
        ("15_学籍_统计卡", rows_from_records(academic["statCards"])),
        ("16_学籍_年级分布", rows_from_records(academic["charts"]["gradeDistribution"])),
        ("17_学籍_专业TOP", rows_from_records(academic["charts"]["majorTop"])),
        ("18_学籍_状态分布", rows_from_records(academic["charts"]["statusDistribution"])),
        ("19_学籍_异动趋势", rows_from_records(academic["charts"]["changeTrend"])),
        ("20_学籍_异动记录", rows_from_records(academic["records"])),
        ("21_培养_统计卡", rows_from_records(training["statCards"])),
        ("22_培养_完成情况", rows_from_records(training["charts"]["planCompletion"])),
        ("23_培养_完成率趋势", rows_from_records(training["charts"]["completionTrend"])),
        ("24_培养_审核状态", rows_from_records(training["charts"]["statusDistribution"])),
        ("25_培养_年级完成率", rows_from_records(training["charts"]["gradeCompletion"])),
        ("26_培养_环节分布", rows_from_records(training["charts"]["stageDistribution"])),
        ("27_培养_评价结果", rows_from_records(training["charts"]["evaluationDistribution"])),
        ("28_培养_雷达指标", rows_from_records(training["charts"]["radar"])),
        ("29_培养_计划列表", rows_from_records(training["plans"])),
        ("30_培养_通知", rows_from_records(training["notices"])),
        ("31_培养_待办", rows_from_records(training["todos"])),
        ("32_学位_统计卡", rows_from_records(degree["statCards"])),
        ("33_学位_申请类型", rows_from_records(degree["charts"]["applicationTypes"])),
        ("34_学位_申请趋势", rows_from_records(degree["charts"]["applicationTrend"])),
        ("35_学位_评阅结果", rows_from_records(degree["charts"]["paperReview"])),
        ("36_学位_答辩结果", rows_from_records(degree["charts"]["defenseResults"])),
        ("37_学位_授予趋势", rows_from_records(degree["charts"]["awardTrend"])),
        ("38_学位_专业分布", rows_from_records(degree["charts"]["disciplineDistribution"])),
        ("39_学位_通知", rows_from_records(degree["notices"])),
        ("40_学位_待办", rows_from_records(degree["todos"])),
        ("41_奖助_统计卡", rows_from_records(scholarship["statCards"])),
        ("42_奖助_奖学金类型", rows_from_records(scholarship["charts"]["scholarshipTypes"])),
        ("43_奖助_助学金类型", rows_from_records(scholarship["charts"]["aidTypes"])),
        ("44_奖助_年级获奖", rows_from_records(scholarship["charts"]["gradeAwards"])),
        ("45_奖助_受奖分布", rows_from_records(scholarship["charts"]["studentAwardDistribution"])),
        ("46_奖助_专业获奖", rows_from_records(scholarship["charts"]["majorAwardTop"])),
        ("47_奖助_资金趋势", rows_from_records(scholarship["charts"]["fundTrend"])),
        ("48_奖助_通知", rows_from_records(scholarship["notices"])),
        ("49_奖助_待办", rows_from_records(scholarship["todos"])),
        ("50_就业_统计卡", rows_from_records(employment["statCards"])),
        ("51_就业_就业率趋势", rows_from_records(employment["metrics"][0]["series"])),
        ("52_就业_签约率趋势", rows_from_records(employment["metrics"][1]["series"])),
        ("53_就业_升学率趋势", rows_from_records(employment["metrics"][2]["series"])),
        ("54_就业_单位性质", rows_from_records(employment["charts"]["unitNature"])),
        ("55_就业_行业TOP", rows_from_records(employment["charts"]["industryTop"])),
        ("56_就业_去向统计", rows_from_records(employment["charts"]["destinationStats"])),
        ("57_就业_信息统计", rows_from_records(employment["charts"]["infoStats"])),
        ("58_就业_省份分布", rows_from_records(employment["charts"]["provinceDistribution"])),
        ("59_消息中心", rows_from_records(messages["messages"])),
        ("60_智能预测_毕业预测", rows_from_records(smart["charts"]["graduatePrediction"])),
        ("61_智能预测_发展指标", rows_from_records(smart["charts"]["studentDevelopment"])),
        ("62_智能预测_科研趋势", rows_from_records(smart["charts"]["researchTrend"])),
    ]


def build_merged_sheets(data: dict):
    home = data["homeMockData"]
    admission = data["admissionMockData"]
    academic = data["academicStatusMockData"]
    training = data["trainingMockData"]
    degree = data["degreeMockData"]
    scholarship = data["scholarshipMockData"]
    employment = data["employmentMockData"]
    messages = data["messageMockData"]
    smart = data["smartPredictionMockData"]

    overview_rows = [
        ["项目", "内容"],
        ["文件来源", "src/mock/graduateManagementMock.js"],
        ["生成时间", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        ["说明", "本工作簿为合并版，减少工作表数量，适合汇报演示。"],
    ]

    home_rows = []
    append_section(home_rows, "首页统计卡", rows_from_records(home["statCards"]))
    append_section(home_rows, "首页趋势", rows_from_records(home["charts"]["trend"]))
    append_section(home_rows, "首页性别", rows_from_records(home["charts"]["gender"]))
    append_section(home_rows, "首页年级", rows_from_records(home["charts"]["grades"]))
    append_section(home_rows, "首页生源地", rows_from_records(home["charts"]["sourceRegions"]))
    append_section(home_rows, "首页通知", rows_from_records(home["notices"]))
    append_section(home_rows, "首页待办", rows_from_records(home["todos"]))

    admission_rows = []
    append_section(admission_rows, "招生统计卡", rows_from_records(admission["statCards"]))
    append_section(admission_rows, "招生报名趋势", rows_from_records(admission["charts"]["applyTrend"]))
    append_section(admission_rows, "招生专业TOP", rows_from_records(admission["charts"]["majorTop"]))
    append_section(admission_rows, "招生生源分布", rows_from_records(admission["charts"]["sourceDistribution"]))
    append_section(admission_rows, "招生进度", rows_from_records(admission["progress"]))
    append_section(admission_rows, "招生通知", rows_from_records(admission["notices"]))

    academic_rows = []
    append_section(academic_rows, "学籍统计卡", rows_from_records(academic["statCards"]))
    append_section(academic_rows, "学籍年级分布", rows_from_records(academic["charts"]["gradeDistribution"]))
    append_section(academic_rows, "学籍专业TOP", rows_from_records(academic["charts"]["majorTop"]))
    append_section(academic_rows, "学籍状态分布", rows_from_records(academic["charts"]["statusDistribution"]))
    append_section(academic_rows, "学籍异动趋势", rows_from_records(academic["charts"]["changeTrend"]))
    append_section(academic_rows, "学籍异动记录", rows_from_records(academic["records"]))

    training_rows = []
    append_section(training_rows, "培养统计卡", rows_from_records(training["statCards"]))
    append_section(training_rows, "培养完成情况", rows_from_records(training["charts"]["planCompletion"]))
    append_section(training_rows, "培养完成率趋势", rows_from_records(training["charts"]["completionTrend"]))
    append_section(training_rows, "培养审核状态", rows_from_records(training["charts"]["statusDistribution"]))
    append_section(training_rows, "培养年级完成率", rows_from_records(training["charts"]["gradeCompletion"]))
    append_section(training_rows, "培养环节分布", rows_from_records(training["charts"]["stageDistribution"]))
    append_section(training_rows, "培养评价结果", rows_from_records(training["charts"]["evaluationDistribution"]))
    append_section(training_rows, "培养雷达指标", rows_from_records(training["charts"]["radar"]))
    append_section(training_rows, "培养计划列表", rows_from_records(training["plans"]))
    append_section(training_rows, "培养通知", rows_from_records(training["notices"]))
    append_section(training_rows, "培养待办", rows_from_records(training["todos"]))

    degree_rows = []
    append_section(degree_rows, "学位统计卡", rows_from_records(degree["statCards"]))
    append_section(degree_rows, "学位申请类型", rows_from_records(degree["charts"]["applicationTypes"]))
    append_section(degree_rows, "学位申请趋势", rows_from_records(degree["charts"]["applicationTrend"]))
    append_section(degree_rows, "学位评阅结果", rows_from_records(degree["charts"]["paperReview"]))
    append_section(degree_rows, "学位答辩结果", rows_from_records(degree["charts"]["defenseResults"]))
    append_section(degree_rows, "学位授予趋势", rows_from_records(degree["charts"]["awardTrend"]))
    append_section(degree_rows, "学位专业分布", rows_from_records(degree["charts"]["disciplineDistribution"]))
    append_section(degree_rows, "学位通知", rows_from_records(degree["notices"]))
    append_section(degree_rows, "学位待办", rows_from_records(degree["todos"]))

    scholarship_rows = []
    append_section(scholarship_rows, "奖助统计卡", rows_from_records(scholarship["statCards"]))
    append_section(scholarship_rows, "奖学金类型", rows_from_records(scholarship["charts"]["scholarshipTypes"]))
    append_section(scholarship_rows, "助学金类型", rows_from_records(scholarship["charts"]["aidTypes"]))
    append_section(scholarship_rows, "年级获奖", rows_from_records(scholarship["charts"]["gradeAwards"]))
    append_section(scholarship_rows, "受奖分布", rows_from_records(scholarship["charts"]["studentAwardDistribution"]))
    append_section(scholarship_rows, "专业获奖", rows_from_records(scholarship["charts"]["majorAwardTop"]))
    append_section(scholarship_rows, "资金趋势", rows_from_records(scholarship["charts"]["fundTrend"]))
    append_section(scholarship_rows, "奖助通知", rows_from_records(scholarship["notices"]))
    append_section(scholarship_rows, "奖助待办", rows_from_records(scholarship["todos"]))

    employment_rows = []
    append_section(employment_rows, "就业统计卡", rows_from_records(employment["statCards"]))
    append_section(employment_rows, "就业率趋势", rows_from_records(employment["metrics"][0]["series"]))
    append_section(employment_rows, "签约率趋势", rows_from_records(employment["metrics"][1]["series"]))
    append_section(employment_rows, "升学率趋势", rows_from_records(employment["metrics"][2]["series"]))
    append_section(employment_rows, "单位性质", rows_from_records(employment["charts"]["unitNature"]))
    append_section(employment_rows, "行业TOP", rows_from_records(employment["charts"]["industryTop"]))
    append_section(employment_rows, "去向统计", rows_from_records(employment["charts"]["destinationStats"]))
    append_section(employment_rows, "信息统计", rows_from_records(employment["charts"]["infoStats"]))
    append_section(employment_rows, "省份分布", rows_from_records(employment["charts"]["provinceDistribution"]))

    other_rows = []
    append_section(other_rows, "共享选项", rows_from_mapping(data["sharedOptions"]))
    append_section(other_rows, "消息中心", rows_from_records(messages["messages"]))
    append_section(other_rows, "智能预测_毕业预测", rows_from_records(smart["charts"]["graduatePrediction"]))
    append_section(other_rows, "智能预测_发展指标", rows_from_records(smart["charts"]["studentDevelopment"]))
    append_section(other_rows, "智能预测_科研趋势", rows_from_records(smart["charts"]["researchTrend"]))

    return [
        ("00_说明", overview_rows),
        ("01_首页总览", home_rows),
        ("02_招生管理", admission_rows),
        ("03_学籍管理", academic_rows),
        ("04_培养管理", training_rows),
        ("05_学位管理", degree_rows),
        ("06_奖助管理", scholarship_rows),
        ("07_就业管理", employment_rows),
        ("08_其他补充", other_rows),
    ]


def styles_xml():
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="3">
    <font>
      <sz val="11"/>
      <name val="Calibri"/>
    </font>
    <font>
      <b/>
      <sz val="11"/>
      <name val="Calibri"/>
      <color rgb="FFFFFFFF"/>
    </font>
    <font>
      <b/>
      <sz val="11"/>
      <name val="Calibri"/>
      <color rgb="FF0A2463"/>
    </font>
  </fonts>
  <fills count="4">
    <fill><patternFill patternType="none"/></fill>
    <fill><patternFill patternType="gray125"/></fill>
    <fill>
      <patternFill patternType="solid">
        <fgColor rgb="FF0A2463"/>
        <bgColor indexed="64"/>
      </patternFill>
    </fill>
    <fill>
      <patternFill patternType="solid">
        <fgColor rgb="FFEAF1FF"/>
        <bgColor indexed="64"/>
      </patternFill>
    </fill>
  </fills>
  <borders count="2">
    <border>
      <left/><right/><top/><bottom/><diagonal/>
    </border>
    <border>
      <left style="thin"><color rgb="FFD9E2F3"/></left>
      <right style="thin"><color rgb="FFD9E2F3"/></right>
      <top style="thin"><color rgb="FFD9E2F3"/></top>
      <bottom style="thin"><color rgb="FFD9E2F3"/></bottom>
      <diagonal/>
    </border>
  </borders>
  <cellStyleXfs count="1">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0"/>
  </cellStyleXfs>
  <cellXfs count="3">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
    <xf numFmtId="0" fontId="1" fillId="2" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1"/>
    <xf numFmtId="0" fontId="2" fillId="3" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1"/>
  </cellXfs>
  <cellStyles count="1">
    <cellStyle name="Normal" xfId="0" builtinId="0"/>
  </cellStyles>
</styleSheet>
"""


def workbook_xml(sheet_names: list[str]):
    sheets = "".join(
        f'<sheet name="{escape(name)}" sheetId="{idx}" r:id="rId{idx}"/>'
        for idx, name in enumerate(sheet_names, start=1)
    )
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
          xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>{sheets}</sheets>
</workbook>
"""


def workbook_rels_xml(sheet_names: list[str]):
    relationships = "".join(
        f'<Relationship Id="rId{idx}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{idx}.xml"/>'
        for idx, _ in enumerate(sheet_names, start=1)
    )
    style_id = len(sheet_names) + 1
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  {relationships}
  <Relationship Id="rId{style_id}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>
"""


def root_rels_xml():
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>
"""


def content_types_xml(sheet_count: int):
    overrides = [
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>',
        '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>',
    ]
    overrides.extend(
        f'<Override PartName="/xl/worksheets/sheet{idx}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        for idx in range(1, sheet_count + 1)
    )
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  {''.join(overrides)}
</Types>
"""


def write_workbook(output_file: Path, sheets: list[tuple[str, list[list]]]):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    sheet_names = [name for name, _ in sheets]

    with zipfile.ZipFile(output_file, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types_xml(len(sheets)))
        zf.writestr("_rels/.rels", root_rels_xml())
        zf.writestr("xl/workbook.xml", workbook_xml(sheet_names))
        zf.writestr("xl/_rels/workbook.xml.rels", workbook_rels_xml(sheet_names))
        zf.writestr("xl/styles.xml", styles_xml())

        for idx, (_, rows) in enumerate(sheets, start=1):
            zf.writestr(f"xl/worksheets/sheet{idx}.xml", worksheet_xml(rows))


def main():
    data = load_mock_data()
    detail_sheets = build_detail_sheets(data)
    merged_sheets = build_merged_sheets(data)
    write_workbook(DETAIL_FILE, detail_sheets)
    write_workbook(MERGED_FILE, merged_sheets)
    print(DETAIL_FILE)
    print(MERGED_FILE)


if __name__ == "__main__":
    main()
