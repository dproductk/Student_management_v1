"""
Faculty and Academic Assignment domain models.
Implements Section 7 of TASKS.md:
- 7.1 Faculty profile, lifecycle, department and organizational information.
- 7.2 Faculty subject-assignment, historical teaching assignments, and scoped student visibility.
- 7.3 Faculty academic items (publications, patents, books, awards, memberships, consultancy, guidance).
"""

from django.db import models
from common.models import TimeStampedUUIDModel
from common.exceptions import InvariantViolationError
from apps.faculty.domain.invariants import (
    validate_faculty_lifecycle,
    validate_faculty_assignment,
    validate_academic_item,
)


class FacultyStatus(models.TextChoices):
    ACTIVE = 'ACTIVE', 'Active'
    ON_LEAVE = 'ON_LEAVE', 'On Leave'
    RESIGNED = 'RESIGNED', 'Resigned'
    RETIRED = 'RETIRED', 'Retired'
    TERMINATED = 'TERMINATED', 'Terminated'


class EmploymentType(models.TextChoices):
    PERMANENT = 'PERMANENT', 'Permanent'
    CONTRACT = 'CONTRACT', 'Contract'
    VISITING = 'VISITING', 'Visiting'
    ADJUNCT = 'ADJUNCT', 'Adjunct'


class AssignmentRole(models.TextChoices):
    PRIMARY_INSTRUCTOR = 'PRIMARY_INSTRUCTOR', 'Primary Instructor'
    CO_INSTRUCTOR = 'CO_INSTRUCTOR', 'Co-Instructor'
    LAB_INSTRUCTOR = 'LAB_INSTRUCTOR', 'Lab Instructor'
    CLASS_TEACHER = 'CLASS_TEACHER', 'Class Teacher / Mentor'


class AcademicItemType(models.TextChoices):
    PUBLICATION = 'PUBLICATION', 'Publication'
    PATENT = 'PATENT', 'Patent'
    BOOK = 'BOOK', 'Book / Book Chapter'
    AWARD = 'AWARD', 'Award / Honor'
    MEMBERSHIP = 'MEMBERSHIP', 'Professional Membership'
    CONSULTANCY = 'CONSULTANCY', 'Consultancy'
    GUIDANCE = 'GUIDANCE', 'Research Guidance'


class Faculty(TimeStampedUUIDModel):
    """Authoritative faculty profile and institutional lifecycle record."""
    user = models.OneToOneField(
        'identity.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='faculty_profile',
        db_column='user_id'
    )
    faculty_id = models.CharField(max_length=50, unique=True, db_index=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, default='')
    designation = models.CharField(max_length=100, default='Assistant Professor')
    employment_type = models.CharField(
        max_length=30,
        choices=EmploymentType.choices,
        default=EmploymentType.PERMANENT
    )
    status = models.CharField(
        max_length=30,
        choices=FacultyStatus.choices,
        default=FacultyStatus.ACTIVE
    )
    date_of_joining = models.DateField()
    date_of_relieving = models.DateField(null=True, blank=True)
    qualification = models.CharField(max_length=255, blank=True, default='')
    specialization = models.CharField(max_length=255, blank=True, default='')

    # Department and organizational info (Task 7.1.2)
    department = models.ForeignKey(
        'academic.Department',
        on_delete=models.PROTECT,
        related_name='faculty_members',
        db_column='department_id'
    )
    is_hod = models.BooleanField(default=False)
    cabin_number = models.CharField(max_length=50, blank=True, default='')
    contact_email = models.EmailField(blank=True, default='')
    responsibilities = models.TextField(blank=True, default='')

    # Audit tracking
    created_by = models.ForeignKey(
        'identity.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_faculty',
        db_column='created_by'
    )
    updated_by = models.ForeignKey(
        'identity.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_faculty',
        db_column='updated_by'
    )

    class Meta:
        db_table = 'faculty'
        ordering = ['first_name', 'last_name']
        verbose_name = 'Faculty'
        verbose_name_plural = 'Faculty'

    def clean(self):
        validate_faculty_lifecycle(
            status=self.status,
            date_of_joining=self.date_of_joining,
            date_of_relieving=self.date_of_relieving
        )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    def __str__(self):
        return f"{self.faculty_id} - {self.full_name} ({self.department.code})"


