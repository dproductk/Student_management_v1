"""
API Views for Administrative Register & Dashboards.
"""

from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status

from apps.register.services.register_query_service import RegisterQueryService
from apps.register.services.dashboard_service import DashboardService
from apps.register.services.export_service import RegisterExportService
from apps.register.api.serializers import (
    RegisterQueryResponseSerializer,
    DashboardSummarySerializer,
)


class StudentRegisterView(APIView):
    """
    GET /api/v1/register/students/
    Returns filtered and paginated student register data.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        filters = {
            'search': request.query_params.get('search'),
            'department': request.query_params.get('department'),
            'program': request.query_params.get('program'),
            'academic_year': request.query_params.get('academic_year'),
            'batch': request.query_params.get('batch'),
            'category': request.query_params.get('category'),
            'gender': request.query_params.get('gender'),
            'status': request.query_params.get('status'),
            'verification_status': request.query_params.get('verification_status'),
        }
        limit = request.query_params.get('limit', 50)
        offset = request.query_params.get('offset', 0)

        data = RegisterQueryService.query_student_register(
            user=request.user,
            filters=filters,
            limit=limit,
            offset=offset
        )
        serializer = RegisterQueryResponseSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AdministrativeDashboardView(APIView):
    """
    GET /api/v1/register/dashboard/
    Returns student-status and administrative distribution metrics.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        department_id = request.query_params.get('department')
        academic_year_id = request.query_params.get('academic_year')

        data = DashboardService.get_dashboard_summary(
            user=request.user,
            department_id=department_id,
            academic_year_id=academic_year_id
        )
        serializer = DashboardSummarySerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RegisterExportView(APIView):
    """
    GET /api/v1/register/export/
    Generates bounded CSV export file based on current filter criteria.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        filters = {
            'search': request.query_params.get('search'),
            'department': request.query_params.get('department'),
            'program': request.query_params.get('program'),
            'academic_year': request.query_params.get('academic_year'),
            'batch': request.query_params.get('batch'),
            'category': request.query_params.get('category'),
            'gender': request.query_params.get('gender'),
            'status': request.query_params.get('status'),
            'verification_status': request.query_params.get('verification_status'),
        }

        csv_content = RegisterExportService.export_register_csv(
            user=request.user,
            filters=filters
        )

        response = HttpResponse(csv_content, content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="student_administrative_register.csv"'
        return response
