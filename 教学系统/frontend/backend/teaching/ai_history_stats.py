"""Read-only registered-semester history. No forecasting, no inferred semester reassignment."""
from collections import defaultdict
from .ai_grade_stats import summarize_grades
from .demo_history_logic import HISTORY, NORMALIZED, DEMO_NOTE

MAX_TERMS = 8
# Completed classes remain part of historical teaching activity.
CANCELLED = {'停开', '已停开', '已取消', '取消'}


def date_quality(dates, start, end):
    valid = bool(start and end and start <= end)
    result = {'missing': 0, 'outside': 0 if valid else None, 'dated': 0}
    for day in dates:
        if day is None:
            result['missing'] += 1
        else:
            result['dated'] += 1
            if valid and not start <= day <= end:
                result['outside'] += 1
    return result


def summarize_term(term, today):
    from django.utils import timezone
    from .models import TeachingClass, Exam, Grade
    start, end = term.start_date, term.end_date
    bounds_valid = bool(start and end and start <= end)
    classes = [r for r in TeachingClass.objects.filter(semester_id=term.id).order_by().values_list(
        'course_id', 'teacher_id', 'capacity', 'enrolled_count', 'status')
        if str(r[4] or '').strip() not in CANCELLED]
    positive = [r for r in classes if r[2] > 0]
    seats = sum(r[2] for r in positive)
    enrolled = sum(r[3] for r in positive)
    exams = list(Exam.objects.filter(semester_id=term.id).order_by().values_list('exam_date', flat=True))
    exam_dates = [timezone.localtime(d).date() if timezone.is_aware(d) else d.date() for d in exams if d is not None]
    exam_dates += [None] * (len(exams) - len(exam_dates))
    grades = Grade.objects.filter(semester_id=term.id, is_published=True).order_by().values_list(
        'student_id', 'course_id', 'course__name', 'score', 'exam__total_score',
        'exam_date', 'exam__semester_id', 'exam__course_id', 'remark')
    grade_dates = []
    conflicts = 0
    generated = normalized = 0
    def grade_rows():
        nonlocal conflicts, generated, normalized
        for row in grades.iterator(chunk_size=2000):
            grade_dates.append(row[5])
            generated += (row[8] or "").startswith(HISTORY)
            normalized += (row[8] or "").startswith(NORMALIZED)
            if row[6] is not None and (row[6] != term.id or row[7] != row[1]):
                conflicts += 1
            yield row[:5]
    g = summarize_grades(grade_rows())
    quality = {'bounds_valid': bounds_valid, 'exams': date_quality(exam_dates, start, end),
               'grades': date_quality(grade_dates, start, end), 'linked_exam_conflicts': conflicts}
    has_data = bool(classes or exams or g['published_records'])
    period = ('unknown' if not bounds_valid else 'future' if start > today else 'closed' if end < today else 'open')
    return {'id': term.id, 'name': term.name, 'start': start.isoformat() if start else None,
            'end': end.isoformat() if end else None, 'period': period, 'has_data': has_data,
            'classes': len(classes), 'courses': len({r[0] for r in classes}), 'teachers': len({r[1] for r in classes}),
            'enrolled': sum(r[3] for r in classes), 'capacity_seats': seats,
            'capacity_enrolled': enrolled, 'capacity_classes': len(positive),
            'capacity_rate': round(100 * enrolled / seats, 2) if seats else None,
            'exams': len(exams), 'grade_records': g['records'], 'published_records': g['published_records'],
            'valid_students': g['valid_students'], 'excluded_records': g['excluded_records'],
            'average_score': g['average_score'], 'pass_rate': g['pass_rate'], 'excellent_rate': g['excellent_rate'],
            'quality': quality, 'demo_generated_grades': generated, 'demo_normalized_grades': normalized}, g['course_results']


def build_course_series(term_results):
    grouped = defaultdict(list)
    for term, courses in term_results:
        for course in courses:
            grouped[course['course_id']].append({'semester_id': term['id'], 'semester': term['name'],
                'period': term['period'], **{k: course[k] for k in ('course_name','student_count','records','average_score','pass_rate','excellent_rate')}})
    return [{'course_id': cid, 'course_name': rows[-1]['course_name'], 'terms': rows}
            for cid, rows in sorted(grouped.items(), key=lambda item: (item[1][-1]['course_name'], item[0])) if len(rows) >= 2]


