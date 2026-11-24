# -*- coding: utf-8 -*-
"""Update only description of the existing reviewed official directory records."""
import hashlib
import json
from datetime import datetime
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from teaching.models import College, Teacher, TeachingClass, UserProfile

DB = 'college_teaching'
COLLEGE = '政治学与公共管理学院'
TAG = '【官网公开师资档案】'

def read_rows(path):
    rows = json.loads(path.read_text(encoding='utf-8-sig'))
    if len(rows) != 93 or len({r['name'] for r in rows}) != 93:
        raise CommandError('Expected reviewed 93 unique directory records.')
    for r in rows:
        key = 'DIR-' + hashlib.sha256(r['name'].encode('utf-8')).hexdigest()[:16].upper()
        if r['teacher_no'] != key or not all(r[k].startswith(TAG+'\n') for k in ('before','after')):
            raise CommandError('Invalid reviewed row: '+r['name'])
        if r['status'] != 'profile_read' and r['before'] != r['after']:
            raise CommandError('Unavailable profile cannot be changed.')
        for k in ('before','after'):
            if '所属系所：'+r['department'] not in r[k].splitlines() or '名录类别：'+r['title'] not in r[k].splitlines():
                raise CommandError('Directory metadata mismatch: '+r['name'])
    return rows

def classify(t, r, college_id):
    if t is None or t.college_id != college_id or t.name != r['name'] or t.title != r['title'] or t.teacher_no != r['teacher_no']:
        return 'conflict'
    if t.description == r['after']: return 'unchanged'
    if t.description == r['before']: return 'update'
    return 'conflict'

def link_snapshot():
    return (list(TeachingClass.objects.order_by('pk').values_list('pk','teacher_id')), list(UserProfile.objects.order_by('pk').values_list('pk','teacher_id')))

class Command(BaseCommand):
    help = 'Preview or update existing official teacher descriptions only; no migration or new teacher.'
    def add_arguments(self,p):
        p.add_argument('--data',type=Path)
        p.add_argument('--execute',action='store_true')
        p.add_argument('--confirm-demo-db',default='')
        p.add_argument('--backup-dir',type=Path)
        p.add_argument('--rollback',type=Path)
    def handle(self,*args,**o):
        if connection.settings_dict['NAME'] != DB: raise CommandError('Unexpected database; expected '+DB)
        if o['execute'] and o['confirm_demo_db'] != DB: raise CommandError('Explicit database confirmation required.')
        if o['rollback']:
            if not o['execute']: raise CommandError('Rollback requires --execute.')
            return self.undo(o['rollback'])
        if not o['data']: raise CommandError('--data required.')
        rows=read_rows(o['data'])
        with transaction.atomic():
            college=College.objects.get(name=COLLEGE)
            qs=Teacher.objects.all()
            if o['execute']: qs=qs.select_for_update()
            existing=list(qs.order_by('pk')); lookup={t.teacher_no:t for t in existing}
            official=[t for t in existing if t.college_id==college.pk and t.teacher_no.startswith('DIR-') and t.description.startswith(TAG)]
            if {t.teacher_no for t in official}!={r['teacher_no'] for r in rows}: raise CommandError('Official directory identity set differs; no writes.')
            changes=[]; conflicts=[]; unchanged=0
            for r in rows:
                t=lookup.get(r['teacher_no']); state=classify(t,r,college.pk)
                if state=='conflict': conflicts.append(r['name'])
                elif state=='update': changes.append((t,r))
                else: unchanged+=1
            links=link_snapshot()
            self.stdout.write('Database: '+DB+' | '+college.name)
            self.stdout.write('Mode: '+('EXECUTE' if o['execute'] else 'PREVIEW (NO WRITES)'))
            self.stdout.write('Official: %d | All teachers: %d | Update: %d | Unchanged: %d | Conflicts: %d'%(len(official),len(existing),len(changes),unchanged,len(conflicts)))
            self.stdout.write('TeachingClass links: %d | Teacher account links: %d'%(sum(x[1] is not None for x in links[0]),sum(x[1] is not None for x in links[1])))
            if conflicts: raise CommandError('Existing descriptions or identity changed; no writes: '+', '.join(conflicts))
            if not o['execute']:
                self.stdout.write(self.style.SUCCESS('PREVIEW OK. NO WRITES.')); return
            if not changes: self.stdout.write('NO CHANGES. Already updated.'); return
            if not o['backup_dir']: raise CommandError('--backup-dir required.')
            o['backup_dir'].mkdir(parents=True,exist_ok=True)
            path=o['backup_dir']/('sdu_profile_update_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f')+'.json')
            manifest={'database':DB,'college_id':college.pk,'changes':[]}
            for t,r in changes:
                manifest['changes'].append({'pk':t.pk,'teacher_no':t.teacher_no,'name':t.name,'title':t.title,'before':t.description,'after':r['after']})
                # QuerySet.update changes the single intended field only, no save hooks.
                if Teacher.objects.filter(pk=t.pk,description=t.description).update(description=r['after'])!=1: raise CommandError('Concurrent change; transaction aborted.')
            if Teacher.objects.count()!=len(existing) or link_snapshot()!=links: raise CommandError('Relationship or count drift; transaction aborted.')
            with path.open('x',encoding='utf-8') as f: json.dump(manifest,f,ensure_ascii=False,indent=2)
        self.stdout.write(self.style.SUCCESS('PROFILE UPDATE COMMITTED. Backup: '+str(path)))
    def undo(self,path):
        m=json.loads(path.read_text(encoding='utf-8'))
        if m['database']!=DB: raise CommandError('Manifest database mismatch.')
        with transaction.atomic():
            college=College.objects.get(name=COLLEGE)
            if m['college_id']!=college.pk: raise CommandError('College mismatch.')
            links=link_snapshot()
            for item in m['changes']:
                t=Teacher.objects.select_for_update().get(pk=item['pk'])
                if t.college_id!=college.pk or any(getattr(t,k)!=item[k] for k in ('name','title','teacher_no')) or t.description!=item['after'] or not item['before'].startswith(TAG): raise CommandError('Record changed; rollback aborted.')
                Teacher.objects.filter(pk=t.pk).update(description=item['before'])
            if link_snapshot()!=links: raise CommandError('Relationship drift; rollback aborted.')
        self.stdout.write(self.style.SUCCESS('PROFILE ROLLBACK COMMITTED.'))
