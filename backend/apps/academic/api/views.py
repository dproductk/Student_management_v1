"""
API Views and ViewSets for Academic Foundation module.
"""

from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from apps.academic.models import (
    Department,
    Program,
    AcademicYear,
    Semester,
    Batch,
    DepartmentIntake,
    Scheme,
    Subject,
    SchemeSubject,
)
from apps.academic.api.serializers import (
    DepartmentSerializer,
    ProgramSerializer,
    AcademicYearSerializer,
    SemesterSerializer,
    BatchSerializer,
    DepartmentIntakeSerializer,
    SchemeSerializer,
    SubjectSerializer,
    SchemeSubjectSerializer,
)
from apps.academic.api.permissions import CanManageAcademicStructure, CanManageCurriculum
from apps.academic.services.academic_service import AcademicService


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [CanManageAcademicStructure]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'code']
    ordering_fields = ['name', 'code', 'created_at']


class ProgramViewSet(viewsets.ModelViewSet):
    queryset = Program.objects.select_related('department').all()
    serializer_class = ProgramSerializer
    permission_classes = [CanManageAcademicStructure]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'code', 'degree_type']
    ordering_fields = ['name', 'code', 'duration_years']

    def get_queryset(self):
        qs = super().get_queryset()
        dept_id = self.request.query_params.get('department')
        if dept_id:
            qs = qs.filter(department_id=dept_id)
        return qs


class AcademicYearViewSet(viewsets.ModelViewSet):
    queryset = AcademicYear.objects.prefetch_related('semesters').all()
    serializer_class = AcademicYearSerializer
    permission_classes = [CanManageAcademicStructure]
    ordering_fields = ['start_date', 'label']


class SemesterViewSet(viewsets.ModelViewSet):
    queryset = Semester.objects.select_related('academic_year').all()
    serializer_class = SemesterSerializer
    permission_classes = [CanManageAcademicStructure]

    def get_queryset(self):
        qs = super().get_queryset()
        ay_id = self.request.query_params.get('academic_year')
        if ay_id:
            qs = qs.filter(academic_year_id=ay_id)
        return qs


class BatchViewSet(viewsets.ModelViewSet):
    queryset = Batch.objects.select_related('department', 'academic_year').all()
    serializer_class = BatchSerializer
    permission_classes = [CanManageAcademicStructure]
    search_fields = ['name']

    def get_queryset(self):
        qs = super().get_queryset()
        dept_id = self.request.query_params.get('department')
        ay_id = self.request.query_params.get('academic_year')
        if dept_id:
            qs = qs.filter(department_id=dept_id)
        if ay_id:
            qs = qs.filter(academic_year_id=ay_id)
        return qs


class DepartmentIntakeViewSet(viewsets.ModelViewSet):
    queryset = DepartmentIntake.objects.select_related('department', 'academic_year', 'program').all()
    serializer_class = DepartmentIntakeSerializer
    permission_classes = [CanManageAcademicStructure]

    def get_queryset(self):
        qs = super().get_queryset()
        dept_id = self.request.query_params.get('department')
        ay_id = self.request.query_params.get('academic_year')
        if dept_id:
            qs = qs.filter(department_id=dept_id)
        if ay_id:
            qs = qs.filter(academic_year_id=ay_id)
        return qs


class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [CanManageCurriculum]
    filter_backends = [SearchFilter]
    search_fields = ['name', 'code']


class SchemeViewSet(viewsets.ModelViewSet):
    queryset = Scheme.objects.select_related('program', 'effective_from_year').prefetch_related('scheme_subjects__subject').all()
    serializer_class = SchemeSerializer
    permission_classes = [CanManageCurriculum]
    search_fields = ['name', 'code']

    def get_queryset(self):
        qs = super().get_queryset()
        prog_id = self.request.query_params.get('program')
        if prog_id:
            qs = qs.filter(program_id=prog_id)
        return qs


class SchemeSubjectViewSet(viewsets.ModelViewSet):
    queryset = SchemeSubject.objects.select_related('scheme', 'subject').all()
    serializer_class = SchemeSubjectSerializer
    permission_classes = [CanManageCurriculum]

    def get_queryset(self):
        qs = super().get_queryset()
        scheme_id = self.request.query_params.get('scheme')
        sem = self.request.query_params.get('semester')
        if scheme_id:
            qs = qs.filter(scheme_id=scheme_id)
        if sem:
            qs = qs.filter(semester_number=sem)
        return qs


class AcademicMasterSearchAPIView(APIView):
    """
    Unified academic search and filter endpoint across departments, programs,
    schemes, subjects, and batches.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        q = request.query_params.get('q', '')
        dept_id = request.query_params.get('department')
        ay_id = request.query_params.get('academic_year')
        results = AcademicService.search_master_data(query=q, department_id=dept_id, academic_year_id=ay_id)
        return Response(results, status=status.HTTP_200_OK)
