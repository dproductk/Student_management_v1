from decimal import Decimal
from datetime import date
from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.academic.models import Department, Program, AcademicYear, Semester
from apps.students.models import Student
from apps.results.models import EligibilityRule, EligibilityDecision
from apps.results.services.credit_eligibility_service import CreditEligibilityService
from apps.results.domain.invariants import EligibilityValidationError

User = get_user_model()


class EligibilityRuleDefinitionTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="admin_dean", email="dean@test.com", password="pass")
        self.dept = Department.objects.create(name="Information Technology", code="IT")
        self.program = Program.objects.create(name="B.Tech IT", code="BTIT", department=self.dept)
        self.ay = AcademicYear.objects.create(label="2024-2025", start_date=date(2024, 8, 1), end_date=date(2025, 5, 31))
        self.sem = Semester.objects.create(academic_year=self.ay, number=2, start_date=date(2025, 1, 1), end_date=date(2025, 5, 31))

    def test_configurable_eligibility_rule_creation(self):
        """12.2.1: Verify configurable eligibility rules can be defined with custom thresholds."""
        rule = CreditEligibilityService.create_or_version_rule(
            name="IT Promotion Rule 2024",
            code="RULE_IT_2024",
            min_credits=Decimal('18.0'),
            min_attendance=Decimal('75.00'),
            max_backlogs=2,
            detention_max_backlogs=4,
            detention_min_attendance=Decimal('50.00'),
            program_id=str(self.program.id),
            academic_year_id=str(self.ay.id),
            user=self.user
        )

        self.assertEqual(rule.name, "IT Promotion Rule 2024")
        self.assertEqual(rule.code, "RULE_IT_2024")
        self.assertEqual(rule.version, 1)
        self.assertTrue(rule.is_active)
        self.assertEqual(rule.min_credits_required, Decimal('18.0'))
        self.assertEqual(rule.min_attendance_percentage, Decimal('75.00'))
        self.assertEqual(rule.max_backlogs_allowed, 2)
        self.assertEqual(rule.detention_max_backlogs, 4)
        self.assertEqual(rule.detention_min_attendance, Decimal('50.00'))

    def test_eligibility_rule_invariant_validations(self):
        """12.2.1: Invariant validation prevents invalid thresholds."""
        # 1. Negative min credits
        with self.assertRaises(EligibilityValidationError):
            CreditEligibilityService.create_or_version_rule(
                name="Invalid Rule", code="INV1",
                min_credits=Decimal('-5.0'), min_attendance=Decimal('75.0'),
                max_backlogs=2, detention_max_backlogs=4, detention_min_attendance=Decimal('50.0'),
                user=self.user
            )

        # 2. Attendance > 100%
        with self.assertRaises(EligibilityValidationError):
            CreditEligibilityService.create_or_version_rule(
                name="Invalid Rule", code="INV2",
                min_credits=Decimal('18.0'), min_attendance=Decimal('105.0'),
                max_backlogs=2, detention_max_backlogs=4, detention_min_attendance=Decimal('50.0'),
                user=self.user
            )

        # 3. Detention backlogs less than max allowable normal backlogs
        with self.assertRaises(EligibilityValidationError):
            CreditEligibilityService.create_or_version_rule(
                name="Invalid Rule", code="INV3",
                min_credits=Decimal('18.0'), min_attendance=Decimal('75.0'),
                max_backlogs=3, detention_max_backlogs=2, detention_min_attendance=Decimal('50.0'),
                user=self.user
            )

        # 4. Detention attendance threshold higher than minimum attendance
        with self.assertRaises(EligibilityValidationError):
            CreditEligibilityService.create_or_version_rule(
                name="Invalid Rule", code="INV4",
                min_credits=Decimal('18.0'), min_attendance=Decimal('70.0'),
                max_backlogs=2, detention_max_backlogs=4, detention_min_attendance=Decimal('80.0'),
                user=self.user
            )

    def test_rule_versioning_preserves_historical_rules(self):
        """12.2.1: Modifying a rule used in prior decisions creates a new version."""
        # 1. Create Rule V1
        rule_v1 = CreditEligibilityService.create_or_version_rule(
            name="General Promotion Rule",
            code="RULE_GEN",
            min_credits=Decimal('18.0'),
            min_attendance=Decimal('75.00'),
            max_backlogs=2,
            detention_max_backlogs=4,
            detention_min_attendance=Decimal('50.00'),
            user=self.user
        )
        self.assertEqual(rule_v1.version, 1)

        # 2. Simulate an eligibility decision linking to Rule V1
        student = Student.objects.create(
            candidate_name="Rohan Gupta", gender="MALE", date_of_birth=date(2005, 5, 20),
            enrollment_no="ENR2024999", application_id="APP2024999"
        )
        decision = EligibilityDecision.objects.create(
            student=student,
            academic_year=self.ay,
            semester=self.sem,
            rule=rule_v1,
            rule_version=rule_v1.version,
            credits_earned=Decimal('20.0'),
            credits_attempted=Decimal('20.0'),
            backlogs_count=0,
            decision='ELIGIBLE',
            version=1,
            is_latest=True
        )

        # 3. Institutional policy changes: update RULE_GEN to require 22 credits
        rule_v2 = CreditEligibilityService.create_or_version_rule(
            name="General Promotion Rule Stricter",
            code="RULE_GEN",
            min_credits=Decimal('22.0'),
            min_attendance=Decimal('75.00'),
            max_backlogs=1,
            detention_max_backlogs=3,
            detention_min_attendance=Decimal('50.00'),
            user=self.user
        )

        # 4. Verify Rule V1 is preserved as inactive historical record
        rule_v1.refresh_from_db()
        self.assertFalse(rule_v1.is_active)
        self.assertEqual(rule_v1.version, 1)

        # Verify Rule V2 is active with version 2
        self.assertEqual(rule_v2.version, 2)
        self.assertTrue(rule_v2.is_active)
        self.assertEqual(rule_v2.min_credits_required, Decimal('22.0'))

        # Historical decision still references Rule V1 (v1)
        decision.refresh_from_db()
        self.assertEqual(decision.rule.id, rule_v1.id)
        self.assertEqual(decision.rule_version, 1)
