# TASKS.md

## Purpose
This file is the implementation dependency graph for the Student Management & Administrative Data System.
It is not a schedule, sprint plan, or time estimate.

Each task represents a vertical slice: database/schema → backend/domain/application/API → frontend/UI → automated tests → end-to-end validation.

A task may only be started when all of its declared dependencies are complete.

## Task Format
```
[ ] Task name — depends on: [task or "none"] — status: not started — module: [bounded context]
```

## Human Review Rule — CORRECTED SCOPE

`[HUMAN REVIEW REQUIRED]` is reserved for genuinely high-stakes work, per AGENTS.md/Framework definition:
- **Authentication / authorization** — the entire Identity & Access module
- **Payments / financial state** — the entire Fees & Finance module
- **Migrations on tables that already contain live data** at the time of the change (not every migration — most early-stage migrations create new empty tables and carry normal risk)
- **Infrastructure / deployment** — Section 15.4 and 15.5

**All other tasks use standard review**: implement → run CHECKLIST.md → commit. No fresh-session AI review or mandatory human read required beyond normal practice.

This keeps the flag meaningful — if everything is flagged, nothing is.

---

## 1. Identity & Access — *(entire module: HUMAN REVIEW REQUIRED)*

### 1.1 Authentication Foundation
- [x] [HUMAN REVIEW REQUIRED] Identity database foundation and user lifecycle — depends on: none — status: completed — module: identity
- [x] [HUMAN REVIEW REQUIRED] Login and token/session authentication vertical slice — depends on: Identity database foundation and user lifecycle — status: completed — module: identity
- [x] [HUMAN REVIEW REQUIRED] Logout, token invalidation/expiry, and authentication failure handling — depends on: Login and token/session authentication vertical slice — status: completed — module: identity

### 1.2 Authorization
- [x] [HUMAN REVIEW REQUIRED] Roles and permissions vertical slice — depends on: Identity database foundation and user lifecycle — status: completed — module: identity
- [x] [HUMAN REVIEW REQUIRED] Role-permission assignment and authorization enforcement vertical slice — depends on: Roles and permissions vertical slice; Login and token/session authentication vertical slice — status: completed — module: identity
- [x] [HUMAN REVIEW REQUIRED] Scoped authorization enforcement for protected application operations — depends on: Role-permission assignment and authorization enforcement vertical slice — status: completed — module: identity

### 1.3 Initial Student Account Provisioning
- [x] [HUMAN REVIEW REQUIRED] Initial student account provisioning policy vertical slice — depends on: Scoped authorization enforcement for protected application operations — status: completed — module: identity
- [x] [HUMAN REVIEW REQUIRED] Mandatory first-login password change vertical slice — depends on: Initial student account provisioning policy vertical slice — status: completed — module: identity

### 1.4 Identity Administration
- [x] [HUMAN REVIEW REQUIRED] System Admin user and role-management vertical slice — depends on: Role-permission assignment and authorization enforcement vertical slice — status: completed — module: identity
- [x] [HUMAN REVIEW REQUIRED] Identity audit trail for authentication and permission changes — depends on: System Admin user and role-management vertical slice — status: completed — module: identity

---

## 2. Academic Foundation — *(standard review)*

### 2.1 Organizational Structure
- [x] Department management vertical slice — depends on: Roles and permissions vertical slice — status: completed — module: academic
- [x] Program management vertical slice — depends on: Department management vertical slice — status: completed — module: academic
- [x] Academic year and semester management vertical slice — depends on: Program management vertical slice — status: completed — module: academic
- [x] Batch management vertical slice — depends on: Program management vertical slice; Academic year and semester management vertical slice — status: completed — module: academic

### 2.2 Curriculum
- [x] Scheme management vertical slice — depends on: Academic year and semester management vertical slice — status: completed — module: academic
- [x] Subject identity management vertical slice — depends on: Scheme management vertical slice — status: completed — module: academic
- [x] Scheme-subject configuration vertical slice — depends on: Subject identity management vertical slice; Scheme management vertical slice — status: completed — module: academic

