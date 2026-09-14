# Feature: Student Onboarding & Import

## 1. Problem

Government Excel data is the starting point for student onboarding, but it must **never be imported directly into production student tables**.

The system requires a controlled ingestion pipeline that preserves the original source data, validates and normalizes rows, detects duplicates, deterministically matches students, handles conflicts explicitly, and safely creates or associates production student records.

The import process must also be idempotent so that re-uploading the same source does not create duplicate students.

---

## 2. Goal

Build the **Onboarding & Import** bounded context as a controlled government-data ingestion pipeline:

**Government Excel → Upload → Import Batch → Staging Rows → Validation → Normalization → Deduplication → Deterministic Identity Matching → Controlled Production Import**

The module must preserve source history, expose row-level validation/error information, handle conflicting matches through manual resolution, support explicit import states and failure recovery, and integrate imported students with account provisioning.

---

## 3. User Stories

- As an authorized operator, I want to upload a Government Excel file so that it can enter the controlled onboarding pipeline.
- As an authorized operator, I want an import batch and staging rows created so that the source can be validated before production changes.
- As an authorized operator, I want validation errors reported at row level so that invalid source data can be identified.
- As an authorized operator, I want normalized values presented so that cleaned data can be reviewed before import.
- As the system, I want deterministic student matching so that existing students are identified consistently.
- As an authorized operator, I want conflicting matches identified for manual resolution rather than automatically merged.
- As the system, I want production imports to be idempotent so that repeated source data does not create duplicate students.
- As an authorized operator, I want import state and failure information available so that failed or partially completed imports can be safely investigated and recovered.
- As the system, I want successfully imported students to integrate with the Identity account-provisioning flow.
- As an authorized operator, I want the original source information preserved so that import history remains auditable.

---

## 4. Scope — Files/Modules Touched

### Onboarding Module

The task graph defines the following vertical slices:

### 4.1 Import Infrastructure

- **Import batch and staging-row database foundation**
  - Depends on Student identity and core student record; Academic Foundation.
- **Government Excel upload and import-batch creation**
  - Depends on Import batch and staging-row database foundation.
- **Excel extraction and staging-row preservation**
  - Depends on Government Excel upload and import-batch creation.

### 4.2 Validation and Normalization

- **Import validation and row-error reporting**
  - Depends on Excel extraction and staging-row preservation.
- **Import normalization and cleaned-value presentation**
  - Depends on Import validation and row-error reporting.

### 4.3 Matching and Production Import

- **Deterministic student matching**
  - Depends on Import normalization and cleaned-value presentation; Student search and detail.
- **Import conflict detection and manual-resolution**
  - Depends on Deterministic student matching.
- **Idempotent production student-import**
  - Depends on Deterministic student matching; Import conflict detection and manual-resolution; Government-source preservation and additive correction history.
- **Import state-machine and failure/recovery**
  - Depends on Idempotent production student-import.

### 4.4 Account Provisioning Integration

- **Imported-student account provisioning**
  - Depends on Idempotent production student-import; Initial student account provisioning policy.
- **End-to-end government import → student → enrollment → account provisioning flow**
  - Depends on Imported-student account provisioning; Student academic enrollment.

All listed tasks are marked **HUMAN REVIEW REQUIRED** in the task graph.

---

## 5. Requirements

### 5.1 Import Batch and Staging

1. Government Excel data MUST enter an import batch before any production student records are created.
2. Government Excel MUST NOT be imported directly into production student tables.
3. The staging layer must preserve:
   - Original row
   - Source file
   - Row number
   - Raw values
   - Normalized values where appropriate
   - Validation errors
   - Processing status
   - Resulting student ID where applicable.
4. Original source rows must remain available even when processing fails.
5. Failed rows must not silently corrupt production data.

### 5.2 Validation and Normalization

6. Imported rows must pass through validation before production import.
7. Validation failures must be associated with the relevant staging row.
8. Normalization must occur after validation according to the defined import pipeline.
9. Cleaned/normalized values must be available for the matching/import workflow.
10. Validation and normalization failures must not silently become production records.

