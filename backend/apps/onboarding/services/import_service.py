"""
Onboarding and Import Service Orchestrator.
Fulfills Section 4 of doc/TASKS.md:
- Excel ingestion, hashing, and staging row preservation (Tasks 4.1.1 - 4.1.3)
- Validation, error logging, and normalization (Tasks 4.2.1 - 4.2.2)
- Deterministic identity matching and conflict management (Tasks 4.3.1 - 4.3.2)
- Production student import with idempotent creation/updates (Tasks 4.3.3 - 4.3.4)
- Student user account provisioning integration (Tasks 4.4.1 - 4.4.2)
- Multi-format Excel parser (HTML table .xls, real .xlsx, CSV)
- Choice-code auto-mapping for institutional programs
"""

import csv
import hashlib
import io
import logging
import re
from datetime import datetime, date
from html.parser import HTMLParser
from typing import Optional, List, Dict, Any, Tuple

import openpyxl
from django.db import transaction
from django.utils import timezone

from apps.onboarding.models import ImportBatch, ImportStagingRow
from apps.onboarding.domain.normalization import normalize_row_dict, clean_header_key
from apps.onboarding.domain.matching import match_staging_student
from apps.students.models import (
    Student,
    StudentAdmission,
    StudentAddress,
    StudentCategory,
    StudentEnrollment,
    StudentDataCorrection,
)
from apps.academic.models import AcademicYear, Department, Program, Semester, Scheme, Batch
from apps.identity.services.provisioning import StudentAccountProvisioningService
from common.security import encrypt_sensitive_value, mask_aadhaar
from common.exceptions import InvariantViolationError, StateTransitionError

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Choice-Code → Department/Program Auto-Mapping
# Maharashtra DTE/State CET Cell allotment files use choice codes to identify
# the program the candidate was allotted to.
# One department holds MANY choice codes (different seat types for the same
# dept, e.g. CSE has both 0603624211T and 603624210). The `T` suffix denotes
# one seat type (TFWS), the shorter/non-T code another — NOT two departments.
# No branch selection is needed at upload/execute time: each Excel row is
# mapped per-row via its choice code.
# ──────────────────────────────────────────────────────────────────────────────

CHOICE_CODE_MAP = {
    # Computer Science and Engineering
    '0603624211T': {'dept_code': 'CSE',  'dept_name': 'Computer Science and Engineering',                'program_code': 'CSE',  'seat_type_hint': 'TFWS'},
    '0603624210':  {'dept_code': 'CSE',  'dept_name': 'Computer Science and Engineering',                'program_code': 'CSE',  'seat_type_hint': 'CAP'},
    '603624210':   {'dept_code': 'CSE',  'dept_name': 'Computer Science and Engineering',                'program_code': 'CSE',  'seat_type_hint': 'CAP'},
    # Artificial Intelligence (AI) and Data Science
    '0603626311T': {'dept_code': 'AIDS', 'dept_name': 'Artificial Intelligence (AI) and Data Science',   'program_code': 'AIDS', 'seat_type_hint': 'TFWS'},
    '0603626310':  {'dept_code': 'AIDS', 'dept_name': 'Artificial Intelligence (AI) and Data Science',   'program_code': 'AIDS', 'seat_type_hint': 'CAP'},
    '603626310':   {'dept_code': 'AIDS', 'dept_name': 'Artificial Intelligence (AI) and Data Science',   'program_code': 'AIDS', 'seat_type_hint': 'CAP'},
    # Electrical Engineering
    '0603629311T': {'dept_code': 'EE',   'dept_name': 'Electrical Engineering',                          'program_code': 'EE',   'seat_type_hint': 'TFWS'},
    '0603629310':  {'dept_code': 'EE',   'dept_name': 'Electrical Engineering',                          'program_code': 'EE',   'seat_type_hint': 'CAP'},
    '603629310':   {'dept_code': 'EE',   'dept_name': 'Electrical Engineering',                          'program_code': 'EE',   'seat_type_hint': 'CAP'},
    # Electronics and Telecommunication Engineering
    '0603637211T': {'dept_code': 'ENTC', 'dept_name': 'Electronics and Telecommunication Engineering',   'program_code': 'ENTC', 'seat_type_hint': 'TFWS'},
    '0603637210':  {'dept_code': 'ENTC', 'dept_name': 'Electronics and Telecommunication Engineering',   'program_code': 'ENTC', 'seat_type_hint': 'CAP'},
    '603637210':   {'dept_code': 'ENTC', 'dept_name': 'Electronics and Telecommunication Engineering',   'program_code': 'ENTC', 'seat_type_hint': 'CAP'},
    # Mechanical and Automation Engineering
    '0603661511T': {'dept_code': 'MAE',  'dept_name': 'Mechanical and Automation Engineering',           'program_code': 'MAE',  'seat_type_hint': 'TFWS'},
    '0603661510':  {'dept_code': 'MAE',  'dept_name': 'Mechanical and Automation Engineering',           'program_code': 'MAE',  'seat_type_hint': 'CAP'},
    '603661510':   {'dept_code': 'MAE',  'dept_name': 'Mechanical and Automation Engineering',           'program_code': 'MAE',  'seat_type_hint': 'CAP'},
}


