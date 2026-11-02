from decimal import Decimal, InvalidOperation
from datetime import date
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
    Q
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
    DeptResource
)
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
                    'is_demo': bool(item.is_demo),
                    'data_source': item.data_source or 'unknown',
                    'source_label': '演示数据' if item.is_demo else '原有记录',
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
            'has_demo_data': demo_count > 0,
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
    """科研经费顶部概览：实际经费 + 年度预算"""

    year = int(
        request.GET.get(
            'year',
            get_latest_year()
        )
    )
    subject = request.GET.get(
        'subject',
        'all'
    )

    # 当前年度实际经费
    actual_qs = FundDetail.objects.filter(
        year=year
    )

    # 当前年度预算
    budget_qs = FundBudget.objects.filter(
        year=year
    )

    # 上一年度实际经费
    last_actual_qs = FundDetail.objects.filter(
        year=year - 1
    )

    # 上一年度预算
    last_budget_qs = FundBudget.objects.filter(
        year=year - 1
    )

    # 学科筛选
    if subject != 'all':
        actual_qs = actual_qs.filter(
            project__subject=subject
        )
        budget_qs = budget_qs.filter(
            project__subject=subject
        )
        last_actual_qs = last_actual_qs.filter(
            project__subject=subject
        )
        last_budget_qs = last_budget_qs.filter(
            project__subject=subject
        )

    total_amount = (
        actual_qs.aggregate(
            total=Sum('amount')
        )['total']
        or Decimal(0)
    )

    budget_total = (
        budget_qs.aggregate(
            total=Sum('budget_amount')
        )['total']
        or Decimal(0)
    )

    last_year_total = (
        last_actual_qs.aggregate(
            total=Sum('amount')
        )['total']
        or Decimal(0)
    )

    last_budget_total = (
        last_budget_qs.aggregate(
            total=Sum('budget_amount')
        )['total']
        or Decimal(0)
    )

    # 判断当前预算数据类型
    has_demo_budget = budget_qs.filter(
        is_demo=True
    ).exists()

    has_real_budget = budget_qs.filter(
        is_demo=False
    ).exists()

    if has_demo_budget and has_real_budget:
        budget_data_mode = 'mixed'
    elif has_demo_budget:
        budget_data_mode = 'demo'
    elif has_real_budget:
        budget_data_mode = 'real'
    else:
        budget_data_mode = 'none'

    budget_sources = list(
        budget_qs.order_by()
        .values_list(
            'data_source',
            flat=True
        )
        .distinct()
    )

    # 经费同比增长
    if last_year_total:
        growth_rate = float(
            (total_amount - last_year_total)
            / last_year_total
            * 100
        )
    else:
        growth_rate = 0

    budget_available = budget_total > 0

    # 当前年度预算执行率与结余
    if budget_available:
        execution_rate = float(
            total_amount
            / budget_total
            * 100
        )

        surplus = (
            budget_total
            - total_amount
        )
    else:
        execution_rate = None
        surplus = None

    # 上年度预算执行率
    if last_budget_total > 0:
        last_execution_rate = float(
            last_year_total
            / last_budget_total
            * 100
        )
    else:
        last_execution_rate = None

    # 执行率同比变化
    if (
        execution_rate is not None
        and last_execution_rate is not None
    ):
        execution_rate_change = (
            execution_rate
            - last_execution_rate
        )
    else:
        execution_rate_change = None

    return JsonResponse({
        'year': year,
        'total_amount': round(
            float(total_amount),
            2
        ),
        'budget_total': round(
            float(budget_total),
            2
        ),
        'budget_available': budget_available,
        'budget_data_mode': budget_data_mode,
        'budget_sources': budget_sources,
        'execution_rate': (
            round(execution_rate, 2)
            if execution_rate is not None
            else None
        ),
        'execution_rate_change': (
            round(execution_rate_change, 2)
            if execution_rate_change is not None
            else None
        ),
        'surplus': (
            round(float(surplus), 2)
            if surplus is not None
            else None
        ),
        'growth_rate': round(
            growth_rate,
            2
        ),
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
    """年度预算执行率仪表盘"""

    year = int(
        request.GET.get(
            'year',
            get_latest_year()
        )
    )

    subject = request.GET.get(
        'subject',
        'all'
    )

    actual_qs = FundDetail.objects.filter(
        year=year
    )

    budget_qs = FundBudget.objects.filter(
        year=year
    )

    if subject != 'all':
        actual_qs = actual_qs.filter(
            project__subject=subject
        )

        budget_qs = budget_qs.filter(
            project__subject=subject
        )

    actual_total = (
        actual_qs.aggregate(
            total=Sum('amount')
        )['total']
        or Decimal(0)
    )

    budget_total = (
        budget_qs.aggregate(
            total=Sum('budget_amount')
        )['total']
        or Decimal(0)
    )

    # 判断预算数据类型
    has_demo_budget = budget_qs.filter(
        is_demo=True
    ).exists()

    has_real_budget = budget_qs.filter(
        is_demo=False
    ).exists()

    if has_demo_budget and has_real_budget:
        budget_data_mode = 'mixed'
    elif has_demo_budget:
        budget_data_mode = 'demo'
    elif has_real_budget:
        budget_data_mode = 'real'
    else:
        budget_data_mode = 'none'

    budget_sources = list(
        budget_qs.order_by()
        .values_list(
            'data_source',
            flat=True
        )
        .distinct()
    )

    if budget_total <= 0:
        return JsonResponse({
            'budget_available': False,
            'budget_data_mode': budget_data_mode,
            'budget_sources': budget_sources,
            'value': None,
            'actual_total': round(
                float(actual_total),
                2
            ),
            'budget_total': 0,
        })

    rate = float(
        actual_total
        / budget_total
        * 100
    )

    return JsonResponse({
        'budget_available': True,
        'budget_data_mode': budget_data_mode,
        'budget_sources': budget_sources,
        'value': round(
            rate,
            2
        ),
        'actual_total': round(
            float(actual_total),
            2
        ),
        'budget_total': round(
            float(budget_total),
            2
        ),
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
    """汇总该教师实际存在的绩效、项目、经费和成果年份。"""
    years = set()

    score_years = TeacherScore.objects.filter(
        teacher=teacher
    ).values_list('year', flat=True).distinct()
    years.update(int(year) for year in score_years if year is not None)

    project_years = Project.objects.filter(
        leader=teacher
    ).values_list('start_date__year', flat=True).distinct()
    years.update(int(year) for year in project_years if year is not None)

    fund_years = FundDetail.objects.filter(
        project__leader=teacher
    ).values_list('year', flat=True).distinct()
    years.update(int(year) for year in fund_years if year is not None)

    achievement_years = Achievement.objects.filter(
        author=teacher
    ).values_list('publish_year', flat=True).distinct()
    years.update(int(year) for year in achievement_years if year is not None)

    return sorted(years)


def teacher_directory(request):
    """教师目录：支持按姓名、职称和系别搜索。"""
    query = request.GET.get('q', '').strip()
    teachers = User.objects.filter(role='teacher').select_related('dept').annotate(
        project_count=Count('projects', distinct=True),
        achievement_count=Count('achievements', distinct=True),
    )

    if query:
        teachers = teachers.filter(
            Q(real_name__icontains=query)
            | Q(title__icontains=query)
            | Q(dept__dept_name__icontains=query)
        )

    teachers = teachers.order_by('dept__dept_name', 'real_name', 'id')
    data = [
        {
            'id': teacher.id,
            'real_name': teacher.real_name,
            'title': teacher.title or '',
            'dept': teacher.dept.dept_name if teacher.dept else '未分配',
            'project_count': teacher.project_count,
            'achievement_count': teacher.achievement_count,
        }
        for teacher in teachers
    ]
    return JsonResponse({'teachers': data, 'total': len(data)})


def teacher_info(request):
    """返回教师基本信息和核心指标；如含演示绩效/合作记录，明确返回来源标记。"""
    teacher, error_response = _teacher_from_request(request)
    if error_response is not None:
        return error_response

    score_rows = list(
        TeacherScore.objects.filter(teacher=teacher).order_by('year', 'id')
    )
    score_by_year = {}
    for score in score_rows:
        score_by_year[score.year] = score

    latest_score_year = max(score_by_year) if score_by_year else None
    latest_score = score_by_year.get(latest_score_year) if latest_score_year is not None else None

    demo_scores = [score for score in score_rows if score.is_demo]
    existing_scores = [score for score in score_rows if not score.is_demo]
    demo_score_years = sorted({score.year for score in demo_scores})

    projects = Project.objects.filter(leader=teacher)
    ongoing_projects = projects.filter(status='在研').count()
    fund_total = FundDetail.objects.filter(
        project__leader=teacher
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

    achievements = Achievement.objects.filter(author=teacher)
    achievement_count = achievements.count()
    citation_values = list(
        achievements.order_by('-citation_count').values_list('citation_count', flat=True)
    )

    if achievement_count:
        total_citation = sum(int(value or 0) for value in citation_values)
        h_index = max(
            (rank for rank, citation_count in enumerate(citation_values, start=1)
             if int(citation_count or 0) >= rank),
            default=0,
        )
    else:
        # 无成果记录时不把缺失数据包装成真实的 0 次引用。
        total_citation = None
        h_index = None

    growth_rate = None
    growth_rate_is_demo = False
    if score_by_year:
        recent_scores = [
            score_by_year[year]
            for year in sorted(score_by_year)
            if latest_score_year - 2 <= year <= latest_score_year
        ]
        if len(recent_scores) >= 2:
            first_score = float(recent_scores[0].comprehensive_score)
            last_score = float(recent_scores[-1].comprehensive_score)
            if first_score != 0 and recent_scores[-1].year > recent_scores[0].year:
                growth_rate = round((last_score - first_score) / first_score * 100, 1)
                growth_rate_is_demo = any(score.is_demo for score in recent_scores)

    years = _teacher_data_years(teacher)
    cooperation_queryset = Cooperation.objects.filter(project__leader=teacher)
    demo_cooperation_count = cooperation_queryset.filter(is_demo=True).count()
    existing_cooperation_count = cooperation_queryset.filter(is_demo=False).count()

    return JsonResponse({
        'id': teacher.id,
        'real_name': teacher.real_name,
        'title': teacher.title or '',
        'dept': teacher.dept.dept_name if teacher.dept else '未分配',
        # User 模型目前没有入职年份字段，故明确返回 null。
        'join_year': None,
        'comprehensive': (
            round(float(latest_score.comprehensive_score), 2)
            if latest_score is not None else None
        ),
        'score_year': latest_score_year,
        'score_is_demo': bool(latest_score.is_demo) if latest_score is not None else False,
        'score_data_source': latest_score.data_source if latest_score is not None else None,
        'ongoing_projects': ongoing_projects,
        'fund_total': round(float(fund_total), 2),
        'achievements_count': achievement_count,
        'total_citation': total_citation,
        'h_index': h_index,
        'cooperation_count': existing_cooperation_count + demo_cooperation_count,
        'existing_cooperation_count': existing_cooperation_count,
        'demo_cooperation_count': demo_cooperation_count,
        'score_count': len(score_rows),
        'existing_score_count': len(existing_scores),
        'demo_score_count': len(demo_scores),
        'demo_score_years': demo_score_years,
        'has_demo_score_data': bool(demo_scores),
        'has_demo_cooperation_data': demo_cooperation_count > 0,
        'has_demo_data': bool(demo_scores) or demo_cooperation_count > 0,
        'growth_rate': growth_rate,
        'growth_rate_is_demo': growth_rate_is_demo,
        'years': years,
        'score_years': sorted(score_by_year),
        'latest_year': years[-1] if years else None,
    })

def teacher_trend(request):
    """返回教师实际年度绩效、项目数和成果数；逐年附带绩效记录来源标记。"""
    teacher, error_response = _teacher_from_request(request)
    if error_response is not None:
        return error_response

    trend_type = request.GET.get('type', '5year')
    limits = {'5year': 5, '3year': 3, 'all': None}
    if trend_type not in limits:
        return JsonResponse(
            {'error': 'type 仅支持 5year、3year 或 all'},
            status=400
        )

    years = _teacher_data_years(teacher)
    limit = limits[trend_type]
    if limit is not None:
        years = years[-limit:]

    scores = []
    score_is_demo = []
    score_data_sources = []
    project_counts = []
    achievement_counts = []

    for year in years:
        score = TeacherScore.objects.filter(
            teacher=teacher,
            year=year
        ).order_by('-id').first()

        scores.append(
            round(float(score.comprehensive_score), 2) if score is not None else None
        )
        score_is_demo.append(bool(score.is_demo) if score is not None else False)
        score_data_sources.append(score.data_source if score is not None else None)
        project_counts.append(
            Project.objects.filter(leader=teacher, start_date__year=year).count()
        )
        achievement_counts.append(
            Achievement.objects.filter(author=teacher, publish_year=year).count()
        )

    return JsonResponse({
        'years': years,
        'scores': scores,
        'score_is_demo': score_is_demo,
        'score_data_sources': score_data_sources,
        'projects': project_counts,
        'achievements': achievement_counts,
        'has_demo_scores': any(score_is_demo),
    })

def teacher_ability(request):
    """返回绩效表中真实记录的科研、教学、服务评分，并标明是否为演示数据。"""
    teacher, error_response = _teacher_from_request(request)
    if error_response is not None:
        return error_response

    raw_year = request.GET.get('year', '').strip()
    if raw_year:
        try:
            year = int(raw_year)
        except (TypeError, ValueError):
            return JsonResponse({'error': 'year 必须是有效年份'}, status=400)
    else:
        year = TeacherScore.objects.filter(
            teacher=teacher
        ).order_by('-year').values_list('year', flat=True).first()

    if year is None:
        return JsonResponse({
            'year': None,
            'data': [],
            'is_demo': False,
            'data_source': None,
        })

    score = TeacherScore.objects.filter(
        teacher=teacher,
        year=year
    ).order_by('-id').first()
    if score is None:
        return JsonResponse({
            'year': year,
            'data': [],
            'is_demo': False,
            'data_source': None,
        })

    data = [
        {'name': '科研得分', 'value': round(float(score.research_score), 2)},
        {'name': '教学得分', 'value': round(float(score.teaching_score), 2)},
        {'name': '服务得分', 'value': round(float(score.service_score), 2)},
    ]
    return JsonResponse({
        'year': year,
        'data': data,
        'is_demo': bool(score.is_demo),
        'data_source': score.data_source,
        'source_label': '演示数据' if score.is_demo else '原有记录',
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
    months = [f"{i}月" for i in range(1, 13)]
    current_year = 2025
    avg_score = TeacherScore.objects.filter(
        year=current_year, is_demo=False
    ).aggregate(avg=Avg('comprehensive_score'))['avg']
    if avg_score is None:
        avg_score = 75.0
    else:
        avg_score = float(avg_score)  # 转换为 float
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
    top_scores = TeacherScore.objects.filter(
        year=year, is_demo=False
    ).order_by('-comprehensive_score')[:10]
    data = []
    y_axis_labels = []
    for idx, ts in enumerate(top_scores):
        teacher = ts.teacher
        comp_score = float(ts.comprehensive_score) if ts.comprehensive_score else 70.0
        # 职称系数：教授0.9，副教授0.7，讲师0.5，助教0.3
        title_factor = {'教授': 0.9, '副教授': 0.7, '讲师': 0.5, '助教': 0.3}.get(teacher.title, 0.3)
        # 晋升概率 = 综合得分 * 职称系数 * 0.8 + 随机波动(0-10)
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
    # 学科分析默认只使用原有绩效，教师画像演示数据不进入未标注的院系统计。
    latest_year = TeacherScore.objects.filter(
        teacher__dept=dept, is_demo=False
    ).aggregate(max_year=Max('year'))['max_year'] or 2025
    teacher_scores = TeacherScore.objects.filter(
        teacher__dept=dept, year=latest_year, is_demo=False
    ).select_related('teacher')
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

# ==================================================
# 科研经费明细台账 API（复用现有 FundDetail / Project 模型）
# ==================================================
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