"""Opt-in, transactional demo history and reversible synthetic date normalization."""
import json
from collections import Counter
from datetime import date, datetime, time, timedelta
from pathlib import Path
from uuid import uuid4
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.core.serializers.json import DjangoJSONEncoder
from django.db import connection, transaction
from django.utils import timezone
from teaching.models import College, Semester, Student, TeachingClass, Exam, Grade
from teaching.demo_history_logic import HISTORY, NORMALIZED, assessment_dates, synthetic_score, select_roster

MODELS = {'TeachingClass': TeachingClass, 'Exam': Exam, 'Grade': Grade}
COLLEGE = 'SPPA'
CANCELLED = {'停开','已停开','取消','已取消','已结课','已结束'}


def jsonable(value):
    return json.loads(json.dumps(value, cls=DjangoJSONEncoder, ensure_ascii=False))


def snapshot(obj):
    # Serialize raw FK IDs and all fields; no user credentials or personal names.
    return jsonable({f.attname: (v.isoformat() if isinstance(v, (datetime, date)) else v)
                     for f in obj._meta.concrete_fields for v in [getattr(obj, f.attname)]})


def restore_values(model, state, fields):
    return {k: model._meta.get_field(k).to_python(state[k]) for k in fields}


def db_identity():
    d = connection.settings_dict
    return {k: str(d.get(k) or '') for k in ('ENGINE','NAME','HOST','PORT')}


def localday(dt):
    return timezone.localtime(dt).date() if timezone.is_aware(dt) else dt.date()


def at(day, hour=9):
    dt = datetime.combine(day, time(hour))
    return timezone.make_aware(dt) if settings.USE_TZ else dt


def prefixed(prefix, text, limit):
    value = prefix + ' ' + (text or '')
    if len(value) > limit:
        raise CommandError('Existing text would be truncated; no write performed.')
    return value


def write_manifest(path, data):
    # Exclusive creation, followed by fsync, before the database transaction commits.
    import os
    with path.open('x', encoding='utf-8') as f:
        json.dump(data, f, cls=DjangoJSONEncoder, ensure_ascii=False, indent=2)
        f.flush(); os.fsync(f.fileno())