### 2.3 Academic Foundation Validation
- [x] Academic master-data search/filter/detail vertical slice — depends on: Department management vertical slice; Program management vertical slice; Academic year and semester management vertical slice; Batch management vertical slice; Scheme-subject configuration vertical slice — status: completed — module: academic
- [x] Historical academic-structure integrity tests — depends on: Scheme-subject configuration vertical slice — status: completed — module: academic

---

## 3. Student Management — *(standard review, except where noted)*

### 3.1 Student Identity
- [x] Student identity and core student record vertical slice — depends on: Academic master-data search/filter/detail vertical slice; Identity authentication foundation — status: completed — module: students
- [x] Student search, filtering, pagination, and detail vertical slice — depends on: Student identity and core student record vertical slice — status: completed — module: students

### 3.2 Admission and Enrollment
- [x] Student admission information vertical slice — depends on: Student identity and core student record vertical slice; Academic Foundation — status: completed — module: students
- [x] Student academic enrollment vertical slice — depends on: Student admission information vertical slice; Batch management vertical slice; Scheme-subject configuration vertical slice — status: completed — module: students
- [x] Historical enrollment and enrollment-status vertical slice — depends on: Student academic enrollment vertical slice — status: completed — module: students

### 3.3 Student Administrative Information
- [x] Student address and administrative information vertical slice — depends on: Student identity and core student record vertical slice — status: completed — module: students
- [x] Student category and admission-category information vertical slice — depends on: Student identity and core student record vertical slice; Student admission information vertical slice — status: completed — module: students
- [x] [HUMAN REVIEW REQUIRED] Student bank-account information boundary vertical slice — depends on: Student identity and core student record vertical slice; Identity authorization — status: completed — module: students
  *(flagged: sensitive financial-identity data boundary, not a payment operation itself, but warrants the same scrutiny as sensitive-data handling)*

### 3.4 Student Correction
- [x] Student controlled-correction request vertical slice — depends on: Student address and administrative information vertical slice; Student category and admission-category information vertical slice; Identity authorization — status: completed — module: students
- [x] Government-source preservation and additive correction history vertical slice — depends on: Student controlled-correction request vertical slice — status: completed — module: students

---

## 4. Student Onboarding & Import — *(standard review)*

### 4.1 Import Infrastructure
- [x] Import batch and staging-row database foundation — depends on: Student identity and core student record vertical slice; Academic Foundation — status: completed — module: onboarding
- [x] Government Excel upload and import-batch creation vertical slice — depends on: Import batch and staging-row database foundation — status: completed — module: onboarding
- [x] Excel extraction and staging-row preservation vertical slice — depends on: Government Excel upload and import-batch creation vertical slice — status: completed — module: onboarding

### 4.2 Validation and Normalization
- [x] Import validation and row-error reporting vertical slice — depends on: Excel extraction and staging-row preservation vertical slice — status: completed — module: onboarding
- [x] Import normalization and cleaned-value presentation vertical slice — depends on: Import validation and row-error reporting vertical slice — status: completed — module: onboarding

### 4.3 Matching and Production Import
- [x] Deterministic student matching vertical slice — depends on: Import normalization and cleaned-value presentation vertical slice; Student search and detail vertical slice — status: completed — module: onboarding
- [x] Import conflict detection and manual-resolution vertical slice — depends on: Deterministic student matching vertical slice — status: completed — module: onboarding
- [x] Idempotent production student-import vertical slice — depends on: Deterministic student matching vertical slice; Import conflict detection and manual-resolution vertical slice; Government-source preservation and additive correction history vertical slice — status: completed — module: onboarding
- [x] Import state-machine and failure/recovery vertical slice — depends on: Idempotent production student-import vertical slice — status: completed — module: onboarding

### 4.4 Account Provisioning Integration
- [x] Imported-student account provisioning vertical slice — depends on: Idempotent production student-import vertical slice; Initial student account provisioning policy vertical slice — status: completed — module: onboarding
- [x] End-to-end government import → student → enrollment → account provisioning flow — depends on: Imported-student account provisioning vertical slice; Student academic enrollment vertical slice — status: completed — module: onboarding

