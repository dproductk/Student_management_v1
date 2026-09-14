"""
Seed Demo Accounts Script.
Creates canonical roles, foundational academic structures, and one user account for each profile:
1. SYSTEM_ADMIN (Platform Administrator)
2. COLLEGE_ADMIN (Principal / Administrative Head)
3. HOD (Head of Department - Computer Engineering)
4. FACULTY (Teaching Faculty Member)
5. VERIFICATION_OFFICER (Document & Admission Verifier)
6. ACCOUNTANT (Finance & Payment Ledger Officer)
7. EXAM_CELL (Results & Marks Examination Controller)
8. STUDENT (Enrolled Student Portal User)
"""

import os
import sys
from datetime import date
from pathlib import Path

# Setup Django standalone environment
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.db import transaction
from apps.identity.models import User, Role, Permission, RolePermission, UserRole
from apps.identity.domain.rbac import CANONICAL_ROLES, CANONICAL_PERMISSIONS
from apps.academic.models import Department, Program, AcademicYear, Semester, Batch, Scheme
from apps.faculty.models import Faculty, FacultyStatus, EmploymentType
from apps.students.models import Student, StudentEnrollment
from apps.finance.models import StudentFeeAccount

DEFAULT_PASSWORD = "Password@123"


def seed_canonical_rbac():
    print("[1/4] Seeding canonical permissions...")
    perm_objs = {}
    for perm_data in CANONICAL_PERMISSIONS:
        perm, _ = Permission.objects.get_or_create(
            codename=perm_data["codename"].strip().lower(),
            defaults={
                "module": perm_data["module"],
                "description": perm_data.get("description", "")
            }
        )
        perm_objs[perm.codename] = perm

    print("[2/4] Seeding canonical roles & permissions...")
    role_objs = {}
    for role_name, role_meta in CANONICAL_ROLES.items():
        role, _ = Role.objects.get_or_create(
            name=role_name,
            defaults={
                "scope_type": role_meta["scope_type"],
                "description": role_meta["description"]
            }
        )
        role_objs[role_name] = role

        # Assign relevant permissions to each role
        if role_name in ("SYSTEM_ADMIN", "COLLEGE_ADMIN"):
            for p in perm_objs.values():
                RolePermission.objects.get_or_create(role=role, permission=p)
        elif role_name == "HOD":
            hod_perms = [
                p for code, p in perm_objs.items()
                if any(k in code for k in ["academic", "faculty", "results", "students.view"])
            ]
            for p in hod_perms:
                RolePermission.objects.get_or_create(role=role, permission=p)
        elif role_name == "FACULTY":
            fac_perms = [
                p for code, p in perm_objs.items()
                if any(k in code for k in ["faculty", "results.enter", "results.view", "students.view"])
            ]
            for p in fac_perms:
                RolePermission.objects.get_or_create(role=role, permission=p)
        elif role_name == "VERIFICATION_OFFICER":
            ver_perms = [
                p for code, p in perm_objs.items()
                if any(k in code for k in ["verification", "documents", "students.view"])
            ]
            for p in ver_perms:
                RolePermission.objects.get_or_create(role=role, permission=p)
        elif role_name == "ACCOUNTANT":
            acc_perms = [
                p for code, p in perm_objs.items()
                if any(k in code for k in ["finance", "students.view", "reporting"])
            ]
            for p in acc_perms:
                RolePermission.objects.get_or_create(role=role, permission=p)
        elif role_name == "EXAM_CELL":
            exam_perms = [
                p for code, p in perm_objs.items()
                if any(k in code for k in ["results", "assessments", "students.view"])
            ]
            for p in exam_perms:
                RolePermission.objects.get_or_create(role=role, permission=p)
        elif role_name == "STUDENT":
            std_perms = [
                p for code, p in perm_objs.items()
                if any(k in code for k in ["students.view", "services.submit", "finance.view"])
            ]
            for p in std_perms:
                RolePermission.objects.get_or_create(role=role, permission=p)

    return role_objs


def seed_academic_foundation():
    print("[3/4] Ensuring foundational academic structures exist...")
    dept, _ = Department.objects.get_or_create(
        code="COMP",
        defaults={"name": "Computer Engineering", "is_active": True}
    )

    prog, _ = Program.objects.get_or_create(
        code="BTECH-CE",
        department=dept,
        defaults={"name": "B.Tech in Computer Engineering", "duration_years": 4, "degree_type": "B.Tech"}
    )

    ay, _ = AcademicYear.objects.get_or_create(
        label="2025-2026",
        defaults={"start_date": date(2025, 7, 1), "end_date": date(2026, 6, 30), "is_current": True}
    )

    sem, _ = Semester.objects.get_or_create(
        academic_year=ay,
        number=1,
        defaults={
            "label": "Semester 1",
            "start_date": date(2025, 7, 1),
            "end_date": date(2025, 12, 31)
        }
    )

    batch, _ = Batch.objects.get_or_create(
        department=dept,
        name="2025-2029",
        academic_year=ay,
        defaults={"is_active": True}
    )

    scheme, _ = Scheme.objects.get_or_create(
        code="SCH-2025-COMP",
        defaults={
            "program": prog,
            "name": "2025 Computer Engineering Curriculum Scheme",
            "effective_from_year": ay
        }
    )

    return dept, prog, ay, sem, batch, scheme


