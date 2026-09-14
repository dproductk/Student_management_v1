import csv
import io
import uuid
from decimal import Decimal
from typing import List, Dict, Any, Optional
from django.db import transaction
from django.utils import timezone

from apps.academic.models import AcademicYear, Semester, Department, Program, SchemeSubject
from apps.students.models import Student, StudentEnrollment
from apps.results.models import (
    ResultImportBatch,
    ResultImportRow,
    StudentResult,
    StudentResultDetail,
    ResultCorrectionRequest,
    ResultCorrectionAudit,
)
from apps.results.domain.invariants import (
    ResultValidationError,
    ResultImmutabilityViolation,
    InvalidLifecycleTransitionError,
    validate_batch_transition,
    validate_result_transition,
    validate_mark_values,
    calculate_grade_and_points,
)


class ResultService:

    @staticmethod
    def create_import_batch(
        academic_year_id: str,
        semester_id: str,
        department_id: str,
        program_id: str,
        file_name: str,
        uploaded_by,
        remarks: str = ""
    ) -> ResultImportBatch:
        """Creates an initial import batch in PENDING state."""
        return ResultImportBatch.objects.create(
            academic_year_id=academic_year_id,
            semester_id=semester_id,
            department_id=department_id,
            program_id=program_id,
            file_name=file_name,
            uploaded_by=uploaded_by,
            status='PENDING',
            remarks=remarks
        )

    @staticmethod
    def extract_and_stage_rows(
        batch: ResultImportBatch,
        rows_data: List[Dict[str, Any]]
    ) -> List[ResultImportRow]:
        """
        Populates ResultImportRow staging records from parsed tabular data.
        Transitions batch to PROCESSING.
        """
        if not rows_data:
            raise ResultValidationError("Cannot stage empty result rows.")

        validate_batch_transition(batch.status, 'PROCESSING')

        created_rows = []
        with transaction.atomic():
            for idx, row in enumerate(rows_data, start=1):
                student_ident = str(
                    row.get('student_identifier') or
                    row.get('enrollment_no') or
                    row.get('application_id') or
                    row.get('seat_no') or ''
                ).strip()

                subject_code = str(row.get('subject_code') or row.get('course_code') or '').strip()

                internal_raw = row.get('internal_marks')
                external_raw = row.get('external_marks')
                total_raw = row.get('total_marks')
                is_absent = bool(row.get('is_absent', False) or str(row.get('grade', '')).upper() == 'AB')

                def parse_dec(val):
                    if val is None or val == '':
                        return None
                    try:
                        return Decimal(str(val))
                    except Exception:
                        return None

                internal_dec = parse_dec(internal_raw)
                external_dec = parse_dec(external_raw)
                total_dec = parse_dec(total_raw)

                if total_dec is None and internal_dec is not None and external_dec is not None:
                    total_dec = internal_dec + external_dec

                staging_row = ResultImportRow.objects.create(
                    batch=batch,
                    row_number=idx,
                    raw_data=row,
                    student_identifier=student_ident,
                    subject_code=subject_code,
                    internal_marks=internal_dec,
                    external_marks=external_dec,
                    total_marks=total_dec,
                    grade=str(row.get('grade') or '').strip().upper(),
                    is_absent=is_absent,
                    status='PENDING'
                )
                created_rows.append(staging_row)

            batch.status = 'PROCESSING'
            batch.total_rows = len(created_rows)
            batch.save(update_fields=['status', 'total_rows', 'updated_at'])

        return created_rows

    @staticmethod
    def parse_csv_content(csv_text: str) -> List[Dict[str, Any]]:
        """Parses CSV text into list of row dictionaries."""
        reader = csv.DictReader(io.StringIO(csv_text.strip()))
        rows = []
        for row in reader:
            cleaned = {k.strip(): v.strip() for k, v in row.items() if k}
            rows.append(cleaned)
        return rows

    @staticmethod
    def validate_and_associate_rows(batch: ResultImportBatch) -> Dict[str, Any]:
        """
        Validates all staging rows for a batch, associates with students and subjects,
        and generates StudentResult & StudentResultDetail records in DRAFT.
        """
        validate_batch_transition(batch.status, 'VALIDATED')

        rows = list(batch.rows.all().order_by('row_number'))
        if not rows:
            batch.status = 'FAILED'
            batch.remarks = 'Batch contains no staging rows.'
            batch.save(update_fields=['status', 'remarks', 'updated_at'])
            return {'success': False, 'message': 'No rows to validate'}

        valid_count = 0
        error_count = 0

        # Cache scheme subjects for this program/semester to optimize lookups
        scheme_subjects = list(SchemeSubject.objects.filter(
            scheme__program=batch.program,
            semester_number=batch.semester.number
        ).select_related('subject'))
        subject_map = {ss.subject.code.strip().upper(): ss for ss in scheme_subjects}

        with transaction.atomic():
            for row in rows:
                errors = []

                if not row.student_identifier:
                    errors.append("Missing student identifier.")
                if not row.subject_code:
                    errors.append("Missing subject code.")

                matched_student = None
                if row.student_identifier:
                    # Deterministic matching: 1. enrollment_no, 2. application_id, 3. university_reg_no
                    matched_student = Student.objects.filter(enrollment_no=row.student_identifier).first()
                    if not matched_student:
                        matched_student = Student.objects.filter(application_id=row.student_identifier).first()
                    if not matched_student and hasattr(Student, 'university_reg_no'):
                        matched_student = Student.objects.filter(university_reg_no=row.student_identifier).first()

                    if not matched_student:
                        errors.append(f"No student record matched identifier '{row.student_identifier}'.")
                    else:
                        # Verify academic enrollment
                        is_enrolled = StudentEnrollment.objects.filter(
                            student=matched_student,
                            academic_year=batch.academic_year,
                            semester=batch.semester,
                            status='ACTIVE'
                        ).exists()
                        if not is_enrolled:
                            errors.append(
                                f"Student '{matched_student.enrollment_no}' has no active enrollment in {batch.academic_year.label} Sem {batch.semester.number}."
                            )

                # Match SchemeSubject
                matched_ss = subject_map.get(row.subject_code.strip().upper())
                if not matched_ss:
                    matched_ss = SchemeSubject.objects.filter(
                        subject__code__iexact=row.subject_code.strip(),
                        semester_number=batch.semester.number
                    ).first()

                if not matched_ss:
                    errors.append(f"Subject code '{row.subject_code}' not found in curriculum for Semester {batch.semester.number}.")

                # Validate marks and grades
                max_marks = Decimal('100.00')
                if matched_ss and hasattr(matched_ss, 'max_marks') and matched_ss.max_marks:
                    max_marks = Decimal(str(matched_ss.max_marks))

                try:
                    if row.internal_marks is None and not row.is_absent:
                        errors.append("Internal marks must be specified or student marked absent.")
                    if row.external_marks is None and not row.is_absent:
                        errors.append("External marks must be specified or student marked absent.")

                    if not errors:
                        total = validate_mark_values(
                            internal_marks=row.internal_marks,
                            external_marks=row.external_marks,
                            max_marks=max_marks,
                            is_absent=row.is_absent
                        )
                        grade_letter, grade_pts, outcome = calculate_grade_and_points(
                            total_marks=total,
                            max_marks=max_marks,
                            is_absent=row.is_absent
                        )
                        row.total_marks = total
                        row.grade = grade_letter
                        row.grade_points = grade_pts
                except ResultValidationError as e:
                    errors.append(str(e))

                row.matched_student = matched_student
                row.matched_scheme_subject = matched_ss
                row.validation_errors = errors

                if errors:
                    row.status = 'INVALID'
                    error_count += 1
                else:
                    row.status = 'VALID'
                    valid_count += 1

                row.save()

            batch.valid_rows = valid_count
            batch.error_rows = error_count

            if error_count > 0:
                batch.status = 'FAILED'
                batch.remarks = f"Validation failed with {error_count} error rows."
                batch.save(update_fields=['status', 'valid_rows', 'error_rows', 'remarks', 'updated_at'])
                return {
                    'success': False,
                    'valid_rows': valid_count,
                    'error_rows': error_count,
                    'message': f"Validation failed with {error_count} errors. Review row errors."
                }

            # If all rows valid, transition to VALIDATED and generate DRAFT student results
            batch.status = 'VALIDATED'
            batch.remarks = f"All {valid_count} rows successfully validated and associated."
            batch.save(update_fields=['status', 'valid_rows', 'error_rows', 'remarks', 'updated_at'])

            ResultService._generate_draft_results_from_batch(batch, rows)

        return {
            'success': True,
            'valid_rows': valid_count,
            'error_rows': 0,
            'message': f"Batch validated successfully. Draft results generated."
        }

    @staticmethod
    def _generate_draft_results_from_batch(batch: ResultImportBatch, rows: List[ResultImportRow]):
        """Internal helper to assemble StudentResult & StudentResultDetail records in DRAFT."""
        # Group rows by student
        from collections import defaultdict
        student_rows = defaultdict(list)
        for r in rows:
            student_rows[r.matched_student].append(r)

        for student, s_rows in student_rows.items():
            # Check existing draft result from same batch or create new
            res = StudentResult.objects.filter(
                student=student,
                academic_year=batch.academic_year,
                semester=batch.semester,
                is_latest=True,
                status='DRAFT'
            ).first()

            if not res:
                res = StudentResult.objects.create(
                    student=student,
                    academic_year=batch.academic_year,
                    semester=batch.semester,
                    version=1,
                    is_latest=True,
                    status='DRAFT',
                    import_batch=batch
                )
            else:
                res.details.all().delete()

            total_obtained = Decimal('0.00')
            total_max = Decimal('0.00')
            has_fail = False

            for r in s_rows:
                ss = r.matched_scheme_subject
                max_m = Decimal(str(ss.max_marks)) if ss and hasattr(ss, 'max_marks') and ss.max_marks else Decimal('100.00')
                subj_name = ss.subject.name if ss else r.subject_code

                total_obtained += (r.total_marks or Decimal('0.00'))
                total_max += max_m

                if r.is_absent or r.grade == 'F':
                    has_fail = True

                StudentResultDetail.objects.create(
                    student_result=res,
                    scheme_subject=ss,
                    subject_code=r.subject_code,
                    subject_name=subj_name,
                    internal_marks=r.internal_marks or Decimal('0.00'),
                    external_marks=r.external_marks or Decimal('0.00'),
                    total_marks=r.total_marks or Decimal('0.00'),
                    max_marks=max_m,
                    grade=r.grade,
                    grade_points=r.grade_points or Decimal('0.00'),
                    is_absent=r.is_absent,
                    status='ABSENT' if r.is_absent else ('FAIL' if r.grade == 'F' else 'PASS')
                )

            percentage = Decimal('0.00')
            if total_max > Decimal('0.00'):
                percentage = (total_obtained / total_max) * Decimal('100.00')

            res.total_marks_obtained = total_obtained
            res.total_max_marks = total_max
            res.percentage = percentage
            res.result_status = 'FAIL' if has_fail else 'PASS'
            res.save()

    @staticmethod
    def approve_result_batch(batch: ResultImportBatch, user) -> ResultImportBatch:
        """Transitions batch and its student results to APPROVED."""
        validate_batch_transition(batch.status, 'APPROVED')

        with transaction.atomic():
            batch.status = 'APPROVED'
            batch.approved_by = user
            batch.approved_at = timezone.now()
            batch.save(update_fields=['status', 'approved_by', 'approved_at', 'updated_at'])

            # Update associated student results from DRAFT to APPROVED
            StudentResult.objects.filter(
                import_batch=batch,
                status='DRAFT'
            ).update(status='APPROVED')

        return batch

    @staticmethod
    def publish_result_batch(batch: ResultImportBatch, user) -> ResultImportBatch:
        """
        Transitions approved results to PUBLISHED.
        Marks are now visible in the student portal.
        """
        validate_batch_transition(batch.status, 'PUBLISHED')

        now = timezone.now()
        with transaction.atomic():
            batch.status = 'PUBLISHED'
            batch.published_by = user
            batch.published_at = now
            batch.save(update_fields=['status', 'published_by', 'published_at', 'updated_at'])

            StudentResult.objects.filter(
                import_batch=batch,
                status='APPROVED'
            ).update(
                status='PUBLISHED',
                published_by=user,
                published_at=now
            )

        # Trigger Result-to-Credit calculation for all published results in batch
        from apps.results.services.credit_eligibility_service import CreditEligibilityService
        CreditEligibilityService.calculate_batch_credits(batch, user=user)

        return batch

    @staticmethod
    def get_student_published_results(
        student: Student,
        academic_year_id: Optional[str] = None,
        semester_id: Optional[str] = None
    ) -> List[StudentResult]:
        """
        Scoped query for student self-portal.
        Strictly returns only PUBLISHED, latest version results.
        """
        qs = StudentResult.objects.filter(
            student=student,
            status='PUBLISHED',
            is_latest=True
        ).select_related(
            'academic_year', 'semester', 'batch'
        ).prefetch_related('details').order_by('-academic_year__start_date', 'semester__number')

        if academic_year_id:
            qs = qs.filter(academic_year_id=academic_year_id)
        if semester_id:
            qs = qs.filter(semester_id=semester_id)

        return list(qs)

    @staticmethod
    def request_result_correction(
        target_result: StudentResult,
        requested_by,
        reason: str,
        proposed_changes: Dict[str, Any]
    ) -> ResultCorrectionRequest:
        """
        Initiates an official correction workflow for a PUBLISHED result.
        """
        if target_result.status != 'PUBLISHED':
            raise ResultValidationError(
                f"Correction can only be requested on 'PUBLISHED' results. Current status is '{target_result.status}'."
            )

        if not reason or not reason.strip():
            raise ResultValidationError("A mandatory justification reason must be provided for result correction.")

        return ResultCorrectionRequest.objects.create(
            target_result=target_result,
            requested_by=requested_by,
            reason=reason.strip(),
            proposed_changes=proposed_changes or {},
            status='PENDING'
        )

    @staticmethod
    def review_result_correction(
        correction_request: ResultCorrectionRequest,
        reviewer,
        approved: bool,
        review_remarks: str = ""
    ) -> ResultCorrectionRequest:
        """
        Reviews a pending correction request. If approved, applies V2 supersession.
        """
        if correction_request.status != 'PENDING':
            raise ResultValidationError(
                f"Correction request is already '{correction_request.status}'."
            )

        now = timezone.now()
        with transaction.atomic():
            correction_request.reviewed_by = reviewer
            correction_request.reviewed_at = now
            correction_request.review_remarks = review_remarks

            if not approved:
                correction_request.status = 'REJECTED'
                correction_request.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'review_remarks', 'updated_at'])
                return correction_request

            correction_request.status = 'APPROVED'
            correction_request.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'review_remarks', 'updated_at'])

            # Spawn V2 superseding result
            ResultService._apply_result_supersession(correction_request, reviewer)

        return correction_request

    @staticmethod
    def _apply_result_supersession(
        correction_request: ResultCorrectionRequest,
        reviewer
    ) -> StudentResult:
        """
        Creates Result V2 superseding V1.
        V1 is preserved historically with is_latest=False, superseded_by=V2, status=SUPERSEDED.
        V2 is created with version=V1.version + 1, is_latest=True, status=PUBLISHED.
        Records an immutable ResultCorrectionAudit entry.
        """
        v1 = correction_request.target_result
        now = timezone.now()

        # Create V2 as a copy of V1 with version incremented
        v2 = StudentResult.objects.create(
            student=v1.student,
            academic_year=v1.academic_year,
            semester=v1.semester,
            batch=v1.batch,
            version=v1.version + 1,
            is_latest=True,
            status='PUBLISHED',
            import_batch=v1.import_batch,
            published_by=reviewer,
            published_at=now
        )

        proposed_subject_updates = correction_request.proposed_changes.get('subjects', {})
        total_obtained = Decimal('0.00')
        total_max = Decimal('0.00')
        has_fail = False

        # Copy over details, applying proposed changes where present
        for d in v1.details.all():
            subj_code = d.subject_code
            internal = d.internal_marks
            external = d.external_marks
            is_absent = d.is_absent

            if subj_code in proposed_subject_updates:
                updates = proposed_subject_updates[subj_code]
                if 'internal_marks' in updates:
                    internal = Decimal(str(updates['internal_marks']))
                if 'external_marks' in updates:
                    external = Decimal(str(updates['external_marks']))
                if 'is_absent' in updates:
                    is_absent = bool(updates['is_absent'])

            tot = validate_mark_values(internal, external, d.max_marks, is_absent)
            grade_l, grade_p, outcome = calculate_grade_and_points(tot, d.max_marks, is_absent)

            total_obtained += tot
            total_max += d.max_marks
            if is_absent or grade_l == 'F':
                has_fail = True

            StudentResultDetail.objects.create(
                student_result=v2,
                scheme_subject=d.scheme_subject,
                subject_code=d.subject_code,
                subject_name=d.subject_name,
                internal_marks=internal,
                external_marks=external,
                total_marks=tot,
                max_marks=d.max_marks,
                grade=grade_l,
                grade_points=grade_p,
                credits_earned=d.credits_earned,
                is_absent=is_absent,
                status=outcome
            )

        pct = Decimal('0.00')
        if total_max > Decimal('0.00'):
            pct = (total_obtained / total_max) * Decimal('100.00')

        v2.total_marks_obtained = total_obtained
        v2.total_max_marks = total_max
        v2.percentage = pct
        v2.result_status = 'FAIL' if has_fail else 'PASS'
        v2.save()

        # Update V1 to superseded (use direct update to bypass immutability guard during supersession)
        StudentResult.objects.filter(id=v1.id).update(
            superseded_by=v2,
            is_latest=False,
            status='SUPERSEDED'
        )

        # Audit trail
        ResultCorrectionAudit.objects.create(
            original_result=v1,
            superseding_result=v2,
            correction_request=correction_request,
            actor=reviewer,
            action='RESULT_SUPERSEDED',
            reason=correction_request.reason
        )

        # Recalculate credits for V2 and preserve V1's historical credit record
        from apps.results.services.credit_eligibility_service import CreditEligibilityService
        CreditEligibilityService.calculate_credits_for_result(v2, user=reviewer)

        return v2
