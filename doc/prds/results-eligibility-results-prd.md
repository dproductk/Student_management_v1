# PRD: Results & Eligibility — Results

## 1. Problem

The system must support importing academic results from Excel, validating and associating result rows with the correct students, moving results through an explicit lifecycle, approving and publishing official results, and preserving published results as immutable historical evidence.

The Results & Eligibility bounded context owns results and result publication. The result workflow is explicitly defined as:

**Result Excel → Import Batch → Rows → Validation → Result Records → Credit/Eligibility Calculation → Approval → Publication.**

Published results must never be silently overwritten. Corrections must create a new result version that supersedes the previous published version while preserving the original.

---

## 2. Goal

Provide a production-grade Results module that:

- Imports result Excel files through a controlled pipeline.
- Preserves imported rows and validation outcomes.
- Associates result rows with the correct students.
- Represents result processing through an explicit state machine.
- Supports result approval and publication.
- Makes published results available for student viewing and reporting.
- Enforces immutability of published results.
- Supports controlled correction of published results through versioned supersession.
- Preserves complete historical result evidence.
- Attributes important result actions to accountable actors.

The Results & Eligibility module owns assessments, marks, results, credits, eligibility, and result publication.

---

## 3. User Stories

### Result Import

- As an authorized result-processing user, I want to upload a result Excel file so that result data can enter the controlled import pipeline.
- As a result-processing user, I want uploaded rows to be preserved so that individual validation and processing outcomes can be reviewed.
- As a result-processing user, I want invalid result rows identified rather than silently imported.
- As a result-processing user, I want valid result rows associated with the correct student records.

### Result Lifecycle

- As an authorized result-processing user, I want results to move through explicit states so that their processing status is unambiguous.
- As an authorized approver, I want to approve validated results before publication.
- As a student, I want to view my result after it has been published.
- As an authorized user, I want published results protected from direct modification.

### Result Correction

- As an authorized user, I want to request correction of a published result through a controlled workflow.
- As an authorized reviewer, I want to review and approve a result correction.
- As an authorized result user, I want the corrected result represented as a new version rather than modifying the historical result.
- As an auditor, I want the original result and its superseding version to remain traceable.

---

# 4. Scope — Files/Modules Touched

### Primary bounded context

**Results & Eligibility**

Owns:

- Result import batches.
- Result import rows.
- Result records.
- Result lifecycle.
- Result approval.
- Result publication.
- Published-result correction and versioning.

The architecture explicitly assigns **Result → Results & Eligibility** as the authoritative ownership boundary.

### Dependencies

The Results module depends on:

- **Identity** — authentication and authorization.
- **Academic Foundation** — established academic entities.
- **Student Management** — authoritative student academic enrollment.
- **Faculty** — faculty assignment.
- **Onboarding** — deterministic student matching capability for association during result import.
- **Audit** — accountable-actor audit.
- **Reporting** — consumes Results-owned query interfaces.
- **Credits & Eligibility** — downstream result-derived calculations.

Results must reference established academic entities rather than recreate academic master data.

### Explicit task scope

The PRD covers these Results tasks:

1. Result import batch and result-import-row database foundation.
2. Result Excel upload and import-batch creation.
3. Result extraction and validation.
4. Result-row-to-student association.
5. Result draft/processing/validated state machine.
6. Result approval.
7. Result publication and student view.
8. Published-result immutability enforcement.
9. Published-result correction request and review.
10. Result V2 supersession and historical-result preservation.
11. Result correction accountable-actor audit.

All are marked **HUMAN REVIEW REQUIRED** in the task graph.

---

# 5. Requirements

## 5.1 Result Import

### R-001 — Import Batch

The system shall create a result import batch for each result Excel import operation.

The import batch shall provide the boundary for the associated imported result rows and their processing state.

### R-002 — Import Rows

The system shall preserve individual result-import rows associated with the import batch.

The staging/import process must preserve source information sufficiently to identify the original imported row and its processing outcome. The architecture requires controlled ingestion through import batches, rows, validation, and structured records.

### R-003 — Excel Upload

The system shall accept result Excel files through the Results import workflow rather than directly modifying production result records.

### R-004 — Extraction

The system shall extract result rows from the uploaded Excel file into the result-import-row representation.

### R-005 — Validation

The system shall validate extracted result rows before creating authoritative structured result records.

Invalid rows shall be identifiable as invalid rather than silently becoming official result records.

### R-006 — Result Association

The system shall associate valid result rows with the appropriate student using the established student identity/matching capability.

The Results module shall not create a second student identity source.

The task graph explicitly makes deterministic student matching a dependency for result-row-to-student association.

### R-007 — Academic Association

Result records shall reference established academic entities and student academic enrollment rather than duplicating academic master-data definitions.

Student academic enrollment is the authoritative enrollment relationship.

---

## 5.2 Result Lifecycle

### R-008 — Explicit State Machine

Result processing shall use the defined lifecycle:

**DRAFT → PROCESSING → VALIDATED → APPROVED → PUBLISHED**

The architecture also identifies **REJECTED** as a possible result state.

The implementation shall not replace this lifecycle with an unstructured collection of boolean flags.

### R-009 — State Transitions

Result state transitions shall be controlled by the Results application/domain layer.

The frontend shall not be authoritative for result state transitions.

### R-010 — Approval

A result must pass through the approval stage before publication.

Approval shall be an authorized operation and shall identify the accountable actor.

### R-011 — Publication

Only an approved result may enter the published state.

Publication shall be an explicit operation rather than an implicit consequence of upload or validation.

### R-012 — Student Result View

Published results shall become available for student viewing after publication.

The result flow explicitly ends in **Student Result Available → Reports / Reporting**.

The exact student-facing API/UI contract is not defined by the architecture and must not be invented here.

---

## 5.3 Published Result Immutability

### R-013 — Published Results Are Immutable

Once a result is published, the published result shall be treated as immutable historical evidence.

The system shall prevent ordinary update or delete operations from modifying the published result in place.

### R-014 — Historical Preservation

The original published result must remain accessible as historical evidence even after a correction.

### R-015 — No Silent Overwrite

The system shall never silently replace a published result with corrected values.

This is an explicit architectural rule.

---

## 5.4 Published Result Correction

### R-016 — Correction Request

A correction to a published result shall begin with a correction request.

### R-017 — Correction Review

A published-result correction shall pass through a correction review and authorized approval before the corrected result becomes authoritative.

The defined flow is:

**Published Result V1 → Correction Request → Correction Review → Authorized Approval → Result V2 → V2 Supersedes V1.**

### R-018 — Result Version 2

An approved correction shall create a new result version rather than modify the existing published version.

### R-019 — Supersession

The new result version shall explicitly supersede the previous published result.

### R-020 — Historical V1

The previous result version shall remain preserved and accessible as historical evidence.

### R-021 — Correction Accountability

Result correction shall record the accountable actor, action, target, timestamp, reason where applicable, and audit information.

The architecture explicitly identifies Results actions such as **approve / publish / correct** as accountable actions.

---

## 5.5 Auditability

### R-022 — Accountable Result Actions

Important result actions shall be attributable to an authenticated and authorized actor.

At minimum, the architecture's accountable-actor pattern requires:

**Actor + Action + Target + Timestamp + Reason where applicable.**

### R-023 — Audit History

Approval, publication, correction, and supersession actions shall produce appropriate audit records.

### R-024 — Historical Traceability

The system shall preserve enough history to establish the relationship between an original published result and any later corrected/superseding version.

---

## 5.6 Reporting Boundary

### R-025 — Results Query Interface

Reporting shall consume Results data through a module-owned query interface.

Reporting shall not directly access Results internal tables as its normal architectural interface.

---

# 6. Data Changes

The Results bounded context requires data structures representing:

- Result import batch.
- Result import rows.
- Structured result records.
- Result lifecycle state.
- Result versions/supersession relationships.
- Approval/publication information.
- Correction requests/review information.
- Accountable actor and audit information where owned by Results.

The task graph explicitly requires the **result-import batch and result-import-row database foundation** as the first Results task.

### Ownership

**Results & Eligibility owns:**

- Result records.
- Result import state.
- Result lifecycle.
- Result approval.
- Result publication.
- Result correction/versioning.

**Student Management owns:**

- Student identity.
- Student academic enrollment.

**Academic Foundation owns:**

- Department.
- Program.
- Academic Year.
- Semester.
- Batch.
- Scheme.
- Subject.
- Scheme Subject.

**Faculty owns:**

- Faculty records and assignments.

These ownership boundaries must not be duplicated inside Results.

### Historical data

Published result history must be preserved. Corrections create a new version, with the new version superseding the previous version.

### Schema details intentionally not specified

The source architecture does **not** finalize:

- Exact result table names.
- Exact result-column definitions.
- Exact import-row schema.
- Exact version-key structure.
- Exact correction-request schema.
- Exact database constraints.
- Exact indexing strategy.

These must be finalized during the database/design work rather than invented in this PRD.

---

# 7. API Changes

The Results module will require API operations corresponding to the defined workflows, including:

- Result Excel upload.
- Result import-batch creation/status.
- Result import-row validation/error reporting.
- Result association.
- Result lifecycle/state operations.
- Result approval.
- Result publication.
- Published-result viewing.
- Published-result correction request.
- Correction review/approval.
- Result-version/history access.

The API layer shall handle:

- Authentication extraction.
- Input validation at the API boundary.
- Authorization enforcement/coordination.
- Serialization.
- Appropriate HTTP status codes.
- Pagination and bounded responses where applicable.
- Safe, consistent error responses.

Business rules and lifecycle transitions shall remain outside the API layer.

### API details intentionally open

The source documents do not define exact:

- URLs/routes.
- HTTP methods.
- Request/response schemas.
- Pagination parameters.
- Error codes.
- Permission names.
- Approval-role matrix.

