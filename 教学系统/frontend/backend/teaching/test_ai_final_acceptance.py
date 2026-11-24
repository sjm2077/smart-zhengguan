"""Final API acceptance. Run only with Django's test runner (isolated test DB)."""
from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from .ai_models import AIWarningCase
from .models import College, Semester, Course, Teacher, TeachingClass, Exam


class AIFinalAcceptanceTests(TestCase):
    def setUp(self):
        today = timezone.localdate()
        self.term = Semester.objects.create(
            name='Final acceptance current', is_current=True,
            start_date=today-timedelta(days=60), end_date=today+timedelta(days=60),
        )
        self.old = Semester.objects.create(
            name='Final acceptance historical',
            start_date=today-timedelta(days=240), end_date=today-timedelta(days=120),
        )
        college = College.objects.create(name='Acceptance college')
        self.course = Course.objects.create(code='ACCEPT-101', name='Acceptance course',
                                            college=college, semester=self.term)
        self.teacher = Teacher.objects.create(teacher_no='ACCEPT-T01', name='Acceptance teacher', college=college)
        self.admin = get_user_model().objects.create_user(username='accept-admin', is_superuser=True, is_staff=True)
        self.client = self.authenticated(self.admin)
        self.start = timezone.make_aware(datetime.combine(today, datetime.min.time()).replace(hour=9))

    def authenticated(self, user):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Bearer '+str(AccessToken.for_user(user)))
        return client

    def teaching_class(self, name, term=None, schedule='', capacity=30, enrolled=20):
        return TeachingClass.objects.create(course=self.course, semester=term or self.term,
                                            teacher=self.teacher, class_name=name, schedule=schedule,
                                            capacity=capacity, enrolled_count=enrolled)

    def exam(self, name, start, location):
        return Exam.objects.create(name=name, course=self.course, semester=self.term,
                                   exam_date=start, duration=60, location=location)

    def get(self, path):
        response = self.client.get('/api/ai/'+path)
        self.assertEqual(response.status_code, 200, response.data)
        return response.data

    def sync(self):
        response = self.client.post('/api/ai/warnings/sync/', {}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        return response.data

    def update(self, pk, expected=200, **data):
        response = self.client.patch('/api/ai/warnings/{}/'.format(pk), data, format='json')
        self.assertEqual(response.status_code, expected, response.data)
        return response.data

    def test_complete_warning_lifecycle_through_authenticated_api(self):
        # The historical exception must not enter the current warning ledger.
        self.teaching_class('old missing schedule', term=self.old)
        self.assertEqual(self.get('overview/')['rule_total'], 0)
        missing = self.teaching_class('missing schedule')
        capacity = self.teaching_class('over capacity', schedule='周三第1-2节', enrolled=35)
        no_room = self.exam('no location', self.start, '')
        self.exam('exam A', self.start, 'A101')
        overlap = self.exam('exam B', self.start+timedelta(minutes=30), 'A101')
        overview = self.get('overview/')
        self.assertTrue(overview['rules_complete'])
        self.assertEqual(overview['rule_total'], 4)
        self.assertEqual({x['rule_code'] for x in overview['rule_preview']},
                         {'missing_schedule', 'over_capacity', 'missing_exam_location', 'room_time_overlap'})
        self.assertEqual(AIWarningCase.objects.count(), 0)
        print('ACCEPT 1: four rules detected; historical records isolated')
        first = self.sync()
        self.assertEqual((first['created'], first['detected']), (4, 4))
        again = self.sync()
        self.assertEqual((again['created'], again['detected']), (0, 4))
        ledger = self.get('warnings/?status=pending')
        self.assertEqual(ledger['count'], 4)
        self.assertTrue(all(x['source_active'] for x in ledger['results']))
        cases = {x['rule_code']:x for x in ledger['results']}
        pk = cases['missing_schedule']['id']
        print('ACCEPT 2: sync idempotent; pending ledger populated')
        self.update(pk, expected=400, status='resolved', resolution_note='')
        self.assertEqual(AIWarningCase.objects.get(pk=pk).status, 'pending')
        self.update(pk, status='in_progress', handler='Acceptance operator', resolution_note='Review started')
        self.assertEqual(self.get('warnings/?status=in_progress')['count'], 1)
        self.assertEqual(self.get('overview/')['case_counts']['in_progress'], 1)
        print('ACCEPT 3: manual handling, validation and status filtering')
        # Fix all source issues in isolated fixture records, then rescan.
        missing.schedule='周一第1-2节'; missing.save(update_fields=['schedule'])
        capacity.enrolled_count=30; capacity.save(update_fields=['enrolled_count'])
        no_room.location='B101'; no_room.save(update_fields=['location'])
        overlap.exam_date=self.start+timedelta(minutes=60); overlap.save(update_fields=['exam_date'])
        self.assertEqual(self.get('overview/')['rule_total'], 0)
        cleared = self.sync()
        self.assertEqual((cleared['cleared'], cleared['detected']), (4, 0))
        case = AIWarningCase.objects.get(pk=pk)
        self.assertFalse(case.source_active)
        self.assertIsNotNone(case.source_cleared_at)
        self.assertEqual((case.status, case.handler, case.resolution_note),
                         ('in_progress', 'Acceptance operator', 'Review started'))
        self.update(pk, status='resolved', resolution_note='Schedule verified')
        dismissed = cases['over_capacity']['id']
        self.update(dismissed, status='dismissed', handler='Acceptance operator', resolution_note='Enrollment verified')
        self.assertEqual(self.get('warnings/?status=resolved')['count'], 1)
        self.assertEqual(self.get('warnings/?status=dismissed')['count'], 1)
        print('ACCEPT 4: source cleared; resolution and dismissal persisted')
        missing.schedule=''; missing.save(update_fields=['schedule'])
        reopened = self.sync()
        self.assertEqual((reopened['created'], reopened['reappeared'], reopened['detected']), (0,1,1))
        case.refresh_from_db()
        self.assertTrue(case.source_active)
        self.assertIsNotNone(case.source_reappeared_at)
        self.assertEqual((case.status,case.handler,case.resolution_note),
                         ('resolved','Acceptance operator','Schedule verified'))
        self.assertEqual(AIWarningCase.objects.count(),4)
        print('ACCEPT 5: recurrence tracked without erasing manual decision')

    def test_unauthorized_users_cannot_read_or_mutate_warning_ledger(self):
        self.teaching_class('missing schedule')
        self.sync()
        case = AIWarningCase.objects.get()
        anon = APIClient()
        self.assertEqual(anon.get('/api/ai/warnings/').status_code,401)
        self.assertEqual(anon.post('/api/ai/warnings/sync/', {}, format='json').status_code,401)
        user=get_user_model().objects.create_user(username='accept-unassigned')
        client=self.authenticated(user)
        self.assertEqual(client.get('/api/ai/overview/').status_code,403)
        self.assertEqual(client.get('/api/ai/warnings/').status_code,403)
        self.assertEqual(client.post('/api/ai/warnings/sync/',{},format='json').status_code,403)
        self.assertEqual(client.patch('/api/ai/warnings/{}/'.format(case.pk), {'status':'in_progress'},format='json').status_code,403)
        self.assertEqual(client.post('/api/ai/demo-replay/',{},format='json').status_code,403)
        case.refresh_from_db()
        self.assertEqual(case.status,'pending')
        print('ACCEPT 6: JWT authorization protects warnings and replay')
