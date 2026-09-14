"""
Faculty business logic and domain service.
Implements operations for faculty lifecycle, department info, teaching assignments, and academic items.
"""

from typing import Optional, Dict, Any, List
from datetime import date
from django.db import transaction
from django.utils import timezone

from apps.faculty.models import (
    Faculty,
    FacultyStatus,
    EmploymentType,
    FacultyAssignment,
    AssignmentRole,
    FacultyAcademicItem,
    AcademicItemType,
)
from apps.faculty.domain.invariants import (
    validate_faculty_lifecycle,
    validate_faculty_assignment,
    validate_academic_item,
)
from apps.academic.models import Department, AcademicYear, Semester, Batch, SchemeSubject
from common.exceptions import InvariantViolationError


class FacultyService:
    """Service governing faculty lifecycle, organizational assignments, and academic portfolio."""

    @classmethod
    @transaction.atomic
    def create_faculty(
        cls,
        faculty_id: str,
        first_name: str,
        last_name: str,
        email: str,
        department: Department,
        date_of_joining: date,
        designation: str = 'Assistant Professor',
        employment_type: str = EmploymentType.PERMANENT,
        status: str = FacultyStatus.ACTIVE,
        phone: str = '',
        user=None,
        is_hod: bool = False,
        cabin_number: str = '',
        contact_email: str = '',
        responsibilities: str = '',
        qualification: str = '',
        specialization: str = '',
        actor=None
    ) -> Faculty:
        validate_faculty_lifecycle(status, date_of_joining, None)

        faculty = Faculty(
            faculty_id=faculty_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            department=department,
            date_of_joining=date_of_joining,
            designation=designation,
            employment_type=employment_type,
            status=status,
            phone=phone,
            user=user,
            is_hod=is_hod,
            cabin_number=cabin_number,
            contact_email=contact_email or email,
            responsibilities=responsibilities,
            qualification=qualification,
            specialization=specialization,
            created_by=actor,
            updated_by=actor
        )
        faculty.save()
        return faculty

    @classmethod
    @transaction.atomic
    def update_faculty(
        cls,
        faculty: Faculty,
        actor=None,
        **fields
    ) -> Faculty:
        for field, value in fields.items():
            if hasattr(faculty, field):
                setattr(faculty, field, value)
        faculty.updated_by = actor
        faculty.save()
        return faculty

    @classmethod
    @transaction.atomic
    def transition_status(
        cls,
        faculty: Faculty,
        new_status: str,
        relieving_date: Optional[date] = None,
        actor=None
    ) -> Faculty:
        if new_status in {FacultyStatus.RESIGNED, FacultyStatus.RETIRED, FacultyStatus.TERMINATED}:
            relieving_date = relieving_date or date.today()

        validate_faculty_lifecycle(new_status, faculty.date_of_joining, relieving_date)

        faculty.status = new_status
        if relieving_date:
            faculty.date_of_relieving = relieving_date
        faculty.updated_by = actor
        faculty.save()

        # If faculty becomes inactive, deactivate active assignments historically
        if new_status in {FacultyStatus.RESIGNED, FacultyStatus.RETIRED, FacultyStatus.TERMINATED}:
            faculty.assignments.filter(is_active=True).update(
                is_active=False,
                effective_end_date=relieving_date or date.today()
            )

        return faculty

    @classmethod
    @transaction.atomic
    def assign_subject(
        cls,
        faculty: Faculty,
        academic_year: AcademicYear,
        semester: Semester,
        scheme_subject: SchemeSubject,
        batch: Optional[Batch] = None,
        role: str = AssignmentRole.PRIMARY_INSTRUCTOR,
        effective_start_date: Optional[date] = None,
        actor=None,
        remarks: str = ''
    ) -> FacultyAssignment:
        """
        Creates an authoritative teaching assignment linking Faculty to Scheme Subject,
        Academic Year, Semester, and Batch.
        Preserves historical continuity.
        """
        validate_faculty_assignment(
            faculty_status=faculty.status,
            academic_year_id=academic_year.id,
            semester_academic_year_id=semester.academic_year_id,
            batch_academic_year_id=batch.academic_year_id if batch else None
        )

        assignment = FacultyAssignment(
            faculty=faculty,
            academic_year=academic_year,
            semester=semester,
            scheme_subject=scheme_subject,
            batch=batch,
            role=role,
            is_active=True,
            effective_start_date=effective_start_date or date.today(),
            assigned_by=actor,
            remarks=remarks
        )
        assignment.save()
        return assignment

    @classmethod
    @transaction.atomic
    def retire_assignment(
        cls,
        assignment: FacultyAssignment,
        end_date: Optional[date] = None,
        actor=None
    ) -> FacultyAssignment:
        """
        Retires an assignment historically without deleting records.
        """
        assignment.is_active = False
        assignment.effective_end_date = end_date or date.today()
        assignment.save()
        return assignment

    @classmethod
    @transaction.atomic
    def add_academic_item(
        cls,
        faculty: Faculty,
        item_type: str,
        title: str,
        year: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        reference_url: str = '',
        actor=None
    ) -> FacultyAcademicItem:
        validate_academic_item(item_type, title, year)
        item = FacultyAcademicItem(
            faculty=faculty,
            item_type=item_type,
            title=title,
            year=year,
            details=details or {},
            reference_url=reference_url,
            created_by=actor
        )
        item.save()
        return item
