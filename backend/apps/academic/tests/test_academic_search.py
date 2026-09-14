"""
Tests for Unified Academic Master Data Search API.
"""

from datetime import date
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from apps.identity.models import User
from apps.academic.models import Department, Program, AcademicYear, Batch, Scheme, Subject
from apps.academic.services.academic_service import AcademicService


class AcademicSearchTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='searcher', password='Pass123!Search', email='s@test.com')
        self.client.force_authenticate(user=self.user)

        self.dept = AcademicService.create_department(name="Information Science", code="ISE")
        self.prog = AcademicService.create_program(department_id=self.dept.id, name="B.Tech Information Science", code="IS")
        self.ay = AcademicService.create_academic_year(
            label="2026-2027",
            start_date=date(2026, 6, 1),
            end_date=date(2027, 5, 31)
        )
        self.batch = AcademicService.create_batch(department_id=self.dept.id, academic_year_id=self.ay.id, name="ISE-Batch-1")
        self.subj = AcademicService.create_subject(name="Web Technologies", code="IS301")
        self.scheme = AcademicService.create_scheme(
            program_id=self.prog.id,
            effective_from_year_id=self.ay.id,
            name="2026 Information Science Scheme",
            code="ISE-SCHEME-2026"
        )

    def test_search_academic_master_data(self):
        # Query matching "Information"
        res = self.client.get('/api/v1/academic/search/?q=Information')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.data
        self.assertTrue(any(d['code'] == 'ISE' for d in data['departments']))
        self.assertTrue(any(p['code'] == 'IS' for p in data['programs']))
        self.assertTrue(any(s['code'] == 'ISE-SCHEME-2026' for s in data['schemes']))

    def test_search_filter_by_department(self):
        res = self.client.get(f'/api/v1/academic/search/?department={self.dept.id}')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.data
        self.assertEqual(len(data['programs']), 1)
        self.assertEqual(data['programs'][0]['code'], 'IS')
        self.assertEqual(len(data['batches']), 1)
        self.assertEqual(data['batches'][0]['name'], 'ISE-Batch-1')
