from decimal import Decimal, InvalidOperation
from datetime import date, timedelta
import json
import csv
from collections import Counter
import random
import math
import re

from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.db.models import (
    Sum,
    Count,
    Avg,
    Max,
    Q,
    F,
)

from .models import (
    User,
    Project,
    FundDetail,
    FundBudget,
    Achievement,
    TeacherScore,
    Cooperation,
    Dept,
    DeptResource,
    RiskWarning
)
from .research_analysis import keyword_cloud, direction_counts, geo_counts

from .research_metrics import teacher_research_metrics, teacher_real_score_rows, teacher_real_years

# ==================================================
# 公共年份工具
# ==================================================

def get_available_years():
    """获取系统中实际存在科研数据的年份"""
    years = set()

    # 项目年份
    project_years = Project.objects.dates(
        'start_date',
        'year'
    )
    years.update(item.year for item in project_years)

    # 经费年份
    fund_years = FundDetail.objects.values_list(
        'year',
        flat=True
    ).distinct()
    years.update(year for year in fund_years if year is not None)

    # 成果年份
    achievement_years = Achievement.objects.values_list(
        'publish_year',
        flat=True
    ).distinct()
    years.update(
        year for year in achievement_years
        if year is not None
    )

    # 教师绩效年份
    # 全局年份筛选仅使用原有非演示绩效，避免模拟年份影响其他业务页面。
    score_years = TeacherScore.objects.filter(
        is_demo=False
    ).values_list(
        'year',
        flat=True
    ).distinct()
    years.update(year for year in score_years if year is not None)

    return sorted(years)


def get_latest_year(default=2025):
    """获取系统最新数据年份"""
    years = get_available_years()
    return years[-1] if years else default


def get_recent_years(count=5):
    """获取截至最新数据年份的最近 N 年"""
    latest_year = get_latest_year()
    return list(
        range(
            latest_year - count + 1,
            latest_year + 1
        )
    )
def available_years(request):
    """返回指定业务范围内真实存在的年份及相应筛选选项。"""
    scope = request.GET.get('scope', 'all')
    response_data = {}

    if scope == 'project':
        project_years = Project.objects.dates(
            'start_date',
            'year',
            order='DESC'
        )
        years = [item.year for item in project_years]
        subjects = list(
            Project.objects
            .exclude(subject__isnull=True)
            .exclude(subject__exact='')
            .values_list('subject', flat=True)
            .distinct()
            .order_by('subject')
        )
        response_data['subjects'] = subjects

    elif scope == 'fund':
        fund_years = FundDetail.objects.values_list(
            'year',
            flat=True
        ).distinct()
        years = sorted(
            {int(year) for year in fund_years if year is not None},
            reverse=True
        )

    elif scope == 'achievement':
        achievement_years = Achievement.objects.values_list(
            'publish_year',
            flat=True
        ).distinct()
        years = sorted(
            {int(year) for year in achievement_years if year is not None},
            reverse=True
        )

        subjects = list(
            Achievement.objects
            .exclude(subject__isnull=True)
            .exclude(subject__exact='')
            .values_list('subject', flat=True)
            .distinct()
            .order_by('subject')
        )
        response_data['subjects'] = subjects

        subject_options = [
            {'value': subject, 'label': subject}
            for subject in subjects
        ]
        has_unclassified = Achievement.objects.filter(
            Q(subject__isnull=True) | Q(subject__exact='')
        ).exists()
        if has_unclassified:
            subject_options.append({
                'value': '__unclassified__',
                'label': '未分类'
            })
        response_data['subject_options'] = subject_options

    else:
        years = sorted(get_available_years(), reverse=True)

    if years:
        latest_year = years[0]
    elif scope == 'achievement':
        latest_year = None
    else:
        latest_year = get_latest_year()

    response_data.update({
        'years': years,
        'latest_year': latest_year
    })
    return JsonResponse(response_data)


def fund_trend(request):
    years = get_recent_years(5)

    data = FundDetail.objects.filter(
        year__in=years
    ).values('year').annotate(
        total=Sum('amount')
    )

    result = {
        item['year']: float(item['total'])
        for item in data
    }

    return JsonResponse({
        'years': years,
        'values': [result.get(y, 0) for y in years]
    })
# ==================================================
# 首页概览接口
# ==================================================

# ---------- 1. 顶部卡片数据（当前年份）----------
def main_card(request):
    year = int(request.GET.get('year', get_latest_year()))
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
    year = int(request.GET.get('year', get_latest_year()))
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

def trend_project_fund(request):
    """返回经费和项目数两个序列，用于双轴图"""
    years_param = request.GET.get('years')
    if years_param:
        years = [
            int(y)
            for y in years_param.split(',')
            if y.strip()
        ]
    else:
        years = get_recent_years(5)
    
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
    """
    科研合作网络。
    - 传入 teacher_id：教师画像展示该教师负责项目的原有与演示合作关系，并逐条返回数据标记。
    - 不传 teacher_id：兼容全院网络页面，但默认排除演示关系，避免在未标注页面中混入模拟数据。
    """
    raw_teacher_id = request.GET.get('teacher_id', '').strip()

    if raw_teacher_id:
        try:
            teacher_id = int(raw_teacher_id)
            if teacher_id <= 0:
                raise ValueError
        except (TypeError, ValueError):
            return JsonResponse({'error': 'teacher_id 必须是正整数'}, status=400)

        try:
            teacher = User.objects.select_related('dept').get(
                pk=teacher_id,
                role='teacher'
            )
        except User.DoesNotExist:
            return JsonResponse({'error': '未找到该教师'}, status=404)

        cooperations = (
            Cooperation.objects
            .filter(
                Q(source=teacher.real_name)
                | Q(target=teacher.real_name)
            )
            .filter(is_demo=False)
            .select_related('project')
            .order_by('id')
        )
        



        demo_count = cooperations.filter(is_demo=True).count()
        existing_count = cooperations.filter(is_demo=False).count()
        teacher_names = set(
            User.objects.filter(role='teacher').values_list('real_name', flat=True)
        )
        names = set()
        links = []

        for item in cooperations:
            source = (item.source or '').strip()
            target = (item.target or '').strip()
            if source:
                names.add(source)
            if target:
                names.add(target)
            if source and target:
                links.append({
                    'source': source,
                    'target': target,
                    'value': item.coop_count or 1,
                    'project_name': item.project.project_name,
                    'is_demo': False,
                    'data_source': item.data_source or 'unknown',
                    'source_label': '正式记录',
                })

        nodes = [
            {
                'name': name,
                'category': 'teacher' if name in teacher_names else 'external',
                'itemStyle': {
                    'color': '#409EFF' if name in teacher_names else '#D4AF37'
                },
            }
            for name in sorted(names)
        ]
        return JsonResponse({
            'nodes': nodes,
            'links': links,
            'total': len(links),
            'summary': {
                'existing_records': existing_count,
                'demo_records': demo_count,
            },
            'has_demo_data': False,
        })

    # 全院网络兼容模式：不展示模拟关系，防止其他页面无标识地使用演示数据。
    teachers = User.objects.filter(role='teacher')
    teacher_names = set(teachers.values_list('real_name', flat=True))
    cooperations = Cooperation.objects.filter(
        is_demo=False
    ).select_related('project').order_by('id')
    excluded_demo_count = Cooperation.objects.filter(is_demo=True).count()
    names = set(teacher_names)
    links = []

    for item in cooperations:
        source = (item.source or '').strip()
        target = (item.target or '').strip()
        if source:
            names.add(source)
        if target:
            names.add(target)
        if source and target:
            links.append({
                'source': source,
                'target': target,
                'value': item.coop_count or 1,
                'is_demo': False,
                'data_source': item.data_source or 'existing',
                'source_label': '原有记录',
            })

    nodes = [
        {
            'name': name,
            'category': 'teacher' if name in teacher_names else 'external',
            'itemStyle': {
                'color': '#409EFF' if name in teacher_names else '#D4AF37'
            },
        }
        for name in sorted(names)
    ]
    return JsonResponse({
        'nodes': nodes,
        'links': links,
        'total': len(links),
        'summary': {
            'existing_records': len(links),
            'demo_records_excluded': excluded_demo_count,
        },
        'has_demo_data': False,
    })

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
# ==================================================
# 科研总览分析接口
# ==================================================

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


def _filtered_project_queryset(request):
    """统一解析项目页面的年份和学科筛选条件。"""
    qs = Project.objects.all()
    year = request.GET.get('year', 'all')
    subject = request.GET.get('subject', 'all')

    if year not in ('all', '', None):
        try:
            year_value = int(year)
        except (TypeError, ValueError):
            return None, JsonResponse({'error': '年份参数无效'}, status=400)
        qs = qs.filter(start_date__year=year_value)

    if subject not in ('all', '', None):
        qs = qs.filter(subject=subject)

    return qs, None


def project_status_pie(request):
    """按当前年份和学科筛选条件统计项目状态。"""
    qs, error_response = _filtered_project_queryset(request)
    if error_response is not None:
        return error_response

    status_counts = qs.values('status').annotate(count=Count('id'))
    counts = {
        (item['status'] or '未设置'): item['count']
        for item in status_counts
    }
    preferred_order = ['在研', '结题', '立项', '审核中']
    status_names = [name for name in preferred_order if counts.get(name, 0) > 0]
    status_names.extend(sorted(
        name for name, count in counts.items()
        if count > 0 and name not in preferred_order
    ))
    data = [{'name': name, 'value': counts[name]} for name in status_names]
    return JsonResponse({
        'data': data,
        'total': sum(item['value'] for item in data)
    })


def project_subject_year_counts(request):
    """按当前筛选条件返回项目学科/年份数量；全部年份时展示最新的三个项目年份。"""
    year_param = request.GET.get('year', 'all')
    subject = request.GET.get('subject', 'all')

    if year_param not in ('all', '', None):
        try:
            selected_year = int(year_param)
        except (TypeError, ValueError):
            return JsonResponse({'error': '年份参数无效'}, status=400)
        years = [selected_year]
    else:
        recent_project_years = Project.objects.dates(
            'start_date',
            'year',
            order='DESC'
        )[:3]
        years = sorted(item.year for item in recent_project_years)

    if not years:
        return JsonResponse({
            'years': [],
            'subjects': [subject] if subject not in ('all', '', None) else [],
            'series': []
        })

    qs = Project.objects.filter(start_date__year__in=years)
    if subject not in ('all', '', None):
        qs = qs.filter(subject=subject)

    grouped_counts = qs.values('subject', 'start_date__year').annotate(
        count=Count('id')
    )

    if subject not in ('all', '', None):
        subjects = [subject]
    else:
        subjects = sorted({
            item['subject'] or '未分类'
            for item in grouped_counts
        })

    count_map = {}
    for item in grouped_counts:
        subject_name = item['subject'] or '未分类'
        count_map[(subject_name, item['start_date__year'])] = item['count']

    series = []
    for project_year in years:
        series.append({
            'name': f'{project_year}年',
            'type': 'bar',
            'barMaxWidth': 48,
            'data': [
                count_map.get((subject_name, project_year), 0)
                for subject_name in subjects
            ]
        })

    return JsonResponse({
        'years': years,
        'subjects': subjects,
        'series': series,
        'total': sum(sum(item['data']) for item in series)
    })


def project_list_api(request):
    """项目列表数据（支持年份、学科筛选，按经费降序）。"""
    qs, error_response = _filtered_project_queryset(request)
    if error_response is not None:
        return error_response

    qs = qs.select_related('leader').order_by('-fund_amount')
    projects = []
    for p in qs:
        leader_name = p.leader.real_name if p.leader else '未指定'
        start_year = p.start_date.year if p.start_date else None
        end_year = p.end_date.year if p.end_date else None
        if start_year and end_year:
            start_end = f'{start_year}-{end_year}'
        elif start_year:
            start_end = f'{start_year}—'
        elif end_year:
            start_end = f'—{end_year}'
        else:
            start_end = '—'

        projects.append({
            'id': p.id,
            'name': p.project_name,
            'leader': leader_name,
            'subject': p.subject or '未分类',
            'fund': float(p.fund_amount or 0),
            'start_end': start_end,
            'status': p.status or '未设置',
        })
    return JsonResponse({'projects': projects, 'total': len(projects)})



def project_detail_api(request):
    """
    返回单个科研项目的详情及关联经费、预算和合作记录。
    只读接口，不修改数据库，也不改变现有项目列表接口。
    请求方式：GET /api/project/detail?id=<项目ID>
    """
    if request.method != 'GET':
        return JsonResponse(
            {'error': '仅支持 GET 请求'},
            status=405
        )

    raw_project_id = request.GET.get('id', '').strip()
    if not raw_project_id:
        return JsonResponse(
            {'error': '缺少项目ID参数'},
            status=400
        )

    try:
        project_id = int(raw_project_id)
    except (TypeError, ValueError):
        return JsonResponse(
            {'error': '项目ID必须是有效整数'},
            status=400
        )

    if project_id <= 0:
        return JsonResponse(
            {'error': '项目ID必须大于0'},
            status=400
        )

    try:
        project = (
            Project.objects
            .select_related('leader', 'leader__dept', 'dept')
            .get(pk=project_id)
        )
    except Project.DoesNotExist:
        return JsonResponse(
            {'error': '未找到该科研项目，项目可能已被删除'},
            status=404
        )

    fund_queryset = (
        FundDetail.objects
        .filter(project_id=project.id)
        .order_by('year', 'usage_type', 'source_type', 'id')
    )

    budget_queryset = (
        FundBudget.objects
        .filter(project_id=project.id)
        .order_by('year')
    )

    # 项目详情默认只展示原有合作记录；教师画像接口会单独展示并标注演示合作关系。
    cooperation_queryset = (
        Cooperation.objects
        .filter(project_id=project.id, is_demo=False)
        .order_by('id')
    )

    actual_fund_total = (
        fund_queryset.aggregate(total=Sum('amount'))['total']
        or Decimal('0')
    )
    budget_total = (
        budget_queryset.aggregate(total=Sum('budget_amount'))['total']
        or Decimal('0')
    )

    fund_details = [
        {
            'id': item.id,
            'year': item.year,
            'source_type': item.source_type or '未注明',
            'usage_type': item.usage_type or '未注明',
            'amount': round(float(item.amount or 0), 2),
        }
        for item in fund_queryset
    ]

    budget_details = [
        {
            'year': item.year,
            'budget_amount': round(float(item.budget_amount or 0), 2),
        }
        for item in budget_queryset
    ]

    cooperation_records = [
        {
            'source': item.source or '未注明',
            'target': item.target or '未注明',
            'count': item.coop_count,
        }
        for item in cooperation_queryset
    ]

    leader = project.leader
    leader_department = (
        leader.dept.dept_name
        if leader and leader.dept
        else '未分配'
    )

    project_data = {
        'id': project.id,
        'project_no': project.project_no or '—',
        'name': project.project_name or '未命名项目',
        'leader_id': project.leader_id,
        'dept_id': project.dept_id,
        'leader': leader.real_name if leader else '未指定',
        'leader_title': leader.title if leader and leader.title else '—',
        'leader_department': leader_department,
        'department': project.dept.dept_name if project.dept else '未分配',
        'subject': project.subject or '未分类',
        'project_type': project.project_type or '未设置',
        'fund_amount': round(float(project.fund_amount or 0), 2),
        'start_date': project.start_date.isoformat() if project.start_date else None,
        'end_date': project.end_date.isoformat() if project.end_date else None,
        'status': project.status or '未设置',
        'actual_progress': int(project.actual_progress or 0),
    }

    return JsonResponse({
        'project': project_data,
        'fund_summary': {
            'actual_total': round(float(actual_fund_total), 2),
            'budget_total': round(float(budget_total), 2),
            'fund_detail_count': len(fund_details),
            'budget_record_count': len(budget_details),
        },
        'fund_details': fund_details,
        'budgets': budget_details,
        'cooperations': cooperation_records,
    })


