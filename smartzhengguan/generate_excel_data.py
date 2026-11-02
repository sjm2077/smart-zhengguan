import pandas as pd
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows

majors = ['政治学理论', '科学社会主义与国际共产主义运动', '中共党史', '行政管理', '国际政治', '国际关系', '统一战线学', '应急管理']
years = ['2021', '2022', '2023', '2024', '2025']
grades = ['2021级', '2022级', '2023级', '2024级', '2025级']

# 首页总览
home_data = {
    '年份': years,
    '在校学生总数': [2850, 3020, 3180, 3350, 3480],
    '硕士生人数': [2350, 2480, 2600, 2720, 2800],
    '博士生人数': [500, 540, 580, 630, 680],
    '国际学生人数': [85, 92, 105, 118, 135],
    '毕业生人数': [680, 720, 750, 780, 820],
}

# 各年级各专业数据
grade_major_data = []
for grade in grades[:5]:
    for major in majors:
        base_count = {'政治学理论': 85, '科学社会主义与国际共产主义运动': 65, '中共党史': 55, '行政管理': 50, '国际政治': 45, '国际关系': 40, '统一战线学': 35, '应急管理': 30}[major]
        year_factor = {'2021级': 0.95, '2022级': 1.0, '2023级': 1.05, '2024级': 1.1, '2025级': 1.15}[grade]
        male_ratio = 0.55 if '政治' in major else 0.48
        total = int(base_count * year_factor)
        grade_major_data.append({'年级': grade, '专业': major, '总人数': total, '男生人数': int(total * male_ratio), '女生人数': int(total * (1 - male_ratio))})

# 生源地数据
source_region_data = [
    {'生源地': '山东', '人数': 780, '占比': '22.1%'}, {'生源地': '江苏', '人数': 380, '占比': '10.8%'},
    {'生源地': '河南', '人数': 320, '占比': '9.1%'}, {'生源地': '广东', '人数': 260, '占比': '7.4%'},
    {'生源地': '湖北', '人数': 220, '占比': '6.2%'}, {'生源地': '上海', '人数': 180, '占比': '5.1%'},
    {'生源地': '浙江', '人数': 180, '占比': '5.1%'}, {'生源地': '北京', '人数': 150, '占比': '4.2%'},
    {'生源地': '湖南', '人数': 140, '占比': '4.0%'}, {'生源地': '河北', '人数': 130, '占比': '3.7%'},
    {'生源地': '其他', '人数': 860, '占比': '24.4%'}
]

# 招生管理数据
admission_data = []
for year in years:
    base_apply = {'2021': 3400, '2022': 3800, '2023': 4200, '2024': 4700, '2025': 5100, '2026': 5400}[year]
    admission_data.append({
        '年份': year,
        '硕士报名人数': int(base_apply * 0.85), '硕士复试人数': int(base_apply * 0.85 * 0.35),
        '硕士拟录取人数': int(base_apply * 0.85 * 0.18), '硕士正式录取人数': int(base_apply * 0.85 * 0.17),
        '博士报名人数': int(base_apply * 0.12), '博士复试人数': int(base_apply * 0.12 * 0.6),
        '博士拟录取人数': int(base_apply * 0.12 * 0.35), '博士正式录取人数': int(base_apply * 0.12 * 0.33),
        '国际学生报名人数': int(base_apply * 0.03), '国际学生录取人数': int(base_apply * 0.03 * 0.45)
    })

# 学籍管理数据
academic_status_data = []
for year in years:
    base_enroll = {'2021': 2850, '2022': 3020, '2023': 3180, '2024': 3350, '2025': 3480, '2026': 3520}[year]
    academic_status_data.append({
        '年份': year, '在籍学生数': base_enroll, '注册学生数': int(base_enroll * 0.985),
        '休学人数': int(base_enroll * 0.012), '复学人数': int(base_enroll * 0.010),
        '退学人数': int(base_enroll * 0.005), '延毕人数': int(base_enroll * 0.025), '其他异动人数': int(base_enroll * 0.008)
    })

# 培养管理数据
training_data = []
for year in years:
    base_plan = {'2021': 680, '2022': 720, '2023': 750, '2024': 780, '2025': 820, '2026': 850}[year]
    training_data.append({
        '年份': year, '培养计划总数': base_plan, '已提交培养计划数量': int(base_plan * 0.95),
        '已审核通过培养计划数量': int(base_plan * 0.88), '未完成培养计划数量': int(base_plan * 0.07),
        '开题人数': int(base_plan * 0.92), '中期考核人数': int(base_plan * 0.85), '答辩阶段人数': int(base_plan * 0.78)
    })

# 课程与培养环节数据
courses_data = []
for year in years:
    for semester in ['春季', '秋季']:
        base_course = {'2021': 110, '2022': 115, '2023': 120, '2024': 125, '2025': 130, '2026': 135}[year]
        courses_data.append({
            '年份': year, '学期': semester, '开课数量': base_course,
            '选课学生人数': int(base_course * 28), '课程通过人数': int(base_course * 26),
            '课程不通过人数': int(base_course * 1.2), '缺勤人数': int(base_course * 8), '请假人数': int(base_course * 4)
        })

# 学位管理数据
degree_data = []
for year in years:
    base_apply = {'2021': 650, '2022': 690, '2023': 720, '2024': 750, '2025': 790, '2026': 820}[year]
    degree_data.append({
        '年份': year, '学位申请人数': base_apply, '论文提交人数': int(base_apply * 0.97),
        '论文送审人数': int(base_apply * 0.95), '论文评阅通过人数': int(base_apply * 0.92),
        '答辩通过人数': int(base_apply * 0.90), '学术学位授予人数': int(base_apply * 0.65), '专业学位授予人数': int(base_apply * 0.25)
    })

