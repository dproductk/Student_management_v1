# PRD: Credits & Eligibility

## 1. Problem

The system must convert published academic results into earned credits and use those credits, together with configurable institutional eligibility rules, to determine whether a student is **ELIGIBLE**, **NOT\_ELIGIBLE**, or **DETAINED**.

Eligibility must not be implemented as hardcoded application logic. The architecture requires configurable eligibility rules and requires each eligibility decision to retain the rule/version used to produce it.

The resulting eligibility information is also used to generate the list for next-year admission.

---

## 2. Goal

Provide a production-grade Credits & Eligibility capability that:

- Calculates credits from published results.
- Preserves historical credit calculations.
- Allows eligibility rules to be configured.
- Calculates eligibility using the configured rules.
- Records the exact rule/version used for each eligibility decision.
- Produces explicit eligibility states.
- Supports detention determination.
- Generates the next-year eligibility list.
- Preserves historical eligibility decisions.
- Prevents historical decisions from being silently changed.
- Provides the required foundation for reporting.

---

## 3. User Stories

### Credit Calculation

- As an authorized academic user, I want credits calculated from published results so that student academic progress can be determined.
- As an administrator, I want historical credit calculations preserved so that previous academic decisions remain explainable.

### Eligibility Rules

- As an authorized user, I want eligibility rules to be configurable so that institutional requirements are not hardcoded into the application.
- As an authorized user, I want each eligibility decision to identify the rule/version used so that the decision can be explained historically.

### Eligibility Decision

- As an authorized academic user, I want students classified as eligible, not eligible, or detained based on the configured rules.
- As an authorized user, I want detention checked as part of the eligibility process.

### Next-Year Admission

- As an authorized academic user, I want a next-year eligibility list generated from the resulting eligibility decisions.

### Historical Integrity

- As an auditor, I want previous credit and eligibility decisions preserved so that historical academic decisions remain traceable.

---

# 4. Scope — Files/Modules Touched

### Primary bounded context

**Results & Eligibility**

This context owns:

- Credits.
- Eligibility.
- Eligibility rules.
- Eligibility decisions.
- Result publication dependency.
- Next-year eligibility determination.

The architecture explicitly assigns credits and eligibility to Results & Eligibility.

### Dependencies

- **Results**
  - Published results provide the source for credit calculation.
- **Academic Foundation**
  - Provides established academic structure used by eligibility rules.
- **Student Management**
  - Provides authoritative student enrollment and enrollment-status history.
- **Identity**
  - Provides authentication and authorization.
- **Reporting**
  - Consumes the Results & Eligibility query interface.

### Exact task scope

The implementation task graph defines these tasks:

1. Result-to-credit calculation.
2. Historical credit calculation integrity.
3. Configurable eligibility-rule definition.
4. Eligibility calculation and rule-version recording.
5. Eligible/not-eligible/detained decision.
6. Next-year eligibility list generation.
7. Eligibility decision history and correction integrity tests.

All are **HUMAN REVIEW REQUIRED**.

---

# 5. Requirements

## 5.1 Credit Calculation

### R-001 — Result-to-Credit Calculation

The system shall calculate credits from published results.

The calculation shall consume authoritative Results data rather than creating another result source.

The defined flow is:

**Result → Credits → Eligibility Calculation → Detention Check.**

### R-002 — Published Result Dependency

Credit calculation shall depend on the published-result workflow.

The task graph explicitly makes **Result publication and student view** a dependency for result-to-credit calculation.

### R-003 — Historical Credit Integrity

Previously calculated credits must remain historically explainable.

Changes to later result versions must not silently rewrite historical credit decisions that were derived from earlier published results.

### R-004 — Result Version Awareness

The credit calculation implementation shall respect the Results module's versioned historical model.

Published result corrections create a new result version rather than modifying the previous published result.

---

## 5.2 Eligibility Rule Definition

### R-005 — Configurable Rules

Eligibility shall be driven by configurable rules rather than hardcoded Python/application logic.

The architecture explicitly identifies possible rule inputs including:

- Minimum Attendance.
- Minimum Credits.
- Maximum Backlogs.

These are examples identified by the architecture; they do **not** constitute a finalized institutional policy.

### R-006 — Rule Definition

The system shall provide a rule-definition capability within Results & Eligibility.

Rules shall be represented as configurable data rather than requiring source-code modification for each institutional rule change.

### R-007 — Rule Version

Eligibility rules shall be versioned sufficiently to identify which rule definition was applied to a particular decision.

### R-008 — Historical Rule Preservation

