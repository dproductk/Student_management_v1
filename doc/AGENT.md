# AGENT.md --- Student Management System

## Production Engineering & AI Implementation Contract

> **Status:** Mandatory project-level instructions for AI coding agents.
>
> **Primary rule:** This document governs implementation.
> `ARCHITECTURE.md` governs architectural intent, and feature-specific
> PRDs govern feature behavior. When these documents conflict, **stop
> and ask for clarification** rather than guessing.

------------------------------------------------------------------------

# 1. Role & Operating Mode

You are a **Staff/Principal-level Software Engineer working under the
project's architecture**, not a rapid prototyping assistant.

Your objective is to build software that is:

-   Correct
-   Secure
-   Maintainable
-   Observable
-   Testable
-   Resilient
-   Performant
-   Easy for another engineer to understand
-   Safe to extend
-   Safe for AI agents to modify later

Do not optimize for "the code works on the happy path."

Optimize for:

> **Correctness → Data integrity → Security → Maintainability →
> Reliability → Performance → Developer convenience**

You are an implementation agent, not the product owner or architect.

If a requirement is ambiguous at the architecture/business-rule level,
**STOP and ask**.

------------------------------------------------------------------------

# 2. Project Identity

## Project

**Student Management & Administrative Data System**

## Purpose

A production-grade student management and administrative data platform
for a college.

It is **not a full college ERP**.

The system focuses on:

-   Student records
-   Student onboarding/import
-   Government-sourced student data
-   Verification workflows
-   Documents
-   Academic structure
-   Faculty and academic assignments
-   Fees and financial records
-   Academic results
-   Eligibility/progression
-   Student service requests
-   Reporting and analytics
-   Auditability
-   System administration

Do not introduce unrelated ERP functionality such as timetable, hostel,
library, university examination registration, or payment gateway
functionality unless explicitly requested and architecturally approved.

------------------------------------------------------------------------

# 3. Technology Baseline

## Backend

-   Django
-   Django REST Framework

## Database

-   PostgreSQL

## Frontend

-   React

## Authentication

-   JWT

## Architecture

-   Modular monolith
-   Domain-oriented bounded contexts
-   Deep modules
-   Layered/hexagonal internal boundaries
-   Single-college deployment

## Deployment Philosophy

Start as a modular monolith.

Do **not** introduce microservices merely because they are considered
"enterprise."

Do not introduce Kafka, CQRS, event sourcing, sharding, Kubernetes,
distributed transactions, or similar infrastructure unless a real
measured requirement and explicit architectural decision justify it.

------------------------------------------------------------------------

# 4. Source-of-Truth Hierarchy

The project has three primary levels of authority:

1.  `ARCHITECTURE.md`
    -   Defines bounded contexts, ownership, dependencies, layering,
        architectural rules, and system-wide patterns.
2.  Feature PRD / approved requirements
    -   Defines what the feature must do.
3.  `AGENT.md`
    -   Defines how the agent must implement the approved design.

The agent must not silently redesign the architecture while implementing
a feature.

If implementation reveals a genuine architectural problem:

1.  Stop.
2.  Explain the conflict.
3.  Propose the architectural change.
4.  Wait for approval.
5.  Only then implement it.

------------------------------------------------------------------------

# 5. Bounded Contexts & Ownership

The system is divided into these business modules:

1.  Identity & Access
2.  Academic Foundation
3.  Student Management
4.  Student Onboarding & Import
5.  Verification
6.  Documents
7.  Faculty & Academic Assignment
8.  Fees & Finance
9.  Academic Results & Eligibility
10. Student Services
11. Reporting & Analytics
12. Audit & Observability

## Ownership Rule

Every important business fact has **one authoritative owner**.

The module that owns a piece of data is the only module allowed to
define its business behavior and write it directly.

Other modules must use the owner's approved interface/use case/query
contract.

### Never do this

A module must not directly reach into another module's ORM/model layer
merely because the data is convenient.

### Correct principle

> **Ownership is stronger than convenience.**

------------------------------------------------------------------------

# 6. Module Responsibilities

## Identity & Access

Owns:

-   Users
-   Roles
-   Permissions
-   Authentication
-   Authorization
-   Credential lifecycle

It does not own student business records.

System Admin can configure users, roles, permissions, master data and
system configuration, and can view system-wide information.

System Admin does **not** directly edit live student records.

------------------------------------------------------------------------

## Academic Foundation

Owns:

-   Departments
-   Programs
-   Academic years
-   Semesters
-   Batches
-   Schemes/curricula
-   Subjects
-   Scheme-subject definitions

It defines the academic structure used by operational modules.

Do not duplicate academic master data inside Student Management,
Faculty, Fees, or Results.

------------------------------------------------------------------------

## Student Management

Owns the authoritative student administrative record and lifecycle.

It owns concepts such as:

-   Student identity
-   Admission information
-   Address
-   Enrollment
-   Student lifecycle
-   Student administrative information

Student enrollment history must remain intact.

Do not replace historical enrollment information with a single "current
year" field when the domain requires history.

------------------------------------------------------------------------

## Student Onboarding & Import

Owns:

-   Import batches
-   Staging rows
-   Source metadata
-   Validation results
-   Import errors
-   Import state
-   Import processing

External files are input sources, not domain models.

Excel must not become the foundation of the student domain.

The import pipeline is conceptually:

``` text
External Source
    ↓
Import Batch
    ↓
Staging
    ↓
Validation
    ↓
Normalization
    ↓
Identity Matching
    ↓
Manual Conflict Review where required
    ↓
Student Management
```

------------------------------------------------------------------------

## Verification

Owns verification workflows and decisions.

It does not become a second student database.

Verification decisions must identify:

-   Actor
-   Action
-   Timestamp
-   Target
-   Reason where applicable

Verification is a workflow/state machine, not a simple boolean such as
`is_verified`.

------------------------------------------------------------------------

## Documents

Owns document metadata, versions, lifecycle and verification state.

Actual document binaries should live in appropriate object storage; the
database stores metadata and secure references.

Documents are versioned.

Never silently overwrite an accepted historical document.

------------------------------------------------------------------------

## Faculty & Academic Assignment

Owns:

-   Faculty records
-   Faculty classification
-   Faculty roles/assignments as applicable
-   Faculty-to-subject assignments
-   Faculty-to-batch assignments
-   Assignment history

Do not create unnecessary inheritance for Permanent/Visiting/Contract
faculty when they represent the same domain concept.

------------------------------------------------------------------------

## Fees & Finance

Owns:

-   Fee heads
-   Fee structures
-   Fee structure items
-   Student charges
-   Payment ledger entries
-   Financial state

This application is the sole source of truth for fee status.

There is no external payment gateway reconciliation requirement in the
current scope.

Payments are append-only ledger entries.

Never overwrite a payment history or turn it into a mutable `paid=true`
flag.

Mistakes are corrected through reversal/correction entries.

Every payment identifies the accountable actor and timestamp.

------------------------------------------------------------------------

## Academic Results & Eligibility

Owns:

-   Assessments
-   Marks
-   Results
-   Credits
-   Eligibility
-   Progression decisions

Result lifecycle is controlled.

Published results are historical records.

A correction creates a new version and links the previous result as
superseded.

Never silently overwrite a published result.

Eligibility must be rule-driven and extensible.

------------------------------------------------------------------------

## Student Services

Owns reusable student service-request workflows.

A new service request type should normally be absorbed by this module
rather than creating a new architectural module.

------------------------------------------------------------------------

## Reporting & Analytics

Reporting is a consumer of authoritative business information.

It does not become a second source of truth.

The initial architecture uses module-owned read/query interfaces.

If future scale requires reporting projections/materialized read data,
those projections remain derived data and must not become authoritative.

------------------------------------------------------------------------

## Audit & Observability

Audit is distinct from ordinary debugging logs.

Audit records important business/security actions such as:

-   Student corrections
-   Verification decisions
-   Document approvals/rejections
-   Payment entries/reversals
-   Result approval/publication/correction
-   Role/permission changes
-   Sensitive-data reveals
-   Administrative actions

Audit history must not be casually editable by business modules.

------------------------------------------------------------------------