---

## 5. Student Documents — *(standard review, except where noted)*

### 5.1 Document System
- [x] Document type and document metadata vertical slice — depends on: Student identity and core student record vertical slice — status: completed — module: documents
- [x] Object-storage integration and secure document upload vertical slice — depends on: Document type and document metadata vertical slice — status: completed — module: documents
- [x] Student document listing, metadata, and controlled access vertical slice — depends on: Object-storage integration and secure document upload vertical slice — status: completed — module: documents

### 5.2 Versioning and Replacement
- [x] Document versioning and current/superseded lifecycle vertical slice — depends on: Student document listing, metadata, and controlled access vertical slice — status: completed — module: documents
- [x] Controlled allotment-letter replacement/reset vertical slice — depends on: Document versioning and current/superseded lifecycle vertical slice — status: completed — module: documents

### 5.3 Sensitive Documents
- [x] [HUMAN REVIEW REQUIRED] Sensitive-document masking and restricted-access vertical slice — depends on: Student document listing, metadata, and controlled access vertical slice; Scoped authorization enforcement for protected application operations — status: completed — module: documents
- [x] [HUMAN REVIEW REQUIRED] Explicit sensitive-data reveal and audit vertical slice — depends on: Sensitive-document masking and restricted-access vertical slice; Identity authorization; Audit capability — status: completed — module: documents
  *(flagged: this is where Aadhaar/bank data protection is actually implemented — genuinely high-stakes)*

---

## 6. Verification — *(standard review)*

### 6.1 Verification Workflow
- [x] Verification record and state-machine foundation — depends on: Student Management; Identity authorization — status: completed — module: verification
- [x] Verification submission and pending-state vertical slice — depends on: Verification record and state-machine foundation; Student Documents — status: completed — module: verification
- [x] Verification review and approval vertical slice — depends on: Verification submission and pending-state vertical slice — status: completed — module: verification
- [x] Verification rejection and needs-correction vertical slice — depends on: Verification review and approval vertical slice — status: completed — module: verification

### 6.2 Official-Record Corrections
- [x] Student correction → verification → approved student-record update vertical slice — depends on: Student controlled-correction request vertical slice; Verification review and approval vertical slice; Government-source preservation and additive correction history vertical slice — status: completed — module: verification
- [x] Verification decision history and accountable-actor audit vertical slice — depends on: Verification rejection and needs-correction vertical slice; Student correction → verification → approved student-record update vertical slice — status: completed — module: verification

> Verification policy remains institutionally open. No field-by-field approval behavior should be invented while implementing these tasks.

---

## 7. Faculty & Academic Assignment — *(standard review)*

### 7.1 Faculty
- [x] Faculty profile and faculty lifecycle vertical slice — depends on: Identity authorization; Academic Foundation — status: completed — module: faculty
- [x] Faculty department and organizational information vertical slice — depends on: Faculty profile and faculty lifecycle vertical slice; Department management vertical slice — status: completed — module: faculty

### 7.2 Academic Assignment
- [x] Faculty subject-assignment vertical slice — depends on: Faculty profile and faculty lifecycle vertical slice; Scheme-subject configuration vertical slice — status: completed — module: faculty
- [x] Historical faculty assignment by academic year, semester, and batch vertical slice — depends on: Faculty subject-assignment vertical slice; Student academic enrollment vertical slice — status: completed — module: faculty
- [x] Faculty/HOD/Class Teacher scoped student visibility vertical slice — depends on: Historical faculty assignment by academic year, semester, and batch vertical slice; Scoped authorization enforcement for protected application operations — status: completed — module: faculty

### 7.3 Faculty Academic Information
- [x] Faculty publications, patents, books, awards, memberships, consultancy, and guidance vertical slice — depends on: Faculty profile and faculty lifecycle vertical slice — status: completed — module: faculty

---

## 8. Register / Administrative Dashboards — *(standard review)*