class FacultyAssignment(TimeStampedUUIDModel):
    """
    Historical teaching and subject assignment record.
    Implements Task 7.2.1 and Task 7.2.2.
    Preserves academic year, semester, and batch context historically.
    """
    faculty = models.ForeignKey(
        Faculty,
        on_delete=models.CASCADE,
        related_name='assignments',
        db_column='faculty_id'
    )
    academic_year = models.ForeignKey(
        'academic.AcademicYear',
        on_delete=models.PROTECT,
        related_name='faculty_assignments',
        db_column='academic_year_id'
    )
    semester = models.ForeignKey(
        'academic.Semester',
        on_delete=models.PROTECT,
        related_name='faculty_assignments',
        db_column='semester_id'
    )
    scheme_subject = models.ForeignKey(
        'academic.SchemeSubject',
        on_delete=models.PROTECT,
        related_name='faculty_assignments',
        db_column='scheme_subject_id'
    )
    batch = models.ForeignKey(
        'academic.Batch',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='faculty_assignments',
        db_column='batch_id'
    )
    role = models.CharField(
        max_length=30,
        choices=AssignmentRole.choices,
        default=AssignmentRole.PRIMARY_INSTRUCTOR
    )
    is_active = models.BooleanField(default=True)
    effective_start_date = models.DateField(null=True, blank=True)
    effective_end_date = models.DateField(null=True, blank=True)
    assigned_by = models.ForeignKey(
        'identity.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_faculty_roles',
        db_column='assigned_by'
    )
    remarks = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'faculty_assignments'
        ordering = ['-academic_year__start_date', '-is_active', 'faculty__last_name']
        verbose_name = 'Faculty Teaching Assignment'
        verbose_name_plural = 'Faculty Teaching Assignments'
        indexes = [
            models.Index(fields=['academic_year', 'semester', 'batch']),
            models.Index(fields=['faculty', 'is_active']),
            models.Index(fields=['scheme_subject']),
        ]

    def clean(self):
        validate_faculty_assignment(
            faculty_status=self.faculty.status,
            academic_year_id=self.academic_year_id,
            semester_academic_year_id=self.semester.academic_year_id,
            batch_academic_year_id=self.batch.academic_year_id if self.batch else None
        )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        batch_str = f" - Batch {self.batch.name}" if self.batch else ""
        return f"{self.faculty.full_name} -> {self.scheme_subject.subject.code} ({self.semester.label or self.semester.number}){batch_str}"


class FacultyAcademicItem(TimeStampedUUIDModel):
    """
    Faculty academic information item.
    Implements Task 7.3.1: publications, patents, books, awards, memberships, consultancy, guidance.
    """
    faculty = models.ForeignKey(
        Faculty,
        on_delete=models.CASCADE,
        related_name='academic_items',
        db_column='faculty_id'
    )
    item_type = models.CharField(
        max_length=30,
        choices=AcademicItemType.choices
    )
    title = models.CharField(max_length=300)
    year = models.PositiveIntegerField(null=True, blank=True)
    details = models.JSONField(default=dict, blank=True)
    reference_url = models.URLField(max_length=500, blank=True, default='')
    created_by = models.ForeignKey(
        'identity.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_academic_items',
        db_column='created_by'
    )

    class Meta:
        db_table = 'faculty_academic_items'
        ordering = ['-year', 'title']
        verbose_name = 'Faculty Academic Item'
        verbose_name_plural = 'Faculty Academic Items'
        indexes = [
            models.Index(fields=['faculty', 'item_type']),
            models.Index(fields=['item_type', 'year']),
        ]

    def clean(self):
        validate_academic_item(
            item_type=self.item_type,
            title=self.title,
            year=self.year
        )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.item_type}] {self.title} ({self.faculty.full_name})"
