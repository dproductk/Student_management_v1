"""
DRF Views for User model, authentication, and lifecycle management.
"""

from rest_framework import status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from common.exceptions import DomainException, EntityNotFoundError
from apps.identity.models import User, Role, Permission
from apps.audit.models import AuditLog
from apps.audit.api.serializers import AuditLogSerializer
from apps.identity.services.user_service import UserService
from apps.identity.services.auth_service import AuthService
from apps.identity.services.role_service import RoleService
from apps.identity.services.provisioning import StudentAccountProvisioningService
from apps.identity.api.permissions import require_permission
from apps.identity.domain.exceptions import (
    AuthenticationFailedError,
    AccountSuspendedError,
    AccountInactiveError,
    InvalidTokenError,
)
from apps.identity.api.serializers import (
    UserSerializer,
    CreateUserSerializer,
    SuspendUserSerializer,
    DeactivateUserSerializer,
    LoginSerializer,
    TokenRefreshRequestSerializer,
    LogoutRequestSerializer,
    RoleSerializer,
    CreateRoleSerializer,
    PermissionSerializer,
    CreatePermissionSerializer,
    AssignPermissionSerializer,
    RolePermissionSerializer,
    AssignRoleSerializer,
    UserRoleSerializer,
    StudentProvisioningInputSerializer,
    StudentProvisioningOutputSerializer,
    BulkStudentProvisioningInputSerializer,
    BulkStudentProvisioningOutputSerializer,
    ChangePasswordSerializer,
)


class LoginView(APIView):
    """
    POST /api/v1/auth/login/
    Public endpoint: Authenticates username & password, returns JWT tokens and profile summary.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            token_data = AuthService.authenticate_and_issue_tokens(
                username=serializer.validated_data['username'],
                password=serializer.validated_data['password']
            )
            return Response(token_data, status=status.HTTP_200_OK)
        except AuthenticationFailedError as e:
            return Response({'error': e.message, 'code': e.code}, status=status.HTTP_401_UNAUTHORIZED)
        except (AccountSuspendedError, AccountInactiveError) as e:
            return Response({'error': e.message, 'code': e.code}, status=status.HTTP_403_FORBIDDEN)
        except DomainException as e:
            return Response({'error': e.message, 'code': e.code}, status=status.HTTP_400_BAD_REQUEST)


class TokenRefreshView(APIView):
    """
    POST /api/v1/auth/token/refresh/
    Public endpoint: Issues a new access token given a valid refresh token.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = TokenRefreshRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            tokens = AuthService.refresh_access_token(serializer.validated_data['refresh'])
            return Response(tokens, status=status.HTTP_200_OK)
        except InvalidTokenError as e:
            return Response({'error': e.message, 'code': e.code}, status=status.HTTP_401_UNAUTHORIZED)
        except AuthenticationFailedError as e:
            return Response({'error': e.message, 'code': e.code}, status=status.HTTP_401_UNAUTHORIZED)
        except (AccountSuspendedError, AccountInactiveError) as e:
            return Response({'error': e.message, 'code': e.code}, status=status.HTTP_403_FORBIDDEN)


class LogoutView(APIView):
    """
    POST /api/v1/auth/logout/
    Revokes the provided refresh token by adding it to the token blacklist.
    Requires authentication.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            AuthService.logout(serializer.validated_data['refresh'])
            return Response({'message': 'Logged out successfully.'}, status=status.HTTP_200_OK)
        except (InvalidTokenError, AuthenticationFailedError) as e:
            return Response({'error': e.message, 'code': e.code}, status=status.HTTP_400_BAD_REQUEST)


class MeView(APIView):
    """
    GET /api/v1/auth/me/
    Authenticated endpoint: Returns current authenticated user's profile.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for listing and retrieving users.
    System administrators can search by username/email and filter by status.
    Protected by identity.manage_users permission.
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, require_permission('identity.manage_users')]

    def get_queryset(self):
        qs = User.objects.all().order_by('-created_at')
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter.strip().upper())

        search = self.request.query_params.get('search')
        if search:
            from django.db.models import Q
            search = search.strip()
            qs = qs.filter(Q(username__icontains=search) | Q(email__icontains=search))

        return qs


