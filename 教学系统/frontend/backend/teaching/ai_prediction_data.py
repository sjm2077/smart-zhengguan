"""Demo-only, time-ordered student/course final-assessment dataset."""
from collections import Counter, defaultdict
from datetime import timedelta
from math import isfinite
from statistics import mean, pstdev

HISTORY = '[DEMO-HIST-V1]'
FEATURES = ('usual_score', 'midterm_score', 'course_early_mean',
            'other_course_early_mean', 'other_course_low_ratio',
            'other_course_std', 'other_course_count', 'has_other_course')
KINDS = ('平时', '期中', '期末')


def cutoff_for(start, end):
    if not start or not end or (end-start).days < 28:
        raise ValueError('Invalid semester date interval')
    return start + timedelta(days=round((end-start).days * .65))


def build_examples(records, start, end):
    """Each row is one student/course. Label is final <60, not a formal warning.
    No future or final score enters features. Only synthetic history is accepted.
    """
    cutoff = cutoff_for(start, end)
    cells = defaultdict(dict)
    counts = Counter()
    for r in records:
        counts['input_records'] += 1
        if not str(r.get('remark') or '').startswith(HISTORY):
            raise ValueError('Non-synthetic grade in selected semester; demo training blocked')
        kind = r['exam_type']
        day = r['exam_date']
        try:
            score = float(r['score'])
        except (ValueError, TypeError):
            counts['invalid_score'] += 1; continue
        if not isfinite(score) or not 0 <= score <= 100:
            counts['invalid_score'] += 1; continue
        if kind not in KINDS or not day or not start <= day <= end:
            counts['invalid_kind_or_date'] += 1; continue
        if r.get('exam_id') and (r.get('exam__course_id') != r['course_id'] or
                r.get('exam__semester_id') != r['semester_id'] or
                r.get('exam__exam_type') != kind+'考试' or
                r.get('exam__total_score') != 100 or r.get('linked_day') != day):
            counts['invalid_exam_link'] += 1; continue
        if kind == '期末':
            if day <= cutoff:
                counts['final_not_after_cutoff'] += 1; continue
        elif day > cutoff:
            counts['early_after_cutoff'] += 1; continue
        key = (r['student_id'], r['course_id'])
        if kind in cells[key]:
            raise ValueError('Duplicate student/course/assessment')
        cells[key][kind] = score
    # Construct other-course features using early records only, including courses
    # whose final is missing. Eligibility must not depend on future outcomes.
    early_by_student = defaultdict(dict)
    for (sid,cid), vals in cells.items():
        early = [vals[k] for k in KINDS[:2] if k in vals]
        if early:
            early_by_student[sid][cid] = early
    rows = []
    for (sid,cid), vals in sorted(cells.items()):
        if not all(k in vals for k in KINDS[:2]):
            counts['missing_early_pair'] += 1; continue
        if '期末' not in vals:
            counts['missing_future_final'] += 1; continue
        usual, mid = (vals[k] for k in KINDS[:2]); avg=(usual+mid)/2
        others = {c:v for c,v in early_by_student[sid].items() if c != cid}
        flat = [x for v in others.values() for x in v]
        features = [usual, mid, avg, mean(flat) if flat else avg,
                    sum(x<60 for x in flat)/len(flat) if flat else 0.,
                    pstdev(flat) if flat else 0., len(others), int(bool(flat))]
        rows.append((sid,cid,features,int(vals['期末']<60)))
    counts['examples'] = len(rows)
    counts['positive'] = sum(r[3] for r in rows)
    counts['students'] = len({r[0] for r in rows})
    return rows, dict(counts), cutoff
