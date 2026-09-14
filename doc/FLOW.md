<!-- Page 1 -->

FLOW.md
Student Management & Administrative Data
System
System and Module Flow Reference
0. Purpose
This document describes how requests and data move through the Student Management & Administrative
Data System.
It exists so that a human developer or AI coding agent can understand the system's flow and module
boundaries before modifying or implementing a feature.
This document does NOT define new business rules.
It translates the finalized architecture and accepted architectural decisions into operational flow diagrams.
When this document conflicts with the architecture:
ARCHITECTURE.md
    ↓
Feature PRD / Approved Requirements
    ↓
AGENTS.md
    ↓
FLOW.md
If a required behavior is not defined by the architecture or an approved PRD:
TBD — needs PRD
Do not invent business rules.
1

---

<!-- Page 2 -->

1. System-Level Request Flow
The system is a modular monolith.
A request does not cross directly between database tables or persistence implementations of different
modules.
The standard request path is:
React Frontend
      |
      v
API Boundary
      |
      v
Authentication / Authorization
      |
      v
Application Layer
      |
      v
Domain Layer
      |
      v
Persistence / Adapter
      |
      v
PostgreSQL
      |
      v
Persistence / Adapter
      |
      v
Domain
      |
      v
Application
      |
      v
API Boundary
      |
      v
React Frontend
2

---

<!-- Page 3 -->

1.1 Request Responsibilities
React Frontend
Responsible for:
- Presenting UI
- Collecting user input
- Sending requests
- Displaying responses
- Displaying only information permitted by the backend
The frontend is NOT the authority for:
- Authentication
- Authorization
- Business rules
- Data ownership
- State transitions
API Boundary
Responsible for:
- HTTP handling
- Authentication extraction
- Request/response serialization
- Input boundary validation
- HTTP status codes
- Rate limiting/security boundary where applicable
Application Layer
Responsible for:
- Use cases
- Orchestration
- Transactions
- Authorization policy coordination
- Idempotency
- Calling domain services
3

---

<!-- Page 4 -->

Domain Layer
Responsible for:
- Business invariants
- Business validation
- State transitions
- Domain-specific rules
- Domain-specific correction/reversal behavior
Persistence / Adapter
Responsible for:
- Persistence implementation
- Repository/data-access concerns
- Adapting the domain/application requirements to PostgreSQL or other
infrastructure
PostgreSQL
Stores authoritative persisted data owned by the respective module.
The database is not a substitute for domain ownership.
A module must not bypass another module's ownership by directly accessing its internal persistence
implementation.
1.2 Cross-Module Request Boundary
When a feature requires another bounded context:
Module A
|
v
Application Interface
|
v
Domain Service / Explicit Contract / Query Interface
|
v
Module B
4

---

<!-- Page 5 -->

|
v
Module B Application / Domain
|
v
Module B Persistence
|
v
PostgreSQL
Never:
Module A
|
v
Module B Database Table
X
Never:
Module A Repository
|
v
Module B Repository
X
Cross-module communication must use application interfaces, domain services, query interfaces, or explicit
contracts.
2. System-Wide Accountability Flow
Important business operations follow the general trust model:
Human Action
|
v
Authenticated Actor
|
v
Authorized Operation
|
v
5

---

<!-- Page 6 -->

Guarded State Transition
|
v
Persistent History
|
v
Audit Visibility
|
v
Correction / Reversal if necessary
The system does not assume that every human action is automatically truthful.
Instead, it provides:
Accountability
Auditability
Reversibility
Important actions conceptually record:
Actor
Action
Target
Timestamp
Reason (where applicable)
This pattern applies to sensitive operations across Student Management, Verification, Documents, Finance,
Results, Identity, and Services.
3. Per-Module Flows
The following flows cover the ten primary bounded contexts plus the two supporting capabilities.
3.1 Identity & Access
Responsibility
Identity owns:
6

---

<!-- Page 7 -->

- Authentication
- Users
- Roles
- Permissions
- JWT
- Account provisioning policy
Authentication Flow
User
  |
  v
