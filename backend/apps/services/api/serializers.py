from rest_framework import serializers
from apps.services.models import ServiceRequestType, ServiceRequest, ServiceRequestAudit
from apps.documents.models import StudentDocument


class ServiceRequestTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceRequestType
        fields = [
            'id',
            'name',
            'code',
            'description',
            'requires_document',
            'allowed_document_types',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ServiceRequestAuditSerializer(serializers.ModelSerializer):
    actor_username = serializers.CharField(source='actor.username', read_only=True)

    class Meta:
        model = ServiceRequestAudit
        fields = [
            'id',
            'service_request',
            'actor',
            'actor_username',
            'action',
            'previous_status',
            'new_status',
            'reason',
            'timestamp',
        ]
        read_only_fields = fields


class ServiceRequestSerializer(serializers.ModelSerializer):
    student_enrollment_no = serializers.CharField(source='student.enrollment_no', read_only=True)
    student_name = serializers.CharField(source='student.candidate_name', read_only=True)
    service_type_name = serializers.CharField(source='service_type.name', read_only=True)
    service_type_code = serializers.CharField(source='service_type.code', read_only=True)
    attached_document_name = serializers.CharField(source='attached_document.original_filename', read_only=True)
    assigned_to_username = serializers.CharField(source='assigned_to.username', read_only=True)
    processed_by_username = serializers.CharField(source='processed_by.username', read_only=True)
    audits = ServiceRequestAuditSerializer(many=True, read_only=True)

    class Meta:
        model = ServiceRequest
        fields = [
            'id',
            'request_number',
            'student',
            'student_enrollment_no',
            'student_name',
            'service_type',
            'service_type_name',
            'service_type_code',
            'status',
            'priority',
            'request_data',
            'attached_document',
            'attached_document_name',
            'assigned_to',
            'assigned_to_username',
            'processed_by',
            'processed_by_username',
            'processed_at',
            'resolution_notes',
            'rejection_reason',
            'created_at',
            'updated_at',
            'audits',
        ]
        read_only_fields = [
            'id',
            'request_number',
            'status',
            'assigned_to',
            'processed_by',
            'processed_at',
            'resolution_notes',
            'rejection_reason',
            'created_at',
            'updated_at',
            'audits',
        ]


class SubmitServiceRequestSerializer(serializers.Serializer):
    student = serializers.UUIDField()
    service_type = serializers.UUIDField()
    priority = serializers.ChoiceField(choices=['NORMAL', 'HIGH', 'URGENT'], default='NORMAL')
    request_data = serializers.JSONField(required=False, default=dict)
    document_id = serializers.UUIDField(required=False, allow_null=True)
