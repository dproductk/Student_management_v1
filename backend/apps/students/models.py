"""
Student Management domain models.
Implements Deliverable D.3 of DATABASE_ARCHITECTURE.md:
Students, Admissions, Addresses, Categories, Bank Accounts,
Educational Histories, Scholarships, Enrollments, and Additive Corrections.
"""

from django.db import models
from django.utils import timezone
from common.models import TimeStampedUUIDModel
from common.exceptions import InvariantViolationError
from apps.students.domain.invariants import (
    validate_student_status,
    validate_gender,
    validate_enrollment_transition,
    validate_correction_request,
)


class Student(TimeStampedUUIDModel):
    """Authoritative student identity and core record."""
    user = models.OneToOneField(
        'identity.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='student_profile',
        db_column='user_id'
    )
    application_id = models.CharField(max_length=50, null=True, blank=True, unique=True)
    enrollment_no = models.CharField(max_length=50, null=True, blank=True, unique=True)
    board_enrollment_no = models.CharField(max_length=50, null=True, blank=True, unique=True)
    candidate_name = models.CharField(max_length=200)
    father_name = models.CharField(max_length=200, null=True, blank=True)
    mother_name = models.CharField(max_length=200, null=True, blank=True)
    gender = models.CharField(max_length=10)
    date_of_birth = models.DateField()
    student_mobile = models.CharField(max_length=15, null=True, blank=True)
    parent_mobile = models.CharField(max_length=15, null=True, blank=True)
    email = models.EmailField(max_length=254, null=True, blank=True)
    religion = models.CharField(max_length=50, null=True, blank=True)
    mother_tongue = models.CharField(max_length=50, null=True, blank=True)
    candidature_type = models.CharField(max_length=30, null=True, blank=True)
    
    # Sensitive identity boundary (ADR-015)
    aadhaar_encrypted = models.BinaryField(null=True, blank=True)
    aadhaar_masked = models.CharField(max_length=20, null=True, blank=True)

    status = models.CharField(max_length=30, default='ACTIVE')
    data_source = models.CharField(max_length=20, default='GOVERNMENT')

    created_by = models.ForeignKey(
        'identity.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_students',
        db_column='created_by'
    )
    updated_by = models.ForeignKey(
        'identity.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_students',
        db_column='updated_by'
    )

    class Meta:
        db_table = 'students'
        ordering = ['candidate_name']
        verbose_name = 'Student'
        verbose_name_plural = 'Students'
        indexes = [
            models.Index(fields=['status'], name='idx_students_status'),
            models.Index(fields=['enrollment_no'], name='idx_students_enrollment'),
            models.Index(fields=['application_id'], name='idx_students_application'),
        ]

    def clean(self):
        validate_student_status(self.status)
        validate_gender(self.gender)

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.enrollment_no or self.application_id or 'NEW'} - {self.candidate_name}"


class StudentAdmission(TimeStampedUUIDModel):
    """Institutional program admission record."""
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='admissions',
        db_column='student_id'
    )
    program = models.ForeignKey(
        'academic.Program',
        on_delete=models.PROTECT,
        related_name='student_admissions',
        db_column='program_id'
    )
    admission_date = models.DateField()
    admission_type = models.CharField(max_length=30, null=True, blank=True)
    admission_category = models.CharField(max_length=30, null=True, blank=True)
    seat_type = models.CharField(max_length=30, null=True, blank=True)
    allotted_seat_type = models.CharField(max_length=30, null=True, blank=True)
    reservation_type = models.CharField(max_length=30, null=True, blank=True)
    choice_code = models.CharField(max_length=20, null=True, blank=True)
    cet_percentile = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    jee_percentile = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    eligibility_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    dsa_dse_flag = models.CharField(max_length=10, null=True, blank=True)
    starting_semester = models.PositiveSmallIntegerField(default=1)
    data_source = models.CharField(max_length=20, default='GOVERNMENT')

    class Meta:
        db_table = 'student_admissions'
        ordering = ['-admission_date']
        verbose_name = 'Student Admission'
        verbose_name_plural = 'Student Admissions'

    def __str__(self):
        return f"{self.student.candidate_name} -> {self.program.code} ({self.admission_date})"