# ==================================================
# 科研项目新建/编辑 API
# ==================================================

def project_options_api(request):
    """返回项目表单所需的负责人、部门、类型和状态选项。"""
    if request.method != 'GET':
        return JsonResponse(
            {'error': '仅支持 GET 请求'},
            status=405
        )

    leaders = []
    for user in User.objects.select_related('dept').order_by('real_name', 'id'):
        leaders.append({
            'id': user.id,
            'name': user.real_name,
            'title': user.title or '',
            'role': user.get_role_display(),
            'department': user.dept.dept_name if user.dept else '',
        })

    departments = [
        {'id': dept.id, 'name': dept.dept_name}
        for dept in Dept.objects.order_by('dept_name', 'id')
    ]

    return JsonResponse({
        'leaders': leaders,
        'departments': departments,
        'types': [
            {'value': value, 'label': label}
            for value, label in Project.TYPE_CHOICES
        ],
        'statuses': [
            {'value': value, 'label': label}
            for value, label in Project.STATUS_CHOICES
        ],
    })


def project_save_api(request):
    """
    新建或编辑科研项目。
    POST /api/project/save：新建
    PUT  /api/project/save：编辑，JSON 中需提供 id

    注意：当前项目尚未接入服务端身份认证/角色授权。该写接口仅适用于本地开发演示；
    在部署到共享服务器或公网前，必须接入真实登录并在服务端校验管理员权限。
    """
    if request.method not in ('POST', 'PUT'):
        return JsonResponse(
            {'error': '仅支持 POST 或 PUT 请求'},
            status=405
        )

    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse(
            {'error': '请求内容不是有效的 JSON 数据'},
            status=400
        )

    if not isinstance(payload, dict):
        return JsonResponse(
            {'error': '请求数据格式错误，应为 JSON 对象'},
            status=400
        )

    project = None
    if request.method == 'PUT':
        raw_id = payload.get('id')
        try:
            project_id = int(raw_id)
        except (TypeError, ValueError):
            return JsonResponse(
                {'error': '编辑项目时必须提供有效的项目 ID'},
                status=400
            )

        if project_id <= 0:
            return JsonResponse(
                {'error': '项目 ID 必须大于 0'},
                status=400
            )

        try:
            project = Project.objects.get(pk=project_id)
        except Project.DoesNotExist:
            return JsonResponse(
                {'error': '未找到要编辑的项目，该项目可能已被删除'},
                status=404
            )

    project_no = str(payload.get('project_no') or '').strip()
    project_name = str(payload.get('project_name') or '').strip()
    subject = str(payload.get('subject') or '').strip()

    if not project_no:
        return JsonResponse({'error': '项目编号不能为空'}, status=400)
    if len(project_no) > 50:
        return JsonResponse({'error': '项目编号不能超过 50 个字符'}, status=400)
    if not project_name:
        return JsonResponse({'error': '项目名称不能为空'}, status=400)
    if len(project_name) > 200:
        return JsonResponse({'error': '项目名称不能超过 200 个字符'}, status=400)
    if len(subject) > 50:
        return JsonResponse({'error': '学科分类不能超过 50 个字符'}, status=400)

    duplicate_qs = Project.objects.filter(project_no=project_no)
    if project is not None:
        duplicate_qs = duplicate_qs.exclude(pk=project.pk)
    if duplicate_qs.exists():
        return JsonResponse({'error': '该项目编号已存在，请检查后重新填写'}, status=400)

    try:
        leader_id = int(payload.get('leader_id'))
    except (TypeError, ValueError):
        return JsonResponse({'error': '请选择有效的项目负责人'}, status=400)

    try:
        leader = User.objects.get(pk=leader_id)
    except User.DoesNotExist:
        return JsonResponse({'error': '所选负责人不存在，请刷新页面后重试'}, status=400)

    raw_dept_id = payload.get('dept_id')
    dept = None
    if raw_dept_id not in (None, ''):
        try:
            dept_id = int(raw_dept_id)
        except (TypeError, ValueError):
            return JsonResponse({'error': '归属部门参数无效'}, status=400)

        try:
            dept = Dept.objects.get(pk=dept_id)
        except Dept.DoesNotExist:
            return JsonResponse({'error': '所选部门不存在，请刷新页面后重试'}, status=400)

    project_type = str(payload.get('project_type') or '').strip()
    valid_types = {value for value, _label in Project.TYPE_CHOICES}
    if project_type not in valid_types:
        return JsonResponse({'error': '请选择有效的项目类型'}, status=400)

    status_value = str(payload.get('status') or '').strip()
    valid_statuses = {value for value, _label in Project.STATUS_CHOICES}
    if status_value not in valid_statuses:
        return JsonResponse({'error': '请选择有效的项目状态'}, status=400)

    try:
        fund_amount = Decimal(str(payload.get('fund_amount') or '').strip())
    except (InvalidOperation, ValueError):
        return JsonResponse({'error': '项目经费必须是有效数字'}, status=400)

    if not fund_amount.is_finite():
        return JsonResponse({'error': '项目经费必须是有限数值'}, status=400)
    if fund_amount < 0:
        return JsonResponse({'error': '项目经费不能小于 0'}, status=400)
    if fund_amount >= Decimal('100000000'):
        return JsonResponse({'error': '项目经费超出当前字段允许的最大范围'}, status=400)
    if fund_amount.as_tuple().exponent < -2:
        return JsonResponse({'error': '项目经费最多保留两位小数'}, status=400)

    try:
        start_date = date.fromisoformat(str(payload.get('start_date') or '').strip())
    except (TypeError, ValueError):
        return JsonResponse({'error': '请选择有效的项目开始日期'}, status=400)

    try:
        end_date = date.fromisoformat(str(payload.get('end_date') or '').strip())
    except (TypeError, ValueError):
        return JsonResponse({'error': '请选择有效的项目结束日期'}, status=400)

    if start_date > end_date:
        return JsonResponse({'error': '项目开始日期不能晚于结束日期'}, status=400)

    raw_progress = str(payload.get('actual_progress', '0')).strip()
    if not re.fullmatch(r'\d{1,3}', raw_progress):
        return JsonResponse({'error': '项目进度必须为 0 至 100 的整数'}, status=400)

    actual_progress = int(raw_progress)
    if actual_progress < 0 or actual_progress > 100:
        return JsonResponse({'error': '项目进度范围应为 0 至 100'}, status=400)

    if project is None:
        project = Project()

    project.project_no = project_no
    project.project_name = project_name
    project.leader = leader
    project.dept = dept
    project.project_type = project_type
    project.fund_amount = fund_amount
    project.start_date = start_date
    project.end_date = end_date
    project.status = status_value
    project.actual_progress = actual_progress
    project.subject = subject or None
    project.save()

    return JsonResponse({
        'success': True,
        'message': '项目创建成功' if request.method == 'POST' else '项目修改成功',
        'project': {
            'id': project.id,
            'project_no': project.project_no,
            'project_name': project.project_name,
        }
    })


def fund_overview(request):
    """科研经费顶部概览：实际经费使用 FundDetail；预算只使用正式 FundBudget。"""
    year = int(request.GET.get('year', get_latest_year()))
    subject = request.GET.get('subject', 'all')

    actual_qs = FundDetail.objects.filter(year=year)
    last_actual_qs = FundDetail.objects.filter(year=year - 1)
    budget_qs = FundBudget.objects.filter(year=year, is_demo=False)
    last_budget_qs = FundBudget.objects.filter(year=year - 1, is_demo=False)

    if subject != 'all':
        actual_qs = actual_qs.filter(project__subject=subject)
        last_actual_qs = last_actual_qs.filter(project__subject=subject)
        budget_qs = budget_qs.filter(project__subject=subject)
        last_budget_qs = last_budget_qs.filter(project__subject=subject)

    total_amount = actual_qs.aggregate(total=Sum('amount'))['total'] or Decimal(0)
    last_year_total = last_actual_qs.aggregate(total=Sum('amount'))['total'] or Decimal(0)
    budget_total = budget_qs.aggregate(total=Sum('budget_amount'))['total'] or Decimal(0)
    last_budget_total = last_budget_qs.aggregate(total=Sum('budget_amount'))['total'] or Decimal(0)

    growth_rate = (
        float((total_amount - last_year_total) / last_year_total * 100)
        if last_year_total else 0
    )

    budget_available = budget_total > 0
    execution_rate = None
    surplus = None
    execution_rate_change = None

    if budget_available:
        execution_rate = float(total_amount / budget_total * 100)
        surplus = budget_total - total_amount
        if last_budget_total > 0:
            last_execution_rate = float(last_year_total / last_budget_total * 100)
            execution_rate_change = execution_rate - last_execution_rate

    return JsonResponse({
        'year': year,
        'total_amount': round(float(total_amount), 2),
        'budget_total': round(float(budget_total), 2) if budget_available else None,
        'budget_available': budget_available,
        'budget_data_mode': 'real' if budget_available else 'none',
        'budget_sources': list(
            budget_qs.order_by().values_list('data_source', flat=True).distinct()
        ),
        'execution_rate': round(execution_rate, 2) if execution_rate is not None else None,
        'execution_rate_change': (
            round(execution_rate_change, 2)
            if execution_rate_change is not None else None
        ),
        'surplus': round(float(surplus), 2) if surplus is not None else None,
        'growth_rate': round(growth_rate, 2),
    })

def fund_sankey(request):
    """桑基图数据：来源 → 学科 → 教师个人"""
    year = request.GET.get('year', get_latest_year())
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
    """年度预算执行率仪表盘：仅使用正式预算。"""
    year = int(request.GET.get('year', get_latest_year()))
    subject = request.GET.get('subject', 'all')

    actual_qs = FundDetail.objects.filter(year=year)
    budget_qs = FundBudget.objects.filter(year=year, is_demo=False)

    if subject != 'all':
        actual_qs = actual_qs.filter(project__subject=subject)
        budget_qs = budget_qs.filter(project__subject=subject)

    actual_total = actual_qs.aggregate(total=Sum('amount'))['total'] or Decimal(0)
    budget_total = budget_qs.aggregate(total=Sum('budget_amount'))['total'] or Decimal(0)

    if budget_total <= 0:
        return JsonResponse({
            'budget_available': False,
            'budget_data_mode': 'none',
            'budget_sources': [],
            'value': None,
            'actual_total': round(float(actual_total), 2),
            'budget_total': None,
        })

    rate = float(actual_total / budget_total * 100)
    return JsonResponse({
        'budget_available': True,
        'budget_data_mode': 'real',
        'budget_sources': list(
            budget_qs.order_by().values_list('data_source', flat=True).distinct()
        ),
        'value': round(rate, 2),
        'actual_total': round(float(actual_total), 2),
        'budget_total': round(float(budget_total), 2),
    })

def fund_expense_bar(request):
    """以所选年份为截止年份，展示近三年经费支出对比"""

    subject = request.GET.get('subject', 'all')

    # 如果前端没有传年份，则默认使用经费数据中的最新年份
    latest_fund_year = FundDetail.objects.aggregate(
        latest=Max('year')
    )['latest']

    if latest_fund_year is None:
        latest_fund_year = get_latest_year()

    end_year = int(
        request.GET.get(
            'year',
            latest_fund_year
        )
    )

    # 以所选年份为截止年份，向前取三年
    years = [
        end_year - 2,
        end_year - 1,
        end_year
    ]

    result = {
        year: {
            '设备费': 0,
            '业务费': 0,
            '劳务费': 0
        }
        for year in years
    }

    qs = FundDetail.objects.filter(
        year__in=years
    ).select_related('project')

    if subject != 'all':
        qs = qs.filter(
            project__subject=subject
        )

    for fd in qs:
        if (
            fd.year in result and
            fd.usage_type in result[fd.year]
        ):
            result[fd.year][fd.usage_type] += float(
                fd.amount
            )

    return JsonResponse({
        'years': years,
        'device': [
            result[year]['设备费']
            for year in years
        ],
        'business': [
            result[year]['业务费']
            for year in years
        ],
        'labor': [
            result[year]['劳务费']
            for year in years
        ],
    })

def fund_dept_ring(request):
    """各学科经费分配环形图"""
    year = request.GET.get('year', get_latest_year())
    qs = FundDetail.objects.filter(year=year).select_related('project')
    dept_funds = {}
    for fd in qs:
        sub = fd.project.subject
        if sub:
            dept_funds[sub] = dept_funds.get(sub, 0) + fd.amount
    data = [{'name': sub, 'value': round(val,2)} for sub, val in dept_funds.items()]
    return JsonResponse({'data': data})


def fund_export(request):
    """导出当前筛选条件下的科研经费明细 CSV（Excel 可直接打开）。"""
    if request.method != 'GET':
        return JsonResponse(
            {'error': '仅支持 GET 请求'},
            status=405
        )

    # 默认使用经费明细中实际存在的最新年份，避免被其他业务数据年份影响。
    raw_year = request.GET.get('year', '').strip()
    if raw_year:
        try:
            year = int(raw_year)
        except (TypeError, ValueError):
            return JsonResponse(
                {'error': '年份参数无效，请重新选择年度。'},
                status=400
            )
    else:
        year = FundDetail.objects.aggregate(latest=Max('year'))['latest']
        if year is None:
            return JsonResponse(
                {'error': '当前没有可导出的科研经费数据。'},
                status=404
            )

    subject = request.GET.get('subject', 'all')
    subject = subject.strip() if isinstance(subject, str) else 'all'

    queryset = (
        FundDetail.objects
        .filter(year=year)
        .select_related('project', 'project__leader')
        .order_by(
            'project__subject',
            'project__project_name',
            'id'
        )
    )

    if subject not in ('all', '', None, '__all__'):
        queryset = queryset.filter(project__subject=subject)

    if not queryset.exists():
        return JsonResponse(
            {
                'error': (
                    f'{year} 年当前学科筛选条件下没有可导出的科研经费明细。'
                )
            },
            status=404
        )

    response = HttpResponse(
        content_type='text/csv; charset=utf-8'
    )
    # UTF-8 BOM 可避免 Excel 打开 CSV 时中文乱码。
    response.write('\ufeff')
    response['Content-Disposition'] = (
        f'attachment; filename="fund_details_{year}.csv"'
    )

    writer = csv.writer(response)
    writer.writerow([
        '年度',
        '项目编号',
        '项目名称',
        '项目负责人',
        '学科',
        '经费来源',
        '支出类型',
        '实际金额（万元）',
    ])

    for record in queryset.iterator():
        project = record.project
        leader = getattr(project, 'leader', None) if project else None
        writer.writerow([
            record.year,
            (getattr(project, 'project_no', '') or '') if project else '',
            (getattr(project, 'project_name', '') or '') if project else '',
            getattr(leader, 'real_name', '') or '未指定',
            (getattr(project, 'subject', '') or '未分类') if project else '未分类',
            record.source_type or '未注明',
            record.usage_type or '未注明',
            format(record.amount or Decimal('0'), '.2f'),
        ])

    return response


# ==================================================
# 科研成果分析接口
# ==================================================

_ACHIEVEMENT_APPLICATION_VALUE = {
    # Achievement 模型没有独立的“应用价值”字段。
    # 为保持原有气泡图结构，这里保留按成果类型配置的参考分值；
    # 学术影响力、成果数量、年份和学科均来自数据库实际记录。
    '期刊论文': 85,
    '学术著作': 75,
    '研究报告': 65,
    '专利': 50,
    '获奖': 90,
    '决策咨询': 70,
}

