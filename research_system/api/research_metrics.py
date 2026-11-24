from decimal import Decimal

from django.db.models import Sum

from .models import Project, FundDetail, Achievement, TeacherScore, Cooperation


def teacher_real_score_rows(teacher):
    return TeacherScore.objects.filter(
        teacher=teacher,
        is_demo=False,
    ).order_by('year', 'id')


def teacher_real_years(teacher):
    years = set()

    years.update(
        int(y) for y in teacher_real_score_rows(teacher)
        .values_list('year', flat=True).distinct()
        if y is not None
    )
    years.update(
        int(y) for y in Project.objects.filter(leader=teacher)
        .values_list('start_date__year', flat=True).distinct()
        if y is not None
    )
    years.update(
        int(y) for y in FundDetail.objects.filter(project__leader=teacher)
        .values_list('year', flat=True).distinct()
        if y is not None
    )
    years.update(
        int(y) for y in Achievement.objects.filter(author=teacher)
        .values_list('publish_year', flat=True).distinct()
        if y is not None
    )
    return sorted(years)


def _h_index(citations):
    ordered = sorted((int(v or 0) for v in citations), reverse=True)
    return max(
        (rank for rank, value in enumerate(ordered, start=1) if value >= rank),
        default=0,
    )


def teacher_research_metrics(teacher):
    projects = Project.objects.filter(leader=teacher)
    achievements = Achievement.objects.filter(author=teacher)

    citations = list(achievements.values_list('citation_count', flat=True))
    total_citation = sum(int(v or 0) for v in citations)
    h_index = _h_index(citations)

    fund_total = (
        FundDetail.objects.filter(project__leader=teacher)
        .aggregate(total=Sum('amount'))['total']
        or Decimal('0')
    )

    cooperation_count = Cooperation.objects.filter(
        project__leader=teacher,
        is_demo=False,
    ).count()

    score_rows = list(teacher_real_score_rows(teacher))
    score_by_year = {}
    for row in score_rows:
        score_by_year[row.year] = row

    latest_score_year = max(score_by_year) if score_by_year else None
    latest_score = score_by_year.get(latest_score_year)

    growth_rate = None
    if latest_score_year is not None:
        recent = [
            score_by_year[y]
            for y in sorted(score_by_year)
            if latest_score_year - 2 <= y <= latest_score_year
        ]
        if len(recent) >= 2:
            first = float(recent[0].comprehensive_score)
            last = float(recent[-1].comprehensive_score)
            if first != 0 and recent[-1].year > recent[0].year:
                growth_rate = round((last - first) / first * 100, 1)

    return {
        'project_count': projects.count(),
        'ongoing_projects': projects.filter(status='在研').count(),
        'fund_total': round(float(fund_total), 2),
        'achievements_count': achievements.count(),
        'total_citation': total_citation,
        'h_index': h_index,
        'cooperation_count': cooperation_count,
        'comprehensive': (
            round(float(latest_score.comprehensive_score), 2)
            if latest_score is not None else None
        ),
        'score_year': latest_score_year,
        'growth_rate': growth_rate,
        'years': teacher_real_years(teacher),
        'score_years': sorted(score_by_year),
    }