# 7. Dependency Rules

The dependency graph must remain acyclic.

There must be **zero circular dependencies**.

Conceptually:

``` text
Identity & Access
       ↑
       │
   All protected modules

Academic Foundation
       ↑
       ├── Student Management
       ├── Faculty & Assignment
       ├── Finance
       └── Results

Student Management
       ↑
       ├── Onboarding
       ├── Verification
       ├── Documents
       ├── Finance
       ├── Results
       └── Services

Faculty & Assignment
       ↑
       └── Results

Results
       ↓
   Reporting

Finance
       ↓
   Reporting

Student Management
       ↓
   Reporting
```

Do not create:

``` text
A → B → C → A
```

If a feature appears to require a circular dependency:

**Stop and ask.**

------------------------------------------------------------------------

# 8. Layering Rules

Within a domain module, respect the conceptual layers:

``` text
API / Presentation
        ↓
Application / Use Cases
        ↓
Domain
        ↓
Persistence / Adapters
```

## API Layer

Responsible for:

-   HTTP concerns
-   Request/response representation
-   Authentication integration
-   Edge validation
-   Calling application use cases

Must not contain core business rules.

Must not directly manipulate ORM records.

------------------------------------------------------------------------

## Application Layer

Responsible for:

-   Use cases
-   Workflow orchestration
-   Transaction boundaries
-   Coordination
-   Idempotency where required
-   Calling domain behavior

------------------------------------------------------------------------

## Domain Layer

Responsible for:

-   Business rules
-   Invariants
-   State transitions
-   Policies
-   Eligibility rules
-   Correction semantics
-   Financial rules
-   Student lifecycle rules

------------------------------------------------------------------------

## Persistence / Adapter Layer

Responsible for:

-   ORM interaction
-   Queries
-   Repository implementations
-   External integrations
-   Storage adapters

------------------------------------------------------------------------

# 9. Database Rules

PostgreSQL is the primary source of persistence.

## Required principles

-   Normalize relational data appropriately.
-   Preserve historical information where the business requires history.
-   Use database constraints for invariants that belong at the data
    layer.
-   Use application/domain validation for business rules.
-   Avoid duplicate sources of truth.
-   Use indexes based on actual query patterns.
-   Analyze expensive queries.
-   Prevent N+1 queries.
-   Use appropriate transaction isolation.
-   Use connection pooling appropriately.
-   Use locking intentionally where concurrent state changes require it.

## Query discipline

Never casually introduce:

-   Unbounded queries
-   `SELECT *`-style broad retrieval when unnecessary
-   N+1 relationship loading
-   Repeated queries inside loops
-   Expensive filtering without appropriate indexes

Use Django ORM safely and efficiently.

Raw SQL is permitted only when genuinely justified and must always be
parameterized.

Never construct SQL through string concatenation.

------------------------------------------------------------------------

# 10. Data Integrity Rules

The database must help enforce critical invariants.

Examples:

-   Unique identifiers must be protected at the database level.
-   Required relationships must be protected.
-   Invalid states should be prevented where database constraints can
    reasonably enforce them.
-   Historical records must not be destructively rewritten.

Application validation is not a substitute for database integrity.

Database constraints are not a substitute for domain validation.

Use both at the appropriate boundary.

------------------------------------------------------------------------

# 11. Government Import Rules

Government data is treated as an immutable source record.

The original government value must never be overwritten in place.

Corrections are additive.

``` text
Original Government Value
        ↓
Preserved Permanently
        ↓
Corrected Authoritative Value
        ↓
Reason + Approver + Timestamp + Audit
```

## Identity matching precedence

Use exactly this order:

``` text
1. Application ID
2. Enrollment No.
3. Board / University Enrollment No.
```

### No match

Create a new student.

### One valid match

Associate the row with that student.

### Conflicting identifiers

Example:

``` text
Application ID → Student A
Enrollment No. → Student B
```

Never auto-merge.

Flag the row for manual review.

------------------------------------------------------------------------

# 12. Correction & Reversal Pattern

## Global Rule

> **Corrections are additive, never destructive.**

Do not delete evidence merely to make the current state look correct.

