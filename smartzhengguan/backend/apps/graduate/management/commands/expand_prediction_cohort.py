"""Prepare a balanced demonstration cohort and sync it without clearing business data."""
import json
import random
import sys
from collections import Counter
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.graduate.models import Student, DegreeType, EnrollmentType
from apps.graduate.management.commands.import_excel_data import Command as ImportCommand


DEGREES = {"学术型硕士": DegreeType.ACADEMIC_MASTER,
           "专业型硕士": DegreeType.PROFESSIONAL_MASTER, "博士": DegreeType.DOCTORAL}


def normalized_degree(row):
    if row[2] in DEGREES:
        return row[2]
    if row[2] == "硕士":
        return "专业型硕士" if "管理" in row[4] else "学术型硕士"
    raise CommandError(f"Unknown degree type: {row[2]}")


def expand_rows(existing, target=35):
    sys.path.insert(0, str(settings.BASE_DIR.parent))
    from expand_prediction_students import GRADES, MAJOR_CODES, SURNAMES, GIVEN_NAMES, ADVISORS, build_row
    rng = random.Random(20261026)
    rows = [list(row) for row in existing]
    for row in rows:
        row[2] = normalized_degree(row)
    counts = Counter((row[2], row[3], row[4]) for row in rows)
    if any(count > 40 for count in counts.values()):
        raise CommandError("Existing group exceeds 40; refusing to delete students")
    used_ids = {str(row[1]) for row in rows}
    used_names = {row[0] for row in rows}
    sequence = 1000
    for degree in DEGREES:
        for grade in GRADES:
            for major, code in MAJOR_CODES.items():
                key = (degree, grade, major)
                for index in range(max(0, target - counts[key])):
                    while True:
                        sequence += 1
                        sid = f"{grade[:4]}{code}{sequence:04d}"
                        if sid not in used_ids:
                            break
                    used_ids.add(sid)
                    while True:
                        name = rng.choice(SURNAMES) + rng.choice(GIVEN_NAMES)
                        if name not in used_names:
                            break
                        # Expand the name space without introducing number placeholders.
                        name = rng.choice(SURNAMES) + rng.choice(GIVEN_NAMES)[0] + rng.choice(GIVEN_NAMES)[-1]
                        if name not in used_names:
                            break
                    used_names.add(name)
                    row = build_row(rng, name, sid, degree, grade, major, rng.choice(ADVISORS))
                    # Demonstration cases: mostly healthy, with visible examples
                    # of overdue work, incomplete training and low communication.
                    bucket = index % 20
                    if bucket < 13:
                        row[7:11] = [rng.randint(83, 96), rng.randint(78, 96), rng.randint(94, 100), "已完成"]
                        row[19:22] = [0, 0, rng.randint(82, 96)]
                    elif bucket < 17:
                        row[7:11] = [rng.randint(80, 90), rng.randint(72, 88), rng.randint(91, 98), "进行中"]
                        row[19:22] = [rng.randint(0, 1), 0, rng.randint(80, 92)]
                    row[17] = rng.randint(0, 1) if bucket in (15, 16, 18) else rng.randint(4, 18)
                    rows.append(row)
    return rows


class Command(BaseCommand):
    help = "Prepare 35 named samples per degree/grade/major, or sync the final workbook"

    def add_arguments(self, parser):
        parser.add_argument('--prepare-json', type=Path)
        parser.add_argument('--sync', action='store_true')
        parser.add_argument('--file', type=Path, default=settings.BASE_DIR.parent / '研究生数据_2021-2026.xlsx')

    def handle(self, *args, **options):
        from openpyxl import load_workbook
        workbook = load_workbook(options['file'], read_only=True)
        sheet = workbook['智能预测-学生数据']
        original = list(sheet.values)
        headers, existing = original[0], [row for row in original[1:] if row[0]]
        if options['prepare_json']:
            rows = expand_rows(existing)
            options['prepare_json'].write_text(json.dumps({'headers': headers, 'rows': rows}, ensure_ascii=False), encoding='utf-8')
            self.stdout.write(f'Prepared {len(rows)} samples; added {len(rows) - len(existing)}')
        if options['sync']:
            rows = [dict(zip(headers, row)) for row in existing]
            counts = Counter((r['类别'], r['年级'], r['专业']) for r in rows)
            if len(counts) != 120 or any(not 30 <= value <= 40 for value in counts.values()):
                raise CommandError('Expected 120 groups with 30-40 samples each')
            if len({str(row['学号']) for row in rows}) != len(rows):
                raise CommandError('Duplicate student IDs')
            importer = ImportCommand()
            new_rows = []
            with transaction.atomic():
                for row in rows:
                    degree = DEGREES[row['类别']]
                    _, created = Student.objects.update_or_create(
                        student_id=str(row['学号']), defaults={
                            'name': row['姓名'], 'grade': row['年级'], 'major': row['专业'],
                            'college': row['学院'], 'advisor_name': row['导师'],
                            'degree_type': degree,
                            'enrollment_type': EnrollmentType.DOCTORAL if degree == DegreeType.DOCTORAL else EnrollmentType.MASTER,
                        })
                    if created:
                        new_rows.append(row)
                # Only new students receive generated snapshots/history. Existing
                # snapshot IDs, history and all other modules stay intact.
                if new_rows:
                    importer.sheet_rows = lambda _workbook, _sheet: new_rows
                    importer.import_predictions(workbook, importer.build_student_context())
                from apps.graduate.models import PredictionSnapshot
                if PredictionSnapshot.objects.filter(student__student_id__in=[str(r['学号']) for r in rows]).values('student_id').distinct().count() != len(rows):
                    raise CommandError('Snapshot count does not match final workbook')
            self.stdout.write(self.style.SUCCESS(f'Synced {len(rows)} students; added {len(new_rows)}; groups={len(counts)} min={min(counts.values())} max={max(counts.values())}'))
        workbook.close()
