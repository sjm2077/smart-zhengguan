"""Fixed model comparison; model and threshold chosen without holdout access."""
import numpy as np
from sklearn.base import clone
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.metrics import (roc_auc_score, average_precision_score, precision_score,
    recall_score, f1_score, brier_score_loss, confusion_matrix)
from xgboost import XGBClassifier
from .ai_prediction_data import FEATURES


def arrays(rows):
    return (np.array([r[2] for r in rows], dtype=float),
            np.array([r[3] for r in rows], dtype=int), np.array([r[0] for r in rows]))


def metrics(y,p,threshold):
    pred = (p>=threshold).astype(int)
    tn,fp,fn,tp = confusion_matrix(y,pred,labels=[0,1]).ravel()
    return dict(roc_auc=float(roc_auc_score(y,p)), average_precision=float(average_precision_score(y,p)),
        precision=float(precision_score(y,pred,zero_division=0)), recall=float(recall_score(y,pred,zero_division=0)),
        f1=float(f1_score(y,pred,zero_division=0)), brier=float(brier_score_loss(y,p)),
        threshold=float(threshold), tn=int(tn),fp=int(fp),fn=int(fn),tp=int(tp))


def threshold_from_oof(y,p):
    # fixed grid; ties favor higher threshold, not evaluation data
    return max(np.arange(.05,.951,.05), key=lambda t:(f1_score(y,p>=t,zero_division=0),t)).item()


def fit_compare(train_rows,test_rows,seed=42):
    X,y,g=arrays(train_rows); Xt,yt,gt=arrays(test_rows)
    for label,a,b,c in [('train',X,y,g),('holdout',Xt,yt,gt)]:
        if len(b)<100 or len(set(c))<20 or min(np.bincount(b,minlength=2))<10:
            raise ValueError(label+' requires >=100 examples, >=20 students and >=10 of each outcome')
    models = {
        'early_mean_baseline': (make_pipeline(StandardScaler(),LogisticRegression(max_iter=1000,random_state=seed)), [2]),
        'logistic_regression': (make_pipeline(StandardScaler(),LogisticRegression(max_iter=1000,random_state=seed)), list(range(len(FEATURES)))),
        'random_forest': (RandomForestClassifier(n_estimators=250,max_depth=6,min_samples_leaf=10,random_state=seed,n_jobs=2), list(range(len(FEATURES)))),
        'xgboost': (XGBClassifier(n_estimators=180,max_depth=3,learning_rate=.04,subsample=.85,colsample_bytree=.9,reg_lambda=3,min_child_weight=5,eval_metric='logloss',random_state=seed,n_jobs=2), list(range(len(FEATURES))))}
    folds=list(StratifiedGroupKFold(n_splits=4,shuffle=True,random_state=seed).split(X,y,g))
    oof={k:np.empty(len(y)) for k in models}; oof['prevalence_baseline']=np.empty(len(y))
    for tr,va in folds:
        if len(set(y[tr]))!=2 or len(set(y[va]))!=2 or set(g[tr]) & set(g[va]):
            raise ValueError('Grouped CV lacks both classes or group separation')
        oof['prevalence_baseline'][va]=y[tr].mean()
        for k,(model,cols) in models.items():
            fitted=clone(model).fit(X[tr][:,cols],y[tr]); oof[k][va]=fitted.predict_proba(X[va][:,cols])[:,1]
    thresholds={k:threshold_from_oof(y,p) for k,p in oof.items()}
    cv={k:metrics(y,p,thresholds[k]) for k,p in oof.items()}
    # Include the simple baseline as a selectable model; no forced complexity.
    selected=max(models,key=lambda k:(cv[k]['average_precision'],-cv[k]['brier']))
    fitted_models={}; test={}
    for k,(model,cols) in models.items():
        fitted=clone(model).fit(X[:,cols],y); fitted_models[k]=fitted
        test[k]=metrics(yt,fitted.predict_proba(Xt[:,cols])[:,1],thresholds[k])
    test['prevalence_baseline']=metrics(yt,np.full(len(yt),y.mean()),thresholds['prevalence_baseline'])
    improvement=(test[selected]['average_precision']>test['early_mean_baseline']['average_precision'] and
                 test[selected]['brier']<=test['early_mean_baseline']['brier'])
    report=dict(selected_by_train_cv=selected, cv=cv, holdout=test,
        student_overlap_count=len(set(g)&set(gt)), train_examples=len(y),holdout_examples=len(yt),
        train_positive=int(y.sum()),holdout_positive=int(yt.sum()),
        candidate_beats_early_mean_on_holdout=bool(improvement),
        demo_only=True, deployment_authorized=False)
    artifact=dict(model=fitted_models[selected],feature_names=list(FEATURES),columns=models[selected][1],
                  threshold=thresholds[selected],model_name=selected,demo_only=True, deployment_authorized=False)
    return report,artifact
