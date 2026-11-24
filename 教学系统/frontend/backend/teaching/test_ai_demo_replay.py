from django.test import SimpleTestCase
from .ai_demo_replay import aggregate, validate_report, PROTOCOL, replay_facts
from .ai_prediction_data import FEATURES

class DemoReplayTests(SimpleTestCase):
    def report(self):
        return dict(demo_only=True,deployment_authorized=False,protocol=PROTOCOL,
                    selected_by_train_cv='logistic_regression',features=list(FEATURES),
                    candidate_beats_early_mean_on_holdout=True,coverage=[{'semester_id':1},{'semester_id':2}],
                    cv={'logistic_regression':{'threshold':.25}},holdout={'logistic_regression':{'threshold':.25}})
    def test_report_contract(self):
        self.assertEqual(validate_report(self.report())[2],.25)
        for key,val in [('demo_only',False),('deployment_authorized',True),('features',[]),('protocol','unknown')]:
            r=self.report();r[key]=val
            with self.assertRaises(ValueError):validate_report(r)
    def test_threshold_and_confusion(self):
        rows=[(i,1,[],y) for i,y in enumerate([1,0,1,0,0])]
        r=aggregate(rows,[.25,.3,.1,.2,.05],{1:'课程'},.25)
        self.assertEqual(r['confusion'],dict(tp=1,fp=1,fn=1,tn=2))
        self.assertEqual(r['flagged'],2)
        self.assertEqual(r['courses'][0]['samples'],5)
        self.assertNotIn('student_id',str(r))
    def test_small_groups_suppressed(self):
        r=aggregate([(1,1,[],0),(2,1,[],1)],[.1,.9],{1:'课程'},.25)
        self.assertEqual(r['courses'],[]);self.assertEqual(r['suppressed_samples'],2)
    def test_bad_probabilities_rejected(self):
        for p in [float('nan'),-1,2]:
            with self.assertRaises(ValueError):aggregate([(1,1,[],1)],[p],{},.25)
    def test_threshold_drift(self):
        r=self.report();r['cv']['logistic_regression']['threshold']=.5
        with self.assertRaises(ValueError):validate_report(r)