Examples:

### Government data

Original value → corrected value

### Fees

Original payment → reversal/correction entry

### Results

Published Result V1 → superseded by Result V2

### Documents

Document V1 → superseded by Document V2

### Verification

Previous decision remains historically traceable; a new decision/action
records the correction.

Every correction should preserve, where applicable:

-   Original record reference
-   New state/value
-   Accountable actor
-   Timestamp
-   Reason
-   Approval
-   Audit record

Do not invent one giant generic correction service that understands
every domain.

The **pattern is shared; the domain behavior remains owned by each
module.**

------------------------------------------------------------------------

# 13. Accountable Actor Pattern

Any sensitive human decision must identify the responsible actor.

At minimum, conceptually:

``` text
WHO
WHAT
WHEN
TARGET
WHY — where required
```

This applies to:

-   Verification approval/rejection
-   Document approval/rejection
-   Payment recording
-   Payment reversal
-   Result approval
-   Result publication
-   Result correction
-   Government-data correction
-   Role/permission changes
-   Sensitive-data reveal

Anonymous status-changing operations are prohibited.

------------------------------------------------------------------------

# 14. Trust Model

This system does not have an external system of record that
independently validates every human-entered administrative decision.

Therefore:

> **The architecture cannot guarantee that every staff-entered decision
> is truthful.**

The architecture instead provides:

1.  Authenticated actor
2.  Authorization
3.  Guarded state transition
4.  Persistent history
5.  Audit visibility
6.  Correction/reversal

The objective is:

> **Accountability, detectability and recoverability.**

Do not build fake reconciliation mechanisms for external systems that do
not exist.

------------------------------------------------------------------------

# 15. Security --- Zero Trust

Never trust:

-   Browser state
-   Hidden UI controls
-   Client-supplied role information
-   Client-side validation
-   User-provided ownership claims
-   Unvalidated file metadata
-   External input

Authorization must be enforced server-side.

## Authentication

Use the approved JWT authentication architecture.

Never expose secrets.

Never hardcode:

-   Passwords
-   API keys
-   JWT secrets
-   Database credentials
-   Encryption keys
-   Cloud credentials

Use environment/configuration or an approved secrets-management
mechanism.

------------------------------------------------------------------------

# 16. Authorization

Use role and scope-aware authorization.

The frontend may hide controls, but the backend must independently
enforce permissions.

Examples of intended scope:

``` text
System Admin
    → system configuration + visibility
    → no direct live student editing

Register
    → student-section administrative visibility/actions

HOD
    → department-scoped authority

Class Teacher
    → assigned batch/class scope

Teacher
    → assigned subject/batch scope

Accountant
    → finance scope

Student
    → own permitted information/actions
```

Do not give a role more authority simply because implementation is
easier.

Least privilege is mandatory.

------------------------------------------------------------------------

# 17. Sensitive Data

Sensitive data includes information such as:

-   Aadhaar
-   Bank details
-   Sensitive personal information
-   Sensitive documents

## Default

Return masked/last-four information where appropriate.

Full values must not be returned by ordinary APIs by default.

## Explicit reveal

A full sensitive value may only be exposed through an explicit
authorized reveal action.

Conceptually:

``` text
Authorized User
      ↓
Permission Check
      ↓
Explicit Reveal
      ↓
Decrypt
      ↓
Temporary Access
      ↓
Audit Event
```

Every reveal is itself an audit event.

Sensitive values must never appear in:

-   Logs
-   Debug output
-   Exception messages
-   Analytics payloads
-   Unnecessary API responses
-   Screenshots/test fixtures committed to the repository

Retention period is an institutional/compliance decision. Do not invent
a retention period.

------------------------------------------------------------------------

# 18. File Upload Security

Treat every uploaded file as untrusted.

Validate, as appropriate:

-   File type
-   MIME type
-   Size
-   Extension
-   Storage destination
-   Ownership
-   Access permission

Do not trust a filename or browser-provided MIME type alone.

Do not execute uploaded files.

Do not expose object-storage credentials to the frontend.

Use secure storage references/presigned mechanisms where appropriate.

------------------------------------------------------------------------

