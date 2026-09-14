"""
Academic Foundation Models.
Implements Deliverable D.2 of DATABASE_ARCHITECTURE.md:
Departments, Programs, Academic Years, Semesters, Batches,
Department Intakes, Schemes, Subjects, and Scheme-Subjects.
"""

from django.db import models
from common.models import TimeStampedUUIDModel
from common.exceptions import InvariantViolationError
from apps.academic.domain.invariants import (
    validate_academic_year_dates,
    validate_semester_dates,
    validate_scheme_subject_marks,
    validate_intake_capacities,
)


class Department(TimeStampedUUIDModel):
    """Authoritative organizational academic department."""
    name = models.CharField(max_length=200, unique=True)
    code = models.CharField(max_length=20, unique=True)
    is_active = models.BooleanField(default=True)
    # Govt CAP choice codes allotted to this department (one dept -> many codes,
    # e.g. CSE has both 0603624211T and 603624210 for different seat types).
    choice_codes = models.JSONField(default=list, blank=True, help_text='DTE choice codes mapped to this department')

    class Meta:
        db_table = 'departments'
        ordering = ['name']
        verbose_name = 'Department'
        verbose_name_plural = 'Departments'

    def __str__(self):
        return f"{self.code} - {self.name}"


class Program(TimeStampedUUIDModel):
    """Academic degree program offered by a department (e.g. B.Tech Computer Science)."""
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name='programs',
        db_column='department_id'
    )
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20)
    duration_years = models.PositiveSmallIntegerField(default=4)
    degree_type = models.CharField(max_length=30, default='B.Tech')
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'programs'
        ordering = ['name']
        unique_together = (('department', 'code'),)
        verbose_name = 'Program'
        verbose_name_plural = 'Programs'

    def __str__(self):
        return f"{self.code} ({self.degree_type}) - {self.department.code}"


class AcademicYear(TimeStampedUUIDModel):
    """Institutional academic session (e.g. 2026-2027)."""
    label = models.CharField(max_length=20, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)

    class Meta:
        db_table = 'academic_years'
        ordering = ['-start_date']
        verbose_name = 'Academic Year'
        verbose_name_plural = 'Academic Years'

    def clean(self):
        validate_academic_year_dates(self.start_date, self.end_date)

    def save(self, *args, **kwargs):
        self.clean()
        if self.is_current:
            # Enforce single current academic year
            AcademicYear.objects.filter(is_current=True).exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.label


class Semester(TimeStampedUUIDModel):
    """Instructional semester division within an academic year."""
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name='semesters',
        db_column='academic_year_id'
    )
    number = models.PositiveSmallIntegerField()
    label = models.CharField(max_length=30, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'semesters'
        ordering = ['academic_year', 'number']
        unique_together = (('academic_year', 'number'),)
        verbose_name = 'Semester'
        verbose_name_plural = 'Semesters'

    def clean(self):
        validate_semester_dates(self.start_date, self.end_date)

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.label or f"Sem {self.number} ({self.academic_year.label})"


class Batch(TimeStampedUUIDModel):
    """Department student cohort organized under an academic year."""
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name='batches',
        db_column='department_id'
    )
    name = models.CharField(max_length=50)
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.PROTECT,
        related_name='batches',
        db_column='academic_year_id'
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'batches'
        ordering = ['department', '-academic_year__start_date', 'name']
        unique_together = (('department', 'name', 'academic_year'),)
        verbose_name = 'Batch'
        verbose_name_plural = 'Batches'

    def __str__(self):
        return f"{self.department.code} - {self.name} ({self.academic_year.label})"


class DepartmentIntake(TimeStampedUUIDModel):
    """Annual intake capacity for department programs per academic year."""
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name='intakes',
        db_column='department_id'
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.PROTECT,
        related_name='department_intakes',
        db_column='academic_year_id'
    )
    program = models.ForeignKey(
        Program,
        on_delete=models.PROTECT,
        related_name='intakes',
        db_column='program_id'
    )
    sanctioned_intake = models.PositiveIntegerField()
    actual_intake = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        db_table = 'department_intakes'
        ordering = ['-academic_year__start_date', 'department', 'program']
        unique_together = (('department', 'academic_year', 'program'),)
        verbose_name = 'Department Intake'
        verbose_name_plural = 'Department Intakes'

    def clean(self):
        validate_intake_capacities(self.sanctioned_intake, self.actual_intake)

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.program.code} Intake {self.sanctioned_intake} ({self.academic_year.label})"


