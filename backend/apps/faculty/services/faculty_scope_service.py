"""
Faculty Scoped Student Visibility Service.
Implements Task 7.2.3: Faculty/HOD/Class Teacher scoped student visibility.
Ensures backend enforcement so that student access is strictly governed by authorized
academic assignments and institutional roles.
"""

from typing import Optional, Set
from django.db.models import QuerySet, Q
from apps.students.models import Student, StudentEnrollment
from apps.faculty.models import Faculty, FacultyAssignment, AssignmentRole
from apps.identity.models import User, UserRole
from apps.identity.domain.rbac import RoleScopeType


class FacultyScopeService:
    """Evaluates and enforces scoped student visibility for faculty, HOD, and class teachers."""

    @classmethod
    def get_scoped_students_queryset(
        cls,
        user: User,
        base_queryset: Optional[QuerySet] = None
    ) -> QuerySet:
        """
        Returns a QuerySet of Student instances visible to the requesting user.
        Enforces backend scoping rules:
        - Superuser / SYSTEM role: All students
        - HOD / Department-scoped role: Students enrolled in the Department
        - Class Teacher / Batch-scoped role: Students enrolled in the assigned Batch
        - Subject Faculty: Students enrolled in the batches where the faculty has active teaching assignments
        """
        qs = base_queryset if base_queryset is not None else Student.objects.all()

        if not user or not user.is_authenticated:
            return qs.none()

        if user.is_superuser:
            return qs

        # Check for system-wide student view permission
        has_system_scope = UserRole.objects.filter(
            user=user,
            role__scope_type=RoleScopeType.SYSTEM.value,
            role__role_permissions__permission__codename='students.view_record'
        ).exists()
        if has_system_scope:
            return qs

        faculty = getattr(user, 'faculty_profile', None)
        
        department_ids: Set[str] = set()
        batch_ids: Set[str] = set()

        # 1. Department-level scope (from UserRole or Faculty.is_hod)
        dept_roles = UserRole.objects.filter(
            user=user,
            role__scope_type=RoleScopeType.DEPARTMENT.value,
            role__role_permissions__permission__codename='students.view_record'
        )
        for r in dept_roles:
            if r.scope_department_id:
                department_ids.add(str(r.scope_department_id))

        if faculty and faculty.is_hod and faculty.department_id:
            department_ids.add(str(faculty.department_id))

        # 2. Batch-level scope (from UserRole or Class Teacher assignments or Active Subject assignments)
        batch_roles = UserRole.objects.filter(
            user=user,
            role__scope_type=RoleScopeType.BATCH.value,
            role__role_permissions__permission__codename='students.view_record'
        )
        for r in batch_roles:
            if r.scope_batch_id:
                batch_ids.add(str(r.scope_batch_id))

        if faculty:
            # Check teaching assignments
            active_assignments = FacultyAssignment.objects.filter(
                faculty=faculty,
                is_active=True
            ).select_related('batch')

            for a in active_assignments:
                if a.batch_id:
                    batch_ids.add(str(a.batch_id))

        # If user has neither department nor batch scope, deny access
        if not department_ids and not batch_ids:
            return qs.none()

        # Build filter criteria based on authoritative StudentEnrollment
        q_filter = Q()
        if department_ids:
            q_filter |= Q(enrollments__department_id__in=department_ids)
        if batch_ids:
            q_filter |= Q(enrollments__batch_id__in=batch_ids)

        return qs.filter(q_filter).distinct()

    @classmethod
    def can_user_view_student(cls, user: User, student: Student) -> bool:
        """
        Determines if a single student record is visible to the given user.
        """
        return cls.get_scoped_students_queryset(user).filter(id=student.id).exists()