### 5.3 Deduplication and Identity Matching

11. Student matching must be deterministic.
12. The accepted matching precedence is:

**Application ID → Enrollment Number → Board / University Enrollment Number**

13. Where there is **no match**, the import flow may create a new student through Student Management.
14. Where there is a **single valid match**, the import row must be associated with the existing student.
15. Conflicting identifiers/matches MUST NOT be automatically merged.
16. Conflicting matches must enter manual review and require explicit resolution.

### 5.4 Production Import

17. Production import must occur only after the controlled staging, validation, normalization, deduplication, and matching workflow.
18. Student Management remains the owner of the actual student record.
19. Onboarding owns the import lifecycle and execution, not the canonical student data.
20. Cross-module interaction must respect bounded-context ownership rather than creating a second student database.

### 5.5 Idempotency

21. The import process must be idempotent.
22. Re-uploading the same source data must not create duplicate students.
23. Existing identity checks and deterministic matching must be used to prevent duplicate student creation.

### 5.6 Import State Machine

The import lifecycle must support:

```text
UPLOADED
    ↓
VALIDATING
    ↓
VALIDATED
    ↓
IMPORTING
    ↓
COMPLETED
```

Failure paths may produce:

```text
FAILED
PARTIALLY_COMPLETED
CANCELLED
```

The system must not infer completion merely from the existence of some student records.

### 5.7 Failure and Recovery

24. Failed imports must retain sufficient staging information to determine what happened.
25. Failed rows must expose their failure classification.
26. Import failures may include:

- Validation failure
- Normalization failure
- Matching conflict
- Database/integrity failure
- Processing failure
- External/storage failure.

27. A `PARTIALLY_COMPLETED` import must treat successfully processed rows as already processed and must not blindly rerun the entire source.
28. A `FAILED` import must not be assumed to have created zero production records.
29. Retry must occur only after investigating the existing database/staging state and confirming idempotency protections.
30. Reprocessing must use the approved import workflow.

### 5.8 Account Provisioning Integration

31. Successfully imported students must integrate with the existing Identity account-provisioning policy.
32. This integration must use the existing Identity-owned provisioning policy rather than redefining account creation inside Onboarding.
33. The complete government-import → student → enrollment → account-provisioning flow must be covered by the defined end-to-end task.

---

## 6. Data Changes

The Onboarding context requires data representing:

- Import batches
- Import/staging rows
- Source-file metadata
- Original source rows/raw values
- Normalized values where appropriate
- Validation errors
- Row processing status
- Resulting student ID where applicable
- Import batch lifecycle state
- Import/matching outcomes
- Conflict/manual-resolution information where required by the workflow

The staging layer may use flexible raw-data representation where appropriate; the architecture explicitly allows JSONB for import raw data, while structured relational information should remain relational.

The exact physical schema, field names, constraints, and indexes are **not defined by this PRD** and must not be invented here.

Student identity remains owned by Student Management. Onboarding must not create a competing canonical student-data store.

---

## 7. API Changes

The Onboarding module must expose capabilities for:

- Import batch creation
- Government Excel upload
- Import/source metadata inspection
- Staging-row inspection
- Validation results and row-level errors
- Normalized-value presentation
- Matching results
- Conflict/manual-resolution workflow
- Controlled production import
- Import state/status
- Failure/recovery information
- Import outcome reporting
- Account-provisioning integration

API boundaries must enforce authentication, authorization, input validation, bounded responses, safe errors, and appropriate pagination where collections are exposed.

**Exact API routes, request/response schemas, pagination parameters, status codes, and permission mappings are not specified by the architecture and remain to be finalized.**

---

## 8. Security Notes

