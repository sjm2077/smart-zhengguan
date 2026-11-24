"""Published-grade descriptive statistics; not an academic warning model."""
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from math import sqrt

BANDS = (("0–<60", 0, 6000), ("60–<70", 6000, 7000),
         ("70–<80", 7000, 8000), ("80–<90", 8000, 9000),
         ("90–100", 9000, 10001))
EXPLANATION = ("仅统计当前学期已发布的百分制成绩记录；同一学生可能有多种考核记录。"
               "60分、90分沿用系统描述性统计口径，不是学校正式学业预警阈值。"
               "未关联考试的成绩按系统百分制字段统计；关联非百分制考试或超出0–100分的记录不纳入。")


def _rate(n, total):
    return round(n * 100 / total, 2) if total else None


def _stats(hist):
    n = sum(hist.values())
    total = sum(s * c for s, c in hist.items())
    sq = sum(s * s * c for s, c in hist.items())
    counts = [sum(c for s, c in hist.items() if lo <= s < hi) for _, lo, hi in BANDS]
    median = None
    if n:
        positions = ((n - 1) // 2, n // 2)
        selected = []
        seen = 0
        for s, c in sorted(hist.items()):
            selected.extend(s for p in positions if seen <= p < seen + c)
            seen += c
            if len(selected) == 2:
                break
        median = round(sum(selected) / 200, 2)
    return {
        "records": n, "average_score": round(total / n / 100, 2) if n else None,
        "median_score": median,
        "std_score": round(sqrt(max(0, n * sq - total * total)) / n / 100, 2) if n else None,
        "pass_count": n - counts[0], "below_pass_count": counts[0], "excellent_count": counts[-1],
        "pass_rate": _rate(n - counts[0], n), "below_pass_rate": _rate(counts[0], n),
        "excellent_rate": _rate(counts[-1], n),
        "distribution": [{"label": label, "count": count, "rate": _rate(count, n)}
                         for (label, _, _), count in zip(BANDS, counts)],
    }


def summarize_grades(rows):
    """Consume (student_id, course_id, course_name, score, exam_total_score).

    Caller filters semester and publication. No individual identifiers leave this function.
    Integer cents ensure precise bin boundaries; population standard deviation.
    """
    hist = Counter()
    course_hist = defaultdict(Counter)
    students = set()
    valid_students = set()
    below_students = set()
    course_students = defaultdict(set)
    course_names = {}
    published = invalid = non_hundred = 0
    for sid, cid, name, raw, exam_total in rows:
        published += 1
        students.add(sid)
        if exam_total is not None and exam_total != 100:
            non_hundred += 1
            continue
        try:
            value = Decimal(str(raw))
            if not value.is_finite() or not 0 <= value <= 100 or value * 100 != (value * 100).to_integral_value():
                raise ValueError("invalid score")
            cents = int(value * 100)
        except (InvalidOperation, ValueError, TypeError):
            invalid += 1
            continue
        hist[cents] += 1
        course_hist[cid][cents] += 1
        course_names[cid] = name
        valid_students.add(sid)
        course_students[cid].add(sid)
        if cents < 6000:
            below_students.add(sid)
    result = _stats(hist)
    courses = []
    for cid in sorted(course_hist, key=lambda k: (course_names[k], k)):
        info = _stats(course_hist[cid])
        courses.append({"course_id": cid, "course_name": course_names[cid],
                        "student_count": len(course_students[cid]),
                        **{k: info[k] for k in ("records", "average_score", "pass_rate", "below_pass_rate", "excellent_rate")}})
    result.update(published_records=published, graded_students=len(students),
                  valid_students=len(valid_students), below_pass_students=len(below_students),
                  excluded_records=invalid + non_hundred, invalid_score_records=invalid,
                  non_hundred_exam_records=non_hundred, course_results=courses,
                  explanation=EXPLANATION)
    return result