# 词云采用“领域词典最长匹配”，只从标题中识别实际出现的完整主题词，
# 不再把标题机械拆成连续字片段，避免出现“的数”“的应急管”等无意义词项。
_ACHIEVEMENT_KEYWORD_PHRASES = tuple(sorted({
    '中国式现代化', '全过程人民民主', '国际共产主义运动', '中国化时代化',
    '国家治理体系', '治理能力现代化', '政府数字化转型', '公共服务均等化',
    '公共服务均衡性', '公共服务可及性', '公共服务供给', '社会保障制度',
    '公共部门算法治理', '人工智能算法', '数字技术赋能', '数字政府建设',
    '应急管理体系', '政府债务风险', '国家治理', '马克思主义', '党的建设',
    '党建引领', '思想政治教育', '自主知识体系', '标识性概念', '揭榜挂帅',
    '投资于人', '目标建构', '系统性回顾', '社区网格化', '网格化治理',
    '地方政府', '营商环境', '产业政策', '公共政策', '政策评估', '政策执行',
    '政策调适', '政策工具', '政策创新', '政策过程', '政策网络', '政策反馈',
    '政策效果', '政策扩散', '政策优化', '社会政策', '外交政策', '区块链技术',
    '区块链', '云计算', '大数据治理', '大数据', '人工智能', '数字治理',
    '数字政府', '数字经济', '数字化转型', '数字鸿沟', '数字技术', '应急管理',
    '公共安全', '风险预警', '风险治理', '风险管理', '社会风险', '社会治理',
    '社区治理', '基层治理', '智慧治理', '智能治理', '算法治理', '平台治理',
    '网络治理', '数据治理', '政府治理', '政府职能', '政府绩效', '政府债务',
    '政府创新', '政府监管', '营商环境', '公共服务', '公共管理', '公共行政',
    '行政管理', '行政改革', '行政体制改革', '机构改革', '行政审批', '行政许可',
    '政务服务', '政务公开', '绩效管理', '干部考核', '社会保障', '养老保障',
    '医疗保障', '社会救助', '民生保障', '养老服务', '教育政策', '教育公平',
    '劳动就业', '乡村振兴', '乡村治理', '城乡融合', '生态文明', '环境治理',
    '绿色发展', '基层党建', '基层协商', '社区协商', '治理模式', '协同治理',
    '治理效能', '治理体系', '治理工具', '治理能力', '制度建设', '制度创新',
    '制度变迁', '社会组织', '政治参与', '政治信任', '民主治理', '国际关系',
    '国际政治', '政治学理论', '政治发展', '共同富裕', '理论与实践', '实践维度',
    '内在机理', '可及性', '公共部门', '公共价值', '公共资源', '公共财政',
    '公共卫生', '突发事件', '社区服务', '社区建设', '社会公平', '社会福利',
    '公民参与', '社会资本', '数据安全', '隐私保护', '个人信息保护', '地方治理',
    '现代化建设', '治理创新', '中国共产党', '社会主义', '中国政治', '政策分析',
    '马克思主义理论', '行政体制', '公共服务', '数字化', '公共部门',
}, key=lambda phrase: (-len(phrase), phrase)))

_ACHIEVEMENT_ENGLISH_STOPWORDS = {
    'the', 'and', 'for', 'with', 'from', 'into', 'that', 'this', 'these',
    'those', 'are', 'was', 'were', 'been', 'being', 'have', 'has', 'had',
    'its', 'their', 'our', 'your', 'you', 'they', 'them', 'who', 'what',
    'when', 'where', 'which', 'while', 'how', 'why', 'about', 'after',
    'before', 'between', 'through', 'towards', 'toward', 'over', 'under',
    'using', 'based', 'study', 'research', 'analysis', 'evidence', 'case',
    'cases', 'approach', 'effect', 'effects', 'role', 'new', 'china',
}


def _achievement_metadata():
    """科研成果筛选元数据：只返回数据库中实际存在的年份和学科。"""
    years = sorted(
        {
            int(year)
            for year in Achievement.objects.values_list(
                'publish_year',
                flat=True
            ).distinct()
            if year is not None
        },
        reverse=True
    )
    subjects = list(
        Achievement.objects
        .exclude(subject__isnull=True)
        .exclude(subject__exact='')
        .values_list('subject', flat=True)
        .distinct()
        .order_by('subject')
    )
    subject_options = [
        {'value': subject, 'label': subject}
        for subject in subjects
    ]
    has_unclassified = Achievement.objects.filter(
        Q(subject__isnull=True) | Q(subject__exact='')
    ).exists()
    if has_unclassified:
        subject_options.append({
            'value': '__unclassified__',
            'label': '未分类'
        })

    return {
        'years': years,
        'subjects': subjects,
        'subject_options': subject_options,
        'latest_year': years[0] if years else None,
    }


def _filtered_achievement_queryset(request):
    """统一解析成果页面的年份和学科筛选条件。"""
    qs = Achievement.objects.all()

    year = request.GET.get('year', 'all')
    year = year.strip() if isinstance(year, str) else year
    if year not in ('all', '', None):
        try:
            year_value = int(year)
        except (TypeError, ValueError):
            return None, JsonResponse(
                {'error': '年份参数无效'},
                status=400
            )
        qs = qs.filter(publish_year=year_value)

    subject = request.GET.get('subject', 'all')
    subject = subject.strip() if isinstance(subject, str) else subject
    if subject not in ('all', '', None):
        if subject == '__unclassified__':
            qs = qs.filter(
                Q(subject__isnull=True) | Q(subject__exact='')
            )
        else:
            qs = qs.filter(subject=subject)

    return qs, None


def achievement_bubble(request):
    """按筛选条件统计成果类型、平均被引次数及成果数量。"""
    qs, error_response = _filtered_achievement_queryset(request)
    if error_response is not None:
        return error_response

    type_stats = qs.values('achievement_type').annotate(
        count=Count('id'),
        avg_citation=Avg('citation_count')
    ).order_by('achievement_type')

    colors = {
        '期刊论文': '#409EFF',
        '学术著作': '#48A999',
        '研究报告': '#F09868',
        '专利': '#9C27B0',
        '获奖': '#D4AF37',
        '决策咨询': '#17A2B8',
    }

    data = []
    for stat in type_stats:
        average_citation = stat['avg_citation']
        influence = (
            round(float(average_citation), 2)
            if average_citation is not None
            else 0
        )
        achievement_type = stat['achievement_type'] or '未分类'
        application_value = _ACHIEVEMENT_APPLICATION_VALUE.get(
            achievement_type,
            60
        )

        data.append({
            'name': achievement_type,
            'value': [
                influence,
                application_value,
                stat['count']
            ],
            'color': colors.get(achievement_type, '#409EFF')
        })

    response_data = {'data': data}
    response_data.update(_achievement_metadata())
    return JsonResponse(response_data)


def achievement_bar(request):
    """按真实成果年份和学科统计成果数量；默认展示最近三个有数据的年份。"""
    raw_years = request.GET.get('years', '').strip()

    available_years = sorted({
        int(year)
        for year in Achievement.objects.values_list(
            'publish_year',
            flat=True
        ).distinct()
        if year is not None
    })

    if raw_years:
        try:
            years = [
                int(value.strip())
                for value in raw_years.split(',')
                if value.strip()
            ]
        except (TypeError, ValueError):
            return JsonResponse(
                {'error': '年份参数无效'},
                status=400
            )

        # 去重并保留调用方传入的顺序，避免无意中生成过长的图表。
        years = list(dict.fromkeys(years))
        if len(years) > 10:
            return JsonResponse(
                {'error': '一次最多查询10个年份'},
                status=400
            )
    else:
        years = sorted(available_years, reverse=True)[:3]
        years.sort()

    if not years:
        return JsonResponse({
            'years': [],
            'subjects': [],
            'series': [],
            'total': 0
        })

    qs = Achievement.objects.filter(
        publish_year__in=years
    )

    grouped_counts = qs.values(
        'subject',
        'publish_year'
    ).annotate(
        count=Count('id')
    )

    subjects = sorted({
        item['subject']
        for item in grouped_counts
        if item['subject']
    })
    has_unclassified = qs.filter(
        Q(subject__isnull=True) | Q(subject__exact='')
    ).exists()
    if has_unclassified and '未分类' not in subjects:
        subjects.append('未分类')

    count_map = {}
    for item in grouped_counts:
        subject_name = item['subject'] or '未分类'
        key = (subject_name, int(item['publish_year']))
        count_map[key] = count_map.get(key, 0) + item['count']

    palette = ['#366092', '#48A999', '#F09868', '#9C27B0', '#17A2B8']
    series = []
    for index, year in enumerate(years):
        series.append({
            'name': str(year),
            'type': 'bar',
            'barMaxWidth': 48,
            'data': [
                count_map.get((subject_name, year), 0)
                for subject_name in subjects
            ],
            'itemStyle': {
                'color': palette[index % len(palette)]
            }
        })

    return JsonResponse({
        'years': years,
        'subjects': subjects,
        'series': series,
        'total': sum(
            sum(item['data'])
            for item in series
        )
    })


def achievement_top(request):
    """按被引次数排序的高影响力成果脱敏榜单。"""
    raw_limit = request.GET.get('limit', '20')
    try:
        limit = int(raw_limit)
    except (TypeError, ValueError):
        return JsonResponse(
            {'error': 'limit 必须是整数'},
            status=400
        )
    limit = max(1, min(limit, 100))

    achievements = (
        Achievement.objects
        .order_by('-citation_count', '-publish_year', 'title', 'id')[:limit]
    )

    data = []
    for rank, achievement in enumerate(achievements, 1):
        data.append({
            'rank': rank,
            'type': achievement.achievement_type or '未分类',
            # subject 是成果学科；dept 是院系，两者不能混用。
            'subject': achievement.subject or '未分类',
            'level': achievement.level or '无',
            'year': achievement.publish_year or '—',
        })

    return JsonResponse({
        'data': data,
        'total': len(data)
    })


def _achievement_title_tokens(title):
    """提取完整、有意义的成果主题词；不使用中文 n-gram 片段兜底。"""
    if not title:
        return set()

    title_text = re.sub(r'\s+', ' ', str(title)).strip()
    if not title_text:
        return set()

    result = set()

    # 领域词典最长匹配。只加入真实出现在标题中的词，不凭空生成关键词。
    # 词典按长度降序排列，因此同一位置优先识别更完整的专业术语。
    index = 0
    while index < len(title_text):
        matched_phrase = None
        for phrase in _ACHIEVEMENT_KEYWORD_PHRASES:
            if title_text.startswith(phrase, index):
                matched_phrase = phrase
                break

        if matched_phrase:
            result.add(matched_phrase)
            index += len(matched_phrase)
        else:
            index += 1

    # 英文标题按完整英文单词提取，并过滤常见虚词；不拆中文标题制造碎片。
    # 数据源中带尾部省略号的英文标题属于截断文本，不从中抽取不完整主题。
    has_trailing_ellipsis = re.search(r"(?:\.{2,}|…)\s*$", title_text) is not None
    if not has_trailing_ellipsis:
        for match in re.finditer(r"[A-Za-z][A-Za-z+#-]{2,}", title_text):
            token = match.group(0)
            normalized = token.lower().strip('-+#.')
            if len(normalized) >= 3 and normalized not in _ACHIEVEMENT_ENGLISH_STOPWORDS:
                result.add(normalized)

    return result


def achievement_wordcloud(request):
    """基于成果标题、学科和成果类型统计词云词频。"""
    qs, error_response = _filtered_achievement_queryset(request)
    if error_response is not None:
        return error_response

    word_counts = Counter()
    total = 0

    for achievement in qs.only(
        'title',
        'subject',
        'achievement_type'
    ).iterator():
        total += 1
        terms = _achievement_title_tokens(achievement.title or '')

        # 分类信息也来自当前成果记录，可补充短标题中的有效主题词。
        if achievement.subject and achievement.subject.strip():
            terms.add(achievement.subject.strip())
        if achievement.achievement_type:
            terms.add(achievement.achievement_type.strip())

        word_counts.update(terms)

    wordcloud_data = [
        {'name': word, 'value': count}
        for word, count in sorted(
            word_counts.items(),
            key=lambda item: (-item[1], item[0])
        )[:80]
    ]

    return JsonResponse({
        'data': wordcloud_data,
        'total': total,
        'source': 'achievement_titles_and_categories'
    })



# ===================== 科研成果管理 API =====================
# 当前版本使用现有 Achievement 字段，不修改数据模型、不要求数据库迁移。
# 与现有项目写接口相同，这些写接口尚未接入服务端登录/角色授权，仅用于本地开发演示。


def _achievement_management_queryset(request):
    """统一解析成果管理列表和导出的筛选条件。"""
    qs = Achievement.objects.select_related('author', 'dept').all()

    query = request.GET.get('q', '').strip()
    if len(query) > 100:
        return None, JsonResponse({'error': '搜索内容不能超过 100 个字符'}, status=400)
    if query:
        qs = qs.filter(
            Q(title__icontains=query)
            | Q(author__real_name__icontains=query)
            | Q(subject__icontains=query)
        )

    raw_year = request.GET.get('year', 'all').strip()
    if raw_year not in ('', 'all'):
        try:
            year = int(raw_year)
        except (TypeError, ValueError):
            return None, JsonResponse({'error': '年份参数无效'}, status=400)
        qs = qs.filter(publish_year=year)

    achievement_type = request.GET.get('type', 'all').strip()
    if achievement_type not in ('', 'all'):
        valid_types = {value for value, _label in Achievement.TYPE_CHOICES}
        if achievement_type not in valid_types:
            return None, JsonResponse({'error': '成果类型参数无效'}, status=400)
        qs = qs.filter(achievement_type=achievement_type)

    level = request.GET.get('level', 'all').strip()
    if level not in ('', 'all'):
        if level == '__unclassified__':
            qs = qs.filter(Q(level__isnull=True) | Q(level__exact=''))
        else:
            qs = qs.filter(level=level)

    raw_dept_id = request.GET.get('dept_id', 'all').strip()
    if raw_dept_id not in ('', 'all'):
        if raw_dept_id == '__unassigned__':
            qs = qs.filter(dept__isnull=True)
        else:
            try:
                dept_id = int(raw_dept_id)
            except (TypeError, ValueError):
                return None, JsonResponse({'error': '系别参数无效'}, status=400)
            qs = qs.filter(dept_id=dept_id)

    raw_subject = request.GET.get('subject', 'all').strip()
    if raw_subject not in ('', 'all'):
        if raw_subject == '__unclassified__':
            qs = qs.filter(Q(subject__isnull=True) | Q(subject__exact=''))
        else:
            qs = qs.filter(subject=raw_subject)

    return qs.order_by('-publish_year', '-citation_count', 'title', 'id'), None


def achievement_options_api(request):
    """返回成果登记表单和筛选器需要的真实字典数据。"""
    if request.method != 'GET':
        return JsonResponse({'error': '仅支持 GET 请求'}, status=405)

    authors = []
    for teacher in User.objects.filter(role='teacher').select_related('dept').order_by(
        'dept__dept_name', 'real_name', 'id'
    ):
        authors.append({
            'id': teacher.id,
            'name': teacher.real_name,
            'dept_id': teacher.dept_id,
            'dept_name': teacher.dept.dept_name if teacher.dept else '',
        })

    departments = [
        {'id': dept.id, 'name': dept.dept_name}
        for dept in Dept.objects.order_by('dept_name', 'id')
    ]
    years = sorted({
        int(year)
        for year in Achievement.objects.values_list('publish_year', flat=True).distinct()
        if year is not None
    }, reverse=True)
    levels = sorted({
        value.strip()
        for value in Achievement.objects.exclude(level__isnull=True).exclude(level__exact='')
        .values_list('level', flat=True).distinct()
        if value and value.strip()
    })
    subjects = sorted({
        value.strip()
        for value in Achievement.objects.exclude(subject__isnull=True).exclude(subject__exact='')
        .values_list('subject', flat=True).distinct()
        if value and value.strip()
    })

    return JsonResponse({
        'authors': authors,
        'departments': departments,
        'types': [
            {'value': value, 'label': label}
            for value, label in Achievement.TYPE_CHOICES
        ],
        'years': years,
        'levels': levels,
        'subjects': subjects,
        'has_unclassified_subject': Achievement.objects.filter(
            Q(subject__isnull=True) | Q(subject__exact='')
        ).exists(),
        'has_unclassified_level': Achievement.objects.filter(
            Q(level__isnull=True) | Q(level__exact='')
        ).exists(),
        'has_unassigned_department': Achievement.objects.filter(dept__isnull=True).exists(),
    })