def seed_accounts(roles, academic_data):
    dept, prog, ay, sem, batch, scheme = academic_data
    print("[4/4] Creating demo accounts for all profiles...")

    # 1. System Administrator
    admin_user, _ = User.objects.get_or_create(
        username="admin",
        defaults={
            "email": "admin@university.edu",
            "is_staff": True,
            "is_superuser": True,
            "must_change_password": False,
            "status": "ACTIVE"
        }
    )
    admin_user.set_password(DEFAULT_PASSWORD)
    admin_user.must_change_password = False
    admin_user.save()
    UserRole.objects.get_or_create(
        user=admin_user,
        role=roles["SYSTEM_ADMIN"],
        defaults={"assigned_by": admin_user}
    )

    # Helper to create standard staff user
    def make_user(username, email, role_name, scope_dept=None):
        u, _ = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "is_staff": True,
                "is_superuser": False,
                "must_change_password": False,
                "status": "ACTIVE"
            }
        )
        u.set_password(DEFAULT_PASSWORD)
        u.must_change_password = False
        u.save()
        UserRole.objects.get_or_create(
            user=u,
            role=roles[role_name],
            scope_department_id=scope_dept.id if scope_dept else None,
            defaults={"assigned_by": admin_user}
        )
        return u

    # 2. College Admin
    make_user("college_admin", "principal@university.edu", "COLLEGE_ADMIN")

    # 3. HOD (Computer Engineering)
    hod_user = make_user("hod_cs", "hod.comp@university.edu", "HOD", scope_dept=dept)
    Faculty.objects.get_or_create(
        faculty_id="FAC-COMP-HOD",
        defaults={
            "user": hod_user,
            "first_name": "Rajesh",
            "last_name": "Verma",
            "email": "hod.comp@university.edu",
            "phone": "9876543210",
            "designation": "Professor & Head",
            "employment_type": EmploymentType.PERMANENT,
            "status": FacultyStatus.ACTIVE,
            "date_of_joining": date(2015, 1, 15),
            "qualification": "Ph.D. in Computer Science",
            "specialization": "Artificial Intelligence & Distributed Systems",
            "department": dept,
            "is_hod": True,
            "cabin_number": "CS-101"
        }
    )

    # 4. Faculty Member
    fac_user = make_user("faculty_sharma", "fac.sharma@university.edu", "FACULTY", scope_dept=dept)
    Faculty.objects.get_or_create(
        faculty_id="FAC-COMP-002",
        defaults={
            "user": fac_user,
            "first_name": "Priya",
            "last_name": "Sharma",
            "email": "fac.sharma@university.edu",
            "phone": "9876543211",
            "designation": "Assistant Professor",
            "employment_type": EmploymentType.PERMANENT,
            "status": FacultyStatus.ACTIVE,
            "date_of_joining": date(2020, 7, 1),
            "qualification": "M.Tech in Software Engineering",
            "specialization": "Database Management Systems",
            "department": dept,
            "is_hod": False,
            "cabin_number": "CS-204"
        }
    )

    # 5. Verification Officer
    make_user("verifier", "verification.officer@university.edu", "VERIFICATION_OFFICER")

    # 6. Accountant
    make_user("accountant", "accounts@university.edu", "ACCOUNTANT")

    # 7. Exam Cell Officer
    make_user("exam_cell", "examcell@university.edu", "EXAM_CELL")

    # 8. Student User & Profile
    std_user, _ = User.objects.get_or_create(
        username="student_rohit",
        defaults={
            "email": "rohit.student@university.edu",
            "is_staff": False,
            "is_superuser": False,
            "must_change_password": False,
            "status": "ACTIVE"
        }
    )
    std_user.set_password(DEFAULT_PASSWORD)
    std_user.must_change_password = False
    std_user.save()
    UserRole.objects.get_or_create(
        user=std_user,
        role=roles["STUDENT"],
        defaults={"assigned_by": admin_user}
    )

    student, _ = Student.objects.get_or_create(
        enrollment_no="ENR2025COMP001",
        defaults={
            "user": std_user,
            "candidate_name": "Rohit Kumar",
            "father_name": "Suresh Kumar",
            "mother_name": "Sunita Kumar",
            "gender": "MALE",
            "date_of_birth": date(2004, 5, 12),
            "student_mobile": "9988776655",
            "email": "rohit.student@university.edu",
            "candidature_type": "GENERAL",
            "status": "ACTIVE"
        }
    )

    StudentEnrollment.objects.get_or_create(
        student=student,
        academic_year=ay,
        semester=sem,
        defaults={
            "department": dept,
            "program": prog,
            "batch": batch,
            "scheme": scheme,
            "status": "ACTIVE",
            "created_by": admin_user
        }
    )

    # Alias accounts matching role accountability guide
    # 1b. sysadmin alias
    sysadmin_u, _ = User.objects.get_or_create(
        username="sysadmin",
        defaults={
            "email": "sysadmin@university.edu",
            "is_staff": True,
            "is_superuser": True,
            "must_change_password": False,
            "status": "ACTIVE"
        }
    )
    sysadmin_u.set_password("Edvana@2026")
    sysadmin_u.must_change_password = False
    sysadmin_u.save()
    UserRole.objects.get_or_create(
        user=sysadmin_u,
        role=roles["SYSTEM_ADMIN"],
        defaults={"assigned_by": admin_user}
    )

    # 2b. administrative_head alias
    admin_head_u = make_user("administrative_head", "admin.head@university.edu", "COLLEGE_ADMIN")
    admin_head_u.set_password("Edvana@2026")
    admin_head_u.save()

    # 3b. Update hod_cs password
    hod_user.set_password("Edvana@2026")
    hod_user.save()

    # 4b. faculty_cs alias
    fac_cs_u = make_user("faculty_cs", "faculty.cs@university.edu", "FACULTY", scope_dept=dept)
    fac_cs_u.set_password("Edvana@2026")
    fac_cs_u.save()
    Faculty.objects.get_or_create(
        faculty_id="FAC-COMP-003",
        defaults={
            "user": fac_cs_u,
            "first_name": "Priya",
            "last_name": "Sharma",
            "email": "faculty.cs@university.edu",
            "phone": "9876543211",
            "designation": "Assistant Professor",
            "employment_type": EmploymentType.PERMANENT,
            "status": FacultyStatus.ACTIVE,
            "date_of_joining": date(2020, 7, 1),
            "qualification": "M.Tech in Software Engineering",
            "specialization": "Database Management Systems",
            "department": dept,
            "is_hod": False,
            "cabin_number": "CS-204"
        }
    )

    # 5b. verifier password
    v_u = User.objects.filter(username="verifier").first()
    if v_u:
        v_u.set_password("Edvana@2026")
        v_u.save()

    # 6b. accountant password
    acc_u = User.objects.filter(username="accountant").first()
    if acc_u:
        acc_u.set_password("Edvana@2026")
        acc_u.save()

    # 7b. examcell alias
    ec_u = make_user("examcell", "examcell.lead@university.edu", "EXAM_CELL")
    ec_u.set_password("Edvana@2026")
    ec_u.save()

    # 8b. student01 alias
    std01_u, _ = User.objects.get_or_create(
        username="student01",
        defaults={
            "email": "student01@university.edu",
            "is_staff": False,
            "is_superuser": False,
            "must_change_password": False,
            "status": "ACTIVE"
        }
    )
    std01_u.set_password("Edvana@2026")
    std01_u.must_change_password = False
    std01_u.save()
    UserRole.objects.get_or_create(
        user=std01_u,
        role=roles["STUDENT"],
        defaults={"assigned_by": admin_user}
    )
    std01_obj, _ = Student.objects.get_or_create(
        enrollment_no="ENR2025COMP002",
        defaults={
            "user": std01_u,
            "candidate_name": "Rohit Kumar",
            "father_name": "Suresh Kumar",
            "mother_name": "Sunita Kumar",
            "gender": "MALE",
            "date_of_birth": date(2004, 5, 12),
            "student_mobile": "9988776655",
            "email": "student01@university.edu",
            "candidature_type": "GENERAL",
            "status": "ACTIVE"
        }
    )
    StudentEnrollment.objects.get_or_create(
        student=std01_obj,
        academic_year=ay,
        semester=sem,
        defaults={
            "department": dept,
            "program": prog,
            "batch": batch,
            "scheme": scheme,
            "status": "ACTIVE",
            "created_by": admin_user
        }
    )
    StudentFeeAccount.objects.get_or_create(
        student=std01_obj,
        defaults={
            "total_billed": 75000,
            "total_paid": 50000,
            "outstanding_balance": 25000
        }
    )


def run():
    print("=" * 60)
    print("      SEEDING DEMO ACCOUNTS FOR ALL SYSTEM PROFILES      ")
    print("=" * 60)
    with transaction.atomic():
        roles = seed_canonical_rbac()
        academic_data = seed_academic_foundation()
        seed_accounts(roles, academic_data)
    print("=" * 60)
    print("DEMO ACCOUNTS CREATION COMPLETED SUCCESSFULLY!")
    print(f"Common Password for all accounts: {DEFAULT_PASSWORD}")
    print("=" * 60)


if __name__ == '__main__':
    run()
