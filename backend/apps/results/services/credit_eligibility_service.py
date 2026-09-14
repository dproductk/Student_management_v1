import uuid
from decimal import Decimal
from typing import List, Dict, Any, Optional
from django.db import transaction
from django.utils import timezone

from apps.academic.models import AcademicYear, Semester, Program, SchemeSubject
from apps.students.models import Student, StudentEnrollment
from apps.results.models import (
    StudentResult,
    StudentResultDetail,
    StudentCredit,
    EligibilityRule,
    EligibilityDecision,
    NextYearEligibilityList,
    ResultImportBatch,
)
from apps.results.domain.invariants import (
    CreditCalculationError,
    EligibilityValidationError,
    ResultImmutabilityViolation,
    validate_eligibility_rule_invariants,
)


class CreditEligibilityService:
    """
    Core domain service orchestrating:
    1. Result-to-credit calculation and historical versioning.
    2. Configurable eligibility rule definition and version management.
    3. Student eligibility and detention decision engine.
    4. Next-year promotion list generation from active StudentEnrollments.
    """

    @staticmethod
    def calculate_credits_for_result(
        result: StudentResult,
        user=None
    ) -> StudentCredit:
        """
        Calculates earned and attempted credits from a PUBLISHED StudentResult.
        Preserves historical credit calculations across result versions.
        """
        if result.status not in ('PUBLISHED', 'SUPERSEDED'):
            raise CreditCalculationError(
                f"Credit calculation rejected: Result status is '{result.status}'. "
                f"Credits can only be derived from published official results."
            )

        details = list(result.details.select_related('scheme_subject').all())
        if not details:
            raise CreditCalculationError(
                f"Cannot calculate credits: Result for student {result.student.enrollment_no} has no subject details."
            )

        total_attempted = Decimal('0.0')
        total_earned = Decimal('0.0')
        total_weighted_points = Decimal('0.00')
        backlogs = 0

        with transaction.atomic():
            for d in details:
                # Resolve subject credit weighting from SchemeSubject or fallback
                subj_credits = Decimal('3.0')
                if d.scheme_subject and hasattr(d.scheme_subject, 'credits') and d.scheme_subject.credits:
                    subj_credits = Decimal(str(d.scheme_subject.credits))
                elif d.credits_earned and d.credits_earned > Decimal('0.0'):
                    subj_credits = d.credits_earned

                total_attempted += subj_credits

                # Credit is earned only if subject is passed and candidate was present
                is_passed = (d.status == 'PASS' and not d.is_absent and d.grade != 'F')
                if is_passed:
                    earned = subj_credits
                    total_earned += earned
                else:
                    earned = Decimal('0.0')
                    backlogs += 1

                # Update subject detail credit record if needed
                if d.credits_earned != earned:
                    StudentResultDetail.objects.filter(id=d.id).update(credits_earned=earned)

                grade_pts = d.grade_points if d.grade_points is not None else Decimal('0.00')
                total_weighted_points += (grade_pts * subj_credits)

            # Calculate SGPA (Semester Grade Point Average)
            sgpa = Decimal('0.00')
            if total_attempted > Decimal('0.0'):
                sgpa = round(total_weighted_points / total_attempted, 2)

            # Calculate CGPA (Cumulative GPA across all published latest results up to this semester)
            prior_results = StudentResult.objects.filter(
                student=result.student,
                status='PUBLISHED',
                is_latest=True
            ).exclude(id=result.id).prefetch_related('details__scheme_subject')

            cum_attempted = total_attempted
            cum_earned = total_earned
            cum_weighted_pts = total_weighted_points

            for pr in prior_results:
                for pd in pr.details.all():
                    p_cred = Decimal('3.0')
                    if pd.scheme_subject and hasattr(pd.scheme_subject, 'credits') and pd.scheme_subject.credits:
                        p_cred = Decimal(str(pd.scheme_subject.credits))
                    cum_attempted += p_cred
                    if pd.status == 'PASS' and not pd.is_absent and pd.grade != 'F':
                        cum_earned += p_cred
                    p_pts = pd.grade_points if pd.grade_points is not None else Decimal('0.00')
                    cum_weighted_pts += (p_pts * p_cred)

            cgpa = Decimal('0.00')
            if cum_attempted > Decimal('0.0'):
                cgpa = round(cum_weighted_pts / cum_attempted, 2)

            # Update SGPA/CGPA on student result for fast reporting queries
            StudentResult.objects.filter(id=result.id).update(sgpa=sgpa, cgpa=cgpa)

            # Manage historical versioning for StudentCredit
            existing_credits = StudentCredit.objects.filter(
                student=result.student,
                academic_year=result.academic_year,
                semester=result.semester,
                is_latest=True
            ).first()

            new_version = 1
            if existing_credits:
                if existing_credits.result_id == result.id and existing_credits.result_version == result.version:
                    # Same result version: update in place
                    existing_credits.credits_attempted = total_attempted
                    existing_credits.credits_earned = total_earned
                    existing_credits.sgpa = sgpa
                    existing_credits.cgpa = cgpa
                    existing_credits.cumulative_credits_earned = cum_earned
                    existing_credits.backlogs_count = backlogs
                    existing_credits.calculated_by = user or existing_credits.calculated_by
                    existing_credits.save()
                    return existing_credits
                else:
                    # New result version (e.g. V2 superseding V1): mark existing as historical
                    new_version = existing_credits.version + 1
                    StudentCredit.objects.filter(id=existing_credits.id).update(is_latest=False)

            credit_record = StudentCredit.objects.create(
                student=result.student,
                academic_year=result.academic_year,
                semester=result.semester,
                result=result,
                result_version=result.version,
                credits_attempted=total_attempted,
                credits_earned=total_earned,
                sgpa=sgpa,
                cgpa=cgpa,
                cumulative_credits_earned=cum_earned,
                backlogs_count=backlogs,
                version=new_version,
                is_latest=True,
                calculated_by=user,
                calculated_at=timezone.now()
            )

        return credit_record

    @staticmethod
    def calculate_batch_credits(batch: ResultImportBatch, user=None) -> List[StudentCredit]:
        """Calculates credits for all published student results in an import batch."""
        published_results = StudentResult.objects.filter(
            import_batch=batch,
            status='PUBLISHED',
            is_latest=True
        )
        calculated = []
        for res in published_results:
            calc = CreditEligibilityService.calculate_credits_for_result(res, user=user)
            calculated.append(calc)
        return calculated

    @staticmethod
    def create_or_version_rule(
        name: str,
        code: str,
        min_credits: Decimal,
        min_attendance: Decimal,
        max_backlogs: int,
        detention_max_backlogs: int,
        detention_min_attendance: Decimal,
        program_id: Optional[str] = None,
        academic_year_id: Optional[str] = None,
        target_semester: Optional[int] = None,
        user=None
    ) -> EligibilityRule:
        """
        Creates or versions an institutional eligibility rule.
        If a rule with this code exists and has decisions, it creates a new version.
        """
        validate_eligibility_rule_invariants(
            min_credits,
            min_attendance,
            max_backlogs,
            detention_max_backlogs,
            detention_min_attendance
        )

        existing_rule = EligibilityRule.objects.filter(code=code, is_active=True).order_by('-version').first()

        with transaction.atomic():
            if existing_rule:
                has_decisions = EligibilityDecision.objects.filter(rule=existing_rule).exists()
                if has_decisions:
                    # Create new version preserving historical decisions on prior version
                    new_version = existing_rule.version + 1
                    existing_rule.is_active = False
                    existing_rule.save(update_fields=['is_active', 'updated_at'])

                    return EligibilityRule.objects.create(
                        name=name,
                        code=code,
                        academic_year_id=academic_year_id,
                        program_id=program_id,
                        target_semester=target_semester,
                        version=new_version,
                        min_credits_required=min_credits,
                        min_attendance_percentage=min_attendance,
                        max_backlogs_allowed=max_backlogs,
                        detention_max_backlogs=detention_max_backlogs,
                        detention_min_attendance=detention_min_attendance,
                        is_active=True,
                        created_by=user
                    )
                else:
                    # Update in place if no decisions link to this rule yet
                    existing_rule.name = name
                    existing_rule.academic_year_id = academic_year_id
                    existing_rule.program_id = program_id
                    existing_rule.target_semester = target_semester
                    existing_rule.min_credits_required = min_credits
                    existing_rule.min_attendance_percentage = min_attendance
                    existing_rule.max_backlogs_allowed = max_backlogs
                    existing_rule.detention_max_backlogs = detention_max_backlogs
                    existing_rule.detention_min_attendance = detention_min_attendance
                    existing_rule.save()
                    return existing_rule

            return EligibilityRule.objects.create(
                name=name,
                code=code,
                academic_year_id=academic_year_id,
                program_id=program_id,
                target_semester=target_semester,
                version=1,
                min_credits_required=min_credits,
                min_attendance_percentage=min_attendance,
                max_backlogs_allowed=max_backlogs,
                detention_max_backlogs=detention_max_backlogs,
                detention_min_attendance=detention_min_attendance,
                is_active=True,
                created_by=user
            )

    @staticmethod
    def get_applicable_rule(
        student: Student,
        academic_year: AcademicYear,
        semester: Semester
    ) -> EligibilityRule:
        """Finds the most specific active eligibility rule for a student."""
        # Check active enrollment to discover program
        enrollment = StudentEnrollment.objects.filter(
            student=student,
            academic_year=academic_year,
            semester=semester
        ).select_related('program').first()

        prog_id = enrollment.program_id if enrollment else None

        # 1. Program + Year + Semester specific
        rule = EligibilityRule.objects.filter(
            is_active=True,
            program_id=prog_id,
            academic_year=academic_year,
            target_semester=semester.number
        ).order_by('-version').first()

        # 2. Program + Year
        if not rule:
            rule = EligibilityRule.objects.filter(
                is_active=True,
                program_id=prog_id,
                academic_year=academic_year,
                target_semester__isnull=True
            ).order_by('-version').first()

        # 3. Program general
        if not rule and prog_id:
            rule = EligibilityRule.objects.filter(
                is_active=True,
                program_id=prog_id,
                academic_year__isnull=True
            ).order_by('-version').first()

        # 4. Global fallback
        if not rule:
            rule = EligibilityRule.objects.filter(
                is_active=True,
                program__isnull=True
            ).order_by('-version').first()

        if not rule:
            # Create a default institutional rule if none exists
            rule = EligibilityRule.objects.create(
                name="Default Institutional Rule",
                code="DEFAULT_RULE",
                version=1,
                min_credits_required=Decimal('18.0'),
                min_attendance_percentage=Decimal('75.00'),
                max_backlogs_allowed=2,
                detention_max_backlogs=4,
                detention_min_attendance=Decimal('50.00'),
                is_active=True
            )

        return rule

    @staticmethod
    def evaluate_student_eligibility(
        student: Student,
        academic_year: AcademicYear,
        semester: Semester,
        rule: Optional[EligibilityRule] = None,
        attendance_percentage: Decimal = Decimal('100.00'),
        user=None
    ) -> EligibilityDecision:
        """
        Evaluates student academic eligibility against configurable rule thresholds.
        Produces explicit decision states: ELIGIBLE, NOT_ELIGIBLE, DETAINED.
        Records exact rule and rule_version.
        """
        if rule is None:
            rule = CreditEligibilityService.get_applicable_rule(student, academic_year, semester)

        # Retrieve or calculate current credits
        credit = StudentCredit.objects.filter(
            student=student,
            academic_year=academic_year,
            semester=semester,
            is_latest=True
        ).first()

        if not credit:
            # Check for published result and calculate credits
            pub_res = StudentResult.objects.filter(
                student=student,
                academic_year=academic_year,
                semester=semester,
                status='PUBLISHED',
                is_latest=True
            ).first()

            if pub_res:
                credit = CreditEligibilityService.calculate_credits_for_result(pub_res, user=user)
            else:
                raise EligibilityValidationError(
                    f"Cannot evaluate eligibility: No published academic result or credit calculation "
                    f"found for student {student.enrollment_no} in Sem {semester.number} ({academic_year.label})."
                )

        # Evaluate Detention Rules first
        is_detained = False
        detention_reasons = []

        if credit.backlogs_count > rule.detention_max_backlogs:
            is_detained = True
            detention_reasons.append(
                f"Backlogs ({credit.backlogs_count}) exceeded detention threshold ({rule.detention_max_backlogs})"
            )

        if attendance_percentage < rule.detention_min_attendance:
            is_detained = True
            detention_reasons.append(
                f"Attendance ({attendance_percentage}%) below detention minimum ({rule.detention_min_attendance}%)"
            )

        if is_detained:
            final_decision = 'DETAINED'
            detention_text = "; ".join(detention_reasons)
            remarks_text = f"Detained under rule {rule.code} (v{rule.version}): {detention_text}"
        else:
            detention_text = ""
            # Evaluate General Eligibility Rules
            ineligibility_reasons = []

            if credit.credits_earned < rule.min_credits_required:
                ineligibility_reasons.append(
                    f"Earned credits ({credit.credits_earned}) below required minimum ({rule.min_credits_required})"
                )

            if credit.backlogs_count > rule.max_backlogs_allowed:
                ineligibility_reasons.append(
                    f"Backlogs ({credit.backlogs_count}) exceed allowed limit ({rule.max_backlogs_allowed})"
                )

            if attendance_percentage < rule.min_attendance_percentage:
                ineligibility_reasons.append(
                    f"Attendance ({attendance_percentage}%) below required minimum ({rule.min_attendance_percentage}%)"
                )

            if ineligibility_reasons:
                final_decision = 'NOT_ELIGIBLE'
                remarks_text = "; ".join(ineligibility_reasons)
            else:
                final_decision = 'ELIGIBLE'
                remarks_text = "Meets all credit, attendance, and backlog requirements."

        with transaction.atomic():
            # Check existing decision for this student and semester
            existing_decision = EligibilityDecision.objects.filter(
                student=student,
                academic_year=academic_year,
                semester=semester,
                is_latest=True
            ).first()

            decision_version = 1
            if existing_decision:
                decision_version = existing_decision.version + 1

            new_decision = EligibilityDecision.objects.create(
                student=student,
                academic_year=academic_year,
                semester=semester,
                rule=rule,
                rule_version=rule.version,
                credits_earned=credit.credits_earned,
                credits_attempted=credit.credits_attempted,
                backlogs_count=credit.backlogs_count,
                attendance_percentage=attendance_percentage,
                decision=final_decision,
                detention_reason=detention_text,
                remarks=remarks_text,
                version=decision_version,
                is_latest=True,
                decided_by=user,
                decided_at=timezone.now()
            )

            if existing_decision:
                # Retain historical decision record
                EligibilityDecision.objects.filter(id=existing_decision.id).update(
                    is_latest=False,
                    superseded_by=new_decision
                )

        return new_decision

    @staticmethod
    def evaluate_cohort_eligibility(
        academic_year: AcademicYear,
        semester: Semester,
        program: Optional[Program] = None,
        rule: Optional[EligibilityRule] = None,
        user=None
    ) -> List[EligibilityDecision]:
        """
        Evaluates eligibility for all students enrolled in a cohort.
        References StudentEnrollment from Student Management.
        """
        enrollment_qs = StudentEnrollment.objects.filter(
            academic_year=academic_year,
            semester=semester,
            status='ACTIVE'
        ).select_related('student', 'program')

        if program:
            enrollment_qs = enrollment_qs.filter(program=program)

        decisions = []
        for enrollment in enrollment_qs:
            try:
                dec = CreditEligibilityService.evaluate_student_eligibility(
                    student=enrollment.student,
                    academic_year=academic_year,
                    semester=semester,
                    rule=rule,
                    user=user
                )
                decisions.append(dec)
            except Exception:
                # If a student has no published results yet, continue with the rest of the cohort
                continue

        return decisions

    @staticmethod
    def generate_next_year_eligibility_list(
        academic_year: AcademicYear,
        semester: Semester,
        program: Program,
        target_academic_year: Optional[AcademicYear] = None,
        target_semester_number: Optional[int] = None,
        user=None
    ) -> NextYearEligibilityList:
        """
        Generates the official Next-Year Promotion Register snapshot.
        Consumes authoritative StudentEnrollment records and latest EligibilityDecisions.
        """
        if target_semester_number is None:
            target_semester_number = semester.number + 1

        enrollments = StudentEnrollment.objects.filter(
            academic_year=academic_year,
            semester=semester,
            program=program,
            status='ACTIVE'
        ).select_related('student')

        items = []
        eligible_count = 0
        not_eligible_count = 0
        detained_count = 0

        for enr in enrollments:
            std = enr.student
            decision = EligibilityDecision.objects.filter(
                student=std,
                academic_year=academic_year,
                semester=semester,
                is_latest=True
            ).first()

            if not decision:
                try:
                    decision = CreditEligibilityService.evaluate_student_eligibility(
                        student=std,
                        academic_year=academic_year,
                        semester=semester,
                        user=user
                    )
                except Exception:
                    decision = None

            if decision:
                dec_status = decision.decision
                if dec_status == 'ELIGIBLE':
                    eligible_count += 1
                elif dec_status == 'DETAINED':
                    detained_count += 1
                else:
                    not_eligible_count += 1

                items.append({
                    'student_id': str(std.id),
                    'enrollment_no': std.enrollment_no,
                    'candidate_name': std.candidate_name,
                    'current_semester': semester.number,
                    'target_semester': target_semester_number,
                    'decision': dec_status,
                    'credits_earned': str(decision.credits_earned),
                    'backlogs_count': decision.backlogs_count,
                    'attendance_percentage': str(decision.attendance_percentage),
                    'detention_reason': decision.detention_reason,
                    'rule_version': decision.rule_version,
                    'remarks': decision.remarks,
                })
            else:
                not_eligible_count += 1
                items.append({
                    'student_id': str(std.id),
                    'enrollment_no': std.enrollment_no,
                    'candidate_name': std.candidate_name,
                    'current_semester': semester.number,
                    'target_semester': target_semester_number,
                    'decision': 'NOT_ELIGIBLE',
                    'credits_earned': '0.0',
                    'backlogs_count': 0,
                    'attendance_percentage': '0.00',
                    'detention_reason': 'No published results available for evaluation',
                    'rule_version': None,
                    'remarks': 'Pending result publication',
                })

        promotion_list = NextYearEligibilityList.objects.create(
            academic_year=academic_year,
            semester=semester,
            target_academic_year=target_academic_year,
            target_semester_number=target_semester_number,
            program=program,
            total_students=len(items),
            eligible_count=eligible_count,
            not_eligible_count=not_eligible_count,
            detained_count=detained_count,
            items=items,
            generated_by=user,
            generated_at=timezone.now()
        )

        return promotion_list