class CreateUserView(APIView):
    """
    API view for provisioning a new user.
    Protected by identity.manage_users permission.
    """
    permission_classes = [IsAuthenticated, require_permission('identity.manage_users')]

    def post(self, request):
        serializer = CreateUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = UserService.create_user(
                username=serializer.validated_data['username'],
                password=serializer.validated_data.get('password'),
                email=serializer.validated_data.get('email'),
                must_change_password=serializer.validated_data.get('must_change_password', True)
            )
            return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
        except DomainException as e:
            return Response({'error': e.message, 'code': e.code}, status=status.HTTP_400_BAD_REQUEST)


class SuspendUserView(APIView):
    """
    Suspends a user account.
    Protected by identity.manage_users permission.
    """
    permission_classes = [IsAuthenticated, require_permission('identity.manage_users')]

    def post(self, request, user_id):
        serializer = SuspendUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = UserService.suspend_user(
                user_id=user_id,
                reason=serializer.validated_data.get('reason'),
                actor=request.user
            )
            return Response(UserSerializer(user).data, status=status.HTTP_200_OK)
        except EntityNotFoundError as e:
            return Response({'error': e.message, 'code': e.code}, status=status.HTTP_404_NOT_FOUND)
        except DomainException as e:
            return Response({'error': e.message, 'code': e.code}, status=status.HTTP_400_BAD_REQUEST)


class ReactivateUserView(APIView):
    """
    Reactivates a suspended user account.
    Protected by identity.manage_users permission.
    """
    permission_classes = [IsAuthenticated, require_permission('identity.manage_users')]

    def post(self, request, user_id):
        try:
            user = UserService.reactivate_user(user_id=user_id, actor=request.user)
            return Response(UserSerializer(user).data, status=status.HTTP_200_OK)
        except EntityNotFoundError as e:
            return Response({'error': e.message, 'code': e.code}, status=status.HTTP_404_NOT_FOUND)
        except DomainException as e:
            return Response({'error': e.message, 'code': e.code}, status=status.HTTP_400_BAD_REQUEST)


class DeactivateUserView(APIView):
    """
    Deactivates a user account (terminal state).
    Protected by identity.manage_users permission.
    """
    permission_classes = [IsAuthenticated, require_permission('identity.manage_users')]

    def post(self, request, user_id):
        serializer = DeactivateUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = UserService.deactivate_user(
                user_id=user_id,
                reason=serializer.validated_data.get('reason'),
                actor=request.user
            )
            return Response(UserSerializer(user).data, status=status.HTTP_200_OK)
        except EntityNotFoundError as e:
            return Response({'error': e.message, 'code': e.code}, status=status.HTTP_404_NOT_FOUND)
        except DomainException as e:
            return Response({'error': e.message, 'code': e.code}, status=status.HTTP_400_BAD_REQUEST)


class RoleViewSet(viewsets.ModelViewSet):
    """
    CRUD ViewSet for Roles.
    List/Retrieve accessible to authenticated users.
    Create/Update/Delete restricted to actors with identity.manage_roles permission.
    """
    queryset = Role.objects.all()
    serializer_class = RoleSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), require_permission('identity.manage_roles')()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = CreateRoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            role = RoleService.create_role(
                name=serializer.validated_data['name'],
                scope_type=serializer.validated_data['scope_type'],
                description=serializer.validated_data.get('description')
            )
            return Response(RoleSerializer(role).data, status=status.HTTP_201_CREATED)
        except DomainException as e:
            return Response({'error': e.message, 'code': e.code}, status=status.HTTP_400_BAD_REQUEST)


class PermissionViewSet(viewsets.ModelViewSet):
    """
    CRUD ViewSet for Permissions.
    List/Retrieve accessible to authenticated users.
    Create/Update/Delete restricted to actors with identity.manage_roles permission.
    """
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), require_permission('identity.manage_roles')()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = CreatePermissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            permission = RoleService.create_permission(
                codename=serializer.validated_data['codename'],
                module=serializer.validated_data['module'],
                description=serializer.validated_data.get('description')
            )
            return Response(PermissionSerializer(permission).data, status=status.HTTP_201_CREATED)
        except DomainException as e:
            return Response({'error': e.message, 'code': e.code}, status=status.HTTP_400_BAD_REQUEST)


