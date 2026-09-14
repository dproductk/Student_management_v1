"""
DRF Serializers for Assessments & Unit Test Marks module.
"""

from decimal import Decimal
from rest_framework import serializers
from apps.assessments.models import (
    AssessmentType,
    Assessment,
    AssessmentMark,
    AssessmentStatus,
)


class AssessmentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssessmentType
        fields = ['id', 'code', 'name', 'description', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class AssessmentMarkSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.candidate_name', read_only=True)
    enrollment_no = serializers.CharField(source='student.enrollment_no', read_only=True)
    application_id = serializers.CharField(source='student.application_id', read_only=True)
    entered_by_name = serializers.CharField(source='entered_by.username', read_only=True, default='')

    class Meta:
        model = AssessmentMark
        fields = [
            'id',
            'assessment',
            'student',
            'student_name',
            'enrollment_no',
            'application_id',
            'enrollment',
            'marks_obtained',
            'is_absent',
            'remarks',
            'entered_by',
            'entered_by_name',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'entered_by', 'entered_by_name']


class AssessmentSerializer(serializers.ModelSerializer):
    assessment_type_name = serializers.CharField(source='assessment_type.name', read_only=True)
    assessment_type_code = serializers.CharField(source='assessment_type.code', read_only=True)
    academic_year_label = serializers.CharField(source='academic_year.label', read_only=True)
    semester_label = serializers.CharField(source='semester.label', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    program_name = serializers.CharField(source='program.name', read_only=True, default='')
    subject_name = serializers.CharField(source='scheme_subject.subject.name', read_only=True)
    subject_code = serializers.CharField(source='scheme_subject.subject.code', read_only=True)
    batch_name = serializers.CharField(source='batch.name', read_only=True, default='')
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, default='')
    marks_count = serializers.SerializerMethodField()

    class Meta:
        model = Assessment
        fields = [
            'id',
            'title',
            'assessment_type',
            'assessment_type_name',
            'assessment_type_code',
            'academic_year',
            'academic_year_label',
            'semester',
            'semester_label',
            'department',
            'department_name',
            'program',
            'program_name',
            'scheme_subject',
            'subject_name',
            'subject_code',
            'batch',
            'batch_name',
            'faculty_assignment',
            'max_marks',
            'passing_marks',
            'assessment_date',
            'status',
            'created_by',
            'created_by_name',
            'published_at',
            'locked_at',
            'marks_count',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id',
            'status',
            'published_at',
            'locked_at',
            'created_by',
            'created_by_name',
            'marks_count',
            'created_at',
            'updated_at'
        ]

    def get_marks_count(self, obj):
        return obj.marks.count()


class MarkRowUploadSerializer(serializers.Serializer):
    enrollment_no = serializers.CharField(required=False, allow_blank=True)
    application_id = serializers.CharField(required=False, allow_blank=True)
    student_id = serializers.CharField(required=False, allow_blank=True)
    marks_obtained = serializers.DecimalField(max_digits=6, decimal_places=2, required=False, allow_null=True)
    is_absent = serializers.BooleanField(required=False, default=False)
    remarks = serializers.CharField(required=False, allow_blank=True, default='')


class UploadUnitTestMarksSerializer(serializers.Serializer):
    marks = MarkRowUploadSerializer(many=True, required=True)


class StudentMarkViewSerializer(serializers.ModelSerializer):
    assessment_title = serializers.CharField(source='assessment.title', read_only=True)
    assessment_type = serializers.CharField(source='assessment.assessment_type.name', read_only=True)
    subject_code = serializers.CharField(source='assessment.scheme_subject.subject.code', read_only=True)
    subject_name = serializers.CharField(source='assessment.scheme_subject.subject.name', read_only=True)
    max_marks = serializers.DecimalField(source='assessment.max_marks', max_digits=6, decimal_places=2, read_only=True)
    passing_marks = serializers.DecimalField(source='assessment.passing_marks', max_digits=6, decimal_places=2, read_only=True)
    academic_year = serializers.CharField(source='assessment.academic_year.label', read_only=True)
    semester = serializers.CharField(source='assessment.semester.label', read_only=True)

    class Meta:
        model = AssessmentMark
        fields = [
            'id',
            'assessment_title',
            'assessment_type',
            'subject_code',
            'subject_name',
            'academic_year',
            'semester',
            'marks_obtained',
            'max_marks',
            'passing_marks',
            'is_absent',
            'remarks',
            'updated_at'
        ]
