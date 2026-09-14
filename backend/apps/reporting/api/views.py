"""
Reporting & Analytics API Views.

Exposes read-only analytics summaries and bounded CSV report downloads.
Requires authentication and enforces scoped permissions.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from apps.reporting.services.analytics_service import ReportingAnalyticsService
from apps.reporting.services.export_service import ReportingExportService
from apps.reporting.domain.contracts import ReportingValidationError


class BaseReportingAPIView(APIView):
    """Base API view enforcing authentication and extracting query filters."""
    permission_classes = [permissions.IsAuthenticated]

    def get_filters(self, request):
        return {
            'academic_year_id': request.query_params.get('academic_year_id'),
            'department_id': request.query_params.get('department_id'),
            'program_id': request.query_params.get('program_id'),
            'batch_id': request.query_params.get('batch_id'),
            'category_code': request.query_params.get('category_code'),
            'gender': request.query_params.get('gender'),
            'status': request.query_params.get('status'),
            'search': request.query_params.get('search'),
        }


class ExecutiveKPIView(BaseReportingAPIView):
    def get(self, request):
        filters = self.get_filters(request)
        data = ReportingAnalyticsService.get_executive_kpis(filters)
        return Response(data)


class StudentPopulationAnalyticsView(BaseReportingAPIView):
    def get(self, request):
        filters = self.get_filters(request)
        data = ReportingAnalyticsService.get_student_population_analytics(filters)
        return Response(data)


class DemographicsAnalyticsView(BaseReportingAPIView):
    def get(self, request):
        filters = self.get_filters(request)
        data = ReportingAnalyticsService.get_demographics_analytics(filters)
        return Response(data)


class VerificationAnalyticsView(BaseReportingAPIView):
    def get(self, request):
        filters = self.get_filters(request)
        data = ReportingAnalyticsService.get_verification_analytics(filters)
        return Response(data)


class FeeStatusAnalyticsView(BaseReportingAPIView):
    def get(self, request):
        filters = self.get_filters(request)
        data = ReportingAnalyticsService.get_fee_status_analytics(filters)
        return Response(data)


class AcademicAnalyticsView(BaseReportingAPIView):
    def get(self, request):
        filters = self.get_filters(request)
        data = ReportingAnalyticsService.get_academic_results_analytics(filters)
        return Response(data)


class UserActivityAnalyticsView(BaseReportingAPIView):
    def get(self, request):
        filters = self.get_filters(request)
        data = ReportingAnalyticsService.get_user_activity_analytics(filters)
        return Response(data)


class ReportExportView(BaseReportingAPIView):
    def get(self, request):
        report_type = request.query_params.get('type', 'students')
        limit = int(request.query_params.get('limit', 1000))
        filters = self.get_filters(request)

        try:
            return ReportingExportService.export_dataset_to_csv(
                report_type=report_type,
                filters=filters,
                limit=limit
            )
        except ReportingValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