class SeedRBACView(APIView):
    """
    POST /api/v1/auth/rbac/seed/
    Administrative endpoint to seed canonical roles and permissions.
    Restricted to actors with identity.manage_roles permission.
    """
    permission_classes = [IsAuthenticated, require_permission('identity.manage_roles')]

    def post(self, request):
        roles_count, perms_count = RoleService.seed_canonical_roles_and_permissions()
        return Response({
            'message': 'Canonical roles and permissions seeded successfully.',
            'roles_created': roles_count,
            'permissions_created': perms_count,
            'total_roles': Role.objects.count(),
            'total_permissions': Permission.objects.count(),
        }, status=status.HTTP_200_OK)


class RolePermissionView(APIView):
    """
    GET /api/v1/auth/roles/<uuid:role_id>/permissions/ -> List permissions of a role
    POST /api/v1/auth/roles/<uuid:role_id>/permissions/ -> Assign a permission to a role
    """
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), require_permission('identity.manage_roles')()]
        return [IsAuthenticated()]

    def get(self, request, role_id):
        try:
            permissions = RoleService.get_permissions_for_role(str(role_id))
            return Response(PermissionSerializer(permissions, many=True).data, status=status.HTTP_200_OK)
        except EntityNotFoundError as e:
            return Response({'error': e.message, 'code': e.code}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, role_id):
        serializer = AssignPermissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            rp = RoleService.assign_permission_to_role(
                role_id=str(role_id),
                permission_id=str(serializer.validated_data['permission_id'])
            )
            return Response(RolePermissionSerializer(rp).data, status=status.HTTP_201_CREATED)
        except EntityNotFoundError as e:
            return Response({'error': e.message, 'code': e.code}, status=status.HTTP_404_NOT_FOUND)
        except DomainException as e:
            return Response({'error': e.message, 'code': e.code}, status=status.HTTP_400_BAD_REQUEST)


class RolePermissionDetailView(APIView):
    """
    DELETE /api/v1/auth/roles/<uuid:role_id>/permissions/<uuid:permission_id>/ -> Revoke permission
    """
    permission_classes = [IsAuthenticated, require_permission('identity.manage_roles')]

    def delete(self, request, role_id, permission_id):
        try:
            RoleService.revoke_permission_from_role(str(role_id), str(permission_id))
            return Response({'message': 'Permission revoked from role successfully.'}, status=status.HTTP_200_OK)
        except EntityNotFoundError as e:
            return Response({'error': e.message, 'code': e.code}, status=status.HTTP_404_NOT_FOUND)


class UserRoleView(APIView):
    """
    GET /api/v1/auth/users/<uuid:user_id>/roles/ -> List roles of a user
    POST /api/v1/auth/users/<uuid:user_id>/roles/ -> Assign a role to a user
    """
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), require_permission('identity.manage_roles')()]
        return [IsAuthenticated()]

    def get(self, request, user_id):
        try:
            roles = RoleService.get_user_roles(str(user_id))
            return Response(RoleSerializer(roles, many=True).data, status=status.HTTP_200_OK)
        except EntityNotFoundError as e:
            return Response({'error': e.message, 'code': e.code}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, user_id):
        serializer = AssignRoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            ur = RoleService.assign_role_to_user(
                user_id=str(user_id),
                role_id=str(serializer.validated_data['role_id']),
                assigned_by=request.user,
                scope_department_id=serializer.validated_data.get('scope_department_id'),
                scope_batch_id=serializer.validated_data.get('scope_batch_id')
            )
            return Response(UserRoleSerializer(ur).data, status=status.HTTP_201_CREATED)
        except EntityNotFoundError as e:
            return Response({'error': e.message, 'code': e.code}, status=status.HTTP_404_NOT_FOUND)
        except DomainException as e:
            return Response({'error': e.message, 'code': e.code}, status=status.HTTP_400_BAD_REQUEST)


