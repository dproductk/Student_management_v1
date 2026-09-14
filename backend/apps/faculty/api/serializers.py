"""
Serializers for Faculty, Assignments, and Academic Items.
"""

from rest_framework import serializers
from apps.faculty.models import (
    Faculty,
    FacultyStatus,
    EmploymentType,
    FacultyAssignment,
    AssignmentRole,
    FacultyAcademicItem,
    AcademicItemType,
)
from apps.academic.models import Department, AcademicYear, Semester, Batch, SchemeSubject
from apps.faculty.services.faculty_service import FacultyService


class FacultyAcademicItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = FacultyAcademicItem
        fields = [
            'id',
            'faculty',
            'item_type',
            'title',
            'year',
            'details',
            'reference_url',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class FacultyAssignmentSerializer(serializers.ModelSerializer):
    faculty_name = serializers.CharField(source='faculty.full_name', read_only=True)
    academic_year_label = serializers.CharField(source='academic_year.label', read_only=True)
    semester_label = serializers.CharField(source='semester.label', read_only=True)
    subject_code = serializers.CharField(source='scheme_subject.subject.code', read_only=True)
    subject_name = serializers.CharField(source='scheme_subject.subject.name', read_only=True)
    batch_name = serializers.CharField(source='batch.name', read_only=True, default=None)
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = FacultyAssignment
        fields = [
            'id',
            'faculty',
            'faculty_name',
            'academic_year',
            'academic_year_label',
            'semester',
            'semester_label',
            'scheme_subject',
            'subject_code',
            'subject_name',
            'batch',
            'batch_name',
            'role',
            'role_display',
            'is_active',
            'effective_start_date',
            'effective_end_date',
            'remarks',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class FacultyListSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    department_code = serializers.CharField(source='department.code', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    active_assignment_count = serializers.IntegerField(source='assignments.count', read_only=True)

    class Meta:
        model = Faculty
        fields = [
            'id',
            'faculty_id',
            'first_name',
            'last_name',
            'full_name',
            'email',
            'phone',
            'designation',
            'employment_type',
            'status',
            'department',
            'department_code',
            'department_name',
            'is_hod',
            'cabin_number',
            'date_of_joining',
            'active_assignment_count',
            'created_at',
        ]


class FacultyDetailSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    department_code = serializers.CharField(source='department.code', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    assignments = FacultyAssignmentSerializer(many=True, read_only=True)
    academic_items = FacultyAcademicItemSerializer(many=True, read_only=True)

    class Meta:
        model = Faculty
        fields = [
            'id',
            'faculty_id',
            'first_name',
            'last_name',
            'full_name',
            'email',
            'phone',
            'designation',
            'employment_type',
            'status',
            'department',
            'department_code',
            'department_name',
            'is_hod',
            'cabin_number',
            'contact_email',
            'responsibilities',
            'qualification',
            'specialization',
            'date_of_joining',
            'date_of_relieving',
            'assignments',
            'academic_items',
            'created_at',
            'updated_at',
        ]


class FacultyCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Faculty
        fields = [
            'id',
            'faculty_id',
            'first_name',
            'last_name',
            'email',
            'phone',
            'designation',
            'employment_type',
            'status',
            'department',
            'is_hod',
            'cabin_number',
            'contact_email',
            'responsibilities',
            'qualification',
            'specialization',
            'date_of_joining',
            'date_of_relieving',
        ]
        read_only_fields = ['id']
