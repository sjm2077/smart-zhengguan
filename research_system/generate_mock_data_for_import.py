import csv
import random
from datetime import datetime, timedelta

# ==================== 教师名单（按系，来自真实数据） ====================
teachers_by_dept = {
    '科学社会主义系': [
        '郭春生', '蒋锐', '李宏', '李亚洲', '刘玉安', '臧秀玲', '赵婷',
        '吕连仁', '王鹏权', '金淑霞', '庞敏', '杨春林', '胡志伟'
    ],
    '政治学系': [
        '楚成亚', '方雷', '孔令栋', '李济时', '李振', '王成', '张继亮',
        '刘琳', '法帅', '王军洋', '徐会平', '钟诚',
        '党成孝', '姬生翔', '黄靖', '孔令伟', '叶紫蒙', '白江波'
    ],
    '国际政治系': [
        '李昕蕾', '黄登学', '李慧明', '刘昌明', '秦亚青', '马荣久', '盛力',
        '王学玉', '张淑兰', '朱贵昌', '方炯升', '黄栋', '展妍男', '赵均佳',
        '米雪', '王薪喜', '霍文乐'
    ],
    '公共管理系': [
        '曹现强', '韩自强', '李辉', '李延伟', '马奔', '马永驰', '楼苏萍',
        '黄晴', '孙宗锋', '滕玉成', '王佃利', '邢占军', '张乐', '张天舒',
        '韩丽华', '季丽新', '李广', '魏铭', '杨志', '王元亮', '俞少宾',
        '刘浩', '刘华兴', '费立国', '程龙', '冷安丽', '陈仁兴', '郑子君',
        '高原', '张健彬', '郑国栋', 'Yunsoo Lee',
        '李欢欢', '陈静', '褚雷', '李梦丹', '赵志华', '罗聪', '朱林旭'
    ]
}

# 所有教师列表（用于分配负责人/作者）
all_teachers = []
for dept, tlist in teachers_by_dept.items():
    for t in tlist:
        all_teachers.append((t, dept))

# ==================== 成果标题（真实 + 模拟） ====================
real_titles = [
    "知识-行为-制度：我国地方政府危机学习模式与进阶路径",
    "Understanding public attitudes towards prog...",
    "Patterns of Family Harsh Parenting and the E...",
    "欧盟竞争力战略中的工业脱碳行动：战略考量、实施路径及其对...",
    "平台治理何以失效：基于政府与数字平台企业的实证研究",
    "党建何以引领社区治理：实践维度与内在机理——基于30个典型案例...",
    "投资于人：增强公共服务均衡性和可及性的目标建构与政策调适",
    "农村居民长期护理保险地方性实践的制度困境与发展路径——基于...",
    "监管对象何以反向影响监管效果——一个探索性混合研究",
    "Social Capital, Long-Term Care Insurance, and Olde...",
    "Phased effects of China'...",
    "公共部门算法治理研究——基于英文文献的系统性回顾",
    "地方政府推行产业政策中的揭榜挂帅：以J市为例",
    "政策叙事何以影响闲置宅基地退出意愿？——一项针对青年...",
    "统还足分？地方政府生成式人工智能本地化部署的模式选择与影...",
    "归口领导原则下的机构改革的限度和挑战——基于对J市新设退役...",
    "武器化之前：关系性逻辑与美俄相互依赖演进",
    "新时代中国共产党国际观的生成逻辑、主要内容与价值意蕴",
    "纵向介入与自主行动：区域联动发展中地方政府合作的图景——基...",
    "数字社会治理的内在逻辑及未来趋势",
    "中国基层治理自主知识体系中标识性概念的建构",
    "差异平议：试析中国国际关系理论的创新",
    "人工智能算法何以重构社会治理？——基于中国警务部门算法运...",
    "地方政府营商环境优化研究",
    "社区治理现代化路径探索",
    "应急管理体系建设评估",
    "公共服务均等化政策评估",
    "智慧城市背景下的城市治理转型",
    "乡村振兴战略中的公共服务供给",
    "基层治理中的数字鸿沟问题",
    "大数据时代公共政策评估方法",
    "地方政府债务风险治理研究",
    "突发公共卫生事件应急管理机制",
    "社区网格化治理模式创新研究",
    "数字政府建设中的治理效能研究",
    "公共部门人力资源管理改革研究",
    "公共政策执行偏差的成因与对策",
    "全过程人民民主的理论与实践",
    "新时代党的建设理论创新",
    "中国式现代化的理论与实践路径",
    "21世纪国际共产主义运动新趋势",
    "国家治理体系与能力现代化",
    "马克思主义中国化时代化研究",
    "新时代政党治理现代化研究",
    "中国特色社会主义理论创新研究"
]

