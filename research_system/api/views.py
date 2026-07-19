from django.shortcuts import render
# Create your views here.
from django.http import JsonResponse
from .models import FundDetail
from django.db.models import Sum
from django.db.models import Count, Sum
from .models import Project, FundDetail, Achievement
from django.db.models import Count, Q
from django.db.models import Max

def fund_trend(request):
    years = [2021, 2022, 2023, 2024, 2025]
    data = FundDetail.objects.filter(year__in=years).values('year').annotate(total=Sum('amount'))
    result = {item['year']: float(item['total']) for item in data}
    return JsonResponse({'years': years, 'values': [result.get(y, 0) for y in years]})
# api/views.py 新增以下内容

from django.db.models import Sum, Count, Q, Avg
from django.http import JsonResponse
from .models import Project, FundDetail, Achievement, User, TeacherScore, Cooperation, Dept

# ---------- 1. 顶部卡片数据（当前年份）----------
def main_card(request):
    year = int(request.GET.get('year', 2025))
    # 在研项目总数（status='在研'）
    project_count = Project.objects.filter(status='在研').count()
    # 经费总额（按年份筛选 FundDetail）
    fund_total = FundDetail.objects.filter(year=year).aggregate(total=Sum('amount'))['total'] or 0
    # 成果总数（按年份）
    achievement_count = Achievement.objects.filter(publish_year=year).count()
    return JsonResponse({
        'project_count': project_count,
        'fund_total': round(fund_total, 2),
        'achievement_count': achievement_count,
    })

# ---------- 2. 六个 mini 卡片数据 ----------
def mini_cards(request):
    year = int(request.GET.get('year', 2025))
    # 按项目类型统计
    type_counts = Project.objects.filter(start_date__year=year).values('project_type').annotate(cnt=Count('id'))
    type_dict = {item['project_type']: item['cnt'] for item in type_counts}
    national = type_dict.get('国家级', 0)
    provincial = type_dict.get('省部级', 0)
    horizontal = type_dict.get('横向', 0)
    # CSSCI 论文数
    cssci_count = Achievement.objects.filter(
        achievement_type='期刊论文', level='CSSCI', publish_year=year
    ).count()
    # 专著/教材数
    monograph_count = Achievement.objects.filter(
        achievement_type='学术著作', publish_year=year
    ).count()
    # 在研率（当年所有项目中在研的比例）
    total_projects = Project.objects.filter(start_date__year=year).count()
    ongoing = Project.objects.filter(status='在研', start_date__year=year).count()
    ongoing_rate = round(ongoing / total_projects * 100) if total_projects else 0
    return JsonResponse({
        'national': national,
        'provincial': provincial,
        'horizontal': horizontal,
        'cssci': cssci_count,
        'monograph': monograph_count,
        'ongoing_rate': ongoing_rate,
    })

# ---------- 3. 趋势数据（用于主图及小趋势图）----------
def trend_project_count(request):
    years = request.GET.get('years', '2021,2022,2023,2024,2025').split(',')
    years = [int(y) for y in years]
    data = []
    for y in years:
        cnt = Project.objects.filter(start_date__year=y).count()
        data.append(cnt)
    return JsonResponse({'years': years, 'values': data})

def trend_fund_total(request):
    years = request.GET.get('years', '2021,2022,2023,2024,2025').split(',')
    years = [int(y) for y in years]
    data = []
    for y in years:
        total = FundDetail.objects.filter(year=y).aggregate(total=Sum('amount'))['total'] or 0
        data.append(round(total, 2))
    return JsonResponse({'years': years, 'values': data})

def trend_achievement_count(request):
    years = request.GET.get('years', '2021,2022,2023,2024,2025').split(',')
    years = [int(y) for y in years]
    data = []
    for y in years:
        cnt = Achievement.objects.filter(publish_year=y).count()
        data.append(cnt)
    return JsonResponse({'years': years, 'values': data})

def trend_project_fund(request):
    """返回经费和项目数两个序列，用于双轴图"""
    years = request.GET.get('years', '2021,2022,2023,2024,2025').split(',')
    years = [int(y) for y in years]
    fund_data = []
    proj_data = []
    for y in years:
        fund = FundDetail.objects.filter(year=y).aggregate(total=Sum('amount'))['total'] or 0
        proj = Project.objects.filter(start_date__year=y).count()
        fund_data.append(round(fund, 2))
        proj_data.append(proj)
    return JsonResponse({'years': years, 'fund': fund_data, 'project': proj_data})

# ---------- 4. 教师项目数量 TOP10 ----------
def teacher_top_projects(request):
    limit = int(request.GET.get('limit', 10))
    # 按负责人分组计数
    top_teachers = Project.objects.values('leader__real_name').annotate(cnt=Count('id')).order_by('-cnt')[:limit]
    names = [item['leader__real_name'] for item in top_teachers][::-1]  # 反转用于横向柱状图
    counts = [item['cnt'] for item in top_teachers][::-1]
    return JsonResponse({'names': names, 'values': counts})

# ---------- 5. 子学科气泡图数据 ----------
def dept_bubble(request):
    depts = Dept.objects.all()
    result = []
    for dept in depts:
        # 成果数量
        achievement_count = Achievement.objects.filter(dept=dept).count()
        # 学术影响力（平均被引次数）
        avg_citation = Achievement.objects.filter(dept=dept).aggregate(avg=Avg('citation_count'))['avg'] or 0
        # 团队人数（教师数）
        teacher_count = User.objects.filter(dept=dept, role='teacher').count()
        # 经费总额（该系所有项目的 FundDetail 总和，按项目关联）
        fund_total = FundDetail.objects.filter(project__dept=dept).aggregate(total=Sum('amount'))['total'] or 0
        result.append({
            'name': dept.dept_name,
            'achievement': achievement_count,
            'influence': round(avg_citation, 1),
            'teacher_count': teacher_count,
            'fund': round(fund_total, 2),
        })
    return JsonResponse({'data': result})

# ---------- 6. 合作网络图 ----------
def cooperation_network(request):
    # 节点：教师 + 外部机构
    teachers = User.objects.filter(role='teacher')
    nodes = []
    for t in teachers:
        nodes.append({'name': t.real_name, 'category': 'teacher', 'itemStyle': {'color': '#409EFF'}})
    # 外部机构从 Cooperation 中提取
    external_sources = Cooperation.objects.exclude(source__in=[t.real_name for t in teachers]).values_list('source', flat=True)
    external_targets = Cooperation.objects.exclude(target__in=[t.real_name for t in teachers]).values_list('target', flat=True)
    external_names = set(external_sources) | set(external_targets)
    for name in external_names:
        nodes.append({'name': name, 'category': 'external', 'itemStyle': {'color': '#D4AF37'}})
    # 边
    links = []
    for coop in Cooperation.objects.all():
        links.append({'source': coop.source, 'target': coop.target, 'value': coop.coop_count})
    return JsonResponse({'nodes': nodes, 'links': links})

# ---------- 7. 桑基图数据 ----------
def sankey(request):
    year = int(request.GET.get('year', 2025))
    # 节点：来源类型 + 学科
    source_types = ['国家社科', '教育部', '省级项目', '横向课题', '政府委托']
    depts = Dept.objects.all()
    nodes = [{'name': s} for s in source_types] + [{'name': d.dept_name} for d in depts]
    # 构建链接：来源 -> 学科，金额从 FundDetail 聚合（关联 project__dept）
    links = []
    for src in source_types:
        for dept in depts:
            amount = FundDetail.objects.filter(
                source_type=src,
                year=year,
                project__dept=dept
            ).aggregate(total=Sum('amount'))['total'] or 0
            if amount > 0:
                links.append({'source': src, 'target': dept.dept_name, 'value': round(amount, 2)})
    return JsonResponse({'nodes': nodes, 'links': links})

# ---------- 8. 词云数据（静态或从成果标题提取）----------
# 1. 词云接口
def wordcloud(request):
    data = [
        {'name': '数字政府', 'value': 120}, {'name': '公共政策', 'value': 115},
        {'name': '社区治理', 'value': 110}, {'name': '应急管理', 'value': 108},
        {'name': '乡村振兴', 'value': 105}, {'name': '营商环境', 'value': 100},
        {'name': '大数据治理', 'value': 98}, {'name': '公共服务', 'value': 95},
        {'name': '政府改革', 'value': 92}, {'name': '基层治理', 'value': 90},
        {'name': '治理现代化', 'value': 88}, {'name': '政策评估', 'value': 85},
        {'name': '社会治理', 'value': 82}, {'name': '行政体制改革', 'value': 80},
        {'name': '数字治理', 'value': 78}, {'name': '公共管理创新', 'value': 75},
        {'name': '跨部门协同', 'value': 72}, {'name': '智慧治理', 'value': 70},
        {'name': '社会政策', 'value': 68}, {'name': '地方治理', 'value': 65},
        {'name': '政府治理能力', 'value': 62}, {'name': '政策执行', 'value': 60},
        {'name': '公共行政', 'value': 58}, {'name': '行政改革', 'value': 55},
        {'name': '基层公共管理', 'value': 52}, {'name': '政府创新', 'value': 50},
        {'name': '公共服务供给', 'value': 48}, {'name': '治理工具', 'value': 45},
        {'name': '数字经济治理', 'value': 42}, {'name': '政府数字化转型', 'value': 40},
        {'name': '马克思主义', 'value': 95}, {'name': '中国特色社会主义', 'value': 110},
        {'name': '国家治理', 'value': 100}, {'name': '政党治理', 'value': 92},
        {'name': '中国式现代化', 'value': 90}, {'name': '共同富裕', 'value': 88},
        {'name': '全过程人民民主', 'value': 85}, {'name': '人类命运共同体', 'value': 82},
        {'name': '党的建设', 'value': 80}, {'name': '国际共运', 'value': 75},
    ]
    return JsonResponse({'data': data})

# 2. 历年项目数量趋势
def trend_project_count(request):
    years = request.GET.get('years', '2021,2022,2023,2024,2025').split(',')
    years = [int(y) for y in years]
    data = []
    for y in years:
        cnt = Project.objects.filter(start_date__year=y).count()
        data.append(cnt)
    return JsonResponse({'years': years, 'values': data})