def achievement_list_api(request):
    """成果管理列表：支持搜索、筛选和服务端分页。"""
    if request.method != 'GET':
        return JsonResponse({'error': '仅支持 GET 请求'}, status=405)

    qs, error_response = _achievement_management_queryset(request)
    if error_response is not None:
        return error_response

    try:
        page = int(request.GET.get('page', '1'))
        page_size = int(request.GET.get('page_size', '10'))
    except (TypeError, ValueError):
        return JsonResponse({'error': '分页参数必须为整数'}, status=400)

    if page < 1:
        return JsonResponse({'error': '页码必须大于 0'}, status=400)
    if page_size not in (10, 20, 50):
        return JsonResponse({'error': '每页条数仅支持 10、20 或 50'}, status=400)

    total = qs.count()
    pages = max(1, math.ceil(total / page_size))
    if page > pages:
        page = pages

    items = []
    start = (page - 1) * page_size
    for item in qs[start:start + page_size]:
        items.append({
            'id': item.id,
            'title': item.title or '',
            'author_id': item.author_id,
            'author_name': item.author.real_name if item.author else '未指定',
            'dept_id': item.dept_id,
            'dept_name': item.dept.dept_name if item.dept else '未分配',
            'achievement_type': item.achievement_type or '',
            'level': item.level or '',
            'publish_year': item.publish_year,
            'citation_count': item.citation_count or 0,
            'is_international': bool(item.is_international),
            'subject': item.subject or '',
        })

    return JsonResponse({
        'items': items,
        'pagination': {
            'page': page,
            'page_size': page_size,
            'total': total,
            'pages': pages,
        },
    })


def achievement_detail_api(request):
    """返回单条成果详情，用于详情查看和编辑表单回填。"""
    if request.method != 'GET':
        return JsonResponse({'error': '仅支持 GET 请求'}, status=405)

    raw_id = request.GET.get('id', '').strip()
    try:
        achievement_id = int(raw_id)
        if achievement_id <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return JsonResponse({'error': '请提供有效的成果 ID'}, status=400)

    try:
        item = Achievement.objects.select_related('author', 'dept').get(pk=achievement_id)
    except Achievement.DoesNotExist:
        return JsonResponse({'error': '未找到该成果记录'}, status=404)

    return JsonResponse({
        'item': {
            'id': item.id,
            'title': item.title or '',
            'author_id': item.author_id,
            'author_name': item.author.real_name if item.author else '未指定',
            'dept_id': item.dept_id,
            'dept_name': item.dept.dept_name if item.dept else '未分配',
            'achievement_type': item.achievement_type or '',
            'level': item.level or '',
            'publish_year': item.publish_year,
            'citation_count': item.citation_count or 0,
            'is_international': bool(item.is_international),
            'subject': item.subject or '',
        }
    })


def achievement_save_api(request):
    """登记或编辑成果。POST 新建，PUT 编辑；不提供删除接口以避免误删历史成果。"""
    if request.method not in ('POST', 'PUT'):
        return JsonResponse({'error': '仅支持 POST 或 PUT 请求'}, status=405)

    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse({'error': '请求内容不是有效的 JSON 数据'}, status=400)
    if not isinstance(payload, dict):
        return JsonResponse({'error': '请求数据格式错误，应为 JSON 对象'}, status=400)

    item = None
    if request.method == 'PUT':
        try:
            item_id = int(payload.get('id'))
            if item_id <= 0:
                raise ValueError
        except (TypeError, ValueError):
            return JsonResponse({'error': '编辑成果时必须提供有效的成果 ID'}, status=400)
        try:
            item = Achievement.objects.get(pk=item_id)
        except Achievement.DoesNotExist:
            return JsonResponse({'error': '未找到要编辑的成果记录'}, status=404)

    title = str(payload.get('title') or '').strip()
    if not title:
        return JsonResponse({'error': '成果名称不能为空'}, status=400)
    if len(title) > 200:
        return JsonResponse({'error': '成果名称不能超过 200 个字符'}, status=400)

    try:
        author_id = int(payload.get('author_id'))
        if author_id <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return JsonResponse({'error': '请选择有效的成果作者'}, status=400)
    try:
        author = User.objects.select_related('dept').get(pk=author_id, role='teacher')
    except User.DoesNotExist:
        return JsonResponse({'error': '成果作者必须是系统中的有效教师'}, status=400)

    raw_dept_id = payload.get('dept_id')
    if raw_dept_id in (None, ''):
        dept = author.dept
    else:
        try:
            dept_id = int(raw_dept_id)
        except (TypeError, ValueError):
            return JsonResponse({'error': '所属系别参数无效'}, status=400)
        try:
            dept = Dept.objects.get(pk=dept_id)
        except Dept.DoesNotExist:
            return JsonResponse({'error': '所选系别不存在，请刷新页面后重试'}, status=400)

    achievement_type = str(payload.get('achievement_type') or '').strip()
    valid_types = {value for value, _label in Achievement.TYPE_CHOICES}
    if achievement_type not in valid_types:
        return JsonResponse({'error': '请选择有效的成果类型'}, status=400)

    level = str(payload.get('level') or '').strip()
    if len(level) > 50:
        return JsonResponse({'error': '成果级别/收录信息不能超过 50 个字符'}, status=400)

    try:
        publish_year = int(payload.get('publish_year'))
    except (TypeError, ValueError):
        return JsonResponse({'error': '发表年份必须为整数'}, status=400)
    if publish_year < 1900 or publish_year > date.today().year + 1:
        return JsonResponse({'error': f'发表年份应在 1900 至 {date.today().year + 1} 年之间'}, status=400)

    try:
        citation_count = int(payload.get('citation_count', 0))
    except (TypeError, ValueError):
        return JsonResponse({'error': '被引次数必须为非负整数'}, status=400)
    if citation_count < 0 or citation_count > 2147483647:
        return JsonResponse({'error': '被引次数超出允许范围'}, status=400)

    subject = str(payload.get('subject') or '').strip()
    if len(subject) > 50:
        return JsonResponse({'error': '所属学科不能超过 50 个字符'}, status=400)

    raw_international = payload.get('is_international', False)
    if isinstance(raw_international, bool):
        is_international = raw_international
    elif raw_international in (0, 1):
        is_international = bool(raw_international)
    elif isinstance(raw_international, str) and raw_international.strip().lower() in ('true', 'false', '1', '0'):
        is_international = raw_international.strip().lower() in ('true', '1')
    else:
        return JsonResponse({'error': '国际发表标记无效'}, status=400)

    duplicate_qs = Achievement.objects.filter(
        title=title,
        author=author,
        publish_year=publish_year,
    )
    if item is not None:
        duplicate_qs = duplicate_qs.exclude(pk=item.pk)
    if duplicate_qs.exists():
        return JsonResponse({
            'error': '检测到相同成果名称、作者和发表年份的记录，请核对后再保存'
        }, status=400)

    if item is None:
        item = Achievement()
    item.title = title
    item.author = author
    item.dept = dept
    item.achievement_type = achievement_type
    item.level = level
    item.publish_year = publish_year
    item.citation_count = citation_count
    item.is_international = is_international
    item.subject = subject or None
    item.save()

    return JsonResponse({
        'success': True,
        'message': '成果登记成功' if request.method == 'POST' else '成果修改成功',
        'item': {
            'id': item.id,
            'title': item.title,
            'author_name': item.author.real_name,
            'publish_year': item.publish_year,
        }
    })


def achievement_export_api(request):
    """按当前筛选条件导出全部匹配成果为 Excel 可打开的 UTF-8 CSV。"""
    if request.method != 'GET':
        return JsonResponse({'error': '仅支持 GET 请求'}, status=405)
    qs, error_response = _achievement_management_queryset(request)
    if error_response is not None:
        return error_response

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response.write('\ufeff')
    response['Content-Disposition'] = f'attachment; filename="research_achievements_{date.today().strftime("%Y%m%d")}.csv"'
    writer = csv.writer(response)
    writer.writerow([
        '成果名称', '作者', '所属系别', '成果类型', '成果级别/收录',
        '发表年份', '被引次数', '国际发表', '所属学科', '成果ID'
    ])
    for item in qs.iterator():
        writer.writerow([
            item.title or '',
            item.author.real_name if item.author else '',
            item.dept.dept_name if item.dept else '',
            item.achievement_type or '',
            item.level or '',
            item.publish_year,
            item.citation_count or 0,
            '是' if item.is_international else '否',
            item.subject or '',
            item.id,
        ])
    return response



# ===================== 教师版智能分析 API =====================


def _teacher_from_request(request):
    """校验 teacher_id，并返回真实教师对象或标准错误响应。"""
    raw_teacher_id = request.GET.get('teacher_id', '').strip()
    if not raw_teacher_id:
        return None, JsonResponse({'error': '缺少 teacher_id 参数'}, status=400)

    try:
        teacher_id = int(raw_teacher_id)
        if teacher_id <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return None, JsonResponse({'error': 'teacher_id 必须是正整数'}, status=400)

    try:
        teacher = User.objects.select_related('dept').get(
            pk=teacher_id,
            role='teacher'
        )
    except User.DoesNotExist:
        return None, JsonResponse({'error': '未找到该教师'}, status=404)

    return teacher, None


def _teacher_data_years(teacher):
    return teacher_real_years(teacher)

def teacher_directory(request):
    query = request.GET.get('q', '').strip()
    teachers = User.objects.filter(role='teacher').select_related('dept')
    if query:
        teachers = teachers.filter(
            Q(real_name__icontains=query)
            | Q(title__icontains=query)
            | Q(dept__dept_name__icontains=query)
        )
    teachers = teachers.order_by('dept__dept_name', 'real_name', 'id')
    data = []
    for teacher in teachers:
        metrics = teacher_research_metrics(teacher)
        data.append({
            'id': teacher.id,
            'real_name': teacher.real_name,
            'title': teacher.title or '',
            'dept': teacher.dept.dept_name if teacher.dept else '未分配',
            'project_count': metrics['project_count'],
            'achievement_count': metrics['achievements_count'],
        })
    return JsonResponse({'teachers': data, 'total': len(data)})

def teacher_info(request):
    teacher, error_response = _teacher_from_request(request)
    if error_response is not None:
        return error_response
    metrics = teacher_research_metrics(teacher)
    return JsonResponse({
        'id': teacher.id,
        'real_name': teacher.real_name,
        'title': teacher.title or '',
        'dept': teacher.dept.dept_name if teacher.dept else '未分配',
        'join_year': None,
        'project_count': metrics['project_count'],
        'ongoing_projects': metrics['ongoing_projects'],
        'fund_total': metrics['fund_total'],
        'achievements_count': metrics['achievements_count'],
        'total_citation': metrics['total_citation'],
        'h_index': metrics['h_index'],
        'cooperation_count': metrics['cooperation_count'],
        'comprehensive': metrics['comprehensive'],
        'score_year': metrics['score_year'],
        'growth_rate': metrics['growth_rate'],
        'years': metrics['years'],
        'score_years': metrics['score_years'],
        'latest_year': metrics['years'][-1] if metrics['years'] else None,
        'score_is_demo': False,
        'growth_rate_is_demo': False,
        'demo_score_count': 0,
        'demo_cooperation_count': 0,
        'existing_cooperation_count': metrics['cooperation_count'],
        'has_demo_score_data': False,
        'has_demo_cooperation_data': False,
        'has_demo_data': False,
    })

def teacher_trend(request):
    teacher, error_response = _teacher_from_request(request)
    if error_response is not None:
        return error_response
    trend_type = request.GET.get('type', '5year')
    limits = {'5year': 5, '3year': 3, 'all': None}
    if trend_type not in limits:
        return JsonResponse({'error': 'type 仅支持 5year、3year 或 all'}, status=400)
    years = teacher_real_years(teacher)
    limit = limits[trend_type]
    if limit is not None:
        years = years[-limit:]
    score_map = {}
    for score in teacher_real_score_rows(teacher):
        score_map[score.year] = score
    scores = []
    projects = []
    achievements = []
    for year in years:
        score = score_map.get(year)
        scores.append(round(float(score.comprehensive_score), 2) if score else None)
        projects.append(Project.objects.filter(leader=teacher, start_date__year=year).count())
        achievements.append(Achievement.objects.filter(author=teacher, publish_year=year).count())
    return JsonResponse({
        'years': years,
        'scores': scores,
        'projects': projects,
        'achievements': achievements,
        'score_is_demo': [False for _ in years],
        'score_data_sources': ['formal' if value is not None else None for value in scores],
        'has_demo_scores': False,
    })

def teacher_ability(request):
    teacher, error_response = _teacher_from_request(request)
    if error_response is not None:
        return error_response
    raw_year = request.GET.get('year', '').strip()
    scores = teacher_real_score_rows(teacher)
    if raw_year:
        try:
            year = int(raw_year)
        except (TypeError, ValueError):
            return JsonResponse({'error': 'year 必须是有效年份'}, status=400)
    else:
        year = scores.order_by('-year', '-id').values_list('year', flat=True).first()
    if year is None:
        return JsonResponse({'year': None, 'data': [], 'is_demo': False, 'data_source': None})
    score = scores.filter(year=year).order_by('-id').first()
    if score is None:
        return JsonResponse({'year': year, 'data': [], 'is_demo': False, 'data_source': None})
    return JsonResponse({
        'year': year,
        'data': [
            {'name': '科研得分', 'value': round(float(score.research_score), 2)},
            {'name': '教学得分', 'value': round(float(score.teaching_score), 2)},
            {'name': '服务得分', 'value': round(float(score.service_score), 2)},
        ],
        'is_demo': False,
        'data_source': score.data_source or 'formal',
    })

def teacher_projects_progress(request):
    """返回该教师全部项目的实际状态、进度和时间信息。"""
    teacher, error_response = _teacher_from_request(request)
    if error_response is not None:
        return error_response

    projects = Project.objects.filter(leader=teacher).order_by('-start_date', 'project_name')
    data = [
        {
            'id': project.id,
            'project_no': project.project_no or '',
            'name': project.project_name,
            'progress': project.actual_progress,
            'status': project.status or '未设置',
            'project_type': project.project_type or '未设置',
            'fund_amount': round(float(project.fund_amount or 0), 2),
            'start_date': project.start_date.isoformat() if project.start_date else None,
            'end_date': project.end_date.isoformat() if project.end_date else None,
        }
        for project in projects
    ]
    return JsonResponse({'data': data, 'total': len(data)})


def teacher_achievement_types(request):
    """按选定年份统计该教师实际成果类型；不把成果类型替换成推测的期刊等级。"""
    teacher, error_response = _teacher_from_request(request)
    if error_response is not None:
        return error_response

    raw_year = request.GET.get('year', '').strip()
    queryset = Achievement.objects.filter(author=teacher)
    year = None
    if raw_year:
        try:
            year = int(raw_year)
        except (TypeError, ValueError):
            return JsonResponse({'error': 'year 必须是有效年份'}, status=400)
        queryset = queryset.filter(publish_year=year)

    grouped = queryset.values('achievement_type').annotate(
        count=Count('id')
    ).order_by('-count', 'achievement_type')
    data = [
        {'name': item['achievement_type'] or '未分类', 'value': item['count']}
        for item in grouped
    ]
    return JsonResponse({
        'year': year,
        'data': data,
        'total': sum(item['value'] for item in data),
    })


