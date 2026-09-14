import uuid
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.identity.services.user_service import UserService
from apps.identity.services.role_service import RoleService
from apps.identity.api.permissions import require_scoped_permission

User = get_user_model()


class MockTargetResource:
    """
    Mock domain resource carrying scope identifiers for testing object-level authorization.
    """
    def __init__(self, department_id=None, batch_id=None, user_id=None):
        self.department_id = department_id
        self.batch_id = batch_id
        self.user_id = user_id


class MockScopedView(APIView):
    """
    Mock protected view using require_scoped_permission.
    """
    permission_classes = [require_scoped_permission('academic.manage_departments')]

    def get(self, request, target_resource):
        self.check_object_permissions(request, target_resource)
        return Response({'status': 'Access granted'}, status=status.HTTP_200_OK)


class ScopedAuthorizationEnforcementTests(TestCase):
    """
    Automated tests verifying scoped authorization enforcement (SYSTEM, DEPARTMENT, BATCH, OWN).
    Governed by DATABASE_ARCHITECTURE.md Deliverable H and identity-and-access-prd.md Requirement 12.
    """

    def setUp(self):
        self.factory = APIRequestFactory()

        # Department UUIDs
        self.dept_a_id = uuid.uuid4()
        self.dept_b_id = uuid.uuid4()

        # Batch UUIDs
        self.batch_1_id = uuid.uuid4()
        self.batch_2_id = uuid.uuid4()

        # Admin user
        self.admin = User.objects.create_superuser(username="root_admin", password="AdminPassword123!")

        # Faculty user
        self.faculty_user = UserService.create_user(username="prof_smith", password="Password123!")

        # Student users
        self.student_1 = UserService.create_user(username="student_001", password="Password123!")
        self.student_2 = UserService.create_user(username="student_002", password="Password123!")

        # Foundational permissions
        self.perm_dept = RoleService.create_permission(codename="academic.manage_departments", module="academic")
        self.perm_view_student = RoleService.create_permission(codename="students.view_record", module="students")

        # Roles with different scope types
        self.role_sys = RoleService.create_role(name="COLLEGE_HEAD", scope_type="SYSTEM")
        self.role_dept = RoleService.create_role(name="HOD_ROLE", scope_type="DEPARTMENT")
        self.role_batch = RoleService.create_role(name="BATCH_COORD", scope_type="BATCH")
        self.role_own = RoleService.create_role(name="STUDENT_ROLE", scope_type="OWN")

        # Link permissions to roles
        RoleService.assign_permission_to_role(str(self.role_sys.id), str(self.perm_dept.id))
        RoleService.assign_permission_to_role(str(self.role_dept.id), str(self.perm_dept.id))
        RoleService.assign_permission_to_role(str(self.role_batch.id), str(self.perm_dept.id))
        RoleService.assign_permission_to_role(str(self.role_own.id), str(self.perm_view_student.id))

    def test_system_scope_grants_access_across_departments(self):
        # Assign SYSTEM scoped role to user
        RoleService.assign_role_to_user(str(self.faculty_user.id), str(self.role_sys.id), assigned_by=self.admin)

        # Access Dept A
        self.assertTrue(RoleService.has_scoped_permission(
            self.faculty_user,
            "academic.manage_departments",
            target_department_id=str(self.dept_a_id)
        ))
        # Access Dept B
        self.assertTrue(RoleService.has_scoped_permission(
            self.faculty_user,
            "academic.manage_departments",
            target_department_id=str(self.dept_b_id)
        ))

    def test_department_scope_grants_access_only_to_assigned_department(self):
        # Assign HOD role scoped to Dept A
        RoleService.assign_role_to_user(
            user_id=str(self.faculty_user.id),
            role_id=str(self.role_dept.id),
            assigned_by=self.admin,
            scope_department_id=self.dept_a_id
        )

        # Access to Dept A must be GRANTED
        self.assertTrue(RoleService.has_scoped_permission(
            self.faculty_user,
            "academic.manage_departments",
            target_department_id=str(self.dept_a_id)
        ))

        # Access to Dept B must be DENIED
        self.assertFalse(RoleService.has_scoped_permission(
            self.faculty_user,
            "academic.manage_departments",
            target_department_id=str(self.dept_b_id)
        ))

    def test_batch_scope_grants_access_only_to_assigned_batch(self):
        # Assign Batch Coordinator scoped to Batch 1
        RoleService.assign_role_to_user(
            user_id=str(self.faculty_user.id),
            role_id=str(self.role_batch.id),
            assigned_by=self.admin,
            scope_batch_id=self.batch_1_id
        )

        # Access to Batch 1 must be GRANTED
        self.assertTrue(RoleService.has_scoped_permission(
            self.faculty_user,
            "academic.manage_departments",
            target_batch_id=str(self.batch_1_id)
        ))

        # Access to Batch 2 must be DENIED
        self.assertFalse(RoleService.has_scoped_permission(
            self.faculty_user,
            "academic.manage_departments",
            target_batch_id=str(self.batch_2_id)
        ))

    def test_own_scope_grants_access_only_to_own_record(self):
        # Assign STUDENT_ROLE (OWN scope) to student 1
        RoleService.assign_role_to_user(str(self.student_1.id), str(self.role_own.id), assigned_by=self.admin)

        # Student 1 accessing own record -> GRANTED
        self.assertTrue(RoleService.has_scoped_permission(
            self.student_1,
            "students.view_record",
            target_user_id=str(self.student_1.id)
        ))

        # Student 1 accessing student 2's record -> DENIED
        self.assertFalse(RoleService.has_scoped_permission(
            self.student_1,
            "students.view_record",
            target_user_id=str(self.student_2.id)
        ))

    def test_superuser_bypasses_all_scope_restrictions(self):
        # Superuser can access Dept A, Dept B, Batch 1, and any student record
        self.assertTrue(RoleService.has_scoped_permission(
            self.admin,
            "academic.manage_departments",
            target_department_id=str(self.dept_a_id)
        ))
        self.assertTrue(RoleService.has_scoped_permission(
            self.admin,
            "academic.manage_departments",
            target_department_id=str(self.dept_b_id)
        ))
        self.assertTrue(RoleService.has_scoped_permission(
            self.admin,
            "students.view_record",
            target_user_id=str(self.student_1.id)
        ))

    def test_drf_object_level_permission_enforcement(self):
        # Assign HOD role scoped to Dept A
        RoleService.assign_role_to_user(
            user_id=str(self.faculty_user.id),
            role_id=str(self.role_dept.id),
            assigned_by=self.admin,
            scope_department_id=self.dept_a_id
        )

        view = MockScopedView.as_view()

        # Request targeting Dept A resource -> 200 OK
        resource_a = MockTargetResource(department_id=self.dept_a_id)
        req_a = self.factory.get('/mock/resource/')
        force_authenticate(req_a, user=self.faculty_user)
        resp_a = view(req_a, target_resource=resource_a)
        self.assertEqual(resp_a.status_code, status.HTTP_200_OK)

        # Request targeting Dept B resource -> 403 FORBIDDEN
        resource_b = MockTargetResource(department_id=self.dept_b_id)
        req_b = self.factory.get('/mock/resource/')
        force_authenticate(req_b, user=self.faculty_user)
        resp_b = view(req_b, target_resource=resource_b)
        self.assertEqual(resp_b.status_code, status.HTTP_403_FORBIDDEN)