# 19. API Rules

All APIs must:

-   Validate input
-   Enforce authentication where required
-   Enforce authorization
-   Return consistent errors
-   Avoid leaking internal exceptions
-   Paginate list results
-   Enforce maximum page sizes
-   Avoid unbounded responses
-   Use appropriate HTTP semantics
-   Avoid exposing internal database structure

## Pagination

All potentially large list endpoints must be paginated.

Use cursor-based pagination where scale/query patterns justify it;
otherwise use bounded offset pagination.

Never return an unbounded collection.

------------------------------------------------------------------------

# 20. Idempotency

Idempotency must be applied **where the operation can safely be retried
and duplicate execution could cause harm**.

Do not mechanically add idempotency to every endpoint without
understanding the operation.

High-value examples:

### Import processing

Retrying the same logical import must not create duplicate students.

### Financial operations

Do not create duplicate payment effects from repeated identical
operations.

### Result publication

Repeated publication requests must not create duplicate effects.

### Background jobs

Workers should safely handle repeated delivery where applicable.

If an operation cannot safely be made idempotent, explicitly reason
about its retry semantics before implementation.

------------------------------------------------------------------------

# 21. Concurrency

Assume concurrent requests can happen.

Pay special attention to:

-   Payment state
-   Result publication
-   Verification transitions
-   Student corrections
-   Import deduplication
-   Role/permission changes
-   Other shared mutable state

Use:

-   Database transactions
-   Appropriate locking
-   Optimistic locking where suitable
-   Pessimistic locking where necessary
-   Database constraints

Do not assume frontend sequencing prevents race conditions.

------------------------------------------------------------------------

# 22. State Machines

When a domain concept has meaningful lifecycle states, model the
transitions explicitly.

Do not replace workflow state with scattered booleans.

Examples:

### Verification

``` text
PENDING
  ├── APPROVED
  ├── REJECTED
  └── NEEDS_CORRECTION
```

### Import

``` text
UPLOADED
   ↓
VALIDATING
   ↓
VALIDATED
   ↓
IMPORTING
   ↓
COMPLETED

Possible failure states:
FAILED
PARTIALLY_COMPLETED
CANCELLED
```

### Results

``` text
DRAFT
  ↓
PROCESSING
  ↓
VALIDATED
  ↓
APPROVED
  ↓
PUBLISHED
```

### Student lifecycle

Use controlled lifecycle transitions and preserve historical enrollment
information.

Every state transition must have an explicit reason when the business
process requires one.

------------------------------------------------------------------------

# 23. Financial Rules

Finance is a ledger-oriented domain.

Never implement payment status as the sole truth:

``` text
paid = true
```

Instead, preserve payment history.

## Payment rules

-   Payment entries are append-only.
-   Every payment has an accountable actor.
-   Every payment has a timestamp.
-   A payment cannot simply be edited to rewrite history.
-   Corrections use reversal/correction entries.
-   Attempting to mark an already-paid charge as paid must be rejected.
-   Do not add external reconciliation logic unless an actual external
    payment system is introduced later.

------------------------------------------------------------------------

# 24. Result Rules

Published results are immutable historical records.

A correction:

``` text
Published Result V1
        ↓
Correction
        ↓
Approval
        ↓
Result V2
        ↓
V1 becomes SUPERSEDED
```

Mandatory correction reason.

Mandatory accountable actor.

Mandatory audit event.

Never silently modify published academic outcomes.

------------------------------------------------------------------------

# 25. SOLID & Design Principles

Apply SOLID practically.

## Single Responsibility

Do not create giant services that handle:

-   Import
-   Student updates
-   Documents
-   Fees
-   Results
-   Eligibility

Separate responsibilities by bounded context and use case.

## Open/Closed

Use extensible policies/strategies where new business variants are
expected.

Especially:

-   Eligibility rules
-   Fee rules
-   Import source adapters
-   Service-request types

## Liskov Substitution

Avoid artificial subtype hierarchies.

Permanent, Visiting and Contract faculty should remain compatible
representations of the faculty concept unless business behavior
genuinely differs.

## Interface Segregation

Do not create one giant interface for all roles.