class StudentAddress(TimeStampedUUIDModel):
    """Residential and communication address (1:1 with student)."""
    student = models.OneToOneField(
        Student,
        on_delete=models.CASCADE,
        related_name='address',
        db_column='student_id'
    )
    address_line = models.TextField(null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    district = models.CharField(max_length=100, null=True, blank=True)
    taluka = models.CharField(max_length=100, null=True, blank=True)
    village = models.CharField(max_length=100, null=True, blank=True)
    pincode = models.CharField(max_length=10, null=True, blank=True)

    class Meta:
        db_table = 'student_addresses'
        verbose_name = 'Student Address'
        verbose_name_plural = 'Student Addresses'

    def __str__(self):
        return f"{self.district or ''}, {self.state or ''} - {self.pincode or ''}"


class StudentCategory(TimeStampedUUIDModel):
    """Social category, caste, minority, and disability classification (1:1 with student)."""
    student = models.OneToOneField(
        Student,
        on_delete=models.CASCADE,
        related_name='category_info',
        db_column='student_id'
    )
    category = models.CharField(max_length=30)
    caste = models.CharField(max_length=100, null=True, blank=True)
    sub_caste = models.CharField(max_length=100, null=True, blank=True)
    is_minority = models.BooleanField(default=False)
    is_disabled = models.BooleanField(default=False)
    disability_type = models.CharField(max_length=100, null=True, blank=True)
    data_source = models.CharField(max_length=20, default='GOVERNMENT')

    class Meta:
        db_table = 'student_categories'
        verbose_name = 'Student Category'
        verbose_name_plural = 'Student Categories'

    def __str__(self):
        return f"{self.category} ({self.caste or 'General'})"


class StudentBankAccount(TimeStampedUUIDModel):
    """Sensitive banking identity boundary (ADR-015, 1:1 with student)."""
    student = models.OneToOneField(
        Student,
        on_delete=models.CASCADE,
        related_name='bank_account',
        db_column='student_id'
    )
    bank_name = models.CharField(max_length=200, null=True, blank=True)
    branch_name = models.CharField(max_length=200, null=True, blank=True)
    account_number_encrypted = models.BinaryField(null=True, blank=True)
    account_number_masked = models.CharField(max_length=20, null=True, blank=True)
    ifsc_code = models.CharField(max_length=20, null=True, blank=True)
    account_holder_name = models.CharField(max_length=200, null=True, blank=True)

    class Meta:
        db_table = 'student_bank_accounts'
        verbose_name = 'Student Bank Account'
        verbose_name_plural = 'Student Bank Accounts'

    def __str__(self):
        return f"{self.bank_name or 'Bank'}: {self.account_number_masked or 'No Account'}"


class StudentEducationalHistory(TimeStampedUUIDModel):
    """Prior educational background (SSC, HSC, etc.)."""
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='educational_histories',
        db_column='student_id'
    )
    exam_type = models.CharField(max_length=10)
    passing_year = models.PositiveSmallIntegerField(null=True, blank=True)
    board_name = models.CharField(max_length=200, null=True, blank=True)
    school_name = models.CharField(max_length=200, null=True, blank=True)
    college_name = models.CharField(max_length=200, null=True, blank=True)
    total_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    data_source = models.CharField(max_length=20, default='GOVERNMENT')

    class Meta:
        db_table = 'student_educational_histories'
        unique_together = (('student', 'exam_type'),)
        verbose_name = 'Student Educational History'
        verbose_name_plural = 'Student Educational Histories'

    def __str__(self):
        return f"{self.student.candidate_name} - {self.exam_type} ({self.total_percentage}%)"


