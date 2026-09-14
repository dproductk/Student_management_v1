"""
API Views and ViewSets for Faculty bounded context.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.faculty.models import Faculty, FacultyAssignment, FacultyAcademicItem
from apps.faculty.api.serializers import (
    FacultyListSerializer,
    FacultyDetailSerializer,
    FacultyCreateUpdateSerializer,
    FacultyAssignmentSerializer,
    FacultyAcademicItemSerializer,
)
from apps.faculty.services.faculty_service import FacultyService
from apps.faculty.services.faculty_scope_service import FacultyScopeService
from apps.students.api.serializers import StudentListSerializer
from common.exceptions import InvariantViolationError


class FacultyViewSet(viewsets.ModelViewSet):
    """
    CRUD for Faculty records and organizational lifecycle management.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Faculty.objects.select_related('department').prefetch_related('assignments', 'academic_items').all()
        dept_id = self.request.query_params.get('department')
        status_filter = self.request.query_params.get('status')
        emp_type = self.request.query_params.get('employment_type')
        is_hod = self.request.query_params.get('is_hod')
        search = self.request.query_params.get('search')

        if dept_id:
            qs = qs.filter(department_id=dept_id)
        if status_filter:
            qs = qs.filter(status=status_filter)
        if emp_type:
            qs = qs.filter(employment_type=emp_type)
        if is_hod is not None:
            qs = qs.filter(is_hod=is_hod.lower() in ('true', '1'))
        if search:
            from django.db.models import Q
            qs = qs.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(faculty_id__icontains=search) |
                Q(email__icontains=search)
            )
        return qs

    def get_serializer_class(self):
        if self.action == 'list':
            return FacultyListSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return FacultyCreateUpdateSerializer
        return FacultyDetailSerializer

    def perform_create(self, serializer):
        faculty = serializer.save(created_by=self.request.user, updated_by=self.request.user)
        # Auto-provision login User + dept-scoped role so HOD/Faculty can sign in immediately.
        # Username = faculty_id, default password = Edvana@2026.
        try:
            from apps.identity.models import User, Role, UserRole
            from apps.identity.domain.rbac import CANONICAL_ROLES
            username = (faculty.faculty_id or '').strip()
            if username and not faculty.user_id:
                user = User.objects.filter(username=username).first()
                if not user:
                    user = User.objects.create_user(
                        username=username,
                        password='Edvana@2026',
                        email=faculty.email or None,
                        is_staff=True,
                        is_superuser=False,
                        must_change_password=False,
                        status='ACTIVE',
                    )
                faculty.user = user
                faculty.save(update_fields=['user'])
                role_name = 'HOD' if faculty.is_hod else 'FACULTY'
                role, _ = Role.objects.get_or_create(
                    name=role_name,
                    defaults={
                        'scope_type': 'DEPARTMENT',
                        'description': CANONICAL_ROLES.get(role_name, {}).get('description', role_name),
                    },
                )
                UserRole.objects.get_or_create(
                    user=user,
                    role=role,
                    scope_department_id=faculty.department_id,
                    scope_batch_id=None,
                    defaults={'assigned_by': self.request.user},
                )
        except Exception:
            import logging
            logging.getLogger(__name__).exception('Faculty auto-provision login failed')

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    @action(detail=True, methods=['post'], url_path='transition-status')
    def transition_status(self, request, pk=None):
        faculty = self.get_object()
        new_status = request.data.get('status')
        relieving_date = request.data.get('relieving_date')

        if not new_status:
            return Response({'detail': 'New status is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            updated = FacultyService.transition_status(
                faculty=faculty,
                new_status=new_status,
                relieving_date=relieving_date,
                actor=request.user
            )
            return Response(FacultyDetailSerializer(updated).data)
        except InvariantViolationError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], url_path='assignments')
    def assignments(self, request, pk=None):
        faculty = self.get_object()
        assignments = faculty.assignments.select_related(
            'academic_year', 'semester', 'scheme_subject__subject', 'batch'
        ).all()
        serializer = FacultyAssignmentSerializer(assignments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get', 'post'], url_path='academic-items')
    def academic_items(self, request, pk=None):
        faculty = self.get_object()
        if request.method == 'GET':
            items = faculty.academic_items.all()
            serializer = FacultyAcademicItemSerializer(items, many=True)
            return Response(serializer.data)
        
        # POST - add item
        serializer = FacultyAcademicItemSerializer(data={**request.data, 'faculty': faculty.id})
        serializer.is_valid(raise_exception=True)
        try:
            item = FacultyService.add_academic_item(
                faculty=faculty,
                item_type=serializer.validated_data['item_type'],
                title=serializer.validated_data['title'],
                year=serializer.validated_data.get('year'),
                details=serializer.validated_data.get('details', {}),
                reference_url=serializer.validated_data.get('reference_url', ''),
                actor=request.user
            )
            return Response(FacultyAcademicItemSerializer(item).data, status=status.HTTP_201_CREATED)
        except InvariantViolationError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class FacultyAssignmentViewSet(viewsets.ModelViewSet):
    """
    CRUD and historical tracking for faculty teaching assignments.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FacultyAssignmentSerializer

    def get_queryset(self):
        qs = FacultyAssignment.objects.select_related(
            'faculty', 'academic_year', 'semester', 'scheme_subject__subject', 'batch'
        ).all()
        faculty_id = self.request.query_params.get('faculty')
        year_id = self.request.query_params.get('academic_year')
        semester_id = self.request.query_params.get('semester')
        batch_id = self.request.query_params.get('batch')
        role = self.request.query_params.get('role')
        is_active = self.request.query_params.get('is_active')

        if faculty_id:
            qs = qs.filter(faculty_id=faculty_id)
        if year_id:
            qs = qs.filter(academic_year_id=year_id)
        if semester_id:
            qs = qs.filter(semester_id=semester_id)
        if batch_id:
            qs = qs.filter(batch_id=batch_id)
        if role:
            qs = qs.filter(role=role)
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() in ('true', '1'))

        return qs

    def perform_create(self, serializer):
        serializer.save(assigned_by=self.request.user)

    @action(detail=True, methods=['post'], url_path='retire')
    def retire(self, request, pk=None):
        assignment = self.get_object()
        end_date = request.data.get('end_date')
        try:
            retired = FacultyService.retire_assignment(assignment, end_date=end_date, actor=request.user)
            return Response(FacultyAssignmentSerializer(retired).data)
        except InvariantViolationError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class FacultyAcademicItemViewSet(viewsets.ModelViewSet):
    """
    CRUD for faculty portfolio items (publications, patents, awards, etc.).
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FacultyAcademicItemSerializer

    def get_queryset(self):
        qs = FacultyAcademicItem.objects.select_related('faculty').all()
        faculty_id = self.request.query_params.get('faculty')
        item_type = self.request.query_params.get('item_type')
        year = self.request.query_params.get('year')

        if faculty_id:
            qs = qs.filter(faculty_id=faculty_id)
        if item_type:
            qs = qs.filter(item_type=item_type)
        if year:
            qs = qs.filter(year=year)

        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class FacultyScopedStudentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Implements Task 7.2.3: Scoped student visibility for Faculty/HOD/Class Teacher.
    Returns only the students visible to the currently authenticated user based on
    their authorized academic assignments and roles.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = StudentListSerializer

    def get_queryset(self):
        return FacultyScopeService.get_scoped_students_queryset(self.request.user)
