"""
Unit tests for Finance reporting interface (Task 14.1.3 & 14.2.4).
"""
from datetime import date
from decimal import Decimal
from django.test import TestCase
from apps.students.models import Student
from apps.academic.models import AcademicYear, Department, Program
from apps.finance.models import (
    FeeHead, FeeStructure, FeeStructureItem, StudentFeeAccount,
    FeeCharge, ChargeStatus
)
from apps.finance.services.finance_reporting import FinanceReportingQueryService


class FinanceReportingInterfaceTestCase(TestCase):
    def setUp(self):
        self.ay = AcademicYear.objects.create(label="2024-2025", start_date=date(2024, 7, 1), end_date=date(2025, 6, 30))
        self.dept = Department.objects.create(name="Civil Engineering", code="CIVIL")
        self.prog = Program.objects.create(name="B.Tech Civil", code="BT_CIVIL", department=self.dept)

        self.student1 = Student.objects.create(
            candidate_name="Fin Student 1",
            gender="MALE",
            date_of_birth=date(2005, 5, 5),
            enrollment_no="ENR_FIN_01",
            application_id="APP_FIN_01"
        )
        self.student2 = Student.objects.create(
            candidate_name="Fin Student 2",
            gender="FEMALE",
            date_of_birth=date(2005, 6, 6),
            enrollment_no="ENR_FIN_02",
            application_id="APP_FIN_02"
        )

        self.head_tuition = FeeHead.objects.create(name="Tuition Fee", code="TUITION")
        self.head_exam = FeeHead.objects.create(name="Exam Fee", code="EXAM")

        self.fs = FeeStructure.objects.create(
            name="General Civil BTech 2024",
            academic_year=self.ay,
            department=self.dept,
            program=self.prog,
            category="OPEN",
            total_amount=Decimal('55000.00'),
            is_locked=False
        )
        FeeStructureItem.objects.create(fee_structure=self.fs, fee_head=self.head_tuition, amount=Decimal('50000.00'))
        FeeStructureItem.objects.create(fee_structure=self.fs, fee_head=self.head_exam, amount=Decimal('5000.00'))
        self.fs.is_locked = True
        self.fs.save()

        self.acc1 = StudentFeeAccount.objects.create(student=self.student1)
        self.acc2 = StudentFeeAccount.objects.create(student=self.student2)

        # Student 1 paid full
        self.c1 = FeeCharge.objects.create(
            account=self.acc1,
            fee_structure=self.fs,
            academic_year=self.ay,
            total_amount=Decimal('55000.00'),
            paid_amount=Decimal('55000.00'),
            status=ChargeStatus.PAID
        )
        self.acc1.update_totals()

        # Student 2 unpaid
        self.c2 = FeeCharge.objects.create(
            account=self.acc2,
            fee_structure=self.fs,
            academic_year=self.ay,
            total_amount=Decimal('55000.00'),
            paid_amount=Decimal('0.00'),
            status=ChargeStatus.UNPAID
        )
        self.acc2.update_totals()

    def test_fee_status_summary(self):
        """14.2.4: Fee-status analytics."""
        summary = FinanceReportingQueryService.get_fee_status_summary()
        self.assertEqual(summary['total_billed'], 110000.0)
        self.assertEqual(summary['total_collected'], 55000.0)
        self.assertEqual(summary['total_outstanding'], 55000.0)
        self.assertEqual(summary['collection_percentage'], 50.0)
        self.assertEqual(summary['paid_charges_count'], 1)
        self.assertEqual(summary['unpaid_charges_count'], 1)

    def test_fee_heads_breakdown(self):
        """Fee heads breakdown aggregation."""
        heads = FinanceReportingQueryService.get_fee_heads_breakdown()
        self.assertEqual(len(heads), 2)
        head_map = {h['code']: h['amount'] for h in heads}
        self.assertEqual(head_map['TUITION'], 50000.0)
        self.assertEqual(head_map['EXAM'], 5000.0)

    def test_defaulters_reporting_records(self):
        """Defaulters query returns students with outstanding balance."""
        res = FinanceReportingQueryService.get_defaulters_reporting_records()
        self.assertEqual(res['total_count'], 1)
        self.assertEqual(res['records'][0]['candidate_name'], "Fin Student 2")
        self.assertEqual(res['records'][0]['outstanding_balance'], 55000.0)