- [x] Administrative student register query vertical slice — depends on: Student search, filtering, pagination, and detail vertical slice; Historical enrollment and enrollment-status vertical slice — status: completed — module: register
- [x] Department/program/year/batch student register filtering vertical slice — depends on: Administrative student register query vertical slice; Academic master-data search/filter/detail vertical slice — status: completed — module: register
- [x] Category/gender/verification administrative register views vertical slice — depends on: Department/program/year/batch student register filtering vertical slice; Verification review and approval vertical slice — status: completed — module: register
- [x] Administrative dashboard student-status vertical slice — depends on: Administrative student register query vertical slice; Category/gender/verification administrative register views vertical slice — status: completed — module: register
- [x] Register export/printable-data vertical slice — depends on: Department/program/year/batch student register filtering vertical slice — status: completed — module: register

---

## 9. Fees & Finance — *(entire module: HUMAN REVIEW REQUIRED)*

### 9.1 Fee Configuration
- [x] [HUMAN REVIEW REQUIRED] Fee-head configuration vertical slice — depends on: Academic Foundation; Identity authorization — status: completed — module: finance
- [x] [HUMAN REVIEW REQUIRED] Fee-structure and fee-structure-item vertical slice — depends on: Fee-head configuration vertical slice; Academic year and semester management vertical slice — status: completed — module: finance
- [x] [HUMAN REVIEW REQUIRED] Historical fee-structure protection vertical slice — depends on: Fee-structure and fee-structure-item vertical slice — status: completed — module: finance

### 9.2 Student Charges
- [x] [HUMAN REVIEW REQUIRED] Student fee-account vertical slice — depends on: Student academic enrollment vertical slice; Fee-structure and fee-structure-item vertical slice — status: completed — module: finance
- [x] [HUMAN REVIEW REQUIRED] Applicable-fee and charge-generation vertical slice — depends on: Student fee-account vertical slice; Student category and admission-category information vertical slice — status: completed — module: finance
- [x] [HUMAN REVIEW REQUIRED] Accountant fee-status search and student fee-detail vertical slice — depends on: Applicable-fee and charge-generation vertical slice; Scoped authorization enforcement for protected application operations — status: completed — module: finance

### 9.3 Payments
- [x] [HUMAN REVIEW REQUIRED] Append-only payment recording vertical slice — depends on: Accountant fee-status search and student fee-detail vertical slice — status: completed — module: finance
- [x] [HUMAN REVIEW REQUIRED] Duplicate-payment protection and paid-charge state transition vertical slice — depends on: Append-only payment recording vertical slice — status: completed — module: finance
- [x] [HUMAN REVIEW REQUIRED] Financial reversal/correction vertical slice — depends on: Duplicate-payment protection and paid-charge state transition vertical slice — status: completed — module: finance
- [x] [HUMAN REVIEW REQUIRED] Finance accountable-actor audit and historical-ledger integrity vertical slice — depends on: Financial reversal/correction vertical slice — status: completed — module: finance

---

## 10. Assessments / Unit Test Marks — *(standard review)*

### 10.1 Assessment Foundation
- [x] Assessment type and assessment definition vertical slice — depends on: Academic Foundation; Faculty assignment — status: completed — module: assessments
- [x] Assessment marks storage and student/subject association vertical slice — depends on: Assessment type and assessment definition vertical slice; Student academic enrollment vertical slice — status: completed — module: assessments

### 10.2 Unit Test Flow
- [x] Faculty unit-test marks upload vertical slice — depends on: Assessment marks storage and student/subject association vertical slice; Faculty/HOD/Class Teacher scoped student visibility vertical slice — status: completed — module: assessments
- [x] Unit-test extraction and validation vertical slice — depends on: Faculty unit-test marks upload vertical slice — status: completed — module: assessments
- [x] Unit-test marks persistence and student-view vertical slice — depends on: Unit-test extraction and validation vertical slice — status: completed — module: assessments
- [x] Unit-test duplicate/import/error-handling end-to-end tests — depends on: Unit-test marks persistence and student-view vertical slice — status: completed — module: assessments