def _choice_code_candidates(choice_code: str) -> List[str]:
    """Raw + leading-zero-stripped + zero-padded variants (T / non-T kept distinct)."""
    raw = str(choice_code).strip().upper()
    cands = [raw]
    stripped = raw.lstrip('0')
    if stripped and stripped != raw:
        cands.append(stripped)
    if not raw.startswith('0') and raw:
        cands.append('0' + raw)
    return cands


def _mark_choice_code_on_department(dept: Department, choice_code: str) -> None:
    """Auto-mark: if dept master lacks this code, append it (idempotent)."""
    code = str(choice_code).strip().upper()
    if not code:
        return
    existing = dept.choice_codes or []
    existing_norm = {str(c).strip().upper() for c in existing}
    if code not in existing_norm:
        dept.choice_codes = [*existing, code]
        dept.save(update_fields=['choice_codes'])


def resolve_department_program_from_choice_code(choice_code: str) -> Tuple[Optional[Department], Optional[Program]]:
    """
    DB-first lookup: one department holds MANY choice codes (different seat
    types for the same dept, e.g. CSE has both 0603624211T and 603624210).
    1. Check Department.choice_codes in DB (all variants).
    2. Fall back to hardcoded CHOICE_CODE_MAP, auto-creating dept/program
       AND auto-marking (saving) the code onto the dept master.
    Returns (department, program) or (None, None) if unrecognized.
    """
    if not choice_code:
        return None, None

    candidates = _choice_code_candidates(choice_code)

    # 1. DB master lookup
    for dept in Department.objects.all():
        stored = {str(c).strip().upper() for c in (dept.choice_codes or [])}
        if not stored:
            continue
        stored_variants: set = set()
        for s in stored:
            stored_variants.add(s)
            if s.lstrip('0'):
                stored_variants.add(s.lstrip('0'))
        if any(c in stored_variants for c in candidates):
            _mark_choice_code_on_department(dept, choice_code)
            prog = Program.objects.filter(department=dept).first()
            if not prog:
                prog, _ = Program.objects.get_or_create(
                    department=dept,
                    code=dept.code,
                    defaults={'name': dept.name, 'duration_years': 4, 'degree_type': 'B.Tech', 'is_active': True},
                )
            return dept, prog

    # 2. Hardcoded fallback + auto-mark onto dept master
    mapping = None
    for c in candidates:
        if c in CHOICE_CODE_MAP:
            mapping = CHOICE_CODE_MAP[c]
            break
    if not mapping:
        return None, None

    dept, _ = Department.objects.get_or_create(
        code=mapping['dept_code'],
        defaults={'name': mapping['dept_name'], 'is_active': True}
    )
    prog, _ = Program.objects.get_or_create(
        department=dept,
        code=mapping['program_code'],
        defaults={
            'name': mapping['dept_name'],
            'duration_years': 4,
            'degree_type': 'B.Tech',
            'is_active': True,
        }
    )
    _mark_choice_code_on_department(dept, choice_code)
    return dept, prog


def get_seat_type_hint_for_choice_code(choice_code: str) -> Optional[str]:
    """Return TFWS/CAP hint for a choice code (`T` suffix = TFWS seat type)."""
    if not choice_code:
        return None
    for c in _choice_code_candidates(choice_code):
        if c in CHOICE_CODE_MAP:
            return CHOICE_CODE_MAP[c].get('seat_type_hint')
    # Fallback: T-suffix convention
    if str(choice_code).strip().upper().endswith('T'):
        return 'TFWS'
    return None


