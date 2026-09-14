# FILE_MAP.md — Student Management & Administrative Data System

## Authoritative System File Map & Implementation Directory Structure

**Governing Architecture:** `ARCHITECTURE.md`, `DECISIONS.md`, `DATABASE_ARCHITECTURE.md`, `AGENT.md`  
**Stack Baseline:** Django + Django REST Framework + PostgreSQL (Modular Monolith) | React (Vite) Frontend  
**Database Target:** PostgreSQL (connection parameters managed in `backend/.env` / `config/settings.py`)

---

## 1. High-Level Directory Overview

```
student-management/
├── backend/                        # Django + DRF backend application
│   ├── config/                     # Project configuration & settings (PostgreSQL, JWT, CORS, Storage)
│   ├── common/                     # Cross-cutting foundational utilities (base models, errors, audit decorators)
│   ├── apps/                       # 12 Domain-Driven Bounded Context modules
│   │   ├── identity/               # 1. Identity & Access (Auth, RBAC, JWT, Accounts)
│   │   ├── academic/               # 2. Academic Foundation (Depts, Programs, Semesters, Schemes, Subjects)
│   │   ├── students/               # 3. Student Management (Identity, Admission, Categories, Bank, Corrections)
│   │   ├── onboarding/             # 4. Onboarding & Import (Staging, Deduplication, Excel pipeline)
│   │   ├── verification/           # 5. Verification (Requests, Requirements, Decisions, Workflow)
│   │   ├── documents/              # 6. Documents (Metadata, Object Storage references, Versioning)
│   │   ├── faculty/                # 7. Faculty & Assignment (Profiles, Teaching assignments, Accreditations)
│   │   ├── results/                # 8. Results & Eligibility (Assessments, Marks, Results, Credits, Rules)
│   │   ├── finance/                # 9. Fees & Finance (Fee heads, Structures, Charges, Append-only Ledger)
│   │   ├── services/               # 10. Student Services (Service requests, Workflow transitions)
│   │   ├── audit/                  # 11. Audit & Observability (Audit logs, Sensitive data reveal logs)
│   │   └── reporting/              # 12. Reporting & Analytics (Read-only projections & exports; no owned tables)
│   ├── manage.py                   # Django CLI management script
│   ├── requirements.txt            # Python dependencies (Django, djangorestframework, psycopg2-binary, etc.)
│   └── .env.example                # Template for PostgreSQL credentials, JWT secret, storage keys
│
├── frontend/                       # React (Vite) Single Page Application
│   ├── src/
│   │   ├── api/                    # Axios/Fetch HTTP client, interceptors, error mapping
│   │   ├── auth/                   # JWT storage, AuthContext, role-based RouteGuard
│   │   ├── components/             # Reusable UI library (Tables, Modals, Forms, Alerts, Badges)
│   │   ├── layouts/                # AppLayout, Sidebar, Navbar, Breadcrumbs
│   │   ├── modules/                # Domain module feature pages, hooks, and local components
│   │   ├── routes/                 # Central router configuration
│   │   └── styles/                 # Design tokens, typography, CSS themes
│   ├── package.json                # Frontend dependencies
│   └── vite.config.js              # Vite bundler configuration
│
├── doc/                            # Architecture & Governance Documentation
│   ├── ARCHITECTURE.md             # System architecture & core boundaries
│   ├── DECISIONS.md                # Architectural Decision Records (ADRs)
│   ├── DATABASE_ARCHITECTURE.md    # Physical DB schema, DDL, ERD, Constraints & Indexes
│   ├── FILE_MAP.md                 # This file: Authoritative file map
│   ├── AGENT.md                    # Engineering & implementation contract
│   ├── TASKS.md                    # Vertical slice dependency graph
│   ├── FLOW.md                     # System workflows & lifecycle diagrams
│   ├── RUNBOOK.md                  # Incident response & operational runbooks
│   ├── CHECKLIST.md                # Quality assurance & pre-commit validation
│   └── prds/                       # 15 Detailed Product Requirement Documents
│
└── docker-compose.yml              # PostgreSQL, Backend, and Frontend local orchestration
```

---

## 2. Standard Module Layering Architecture

Every bounded context in `backend/apps/<module>/` strictly follows the layered architecture defined in `AGENT.md`:

```
backend/apps/<module>/
├── __init__.py
├── apps.py                         # Django AppConfig with explicit name/label
├── models.py                       # Persistence entities (matches DATABASE_ARCHITECTURE.md)
├── domain/                         # Pure domain logic (entities, invariants, value objects, state machines)
│   ├── __init__.py
│   ├── entities.py                 # Domain models independent of Django ORM
│   ├── state_machines.py           # Explicit state transition rules (e.g. SUBMITTED -> VERIFIED)
│   └── exceptions.py               # Domain-specific validation & business errors
├── services/                       # Application use cases & workflow orchestration
│   ├── __init__.py
│   ├── commands.py                 # Write operations (executes within transaction.atomic)
│   └── queries.py                  # Read operations (optimized querysets, aggregations)
├── api/                            # HTTP / REST presentation layer
│   ├── __init__.py
│   ├── serializers.py              # DRF input validation & response formatting
│   ├── views.py                    # DRF ViewSets / APIViews (calls application services)
│   ├── permissions.py              # Module-level RBAC checks
│   └── urls.py                     # Route declarations mapped under /api/v1/<module>/
└── tests/                          # Automated tests
    ├── __init__.py
    ├── test_domain.py              # Pure unit tests for invariants & state transitions
    ├── test_services.py            # Service layer workflow & transaction tests
    └── test_api.py                 # DRF endpoint & permission integration tests
```

---

## 3. Detailed Backend File Map

### 3.1 `backend/config/` (Project Configuration)

| File Path | Description / Responsibility |
|---|---|
| `backend/config/__init__.py` | Package initialization |
| `backend/config/settings.py` | Dev settings: SQLite default, `DB_ENGINE=postgresql` switches to PostgreSQL via env vars; JWT, Installed Apps, Middleware, REST_FRAMEWORK |
| `backend/config/settings_production.py` | Production settings: strict SSL/HSTS, DB pooling, JSON logging (`DEBUG=False`) |
| `backend/config/urls.py` | Root URL router mounting `/api/v1/` routes for all 14 apps (identity/audit/academic/students/onboarding/documents/verification/faculty/register/finance/assessments/results/services/reporting) |
| `backend/config/wsgi.py` | WSGI entry for Gunicorn prod (`--workers 4 --threads 2`) |
| `backend/config/asgi.py` | ASGI application entry point |

### 3.2 `backend/common/` (Shared Infrastructure & Utilities — synced to actual tree)