A rule version used by an existing eligibility decision shall remain identifiable so that the historical decision can be explained.

---

## 5.3 Eligibility Calculation

### R-009 — Eligibility Calculation

The system shall calculate eligibility using:

**Published Result → Credits → Configured Eligibility Rules → Eligibility Decision.**

### R-010 — Rule-Version Recording

Each eligibility calculation/decision shall retain the rule/version used for the calculation.

This is an explicit architectural requirement.

### R-011 — Detention Check

The eligibility workflow shall include a detention check before producing the final eligibility outcome.

### R-012 — Explicit Decision States

The system shall represent eligibility using the defined states:

- **ELIGIBLE**
- **NOT\_ELIGIBLE**
- **DETAINED**

The architecture explicitly defines these eligibility states.

---

## 5.4 Next-Year Eligibility

### R-013 — Next-Year Eligibility List

The system shall generate a list for next-year admission based on the resulting eligibility decisions.

The defined flow is:

**Eligible / Not Eligible / Detained → Generate List for Next-Year Admission.**

### R-014 — Enrollment Context

Next-year eligibility shall use the authoritative historical enrollment and enrollment-status information from Student Management.

The task graph explicitly makes **Historical enrollment and enrollment-status** a dependency for next-year eligibility list generation.

### R-015 — No Duplicate Enrollment Authority

Results & Eligibility shall not create a competing source of truth for student enrollment or enrollment status.

---

## 5.5 Historical Decision Integrity

### R-016 — Decision History

Eligibility decisions shall retain historical records sufficient to determine:

- The student.
- The decision.
- The applicable rule/version.

Additional historical fields shall only be introduced where supported by the finalized design.

### R-017 — Historical Decisions

Previous eligibility decisions shall not be silently overwritten when later academic information or rule versions change.

### R-018 — Correction Integrity

The system shall test that historical credit and eligibility information remains internally consistent when result versions or eligibility rules change.

The task graph explicitly includes **Eligibility decision history and correction integrity tests**.

---

## 5.6 Authorization & Accountability

### R-019 — Backend Authorization

Protected credit and eligibility configuration operations shall require backend authorization.

### R-020 — Accountable Actor

Important administrative eligibility actions shall be attributable to an authenticated actor.

The architecture's general accountability pattern requires:

**Actor + Action + Target + Timestamp + Reason where applicable.**

### R-021 — Audit

Relevant eligibility-rule changes and important eligibility operations shall produce appropriate audit information.

---

# 6. Data Changes

The Results & Eligibility context requires data structures representing:

- Credit calculations.
- Eligibility rule definitions.
- Eligibility rule versions.
- Eligibility calculations/decisions.
- Eligibility decision states.
- Historical eligibility decisions.
- Next-year eligibility results/list membership where required by the finalized design.

### Ownership

**Results & Eligibility owns:**

- Credits.
- Eligibility rules.
- Eligibility calculations.
- Eligibility decisions.
- Next-year eligibility determination.

**Results owns:**

- Official result records and publication.

**Student Management owns:**

- Student identity.
- Enrollment.
- Enrollment history/status.

**Academic Foundation owns:**

- Academic structure.

No downstream module may duplicate ownership of these facts.

### Historical integrity

Historical credit and eligibility decisions must remain explainable using the relevant result and rule versions.

### Schema intentionally not finalized

The supplied architecture does not define:

- Exact credit table names.
- Exact eligibility-rule table structure.
- Exact eligibility-rule version schema.
- Exact decision schema.
- Exact next-year-list schema.
- Exact database constraints/indexes.
- Exact representation of individual rule parameters.

These must be finalized during database design.

---

# 7. API Changes

The module will require API operations corresponding to the defined workflows, including:

- Credit calculation.
- Credit/history viewing where applicable.
- Eligibility-rule configuration.
- Rule-version management.
- Eligibility calculation.
- Eligibility decision viewing.
- Next-year eligibility list generation/viewing.
- Historical eligibility decision access.

The API layer shall handle:

- Authentication extraction.
- Input validation.
- Authorization.
- Serialization.
- HTTP status handling.
- Pagination and bounded responses where applicable.
- Safe error responses.

The application/domain layer shall own:

- Credit calculation.
- Rule evaluation.
- Eligibility state transitions.
- Rule-version association.
- Historical integrity.

### API details intentionally open

The architecture does not define:

- Exact routes.
- HTTP methods.
- Request/response schemas.
- Permission names.
- Pagination contracts.
- Rule-management UI/API details.
- Exact next-year-list response structure.

