<!-- Page 1 -->

Architecture Decision Records
This document records architectural decisions that are considered settled and should not be casually
reversed by future implementation sessions, humans, or AI coding agents.
ADR-001: Modular Monolith Over Microservices
Date: 2026-09-06
Status: Accepted
Decision: The system will be implemented as a modular monolith rather than as a microservices
architecture.
Why: The architectural objective is a simple system that is easy for humans to understand while maintaining
strong domain boundaries and preventing an AI coding agent from casually crossing them. The
architecture explicitly states that no module needs to be split and that no additional bounded context is
required.
Alternatives considered: Microservices were not explicitly discussed in the supplied finalization material.
Affects: Entire system architecture; all bounded contexts and deployment structure.
ADR-002: Bounded Context List and Boundaries
Date: 2026-09-06
Status: Accepted
Decision: The system is divided into the following bounded contexts: Identity & Access, Student
Management, Verification, Faculty, Onboarding, Documents, Academic Foundation, Results & Eligibility,
Finance, Reporting, and Audit. These boundaries remain unchanged by the finalization decisions.
Why: The final architecture states that no bounded-context dependency changes are required, no module
needs to be split or merged, no circular dependency is introduced, Reporting remains downstream/read-
oriented, and Audit remains a supporting cross-cutting capability.
Alternatives considered: Not explicitly discussed.
Affects: All modules and their dependency relationships.
ADR-003: Deep Modules Over Shallow Modules
Date: 2026-09-06
Status: Accepted
Decision: Bounded contexts should remain deep modules with meaningful internal ownership rather than
becoming shallow wrappers around shared services or data. Domain-specific behavior remains inside the
owning module.
Why: The finalization explicitly assigns domain-specific correction behavior to the context that owns the
affected data and rejects a generic service that understands every domain. This preserves clear
responsibilities and prevents architectural complexity from being introduced merely to share behavior.
1

---

<!-- Page 2 -->

Alternatives considered: A generic cross-domain CorrectionService was considered and rejected because
each bounded context must own its domain-specific correction behavior.
Affects: All bounded contexts, especially Student Management, Finance, Results, Documents, Verification,
and cross-cutting capabilities.
ADR-004: Student Management vs Onboarding Separation
Date: 2026-09-06
Status: Accepted
Decision: Student Onboarding and Student Management remain separate bounded contexts, with
onboarding functioning as the controlled pipeline through which submitted information can become an
official student record.
Why: The architecture distinguishes submission, acceptance, and official-record status. Student
Management owns actual student information, while workflows that require confirmation pass through the
appropriate workflow before becoming accepted into the official record.
Alternatives considered: Not explicitly discussed.
Affects: Onboarding, Student Management, Verification, Identity, Documents, and student-data workflows.
ADR-005: Student Enrollment as the Source of Truth
Date: 2026-09-06
Status: Accepted
Decision: Student enrollment records are the authoritative source for determining a student's academic
enrollment state; students.current_semester  must not become an independent competing source of
truth.
Why: The architecture requires authoritative student information and preserves source-of-truth boundaries
between domains. Enrollment state must therefore be represented through the authoritative enrollment
model rather than relying on a mutable convenience field.
Alternatives considered: A direct students.current_semester  value as the authoritative state was
rejected in the finalized architecture.
Affects: Student Management, Academic Foundation, Results & Eligibility, Reporting, and any workflow
dependent on enrollment state.
ADR-006: System Admin Cannot Directly Edit Live Student Records
Date: 2026-09-06
Status: Accepted
Decision: The System Admin may manage users, roles, permissions, master data, system settings, system-
wide information, and audit activity, but must not directly edit live student records. Student-data corrections
must pass through Student Management and Verification workflows and remain auditable.
Why: This preserves the separation between system administration and business-data administration. Even
corrections initiated by an administrator must use the controlled business workflow rather than bypassing
it. Alternatives considered: Direct editing of live student records by System Admin was rejected by the
2

---

<!-- Page 3 -->

