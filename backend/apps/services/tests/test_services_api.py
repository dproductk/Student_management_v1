from datetime import date
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

from apps.students.models import Student
from apps.documents.models import StudentDocument
from apps.services.models import ServiceRequestType, ServiceRequest

User = get_user_model()


class ServicesAPITestCase(APITestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(username="staff_svc", email="staff@clg.edu", password="password123")
        self.client.force_authenticate(user=self.staff_user)

        self.student = Student.objects.create(
            candidate_name="Arjun Verma",
            gender="MALE",
            date_of_birth=date(2005, 8, 18),
            enrollment_no="ENR_API_01",
            application_id="APP_API_01"
        )
        self.st = ServiceRequestType.objects.create(
            name="Official Transcript",
            code="TRANSCRIPT_API",
            description="University official transcript copies",
            requires_document=False,
            is_active=True
        )

    def test_full_services_api_lifecycle(self):
        """End-to-end API test: types -> submit -> process -> approve -> complete -> audits."""
        # 1. List Service Types
        types_resp = self.client.get('/api/v1/services/types/')
        self.assertEqual(types_resp.status_code, 200)
        types_items = types_resp.data.get('results', types_resp.data)
        self.assertEqual(len(types_items), 1)

        # 2. Submit Service Request
        submit_resp = self.client.post('/api/v1/services/requests/submit/', {
            'student': str(self.student.id),
            'service_type': str(self.st.id),
            'priority': 'NORMAL',
            'request_data': {'copies': 3, 'destination': 'Graduate School'}
        }, format='json')
        self.assertEqual(submit_resp.status_code, 201)
        req_id = submit_resp.data['id']
        self.assertEqual(submit_resp.data['status'], 'SUBMITTED')
        self.assertTrue(submit_resp.data['request_number'].startswith('SR-'))

        # 3. Process Request (Staff begins processing)
        proc_resp = self.client.post(f'/api/v1/services/requests/{req_id}/process/', {
            'notes': 'Printing official seal transcript'
        }, format='json')
        self.assertEqual(proc_resp.status_code, 200)
        self.assertEqual(proc_resp.data['status'], 'IN_PROGRESS')

        # 4. Approve Request
        appr_resp = self.client.post(f'/api/v1/services/requests/{req_id}/approve/', {
            'remarks': 'Approved by Academic Records section'
        }, format='json')
        self.assertEqual(appr_resp.status_code, 200)
        self.assertEqual(appr_resp.data['status'], 'APPROVED')

        # 5. Complete Request
        comp_resp = self.client.post(f'/api/v1/services/requests/{req_id}/complete/', {
            'resolution_notes': 'Transcripts dispatched via registered post'
        }, format='json')
        self.assertEqual(comp_resp.status_code, 200)
        self.assertEqual(comp_resp.data['status'], 'COMPLETED')

        # 6. Student Query / My Requests
        my_resp = self.client.get(f'/api/v1/services/requests/my-requests/?student_id={self.student.id}')
        self.assertEqual(my_resp.status_code, 200)
        my_items = my_resp.data.get('results', my_resp.data) if isinstance(my_resp.data, dict) else my_resp.data
        self.assertEqual(len(my_items), 1)
        self.assertEqual(my_items[0]['id'], req_id)

        # 7. Audits API
        audit_resp = self.client.get(f'/api/v1/services/audits/?request_id={req_id}')
        self.assertEqual(audit_resp.status_code, 200)
        audit_items = audit_resp.data.get('results', audit_resp.data)
        self.assertEqual(len(audit_items), 4) # SUBMITTED, IN_PROGRESS, APPROVED, COMPLETED
