# Feature: Verification

## 1. Problem

The system needs a controlled workflow for determining whether submitted or corrected information is approved for official use.

Verification must remain separate from Student Management: **Verification owns the decision and workflow, while Student Management owns the actual student information.** Verification must therefore not become a second student database.

The system must also preserve previous verification decisions and correction history rather than silently rewriting historical decisions.

---

## 2. Goal

Build the **Verification** bounded context to provide:

- Verification record and workflow state
- Submission and pending state
- Administrative review
- Approval
- Rejection
- Needs-correction workflow
- Correction/re-submission flow
- Verification decision history
- Accountable-actor auditability
- Controlled transition of accepted information to official use

The exact field-by-field verification policy remains an institutional decision and must not be invented by implementation.

---

## 3. User Stories

- As an authorized reviewer, I want to review submitted information so that I can make a verification decision.
- As an authorized reviewer, I want to approve valid submissions so that they can become accepted for official use where applicable.
- As an authorized reviewer, I want to reject submissions that should not be accepted.
- As an authorized reviewer, I want to request correction when submitted information needs to be corrected.
- As a student/authorized user, I want to correct information that has been returned for correction and re-submit it.
- As an authorized reviewer, I want previous verification decisions to remain visible as history.
- As the system, I want every important verification action to identify the responsible actor.
- As Student Management, I want Verification to communicate approval decisions without duplicating ownership of student information.
- As Documents, I want submitted documents to participate in verification where institutional policy requires it.

---

## 4. Scope — Files/Modules Touched

### Verification Module

The task graph defines these vertical slices:

### 4.1 Verification Workflow

- **Verification record and state-machine foundation**
  - Depends on Student Management; Identity authorization.
- **Verification submission and pending-state vertical slice**
  - Depends on Verification record and state-machine foundation; Student Documents.
- **Verification review and approval vertical slice**
  - Depends on Verification submission and pending-state.
- **Verification rejection and needs-correction vertical slice**
  - Depends on Verification review and approval.

### 4.2 Official-Record Corrections

- **Student correction → verification → approved student-record update vertical slice**
  - Depends on Student controlled-correction request; Verification review and approval; Government-source preservation and additive correction history.
- **Verification decision history and accountable-actor audit vertical slice**
  - Depends on Verification rejection and needs-correction; Student correction → verification → approved student-record update.

All listed Verification tasks are marked **HUMAN REVIEW REQUIRED**.

---

## 5. Requirements

### 5.1 Ownership Boundary

1. Verification owns:
   - Verification workflow
   - Verification decisions
   - Correction requests
   - Verification history.
2. Student Management owns actual student information.
3. Verification must not create a second copy of canonical student data.
4. Other modules must interact through approved application/domain/query contracts rather than direct persistence access.

### 5.2 Verification State Machine

5. Verification must use explicit workflow states.
6. The defined states are:

```text
PENDING
   ↓
APPROVED
   ↓
REJECTED / NEEDS_CORRECTION
```

More precisely, the architecture defines the possible outcomes as:

- `APPROVED`
- `REJECTED`
- `NEEDS_CORRECTION`

7. State transitions must be guarded by the application/domain layers.
8. Verification status must not be implemented as an uncontrolled collection of boolean flags.

### 5.3 Submission

9. Information requiring administrative confirmation enters the Verification workflow.
10. A submission must remain distinguishable from an approved/official value.
11. A submitted item may remain `SUBMITTED` while approval determines whether it becomes accepted for official use.
12. Verification submission must support a pending state.

### 5.4 Review and Approval

13. Authorized reviewers must be able to review pending verification items.
14. Approval must be an explicit state transition.
15. An approved submission may become accepted for official use where the applicable business policy requires this.
16. Verification approval must identify the accountable actor.

### 5.5 Rejection

17. Authorized reviewers must be able to reject a submission.
18. Rejection must be an explicit state transition.
19. The previous decision must remain historically preserved.
20. A new submission/review must create new history rather than silently rewriting the previous decision.

### 5.6 Needs Correction

21. Authorized reviewers must be able to place a submission into `NEEDS_CORRECTION`.
22. A correction request must allow the submission to be corrected and re-submitted.
23. Re-submission must enter the Verification workflow again.
24. Previous verification decisions remain historical records.

The defined flow is:

```text
Submitted Information
        ↓
Verification
        ↓
REJECTED / NEEDS_CORRECTION
        ↓
Correction Request
        ↓
Student / Authorized User
        ↓
Corrected Information
        ↓
Re-Submission
        ↓
Verification
        ↓
APPROVED / REJECTED / NEEDS_CORRECTION
        ↓
Student Management / Official Use
```

### 5.7 Student Record Boundary

25. Verification must not directly become the source of truth for student data.
26. Where an approved correction affects official student information, the approved result must flow back through the Student Management ownership boundary.
27. Student Management remains responsible for the actual student record.
28. Verification records the decision that the submitted/corrected information is approved for official use.

### 5.8 Document Boundary

29. Documents remain owned by the Documents module.
30. Verification may receive documents for review where the institutional policy requires verification.
31. Verification must not take ownership of document metadata, storage, or document lifecycle.
32. The exact document-by-document verification requirement remains open.

The defined document flow is:

```text
Student
   ↓
Document Upload
   ↓
Documents
   ↓
Document Metadata + Storage Reference
   ↓
Verification
   ↓
APPROVED / REJECTED / NEEDS_CORRECTION
   ↓
Student Management
   ↓
Accepted / Official Current Value
   ↓
Audit
```

### 5.9 Accountable Actor

33. Verification actions must identify the responsible actor.
34. Important verification actions include:

- Approve
- Reject
- Request correction

35. The minimum conceptual accountability information is:

- Actor
- Action
- Target
- Timestamp
- Reason where applicable.

### 5.10 Historical Decisions

36. Previous verification decisions must not be silently rewritten.
37. New decisions or correction actions must create new history.
38. Verification history must remain explainable and auditable.

---

## 6. Data Changes

The Verification context requires data representing:

- Verification records
- Verification state
- Submitted information/reference
- Verification decision
- Correction request information
- Verification history
- Accountable actor information
- Relevant timestamps/reasons
- References to the affected student/document/owned resource

Verification must **not duplicate the canonical student record**.

The exact physical schema, table names, field names, and relationships are not finalized in the supplied architecture and must not be invented in this PRD.

---

## 7. API Changes

The Verification module must provide capabilities for:

- Creating/submitting verification records
- Viewing pending verification work
- Reviewing submissions
- Approving submissions
- Rejecting submissions
- Requesting corrections
- Receiving corrected submissions
- Re-submitting corrected information
- Viewing verification history
- Recording accountable actors
- Communicating approved decisions to the owning module

API behavior must enforce:

- Authentication
- Backend authorization
- Input validation
- State-transition validation
- Safe errors
- Bounded responses
- Ownership boundaries

Exact routes, payloads, response schemas, permission names, and status-code contracts are not defined by the source material and remain open.

---

## 8. Security Notes

- Verification actions require authenticated users.
- Authorization must be enforced server-side.
- Reviewer permissions must not be implemented solely in React.
- State transitions must be guarded.
- Sensitive information must follow the system-wide masked-by-default/restricted-access model.
- Verification actions must be auditable.
- Audit records should not unnecessarily contain raw sensitive values.
- The system provides accountability, auditability, and reversibility; it cannot guarantee that every human decision is truthful.
- Verification must not expose or duplicate information beyond the authorization boundary of the underlying resource.

---

## 9. Definition of Done

-  Verification record and state-machine foundation is implemented.
-  Verification submission and pending state are implemented.
-  Verification review is implemented.
-  Approval is implemented as an explicit state transition.
-  Rejection is implemented as an explicit state transition.
-  Needs-correction is implemented as an explicit state transition.
-  Correction and re-submission flow works correctly.
-  Previous verification decisions remain preserved.
-  Verification history is maintained.
-  Accountable actor information is recorded.
-  Approved corrections respect Student Management ownership.
-  Verification does not become a second student database.
-  Documents remain owned by Documents.
-  Authentication and authorization are enforced server-side.
-  Invalid state transitions are rejected.
-  Verification failure paths are handled safely.
-  Historical verification behavior is tested.
-  Approval/rejection/correction authorization is tested.
-  Correction/re-submission behavior is tested.
-  Accountable-actor audit behavior is tested.
-  Cross-module ownership boundaries are tested.
-  Queries remain bounded and avoid N+1/unbounded access.
-  Required human review is completed.

---

## 10. Out of Scope

- Owning or duplicating student information.
- Student identity/admission/enrollment implementation.
- Document storage or document lifecycle.
- Defining academic master data.
- Defining financial records.
- Defining result records.
- Generic cross-domain `CorrectionService`.
- Authentication implementation.
- Defining institutional field-by-field verification policy.
- Defining which documents require verification.
- Defining sensitive-data retention periods.
- Automatic rewriting of previous verification decisions.

The architecture explicitly rejects inventing field-level approval behavior while the Verification Policy Matrix remains open.

---

## 11. Open Questions

1. Which individual student fields require verification before becoming official?
2. Which student fields are immediately usable after submission?
3. Which documents require verification?
4. Which documents can be accepted without verification?
5. What roles/permissions can review, approve, reject, or request correction?
6. What information/reason is mandatory when rejecting or requesting correction?
7. What exact verification states/transitions are required beyond the architecture-defined states?
8. What exact API routes and request/response contracts are required?
9. What exact physical schema should represent verification history?
10. What institutional retention rules apply to verification history and related sensitive data?

**Important:** Questions 1–4 are explicitly institutionally open and must be resolved before field/document-specific behavior is implemented.

---

## 12. Dependencies

### Direct task dependencies

**Student Management + Identity authorization**
→ Verification record and state-machine foundation

**Verification foundation + Student Documents**
→ Verification submission and pending state

**Verification submission**
→ Verification review and approval

**Verification review and approval**
→ Verification rejection and needs-correction

**Student controlled correction + Verification approval + Government-source preservation/additive correction history**
→ Student correction → verification → approved student-record update

**Rejection/needs-correction + approved student-record update**
→ Verification decision history and accountable-actor audit

### Cross-module boundary

**Student Management owns data → Verification owns decision → Audit records accountable action**

This preserves the architectural rule that submission, acceptance, and official-record status are distinct concepts.

**Status:** PRD #6 — `PRD-verification.md`