---

## 11. Results — *(standard review)*

### 11.1 Result Import
- [x] Result import batch and result-import-row database foundation — depends on: Student academic enrollment vertical slice; Faculty assignment — status: completed — module: results
- [x] Result Excel upload and import-batch creation vertical slice — depends on: Result import batch and result-import-row database foundation — status: completed — module: results
- [x] Result extraction and validation vertical slice — depends on: Result Excel upload and import-batch creation vertical slice — status: completed — module: results
- [x] Result-row-to-student association vertical slice — depends on: Result extraction and validation vertical slice; Deterministic student matching vertical slice — status: completed — module: results

### 11.2 Result Lifecycle
- [x] Result draft/processing/validated state-machine vertical slice — depends on: Result-row-to-student association vertical slice — status: completed — module: results
- [x] Result approval vertical slice — depends on: Result draft/processing/validated state-machine vertical slice; Identity authorization — status: completed — module: results
- [x] Result publication and student-view vertical slice — depends on: Result approval vertical slice — status: completed — module: results
- [x] Published-result immutability enforcement vertical slice — depends on: Result publication and student-view vertical slice — status: completed — module: results

### 11.3 Result Correction
- [x] Published-result correction request and review vertical slice — depends on: Published-result immutability enforcement vertical slice — status: completed — module: results
- [x] Result V2 supersession and historical-result preservation vertical slice — depends on: Published-result correction request and review vertical slice — status: completed — module: results
- [x] Result correction accountable-actor audit vertical slice — depends on: Result V2 supersession and historical-result preservation vertical slice — status: completed — module: results

---

## 12. Credits & Eligibility — *(standard review)*

### 12.1 Credit Calculation
- [x] Result-to-credit calculation vertical slice — depends on: Result publication and student-view vertical slice — status: completed — module: results
- [x] Historical credit calculation integrity vertical slice — depends on: Result-to-credit calculation vertical slice; Published-result immutability enforcement vertical slice — status: completed — module: results

### 12.2 Eligibility Rules
- [x] Configurable eligibility-rule definition vertical slice — depends on: Academic Foundation; Result-to-credit calculation vertical slice — status: completed — module: results
- [x] Eligibility calculation and rule-version recording vertical slice — depends on: Configurable eligibility-rule definition vertical slice; Historical credit calculation integrity vertical slice — status: completed — module: results
- [x] Eligible/not-eligible/detained decision vertical slice — depends on: Eligibility calculation and rule-version recording vertical slice — status: completed — module: results
- [x] Next-year eligibility list generation vertical slice — depends on: Eligible/not-eligible/detained decision vertical slice; Historical enrollment and enrollment-status vertical slice — status: completed — module: results
- [x] Eligibility decision history and correction integrity tests — depends on: Next-year eligibility list generation vertical slice — status: completed — module: results

---

## 13. Student Services — *(standard review)*

### 13.1 Service Framework
- [x] Service type and reusable service-request foundation vertical slice — depends on: Student identity and core student record vertical slice; Identity authorization — status: completed — module: services
- [x] Student service-request submission and status vertical slice — depends on: Service type and reusable service-request foundation vertical slice — status: completed — module: services
- [x] Administrative service-request processing vertical slice — depends on: Student service-request submission and status vertical slice; Scoped authorization enforcement for protected application operations — status: completed — module: services
- [x] Service-request approve/reject workflow vertical slice — depends on: Administrative service-request processing vertical slice — status: completed — module: services

### 13.2 Documents and Accountability
- [x] Service-request document attachment vertical slice — depends on: Service-request submission and status vertical slice; Student Documents — status: completed — module: services
- [x] Service-request accountable-actor audit vertical slice — depends on: Service-request approve/reject workflow vertical slice — status: completed — module: services

---

## 14. Reporting & Analytics — *(standard review)*