finalized architecture.
Affects: System Admin, Identity & Access, Student Management, Verification, and Audit.
ADR-007: Government Data Is Immutable
Date: 2026-09-06
Status: Accepted
Decision: Government-provided data is treated as an immutable source record. Corrections are additive: the
original value remains preserved while a new authoritative value, approver, reason, timestamp, and audit
record are recorded.
Why: The architecture explicitly distinguishes source history from the current authoritative business value
and requires that the original government value never be overwritten. This preserves historical evidence
while allowing controlled correction. Alternatives considered: Destructive overwrite of the original
government value was rejected.
Affects: Student Management, Onboarding, Verification, Documents, Identity, and Audit.
ADR-008: Deterministic Student Identity Matching
Date: 2026-09-06
Status: Accepted
Decision: Government imports use deterministic identity-matching precedence: Application ID →
Enrollment Number → Board/University Enrollment Number. No match creates a new student; a single valid
match associates the import with the matched student; conflicting matches require manual resolution.
Why: Deterministic precedence prevents ambiguous imports from silently producing incorrect associations.
Conflicting matches must enter CONFLICT → MANUAL REVIEW → Explicit Resolution rather than
automatically merging records. Alternatives considered: Automatic merging of conflicting records was
explicitly rejected.
Affects: Student Management, Onboarding, Identity & Access, Verification, and import processing.
ADR-009: Enrollment Number as Initial Student Credential
Date: 2026-09-06
Status: Accepted
Decision: The initial student account policy uses the Enrollment Number as both username and initial
password, with a mandatory password change at first login. The policy remains changeable and is owned by
Identity.
Why: This provides a simple initial provisioning mechanism while keeping authentication policy separate
from Student Management. Future activation mechanisms such as OTP-based activation or invitation-based
onboarding can therefore be introduced without redesigning Student Management. Alternatives
considered: OTP-based activation and invitation-based onboarding are identified as possible future policies
rather than the initial policy.
Affects: Identity & Access, Student Management, and Onboarding.
3

---

<!-- Page 4 -->

ADR-010: Internal Finance Ledger Is the Fee Authority
Date: 2026-09-06
Status: Accepted
Decision: The Finance module's charges and payment records are the sole source of truth for fee status. The
system does not implement reconciliation against an external payment system.
Why: There is no external payment system that this application must reconcile against; therefore there is no
external system to trust as an independent authority for fee status. Payments are append-only financial
events, and mistaken payments are corrected through reversal/correction entries rather than editing or
deletion. Alternatives considered: External payment reconciliation and dispute architecture were explicitly
excluded because there is no external payment system that the application must reconcile against.
Affects: Finance, Student Management, Reporting, and Audit.
ADR-011: Corrections and Reversals Are Cross-Cutting, Not a
Module
Date: 2026-09-06
Status: Accepted
Decision: Corrections, replacements, supersessions, and reversals follow a shared architectural pattern but
remain owned by the bounded context whose data is being corrected. No separate Correction Module will
be created.
Why: The system-wide rule is that corrections are additive and never destructive. Domain-specific semantics
differ: Finance performs financial reversals, Results use result supersession, Student Management performs
data correction, and Documents perform document replacement. Alternatives considered: A separate
Correction Module was explicitly rejected because correction semantics belong to the domain whose data is
being corrected. Affects: All bounded contexts that support correction, reversal, replacement, or
supersession.
ADR-012: Trust Model — Accountability, Auditability, and
Reversibility
Date: 2026-09-06
Status: Accepted
Decision: The system's trust model is based on accountability, auditability, and reversibility rather than
attempting to guarantee that every human action is truthful.
Why: Several workflows have no external system of record that independently validates whether a human
action was correct. The architecture therefore requires authenticated actors, authorized operations,
guarded state transitions, persistent history, audit visibility, and correction/reversal mechanisms.
Alternatives considered: A model based on preventing or technically guaranteeing the correctness of every
human decision was not presented as achievable; no alternative was explicitly discussed.
Affects: Verification, Documents, Finance, Results, Student Management, Identity, Services, and Audit.
4

---

<!-- Page 5 -->

