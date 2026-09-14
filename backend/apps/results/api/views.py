from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from apps.results.models import (
    ResultImportBatch,
    ResultImportRow,
    StudentResult,
    ResultCorrectionRequest,
    ResultCorrectionAudit,
    StudentCredit,
    EligibilityRule,
    EligibilityDecision,
    NextYearEligibilityList,
)
from apps.results.api.serializers import (
    ResultImportBatchSerializer,
    ResultImportRowSerializer,
    UploadResultBatchSerializer,
    StudentResultSerializer,
    ResultCorrectionRequestSerializer,
    ResultCorrectionAuditSerializer,
    StudentCreditSerializer,
    EligibilityRuleSerializer,
    EligibilityDecisionSerializer,
    NextYearEligibilityListSerializer,
)
from apps.results.services.result_service import ResultService
from apps.results.services.credit_eligibility_service import CreditEligibilityService
from apps.results.domain.invariants import (
    ResultValidationError,
    ResultImmutabilityViolation,
    InvalidLifecycleTransitionError,
    CreditCalculationError,
    EligibilityValidationError,
)
from apps.academic.models import AcademicYear, Semester, Program
from apps.students.models import Student


class ResultImportBatchViewSet(viewsets.ModelViewSet):
    queryset = ResultImportBatch.objects.all().select_related(
        'academic_year', 'semester', 'department', 'program', 'uploaded_by', 'approved_by', 'published_by'
    )
    serializer_class = ResultImportBatchSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['post'], url_path='upload')
    def upload_batch(self, request):
        """Uploads a CSV/Excel file or raw CSV text and creates batch + staging rows."""
        serializer = UploadResultBatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        csv_content = data.get('csv_content', '')
        file_obj = data.get('file')

        if file_obj:
            try:
                csv_content = file_obj.read().decode('utf-8', errors='replace')
            except Exception as e:
                return Response({'detail': f"Failed to read uploaded file: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        if not csv_content or not csv_content.strip():
            return Response({'detail': "No CSV content or file provided."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            batch = ResultService.create_import_batch(
                academic_year_id=str(data['academic_year']),
                semester_id=str(data['semester']),
                department_id=str(data['department']),
                program_id=str(data['program']),
                file_name=data.get('file_name', getattr(file_obj, 'name', 'results_upload.csv')),
                uploaded_by=request.user,
                remarks=data.get('remarks', '')
            )

            rows_data = ResultService.parse_csv_content(csv_content)
            if not rows_data:
                batch.status = 'FAILED'
                batch.remarks = "Empty or invalid CSV headers."
                batch.save()
                return Response({'detail': "No valid data rows found in CSV."}, status=status.HTTP_400_BAD_REQUEST)

            ResultService.extract_and_stage_rows(batch, rows_data)
            return Response(ResultImportBatchSerializer(batch).data, status=status.HTTP_201_CREATED)
        except (ResultValidationError, InvalidLifecycleTransitionError) as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='validate')
    def validate_batch(self, request, pk=None):
        """Triggers validation and student/subject matching for all staging rows in the batch."""
        batch = self.get_object()
        try:
            result = ResultService.validate_and_associate_rows(batch)
            batch.refresh_from_db()
            return Response({
                'batch': ResultImportBatchSerializer(batch).data,
                'summary': result
            }, status=status.HTTP_200_OK if result['success'] else status.HTTP_400_BAD_REQUEST)
        except (ResultValidationError, InvalidLifecycleTransitionError) as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='approve')
    def approve_batch(self, request, pk=None):
        """Accountable actor approves the validated batch."""
        batch = self.get_object()
        try:
            approved_batch = ResultService.approve_result_batch(batch, request.user)
            return Response(ResultImportBatchSerializer(approved_batch).data, status=status.HTTP_200_OK)
        except (ResultValidationError, InvalidLifecycleTransitionError) as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='publish')
    def publish_batch(self, request, pk=None):
        """Publishes the approved batch making marks visible to students."""
        batch = self.get_object()
        try:
            published_batch = ResultService.publish_result_batch(batch, request.user)
            return Response(ResultImportBatchSerializer(published_batch).data, status=status.HTTP_200_OK)
        except (ResultValidationError, InvalidLifecycleTransitionError) as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], url_path='rows')
    def list_rows(self, request, pk=None):
        """Lists staging rows with validation outcomes."""
        batch = self.get_object()
        rows = batch.rows.all().select_related('matched_student', 'matched_scheme_subject__subject').order_by('row_number')
        return Response(ResultImportRowSerializer(rows, many=True).data)


class StudentResultViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StudentResult.objects.all().select_related(
        'student', 'academic_year', 'semester', 'batch'
    ).prefetch_related('details').order_by('-academic_year__start_date', 'semester__number', 'student__enrollment_no')
    serializer_class = StudentResultSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        student_id = self.request.query_params.get('student_id')
        enrollment_no = self.request.query_params.get('enrollment_no')
        academic_year = self.request.query_params.get('academic_year')
        semester = self.request.query_params.get('semester')
        status_filter = self.request.query_params.get('status')
        latest_only = self.request.query_params.get('latest_only')

        if student_id:
            qs = qs.filter(student_id=student_id)
        if enrollment_no:
            qs = qs.filter(student__enrollment_no__iexact=enrollment_no)
        if academic_year:
            qs = qs.filter(academic_year_id=academic_year)
        if semester:
            qs = qs.filter(semester_id=semester)
        if status_filter:
            qs = qs.filter(status=status_filter)
        if latest_only in ('true', '1', True):
            qs = qs.filter(is_latest=True)

        return qs


class StudentResultSelfView(APIView):
    """Scoped endpoint for logged-in students to view their own published results."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        # Find matching student record by username or linked student
        from apps.students.models import Student
        student = Student.objects.filter(enrollment_no=user.username).first()
        if not student:
            # Check if user has related student
            student = getattr(user, 'student_profile', None)

        if not student:
            # Fallback: check query parameter if student_id or enrollment_no provided
            student_id = request.query_params.get('student_id')
            enrollment_no = request.query_params.get('enrollment_no')
            if student_id:
                student = Student.objects.filter(id=student_id).first()
            elif enrollment_no:
                student = Student.objects.filter(enrollment_no__iexact=enrollment_no).first()

        if not student:
            return Response([], status=status.HTTP_200_OK)

        results = ResultService.get_student_published_results(
            student=student,
            academic_year_id=request.query_params.get('academic_year'),
            semester_id=request.query_params.get('semester')
        )
        return Response(StudentResultSerializer(results, many=True).data)


class ResultCorrectionRequestViewSet(viewsets.ModelViewSet):
    queryset = ResultCorrectionRequest.objects.all().select_related(
        'target_result__student', 'requested_by', 'reviewed_by'
    )
    serializer_class = ResultCorrectionRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        target_result_id = self.request.data.get('target_result')
        target_result = get_object_or_404(StudentResult, id=target_result_id)
        reason = self.request.data.get('reason', '')
        proposed_changes = self.request.data.get('proposed_changes', {})

        correction_req = ResultService.request_result_correction(
            target_result=target_result,
            requested_by=self.request.user,
            reason=reason,
            proposed_changes=proposed_changes
        )
        serializer.instance = correction_req

    @action(detail=True, methods=['post'], url_path='review')
    def review_request(self, request, pk=None):
        """Authorized reviewer approves or rejects the correction request."""
        correction_req = self.get_object()
        approved = bool(request.data.get('approved', False))
        remarks = request.data.get('review_remarks', '')

        try:
            updated_req = ResultService.review_result_correction(
                correction_request=correction_req,
                reviewer=request.user,
                approved=approved,
                review_remarks=remarks
            )
            return Response(ResultCorrectionRequestSerializer(updated_req).data, status=status.HTTP_200_OK)
        except (ResultValidationError, InvalidLifecycleTransitionError) as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ResultCorrectionAuditViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ResultCorrectionAudit.objects.all().select_related(
        'original_result__student', 'superseding_result__student', 'actor'
    )
    serializer_class = ResultCorrectionAuditSerializer
    permission_classes = [permissions.IsAuthenticated]


class StudentCreditViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only and calculation operations for student semester credits.
    """
    queryset = StudentCredit.objects.all().select_related(
        'student', 'academic_year', 'semester', 'result', 'calculated_by'
    )
    serializer_class = StudentCreditSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        student_id = self.request.query_params.get('student')
        academic_year_id = self.request.query_params.get('academic_year')
        semester_id = self.request.query_params.get('semester')
        is_latest = self.request.query_params.get('is_latest')

        if student_id:
            qs = qs.filter(student_id=student_id)
        if academic_year_id:
            qs = qs.filter(academic_year_id=academic_year_id)
        if semester_id:
            qs = qs.filter(semester_id=semester_id)
        if is_latest is not None:
            qs = qs.filter(is_latest=is_latest.lower() in ('true', '1'))

        return qs

    @action(detail=False, methods=['post'], url_path='calculate')
    def calculate_credits(self, request):
        """Calculates credits for a specific result or an entire batch."""
        result_id = request.data.get('result_id')
        batch_id = request.data.get('batch_id')

        try:
            if result_id:
                res = get_object_or_404(StudentResult, id=result_id)
                credit = CreditEligibilityService.calculate_credits_for_result(res, user=request.user)
                return Response(StudentCreditSerializer(credit).data, status=status.HTTP_200_OK)
            elif batch_id:
                batch = get_object_or_404(ResultImportBatch, id=batch_id)
                credits = CreditEligibilityService.calculate_batch_credits(batch, user=request.user)
                return Response(
                    StudentCreditSerializer(credits, many=True).data,
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {'detail': 'Either result_id or batch_id must be provided.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except (CreditCalculationError, ResultValidationError) as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class EligibilityRuleViewSet(viewsets.ModelViewSet):
    """
    CRUD management for configurable institutional eligibility rules.
    """
    queryset = EligibilityRule.objects.all().select_related(
        'academic_year', 'program', 'created_by'
    )
    serializer_class = EligibilityRuleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        program_id = self.request.query_params.get('program')
        academic_year_id = self.request.query_params.get('academic_year')
        is_active = self.request.query_params.get('is_active')

        if program_id:
            qs = qs.filter(program_id=program_id)
        if academic_year_id:
            qs = qs.filter(academic_year_id=academic_year_id)
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() in ('true', '1'))

        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'], url_path='create-version')
    def create_new_version(self, request, pk=None):
        """Creates an updated version of the rule without breaking past decisions."""
        rule = self.get_object()
        from decimal import Decimal
        try:
            new_rule = CreditEligibilityService.create_or_version_rule(
                name=request.data.get('name', rule.name),
                code=rule.code,
                min_credits=Decimal(str(request.data.get('min_credits_required', rule.min_credits_required))),
                min_attendance=Decimal(str(request.data.get('min_attendance_percentage', rule.min_attendance_percentage))),
                max_backlogs=int(request.data.get('max_backlogs_allowed', rule.max_backlogs_allowed)),
                detention_max_backlogs=int(request.data.get('detention_max_backlogs', rule.detention_max_backlogs)),
                detention_min_attendance=Decimal(str(request.data.get('detention_min_attendance', rule.detention_min_attendance))),
                program_id=request.data.get('program', rule.program_id),
                academic_year_id=request.data.get('academic_year', rule.academic_year_id),
                target_semester=request.data.get('target_semester', rule.target_semester),
                user=request.user
            )
            return Response(EligibilityRuleSerializer(new_rule).data, status=status.HTTP_201_CREATED)
        except (EligibilityValidationError, ValueError) as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class EligibilityDecisionViewSet(viewsets.ModelViewSet):
    """
    Manages and queries student eligibility decisions.
    """
    queryset = EligibilityDecision.objects.all().select_related(
        'student', 'academic_year', 'semester', 'rule', 'decided_by'
    )
    serializer_class = EligibilityDecisionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        student_id = self.request.query_params.get('student')
        academic_year_id = self.request.query_params.get('academic_year')
        semester_id = self.request.query_params.get('semester')
        decision = self.request.query_params.get('decision')
        is_latest = self.request.query_params.get('is_latest')

        if student_id:
            qs = qs.filter(student_id=student_id)
        if academic_year_id:
            qs = qs.filter(academic_year_id=academic_year_id)
        if semester_id:
            qs = qs.filter(semester_id=semester_id)
        if decision:
            qs = qs.filter(decision=decision.upper())
        if is_latest is not None:
            qs = qs.filter(is_latest=is_latest.lower() in ('true', '1'))

        return qs

    @action(detail=False, methods=['post'], url_path='evaluate')
    def evaluate_student(self, request):
        """Evaluates single student eligibility."""
        student_id = request.data.get('student')
        academic_year_id = request.data.get('academic_year')
        semester_id = request.data.get('semester')
        rule_id = request.data.get('rule')
        attendance = request.data.get('attendance_percentage', '100.00')

        if not student_id or not academic_year_id or not semester_id:
            return Response(
                {'detail': 'student, academic_year, and semester are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        student = get_object_or_404(Student, id=student_id)
        academic_year = get_object_or_404(AcademicYear, id=academic_year_id)
        semester = get_object_or_404(Semester, id=semester_id)
        rule = get_object_or_404(EligibilityRule, id=rule_id) if rule_id else None

        from decimal import Decimal
        try:
            decision = CreditEligibilityService.evaluate_student_eligibility(
                student=student,
                academic_year=academic_year,
                semester=semester,
                rule=rule,
                attendance_percentage=Decimal(str(attendance)),
                user=request.user
            )
            return Response(EligibilityDecisionSerializer(decision).data, status=status.HTTP_201_CREATED)
        except (EligibilityValidationError, ValueError) as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='evaluate-cohort')
    def evaluate_cohort(self, request):
        """Evaluates eligibility for all students enrolled in a cohort."""
        academic_year_id = request.data.get('academic_year')
        semester_id = request.data.get('semester')
        program_id = request.data.get('program')
        rule_id = request.data.get('rule')

        if not academic_year_id or not semester_id:
            return Response(
                {'detail': 'academic_year and semester are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        academic_year = get_object_or_404(AcademicYear, id=academic_year_id)
        semester = get_object_or_404(Semester, id=semester_id)
        program = get_object_or_404(Program, id=program_id) if program_id else None
        rule = get_object_or_404(EligibilityRule, id=rule_id) if rule_id else None

        try:
            decisions = CreditEligibilityService.evaluate_cohort_eligibility(
                academic_year=academic_year,
                semester=semester,
                program=program,
                rule=rule,
                user=request.user
            )
            return Response(
                EligibilityDecisionSerializer(decisions, many=True).data,
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class NextYearEligibilityListViewSet(viewsets.ReadOnlyModelViewSet):
    """
    View and generate snapshots of official Next-Year Promotion Lists.
    """
    queryset = NextYearEligibilityList.objects.all().select_related(
        'academic_year', 'semester', 'target_academic_year', 'program', 'generated_by'
    )
    serializer_class = NextYearEligibilityListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        program_id = self.request.query_params.get('program')
        academic_year_id = self.request.query_params.get('academic_year')
        semester_id = self.request.query_params.get('semester')

        if program_id:
            qs = qs.filter(program_id=program_id)
        if academic_year_id:
            qs = qs.filter(academic_year_id=academic_year_id)
        if semester_id:
            qs = qs.filter(semester_id=semester_id)

        return qs

    @action(detail=False, methods=['post'], url_path='generate')
    def generate_list(self, request):
        """Generates the official promotion list snapshot for next-year admission."""
        academic_year_id = request.data.get('academic_year')
        semester_id = request.data.get('semester')
        program_id = request.data.get('program')
        target_ay_id = request.data.get('target_academic_year')
        target_sem_num = request.data.get('target_semester_number')

        if not academic_year_id or not semester_id or not program_id:
            return Response(
                {'detail': 'academic_year, semester, and program are mandatory.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        academic_year = get_object_or_404(AcademicYear, id=academic_year_id)
        semester = get_object_or_404(Semester, id=semester_id)
        program = get_object_or_404(Program, id=program_id)
        target_ay = get_object_or_404(AcademicYear, id=target_ay_id) if target_ay_id else None
        target_sem = int(target_sem_num) if target_sem_num else None

        try:
            promotion_list = CreditEligibilityService.generate_next_year_eligibility_list(
                academic_year=academic_year,
                semester=semester,
                program=program,
                target_academic_year=target_ay,
                target_semester_number=target_sem,
                user=request.user
            )
            return Response(
                NextYearEligibilityListSerializer(promotion_list).data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
