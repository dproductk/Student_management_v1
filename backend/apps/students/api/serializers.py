"""
Serializers for Student Management API.
"""

from rest_framework import serializers
from apps.students.models import (
    Student,
    StudentAdmission,
    StudentAddress,
    StudentCategory,
    StudentBankAccount,
    StudentEducationalHistory,
    StudentScholarship,
    StudentEnrollment,
    StudentDataCorrection,
)


class StudentListSerializer(serializers.ModelSerializer):
    current_batch = serializers.SerializerMethodField()
    current_department = serializers.SerializerMethodField()
    current_program = serializers.SerializerMethodField()
    current_division = serializers.SerializerMethodField()
    has_login = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = [
            'id', 'candidate_name', 'father_name', 'enrollment_no', 'application_id',
            'gender', 'date_of_birth', 'email', 'student_mobile', 'parent_mobile',
            'status', 'data_source', 'current_batch', 'current_department',
            'current_program', 'current_division', 'has_login', 'username', 'created_at'
        ]

    def get_has_login(self, obj):
        return bool(getattr(obj, 'user_id', None))

    def get_username(self, obj):
        # Prefetched user avoids extra queries; fall back safely.
        user = getattr(obj, 'user', None)
        try:
            return user.username if user else None
        except Exception:
            return None

    def get_current_division(self, obj):
        latest = self._get_latest_enrollment(obj)
        return getattr(latest, 'division', None) if latest else None

    def _get_latest_enrollment(self, obj):
        if hasattr(obj, '_cached_latest_enrollment'):
            return obj._cached_latest_enrollment
        if hasattr(obj, '_prefetched_objects_cache') and 'enrollments' in obj._prefetched_objects_cache:
            enrollments = sorted(obj.enrollments.all(), key=lambda e: e.created_at, reverse=True)
            obj._cached_latest_enrollment = enrollments[0] if enrollments else None
        else:
            obj._cached_latest_enrollment = obj.enrollments.order_by('-created_at').first()
        return obj._cached_latest_enrollment

    def get_current_batch(self, obj):
        latest_enrollment = self._get_latest_enrollment(obj)
        return latest_enrollment.batch.name if latest_enrollment and latest_enrollment.batch else None

    def get_current_department(self, obj):
        latest_enrollment = self._get_latest_enrollment(obj)
        return latest_enrollment.department.code if latest_enrollment and latest_enrollment.department else None

    def get_current_program(self, obj):
        latest_enrollment = self._get_latest_enrollment(obj)
        return latest_enrollment.program.code if latest_enrollment and latest_enrollment.program else None


class StudentAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentAddress
        fields = ['id', 'address_line', 'state', 'district', 'taluka', 'village', 'pincode']


class StudentCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentCategory
        fields = ['id', 'category', 'caste', 'sub_caste', 'is_minority', 'is_disabled', 'disability_type']


class StudentBankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentBankAccount
        fields = ['id', 'bank_name', 'branch_name', 'account_number_masked', 'ifsc_code', 'account_holder_name']


class StudentAdmissionSerializer(serializers.ModelSerializer):
    program_name = serializers.ReadOnlyField(source='program.name')
    program_code = serializers.ReadOnlyField(source='program.code')

    class Meta:
        model = StudentAdmission
        fields = [
            'id', 'program', 'program_name', 'program_code', 'admission_date',
            'admission_type', 'admission_category', 'seat_type', 'allotted_seat_type',
            'reservation_type', 'choice_code', 'cet_percentile', 'jee_percentile',
            'eligibility_percentage', 'dsa_dse_flag', 'starting_semester', 'data_source'
        ]


class StudentEnrollmentSerializer(serializers.ModelSerializer):
    academic_year_label = serializers.ReadOnlyField(source='academic_year.label')
    semester_number = serializers.ReadOnlyField(source='semester.number')
    department_code = serializers.ReadOnlyField(source='department.code')
    program_code = serializers.ReadOnlyField(source='program.code')
    batch_name = serializers.ReadOnlyField(source='batch.name')
    scheme_code = serializers.ReadOnlyField(source='scheme.code')

    class Meta:
        model = StudentEnrollment
        fields = [
            'id', 'academic_year', 'academic_year_label', 'semester', 'semester_number',
            'department', 'department_code', 'program', 'program_code',
            'batch', 'batch_name', 'scheme', 'scheme_code', 'division', 'status', 'created_at'
        ]


class StudentCorrectionSerializer(serializers.ModelSerializer):
    approved_by_username = serializers.ReadOnlyField(source='approved_by.username')

    class Meta:
        model = StudentDataCorrection
        fields = [
            'id', 'field_name', 'original_value', 'corrected_value',
            'correction_reason', 'approved_by_username', 'approved_at', 'source'
        ]


class StudentDetailSerializer(serializers.ModelSerializer):
    address = StudentAddressSerializer(read_only=True)
    category_info = StudentCategorySerializer(read_only=True)
    bank_account = StudentBankAccountSerializer(read_only=True)
    admissions = StudentAdmissionSerializer(many=True, read_only=True)
    enrollments = StudentEnrollmentSerializer(many=True, read_only=True)
    corrections = StudentCorrectionSerializer(many=True, read_only=True)

    class Meta:
        model = Student
        fields = [
            'id', 'user', 'application_id', 'enrollment_no', 'board_enrollment_no',
            'candidate_name', 'father_name', 'mother_name', 'gender', 'date_of_birth',
            'student_mobile', 'parent_mobile', 'email', 'religion', 'mother_tongue',
            'candidature_type', 'aadhaar_masked', 'status', 'data_source',
            'address', 'category_info', 'bank_account', 'admissions',
            'enrollments', 'corrections', 'created_at', 'updated_at'
        ]


class SensitiveRevealRequestSerializer(serializers.Serializer):
    field_name = serializers.ChoiceField(choices=['aadhaar', 'bank_account'])
    reason = serializers.CharField(min_length=5, max_length=500)


class CorrectionRequestSerializer(serializers.Serializer):
    field_name = serializers.CharField(max_length=100)
    new_value = serializers.CharField(max_length=500)
    reason = serializers.CharField(min_length=5, max_length=500)