| File Path | Description / Responsibility |
|---|---|
| `backend/common/__init__.py` | Package initialization |
| `backend/common/models.py` | `TimeStampedUUIDModel` (UUID PK, `created_at`, `updated_at`) |
| `backend/common/exceptions.py` | Custom domain exceptions (DomainException, InvariantViolationError, StateTransitionError, EntityNotFoundError) |
| `backend/common/exception_handler.py` | DRF handler: standardized JSON, masks 500s in prod, 429 JSON |
| `backend/common/security.py` | AES encryption/decryption for Aadhaar/bank per ADR-015 |
| `backend/common/throttling.py` | `AuthRateThrottle` (5/min), `SensitiveRevealRateThrottle` (10/hr) — ADR-031 |
| `backend/common/tests/` | Audits: `test_api_security_audit`, `test_database_constraints_audit`, `test_migration_safety_audit`, `test_idempotency_audit`, `test_historical_integrity_audit`, `test_query_performance_audit`, `test_concurrency_audit`, `test_failure_recovery_audit`, `test_load_benchmark` |

> Removed from map (do not exist in prototype): `permissions.py`, `pagination.py`, `storage.py`, `audit_decorator.py`. RBAC lives in `apps/identity/api/permissions.py`; pagination is per-view; storage is `MEDIA`/object-storage via documents service + `scripts/verify_document_storage.py`.

---

### 3.3 Module 1: `backend/apps/identity/` (Identity & Access)

**Tables Owned:** `users`, `roles`, `permissions`, `user_roles`, `role_permissions`  
**Responsibilities:** User lifecycle, JWT token issuance/invalidation, RBAC enforcement, Account provisioning policy (ADR-004).

| File Path | Description / Responsibility |
|---|---|
| `backend/apps/identity/apps.py` | `IdentityConfig` registration |
| `backend/apps/identity/models.py` | `User` (AbstractBaseUser), `Role`, `Permission`, `UserRole`, `RolePermission` |
| `backend/apps/identity/domain/state_machines.py` | User status rules (`ACTIVE`, `SUSPENDED`, `MUST_CHANGE_PASSWORD`, `INACTIVE`) |
| `backend/apps/identity/domain/rbac.py` | RBAC domain invariants, scope types (`SYSTEM`, `DEPARTMENT`, `BATCH`, `OWN`), canonical roles/permissions catalogue |
| `backend/apps/identity/domain/exceptions.py` | Authentication and domain error definitions |
| `backend/apps/identity/services/auth_service.py` | Login, JWT token generation, refresh, logout/blacklist |
| `backend/apps/identity/services/role_service.py` | Role and Permission creation, query services, and canonical RBAC seeding |
| `backend/apps/identity/services/provisioning.py` | Initial student account provisioning (Username=Enrollment, Password=Enrollment) |
| `backend/apps/identity/services/user_service.py` | User management, password resets, role assignment |
| `backend/apps/identity/api/serializers.py` | `LoginSerializer`, `UserDetailSerializer`, `RoleSerializer`, `PermissionSerializer` |
| `backend/apps/identity/api/views.py` | `LoginView`, `LogoutView`, `TokenRefreshView`, `UserViewSet`, `RoleViewSet`, `PermissionViewSet`, `SeedRBACView` |
| `backend/apps/identity/api/permissions.py` | DRF authorization enforcement classes (`RequirePermission`, `RequireRole`, `require_permission`, `require_role`) |
| `backend/apps/identity/api/urls.py` | Routes: `/api/v1/auth/login/`, `/logout/`, `/users/`, `/roles/`, `/permissions/`, `/rbac/seed/` |
| `backend/apps/identity/tests/test_auth.py` | Authentication & token tests |
| `backend/apps/identity/tests/test_logout.py` | Logout, token revocation/blacklisting, and failure handling tests |
| `backend/apps/identity/tests/test_roles_permissions.py` | Role and Permission model, invariant, and API tests |
| `backend/apps/identity/tests/test_rbac.py` | Role-permission assignment & enforcement tests |
| `backend/apps/identity/tests/test_scoped_enforcement.py` | Scoped authorization enforcement (SYSTEM, DEPARTMENT, BATCH, OWN) & object-level permission tests |
| `backend/apps/identity/tests/test_provisioning.py` | Student account provisioning policy (ADR-009) tests & endpoints |
| `backend/apps/identity/tests/test_password_change.py` | Mandatory first-login password change & access enforcement tests |
| `backend/apps/identity/tests/test_system_admin.py` | System Admin user and role management RBAC tests |
| `backend/apps/identity/tests/test_audit_trail.py` | Identity audit trail for authentication and permission changes tests |
| `backend/apps/identity/tests/test_auth_security_audit.py` | Full authentication and authorization security audit tests (cross-cutting, Task 15.1) |
| `backend/apps/identity/tests/test_user_lifecycle.py` | User lifecycle management tests (status transitions, account states) |

---

### 3.4 Module 2: `backend/apps/academic/` (Academic Foundation)

**Tables Owned:** `departments`, `programs`, `academic_years`, `semesters`, `batches`, `schemes`, `subjects`, `scheme_subjects`, `department_intakes`  
**Responsibilities:** Authoritative master data for departments, curricula, academic calendars, batch structures.

| File Path | Description / Responsibility |
|---|---|
| `backend/apps/academic/apps.py` | `AcademicConfig` registration |
| `backend/apps/academic/models.py` | `Department`, `Program`, `AcademicYear`, `Semester`, `Batch`, `Scheme`, `Subject`, `SchemeSubject`, `DepartmentIntake` |
| `backend/apps/academic/domain/invariants.py` | Semester ordering, credit validation, year date overlaps, intake capacity rules |
| `backend/apps/academic/services/academic_service.py` | Department, program, calendar, batch, intake, curriculum, and unified search operations |
| `backend/apps/academic/api/permissions.py` | RBAC permission classes (`CanManageAcademicStructure`, `CanManageCurriculum`) |
| `backend/apps/academic/api/serializers.py` | DRF serializers for all 9 academic master entities |
| `backend/apps/academic/api/views.py` | ViewSets for Department, Program, Batch, AcademicYear, Scheme, Subject, SchemeSubject, and Unified Search API |
| `backend/apps/academic/api/urls.py` | Routes: `/api/v1/academic/departments/`, `/programs/`, `/academic-years/`, `/semesters/`, `/batches/`, `/intakes/`, `/schemes/`, `/subjects/`, `/scheme-subjects/`, `/search/` |
| `backend/apps/academic/tests/test_departments_programs.py` | Department & Program CRUD, code uniqueness, scoped invariants, and RBAC enforcement tests |
| `backend/apps/academic/tests/test_academic_calendar.py` | Academic Year dates, current-year exclusivity, semester ordering, batch, and intake capacity tests |
| `backend/apps/academic/tests/test_curriculum.py` | Scheme, Subject, Scheme-Subject mapping, mark invariants, and locked historical integrity preservation tests |
| `backend/apps/academic/tests/test_academic_search.py` | Unified master-data search and department-scoped filtering tests |

---

### 3.5 Module 3: `backend/apps/students/` (Student Management)

**Tables Owned:** `students`, `student_admissions`, `student_addresses`, `student_categories`, `student_bank_accounts`, `student_educational_histories`, `student_scholarships`, `student_enrollments`, `student_data_corrections`  
**Responsibilities:** Student canonical identity, admissions, demographics, historical enrollments, additive government corrections (ADR-007).

