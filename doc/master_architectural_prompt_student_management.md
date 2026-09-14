<!-- Page 1 -->

Master Architectural Prompt • Page 1
Production Database Architecture Prompt
College Student Management & Administrative Data System
Role: Act as a Principal Database Architect, Senior Backend Engineer, Domain-Driven Design (DDD) Architect,
and PostgreSQL specialist.
Stack: Django + Django REST Framework + PostgreSQL (Modular Monolith, NOT microservices).
Your responsibility is NOT to blindly convert a field list into tables. Your responsibility is to first understand the
domain, identify ownership and lifecycle of every piece of data, model relationships correctly, preserve historical
integrity, prevent duplication, and produce a database that is performant, secure, maintainable, and safe to evolve.
1. Product Scope
The system manages: System Admin, College Staff, Register, Student Management/Clerk, Accountant,
Scholarship Staff, Principal, HOD, Class Teacher, Teacher, Students, Government student-data imports, Student
onboarding/verification, Documents, Batch management, Academic enrollment, Scheme/curriculum, Unit Test
marks, Result Excel imports, Results, Credits, Eligibility, Detention/progression, Fee structures/payments, Student
services, Reports, Analytics, and Audit logs.
OUT OF SCOPE: This is NOT a complete university ERP. Do NOT introduce unrelated modules (University exam
registration, complex timetable engine, Hostel, Library, Gymkhana) unless explicitly requested.
2. Core Architectural Principles
Single Source of Truth: Every important piece of information must have one authoritative location. Never store the
same business fact in multiple places.
Domain Ownership: For every important field, determine: Who provides it? Who owns it? Who can modify/verify it?
What is its source? Does it need historical tracking?
Normalize by Default: Avoid comma-separated values, repeated columns, and giant tables. However, do not
over-normalize. Use JSONB only for genuinely flexible data (import raw rows, audit snapshots, controlled
metadata).
No God Tables: Do not create tables merely to reduce columns. Do not merge genuinely different domain entities
merely to reduce table count.
3. Student Architecture & Raw Data Dictionary
Architectural Rule: Do NOT create a giant students table. Separate data by domain ownership:
`students` (stable identity), `student_addresses`, `student_admissions`, `student_categories`,
`student_bank_accounts`, `student_scholarships`, `student_enrollments`, `student_documents`.
Distribute the following raw fields into the appropriate sub-tables based on their lifecycle and domain:
Identity/Demographics: Application ID, Enrollment No., Board/University Enrollment No., Candidate Name, Father
Name, Mother Name, Gender, Date of Birth, Student Mobile, Parent Mobile, Email, Religion, Category, Mother
Tongue, Candidature Type.
Address: Address, State, District, Taluka, Village, Pincode.
Educational History: SSC Passing Year, SSC Board, SSC Total%, HSC Passing Year, HSC Board, HSC School
Name, HSC College Name, HSC Total%.
Admission & Entrance: CET Percentile, JEE Percentile, Eligibility Percentage, Choice Code, Seat Type, Admission
Category, Reservation Type, Allotted Seat Type, Admission Type, Admission Date, DSA/DSE Flag, Starting
Semester.
Financial/Scholarship: Annual Family Income, Income Range/Slab, Scholarship Applied, Scholarship Type.

---

<!-- Page 2 -->