Login Request
  |
  v
API Boundary
  |
  v
Identity
  |
  v
Authenticate User
  |
  v
Issue JWT
  |
  v
Authenticated Request
  |
  v
Application Layer
  |
  v
Authorized Operation
Authentication belongs to Identity.
Authorization is enforced by the backend together with application policy.
Initial Student Account Provisioning
Student Created
      |
      v
7

---

<!-- Page 8 -->

Identity Account Provisioning
      |
      v
Username = Enrollment Number
      |
      v
Initial Password = Enrollment Number
      |
      v
Student First Login
      |
      v
Mandatory Password Change
The initial provisioning policy is changeable.
Identity owns its implementation.
Future activation mechanisms must not require redesigning Student Management.
3.2 Academic Foundation
Responsibility
Academic Foundation owns:
- Departments
- Programs
- Academic Years
- Semesters
- Batches
- Schemes
- Subjects
- Scheme Subjects
- Academic structure
Academic Structure Flow
Academic Configuration
      |
      v
Department
8

---

<!-- Page 9 -->

|
      v
Program
      |
      v
Academic Year
      |
      v
Semester
      |
      v
Batch
      |
      v
Scheme
      |
      v
Scheme Subject
A Subject is a reusable identity.
A Scheme Subject represents that subject under a specific scheme and carries the relevant scheme-specific
academic definition.
Historical Scheme Flow
Existing Scheme
      |
      v
Student Enrollment
      |
      v
Historical Scheme Relationship
      |
      v
Future Scheme Introduced
      |
      v
Existing Historical Relationship Remains Intact
Historical scheme definitions must not be changed in a way that changes historical results.
9

---

<!-- Page 10 -->

3.3 Student Management
Responsibility
Student Management owns:
- Canonical student identity
- Admissions
- Enrollments
- Addresses
- Categories
- Bank accounts
- Student business information
Student Record Flow
Accepted Student Information
|
v
Student Management
|
+----> Student Identity
|
+----> Admission Information
|
+----> Address Information
|
+----> Category Information
|
+----> Bank Information
|
+----> Enrollment
|
v
Official Student Record
Student Management is the authoritative owner of actual student information.
Verification does not become a second student database.
10

---

<!-- Page 11 -->

Enrollment Flow
Student
  |
  v
Student Enrollment
  |
  +---- Academic Year
  +---- Semester
  +---- Department
  +---- Program
  +---- Batch
  +---- Scheme
  +---- Status
  |
  v
Authoritative Enrollment State
Enrollment is the authoritative source for academic enrollment state.
Do NOT use a mutable convenience field such as:
students.current_semester
as an independent source of truth.
Student Correction Flow
Correction Required
      |
      v
Student Management
      |
      v
Correction Workflow
      |
      v
Verification
      |
      v
Approved Correction
      |
11

---

<!-- Page 12 -->

v
Student Record
The original historical value is preserved.
Corrections are additive rather than destructive.
3.4 Onboarding
Responsibility
Onboarding owns:
- Import lifecycle
- Staging
- Validation
- Normalization
- Deduplication
- Matching
- Import execution
Government Excel Import Flow
Government Excel
|
v
Upload
|
v
Import Batch
|
v
Staging Rows
|
v
Validation
|
v
Normalization
|
v
Deduplication
12

---

<!-- Page 13 -->

|
v
Identity Matching
|
+-----------------------------+
|
|
| No Match
| Single Valid Match
v
v
Create Student
Associate Import
|
with Student
+-------------+---------------+
|
v
Production Records
Government Excel must never be imported directly into production tables.
Import States
UPLOADED
    |
    v
VALIDATING
    |
    v
VALIDATED
    |
    v
IMPORTING
    |
    v
COMPLETED
Failure paths may produce:
FAILED
PARTIALLY_COMPLETED
CANCELLED
Identity Matching Flow
Matching precedence:
13

---

<!-- Page 14 -->

Application ID
     |
     v
Enrollment Number
     |
     v