ADR-013: Accountable Actor Across Sensitive Operations
Date: 2026-09-06
Status: Accepted
Decision: Sensitive business actions must identify the responsible actor, with the reusable conceptual record
consisting of Actor + Action + Target + Timestamp + Reason where applicable. This pattern applies across
Student Management, Verification, Documents, Finance, Results, Identity, and Services.
Why: Accountability is treated as a reusable architectural pattern rather than something reinvented
independently in every module. The architecture explicitly identifies controlled corrections, approvals,
payments, reversals, publishing, permission changes, and service decisions as accountable actions.
Alternatives considered: Independent accountability implementations per module were rejected in favor of
a reusable architectural pattern.
Affects: Student Management, Verification, Documents, Finance, Results, Identity & Access, Services, and
Audit.
ADR-014: Verification Owns the Decision, Not the Student Data
Date: 2026-09-06
Status: Accepted
Decision: Student Management owns actual student information, while Verification owns the decision about
whether submitted or corrected information is approved for official use. Verification must not become a
second student database.
Why: The architecture deliberately separates data ownership from approval authority. Submission,
acceptance, and official-record status are distinct concepts, and information requiring administrative
confirmation must pass through Verification before becoming accepted as official. Alternatives considered:
Making Verification a second student-data store was explicitly rejected.
Affects: Student Management, Verification, Onboarding, Documents, Identity, and student-submitted
information workflows.
ADR-015: Sensitive Data Is Masked by Default
Date: 2026-09-06
Status: Accepted
Decision: Sensitive information such as Aadhaar and bank details is masked by default. Full values can only
be exposed through an explicit authorized reveal action that performs a permission check and records an
audit event.
Why: Normal student-detail APIs must not automatically expose full sensitive values. The reveal flow is
explicitly controlled and auditable, recording the actor, sensitive resource, action, timestamp, and context/
reason where applicable. Alternatives considered: Automatically exposing full sensitive values through
normal student-detail APIs was explicitly rejected.
Affects: Documents, Student Management, Verification, Identity & Access, Sensitive Data boundaries, and
Audit.
5

---

<!-- Page 6 -->

ADR-016: Published Results Are Immutable
Date: 2026-09-06
Status: Accepted
Decision: Once published, a result is immutable historical evidence. Corrections create a new result version
that supersedes the previous version; the original remains accessible as history.
Why: Published results must never be silently updated in place. A correction requires an authorized actor,
mandatory reason, approval, timestamp, and audit record. Alternatives considered: Updating published
results in place was explicitly rejected.
Affects: Results & Eligibility, Verification, Reporting, Student Management, and Audit.
ADR-017: Reporting Uses Module-Owned Query Interfaces
Date: 2026-09-06
Status: Accepted
Decision: Reporting must access authoritative data through module-owned query interfaces rather than
directly accessing another module's tables. If future performance evidence requires it, purpose-built
derived read projections may be introduced without becoming sources of truth.
Why: Direct table access would make Reporting dependent on persistence implementation details and
weaken source-of-truth boundaries. Module-owned query interfaces are therefore the initial default, with
performance-driven projections permitted only when justified by actual query/load evidence. Alternatives
considered: Direct access to other modules' tables was rejected as the normal architectural interface.
Materialized reporting projections remain a future performance exception.
Affects: Reporting and every module exposing authoritative data to Reporting.
ADR-018: No Premature Infrastructure Complexity
Date: 2026-09-06
Status: Accepted
Decision: Infrastructure such as Kafka, CQRS, event sourcing, sharding, or equivalent complexity must not
be introduced prematurely. Additional infrastructure is justified only by concrete evidence and
demonstrated system needs.
Why: The finalized architecture deliberately preserves a simple modular monolith and states that behavioral
and contractual improvements do not require additional domains or module splits. The objective is to make
the system easy for humans to understand while maintaining disciplined boundaries. Alternatives
considered: Premature infrastructure expansion was not explicitly discussed item-by-item in the supplied
material.
Affects: Overall architecture, deployment, data access, Reporting, messaging, and platform infrastructure.
6

---

<!-- Page 7 -->