def teacher_fund_usage(request):
    """返回该教师真实经费分类汇总和年度汇总；支持按项目 ID 筛选。"""
    teacher, error_response = _teacher_from_request(request)
    if error_response is not None:
        return error_response

    projects = Project.objects.filter(leader=teacher).order_by('project_name', 'id')
    queryset = FundDetail.objects.filter(project__leader=teacher)

    raw_project_id = request.GET.get('project_id', '').strip()
    if raw_project_id:
        try:
            project_id = int(raw_project_id)
        except (TypeError, ValueError):
            return JsonResponse({'error': 'project_id 必须是有效整数'}, status=400)
        if not projects.filter(pk=project_id).exists():
            return JsonResponse({'error': '该项目不属于所选教师或项目不存在'}, status=404)
        queryset = queryset.filter(project_id=project_id)
    else:
        # 兼容旧页面曾使用的 project_name 参数。
        project_name = request.GET.get('project_name', '').strip()
        if project_name and project_name != 'all':
            queryset = queryset.filter(project__project_name=project_name)

    categories = [choice[0] for choice in FundDetail.USAGE_CHOICES]
    usage_totals = queryset.values('usage_type').annotate(total=Sum('amount'))
    usage_map = {
        item['usage_type']: float(item['total'] or 0)
        for item in usage_totals
    }
    values = [round(usage_map.get(category, 0), 2) for category in categories]

    yearly_totals = queryset.values('year').annotate(
        total=Sum('amount')
    ).order_by('year')
    year_totals = [
        {'year': item['year'], 'total': round(float(item['total'] or 0), 2)}
        for item in yearly_totals
    ]

    project_options = [
        {'id': project.id, 'name': project.project_name}
        for project in projects
    ]
    return JsonResponse({
        'categories': categories,
        'values': values,
        'has_data': queryset.exists(),
        'year_totals': year_totals,
        'projects': project_options,
    })


def _get_project_risk_info(project, today):
    """根据项目真实进度和结题日期识别风险；只计算结果，不写入数据库。"""
    progress = int(project.actual_progress or 0)
    end_date = project.end_date
    days_remaining = (end_date - today).days if end_date else None

    reasons = []
    suggestions = []
    high_risk = False

    # 进度风险：沿用原有低于50%的提醒范围，并区分高、中风险。
    if progress < 30:
        reasons.append('项目实际进度低于30%')
        suggestions.append('优先核对项目任务安排与实际进度')
        high_risk = True
    elif progress < 50:
        reasons.append('项目实际进度低于50%')
        suggestions.append('关注阶段性任务并及时更新进度')

    # 期限风险：仅对在研、立项项目调用本函数。
    if days_remaining is not None:
        if days_remaining < 0:
            reasons.append('已超过计划结题日期，项目仍处于在研或立项状态')
            suggestions.append('核实逾期原因并确认项目当前状态')
            high_risk = True
        elif days_remaining <= 7:
            reasons.append('距离计划结题日期不超过7天')
            suggestions.append('尽快核对结题材料与验收安排')
            high_risk = True
        elif days_remaining <= 30:
            reasons.append('距离计划结题日期不超过30天')
            suggestions.append('提前准备结题材料和验收工作')

    if not reasons:
        return None

    return {
        'project_id': project.id,
        'project_no': project.project_no or '—',
        'project_name': project.project_name,
        'end_date': end_date.strftime('%Y-%m-%d') if end_date else '—',
        'status': project.status,
        'progress': progress,
        'days_remaining': days_remaining,
        'risk_level': '高' if high_risk else '中',
        'risk_reason': '；'.join(reasons),
        'suggestion': '；'.join(suggestions),
    }


def teacher_risk_warnings(request):
    """教师个人科研风险预警：依据本人项目进度和结题期限动态计算。"""
    teacher, error_response = _teacher_from_request(request)
    if error_response is not None:
        return error_response

    today = date.today()
    projects = Project.objects.filter(
        leader=teacher,
        status__in=['在研', '立项'],
    ).select_related('leader').order_by('end_date', 'project_name')

    warnings = []
    for project in projects:
        risk_info = _get_project_risk_info(project, today)
        if risk_info is not None:
            warnings.append(risk_info)

    warnings.sort(key=lambda item: (
        0 if item['risk_level'] == '高' else 1,
        item['days_remaining'] if item['days_remaining'] is not None else 999999,
        item['project_name'],
    ))

    return JsonResponse({
        'warnings': warnings,
        'total': len(warnings),
        'high_risk_count': sum(1 for item in warnings if item['risk_level'] == '高'),
        'medium_risk_count': sum(1 for item in warnings if item['risk_level'] == '中'),
        'check_date': today.strftime('%Y-%m-%d'),
    })


# ==================== 管理员版智能分析 API ====================


def admin_perf_bubble(request):
    """全院绩效气泡图数据（科研能力 vs 教学质量，气泡大小=综合得分）"""
    year = request.GET.get('year', '2024')
    teachers = User.objects.filter(role='teacher')

    if year == 'all':
        # 取近5年平均 (2021-2025)
        years = [2021, 2022, 2023, 2024, 2025]
        result = []
        for t in teachers:
            scores = TeacherScore.objects.filter(
                teacher=t, year__in=years, is_demo=False
            )
            if not scores.exists():
                continue
            avg_research = scores.aggregate(avg=Avg('research_score'))['avg'] or 0
            avg_teaching = scores.aggregate(avg=Avg('teaching_score'))['avg'] or 0
            avg_compre = scores.aggregate(avg=Avg('comprehensive_score'))['avg'] or 0
            result.append({
                'teacher_id': t.id,
                'name': t.real_name,
                'value': [round(float(avg_research), 1), round(float(avg_teaching), 1), round(float(avg_compre), 1)]
            })
        return JsonResponse({'data': result})
    else:
        year = int(year)
        scores = TeacherScore.objects.filter(
            year=year, is_demo=False
        ).select_related('teacher')
        data = []
        for s in scores:
            data.append({
                'teacher_id': s.teacher_id,
                'name': s.teacher.real_name,
                'value': [float(s.research_score), float(s.teaching_score), float(s.comprehensive_score)]
            })
        return JsonResponse({'data': data})


def admin_rank(request):
    """全院教师教学/科研/服务得分排行（取前12名）"""
    year = int(request.GET.get('year', '2024'))
    scores = TeacherScore.objects.filter(
        year=year, is_demo=False
    ).select_related('teacher').order_by('-comprehensive_score')[:12]
    names = [s.teacher.real_name[0] for s in scores]  # 取姓氏（或全名，视情况）
    teach = [float(s.teaching_score) for s in scores]
    research = [float(s.research_score) for s in scores]
    service = [float(s.service_score) for s in scores]
    return JsonResponse({'names': names, 'teach': teach, 'research': research, 'service': service})



def admin_trend(request):
    """全院年度绩效趋势：只统计正式 TeacherScore。"""
    rows = (
        TeacherScore.objects.filter(is_demo=False)
        .values('year')
        .annotate(avg=Avg('comprehensive_score'))
        .order_by('year')
    )
    years = [str(item['year']) for item in rows if item['avg'] is not None]
    scores = [round(float(item['avg']), 2) for item in rows if item['avg'] is not None]
    return JsonResponse({
        'months': years,
        'years': years,
        'scores': scores,
        'granularity': 'year',
    })

def admin_develop(request):
    """全院发展轨迹：返回真实项目数、成果数和实际经费。"""
    year_candidates = set(
        y for y in Project.objects.values_list('start_date__year', flat=True) if y
    )
    year_candidates.update(
        y for y in Achievement.objects.values_list('publish_year', flat=True) if y
    )
    year_candidates.update(
        y for y in FundDetail.objects.values_list('year', flat=True) if y
    )
    years = sorted(year_candidates)[-5:] if year_candidates else get_recent_years(5)

    project_counts = []
    achievement_counts = []
    fund_totals = []
    for year in years:
        project_counts.append(Project.objects.filter(start_date__year=year).count())
        achievement_counts.append(Achievement.objects.filter(publish_year=year).count())
        total = (
            FundDetail.objects.filter(year=year)
            .aggregate(total=Sum('amount'))['total']
            or Decimal('0')
        )
        fund_totals.append(round(float(total), 2))

    return JsonResponse({
        'years': years,
        'scale': project_counts,
        'project_counts': project_counts,
        'achievements': achievement_counts,
        'funds': fund_totals,
        'fund_unit': '万元',
    })

def admin_heat(request):
    """教师科研表现热力图：直接使用正式科研得分，不估算晋升概率。"""
    year = int(request.GET.get('year', '2024'))
    titles = ['教授', '副教授', '讲师', '助教', '其他']
    scores = (
        TeacherScore.objects.filter(year=year, is_demo=False)
        .select_related('teacher')
        .order_by('-research_score', 'teacher__real_name')
    )

    data = []
    y_axis_labels = []
    for idx, score in enumerate(scores):
        teacher = score.teacher
        title = teacher.title if teacher.title in titles[:-1] else '其他'
        data.append([titles.index(title), idx, round(float(score.research_score), 1)])
        y_axis_labels.append(teacher.real_name)

    return JsonResponse({
        'data': data,
        'xAxis': titles,
        'yAxis': y_axis_labels,
        'metric': 'research_score',
        'year': year,
    })

def admin_teacher_status(request):
    """基于最新正式综合得分的教师绩效分层。"""
    latest_year = (
        TeacherScore.objects.filter(is_demo=False)
        .aggregate(max_year=Max('year'))['max_year']
    )
    if latest_year is None:
        return JsonResponse({'year': None, 'high': [], 'middle': [], 'low': [], 'total': 0})

    scores = (
        TeacherScore.objects.filter(year=latest_year, is_demo=False)
        .select_related('teacher')
        .order_by('-comprehensive_score', 'teacher__real_name')
    )

    high, middle, low = [], [], []
    for score in scores:
        item = {
            'teacher_id': score.teacher_id,
            'name': score.teacher.real_name,
            'score': round(float(score.comprehensive_score), 1),
        }
        if item['score'] >= 85:
            high.append(item)
        elif item['score'] >= 60:
            middle.append(item)
        else:
            low.append(item)

    return JsonResponse({
        'year': latest_year,
        'high': high,
        'middle': middle,
        'low': low,
        'total': len(high) + len(middle) + len(low),
    })


def admin_progress_gauge(request):
    """全院科研整体进度（所有在研/立项项目的平均进度）"""
    projects = Project.objects.filter(status__in=['在研', '立项'])
    if not projects.exists():
        avg_progress = 0
    else:
        total_progress = sum(p.actual_progress for p in projects)
        avg_progress = round(total_progress / len(projects), 1)
    return JsonResponse({'value': avg_progress})

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
    """全院科研风险项目预警：统一使用项目进度和结题期限规则。"""
    today = date.today()
    projects = Project.objects.filter(
        status__in=['在研', '立项'],
    ).select_related('leader').order_by('end_date', 'project_name')

    data = []
    for project in projects:
        risk_info = _get_project_risk_info(project, today)
        if risk_info is None:
            continue
        risk_info['leader'] = project.leader.real_name
        data.append(risk_info)

    data.sort(key=lambda item: (
        0 if item['risk_level'] == '高' else 1,
        item['days_remaining'] if item['days_remaining'] is not None else 999999,
        item['project_name'],
    ))

    return JsonResponse({
        'data': data,
        'total': len(data),
        'high_risk_count': sum(1 for item in data if item['risk_level'] == '高'),
        'medium_risk_count': sum(1 for item in data if item['risk_level'] == '中'),
        'check_date': today.strftime('%Y-%m-%d'),
    })

def _filtered_dept_scope(dept, year_param):
    projects = Project.objects.filter(dept=dept)
    achievements = Achievement.objects.filter(dept=dept)
    if year_param != 'all':
        year = int(year_param)
        projects = projects.filter(start_date__year=year)
        achievements = achievements.filter(publish_year=year)
    return projects, achievements


def _keyword_counts(projects_qs, achievements_qs, mapping):
    counts = []
    for label, keywords in mapping:
        q_project = Q()
        q_achievement = Q()
        for keyword in keywords:
            q_project |= Q(project_name__icontains=keyword)
            q_achievement |= Q(title__icontains=keyword)
        counts.append(
            projects_qs.filter(q_project).count()
            + achievements_qs.filter(q_achievement).count()
        )
    return counts


def _relative_activity(values):
    if not values or max(values) <= 0:
        return [0 for _ in values]
    max_value = max(values)
    return [round(v / max_value * 100, 1) for v in values]


def _wordcloud_from_titles(projects_qs, achievements_qs, vocabulary, limit=30):
    data = []
    for word in vocabulary:
        count = (
            projects_qs.filter(project_name__icontains=word).count()
            + achievements_qs.filter(title__icontains=word).count()
        )
        if count > 0:
            data.append({'name': word, 'value': count})
    data.sort(key=lambda item: (-item['value'], item['name']))
    return data[:limit]


def _growth_rate(current, previous):
    if previous in (None, 0):
        return None
    return round((current - previous) / previous * 100, 1)



def _dept_scope(dept, year_param):
    projects = Project.objects.filter(dept=dept)
    achievements = Achievement.objects.filter(dept=dept)
    if year_param != 'all':
        year = int(year_param)
        projects = projects.filter(start_date__year=year)
        achievements = achievements.filter(publish_year=year)
    return projects, achievements

def _activity_percent(values):
    if not values or max(values) <= 0:
        return [0 for _ in values]
    mx=max(values)
    return [round(v/mx*100,1) for v in values]

def _growth(current, previous):
    if not previous:
        return None
    return round((current-previous)/previous*100,1)

def dept_science(request):
    year_param=request.GET.get('year','all')
    try: dept=Dept.objects.get(dept_name='科学社会主义系')
    except Dept.DoesNotExist: return JsonResponse({'error':'科学社会主义系不存在'},status=404)
    projects=Project.objects.filter(dept=dept)
    achievements=Achievement.objects.filter(dept=dept)
    scoped_p,scoped_a=_dept_scope(dept,year_param)
    funds=FundDetail.objects.filter(project__dept=dept)
    teachers=User.objects.filter(dept=dept,role='teacher')

    pie=list(scoped_a.values('achievement_type').annotate(value=Count('id')).values(name=F('achievement_type'),value=F('value')))
    categories=['国家级','省部级','横向','校级']
    values=[scoped_p.filter(project_type=x).count() for x in categories]
    cloud=keyword_cloud(list(scoped_p)+list(scoped_a))

    labels=['中国特色社会主义','国家治理与现代化','党的建设与政党治理','共同富裕与社会发展','马克思主义理论']
    raw=direction_counts(list(scoped_p)+list(scoped_a),labels)

    years=list(range(2021,2026))
    series=[]
    for typ in ['期刊论文','学术著作','研究报告','决策咨询','获奖']:
        series.append({'name':typ,'data':[achievements.filter(publish_year=y,achievement_type=typ).count() for y in years]})

    latest=TeacherScore.objects.filter(teacher__dept=dept,is_demo=False).aggregate(v=Max('year'))['v']
    bubbles=[]
    if latest:
        for s in TeacherScore.objects.filter(teacher__dept=dept,is_demo=False,year=latest).select_related('teacher'):
            bubbles.append({'teacher_id':s.teacher_id,'name':s.teacher.real_name,'value':[float(s.research_score),float(s.teaching_score),float(s.comprehensive_score)]})

    return JsonResponse({
      'stat_cards':{
        'teacher_count':teachers.count(),'project_count':projects.count(),
        'total_fund':round(float(funds.aggregate(v=Sum('amount'))['v'] or 0),2),
        'achievement_count':achievements.count(),
        'national_ratio':round(projects.filter(project_type='国家级').count()/projects.count()*100,1) if projects.count() else 0,
        'young_output_rate':round(achievements.filter(author__title__in=['讲师','助教']).count()/achievements.count()*100,1) if achievements.count() else 0,
      },
      'pie_data':pie,'bar_categories':categories,'bar_values':values,
      'wordcloud_data':cloud,'radar_labels':labels,'radar_data':_activity_percent(raw),
      'trend_years':years,'trend_series':series,'bubble_data':bubbles,
      'achievements_table':[{'序号':i,'成果名称':a.title,'负责人':a.author.real_name,'类型':a.achievement_type,'年份':a.publish_year} for i,a in enumerate(scoped_a.select_related('author').order_by('-publish_year','id')[:10],1)],
      'projects_table':[{'项目名称':x.project_name,'负责人':x.leader.real_name,'级别':x.project_type,'进度':f'{x.actual_progress}%','状态':x.status} for x in scoped_p.select_related('leader').filter(project_type='国家级')[:15]],
    })

