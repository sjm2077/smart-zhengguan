"""Deterministic synthetic teaching data helpers. Never a real data imputation model."""
from datetime import timedelta, date
from decimal import Decimal
from hashlib import sha256
import random

HISTORY = '[DEMO-HIST-V1]'
NORMALIZED = '[DEMO-NORM-V1]'
DEMO_NOTE = '演示数据：包含合成历史记录或人工生成的考核日期，仅供系统功能展示，不代表真实教学历史，不可作为真实预测效果证据。'


def rng(seed, *keys):
    digest = sha256('|'.join(map(str, (seed,) + keys)).encode('utf-8')).digest()
    return random.Random(int.from_bytes(digest[:8], 'big'))


def point(start, end, fraction):
    if start is None or end is None or start >= end:
        raise ValueError('invalid date interval')
    return start + timedelta(days=round((end - start).days * fraction))


def assessment_dates(start, end):
    if (end - start).days < 28:
        raise ValueError('need at least 28 days for assessments')
    return {'平时': point(start, end, .30), '期中': point(start, end, .52), '期末': point(start, end, .88)}


def select_roster(students, course_id, term_id, start, capacity, seed):
    """Students are (id, enrollment_year); no future-entry students or over-capacity."""
    cutoff_year = start.year if start.month >= 8 else start.year - 1
    eligible = [sid for sid, year in students if year <= cutoff_year]
    # Stable course affinity, with a small term-specific shift; no current scores used.
    ordered = sorted(eligible, key=lambda sid: (rng(seed, 'affinity', sid, course_id).random() + .12*rng(seed, 'shift', sid, course_id, term_id).random(), sid))
    n = min(capacity, len(eligible), max(1, round(len(eligible)*rng(seed,'size',term_id,course_id).uniform(.82,.96))))
    return ordered[:n]


def synthetic_score(seed, student_id, course_id, term_id, term_index, assessment):
    # Persistent student factor, course effect, term shock and assessment noise.
    ability = rng(seed,'ability',student_id).gauss(0, 10)
    difficulty = rng(seed,'course',course_id).gauss(0, 3)
    shift = rng(seed,'student-term',student_id,term_id).gauss(0, 4)
    noise = rng(seed,'assessment',student_id,course_id,term_id,assessment).gauss(0, 9)
    return Decimal(str(round(min(100, max(0, 74 + ability + difficulty + shift + noise + .8*term_index)), 2)))