ADR-019: Single-College Deployment
Date: 2026-09-06
Status: Accepted
Decision: The system is designed for deployment within a single college rather than as a multi-tenant SaaS
platform.
Why: The finalized architecture retains a simple bounded-context model and does not introduce tenant
isolation as an architectural concern. No new bounded context or dependency change is required for the
finalized design.
Alternatives considered: Multi-tenant SaaS was not explicitly discussed in the supplied finalization material.
Affects: Overall deployment model, Student Management, Identity & Access, Finance, Reporting, and
configuration.
ADR-020: Batch Is Used; Division Is Implemented as Optional Enrollment Attribute
Date: 2026-09-06 (Amended 2026-09-08 to match prototype implementation)
Status: Accepted (Amended — supersedes Division-deferred scope)
Decision: Batch remains the primary academic grouping model. Division is implemented as an optional,
non-authoritative attribute on `student_enrollments.division` (default `'A'`, e.g. A/B/C) for class-section
grouping within a batch. It does not create a new bounded context, table, or source of truth; enrollment
(batch/year/semester/scheme) remains authoritative per ADR-005.
Why: Prototype iteration added `division` to support real class-section operations without breaking batch
history. Kept as a plain CharField (not FK, not part of enrollment uniqueness) to avoid complexity.
Alternatives considered: Keeping Division fully deferred (rejected — prototype needs section grouping);
separate Division table (rejected — premature normalization).
Affects: Student Management (`student_enrollments.division`), Academic Foundation, Faculty assignments,
Results & Eligibility, Reporting filters.
ADR-021: Minimal Scholarship Scope for V1
Date: 2026-09-06
Status: Accepted
Decision: Scholarship functionality in v1 is intentionally limited to scholarship type, status, supporting
documents, and approval. Broader scholarship-management capabilities are outside the initial scope.
Why: The architecture keeps the initial domain scope deliberately constrained rather than introducing
unnecessary complexity. The finalized design emphasizes simple bounded contexts and disciplined module
ownership.
Alternatives considered: A broader scholarship-management workflow was not explicitly detailed in the
supplied finalization material.
Affects: Student Management, Documents, Verification, Finance, and Reporting.
7

---

<!-- Page 8 -->

ADR-022: Verification Policy Matrix Remains Open
Date: 2026-09-06
Status: Open
Decision: The field-by-field Verification policy has not yet been finalized. The system must not invent
institutional policy determining which individual student fields or documents require verification before
becoming official.
Why: The architecture explicitly states that the exact verification matrix remains a business-policy decision.
Examples include Photo, Signature, Aadhaar, Bank Details, Address, HSC Information, and Government
Corrections, but their final approval rules remain TBD. Alternatives considered: Inventing verification rules
in the software architecture was explicitly rejected because these rules are institutional policy.
Affects: Verification, Student Management, Onboarding, Documents, Identity, and all workflows whose
official-record status depends on verification.
ADR-023: Sensitive-Data Retention Period Remains Open
Date: 2026-09-06
Status: Open
Decision: The retention duration for Aadhaar, bank information, and sensitive documents remains an
institutional/compliance decision and is not defined as an engineering default.
Why: The architecture explicitly leaves sensitive-data retention duration open because the appropriate
period depends on institutional and compliance requirements. The system should therefore not hard-code
an invented retention period as an architectural decision. Alternatives considered: Selecting an engineering-
defined retention period was rejected/deferred because the retention decision belongs to institutional/
compliance policy.
Affects: Sensitive Data, Documents, Student Management, Verification, Storage, Security, and Audit.
ADR-024: Register / Administrative Dashboards as Read-Oriented Projection
Date: 2026-09-07
Status: Accepted
Decision: The Register and Administrative Dashboard capability operates strictly as a read-oriented projection
and reporting layer. It does not own or duplicate database tables for student records, enrollments, academic entities,
or verification decisions. It queries and projects authoritative data through module-owned read interfaces,
enforces server-side scoped authorization, strictly masks sensitive identity attributes (e.g. Aadhaar), and
applies resource-safe safety limits on tabular exports.
Why: Per ARCHITECTURE.md Section 12 and PRD-8, read and reporting capabilities must preserve single sources of
truth and avoid creating competing or stale copies of core operational state.
Affects: Register, Student Management, Academic Foundation, Verification, Faculty, Security, and Reporting.