class Scheme(TimeStampedUUIDModel):
    """Curriculum scheme revision applicable to a program from an academic year onward."""
    program = models.ForeignKey(
        Program,
        on_delete=models.PROTECT,
        related_name='schemes',
        db_column='program_id'
    )
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=30, unique=True)
    effective_from_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.PROTECT,
        related_name='effective_schemes',
        db_column='effective_from_year_id'
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'schemes'
        ordering = ['program', '-effective_from_year__start_date', 'name']
        verbose_name = 'Scheme'
        verbose_name_plural = 'Schemes'

    def __str__(self):
        return f"{self.code} - {self.name} ({self.program.code})"


class Subject(TimeStampedUUIDModel):
    """Reusable subject identity independent of specific schemes."""
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=30, unique=True)

    class Meta:
        db_table = 'subjects'
        ordering = ['code']
        verbose_name = 'Subject'
        verbose_name_plural = 'Subjects'

    def __str__(self):
        return f"{self.code} - {self.name}"


class SchemeSubject(TimeStampedUUIDModel):
    """Mapping and credit/evaluation configuration of a subject within a specific scheme."""
    class SubjectType(models.TextChoices):
        THEORY = 'THEORY', 'Theory'
        PRACTICAL = 'PRACTICAL', 'Practical'
        PROJECT = 'PROJECT', 'Project'
        SEMINAR = 'SEMINAR', 'Seminar'
        OTHER = 'OTHER', 'Other'

    scheme = models.ForeignKey(
        Scheme,
        on_delete=models.PROTECT,
        related_name='scheme_subjects',
        db_column='scheme_id'
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.PROTECT,
        related_name='scheme_mappings',
        db_column='subject_id'
    )
    semester_number = models.PositiveSmallIntegerField()
    subject_type = models.CharField(
        max_length=30,
        choices=SubjectType.choices,
        default=SubjectType.THEORY
    )
    credits = models.PositiveSmallIntegerField(default=3)
    max_marks = models.PositiveSmallIntegerField(default=100)
    passing_marks = models.PositiveSmallIntegerField(default=40)
    max_internal_marks = models.PositiveSmallIntegerField(null=True, blank=True)
    passing_internal_marks = models.PositiveSmallIntegerField(null=True, blank=True)
    is_elective = models.BooleanField(default=False)
    is_locked = models.BooleanField(
        default=False,
        help_text="Once results or enrollments exist for this scheme subject, it is locked against modification."
    )

    class Meta:
        db_table = 'scheme_subjects'
        ordering = ['scheme', 'semester_number', 'subject__code']
        unique_together = (('scheme', 'subject', 'semester_number'),)
        indexes = [
            models.Index(fields=['scheme', 'semester_number'], name='idx_scheme_subj_scheme_sem'),
        ]
        verbose_name = 'Scheme Subject'
        verbose_name_plural = 'Scheme Subjects'

    def clean(self):
        validate_scheme_subject_marks(
            self.max_marks,
            self.passing_marks,
            self.max_internal_marks,
            self.passing_internal_marks
        )

    def save(self, *args, **kwargs):
        if self.pk:
            # Check historical immutability if locked
            prev = SchemeSubject.objects.filter(pk=self.pk).first()
            if prev and prev.is_locked:
                # Disallow altering credit or marks distribution on locked scheme subjects
                critical_fields = ['credits', 'max_marks', 'passing_marks', 'max_internal_marks', 'passing_internal_marks', 'subject_type']
                for field in critical_fields:
                    if getattr(self, field) != getattr(prev, field):
                        raise InvariantViolationError(
                            f"Cannot modify '{field}' on locked SchemeSubject: historical integrity must be preserved."
                        )
        self.clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.is_locked:
            raise InvariantViolationError(
                "Cannot delete locked SchemeSubject: historical integrity must be preserved."
            )
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.scheme.code} | Sem {self.semester_number} | {self.subject.code} ({self.credits} cr)"