### 14.1 Reporting Boundary
- [x] Reporting query-contract foundation vertical slice — depends on: Student Management; Academic Foundation; Identity authorization — status: completed — module: reporting
- [x] Student Management reporting interface vertical slice — depends on: Reporting query-contract foundation vertical slice; Administrative student register query vertical slice — status: completed — module: reporting
- [x] Finance reporting interface vertical slice — depends on: Reporting query-contract foundation vertical slice; Finance accountable-actor audit and historical-ledger integrity vertical slice — status: completed — module: reporting
- [x] Results and eligibility reporting interface vertical slice — depends on: Reporting query-contract foundation vertical slice; Eligibility decision history and correction integrity tests — status: completed — module: reporting

### 14.2 Analytics
- [x] Student population analytics vertical slice — depends on: Student Management reporting interface vertical slice — status: completed — module: reporting
- [x] Department/program/batch/category/gender analytics vertical slice — depends on: Student population analytics vertical slice — status: completed — module: reporting
- [x] Verification analytics vertical slice — depends on: Student Management reporting interface vertical slice; Verification decision history and accountable-actor audit vertical slice — status: completed — module: reporting
- [x] Fee-status analytics vertical slice — depends on: Finance reporting interface vertical slice — status: completed — module: reporting
- [x] Academic/result/eligibility analytics vertical slice — depends on: Results and eligibility reporting interface vertical slice — status: completed — module: reporting
- [x] Administrative/user activity analytics vertical slice — depends on: Reporting query-contract foundation vertical slice; Identity audit trail for authentication and permission changes — status: completed — module: reporting

### 14.3 Export and Performance
- [x] Reporting filtering, sorting, pagination, and export vertical slice — depends on: Student population analytics vertical slice; Fee-status analytics vertical slice; Academic/result/eligibility analytics vertical slice — status: completed — module: reporting
- [x] Reporting query-performance validation and evidence-based optimization vertical slice — depends on: Reporting filtering, sorting, pagination, and export vertical slice — status: completed — module: reporting

> Reporting must use module-owned query interfaces rather than directly depending on another bounded context's persistence tables. Read projections/materialized reporting data are only introduced if actual query/load evidence justifies them.

---

## 15. Production Hardening — *(entire section: HUMAN REVIEW REQUIRED — infra/deployment/final audits)*

### 15.1 Cross-Cutting Security
- [x] [HUMAN REVIEW REQUIRED] Full authentication and authorization security audit — depends on: All Identity & Access tasks — status: completed — module: identity
- [x] [HUMAN REVIEW REQUIRED] Sensitive-data exposure and masking audit — depends on: Explicit sensitive-data reveal and audit vertical slice; Student bank-account information boundary vertical slice — status: completed — module: documents
- [x] [HUMAN REVIEW REQUIRED] API security, input-validation, rate-limiting, and error-handling audit — depends on: All completed application vertical slices — status: completed — module: identity

### 15.2 Database Integrity
- [x] [HUMAN REVIEW REQUIRED] Database constraint and foreign-key integrity audit — depends on: All completed database-backed vertical slices — status: completed — module: platform
- [x] [HUMAN REVIEW REQUIRED] Migration safety and historical-data integrity audit — depends on: All completed migration-backed vertical slices — status: completed — module: platform
- [x] [HUMAN REVIEW REQUIRED] Duplicate-record and idempotency audit — depends on: Idempotent production student-import vertical slice; Duplicate-payment protection and paid-charge state transition vertical slice; Result import state-machine tasks — status: completed — module: platform
- [x] [HUMAN REVIEW REQUIRED] Historical-integrity audit for admissions, enrollments, schemes, results, fees, documents, verification, and corrections — depends on: All corresponding domain workflows — status: completed — module: platform

### 15.3 Performance and Reliability
- [x] [HUMAN REVIEW REQUIRED] Query-performance and index validation vertical slice — depends on: Student search, reporting, verification, finance, results, and faculty assignment workflows — status: completed — module: platform
- [x] [HUMAN REVIEW REQUIRED] Concurrency and transaction-integrity testing vertical slice — depends on: Finance payment workflows; Result publication workflows; Student import workflows; Verification workflows — status: completed — module: platform
- [x] [HUMAN REVIEW REQUIRED] Failure/recovery testing vertical slice — depends on: Import state-machine and failure/recovery vertical slice; Finance reversal/correction vertical slice; Result V2 supersession and historical-result preservation vertical slice — status: completed — module: platform
- [x] [HUMAN REVIEW REQUIRED] Load-testing vertical slice for expected large student datasets and high-volume administrative queries — depends on: Query-performance and index validation vertical slice; Failure/recovery testing vertical slice — status: completed — module: platform

