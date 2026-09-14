import json
from decimal import Decimal
from datetime import date
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

from apps.academic.models import Department, Program, AcademicYear, Semester, Scheme, Subject, SchemeSubject, Batch
from apps.students.models import Student, StudentEnrollment
from apps.results.models import ResultImportBatch, StudentResult
from apps.results.services.result_service import ResultService

User = get_user_model()


class ResultsAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="controller", email="ctrl@test.com", password="password123")
        self.client.force_authenticate(user=self.user)

        self.dept = Department.objects.create(name="Electrical Engineering", code="EE")
        self.program = Program.objects.create(name="B.Tech Electrical", code="BTEE", department=self.dept)
        self.ay = AcademicYear.objects.create(label="2024-2025", start_date=date(2024, 8, 1), end_date=date(2025, 5, 31))
        self.sem = Semester.objects.create(academic_year=self.ay, number=6, start_date=date(2025, 1, 1), end_date=date(2025, 5, 31))
        self.batch = Batch.objects.create(department=self.dept, academic_year=self.ay, name="2024-EE")
        self.scheme = Scheme.objects.create(program=self.program, name="EE Scheme 2024", code="SCH_EE", effective_from_year=self.ay)

        self.subj = Subject.objects.create(name="Power Systems", code="EE601")
        self.ss = SchemeSubject.objects.create(
            scheme=self.scheme,
            subject=self.subj,
            semester_number=self.sem.number,
            max_internal_marks=40,
            max_marks=100
        )

        self.student = Student.objects.create(
            candidate_name="Vikram Malhotra",
            gender="MALE",
            date_of_birth=date(2005, 5, 10),
            enrollment_no="ENR2024601",
            application_id="APP2024601",
            email="vikram@student.edu"
        )
        StudentEnrollment.objects.create(
            student=self.student,
            academic_year=self.ay,
            semester=self.sem,
            department=self.dept,
            program=self.program,
            batch=self.batch,
            scheme=self.scheme,
            status='ACTIVE'
        )

    def test_full_api_workflow(self):
        """End-to-end API test: upload -> validate -> approve -> publish -> correction -> review."""
        # 1. Upload batch
        csv_content = f"student_identifier,subject_code,internal_marks,external_marks\n{self.student.enrollment_no},EE601,35,50\n"
        upload_resp = self.client.post('/api/v1/results/batches/upload/', {
            'academic_year': str(self.ay.id),
            'semester': str(self.sem.id),
            'department': str(self.dept.id),
            'program': str(self.program.id),
            'file_name': 'ee_sem6.csv',
            'csv_content': csv_content
        }, format='json')
        self.assertEqual(upload_resp.status_code, 201)
        batch_id = upload_resp.data['id']
        self.assertEqual(upload_resp.data['status'], 'PROCESSING')

        # 2. Check rows
        rows_resp = self.client.get(f'/api/v1/results/batches/{batch_id}/rows/')
        self.assertEqual(rows_resp.status_code, 200)
        self.assertEqual(len(rows_resp.data), 1)

        # 3. Validate batch
        val_resp = self.client.post(f'/api/v1/results/batches/{batch_id}/validate/')
        self.assertEqual(val_resp.status_code, 200)
        self.assertEqual(val_resp.data['batch']['status'], 'VALIDATED')

        # 4. Approve batch
        app_resp = self.client.post(f'/api/v1/results/batches/{batch_id}/approve/')
        self.assertEqual(app_resp.status_code, 200)
        self.assertEqual(app_resp.data['status'], 'APPROVED')

        # 5. Publish batch
        pub_resp = self.client.post(f'/api/v1/results/batches/{batch_id}/publish/')
        self.assertEqual(pub_resp.status_code, 200)
        self.assertEqual(pub_resp.data['status'], 'PUBLISHED')

        # 6. Student results list
        results_resp = self.client.get(f'/api/v1/results/records/?enrollment_no={self.student.enrollment_no}')
        self.assertEqual(results_resp.status_code, 200)
        items = results_resp.data.get('results', results_resp.data)
        self.assertEqual(len(items), 1)
        result_id = items[0]['id']
        self.assertEqual(items[0]['status'], 'PUBLISHED')
        self.assertEqual(items[0]['version'], 1)

        # 7. Student self-portal endpoint
        portal_resp = self.client.get(f'/api/v1/results/student-portal/?student_id={self.student.id}')
        self.assertEqual(portal_resp.status_code, 200)
        portal_items = portal_resp.data.get('results', portal_resp.data) if isinstance(portal_resp.data, dict) else portal_resp.data
        self.assertEqual(len(portal_items), 1)

        # 8. Request correction
        corr_resp = self.client.post('/api/v1/results/corrections/', {
            'target_result': result_id,
            'reason': 'Recalculation of external component',
            'proposed_changes': {'subjects': {'EE601': {'external_marks': 55}}}
        }, format='json')
        self.assertEqual(corr_resp.status_code, 201)
        corr_id = corr_resp.data['id']

        # 9. Review and approve correction
        rev_resp = self.client.post(f'/api/v1/results/corrections/{corr_id}/review/', {
            'approved': True,
            'review_remarks': 'Approved after verification with university controller'
        }, format='json')
        self.assertEqual(rev_resp.status_code, 200)
        self.assertEqual(rev_resp.data['status'], 'APPROVED')

        # 10. Verify supersession via API
        records_after = self.client.get(f'/api/v1/results/records/?enrollment_no={self.student.enrollment_no}&latest_only=true')
        self.assertEqual(records_after.status_code, 200)
        after_items = records_after.data.get('results', records_after.data)
        self.assertEqual(len(after_items), 1)
        self.assertEqual(after_items[0]['version'], 2)
        self.assertEqual(Decimal(str(after_items[0]['total_marks_obtained'])), Decimal('90.00'))

        # 11. Credits API endpoint
        cred_resp = self.client.get(f'/api/v1/results/credits/?student={self.student.id}')
        self.assertEqual(cred_resp.status_code, 200)
        cred_items = cred_resp.data.get('results', cred_resp.data)
        self.assertTrue(len(cred_items) >= 1)

        # 12. Create Eligibility Rule API endpoint
        rule_resp = self.client.post('/api/v1/results/eligibility-rules/', {
            'name': 'B.Tech Electrical Rule',
            'code': 'RULE_BTEE_API',
            'program': str(self.program.id),
            'academic_year': str(self.ay.id),
            'min_credits_required': '3.0',
            'min_attendance_percentage': '75.00',
            'max_backlogs_allowed': 1,
            'detention_max_backlogs': 2,
            'detention_min_attendance': '50.00'
        }, format='json')
        self.assertEqual(rule_resp.status_code, 201)
        rule_id = rule_resp.data['id']

        # 13. Evaluate Eligibility API endpoint
        eval_resp = self.client.post('/api/v1/results/eligibility-decisions/evaluate/', {
            'student': str(self.student.id),
            'academic_year': str(self.ay.id),
            'semester': str(self.sem.id),
            'rule': rule_id,
            'attendance_percentage': '85.00'
        }, format='json')
        self.assertEqual(eval_resp.status_code, 201)
        self.assertEqual(eval_resp.data['decision'], 'ELIGIBLE')

        # 14. Next-Year Eligibility List Generation API endpoint
        gen_resp = self.client.post('/api/v1/results/next-year-eligibility/generate/', {
            'academic_year': str(self.ay.id),
            'semester': str(self.sem.id),
            'program': str(self.program.id),
            'target_semester_number': 7
        }, format='json')
        self.assertEqual(gen_resp.status_code, 201)
        self.assertEqual(gen_resp.data['total_students'], 1)
        self.assertEqual(gen_resp.data['eligible_count'], 1)
