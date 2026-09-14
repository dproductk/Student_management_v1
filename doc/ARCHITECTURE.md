<!-- Page 1 -->

Software Architecture
Architecture Finalization — Updated Sections
Architecture Finalization — Updated Sections
1. Finalized Architectural Decisions
System Admin Boundary
The System Admin is the software/system-management authority operated by the development/system team. The
System Admin may manage users, roles and permissions, master data, system settings, system-wide information,
and audit activity. The System Admin must not directly edit live student records. Student-data corrections, including
corrections initiated by an Admin, must pass through the appropriate Student Management + Verification workflow
and must be auditable.
System Admin
     I
     I configuration / visibility
     M
System
Student correction
     I
     M
Student Management
     I
     M
Verification
     I
     M
Approved correction
     I
     M
Student Record
This preserves separation between system administration and business-data administration.
2. Government Data Authority & Correction Model
Government-provided data is treated as an immutable source record. The original value is never overwritten. The
system distinguishes source history from current authoritative business value. A correction is additive rather than
destructive.
Applies particularly to Application ID, Enrollment number, Board/university enrollment number, Name, Date of birth,
Category, Admission information, and other official source fields.
Government Source Value
        I
        I preserved permanently
        M
Original Value
        I
        IIIIIIII Correction
                    I
                    III New authoritative value
                    III Approver
                    III Reason
                    III Timestamp
                    III Audit record
3. Student Identity Matching
Government imports use deterministic matching precedence:
1. Application ID
2. Enrollment No.

---

<!-- Page 2 -->

3. Board / University Enrollment No.
No match → create a new student.
Single valid match → associate the import row with the matched student.
Conflicting matches must not automatically merge records. They go to CONFLICT → MANUAL REVIEW → Explicit resolution.
4. Student Account Provisioning
Initial policy:
Username = Enrollment Number
Initial Password = Enrollment Number
First Login → Mandatory Password Change
This is a changeable authentication policy, not an immutable architectural assumption. The Identity module owns
implementation, allowing future OTP-based activation or invitation-based onboarding without redesigning Student
Management.
5. Fee Authority — Final Model
There is no external payment system that this application must reconcile against. The Finance module's charges and
payment records are the sole source of truth for fee status. There is no reconciliation/dispute architecture.
Fee Structure → Applicable Fee → Charge → Payment Ledger Entry
A payment is an append-only financial event, not a mutable paid flag.
UNPAID → Accountant records payment → PAID
Attempting to mark an already-paid charge as paid again is rejected. A mistaken payment is corrected by a
reversal/correction entry, not edited or deleted. Every payment records accountable actor, timestamp, relevant
charge, payment information, and audit information.
6. General Correction/Reversal Pattern
Corrections are additive, never destructive. This is a system-wide architectural principle.
Original Record
      I
      I preserved
      M
Correction / Replacement / Reversal
      I
      III Actor
      III Timestamp
      III Reason
      III Reference to original
      III Audit record
Government data: original government value + corrected value + reason/approver.
Fees: original payment + reversal/correction entry.
Results: Published Result V1 → SUPERSEDED BY → Result V2.
Documents: Document V1 → SUPERSEDED → Document V2.
Verification: previous decisions are not silently rewritten; new state transitions or correction actions record the new decis
Never destroy evidence of what previously happened.
7. Trust Model
For several workflows there is no external system of record that independently validates whether a human action was
correct, including fee payments, verification, document approval, result submission/approval, and authorized
administrative corrections.
The architecture cannot guarantee that every human-entered decision is truthful. Instead it provides:
1. Accountable actor
2. Auditability
3. Reversibility
Human Action

---

<!-- Page 3 -->

↓
Authenticated Actor
     ↓
Authorized Operation
     ↓
Guarded State Transition
     ↓
Persistent History
     ↓
Audit Visibility
     ↓
Correction / Reversal if necessary
The goal is accountability, detectability and recoverability.
8. Accountable Actor Pattern
Sensitive actions must identify the responsible actor.
Student Management — Controlled correction
Verification — Approve / reject / request correction
Documents — Approve / reject / reset / replace
Finance — Record payment / reversal
Results — Approve / publish / correct
Identity — Role/permission changes
Services — Approve/reject service requests
Minimum conceptual information:
Actor + Action + Target + Timestamp + Reason where applicable.
This is a reusable architectural pattern, not something reinvented separately by every module.
9. Verification ↔ Student Management Boundary
Student Management owns the actual student information.
Verification owns the decision about whether submitted/corrected information is approved for official use.
Student Data
     L
     I
Verification Decision
     L
     I
Verification Workflow
Verification does not become a second student database.
Information that affects the official student record and requires administrative confirmation must pass through
verification before becoming accepted. Examples: student-submitted personal information, corrected
government-sourced information, sensitive financial identity information where institutional verification is required, and
student-submitted academic documents.
The exact field-by-field verification matrix remains a business-policy decision.
Submission, acceptance, and official-record status are distinct concepts. A student upload may be stored as
SUBMITTED while approval determines whether it becomes the official/current value.
10. Documents & Sensitive Data — Reveal Pattern
Sensitive information includes Aadhaar, bank details, and sensitive personal information.
Default behavior: only masked information is normally exposed.

