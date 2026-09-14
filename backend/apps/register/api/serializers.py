"""
Serializers for Register and Administrative Dashboards.
"""

from rest_framework import serializers


class RegisterStudentSerializer(serializers.Serializer):
    id = serializers.CharField()
    candidate_name = serializers.CharField()
    enrollment_no = serializers.CharField(allow_null=True)
    application_id = serializers.CharField(allow_null=True)
    gender = serializers.CharField()
    date_of_birth = serializers.CharField(allow_null=True)
    email = serializers.CharField(allow_null=True)
    student_mobile = serializers.CharField(allow_null=True)
    status = serializers.CharField()
    category = serializers.CharField()
    caste = serializers.CharField(allow_null=True, required=False)
    department_code = serializers.CharField(allow_null=True)
    department_name = serializers.CharField(allow_null=True)
    program_code = serializers.CharField(allow_null=True)
    batch_name = serializers.CharField(allow_null=True)
    academic_year = serializers.CharField(allow_null=True)
    semester_number = serializers.IntegerField(allow_null=True)
    verification_status = serializers.CharField()
    aadhaar_masked = serializers.CharField()
    created_at = serializers.CharField(allow_null=True)


class RegisterQueryResponseSerializer(serializers.Serializer):
    total_count = serializers.IntegerField()
    limit = serializers.IntegerField()
    offset = serializers.IntegerField()
    results = RegisterStudentSerializer(many=True)


class DepartmentDistributionSerializer(serializers.Serializer):
    department_id = serializers.CharField()
    code = serializers.CharField()
    name = serializers.CharField()
    student_count = serializers.IntegerField()


class DashboardSummarySerializer(serializers.Serializer):
    total_students = serializers.IntegerField()
    active_students = serializers.IntegerField()
    status_distribution = serializers.DictField(child=serializers.IntegerField())
    gender_distribution = serializers.DictField(child=serializers.IntegerField())
    category_distribution = serializers.DictField(child=serializers.IntegerField())
    department_distribution = DepartmentDistributionSerializer(many=True)
    verification_breakdown = serializers.DictField(child=serializers.IntegerField())