These must not be invented in this PRD.

---

# 8. Security Notes

### Authentication

All protected eligibility configuration and administrative operations require authenticated users.

### Authorization

Authorization must be enforced by the backend and application layer.

### Rule configuration

Only authorized users may create or modify eligibility-rule definitions.

### Historical protection

Existing decisions must not be silently rewritten when rules are changed.

### Audit

Rule changes and important eligibility actions must be attributable to accountable actors.

### Sensitive student information

Eligibility operations must not unnecessarily expose sensitive student information. Normal APIs should expose only information required for the operation.

---

# 9. Definition of Done

-  Result-to-credit calculation implemented.
-  Credit calculation uses authoritative published results.
-  Historical credit calculation integrity implemented and tested.
-  Configurable eligibility-rule definition implemented.
-  Eligibility rules are not hardcoded into application logic.
-  Eligibility rule versions are preserved.
-  Eligibility calculation implemented.
-  Eligibility decisions record the rule/version used.
-  Detention check implemented.
-  ELIGIBLE state implemented.
-  NOT\_ELIGIBLE state implemented.
-  DETAINED state implemented.
-  Next-year eligibility list generation implemented.
-  Historical enrollment/status is obtained from Student Management.
-  Eligibility decision history preserved.
-  Correction/historical-integrity tests implemented.
-  Backend authentication and authorization enforced.
-  Important administrative actions are attributable to accountable actors.
-  Relevant audit records implemented.
-  Queries are bounded and avoid N+1 behavior.
-  Database migrations are safe.
-  Unit tests cover credit calculations and eligibility rules.
-  Integration tests cover database/state/history behavior.
-  End-to-end eligibility flow tested.
-  **Human review completed for every Credits & Eligibility task.**

---

# 10. Out of Scope

- Inventing the institution's actual eligibility policy.
- Hardcoding minimum attendance requirements.
- Hardcoding minimum-credit requirements.
- Hardcoding maximum-backlog requirements.
- Inventing additional eligibility criteria.
- Building a separate eligibility bounded context.
- Creating a second student enrollment source.
- Creating a second result source.
- Direct access to internal tables owned by other modules.
- Full university examination-management functionality.
- University-level examination rules not defined in the architecture.
- Advanced analytics beyond the Results & Eligibility capability.

The architecture explicitly states that the **complete institutional eligibility policy is TBD and needs the PRD**, so this document does not invent the actual policy.

---

# 11. Open Questions

1. **Exact eligibility policy**
   - What institutional rules determine eligibility?
2. **Attendance**
   - Is attendance actually a required input?
   - If so, what attendance source/module provides it?
3. **Minimum credits**
   - What minimum-credit thresholds apply?
   - Do thresholds vary by academic context?
4. **Maximum backlogs**
   - What backlog definition and thresholds apply?
5. **Detention policy**
   - What exact conditions produce `DETAINED` rather than `NOT_ELIGIBLE`?
6. **Rule applicability**
   - Which academic contexts use which eligibility-rule versions?
7. **Rule authority**
   - Which role(s) may create, activate, replace, or retire eligibility rules?
8. **Rule effective dates**
   - How are rule versions associated with academic years/semesters?
9. **Credit calculation policy**
   - The architecture requires result-to-credit calculation but does not define the complete institutional calculation rules.
10. **Correction behavior**
    - When a published result is corrected, exactly how and when should previously calculated credits and eligibility decisions be recalculated or superseded?
11. **Next-year list semantics**
    - Exactly which students should appear in the generated list and what fields must the list contain?

These must be resolved before implementation wherever they affect irreversible business rules. The architecture explicitly requires the system to stop and ask rather than guess when business rules, ownership, historical behavior, or role authority are unclear.

---

# 12. Dependencies

### Upstream

1. **Results**
   - Result publication.
   - Published result data.
2. **Academic Foundation**
   - Academic structure.
3. **Student Management**
   - Student identity.
   - Historical enrollment.
   - Enrollment status.
4. **Identity & Access**
   - Authentication.
   - Authorization.

### Downstream

1. **Reporting & Analytics**
   - Results and eligibility reporting interface.
2. **Next-Year Admission/administrative workflows**
   - Consumes the generated eligibility list where applicable.

### Exact implementation dependency order

**Published Results → Result-to-Credit Calculation → Historical Credit Integrity → Eligibility Rule Definition → Eligibility Calculation + Rule Version → Eligibility Decision → Next-Year Eligibility List → Eligibility History/Correction Integrity.**

This follows the task graph exactly.
