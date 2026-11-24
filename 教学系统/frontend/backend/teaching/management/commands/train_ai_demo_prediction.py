"""Read-only database training command; outputs aggregate report and local demo artifact."""
import json
from pathlib import Path
from datetime import datetime
from uuid import uuid4
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.utils import timezone
from teaching.models import Semester, Grade
from teaching.ai_prediction_data import build_examples, HISTORY, FEATURES


class Command(BaseCommand):
    help = 'Train demo-only final score <60 classifiers using two closed synthetic semesters.'

    def add_arguments(self, parser):
        parser.add_argument('--output-dir', required=True)
        parser.add_argument('--confirm-demo-db', required=True)
        parser.add_argument('--seed', type=int, default=42)

    def handle(self, *args, **opts):
        if str(connection.settings_dict['NAME']) != opts['confirm_demo_db']:
            raise CommandError('Database name mismatch')
        current = list(Semester.objects.filter(is_current=True))
        if len(current)!=1 or not current[0].start_date:
            raise CommandError('Expected one dated current semester')
        terms=list(Semester.objects.filter(end_date__lt=current[0].start_date,start_date__isnull=False).order_by('-start_date','id')[:2])[::-1]
        if len(terms)!=2 or terms[0].end_date>=terms[1].start_date or terms[1].end_date>=timezone.localdate():
            raise CommandError('Need two completed, non-overlapping historical semesters')
        try:
            import sklearn, xgboost, joblib, numpy
            from teaching.ai_prediction_train import fit_compare
        except ImportError as exc:
            raise CommandError('Install prediction dependencies in the project environment: '+str(exc)) from exc
        samples=[]; coverage=[]
        for term in terms:
            qs=Grade.objects.filter(semester=term,is_published=True).order_by('id')
            if not qs.exists() or qs.exclude(remark__startswith=HISTORY).exists():
                raise CommandError('Selected semester is empty or contains non-demo grades: '+term.name)
            data=[]
            for r in qs.values('student_id','course_id','semester_id','score','exam_type','exam_date','remark','exam_id',
                    'exam__course_id','exam__semester_id','exam__exam_type','exam__total_score','exam__exam_date').iterator(chunk_size=1000):
                dt=r.pop('exam__exam_date')
                r['linked_day']=(timezone.localtime(dt).date() if timezone.is_aware(dt) else dt.date()) if dt else None
                data.append(r)
            try:
                rows,counts,cutoff=build_examples(data,term.start_date,term.end_date)
            except ValueError as exc:
                raise CommandError(str(exc)) from exc
            samples.append(rows)
            info=dict(semester_id=term.pk,semester=term.name,cutoff=cutoff.isoformat(),**counts)
            coverage.append(info)
            self.stdout.write(json.dumps(info,ensure_ascii=False))
        try:
            report,artifact=fit_compare(*samples,seed=opts['seed'])
        except ValueError as exc:
            raise CommandError(str(exc)) from exc
        report.update(protocol='first_closed_demo_term_group_cv_then_second_closed_demo_term_holdout',
            target='same student/course final assessment score <60; demo only',
            cutoff='65% of semester duration; early assessments only',
            caveats=['Synthetic assessment dates do not prove actual publication time.',
                'Holdout students may overlap training students; no direct identifiers are features.',
                'No cross-semester history features in v1: only two comparable synthetic terms.',
                'No real-world validity or deployment authorization. Current term excluded entirely.'],
            coverage=coverage,features=list(FEATURES),seed=opts['seed'],
            versions=dict(sklearn=sklearn.__version__,xgboost=xgboost.__version__,numpy=numpy.__version__,joblib=joblib.__version__))
        out=Path(opts['output_dir']).expanduser().resolve()/('demo_prediction_'+datetime.now().strftime('%Y%m%d_%H%M%S')+'_'+uuid4().hex[:8])
        out.mkdir(parents=True,exist_ok=False)
        artifact['protocol']=report['protocol']; artifact['versions']=report['versions']; artifact['train_semester_id']=terms[0].pk
        joblib.dump(artifact,out/'demo_model.joblib')
        (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
        self.stdout.write('\nHOLDOUT RESULTS (DEMO ONLY)')
        for name,m in report['holdout'].items():
            self.stdout.write('%-22s ROC-AUC %.4f  AP %.4f  F1 %.4f  Brier %.4f  Precision %.4f  Recall %.4f' % (name,m['roc_auc'],m['average_precision'],m['f1'],m['brier'],m['precision'],m['recall']))
        self.stdout.write('Selected by train CV: '+report['selected_by_train_cv'])
        self.stdout.write('Beats early-mean baseline on holdout (AP and Brier): '+str(report['candidate_beats_early_mean_on_holdout']))
        self.stdout.write('Report: '+str(out/'report.json'))
        self.stdout.write('DEMO TRAINING COMPLETE. NO DATABASE WRITES. NO DEPLOYMENT AUTHORIZATION.')
