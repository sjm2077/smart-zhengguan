"""扩充「智能预测-学生数据」工作表，使每个年级×专业组合约 15 人。

背景：原表每个年级×专业只有 1 人（共 30 行），进入智能预测页面后
可选预测对象过少。本脚本把它补到 5 年级 × 8 专业 × 15 ≈ 600 人。

设计约定（都是从现有数据反推出来的，不是随意设定）：
  - 学号 = 年级(4) + 专业代码(2) + 序号(4)，与原表规律一致；
  - 保留原有 30 行不动（学号、姓名、数值全部原样保留），只追加新行；
  - 各项指标在原表观测到的取值范围内生成，并刻意铺开风险分布，
    让高风险/预警/关注/正常四档都有样本，否则预警模块无数据可看；
  - 固定随机种子，重复执行结果一致，便于核对。

用法：
    python expand_prediction_students.py                  # 默认每组合 15 人
    python expand_prediction_students.py --per-group 20
    python expand_prediction_students.py --dry-run        # 只预览不写盘
"""

import argparse
import random
import shutil
from collections import Counter
from datetime import datetime
from pathlib import Path

import openpyxl

WORKBOOK = Path("研究生数据_2021-2026.xlsx")
SHEET = "智能预测-学生数据"
QUOTA_SHEET = "首页总览-年级专业"

GRADES = ["2021级", "2022级", "2023级", "2024级", "2025级"]

# 专业 -> 学号里的两位专业代码，取自原表既有规律
MAJOR_CODES = {
    "政治学理论": "01",
    "科学社会主义与国际共产主义运动": "02",
    "中共党史": "03",
    "行政管理": "04",
    "国际政治": "05",
    "国际关系": "06",
    "统一战线学": "07",
    "应急管理": "08",
}

ADVISORS = ["王教授", "李教授", "张教授", "刘教授", "陈教授", "赵教授", "孙教授", "周教授"]

SURNAMES = [
    "张", "李", "王", "刘", "陈", "赵", "孙", "周", "吴", "郑", "黄", "林", "何", "马",
    "罗", "高", "梁", "谢", "宋", "唐", "许", "韩", "冯", "邓", "曹", "彭", "曾", "田",
    "于", "董", "袁", "蔡", "蒋", "余", "杜", "叶", "程", "苏", "魏", "吕",
]
GIVEN_NAMES = [
    "浩然", "思琪", "博文", "雅琪", "嘉欣", "子轩", "雨萱", "俊豪", "佳怡", "子涵",
    "思远", "雨桐", "晨曦", "艺凡", "宇航", "安琪", "语涵", "明轩", "睿哲", "欣怡",
    "泽宇", "若曦", "子墨", "梦瑶", "天翊", "静姝", "文博", "芷若", "昊宇", "clara",
    "嘉树", "астра", "伊然", "承志", "книга", "思源", "олег", "婉清", "柏舟", "澜依",
]
# 清掉上面混入的非中文占位，保证姓名可读
GIVEN_NAMES = [n for n in GIVEN_NAMES if all("一" <= ch <= "鿿" for ch in n)]

# 风险画像：按比例铺开，保证四个风险档位都有样本。
# 字段含义见原表表头；取值区间参考原表 min/max 并适度外扩低端，
# 以便产生真实的高风险样本（原表数据过于理想，几乎全是低风险）。
PROFILES = [
    # (权重, 课程成绩, 学分完成, 考勤, 培养节点, 逾期, 未打卡, 心理分, 导师评价)
    ("healthy", 40, (85, 96), (78, 92), (94, 99), "已完成", (0, 0), (0, 0), (82, 95), (88, 99)),
    ("watch", 25, (78, 88), (68, 82), (90, 96), "进行中", (0, 1), (0, 1), (76, 88), (82, 93)),
    ("alert", 22, (70, 80), (60, 72), (86, 93), "进行中", (1, 2), (1, 2), (70, 80), (75, 86)),
    ("high", 13, (58, 72), (45, 63), (76, 89), "未开始", (2, 5), (2, 4), (56, 70), (62, 78)),
]


def weighted_profile(rng):
    total = sum(item[1] for item in PROFILES)
    pick = rng.uniform(0, total)
    upto = 0
    for profile in PROFILES:
        upto += profile[1]
        if pick <= upto:
            return profile
    return PROFILES[-1]


def build_row(rng, name, student_id, degree, grade, major, advisor):
    (
        _label,
        _weight,
        course,
        credit,
        attendance,
        training,
        overdue,
        missed,
        wellbeing,
        advisor_score,
    ) = weighted_profile(rng)

    return [
        name,
        student_id,
        degree,
        grade,
        major,
        "政治学与公共管理学院",
        advisor,
        rng.randint(*course),             # 课程成绩
        rng.randint(*credit),             # 学分完成情况
        rng.randint(*attendance),         # 考勤情况
        training,                          # 培养节点完成情况
        rng.randint(0, 5),                # 科研成果数量
        rng.randint(0, 3),                # 科研项目参与数量
        rng.randint(3, 16),               # 活动参与次数
        rng.randint(15, 60),              # 活动时长
        rng.randint(1, 8),                # 社会实践次数
        rng.randint(20, 70),              # 社会实践时长
        rng.randint(4, 20),               # 导师沟通次数
        rng.randint(*advisor_score),      # 导师评价分数
        rng.randint(*overdue),            # 任务逾期次数
        rng.randint(*missed),             # 未打卡记录次数
        rng.randint(*wellbeing),          # 心理测评分数
    ]