Master Architectural Prompt • Page 2
Current Status: Current Status (Note: Do not use this as the authoritative academic state; use
`student_enrollments`).
4. Student Lifecycle & Enrollments
Initial rollout is first-year students, but the schema must support: First Year → Second Year → Third Year →
Completion/Exit without redesign.
Rule: Do NOT make `students.current_semester` the authoritative academic history.
Source of Truth: Use `student_enrollments` containing: student, academic year, semester, department, program,
batch, scheme, and status. Historical enrollments must remain intact.
5. Government Excel Import Pipeline
Never import government Excel directly into production tables. Use a strict pipeline:
Source File → Import Batch → Staging Rows → Validation → Normalization → Deduplication →
Production Records
Staging Layer: Preserve original row, row number, raw data, normalized values, validation errors, processing
status, resulting student ID.
Idempotency: Re-uploading the same source data must NOT create duplicate students. Explicitly define matching
precedence (Application ID vs Enrollment No. vs Board Enrollment No.).
States: UPLOADED, VALIDATING, VALIDATED, IMPORTING, COMPLETED, FAILED,
PARTIALLY_COMPLETED, CANCELLED.
6. Academic Foundation & Historical Integrity
Separate: Department, Program, Academic Year, Semester, Batch, Department Intake, Scheme, Subject, Scheme
Subject.
Subject: Reusable identity.
Scheme Subject: Subject under a specific scheme (semester, type, credits, marks, passing requirements).
Historical Integrity: Do not mutate historical scheme-subject definitions in a way that changes old results. Students
must retain their historical scheme relationships even if the college introduces a new scheme.
7. Faculty & Accreditations
Use ONE `faculties` table for Permanent, Visiting, and Contract faculty.
Track subject assignments historically (faculty, scheme subject, academic year, semester, batch). Do not store
subjects taught as comma-separated text.
Accreditations: Keep genuinely different entities separate. Do not force distinct entities into a single generic table
just to save space. Use separate tables for: `publications`, `patents`, `books`, `awards`, `memberships`,
`consultancy`, `project_phd_guidance`.
8. Documents & Sensitive Data
Storage: Do NOT store actual files as large binary fields in Postgres. Store secure metadata (document type,
owner, storage key, checksum, file size, MIME type, verification status, reviewer, rejection reason, version status)
in Postgres. Actual files go to object storage.
Ownership: Avoid polymorphic foreign keys (`entity_type`, `entity_id`). Use typed ownership: `student_documents`,
`faculty_documents`.
History: Document replacement must preserve history (e.g., Old Letter → SUPERSEDED, New Letter →
CURRENT). Never silently overwrite.

---

<!-- Page 3 -->

Master Architectural Prompt • Page 3
Sensitive Data: Aadhaar, bank details, and personal contacts require strong protection. Do not expose via ordinary
APIs/logs. Use encryption and audit access.
9. Verification, Assessments & Results
Verification: A workflow, not a boolean. States: PENDING, APPROVED, REJECTED, NEEDS_CORRECTION.
Track submitter, reviewer, time, and rejection reasons. Government-sourced information cannot be freely edited by
students.
Assessments: Extensible model (`assessment_types`, `assessments`, `assessment_marks`). Do not hardcode
only `unit_test_marks`.
Results Pipeline: Result Excel → Result Import Batch → Rows → Validation → Result Records → Credit/Eligibility
Calc → Approval → Publication.
Result States: DRAFT, PROCESSING, VALIDATED, APPROVED, PUBLISHED, REJECTED. Never silently
overwrite previous attempts or published history.
10. Eligibility & Fees
Eligibility: Driven by configurable rules (min attendance, min credits, max backlogs), NOT hardcoded Python logic.
Store decisions with the rule/version used. States: ELIGIBLE, NOT_ELIGIBLE, DETAINED.
Fees: Separate Fee Definitions (`fee_heads`, `fee_structures`, `fee_structure_items`) from Student Financial State
(`student_fee_accounts`, `fee_charges`, `payments`). A charge is what is owed; a payment is the financial event.
Support partial payments. Historical fee structures must never change after use.
11. Advanced Database Design Rules
IDs (UUIDs vs Business Keys): Use UUIDs for internal primary keys. Do NOT confuse them with business
identifiers (Enrollment No, Application ID, Employee Code). Business identifiers must have strict UNIQUE
constraints.
Soft Deletion: Do NOT use `is_deleted` as a universal lifecycle solution. Use explicit state machines (e.g., ACTIVE,
DETAINED, PASSED_OUT, DROPPED, TRANSFERRED).
Operational Metadata: Include `created_at`, `updated_at`, `created_by`, `updated_by` on important mutable
records. Do not add them blindly to immutable lookup tables.
Constraints: Explicitly determine PK, FK, NOT NULL, UNIQUE, CHECK constraints, ON DELETE/UPDATE
behavior for EVERY table. Enforce invariants at the DB level.
Indexing: Design indexes from actual query patterns (search by enrollment, filter by batch, category reports). Use
composite indexes and Postgres-specific indexes (trigram/GIN) only when justified. Validate with EXPLAIN
ANALYZE.
12. Performance, Concurrency & Migrations
Performance: Do NOT prematurely introduce sharding, Kafka, CQRS, event sourcing, or partitioning. Rely on
Postgres, proper normalization, connection pooling, Django `select_related`/`prefetch_related`, and Redis only
where justified.
Concurrency: Identify transaction boundaries (Student import, Fee payments, Result publication). Use
idempotency to prevent duplicate financial/academic corruption from concurrent requests.
Migrations: Every schema change must be a migration. Design for backward compatibility, safe deployment, and
zero/low downtime.
13. RBAC and Authorization
Use `Users`, `Roles`, `Permissions`, `RolePermissions`, `UserRoles`. Support scoped authorization:
System Admin → System-wide

