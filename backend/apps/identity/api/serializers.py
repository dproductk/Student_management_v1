"""
DRF Serializers for User model, authentication, and lifecycle operations.
"""

from rest_framework import serializers
from apps.identity.models import User, Role, Permission, RolePermission, UserRole


class LoginSerializer(serializers.Serializer):
    """
    Input serializer for user login authentication.
    """
    username = serializers.CharField(required=True, max_length=150)
    password = serializers.CharField(required=True, max_length=128, write_only=True)


class TokenRefreshRequestSerializer(serializers.Serializer):
    """
    Input serializer for JWT token refresh.
    """
    refresh = serializers.CharField(required=True)


class LogoutRequestSerializer(serializers.Serializer):
    """
    Input serializer for user logout and token revocation.
    """
    refresh = serializers.CharField(required=True)


class UserSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for User details. Never exposes password hash.
    """
    roles = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    faculty_id = serializers.SerializerMethodField()
    enrollment_no = serializers.SerializerMethodField()
    department_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'status',
            'is_active',
            'is_staff',
            'is_superuser',
            'must_change_password',
            'last_login',
            'created_at',
            'updated_at',
            'roles',
            'permissions',
            'full_name',
            'faculty_id',
            'enrollment_no',
            'department_name',
        ]
        read_only_fields = fields

    def get_roles(self, obj):
        from apps.identity.models import UserRole
        roles = list(
            UserRole.objects.filter(user=obj).select_related('role').values(
                'role__id', 'role__name', 'role__scope_type', 'scope_department_id', 'scope_batch_id'
            )
        )
        formatted = [
            {
                'id': str(r['role__id']),
                'name': r['role__name'],
                'role__name': r['role__name'],
                'scope_type': r['role__scope_type'],
                'scope_department_id': str(r['scope_department_id']) if r['scope_department_id'] else None,
                'scope_batch_id': str(r['scope_batch_id']) if r['scope_batch_id'] else None,
            }
            for r in roles
        ]
        if obj.is_superuser and not any(r['name'] == 'SYSTEM_ADMIN' for r in formatted):
            formatted.append({
                'name': 'SYSTEM_ADMIN',
                'role__name': 'SYSTEM_ADMIN',
                'scope_type': 'SYSTEM'
            })
        return formatted

    def get_permissions(self, obj):
        from apps.identity.services.role_service import RoleService
        return list(RoleService.get_user_permissions(obj))

    def get_full_name(self, obj):
        try:
            from apps.faculty.models import Faculty
            faculty = Faculty.objects.filter(user=obj).first()
            if faculty:
                return f"{faculty.first_name} {faculty.last_name}".strip()
        except Exception:
            pass
        try:
            from apps.students.models import Student
            student = Student.objects.filter(user=obj).first()
            if student:
                return student.candidate_name
        except Exception:
            pass
        return obj.username

    def get_faculty_id(self, obj):
        try:
            from apps.faculty.models import Faculty
            faculty = Faculty.objects.filter(user=obj).first()
            return faculty.faculty_id if faculty else None
        except Exception:
            return None

    def get_enrollment_no(self, obj):
        try:
            from apps.students.models import Student
            student = Student.objects.filter(user=obj).first()
            return student.enrollment_no if student else None
        except Exception:
            return None

    def get_department_name(self, obj):
        try:
            from apps.faculty.models import Faculty
            faculty = Faculty.objects.filter(user=obj).select_related('department').first()
            return faculty.department.name if (faculty and faculty.department) else None
        except Exception:
            return None


class CreateUserSerializer(serializers.Serializer):
    """
    Input serializer for user creation.
    """
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(max_length=128, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_null=True)
    must_change_password = serializers.BooleanField(default=True)


class SuspendUserSerializer(serializers.Serializer):
    """
    Input serializer for suspending a user account.
    """
    reason = serializers.CharField(required=False, allow_blank=True)


class DeactivateUserSerializer(serializers.Serializer):
    """
    Input serializer for deactivating a user account.
    """
    reason = serializers.CharField(required=False, allow_blank=True)


class RoleSerializer(serializers.ModelSerializer):
    """
    Serializer for Role representations.
    """
    class Meta:
        model = Role
        fields = [
            'id',
            'name',
            'description',
            'scope_type',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CreateRoleSerializer(serializers.Serializer):
    """
    Input serializer for creating a new role.
    """
    name = serializers.CharField(max_length=100)
    scope_type = serializers.CharField(max_length=30)
    description = serializers.CharField(required=False, allow_blank=True)


class PermissionSerializer(serializers.ModelSerializer):
    """
    Serializer for Permission representations.
    """
    class Meta:
        model = Permission
        fields = [
            'id',
            'codename',
            'description',
            'module',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CreatePermissionSerializer(serializers.Serializer):
    """
    Input serializer for creating a new permission.
    """
    codename = serializers.CharField(max_length=150)
    module = serializers.CharField(max_length=50)
    description = serializers.CharField(required=False, allow_blank=True)


class AssignPermissionSerializer(serializers.Serializer):
    """
    Input serializer for attaching a permission to a role.
    """
    permission_id = serializers.UUIDField(required=True)


class RolePermissionSerializer(serializers.ModelSerializer):
    """
    Serializer for RolePermission link with nested permission details.
    """
    permission = PermissionSerializer(read_only=True)

    class Meta:
        model = RolePermission
        fields = ['id', 'role_id', 'permission', 'created_at']
        read_only_fields = fields


class AssignRoleSerializer(serializers.Serializer):
    """
    Input serializer for attaching a role to a user.
    """
    role_id = serializers.UUIDField(required=True)
    scope_department_id = serializers.UUIDField(required=False, allow_null=True)
    scope_batch_id = serializers.UUIDField(required=False, allow_null=True)


class UserRoleSerializer(serializers.ModelSerializer):
    """
    Serializer for UserRole mappings.
    """
    role = RoleSerializer(read_only=True)

    class Meta:
        model = UserRole
        fields = [
            'id',
            'user_id',
            'role',
            'scope_department_id',
            'scope_batch_id',
            'created_at',
            'assigned_by_id',
        ]
        read_only_fields = fields


class StudentProvisioningInputSerializer(serializers.Serializer):
    """
    Input serializer for provisioning a student account per ADR-009.
    Accepts enrollment_number OR application_id as the unique identifier.
    Username = identifier, Password = identifier (default), must_change_password=True.
    """
    enrollment_number = serializers.CharField(max_length=100, required=False, allow_blank=True, default='')
    application_id = serializers.CharField(max_length=100, required=False, allow_blank=True, default='')
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)

    def validate(self, attrs):
        enr = (attrs.get('enrollment_number') or '').strip()
        app = (attrs.get('application_id') or '').strip()
        if not enr and not app:
            raise serializers.ValidationError("Either enrollment_number or application_id is required.")
        # Normalise: prefer enrollment_number, else application_id
        attrs['enrollment_number'] = enr or app
        return attrs


class StudentProvisioningOutputSerializer(serializers.Serializer):
    """
    Response representation for provisioned student account.
    """
    user_id = serializers.UUIDField()
    username = serializers.CharField()
    email = serializers.EmailField(allow_null=True, required=False)
    status = serializers.CharField()
    must_change_password = serializers.BooleanField()
    created = serializers.BooleanField()


class BulkStudentProvisioningInputSerializer(serializers.Serializer):
    """
    Input serializer for batch student account provisioning.
    """
    students = StudentProvisioningInputSerializer(many=True, required=True)


class BulkStudentProvisioningOutputSerializer(serializers.Serializer):
    """
    Response representation for bulk provisioning batch results.
    """
    total = serializers.IntegerField()
    created_count = serializers.IntegerField()
    existing_count = serializers.IntegerField()
    failed_count = serializers.IntegerField()
    created = serializers.ListField(child=serializers.DictField())
    existing = serializers.ListField(child=serializers.DictField())
    errors = serializers.ListField(child=serializers.DictField())


class ChangePasswordSerializer(serializers.Serializer):
    """
    Input serializer for mandatory first-login or regular password changes.
    """
    current_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, min_length=8)
    confirm_password = serializers.CharField(required=True, write_only=True, min_length=8)


