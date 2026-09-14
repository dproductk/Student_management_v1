from rest_framework import serializers
from apps.results.models import (
    ResultImportBatch,
    ResultImportRow,
    StudentResult,
    StudentResultDetail,
    ResultCorrectionRequest,
    ResultCorrectionAudit,
    StudentCredit,
    EligibilityRule,
    EligibilityDecision,
    NextYearEligibilityList,
)


class ResultImportRowSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()

    class Meta:
        model = ResultImportRow
        fields = [
            'id',
            'batch',
            'row_number',
            'raw_data',
            'student_identifier',
            'matched_student',
            'student_name',
            'subject_code',
            'matched_scheme_subject',
            'internal_marks',
            'external_marks',
            'total_marks',
            'grade',
            'grade_points',
            'is_absent',
            'status',
            'validation_errors',
            'created_at',
        ]
        read_only_fields = fields

    def get_student_name(self, obj):
        if obj.matched_student:
            return getattr(obj.matched_student, 'candidate_name', '')
        return None


class ResultImportBatchSerializer(serializers.ModelSerializer):
    academic_year_name = serializers.CharField(source='academic_year.label', read_only=True)
    semester_number = serializers.IntegerField(source='semester.number', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    program_name = serializers.CharField(source='program.name', read_only=True)
    uploaded_by_username = serializers.CharField(source='uploaded_by.username', read_only=True)
    approved_by_username = serializers.CharField(source='approved_by.username', read_only=True)
    published_by_username = serializers.CharField(source='published_by.username', read_only=True)

    class Meta:
        model = ResultImportBatch
        fields = [
            'id',
            'academic_year',
            'academic_year_name',
            'semester',
            'semester_number',
            'department',
            'department_name',
            'program',
            'program_name',
            'file_name',
            'file_path',
            'status',
            'total_rows',
            'valid_rows',
            'error_rows',
            'uploaded_by',
            'uploaded_by_username',
            'approved_by',
            'approved_by_username',
            'approved_at',
            'published_by',
            'published_by_username',
            'published_at',
            'remarks',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'status',
            'total_rows',
            'valid_rows',
            'error_rows',
            'uploaded_by',
            'approved_by',
            'approved_at',
            'published_by',
            'published_at',
            'created_at',
            'updated_at',
        ]


class UploadResultBatchSerializer(serializers.Serializer):
    academic_year = serializers.UUIDField()
    semester = serializers.UUIDField()
    department = serializers.UUIDField()
    program = serializers.UUIDField()
    file_name = serializers.CharField(max_length=255, default="results_upload.csv")
    csv_content = serializers.CharField(required=False, allow_blank=True)
    file = serializers.FileField(required=False)
    remarks = serializers.CharField(required=False, allow_blank=True, default="")


class StudentResultDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentResultDetail
        fields = [
            'id',
            'scheme_subject',
            'subject_code',
            'subject_name',
            'internal_marks',
            'external_marks',
            'total_marks',
            'max_marks',
            'grade',
            'grade_points',
            'credits_earned',
            'is_absent',
            'status',
        ]
        read_only_fields = fields


class StudentResultSerializer(serializers.ModelSerializer):
    student_enrollment_no = serializers.CharField(source='student.enrollment_no', read_only=True)
    student_name = serializers.SerializerMethodField()
    academic_year_name = serializers.CharField(source='academic_year.label', read_only=True)
    semester_number = serializers.IntegerField(source='semester.number', read_only=True)
    details = StudentResultDetailSerializer(many=True, read_only=True)

    class Meta:
        model = StudentResult
        fields = [
            'id',
            'student',
            'student_enrollment_no',
            'student_name',
            'academic_year',
            'academic_year_name',
            'semester',
            'semester_number',
            'batch',
            'version',
            'is_latest',
            'superseded_by',
            'status',
            'total_marks_obtained',
            'total_max_marks',
            'percentage',
            'sgpa',
            'cgpa',
            'result_status',
            'import_batch',
            'published_at',
            'created_at',
            'details',
        ]
        read_only_fields = fields

    def get_student_name(self, obj):
        if obj.student:
            return getattr(obj.student, 'candidate_name', '')
        return ""


class ResultCorrectionRequestSerializer(serializers.ModelSerializer):
    student_enrollment_no = serializers.CharField(source='target_result.student.enrollment_no', read_only=True)
    target_version = serializers.IntegerField(source='target_result.version', read_only=True)
    requested_by_username = serializers.CharField(source='requested_by.username', read_only=True)
    reviewed_by_username = serializers.CharField(source='reviewed_by.username', read_only=True)

    class Meta:
        model = ResultCorrectionRequest
        fields = [
            'id',
            'target_result',
            'student_enrollment_no',
            'target_version',
            'requested_by',
            'requested_by_username',
            'reason',
            'proposed_changes',
            'status',
            'reviewed_by',
            'reviewed_by_username',
            'reviewed_at',
            'review_remarks',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'requested_by',
            'reviewed_by',
            'reviewed_at',
            'created_at',
            'updated_at',
        ]


class ResultCorrectionAuditSerializer(serializers.ModelSerializer):
    actor_username = serializers.CharField(source='actor.username', read_only=True)

    class Meta:
        model = ResultCorrectionAudit
        fields = [
            'id',
            'original_result',
            'superseding_result',
            'correction_request',
            'actor',
            'actor_username',
            'action',
            'reason',
            'timestamp',
        ]
        read_only_fields = fields


class StudentCreditSerializer(serializers.ModelSerializer):
    student_enrollment_no = serializers.CharField(source='student.enrollment_no', read_only=True)
    student_name = serializers.CharField(source='student.candidate_name', read_only=True)
    academic_year_name = serializers.CharField(source='academic_year.label', read_only=True)
    semester_number = serializers.IntegerField(source='semester.number', read_only=True)
    calculated_by_username = serializers.CharField(source='calculated_by.username', read_only=True)

    class Meta:
        model = StudentCredit
        fields = [
            'id',
            'student',
            'student_enrollment_no',
            'student_name',
            'academic_year',
            'academic_year_name',
            'semester',
            'semester_number',
            'result',
            'result_version',
            'credits_attempted',
            'credits_earned',
            'sgpa',
            'cgpa',
            'cumulative_credits_earned',
            'backlogs_count',
            'version',
            'is_latest',
            'calculated_by',
            'calculated_by_username',
            'calculated_at',
        ]
        read_only_fields = [
            'id',
            'result_version',
            'sgpa',
            'cgpa',
            'cumulative_credits_earned',
            'backlogs_count',
            'version',
            'is_latest',
            'calculated_by',
            'calculated_at',
        ]


class EligibilityRuleSerializer(serializers.ModelSerializer):
    academic_year_name = serializers.CharField(source='academic_year.label', read_only=True)
    program_name = serializers.CharField(source='program.name', read_only=True)
    program_code = serializers.CharField(source='program.code', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = EligibilityRule
        fields = [
            'id',
            'name',
            'code',
            'academic_year',
            'academic_year_name',
            'program',
            'program_name',
            'program_code',
            'target_semester',
            'version',
            'min_credits_required',
            'min_attendance_percentage',
            'max_backlogs_allowed',
            'detention_max_backlogs',
            'detention_min_attendance',
            'is_active',
            'created_by',
            'created_by_username',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'version', 'created_by', 'created_at', 'updated_at']


class EligibilityDecisionSerializer(serializers.ModelSerializer):
    student_enrollment_no = serializers.CharField(source='student.enrollment_no', read_only=True)
    student_name = serializers.CharField(source='student.candidate_name', read_only=True)
    academic_year_name = serializers.CharField(source='academic_year.label', read_only=True)
    semester_number = serializers.IntegerField(source='semester.number', read_only=True)
    rule_code = serializers.CharField(source='rule.code', read_only=True)
    rule_name = serializers.CharField(source='rule.name', read_only=True)
    decided_by_username = serializers.CharField(source='decided_by.username', read_only=True)

    class Meta:
        model = EligibilityDecision
        fields = [
            'id',
            'student',
            'student_enrollment_no',
            'student_name',
            'academic_year',
            'academic_year_name',
            'semester',
            'semester_number',
            'rule',
            'rule_code',
            'rule_name',
            'rule_version',
            'credits_earned',
            'credits_attempted',
            'backlogs_count',
            'attendance_percentage',
            'decision',
            'detention_reason',
            'remarks',
            'version',
            'is_latest',
            'superseded_by',
            'decided_by',
            'decided_by_username',
            'decided_at',
        ]
        read_only_fields = [
            'id',
            'rule_version',
            'credits_earned',
            'credits_attempted',
            'backlogs_count',
            'version',
            'is_latest',
            'superseded_by',
            'decided_by',
            'decided_at',
        ]


class NextYearEligibilityListSerializer(serializers.ModelSerializer):
    academic_year_name = serializers.CharField(source='academic_year.label', read_only=True)
    semester_number = serializers.IntegerField(source='semester.number', read_only=True)
    target_academic_year_name = serializers.CharField(source='target_academic_year.label', read_only=True)
    program_name = serializers.CharField(source='program.name', read_only=True)
    program_code = serializers.CharField(source='program.code', read_only=True)
    generated_by_username = serializers.CharField(source='generated_by.username', read_only=True)

    class Meta:
        model = NextYearEligibilityList
        fields = [
            'id',
            'academic_year',
            'academic_year_name',
            'semester',
            'semester_number',
            'target_academic_year',
            'target_academic_year_name',
            'target_semester_number',
            'program',
            'program_name',
            'program_code',
            'total_students',
            'eligible_count',
            'not_eligible_count',
            'detained_count',
            'items',
            'generated_by',
            'generated_by_username',
            'generated_at',
        ]
        read_only_fields = fields
