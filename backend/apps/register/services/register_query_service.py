"""
Register Query Service.
Implements Task 8.1, 8.2, 8.3:
- 8.1 Administrative student register query
- 8.2 Department/program/year/batch student register filtering
- 8.3 Category/gender/verification administrative register views
Per ARCHITECTURE.md: Operates as a read capability consuming authoritative data without duplicate tables.
"""

from typing import Dict, Any, List, Optional
from django.db.models import Q, QuerySet
from apps.students.models import Student, StudentEnrollment
from apps.faculty.services.faculty_scope_service import FacultyScopeService
from apps.verification.models import VerificationRequest


class RegisterQueryService:
    """Read-oriented administrative service for student register search, filters, and projections."""

    @classmethod
    def get_base_scoped_queryset(cls, user) -> QuerySet:
        """
        Returns the base student queryset filtered by user's authorized scope.
        """
        if not user or not user.is_authenticated:
            return Student.objects.none()
        
        # Scoped authorization enforcement
        return FacultyScopeService.get_scoped_students_queryset(user)

    @classmethod
    def query_student_register(
        cls,
        user,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Queries and projects authoritative student register data with academic and administrative filters.
        Enforces pagination bounds and server-side authorization.
        """
        filters = filters or {}
        limit = min(max(int(limit), 1), 100)  # bounded between 1 and 100
        offset = max(int(offset), 0)

        qs = cls.get_base_scoped_queryset(user)

        # 1. Search filter
        search = filters.get('search')
        if search:
            search = search.strip()
            qs = qs.filter(
                Q(candidate_name__icontains=search) |
                Q(enrollment_no__icontains=search) |
                Q(application_id__icontains=search) |
                Q(email__icontains=search)
            )

        # 2. Academic filters (Task 8.2)
        department_id = filters.get('department')
        if department_id:
            qs = qs.filter(enrollments__department_id=department_id)

        program_id = filters.get('program')
        if program_id:
            qs = qs.filter(enrollments__program_id=program_id)

        academic_year_id = filters.get('academic_year')
        if academic_year_id:
            qs = qs.filter(enrollments__academic_year_id=academic_year_id)

        batch_id = filters.get('batch')
        if batch_id:
            qs = qs.filter(enrollments__batch_id=batch_id)

        # 3. Administrative filters (Task 8.3)
        category = filters.get('category')
        if category:
            qs = qs.filter(category_info__category=category)

        gender = filters.get('gender')
        if gender:
            qs = qs.filter(gender=gender)

        student_status = filters.get('status')
        if student_status:
            qs = qs.filter(status=student_status)

        verification_status = filters.get('verification_status')
        if verification_status:
            if verification_status == 'UNSUBMITTED':
                qs = qs.filter(verification_requests__isnull=True)
            else:
                qs = qs.filter(verification_requests__status=verification_status)

        qs = qs.distinct().prefetch_related(
            'enrollments__department',
            'enrollments__program',
            'enrollments__batch',
            'enrollments__academic_year',
            'enrollments__semester',
            'category_info',
            'verification_requests'
        ).order_by('candidate_name')

        total_count = qs.count()
        page_results = qs[offset:offset + limit]

        # Build clean projection list
        projected = []
        for s in page_results:
            latest_enrollment = s.enrollments.order_by('-created_at').first()
            latest_verif = s.verification_requests.order_by('-submitted_at').first()

            # Determine overall verification status
            if not latest_verif:
                computed_verif = 'UNSUBMITTED'
            else:
                all_statuses = set(s.verification_requests.values_list('status', flat=True))
                if 'NEEDS_CORRECTION' in all_statuses:
                    computed_verif = 'NEEDS_CORRECTION'
                elif 'REJECTED' in all_statuses:
                    computed_verif = 'REJECTED'
                elif 'PENDING' in all_statuses:
                    computed_verif = 'PENDING'
                elif 'APPROVED' in all_statuses:
                    computed_verif = 'APPROVED'
                else:
                    computed_verif = latest_verif.status

            projected.append({
                'id': str(s.id),
                'candidate_name': s.candidate_name,
                'enrollment_no': s.enrollment_no,
                'application_id': s.application_id,
                'gender': s.gender,
                'date_of_birth': str(s.date_of_birth) if s.date_of_birth else None,
                'email': s.email,
                'student_mobile': s.student_mobile,
                'status': s.status,
                'category': s.category_info.category if hasattr(s, 'category_info') and s.category_info else 'N/A',
                'caste': s.category_info.caste if hasattr(s, 'category_info') and s.category_info else None,
                'department_code': latest_enrollment.department.code if latest_enrollment and latest_enrollment.department else None,
                'department_name': latest_enrollment.department.name if latest_enrollment and latest_enrollment.department else None,
                'program_code': latest_enrollment.program.code if latest_enrollment and latest_enrollment.program else None,
                'batch_name': latest_enrollment.batch.name if latest_enrollment and latest_enrollment.batch else None,
                'academic_year': latest_enrollment.academic_year.label if latest_enrollment and latest_enrollment.academic_year else None,
                'semester_number': latest_enrollment.semester.number if latest_enrollment and latest_enrollment.semester else None,
                'verification_status': computed_verif,
                # Sensitive identity protection (masked only)
                'aadhaar_masked': s.aadhaar_masked or 'Not Provided',
                'created_at': s.created_at.isoformat() if s.created_at else None,
            })

        return {
            'total_count': total_count,
            'limit': limit,
            'offset': offset,
            'results': projected
        }