| File Path | Description / Responsibility |
|---|---|
| `backend/apps/students/apps.py` | `StudentsConfig` registration |
| `backend/apps/students/models.py` | `Student`, `StudentAdmission`, `StudentAddress`, `StudentCategory`, `StudentBankAccount`, `StudentEducationalHistory`, `StudentScholarship`, `StudentEnrollment`, `StudentDataCorrection` |
| `backend/apps/students/domain/invariants.py` | Student status, gender, enrollment state transition, and correction invariants |
| `backend/apps/students/services/student_service.py` | Core student lifecycle, sensitive AES reveal, semester enrollment, search & filtering |
| `backend/apps/students/services/correction_service.py` | Additive government data correction and authoritative field update (ADR-007) |
| `backend/apps/students/services/student_reporting.py` | `StudentReportingQueryService` — student population, department/program/batch demographics, gender/category breakdowns, active students list (consumed by Reporting module) |
| `backend/apps/students/api/permissions.py` | RBAC permissions (`CanViewStudents`, `CanManageStudents`) |
| `backend/apps/students/api/serializers.py` | Serializers for student list, detail, admissions, addresses, categories, bank accounts, enrollments, corrections |
| `backend/apps/students/api/views.py` | `StudentViewSet` (CRUD, reveal-sensitive, corrections, bank-account, enroll) and `StudentCorrectionViewSet` |
| `backend/apps/students/api/urls.py` | Routes: `/api/v1/students/`, `/students/{id}/reveal-sensitive/`, `/students/{id}/corrections/`, etc. |
| `backend/apps/students/tests/test_student_lifecycle.py` | Student creation, unique constraints, status validation, address and category tests |
| `backend/apps/students/tests/test_admissions_enrollments.py` | Student admissions and authoritative semester enrollment tests |
| `backend/apps/students/tests/test_sensitive_data_boundary.py` | AES encryption/masking, audited reveal boundary, and SensitiveDataAccessLog tests |
| `backend/apps/students/tests/test_additive_corrections.py` | Additive government data correction and history preservation tests |
| `backend/apps/students/tests/test_student_search_filter.py` | Multi-criteria search, department/batch filtering, and detail representation tests |

---

### 3.6 Module 4: `backend/apps/onboarding/` (Student Onboarding & Import)

**Tables Owned:** `import_batches`, `import_staging_rows`  
**Responsibilities:** Government Excel ingestion, deterministic identity matching precedence (ADR-003), staging row lifecycle, conflict review.

| File Path | Description / Responsibility |
|---|---|
| `backend/apps/onboarding/apps.py` | `OnboardingConfig` registration |
| `backend/apps/onboarding/models.py` | `ImportBatch`, `ImportStagingRow` |
| `backend/apps/onboarding/domain/matching_engine.py` | Precedence matcher: 1. Application ID, 2. Enrollment No., 3. University Reg No. |
| `backend/apps/onboarding/domain/excel_parser.py` | Parses XLSX/CSV into raw staging rows with schema validation |
| `backend/apps/onboarding/services/import_service.py` | Orchestrates batch creation, extraction, validation, matching, and commit |
| `backend/apps/onboarding/services/conflict_resolution.py` | Manual conflict review and resolution workflows |
| `backend/apps/onboarding/api/serializers.py` | `ImportBatchSerializer`, `StagingRowSerializer`, `ConflictResolutionSerializer` |
| `backend/apps/onboarding/api/views.py` | `ImportBatchViewSet`, `StagingRowViewSet`, `CommitBatchView` |
| `backend/apps/onboarding/api/urls.py` | Routes: `/api/v1/onboarding/batches/`, `/batches/{id}/commit/`, `/staging-rows/` |
| `backend/apps/onboarding/tests/test_matching.py` | Deterministic matching & conflict generation tests |

---

### 3.7 Module 5: `backend/apps/verification/` (Verification)

**Tables Owned:** `verification_requests`, `verification_requirements`, `verification_decisions`  
**Responsibilities:** Multi-stage verification workflows, review decisions, immutable decision trails (ADR-008, ADR-022).

| File Path | Description / Responsibility |
|---|---|
| `backend/apps/verification/apps.py` | `VerificationConfig` registration |
| `backend/apps/verification/models.py` | `VerificationRequest`, `VerificationRequirement`, `VerificationDecision` |
| `backend/apps/verification/domain/invariants.py` | State machine: `PENDING -> APPROVED/REJECTED/NEEDS_CORRECTION`; `NEEDS_CORRECTION/REJECTED -> PENDING` on re-submission; `APPROVED` terminal (new version required). Decisions append-only in `verification_decisions`. |
| `backend/apps/verification/services/verification_service.py` | Request creation, reviewer assignment, decision recording |
| `backend/apps/verification/services/verification_reporting.py` | `VerificationReportingQueryService` — request throughput, status distribution, average turnaround time, bottlenecks (consumed by Reporting module) |
| `backend/apps/verification/api/serializers.py` | `VerificationRequestSerializer`, `DecisionRecordSerializer` |
| `backend/apps/verification/api/views.py` | `VerificationRequestViewSet`, `RecordDecisionView` |
| `backend/apps/verification/api/urls.py` | Routes: `/api/v1/verification/requests/`, `/requests/{id}/decide/` |
| `backend/apps/verification/tests/test_verification.py` | Verification state transition tests |

---

### 3.8 Module 6: `backend/apps/documents/` (Documents)

**Tables Owned:** `student_documents` *(Note: `FacultyDocument` model exists in DATABASE_ARCHITECTURE.md but is not implemented as a model in the current codebase; only `StudentDocument` is present)*  
**Responsibilities:** Document metadata, secure object-storage references, versioning (ADR-011), superseded status tracking, MIME-type and file-size validation, sensitive-document reveal boundary (ADR-015).