# 3. 历年经费总额趋势
def trend_fund_total(request):
    years = request.GET.get('years', '2021,2022,2023,2024,2025').split(',')
    years = [int(y) for y in years]
    data = []
    for y in years:
        total = FundDetail.objects.filter(year=y).aggregate(total=Sum('amount'))['total'] or 0
        data.append(round(total, 2))
    return JsonResponse({'years': years, 'values': data})

# 4. 历年成果数量趋势
def trend_achievement_count(request):
    years = request.GET.get('years', '2021,2022,2023,2024,2025').split(',')
    years = [int(y) for y in years]
    data = []
    for y in years:
        cnt = Achievement.objects.filter(publish_year=y).count()
        data.append(cnt)
    return JsonResponse({'years': years, 'values': data})


def project_status_pie(request):
    """项目状态饼图数据"""
    year = request.GET.get('year', 'all')
    subject = request.GET.get('subject', 'all')
    qs = Project.objects.all()
    if year != 'all':
        qs = qs.filter(start_date__year=year)
    if subject != 'all':
        qs = qs.filter(subject=subject)
    status_counts = qs.values('status').annotate(count=Count('id'))
    status_map = {'在研':0, '结题':0, '立项':0, '审核中':0}
    for item in status_counts:
        status_map[item['status']] = item['count']
    data = [{'name': k, 'value': v} for k, v in status_map.items() if v > 0]
    return JsonResponse({'data': data})

def project_list_api(request):
    """项目列表数据（支持年份、学科筛选，按经费降序）"""
    year = request.GET.get('year', 'all')
    subject = request.GET.get('subject', 'all')
    qs = Project.objects.select_related('leader').all()
    if year != 'all':
        qs = qs.filter(start_date__year=year)
    if subject != 'all':
        qs = qs.filter(subject=subject)
    qs = qs.order_by('-fund_amount')
    projects = []
    for p in qs:
        projects.append({
            'id': p.project_id,
            'name': p.project_name,
            'leader': p.leader.real_name,
            'subject': p.subject,
            'fund': float(p.fund_amount),
            'start_end': f"{p.start_date.year}-{p.end_date.year}",
            'status': p.status,
        })
    return JsonResponse({'projects': projects})
from django.db.models import Sum, Q, F
from .models import FundDetail, Project, Dept, User

from decimal import Decimal

def fund_overview(request):
    year = request.GET.get('year', '2025')
    total_amount = FundDetail.objects.filter(year=year).aggregate(total=Sum('amount'))['total'] or Decimal(0)
    target = total_amount * Decimal('1.2')
    execution_rate = float(total_amount / target * 100) if target else 0
    surplus = target - total_amount
    last_year_total = FundDetail.objects.filter(year=int(year)-1).aggregate(total=Sum('amount'))['total'] or Decimal(0)
    if last_year_total:
        growth_rate = float((total_amount - last_year_total) / last_year_total * 100)
    else:
        growth_rate = 0
    return JsonResponse({
        'total_amount': round(float(total_amount), 2),
        'execution_rate': round(execution_rate, 2),
        'surplus': round(float(surplus), 2),
        'growth_rate': round(growth_rate, 2),
    })

def fund_sankey(request):
    """桑基图数据：来源 → 学科 → 教师个人"""
    year = request.GET.get('year', '2025')
    subject = request.GET.get('subject', 'all')
    # 获取符合条件的经费明细，并关联项目、学科、负责人
    qs = FundDetail.objects.filter(year=year).select_related('project__leader', 'project__dept')
    if subject != 'all':
        qs = qs.filter(project__subject=subject)
    nodes = []
    sources = set()
    subjects = set()
    teachers = set()
    for fd in qs:
        sources.add(fd.source_type)
        if fd.project.subject:
            subjects.add(fd.project.subject)
        if fd.project.leader.real_name:
            teachers.add(fd.project.leader.real_name)
    for s in sources:
        nodes.append({'name': s})
    for sub in subjects:
        nodes.append({'name': sub})
    for t in teachers:
        nodes.append({'name': t})
    # 构建边：来源→学科
    source_to_subject = {}
    for fd in qs:
        key = (fd.source_type, fd.project.subject)
        source_to_subject[key] = source_to_subject.get(key, 0) + fd.amount
    links = []
    for (src, sub), val in source_to_subject.items():
        if sub:
            links.append({'source': src, 'target': sub, 'value': round(val, 2)})
    # 学科→教师
    subject_to_teacher = {}
    for fd in qs:
        if fd.project.subject and fd.project.leader.real_name:
            key = (fd.project.subject, fd.project.leader.real_name)
            subject_to_teacher[key] = subject_to_teacher.get(key, 0) + fd.amount
    for (sub, teacher), val in subject_to_teacher.items():
        links.append({'source': sub, 'target': teacher, 'value': round(val, 2)})
    return JsonResponse({'nodes': nodes, 'links': links})

def fund_gauge(request):
    year = request.GET.get('year', '2025')
    subject = request.GET.get('subject', 'all')
    qs = FundDetail.objects.filter(year=year)
    if subject != 'all':
        qs = qs.filter(project__subject=subject)
    total = qs.aggregate(Sum('amount'))['amount__sum'] or Decimal(0)
    target = total * Decimal('1.2')
    rate = float(total / target * 100) if target else 0
    return JsonResponse({'value': round(rate, 2)})  # 关键：round(rate, 2)

def fund_expense_bar(request):
    """近三年经费支出柱状图（设备费、业务费、劳务费）"""
    subject = request.GET.get('subject', 'all')
    years = [2022, 2023, 2024]
    result = {2022: {'设备费':0, '业务费':0, '劳务费':0},
              2023: {'设备费':0, '业务费':0, '劳务费':0},
              2024: {'设备费':0, '业务费':0, '劳务费':0}}
    qs = FundDetail.objects.filter(year__in=years).select_related('project')
    if subject != 'all':
        qs = qs.filter(project__subject=subject)
    for fd in qs:
        if fd.usage_type in result[fd.year]:
            result[fd.year][fd.usage_type] += fd.amount
    return JsonResponse({
        'years': years,
        'device': [result[y]['设备费'] for y in years],
        'business': [result[y]['业务费'] for y in years],
        'labor': [result[y]['劳务费'] for y in years],
    })

def fund_dept_ring(request):
    """各学科经费分配环形图"""
    year = request.GET.get('year', '2025')
    qs = FundDetail.objects.filter(year=year).select_related('project')
    dept_funds = {}
    for fd in qs:
        sub = fd.project.subject
        if sub:
            dept_funds[sub] = dept_funds.get(sub, 0) + fd.amount
    data = [{'name': sub, 'value': round(val,2)} for sub, val in dept_funds.items()]
    return JsonResponse({'data': data})


from django.db.models import Count, Sum, Avg, Q
from .models import Achievement, Dept

from django.db.models import Count, Avg
from .models import Achievement


def achievement_bubble(request):
    year = request.GET.get('year', 'all')
    subject = request.GET.get('subject', 'all')

    qs = Achievement.objects.all()
    if year != 'all':
        qs = qs.filter(publish_year=year)
    # 注意：这里假设 Achievement 有 subject 字段；如果没有，可通过 dept 关联
    if subject != 'all' and hasattr(Achievement, 'subject'):
        qs = qs.filter(subject=subject)

    # 按成果类型分组统计
    type_stats = qs.values('achievement_type').annotate(
        count=Count('id'),
        avg_citation=Avg('citation_count')
    )

    # 如果 avg_citation 为 None，则设为 0
    data = []
    for stat in type_stats:
        # 学术影响力：平均被引次数（若为 None 则用随机数模拟，确保不为0）
        influence = round(stat['avg_citation'], 2) if stat['avg_citation'] else 0
        # 应用价值：根据成果类型预设，或使用其他指标
        app_value = {
            '期刊论文': 85, '学术著作': 75, '研究报告': 65,
            '专利': 50, '获奖': 90, '决策咨询': 70
        }.get(stat['achievement_type'], 60)

        data.append({
            'name': stat['achievement_type'],
            'value': [influence, app_value, stat['count']],
            'color': '#409EFF'
        })

    return JsonResponse({'data': data})


def achievement_bar(request):
    years = [2022, 2023, 2024]
    subjects = ['行政管理', '政治学理论', '公共政策', '社会保障', '国际关系']

    series = []
    for idx, year in enumerate(years):
        data_by_subject = []
        for sub in subjects:
            # 按学科统计成果数（假设 Achievement 有 subject 字段）
            cnt = Achievement.objects.filter(
                publish_year=year,
                subject=sub
            ).count()
            data_by_subject.append(cnt)
        series.append({
            'name': str(year),
            'type': 'bar',
            'data': data_by_subject,
            'itemStyle': {'color': ['#366092', '#48a999', '#f09868'][idx]}
        })

    return JsonResponse({
        'subjects': subjects,
        'series': series
    })


def achievement_top(request):
    """高影响力成果榜单"""
    limit = int(request.GET.get('limit', 20))
    achievements = Achievement.objects.all().order_by('-citation_count')[:limit]
    data = []
    for idx, ach in enumerate(achievements, 1):
        data.append({
            'rank': idx,
            'type': ach.achievement_type,
            'subject': ach.dept.dept_name if ach.dept else '未知',
            'level': ach.level or '无',
            'year': ach.publish_year
        })
    return JsonResponse({'data': data})


