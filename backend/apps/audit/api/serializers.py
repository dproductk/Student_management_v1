"""
Serializers for Audit log entries.
Read-only presentation representations.
"""

from rest_framework import serializers
from apps.audit.models import AuditLog, SensitiveDataAccessLog


class AuditLogSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for AuditLog records.
    """
    actor_username = serializers.CharField(source='actor.username', read_only=True, default=None)

    class Meta:
        model = AuditLog
        fields = [
            'id',
            'actor_id',
            'actor_username',
            'action',
            'target_type',
            'target_id',
            'module',
            'old_value',
            'new_value',
            'reason',
            'ip_address',
            'occurred_at',
        ]
        read_only_fields = fields


class SensitiveDataAccessLogSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for SensitiveDataAccessLog records.
    """
    accessor_username = serializers.CharField(source='accessor.username', read_only=True, default=None)

    class Meta:
        model = SensitiveDataAccessLog
        fields = [
            'id',
            'accessor',
            'accessor_username',
            'student_id',
            'field_name',
            'reason',
            'ip_address',
            'accessed_at',
        ]
        read_only_fields = fields
