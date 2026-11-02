"""
生成用于测试数据上传功能的 Excel 文件
"""
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from datetime import datetime, timedelta
import random

def generate_student_data():
    """生成学生基本信息测试数据"""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "学生基本信息"

    # 设置表头
    headers = [
        '学号', '姓名', '性别', '年级', '学院', '专业',
        '培养层次', '学籍状态', '导师姓名', '入学日期'
    ]

    # 写入表头并设置样式
    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.font = Font(bold=True, size=12)
        cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.font = Font(bold=True, size=12, color="FFFFFF")

    # 生成测试数据
    majors = ['计算机科学与技术', '软件工程', '人工智能', '网络工程', '信息安全']
    grades = ['2021级', '2022级', '2023级', '2024级']
    degree_types = ['学术硕士', '专业硕士', '博士']
    statuses = ['在读', '在读', '在读', '休学']  # 大部分在读
    advisors = ['张教授', '李教授', '王教授', '刘教授', '陈教授']

    last_names = ['张', '王', '李', '刘', '陈', '杨', '黄', '赵', '吴', '周']
    first_names = ['伟', '芳', '娜', '秀英', '敏', '静', '丽', '强', '磊', '军', '洋', '勇', '艳', '杰', '涛']

    for i in range(1, 51):  # 生成50条数据
        student_id = f"2023{str(i).zfill(3)}"
        name = random.choice(last_names) + random.choice(first_names) + (random.choice(first_names) if random.random() > 0.7 else '')
        gender = random.choice(['男', '女'])
        grade = random.choice(grades)
        college = '政治学与公共管理学院'
        major = random.choice(majors)
        degree_type = random.choice(degree_types)
        status = random.choice(statuses)
        advisor = random.choice(advisors)
        admission_date = f"{grade[:4]}-09-01"

        row_data = [
            student_id, name, gender, grade, college, major,
            degree_type, status, advisor, admission_date
        ]

        for col_idx, value in enumerate(row_data, start=1):
            ws.cell(row=i+1, column=col_idx, value=value)

    # 调整列宽
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = (max_length + 2) * 1.2
        ws.column_dimensions[column].width = adjusted_width

    wb.save('测试数据_学生基本信息.xlsx')
    print("已生成：测试数据_学生基本信息.xlsx")


def generate_scholarship_data():
    """生成奖学金数据"""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "奖学金获奖记录"

    # 设置表头
    headers = ['学号', '姓名', '奖项名称', '获奖年度', '金额（元）', '等级']

    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.font = Font(bold=True, size=12)
        cell.fill = PatternFill(start_color="70AD47", end_color="70AD47", fill_type="solid")
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.font = Font(bold=True, size=12, color="FFFFFF")

    # 奖学金类型
    awards = [
        ('国家奖学金', 20000, '国家级'),
        ('学业奖学金一等奖', 12000, '一等'),
        ('学业奖学金二等奖', 8000, '二等'),
        ('学业奖学金三等奖', 4000, '三等'),
        ('优秀学生奖学金', 3000, '优秀'),
    ]

    last_names = ['张', '王', '李', '刘', '陈', '杨', '黄', '赵', '吴', '周']
    first_names = ['伟', '芳', '娜', '秀英', '敏', '静', '丽', '强', '磊', '军']

    row_idx = 2
    for i in range(1, 51):
        student_id = f"2023{str(i).zfill(3)}"
        name = random.choice(last_names) + random.choice(first_names)

        # 30%的学生获得奖学金
        if random.random() < 0.3:
            award, amount, level = random.choice(awards)
            year = random.choice([2023, 2024])

            row_data = [student_id, name, award, year, amount, level]

            for col_idx, value in enumerate(row_data, start=1):
                ws.cell(row=row_idx, column=col_idx, value=value)

            row_idx += 1

    # 调整列宽
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = (max_length + 2) * 1.2
        ws.column_dimensions[column].width = adjusted_width

    wb.save('测试数据_奖学金记录.xlsx')
    print("已生成：测试数据_奖学金记录.xlsx")