class StudentScholarship(TimeStampedUUIDModel):
    """Financial aid and scholarship application tracking."""
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='scholarships',
        db_column='student_id'
    )
    scholarship_type = models.CharField(max_length=100, null=True, blank=True)
    annual_family_income = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    income_slab = models.CharField(max_length=50, null=True, blank=True)
    status = models.CharField(max_length=30, default='PENDING')
    academic_year = models.ForeignKey(
        'academic.AcademicYear',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='scholarships',
        db_column='academic_year_id'
    )
    approved_by = models.ForeignKey(
        'identity.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_scholarships',
        db_column='approved_by'
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'student_scholarships'
        verbose_name = 'Student Scholarship'
        verbose_name_plural = 'Student Scholarships'

    def __str__(self):
        return f"{self.student.candidate_name} - {self.scholarship_type} ({self.status})"


class StudentEnrollment(TimeStampedUUIDModel):
    """Authoritative semester enrollment state (ADR-005)."""
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='enrollments',
        db_column='student_id'
    )
    academic_year = models.ForeignKey(
        'academic.AcademicYear',
        on_delete=models.PROTECT,
        related_name='student_enrollments',
        db_column='academic_year_id'
    )
    semester = models.ForeignKey(
        'academic.Semester',
        on_delete=models.PROTECT,
        related_name='student_enrollments',
        db_column='semester_id'
    )
    department = models.ForeignKey(
        'academic.Department',
        on_delete=models.PROTECT,
        related_name='student_enrollments',
        db_column='department_id'
    )
    program = models.ForeignKey(
        'academic.Program',
        on_delete=models.PROTECT,
        related_name='student_enrollments',
        db_column='program_id'
    )
    batch = models.ForeignKey(
        'academic.Batch',
        on_delete=models.PROTECT,
        related_name='student_enrollments',
        db_column='batch_id'
    )
    scheme = models.ForeignKey(
        'academic.Scheme',
        on_delete=models.PROTECT,
        related_name='student_enrollments',
        db_column='scheme_id'
    )
    division = models.CharField(max_length=20, default='A', help_text='Class division within batch (A, B, C...)')
    status = models.CharField(max_length=30, default='ACTIVE')
    created_by = models.ForeignKey(
        'identity.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_enrollments',
        db_column='created_by'
    )

    class Meta:
        db_table = 'student_enrollments'
        unique_together = (('student', 'academic_year', 'semester'),)
        verbose_name = 'Student Enrollment'
        verbose_name_plural = 'Student Enrollments'
        indexes = [
            models.Index(fields=['student'], name='idx_enrollments_student'),
            models.Index(fields=['batch'], name='idx_enrollments_batch'),
            models.Index(fields=['scheme'], name='idx_enrollments_scheme'),
        ]

    def save(self, *args, **kwargs):
        if self.pk:
            prev = StudentEnrollment.objects.filter(pk=self.pk).first()
            if prev and prev.status != self.status:
                validate_enrollment_transition(prev.status, self.status)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.candidate_name} | {self.batch.name} | Sem {self.semester.number} ({self.status})"


class StudentDataCorrection(TimeStampedUUIDModel):
    """Additive correction log for government-sourced student data (ADR-007, ADR-011)."""
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='corrections',
        db_column='student_id'
    )
    field_name = models.CharField(max_length=100)
    original_value = models.TextField(null=True, blank=True)
    corrected_value = models.TextField()
    correction_reason = models.TextField()
    approved_by = models.ForeignKey(
        'identity.User',
        on_delete=models.PROTECT,
        related_name='approved_corrections',
        db_column='approved_by'
    )
    approved_at = models.DateTimeField(default=timezone.now)
    source = models.CharField(max_length=30, default='ADMIN_CORRECTION')

    class Meta:
        db_table = 'student_data_corrections'
        ordering = ['-approved_at']
        verbose_name = 'Student Data Correction'
        verbose_name_plural = 'Student Data Corrections'
        indexes = [
            models.Index(fields=['student', 'field_name'], name='idx_student_corr_field'),
        ]

    def __str__(self):
        return f"Correction for {self.student.candidate_name}: {self.field_name} -> {self.corrected_value}"