def collect_history(current_id=None):
    from django.utils import timezone
    from .models import Semester
    today = timezone.localdate()
    all_terms = list(Semester.objects.all().order_by('start_date', 'id'))
    current = next((s for s in all_terms if s.id == current_id), None)
    cutoff = current.start_date if current and current.start_date else today
    prior = [s for s in all_terms if s.id != current_id and s.start_date and s.start_date < cutoff and s.start_date <= today]
    selected = prior[-(MAX_TERMS - 1 if current else MAX_TERMS):] + ([current] if current else [])
    selected.sort(key=lambda s: (s.start_date is None, s.start_date or today, s.id))
    results = [summarize_term(s, today) for s in selected]
    rows = [r for r, _ in results]
    return {'terms': rows, 'courses': build_course_series(results), 'current_id': current_id,
            'total_archives': len(all_terms), 'undated_archives': sum(s.start_date is None for s in all_terms),
            'excluded_archives': len(all_terms) - len(rows),
            'observed_terms': sum(r['has_data'] for r in rows),
            'grade_terms': sum(r['grade_records'] > 0 for r in rows),
            'note': (DEMO_NOTE + ' ' if any(r['demo_generated_grades'] or r['demo_normalized_grades'] for r in rows) else '') + '按业务记录登记学期统计，最多8期（当前学期及此前有起始日期的学期）。历史教学班保留已结课班，排除停开、取消班；课程按教学班去重。无记录不等于实际为零；在读学期与结课学期、考核构成可能不同，仅作登记数据描述性对照。日期异常不自动改归属，不据此预测。'}


def history_facts(history):
    if not history:
        return {'说明': '本次未读取历史数据。'}
    periods = {'open':'进行中','closed':'日期已结束（不代表数据齐全）','unknown':'日期不完整或无效','future':'尚未开始'}
    rows = []
    for r in history['terms']:
        q = r['quality']
        row = {'学期': r['name'], '起止日期': [r['start'],r['end']], '日期状态': periods[r['period']],
               '有业务记录': r['has_data'], '合成演示成绩记录数': r.get('demo_generated_grades',0), '人工规范化日期成绩记录数': r.get('demo_normalized_grades',0), '登记课程数': r['courses'], '登记教学班数': r['classes'],
               '任课教师数': r['teachers'], '选课登记人次': r['enrolled'], '正容量班容量利用率百分数': r['capacity_rate'],
               '登记考试数': r['exams'], '有效成绩记录数': r['grade_records'], '排除成绩记录数': r['excluded_records'],
               '考试日期越界数': q['exams']['outside'], '考试缺日期数': q['exams']['missing'],
               '已发布成绩日期越界数': q['grades']['outside'], '已发布成绩缺日期数': q['grades']['missing'],
               '成绩关联考试学期或课程冲突数': q['linked_exam_conflicts']}
        if r['valid_students'] >= 5:
            row.update({'记录均分':r['average_score'], '记录及格率百分数':r['pass_rate'], '记录优秀率百分数':r['excellent_rate']})
        else:
            row['成绩说明'] = '有效成绩涉及学生不足5人，不提供详细分数统计。'
        rows.append(row)
    series = []
    for c in history['courses']:
        eligible = [t for t in c['terms'] if t['student_count'] >= 5]
        if len(eligible) >= 2:
            series.append({'课程':c['course_name'], '学期统计':[{'学期':t['semester'],'有效记录数':t['records'],
                '记录均分':t['average_score'],'记录及格率百分数':t['pass_rate'],'记录优秀率百分数':t['excellent_rate']} for t in eligible]})
    return {'说明':history['note'], '学期档案总数':history['total_archives'], '未展示档案数':history['excluded_archives'],
            '有业务记录学期数':history['observed_terms'], '有有效成绩学期数':history['grade_terms'],
            '学期统计':rows, '同课程样本':series[:15], '同课程样本说明':'只按相同课程ID关联；每期至少5名不同学生，最多15门，不代表全体。'}