Board / University Enrollment Number
Possible outcomes:
No Match
    |
    v
Create New Student
Single Valid Match
    |
    v
Associate Import Row
with Existing Student
Conflicting Matches
    |
    v
CONFLICT
    |
    v
MANUAL REVIEW
    |
    v
Explicit Resolution
Conflicting records must never be automatically merged.
Import Idempotency
Source Data
    |
    v
Import Attempt
    |
    v
14

---

<!-- Page 15 -->

Existing Identity Check
    |
    v
Deterministic Matching
    |
    v
Prevent Duplicate Student Creation
Re-uploading the same source data must not create duplicate students.
3.5 Verification
Responsibility
Verification owns:
- Verification workflow
- Verification decisions
- Correction requests
- Verification history
Verification owns the DECISION.
Student Management owns the actual student data.
Verification Flow
Submitted Information
      |
      v
Verification
      |
      +-------------------+
      |         |         |
      v         v         v
   APPROVED  REJECTED  NEEDS_CORRECTION
For information affecting the official student record:
Submission
|
15

---

<!-- Page 16 -->

v
Verification
|
v
Approval
|
v
Accepted for Official Use
The exact field-by-field verification policy is:
TBD — needs PRD
The architecture explicitly leaves the exact verification matrix as a business-policy decision.
Verification Correction Flow
Existing Submission
      |
      v
Verification Review
      |
      v
NEEDS_CORRECTION
      |
      v
Correction Request
      |
      v
Corrected Submission
      |
      v
Verification
      |
      v
APPROVED / REJECTED / NEEDS_CORRECTION
Previous verification decisions are not silently rewritten.
New decisions or correction actions create new history.
16

---

<!-- Page 17 -->

3.6 Documents
Responsibility
Documents owns:
- Document metadata
- Document versions
- Storage references
- Document lifecycle
Actual files are stored outside PostgreSQL.
PostgreSQL stores document metadata and storage references.
Document Upload Flow
Student / Authorized User
|
v
Document Upload
|
v
Document Storage
|
v
Document Metadata
|
v
Verification where required
|
v
Document Status
Possible document examples include:
- Student Photo
- Signature
- Aadhaar
- SSC Result
- HSC Result
- Bank-related Document
- Allotment Letter
17

---

<!-- Page 18 -->

- Other Required Certificates
- Service-request Documents
The exact verification requirement for each document:
TBD — needs PRD
Document Replacement Flow
Existing Document V1
      |
      v
Replacement / Reset
      |
      v
New Document V2
      |
      v
V1 = SUPERSEDED
V2 = CURRENT
Documents must not be silently overwritten.
Historical versions remain explainable.
Sensitive Document Reveal Flow
Authorized User
      |
      v
Explicit Reveal Action
      |
      v
Permission Check
      |
      v
Sensitive Data Decryption
      |
      v
Temporary Display
      |
18

---

<!-- Page 19 -->

v
Audit Event
Sensitive information is masked by default.
Normal student-detail APIs must not automatically return full sensitive values.
3.7 Faculty
Responsibility
Faculty owns:
- Faculty records
- Teaching assignments
- Subject assignments
- Batch assignments
Faculty Assignment Flow
Faculty
   |
   v
Assignment
   |
   +---- Scheme Subject
   +---- Academic Year
   +---- Semester
   +---- Batch
   |
   v
Teaching Assignment
Teaching assignments are historical.
Subjects taught must not be stored as comma-separated values.
19

---

<!-- Page 20 -->

Unit Test Marks Flow
Teacher
|
v
Upload Unit Test Marks
|
v
System Extracts Data
|
v
Validate
|
v
Store Marks
|
v
Student Views Marks
The assessment architecture is extensible.
It must not be hardcoded exclusively around Unit Tests.
Result Excel Initiation
Teacher / Class Teacher
      |
      v
Result Excel
      |
      v
Results & Eligibility Module
The detailed result processing flow is defined under Results & Eligibility.
3.8 Finance
Responsibility
Finance owns:
20

---

<!-- Page 21 -->

