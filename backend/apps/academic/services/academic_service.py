"""
Service layer for Academic Foundation master data and curriculum management.
"""

from django.db import transaction
from django.db.models import Q
from common.exceptions import InvariantViolationError, EntityNotFoundError
from apps.academic.models import (
    Department,
    Program,
    AcademicYear,
    Semester,
    Batch,
    DepartmentIntake,
    Scheme,
    Subject,
    SchemeSubject,
)


class AcademicService:
    """Business operations for departments, programs, calendar, batches, and curricula."""

    @staticmethod
    def create_department(name: str, code: str, is_active: bool = True) -> Department:
        name = name.strip()
        code = code.strip().upper()
        if Department.objects.filter(code__iexact=code).exists():
            raise InvariantViolationError(f"Department code '{code}' is already in use.")
        if Department.objects.filter(name__iexact=name).exists():
            raise InvariantViolationError(f"Department name '{name}' is already in use.")
        return Department.objects.create(name=name, code=code, is_active=is_active)

    @staticmethod
    def create_program(department_id, name: str, code: str, duration_years: int = 4, degree_type: str = 'B.Tech') -> Program:
        name = name.strip()
        code = code.strip().upper()
        department = Department.objects.filter(id=department_id).first()
        if not department:
            raise EntityNotFoundError("Department not found.")
        if Program.objects.filter(department=department, code__iexact=code).exists():
            raise InvariantViolationError(f"Program with code '{code}' already exists in department '{department.code}'.")
        return Program.objects.create(
            department=department,
            name=name,
            code=code,
            duration_years=duration_years,
            degree_type=degree_type
        )

    @staticmethod
    def create_academic_year(label: str, start_date, end_date, is_current: bool = False) -> AcademicYear:
        label = label.strip()
        if AcademicYear.objects.filter(label__iexact=label).exists():
            raise InvariantViolationError(f"Academic year '{label}' already exists.")
        return AcademicYear.objects.create(
            label=label,
            start_date=start_date,
            end_date=end_date,
            is_current=is_current
        )

    @staticmethod
    def create_semester(academic_year_id, number: int, label: str = None, start_date=None, end_date=None) -> Semester:
        ay = AcademicYear.objects.filter(id=academic_year_id).first()
        if not ay:
            raise EntityNotFoundError("Academic year not found.")
        if Semester.objects.filter(academic_year=ay, number=number).exists():
            raise InvariantViolationError(f"Semester {number} already exists for academic year {ay.label}.")
        return Semester.objects.create(
            academic_year=ay,
            number=number,
            label=label or f"Semester {number}",
            start_date=start_date,
            end_date=end_date
        )

    @staticmethod
    def create_batch(department_id, academic_year_id, name: str) -> Batch:
        name = name.strip()
        department = Department.objects.filter(id=department_id).first()
        if not department:
            raise EntityNotFoundError("Department not found.")
        ay = AcademicYear.objects.filter(id=academic_year_id).first()
        if not ay:
            raise EntityNotFoundError("Academic year not found.")
        if Batch.objects.filter(department=department, academic_year=ay, name__iexact=name).exists():
            raise InvariantViolationError(f"Batch '{name}' already exists in department '{department.code}' for year '{ay.label}'.")
        return Batch.objects.create(department=department, academic_year=ay, name=name)

    @staticmethod
    def create_intake(department_id, academic_year_id, program_id, sanctioned_intake: int, actual_intake: int = None) -> DepartmentIntake:
        department = Department.objects.filter(id=department_id).first()
        if not department:
            raise EntityNotFoundError("Department not found.")
        ay = AcademicYear.objects.filter(id=academic_year_id).first()
        if not ay:
            raise EntityNotFoundError("Academic year not found.")
        program = Program.objects.filter(id=program_id, department=department).first()
        if not program:
            raise EntityNotFoundError("Program not found or does not belong to department.")
        
        intake, created = DepartmentIntake.objects.update_or_create(
            department=department,
            academic_year=ay,
            program=program,
            defaults={
                'sanctioned_intake': sanctioned_intake,
                'actual_intake': actual_intake
            }
        )
        return intake

    @staticmethod
    def create_subject(name: str, code: str) -> Subject:
        name = name.strip()
        code = code.strip().upper()
        if Subject.objects.filter(code__iexact=code).exists():
            raise InvariantViolationError(f"Subject with code '{code}' already exists.")
        return Subject.objects.create(name=name, code=code)

    @staticmethod
    def create_scheme(program_id, effective_from_year_id, name: str, code: str) -> Scheme:
        name = name.strip()
        code = code.strip().upper()
        program = Program.objects.filter(id=program_id).first()
        if not program:
            raise EntityNotFoundError("Program not found.")
        ay = AcademicYear.objects.filter(id=effective_from_year_id).first()
        if not ay:
            raise EntityNotFoundError("Academic year not found.")
        if Scheme.objects.filter(code__iexact=code).exists():
            raise InvariantViolationError(f"Scheme code '{code}' already exists.")
        return Scheme.objects.create(
            program=program,
            effective_from_year=ay,
            name=name,
            code=code
        )

    @staticmethod
    def add_scheme_subject(scheme_id, subject_id, semester_number: int, **kwargs) -> SchemeSubject:
        scheme = Scheme.objects.filter(id=scheme_id).first()
        if not scheme:
            raise EntityNotFoundError("Scheme not found.")
        subject = Subject.objects.filter(id=subject_id).first()
        if not subject:
            raise EntityNotFoundError("Subject not found.")
        if SchemeSubject.objects.filter(scheme=scheme, subject=subject, semester_number=semester_number).exists():
            raise InvariantViolationError(f"Subject '{subject.code}' is already added to Semester {semester_number} of Scheme '{scheme.code}'.")
        
        return SchemeSubject.objects.create(
            scheme=scheme,
            subject=subject,
            semester_number=semester_number,
            **kwargs
        )

    @staticmethod
    def search_master_data(query: str = '', department_id: str = None, academic_year_id: str = None):
        """Unified query search across departments, programs, schemes, and subjects."""
        results = {
            'departments': [],
            'programs': [],
            'schemes': [],
            'subjects': [],
            'batches': []
        }
        q = query.strip()
        
        dept_qs = Department.objects.all()
        if q:
            dept_qs = dept_qs.filter(Q(name__icontains=q) | Q(code__icontains=q))
        results['departments'] = list(dept_qs.values('id', 'name', 'code', 'is_active'))

        prog_qs = Program.objects.select_related('department')
        if department_id:
            prog_qs = prog_qs.filter(department_id=department_id)
        if q:
            prog_qs = prog_qs.filter(Q(name__icontains=q) | Q(code__icontains=q))
        results['programs'] = [
            {
                'id': str(p.id),
                'name': p.name,
                'code': p.code,
                'degree_type': p.degree_type,
                'duration_years': p.duration_years,
                'department_code': p.department.code,
                'department_name': p.department.name
            }
            for p in prog_qs
        ]

        subj_qs = Subject.objects.all()
        if q:
            subj_qs = subj_qs.filter(Q(name__icontains=q) | Q(code__icontains=q))
        results['subjects'] = list(subj_qs.values('id', 'name', 'code'))

        scheme_qs = Scheme.objects.select_related('program', 'effective_from_year')
        if q:
            scheme_qs = scheme_qs.filter(Q(name__icontains=q) | Q(code__icontains=q))
        results['schemes'] = [
            {
                'id': str(s.id),
                'name': s.name,
                'code': s.code,
                'program_code': s.program.code,
                'effective_from': s.effective_from_year.label,
                'is_active': s.is_active
            }
            for s in scheme_qs
        ]

        batch_qs = Batch.objects.select_related('department', 'academic_year')
        if department_id:
            batch_qs = batch_qs.filter(department_id=department_id)
        if academic_year_id:
            batch_qs = batch_qs.filter(academic_year_id=academic_year_id)
        if q:
            batch_qs = batch_qs.filter(name__icontains=q)
        results['batches'] = [
            {
                'id': str(b.id),
                'name': b.name,
                'department_code': b.department.code,
                'academic_year': b.academic_year.label,
                'is_active': b.is_active
            }
            for b in batch_qs
        ]

        return results