| File Path | Description / Responsibility |
|---|---|
| `backend/apps/documents/apps.py` | `DocumentsConfig` registration |
| `backend/apps/documents/models.py` | `StudentDocument` (with `version`, `version_status`, `superseded_by`, `verification_status`, `rejection_reason`, `reviewed_by`, `checksum`, `storage_key`, `is_sensitive` property) |
| `backend/apps/documents/domain/invariants.py` | `DOCUMENT_TYPES`, `SENSITIVE_DOCUMENT_TYPES`, `VERSION_STATUS_CHOICES`, `VERIFICATION_STATUS_CHOICES`, `ALLOWED_MIME_TYPES` (PDF/JPEG/PNG), `MAX_FILE_SIZE_BYTES` (10 MB), validation functions — **replaces the originally planned `document_rules.py`** |
| `backend/apps/documents/services/document_service.py` | `DocumentService`: `upload_student_document`, `replace_allotment_letter`, `reveal_sensitive_document`, version supersession |
| `backend/apps/documents/services/storage_service.py` | `StorageService`: `store_student_document` (SHA-256 checksum, UUID prefix key), `get_document_stream`, `delete_document` — **new file, not in original plan** |
| `backend/apps/documents/api/serializers.py` | `StudentDocumentSerializer`, `DocumentUploadSerializer`, `AllotmentLetterReplaceSerializer`, `DocumentRevealSerializer` |
| `backend/apps/documents/api/views.py` | `StudentDocumentViewSet` with custom actions: `upload`, `download` (blocks sensitive), `reveal` (ADR-015 reveal with audit), `replace_allotment_letter`, `history` — **no separate `FacultyDocumentViewSet` or `DocumentDownloadView` as originally planned** |
| `backend/apps/documents/api/urls.py` | Router registers `StudentDocumentViewSet` at `/api/v1/documents/` — **routes changed from original plan** (`/documents/students/`, `/documents/faculty/` → single root router) |
| `backend/apps/documents/tests/test_document_upload_and_storage.py` | Upload, storage key generation, checksum, MIME validation, and file-size boundary tests |
| `backend/apps/documents/tests/test_document_versioning_and_replacement.py` | Document versioning, supersession, allotment-letter replacement with reason, and version history tests |
| `backend/apps/documents/tests/test_sensitive_documents_and_reveal.py` | ADR-015 sensitive-document access block, explicit reveal flow, and audit event recording tests |
| `backend/apps/documents/tests/test_sensitive_data_audit.py` | `SensitiveDataAccessLog` audit record creation, actor/reason/timestamp integrity tests |
| `backend/apps/documents/tests/test_documents_api.py` | DRF endpoint integration tests for all custom actions |

---

### 3.9 Module 7: `backend/apps/faculty/` (Faculty & Academic Assignment)

**Tables Owned:** `faculty`, `faculty_assignments`, `faculty_academic_items`  
**Responsibilities:** Faculty lifecycle profiles, departmental organizational metadata, teaching assignments historically preserved by academic year/semester/batch, scoped student visibility, and research portfolio (publications, patents, books, awards, memberships, consultancy, guidance).

| File Path | Description / Responsibility |
|---|---|
| `backend/apps/faculty/apps.py` | `FacultyConfig` registration |
| `backend/apps/faculty/models.py` | `Faculty`, `FacultyAssignment`, `FacultyAcademicItem` |
| `backend/apps/faculty/domain/invariants.py` | Lifecycle validation, teaching assignment constraints, academic portfolio guards |
| `backend/apps/faculty/services/faculty_service.py` | Faculty creation, status transitions, historical assignment retirement, portfolio item management |
| `backend/apps/faculty/services/faculty_scope_service.py` | Server-side scoped student visibility enforcement for Faculty, HOD, and Class Teachers |
| `backend/apps/faculty/api/serializers.py` | Serializers for Faculty, Assignments, and Academic Items |
| `backend/apps/faculty/api/views.py` | `FacultyViewSet` (CRUD, `transition_status`, `assignments`, `academic_items` actions; **auto-provisions login User + dept-scoped HOD/FACULTY role on `perform_create` — username=`faculty_id`, password=`Edvana@2026`**), `FacultyAssignmentViewSet` (`retire` action), `FacultyAcademicItemViewSet`, `FacultyScopedStudentViewSet` |
| `backend/apps/faculty/api/urls.py` | Routes: `/api/v1/faculty/members/`, `/assignments/`, `/academic-items/`, `/scoped-students/` |
| `backend/apps/faculty/tests/test_faculty_lifecycle.py` | Faculty profile creation, status transitions, and lifecycle invariant tests |
| `backend/apps/faculty/tests/test_faculty_department.py` | Faculty department organisational metadata tests |
| `backend/apps/faculty/tests/test_faculty_assignments.py` | Teaching assignment creation, retirement, and historical preservation tests |
| `backend/apps/faculty/tests/test_scoped_student_visibility.py` | Faculty/HOD/Class Teacher scoped student visibility enforcement tests |
| `backend/apps/faculty/tests/test_faculty_academic_items.py` | Faculty portfolio item (publications, patents, awards, etc.) tests |
| `backend/apps/faculty/tests/test_faculty_api.py` | DRF endpoint integration tests |

---

### 3.10 Module 8: `backend/apps/register/` (Register / Administrative Dashboards)

**Tables Owned:** None (Per ARCHITECTURE.md: Pure read-oriented projection capability consuming Student Management, Academic Foundation, and Verification).  
**Responsibilities:** Multi-dimensional student search, department/program/year/batch filtering, category/gender/verification views, student-status KPI dashboard, and bounded CSV/printable register exports.

| File Path | Description / Responsibility |
|---|---|
| `backend/apps/register/apps.py` | `RegisterConfig` registration |
| `backend/apps/register/models.py` | Module specification (read-only projection layer; no `domain/` subfolder — acceptable for no-table modules) |
| `backend/apps/register/services/register_query_service.py` | Filtered, scoped student register queries with sensitive data masking |
| `backend/apps/register/services/dashboard_service.py` | Aggregated student lifecycle status, category, gender, and department distributions |
| `backend/apps/register/services/export_service.py` | Bounded CSV export generation with data protection boundaries |
| `backend/apps/register/api/serializers.py` | Serializers for Register entries, query responses, and dashboard distributions |
| `backend/apps/register/api/views.py` | Endpoints: `StudentRegisterView`, `AdministrativeDashboardView`, `RegisterExportView` |
| `backend/apps/register/api/urls.py` | Routes: `/api/v1/register/students/`, `/dashboard/`, `/export/` |
| `backend/apps/register/tests/test_register_queries.py` | Filtered student register query tests |
| `backend/apps/register/tests/test_academic_filtering.py` | Department/program/year/batch filter tests |
| `backend/apps/register/tests/test_administrative_views.py` | Category/gender/verification filter tests |
| `backend/apps/register/tests/test_dashboard_metrics.py` | Administrative dashboard KPI and distribution tests |
| `backend/apps/register/tests/test_register_export.py` | CSV export generation and data-protection boundary tests |
| `backend/apps/register/tests/test_register_api.py` | DRF endpoint integration tests |

---

### 3.11 Module 11: `backend/apps/results/` (Academic Results & Correction Lifecycle)

**Tables Owned:** `result_import_batches`, `result_import_rows`, `student_results`, `student_result_details`, `result_correction_requests`, `result_correction_audits`  
**Responsibilities:** Academic results ingestion from CSV/Excel, staging rows, deterministic student matching, multi-stage lifecycle state machine (`PENDING` -> `PROCESSING` -> `VALIDATED` -> `APPROVED` -> `PUBLISHED`), immutable published results, student portal marksheet queries, controlled correction requests, Result V2 supersession preserving historical V1 (ADR-016), Result-to-Credit calculation and versioning, configurable eligibility and detention rules, explicit decision states (`ELIGIBLE`, `NOT_ELIGIBLE`, `DETAINED`), and next-year promotion list generation (ADR-028).