- Fee Heads
- Fee Structures
- Charges
- Payments
- Financial History
Finance is the sole source of truth for fee status.
Fee Configuration Flow
System Admin
      |
      v
Configure Default Fee Structure
      |
      v
Fee Structure
      |
      v
Fee Structure Items / Fee Heads
Applicable fee structures may depend on configured criteria such as:
- Student Category
- Admission Category
- Program
- Academic context
The exact applicability rules are:
TBD — needs PRD
Student Fee Flow
Fee Structure
      |
      v
Applicable Fee
      |
      v
Student Fee Charge
21

---

<!-- Page 22 -->

|
      v
Accountant Views Student
      |
      v
Accountant Records Payment
      |
      v
Payment Ledger Entry
Fee status is derived from the Finance records.
A payment is an append-only financial event.
Payment Flow (ADR-025 — QR + partial payments)
UNPAID
   |
   v
Student pays externally via University Portal QR -> receipt + UTR
   |
   v
Accountant verifies receipt/UTR -> Records Payment (receipt_no UNIQUE)
   |
   v
Payment Ledger Entry
   |
   v
PARTIALLY_PAID (if balance remains) / PAID (if fully covered)
Charge states: UNPAID/PARTIALLY_PAID/PAID/CANCELLED (backend/apps/finance/models.py:22).
Attempting to mark an already-paid charge as paid again is rejected (duplicate receipt_no rejected).
Payment Correction Flow
Original Payment
      |
      v
Reversal / Correction Entry
      |
      v
Financial History Preserved
Payments are not edited or deleted to correct mistakes.
There is no external payment reconciliation flow in the current architecture.
22

---

<!-- Page 23 -->

3.9 Results & Eligibility
Responsibility
Results & Eligibility owns:
- Assessments
- Marks
- Results
- Credits
- Eligibility
- Result publication
Result Import Flow
Result Excel
      |
      v
Result Import Batch
      |
      v
Result Rows
      |
      v
Validation
      |
      v
Result Records
      |
      v
Credit / Eligibility Calculation
      |
      v
Approval
      |
      v
Publication
Result States
DRAFT
  |
23

---

<!-- Page 24 -->

v
PROCESSING
  |
  v
VALIDATED
  |
  v
APPROVED
  |
  v
PUBLISHED
A result may also enter:
REJECTED
Published results are immutable historical evidence.
Published Result Correction
Published Result V1
      |
      v
Correction Request
      |
      v
Correction Review
      |
      v
APPROVED
      |
      v
Result V2
      |
      v
V2 SUPERSEDES V1
V1 remains accessible as historical evidence.
Published results must never be silently updated in place.
24

---

<!-- Page 25 -->

Eligibility Flow
Result
  |
  v
Credits
  |
  v
Eligibility Calculation
  |
  v
Detention Check
  |
  +-----------------------+
  |                       |
  v                       v
ELIGIBLE             NOT_ELIGIBLE
                          |
                          v
                      DETAINED
  |
  v
Generate List for
Next-Year Admission
Eligibility is driven by configurable rules.
The decision records the rule/version used.
The architecture identifies possible rule inputs such as:
- Minimum Attendance
- Minimum Credits
- Maximum Backlogs
The complete institutional eligibility policy:
TBD — needs PRD
25

---

<!-- Page 26 -->

3.10 Student Services
Responsibility
Services owns:
- Student Service Requests
- Service Request Workflow
- Status
- Resolution
Service Request Flow
Student
   |
   v
Submit Service Request
   |
   v
Administrative Staff
   |
   v
Process Request
   |
   v
Approve / Reject
   |
   v
Status
   |
   v
Resolution
Example:
Duplicate ID Card
    |
    v
Student submits request
    |
    v
Administrative Staff
    |
26

---

<!-- Page 27 -->

v
Process
    |
    v
Approve / Reject
    |
    v