# 扩充标题（组合生成）
extra_titles = []
for i in range(50):
    extra_titles.append(
        f"基于{random.choice(['大数据','人工智能','区块链','云计算'])}的"
        f"{random.choice(['社会治理','公共服务','应急管理','数字治理','政策评估'])}研究"
    )
titles = real_titles + extra_titles

# ==================== 项目名称生成 ====================
project_parts = [
    "中国式现代化", "数字政府", "乡村振兴", "基层治理", "应急管理",
    "公共服务", "社会保障", "教育政策", "环境治理", "区域协调",
    "科技创新", "产业政策", "对外开放", "法治建设", "文化自信",
    "共同富裕", "碳中和", "人工智能治理", "数据安全", "城市管理",
    "社区服务", "公共卫生", "老龄化", "儿童福利", "住房保障",
    "就业促进", "金融监管", "国际贸易", "一带一路", "全球治理"
]
def generate_project_name():
    return f"{random.choice(project_parts)}的{random.choice(['路径','机制','模式','对策','评估','演进','实践','创新'])}研究"

# ==================== 生成数据 ====================
def generate_projects(num=300):
    projects = []
    for _ in range(num):
        leader, dept = random.choice(all_teachers)
        ptype = random.choice(['国家级', '省部级', '横向', '校级'])
        status = random.choice(['在研', '结题', '立项', '审核中'])
        fund = round(random.uniform(10, 500), 2)
        start_year = random.randint(2021, 2024)
        end_year = start_year + random.randint(1, 3)
        start_date = f"{start_year}-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
        end_date = f"{end_year}-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
        progress = random.randint(0, 100) if status != '结题' else 100
        subject = random.choice(['行政管理', '公共政策', '政治学理论', '社会保障', '国际关系'])
        project_name = generate_project_name()
        projects.append([project_name, leader, dept, fund, start_date, end_date, ptype, status, subject, progress])
    return projects

def generate_achievements(num=800):
    achievements = []
    for _ in range(num):
        title = random.choice(titles)
        author, dept = random.choice(all_teachers)
        ach_type = random.choice(['期刊论文', '学术著作', '研究报告', '决策咨询', '专利', '获奖'])
        if ach_type in ['期刊论文', '学术著作']:
            level = random.choice(['CSSCI', 'SSCI', '核心期刊', '国家级出版社', '省级采纳'])
        else:
            level = ''
        year = random.randint(2021, 2025)
        citation = random.randint(0, 80) if ach_type == '期刊论文' else 0
        is_international = random.choice([True, False]) if dept == '国际政治系' else False
        achievements.append([title, author, dept, ach_type, level, year, citation, is_international])
    return achievements

def generate_funds(projects, num=1200):
    funds = []
    usage_types = ['人员费', '调研费', '设备费', '会议费', '出版费', '其他']
    source_types = ['国家社科', '教育部', '省级项目', '横向课题', '政府委托']
    for _ in range(num):
        proj = random.choice(projects)
        project_name = proj[0]
        source = random.choice(source_types)
        amount = round(random.uniform(1, 80), 2)
        year = random.randint(2021, 2025)
        usage = random.choice(usage_types)
        funds.append([project_name, source, amount, year, usage])
    return funds

# ==================== 写入CSV ====================
def write_csv(filename, header, rows):
    with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)

# 生成数据
projects = generate_projects(300)
achievements = generate_achievements(800)
funds = generate_funds(projects, 1200)

write_csv('projects.csv',
          ['project_name', 'leader_name', 'dept_name', 'fund_amount', 'start_date', 'end_date', 'project_type', 'status', 'subject', 'actual_progress'],
          projects)

write_csv('achievements.csv',
          ['title', 'author_name', 'dept_name', 'achievement_type', 'level', 'publish_year', 'citation_count', 'is_international'],
          achievements)

write_csv('funds.csv',
          ['project_name', 'source_type', 'amount', 'year', 'usage_type'],
          funds)

print(f"✅ 生成完成：项目 {len(projects)} 个，成果 {len(achievements)} 项，经费明细 {len(funds)} 条。")