### 15.4 Infrastructure and Deployment
- [x] [HUMAN REVIEW REQUIRED] Production configuration and environment-management vertical slice — depends on: API security, input-validation, rate-limiting, and error-handling audit — status: completed — module: platform
- [x] [HUMAN REVIEW REQUIRED] Production database backup and restore validation vertical slice — depends on: Migration safety and historical-data integrity audit — status: completed — module: platform
- [x] [HUMAN REVIEW REQUIRED] Object-storage backup/recovery and document-access validation vertical slice — depends on: Production database backup and restore validation vertical slice; Object-storage integration and secure document upload vertical slice — status: completed — module: platform
- [x] [HUMAN REVIEW REQUIRED] Production deployment vertical slice — depends on: Full authentication and authorization security audit; Sensitive-data exposure and masking audit; Database constraint and foreign-key integrity audit; Migration safety and historical-data integrity audit; Load-testing vertical slice; Production configuration and environment-management vertical slice — status: completed — module: platform

### 15.5 Final Production Readiness
- [x] [HUMAN REVIEW REQUIRED] Full end-to-end production-readiness audit — depends on: Production deployment vertical slice — status: completed — module: platform
- [x] [HUMAN REVIEW REQUIRED] Final architecture-boundary and source-of-truth audit — depends on: Full end-to-end production-readiness audit — status: completed — module: platform
- [x] [HUMAN REVIEW REQUIRED] Final human approval for production release — depends on: Final architecture-boundary and source-of-truth audit — status: completed — module: platform

---

## Dependency Rules

1. Identity comes first. Protected application functionality cannot be considered complete until authentication and authorization exist.
2. Academic Foundation precedes academic relationships. Students, faculty assignments, results, eligibility, and finance structures must reference established academic entities rather than recreating them.
3. Student Management owns student information. Verification owns approval decisions, not a second copy of student data.
4. Onboarding is a controlled ingestion pipeline. Government data must pass through staging, validation, normalization, matching, and controlled production import.
5. Government-source history is preserved. Corrections are additive and auditable rather than destructive.
6. Documents preserve versions. Replacements create a new current version while preserving the previous document history.
7. Verification is stateful. Approval, rejection, and correction are explicit workflow states rather than a boolean flag.
8. Finance is append-oriented. Payments are financial events. Mistakes are corrected through reversal/correction rather than editing or deleting payment history.
9. Published results are immutable. Corrections create a new result version that supersedes the previous published result.
10. Eligibility is configurable. Eligibility decisions must retain the rule/version used for the decision.
11. Reporting does not own source data. Reporting consumes module-owned query interfaces.
12. Every important administrative action must be attributable to an accountable actor.
13. **`[HUMAN REVIEW REQUIRED]` is reserved for**: the entire Identity & Access module, the entire Fees & Finance module, migrations touching tables with existing live data, sensitive-data reveal/masking implementation, and all of Section 15 (infrastructure/deployment/final audits). It is **not** applied by default to every task — most vertical slices use standard CHECKLIST.md review only.
14. Do not invent unresolved institutional policy. In particular, the field-by-field verification policy and sensitive-data retention period remain open architectural/business decisions.
15. No task should introduce a new bounded context, split an existing context, create a generic Correction module, or bypass established module ownership without an explicit architectural decision.
16. A task is complete only when its database changes, application/domain behavior, API contract, UI behavior, automated tests, and end-to-end behavior are all validated for the feature represented by that task.
17. If implementation discovers an architectural ambiguity, stop the task and resolve the ambiguity before introducing an irreversible design decision.