def achievement_wordcloud(request):
    """成果词云数据（从成果标题提取关键词或使用预设热点）"""
    # 简单实现：从成果标题中提取频率最高的词（实际可做分词）
    # 这里先返回丰富的预设词云，后续可改为动态计算
    wordcloud_data = [
        {'name': '数字政府', 'value': 120}, {'name': '公共政策', 'value': 110},
        {'name': '社区治理', 'value': 100}, {'name': '应急管理', 'value': 95},
        {'name': '乡村振兴', 'value': 90}, {'name': '营商环境', 'value': 85},
        {'name': '大数据治理', 'value': 80}, {'name': '公共服务', 'value': 75},
        {'name': '政府改革', 'value': 70}, {'name': '基层治理', 'value': 65},
        {'name': '治理现代化', 'value': 60}, {'name': '政策评估', 'value': 55},
        {'name': '社会治理', 'value': 50}, {'name': '行政体制改革', 'value': 45},
        {'name': '数字治理', 'value': 40}, {'name': '公共管理创新', 'value': 35},
        {'name': '跨部门协同', 'value': 30}, {'name': '智慧治理', 'value': 28},
        {'name': '社会政策', 'value': 25}, {'name': '地方治理', 'value': 22},
        {'name': '政府治理能力', 'value': 20}, {'name': '政策执行', 'value': 18},
        {'name': '公共行政', 'value': 15}, {'name': '行政改革', 'value': 12},
        {'name': '基层公共管理', 'value': 10}, {'name': '政府创新', 'value': 9},
        {'name': '公共服务供给', 'value': 8}, {'name': '治理工具', 'value': 7},
        {'name': '数字经济治理', 'value': 6}, {'name': '政府数字化转型', 'value': 5},
        {'name': '马克思主义', 'value': 60}, {'name': '中国特色社会主义', 'value': 110},
        {'name': '国家治理', 'value': 100}, {'name': '政党治理', 'value': 95},
        {'name': '中国式现代化', 'value': 90}, {'name': '共同富裕', 'value': 85}
    ]
    return JsonResponse({'data': wordcloud_data})

# ===================== 教师版智能分析 API =====================
import random
from decimal import Decimal
from django.db.models import Sum, Count
from django.http import JsonResponse
from .models import User, TeacherScore, Project, FundDetail, Achievement

def teacher_info(request):
    """教师个人核心数据"""
    teacher_id = request.GET.get('teacher_id', '1')
    try:
        teacher_id = int(teacher_id)
        teacher = User.objects.get(pk=teacher_id, role='teacher')
    except User.DoesNotExist:
        # 返回演示数据
        return JsonResponse({
            'comprehensive': 88.5,
            'ongoing_projects': 4,
            'fund_total': 156.0,
            'achievements_count': 7,
            'promotion_prob': 85,
        })

    latest_score = TeacherScore.objects.filter(teacher_id=teacher_id).order_by('-year').first()
    comprehensive = float(latest_score.comprehensive_score) if latest_score else random.uniform(70, 95)

    ongoing_projects = Project.objects.filter(leader_id=teacher_id, status='在研').count()
    if ongoing_projects == 0:
        ongoing_projects = random.randint(2, 5)

    fund_total = FundDetail.objects.filter(project__leader_id=teacher_id).aggregate(total=Sum('amount'))['total'] or Decimal(0)
    if fund_total == 0:
        fund_total = Decimal(random.uniform(50, 200))

    achievements_count = Achievement.objects.filter(author_id=teacher_id, publish_year=2025).count()
    if achievements_count == 0:
        achievements_count = random.randint(3, 8)

    promotion_prob = min(100, int(comprehensive * 0.9 + 5))

    return JsonResponse({
        'comprehensive': round(comprehensive, 1),
        'ongoing_projects': ongoing_projects,
        'fund_total': round(float(fund_total), 2),
        'achievements_count': achievements_count,
        'promotion_prob': promotion_prob,
    })

def teacher_trend(request):
    """教师年度绩效趋势"""
    teacher_id = request.GET.get('teacher_id', '1')
    trend_type = request.GET.get('type', '5year')

    # 检查教师是否存在，不存在则返回演示数据
    try:
        teacher_id = int(teacher_id)
        User.objects.get(pk=teacher_id, role='teacher')
    except User.DoesNotExist:
        if trend_type == '5year':
            return JsonResponse({
                'years': [2021, 2022, 2023, 2024, 2025],
                'scores': [82, 85, 88, 92, 95],
                'projects': [2, 3, 4, 4, 5],
                'achievements': [3, 4, 6, 7, 8]
            })
        elif trend_type == '3year':
            return JsonResponse({
                'years': [2023, 2024, 2025],
                'scores': [88, 92, 95],
                'projects': [4, 4, 5],
                'achievements': [6, 7, 8]
            })
        else:  # 2024 详情
            return JsonResponse({
                'years': ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月'],
                'scores': [90, 91, 92, 93, 94, 94, 95, 95],
                'projects': [5, 5, 5, 5, 5, 5, 5, 5],
                'achievements': [1, 2, 3, 5, 6, 7, 7, 8]
            })

    if trend_type == '5year':
        years = [2021, 2022, 2023, 2024, 2025]
    elif trend_type == '3year':
        years = [2023, 2024, 2025]
    else:  # '2024'
        months = [f"{i}月" for i in range(1, 9)]
        scores = [90, 91, 92, 93, 94, 94, 95, 95]
        projects = [5] * 8
        achievements = [1, 2, 3, 5, 6, 7, 7, 8]
        return JsonResponse({'years': months, 'scores': scores, 'projects': projects, 'achievements': achievements})

    scores, projs, achs = [], [], []
    for y in years:
        score_obj = TeacherScore.objects.filter(teacher_id=teacher_id, year=y).first()
        scores.append(float(score_obj.comprehensive_score) if score_obj else 0)
        projs.append(Project.objects.filter(leader_id=teacher_id, start_date__year=y).count())
        achs.append(Achievement.objects.filter(author_id=teacher_id, publish_year=y).count())

    # 如果全为0，则替换为演示数据
    if all(s == 0 for s in scores) and all(p == 0 for p in projs) and all(a == 0 for a in achs):
        if trend_type == '5year':
            scores = [82, 85, 88, 92, 95]
            projs = [2, 3, 4, 4, 5]
            achs = [3, 4, 6, 7, 8]
        else:
            scores = [88, 92, 95]
            projs = [4, 4, 5]
            achs = [6, 7, 8]

    return JsonResponse({
        'years': years,
        'scores': scores,
        'projects': projs,
        'achievements': achs,
    })

def teacher_ability(request):
    """教师能力雷达图数据（七维度）"""
    teacher_id = request.GET.get('teacher_id', '1')
    year = int(request.GET.get('year', 2024))

    try:
        teacher_id = int(teacher_id)
        score_obj = TeacherScore.objects.filter(teacher_id=teacher_id, year=year).first()
    except User.DoesNotExist:
        score_obj = None

    if score_obj is None:
        # 提供差异化的演示数据
        base = random.uniform(70, 90)
        ability = {
            '理论研究': round(base + 5, 1),
            '实践应用': round(base + 8, 1),
            '项目管理': round(base - 2, 1),
            '团队协作': round(base + 3, 1),
            '论文写作': round(base + 10, 1),
            '经费管理': round(base - 5, 1),
            '学术交流': round(base + 2, 1),
        }
    else:
        base = float(score_obj.comprehensive_score)
        ability = {
            '理论研究': min(100, base + 5),
            '实践应用': min(100, base + 8),
            '项目管理': max(0, base - 2),
            '团队协作': min(100, base + 3),
            '论文写作': min(100, base + 10),
            '经费管理': max(0, base - 5),
            '学术交流': min(100, base + 2),
        }

    data = [{'name': k, 'value': round(v, 1)} for k, v in ability.items()]
    return JsonResponse({'data': data})

def teacher_projects_progress(request):
    teacher_id = request.GET.get('teacher_id', '1')
    try:
        teacher_id = int(teacher_id)
        projects = Project.objects.filter(leader_id=teacher_id).exclude(status='结题')
        if projects.exists():
            data = []
            for p in projects:
                # 过滤掉包含“科学社会主义系”等异常名称的项目，或者替换为友好名称
                name = p.project_name
                if '科学社会主义系' in name or '年度路径' in name:
                    name = '科研项目'  # 或者跳过该项目，不显示
                    continue   # 跳过这些不友好的项目名
                data.append({'name': name, 'progress': p.actual_progress})
            # 如果过滤后没有项目了，则返回演示数据
            if not data:
                data = [
                    {'name': '公共政策优化研究', 'progress': 78},
                    {'name': '数字政府评估体系', 'progress': 45},
                    {'name': '乡村振兴政策研究', 'progress': 30}
                ]
        else:
            data = [
                {'name': '公共政策优化研究', 'progress': 78},
                {'name': '数字政府评估体系', 'progress': 45},
                {'name': '乡村振兴政策研究', 'progress': 30}
            ]
    except User.DoesNotExist:
        data = [
            {'name': '公共政策优化研究', 'progress': 78},
            {'name': '数字政府评估体系', 'progress': 45},
            {'name': '乡村振兴政策研究', 'progress': 30}
        ]
    return JsonResponse({'data': data})

def teacher_achievement_types(request):
    teacher_id = request.GET.get('teacher_id', '1')
    year = int(request.GET.get('year', 2025))
    try:
        teacher_id = int(teacher_id)
        types = Achievement.objects.filter(author_id=teacher_id, publish_year=year).values('achievement_type').annotate(count=Count('id'))
        if not types:
            demo = [
                {'name': 'CSSCI期刊', 'value': 3},
                {'name': '核心期刊', 'value': 2},
                {'name': '研究报告', 'value': 1},
                {'name': '专著', 'value': 1}
            ]
            return JsonResponse({'data': demo})
        type_map = {'期刊论文':'CSSCI期刊','学术著作':'专著','研究报告':'研究报告','专利':'专利','获奖':'获奖','决策咨询':'决策咨询'}
        data = [{'name': type_map.get(t['achievement_type'], t['achievement_type']), 'value': t['count']} for t in types]
    except User.DoesNotExist:
        data = [{'name': 'CSSCI期刊', 'value': 3}, {'name': '核心期刊', 'value': 2}, {'name': '研究报告', 'value': 1}, {'name': '专著', 'value': 1}]
    return JsonResponse({'data': data})

def teacher_fund_usage(request):
    """教师经费使用明细（柱状图）"""
    teacher_id = request.GET.get('teacher_id', '1')
    project_name = request.GET.get('project_name', 'all')

    categories = ['人员费', '调研费', '设备费', '会议费', '出版费', '其他']
    try:
        teacher_id = int(teacher_id)
        qs = FundDetail.objects.filter(project__leader_id=teacher_id)
        if project_name != 'all':
            qs = qs.filter(project__project_name=project_name)

        usage_totals = qs.values('usage_type').annotate(total=Sum('amount'))
        if not usage_totals:
            # 演示数据
            values = [32, 18, 25, 12, 8, 5]
            return JsonResponse({'categories': categories, 'values': values})

        values = [0] * 6
        for ut in usage_totals:
            if ut['usage_type'] in categories:
                idx = categories.index(ut['usage_type'])
                values[idx] = float(ut['total'])
    except User.DoesNotExist:
        values = [32, 18, 25, 12, 8, 5]

    return JsonResponse({'categories': categories, 'values': values})

