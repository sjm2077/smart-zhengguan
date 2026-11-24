"""Read-only retrospective replay, restricted to marked synthetic holdout grades.
Never scores current or real student records. Only aggregate output leaves this module.
The artifact path is configured by a trusted local operator, never by a request.
"""
import json
import os
from collections import defaultdict
from pathlib import Path
from math import isfinite
from .ai_prediction_data import FEATURES, HISTORY, build_examples

PROTOCOL = 'first_closed_demo_term_group_cv_then_second_closed_demo_term_holdout'
NOTE = '历史合成数据回放：仅供功能演示，不是当前学期预测，不代表真实学生风险或正式学业预警。'


def validate_report(report):
    if (report.get('demo_only') is not True or report.get('deployment_authorized') is not False
            or report.get('protocol') != PROTOCOL or report.get('selected_by_train_cv') != 'logistic_regression'
            or report.get('features') != list(FEATURES) or report.get('candidate_beats_early_mean_on_holdout') is not True):
        raise ValueError('Unsupported demo report')
    coverage = report['coverage']
    if len(coverage) != 2 or coverage[0]['semester_id'] == coverage[1]['semester_id']:
        raise ValueError('Expected two distinct historical terms')
    m = report['holdout']['logistic_regression']
    threshold = float(m['threshold'])
    if not 0 < threshold < 1 or threshold != report['cv']['logistic_regression']['threshold']:
        raise ValueError('Invalid frozen threshold')
    return coverage, m, threshold


def aggregate(rows, probabilities, names, threshold):
    if len(rows) != len(probabilities) or not rows:
        raise ValueError('Missing replay samples')
    counts = dict(tn=0, fp=0, fn=0, tp=0)
    groups = defaultdict(list)
    for row, p in zip(rows, probabilities):
        p = float(p)
        if not isfinite(p) or not 0 <= p <= 1:
            raise ValueError('Invalid probability')
        sid, cid, _, label = row
        if label not in (0, 1):
            raise ValueError('Invalid label')
        flagged = p >= threshold
        counts[{(False,0):'tn',(True,0):'fp',(False,1):'fn',(True,1):'tp'}[(flagged,label)]] += 1
        groups[cid].append((sid,p,flagged))
    courses = []
    for cid, vals in groups.items():
        if len({x[0] for x in vals}) < 5:
            continue
        courses.append(dict(course=names.get(cid,'未命名课程'), samples=len(vals), flagged=sum(x[2] for x in vals),
                            mean_probability=round(sum(x[1] for x in vals)/len(vals),6)))
    courses.sort(key=lambda r:(-r['mean_probability'],r['course']))
    return dict(samples=len(rows), flagged=counts['tp']+counts['fp'], unflagged=counts['tn']+counts['fn'],
                actual_low=counts['tp']+counts['fn'], confusion=counts, courses=courses,
                suppressed_samples=len(rows)-sum(c['samples'] for c in courses))


