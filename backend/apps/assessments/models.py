"""
Assessments and Unit Test Marks domain models.
Implements Section 10 of TASKS.md:
- 10.1 Assessment type and assessment definition vertical slice
- 10.1 Assessment marks storage and student/subject association
- 10.2 Faculty unit-test marks upload, extraction, validation, persistence, and student view
"""

from decimal import Decimal
from django.db import models
from django.utils import timezone
from common.models import TimeStampedUUIDModel
from apps.assessments.domain.invariants import (
    validate_mark_entry,
    validate_assessment_lock,
)


class AssessmentStatus(models.TextChoices):
    DRAFT = 'DRAFT', 'Draft'
    PUBLISHED = 'PUBLISHED', 'Published'
    LOCKED = 'LOCKED', 'Locked'


class AssessmentType(TimeStampedUUIDModel):
    """
    Extensible category of academic assessment (Task 10.1.1).
    Examples: UNIT_TEST_1, UNIT_TEST_2, IN_SEM, MID_TERM, ASSIGNMENT, PRACTICAL.
    """
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default='')
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'assessment_types'
        ordering = ['code']
        verbose_name = 'Assessment Type'
        verbose_name_plural = 'Assessment Types'

    def __str__(self):
        return f"{self.code} - {self.name}"


class Assessment(TimeStampedUUIDModel):
    """
    Authoritative academic assessment definition.
    Anchored in Academic Foundation (AcademicYear, Semester, Department, SchemeSubject).
    Linked to FacultyAssignment to govern teacher ownership.
    """
    title = models.CharField(max_length=200)
    assessment_type = models.ForeignKey(
        AssessmentType,
        on_delete=models.PROTECT,
        related_name='assessments',
        db_column='assessment_type_id'
    )
    academic_year = models.ForeignKey(
        'academic.AcademicYear',
        on_delete=models.PROTECT,
        related_name='assessments',
        db_column='academic_year_id'
    )
    semester = models.ForeignKey(
        'academic.Semester',
        on_delete=models.PROTECT,
        related_name='assessments',
        db_column='semester_id'
    )
    department = models.ForeignKey(
        'academic.Department',
        on_delete=models.PROTECT,
        related_name='assessments',
        db_column='department_id'
    )
    program = models.ForeignKey(
        'academic.Program',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='assessments',
        db_column='program_id'
    )
    scheme_subject = models.ForeignKey(
        'academic.SchemeSubject',
        on_delete=models.PROTECT,
        related_name='assessments',
        db_column='scheme_subject_id'
    )
    batch = models.ForeignKey(
        'academic.Batch',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='assessments',
        db_column='batch_id',
        help_text="Optional cohort/batch division filter"
    )
    faculty_assignment = models.ForeignKey(
        'faculty.FacultyAssignment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assessments',
        db_column='faculty_assignment_id'
    )
    max_marks = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal('25.00')
    )
    passing_marks = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal('10.00')
    )
    assessment_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=30,
        choices=AssessmentStatus.choices,
        default=AssessmentStatus.DRAFT
    )
    created_by = models.ForeignKey(
        'identity.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_assessments',
        db_column='created_by'
    )
    published_at = models.DateTimeField(null=True, blank=True)
    locked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'assessments'
        ordering = ['-academic_year__start_date', 'semester', 'scheme_subject__subject__name']
        verbose_name = 'Assessment'
        verbose_name_plural = 'Assessments'

    @property
    def is_locked(self) -> bool:
        return self.status == AssessmentStatus.LOCKED

    def __str__(self):
        return f"{self.title} ({self.scheme_subject.subject.code}) - {self.academic_year.label} [{self.status}]"


class AssessmentMark(TimeStampedUUIDModel):
    """
    Authoritative student assessment mark record (Task 10.1.2).
    Associated with student and subject context.
    """
    assessment = models.ForeignKey(
        Assessment,
        on_delete=models.CASCADE,
        related_name='marks',
        db_column='assessment_id'
    )
    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='assessment_marks',
        db_column='student_id'
    )
    enrollment = models.ForeignKey(
        'students.StudentEnrollment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assessment_marks',
        db_column='enrollment_id'
    )
    marks_obtained = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True
    )
    is_absent = models.BooleanField(default=False)
    remarks = models.TextField(blank=True, default='')
    entered_by = models.ForeignKey(
        'identity.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='entered_marks',
        db_column='entered_by'
    )

    class Meta:
        db_table = 'assessment_marks'
        unique_together = (('assessment', 'student'),)
        ordering = ['student__candidate_name']
        verbose_name = 'Assessment Mark'
        verbose_name_plural = 'Assessment Marks'

    def clean(self):
        validate_assessment_lock(self.assessment.is_locked)
        validate_mark_entry(
            marks_obtained=self.marks_obtained,
            max_marks=self.assessment.max_marks,
            is_absent=self.is_absent
        )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        marks_str = "ABSENT" if self.is_absent else str(self.marks_obtained)
        return f"{self.student.candidate_name}: {marks_str}/{self.assessment.max_marks} ({self.assessment.title})"