Status
The service-request model is intended to be reusable.
The exact service-specific workflows:
TBD — needs PRD
3.11 Reporting
Responsibility
Reporting is read-only.
Reporting owns:
- Read-only analytics
- Reports
- Exports
Reporting does NOT own the business data being reported.
Reporting Read Flow
Reporting Request
|
v
Reporting
|
v
Module-Owned Query Interface
|
v
27

---

<!-- Page 28 -->

Authoritative Module Data
|
v
Reporting Result
Examples:
Reporting
|
+--> Student Management Query Interface
|
|
|
v
|
Student Data
|
+--> Finance Query Interface
|
|
|
v
|
Fee Data
|
+--> Results Query Interface
|
v
Academic Data
Reporting must not directly access another module's internal tables as its normal interface.
Reporting Performance Exception
Initially:
Reporting
|
v
Module-Owned Query Interface
|
v
Authoritative Data
Only if actual query/load evidence demonstrates that live interfaces are insufficient:
Authoritative Module Data
      |
      v
28

---

<!-- Page 29 -->

Purpose-Built Derived Read Projection
      |
      v
Reporting
Such projections remain derived data.
They never become a source of truth.
3.12 Audit
Responsibility
Audit is a supporting cross-cutting capability.
Audit owns:
- Append-only audit records
- Audit visibility
- Cross-cutting audit history
Audit Flow
Sensitive Business Action
      |
      v
Owning Module
      |
      v
Action Recorded
      |
      v
Audit
      |
      v
Append-Only Audit Record
Conceptually:
Actor
  +
29

---

<!-- Page 30 -->

Action
  +
Target
  +
Timestamp
  +
Reason where applicable
      |
      v
Audit Record
Examples include:
- Login
- Student data changes
- Government-data corrections
- Verification actions
- Document uploads
- Document resets
- Fee status changes
- Result uploads
- Result changes
- User/role changes
- Administrative actions
- Sensitive-data reveals
Audit must not unnecessarily contain raw sensitive values.
4. Cross-Module Flows
These are the primary workflows where multiple bounded contexts interact.
4.1 Government Import → Student Creation →
Account Provisioning → Verification
Modules Touched
1. Onboarding
2. Student Management
30

---

<!-- Page 31 -->

3. Identity & Access
4. Verification
Flow
Government Excel
      |
      v
Onboarding
      |
      v
Import Batch
      |
      v
Staging
      |
      v
Validation
      |
      v
Normalization
      |
      v
Deduplication
      |
      v
Deterministic Identity Matching
      |
      +-----------------------------+
      |                             |
      | No Match                    | Existing Match
      v                             v
Student Management            Associate Import
creates Student               with Student
      |                             |
      +-------------+---------------+
                    |
                    v
            Student Management
                    |
                    v
            Related Records
                    |
                    v
            Identity
                    |
31

---

<!-- Page 32 -->

v
            Student Account
                    |
                    v
            Student Login
                    |
                    v
            Student Completes
            Required Information
                    |
                    v
            Verification
                    |
                    v
            Approved / Rejected /
            Needs Correction
The exact verification policy for each submitted field/document remains:
TBD — needs PRD
4.2 Student Document Upload → Verification →
Official Record
Modules Touched
1. Student Management
2. Documents
3. Verification
4. Audit
Flow
Student
|
v
Student Management / Student Context
|
v
Document Upload
32

---

<!-- Page 33 -->

|
v
Documents
|
v
Document Metadata + Storage Reference
|
v
Verification
|
+--------------------+
|
|
|
v
v
v
APPROVED
REJECTED
NEEDS_CORRECTION
|
v
Student Management
|
v
Accepted / Official Current Value
|
v
Audit
Important boundary:
Documents owns document metadata/lifecycle.
Verification owns the verification decision.
Student Management owns actual student information.
The exact field/document verification matrix:
TBD — needs PRD
33

---

<!-- Page 34 -->

4.3 Accountant Records Payment → Finance
Ledger → Audit
Modules Touched
1. Student Management
2. Finance
3. Audit
Flow
Accountant
    |
    v
Student Lookup
    |
    v
Student Management Query
    |
    v
Finance
    |
    v
Applicable Fee / Charge
    |
    v
