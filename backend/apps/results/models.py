import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from apps.results.domain.invariants import (
    validate_result_immutability,
    validate_eligibility_rule_invariants,
    validate_decision_immutability,
)


class ResultImportBatch(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('VALIDATED', 'Validated'),
        ('APPROVED', 'Approved'),
        ('PUBLISHED', 'Published'),
        ('REJECTED', 'Rejected'),
        ('FAILED', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    academic_year = models.ForeignKey(
        'academic.AcademicYear',
        on_delete=models.PROTECT,
        related_name='result_batches'
    )
    semester = models.ForeignKey(
        'academic.Semester',
        on_delete=models.PROTECT,
        related_name='result_batches'
    )
    department = models.ForeignKey(
        'academic.Department',
        on_delete=models.PROTECT,
        related_name='result_batches'
    )
    program = models.ForeignKey(
        'academic.Program',
        on_delete=models.PROTECT,
        related_name='result_batches'
    )
    file_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500, blank=True, null=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='PENDING')
    total_rows = models.PositiveIntegerField(default=0)
    valid_rows = models.PositiveIntegerField(default=0)
    error_rows = models.PositiveIntegerField(default=0)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='result_batches_uploaded'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='result_batches_approved'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='result_batches_published'
    )
    published_at = models.DateTimeField(null=True, blank=True)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'result_import_batches'
        ordering = ['-created_at']

    def __str__(self):
        return f"ResultBatch {self.file_name} ({self.status}) - {self.academic_year.label}"


class ResultImportRow(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('VALID', 'Valid'),
        ('INVALID', 'Invalid'),
        ('PROCESSED', 'Processed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch = models.ForeignKey(
        ResultImportBatch,
        on_delete=models.CASCADE,
        related_name='rows'
    )
    row_number = models.PositiveIntegerField()
    raw_data = models.JSONField(default=dict)
    student_identifier = models.CharField(max_length=100)
    matched_student = models.ForeignKey(
        'students.Student',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='result_import_rows'
    )
    subject_code = models.CharField(max_length=50)
    matched_scheme_subject = models.ForeignKey(
        'academic.SchemeSubject',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='result_import_rows'
    )
    internal_marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    external_marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    total_marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    grade = models.CharField(max_length=10, blank=True)
    grade_points = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    is_absent = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    validation_errors = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'result_import_rows'
        ordering = ['batch', 'row_number']

    def __str__(self):
        return f"Row {self.row_number}: {self.student_identifier} - {self.subject_code} ({self.status})"


class StudentResult(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('APPROVED', 'Approved'),
        ('PUBLISHED', 'Published'),
        ('SUPERSEDED', 'Superseded'),
    ]

    OUTCOME_CHOICES = [
        ('PASS', 'Pass'),
        ('FAIL', 'Fail'),
        ('ATKT', 'Allowed to Keep Term'),
        ('WITHHELD', 'Withheld'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        'students.Student',
        on_delete=models.PROTECT,
        related_name='results'
    )
    academic_year = models.ForeignKey(
        'academic.AcademicYear',
        on_delete=models.PROTECT,
        related_name='student_results'
    )
    semester = models.ForeignKey(
        'academic.Semester',
        on_delete=models.PROTECT,
        related_name='student_results'
    )
    batch = models.ForeignKey(
        'academic.Batch',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='student_results'
    )
    version = models.PositiveIntegerField(default=1)
    is_latest = models.BooleanField(default=True)
    superseded_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='superseded_versions'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    total_marks_obtained = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal('0.00'))
    total_max_marks = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal('0.00'))
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    sgpa = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    cgpa = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    result_status = models.CharField(max_length=20, choices=OUTCOME_CHOICES, default='PASS')
    import_batch = models.ForeignKey(
        ResultImportBatch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='student_results'
    )
    published_at = models.DateTimeField(null=True, blank=True)
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='published_results'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'student_results'
        ordering = ['-academic_year__start_date', 'semester__number', 'student__enrollment_no', '-version']
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'academic_year', 'semester', 'version'],
                name='unique_student_semester_result_version'
            )
        ]

    def delete(self, *args, **kwargs):
        validate_result_immutability(self)
        return super().delete(*args, **kwargs)

    def __str__(self):
        return f"Result {self.student.enrollment_no} - Sem {self.semester.number} (v{self.version}, {self.status})"