| File Path | Description / Responsibility |
|---|---|
| `backend/apps/results/apps.py` | `ResultsConfig` registration |
| `backend/apps/results/models.py` | `ResultImportBatch`, `ResultImportRow`, `StudentResult`, `StudentResultDetail`, `ResultCorrectionRequest`, `ResultCorrectionAudit`, `StudentCredit`, `EligibilityRule`, `EligibilityDecision`, `NextYearEligibilityList` |
| `backend/apps/results/domain/invariants.py` | Mark value validation, UGC 10-point scale grade calculator, state machine transitions, published result immutability enforcement, eligibility rule threshold invariants, decision immutability |
| `backend/apps/results/services/result_service.py` | Batch extraction, staging, deterministic student/scheme matching, draft result generation, accountable approval, publication, student views, correction requests, and V2 supersession |
| `backend/apps/results/services/credit_eligibility_service.py` | Result-to-credit calculation, SGPA/CGPA computation, configurable rule definition and versioning, eligibility and detention evaluation engine, and next-year promotion register generation |
| `backend/apps/results/services/results_reporting.py` | `ResultsReportingQueryService` — pass/fail/ATKT distributions, SGPA/CGPA analytics, eligibility and detention rates, results summary list (consumed by Reporting module) |
| `backend/apps/results/api/serializers.py` | Serializers for batches, rows, student results, details, correction requests, correction audits, `StudentCreditSerializer`, `EligibilityRuleSerializer`, `EligibilityDecisionSerializer`, `NextYearEligibilityListSerializer` |
| `backend/apps/results/api/views.py` | ViewSets for batches, results, student portal, corrections, audits, `StudentCreditViewSet` (calculate), `EligibilityRuleViewSet` (versioning), `EligibilityDecisionViewSet` (evaluate, cohort), `NextYearEligibilityListViewSet` (generate) |
| `backend/apps/results/api/urls.py` | Routes: `/api/v1/results/batches/`, `/records/`, `/student-portal/`, `/corrections/`, `/audits/`, `/credits/`, `/eligibility-rules/`, `/eligibility-decisions/`, `/next-year-eligibility/` |
| `backend/apps/results/tests/test_result_import.py` | Tests for batch foundation, CSV parsing, extraction, validation, and deterministic student matching |
| `backend/apps/results/tests/test_result_lifecycle.py` | Tests for state machine, accountable approval, publication, student view scoping, and published immutability |
| `backend/apps/results/tests/test_result_correction.py` | Tests for correction requests, rejection, approval, Result V2 supersession, V1 preservation, and audit logging |
| `backend/apps/results/tests/test_credits.py` | Tests for result-to-credit calculation from published results and historical credit calculation integrity across supersessions |
| `backend/apps/results/tests/test_eligibility_rules.py` | Tests for configurable eligibility rule definition, threshold invariant validations, and version preservation |
| `backend/apps/results/tests/test_eligibility_decisions.py` | Tests for eligibility and detention decision engine (`ELIGIBLE`, `NOT_ELIGIBLE`, `DETAINED`), rule version recording, and cohort evaluation |
| `backend/apps/results/tests/test_next_year_eligibility.py` | Tests for next-year promotion list generation connecting `StudentEnrollment` and decision history/correction integrity |
| `backend/apps/results/tests/test_results_api.py` | DRF integration tests covering end-to-end API lifecycle, credits, rules, decisions, and promotion lists |
| `frontend/src/modules/results/ResultManagementPage.jsx` | Full institutional UI: Ingestion Batches, Lifecycle actions (Validate, Approve, Publish), Staging rows inspector modal, Official Published Results registry, Marksheet modal, Correction & V2 Supersession workflow, and integrated Credits & Eligibility tab |
| `frontend/src/modules/results/EligibilityDashboard.jsx` | Rich interactive dashboard for Decision Matrix, Configurable Rules manager, Calculated Credits table, and Next-Year Promotion Register generator |

---

### 3.12 Module 9: `backend/apps/finance/` (Fees & Finance)

**Tables Owned:** `fee_heads`, `fee_structures`, `fee_structure_items`, `student_fee_accounts`, `fee_charges`, `payment_ledger_entries`  
**Responsibilities:** Sole source of truth for fee status (ADR-010, ADR-025), annual fee assessment, external university portal QR payment verification, append-only ledger, duplicate payment protection, and controlled corrections via reversals (ADR-011).

| File Path | Description / Responsibility |
|---|---|
| `backend/apps/finance/apps.py` | `FinanceConfig` registration |
| `backend/apps/finance/models.py` | `FeeHead`, `FeeStructure`, `FeeStructureItem`, `StudentFeeAccount`, `FeeCharge`, `PaymentLedgerEntry` |
| `backend/apps/finance/domain/invariants.py` | Invariants: fee structure lock protection, positive amounts, duplicate payment guard on `PAID` charges, overpayment prevention, reversal rules |
| `backend/apps/finance/services/fee_service.py` | Fee head/structure creation, annual charge assessment with cohort locking, append-only payment recording, and controlled reversal |
| `backend/apps/finance/services/finance_reporting.py` | `FinanceReportingQueryService` — fee assessments, collections, outstanding dues, payment status breakdown, fee defaulters list (consumed by Reporting module) |
| `backend/apps/finance/api/serializers.py` | Serializers for FeeHeads, Structures, Student Fee Accounts, Charges, Ledger Entries, and Payment/Reversal requests |
| `backend/apps/finance/api/views.py` | `FeeHeadViewSet`, `FeeStructureViewSet`, `StudentFeeAccountViewSet`, `FeeChargeViewSet`, `PaymentLedgerViewSet`, `AssessAnnualFeesView`, `RecordPaymentView`, `ReversePaymentView` |
| `backend/apps/finance/api/urls.py` | Routes: `/api/v1/finance/heads/`, `/structures/`, `/accounts/`, `/charges/`, `/ledger/`, `/assess-annual-fees/`, `/record-payment/`, `/reverse-payment/` |
| `backend/apps/finance/tests/test_fee_configuration.py` | Tests for fee heads, structures, and historical structure locking |
| `backend/apps/finance/tests/test_charge_generation.py` | Tests for student fee account generation and cohort annual assessment |
| `backend/apps/finance/tests/test_payment_ledger.py` | Tests for append-only payments, duplicate-payment protection, and overpayment guards |
| `backend/apps/finance/tests/test_reversals_and_audit.py` | Tests for append-only reversals, linked audit preservation, and actor accountability |
| `backend/apps/finance/tests/test_finance_api.py` | Tests for DRF API endpoints and validations |
| `frontend/src/modules/finance/FeeManagementPage.jsx` | Full institutional UI: Student Fee Registry, University Portal QR modal, Payment confirmation modal, Annual Assessment tab, and Append-only Ledger |

---

### 3.13 Module 10: `backend/apps/assessments/` (Assessments & Unit Test Marks)

**Tables Owned:** `assessment_types`, `assessments`, `assessment_marks`  
**Responsibilities:** Extensible assessment definitions (Unit Tests, Assignments, Continuous Evaluations), faculty scoped mark uploads with spreadsheet validation, absent handling, atomic transactional persistence, draft-vs-published student visibility boundaries, and historical locking.