def generate_course_data():
    """生成课程成绩数据"""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "课程成绩"

    # 设置表头
    headers = ['学号', '姓名', '课程名称', '课程代码', '学分', '成绩', '学期', '考试时间']

    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.font = Font(bold=True, size=12)
        cell.fill = PatternFill(start_color="FFC000", end_color="FFC000", fill_type="solid")
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.font = Font(bold=True, size=12, color="FFFFFF")

    courses = [
        ('高级算法', 'CS601', 3),
        ('机器学习', 'CS602', 3),
        ('数据挖掘', 'CS603', 2),
        ('计算机视觉', 'CS604', 2),
        ('自然语言处理', 'CS605', 2),
        ('分布式系统', 'CS606', 3),
    ]

    semesters = ['2023-2024学年第一学期', '2023-2024学年第二学期', '2024-2025学年第一学期']

    last_names = ['张', '王', '李', '刘', '陈', '杨', '黄', '赵', '吴', '周']
    first_names = ['伟', '芳', '娜', '秀英', '敏', '静', '丽', '强', '磊', '军']

    row_idx = 2
    for i in range(1, 31):  # 30个学生
        student_id = f"2023{str(i).zfill(3)}"
        name = random.choice(last_names) + random.choice(first_names)

        # 每个学生随机选3-5门课
        num_courses = random.randint(3, 5)
        selected_courses = random.sample(courses, num_courses)

        for course_name, course_code, credit in selected_courses:
            score = random.randint(60, 100)
            semester = random.choice(semesters)
            exam_date = f"{random.choice([2023, 2024])}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"

            row_data = [student_id, name, course_name, course_code, credit, score, semester, exam_date]

            for col_idx, value in enumerate(row_data, start=1):
                ws.cell(row=row_idx, column=col_idx, value=value)

            row_idx += 1

    # 调整列宽
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = (max_length + 2) * 1.2
        ws.column_dimensions[column].width = adjusted_width

    wb.save('测试数据_课程成绩.xlsx')
    print("已生成：测试数据_课程成绩.xlsx")


def generate_employment_data():
    """生成就业信息数据"""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "就业信息"

    # 设置表头
    headers = ['学号', '姓名', '毕业年份', '就业单位', '就业类型', '职位', '薪资范围', '工作地点']

    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.font = Font(bold=True, size=12)
        cell.fill = PatternFill(start_color="ED7D31", end_color="ED7D31", fill_type="solid")
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.font = Font(bold=True, size=12, color="FFFFFF")

    companies = [
        '华为技术有限公司', '腾讯科技', '阿里巴巴', '百度', '字节跳动',
        '京东', '美团', '滴滴出行', '小米科技', '网易'
    ]

    job_types = ['企业就业', '事业单位', '继续深造', '自主创业']
    positions = ['软件工程师', '算法工程师', '产品经理', '数据分析师', '项目经理']
    salary_ranges = ['10-15万', '15-20万', '20-25万', '25-30万', '30万以上']
    cities = ['北京', '上海', '深圳', '杭州', '广州', '成都', '南京', '武汉']

    last_names = ['张', '王', '李', '刘', '陈', '杨', '黄', '赵', '吴', '周']
    first_names = ['伟', '芳', '娜', '秀英', '敏', '静', '丽', '强', '磊', '军']

    row_idx = 2
    for i in range(1, 21):  # 20个毕业生
        student_id = f"2021{str(i).zfill(3)}"
        name = random.choice(last_names) + random.choice(first_names)
        grad_year = 2024
        company = random.choice(companies)
        job_type = random.choice(job_types)
        position = random.choice(positions)
        salary = random.choice(salary_ranges)
        city = random.choice(cities)

        row_data = [student_id, name, grad_year, company, job_type, position, salary, city]

        for col_idx, value in enumerate(row_data, start=1):
            ws.cell(row=row_idx, column=col_idx, value=value)

        row_idx += 1

    # 调整列宽
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = (max_length + 2) * 1.2
        ws.column_dimensions[column].width = adjusted_width

    wb.save('测试数据_就业信息.xlsx')
    print("已生成：测试数据_就业信息.xlsx")


