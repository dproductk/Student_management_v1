"""
RBAC Domain models, enums, and invariants.
Governed by ARCHITECTURE.md, identity-and-access-prd.md, and DATABASE_ARCHITECTURE.md Deliverable H.
"""

from enum import Enum
from typing import Dict, List
from common.exceptions import InvariantViolationError


class RoleScopeType(str, Enum):
    SYSTEM = "SYSTEM"
    DEPARTMENT = "DEPARTMENT"
    BATCH = "BATCH"
    OWN = "OWN"


# Canonical system roles as defined in Deliverable H of DATABASE_ARCHITECTURE.md
CANONICAL_ROLES: Dict[str, Dict[str, str]] = {
    "SYSTEM_ADMIN": {
        "description": "System administrator with platform management privileges.",
        "scope_type": RoleScopeType.SYSTEM.value,
    },
    "COLLEGE_ADMIN": {
        "description": "College principal / administrative head with full operational visibility.",
        "scope_type": RoleScopeType.SYSTEM.value,
    },
    "HOD": {
        "description": "Head of Department with department-scoped management authority.",
        "scope_type": RoleScopeType.DEPARTMENT.value,
    },
    "FACULTY": {
        "description": "Academic faculty member with teaching assignment and assessment permissions.",
        "scope_type": RoleScopeType.DEPARTMENT.value,
    },
    "VERIFICATION_OFFICER": {
        "description": "Administrative officer managing document and student verification queues.",
        "scope_type": RoleScopeType.SYSTEM.value,
    },
    "ACCOUNTANT": {
        "description": "Financial officer managing fee structures and payment ledger entries.",
        "scope_type": RoleScopeType.SYSTEM.value,
    },
    "EXAM_CELL": {
        "description": "Examination cell officer managing result publication and mark processing.",
        "scope_type": RoleScopeType.SYSTEM.value,
    },
    "STUDENT": {
        "description": "Student user with self-service access to own profile, fees, and results.",
        "scope_type": RoleScopeType.OWN.value,
    },
}

# Standard foundational permissions by module
CANONICAL_PERMISSIONS: List[Dict[str, str]] = [
    # Identity & Access
    {"codename": "identity.manage_users", "description": "Create, suspend, and manage user accounts", "module": "identity"},
    {"codename": "identity.manage_roles", "description": "Manage roles and role-permission assignments", "module": "identity"},
    {"codename": "identity.view_audit", "description": "Inspect identity and security audit logs", "module": "identity"},

    # Academic Foundation
    {"codename": "academic.manage_departments", "description": "Create and configure departments", "module": "academic"},
    {"codename": "academic.manage_structure", "description": "Create and configure departments, programs, calendar, and batches", "module": "academic"},
    {"codename": "academic.manage_curriculum", "description": "Manage schemes, subjects, and scheme-subjects", "module": "academic"},
    {"codename": "academic.view_structure", "description": "View academic master data structure", "module": "academic"},
    {"codename": "academic.view_curriculum", "description": "View curriculum, schemes, and subject configurations", "module": "academic"},

    # Student Management
    {"codename": "students.view_directory", "description": "Search, filter, and view student directory", "module": "students"},
    {"codename": "students.manage_profile", "description": "Manage and correct student profile data", "module": "students"},
    {"codename": "students.view_own_record", "description": "View own student record", "module": "students"},
    {"codename": "students.reveal_sensitive", "description": "Reveal masked sensitive data (Aadhaar, Bank)", "module": "students"},
]


def validate_role_name(name: str) -> None:
    if not name or not name.strip():
        raise InvariantViolationError("Role name cannot be empty.")
    if len(name.strip()) > 100:
        raise InvariantViolationError("Role name cannot exceed 100 characters.")


def validate_scope_type(scope_type: str) -> None:
    valid_scopes = [s.value for s in RoleScopeType]
    if scope_type not in valid_scopes:
        raise InvariantViolationError(
            f"Invalid scope_type '{scope_type}'. Must be one of: {valid_scopes}"
        )


def validate_permission_codename(codename: str) -> None:
    if not codename or not codename.strip():
        raise InvariantViolationError("Permission codename cannot be empty.")
    if len(codename.strip()) > 150:
        raise InvariantViolationError("Permission codename cannot exceed 150 characters.")
    if "." not in codename:
        raise InvariantViolationError("Permission codename must follow '<module>.<action>' format.")