Payment Recording
    |
    v
Payment Ledger Entry
    |
    v
Fee Status
    |
    v
Audit
Payment:
UNPAID -> PARTIALLY_PAID -> PAID (CANCELLED terminal; backend/apps/finance/models.py:22)
   |
   v
34

---

<!-- Page 35 -->

Payment Recorded (QR receipt + UTR verified, receipt_no UNIQUE)
   |
   v
PARTIALLY_PAID / PAID
Correction:
Original Payment
     |
     v
Finance Reversal / Correction Entry
     |
     v
Audit
Finance remains the authoritative source for fee status.
4.4 Teacher Result Upload → Validation →
Publication → Eligibility
Modules Touched
1. Faculty
2. Results & Eligibility
3. Academic Foundation
4. Student Management
5. Reporting
6. Audit
Flow
Teacher / Class Teacher
      |
      v
Result Excel
      |
      v
Results & Eligibility
      |
      v
35

---

<!-- Page 36 -->

Result Import Batch
      |
      v
Result Rows
      |
      v
Validation
      |
      v
Structured Result Records
      |
      v
Credit Calculation
      |
      v
Eligibility Calculation
      |
      v
Approval
      |
      v
Publication
      |
      v
Student Result Available
      |
      v
Reports / Reporting
Eligibility follows:
Result
   |
   v
Credits
   |
   v
Eligibility Calculation
   |
   v
Detention Check
   |
   v
Eligible / Not Eligible / Detained
Audit records relevant accountable actions.
36

---

<!-- Page 37 -->

4.5 Verification Rejection → Correction → Re-
Submission
Modules Touched
1. Student Management
2. Documents where applicable
3. Verification
4. Audit
Flow
Submitted Information
      |
      v
Verification
      |
      v
REJECTED / NEEDS_CORRECTION
      |
      v
Correction Request
      |
      v
Student / Authorized User
      |
      v
Corrected Information
      |
      v
Re-Submission
      |
      v
Verification
      |
      +----------------------+
      |                      |
      v                      v
  APPROVED              REJECTED /
                         NEEDS_CORRECTION
      |
      v
37

---

<!-- Page 38 -->

Student Management
/ Official Use
      |
      v
    Audit
Previous decisions remain historical records.
They are not silently rewritten.
4.6 Published Result Correction → Supersession
Modules Touched
1. Results & Eligibility
2. Verification / correction workflow where applicable
3. Audit
4. Reporting
5. Student Management where applicable
Flow
Published Result V1
      |
      v
Correction Request
      |
      v
Correction Review
      |
      v
Authorized Approval
      |
      v
Result V2
      |
      v
V2 SUPERSEDES V1
      |
      +--------------------+
      |                    |
      v                    v
38

---

<!-- Page 39 -->

Historical V1          Current V2
      |                    |
      v                    v
   Reporting          Student View
      |
      v
    Audit
V1 is never silently overwritten.
5. Cross-Module Boundary Rules
Rule 1 — One Owner
Every important business fact has one authoritative owner.
Examples:
Student Identity       → Student Management
Role                   → Identity
Subject                → Academic Foundation
Fee Charge             → Finance
Payment                → Finance
Verification Decision  → Verification
Result                 → Results & Eligibility
Document Metadata      → Documents
Other modules may reference authoritative data.
They must not duplicate ownership.
Rule 2 — Verification Does Not Own Student Data
Correct:
Student Management
      |
      | student information
      v
Student Data
39

---

<!-- Page 40 -->

Verification
      |
      | approval decision
      v
Verification Decision
Incorrect:
Verification
      |
      v
Second Student Database
Rule 3 — Reporting Does Not Own Source Data
Correct:
Reporting
|
v
Module Query Interface
|
v
Authoritative Module
Incorrect:
Reporting
   |
   v
Direct Access to Module Tables
Rule 4 — Corrections Belong to the Owning Domain
There is no Correction Module.
Instead:
40

---

<!-- Page 41 -->

