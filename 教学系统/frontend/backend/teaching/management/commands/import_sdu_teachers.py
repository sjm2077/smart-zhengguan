# -*- coding: utf-8 -*-
"""Import reviewed public faculty directory without reassigning demo classes."""
import csv
import hashlib
import json
import re
from pathlib import Path
from datetime import datetime
from urllib.parse import urlsplit
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from teaching.models import College, Teacher, TeachingClass, UserProfile

DB = 'college_teaching'
COLLEGE = '政治学与公共管理学院'
ROSTER = 'https://pspa.sdu.edu.cn/jytd/qzjs.htm'
DEPTS = {'科社系、当代社会主义研究基地':13,'政治学系':19,'国际政治系':17,'公共管理系':39,'公共治理研究院':5}
TITLES = {'教授','副教授','讲师','助理研究员','副研究员','博士后'}
EXTRA = [('degree','学位'),('education','学历'),('graduated_from','毕业院校'),('discipline','学科'),('research_direction','研究方向')]
DEMO = re.compile(r'^(?:演示)?教师(0[1-9]|10)$')
TAG = '【官网公开师资档案】'
DEMO_TAG = '【演示教师】虚拟业务账号/教师档案；关联教学任务均用于系统演示，不对应官网真实教师。'
FIELDS = ('teacher_no','name','gender','college_id','title','phone','email','description','is_active')

def official_url(url):
    p=urlsplit(url)
    host=p.hostname or ''
    return p.scheme=='https' and host.endswith('.sdu.edu.cn') and not p.username and not p.password

def load_rows(path):
    from collections import Counter
    with Path(path).open(encoding='utf-8-sig', newline='') as f:
        rows=[{k:(v or '').strip() for k,v in r.items()} for r in csv.DictReader(f)]
    if len(rows)!=93 or len({r['name'] for r in rows})!=93 or Counter(r['department'] for r in rows)!=DEPTS:
        raise CommandError('CSV does not match the reviewed 93-row roster.')
    for r in rows:
        if not r['name'] or len(r['name'])>80 or r['title'] not in TITLES or r['source_url']!=ROSTER:
            raise CommandError('Invalid roster row: '+r['name'])
        if r['profile_url'] and not official_url(r['profile_url']):
            raise CommandError('Non-official profile URL: '+r['name'])
        if r['gender'] not in ('','男','女') or r['degree']=='博士生' or r['research_direction']=='论文成果':
            raise CommandError('Unclean profile data: '+r['name'])
    return rows

def values(row, college_id):
    # Stable local directory number, not an official staff identifier.
    key=hashlib.sha256(row['name'].encode('utf-8')).hexdigest()[:16].upper()
    desc=[TAG,'所属系所：'+row['department'],'名录类别：'+row['title'], '档案编号为系统本地编号，非学校正式工号。','名录来源：'+ROSTER,'名录快照：'+row['snapshot_date']]
    if row['profile_url']:
        desc.append('个人主页：'+row['profile_url'])
    if row['profile_status']=='profile_read':
        extra=[label+'：'+row[k] for k,label in EXTRA if row[k]]
        if extra: desc+=['主页自动采集信息（待进一步核实）：']+extra
    else:
        desc.append('个人主页资料暂未取得。')
    desc.append('公开师资名录导入；不证明内部人事状态、实际授课安排，不关联演示教学任务。')
    return dict(teacher_no='DIR-'+key,name=row['name'],gender=row['gender'] or '未说明',college_id=college_id,title=row['title'],phone='',email='',description='\n'.join(desc),is_active=True)

def snapshot(obj): return {k:getattr(obj,k) for k in FIELDS}

def related_exists(obj):
    # Also guard against relationships added in later versions of the schema.
    for rel in obj._meta.related_objects:
        accessor=rel.get_accessor_name()
        if not accessor: continue
        if rel.one_to_one:
            if hasattr(obj,accessor): return True
        else:
            if getattr(obj,accessor).exists(): return True
    return False