| File Path | Description / Responsibility |
|---|---|
| `backend/apps/assessments/apps.py` | `AssessmentsConfig` registration |
| `backend/apps/assessments/models.py` | `AssessmentType`, `Assessment`, `AssessmentMark` |
| `backend/apps/assessments/domain/invariants.py` | Invariants: mark range ($0 \le \text{marks} \le \text{max}$), absent mark guards, assessment lock enforcement, duplicate student row detection |
| `backend/apps/assessments/services/assessment_service.py` | Assessment creation, faculty teaching assignment scoping, batch mark validation and upload, publish (draft -> published), lock, and scoped student mark queries |
| `backend/apps/assessments/api/serializers.py` | Serializers for AssessmentType, Assessment, AssessmentMark, UploadUnitTestMarks, StudentMarkView |
| `backend/apps/assessments/api/views.py` | `AssessmentTypeViewSet`, `AssessmentViewSet` (with `upload_marks`, `publish`, `lock`, `marks` custom actions), `AssessmentMarkViewSet`, `StudentMarksView` |
| `backend/apps/assessments/api/urls.py` | Routes: `/api/v1/assessments/types/`, `/assessments/`, `/assessments/{id}/upload-marks/`, `/assessments/{id}/publish/`, `/assessments/{id}/lock/`, `/student-marks/` |
| `backend/apps/assessments/tests/test_assessment_definition.py` | Tests for assessment types, schema boundaries, and academic/faculty associations |
| `backend/apps/assessments/tests/test_marks_upload_and_validation.py` | Tests for faculty upload scoping, out-of-range marks, absent flags, duplicate rows, and atomic rollback |
| `backend/apps/assessments/tests/test_persistence_and_student_view.py` | Tests for mark persistence, draft-hidden vs published student view, and locked immutability |
| `backend/apps/assessments/tests/test_assessments_api.py` | Tests for DRF API endpoints and actions |
| `frontend/src/modules/assessments/AssessmentManagementPage.jsx` | Full institutional UI: Faculty Assessment Workspace, Status filters, Create Assessment modal, Unit Test spreadsheet upload modal with CSV preview/validation, View Marks modal with publication/lock controls, and Student Portal self-view |

---

### 3.14 Module 12: `backend/apps/services/` (Student Services)

**Tables Owned:** `service_request_types`, `service_requests`, `service_request_audits`  
**Responsibilities:** Extensible student service request workflows (bonafide certificates, transcript requests, fee concession, corrections, duplicate ID), mandatory rejection reason enforcement, canonical document attachments referencing `apps.documents.StudentDocument`, and immutable accountable-actor audit trail (`ServiceRequestAudit`).

| File Path | Description / Responsibility |
|---|---|
| `backend/apps/services/apps.py` | `ServicesConfig` registration (`apps.services`) |
| `backend/apps/services/models.py` | `ServiceRequestType`, `ServiceRequest`, `ServiceRequestAudit` models |
| `backend/apps/services/domain/invariants.py` | Workflow transitions (`SUBMITTED` -> `IN_PROGRESS` -> `APPROVED`/`REJECTED` -> `COMPLETED`, `CANCELLED`), mandatory rejection reason invariant, and canonical document requirement validation |
| `backend/apps/services/services/request_service.py` | `ServiceRequestService` (submit_request, assign_request, process_request, approve_request, reject_request, complete_request, cancel_request, attach_document) |
| `backend/apps/services/api/serializers.py` | Serializers for `ServiceRequestType`, `ServiceRequest`, `ServiceRequestAudit`, and `SubmitServiceRequest` |
| `backend/apps/services/api/views.py` | `ServiceRequestTypeViewSet`, `ServiceRequestViewSet` (with `submit`, `process`, `approve`, `reject`, `complete`, `cancel`, `attach_document`, `my_requests` actions), and `ServiceRequestAuditViewSet` |
| `backend/apps/services/api/urls.py` | Routes: `/api/v1/services/types/`, `/services/requests/`, `/services/audits/` |
| `backend/apps/services/tests/test_service_framework.py` | Pure domain tests for `ServiceRequestType`, code uniqueness, and invariant rules |
| `backend/apps/services/tests/test_student_submission.py` | Tests for student request submission, default status `SUBMITTED`, ticket number generation, and student scoping |
| `backend/apps/services/tests/test_administrative_processing.py` | Tests for administrative assignment and transitioning from `SUBMITTED` to `IN_PROGRESS` |
| `backend/apps/services/tests/test_approval_rejection_workflow.py` | Tests for valid approval, mandatory rejection reasons, and invalid state transitions |
| `backend/apps/services/tests/test_document_attachment.py` | Tests for canonical document requirement validation and document attachment |
| `backend/apps/services/tests/test_accountable_actor_audit.py` | Tests for immutable audit trail recording state changes and accountable actors |
| `backend/apps/services/tests/test_services_api.py` | Integration tests for DRF endpoints, filters, custom actions, and student isolation |
| `frontend/src/modules/services/StudentServicesPage.jsx` | Full institutional UI: Student requests queue, status badges, submit modal, approval/process buttons, reject modal with mandatory reason, service catalog, and immutable audit timeline |

---

### 3.15 Module 13: `backend/apps/audit/` (Audit & Observability)

**Tables Owned:** `audit_log`, `sensitive_data_access_log`  
**Responsibilities:** Immutable system-wide business audit trails, sensitive data reveal logging (ADR-015), accountability records.

| File Path | Description / Responsibility |
|---|---|
| `backend/apps/audit/apps.py` | `AuditConfig` registration |
| `backend/apps/audit/models.py` | `AuditLog`, `SensitiveDataAccessLog` |
| `backend/apps/audit/services/audit_service.py` | Write audit entry, write sensitive reveal entry (called by other services) |
| `backend/apps/audit/services/audit_reporting.py` | `AuditReportingQueryService` — action distribution, top administrative actors, sensitive reveal logs (consumed by Reporting module) |
| `backend/apps/audit/api/serializers.py` | Read-only audit serializers |
| `backend/apps/audit/api/views.py` | Read-only views for System Admin and Compliance officers |
| `backend/apps/audit/api/urls.py` | Routes: `/api/v1/audit/logs/`, `/audit/sensitive-access/` |
| `backend/apps/audit/tests/test_audit.py` | Audit log creation and immutability tests |

---

### 3.16 Module 14: `backend/apps/reporting/` (Reporting & Analytics)

**Tables Owned:** None (Pure downstream consumer; queries owning modules via read-only interfaces).  
**Responsibilities:** Multi-dimensional analytics, institutional overview metrics, population and demographic breakdowns, verification throughput tracking, fee collection vs defaulter analysis, academic pass/retention analytics, administrative audit activity tracking, and bounded tabular data exports (CSV) with row guardrails (ADR-017, ADR-030).