Student Management → Data Correction
Finance → Financial Reversal
Results → Result Supersession
Documents → Document Replacement
Corrections follow a common architectural pattern but remain owned by the domain being corrected.
Rule 5 — Historical Truth Is Preserved
Never:
Original
   |
   v
Overwrite
   X
Instead:
Original
|
+------------------> Historical Record
|
v
Correction / Replacement / Reversal
|
v
New Authoritative State
Rule 6 — Sensitive Data Is Masked
Default:
Sensitive Data
     |
41

---

<!-- Page 42 -->

v
Masked
Explicit authorized access:
Authorized User
     |
     v
Explicit Reveal
     |
     v
Permission Check
     |
     v
Decryption
     |
     v
Temporary Display
     |
     v
Audit
Rule 7 — No Direct Cross-Module Persistence Access
Never:
Module A
|
v
Module B Repository
X
Never:
Module A
|
v
Module B Table
X
Use:
42

---

<!-- Page 43 -->

Module A
|
v
Application Interface /
Domain Service /
Query Interface /
Explicit Contract
|
v
Module B
6. Global State and History Pattern
The system favors explicit state machines over scattered boolean flags.
Generic state transition:
Current State
     |
     v
Authorized Action
     |
     v
Valid State Transition
     |
     v
New State
     |
     v
Persistent History
     |
     v
Audit
Examples:
Verification:
PENDING
|
+--> APPROVED
|
43

---

<!-- Page 44 -->

+--> REJECTED
|
+--> NEEDS_CORRECTION
Import:
UPLOADED
  |
  v
VALIDATING
  |
  v
VALIDATED
  |
  v
IMPORTING
  |
  v
COMPLETED
Result:
DRAFT
  |
  v
PROCESSING
  |
  v
VALIDATED
  |
  v
APPROVED
  |
  v
PUBLISHED
Fee:
UNPAID
  |
  v
Payment Recorded
  |
44

---

<!-- Page 45 -->

v
PAID
Correction/reversal does not erase the previous state or event.
7. Quick Lookup — "Where Does X Go?"
Feature Request
Applicable Flow
Owning Module
Add a new fee head
Finance → Fee
Configuration Flow
Finance
Change a fee structure
Finance → Fee
Configuration Flow
Finance
Mark a student's fee as paid
Accountant → Finance
Ledger Flow
Finance
Correct a mistaken payment
Finance → Payment
Correction Flow
Finance
Add a new document type
Documents → Document
Upload Flow
Documents
Replace an incorrect document
Documents → Document
Replacement Flow
Documents
Verify a student document
Document Upload →
Verification Flow
Verification owns decision;
Documents owns document
Change a student's official
information
Student Correction Flow
Student Management
Approve a student-data
correction
Student Correction Flow
Verification owns decision
Import government student
data
Government Import Flow
Onboarding
Resolve duplicate/conflicting
import matches
Identity Matching Flow
Onboarding
Create a student from
government data
Government Import →
Student Creation
Student Management
Create a student's login
Account Provisioning Flow
Identity & Access
Change student login/
authentication policy
Account Provisioning /
Authentication Flow
Identity & Access
45

---

<!-- Page 46 -->

Feature Request
Applicable Flow
Owning Module
Add a department
Academic Structure Flow
Academic Foundation
Add a program
Academic Structure Flow
Academic Foundation
Add a batch
Academic Structure Flow
Academic Foundation
Add a subject
Academic Structure Flow
Academic Foundation
Create a scheme subject
Academic Structure Flow
Academic Foundation
Assign faculty to a subject/batch
Faculty Assignment Flow
Faculty
Upload Unit Test marks
Unit Test Marks Flow
Faculty / Results & Eligibility as
applicable
Upload result Excel
Result Import Flow
Results & Eligibility
Correct a published result
Published Result Correction
Flow
Results & Eligibility
Calculate credits
Result → Credits →
Eligibility Flow
Results & Eligibility
Determine next-year eligibility
Eligibility Flow
Results & Eligibility
Create a student service request
Service Request Flow
Services
Approve/reject a service request
Service Request Flow
Services
Generate a report
Reporting Read Flow
Reporting
Export report data
Reporting Read Flow
Reporting
View audit history
Audit Flow
Audit
Reveal Aadhaar/bank
information
Sensitive Data Reveal Flow
Owning sensitive-data boundary +
Identity authorization + Audit
Add a new role
Identity & Access Flow
Identity & Access
Add/change permissions
Identity & Access Flow
Identity & Access
Allow System Admin to directly
edit student records
No valid flow
Not permitted by architecture
Create a Correction Module
No valid flow
Not permitted by architecture
Make Reporting directly query
module tables
No valid flow
Not permitted by architecture
Add Division in v1
No valid flow
Deferred
Build university payment
reconciliation
No valid flow
Out of current architecture
46