# ──────────────────────────────────────────────────────────────────────────────
# HTML Table Parser — handles DTE .xls files that are HTML tables
# ──────────────────────────────────────────────────────────────────────────────

class _HTMLTableParser(HTMLParser):
    """Lightweight parser that extracts the first <table> into a list of rows."""

    def __init__(self):
        super().__init__()
        self._rows: List[List[str]] = []
        self._current_row: Optional[List[str]] = None
        self._current_cell: Optional[list] = None
        self._in_table = False

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag == 'table':
            self._in_table = True
        elif tag == 'tr' and self._in_table:
            self._current_row = []
        elif tag in ('td', 'th') and self._current_row is not None:
            self._current_cell = []

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in ('td', 'th') and self._current_cell is not None:
            text = ''.join(self._current_cell).strip()
            self._current_row.append(text if text else None)
            self._current_cell = None
        elif tag == 'tr' and self._current_row is not None:
            self._rows.append(self._current_row)
            self._current_row = None
        elif tag == 'table':
            self._in_table = False

    def handle_data(self, data):
        if self._current_cell is not None:
            self._current_cell.append(data)

    def get_rows(self) -> List[List[str]]:
        return self._rows


def _parse_html_table(content: bytes) -> List[List[Optional[str]]]:
    """Parse an HTML file and return all rows from the first <table>."""
    # Try common encodings for Indian government portals
    text = None
    for encoding in ('utf-8', 'latin-1', 'cp1252', 'iso-8859-1'):
        try:
            text = content.decode(encoding)
            break
        except (UnicodeDecodeError, ValueError):
            continue
    if text is None:
        text = content.decode('utf-8', errors='replace')

    parser = _HTMLTableParser()
    parser.feed(text)
    return parser.get_rows()


def _detect_file_format(content: bytes) -> str:
    """
    Detect the actual format of the uploaded file:
    - 'xlsx' for real zipped Office Open XML
    - 'html' for HTML table (government .xls masquerade)
    - 'csv' for comma-separated values
    - 'xls_binary' for legacy BIFF .xls (not supported, raise helpful error)
    """
    if content[:4] == b'PK\x03\x04':
        return 'xlsx'

    # Check for HTML markers
    head = content[:2048].lower()
    if b'<table' in head or b'<html' in head or b'<tr' in head or b'<!doctype html' in head:
        return 'html'

    # Check for legacy binary BIFF8 format (starts with 0xD0CF11E0)
    if content[:4] == b'\xd0\xcf\x11\xe0':
        return 'xls_binary'

    # Check if it looks like CSV
    try:
        sample = content[:4096].decode('utf-8', errors='replace')
        if ',' in sample and '\n' in sample:
            return 'csv'
    except Exception:
        pass

    return 'unknown'


def _parse_file_to_rows(content: bytes) -> List[List[Optional[str]]]:
    """
    Detect file format and parse into a list of rows (list of cell values).
    Supports: real .xlsx, HTML table .xls, CSV.
    """
    fmt = _detect_file_format(content)
    logger.info(f"Detected file format: {fmt}")

    if fmt == 'xlsx':
        wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True)
        sheet = wb.active
        rows = []
        for row in sheet.iter_rows(values_only=True):
            rows.append([str(c).strip() if c is not None else None for c in row])
        return rows

    if fmt == 'html':
        return _parse_html_table(content)

    if fmt == 'csv':
        text = content.decode('utf-8', errors='replace')
        reader = csv.reader(io.StringIO(text))
        rows = []
        for row in reader:
            rows.append([c.strip() if c.strip() else None for c in row])
        return rows

    if fmt == 'xls_binary':
        raise InvariantViolationError(
            "Legacy binary .xls (BIFF) format detected. "
            "Please re-save the file as .xlsx or .csv before uploading."
        )

    raise InvariantViolationError(
        "Unrecognized file format. Supported formats: .xlsx, .xls (HTML table), .csv"
    )