- Backend authentication and authorization are mandatory; frontend controls are not sufficient.
- Only authorized actors may perform import operations.
- Import files and rows must be treated as untrusted input.
- Original source data must not be silently altered to hide processing failures.
- Sensitive student information contained in imported data must follow the platform's masking, authorization, and audit requirements.
- Important import actions must identify the accountable actor and relevant operation.
- Production writes must occur only through the controlled application workflow.
- Conflicting student records must never be automatically merged.
- Import operations must be auditable.
- Source data/history must not be destructively overwritten.

The runbook specifically requires preserving original failed rows, affected row numbers, conflict-resolution records, and accountable actors.

---

## 9. Definition of Done

-  All defined Onboarding & Import vertical slices are implemented.
-  Import batch and staging-row ownership is clear.
-  Government Excel cannot bypass staging and enter production directly.
-  Original source rows and required staging information are preserved.
-  Validation and row-level error reporting work correctly.
-  Normalization and cleaned-value presentation work correctly.
-  Deterministic matching follows the approved precedence.
-  Conflicting matches require explicit manual resolution.
-  No automatic merging occurs for conflicting identities.
-  Production import is idempotent.
-  Re-import does not create duplicate students.
-  Import state transitions are explicit.
-  Failed and partially completed imports can be investigated and safely recovered.
-  Previously successful rows are not duplicated during recovery.
-  Student Management remains the canonical owner of student data.
-  Account provisioning integrates through Identity's existing policy.
-  Authentication and authorization are enforced server-side.
-  Validation, failure handling, historical preservation, and security behavior are tested.
-  Relevant audit/accountability information is preserved.
-  Queries and import processing remain bounded and avoid known performance anti-patterns.
-  Automated tests cover the defined business rules and failure cases.
-  Required human review is completed for all task-graph items.

---

## 10. Out of Scope

- Redefining Student Management's canonical student data model.
- Academic Foundation master-data management.
- Verification decision policy.
- Document management.
- Finance.
- Results and eligibility.
- Faculty management.
- Reporting/analytics.
- A generic Correction module.
- Automatic merging of conflicting student identities.
- Direct production import bypassing staging.
- University/ERP modules not explicitly defined by the architecture.
- Exact verification field/document policy.
- Unspecified API contracts or physical database details.

The exact verification policy remains explicitly TBD and is a separate business-policy decision.

---

## 11. Open Questions

1. What exact API routes and request/response contracts should expose the import workflow?
2. What exact database schema, constraints, and indexes should represent ImportBatch and staging rows?
3. What exact role/permission matrix controls upload, validation, matching, manual resolution, and production import?
4. What exact file-format, size, encoding, and structural validation rules should apply to Government Excel files?
5. What exact normalization rules should apply to each imported field?
6. What exact row-level validation rules should apply to each source field?
7. What exact conflict-resolution UI and permitted resolution actions should be provided?
8. What exact import cancellation/retry permissions and state-transition rules should apply?
9. What exact source-file identity/fingerprint mechanism should be used to enforce idempotency?
10. What exact account-provisioning behavior should occur when imported students are created or associated?

These are left open because the supplied architecture/task material does not define the detailed business/API/schema rules.

---

## 12. Dependencies

### Direct task dependencies

**Student Management**
→ Import batch and staging-row database foundation

**Academic Foundation**
→ Import batch and staging-row database foundation

**Import batch/staging foundation**
→ Government Excel upload/import-batch creation

**Upload/import-batch creation**
→ Excel extraction/staging preservation

**Extraction/staging**
→ Validation/row-error reporting

**Validation**
→ Normalization/cleaned-value presentation

**Normalization + Student search/detail**
→ Deterministic student matching

**Deterministic matching**
→ Conflict detection/manual resolution

**Deterministic matching + Conflict resolution + Government-source preservation**
→ Idempotent production student import

**Idempotent production import**
→ Import state-machine/failure/recovery

**Idempotent production import + Initial student account provisioning policy**
→ Imported-student account provisioning

**Imported-student account provisioning + Student academic enrollment**
→ End-to-end government import → student → enrollment → account provisioning

**Status:** PRD #4 — `PRD-onboarding-import.md`