"""
Tests for Verification Record, State-Machine Foundation, Submission, Approval,
Rejection, and Needs-Correction (Tasks 6.1.1, 6.1.2, 6.1.3, 6.1.4).
"""

from datetime import date
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.identity.models import User
from apps.students.models import Student
from apps.documents.models import StudentDocument
from apps.documents.services.document_service import DocumentService
from apps.documents.services.storage_service import StorageService
from apps.verification.models import VerificationRequest, VerificationDecision
from apps.verification.services.verification_service import VerificationService
from common.exceptions import InvariantViolationError, StateTransitionError


class VerificationWorkflowTests(TestCase):
    def setUp(self):
        self.staff_reviewer = User.objects.create_user(
            username="verifier_agent",
            password="Password@123",
            email="verifier@edvana.edu",
            is_staff=True
        )
        self.student_user = User.objects.create_user(
            username="ENR-VERIF-01",
            password="Password@123",
            email="verif_student@edvana.edu"
        )
        self.student = Student.objects.create(
            user=self.student_user,
            candidate_name="Priyanka Deshpande",
            gender="FEMALE",
            date_of_birth=date(2005, 5, 12),
            application_id="APP-VERIF-01",
            enrollment_no="ENR-VERIF-01"
        )

        # Upload a marksheet document
        pdf_file = SimpleUploadedFile("ssc_doc.pdf", b"SSC Certificate Content", content_type="application/pdf")
        self.document = DocumentService.upload_student_document(
            student=self.student,
            document_type="SSC_MARKSHEET",
            file_obj=pdf_file,
            filename="ssc_doc.pdf",
            uploaded_by=self.student_user
        )

    def tearDown(self):
        docs = StudentDocument.objects.all()
        for d in docs:
            StorageService.delete_document(d.storage_key)

    def test_verification_request_foundation(self):
        """Task 6.1.1: VerificationRequest model foundation per Deliverable D.5."""
        req = VerificationRequest.objects.create(
            student=self.student,
            entity_type="DOCUMENT",
            entity_id=self.document.id,
            status="PENDING",
            current_version=1,
            submitted_by=self.student_user
        )
        self.assertIsNotNone(req.id)
        self.assertEqual(req.status, "PENDING")
        self.assertEqual(req.current_version, 1)

    def test_state_transition_guards(self):
        """Task 6.1.1: Guarded state transitions reject illegal state changes."""
        req = VerificationRequest.objects.create(
            student=self.student,
            entity_type="DOCUMENT",
            entity_id=self.document.id,
            status="APPROVED",
            current_version=1,
            submitted_by=self.student_user
        )

        # Direct transition from APPROVED to REJECTED is forbidden
        req.status = "REJECTED"
        with self.assertRaises(StateTransitionError):
            req.save()

    def test_verification_submission_pending_state(self):
        """Task 6.1.2: Submitting an item sets PENDING state."""
        verif_req = VerificationService.submit_for_verification(
            student=self.student,
            entity_type="DOCUMENT",
            entity_id=str(self.document.id),
            submitted_by=self.student_user
        )
        self.assertEqual(verif_req.status, "PENDING")
        self.assertEqual(verif_req.current_version, 1)
        self.assertEqual(verif_req.student, self.student)

    def test_verification_approval_decision(self):
        """Task 6.1.3: Approval transitions request to APPROVED and updates document status."""
        verif_req = VerificationService.submit_for_verification(
            student=self.student,
            entity_type="DOCUMENT",
            entity_id=str(self.document.id),
            submitted_by=self.student_user
        )

        req_obj, dec_obj = VerificationService.record_decision(
            verification_request=verif_req,
            decision="APPROVED",
            reviewer=self.staff_reviewer,
            notes="Document clear and verified against state board records"
        )

        self.assertEqual(req_obj.status, "APPROVED")
        self.assertEqual(dec_obj.decision, "APPROVED")
        self.assertEqual(dec_obj.reviewer, self.staff_reviewer)
        self.assertEqual(dec_obj.version, 1)

        # Document updated
        self.document.refresh_from_db()
        self.assertEqual(self.document.verification_status, "APPROVED")
        self.assertEqual(self.document.reviewed_by, self.staff_reviewer)

    def test_verification_rejection_and_needs_correction(self):
        """Task 6.1.4: Rejection and Needs-Correction require mandatory reason."""
        verif_req = VerificationService.submit_for_verification(
            student=self.student,
            entity_type="DOCUMENT",
            entity_id=str(self.document.id),
            submitted_by=self.student_user
        )

        # 1. Missing reason causes InvariantViolationError
        with self.assertRaises(InvariantViolationError):
            VerificationService.record_decision(
                verification_request=verif_req,
                decision="NEEDS_CORRECTION",
                reviewer=self.staff_reviewer,
                rejection_reason=""  # Missing reason
            )

        # 2. Valid needs-correction
        req_obj, dec_obj = VerificationService.record_decision(
            verification_request=verif_req,
            decision="NEEDS_CORRECTION",
            reviewer=self.staff_reviewer,
            rejection_reason="Marksheet scan is blurry; please upload high-res copy."
        )
        self.assertEqual(req_obj.status, "NEEDS_CORRECTION")
        self.assertEqual(dec_obj.rejection_reason, "Marksheet scan is blurry; please upload high-res copy.")

        # Document reflects status
        self.document.refresh_from_db()
        self.assertEqual(self.document.verification_status, "NEEDS_CORRECTION")

        # 3. Student re-submits correction
        re_req = VerificationService.resubmit_correction(
            verification_request=req_obj,
            new_entity_id=str(self.document.id),
            submitted_by=self.student_user
        )
        self.assertEqual(re_req.status, "PENDING")
        self.assertEqual(re_req.current_version, 2)
