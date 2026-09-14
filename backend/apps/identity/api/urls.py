from django.urls import path
from apps.identity.api.views import (
    LoginView,
    TokenRefreshView,
    LogoutView,
    MeView,
    UserViewSet,
    CreateUserView,
    SuspendUserView,
    ReactivateUserView,
    DeactivateUserView,
    RoleViewSet,
    PermissionViewSet,
    SeedRBACView,
    RolePermissionView,
    RolePermissionDetailView,
    UserRoleView,
    UserRoleDetailView,
    UserPermissionsView,
    ProvisionStudentView,
    BulkProvisionStudentView,
    ChangePasswordView,
    IdentityAuditLogView,
)

urlpatterns = [
    # Authentication endpoints
    path('login/', LoginView.as_view(), name='auth-login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='auth-token-refresh'),
    path('logout/', LogoutView.as_view(), name='auth-logout'),
    path('me/', MeView.as_view(), name='auth-me'),
    path('change-password/', ChangePasswordView.as_view(), name='auth-change-password'),
    path('audit/', IdentityAuditLogView.as_view(), name='identity-audit-log'),

    # User lifecycle management endpoints
    path('users/', UserViewSet.as_view({'get': 'list'}), name='user-list'),
    path('users/<uuid:pk>/', UserViewSet.as_view({'get': 'retrieve'}), name='user-detail'),
    path('users/create/', CreateUserView.as_view(), name='user-create'),
    path('users/provision-student/', ProvisionStudentView.as_view(), name='user-provision-student'),
    path('users/provision-student/bulk/', BulkProvisionStudentView.as_view(), name='user-provision-student-bulk'),
    path('users/<uuid:user_id>/suspend/', SuspendUserView.as_view(), name='user-suspend'),
    path('users/<uuid:user_id>/reactivate/', ReactivateUserView.as_view(), name='user-reactivate'),
    path('users/<uuid:user_id>/deactivate/', DeactivateUserView.as_view(), name='user-deactivate'),

    # Role endpoints
    path('roles/', RoleViewSet.as_view({'get': 'list', 'post': 'create'}), name='role-list-create'),
    path('roles/<uuid:pk>/', RoleViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name='role-detail'),
    path('roles/<uuid:role_id>/permissions/', RolePermissionView.as_view(), name='role-permissions'),
    path('roles/<uuid:role_id>/permissions/<uuid:permission_id>/', RolePermissionDetailView.as_view(), name='role-permission-detail'),

    # Permission endpoints
    path('permissions/', PermissionViewSet.as_view({'get': 'list', 'post': 'create'}), name='permission-list-create'),
    path('permissions/<uuid:pk>/', PermissionViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name='permission-detail'),

    # User-Role assignment endpoints
    path('users/<uuid:user_id>/roles/', UserRoleView.as_view(), name='user-roles'),
    path('users/<uuid:user_id>/roles/<uuid:role_id>/', UserRoleDetailView.as_view(), name='user-role-detail'),
    path('users/<uuid:user_id>/permissions/', UserPermissionsView.as_view(), name='user-permissions'),

    # RBAC seeding endpoint
    path('rbac/seed/', SeedRBACView.as_view(), name='rbac-seed'),
]