def build_plan(seed, normalize, today):
    colleges = list(College.objects.filter(code=COLLEGE, is_active=True))
    if len(colleges) != 1:
        raise CommandError('Expected exactly one active SPPA demo college.')
    college = colleges[0]
    current = list(Semester.objects.filter(is_current=True))
    if len(current) != 1:
        raise CommandError('Expected exactly one current semester.')
    current = current[0]
    if not current.start_date or not current.end_date or not current.start_date <= today <= current.end_date:
        raise CommandError('Current term dates must include the local date; do not fabricate a clock.')
    terms = list(Semester.objects.filter(end_date__lt=current.start_date, start_date__isnull=False).order_by('-start_date','id')[:2])[::-1]
    if len(terms) != 2 or any(t.start_date >= t.end_date for t in terms) or terms[0].end_date >= terms[1].start_date:
        raise CommandError('Expected two non-overlapping closed historical terms.')
    for t in terms:
        if any(m.objects.filter(semester=t).exists() for m in MODELS.values()):
            raise CommandError('Historical term already contains records: %s. Refusing to append or overwrite; use rollback if this was a previous batch.' % t.name)
    classes = list(TeachingClass.objects.filter(semester=current).select_related('course','teacher').order_by('course_id','id'))
    active = [c for c in classes if c.status not in CANCELLED]
    if not active or len({c.course_id for c in active}) != len(active):
        raise CommandError('Need one active current class per course for this demo generator.')
    if any(c.course.college_id != college.id or c.teacher.college_id != college.id or not c.course.code.startswith('SPPA') or c.capacity <= 0 for c in active):
        raise CommandError('Current classes must be SPPA demo courses/teachers with positive capacity.')
    if len(active)>20:
        raise CommandError('This demo timetable supports at most 20 current courses; no overlapping class slots are invented.')
    course_ids = {c.course_id for c in active}
    students = list(Student.objects.filter(college=college,is_active=True).order_by('id').values_list('id','enrollment_year'))
    if not students:
        raise CommandError('No eligible SPPA students.')
    creates = []
    for ti, term in enumerate(terms):
        dates = assessment_dates(term.start_date, term.end_date)
        for ci, c in enumerate(active):
            roster = select_roster(students,c.course_id,term.id,term.start_date,c.capacity,seed)
            if len(roster) < 5:
                raise CommandError('Fewer than five historically eligible students for term %s; do not backdate admissions.' % term.name)
            # Reuse existing course and teacher IDs, not duplicate course catalog entries.
            key = '%s:%s' % (term.id,c.course_id)
            creates.append(('TeachingClass',key,dict(course_id=c.course_id,semester_id=term.id,teacher_id=c.teacher_id,
                class_name=HISTORY+' '+c.course.name[:70]+' 教学班',capacity=c.capacity,enrolled_count=len(roster),
                schedule='周%s第%s-%s节' % ('一二三四五'[ci%5], 1+2*(ci//5),2+2*(ci//5)),
                classroom='演示教室H-%03d' % (ci+1),status='已结课')))
            # Separate time slots also avoid clashes for students in multiple courses.
            course_dates = dict(dates)
            for kind in ('期中','期末'):
                course_dates[kind] = dates[kind] + timedelta(days=ci//2)
            if course_dates['期末'] > term.end_date or dates['期中']+timedelta(days=(len(active)-1)//2) >= dates['期末']:
                raise CommandError('Historical term too short for non-overlapping course exam timetable.')
            for kind in ('期中','期末'):
                ek = key+':'+kind
                creates.append(('Exam',ek,dict(name=HISTORY+' '+c.course.name[:100]+kind+'考试',course_id=c.course_id,semester_id=term.id,
                    exam_type=kind+'考试',exam_date=at(course_dates[kind],9 if ci%2==0 else 14),duration=120,total_score=100,
                    location='演示考场H-%03d' % (ci+1),status='已结束')))
            for sid in roster:
                for kind in ('平时','期中','期末'):
                    creates.append(('Grade',None,dict(student_id=sid,course_id=c.course_id,semester_id=term.id,
                        _exam_key=(key+':'+kind if kind!='平时' else None),score=synthetic_score(seed,sid,c.course_id,term.id,ti,kind),
                        grade_point=None,exam_type=kind,exam_date=course_dates[kind],remark=HISTORY+' 合成考核成绩；仅供演示。',is_published=True)))
    updates = []
    if normalize:
        dates = assessment_dates(current.start_date, min(today,current.end_date))
        exams = list(Exam.objects.filter(semester=current).order_by('course_id','id'))
        grades = list(Grade.objects.filter(semester=current,is_published=True).select_related('exam','student','course').order_by('id'))
        if not grades or not exams:
            raise CommandError('No current demo exam/grade records to normalize.')
        if any(e.course_id not in course_ids for e in exams) or any(g.course_id not in course_ids or g.student.college_id != college.id or g.student.enrollment_year > current.start_date.year for g in grades):
            raise CommandError('Current data outside confirmed SPPA cohort; refusing normalization.')
        if any(g.remark.startswith((HISTORY,NORMALIZED)) for g in grades) or any(e.name.startswith((HISTORY,NORMALIZED)) for e in exams):
            raise CommandError('Current records already marked as demo batch; refusing re-normalization.')
        if any(g.exam_type not in dates or (g.exam_id and (g.exam.semester_id != current.id or g.exam.course_id != g.course_id or g.exam.exam_type != g.exam_type+'考试')) for g in grades):
            raise CommandError('Unsupported assessment or inconsistent linked exam; no automatic relinking.')
        linked = {g.exam_id for g in grades if g.exam_id}
        # A linked published grade cannot be normalized to a future exam. All existing valid dates are preserved.
        new_exam_days = {}
        for i,e in enumerate(exams):
            original = localday(e.exam_date)
            limit = today if e.pk in linked else current.end_date
            if current.start_date <= original <= limit:
                new_exam_days[e.pk] = original
                continue
            if e.exam_type not in ('期中考试','期末考试','课程考核','补考'):
                raise CommandError('Unsupported exam type for date normalization.')
            base = dates['期中' if e.exam_type == '期中考试' else '期末']
            # Spread across days and morning/afternoon; preserve existing location and duration.
            candidate = min(limit, base + timedelta(days=i//2))
            new_dt = at(candidate, 9 if i%2==0 else 14)
            new_exam_days[e.pk] = candidate
            updates.append(('Exam',e,dict(exam_date=new_dt,name=prefixed(NORMALIZED,e.name,160))))
        for g in grades:
            if g.exam_id:
                day = new_exam_days[g.exam_id]
            elif g.exam_date and current.start_date <= g.exam_date <= today:
                day = g.exam_date
            else:
                day = dates[g.exam_type]
            if day != g.exam_date:
                updates.append(('Grade',g,dict(exam_date=day,remark=prefixed(NORMALIZED,g.remark,250))))
        # Reject unrelated grades (including unpublished) that would silently see moved exams.
        changed_exam_ids = [obj.pk for name,obj,_ in updates if name=='Exam']
        if Grade.objects.filter(exam_id__in=changed_exam_ids).exclude(semester=current,is_published=True).exists():
            raise CommandError('Moved exams have out-of-scope/unpublished linked grades; refusing to change them.')
        # Verify final exam venue intervals, including unchanged exams. No silent new clashes.
        changed = {obj.pk: changes['exam_date'] for name,obj,changes in updates if name=='Exam'}
        intervals = {}
        for e in exams:
            if not e.location.strip():
                continue
            start = changed.get(e.pk,e.exam_date); end = start+timedelta(minutes=e.duration)
            bucket=intervals.setdefault(e.location.strip(),[])
            if any(start < b and a < end for a,b in bucket):
                raise CommandError('Proposed normalization would leave an exam venue collision; no write.')
            bucket.append((start,end))
    return current,terms,creates,updates


class Command(BaseCommand):
    help = 'Preview by default. Generate marked SPPA demo history; optional synthetic date normalization, reversible via manifest.'

    def add_arguments(self, parser):
        parser.add_argument('--execute',action='store_true')
        parser.add_argument('--confirm-demo-db',default='')
        parser.add_argument('--normalize-current',action='store_true')
        parser.add_argument('--seed',type=int,default=42)
        parser.add_argument('--backup-dir')
        parser.add_argument('--rollback',help='Path to exact batch manifest. Default is rollback preview; --execute commits.')

    def handle(self,*args,**opts):
        execute=opts['execute']
        if execute and opts['confirm_demo_db'] != str(connection.settings_dict['NAME']):
            raise CommandError('Writes require --confirm-demo-db matching the database name and your confirmation it is a disposable DEMO database.')
        if execute and connection.vendor not in ('mysql','sqlite','postgresql'):
            raise CommandError('Unsupported transactional database.')
        if execute and connection.vendor == 'mysql':
            names=[m._meta.db_table for m in MODELS.values()]+[Semester._meta.db_table]
            with connection.cursor() as cursor:
                cursor.execute('SELECT TABLE_NAME, ENGINE FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME IN ('+','.join(['%s']*len(names))+')',names)
                engines=dict(cursor.fetchall())
            if any(str(engines.get(n,'')).lower()!='innodb' for n in names):
                raise CommandError('All affected MySQL tables must use InnoDB for atomic writes.')
        if opts['rollback']:
            return self.rollback(opts['rollback'],execute)
        if execute and not opts['backup_dir']:
            raise CommandError('Provide --backup-dir outside the repository.')
        # Stop other writers (including runserver) before execution. Locks serialize this command.
        with transaction.atomic():
            if execute:
                list(Semester.objects.select_for_update().order_by('id').values_list('id',flat=True))
            current,terms,creates,updates=build_plan(opts['seed'],opts['normalize_current'],timezone.localdate())
            self.stdout.write('Database: '+str(connection.settings_dict['NAME']))
            self.stdout.write('Mode: '+('EXECUTE DEMO ONLY' if execute else 'PREVIEW (NO WRITES)'))
            self.stdout.write('Current term: '+current.name)
            for t in terms:
                counts=Counter(m for m,_,values in creates if values['semester_id']==t.id)
                self.stdout.write('%s | %s..%s | %s' % (t.name,t.start_date,t.end_date,dict(counts)))
            self.stdout.write('Normalize existing current records: '+str(dict(Counter(m for m,_,_ in updates))))
            if not execute:
                self.stdout.write('PREVIEW OK. No database changes.'); return
            folder=Path(opts['backup_dir']).expanduser().resolve()
            root=Path(settings.BASE_DIR).resolve().parent
            if folder == root or root in folder.parents:
                raise CommandError('Backup directory must be outside project repository.')
            folder.mkdir(parents=True,exist_ok=True)
            path=folder/('demo_history_'+uuid4().hex+'.json')
            manifest={'version':1,'database':db_identity(),'seed':opts['seed'],'created':[],'updated':[], 'linked_guard':{}}
            exams={}
            grade_objects=[]
            for name,key,values in creates:
                v=dict(values)
                if name=='Grade':
                    ek=v.pop('_exam_key'); v['exam_id']=exams.get(ek)
                    if ek and not v['exam_id']:
                        raise CommandError('Internal exam link error.')
                    grade_objects.append(Grade(**v))
                else:
                    obj=MODELS[name].objects.create(**v)
                    if name=='Exam': exams[key]=obj.pk
            Grade.objects.bulk_create(grade_objects,batch_size=500)
            # Both terms were empty and writers stopped. Read DB-decoded snapshots,
            # including IDs on MySQL versions that do not return IDs for bulk_create.
            term_ids=[t.id for t in terms]
            for name,model in MODELS.items():
                for obj in model.objects.filter(semester_id__in=term_ids).order_by('id').iterator(chunk_size=1000):
                    manifest['created'].append({'model':name,'after':snapshot(obj)})
            if len(manifest['created'])!=len(creates):
                raise CommandError('Unexpected rows in historical terms; rollback transaction.')
            for name,model in MODELS.items():
                group=[(obj,changes) for m,obj,changes in updates if m==name]
                if not group: continue
                before={obj.pk:snapshot(obj) for obj,_ in group}
                fields=list(group[0][1])
                if any(set(changes)!=set(fields) for _,changes in group):
                    raise CommandError('Inconsistent update fields.')
                for obj,changes in group:
                    for field,value in changes.items(): setattr(obj,field,value)
                model.objects.bulk_update([obj for obj,_ in group],fields,batch_size=500)
                after=model.objects.in_bulk(list(before))
                for pk,original in before.items():
                    manifest['updated'].append({'model':name,'fields':fields,'before':original,'after':snapshot(after[pk])})
            moved=[e['after']['id'] for e in manifest['updated'] if e['model']=='Exam']
            for eid in moved:
                manifest['linked_guard'][str(eid)]=list(Grade.objects.filter(exam_id=eid).order_by('id').values_list('id',flat=True))
            write_manifest(path,manifest)
            self.stdout.write('Rollback manifest (keep private): '+str(path))
        self.stdout.write(self.style.SUCCESS('DEMO HISTORY COMMITTED.'))

    def rollback(self, filename, execute):
        path=Path(filename)
        data=json.loads(path.read_text(encoding='utf-8'))
        if data.get('version')!=1 or data.get('database')!=db_identity():
            raise CommandError('Manifest version/database mismatch.')
        with transaction.atomic():
            if execute:
                list(Semester.objects.select_for_update().order_by('id').values_list('id',flat=True))
            created=data['created']; updated=data['updated']
            for name,model in MODELS.items():
                entries=[e for e in created+updated if e['model']==name]
                actual=model.objects.in_bulk([e['after']['id'] for e in entries])
                for entry in entries:
                    expected=entry['after']; obj=actual.get(expected['id'])
                    if obj is None or snapshot(obj)!=expected:
                        raise CommandError('Rollback stopped: row missing or changed since batch: %s/%s' % (name,expected['id']))
            for eid,ids in data.get('linked_guard',{}).items():
                if list(Grade.objects.filter(exam_id=eid).order_by('id').values_list('id',flat=True)) != ids:
                    raise CommandError('Rollback stopped: links to a normalized exam changed.')
            markers={'Grade':'remark','Exam':'name','TeachingClass':'class_name'}
            if any(not e['after'][markers[e['model']]].startswith(HISTORY) for e in created):
                raise CommandError('Rollback stopped: unmarked generated record in manifest.')
            grade_ids=[e['after']['id'] for e in created if e['model']=='Grade']
            exam_ids=[e['after']['id'] for e in created if e['model']=='Exam']
            if Grade.objects.filter(exam_id__in=exam_ids).exclude(pk__in=grade_ids).exists():
                raise CommandError('Rollback stopped: other grades now reference generated exams.')
            self.stdout.write('Rollback %s | delete %s generated rows | restore %s existing rows' % ('EXECUTE' if execute else 'PREVIEW',len(created),len(updated)))
            if not execute: return
            for entry in reversed(updated):
                model=MODELS[entry['model']]; before=entry['before']
                model.objects.filter(pk=before['id']).update(**restore_values(model,before,entry['fields']))
            for name in ('Grade','Exam','TeachingClass'):
                ids=[e['after']['id'] for e in created if e['model']==name]
                MODELS[name].objects.filter(pk__in=ids).delete()
        self.stdout.write(self.style.SUCCESS('ROLLBACK COMMITTED.'))