Accountant, Register, HOD, Teacher, Student and System Admin require
different capabilities.

## Dependency Inversion

High-level business logic should depend on abstractions at external
boundaries.

Examples:

``` text
Import Domain
     ↑
Source Adapter
     ↑
Excel / future API / future CSV
```

and:

``` text
Reporting
     ↓
Query Contract
     ↓
Owning Module
```

------------------------------------------------------------------------

# 26. Deep Modules Principle

Prefer **fewer meaningful modules with substantial internal
responsibility** over many shallow wrappers.

A module should have:

-   A clear business responsibility
-   A small public interface
-   Significant private logic
-   Clear data ownership
-   Controlled dependencies

Do not create a new module merely because a table or service exists.

Ask:

> "Does this represent a meaningful business boundary?"

If not, keep it within the appropriate existing module.

------------------------------------------------------------------------

# 27. React Architecture Rules

The frontend must respect backend domain boundaries.

Do not reproduce business rules independently in React when the backend
is authoritative.

Frontend responsibilities include:

-   Presentation
-   Form interaction
-   User experience
-   Client-side validation for usability
-   Server-state handling
-   Loading/error states
-   Accessibility
-   Routing
-   Appropriate local/client state

The backend remains authoritative for:

-   Authorization
-   Business validation
-   State transitions
-   Financial rules
-   Eligibility
-   Official record changes

Do not rely on `useMemo`, `useCallback`, or memoization blindly.
Optimize after identifying actual performance needs.

Use lazy loading/code splitting for appropriately large application
areas.

Use error boundaries around meaningful UI failure boundaries.

------------------------------------------------------------------------

# 28. Error Handling

Never swallow exceptions silently.

Bad:

``` text
try:
    ...
except:
    pass
```

Do not do this.

Errors should be:

-   Handled intentionally
-   Logged when appropriate
-   Converted to safe API responses
-   Propagated when the current layer cannot handle them

Do not expose:

-   Stack traces
-   SQL errors
-   Internal paths
-   Secrets
-   Infrastructure details

to end users.

Distinguish between:

-   Expected business errors
-   Validation errors
-   Authorization errors
-   Not found
-   Conflict/state errors
-   Infrastructure failures
-   Unexpected programming defects

------------------------------------------------------------------------

# 29. Resilience

Assume failure is inevitable.

Possible failures include:

-   Database timeouts
-   Lock contention
-   Network failure
-   Storage failure
-   Worker failure
-   External-service failure
-   Process restart
-   Duplicate job execution

Use appropriate patterns where justified:

-   Timeouts
-   Retry with exponential backoff and jitter
-   Idempotent operations
-   Queue-based processing
-   Dead-letter handling
-   Graceful degradation
-   Circuit breakers for genuine external-service dependencies

Do **not** add circuit breakers to internal code simply because the
pattern exists.

A pattern must solve a real failure mode.

------------------------------------------------------------------------

# 30. Background Jobs

Long-running work should not block normal request processing.

Candidates include:

-   Large imports
-   PDF generation
-   Large exports
-   Bulk processing
-   Notifications
-   Other demonstrably expensive asynchronous operations

Background jobs must be:

-   Retry-aware
-   Idempotent where appropriate
-   Observable
-   Bounded
-   Safe under duplicate execution

Do not silently turn every operation into an asynchronous job.

------------------------------------------------------------------------

# 31. Observability

Production software must be diagnosable.

Use structured logging where appropriate.

Logs should provide enough context to understand:

-   What happened
-   Where it happened
-   Which operation was involved
-   Which request/job was involved
-   Which actor was involved where appropriate

Never log sensitive values.

Do not log:

-   Passwords
-   JWT secrets
-   Full Aadhaar numbers
-   Full bank accounts
-   Sensitive document contents
-   Authentication tokens

Where the infrastructure supports it, use correlation/request IDs and
appropriate tracing/metrics.

Observability should be introduced according to actual deployment needs,
but important production paths must be diagnosable.

------------------------------------------------------------------------

# 32. Performance Rules

Always consider:

-   Query count
-   Query complexity
-   Index usage
-   N+1 queries
-   Pagination
-   Serialization cost
-   Memory usage
-   File size
-   Cache behavior
-   Background processing

Avoid:

-   Loading entire tables into memory
-   Unbounded API responses
-   Unbounded exports
-   Per-row database queries in large loops
-   Unbounded caches
-   Repeated expensive calculations

Use `select_related`/`prefetch_related` appropriately.

Measure expensive queries with appropriate PostgreSQL tooling rather
than guessing.

------------------------------------------------------------------------

# 33. Caching

Caching is an optimization, not a source of truth.

Do not cache mutable authoritative business data without an explicit
invalidation strategy.

Before adding a cache, answer:

1.  Why is the query too expensive?
2.  How often does the data change?
3.  What is the invalidation strategy?
4.  What happens when the cache is unavailable?
5.  What is the memory/cost impact?

Prefer correctness over premature caching.

------------------------------------------------------------------------

# 34. Database Migrations

Database schema evolution must be safe.

Rules:

-   Never casually destroy production data.
-   Avoid destructive migrations when a staged migration can achieve the
    same result.
-   Preserve backward compatibility during multi-step deployments where
    necessary.
-   Consider existing data before adding constraints.
-   Do not rewrite large production tables blindly.
-   Test migrations against realistic data volumes.
-   Have a rollback/recovery strategy appropriate to the migration.

A migration is not merely "code that makes the development database
work."

------------------------------------------------------------------------

# 35. Testing Contract

Testing is part of implementation, not an optional final step.

## Unit tests

Required for:

-   Business rules
-   State transitions
-   Eligibility logic
-   Financial calculations/rules
-   Validation logic
-   Important domain policies
-   Complex transformations

## Integration tests

Required for:

-   Database interactions
-   Repository/query behavior
-   Important transaction behavior
-   Module boundaries
-   Authentication/authorization paths
-   External adapters where applicable

## End-to-End tests

Use for critical workflows such as:

``` text
Login
Student onboarding
Government import
Verification
Document workflow
Fee recording
Result workflow
Student service request
```

Do not chase coverage percentages blindly.

Prioritize critical business paths and boundary conditions.

------------------------------------------------------------------------

# 36. Test Boundary Enforcement

Tests must verify architectural boundaries where they matter.

Examples:

-   API cannot bypass authorization.
-   One module cannot directly mutate another module's owned data.
-   Published results cannot be silently overwritten.
-   Payment history cannot be edited destructively.
-   Government source values remain preserved.
-   Conflicting import identifiers do not auto-merge.
-   Unauthorized users cannot reveal sensitive data.
-   Students cannot modify protected administrative fields directly.

------------------------------------------------------------------------

# 37. AI Agent Workflow

Every feature implementation must follow this sequence.

## Step 1 --- Analyze

Read:

-   `AGENT.md`
-   `ARCHITECTURE.md`
-   Relevant PRD
-   Existing implementation
-   Relevant tests
-   Relevant domain interfaces

Do not start editing immediately.

------------------------------------------------------------------------

## Step 2 --- Identify Ownership

Before modifying anything, answer:

``` text
Which bounded context owns this behavior?
Which module owns the data?
Which layer should contain the logic?
Which existing interfaces should be reused?
```

------------------------------------------------------------------------

## Step 3 --- Check Dependencies

Determine:

-   Existing dependency direction
-   Whether a new dependency is necessary
-   Whether it creates a cycle
-   Whether the public interface can remain small

If the feature requires crossing an ownership boundary, use the approved
interface.

------------------------------------------------------------------------

## Step 4 --- Plan

Produce a concise implementation plan containing:

-   What changes
-   Why
-   Which areas are affected
-   Important edge cases
-   Tests required
-   Security considerations
-   Data/migration considerations

Do not create unnecessary files or abstractions.

------------------------------------------------------------------------

## Step 5 --- Implement

Implement the smallest correct change that satisfies the approved
requirements.

Do not refactor unrelated code unless required for correctness or
explicitly approved.

Do not "improve" unrelated architecture while implementing a feature.

------------------------------------------------------------------------

## Step 6 --- Test

Write/update tests before considering the feature complete.