ADR-025: College Fee Accounting, University Portal QR Payments & Append-Only Record-Keeping
Date: 2026-09-07
Status: Accepted
Decision: 
1. Annual Assessment: The Fee Accountant once a year configures annual fee structures and assesses fees across enrolled student cohorts for an academic year.
2. Historical Fee Structure Lock: Once charges have been generated against a fee structure, the fee structure is permanently locked (`is_locked=True`) to prevent retrospective tampering.
3. External University Payment QR: Students execute their fee payments externally via a QR code / university payment portal to which the internal college system has no direct gateway API access.
4. Internal Record-Keeping & Duplicate-Payment Protection: The college Fee Accountant verifies the student's external payment receipt and UTR reference, then records the transaction in an append-only payment ledger (`PaymentLedgerEntry`). The student charge transitions from `UNPAID` to `PAID` (or `PARTIALLY_PAID`). Once marked `PAID`, additional payments against that charge are strictly rejected to eliminate accidental double recording.
5. Reversal Audit Integrity: Erroneous payment records are never edited or deleted; they are corrected strictly via linked append-only reversal entries requiring a mandatory accountable justification.
Why: Matches institutional governance (ADR-010, ADR-011) and college operating realities where university gateways are external and unintegrated, establishing the internal finance ledger as the sole authoritative college record for student fee status.
Affects: Fees & Finance, Student Management, Academic Foundation, Identity Audit, and Administrative Dashboards.

ADR-026: Extensible Assessment Architecture, Scoped Faculty Mark Uploads & Student Visibility Boundaries
Date: 2026-09-07
Status: Accepted
Decision:
1. Extensible Assessment Model: Assessments are decoupled from fixed test kinds; an extensible `AssessmentType` catalogue defines continuous assessment categories (Unit Test 1, Unit Test 2, Assignments, Lab Practicals, Seminars).
2. Faculty Scoped Upload: Faculty members can only upload marks for subjects, semesters, and batches to which they have an active `FacultyAssignment`. Attempts to upload marks outside their assigned cohort or department are rejected at the service layer.
3. Batch Mark Ingestion & Invariant Validation: Mark uploads (spreadsheet/batch JSON) are subject to rigorous server-side validation:
   - Mark bounds: $0 \le \text{marks} \le \text{max\_marks}$.
   - Absent students: If `is_absent=True`, marks must be 0 or null; if absent, the student is recorded as absent with no positive score.
   - Duplicate prevention: Duplicate student identifiers in the upload payload are caught and rejected prior to persistence.
   - Enrollment verification: Marks can only be entered for students currently enrolled in the corresponding academic program, semester, and batch.
   - Atomic rollback: Any invalid row or invariant failure aborts the entire upload transaction.
4. Visibility Boundaries: Marks in `DRAFT` status are strictly hidden from students. Only once an assessment transitions to `PUBLISHED` (or `LOCKED`) do marks become visible in the student self-portal.
5. Historical Immutability: Once locked (`LOCKED`), assessment marks cannot be modified, deleted, or re-uploaded.
Why: Preserves institutional assessment integrity, upholds faculty accountability without allowing cross-cohort tampering, prevents student exposure to provisional draft marks, and guarantees immutable historical records.
Affects: Assessments, Faculty, Academic Foundation, Student Management, and Identity.

ADR-027: Academic Results Lifecycle, Staged Ingestion, Published Immutability & V2 Supersession Architecture
Date: 2026-09-07
Status: Accepted
Decision:
1. Controlled Ingestion Pipeline: Official results are ingested via an explicit staged pipeline:
   `Result Excel/CSV` -> `ResultImportBatch` (PENDING) -> `ResultImportRow` (PROCESSING) -> `Row Validation & Deterministic Matching` -> `Draft Generation` (VALIDATED).
2. Deterministic Student Association: Result staging rows are matched against canonical student records using established matching precedence (1. Enrollment No, 2. Application ID, 3. University Reg No) and verified against active semester enrollment. Missing students or invalid marks flag the individual staging row and prevent unauthorized publication.
3. Multi-Stage Lifecycle: Results adhere to an explicit domain state machine:
   `DRAFT` -> `PROCESSING` -> `VALIDATED` -> `APPROVED` -> `PUBLISHED`.
   Publication cannot occur without explicit approval by an authorized actor (e.g., Dean Academics / Exam Controller).