These must be finalized without introducing rules unsupported by the architecture.

---

# 8. Security Notes

### Authentication & Authorization

All protected Results operations shall require backend authentication and authorization.

Authorization must be enforced server-side; frontend visibility is not an authorization boundary.

### Scoped access

Result upload, approval, publication, correction, and historical-result access shall respect the application's established authorization model.

The exact role-to-permission matrix is not defined in the supplied architecture and must not be guessed.

### Published-result protection

The backend must prevent unauthorized modification of published results.

### Auditability

Approval, publication, correction, and supersession actions must be attributable to accountable actors.

### Sensitive information

Results APIs must not expose unrelated sensitive student information merely because a result is being viewed.

### Logging

Logs must not contain sensitive student information or unnecessary result data. Structured operational logging should identify the request/job, actor, operation, and outcome without exposing protected values.

---

# 9. Definition of Done

-  Result import batch and result-import-row database foundation implemented.
-  Result Excel upload and import-batch creation implemented.
-  Result extraction and validation implemented.
-  Result-row-to-student association implemented.
-  Result lifecycle state machine implemented.
-  Result approval implemented.
-  Result publication implemented.
-  Student result view implemented.
-  Published-result immutability enforced at the application and persistence boundaries.
-  Published-result correction workflow implemented.
-  Result V2 supersession implemented.
-  Historical result V1 preserved.
-  Accountable-actor audit implemented for relevant result actions.
-  Authentication and authorization enforced server-side.
-  Business rules and state transitions covered by automated tests.
-  Import failure and invalid-row behavior tested.
-  Duplicate/concurrency risks for result processing and publication addressed.
-  Database migrations are safe and reviewed.
-  Queries are bounded and avoid N+1 behavior.
-  Reporting uses the Results-owned query interface.
-  End-to-end result import → validation → approval → publication flow tested.
-  Published-result correction → V2 supersession → historical V1 preservation tested.
-  **Human review completed for every Results task.**

Every task in this Results section is explicitly marked **HUMAN REVIEW REQUIRED** in the implementation task graph.

---

# 10. Out of Scope

The following are not part of this PRD:

- Full university examination management system.
- Paper/question-paper setting and checking system.
- Complex examination timetable/seating engine.
- University payment/reconciliation system.
- Unspecified examination-board integrations.
- New bounded contexts.
- A generic cross-domain Correction module.
- Direct access to another module's internal database tables.
- Changing the established ownership of Student Management, Academic Foundation, Faculty, Verification, Finance, or Reporting.
- Inventing institutional result-calculation rules not defined in the architecture.
- Inventing institutional approval-role rules not defined in the architecture.

The project context explicitly excludes a full university exam system and complex examination functionality.

---

# 11. Open Questions

These are intentionally left open because the supplied architecture does not define them:

1. **Result Excel format**
   - Exact columns and supported workbook/sheet structure are not finalized.
2. **Result validation rules**
   - Exact mark ranges, grading rules, missing-value rules, duplicate-row rules, and subject-specific validation requirements are not specified.
3. **Result calculation rules**
   - Exact institutional calculation rules for marks/grades are not finalized in the supplied sources.
4. **Approval authority**
   - Exact roles permitted to approve results are not defined.
5. **Publication authority**
   - Exact roles permitted to publish results are not defined.
6. **Correction authority**
   - Exact roles permitted to request, review, and approve published-result corrections are not defined.
7. **Correction reason policy**
   - The architecture requires accountable correction information and a reason where applicable, but the exact mandatory reason policy is not defined.
8. **Result version numbering**
   - The architecture defines V1/V2 supersession but does not prescribe the physical versioning implementation.
9. **Student result visibility policy**
   - The architecture establishes availability after publication, but does not define additional student-view restrictions.
10. **Exact result data model**
    - Final physical fields and constraints require database-design decisions.

No unresolved institutional policy should be invented during implementation; architectural ambiguity must be resolved before an irreversible design decision is introduced.

---

# 12. Dependencies

### Upstream

1. **Identity & Access**
   - Authentication.
   - Authorization.
2. **Academic Foundation**
   - Academic year.
   - Semester.
   - Program.
   - Department.
   - Batch.
   - Scheme.
   - Subject/Scheme Subject.
3. **Student Management**
   - Student identity.
   - Student academic enrollment.
4. **Faculty**
   - Faculty assignment.
5. **Onboarding**
   - Deterministic student matching capability.
6. **Audit**
   - Accountable-actor audit capability.

### Downstream

1. **Credits & Eligibility**
   - Result publication is a dependency for result-to-credit calculation.
2. **Reporting**
   - Consumes Results through the module-owned query interface.

### Dependency order

The Results implementation order is:

**Result Import Foundation → Excel Upload → Extraction/Validation → Student Association → Result Lifecycle → Approval → Publication/Student View → Published Immutability → Correction Review → V2 Supersession → Audit.**

The task graph explicitly establishes these dependencies.
