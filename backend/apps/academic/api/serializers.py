"""
DRF Serializers for Academic Foundation entities.
"""

from rest_framework import serializers
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


class DepartmentSerializer(serializers.ModelSerializer):
    program_count = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = ['id', 'name', 'code', 'is_active', 'choice_codes', 'program_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_program_count(self, obj):
        return obj.programs.count()


class ProgramSerializer(serializers.ModelSerializer):
    department_name = serializers.ReadOnlyField(source='department.name')
    department_code = serializers.ReadOnlyField(source='department.code')

    class Meta:
        model = Program
        fields = [
            'id', 'department', 'department_name', 'department_code',
            'name', 'code', 'duration_years', 'degree_type', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SemesterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Semester
        fields = ['id', 'academic_year', 'number', 'label', 'start_date', 'end_date', 'created_at']
        read_only_fields = ['id', 'created_at']


class AcademicYearSerializer(serializers.ModelSerializer):
    semesters = SemesterSerializer(many=True, read_only=True)

    class Meta:
        model = AcademicYear
        fields = ['id', 'label', 'start_date', 'end_date', 'is_current', 'semesters', 'created_at']
        read_only_fields = ['id', 'created_at']


class BatchSerializer(serializers.ModelSerializer):
    department_name = serializers.ReadOnlyField(source='department.name')
    department_code = serializers.ReadOnlyField(source='department.code')
    academic_year_label = serializers.ReadOnlyField(source='academic_year.label')

    class Meta:
        model = Batch
        fields = [
            'id', 'department', 'department_name', 'department_code',
            'name', 'academic_year', 'academic_year_label', 'is_active',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class DepartmentIntakeSerializer(serializers.ModelSerializer):
    department_code = serializers.ReadOnlyField(source='department.code')
    program_name = serializers.ReadOnlyField(source='program.name')
    academic_year_label = serializers.ReadOnlyField(source='academic_year.label')

    class Meta:
        model = DepartmentIntake
        fields = [
            'id', 'department', 'department_code', 'academic_year',
            'academic_year_label', 'program', 'program_name',
            'sanctioned_intake', 'actual_intake', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ['id', 'name', 'code', 'created_at']
        read_only_fields = ['id', 'created_at']


class SchemeSubjectSerializer(serializers.ModelSerializer):
    subject_code = serializers.ReadOnlyField(source='subject.code')
    subject_name = serializers.ReadOnlyField(source='subject.name')
    scheme_code = serializers.ReadOnlyField(source='scheme.code')

    class Meta:
        model = SchemeSubject
        fields = [
            'id', 'scheme', 'scheme_code', 'subject', 'subject_code', 'subject_name',
            'semester_number', 'subject_type', 'credits', 'max_marks', 'passing_marks',
            'max_internal_marks', 'passing_internal_marks', 'is_elective', 'is_locked',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class SchemeSerializer(serializers.ModelSerializer):
    program_name = serializers.ReadOnlyField(source='program.name')
    program_code = serializers.ReadOnlyField(source='program.code')
    effective_from_year_label = serializers.ReadOnlyField(source='effective_from_year.label')
    scheme_subjects = SchemeSubjectSerializer(many=True, read_only=True)

    class Meta:
        model = Scheme
        fields = [
            'id', 'program', 'program_name', 'program_code',
            'name', 'code', 'effective_from_year', 'effective_from_year_label',
            'is_active', 'scheme_subjects', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