class Command(BaseCommand):
    help='Preview/apply reviewed SDU faculty directory import. No grade/class/account reassignment.'
    def add_arguments(self,p):
        p.add_argument('--csv',type=Path)
        p.add_argument('--execute',action='store_true')
        p.add_argument('--confirm-demo-db',default='')
        p.add_argument('--mark-demo',action='store_true')
        p.add_argument('--backup-dir',type=Path)
        p.add_argument('--rollback',type=Path)
    def handle(self,*args,**o):
        if connection.settings_dict['NAME']!=DB: raise CommandError('Unexpected database; expected '+DB)
        if o['execute'] and o['confirm_demo_db']!=DB: raise CommandError('Explicit demo database confirmation required.')
        if o['rollback']:
            if not o['execute']: raise CommandError('Rollback requires --execute and database confirmation.')
            return self.undo(o['rollback'])
        if not o['csv']: raise CommandError('--csv required')
        rows=load_rows(o['csv'])
        # Both modes use the same planning path; preview never calls save/create.
        with transaction.atomic():
            colleges=College.objects.filter(name=COLLEGE)
            if o['execute']: colleges=colleges.select_for_update()
            college=colleges.get()
            qs=Teacher.objects.all()
            if o['execute']: qs=qs.select_for_update()
            existing=list(qs.order_by('pk'))
            by_no={t.teacher_no:t for t in existing}
            by_name={}
            for t in existing:
                if t.college_id==college.pk: by_name.setdefault(t.name,[]).append(t)
            create=[]; unchanged=[]; conflicts=[]; demos=[]
            for r in rows:
                v=values(r,college.pk); t=by_no.get(v['teacher_no']); same=by_name.get(v['name'],[])
                if t:
                    if snapshot(t)==v and len(same)==1 and same[0].pk==t.pk: unchanged.append(t.pk)
                    else: conflicts.append(v['name']+' (local number or existing record mismatch)')
                elif same: conflicts.append(v['name']+' (existing same-name record; manual review needed)')
                else: create.append(v)
            if o['mark_demo']:
                candidates=[t for t in existing if t.college_id==college.pk and DEMO.fullmatch(t.name)]
                numbers=[DEMO.fullmatch(t.name).group(1) for t in candidates]
                if sorted(numbers)!=['%02d'%i for i in range(1,11)]:
                    raise CommandError('Expected exactly demo teacher 01..10; no records changed.')
                for t in candidates:
                    name='演示教师'+DEMO.fullmatch(t.name).group(1)
                    if any(x.pk!=t.pk for x in by_name.get(name,[])): raise CommandError('Demo name collision')
                    desc=t.description
                    if DEMO_TAG not in desc: desc=(desc+'\n'+DEMO_TAG).strip()
                    if t.name!=name or t.description!=desc: demos.append((t,name,desc))
            self.stdout.write('Database: '+DB+' | College: '+college.name+' | id='+str(college.pk))
            self.stdout.write('Mode: '+('EXECUTE' if o['execute'] else 'PREVIEW (NO WRITES)'))
            self.stdout.write('Create official directory: %d; already identical: %d; conflicts: %d; mark demo: %d'%(len(create),len(unchanged),len(conflicts),len(demos)))
            self.stdout.write('Existing teacher total: %d; expected total: %d'%(len(existing),len(existing)+len(create)))
            self.stdout.write('TeachingClass links: %d; UserProfile teacher links: %d'%(TeachingClass.objects.count(),UserProfile.objects.filter(teacher__isnull=False).count()))
            for t,name,_ in demos: self.stdout.write('DEMO %s -> %s | id=%s | classes=%s | linked accounts=%s'%(t.name,name,t.pk,TeachingClass.objects.filter(teacher=t).count(),UserProfile.objects.filter(teacher=t).count()))
            if conflicts: raise CommandError('Conflicts (no writes): '+'; '.join(conflicts))
            if not o['execute']:
                self.stdout.write('PREVIEW OK. NO WRITES.'); return
            if not create and not demos:
                self.stdout.write('NO CHANGES. Already imported.'); return
            if not o['backup_dir']: raise CommandError('--backup-dir required for writes.')
            backup=o['backup_dir']; backup.mkdir(parents=True,exist_ok=True)
            path=backup/('sdu_teacher_import_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f')+'.json')
            manifest={'database':DB,'college_id':college.pk,'created':[],'marked':[]}
            for v in create:
                t=Teacher(**v); t.full_clean(); t.save(force_insert=True)
                manifest['created'].append({'pk':t.pk,'after':snapshot(t)})
            for t,name,desc in demos:
                before=snapshot(t); t.name=name;t.description=desc;t.full_clean();t.save(update_fields=['name','description'])
                manifest['marked'].append({'pk':t.pk,'before':before,'after':snapshot(t)})
            # If manifest cannot be written the transaction is rolled back.
            with path.open('x',encoding='utf-8') as f: json.dump(manifest,f,ensure_ascii=False,indent=2)
        self.stdout.write(self.style.SUCCESS('IMPORT COMMITTED. Manifest: '+str(path)))
    def undo(self,path):
        m=json.loads(path.read_text(encoding='utf-8'))
        if m['database']!=DB: raise CommandError('Manifest database mismatch.')
        with transaction.atomic():
            created=[]; marked=[]
            for item in m['created']:
                t=Teacher.objects.select_for_update().get(pk=item['pk'])
                if t.college_id!=m['college_id'] or snapshot(t)!=item['after'] or not t.description.startswith(TAG) or related_exists(t):
                    raise CommandError('Imported record changed or has links; rollback stopped: '+str(t.pk))
                created.append(t)
            for item in m['marked']:
                t=Teacher.objects.select_for_update().get(pk=item['pk'])
                if t.college_id!=m['college_id'] or snapshot(t)!=item['after']: raise CommandError('Demo record changed; rollback stopped: '+str(t.pk))
                marked.append((t,item['before']))
            for t in created: t.delete()
            for t,before in marked:
                t.name=before['name'];t.description=before['description'];t.save(update_fields=['name','description'])
        self.stdout.write(self.style.SUCCESS('ROLLBACK COMMITTED.'))
