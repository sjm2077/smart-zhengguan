"""Read-only operational aggregates. No invented timetable or workload hours."""
from collections import Counter, defaultdict
import re

WEEKDAYS = '一二三四五六日'
# Only unambiguous single weekday + period strings; free text stays unparsed.
SLOT = re.compile(r'(?:周|星期)([一二三四五六日天])\s*第?\s*\d+(?:\s*[-－—至~～]\s*\d+)?\s*节')


def summarize_operations(classes, exams, local_datetime=lambda value: value):
    teachers = defaultdict(lambda: {'name': '', 'classes': 0, 'courses': set()})
    capacity = enrolled_known = enrolled_all = spare = excess = full = over = known = 0
    weekdays = Counter()
    unparsed = unscheduled = 0
    for row in classes:
        teacher = teachers[row.teacher_id]
        teacher['name'] = row.teacher.name
        teacher['classes'] += 1
        teacher['courses'].add(row.course_id)
        enrolled_all += row.enrolled_count
        if row.capacity > 0:
            known += 1
            capacity += row.capacity
            enrolled_known += row.enrolled_count
            spare += max(0, row.capacity - row.enrolled_count)
            excess += max(0, row.enrolled_count - row.capacity)
            full += int(row.enrolled_count == row.capacity)
            over += int(row.enrolled_count > row.capacity)
        schedule = str(row.schedule or '').strip()
        if not schedule:
            unscheduled += 1
        else:
            match = SLOT.fullmatch(schedule)
            if match:
                weekdays['日' if match[1] == '天' else match[1]] += 1
            else:
                unparsed += 1
    teacher_rows = sorted(
        ({'id': key, 'name': row['name'], 'classes': row['classes'], 'courses': len(row['courses'])}
         for key, row in teachers.items()), key=lambda x: (-x['classes'], x['id']))
    days, rooms = Counter(), Counter()
    for exam in exams:
        if exam.exam_date is not None:
            days[local_datetime(exam.exam_date).date().isoformat()] += 1
        room = str(exam.location or '').strip()
        if room:
            rooms[room] += 1
    busiest = sorted(days.items(), key=lambda pair: (-pair[1], pair[0]))[:8]
    return {
        'active_classes': len(classes), 'active_courses': len({c.course_id for c in classes}),
        'teachers': len(teachers), 'enrolled_total': enrolled_all,
        'teacher_average_classes': round(len(classes) / len(teachers), 2) if teachers else None,
        'teacher_max_classes': max((x['classes'] for x in teacher_rows), default=None),
        'teacher_distribution': [{'classes': k, 'teachers': v} for k, v in sorted(Counter(x['classes'] for x in teacher_rows).items())],
        'teacher_preview': teacher_rows[:8],
        'capacity': {'known_classes': known, 'unknown_classes': len(classes)-known, 'seats': capacity,
                     'enrolled': enrolled_known, 'utilization': round(100*enrolled_known/capacity, 2) if capacity else None,
                     'spare': spare, 'excess': excess, 'full_classes': full, 'over_classes': over},
        'schedule': {'parsed': sum(weekdays.values()), 'unparsed': unparsed, 'missing': unscheduled,
                     'weekdays': [{'label': '周'+day, 'count': weekdays[day]} for day in WEEKDAYS]},
        'exams': {'total': len(exams), 'days': len(days), 'dated': sum(days.values()),
                  'peak_daily': max(days.values(), default=None), 'venues': len(rooms),
                  'located': sum(rooms.values()), 'peak_venue': max(rooms.values(), default=None),
                  'busiest_days': [{'date': day, 'count': count} for day,count in busiest]},
    }


def operation_facts(stats):
    """External provider only receives aggregate numbers; no teacher names/IDs/room labels."""
    if stats is None:
        return {'说明': '当前学期未建立或教学班、考试记录超过完整统计上限，暂无综合统计。'}
    s, c, e = stats['schedule'], stats['capacity'], stats['exams']
    return {
        '在开教学班数': stats['active_classes'], '在开课程数（按教学班去重）': stats['active_courses'],
        '任课教师去重人数': stats['teachers'], '选课登记人次': stats['enrolled_total'],
        '教师平均承担教学班数': stats['teacher_average_classes'], '教师最多承担教学班数': stats['teacher_max_classes'],
        '教师任务分布': [{'承担教学班数': x['classes'], '教师人数': x['teachers']} for x in stats['teacher_distribution']],
        '教学任务口径': '按教学班数量统计，不是实际授课学时或教师绩效。选课人次不是去重人数。',
        '容量统计': {'已登记正容量班数': c['known_classes'], '未登记正容量班数': c['unknown_classes'],
                    '计划总容量': c['seats'], '对应选课人次': c['enrolled'], '容量利用率百分数': c['utilization'],
                    '各班剩余容量合计': c['spare'], '各班超出容量合计': c['excess'], '恰好满额班数': c['full_classes'], '超容量班数': c['over_classes']},
        '排课统计': {'可解析班数': s['parsed'], '格式未解析班数': s['unparsed'], '未登记班数': s['missing'],
                   '星期分布': [{'星期': x['label'], '班数': x['count']} for x in s['weekdays']],
                   '说明': '仅识别单一明确星期及节次格式，不代表实际每周课时。'},
        '考试统计': {'登记场次': e['total'], '有日期场次': e['dated'], '涉及日期数': e['days'], '单日最多场次': e['peak_daily'],
                   '已登记地点场次': e['located'], '不同地点名称数': e['venues'], '单一地点最多累计场次': e['peak_venue'],
                   '说明': '按本地日期和原登记地点名称统计，不能推断实际考场占用率或座位利用率。'},
    }