class StudentResultDetail(models.Model):
    STATUS_CHOICES = [
        ('PASS', 'Pass'),
        ('FAIL', 'Fail'),
        ('ABSENT', 'Absent'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student_result = models.ForeignKey(
        StudentResult,
        on_delete=models.CASCADE,
        related_name='details'
    )
    scheme_subject = models.ForeignKey(
        'academic.SchemeSubject',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='result_details'
    )
    subject_code = models.CharField(max_length=50)
    subject_name = models.CharField(max_length=200)
    internal_marks = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    external_marks = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    total_marks = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    max_marks = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('100.00'))
    grade = models.CharField(max_length=10, default='P')
    grade_points = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('0.00'))
    credits_earned = models.DecimalField(max_digits=4, decimal_places=1, default=Decimal('0.0'))
    is_absent = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PASS')

    class Meta:
        db_table = 'student_result_details'
        ordering = ['student_result', 'subject_code']

    def delete(self, *args, **kwargs):
        validate_result_immutability(self)
        return super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.subject_code} - {self.total_marks}/{self.max_marks} ({self.grade})"


class ResultCorrectionRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    target_result = models.ForeignKey(
        StudentResult,
        on_delete=models.PROTECT,
        related_name='correction_requests'
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='result_corrections_requested'
    )
    reason = models.TextField()
    proposed_changes = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='result_corrections_reviewed'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'result_correction_requests'
        ordering = ['-created_at']

    def __str__(self):
        return f"Correction for {self.target_result.student.enrollment_no} - {self.status}"


class ResultCorrectionAudit(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    original_result = models.ForeignKey(
        StudentResult,
        on_delete=models.SET_NULL,
        null=True,
        related_name='original_audits'
    )
    superseding_result = models.ForeignKey(
        StudentResult,
        on_delete=models.SET_NULL,
        null=True,
        related_name='superseding_audits'
    )
    correction_request = models.ForeignKey(
        ResultCorrectionRequest,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audits'
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='result_correction_audits'
    )
    action = models.CharField(max_length=50)
    reason = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'result_correction_audits'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.action} by {self.actor} at {self.timestamp}"


class StudentCredit(models.Model):
    """
    Derived credit record generated from published StudentResult.
    Preserves historical calculations for each result version.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        'students.Student',
        on_delete=models.PROTECT,
        related_name='credits'
    )
    academic_year = models.ForeignKey(
        'academic.AcademicYear',
        on_delete=models.PROTECT,
        related_name='student_credits'
    )
    semester = models.ForeignKey(
        'academic.Semester',
        on_delete=models.PROTECT,
        related_name='student_credits'
    )
    result = models.ForeignKey(
        StudentResult,
        on_delete=models.PROTECT,
        related_name='credit_records'
    )
    result_version = models.PositiveIntegerField(default=1)
    credits_attempted = models.DecimalField(max_digits=5, decimal_places=1, default=Decimal('0.0'))
    credits_earned = models.DecimalField(max_digits=5, decimal_places=1, default=Decimal('0.0'))
    sgpa = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    cgpa = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    cumulative_credits_earned = models.DecimalField(max_digits=6, decimal_places=1, default=Decimal('0.0'))
    backlogs_count = models.PositiveIntegerField(default=0)
    version = models.PositiveIntegerField(default=1)
    is_latest = models.BooleanField(default=True)
    calculated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='calculated_credits'
    )
    calculated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'student_credits'
        ordering = ['-academic_year__start_date', 'semester__number', '-version']
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'academic_year', 'semester', 'version'],
                name='unique_student_credit_per_version'
            )
        ]

    def delete(self, *args, **kwargs):
        if not self.is_latest or (self.result and self.result.status in ('PUBLISHED', 'SUPERSEDED')):
            validate_result_immutability(self.result)
        return super().delete(*args, **kwargs)

    def __str__(self):
        return f"Credit {self.student.enrollment_no} - Sem {self.semester.number} (Earned: {self.credits_earned}/{self.credits_attempted})"


class EligibilityRule(models.Model):
    """
    Configurable academic eligibility and detention rule definition.
    Versioned to maintain historical explainability for all academic decisions.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=50)
    academic_year = models.ForeignKey(
        'academic.AcademicYear',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='eligibility_rules'
    )
    program = models.ForeignKey(
        'academic.Program',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='eligibility_rules'
    )
    target_semester = models.PositiveSmallIntegerField(null=True, blank=True)
    version = models.PositiveIntegerField(default=1)
    min_credits_required = models.DecimalField(max_digits=5, decimal_places=1, default=Decimal('18.0'))
    min_attendance_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('75.00'))
    max_backlogs_allowed = models.PositiveIntegerField(default=2)
    detention_max_backlogs = models.PositiveIntegerField(default=4)
    detention_min_attendance = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('50.00'))
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_eligibility_rules'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'eligibility_rules'
        ordering = ['-created_at', '-version']
        constraints = [
            models.UniqueConstraint(
                fields=['code', 'version'],
                name='unique_rule_code_version'
            )
        ]

    def clean(self):
        validate_eligibility_rule_invariants(
            self.min_credits_required,
            self.min_attendance_percentage,
            self.max_backlogs_allowed,
            self.detention_max_backlogs,
            self.detention_min_attendance
        )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        prog = self.program.code if self.program else "GLOBAL"
        return f"{self.name} (v{self.version}, {prog})"