4. Published Result Immutability: Published results (`status='PUBLISHED'`) and their breakdown details are treated as immutable historical legal evidence. In-place modification or deletion raises `ResultImmutabilityViolation` at the domain and model boundary.
5. Additive Correction via V2 Supersession (ADR-016): Corrections must originate via an authorized `ResultCorrectionRequest` with mandatory justification. Upon review and approval:
   - Historical Result V1 is preserved with `is_latest=False`, `status='SUPERSEDED'`, and linked to `superseded_by=V2`.
   - Result V2 is generated with `version=2`, `is_latest=True`, and `status='PUBLISHED'`.
   - An immutable `ResultCorrectionAudit` entry records the responsible actor, timestamp, action, and justification.
Why: Strictly enforces PRD Section 5 and ARCHITECTURE.md Section 11, eliminating silent data tampering, preserving official historical evidence, guaranteeing student-view isolation for draft results, and ensuring complete accountability.
Affects: Results, Academic Foundation, Student Management, Onboarding, and Identity Audit.

ADR-028: Result-to-Credit Derivation, Configurable Eligibility Rules, Explicit Decision States & Promotion Register
Date: 2026-09-07
Status: Accepted
Decision:
1. Result-to-Credit Calculation: Earned credits and grade points are calculated strictly from published StudentResult records using SchemeSubject credit weightings. Non-passing or absent subjects earn 0 credits and increment the backlog count. SGPA and cumulative CGPA are derived deterministically.
2. Historical Credit Calculation Integrity: Credit records (StudentCredit) are linked to specific result versions. When a result is superseded (V1 -> V2), V1's StudentCredit is retained with `is_latest=False` as an immutable record, and a new StudentCredit record is created for V2, ensuring historical decisions remain explainable.
3. Configurable Eligibility Rules & Versioning: Institutional promotion criteria (min credits, min attendance %, max backlogs, and detention thresholds) are modeled as configurable data entities (EligibilityRule) with version tracking rather than hardcoded logic. Modifying an active rule that has associated decisions spawns a new version (v2, v3, etc.) preserving prior rule definitions for historical audit.
4. Explicit Eligibility & Detention States: The evaluation engine evaluates student academic standing and produces explicit decision states: ELIGIBLE, NOT_ELIGIBLE, or DETAINED. Detention conditions (excessive backlogs or critically low attendance) take precedence over general ineligibility. Decisions snapshot the exact rule and rule_version applied.
5. Next-Year Promotion Register: The promotion register consumes authoritative active StudentEnrollment records from Student Management and joins them with the latest EligibilityDecisions, generating promotion registers without duplicating student enrollment state.
Why: Enforces PRD Section 5 and ARCHITECTURE.md Section 11, eliminating hardcoded business logic, guaranteeing historical explainability for academic standing, and providing a clean query foundation for reporting.
Affects: Results & Eligibility, Academic Foundation, Student Management, and Reporting.

ADR-029: Reusable Student Services Framework, Explicit Approval Workflows & Document Integration
Date: 2026-09-07
Status: Accepted
Decision:
1. Reusable Service Foundation: Student services are driven by configurable `ServiceRequestType` definitions (code, name, `requires_document` + `allowed_document_types`) rather than separate ad-hoc tables per service type. Prototype defers `category/SLA days/fee` catalog columns until institutional catalog requires them.
2. Explicit Workflow State Machine: Service requests follow an explicit, enforced lifecycle:
   `SUBMITTED` -> `IN_PROGRESS` -> `APPROVED` / `REJECTED` -> `COMPLETED` (with optional `CANCELLED` from non-terminal states). Arbitrary status jumps (such as jumping directly from `SUBMITTED` to `APPROVED` or `COMPLETED`) raise `ServiceStateTransitionError`.
