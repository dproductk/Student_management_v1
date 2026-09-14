"""
Integration tests for Finance DRF API endpoints.
"""

from decimal import Decimal
from datetime import date
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from apps.identity.models import User
from apps.academic.models import AcademicYear, Department, Program, Semester, Batch
from apps.students.models import Student, StudentEnrollment
from apps.finance.models import (
    FeeHead,
    FeeStructure,
    StudentFeeAccount,
    FeeCharge,
    ChargeStatus,
    PaymentLedgerEntry,
)
from apps.finance.services.fee_service import FeeService


class FinanceAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='accountant_api',
            email='accountant_api@college.edu',
            password='TestPassword123!'
        )
        self.client.force_authenticate(user=self.user)

        self.ay = AcademicYear.objects.create(
            label='2024-25',
            start_date=date(2024, 7, 1),
            end_date=date(2025, 6, 30)
        )
        self.dept = Department.objects.create(name='Information Technology', code='IT')
        self.prog = Program.objects.create(name='B.Tech IT', code='BTIT', department=self.dept)

        self.head = FeeService.create_fee_head(name='Tuition', code='TUIT_API')
        self.struct = FeeService.create_fee_structure(
            name='IT Fee Structure 2024',
            academic_year=self.ay,
            items=[{'fee_head': self.head, 'amount': Decimal('60000.00')}],
            actor=self.user
        )

        self.student = Student.objects.create(
            candidate_name='Ananya Deshmukh',
            enrollment_no='ENR2024300',
            application_id='APP2024300',
            date_of_birth=date(2005, 4, 15),
            gender='FEMALE'
        )
        self.account = StudentFeeAccount.objects.create(student=self.student)
        self.charge = FeeCharge.objects.create(
            account=self.account,
            fee_structure=self.struct,
            academic_year=self.ay,
            total_amount=Decimal('60000.00'),
            status=ChargeStatus.UNPAID
        )
        self.account.update_totals()

    def test_fee_head_list_and_create(self):
        res = self.client.get('/api/v1/finance/heads/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        create_res = self.client.post('/api/v1/finance/heads/', {
            'name': 'Gymkhana Fee',
            'code': 'GYM_API',
            'description': 'Sports facilities'
        })
        self.assertEqual(create_res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(create_res.data['code'], 'GYM_API')

    def test_student_fee_accounts_search_and_filter(self):
        # Search by student name
        res = self.client.get(f'/api/v1/finance/accounts/?search=Ananya')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['results']), 1)
        self.assertEqual(res.data['results'][0]['candidate_name'], 'Ananya Deshmukh')
        self.assertEqual(Decimal(res.data['results'][0]['outstanding_balance']), Decimal('60000.00'))

        # Filter by UNPAID status
        res_unpaid = self.client.get('/api/v1/finance/accounts/?status=UNPAID')
        self.assertEqual(res_unpaid.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_unpaid.data['results']), 1)

    def test_record_payment_api(self):
        """Accountant logs payment confirmed on external university portal."""
        res = self.client.post('/api/v1/finance/record-payment/', {
            'charge_id': str(self.charge.id),
            'amount': '60000.00',
            'receipt_no': 'REC-API-001',
            'external_transaction_ref': 'UTR-UNIV-999888',
            'payment_mode': 'UNIVERSITY_PORTAL_QR',
            'reason': 'Student produced payment receipt from university portal'
        })

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['receipt_no'], 'REC-API-001')
        self.assertEqual(res.data['external_transaction_ref'], 'UTR-UNIV-999888')

        # Charge must now be PAID
        self.charge.refresh_from_db()
        self.assertEqual(self.charge.status, ChargeStatus.PAID)
        self.assertEqual(self.charge.remaining_balance, Decimal('0.00'))

    def test_reverse_payment_api(self):
        """Accountant issues reversal with mandatory reason."""
        entry = FeeService.record_payment(
            charge_id=str(self.charge.id),
            amount=Decimal('60000.00'),
            receipt_no='REC-TO-REV',
            actor=self.user
        )

        res = self.client.post('/api/v1/finance/reverse-payment/', {
            'payment_entry_id': str(entry.id),
            'reason': 'Accidental duplicate entry by student',
            'reversal_receipt_no': 'REV-API-001'
        })

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['entry_type'], 'REVERSAL')

        self.charge.refresh_from_db()
        self.assertEqual(self.charge.status, ChargeStatus.UNPAID)