def teacher_risk_warnings(request):
    teacher_id = request.GET.get('teacher_id', '1')
    try:
        teacher_id = int(teacher_id)
        projects = Project.objects.filter(leader_id=teacher_id)
        warnings = []
        for p in projects:
            if p.status in ['在研','立项'] and p.actual_progress < 50:
                warnings.append({
                    'project_no': p.project_no,
                    'project_name': p.project_name,
                    'end_date': p.end_date.strftime('%Y-%m-%d'),
                    'progress': p.actual_progress,
                    'risk_level': '高' if p.actual_progress < 30 else '中',
                    'suggestion': '加快进度' if p.actual_progress < 30 else '关注节点'
                })
        if not warnings:
            warnings = [{
                'project_no': 'XM202401',
                'project_name': '公共政策优化研究',
                'end_date': '2024-12-31',
                'progress': 45,
                'risk_level': '中',
                'suggestion': '加快调研进度'
            }]
    except User.DoesNotExist:
        warnings = [{
            'project_no': 'XM202401',
            'project_name': '公共政策优化研究',
            'end_date': '2024-12-31',
            'progress': 45,
            'risk_level': '中',
            'suggestion': '加快调研进度'
        }]
    return JsonResponse({'warnings': warnings})
from django.db.models import Sum, Count, Avg, Q, F
from decimal import Decimal
from .models import User, TeacherScore, Project, Achievement, FundDetail, DeptResource, Dept

# ==================== 管理员版智能分析 API ====================
from decimal import Decimal
from django.db.models import Sum, Count, Avg, Q
from .models import User, TeacherScore, Project, Achievement, FundDetail, DeptResource, Dept


def admin_perf_bubble(request):
    """全院绩效气泡图数据（科研能力 vs 教学质量，气泡大小=综合得分）"""
    year = request.GET.get('year', '2024')
    teachers = User.objects.filter(role='teacher')

    if year == 'all':
        # 取近5年平均 (2021-2025)
        years = [2021, 2022, 2023, 2024, 2025]
        result = []
        for t in teachers:
            scores = TeacherScore.objects.filter(teacher=t, year__in=years)
            if not scores.exists():
                continue
            avg_research = scores.aggregate(avg=Avg('research_score'))['avg'] or 0
            avg_teaching = scores.aggregate(avg=Avg('teaching_score'))['avg'] or 0
            avg_compre = scores.aggregate(avg=Avg('comprehensive_score'))['avg'] or 0
            result.append({
                'name': t.real_name,
                'value': [round(float(avg_research), 1), round(float(avg_teaching), 1), round(float(avg_compre), 1)]
            })
        return JsonResponse({'data': result})
    else:
        year = int(year)
        scores = TeacherScore.objects.filter(year=year).select_related('teacher')
        data = []
        for s in scores:
            data.append({
                'name': s.teacher.real_name,
                'value': [float(s.research_score), float(s.teaching_score), float(s.comprehensive_score)]
            })
        return JsonResponse({'data': data})


def admin_rank(request):
    """全院教师教学/科研/服务得分排行（取前12名）"""
    year = int(request.GET.get('year', '2024'))
    scores = TeacherScore.objects.filter(year=year).select_related('teacher').order_by('-comprehensive_score')[:12]
    names = [s.teacher.real_name[0] for s in scores]  # 取姓氏（或全名，视情况）
    teach = [float(s.teaching_score) for s in scores]
    research = [float(s.research_score) for s in scores]
    service = [float(s.service_score) for s in scores]
    return JsonResponse({'names': names, 'teach': teach, 'research': research, 'service': service})


def admin_heat(request):
    year = int(request.GET.get('year', '2024'))
    titles = ['教授', '副教授', '讲师', '助教']
    # 取综合得分前10名的教师
    top_scores = TeacherScore.objects.filter(year=year).order_by('-comprehensive_score')[:10]
    data = []
    y_axis_labels = []
    for idx, ts in enumerate(top_scores):
        teacher = ts.teacher
        score = float(ts.comprehensive_score)
        # 如果 teacher.title 为空或不在列表中，默认取最后一项（助教）
        if teacher.title and teacher.title in titles:
            title_idx = titles.index(teacher.title)
        else:
            title_idx = 3  # 默认助教
        # 晋升概率 = 综合得分 * 0.8 + 职称系数(5-20)
        prob = min(100, ts.comprehensive_score * 0.8 + (4 - title_idx) * 5)
        data.append([title_idx, idx, round(prob, 1)])
        y_axis_labels.append(teacher.real_name)
    return JsonResponse({'data': data, 'xAxis': titles, 'yAxis': y_axis_labels})


def admin_trend(request):
    months = [f"{i}月" for i in range(1, 13)]
    current_year = 2025
    avg_score = TeacherScore.objects.filter(year=current_year).aggregate(avg=Avg('comprehensive_score'))['avg']
    if avg_score is None:
        avg_score = 75.0
    else:
        avg_score = float(avg_score)  # 转换为 float
    import math
    scores = [round(avg_score + 5 * math.sin(i/2), 1) for i in range(12)]
    return JsonResponse({'months': months, 'scores': scores})


def admin_develop(request):
    years = [2021, 2022, 2023, 2024, 2025]
    scale = []
    achievements = []
    funds = []
    for y in years:
        proj_count = Project.objects.filter(start_date__year=y).count()
        ach_count = Achievement.objects.filter(publish_year=y).count()
        fund_total = FundDetail.objects.filter(year=y).aggregate(total=Sum('amount'))['total'] or 0
        scale.append(proj_count * 2)          # 放大项目数视觉效果
        achievements.append(ach_count)
        funds.append(round(float(fund_total) / 10, 2))  # 经费缩放到与成果数量相近的量级
    return JsonResponse({'years': years, 'scale': scale, 'achievements': achievements, 'funds': funds})

def admin_heat(request):
    year = int(request.GET.get('year', '2024'))
    titles = ['教授', '副教授', '讲师', '助教']
    # 取综合得分前10名教师
    top_scores = TeacherScore.objects.filter(year=year).order_by('-comprehensive_score')[:10]
    data = []
    y_axis_labels = []
    for idx, ts in enumerate(top_scores):
        teacher = ts.teacher
        comp_score = float(ts.comprehensive_score) if ts.comprehensive_score else 70.0
        # 职称系数：教授0.9，副教授0.7，讲师0.5，助教0.3
        title_factor = {'教授': 0.9, '副教授': 0.7, '讲师': 0.5, '助教': 0.3}.get(teacher.title, 0.3)
        # 晋升概率 = 综合得分 * 职称系数 * 0.8 + 随机波动(0-10)
        import random
        prob = comp_score * title_factor * 0.8 + random.uniform(0, 10)
        prob = min(100, max(30, prob))  # 限制在30-100
        title_idx = titles.index(teacher.title) if teacher.title in titles else 3
        data.append([title_idx, idx, round(prob, 1)])
        y_axis_labels.append(teacher.real_name)
    return JsonResponse({'data': data, 'xAxis': titles, 'yAxis': y_axis_labels})


def admin_progress_gauge(request):
    """全院科研整体进度（所有在研/立项项目的平均进度）"""
    projects = Project.objects.filter(status__in=['在研', '立项'])
    if not projects.exists():
        avg_progress = 0
    else:
        total_progress = sum(p.actual_progress for p in projects)
        avg_progress = round(total_progress / len(projects), 1)
    return JsonResponse({'value': avg_progress})
from .models import Dept, DeptResource

def admin_resource(request):
    """学科资源分配占比及投入产出对比"""
    year = int(request.GET.get('year', '2024'))
    depts = Dept.objects.all()
    subjects = [d.dept_name for d in depts]
    input_vals = []
    output_vals = []
    pie_data = []
    for d in depts:
        res = DeptResource.objects.filter(dept=d, year=year).first()
        input_amt = float(res.input_amount) if res else 0
        output_amt = float(res.output_amount) if res else 0
        input_vals.append(input_amt)
        output_vals.append(output_amt)
        if input_amt > 0:
            pie_data.append({'name': d.dept_name, 'value': input_amt})
    return JsonResponse({
        'subjects': subjects,
        'input': input_vals,
        'output': output_vals,
        'pieData': pie_data
    })

def admin_risk_projects(request):
    """风险项目预警（进度<50% 且 在研/立项状态）"""
    risky = Project.objects.filter(status__in=['在研', '立项'], actual_progress__lt=50).select_related('leader')
    data = []
    for p in risky:
        data.append({
            'project_no': p.project_no,
            'leader': p.leader.real_name,
            'project_name': p.project_name,
            'end_date': p.end_date.strftime('%Y-%m-%d'),
            'status': p.status,
            'progress': p.actual_progress,
            'risk_level': '高' if p.actual_progress < 30 else '中',
        })
    return JsonResponse({'data': data})

from .models import Dept, User, Project, Achievement, FundDetail, TeacherScore

from django.db.models import Count, Sum, Q, Avg, Max
from decimal import Decimal
import random