class EligibilityDecision(models.Model):
    """
    Explicit eligibility decision (ELIGIBLE, NOT_ELIGIBLE, DETAINED).
    Retains the exact rule and rule version used to produce the decision.
    """
    DECISION_CHOICES = [
        ('ELIGIBLE', 'Eligible'),
        ('NOT_ELIGIBLE', 'Not Eligible'),
        ('DETAINED', 'Detained'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        'students.Student',
        on_delete=models.PROTECT,
        related_name='eligibility_decisions'
    )
    academic_year = models.ForeignKey(
        'academic.AcademicYear',
        on_delete=models.PROTECT,
        related_name='eligibility_decisions'
    )
    semester = models.ForeignKey(
        'academic.Semester',
        on_delete=models.PROTECT,
        related_name='eligibility_decisions'
    )
    rule = models.ForeignKey(
        EligibilityRule,
        on_delete=models.PROTECT,
        related_name='decisions'
    )
    rule_version = models.PositiveIntegerField()
    credits_earned = models.DecimalField(max_digits=5, decimal_places=1, default=Decimal('0.0'))
    credits_attempted = models.DecimalField(max_digits=5, decimal_places=1, default=Decimal('0.0'))
    backlogs_count = models.PositiveIntegerField(default=0)
    attendance_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('100.00'))
    decision = models.CharField(max_length=20, choices=DECISION_CHOICES, default='ELIGIBLE')
    detention_reason = models.TextField(blank=True)
    remarks = models.TextField(blank=True)
    version = models.PositiveIntegerField(default=1)
    is_latest = models.BooleanField(default=True)
    superseded_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='superseded_decisions'
    )
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='eligibility_decisions_made'
    )
    decided_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'eligibility_decisions'
        ordering = ['-decided_at', '-version']

    def delete(self, *args, **kwargs):
        validate_decision_immutability(self)
        return super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.student.enrollment_no} - Sem {self.semester.number}: {self.decision} (Rule v{self.rule_version})"


class NextYearEligibilityList(models.Model):
    """
    Official promotion register snapshot for next-year admission.
    Generated from active StudentEnrollment and latest EligibilityDecision records.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    academic_year = models.ForeignKey(
        'academic.AcademicYear',
        on_delete=models.PROTECT,
        related_name='next_year_lists'
    )
    semester = models.ForeignKey(
        'academic.Semester',
        on_delete=models.PROTECT,
        related_name='next_year_lists'
    )
    target_academic_year = models.ForeignKey(
        'academic.AcademicYear',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='target_next_year_lists'
    )
    target_semester_number = models.PositiveSmallIntegerField()
    program = models.ForeignKey(
        'academic.Program',
        on_delete=models.PROTECT,
        related_name='next_year_lists'
    )
    total_students = models.PositiveIntegerField(default=0)
    eligible_count = models.PositiveIntegerField(default=0)
    not_eligible_count = models.PositiveIntegerField(default=0)
    detained_count = models.PositiveIntegerField(default=0)
    items = models.JSONField(default=list)
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generated_next_year_lists'
    )
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'next_year_eligibility_lists'
        ordering = ['-generated_at']

    def __str__(self):
        return f"Promotion List {self.program.code} Sem {self.semester.number} -> {self.target_semester_number} ({self.total_students} students)"