---

<!-- Page 4 -->

Master Architectural Prompt • Page 4
Register → Student Section
HOD → Department
Class Teacher → Assigned batch/class
Teacher → Assigned subjects/batches
Accountant → Fee operations
Student → Own permitted records
Backend MUST enforce permissions and scopes; do not rely on frontend hiding.
14. Required Deliverables
Do NOT jump directly to Django models. Produce the following in order:
• A. Domain & Bounded-Context Map: Show all modules and their boundaries.
• B. Source-of-Truth Map: Explicitly state which table owns which data.
• C. Complete ERD: Show all entities and relationships.
• D. Table Catalogue: For every table provide: purpose, columns, Postgres types, nullable, default, PK, FK,
unique, check constraints, indexes, delete/update behavior.
• E. Relationship Catalogue: Explicitly explain every 1:1, 1:N, M:N relationship.
• F. Business Constraints & State Machines: List invariants and define state transitions for verification, imports,
documents, results, fees, and eligibility.
• G. Historical Data Strategy: Explain how history is preserved for enrollments, schemes, results, fees, and
documents.
• H. Import & Document Architecture: Detail the Excel staging pipeline and document metadata storage.
• I. Security & Sensitive Data Strategy: Explain protection for Aadhaar, bank details, and audit info.
• J. RBAC & Scoped Authorization Model: Detail the permission matrix.
• K. Transaction, Concurrency & Index Strategy: Identify transaction boundaries, idempotency keys, and explain
which query each important index optimizes.
• L. Performance & Failure Scenarios: Explain what happens when: Excel has duplicates, import partially fails,
result Excel is malformed, two users update the same student, payment is submitted twice, or published results
need correction.
• M. Critical Architecture Review: Before finalizing, explicitly search for and document checks against: duplicated
data, missing FKs, orphan possibilities, over/under-normalization, historical corruption risks, race conditions,
sensitive-data exposure, and JSONB misuse.
• N. Final PostgreSQL Schema: The complete, executable SQL/Schema definition.
• O. Django App/Model Mapping & Migration Strategy: Map the schema to Django apps/models and define the
migration rollout plan.
15. Final Quality Standard
Do not claim the design is perfect merely because all listed fields exist.
The goal is NOT the fewest tables. The goal is: THE SIMPLEST DATABASE THAT CORRECTLY REPRESENTS
THE REAL BUSINESS DOMAIN AND REMAINS SAFE AS THE SYSTEM GROWS.
If requirements are ambiguous, identify the ambiguity and ask before making an irreversible architectural
assumption.
