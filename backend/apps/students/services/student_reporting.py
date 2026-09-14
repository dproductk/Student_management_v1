"""
Student Management Reporting Query Interface.

Implements Task 14.1.2: Student Management reporting interface vertical slice.
Exposes authoritative, read-only query contracts for student populations,
demographics, and enrollments without allowing external direct ORM mutation.
"""
from typing import Dict, Any, Optional, List
from django.db.models import Count, Q
from apps.students.models import Student, StudentEnrollment, StudentCategory


class StudentReportingQueryService:
    """Read-only reporting query interface owned by apps.students."""

    @staticmethod
    def get_population_summary(filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Calculates authoritative aggregate student counts."""
        filters = filters or {}
        qs = Student.objects.all()

        if filters.get('gender'):
            qs = qs.filter(gender=filters['gender'])
        if filters.get('status'):
            qs = qs.filter(status=filters['status'])

        total = qs.count()
        active = qs.filter(status='ACTIVE').count()
        detained = qs.filter(status='DETAINED').count()
        passed_out = qs.filter(status='PASSED_OUT').count()
        dropped = qs.filter(status='DROPPED').count()

        # Enrolled count in current/selected academic year if provided
        enrollments_qs = StudentEnrollment.objects.filter(status='ACTIVE')
        if filters.get('academic_year_id'):
            enrollments_qs = enrollments_qs.filter(academic_year_id=filters['academic_year_id'])
        if filters.get('department_id'):
            enrollments_qs = enrollments_qs.filter(department_id=filters['department_id'])
        if filters.get('program_id'):
            enrollments_qs = enrollments_qs.filter(program_id=filters['program_id'])

        total_enrolled = enrollments_qs.values('student_id').distinct().count()

        return {
            'total_students': total,
            'active_students': active,
            'detained_students': detained,
            'passed_out_students': passed_out,
            'dropped_students': dropped,
            'total_enrolled': total_enrolled,
        }

    @staticmethod
    def get_demographics_breakdown(filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Calculates multi-dimensional breakdown across gender, category, department, program, batch."""
        filters = filters or {}

        # 1. Gender distribution
        gender_qs = Student.objects.all()
        if filters.get('department_id') or filters.get('academic_year_id') or filters.get('batch_id'):
            enrollment_filter = Q(enrollments__status='ACTIVE')
            if filters.get('department_id'):
                enrollment_filter &= Q(enrollments__department_id=filters['department_id'])
            if filters.get('academic_year_id'):
                enrollment_filter &= Q(enrollments__academic_year_id=filters['academic_year_id'])
            if filters.get('batch_id'):
                enrollment_filter &= Q(enrollments__batch_id=filters['batch_id'])
            gender_qs = gender_qs.filter(enrollment_filter).distinct()

        gender_counts = list(
            gender_qs.values('gender')
            .annotate(count=Count('id'))
            .order_by('gender')
        )

        # 2. Category distribution
        category_qs = StudentCategory.objects.all()
        if filters.get('department_id') or filters.get('academic_year_id'):
            c_filter = Q(student__enrollments__status='ACTIVE')
            if filters.get('department_id'):
                c_filter &= Q(student__enrollments__department_id=filters['department_id'])
            if filters.get('academic_year_id'):
                c_filter &= Q(student__enrollments__academic_year_id=filters['academic_year_id'])
            category_qs = category_qs.filter(c_filter).distinct()

        category_counts = list(
            category_qs.values('category')
            .annotate(count=Count('student_id', distinct=True))
            .order_by('category')
        )

        # 3. Department distribution
        enrollment_qs = StudentEnrollment.objects.filter(status='ACTIVE')
        if filters.get('academic_year_id'):
            enrollment_qs = enrollment_qs.filter(academic_year_id=filters['academic_year_id'])

        dept_counts = list(
            enrollment_qs.values('department__name', 'department__code')
            .annotate(count=Count('student_id', distinct=True))
            .order_by('department__name')
        )

        # 4. Program distribution
        program_counts = list(
            enrollment_qs.values('program__name', 'program__code')
            .annotate(count=Count('student_id', distinct=True))
            .order_by('program__name')
        )

        # 5. Batch distribution
        batch_counts = list(
            enrollment_qs.values('batch__name')
            .annotate(count=Count('student_id', distinct=True))
            .order_by('batch__name')
        )

        return {
            'by_gender': gender_counts,
            'by_category': category_counts,
            'by_department': dept_counts,
            'by_program': program_counts,
            'by_batch': batch_counts,
        }

    @staticmethod
    def get_student_reporting_records(
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 50,
        offset: int = 0,
        ordering: Optional[str] = '-created_at'
    ) -> Dict[str, Any]:
        """Provides a paginated, bounded query for tabular student reports."""
        filters = filters or {}
        qs = Student.objects.select_related('user').prefetch_related(
            'enrollments__department',
            'enrollments__program',
            'enrollments__batch',
            'enrollments__semester'
        ).all()

        if filters.get('gender'):
            qs = qs.filter(gender=filters['gender'])
        if filters.get('status'):
            qs = qs.filter(status=filters['status'])
        if filters.get('department_id'):
            qs = qs.filter(enrollments__department_id=filters['department_id'], enrollments__status='ACTIVE')
        if filters.get('program_id'):
            qs = qs.filter(enrollments__program_id=filters['program_id'], enrollments__status='ACTIVE')
        if filters.get('academic_year_id'):
            qs = qs.filter(enrollments__academic_year_id=filters['academic_year_id'], enrollments__status='ACTIVE')
        if filters.get('batch_id'):
            qs = qs.filter(enrollments__batch_id=filters['batch_id'], enrollments__status='ACTIVE')
        if filters.get('search'):
            s = filters['search']
            qs = qs.filter(
                Q(candidate_name__icontains=s) |
                Q(enrollment_no__icontains=s) |
                Q(application_id__icontains=s)
            )

        qs = qs.distinct()
        total_count = qs.count()

        if ordering:
            qs = qs.order_by(ordering)

        records = []
        for s in qs[offset:offset + limit]:
            active_enr = next((e for e in s.enrollments.all() if e.status == 'ACTIVE'), None)
            records.append({
                'id': str(s.id),
                'candidate_name': s.candidate_name,
                'enrollment_no': s.enrollment_no or '',
                'application_id': s.application_id or '',
                'gender': s.gender,
                'status': s.status,
                'aadhaar_masked': s.aadhaar_masked or '',
                'department_name': active_enr.department.name if active_enr and active_enr.department else '',
                'program_name': active_enr.program.name if active_enr and active_enr.program else '',
                'batch_name': active_enr.batch.name if active_enr and active_enr.batch else '',
                'semester_number': active_enr.semester.number if active_enr and active_enr.semester else None,
            })

        return {
            'total_count': total_count,
            'limit': limit,
            'offset': offset,
            'records': records,
        }