def generate_multi_sheet_data():
    """生成包含多个Sheet的综合测试文件"""
    wb = openpyxl.Workbook()

    # Sheet 1: 学生基本信息
    ws1 = wb.active
    ws1.title = "学生信息"
    headers1 = ['学号', '姓名', '性别', '年级', '专业', '导师']
    for col_idx, header in enumerate(headers1, start=1):
        cell = ws1.cell(row=1, column=col_idx, value=header)
        cell.font = Font(bold=True)

    for i in range(1, 11):
        ws1.cell(row=i+1, column=1, value=f"2023{str(i).zfill(3)}")
        ws1.cell(row=i+1, column=2, value=f"学生{i}")
        ws1.cell(row=i+1, column=3, value=random.choice(['男', '女']))
        ws1.cell(row=i+1, column=4, value='2023级')
        ws1.cell(row=i+1, column=5, value='计算机科学与技术')
        ws1.cell(row=i+1, column=6, value=f"{random.choice(['张', '王', '李'])}教授")

    # Sheet 2: 奖学金
    ws2 = wb.create_sheet("奖学金")
    headers2 = ['学号', '奖项名称', '金额', '年度']
    for col_idx, header in enumerate(headers2, start=1):
        cell = ws2.cell(row=1, column=col_idx, value=header)
        cell.font = Font(bold=True)

    for i in range(1, 6):
        ws2.cell(row=i+1, column=1, value=f"2023{str(i).zfill(3)}")
        ws2.cell(row=i+1, column=2, value='学业奖学金一等奖')
        ws2.cell(row=i+1, column=3, value=12000)
        ws2.cell(row=i+1, column=4, value=2024)

    # Sheet 3: 课程成绩
    ws3 = wb.create_sheet("成绩")
    headers3 = ['学号', '课程名称', '成绩', '学分']
    for col_idx, header in enumerate(headers3, start=1):
        cell = ws3.cell(row=1, column=col_idx, value=header)
        cell.font = Font(bold=True)

    courses = ['高级算法', '机器学习', '数据挖掘']
    row_idx = 2
    for i in range(1, 6):
        for course in courses:
            ws3.cell(row=row_idx, column=1, value=f"2023{str(i).zfill(3)}")
            ws3.cell(row=row_idx, column=2, value=course)
            ws3.cell(row=row_idx, column=3, value=random.randint(70, 95))
            ws3.cell(row=row_idx, column=4, value=3)
            row_idx += 1

    wb.save('测试数据_多Sheet综合.xlsx')
    print("已生成：测试数据_多Sheet综合.xlsx")


if __name__ == '__main__':
    print("开始生成测试数据...")
    print()

    generate_student_data()
    generate_scholarship_data()
    generate_course_data()
    generate_employment_data()
    generate_multi_sheet_data()

    print()
    print("=" * 50)
    print("所有测试数据已生成完成！")
    print("=" * 50)
    print()
    print("生成的文件列表：")
    print("1. 测试数据_学生基本信息.xlsx - 50条学生记录")
    print("2. 测试数据_奖学金记录.xlsx - 奖学金获奖记录")
    print("3. 测试数据_课程成绩.xlsx - 课程成绩数据")
    print("4. 测试数据_就业信息.xlsx - 毕业生就业信息")
    print("5. 测试数据_多Sheet综合.xlsx - 包含多个Sheet的测试文件")
    print()
    print("使用说明：")
    print("1. 启动后端服务器：cd backend && python manage.py runserver")
    print("2. 在数据管理页面点击上传，选择生成的Excel文件")
    print("3. 系统会自动识别Sheet和字段")
    print("4. 按照向导完成数据导入")