---

<!-- Page 47 -->

Feature Request
Applicable Flow
Owning Module
Build full university examination
management
No valid flow
Out of current scope
Define which exact student
fields require verification
Verification Flow
TBD — needs PRD
Define exact document-by-
document verification rules
Verification Flow
TBD — needs PRD
Define sensitive-data retention
period
Sensitive Data Flow
TBD — institutional/compliance
decision
Define exact eligibility policy
Eligibility Flow
TBD — needs PRD
8. Feature Implementation Decision Path
Before implementing a feature, follow this sequence:
Feature Request
|
v
Identify the User / Actor
|
v
Identify the Bounded Context
|
v
Identify the Data Owner
|
v
Identify the Existing Flow
|
v
Identify Cross-Module Dependencies
|
v
Identify Required State Transition
|
v
Identify Historical Requirements
|
v
Identify Authorization Boundary
|
47

---

<!-- Page 48 -->

v
Identify Audit Requirement
|
v
Identify Failure / Retry / Idempotency Requirements
|
v
Check for Existing Entity / Workflow
|
v
Implement Within Existing Boundary
If ownership, business rules, correction behavior, role authority, historical behavior, or external integration
is unclear:
STOP
|
v
Ask for clarification / PRD
|
v
Do not guess
9. Architecture-Level End-to-End View
The overall system can be understood as:
SYSTEM ADMIN
|
v
System Configuration
|
v
Government Student Data
|
v
ONBOARDING
|
v
Student Management
|
+----------------------+
|
|
48

---

<!-- Page 49 -->

v
v
Identity
Student Information
|
|
v
v
Student Login
DOCUMENTS
|
v
VERIFICATION
|
v
Official Student Data
|
+-----------------+------------------+
|
|
|
v
v
v
FINANCE
FACULTY
SERVICES
|
|
|
v
v
v
Fee Status
Assessments
Requests
|
v
RESULTS & ELIGIBILITY
|
v
Credits
|
v
Eligibility
|
v
Next-Year Status
|
v
REPORTING
Across all important operations:
Authenticated Actor
      |
      v
Authorized Operation
      |
      v
Guarded State Transition
      |
      v
49

---

<!-- Page 50 -->

Persistent History
      |
      v
AUDIT
The architecture remains:
Modular Monolith
|
+--> Identity & Access
+--> Academic Foundation
+--> Student Management
+--> Onboarding
+--> Verification
+--> Documents
+--> Faculty
+--> Finance
+--> Results & Eligibility
+--> Services
|
+--> Reporting
|
+--> Audit
No new bounded context is introduced by these flows.
No module is split or merged merely to implement these workflows.
No separate Correction Module exists.
No module may become a second source of truth.
10. Final Rule
Before touching code, an agent must be able to answer:
What flow am I modifying?
Which module owns it?
Which data does that module own?
Which other modules must be consulted?
What interface crosses the boundary?
What state transition occurs?
What historical record must remain?
50

---

<!-- Page 51 -->

Who is accountable for the action?
What must be audited?
What happens if the operation is retried or fails?
If these answers cannot be established from:
ARCHITECTURE.md
DECISIONS.md
AGENTS.md
Approved Feature PRD
then:
STOP
ASK
DO NOT GUESS
51