# 答辩管理数据
defense_data = []
for year in years:
    base_defense = {'2021': 620, '2022': 660, '2023': 690, '2024': 720, '2025': 760, '2026': 790}[year]
    defense_data.append({
        '年份': year, '答辩学生人数': base_defense, '答辩场次数量': int(base_defense / 6),
        '答辩通过人数': int(base_defense * 0.96), '答辩未通过人数': int(base_defense * 0.04)
    })

# 奖助管理数据
scholarship_data = []
for year in years:
    base_student = {'2021': 2850, '2022': 3020, '2023': 3180, '2024': 3350, '2025': 3480, '2026': 3520}[year]
    scholarship_data.append({
        '年份': year, '国家奖学金人数': 8, '国家奖学金金额': 8 * 30000,
        '学业奖学金人数': int(base_student * 0.35), '学业奖学金金额': int(base_student * 0.35 * 12000),
        '社会奖学金人数': int(base_student * 0.08), '社会奖学金金额': int(base_student * 0.08 * 8000),
        '助学金人数': int(base_student * 0.45), '助学金金额': int(base_student * 0.45 * 6000)
    })

# 就业管理数据
employment_data = []
for year in years:
    base_grad = {'2021': 680, '2022': 720, '2023': 750, '2024': 780, '2025': 820, '2026': 850}[year]
    employment_data.append({
        '年份': year, '毕业生总人数': base_grad, '已就业人数': int(base_grad * 0.92),
        '升学人数': int(base_grad * 0.15), '出国出境人数': int(base_grad * 0.08),
        '灵活就业人数': int(base_grad * 0.05), '未就业人数': int(base_grad * 0.08), '签约人数': int(base_grad * 0.85)
    })

# 智能预测数据
student_names = ['张浩然', '李思琪', '王博文', '刘雅琪', '陈嘉欣', '赵子轩', '孙雨萱', '周俊豪', '吴佳怡', '郑子涵', '黄思远', '周子涵', '林子轩', '何雨桐', '马晨曦', '罗艺凡', '高子轩', '梁雨萱', '谢佳怡', '宋子涵', '唐思远', '许雨桐', '邓子轩', '韩佳怡', '曹思远', '曾雨萱', '彭子涵', '肖佳怡', '田思远', '董雨桐']
student_predict_data = []
degree_cycle = ['硕士', '专业硕士', '博士']
advisor_cycle = ['王教授', '李教授', '张教授', '刘教授', '陈教授', '赵教授', '孙教授', '周教授']
training_status_cycle = ['已完成', '已完成', '进行中', '进行中', '进行中']
pair_size = 2
for i, name in enumerate(student_names):
    combo_idx = i // pair_size
    grade_idx = combo_idx % len(grades)
    degree_idx = (combo_idx // len(grades)) % len(degree_cycle)
    major_idx = (combo_idx * 2) % len(majors)
    student_predict_data.append({
        '姓名': name,
        '学号': f'{2021 + grade_idx}{major_idx + 1:02d}{i + 1:04d}',
        '类别': degree_cycle[degree_idx],
        '年级': grades[grade_idx],
        '专业': majors[major_idx],
        '学院': '政治学与公共管理学院',
        '导师': advisor_cycle[major_idx],
        '课程成绩': round(82 + (i % 5) * 3 + (i % 3), 1), '学分完成情况': 60 + (i % 40),
        '考勤情况': 92 + (i % 8), '培养节点完成情况': training_status_cycle[grade_idx],
        '科研成果数量': i % 5, '科研项目参与数量': i % 3, '活动参与次数': 5 + (i % 10),
        '活动时长': 20 + (i % 30), '社会实践次数': 2 + (i % 5), '社会实践时长': 30 + (i % 50),
        '导师沟通次数': 8 + (i % 12), '导师评价分数': round(85 + (i % 15), 1),
        '任务逾期次数': i % 3, '未打卡记录次数': i % 2, '心理测评分数': round(75 + (i % 20), 1)
    })

# 生成Excel文件
wb = Workbook()
wb.remove(wb.active)

# 创建各个工作表
sheets = [
    ('首页总览-年度数据', pd.DataFrame(home_data)),
    ('首页总览-年级专业', pd.DataFrame(grade_major_data)),
    ('首页总览-生源地', pd.DataFrame(source_region_data)),
    ('招生管理-年度汇总', pd.DataFrame(admission_data)),
    ('学籍管理', pd.DataFrame(academic_status_data)),
    ('培养管理', pd.DataFrame(training_data)),
    ('课程与培养环节', pd.DataFrame(courses_data)),
    ('学位管理', pd.DataFrame(degree_data)),
    ('答辩管理', pd.DataFrame(defense_data)),
    ('奖助管理', pd.DataFrame(scholarship_data)),
    ('就业管理', pd.DataFrame(employment_data)),
    ('智能预测-学生数据', pd.DataFrame(student_predict_data))
]

for name, df in sheets:
    ws = wb.create_sheet(name)
    for r in dataframe_to_rows(df, index=False, header=True):
        ws.append(r)

# 保存文件
output_path = '研究生数据_2021-2025.xlsx'
legacy_output_path = '研究生数据_2021-2026.xlsx'
wb.save(output_path)
wb.save(legacy_output_path)
print(f"Excel文件已生成: {output_path}")
print(f"兼容副本已生成: {legacy_output_path}")
print(f"包含 {len(sheets)} 个工作表")