class ImportService:
    """End-to-end management of student data onboarding."""

    @staticmethod
    def upload_and_stage_excel(
        file_obj,
        source_file_name: str,
        academic_year_id: Optional[str] = None,
        department_id: Optional[str] = None,
        uploaded_by=None
    ) -> ImportBatch:
        """
        Ingest an Excel/CSV/HTML-table file, compute content hash for idempotency,
        and preserve raw staging rows verbatim.

        The department_id is now optional. If the file contains choice codes,
        students are auto-mapped to departments during production import.
        """
        content = file_obj.read()
        file_hash = hashlib.sha256(content).hexdigest()

        # Create the ImportBatch (department_id is optional for college-wide uploads)
        batch = ImportBatch.objects.create(
            source_file_name=source_file_name,
            source_file_hash=file_hash,
            academic_year_id=academic_year_id,
            department_id=department_id,
            uploaded_by=uploaded_by,
            status='UPLOADED'
        )

        # Multi-format parse
        rows = _parse_file_to_rows(content)

        if not rows:
            batch.total_rows = 0
            batch.status = 'VALIDATED'
            batch.save(update_fields=['total_rows', 'status'])
            return batch

        headers = [str(cell).strip() if cell is not None else f"col_{idx}" for idx, cell in enumerate(rows[0])]

        staging_rows = []
        row_counter = 0
        for row_idx, row_values in enumerate(rows[1:], start=2):
            if not any(val is not None and str(val).strip() != '' for val in row_values):
                continue  # Skip entirely blank rows

            row_dict = {}
            for h, v in zip(headers, row_values):
                row_dict[h] = str(v).strip() if v is not None else None

            row_counter += 1
            staging_rows.append(
                ImportStagingRow(
                    import_batch=batch,
                    row_number=row_counter,
                    raw_data=row_dict,
                    processing_status='PENDING'
                )
            )

        ImportStagingRow.objects.bulk_create(staging_rows)
        batch.total_rows = len(staging_rows)
        batch.save(update_fields=['total_rows'])
        return batch

    @classmethod
    def validate_and_normalize_batch(cls, batch: ImportBatch) -> ImportBatch:
        """
        Normalize row data, apply schema validation, run deterministic identity matching,
        and flag invalid or conflicting records.
        """
        if batch.status not in ['UPLOADED', 'VALIDATING', 'VALIDATED']:
            raise StateTransitionError(batch.status, 'VALIDATING', ['UPLOADED', 'VALIDATED'])

        batch.status = 'VALIDATING'
        batch.save(update_fields=['status'])

        staging_rows = list(batch.staging_rows.all().order_by('row_number'))
        error_count = 0

        for row in staging_rows:
            normalized = normalize_row_dict(row.raw_data)
            errors = []

            # 1. Mandatory Fields Validation
            if not normalized.get('candidate_name'):
                errors.append("Candidate name is required.")
            if not normalized.get('gender') or normalized.get('gender') not in ['MALE', 'FEMALE', 'OTHER']:
                errors.append("Valid gender (MALE, FEMALE, OTHER) is required.")
            if not normalized.get('date_of_birth'):
                errors.append("Valid date of birth (YYYY-MM-DD) is required.")
            else:
                try:
                    datetime.strptime(normalized['date_of_birth'], '%Y-%m-%d')
                except ValueError:
                    errors.append("Date of birth must be a valid calendar date in YYYY-MM-DD format.")

            # 2. Length / format validations
            if 'student_mobile' in normalized and len(normalized['student_mobile']) != 10:
                errors.append("Student mobile number must be 10 digits.")
            if 'aadhaar_number' in normalized and len(normalized['aadhaar_number']) != 12:
                errors.append("Aadhaar number must be 12 digits.")

            row.normalized_data = normalized

            if errors:
                row.processing_status = 'INVALID'
                row.validation_errors = errors
                error_count += 1
                row.save(update_fields=['normalized_data', 'processing_status', 'validation_errors'])
                continue

            # 3. Deterministic Identity Matching
            match_type, matched_student, conflict_info = match_staging_student(normalized)
            row.match_type = match_type
            row.matched_student = matched_student
            row.conflict_details = conflict_info

            if match_type == 'CONFLICT':
                row.processing_status = 'CONFLICT'
                error_count += 1
            else:
                row.processing_status = 'VALIDATED'
                row.validation_errors = None

            row.save(update_fields=[
                'normalized_data',
                'processing_status',
                'match_type',
                'matched_student',
                'conflict_details',
                'validation_errors'
            ])

        batch.error_rows = error_count
        batch.status = 'VALIDATED'
        batch.save(update_fields=['status', 'error_rows'])
        return batch

    @staticmethod
    def resolve_staging_conflict(
        staging_row: ImportStagingRow,
        resolution_action: str,
        chosen_student_id: Optional[str] = None,
        resolved_by=None
    ) -> ImportStagingRow:
        """
        Manually resolve identity conflict for a staged student record.
        Supported actions:
        - 'LINK_TO_STUDENT': Explicitly associate row to chosen existing student record.
        - 'FORCE_AS_NEW': Clear association and create as distinct new student.
        - 'SKIP': Mark row as skipped.
        """
        if staging_row.processing_status != 'CONFLICT':
            raise InvariantViolationError("Only rows in CONFLICT status can be manually resolved.")

        if resolution_action == 'LINK_TO_STUDENT':
            if not chosen_student_id:
                raise InvariantViolationError("chosen_student_id is required to link to an existing student.")
            student = Student.objects.get(id=chosen_student_id)
            staging_row.matched_student = student
            staging_row.match_type = 'APPLICATION_ID'
            staging_row.processing_status = 'VALIDATED'
        elif resolution_action == 'FORCE_AS_NEW':
            staging_row.matched_student = None
            staging_row.match_type = 'NEW'
            staging_row.processing_status = 'VALIDATED'
        elif resolution_action == 'SKIP':
            staging_row.processing_status = 'SKIPPED'
        else:
            raise InvariantViolationError(f"Unsupported resolution action: {resolution_action}")

        staging_row.save(update_fields=['matched_student', 'match_type', 'processing_status'])
        return staging_row

    @classmethod
    def execute_production_import(
        cls,
        batch: ImportBatch,
        user=None,
        default_program_id: Optional[str] = None,
        default_semester_id: Optional[str] = None,
        default_scheme_id: Optional[str] = None,
        default_batch_id: Optional[str] = None
    ) -> ImportBatch:
        """
        Execute idempotent production migration for all validated staging rows.
        - Idempotently creates Student, StudentAdmission, StudentAddress, StudentCategory
        - Applies additive corrections if matching existing student
        - Provisions student user accounts per ADR-009
        - Creates initial StudentEnrollment if academic context provided
        """
        if batch.status not in ['VALIDATED', 'PARTIALLY_COMPLETED']:
            raise StateTransitionError(batch.status, 'IMPORTING', ['VALIDATED', 'PARTIALLY_COMPLETED'])

        batch.status = 'IMPORTING'
        batch.save(update_fields=['status'])

        rows_to_import = batch.staging_rows.filter(
            processing_status='VALIDATED'
        ).order_by('row_number')

        processed_count = batch.processed_rows

        # Fetch optional academic foundation objects
        program = Program.objects.filter(id=default_program_id).first() if default_program_id else None
        semester = Semester.objects.filter(id=default_semester_id).first() if default_semester_id else None
        scheme = Scheme.objects.filter(id=default_scheme_id).first() if default_scheme_id else None
        academic_batch = Batch.objects.filter(id=default_batch_id).first() if default_batch_id else None

        # Fallback academic context so every import yields an enrollment
        # (required for Student Directory dept filter + HOD scoped view).
        fallback_ay = (
            batch.academic_year
            or AcademicYear.objects.filter(is_current=True).first()
            or AcademicYear.objects.order_by('-start_date').first()
        )
        fallback_sem = (
            semester
            or (Semester.objects.filter(academic_year=fallback_ay).order_by('number').first() if fallback_ay else None)
        )

        for row in rows_to_import:
            data = row.normalized_data or {}

            with transaction.atomic():
                student = None

                if row.match_type == 'NEW':
                    # 1. Create Core Student Record
                    encrypted_aadhaar = None
                    masked_aadhaar = None
                    if 'aadhaar_number' in data:
                        encrypted_aadhaar = encrypt_sensitive_value(data['aadhaar_number'])
                        masked_aadhaar = mask_aadhaar(data['aadhaar_number'])

                    student = Student.objects.create(
                        candidate_name=data['candidate_name'],
                        gender=data['gender'],
                        date_of_birth=data['date_of_birth'],
                        application_id=data.get('application_id'),
                        enrollment_no=data.get('enrollment_no'),
                        board_enrollment_no=data.get('board_enrollment_no'),
                        father_name=data.get('father_name'),
                        mother_name=data.get('mother_name'),
                        student_mobile=data.get('student_mobile'),
                        parent_mobile=data.get('parent_mobile'),
                        email=data.get('email'),
                        religion=data.get('religion'),
                        mother_tongue=data.get('mother_tongue'),
                        candidature_type=data.get('candidature_type'),
                        aadhaar_encrypted=encrypted_aadhaar,
                        aadhaar_masked=masked_aadhaar,
                        data_source='GOVERNMENT',
                        created_by=user,
                        status='ACTIVE'
                    )

                    # 2. Student Address — only real Excel values, never invented
                    # defaults. Missing fields stay empty for the student to fill.
                    address_parts = [
                        data.get('address_line_1'),
                        data.get('address_line_2'),
                        data.get('address_line_3'),
                        data.get('address'),
                    ]
                    address_line = ', '.join(p for p in address_parts if p) or None
                    StudentAddress.objects.create(
                        student=student,
                        address_line=address_line,
                        state=data.get('state'),
                        district=data.get('district'),
                        taluka=data.get('taluka'),
                        village=data.get('village'),
                        pincode=data.get('pincode')
                    )

                    # 3. Student Category — only the real Excel value; empty when
                    # the file has none (student fills it later).
                    StudentCategory.objects.create(
                        student=student,
                        category=data.get('category') or '',
                        data_source='GOVERNMENT'
                    )

                    # 4. Student Admission — per-row choice-code auto-mapping.
                    # No branch selection needed: Excel holds mixed branches,
                    # each row maps via its own choice code (one dept = many codes).
                    target_dept = batch.department
                    target_program = program

                    # Try choice-code auto-mapping first (government allotment files)
                    raw_choice_code = data.get('choice_code')
                    choice_code = raw_choice_code or data.get('program_code')
                    if choice_code:
                        mapped_dept, mapped_prog = resolve_department_program_from_choice_code(choice_code)
                        if mapped_prog:
                            target_program = mapped_prog
                            target_dept = mapped_dept

                    # Fallback: try program_code lookup
                    if not target_program and 'program_code' in data:
                        target_program = Program.objects.filter(code=data['program_code']).first()
                        if target_program and not target_dept:
                            target_dept = target_program.department

                    if target_program:
                        # Preserve seat-type distinction: T-suffix = TFWS, else CAP,
                        # unless Excel already carries an explicit seat_type.
                        # Unknown stays empty for the student/staff to fill.
                        effective_seat_type = data.get('seat_type')
                        if not effective_seat_type and raw_choice_code:
                            effective_seat_type = get_seat_type_hint_for_choice_code(raw_choice_code)
                        admission_date = timezone.now().date()
                        if data.get('admission_date'):
                            try:
                                admission_date = datetime.strptime(data['admission_date'], '%Y-%m-%d').date()
                            except (ValueError, TypeError):
                                pass
                        StudentAdmission.objects.get_or_create(
                            student=student,
                            program=target_program,
                            defaults={
                                'admission_date': admission_date,
                                'admission_category': data.get('category'),
                                'seat_type': effective_seat_type,
                                'choice_code': str(raw_choice_code).strip().upper() if raw_choice_code else None,
                                'data_source': 'GOVERNMENT',
                            }
                        )

                else:
                    # Matched existing student -> Apply idempotent additive corrections
                    student = row.matched_student

                    # Additive updates: only populate empty fields from import
                    save_fields = []
                    for field in (
                        'student_mobile', 'parent_mobile', 'email',
                        'enrollment_no', 'board_enrollment_no',
                        'father_name', 'mother_name', 'religion',
                        'mother_tongue', 'candidature_type',
                    ):
                        if not getattr(student, field) and data.get(field):
                            setattr(student, field, data[field])
                            save_fields.append(field)

                    if save_fields:
                        student.updated_by = user
                        save_fields.append('updated_by')
                        student.save(update_fields=save_fields)

                # 5. Account Provisioning Integration (Tasks 4.4.1 & 4.4.2)
                # Use enrollment_no if present, else fall back to application_id
                # so govt imports (AppID only) still get a login.
                # Username = identifier, Password = identifier, must_change_password=True.
                login_id = (student.enrollment_no or student.application_id or '').strip() if student else ''
                if login_id and not student.user:
                    user_account, _ = StudentAccountProvisioningService.provision_student_account(
                        enrollment_number=login_id,
                        email=student.email,
                        assigned_by=user
                    )
                    student.user = user_account
                    student.save(update_fields=['user'])

                # 6. Academic Enrollment Creation (with fallbacks so Directory/HOD filters work)
                # Resolve per-row dept/program (choice-code wins, else Execute-modal defaults).
                row_program = target_program if row.match_type == 'NEW' else program
                row_dept = target_dept if row.match_type == 'NEW' else batch.department
                if row.match_type != 'NEW':
                    cc = data.get('choice_code') or data.get('program_code')
                    if cc:
                        md, mp = resolve_department_program_from_choice_code(cc)
                        if mp:
                            row_program, row_dept = mp, md
                    if not row_program and 'program_code' in data:
                        row_program = Program.objects.filter(code=data['program_code']).first()
                        if row_program and not row_dept:
                            row_dept = row_program.department
                if row_program and not row_dept:
                    row_dept = row_program.department
                if not row_program and row_dept:
                    row_program = Program.objects.filter(department=row_dept).first()

                row_ay = batch.academic_year or fallback_ay
                row_sem = semester or fallback_sem
                # Ensure semester belongs to row_ay; else pick first sem of row_ay
                if row_ay and row_sem and row_sem.academic_year_id != row_ay.id:
                    row_sem = Semester.objects.filter(academic_year=row_ay).order_by('number').first()
                if row_ay and not row_sem:
                    row_sem = Semester.objects.filter(academic_year=row_ay).order_by('number').first()
                    if not row_sem:
                        row_sem = Semester.objects.create(
                            academic_year=row_ay,
                            number=1,
                            label='Semester 1',
                        )
                row_batch = academic_batch
                if not row_batch and row_dept and row_ay:
                    row_batch = Batch.objects.filter(department=row_dept, academic_year=row_ay).first()
                    if not row_batch:
                        row_batch = Batch.objects.create(
                            department=row_dept,
                            academic_year=row_ay,
                            name=row_ay.label,
                            is_active=True,
                        )
                row_scheme = scheme
                if not row_scheme and row_program:
                    row_scheme = Scheme.objects.filter(program=row_program).first()
                    if not row_scheme and row_ay:
                        # Auto-create a default scheme so imports never block on missing curriculum
                        row_scheme, _ = Scheme.objects.get_or_create(
                            code=f"SCH-{row_ay.label}-{row_program.code}",
                            defaults={
                                'program': row_program,
                                'name': f"{row_program.code} Default Scheme {row_ay.label}",
                                'effective_from_year': row_ay,
                                'is_active': True,
                            },
                        )

                if row_ay and row_sem and row_dept and row_program and row_batch and row_scheme:
                    existing_enrollment = StudentEnrollment.objects.filter(
                        student=student,
                        academic_year=row_ay,
                        semester=row_sem
                    ).first()

                    if not existing_enrollment:
                        StudentEnrollment.objects.create(
                            student=student,
                            academic_year=row_ay,
                            semester=row_sem,
                            department=row_dept,
                            program=row_program,
                            batch=row_batch,
                            scheme=row_scheme,
                            status='ACTIVE',
                            created_by=user
                        )

                # Mark staging row as IMPORTED
                row.matched_student = student
                row.processing_status = 'IMPORTED'
                row.save(update_fields=['matched_student', 'processing_status'])
                processed_count += 1

        batch.processed_rows = processed_count

        # Evaluate final batch state
        unresolved_count = batch.staging_rows.filter(
            processing_status__in=['INVALID', 'CONFLICT', 'PENDING']
        ).count()

        if unresolved_count > 0:
            batch.status = 'PARTIALLY_COMPLETED'
        else:
            batch.status = 'COMPLETED'

        batch.completed_at = timezone.now()
        batch.save(update_fields=['status', 'processed_rows', 'completed_at'])
        return batch