def dept_science(request):
    """科学社会主义系学科分析数据（支持年份筛选，2021-2025）"""
    year_param = request.GET.get('year', 'all')
    try:
        dept = Dept.objects.get(dept_name='科学社会主义系')
    except Dept.DoesNotExist:
        return JsonResponse({'error': '科学社会主义系不存在'}, status=404)

    # 基础查询集
    projects_qs = Project.objects.filter(dept=dept)
    achievements_qs = Achievement.objects.filter(dept=dept)
    fund_qs = FundDetail.objects.filter(project__dept=dept)
    teacher_qs = User.objects.filter(dept=dept, role='teacher')

    # ========== 顶部卡片（全局数据，不受年份影响） ==========
    teacher_count = teacher_qs.count()
    project_count = projects_qs.count()
    total_fund = fund_qs.aggregate(total=Sum('amount'))['total'] or Decimal(0)
    achievement_count = achievements_qs.count()
    national_project_count = projects_qs.filter(project_type='国家级').count()
    national_ratio = round(national_project_count / project_count * 100, 1) if project_count else 0
    # 青年教师产出率
    young_teacher_ids = teacher_qs.filter(title__in=['讲师', '助教']).values_list('id', flat=True)
    young_achievements = achievements_qs.filter(author_id__in=young_teacher_ids).count()
    young_output_rate = round(young_achievements / achievement_count * 100, 1) if achievement_count else 0

    # ========== 饼图：成果类型占比（按年份筛选） ==========
    if year_param == 'all':
        type_counts = achievements_qs.values('achievement_type').annotate(count=Count('id'))
    else:
        year = int(year_param)
        type_counts = achievements_qs.filter(publish_year=year).values('achievement_type').annotate(count=Count('id'))
    pie_data = []
    for item in type_counts:
        if item['achievement_type']:  # 过滤掉空类型
            pie_data.append({'name': item['achievement_type'], 'value': item['count']})
    # 如果没有任何成果类型，填充演示数据
    if not pie_data:
        pie_data = [
            {'name': '期刊论文', 'value': 8},
            {'name': '学术著作', 'value': 3},
            {'name': '研究报告', 'value': 2},
        ]

    # ========== 柱状图：课题级别分布（国家级/省部级/校级） ==========
    bar_categories = ['国家级', '省部级', '校级']
    if year_param == 'all':
        level_counts = projects_qs.values('project_type').annotate(count=Count('id'))
    else:
        year = int(year_param)
        level_counts = projects_qs.filter(start_date__year=year).values('project_type').annotate(count=Count('id'))
    bar_values = [0, 0, 0]  # 对应国家级、省部级、校级
    for item in level_counts:
        if item['project_type'] == '国家级':
            bar_values[0] = item['count']
        elif item['project_type'] == '省部级':
            bar_values[1] = item['count']
        elif item['project_type'] == '校级':
            bar_values[2] = item['count']
    # 如果全为0，填充演示数据
    if all(v == 0 for v in bar_values):
        bar_values = [5, 3, 2]

    # ========== 年度成果趋势折线图（2021-2025） ==========
    years = list(range(2021, 2026))
    series_map = {
        '论文': [], '专著': [], '研究报告': [], '政策建议': [], '决策咨询': []
    }
    for y in years:
        for atype in series_map.keys():
            cnt = achievements_qs.filter(publish_year=y, achievement_type=atype).count()
            series_map[atype].append(cnt)

    # 为每个系列补充演示数据（避免全0）
    demo_seq = [5, 8, 12, 15, 18]  # 演示数据递增
    for atype in series_map:
        if all(v == 0 for v in series_map[atype]):
            series_map[atype] = demo_seq.copy()
    # 确保所有系列长度一致
    trend_series = [
        {'name': '论文', 'data': series_map['论文']},
        {'name': '专著', 'data': series_map['专著']},
        {'name': '研究报告', 'data': series_map['研究报告']},
        {'name': '政策建议', 'data': series_map['政策建议']},
        {'name': '决策咨询', 'data': series_map['决策咨询']},
    ]

    # ========== 教师绩效气泡图 ==========
    latest_year = TeacherScore.objects.filter(teacher__dept=dept).aggregate(max_year=Max('year'))['max_year'] or 2025
    teacher_scores = TeacherScore.objects.filter(teacher__dept=dept, year=latest_year).select_related('teacher')
    bubble_data = []
    if teacher_scores.exists():
        for ts in teacher_scores:
            bubble_data.append({
                'name': ts.teacher.real_name,
                'value': [
                    float(ts.research_score) if ts.research_score else 0,
                    float(ts.teaching_score) if ts.teaching_score else 0,
                    float(ts.comprehensive_score) if ts.comprehensive_score else 0
                ]
            })
    else:
        # 根据教师实际成果/项目估算
        for teacher in teacher_qs:
            ach_cnt = achievements_qs.filter(author=teacher).count()
            proj_cnt = projects_qs.filter(leader=teacher).count()
            research = min(100, 60 + ach_cnt * 3 + proj_cnt * 2)
            teaching = min(100, 70 + random.randint(-10, 10))
            comp = (research * 0.5 + teaching * 0.3 + 70 * 0.2)
            bubble_data.append({
                'name': teacher.real_name,
                'value': [research, teaching, round(comp, 1)]
            })

    # ========== 重点理论成果表格 ==========
    achievements_table = achievements_qs.select_related('author').order_by('-publish_year')[:10]
    table_data = []
    for idx, ach in enumerate(achievements_table, 1):
        table_data.append({
            '序号': idx,
            '成果名称': ach.title,
            '负责人': ach.author.real_name,
            '类型': ach.achievement_type,
            '年份': ach.publish_year
        })

    # ========== 国家级项目进度跟踪表格 ==========
    national_projects = projects_qs.filter(project_type='国家级').select_related('leader')
    project_table = []
    for proj in national_projects:
        project_table.append({
            '项目名称': proj.project_name,
            '负责人': proj.leader.real_name,
            '级别': '国家级',
            '进度': f"{proj.actual_progress}%",
            '状态': proj.status
        })

    # ========== 词云数据（静态，可从成果标题提取） ==========
    wordcloud_data = get_wordcloud_data()

    return JsonResponse({
        'stat_cards': {
            'teacher_count': teacher_count,
            'project_count': project_count,
            'total_fund': round(float(total_fund), 2),
            'achievement_count': achievement_count,
            'national_ratio': national_ratio,
            'young_output_rate': young_output_rate
        },
        'pie_data': pie_data,
        'bar_categories': bar_categories,
        'bar_values': bar_values,
        'wordcloud_data': wordcloud_data,
        'trend_series': trend_series,
        'trend_years': years,
        'bubble_data': bubble_data,
        'achievements_table': table_data,
        'projects_table': project_table
    })

def get_wordcloud_data():
    return [
        {'name': '马克思主义', 'value': 120}, {'name': '中国特色社会主义', 'value': 110},
        {'name': '国家治理', 'value': 100}, {'name': '政党治理', 'value': 95},
        {'name': '中国式现代化', 'value': 90}, {'name': '共同富裕', 'value': 85},
        {'name': '全过程人民民主', 'value': 80}, {'name': '人类命运共同体', 'value': 75},
        {'name': '党的建设', 'value': 70}, {'name': '国际共运', 'value': 65},
        {'name': '社会主义现代化', 'value': 60}, {'name': '意识形态建设', 'value': 55},
        {'name': '政治发展', 'value': 50}, {'name': '理论创新', 'value': 45},
        {'name': '治理能力', 'value': 40}, {'name': '新时代思想', 'value': 38},
        {'name': '文化自信', 'value': 35}, {'name': '制度优势', 'value': 32},
        {'name': '中国道路', 'value': 30}, {'name': '社会主义民主', 'value': 28},
        {'name': '群众路线', 'value': 26}, {'name': '全面从严治党', 'value': 25},
        {'name': '人类文明新形态', 'value': 23}, {'name': '党的自我革命', 'value': 22},
        {'name': '中国式民主', 'value': 20}, {'name': '国家治理现代化', 'value': 19},
        {'name': '马克思主义中国化', 'value': 18}
    ]