class UserRoleDetailView(APIView):
    """
    DELETE /api/v1/auth/users/<uuid:user_id>/roles/<uuid:role_id>/ -> Revoke role from a user
    """
    permission_classes = [IsAuthenticated, require_permission('identity.manage_roles')]

    def delete(self, request, user_id, role_id):
        try:
            RoleService.revoke_role_from_user(str(user_id), str(role_id))
            return Response({'message': 'Role revoked from user successfully.'}, status=status.HTTP_200_OK)
        except EntityNotFoundError as e:
            return Response({'error': e.message, 'code': e.code}, status=status.HTTP_404_NOT_FOUND)


class UserPermissionsView(APIView):
    """
    GET /api/v1/auth/users/<uuid:user_id>/permissions/ -> List resolved permission codenames for user
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            perms = RoleService.get_user_permissions(user)
            return Response({'user_id': str(user.id), 'permissions': sorted(list(perms))}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': f"User with identifier '{user_id}' was not found.", 'code': 'NOT_FOUND'}, status=status.HTTP_404_NOT_FOUND)


class ProvisionStudentView(APIView):
    """
    POST /api/v1/auth/users/provision-student/
    Provisions a student account per ADR-009 (Username=Enrollment, Password=Enrollment).
    Protected by identity.manage_users permission.
    """
    permission_classes = [IsAuthenticated, require_permission('identity.manage_users')]

    def post(self, request):
        serializer = StudentProvisioningInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user, created = StudentAccountProvisioningService.provision_student_account(
                enrollment_number=serializer.validated_data['enrollment_number'],
                email=serializer.validated_data.get('email'),
                assigned_by=request.user
            )
            output_data = {
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'status': user.status,
                'must_change_password': user.must_change_password,
                'created': created
            }
            res_serializer = StudentProvisioningOutputSerializer(output_data)
            resp_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
            return Response(res_serializer.data, status=resp_status)
        except DomainException as e:
            return Response({'error': e.message, 'code': e.code}, status=status.HTTP_400_BAD_REQUEST)


class BulkProvisionStudentView(APIView):
    """
    POST /api/v1/auth/users/provision-student/bulk/
    Batch provisions student accounts per ADR-009.
    Protected by identity.manage_users permission.
    """
    permission_classes = [IsAuthenticated, require_permission('identity.manage_users')]

    def post(self, request):
        serializer = BulkStudentProvisioningInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = StudentAccountProvisioningService.bulk_provision_student_accounts(
            student_records=serializer.validated_data['students'],
            assigned_by=request.user
        )
        res_serializer = BulkStudentProvisioningOutputSerializer(result)
        return Response(res_serializer.data, status=status.HTTP_200_OK)


class ChangePasswordView(APIView):
    """
    POST /api/v1/auth/change-password/
    Allows authenticated users to complete mandatory first-login password changes
    or standard password updates. Issues fresh JWT tokens upon success.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            result = AuthService.change_password(
                user=request.user,
                current_password=serializer.validated_data['current_password'],
                new_password=serializer.validated_data['new_password'],
                confirm_password=serializer.validated_data['confirm_password']
            )
            return Response(result, status=status.HTTP_200_OK)
        except AuthenticationFailedError as e:
            return Response({'error': e.message, 'code': e.code}, status=status.HTTP_400_BAD_REQUEST)
        except DomainException as e:
            return Response({'error': e.message, 'code': e.code}, status=status.HTTP_400_BAD_REQUEST)


class IdentityAuditLogView(APIView):
    """
    GET /api/v1/auth/audit/
    Retrieves identity-related audit trail entries.
    Protected by identity.view_audit permission.
    """
    permission_classes = [IsAuthenticated, require_permission('identity.view_audit')]

    def get(self, request):
        qs = AuditLog.objects.filter(module='identity').select_related('actor').order_by('-occurred_at')

        action = request.query_params.get('action')
        if action:
            qs = qs.filter(action=action.strip().upper())

        target_id = request.query_params.get('target_id')
        if target_id:
            qs = qs.filter(target_id=target_id.strip())

        actor_id = request.query_params.get('actor_id')
        if actor_id:
            qs = qs.filter(actor_id=actor_id.strip())

        serializer = AuditLogSerializer(qs[:100], many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