def dept_political(request):
    year_param=request.GET.get('year','all')
    try: dept=Dept.objects.get(dept_name='政治学系')
    except Dept.DoesNotExist: return JsonResponse({'error':'政治学系不存在'},status=404)
    projects=Project.objects.filter(dept=dept); achievements=Achievement.objects.filter(dept=dept); funds=FundDetail.objects.filter(project__dept=dept)
    scoped_p,scoped_a=_dept_scope(dept,year_param)

    years=list(range(2021,2026))
    fund_trend={'all':[],'national':[],'provincial':[],'school':[],'horizontal':[]}
    for y in years:
        vals={}
        for typ,key in [('国家级','national'),('省部级','provincial'),('校级','school'),('横向','horizontal')]:
            vals[key]=float(funds.filter(year=y,project__project_type=typ).aggregate(v=Sum('amount'))['v'] or 0)
            fund_trend[key].append(round(vals[key],2))
        fund_trend['all'].append(round(sum(vals.values()),2))

    ring=list(scoped_a.values('achievement_type').annotate(value=Count('id')).values(name=F('achievement_type'),value=F('value')))
    level_rows=list(scoped_a.exclude(level='').values('level').annotate(count=Count('id')).order_by('-count','level'))
    missing=scoped_a.filter(Q(level='')|Q(level__isnull=True)).count()
    categories=[r['level'] for r in level_rows]; values=[r['count'] for r in level_rows]
    if missing: categories.append('未填写'); values.append(missing)

    labels=['政治思想与理论','比较政治与制度','政党政治','民主与治理','公共政策与智库']
    raw=direction_counts(list(scoped_p)+list(scoped_a),labels)

    y24=achievements.filter(publish_year=2024,level='CSSCI').count()
    y23=achievements.filter(publish_year=2023,level='CSSCI').count()

    return JsonResponse({
      'stat_cards':{
        'teacher_count':User.objects.filter(dept=dept,role='teacher').count(),
        'project_count':projects.count(),'total_fund':round(float(funds.aggregate(v=Sum('amount'))['v'] or 0),2),
        'achievement_count':achievements.count(),
        'high_level_ratio':round(projects.filter(project_type__in=['国家级','省部级']).count()/projects.count()*100,1) if projects.count() else 0,
        'csci_growth':_growth(y24,y23)
      },
      'fund_trend':fund_trend,'fund_years':years,'ring_data':ring,
      'bar_categories':categories,'bar_values':values,'bar_title':'成果级别 / 收录分布',
      'radar_labels':labels,'radar_data':_activity_percent(raw),
      'wordcloud_data':keyword_cloud(list(scoped_p)+list(scoped_a)),
      'achievements_table':[{'序号':i,'成果名称':a.title,'负责人':a.author.real_name,'成果类型':a.achievement_type,'年度':a.publish_year} for i,a in enumerate(scoped_a.select_related('author').order_by('-publish_year','id')[:10],1)],
      'projects_table':[{'项目名称':x.project_name,'负责人':x.leader.real_name,'项目类型':x.project_type,'进度':f'{x.actual_progress}%','状态':x.status} for x in scoped_p.select_related('leader').filter(project_type__in=['省部级','横向'],status__in=['在研','立项'])[:15]],
    })

def dept_international(request):
    year_param = request.GET.get('year', 'all')
    try:
        dept = Dept.objects.get(dept_name='国际政治系')
    except Dept.DoesNotExist:
        return JsonResponse({'error': '国际政治系不存在'}, status=404)

    projects = Project.objects.filter(dept=dept)
    achievements = Achievement.objects.filter(dept=dept)
    funds = FundDetail.objects.filter(project__dept=dept)
    scoped_p, scoped_a = _dept_scope(dept, year_param)

    international_directions = [
        '地缘政治与区域格局',
        '大国关系与战略竞争',
        '全球治理与国际组织',
        '区域国别研究',
        '国际安全',
    ]

    project_signal = (
        (~Q(region__isnull=True) & ~Q(region='')) |
        (~Q(country_or_region__isnull=True) & ~Q(country_or_region='')) |
        Q(research_direction__in=international_directions) |
        Q(project_name__icontains='国际') |
        Q(project_name__icontains='国别') |
        Q(project_name__icontains='全球') |
        Q(project_name__icontains='中美') |
        Q(project_name__icontains='地缘') |
        Q(project_name__icontains='一带一路') |
        Q(project_name__icontains='涉外') |
        Q(project_name__icontains='海外') |
        Q(project_name__icontains='区域')
    )

    foreign_projects = projects.filter(project_signal).distinct()
    active_foreign_projects = foreign_projects.filter(status__in=['在研', '立项'])

    achievement_signal = (
        Q(is_international=True) |
        (~Q(region__isnull=True) & ~Q(region='')) |
        (~Q(country_or_region__isnull=True) & ~Q(country_or_region='')) |
        Q(research_direction__in=international_directions)
    )
    foreign_achievements = achievements.filter(achievement_signal).distinct()

    geo_tokens = set()
    for row in list(scoped_p.only('country_or_region', 'region')) + list(scoped_a.only('country_or_region', 'region')):
        country = (row.country_or_region or '').strip()
        region = (row.region or '').strip()
        if country:
            for token in re.split(r'[、,，;/；\s]+', country):
                if token:
                    geo_tokens.add(token)
        elif region:
            geo_tokens.add(region)

    country_coverage = len(geo_tokens) if geo_tokens else None

    foreign_project_ids = foreign_projects.values_list('id', flat=True)
    total_foreign_fund = funds.filter(project_id__in=foreign_project_ids).aggregate(
        total=Sum('amount')
    )['total'] or Decimal(0)

    national_foreign_ratio = (
        round(
            foreign_projects.filter(project_type='国家级').count()
            / foreign_projects.count() * 100,
            1
        )
        if foreign_projects.exists()
        else 0
    )

    latest_year = projects.aggregate(max_year=Max('start_date__year'))['max_year']
    foreign_growth = None
    if latest_year:
        current_count = foreign_projects.filter(start_date__year=latest_year).count()
        previous_count = foreign_projects.filter(start_date__year=latest_year - 1).count()
        foreign_growth = _growth(current_count, previous_count)

    years = list(range(2021, 2026))
    foreign_funds, domestic_funds = [], []
    for year in years:
        total = funds.filter(year=year).aggregate(total=Sum('amount'))['total'] or Decimal(0)
        foreign = funds.filter(
            year=year,
            project_id__in=foreign_project_ids
        ).aggregate(total=Sum('amount'))['total'] or Decimal(0)
        foreign_funds.append(round(float(foreign), 2))
        domestic_funds.append(round(float(total - foreign), 2))

    direction_labels = international_directions
    direction_values = direction_counts(
        list(scoped_p) + list(scoped_a),
        direction_labels
    )

    regions, region_values = geo_counts(list(scoped_p) + list(scoped_a))

    ring_data = list(
        scoped_a.filter(achievement_signal)
        .values('achievement_type')
        .annotate(value=Count('id'))
        .values(name=F('achievement_type'), value=F('value'))
        .order_by('-value', 'name')
    )

    radar_values = _activity_percent(direction_values)
    wordcloud_data = keyword_cloud(list(scoped_p) + list(scoped_a))

    achievement_rows = (
        scoped_a.filter(achievement_signal)
        .select_related('author')
        .order_by('-publish_year', 'id')[:10]
    )
    achievements_table = [{
        '序号': idx,
        '成果名称': ach.title,
        '负责人': ach.author.real_name,
        '成果类型': ach.achievement_type,
        '发布年份': ach.publish_year,
    } for idx, ach in enumerate(achievement_rows, 1)]

    project_rows = (
        scoped_p.filter(project_signal)
        .filter(status__in=['在研', '立项'])
        .select_related('leader')
        .order_by('-start_date', 'id')[:15]
    )
    projects_table = [{
        '项目名称': proj.project_name,
        '负责人': proj.leader.real_name,
        '项目类型': proj.project_type,
        '进度': f'{proj.actual_progress}%',
        '状态': proj.status,
    } for proj in project_rows]

    return JsonResponse({
        'stat_cards': {
            'country_coverage': country_coverage,
            'international_projects': active_foreign_projects.count(),
            'total_foreign_fund': round(float(total_foreign_fund), 2),
            'international_publications': foreign_achievements.count(),
            'national_foreign_ratio': national_foreign_ratio,
            'academic_exchange_growth': foreign_growth,
        },
        'fund_trend': {
            'years': years,
            'domestic': domestic_funds,
            'foreign': foreign_funds,
        },
        'continents': direction_labels,
        'continent_data': direction_values,
        'continent_available': any(direction_values),
        'region_labels': regions,
        'region_values': region_values,
        'identified_geo': sorted(geo_tokens),
        'ring_data': ring_data,
        'radar_labels': direction_labels,
        'radar_data': radar_values,
        'wordcloud_data': wordcloud_data,
        'achievements_table': achievements_table,
        'projects_table': projects_table,
    })

def dept_public(request):
    year_param=request.GET.get('year','all')
    try: dept=Dept.objects.get(dept_name='公共管理系')
    except Dept.DoesNotExist: return JsonResponse({'error':'公共管理系不存在'},status=404)
    projects=Project.objects.filter(dept=dept); achievements=Achievement.objects.filter(dept=dept); funds=FundDetail.objects.filter(project__dept=dept)
    scoped_p,scoped_a=_dept_scope(dept,year_param)

    years=list(range(2021,2026))
    vertical=[round(float(funds.filter(year=y,project__project_type__in=['国家级','省部级']).aggregate(v=Sum('amount'))['v'] or 0),2) for y in years]
    horizontal=[round(float(funds.filter(year=y,project__project_type='横向').aggregate(v=Sum('amount'))['v'] or 0),2) for y in years]

    labels=['数字治理','公共政策','社区与基层治理','应急与风险治理','公共服务与社会保障','政府改革与行政管理']
    raw=direction_counts(list(scoped_p)+list(scoped_a),labels)
    achievement_raw=direction_counts(list(scoped_a),labels)

    source_map=[('国家级课题','国家级'),('省部级课题','省部级'),('横向课题','横向'),('校级课题','校级')]
    pie=[{'name':name,'value':scoped_p.filter(project_type=typ).count()} for name,typ in source_map]
    pie=[x for x in pie if x['value']>0]

    latest=projects.aggregate(v=Max('start_date__year'))['v']
    cg=None
    if latest:
        cg=_growth(projects.filter(start_date__year=latest,research_direction='社区与基层治理').count(),
                   projects.filter(start_date__year=latest-1,research_direction='社区与基层治理').count())

    result_years=years
    journal=[achievements.filter(publish_year=y,achievement_type='期刊论文').count() for y in years]
    mono=[achievements.filter(publish_year=y,achievement_type='学术著作').count() for y in years]
    report=[achievements.filter(publish_year=y,achievement_type='研究报告').count() for y in years]

    ranked=sorted(zip(labels,raw),key=lambda x:(-x[1],x[0]))
    active=[x for x in ranked if x[1]>0]
    if active:
        summary=f'当前记录中，{active[0][0]}关联项目/成果最多（{active[0][1]}条）。'
        weak=f'相对较少的方向为{active[-1][0]}（{active[-1][1]}条）。'
        suggest='建议结合现有项目和成果结构，继续完善相对薄弱方向的课题与成果布局。'
    else:
        summary='当前筛选范围暂无可用于方向分析的记录。'; weak='暂无足够数据识别相对薄弱方向。'; suggest='建议完善项目与成果的研究方向和关键词信息。'

    return JsonResponse({
      'stat_cards':{
        'gov_projects':projects.filter(project_type='横向').count(),
        'horizontal_projects':projects.filter(project_type='横向').count(),
        'total_fund':round(float(funds.aggregate(v=Sum('amount'))['v'] or 0),2),
        'core_achievements':achievements.filter(level__in=['CSSCI','核心期刊']).count(),
        'digital_gov_projects':projects.filter(research_direction='数字治理').count(),
        'community_growth':cg,
        'emergency_projects':projects.filter(research_direction='应急与风险治理').count(),
      },
      'fund_trend':{'years':years,'vertical':vertical,'horizontal':horizontal},
      'directions':labels,'dir_counts':achievement_raw,'pie_data':pie,'radar_values':_activity_percent(raw),
      'wordcloud_data':keyword_cloud(list(scoped_p)+list(scoped_a)),
      'result_years':result_years,'journal_counts':journal,'monograph_counts':mono,'report_counts':report,
      'achievements_table':[{'序号':i,'成果名称':a.title,'负责人':a.author.real_name,'成果类型':a.achievement_type,'发布年份':a.publish_year} for i,a in enumerate(scoped_a.select_related('author').order_by('-publish_year','id')[:10],1)],
      'projects_table':[{'项目名称':x.project_name,'负责人':x.leader.real_name,'项目类型':x.project_type,'进度':f'{x.actual_progress}%','状态':x.status} for x in scoped_p.select_related('leader').filter(Q(project_type='横向')|Q(project_name__icontains='政府'),status__in=['在研','立项'])[:15]],
      'analysis':{'summary':summary,'weak':weak,'suggest':suggest},
    })

def fund_project_options(request):
    """返回经费登记表可关联的项目选项。"""
    if request.method != 'GET':
        return JsonResponse({'error': '仅支持 GET 请求'}, status=405)
    projects = Project.objects.select_related('leader').order_by('project_name', 'id')
    data = [{
        'id': item.id,
        'project_no': item.project_no or '',
        'project_name': item.project_name or '',
        'leader_name': item.leader.real_name if item.leader_id and item.leader else '',
    } for item in projects]
    return JsonResponse({'data': data})