| File Path | Description / Responsibility |
|---|---|
| `backend/apps/reporting/apps.py` | `ReportingConfig` registration |
| `backend/apps/reporting/domain/contracts.py` | Query contracts: `ReportFilterSpec`, `PaginationSpec`, `ReportQueryResult`, `ReportingValidationError`, and export limit constraints (`MAX_EXPORT_LIMIT = 5000`) |
| `backend/apps/students/services/student_reporting.py` | `StudentReportingQueryService` (student population, department/program/batch demographics, gender/category breakdowns, active students list) |
| `backend/apps/finance/services/finance_reporting.py` | `FinanceReportingQueryService` (fee assessments, collections, outstanding dues, payment status breakdown, fee defaulters list) |
| `backend/apps/results/services/results_reporting.py` | `ResultsReportingQueryService` (pass/fail/ATKT distributions, SGPA/CGPA analytics, eligibility and detention rates, results summary list) |
| `backend/apps/verification/services/verification_reporting.py` | `VerificationReportingQueryService` (request throughput, status distribution, average turnaround time, bottlenecks) |
| `backend/apps/audit/services/audit_reporting.py` | `AuditReportingQueryService` (action distribution, top administrative actors, sensitive reveal logs) |
| `backend/apps/reporting/services/analytics_service.py` | `ReportingAnalyticsService` cross-module aggregation service (KPI overview, demographics, verification, finance, academic, audit activity) |
| `backend/apps/reporting/services/export_service.py` | `ReportingExportService` bounded tabular CSV export generator enforcing the 5,000-row guardrail |
| `backend/apps/reporting/api/views.py` | DRF API views for all analytics dashboards (`ExecutiveOverviewView`, `DemographicsAnalyticsView`, `VerificationAnalyticsView`, `FeeStatusAnalyticsView`, `AcademicAnalyticsView`, `AuditAnalyticsView`) and bounded tabular export (`ReportExportView`) |
| `backend/apps/reporting/api/urls.py` | Routes: `/api/v1/reporting/overview/`, `/demographics/`, `/verification/`, `/finance/`, `/academics/`, `/audit/`, `/export/` |
| `backend/apps/reporting/tests/test_query_contract_foundation.py` | Tests for contract specifications, pagination bounds, validation errors, and export limits |
| `backend/apps/reporting/tests/test_student_reporting_interface.py` | Tests for Student Management reporting queries, filters, demographics, and active student list |
| `backend/apps/reporting/tests/test_finance_reporting_interface.py` | Tests for Finance reporting queries, collection summaries, dues, and defaulter detection |
| `backend/apps/reporting/tests/test_results_reporting_interface.py` | Tests for Results \& Eligibility reporting queries, grade distribution, and eligibility rates |
| `backend/apps/reporting/tests/test_analytics_services.py` | Tests for cross-module executive overview, population aggregation, and KPI computations |
| `backend/apps/reporting/tests/test_filtering_sorting_export.py` | Tests for bounded CSV export streaming, maximum row guardrails, and filter specifications |
| `backend/apps/reporting/tests/test_query_performance_and_optimization.py` | Tests validating bounded SQL query count execution and N+1 query elimination |
| `backend/apps/reporting/tests/test_reporting_api.py` | Integration tests for DRF API endpoints covering all analytics and export routes |
| `frontend/src/modules/reporting/AnalyticsDashboardPage.jsx` | Full institutional UI: Executive KPI cards, Demographics distribution charts, Fee collection and defaulter metrics, Academic grading & eligibility rates, Verification operational metrics, and Bounded CSV Export Center |

> **Note:** `reporting/services/__init__.py` has been added to ensure reliable Python package resolution.
> **Note:** Reporting has no `domain/entities.py` or `state_machines.py` — it only has `domain/contracts.py`. This is by design (read-only module with no owned tables) but is an exception to the standard module structure.

---

## 4. Frontend File Map (`frontend/`)

```
frontend/ (synced 2026-09-08 to actual tree — no src/api/, src/auth/, src/components/, src/routes/)
├── package.json / vite.config.js / index.html
├── src/
│   ├── main.jsx / App.jsx          # Entry + RouterProvider (routing lives in App.jsx, not src/routes/)
│   ├── services/api.js             # Axios JWT interceptor + refresh (replaces documented api/client.js)
│   ├── context/AuthContext.jsx     # Auth provider (replaces documented auth/AuthContext.jsx)
│   ├── layouts/
│   │   ├── DashboardLayout.jsx / Navbar.jsx / Sidebar.jsx
│   ├── modules/ (12 domain folders, flat pages — no shared components/ library)
│   │   ├── auth/LoginPage.jsx
│   │   ├── academic/DepartmentList.jsx, AcademicCalendarPage.jsx, CurriculumPage.jsx
│   │   ├── students/StudentDirectory.jsx, StudentProfile.jsx, StudentDashboard.jsx, StudentPaymentHistory.jsx, CorrectionModal.jsx, profile/
│   │   ├── onboarding/ImportBatchList.jsx, StagingRowViewer.jsx (replaces documented ConflictReview.jsx)
│   │   ├── verification/VerificationQueue.jsx
│   │   ├── documents/StudentDocumentList.jsx
│   │   ├── faculty/FacultyList.jsx, FacultyDetail.jsx, DivisionBatchManagement.jsx (division UI — ADR-020 amended)
│   │   ├── register/StudentRegister.jsx
│   │   ├── finance/FeeManagementPage.jsx, FeeHeadConfigPage.jsx, CandidateFeeDesk.jsx (QR desk — ADR-025)
│   │   ├── assessments/AssessmentManagementPage.jsx
│   │   ├── results/ResultManagementPage.jsx, EligibilityDashboard.jsx
│   │   ├── services/StudentServicesPage.jsx
│   │   └── reporting/AnalyticsDashboardPage.jsx
│   └── styles/tokens.css, global.css, edvana-style-system.css
```

---

## 5. Model-to-Table Cross-Reference