3. Mandatory Rejection Reason: Transitioning a request to `REJECTED` strictly requires a non-empty `rejection_reason`. Attempting to reject without a justification raises `ServiceValidationError` and is prevented at the domain boundary.
4. Canonical Document Attachment: Service request document requirements reference canonical `apps.documents.StudentDocument` records owned by the Documents bounded context. No separate file store or duplicate document records are introduced. Validates that attached documents match the allowed document types defined on the service type.
5. Accountable-Actor Audit: Every state transition, document attachment, and assignment is recorded in an append-only `ServiceRequestAudit` log capturing the timestamp, old status, new status, accountable actor User FK, action name, and administrative notes/reasons.
6. Scoped Access & Student Isolation: Students are strictly scoped to viewing and submitting their own service requests (`/api/v1/services/requests/my_requests/` and auto-scoping based on the authenticated user's linked student). Administrative actions (assign, process, approve, reject, complete) require staff privileges.
Why: Preserves institutional governance, prevents unvetted status changes, guarantees student transparency for rejections, eliminates redundant document storage, and establishes a complete legal audit trail for student certificates and official requests.
Affects: Student Services, Documents, Student Management, and Identity & Access.

ADR-030: Read-Only Module Query Interfaces, Multi-Dimensional Analytics & Bounded Export Architecture
Date: 2026-09-07
Status: Accepted
Decision:
1. Read-Only Downstream Consumer Bounded Context: `apps.reporting` owns zero operational database tables. It operates strictly as a read-oriented consumer layer and never executes state-mutating writes on core business models.
2. Module-Owned Query Interfaces (ADR-017): Reporting queries strictly consume authoritative data through dedicated query services owned and encapsulated by the respective bounded contexts (`StudentReportingQueryService`, `FinanceReportingQueryService`, `ResultsReportingQueryService`, `VerificationReportingQueryService`, `AuditReportingQueryService`). Reporting never makes raw or uncoordinated direct table queries across domain boundaries.
3. Bounded Export Guardrails: All tabular report exports (CSV) enforce a strict maximum ceiling (`MAX_EXPORT_LIMIT = 5000` rows) and validated pagination/filter contracts (`ReportFilterSpec`, `PaginationSpec`). Requests exceeding limits or attempting unbounded memory buffers are rejected, protecting application memory and guarding against denial of service.
4. Multi-Dimensional Analytics Aggregation: Cross-cutting analytical summaries (demographic distributions, fee collection vs outstanding dues, verification turnaround bottlenecks, academic grade distributions, and administrative actor activity) use standard bounded ORM aggregations (`Count`, `Sum`, `Avg`) without introducing premature event streaming, external search engines, or CQRS messaging systems (per ADR-018).
5. N+1 Query Elimination via In-Memory Traversal of Prefetched Relations: Reverse foreign key relations are traversed using in-memory prefetch caches (`next((e for e in s.enrollments.all() if e.status == 'ACTIVE'), None)`) rather than triggering ad-hoc ORM queries (`.filter().first()`), maintaining a constant bounded query profile ($\le 8$ SQL queries) under production cohort loads.
Why: Preserves strict bounded-context isolation, maintains single sources of truth, protects database connection pools and application memory from resource exhaustion, and delivers responsive, real-time analytics across all institutional operational dimensions.
Affects: Reporting & Analytics, Student Management, Fees & Finance, Results & Eligibility, Verification, Audit & Observability, and Frontend Intelligence.

ADR-031: Production Hardening, Zero-Trust Platform Security, and Resilient Deployment Architecture
Date: 2026-09-07
Status: Accepted
Decision:
1. Cross-Cutting Defense-in-Depth Security:
   - Scoped Throttling & Rate Limiting: Authentication endpoints (`/auth/login/`, `/auth/token/refresh/`) are protected by `AuthRateThrottle` (5 requests/minute). Sensitive data reveal endpoints (`/reveal-sensitive/`) are protected by `SensitiveRevealRateThrottle` (10 reveals/hour per authenticated user).
   - Strict Security Headers & Production SSL: Enforces `SECURE_BROWSER_XSS_FILTER = True`, `SECURE_CONTENT_TYPE_NOSNIFF = True`, `X_FRAME_OPTIONS = 'DENY'`, and strict HTTP Strict Transport Security (`SECURE_HSTS_SECONDS = 31536000`, include subdomains, preload) with secure session/CSRF cookies in production (`DEBUG=False`).
   - Generic Production Error Masking: Custom exception handler masks unhandled 500 server errors in production, returning sanitized JSON (`{"error": "Internal server error. Please contact the administrator."}`) to eliminate information disclosure of stack traces, database schemas, or infrastructure paths.
2. Database & Historical Integrity Preservation:
   - Zero New Business Tables: Production hardening introduces zero redundant operational tables, alternative persistence stores, or duplicate sources of truth.
   - Non-Destructive Additive History: Enforces relational database constraints, cascading protections (`RESTRICT` on accountable actors, fee heads, and scheme rules), and append-only audit preservation across financial transactions, published results, and student documents.
   - Idempotent Production Workflows: Validates that repeated imports and payment operations produce idempotent results without creating phantom duplicate rows or corrupting account ledgers.
3. Performance SLAs & N+1 Query Eradication:
   - Prefetched In-Memory Traversal: Eradicated N+1 query patterns across student directory listing serializers by resolving related enrollments from Django's prefetch cache rather than executing ad-hoc subqueries per row.
   - Performance SLA Criteria: High-volume student directory searches (<250ms), cross-module KPI analytics aggregations (<300ms), and bounded CSV streaming exports (<1500ms) operate within verified sub-second latency bounds under full cohort scale.
   - Concurrency & Row-Level Locking: Financial balance modifications, payment reversals, and result publications utilize atomic transactions and row-level locking (`select_for_update()`) to eliminate race conditions under concurrent workloads.
4. Containerized Deployment & Disaster Recovery:
   - Multi-stage containerization: Production `backend/Dockerfile` utilizes unprivileged user execution (`appuser`), multi-worker Gunicorn WSGI (`--workers 4 --threads 2`), and health checks; `frontend/Dockerfile` uses multi-stage Node/Vite build serving optimized static bundles via Nginx.
   - Production Reverse Proxy: Nginx reverse proxy configuration enforces HTTPS, forwards client headers (`X-Real-IP`, `X-Forwarded-For`), serves static/media volumes directly, and implements gzip compression.
   - Cryptographic Backup & Restore: Automated disaster recovery scripts (`backup_db.py`, `restore_db.py`) produce transactional backups with SHA-256 integrity checksums, rejecting corrupted or tampered dump files prior to restoration.
   - Production Pre-Flight Checklist: Automated deployment verification script (`check_production_readiness.py`) inspects unapplied migrations, security settings, directory permissions, and encryption keys before traffic routing.
Why: Ensures institutional-grade reliability, strict data integrity, zero-trust security posture, and non-destructive historical explainability without compromising the clean boundaries of the modular monolith.
Affects: Platform Infrastructure, Identity & Access, Student Management, Documents, Fees & Finance, Results & Eligibility, Reporting & Analytics, and Production Operations.

ADR-032: Faculty Account Auto-Provisioning on Creation
Date: 2026-09-08
Status: Accepted
Decision: When a new Faculty record is created via the Faculty API (`POST /api/v1/faculty/members/`), the Faculty bounded context auto-provisions a login `User` account in the Identity module within the same atomic transaction. The provisioned account uses:
- `username` = `faculty_id` (the faculty's institutional ID)
- Initial `password` = `Edvana@2026` (requires mandatory password change on first login per ADR-009 policy)
- A department-scoped `HOD` role is assigned if the faculty is created with `designation=HOD`; otherwise a department-scoped `FACULTY` role is assigned.
Why: Faculty onboarding requires immediate system access without a separate administrative provisioning step. Keeping provisioning atomic with faculty record creation prevents orphaned faculty records with no login access. The username convention (faculty_id) matches the student provisioning convention (enrollment_no) established in ADR-009, maintaining a consistent provisioning pattern.
Constraints: The default password `Edvana@2026` is an institutional default and must be changed at first login. This credential must never be stored in version control, logs, or audit payloads. The Identity module's credential lifecycle rules (ADR-009) govern the password change policy.
Alternatives considered: A separate administrator-triggered provisioning step (rejected — risk of orphaned faculty records); an invitation-based email flow (deferred — no email infrastructure in current scope per ADR-018).
Affects: Faculty & Academic Assignment, Identity & Access, and Audit.

Decision Integrity Rule
Future implementation work must treat all ADRs marked Accepted as settled architectural constraints. They
should not be reversed merely to simplify an implementation, satisfy an AI coding agent, or introduce a
familiar architectural pattern.
The two ADRs marked Open are intentionally unresolved and must remain policy decisions until explicitly
finalized.
The architectural objective remains a simple modular monolith that is difficult to corrupt accidentally, easy
for humans to understand, and constrained enough that an AI coding agent cannot casually cross domain
boundaries.


8