---

<!-- Page 4 -->

Aadhaar: XXXX XXXX 1234
Bank Account: 1234
Explicit reveal requires:
Authorized User → Explicit Reveal Action → Permission Check → Sensitive Data Decryption → Temporary Display → Audit Event
Every reveal records actor, sensitive resource, reveal action, timestamp, and context/reason where applicable.
A normal student-detail API must not automatically return full sensitive values. Default: masked unless explicitly and
legitimately revealed.
Sensitive-data retention duration is an institutional/compliance decision, not an engineering default.
11. Results — Final Correction Model
A published result is immutable historical evidence.
Published Result V1
        I
        I correction request
        M
Correction Review
        I
        I APPROVE
        M
Result V2
        I
        III SUPERSEDES V1
The original remains accessible as history. Correction requires authorized actor, mandatory reason, approval,
timestamp, and audit record. Published results must never be silently updated in place.
12. Reporting Read Boundary — Final Decision
Reporting is not permitted to directly access another module's tables as its normal architectural interface.
Reporting → Module-owned read interface → Authoritative module data
Examples:
Reporting → Student Management query interface → Student data
Reporting → Finance query interface → Fee data
Reporting → Results query interface → Academic data
This preserves source-of-truth boundaries. Reporting should not depend on internal tables because those are
implementation details.
Performance exception: if reporting volume eventually makes live interfaces too expensive, purpose-built read
projections/materialized reporting data may be introduced. Such projections are derived read data, never a source of
truth. The decision must be based on actual query/load evidence. Initially, module-owned query interfaces are the
default.
13. SOLID Updates
Single Responsibility: do not create one generic CorrectionService that understands every domain. Each bounded
context owns its domain-specific correction behavior.
Finance → Financial Reversal
Results → Result Supersession
Student Management → Data Correction
Documents → Document Replacement
Open/Closed: accountability should accommodate new sensitive actions without rewriting the audit architecture.
Eligibility rules remain strategies rather than one giant function.
Dependency Inversion: Reporting depends on query contracts, not persistence internals. Import processing depends
on an external-data-source abstraction rather than direct coupling to Excel.
14. Updated Cross-Cutting Concern Matrix

---

<!-- Page 5 -->

Authentication — Identity
Authorization — Identity + application policy
Input validation — API + Domain
Business validation — Domain
Transactions — Application layer
Idempotency — Application layer / owning module
Rate limiting — API/security boundary
Audit logging — Audit
Accountable actor — Owning module + Audit
Sensitive-data reveal — Sensitive-data/document boundary
Correction/reversal pattern — Cross-cutting architectural rule + owning module
Error handling — Application/API boundary
Reporting reads — Reporting through module-owned query interfaces
Observability — Platform/operations capability
15. Updated Dependency Map
No bounded-context dependency changes are required.
IIIIIIIIIIIIIIIIIII
I Identity & I
I Access I
IIIIIIIIIIIIIIIIIII
I
IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII
M M M
Student Management Verification Faculty
L I I
I M I
Onboarding Documents I
I I
IIIIIIIIIIIIIIII IIIIIIIIIIIIIIII
M M
Academic Foundation
I
M
Results & Eligibility
I
IIIIIIIIIIIIIIIIIIIIIIIIIIIIII
M M

---

<!-- Page 6 -->

Finance Reporting
I I
IIIIIIIIIIIIIIIIIIIIIIIIIIIIII
M
Audit
The changes are behavioral and contractual, not new domains.
No new bounded context is required.
No module needs to be split.
No existing module needs to merge.
No circular dependency is introduced.
Reporting remains downstream/read-oriented.
Audit remains a supporting cross-cutting capability.
Correction/reversal is a shared architectural pattern, not a new business module.
Creating a separate Correction Module would make the architecture worse because correction semantics belong to
the domain whose data is being corrected.
16. Final Open Questions
Only two areas remain explicitly open before implementation.
A. Verification Policy Matrix
The exact answer is still needed for which individual student fields/documents require verification before becoming
official, and which are immediately usable after submission.
Example policy matrix:
Photo — Student — Yes — TBD — TBD
Signature — Student — Yes — TBD — TBD
Aadhaar — Student — Yes — TBD — TBD
Bank details — Student — Yes — TBD — TBD
Address — Student — Yes — TBD — TBD
HSC information — Government/Student — Yes — TBD — TBD
Government correction — Staff — No — Yes — TBD
These approval rules should not be invented because they are institutional policy rather than software architecture.
B. Sensitive-data retention
Retention duration for Aadhaar, bank information, and sensitive documents remains a compliance/institutional
decision rather than an engineering default.
Final Confirmation
The architecture is substantially stronger because the most important trust and historical-integrity decisions are
locked:
Immutable source history → controlled correction → accountable actor → guarded state transition → audit trail → reversibl
These improvements do not require changing the bounded-context map or dependency graph; they make existing
modules more disciplined internally rather than adding architectural complexity.

---

<!-- Page 7 -->

The architectural objective remains: a simple modular monolith that is difficult to corrupt accidentally, easy for humans
to understand, and constrained enough that an AI coding agent cannot casually cross domain boundaries.
