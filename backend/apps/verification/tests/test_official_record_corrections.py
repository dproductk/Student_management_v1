"""
Tests for Official-Record Corrections and Decision History Audit
(Tasks 6.2.1, 6.2.2).
"""

from datetime import date
from django.test import TestCase
from apps.identity.models import User
from apps.students.models import Student, StudentDataCorrection
from apps.verification.models import VerificationRequest, VerificationDecision
from apps.verification.services.verification_service import VerificationService
from apps.audit.models import AuditLog


class OfficialRecordCorrectionsTests(TestCase):
    def setUp(self):
        self.staff_reviewer = User.objects.create_user(
            username="academic_verifier",
            password="Password@123",
            email="academic_verifier@edvana.edu",
            is_staff=True
        )
        self.student = Student.objects.create(
            candidate_name="Aniket Kulkarni",
            gender="MALE",
            date_of_birth=date(2005, 8, 22),
            application_id="APP-ANIKET-01",
            enrollment_no="ENR-ANIKET-01",
            mother_name="Sunita",
            student_mobile="9876500000"
        )

    def test_student_correction_to_approved_record_update(self):
        """Task 6.2.1: Approved correction updates Student record and logs StudentDataCorrection."""
        # 1. Submit field correction for verification
        verif_req = VerificationService.submit_for_verification(
            student=self.student,
            entity_type="GOVERNMENT_CORRECTION",
            field_name="mother_name",
            submitted_value="Sunita Kulkarni",
            submitted_by=self.staff_reviewer
        )

        # Before approval: student record is NOT changed
        self.student.refresh_from_db()
        self.assertEqual(self.student.mother_name, "Sunita")

        # 2. Reviewer approves
        VerificationService.record_decision(
            verification_request=verif_req,
            decision="APPROVED",
            reviewer=self.staff_reviewer,
            notes="Verified with gazetted name change affidavit"
        )

        # After approval: authoritative student record is updated
        self.student.refresh_from_db()
        self.assertEqual(self.student.mother_name, "Sunita Kulkarni")

        # Additive StudentDataCorrection history record exists
        correction_log = StudentDataCorrection.objects.filter(
            student=self.student,
            field_name="mother_name"
        ).first()
        self.assertIsNotNone(correction_log)
        self.assertEqual(correction_log.original_value, "Sunita")
        self.assertEqual(correction_log.corrected_value, "Sunita Kulkarni")
        self.assertEqual(correction_log.approved_by, self.staff_reviewer)
        self.assertEqual(correction_log.source, "VERIFICATION_APPROVED")

    def test_decision_history_and_accountable_actor_audit(self):
        """Task 6.2.2: Immutable decision history preserves all review iterations and logs audit trail."""
        # 1. Submit
        verif_req = VerificationService.submit_for_verification(
            student=self.student,
            entity_type="PERSONAL_INFO",
            field_name="student_mobile",
            submitted_value="9999911111",
            submitted_by=self.staff_reviewer
        )

        # 2. Reviewer 1 requests correction (v1)
        VerificationService.record_decision(
            verification_request=verif_req,
            decision="NEEDS_CORRECTION",
            reviewer=self.staff_reviewer,
            rejection_reason="Mobile number requires OTP verification certificate"
        )

        # 3. Student re-submits (v2)
        VerificationService.resubmit_correction(
            verification_request=verif_req,
            new_submitted_value="9999922222",
            submitted_by=self.staff_reviewer
        )

        # 4. Reviewer approves (v2)
        VerificationService.record_decision(
            verification_request=verif_req,
            decision="APPROVED",
            reviewer=self.staff_reviewer,
            notes="Valid certificate attached"
        )

        # Check full history in VerificationDecision
        decisions = verif_req.decisions.all().order_by('version')
        self.assertEqual(decisions.count(), 2)

        v1_dec = decisions[0]
        self.assertEqual(v1_dec.version, 1)
        self.assertEqual(v1_dec.decision, "NEEDS_CORRECTION")
        self.assertEqual(v1_dec.reviewer, self.staff_reviewer)

        v2_dec = decisions[1]
        self.assertEqual(v2_dec.version, 2)
        self.assertEqual(v2_dec.decision, "APPROVED")
        self.assertEqual(v2_dec.reviewer, self.staff_reviewer)

        # Check audit trail in AuditLog
        self.assertTrue(AuditLog.objects.filter(
            target_id=verif_req.id,
            action="VERIFICATION_NEEDS_CORRECTION"
        ).exists())
        self.assertTrue(AuditLog.objects.filter(
            target_id=verif_req.id,
            action="VERIFICATION_APPROVED"
        ).exists())
