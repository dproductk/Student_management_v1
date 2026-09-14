"""
Serializers for Verification API endpoints.
"""

from rest_framework import serializers
from apps.verification.models import VerificationRequest, VerificationDecision, VerificationRequirement
from apps.verification.domain.invariants import ENTITY_TYPE_CHOICES, ALLOWED_DECISIONS


class VerificationDecisionSerializer(serializers.ModelSerializer):
    reviewer_username = serializers.CharField(source='reviewer.username', read_only=True)

    class Meta:
        model = VerificationDecision
        fields = [
            'id',
            'version',
            'decision',
            'reviewer',
            'reviewer_username',
            'reviewed_at',
            'rejection_reason',
            'notes',
            'created_at',
        ]
        read_only_fields = ['id', 'version', 'reviewed_at', 'created_at']


class VerificationRequestSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.candidate_name', read_only=True)
    submitted_by_username = serializers.CharField(source='submitted_by.username', read_only=True)
    decisions = VerificationDecisionSerializer(many=True, read_only=True)

    class Meta:
        model = VerificationRequest
        fields = [
            'id',
            'student',
            'student_name',
            'entity_type',
            'entity_id',
            'field_name',
            'submitted_value',
            'status',
            'current_version',
            'submitted_by',
            'submitted_by_username',
            'submitted_at',
            'decisions',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'status', 'current_version', 'submitted_by', 'submitted_at', 'created_at', 'updated_at']


class VerificationSubmitSerializer(serializers.Serializer):
    student_id = serializers.UUIDField(required=True)
    entity_type = serializers.ChoiceField(choices=[k for k, _ in ENTITY_TYPE_CHOICES], required=True)
    entity_id = serializers.UUIDField(required=False, allow_null=True)
    field_name = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)
    submitted_value = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class VerificationDecisionActionSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=sorted(list(ALLOWED_DECISIONS)), required=True)
    rejection_reason = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class VerificationResubmitSerializer(serializers.Serializer):
    new_submitted_value = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    new_entity_id = serializers.UUIDField(required=False, allow_null=True)