| Django Model Class | Database Table Name | Owning Module |
|---|---|---|
| `User` | `users` | `identity` |
| `Role` | `roles` | `identity` |
| `Permission` | `permissions` | `identity` |
| `UserRole` | `user_roles` | `identity` |
| `RolePermission` | `role_permissions` | `identity` |
| `Department` | `departments` | `academic` |
| `Program` | `programs` | `academic` |
| `AcademicYear` | `academic_years` | `academic` |
| `Semester` | `semesters` | `academic` |
| `Batch` | `batches` | `academic` |
| `Scheme` | `schemes` | `academic` |
| `Subject` | `subjects` | `academic` |
| `SchemeSubject` | `scheme_subjects` | `academic` |
| `DepartmentIntake` | `department_intakes` | `academic` |
| `Student` | `students` | `students` |
| `StudentAdmission` | `student_admissions` | `students` |
| `StudentAddress` | `student_addresses` | `students` |
| `StudentCategory` | `student_categories` | `students` |
| `StudentBankAccount` | `student_bank_accounts` | `students` |
| `StudentEducationalHistory` | `student_educational_histories` | `students` |
| `StudentScholarship` | `student_scholarships` | `students` |
| `StudentEnrollment` | `student_enrollments` | `students` |
| `StudentDataCorrection` | `student_data_corrections` | `students` |
| `ImportBatch` | `import_batches` | `onboarding` |
| `ImportStagingRow` | `import_staging_rows` | `onboarding` |
| `VerificationRequest` | `verification_requests` | `verification` |
| `VerificationRequirement` | `verification_requirements` | `verification` |
| `VerificationDecision` | `verification_decisions` | `verification` |
| `StudentDocument` | `student_documents` | `documents` |
| `FacultyDocument` | `faculty_documents` | `documents` |
| `Faculty` | `faculty` | `faculty` |
| `FacultyAssignment` | `faculty_assignments` | `faculty` |
| `FacultyAcademicItem` | `faculty_academic_items` | `faculty` |
| `AssessmentType` | `assessment_types` | `assessments` (separate app) |
| `Assessment` | `assessments` | `assessments` (separate app) |
| `AssessmentMark` | `assessment_marks` | `assessments` (separate app) |
| `ResultImportBatch` | `result_import_batches` | `results` |
| `ResultImportRow` | `result_import_rows` | `results` |
| `StudentResult` | `student_results` | `results` |
| `StudentResultDetail` | `student_result_details` | `results` |
| `ResultCorrectionRequest` | `result_correction_requests` | `results` |
| `ResultCorrectionAudit` | `result_correction_audits` | `results` |
| `StudentCredit` | `student_credits` | `results` |
| `EligibilityRule` | `eligibility_rules` | `results` |
| `EligibilityDecision` | `eligibility_decisions` | `results` |
| `NextYearEligibilityList` | `next_year_eligibility_lists` | `results` |
| `FeeHead` | `fee_heads` | `finance` |
| `FeeStructure` | `fee_structures` | `finance` |
| `FeeStructureItem` | `fee_structure_items` | `finance` |
| `StudentFeeAccount` | `student_fee_accounts` | `finance` |
| `FeeCharge` | `fee_charges` | `finance` |
| `PaymentLedgerEntry` | `payment_ledger_entries` | `finance` |
| `ServiceRequestType` | `service_request_types` | `services` |
| `ServiceRequest` | `service_requests` | `services` |
| `ServiceRequestAudit` | `service_request_audits` | `services` |
| `AuditLog` | `audit_log` | `audit` |
| `SensitiveDataAccessLog` | `sensitive_data_access_log` | `audit` |

---

## 6. Architectural Invariants & Import Rules

1. **Acyclic Dependency Graph**: Imports between apps must follow the flow defined in `AGENT.md` Section 7.
2. **No Direct Cross-Module ORM Writes**:
   - Module A must NEVER call `ModelB.objects.create(...)` or `model_b_instance.save()`.
   - All state mutations must call the owning module's application service (e.g. `students.services.correction_service.apply_correction(...)`).
3. **Additive History Preservation**:
   - Never use `.delete()` on government-sourced data, ledger entries, published results, or audit logs.
4. **Database Configuration (SQLite dev / PostgreSQL prod)**:
   - All models use UUID PKs (`UUIDField(primary_key=True, default=uuid.uuid4, editable=False)`).
   - `backend/config/settings.py`: SQLite default (`backend/db.sqlite3`); set `DB_ENGINE=postgresql` in `backend/.env` (`DB_NAME/DB_USER/DB_PASSWORD/DB_HOST/DB_PORT`) for PostgreSQL.
   - `docker-compose.yml` runs `postgres:16-alpine` + Gunicorn backend + Nginx; prod uses `config.settings_production`.

---

## 7. Production Hardening, Infrastructure & Operational Tooling (Section 15)

### 7.1 Cross-Cutting Security & Throttling
- `backend/common/throttling.py`: Scoped rate throttling classes (`AuthRateThrottle`: 5/min, `SensitiveRevealRateThrottle`: 10/hr).
- `backend/common/exception_handler.py`: Production error masking for 500 exceptions (suppressing stack traces) and 429 JSON handlers.
- `backend/apps/identity/tests/test_auth_security_audit.py`: Full authentication and authorization audit suite (Task 15.1.1).
- `backend/apps/documents/tests/test_sensitive_data_audit.py`: Sensitive data masking, encryption, and audit suite (Task 15.1.2).
- `backend/common/tests/test_api_security_audit.py`: Rate limiting, XSS, nosniff, and frame deny security header audit (Task 15.1.3).

### 7.2 Database & Historical Integrity
- `backend/common/tests/test_database_constraints_audit.py`: ForeignKey, nullability, cascading deletion protection audit (Task 15.2.1).
- `backend/common/tests/test_migration_safety_audit.py`: Non-destructive schema migration and leaf node consistency audit (Task 15.2.2).
- `backend/common/tests/test_idempotency_audit.py`: Idempotent student onboarding and duplicate-payment prevention audit (Task 15.2.3).
- `backend/common/tests/test_historical_integrity_audit.py`: Immutability and audit preservation audit across domains (Task 15.2.4).

### 7.3 Performance, Reliability & Concurrency
- `backend/common/tests/test_query_performance_audit.py`: Index and bounded query profile validation (Task 15.3.1).
- `backend/common/tests/test_concurrency_audit.py`: Row-level locking and transaction atomicity audit (Task 15.3.2).
- `backend/common/tests/test_failure_recovery_audit.py`: Financial reversals and transaction rollback validation (Task 15.3.3).
- `backend/common/tests/test_load_benchmark.py`: Automated SLA validation for 100+ student cohorts (Task 15.3.4).
- `backend/scripts/load_test_benchmark.py`: High-volume cohort benchmark runner with latency timing.

### 7.4 Infrastructure, Orchestration & Disaster Recovery
- `backend/config/settings_production.py`: Production settings with strict SSL, DB pooling, and structured JSON logging.
- `backend/.env.production.example`: Production environment variables template.
- `backend/Dockerfile`: Multi-worker Gunicorn production container with unprivileged user execution.
- `frontend/Dockerfile`: Multi-stage Node 20 / Vite build container with Nginx static distribution.
- `docker-compose.yml`: Production orchestration for PostgreSQL 16 Alpine, Backend Gunicorn, and Nginx proxy.
- `nginx/nginx.conf`: Production Nginx reverse proxy with gzip, caching, security headers, and SPA routing.
- `backend/scripts/backup_db.py`: Automated database backup script with SHA-256 integrity checksumming.
- `backend/scripts/restore_db.py`: Cryptographically verified database restore script.
- `backend/scripts/tests/test_backup_restore.py`: Automated tests for backup creation, tampering detection, and restore.
- `backend/scripts/verify_document_storage.py`: Document storage physical presence and SHA-256 audit script.
- `backend/scripts/tests/test_document_storage.py`: Automated tests for object storage audit and corruption detection.
- `backend/scripts/check_production_readiness.py`: Pre-flight deployment verification script.