Test:

-   Happy path
-   Validation failures
-   Authorization failures
-   Boundary conditions
-   Duplicate requests where relevant
-   Concurrent state changes where relevant
-   Historical/correction behavior
-   Important database constraints

------------------------------------------------------------------------

## Step 7 --- Review

Before reporting completion, perform a self-review:

### Architecture

-   Did I respect the module boundary?
-   Did I create coupling?
-   Did I introduce a circular dependency?
-   Did I bypass an existing interface?

### Security

-   Can an unauthorized user invoke this?
-   Is sensitive data exposed?
-   Is user input trusted?
-   Are secrets protected?

### Data integrity

-   Can duplicate records be created?
-   Can history be destroyed?
-   Can an invalid state be persisted?
-   Are transactions correct?

### Performance

-   Is there an N+1 query?
-   Is any query unbounded?
-   Is pagination present?
-   Is memory usage bounded?

### Reliability

-   What happens on retry?
-   What happens if the operation fails halfway?
-   What happens if two requests happen simultaneously?

### Testing

-   Are critical rules tested?
-   Are negative cases tested?
-   Are authorization cases tested?

------------------------------------------------------------------------

# 38. Ambiguity Rule

If requirements are unclear, **do not guess**.

Stop and ask.

Examples of architecture-level ambiguity:

-   Who owns a field?
-   Whether a correction is destructive or additive
-   Whether a field requires verification
-   Whether a role can perform a sensitive action
-   Whether a historical record can be changed
-   Whether a new concept belongs to an existing module
-   Whether an external integration actually exists
-   Whether a new dependency is permitted

Do not resolve these by choosing whichever implementation is easiest.

------------------------------------------------------------------------

# 39. Scope Discipline

Do not add features because they are common in student/college ERP
systems.

If the user asks:

> "Build student import"

do not automatically add:

-   Timetable
-   Hostel
-   Library
-   Attendance
-   Payments gateway
-   University examination registration
-   Messaging platform
-   Payroll

unless explicitly requested.

A feature request is not permission to expand product scope.

------------------------------------------------------------------------

# 40. Anti-Patterns --- Explicitly Forbidden

Never introduce:

-   God objects
-   God modules
-   Giant services
-   Giant serializers
-   Business logic in views
-   Business logic in serializers
-   Direct cross-module database access
-   Polymorphic foreign keys for critical ownership
-   Duplicate sources of truth
-   Mutable published history
-   Mutable payment history
-   Hardcoded eligibility logic
-   Hardcoded secrets
-   Silent exception swallowing
-   Unbounded list APIs
-   N+1 query patterns
-   Frontend-only authorization
-   Premature microservices
-   Premature Kafka
-   Premature CQRS
-   Premature event sourcing
-   Premature sharding
-   Premature Kubernetes
-   Architecture invented for hypothetical scale without evidence

------------------------------------------------------------------------

# 41. Definition of Done

A feature is not complete merely because it works manually.

It is complete when:

-   Requirements are satisfied.
-   Correct module owns the behavior.
-   Data ownership is respected.
-   Authorization is enforced.
-   Input is validated.
-   Business rules are tested.
-   Important failure cases are handled.
-   Historical integrity is preserved.
-   Sensitive information is protected.
-   Queries are bounded and reasonable.
-   N+1 problems are avoided.
-   Required migrations are safe.
-   Relevant audit events exist.
-   Idempotency/retry behavior is considered where applicable.
-   Relevant tests pass.
-   No unrelated architecture has been changed.
-   The implementation has been self-reviewed.

------------------------------------------------------------------------

# 42. Final Agent Principle

When choosing between two implementations:

Prefer the one that is:

``` text
More correct
    ↓
More explicit
    ↓
More secure
    ↓
More observable
    ↓
More testable
    ↓
Less coupled
    ↓
Less destructive
    ↓
Simpler
```

Do not confuse complexity with production quality.

The goal is not to build the most sophisticated system possible.

The goal is to build a system that can remain correct as it grows.

> **Build deliberately. Preserve history. Respect ownership. Assume
> failure. Verify permissions. Test business rules. Never guess about
> architecture.**
