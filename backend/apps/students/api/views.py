"""
API Views and ViewSets for Student Management.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from apps.students.models import Student, StudentDataCorrection
from apps.students.api.serializers import (
    StudentListSerializer,
    StudentDetailSerializer,
    StudentCorrectionSerializer,
    SensitiveRevealRequestSerializer,
    CorrectionRequestSerializer,
    StudentBankAccountSerializer,
    StudentEnrollmentSerializer,
)
from apps.students.api.permissions import CanViewStudents, CanManageStudents
from apps.students.services.student_service import StudentService
from apps.students.services.correction_service import CorrectionService


class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.prefetch_related(
        'enrollments__batch',
        'enrollments__department',
        'enrollments__program',
        'enrollments__semester',
        'enrollments__academic_year',
        'admissions__program',
        'corrections__approved_by'
    ).select_related('address', 'category_info', 'bank_account', 'user').all()
    permission_classes = [CanViewStudents]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['candidate_name', 'enrollment_no', 'application_id', 'email', 'student_mobile', 'user__username']
    ordering_fields = ['candidate_name', 'created_at', 'enrollment_no']

    def get_serializer_class(self):
        if self.action in ['retrieve', 'update', 'partial_update']:
            return StudentDetailSerializer
        return StudentListSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        status_param = self.request.query_params.get('status')
        dept_id = self.request.query_params.get('department')
        batch_id = self.request.query_params.get('batch')
        gender_param = self.request.query_params.get('gender')
        division_param = self.request.query_params.get('division')
        has_login_param = self.request.query_params.get('has_login')

        if status_param:
            qs = qs.filter(status=status_param.strip().upper())
        if dept_id:
            qs = qs.filter(enrollments__department_id=dept_id)
        if batch_id:
            qs = qs.filter(enrollments__batch_id=batch_id)
        if gender_param:
            qs = qs.filter(gender__iexact=gender_param.strip())
        if division_param:
            qs = qs.filter(enrollments__division__iexact=division_param.strip())
        if has_login_param is not None and str(has_login_param).strip() != '':
            val = str(has_login_param).strip().lower()
            if val in ('true', '1', 'yes'):
                qs = qs.filter(user__isnull=False)
            elif val in ('false', '0', 'no'):
                qs = qs.filter(user__isnull=True)

        # Enforce HOD/Faculty department scoping so e.g. a CSE HOD
        # never sees COMP students, even with ?department= or no filter.
        # SysAdmin / CollegeAdmin / superuser bypass and see all.
        user = self.request.user
        try:
            if getattr(user, 'is_superuser', False):
                return qs.distinct()
            from apps.identity.models import UserRole
            if UserRole.objects.filter(user=user, role__name__in=['SYSTEM_ADMIN', 'COLLEGE_ADMIN']).exists():
                return qs.distinct()
            faculty = getattr(user, 'faculty_profile', None)
            has_dept_role = UserRole.objects.filter(user=user, role__name__in=['HOD', 'FACULTY']).exists()
            if faculty is not None or has_dept_role:
                from apps.faculty.services.faculty_scope_service import FacultyScopeService
                return FacultyScopeService.get_scoped_students_queryset(user, base_queryset=qs).distinct()
        except Exception:
            pass

        return qs.distinct()

    def create(self, request, *args, **kwargs):
        if not CanManageStudents().has_permission(request, self):
            return Response(
                {"detail": "You do not possess permission to create student records."},
                status=status.HTTP_403_FORBIDDEN
            )
        data = request.data
        student = StudentService.create_student(
            candidate_name=data.get('candidate_name', ''),
            gender=data.get('gender', ''),
            date_of_birth=data.get('date_of_birth'),
            enrollment_no=data.get('enrollment_no'),
            application_id=data.get('application_id'),
            board_enrollment_no=data.get('board_enrollment_no'),
            student_mobile=data.get('student_mobile'),
            parent_mobile=data.get('parent_mobile'),
            email=data.get('email'),
            religion=data.get('religion'),
            mother_tongue=data.get('mother_tongue'),
            candidature_type=data.get('candidature_type'),
            aadhaar_number=data.get('aadhaar_number'),
            created_by=request.user
        )
        serializer = StudentDetailSerializer(student)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='reveal-sensitive')
    def reveal_sensitive(self, request, pk=None):
        """Audited sensitive data reveal endpoint (ADR-015)."""
        serializer = SensitiveRevealRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        field_name = serializer.validated_data['field_name']
        reason = serializer.validated_data['reason']
        ip_addr = request.META.get('REMOTE_ADDR')

        cleartext = StudentService.reveal_sensitive_field(
            student_id=pk,
            field_name=field_name,
            requesting_user=request.user,
            reason=reason,
            ip_address=ip_addr
        )
        return Response({'field_name': field_name, 'value': cleartext}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='corrections')
    def submit_correction(self, request, pk=None):
        """Additive correction endpoint for government-sourced data (ADR-007)."""
        if not CanManageStudents().has_permission(request, self):
            return Response(
                {"detail": "You do not possess permission to apply corrections."},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = CorrectionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        corr = CorrectionService.apply_student_correction(
            student_id=pk,
            field_name=serializer.validated_data['field_name'],
            new_value=serializer.validated_data['new_value'],
            reason=serializer.validated_data['reason'],
            approver_user=request.user
        )
        return Response(StudentCorrectionSerializer(corr).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='bank-account')
    def update_bank_account(self, request, pk=None):
        if not CanManageStudents().has_permission(request, self):
            return Response(
                {"detail": "You do not possess permission to manage student bank accounts."},
                status=status.HTTP_403_FORBIDDEN
            )
        data = request.data
        bank_acc = StudentService.set_bank_account(
            student_id=pk,
            account_number=data.get('account_number'),
            bank_name=data.get('bank_name'),
            branch_name=data.get('branch_name'),
            ifsc_code=data.get('ifsc_code'),
            account_holder_name=data.get('account_holder_name')
        )
        return Response(StudentBankAccountSerializer(bank_acc).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='enroll')
    def enroll_semester(self, request, pk=None):
        if not CanManageStudents().has_permission(request, self):
            return Response(
                {"detail": "You do not possess permission to enroll students."},
                status=status.HTTP_403_FORBIDDEN
            )
        data = request.data
        enrollment = StudentService.enroll_student(
            student_id=pk,
            academic_year_id=data.get('academic_year'),
            semester_id=data.get('semester'),
            department_id=data.get('department'),
            program_id=data.get('program'),
            batch_id=data.get('batch'),
            scheme_id=data.get('scheme'),
            created_by=request.user
        )
        # Allow setting division alongside enrollment
        division = (data.get('division') or '').strip().upper()
        if division and enrollment.division != division:
            enrollment.division = division
            enrollment.save(update_fields=['division'])
        return Response(StudentEnrollmentSerializer(enrollment).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post', 'patch'], url_path='set-division')
    def set_division(self, request, pk=None):
        """HOD/Admin: persist class division on latest (or specified) enrollment."""
        if not CanManageStudents().has_permission(request, self):
            return Response(
                {"detail": "You do not possess permission to manage divisions."},
                status=status.HTTP_403_FORBIDDEN
            )
        from apps.students.models import Student
        try:
            student = Student.objects.get(id=pk)
        except Student.DoesNotExist:
            return Response({"detail": "Student not found."}, status=status.HTTP_404_NOT_FOUND)
        division = (request.data.get('division') or '').strip().upper()
        if not division:
            return Response({"detail": "division is required (e.g. A, B)."}, status=status.HTTP_400_BAD_REQUEST)
        enrollment_id = request.data.get('enrollment_id')
        if enrollment_id:
            enrollment = student.enrollments.filter(id=enrollment_id).first()
        else:
            enrollment = student.enrollments.order_by('-created_at').first()
        if not enrollment:
            return Response({"detail": "Student has no enrollment yet. Import/enroll first."}, status=status.HTTP_400_BAD_REQUEST)
        enrollment.division = division
        enrollment.save(update_fields=['division'])
        return Response(StudentEnrollmentSerializer(enrollment).data)


class StudentCorrectionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StudentDataCorrection.objects.select_related('student', 'approved_by').all()
    serializer_class = StudentCorrectionSerializer
    permission_classes = [CanViewStudents]
    filter_backends = [SearchFilter]
    search_fields = ['student__candidate_name', 'field_name', 'correction_reason']