def fund_details_api(request):
    """经费明细分页列表；传 id 时返回单条记录详情。"""
    if request.method != 'GET':
        return JsonResponse({'error': '仅支持 GET 请求'}, status=405)

    raw_id = request.GET.get('id', '').strip()
    queryset = FundDetail.objects.select_related('project', 'project__leader').all()
    if raw_id:
        try:
            record_id = int(raw_id)
            record = queryset.get(pk=record_id)
        except (TypeError, ValueError):
            return JsonResponse({'error': '经费明细编号无效'}, status=400)
        except FundDetail.DoesNotExist:
            return JsonResponse({'error': '未找到该经费明细'}, status=404)
        project = record.project
        return JsonResponse({'record': {
            'id': record.id,
            'project_id': record.project_id,
            'project_no': project.project_no or '',
            'project_name': project.project_name or '',
            'leader_name': project.leader.real_name if project.leader_id and project.leader else '',
            'subject': project.subject or '',
            'year': record.year,
            'amount': format(record.amount, '.2f'),
            'source_type': record.source_type,
            'usage_type': record.usage_type,
        }})

    raw_year = request.GET.get('year', '').strip()
    if raw_year:
        try:
            queryset = queryset.filter(year=int(raw_year))
        except (TypeError, ValueError):
            return JsonResponse({'error': '年份参数无效'}, status=400)

    subject = request.GET.get('subject', 'all').strip()
    if subject not in ('', 'all', '__all__'):
        queryset = queryset.filter(project__subject=subject)

    keyword = request.GET.get('keyword', '').strip()
    if keyword:
        queryset = queryset.filter(
            Q(project__project_name__icontains=keyword)
            | Q(project__project_no__icontains=keyword)
            | Q(project__leader__real_name__icontains=keyword)
            | Q(source_type__icontains=keyword)
            | Q(usage_type__icontains=keyword)
        )

    queryset = queryset.order_by('-year', 'project__project_name', '-id')
    try:
        page = max(1, int(request.GET.get('page', '1')))
        page_size = min(100, max(1, int(request.GET.get('page_size', '10'))))
    except (TypeError, ValueError):
        return JsonResponse({'error': '分页参数无效'}, status=400)

    total = queryset.count()
    total_pages = max(1, (total + page_size - 1) // page_size)
    page = min(page, total_pages)
    start = (page - 1) * page_size
    records = queryset[start:start + page_size]
    results = []
    for record in records:
        project = record.project
        results.append({
            'id': record.id,
            'project_id': record.project_id,
            'project_no': project.project_no or '',
            'project_name': project.project_name or '',
            'leader_name': project.leader.real_name if project.leader_id and project.leader else '',
            'subject': project.subject or '',
            'year': record.year,
            'amount': float(record.amount or 0),
            'source_type': record.source_type,
            'usage_type': record.usage_type,
        })
    return JsonResponse({
        'results': results,
        'total': total,
        'page': page,
        'page_size': page_size,
        'total_pages': total_pages,
    })


def fund_save_api(request):
    """新增或编辑经费明细。不修改 FundBudget，不自动生成预算。"""
    if request.method != 'POST':
        return JsonResponse({'error': '仅支持 POST 请求'}, status=405)
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse({'error': '提交内容不是有效 JSON'}, status=400)
    if not isinstance(payload, dict):
        return JsonResponse({'error': '提交内容格式无效'}, status=400)

    try:
        project_id = int(payload.get('project_id'))
        year = int(payload.get('year'))
        amount = Decimal(str(payload.get('amount', '')).strip())
    except (TypeError, ValueError, InvalidOperation):
        return JsonResponse({'error': '项目、年度或金额格式无效'}, status=400)

    if year < 1900 or year > 2100:
        return JsonResponse({'error': '经费年度必须在 1900 至 2100 之间'}, status=400)
    if not amount.is_finite() or amount <= 0 or amount > Decimal('99999999.99'):
        return JsonResponse({'error': '经费金额必须大于 0，且不能超过字段允许范围'}, status=400)

    source_type = str(payload.get('source_type', '')).strip()
    usage_type = str(payload.get('usage_type', '')).strip()
    allowed_sources = {choice[0] for choice in FundDetail.SOURCE_CHOICES}
    allowed_usages = {choice[0] for choice in FundDetail.USAGE_CHOICES}
    if source_type not in allowed_sources:
        return JsonResponse({'error': '经费来源不在允许范围内'}, status=400)
    if usage_type not in allowed_usages:
        return JsonResponse({'error': '经费用途不在允许范围内'}, status=400)

    try:
        project = Project.objects.get(pk=project_id)
    except Project.DoesNotExist:
        return JsonResponse({'error': '关联科研项目不存在，请重新选择'}, status=404)

    raw_id = payload.get('id')
    if raw_id not in (None, ''):
        try:
            record_id = int(raw_id)
            record = FundDetail.objects.get(pk=record_id)
        except (TypeError, ValueError):
            return JsonResponse({'error': '经费明细编号无效'}, status=400)
        except FundDetail.DoesNotExist:
            return JsonResponse({'error': '待编辑的经费明细不存在'}, status=404)
        record.project = project
        record.year = year
        record.amount = amount
        record.source_type = source_type
        record.usage_type = usage_type
        record.save(update_fields=['project', 'year', 'amount', 'source_type', 'usage_type'])
        message = '经费明细更新成功'
    else:
        record = FundDetail.objects.create(
            project=project,
            year=year,
            amount=amount,
            source_type=source_type,
            usage_type=usage_type,
        )
        message = '经费明细登记成功'

    return JsonResponse({'success': True, 'message': message, 'id': record.id})

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


# ==================================================
# 科研首页工作台 2.0
# 全局科研查询 + 待办 / 风险提醒
# ==================================================

def workbench_options(request):
    project_subjects = set(
        Project.objects.exclude(subject__isnull=True).exclude(subject__exact='')
        .values_list('subject', flat=True)
    )
    achievement_subjects = set(
        Achievement.objects.exclude(subject__isnull=True).exclude(subject__exact='')
        .values_list('subject', flat=True)
    )
    teachers = list(
        User.objects.filter(role='teacher').select_related('dept').order_by('real_name')
        .values('id', 'real_name', 'title', 'dept__dept_name')
    )
    return JsonResponse({
        'years': sorted(get_available_years(), reverse=True),
        'subjects': sorted(project_subjects | achievement_subjects),
        'teachers': teachers,
        'statuses': [{'value': v, 'label': l} for v, l in Project.STATUS_CHOICES],
    })


def _workbench_int(value, field_name):
    if value in (None, ''):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        raise ValueError(f'{field_name}格式无效')
    if parsed <= 0:
        raise ValueError(f'{field_name}格式无效')
    return parsed


def workbench_overview(request):
    keyword = str(request.GET.get('keyword', '')).strip()
    subject = str(request.GET.get('subject', '')).strip()
    status = str(request.GET.get('status', '')).strip()

    try:
        year = _workbench_int(request.GET.get('year'), '年份')
        teacher_id = _workbench_int(request.GET.get('teacher_id'), '教师编号')
    except ValueError as exc:
        return JsonResponse({'error': str(exc)}, status=400)

    if status and status not in {value for value, _ in Project.STATUS_CHOICES}:
        return JsonResponse({'error': '项目状态不在允许范围内'}, status=400)

    projects = Project.objects.select_related('leader', 'dept').all()
    achievements = Achievement.objects.select_related('author', 'dept').all()

    if keyword:
        projects = projects.filter(
            Q(project_name__icontains=keyword) |
            Q(project_no__icontains=keyword) |
            Q(leader__real_name__icontains=keyword) |
            Q(subject__icontains=keyword) |
            Q(dept__dept_name__icontains=keyword)
        )
        achievements = achievements.filter(
            Q(title__icontains=keyword) |
            Q(author__real_name__icontains=keyword) |
            Q(subject__icontains=keyword) |
            Q(dept__dept_name__icontains=keyword)
        )

    if year:
        projects = projects.filter(start_date__year=year)
        achievements = achievements.filter(publish_year=year)
    if subject:
        projects = projects.filter(subject=subject)
        achievements = achievements.filter(subject=subject)
    if teacher_id:
        projects = projects.filter(leader_id=teacher_id)
        achievements = achievements.filter(author_id=teacher_id)
    if status:
        projects = projects.filter(status=status)

    projects = projects.order_by('-start_date', '-id')
    achievements = achievements.order_by('-publish_year', '-id')

    teacher_ids = set(projects.values_list('leader_id', flat=True)) | set(
        achievements.values_list('author_id', flat=True)
    )
    teachers = (
        User.objects.filter(role='teacher', id__in=teacher_ids)
        .select_related('dept')
        .annotate(
            project_count=Count('projects', distinct=True),
            achievement_count=Count('achievements', distinct=True),
        )
        .order_by('real_name')
    )

    fund_qs = FundDetail.objects.filter(project__in=projects)
    if year:
        fund_qs = fund_qs.filter(year=year)
    fund_total = fund_qs.aggregate(total=Sum('amount'))['total'] or Decimal('0')

    project_rows = list(projects.values(
        'id', 'project_no', 'project_name', 'leader__real_name',
        'dept__dept_name', 'project_type', 'subject', 'status',
        'start_date', 'end_date', 'actual_progress'
    )[:8])
    for row in project_rows:
        row['start_date'] = row['start_date'].isoformat() if row['start_date'] else None
        row['end_date'] = row['end_date'].isoformat() if row['end_date'] else None
        row['url'] = f"/project-detail/?id={row['id']}"

    achievement_rows = list(achievements.values(
        'id', 'title', 'author__real_name', 'dept__dept_name',
        'achievement_type', 'level', 'publish_year', 'subject'
    )[:8])
    for row in achievement_rows:
        row['url'] = f"/achievement-detail/?id={row['id']}"

    teacher_rows = [{
        'id': t.id,
        'real_name': t.real_name,
        'title': t.title,
        'dept': t.dept.dept_name if t.dept else '',
        'project_count': t.project_count,
        'achievement_count': t.achievement_count,
        'url': f"/analysis/teacher/?teacher_id={t.id}",
    } for t in teachers[:8]]

    today = date.today()
    due_soon_end = today + timedelta(days=90)
    unfinished = projects.exclude(status='结题')
    overdue_qs = unfinished.filter(end_date__lt=today)
    due_soon_qs = unfinished.filter(end_date__gte=today, end_date__lte=due_soon_end)
    missing_subject_qs = projects.filter(Q(subject__isnull=True) | Q(subject__exact=''))
    existing_warning_qs = (
        RiskWarning.objects.filter(is_resolved=False, project__in=projects)
        .select_related('project', 'project__leader')
        .order_by('-warning_date', '-id')
    )

    todo_items = []
    for warning in existing_warning_qs[:6]:
        todo_items.append({
            'kind': 'risk_warning', 'level': warning.risk_level,
            'title': warning.reason,
            'detail': f"{warning.project.project_name} · {warning.project.leader.real_name}",
            'project_id': warning.project_id,
            'url': f"/project-detail/?id={warning.project_id}",
            'date': warning.warning_date.isoformat(),
            'source': '已有风险记录',
        })

    for project in overdue_qs[:6]:
        todo_items.append({
            'kind': 'overdue', 'level': '高',
            'title': '项目已到期但尚未结题',
            'detail': f"{project.project_name} · {project.leader.real_name} · 已逾期 {(today - project.end_date).days} 天",
            'project_id': project.id, 'url': f"/project-detail/?id={project.id}",
            'date': project.end_date.isoformat(), 'source': '系统规则',
        })

    for project in due_soon_qs[:6]:
        todo_items.append({
            'kind': 'due_soon', 'level': '中',
            'title': '项目将在 90 天内到期',
            'detail': f"{project.project_name} · {project.leader.real_name} · 剩余 {(project.end_date - today).days} 天",
            'project_id': project.id, 'url': f"/project-detail/?id={project.id}",
            'date': project.end_date.isoformat(), 'source': '系统规则',
        })

    for project in missing_subject_qs[:6]:
        todo_items.append({
            'kind': 'missing_subject', 'level': '低',
            'title': '项目缺少学科分类',
            'detail': f"{project.project_name} · {project.leader.real_name}",
            'project_id': project.id, 'url': f"/project-detail/?id={project.id}",
            'date': None, 'source': '数据完整性检查',
        })

    level_rank = {'高': 0, '中': 1, '低': 2}
    todo_items.sort(key=lambda item: (level_rank.get(item['level'], 9), item['date'] or '9999-12-31'))

    return JsonResponse({
        'filters': {
            'keyword': keyword, 'year': year, 'subject': subject,
            'teacher_id': teacher_id, 'status': status,
        },
        'summary': {
            'project_count': projects.count(),
            'achievement_count': achievements.count(),
            'teacher_count': teachers.count(),
            'fund_total': round(float(fund_total), 2),
        },
        'results': {
            'projects': project_rows,
            'achievements': achievement_rows,
            'teachers': teacher_rows,
        },
        'todo': {
            'items': todo_items[:10],
            'counts': {
                'existing_warning': existing_warning_qs.count(),
                'overdue': overdue_qs.count(),
                'due_soon': due_soon_qs.count(),
                'missing_subject': missing_subject_qs.count(),
            },
            'rule_note': '自动提醒仅基于现有字段进行规则判断；不代表审批结论或项目绩效评价。',
        },
    })


# ==================================================
# 科研综合查询结果页
# ==================================================

def research_query_page(request):
    return render(request, '科研综合查询.html')


def workbench_search_api(request):
    keyword = str(request.GET.get('keyword', '')).strip()
    subject = str(request.GET.get('subject', '')).strip()
    status = str(request.GET.get('status', '')).strip()
    result_type = str(request.GET.get('type', 'project')).strip()

    try:
        year = _workbench_int(request.GET.get('year'), '年份')
        teacher_id = _workbench_int(request.GET.get('teacher_id'), '教师编号')
        page = max(1, int(request.GET.get('page', 1)))
        page_size = min(50, max(5, int(request.GET.get('page_size', 10))))
    except (ValueError, TypeError):
        return JsonResponse({'error': '查询参数格式无效'}, status=400)

    if result_type not in {'project', 'achievement', 'teacher'}:
        return JsonResponse({'error': '结果类型无效'}, status=400)

    if status and status not in {value for value, _ in Project.STATUS_CHOICES}:
        return JsonResponse({'error': '项目状态不在允许范围内'}, status=400)

    projects = Project.objects.select_related('leader', 'dept').all()
    achievements = Achievement.objects.select_related('author', 'dept').all()

    if keyword:
        projects = projects.filter(
            Q(project_name__icontains=keyword) |
            Q(project_no__icontains=keyword) |
            Q(leader__real_name__icontains=keyword) |
            Q(subject__icontains=keyword) |
            Q(dept__dept_name__icontains=keyword)
        )
        achievements = achievements.filter(
            Q(title__icontains=keyword) |
            Q(author__real_name__icontains=keyword) |
            Q(subject__icontains=keyword) |
            Q(dept__dept_name__icontains=keyword)
        )

    if year:
        projects = projects.filter(start_date__year=year)
        achievements = achievements.filter(publish_year=year)
    if subject:
        projects = projects.filter(subject=subject)
        achievements = achievements.filter(subject=subject)
    if teacher_id:
        projects = projects.filter(leader_id=teacher_id)
        achievements = achievements.filter(author_id=teacher_id)
    if status:
        projects = projects.filter(status=status)

    projects = projects.order_by('-start_date', '-id')
    achievements = achievements.order_by('-publish_year', '-id')

    teacher_ids = set(projects.values_list('leader_id', flat=True)) | set(
        achievements.values_list('author_id', flat=True)
    )
    teachers = (
        User.objects.filter(role='teacher', id__in=teacher_ids)
        .select_related('dept')
        .annotate(
            project_count=Count('projects', distinct=True),
            achievement_count=Count('achievements', distinct=True),
        )
        .order_by('real_name')
    )

    fund_qs = FundDetail.objects.filter(project__in=projects)
    if year:
        fund_qs = fund_qs.filter(year=year)
    fund_total = fund_qs.aggregate(total=Sum('amount'))['total'] or Decimal('0')

    counts = {
        'project': projects.count(),
        'achievement': achievements.count(),
        'teacher': teachers.count(),
    }

    source = projects if result_type == 'project' else achievements if result_type == 'achievement' else teachers
    total = counts[result_type]
    total_pages = max(1, math.ceil(total / page_size)) if total else 1
    page = min(page, total_pages)
    start = (page - 1) * page_size
    end = start + page_size

    rows = []
    if result_type == 'project':
        for item in source[start:end]:
            rows.append({
                'id': item.id,
                'project_no': item.project_no,
                'project_name': item.project_name,
                'leader': item.leader.real_name,
                'dept': item.dept.dept_name if item.dept else '',
                'project_type': item.project_type,
                'subject': item.subject or '',
                'status': item.status,
                'start_date': item.start_date.isoformat() if item.start_date else '',
                'end_date': item.end_date.isoformat() if item.end_date else '',
                'actual_progress': item.actual_progress,
                'url': f'/project-detail/?id={item.id}',
            })
    elif result_type == 'achievement':
        for item in source[start:end]:
            rows.append({
                'id': item.id,
                'title': item.title,
                'author': item.author.real_name,
                'dept': item.dept.dept_name if item.dept else '',
                'achievement_type': item.achievement_type,
                'level': item.level or '',
                'publish_year': item.publish_year,
                'subject': item.subject or '',
                'citation_count': item.citation_count,
                'url': f'/achievement-detail/?id={item.id}',
            })
    else:
        for item in source[start:end]:
            rows.append({
                'id': item.id,
                'real_name': item.real_name,
                'title': item.title or '',
                'dept': item.dept.dept_name if item.dept else '',
                'project_count': item.project_count,
                'achievement_count': item.achievement_count,
                'url': f'/analysis/teacher/?teacher_id={item.id}',
            })

    return JsonResponse({
        'filters': {
            'keyword': keyword,
            'year': year,
            'subject': subject,
            'teacher_id': teacher_id,
            'status': status,
            'type': result_type,
        },
        'summary': {
            'project_count': counts['project'],
            'achievement_count': counts['achievement'],
            'teacher_count': counts['teacher'],
            'fund_total': round(float(fund_total), 2),
        },
        'counts': counts,
        'pagination': {
            'page': page,
            'page_size': page_size,
            'total': total,
            'total_pages': total_pages,
        },
        'rows': rows,
    })


# ==================================================
# 项目综合详情页
# ==================================================

def project_overview_page(request):
    return render(request, '项目综合详情.html')


def project_overview_api(request):
    raw_id = str(request.GET.get('id', '')).strip()
    try:
        project_id = int(raw_id)
        if project_id <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return JsonResponse({'error': '项目编号参数无效'}, status=400)

    try:
        project = (
            Project.objects
            .select_related('leader', 'leader__dept', 'dept')
            .get(pk=project_id)
        )
    except Project.DoesNotExist:
        return JsonResponse({'error': '未找到该项目'}, status=404)

    funds = list(
        FundDetail.objects
        .filter(project=project)
        .order_by('year', 'id')
        .values('id', 'year', 'source_type', 'usage_type', 'amount')
    )
    budgets = list(
        FundBudget.objects
        .filter(project=project)
        .order_by('year', 'id')
        .values('id', 'year', 'budget_amount', 'is_demo', 'data_source')
    )
    warnings = list(
        RiskWarning.objects
        .filter(project=project)
        .order_by('-warning_date', '-id')
        .values(
            'id', 'warning_date', 'risk_level',
            'reason', 'suggested_action', 'is_resolved'
        )
    )
    cooperations = list(
        Cooperation.objects
        .filter(project=project, is_demo=False)
        .order_by('-coop_count', 'id')
        .values('id', 'source', 'target', 'coop_count')
    )

    fund_total = sum((item['amount'] or Decimal('0')) for item in funds)
    budget_total = sum((item['budget_amount'] or Decimal('0')) for item in budgets)
    formal_budget_total = sum(
        (item['budget_amount'] or Decimal('0'))
        for item in budgets if not item['is_demo']
    )
    demo_budget_total = sum(
        (item['budget_amount'] or Decimal('0'))
        for item in budgets if item['is_demo']
    )

    fund_by_year = {}
    for item in funds:
        year = int(item['year'])
        fund_by_year[year] = fund_by_year.get(year, Decimal('0')) + (item['amount'] or Decimal('0'))

    budget_by_year = {}
    for item in budgets:
        year = int(item['year'])
        budget_by_year[year] = budget_by_year.get(year, Decimal('0')) + (item['budget_amount'] or Decimal('0'))

    years = sorted(set(fund_by_year) | set(budget_by_year))
    fund_trend = [
        {
            'year': year,
            'fund': round(float(fund_by_year.get(year, Decimal('0'))), 2),
            'budget': round(float(budget_by_year.get(year, Decimal('0'))), 2),
        }
        for year in years
    ]

    leader_metrics = teacher_research_metrics(project.leader)
    leader_project_count = leader_metrics['project_count']
    leader_achievement_count = leader_metrics['achievements_count']

    active_warning_count = sum(1 for item in warnings if not item['is_resolved'])
    high_warning_count = sum(
        1 for item in warnings
        if not item['is_resolved'] and item['risk_level'] == '高'
    )

    today = date.today()
    if project.status == '结题':
        deadline_state = '已结题'
        deadline_days = None
    else:
        delta = (project.end_date - today).days
        deadline_days = delta
        if delta < 0:
            deadline_state = '已逾期'
        elif delta <= 90:
            deadline_state = '90天内到期'
        else:
            deadline_state = '正常'

    for item in funds:
        item['amount'] = round(float(item['amount'] or 0), 2)

    for item in budgets:
        item['budget_amount'] = round(float(item['budget_amount'] or 0), 2)

    for item in warnings:
        item['warning_date'] = item['warning_date'].isoformat() if item['warning_date'] else None

    return JsonResponse({
        'project': {
            'id': project.id,
            'project_no': project.project_no,
            'project_name': project.project_name,
            'project_type': project.project_type,
            'subject': project.subject or '',
            'status': project.status,
            'fund_amount': round(float(project.fund_amount or 0), 2),
            'start_date': project.start_date.isoformat(),
            'end_date': project.end_date.isoformat(),
            'actual_progress': project.actual_progress,
            'dept': project.dept.dept_name if project.dept else '',
            'deadline_state': deadline_state,
            'deadline_days': deadline_days,
        },
        'leader': {
            'id': project.leader.id,
            'real_name': project.leader.real_name,
            'title': project.leader.title or '',
            'dept': project.leader.dept.dept_name if project.leader.dept else '',
            'project_count': leader_project_count,
            'achievement_count': leader_achievement_count,
            'profile_url': f'/analysis/teacher/?teacher_id={project.leader.id}',
        },
        'fund': {
            'project_fund_amount': round(float(project.fund_amount or 0), 2),
            'detail_total': round(float(fund_total), 2),
            'budget_total': round(float(budget_total), 2) if budget_total else None,
            'formal_budget_total': round(float(formal_budget_total), 2),
            'demo_budget_total': round(float(demo_budget_total), 2),
            'details': funds,
            'budgets': budgets,
            'trend': fund_trend,
        },
        'risk': {
            'active_count': active_warning_count,
            'high_count': high_warning_count,
            'warnings': warnings,
        },
        'cooperation': {
            'count': len(cooperations),
            'items': cooperations[:20],
        },
        'relation_note': (
            '当前数据模型未建立 Achievement 与 Project 的直接外键关系，'
            '因此本页不将任何成果直接标记为“本项目成果”。'
        ),
    })

# ==================================================
# 成果综合详情页
# ==================================================
def achievement_overview_page(request):
    return render(request, '成果综合详情.html')


# ==================================================
# 科研综合查询 2.0
# ==================================================

def research_query_options_v2(request):
    years = sorted(get_available_years(), reverse=True)
    depts = list(
        Dept.objects.values_list('dept_name', flat=True)
        .distinct().order_by('dept_name')
    )
    subjects = sorted(set(
        list(Project.objects.exclude(subject__isnull=True).exclude(subject='').values_list('subject', flat=True))
        + list(Achievement.objects.exclude(subject__isnull=True).exclude(subject='').values_list('subject', flat=True))
    ))
    teachers = list(
        User.objects.filter(role='teacher')
        .select_related('dept')
        .order_by('dept__dept_name', 'real_name')
        .values('id', 'real_name', 'title', 'dept__dept_name')
    )
    achievement_levels = list(
        Achievement.objects.exclude(level__isnull=True).exclude(level='')
        .values_list('level', flat=True).distinct().order_by('level')
    )
    return JsonResponse({
        'years': years,
        'depts': depts,
        'subjects': subjects,
        'teachers': teachers,
        'project_statuses': [{'value': v, 'label': l} for v, l in Project.STATUS_CHOICES],
        'project_types': [{'value': v, 'label': l} for v, l in Project.TYPE_CHOICES],
        'fund_sources': [{'value': v, 'label': l} for v, l in FundDetail.SOURCE_CHOICES],
        'achievement_types': [{'value': v, 'label': l} for v, l in Achievement.TYPE_CHOICES],
        'achievement_levels': achievement_levels,
        'international_options': [
            {'value': 'true', 'label': '国际发表'},
            {'value': 'false', 'label': '非国际发表'},
        ],
    })


def research_query_search_v2(request):
    keyword = str(request.GET.get('keyword', '')).strip()
    dept = str(request.GET.get('dept', '')).strip()
    subject = str(request.GET.get('subject', '')).strip()
    status = str(request.GET.get('status', '')).strip()
    project_type = str(request.GET.get('project_type', '')).strip()
    fund_source = str(request.GET.get('fund_source', '')).strip()
    achievement_type = str(request.GET.get('achievement_type', '')).strip()
    achievement_level = str(request.GET.get('achievement_level', '')).strip()
    international = str(request.GET.get('international', '')).strip().lower()
    result_type = str(request.GET.get('type', 'project')).strip()

    try:
        year = _workbench_int(request.GET.get('year'), '年份')
        fund_year = _workbench_int(request.GET.get('fund_year'), '经费年份')
        teacher_id = _workbench_int(request.GET.get('teacher_id'), '教师编号')
        page = max(1, int(request.GET.get('page', 1)))
        page_size = min(50, max(5, int(request.GET.get('page_size', 10))))
    except (ValueError, TypeError):
        return JsonResponse({'error': '查询参数格式无效'}, status=400)

    if result_type not in {'project', 'achievement', 'teacher'}:
        return JsonResponse({'error': '结果类型无效'}, status=400)
    if status and status not in {v for v, _ in Project.STATUS_CHOICES}:
        return JsonResponse({'error': '项目状态无效'}, status=400)
    if project_type and project_type not in {v for v, _ in Project.TYPE_CHOICES}:
        return JsonResponse({'error': '项目类型无效'}, status=400)
    if fund_source and fund_source not in {v for v, _ in FundDetail.SOURCE_CHOICES}:
        return JsonResponse({'error': '经费来源无效'}, status=400)
    if achievement_type and achievement_type not in {v for v, _ in Achievement.TYPE_CHOICES}:
        return JsonResponse({'error': '成果类型无效'}, status=400)
    if international not in {'', 'true', 'false'}:
        return JsonResponse({'error': '国际发表筛选值无效'}, status=400)

    projects = Project.objects.select_related('leader', 'dept').all()
    achievements = Achievement.objects.select_related('author', 'dept').all()

    # 通用条件
    if keyword:
        projects = projects.filter(
            Q(project_name__icontains=keyword)
            | Q(project_no__icontains=keyword)
            | Q(leader__real_name__icontains=keyword)
            | Q(subject__icontains=keyword)
            | Q(dept__dept_name__icontains=keyword)
        )
        achievements = achievements.filter(
            Q(title__icontains=keyword)
            | Q(author__real_name__icontains=keyword)
            | Q(subject__icontains=keyword)
            | Q(dept__dept_name__icontains=keyword)
        )

    if dept:
        projects = projects.filter(dept__dept_name=dept)
        achievements = achievements.filter(dept__dept_name=dept)
    if subject:
        projects = projects.filter(subject=subject)
        achievements = achievements.filter(subject=subject)
    if year:
        projects = projects.filter(start_date__year=year)
        achievements = achievements.filter(publish_year=year)
    if teacher_id:
        projects = projects.filter(leader_id=teacher_id)
        achievements = achievements.filter(author_id=teacher_id)

    # 项目专属条件
    if status:
        projects = projects.filter(status=status)
    if project_type:
        projects = projects.filter(project_type=project_type)
    if fund_source:
        projects = projects.filter(funds__source_type=fund_source)
    if fund_year:
        projects = projects.filter(funds__year=fund_year)

    # 成果专属条件
    if achievement_type:
        achievements = achievements.filter(achievement_type=achievement_type)
    if achievement_level:
        achievements = achievements.filter(level=achievement_level)
    if international == 'true':
        achievements = achievements.filter(is_international=True)
    elif international == 'false':
        achievements = achievements.filter(is_international=False)

    projects = projects.distinct().order_by('-start_date', '-id')
    achievements = achievements.distinct().order_by('-publish_year', '-id')

    # 涉及教师：以当前筛选后的项目负责人 + 成果作者为准。
    # 关键词可以命中项目/成果名称，因此不能再要求教师姓名本身也包含关键词。
    related_teacher_ids = set(projects.values_list('leader_id', flat=True))
    related_teacher_ids |= set(achievements.values_list('author_id', flat=True))

    teachers = (
        User.objects.filter(role='teacher', id__in=related_teacher_ids)
        .select_related('dept')
        .annotate(
            project_count=Count('projects', distinct=True),
            achievement_count=Count('achievements', distinct=True),
        )
        .order_by('dept__dept_name', 'real_name', 'id')
    )

    # 当用户明确指定教师时，结果只保留该教师。
    if teacher_id:
        teachers = teachers.filter(id=teacher_id)

    # 关联经费基于当前项目集合；如指定经费年份，则按该年份汇总。
    fund_qs = FundDetail.objects.filter(project__in=projects)
    if fund_year:
        fund_qs = fund_qs.filter(year=fund_year)
    fund_total = fund_qs.aggregate(total=Sum('amount'))['total'] or Decimal('0')

    counts = {
        'project': projects.count(),
        'achievement': achievements.count(),
        'teacher': teachers.count(),
    }

    source = projects if result_type == 'project' else achievements if result_type == 'achievement' else teachers
    total = counts[result_type]
    total_pages = max(1, math.ceil(total / page_size)) if total else 1
    page = min(page, total_pages)
    start = (page - 1) * page_size
    end = start + page_size

    rows = []
    if result_type == 'project':
        for item in source[start:end]:
            rows.append({
                'id': item.id,
                'project_no': item.project_no,
                'project_name': item.project_name,
                'leader': item.leader.real_name,
                'dept': item.dept.dept_name if item.dept else '',
                'project_type': item.project_type,
                'subject': item.subject or '',
                'status': item.status,
                'start_date': item.start_date.isoformat() if item.start_date else '',
                'end_date': item.end_date.isoformat() if item.end_date else '',
                'actual_progress': item.actual_progress,
                'url': f'/project-detail/?id={item.id}',
            })
    elif result_type == 'achievement':
        for item in source[start:end]:
            rows.append({
                'id': item.id,
                'title': item.title,
                'author': item.author.real_name,
                'dept': item.dept.dept_name if item.dept else '',
                'achievement_type': item.achievement_type,
                'level': item.level or '',
                'publish_year': item.publish_year,
                'subject': item.subject or '',
                'citation_count': item.citation_count,
                'is_international': bool(item.is_international),
                'url': f'/achievement-detail/?id={item.id}',
            })
    else:
        for item in source[start:end]:
            rows.append({
                'id': item.id,
                'real_name': item.real_name,
                'title': item.title or '',
                'dept': item.dept.dept_name if item.dept else '',
                'project_count': item.project_count,
                'achievement_count': item.achievement_count,
                'url': f'/analysis/teacher/?teacher_id={item.id}',
            })

    return JsonResponse({
        'filters': {
            'keyword': keyword,
            'year': year,
            'fund_year': fund_year,
            'dept': dept,
            'subject': subject,
            'teacher_id': teacher_id,
            'status': status,
            'project_type': project_type,
            'fund_source': fund_source,
            'achievement_type': achievement_type,
            'achievement_level': achievement_level,
            'international': international,
            'type': result_type,
        },
        'summary': {
            'project_count': counts['project'],
            'achievement_count': counts['achievement'],
            'teacher_count': counts['teacher'],
            'fund_total': round(float(fund_total), 2),
        },
        'counts': counts,
        'pagination': {
            'page': page,
            'page_size': page_size,
            'total': total,
            'total_pages': total_pages,
        },
        'rows': rows,
    })