def replay():
    import joblib
    import numpy as np
    import sklearn
    from django.utils import timezone
    from .models import Semester, Grade, Course
    configured = os.environ.get('AI_DEMO_REPLAY_DIR','').strip()
    if not configured:
        raise ValueError('Replay not configured')
    folder = Path(configured).resolve(strict=True)
    report = json.loads((folder/'report.json').read_text(encoding='utf-8'))
    coverage, m, threshold = validate_report(report)
    for name, value in [('sklearn',sklearn.__version__),('numpy',np.__version__),('joblib',joblib.__version__)]:
        if report['versions'][name] != value:
            raise ValueError('Artifact runtime version mismatch')
    train, term = (Semester.objects.get(pk=c['semester_id']) for c in coverage)
    current = Semester.objects.get(is_current=True)
    if not (train.start_date and train.end_date and term.start_date and term.end_date and current.start_date
            and train.start_date < train.end_date < term.start_date < term.end_date < current.start_date
            and term.end_date < timezone.localdate() and not train.is_current and not term.is_current):
        raise ValueError('Replay terms are not closed historical terms')
    qs = Grade.objects.filter(semester=term,is_published=True).order_by('id')
    if qs.exclude(remark__startswith=HISTORY).exists() or not qs.exists():
        raise ValueError('Only synthetic grades may be replayed')
    if qs.count() > 100000:
        raise ValueError('Replay limit exceeded')
    data=[]
    for r in qs.values('student_id','course_id','semester_id','score','exam_type','exam_date','remark','exam_id',
            'exam__course_id','exam__semester_id','exam__exam_type','exam__total_score','exam__exam_date').iterator(chunk_size=1000):
        dt=r.pop('exam__exam_date')
        r['linked_day']=(timezone.localtime(dt).date() if timezone.is_aware(dt) else dt.date()) if dt else None
        data.append(r)
    rows, counts, cutoff = build_examples(data,term.start_date,term.end_date)
    if (cutoff.isoformat()!=coverage[1]['cutoff'] or any(counts.get(k)!=coverage[1].get(k) for k in ('input_records','examples','positive','students'))
            or len(rows)!=report['holdout_examples'] or counts['positive']!=report['holdout_positive']):
        raise ValueError('Historical coverage differs from frozen report')
    # joblib can execute code on load. Only the operator's own previously trained artifact is allowed.
    artifact=joblib.load(folder/'demo_model.joblib')
    if (artifact.get('demo_only') is not True or artifact.get('deployment_authorized') is not False
            or artifact.get('model_name')!='logistic_regression' or artifact.get('feature_names')!=list(FEATURES)
            or artifact.get('columns')!=list(range(len(FEATURES))) or artifact.get('threshold')!=threshold
            or artifact.get('protocol')!=PROTOCOL or artifact.get('train_semester_id')!=train.pk
            or artifact.get('versions')!=report['versions']):
        raise ValueError('Artifact contract mismatch')
    model=artifact['model']
    if list(model.classes_)!=[0,1]:
        raise ValueError('Unexpected classes')
    p=model.predict_proba(np.asarray([r[2] for r in rows],dtype=float))[:,1]
    names=dict(Course.objects.filter(pk__in={r[1] for r in rows}).values_list('pk','name'))
    result=aggregate(rows,p,names,threshold)
    # Recompute metrics: never present stale report values as a fresh replay result.
    from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss, f1_score, precision_score, recall_score
    y=np.asarray([r[3] for r in rows]); pred=p>=threshold
    actual=dict(roc_auc=roc_auc_score(y,p),average_precision=average_precision_score(y,p),brier=brier_score_loss(y,p),
                f1=f1_score(y,pred,zero_division=0),precision=precision_score(y,pred,zero_division=0),recall=recall_score(y,pred,zero_division=0))
    if result['confusion']!={k:m[k] for k in ('tn','fp','fn','tp')} or any(abs(v-m[k])>1e-7 for k,v in actual.items()):
        raise ValueError('Replay metrics differ from frozen report')
    result.update(metrics={k:round(float(v),6) for k,v in actual.items()}, threshold=threshold, model='逻辑回归',
                  semester=term.name, cutoff=cutoff.isoformat(), train_semester=train.name, note=NOTE,
                  demo_only=True, deployment_authorized=False)
    return result


def replay_facts(result):
    """Chinese aggregate fields only; no individual output."""
    return {'说明':NOTE,'回放学期':result['semester'],'模拟预测截止日':result['cutoff'],
            '模型':result['model'],'演示关注阈值':result['threshold'],'回放样本数':result['samples'],
            '达到关注阈值样本数':result['flagged'],'未达到阈值样本数':result['unflagged'],
            '实际低分样本数':result['actual_low'],
            '正确关注':result['confusion']['tp'],'误报':result['confusion']['fp'],'漏报':result['confusion']['fn'],
            '正确未关注':result['confusion']['tn'],
            '演示评估指标':{'ROC-AUC':result['metrics']['roc_auc'],'AP':result['metrics']['average_precision'],
                       'F1':result['metrics']['f1'],'Brier误差':result['metrics']['brier']},
            '课程聚合示例': [{'课程':c['course'],'样本数':c['samples'],'关注样本数':c['flagged'],
                         '平均模型概率':c['mean_probability']} for c in result['courses'][:15]]}
