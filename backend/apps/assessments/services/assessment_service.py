"""
Assessment Application Service Layer.
Implements:
- Assessment type and definition management (Tasks 10.1.1)
- Structured marks storage and student/subject association (Task 10.1.2)
- Faculty unit-test marks upload, extraction, and validation (Tasks 10.2.1, 10.2.2)
- Unit-test marks persistence and student-view retrieval (Task 10.2.3)
- Duplicate/error-handling guards (Task 10.2.4)
"""

from decimal import Decimal
from typing import Optional, List, Dict, Any, Union
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied

from apps.assessments.models import (
    AssessmentType,
    Assessment,
    AssessmentMark,
    AssessmentStatus,
)
from apps.assessments.domain.invariants import (
    validate_mark_entry,
    validate_assessment_lock,
    validate_duplicate_entries,
)
from apps.academic.models import AcademicYear, Semester, Department, Program, SchemeSubject, Batch
from apps.students.models import Student, StudentEnrollment
from apps.faculty.models import Faculty, FacultyAssignment
from apps.faculty.services.faculty_scope_service import FacultyScopeService
from common.exceptions import InvariantViolationError


class AssessmentService:
    """Core domain service orchestrating assessment creation, mark imports, and publication."""

    @classmethod
    @transaction.atomic
    def create_assessment_type(
        cls,
        code: str,
        name: str,
        description: str = '',
        is_active: bool = True
    ) -> AssessmentType:
        return AssessmentType.objects.create(
            code=code.strip().upper(),
            name=name.strip(),
            description=description,
            is_active=is_active
        )

    @classmethod
    @transaction.atomic
    def create_assessment(
        cls,
        title: str,
        assessment_type: AssessmentType,
        academic_year: AcademicYear,
        semester: Semester,
        department: Department,
        scheme_subject: SchemeSubject,
        max_marks: Decimal = Decimal('25.00'),
        passing_marks: Decimal = Decimal('10.00'),
        program: Optional[Program] = None,
        batch: Optional[Batch] = None,
        faculty_assignment: Optional[FacultyAssignment] = None,
        assessment_date=None,
        actor=None
    ) -> Assessment:
        """Creates an assessment definition connected to academic foundation and faculty assignment."""
        return Assessment.objects.create(
            title=title,
            assessment_type=assessment_type,
            academic_year=academic_year,
            semester=semester,
            department=department,
            program=program,
            scheme_subject=scheme_subject,
            batch=batch,
            faculty_assignment=faculty_assignment,
            max_marks=max_marks,
            passing_marks=passing_marks,
            assessment_date=assessment_date,
            status=AssessmentStatus.DRAFT,
            created_by=actor
        )

    @classmethod
    @transaction.atomic
    def upload_unit_test_marks(
        cls,
        assessment_id: str,
        mark_rows: List[Dict[str, Any]],
        actor=None
    ) -> Dict[str, Any]:
        """
        Extracts, validates, and persists unit test marks uploaded by faculty.
        Enforces:
        - Faculty assignment & scoped student visibility
        - Locked assessment protection
        - In-file duplicate entry detection
        - Range and absence validity
        - Student enrollment verification
        - Concurrency-safe atomic persistence
        """
        assessment = Assessment.objects.select_for_update().get(id=assessment_id)
        validate_assessment_lock(assessment.is_locked)

        # 1. Authorize faculty scope
        if actor and not actor.is_superuser:
            # Check if actor is the assigned faculty or HOD of the department
            is_hod = Faculty.objects.filter(user=actor, department=assessment.department, is_hod=True).exists()
            is_assigned = False
            if assessment.faculty_assignment and assessment.faculty_assignment.faculty.user_id == actor.id:
                is_assigned = True
            elif FacultyAssignment.objects.filter(
                faculty__user=actor,
                scheme_subject=assessment.scheme_subject,
                academic_year=assessment.academic_year,
                is_active=True
            ).exists():
                is_assigned = True

            if not is_hod and not is_assigned:
                raise PermissionDenied("You do not have authorized teaching scope for this subject assessment.")

        # 2. Duplicate detection in upload rows
        identifiers = [
            str(r.get('enrollment_no') or r.get('application_id') or r.get('student_id', '')).strip()
            for r in mark_rows
            if str(r.get('enrollment_no') or r.get('application_id') or r.get('student_id', '')).strip()
        ]
        validate_duplicate_entries(identifiers)

        # 3. Extraction, validation & persistence
        created_count = 0
        updated_count = 0

        for row in mark_rows:
            ident = str(row.get('enrollment_no') or row.get('application_id') or row.get('student_id', '')).strip()
            if not ident:
                raise InvariantViolationError("Each row must provide a student enrollment number or ID.")

            student = Student.objects.filter(
                Q(enrollment_no=ident) | Q(application_id=ident)
            ).first()

            if not student:
                try:
                    import uuid
                    uuid_val = uuid.UUID(ident)
                    student = Student.objects.filter(id=uuid_val).first()
                except (ValueError, TypeError):
                    pass

            if not student:
                raise InvariantViolationError(f"Student with identifier '{ident}' does not exist in college records.")

            # Validate enrollment in assessment context
            enrollment = StudentEnrollment.objects.filter(
                student=student,
                academic_year=assessment.academic_year,
                semester=assessment.semester
            ).first()

            is_absent = bool(row.get('is_absent', False))
            marks_raw = row.get('marks_obtained')

            marks_dec = None
            if not is_absent:
                if marks_raw is None or marks_raw == '':
                    raise InvariantViolationError(f"Marks obtained is required for present student {ident}.")
                marks_dec = Decimal(str(marks_raw))

            # Validate mark entry invariant
            validate_mark_entry(
                marks_obtained=marks_dec,
                max_marks=assessment.max_marks,
                is_absent=is_absent
            )

            # Persist mark record
            mark_obj, created = AssessmentMark.objects.update_or_create(
                assessment=assessment,
                student=student,
                defaults={
                    'enrollment': enrollment,
                    'marks_obtained': marks_dec,
                    'is_absent': is_absent,
                    'remarks': row.get('remarks', ''),
                    'entered_by': actor
                }
            )

            if created:
                created_count += 1
            else:
                updated_count += 1

        return {
            'assessment_id': str(assessment.id),
            'assessment_title': assessment.title,
            'total_processed': len(mark_rows),
            'created_marks': created_count,
            'updated_marks': updated_count,
        }

    @classmethod
    @transaction.atomic
    def publish_assessment(cls, assessment_id: str, actor=None) -> Assessment:
        """Transitions assessment to PUBLISHED state so marks become visible to students."""
        assessment = Assessment.objects.select_for_update().get(id=assessment_id)
        validate_assessment_lock(assessment.is_locked)
        assessment.status = AssessmentStatus.PUBLISHED
        assessment.published_at = timezone.now()
        assessment.save(update_fields=['status', 'published_at'])
        return assessment

    @classmethod
    @transaction.atomic
    def lock_assessment(cls, assessment_id: str, actor=None) -> Assessment:
        """Permanently locks assessment marks against any further modifications."""
        assessment = Assessment.objects.select_for_update().get(id=assessment_id)
        assessment.status = AssessmentStatus.LOCKED
        assessment.locked_at = timezone.now()
        assessment.save(update_fields=['status', 'locked_at'])
        return assessment

    @classmethod
    def get_student_marks(cls, student_user) -> List[AssessmentMark]:
        """Returns published/locked marks for a student's own record."""
        student = getattr(student_user, 'student_profile', None)
        if not student:
            return []

        return list(AssessmentMark.objects.filter(
            student=student,
            assessment__status__in=[AssessmentStatus.PUBLISHED, AssessmentStatus.LOCKED]
        ).select_related(
            'assessment',
            'assessment__assessment_type',
            'assessment__scheme_subject__subject',
            'assessment__academic_year',
            'assessment__semester'
        ).order_by('-assessment__academic_year__start_date', '-created_at'))
