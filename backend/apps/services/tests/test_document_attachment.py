from datetime import date
from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.students.models import Student
from apps.documents.models import StudentDocument
from apps.services.models import ServiceRequestType, ServiceRequest
from apps.services.services.request_service import ServiceRequestService
from apps.services.domain.invariants import ServiceValidationError

User = get_user_model()


class DocumentAttachmentTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="student_doc", email="doc@test.com", password="pass")
        self.student = Student.objects.create(
            candidate_name="Ritesh Deshmukh",
            gender="MALE",
            date_of_birth=date(2005, 4, 1),
            enrollment_no="ENR_DOC_01",
            application_id="APP_DOC_01"
        )

        self.doc_income = StudentDocument.objects.create(
            student=self.student,
            document_type='INCOME_CERTIFICATE',
            storage_key='documents/income_cert_2024.pdf',
            original_filename='income_cert_2024.pdf',
            version=1,
            uploaded_by=self.user
        )
        self.doc_photo = StudentDocument.objects.create(
            student=self.student,
            document_type='PHOTO',
            storage_key='documents/photo.jpg',
            original_filename='photo.jpg',
            version=1,
            uploaded_by=self.user
        )

        self.st_requires_doc = ServiceRequestType.objects.create(
            name="EWS Fee Concession",
            code="EWS_CONCESSION",
            requires_document=True,
            allowed_document_types=['INCOME_CERTIFICATE'],
            is_active=True
        )

    def test_document_attachment_vertical_slice(self):
        """13.2.1: Document attachment requirements and canonical storage integration."""
        # 1. Missing document when mandatory raises error
        with self.assertRaises(ServiceValidationError):
            ServiceRequestService.submit_request(
                student=self.student,
                service_type=self.st_requires_doc,
                document=None,
                actor=self.user
            )

        # 2. Incompatible document type raises error
        with self.assertRaises(ServiceValidationError):
            ServiceRequestService.submit_request(
                student=self.student,
                service_type=self.st_requires_doc,
                document=self.doc_photo,
                actor=self.user
            )

        # 3. Valid document attachment succeeds
        req = ServiceRequestService.submit_request(
            student=self.student,
            service_type=self.st_requires_doc,
            document=self.doc_income,
            actor=self.user
        )
        self.assertEqual(req.attached_document, self.doc_income)
        self.assertEqual(req.attached_document.document_type, 'INCOME_CERTIFICATE')