def classify(course, credit, attendance, training, overdue, missed, wellbeing):
    """复刻 import_excel_data.prediction_risk_fields 的判级逻辑，用于预览分布。"""
    training_rate = 100.0 if training == "已完成" else 72.0
    issues = 0
    if course < 75:
        issues += 1
    if credit < 70:
        issues += 1
    if attendance < 90:
        issues += 1
    if training_rate < 80:
        issues += 1
    if overdue >= 2:
        issues += 1
    if missed >= 2:
        issues += 1
    if wellbeing < 75:
        issues += 1

    if issues >= 4 or wellbeing < 65:
        return "高风险"
    if issues >= 2 or course < 80:
        return "预警"
    if issues:
        return "关注"
    return "正常"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-group", type=int, default=15, help="每个年级×专业的目标人数")
    parser.add_argument("--dry-run", action="store_true", help="只预览，不写入文件")
    parser.add_argument(
        "--output",
        type=str,
        default="",
        help="写到指定文件而不是覆盖原表（原表被 Excel 占用时很有用）",
    )
    parser.add_argument("--seed", type=int, default=20260101)
    args = parser.parse_args()

    if not WORKBOOK.exists():
        raise SystemExit(f"找不到 {WORKBOOK}")

    rng = random.Random(args.seed)
    workbook = openpyxl.load_workbook(WORKBOOK)
    sheet = workbook[SHEET]

    existing = [r for r in sheet.iter_rows(min_row=2, values_only=True) if r and r[0]]
    used_ids = {str(r[1]) for r in existing}
    used_names = {str(r[0]) for r in existing}
    group_counts = Counter((str(r[3]), str(r[4])) for r in existing)

    # 配额校验：导入脚本会用「首页总览-年级专业」的总人数卡预测表的行，
    # 超出配额的行会被静默跳过，所以这里先确认目标人数没有超。
    quota = {}
    for row in workbook[QUOTA_SHEET].iter_rows(min_row=2, values_only=True):
        if row and row[0]:
            quota[(str(row[0]), str(row[1]))] = int(row[2] or 0)

    new_rows = []
    sequence = max((int(str(sid)[6:]) for sid in used_ids), default=0)

    for grade in GRADES:
        for major, code in MAJOR_CODES.items():
            key = (grade, major)
            limit = quota.get(key)
            target = args.per_group
            if limit is not None and target > limit:
                print(f"  [WARN] {grade}/{major} 配额仅 {limit}，目标下调为 {limit}")
                target = limit

            need = max(target - group_counts.get(key, 0), 0)
            for _ in range(need):
                sequence += 1
                student_id = f"{grade[:4]}{code}{sequence:04d}"
                while student_id in used_ids:
                    sequence += 1
                    student_id = f"{grade[:4]}{code}{sequence:04d}"
                used_ids.add(student_id)

                # 姓名尽量不重复；重名空间用尽时允许重复（学号仍唯一）
                name = None
                for _attempt in range(60):
                    candidate = rng.choice(SURNAMES) + rng.choice(GIVEN_NAMES)
                    if candidate not in used_names:
                        name = candidate
                        break
                name = name or rng.choice(SURNAMES) + rng.choice(GIVEN_NAMES)
                used_names.add(name)

                # 博士占比约 1/4，与原表 18:12 的量级接近
                degree = "博士" if rng.random() < 0.25 else "硕士"
                new_rows.append(
                    build_row(
                        rng, name, student_id, degree, grade, major, rng.choice(ADVISORS)
                    )
                )

    print(f"原有 {len(existing)} 行，新增 {len(new_rows)} 行，合计 {len(existing) + len(new_rows)} 行")

    all_rows = [list(r) for r in existing] + new_rows
    dist = Counter(
        classify(r[7], r[8], r[9], r[10], r[19], r[20], r[21]) for r in all_rows
    )
    print("风险分布预览:", dict(dist))
    per_group = Counter((r[3], r[4]) for r in all_rows)
    print(
        "每组合人数: min=%d max=%d 组合数=%d"
        % (min(per_group.values()), max(per_group.values()), len(per_group))
    )

    if args.dry_run:
        print("\n--dry-run，未写入文件。样例新行：")
        for row in new_rows[:3]:
            print("  ", row)
        return

    target_path = Path(args.output) if args.output else WORKBOOK

    for row in new_rows:
        sheet.append(row)

    if target_path == WORKBOOK:
        # 覆盖原表前先备份。原表被 Excel 打开时保存会 PermissionError，
        # 这种情况下建议改用 --output 写到新文件。
        backup = WORKBOOK.with_name(
            f"{WORKBOOK.stem}_备份_{datetime.now():%Y%m%d_%H%M%S}{WORKBOOK.suffix}"
        )
        shutil.copy2(WORKBOOK, backup)
        print(f"已备份原文件 -> {backup.name}")

    try:
        workbook.save(target_path)
    except PermissionError:
        raise SystemExit(
            f"\n无法写入 {target_path.name}：文件正被 Excel 占用。\n"
            f"请关闭该文件后重试，或用 --output 写到新文件。"
        )
    print(f"已写入 {target_path.name}，{SHEET} 现有 {sheet.max_row - 1} 行数据")


if __name__ == "__main__":
    main()