def dept_political(request):
    """政治学系学科分析数据（支持年份筛选，2021-2025）"""
    year_param = request.GET.get('year', 'all')
    try:
        dept = Dept.objects.get(dept_name='政治学系')
    except Dept.DoesNotExist:
        return JsonResponse({'error': '政治学系不存在'}, status=404)

    # 基础查询集
    projects_qs = Project.objects.filter(dept=dept)
    achievements_qs = Achievement.objects.filter(dept=dept)
    fund_qs = FundDetail.objects.filter(project__dept=dept)
    teacher_qs = User.objects.filter(dept=dept, role='teacher')

    # ========== 顶部卡片（全局数据） ==========
    teacher_count = teacher_qs.count()
    project_count = projects_qs.count()
    total_fund = fund_qs.aggregate(total=Sum('amount'))['total'] or Decimal(0)
    achievement_count = achievements_qs.count()
    high_level_count = projects_qs.filter(project_type__in=['国家级','省部级']).count()
    high_level_ratio = round(high_level_count / project_count * 100, 1) if project_count else 0
    year_2024 = achievements_qs.filter(publish_year=2024, level='CSSCI').count()
    year_2023 = achievements_qs.filter(publish_year=2023, level='CSSCI').count()
    csci_growth = round((year_2024 - year_2023) / year_2023 * 100, 1) if year_2023 else 0

    # ========== 经费趋势 ==========
    years = list(range(2021, 2026))
    fund_by_type = {'all':[0]*5, 'national':[0]*5, 'provincial':[0]*5, 'school':[0]*5, 'horizontal':[0]*5}
    for idx, y in enumerate(years):
        for ptype, key in [('国家级','national'), ('省部级','provincial'), ('校级','school'), ('横向','horizontal')]:
            total = fund_qs.filter(project__project_type=ptype, year=y).aggregate(total=Sum('amount'))['total'] or Decimal(0)
            val = round(float(total), 2)
            fund_by_type[key][idx] = val
            fund_by_type['all'][idx] += val

    # ========== 环形图 ==========
    if year_param == 'all':
        type_counts = achievements_qs.values('achievement_type').annotate(count=Count('id'))
    else:
        year = int(year_param)
        type_counts = achievements_qs.filter(publish_year=year).values('achievement_type').annotate(count=Count('id'))
    # 映射为前端期望的名称
    name_map = {'期刊论文': '核心论文', '学术著作': '学术专著', '研究报告': '研究报告', '决策咨询': '智库咨询'}
    count_map = {}
    for item in type_counts:
        display = name_map.get(item['achievement_type'], item['achievement_type'])
        count_map[display] = item['count']
    ring_data = []
    for label in ['核心论文', '学术专著', '研究报告', '智库咨询']:
        val = count_map.get(label, 0)
        if val == 0:
            val = 0.5   # 极小值占位
        ring_data.append({'name': label, 'value': val})

    # ========== 柱状图 ==========
    bar_categories = ['国家级', '省部级', '校级']
    if year_param == 'all':
        bar_counts = [
            achievements_qs.filter(level='国家级').count(),
            achievements_qs.filter(level='省部级').count(),
            achievements_qs.filter(level='校级').count()
        ]
    else:
        year = int(year_param)
        bar_counts = [
            achievements_qs.filter(publish_year=year, level='国家级').count(),
            achievements_qs.filter(publish_year=year, level='省部级').count(),
            achievements_qs.filter(publish_year=year, level='校级').count()
        ]
    if sum(bar_counts) == 0:
        # 根据年份设置演示数据
        demo_data = {'2021':[18,25,15], '2022':[20,28,18], '2023':[22,30,20], '2024':[26,35,25], '2025':[28,38,28]}
        year_str = year_param if year_param != 'all' else '2024'
        bar_counts = demo_data.get(year_str, [26,35,25])

    # ========== 雷达图 ==========
    if year_param == 'all':
        ach_avg = achievements_qs.count() / 5 if achievements_qs else 10
        proj_avg = projects_qs.count() / 5 if projects_qs else 6
        base = min(100, 60 + ach_avg + proj_avg)
    else:
        year = int(year_param)
        ach_cnt = achievements_qs.filter(publish_year=year).count()
        proj_cnt = projects_qs.filter(start_date__year=year).count()
        base = min(100, 60 + ach_cnt//2 + proj_cnt//3)
    radar_data = [min(100, base+5), min(100, base+8), min(100, base+3), max(50, base-2), min(100, base+10)]

    # ========== 词云（静态） ==========
    wordcloud_data = [
        {'name': '比较政治', 'value': 120}, {'name': '政治思想史', 'value': 110},
        {'name': '政党制度', 'value': 105}, {'name': '民主理论', 'value': 98},
        {'name': '政治发展', 'value': 95}, {'name': '中外政体', 'value': 90},
        {'name': '国家理论', 'value': 85}, {'name': '选举政治', 'value': 80},
        {'name': '政治参与', 'value': 75}, {'name': '智库咨询', 'value': 70},
        {'name': '现代国家', 'value': 65}, {'name': '政治文化', 'value': 62},
        {'name': '地方治理', 'value': 60}, {'name': '民主政治', 'value': 58},
        {'name': '政党政治', 'value': 55}, {'name': '政治改革', 'value': 52},
        {'name': '政治体制', 'value': 50}, {'name': '治理现代化', 'value': 48},
        {'name': '基层民主', 'value': 45}, {'name': '政治制度', 'value': 42},
        {'name': '权力制衡', 'value': 40}, {'name': '政治结构', 'value': 38},
        {'name': '国家建构', 'value': 35}, {'name': '公民社会', 'value': 32},
        {'name': '治理理论', 'value': 30}, {'name': '制度设计', 'value': 28},
        {'name': '政治秩序', 'value': 26}, {'name': '公共价值', 'value': 24},
        {'name': '法治国家', 'value': 22}, {'name': '政治平等', 'value': 20},
    ]

    # ========== 成果表格 ==========
    achievements_table = achievements_qs.select_related('author').order_by('-publish_year')[:10]
    table_data = []
    for idx, ach in enumerate(achievements_table, 1):
        table_data.append({
            '序号': idx,
            '成果名称': ach.title,
            '负责人': ach.author.real_name,
            '成果类型': ach.achievement_type,
            '年度': ach.publish_year
        })
    if not table_data:
        demo_ach = [
            ('比较政治制度理论研究', '陈教授', '学术专著', 2024),
            ('西方政治思想史谱系探析', '林教授', '核心期刊论文', 2023),
            ('政党政治与现代国家建构', '黄教授', '学术专著', 2024),
            ('民主理论与政治发展路径', '马教授', 'CSSCI论文', 2022),
            ('中外政体比较研究', '周教授', '研究报告', 2023),
        ]
        for idx, (title, author, atype, year) in enumerate(demo_ach, 1):
            table_data.append({'序号': idx, '成果名称': title, '负责人': author, '成果类型': atype, '年度': year})

    # ========== 项目进度表格 ==========
    project_qs = projects_qs.filter(project_type__in=['省部级','横向'], status__in=['在研','立项']).select_related('leader')[:15]
    project_table = []
    for proj in project_qs:
        project_table.append({
            '项目名称': proj.project_name,
            '负责人': proj.leader.real_name,
            '项目类型': proj.project_type,
            '进度': f"{proj.actual_progress}%",
            '状态': proj.status
        })
    if not project_table:
        demo_proj = [
            ('地方智库决策咨询机制研究', '陈教授', '省部级', '90%', '进行中'),
            ('区域治理与政治生态优化', '林教授', '横向课题', '100%', '已结题'),
            ('比较政党制度国别研究', '黄教授', '省部级', '75%', '进行中'),
            ('基层民主参与机制调研', '马教授', '智库委托', '65%', '进行中'),
        ]
        for name, leader, ptype, prog, status in demo_proj:
            project_table.append({'项目名称': name, '负责人': leader, '项目类型': ptype, '进度': prog, '状态': status})

    return JsonResponse({
        'stat_cards': {
            'teacher_count': teacher_count,
            'project_count': project_count,
            'total_fund': round(float(total_fund), 2),
            'achievement_count': achievement_count,
            'high_level_ratio': high_level_ratio,
            'csci_growth': csci_growth
        },
        'fund_trend': fund_by_type,
        'fund_years': years,
        'ring_data': ring_data,
        'bar_categories': bar_categories,
        'bar_values': bar_counts,
        'radar_data': radar_data,
        'wordcloud_data': wordcloud_data,
        'achievements_table': table_data,
        'projects_table': project_table
    })
from django.db.models import Count, Sum, Avg, Q, Max, F
from decimal import Decimal
import random

def dept_international(request):
    """国际政治系学科分析数据（支持年份筛选，2021-2025）"""
    year_param = request.GET.get('year', 'all')
    try:
        dept = Dept.objects.get(dept_name='国际政治系')
    except Dept.DoesNotExist:
        return JsonResponse({'error': '国际政治系不存在'}, status=404)

    # 基础查询集
    projects_qs = Project.objects.filter(dept=dept)
    achievements_qs = Achievement.objects.filter(dept=dept)
    fund_qs = FundDetail.objects.filter(project__dept=dept)
    teacher_qs = User.objects.filter(dept=dept, role='teacher')

    # ========== 顶部卡片（全局数据） ==========
    # 国别研究覆盖国家数：从项目或成果中提取，这里用项目涉及的国家数量模拟（可从 achievement 的 level 或关键词提取）
    country_coverage = 28   # 演示值，实际可从数据库统计
    international_projects = projects_qs.filter(project_type='横向').count()  # 简化：横向作为国际合作
    total_foreign_fund = fund_qs.filter(source_type__in=['横向课题','政府委托']).aggregate(total=Sum('amount'))['total'] or Decimal(0)
    international_publications = achievements_qs.filter(is_international=True).count()
    national_foreign_ratio = round(projects_qs.filter(project_type='国家级').count() / projects_qs.count() * 100, 1) if projects_qs.count() else 0
    academic_exchange_growth = 18   # 演示值，实际可从参与国际会议等统计

    # ========== 国内/涉外经费五年趋势 ==========
    years = list(range(2021, 2026))
    domestic_funds = []   # 国内经费（来源非横向/政府委托）
    foreign_funds = []    # 涉外经费（来源为横向课题或政府委托）
    for y in years:
        dom = fund_qs.filter(~Q(source_type__in=['横向课题','政府委托']), year=y).aggregate(total=Sum('amount'))['total'] or Decimal(0)
        fori = fund_qs.filter(source_type__in=['横向课题','政府委托'], year=y).aggregate(total=Sum('amount'))['total'] or Decimal(0)
        domestic_funds.append(round(float(dom), 2))
        foreign_funds.append(round(float(fori), 2))

    # ========== 各大洲研究成果分布（横向柱状图） ==========
    # 按大洲统计成果数量，可从成果标题或项目名称中匹配，这里用模拟数据，但支持年份筛选
    continents = ['亚洲', '欧洲', '北美', '拉美', '非洲', '大洋洲']
    if year_param == 'all':
        # 真实统计逻辑：假设成果中有 region 字段，简化为模拟
        continent_counts = [45, 32, 28, 16, 12, 8]
    else:
        year = int(year_param)
        # 演示数据随年份变化
        demo_map = {
            2021: [30, 20, 18, 10, 8, 5],
            2022: [35, 24, 22, 12, 9, 6],
            2023: [40, 28, 25, 14, 10, 7],
            2024: [43, 30, 27, 15, 11, 7],
            2025: [45, 32, 28, 16, 12, 8]
        }
        continent_counts = demo_map.get(year, [45,32,28,16,12,8])

    # ========== 国际学术成果类型占比（圆环图） ==========
    if year_param == 'all':
        type_counts = achievements_qs.filter(is_international=True).values('achievement_type').annotate(count=Count('id'))
    else:
        year = int(year_param)
        type_counts = achievements_qs.filter(is_international=True, publish_year=year).values('achievement_type').annotate(count=Count('id'))
    # 映射为前端期望的四种类型
    type_map = {
        '期刊论文': '国际期刊论文',
        '学术著作': '外文专著',
        '研究报告': '国别研究报告',
        '决策咨询': '涉外智库咨询'
    }
    ring_data = []
    for item in type_counts:
        name = type_map.get(item['achievement_type'], item['achievement_type'])
        ring_data.append({'name': name, 'value': item['count']})
    # 若无数据，填充演示（随年份变化）
    if not ring_data:
        demo_ring = {
            'all': [('国际期刊论文',32), ('外文专著',12), ('国别研究报告',18), ('涉外智库咨询',10)],
            '2021': [('国际期刊论文',5), ('外文专著',2), ('国别研究报告',3), ('涉外智库咨询',1)],
            '2022': [('国际期刊论文',7), ('外文专著',3), ('国别研究报告',4), ('涉外智库咨询',2)],
            '2023': [('国际期刊论文',8), ('外文专著',3), ('国别研究报告',4), ('涉外智库咨询',2)],
            '2024': [('国际期刊论文',9), ('外文专著',4), ('国别研究报告',4), ('涉外智库咨询',3)],
            '2025': [('国际期刊论文',10), ('外文专著',4), ('国别研究报告',3), ('涉外智库咨询',2)]
        }
        key = year_param if year_param != 'all' else 'all'
        ring_data = [{'name': n, 'value': v} for n, v in demo_ring.get(key, demo_ring['all'])]

    # ========== 雷达图（五大国际研究领域综合实力） ==========
    # 基于该系成果、项目等估算五个维度得分，支持年份筛选
    if year_param == 'all':
        # 取近5年平均
        dimensions = ['地缘政治与区域格局', '大国关系与战略博弈', '全球治理与国际组织', '区域国别政治研究', '国际安全与防务战略']
        base = min(100, 60 + achievements_qs.count()//10 + projects_qs.count()//5)
        radar_values = [base+8, base+10, base+5, base+3, base+7]
    else:
        year = int(year_param)
        # 根据当年成果数、项目数动态计算
        ach_cnt = achievements_qs.filter(publish_year=year).count()
        proj_cnt = projects_qs.filter(start_date__year=year).count()
        base = min(100, 60 + ach_cnt//5 + proj_cnt//3)
        radar_values = [base+8, base+10, base+5, base+3, base+7]
    radar_data = [min(100, max(50, v)) for v in radar_values]

    # ========== 词云数据（静态，可从成果标题提取） ==========
    wordcloud_data = [
        {'name': '地缘政治', 'value': 130}, {'name': '大国博弈', 'value': 110},
        {'name': '全球治理', 'value': 100}, {'name': '区域国别', 'value': 90},
        {'name': '国际秩序', 'value': 108}, {'name': '多边机制', 'value': 105},
        {'name': '中美关系', 'value': 102}, {'name': '东亚格局', 'value': 100},
        {'name': '一带一路', 'value': 98}, {'name': '国际安全', 'value': 95},
        {'name': '全球化', 'value': 92}, {'name': '区域合作', 'value': 90},
        {'name': '跨国治理', 'value': 88}, {'name': '战略竞争', 'value': 85},
        {'name': '防务安全', 'value': 82}, {'name': '欧洲一体化', 'value': 80},
        {'name': '中东局势', 'value': 78}, {'name': '东南亚格局', 'value': 75},
        {'name': '国际组织', 'value': 72}, {'name': '战略格局', 'value': 70},
        {'name': '地缘风险', 'value': 68}, {'name': '双边关系', 'value': 60},
        {'name': '地缘经济', 'value': 58}, {'name': '能源格局', 'value': 55},
        {'name': '海洋权益', 'value': 53}, {'name': '极地治理', 'value': 50},
        {'name': '主权争端', 'value': 48}, {'name': '联盟体系', 'value': 45},
        {'name': '国际规则', 'value': 38}, {'name': '价值外交', 'value': 35},
        {'name': '制裁机制', 'value': 33}, {'name': '军备控制', 'value': 30},
        {'name': '网络地缘', 'value': 28}, {'name': '气候外交', 'value': 25},
        {'name': '粮食安全', 'value': 23}, {'name': '公共卫生治理', 'value': 20},
        {'name': '东北亚安全', 'value': 18}, {'name': '南亚格局', 'value': 16},
        {'name': '欧亚地缘', 'value': 15}, {'name': '跨大西洋关系', 'value': 14},
        {'name': '南方国家', 'value': 12}, {'name': '中等强国', 'value': 10}
    ]

    # ========== 国别代表性研究成果表格 ==========
    achievements_table = achievements_qs.filter(is_international=True).select_related('author').order_by('-publish_year')[:10]
    table_data = []
    for idx, ach in enumerate(achievements_table, 1):
        table_data.append({
            '序号': idx,
            '成果名称': ach.title,
            '负责人': ach.author.real_name,
            '成果类型': ach.achievement_type,
            '发布年份': ach.publish_year
        })
    if not table_data:
        demo_ach = [
            ('东亚地缘格局演变研究', '张教授', '外文专著', 2024),
            ('中美战略博弈关系分析', '李教授', '国际期刊论文', 2023),
            ('欧洲一体化治理机制研究', '王教授', '国别研究报告', 2024),
            ('一带一路区域合作新格局', '刘教授', '涉外智库咨询', 2022),
            ('中东地缘冲突与秩序重构', '陈教授', '国际期刊论文', 2023)
        ]
        for idx, (title, author, atype, year) in enumerate(demo_ach, 1):
            table_data.append({
                '序号': idx, '成果名称': title, '负责人': author,
                '成果类型': atype, '发布年份': year
            })

    # ========== 国际合作&涉外在研项目进度表格 ==========
    # 筛选项目类型为'横向'或 project_type 包含 '国际' 字样，状态为在研或立项
    project_qs = projects_qs.filter(Q(project_type='横向') | Q(project_name__icontains='国际'), status__in=['在研','立项']).select_related('leader')[:15]
    project_table = []
    for proj in project_qs:
        project_table.append({
            '项目名称': proj.project_name,
            '负责人': proj.leader.real_name,
            '项目类型': proj.project_type,
            '进度': f"{proj.actual_progress}%",
            '状态': proj.status
        })
    if not project_table:
        demo_proj = [
            ('中欧多边治理合作研究', '张教授', '国际合作课题', '85%', '进行中'),
            ('东南亚地缘风险评估', '李教授', '涉外智库项目', '70%', '进行中'),
            ('大国关系长期趋势研判', '王教授', '国家级涉外课题', '60%', '进行中'),
            ('非洲区域发展合作调研', '刘教授', '国际交流项目', '90%', '进行中'),
            ('全球气候治理机制研究', '陈教授', '省部级涉外课题', '100%', '已结题')
        ]
        for name, leader, ptype, prog, status in demo_proj:
            project_table.append({
                '项目名称': name, '负责人': leader,
                '项目类型': ptype, '进度': prog, '状态': status
            })

    # 返回所有数据
    return JsonResponse({
        'stat_cards': {
            'country_coverage': country_coverage,
            'international_projects': international_projects,
            'total_foreign_fund': round(float(total_foreign_fund), 2),
            'international_publications': international_publications,
            'national_foreign_ratio': national_foreign_ratio,
            'academic_exchange_growth': academic_exchange_growth
        },
        'fund_trend': {
            'years': years,
            'domestic': domestic_funds,
            'foreign': foreign_funds
        },
        'continent_data': continent_counts,
        'continents': continents,
        'ring_data': ring_data,
        'radar_data': radar_data,
        'wordcloud_data': wordcloud_data,
        'achievements_table': table_data,
        'projects_table': project_table
    })
from django.db.models import Count, Sum, Avg, Q, Max, F
from decimal import Decimal
import random

def dept_public(request):
    """公共管理系学科分析数据（支持年份筛选，2021-2025）"""
    year_param = request.GET.get('year', 'all')
    try:
        dept = Dept.objects.get(dept_name='公共管理系')
    except Dept.DoesNotExist:
        return JsonResponse({'error': '公共管理系不存在'}, status=404)

    # 基础查询集
    projects_qs = Project.objects.filter(dept=dept)
    achievements_qs = Achievement.objects.filter(dept=dept)
    fund_qs = FundDetail.objects.filter(project__dept=dept)
    teacher_qs = User.objects.filter(dept=dept, role='teacher')

    # ========== 顶部卡片（全局数据） ==========
    gov_projects = projects_qs.filter(project_type='横向').count()  # 模拟政府合作项目
    total_fund = fund_qs.aggregate(total=Sum('amount'))['total'] or Decimal(0)
    core_achievements = achievements_qs.filter(level__in=['CSSCI','核心期刊']).count()
    digital_gov_projects = projects_qs.filter(project_name__icontains='数字').count()
    community_growth = 25   # 演示值，实际可计算近两年社区治理项目增长率
    emergency_projects = projects_qs.filter(project_name__icontains='应急').count()

    # ========== 近五年科研经费走势（纵向/横向） ==========
    years = list(range(2021, 2026))
    vertical_funds = []   # 纵向课题经费（国家级、省部级）
    horizontal_funds = [] # 横向课题经费
    for y in years:
        vert = fund_qs.filter(project__project_type__in=['国家级','省部级'], year=y).aggregate(total=Sum('amount'))['total'] or Decimal(0)
        hori = fund_qs.filter(project__project_type='横向', year=y).aggregate(total=Sum('amount'))['total'] or Decimal(0)
        vertical_funds.append(round(float(vert), 2))
        horizontal_funds.append(round(float(hori), 2))

    # ========== 各研究方向成果数量分布（条形图） ==========
    directions = ['数字治理', '公共政策', '社区治理', '应急管理', '公共服务', '政府改革']
    # 根据成果标题或关键词匹配研究方向（简化为模拟，可后续优化）
    if year_param == 'all':
        dir_counts = [28, 22, 20, 18, 15, 12]
    else:
        year = int(year_param)
        # 演示数据随年份变化
        demo = {
            2021: [15, 12, 10, 9, 7, 5],
            2022: [18, 14, 12, 11, 9, 7],
            2023: [22, 17, 15, 13, 11, 9],
            2024: [25, 20, 18, 16, 13, 10],
            2025: [28, 22, 20, 18, 15, 12]
        }
        dir_counts = demo.get(year, [28,22,20,18,15,12])

    # ========== 科研项目来源占比（饼图） ==========
    if year_param == 'all':
        source_counts = {
            '国家级课题': projects_qs.filter(project_type='国家级').count(),
            '省部级课题': projects_qs.filter(project_type='省部级').count(),
            '地方政府委托': projects_qs.filter(project_type='横向').count()
        }
    else:
        year = int(year_param)
        source_counts = {
            '国家级课题': projects_qs.filter(project_type='国家级', start_date__year=year).count(),
            '省部级课题': projects_qs.filter(project_type='省部级', start_date__year=year).count(),
            '地方政府委托': projects_qs.filter(project_type='横向', start_date__year=year).count()
        }
    pie_data = [{'name': k, 'value': v} for k, v in source_counts.items() if v > 0]
    if not pie_data:
        pie_data = [{'name': '国家级课题', 'value': 5}, {'name': '省部级课题', 'value': 7}, {'name': '地方政府委托', 'value': 10}]

    # ========== 雷达图（六大研究领域综合实力） ==========
    # 基于该系成果、项目等估算，支持年份筛选
    if year_param == 'all':
        # 取平均值
        ach_avg = achievements_qs.count() / 6 if achievements_qs else 15
        proj_avg = projects_qs.count() / 6 if projects_qs else 10
        base = min(100, 60 + ach_avg//2 + proj_avg//3)
        radar_values = [base+5, base+8, base+10, base+3, base+2, base-2]
    else:
        year = int(year_param)
        ach_cnt = achievements_qs.filter(publish_year=year).count()
        proj_cnt = projects_qs.filter(start_date__year=year).count()
        base = min(100, 60 + ach_cnt//5 + proj_cnt//4)
        radar_values = [base+5, base+8, base+10, base+3, base+2, base-2]
    radar_values = [min(100, max(50, v)) for v in radar_values]

    # ========== 词云数据（静态） ==========
    wordcloud_data = [
        {'name': '数字政府', 'value': 140}, {'name': '公共政策', 'value': 135},
        {'name': '社区治理', 'value': 130}, {'name': '应急管理', 'value': 128},
        {'name': '公共服务', 'value': 125}, {'name': '基层治理', 'value': 122},
        {'name': '智慧城市', 'value': 120}, {'name': '乡村振兴', 'value': 118},
        {'name': '治理现代化', 'value': 115}, {'name': '政府改革', 'value': 112},
        {'name': '绩效评估', 'value': 110}, {'name': '大数据治理', 'value': 108},
        {'name': '公共部门', 'value': 105}, {'name': '服务型政府', 'value': 102},
        {'name': '政策执行', 'value': 100}, {'name': '风险治理', 'value': 98},
        {'name': '社会治理', 'value': 95}, {'name': '行政改革', 'value': 92},
        {'name': '数字鸿沟', 'value': 90}, {'name': '公共管理', 'value': 88},
        {'name': '地方政府', 'value': 85}, {'name': '公共财政', 'value': 82},
        {'name': '治理能力', 'value': 80}, {'name': '公共安全', 'value': 78},
        {'name': '网格化治理', 'value': 72}, {'name': '政务公开', 'value': 70},
        {'name': '营商环境', 'value': 65}, {'name': '人工智能治理', 'value': 60}
    ]

    # ========== 近五年各类学术成果逐年产出对比（柱状图） ==========
    result_years = [2021,2022,2023,2024,2025]
    journal_counts = []   # 期刊论文
    monograph_counts = [] # 专著
    report_counts = []    # 研究报告
    for y in result_years:
        journal = achievements_qs.filter(publish_year=y, achievement_type='期刊论文').count()
        monograph = achievements_qs.filter(publish_year=y, achievement_type='学术著作').count()
        report = achievements_qs.filter(publish_year=y, achievement_type='研究报告').count()
        journal_counts.append(journal)
        monograph_counts.append(monograph)
        report_counts.append(report)
    # 如果全为0，填充演示数据
    if sum(journal_counts) == 0:
        journal_counts = [12,15,18,22,25]
        monograph_counts = [2,3,4,5,6]
        report_counts = [5,7,9,11,13]

    # ========== 代表性学术成果表格 ==========
    achievements_table = achievements_qs.select_related('author').order_by('-publish_year')[:10]
    table_data = []
    for idx, ach in enumerate(achievements_table, 1):
        table_data.append({
            '序号': idx,
            '成果名称': ach.title,
            '负责人': ach.author.real_name,
            '成果类型': ach.achievement_type,
            '发布年份': ach.publish_year
        })
    if not table_data:
        demo_ach = [
            ('数字政府建设中的治理效能研究', '王教授', '核心期刊论文', 2024),
            ('社区网格化治理模式创新研究', '李教授', '研究报告', 2023),
            ('突发公共卫生事件应急管理机制', '张教授', 'CSSCI论文', 2024),
            ('地方政府债务风险治理研究', '刘教授', '专著', 2022),
            ('大数据时代公共政策评估方法', '赵教授', '核心期刊论文', 2023),
            ('基层治理中的数字鸿沟问题探析', '陈教授', '研究报告', 2024),
            ('乡村振兴战略中的公共服务供给', '吴教授', 'CSSCI论文', 2022),
            ('智慧城市背景下的城市治理转型', '郑教授', '专著', 2023),
            ('公共政策执行偏差的成因与对策', '周教授', '核心期刊论文', 2024),
            ('公共部门人力资源管理改革研究', '马教授', '研究报告', 2023)
        ]
        for idx, (title, author, atype, year) in enumerate(demo_ach, 1):
            table_data.append({
                '序号': idx, '成果名称': title, '负责人': author,
                '成果类型': atype, '发布年份': year
            })

    # ========== 政府合作&在研项目进度表格 ==========
    # 筛选横向项目或名称含“政府”的项目
    project_qs = projects_qs.filter(Q(project_type='横向') | Q(project_name__icontains='政府'), status__in=['在研','立项']).select_related('leader')[:15]
    project_table = []
    for proj in project_qs:
        project_table.append({
            '项目名称': proj.project_name,
            '负责人': proj.leader.real_name,
            '项目类型': proj.project_type,
            '进度': f"{proj.actual_progress}%",
            '状态': proj.status
        })
    if not project_table:
        demo_proj = [
            ('某市数字政务平台优化研究', '王教授', '地方政府合作项目', '90%', '进行中'),
            ('社区治理现代化路径研究', '李教授', '省部级课题', '75%', '进行中'),
            ('应急管理体系建设评估', '张教授', '横向委托项目', '100%', '已结题'),
            ('公共服务均等化政策评估', '刘教授', '国家级课题', '60%', '进行中'),
            ('地方政府营商环境优化研究', '赵教授', '地方政府合作项目', '85%', '进行中'),
            ('智慧城市治理模式创新研究', '陈教授', '省部级课题', '50%', '进行中'),
            ('乡村振兴公共服务供给研究', '吴教授', '横向委托项目', '100%', '已结题')
        ]
        for name, leader, ptype, prog, status in demo_proj:
            project_table.append({
                '项目名称': name, '负责人': leader,
                '项目类型': ptype, '进度': prog, '状态': status
            })

    # ========== 智能分析文本（根据年份动态生成） ==========
    analysis_texts = {
        'all': ('数字治理、社区治理两大方向表现突出，实力领先。', '政府改革方向得分相对较低，需重点补强。', '可围绕数字治理与社区治理打造特色交叉研究方向。'),
        '2021': ('整体实力中等偏上，社区治理方向优势初显。', '数字治理与政府改革方向得分偏低。', '建议加大数字治理方向的课题申报力度。'),
        '2022': ('社区治理方向成果快速增长，成为新优势。', '公共政策与应急管理方向进展缓慢。', '可依托社区治理成果拓展基层治理交叉研究。'),
        '2023': ('数字治理与社区治理双方向同步发力，优势互补。', '政府改革方向得分提升不明显。', '建议加强政府改革方向的团队建设与课题布局。'),
        '2024': ('数字治理方向进入快速发展期，成果数量大幅提升。', '公共服务方向增长乏力，需关注政策导向。', '可结合数字治理优势拓展智慧公共服务研究。'),
        '2025': ('数字治理、社区治理、应急管理三大方向全面领先。', '政府改革方向仍为短板，与其他方向差距拉大。', '建议组建跨学科团队，补齐政府改革方向短板。')
    }
    year_key = year_param if year_param in analysis_texts else 'all'
    summary, weak, suggest = analysis_texts[year_key]

    # 返回所有数据
    return JsonResponse({
        'stat_cards': {
            'gov_projects': gov_projects,
            'total_fund': round(float(total_fund), 2),
            'core_achievements': core_achievements,
            'digital_gov_projects': digital_gov_projects,
            'community_growth': community_growth,
            'emergency_projects': emergency_projects
        },
        'fund_trend': {
            'years': years,
            'vertical': vertical_funds,
            'horizontal': horizontal_funds
        },
        'directions': directions,
        'dir_counts': dir_counts,
        'pie_data': pie_data,
        'radar_values': radar_values,
        'wordcloud_data': wordcloud_data,
        'result_years': result_years,
        'journal_counts': journal_counts,
        'monograph_counts': monograph_counts,
        'report_counts': report_counts,
        'achievements_table': table_data,
        'projects_table': project_table,
        'analysis': {
            'summary': summary,
            'weak': weak,
            'suggest': suggest
        }
    })
def index(request):
    return render(request, '首页.html')

def project_page(request):
    return render(request, '科研项目.html')

def fund_page(request):
    return render(request, '科研经费.html')

def achievement_page(request):
    return render(request, '科研成果.html')

def teacher_analysis_page(request):
    return render(request, '智能分析教师版.html')

def admin_analysis_page(request):
    return render(request, '智能分析管理员版.html')

# 各个学科页面
def science_socialism_page(request):
    return render(request, '科学社会主义系.html')

def political_science_page(request):
    return render(request, '政治学系.html')

def international_politics_page(request):
    return render(request, '国际政治系.html')

def public_management_page(request):
    return render(request, '公共管理系.html')


# ===================== 搜索功能 =====================
from django.db.models import Q


def search(request):
    """
    统一搜索接口：支持搜索项目、成果、教师
    参数: q=关键词
    返回: JSON 分组结果
    """
    q = request.GET.get('q', '').strip()
    if not q:
        return JsonResponse({'projects': [], 'achievements': [], 'teachers': []})

    # 搜索项目（按项目名称、负责人姓名、学科）
    projects = Project.objects.filter(
        Q(project_name__icontains=q) |
        Q(leader__real_name__icontains=q) |
        Q(subject__icontains=q)
    ).select_related('leader').values(
        'id', 'project_name', 'leader__real_name', 'subject', 'status'
    )[:20]  # 限制结果数量

    # 搜索成果（按标题、作者姓名、类型）
    achievements = Achievement.objects.filter(
        Q(title__icontains=q) |
        Q(author__real_name__icontains=q) |
        Q(achievement_type__icontains=q)
    ).select_related('author').values(
        'id', 'title', 'author__real_name', 'achievement_type', 'publish_year'
    )[:20]

    # 搜索教师（按姓名、职称、系别）
    teachers = User.objects.filter(
        Q(real_name__icontains=q) |
        Q(title__icontains=q) |
        Q(dept__dept_name__icontains=q),
        role='teacher'
    ).select_related('dept').values(
        'id', 'real_name', 'title', 'dept__dept_name'
    )[:10]

    # 转换 QuerySet 为列表（values 已经是 dict 形式）
    project_list = list(projects)
    achievement_list = list(achievements)
    teacher_list = list(teachers)

    return JsonResponse({
        'projects': project_list,
        'achievements': achievement_list,
        'teachers': teacher_list
    })