# PRD: Reporting & Analytics

## 1. Problem

The system needs a read-only reporting and analytics capability that can present information from the authoritative bounded contexts without creating duplicate ownership of business data.

Reporting must consume data through module-owned query interfaces rather than directly depending on internal database tables.

---

# 2. Goal

Provide a production-grade Reporting & Analytics capability that:

- Provides standardized read-only query contracts.
- Retrieves authoritative data from owning modules.
- Provides administrative reports and exports.
- Provides student-population analytics.
- Provides academic, result, eligibility, verification, and fee-status analytics.
- Supports filtering, sorting, pagination, and bounded result sets.
- Preserves source-of-truth boundaries.
- Does not modify operational business data.
- Allows purpose-built derived projections only when actual performance evidence requires them.

---

# 3. User Stories

### Reporting

- As an authorized administrative user, I want to retrieve student information for reporting purposes.
- As an authorized user, I want to filter and sort report data so that I can analyze the required population.
- As an authorized user, I want to export report data.
- As an authorized user, I want to view fee-status information for reporting.
- As an authorized user, I want to view academic, result, and eligibility information for reporting.
- As an administrator, I want reporting to use authoritative data rather than duplicated reporting tables.

### Analytics

- As an authorized user, I want to analyze student populations.
- As an authorized user, I want department/program/batch/category/gender analytics.
- As an authorized user, I want verification analytics.
- As an authorized user, I want fee-status analytics.
- As an authorized user, I want academic/result/eligibility analytics.
- As an authorized user, I want administrative/user-activity analytics.

---

# 4. Scope — Files/Modules Touched

## Primary bounded context

**Reporting**

Reporting owns:

- Read-only analytics.
- Reports.
- Exports.

Reporting does **not** own the business data being reported.

## Query boundaries

Reporting shall consume:

- Student Management query interfaces for student data.
- Academic Foundation query interfaces for academic data.
- Finance query interfaces for fee data.
- Results & Eligibility query interfaces for results/eligibility data.
- Identity/Audit interfaces for relevant user/activity information.

The architecture explicitly defines:

**Reporting → Module-Owned Query Interface → Authoritative Module Data.**

## Exact task scope

### Reporting Boundary

1. Reporting query-contract foundation.
2. Student Management reporting interface.
3. Finance reporting interface.
4. Results and eligibility reporting interface.

### Analytics

5. Student population analytics.
6. Department/program/batch/category/gender analytics.
7. Verification analytics.
8. Fee-status analytics.
9. Academic/result/eligibility analytics.
10. Administrative/user-activity analytics.

### Export & Performance

11. Reporting filtering, sorting, pagination, and export.

These are the defined Reporting task areas, with the task graph marking them **HUMAN REVIEW REQUIRED**.

---

# 5. Requirements

## 5.1 Reporting Query Boundary

### R-001 — Query Contract Foundation

The Reporting module shall provide a query-contract foundation through which reporting requests obtain data from authoritative modules.

### R-002 — No Direct Table Access

Reporting shall not directly access another module's internal tables as its normal interface.

The authoritative pattern is:

**Reporting → Module-Owned Query Interface → Authoritative Module Data.**

### R-003 — Read-Only

Reporting shall be read-only with respect to operational business data.

A reporting operation shall not modify student, finance, academic, result, verification, or other authoritative records.

### R-004 — Source Ownership

Reporting shall not become a second source of truth for any business fact.

---

## 5.2 Student Reporting

### R-005 — Student Management Reporting Interface

Student Management shall expose an approved query interface for reporting purposes.

### R-006 — Student Population Analytics

Reporting shall support student-population analytics.

### R-007 — Academic Population Analytics

Reporting shall support analytics involving the defined academic dimensions:

- Department.
- Program.
- Batch.
- Category.
- Gender.

The exact metrics and visualizations are not specified in the source documents and shall not be invented.

---

## 5.3 Verification Analytics

### R-008 — Verification Reporting Interface

Reporting shall consume verification information through an approved query boundary rather than accessing Verification's internal tables.

### R-009 — Verification Analytics

Reporting shall support verification analytics.

The exact metrics, filters, and breakdowns are not finalized by the architecture.

---

## 5.4 Finance Reporting

### R-010 — Finance Reporting Interface

Finance shall provide the query interface required by Reporting.

### R-011 — Fee-Status Analytics

Reporting shall support fee-status analytics using Finance's authoritative data.

Finance remains the sole source of truth for fee status.

### R-012 — No Finance Mutation

Reporting operations shall not modify charges, payments, reversals, or financial history.

---

## 5.5 Results & Eligibility Reporting

### R-013 — Results Query Interface

Results & Eligibility shall provide the query interface required for reporting.

### R-014 — Academic/Result/Eligibility Analytics

Reporting shall support academic, result, and eligibility analytics.

### R-015 — Historical Results

Reporting shall respect the historical result model.

Published results remain immutable, and corrected results create new versions that supersede previous versions.

### R-016 — Eligibility History

Reporting shall obtain eligibility information through the Results & Eligibility query boundary and shall not independently calculate or alter eligibility.

---

## 5.6 Administrative/User Activity Analytics

### R-017 — User Activity Analytics

Reporting shall support administrative/user-activity analytics based on the approved Identity/Audit reporting interfaces.

### R-018 — Audit Boundary

Reporting shall not modify audit history.

Audit remains a supporting cross-cutting capability.

---

## 5.7 Filtering, Sorting & Pagination

### R-019 — Filtering

Reporting shall support filtering appropriate to each report/query.

### R-020 — Sorting

Reporting shall support sorting where applicable.

### R-021 — Pagination

Large result sets shall be paginated.

### R-022 — Bounded Queries

Reporting queries shall remain bounded and shall not expose unbounded database operations to users.

### R-023 — Maximum Result Size

Report endpoints shall enforce appropriate maximum result sizes.

Exact limits are not specified in the source architecture and therefore remain an implementation decision.

---

## 5.8 Export

### R-024 — Report Export

Reporting shall support export of report data.

### R-025 — Export Authorization

Export operations shall be subject to the same applicable authorization requirements as the underlying report.

### R-026 — Bounded Export

Exports shall be bounded and must not permit uncontrolled extraction of arbitrarily large datasets.

The exact export formats and limits are not defined by the architecture.

---

## 5.9 Performance

### R-027 — Initial Query Strategy

Reporting shall initially use module-owned query interfaces.

### R-028 — Performance Evidence

A derived reporting projection may only be introduced when actual query/load evidence demonstrates that live module-owned query interfaces are insufficient.

### R-029 — Derived Data

If a derived reporting projection is introduced, it shall remain derived data and shall never become the authoritative source of business information.

---

# 6. Data Changes

Reporting does **not** become the owner of operational business data.

The Reporting capability may require:

- Query contracts/interfaces.
- Report-specific configuration where required.
- Derived read projections only when justified by measured performance evidence.

### Authoritative ownership remains:

- Student data → Student Management.
- Academic data → Academic Foundation.
- Verification decisions → Verification.
- Fee data → Finance.
- Results/eligibility → Results & Eligibility.
- User/permission information → Identity.
- Audit history → Audit.

Reporting must consume these through approved query interfaces.

### Schema intentionally not finalized

The source documents do not define:

- Reporting table schemas.
- Projection schemas.
- Exact materialized-view strategy.
- Exact report configuration model.
- Exact indexes.

No reporting database structure should be invented before actual query requirements and performance evidence justify it.

---

# 7. API Changes

The Reporting module will require APIs for:

- Report/query contracts.
- Student reports.
- Verification analytics.
- Fee-status reports.
- Results/eligibility reports.
- Population analytics.
- Academic analytics.
- Administrative/user-activity analytics.
- Filtering.
- Sorting.
- Pagination.
- Export.

The API layer shall handle:

- Authentication extraction.
- Authorization.
- Request validation.
- Serialization.
- Pagination.
- Bounded responses.
- Safe error handling.

Business ownership and calculations remain with the authoritative modules.

### API details intentionally open

The supplied architecture does not define:

- Exact routes.
- HTTP methods.
- Exact report parameters.
- Exact response schemas.
- Export formats.
- Export size limits.
- Exact report permissions.

These must be finalized separately without guessing.

---

# 8. Security Notes

### Authentication

All protected reporting operations shall require authenticated users.

### Authorization

The backend shall enforce authorization for reports, analytics, and exports.

### Data minimization

Reports should expose only the information required for the authorized reporting operation.

### Cross-module access

Reporting must use approved query interfaces rather than bypassing module boundaries.

### Export protection

Export must be treated as a potentially high-impact data operation and must respect authorization and bounded-output requirements.

### Sensitive information

Sensitive student information must not automatically become available through reporting merely because it exists in an authoritative module.

### Audit

Important administrative/reporting actions shall be auditable where required by the established audit model.

---

# 9. Definition of Done

-  Reporting query-contract foundation implemented.
-  Student Management reporting interface implemented.
-  Finance reporting interface implemented.
-  Results and eligibility reporting interface implemented.
-  Student population analytics implemented.
-  Department/program/batch/category/gender analytics implemented.
-  Verification analytics implemented.
-  Fee-status analytics implemented.
-  Academic/result/eligibility analytics implemented.
-  Administrative/user-activity analytics implemented.
-  Filtering implemented.
-  Sorting implemented.
-  Pagination implemented.
-  Export implemented.
-  Reporting remains read-only.
-  Reporting does not directly query another module's internal tables.
-  Backend authentication and authorization enforced.
-  Large queries/results are bounded.
-  Sensitive information is appropriately protected.
-  Historical result/eligibility data is represented through authoritative query interfaces.
-  Automated tests cover query contracts and authorization.
-  Integration tests cover module boundaries.
-  Export authorization and bounded-output behavior tested.
-  Performance is validated against actual query patterns.
-  Any derived projection is justified by measured performance evidence.
-  **Human review completed for every Reporting task.**

---

# 10. Out of Scope

- Owning student, academic, finance, verification, result, or identity data.
- Direct access to another module's internal database tables.
- Modifying authoritative business data through reports.
- Creating a second source of truth.
- Premature data warehouse infrastructure.
- Premature CQRS/event-sourcing architecture.
- Derived projections without actual performance evidence.
- Inventing institutional reporting metrics not defined by requirements.
- Inventing report-specific business rules.
- Unbounded exports.
- A new Reporting-related bounded context.

The architecture explicitly rejects direct reporting access to module tables and permits derived projections only when actual performance evidence demonstrates the need.

---

# 11. Open Questions

1. **Report catalogue**
   - Which exact reports are required in the initial release?
2. **Analytics metrics**
   - What exact metrics should each analytics view calculate?
3. **Report permissions**
   - Which roles may access each report?
4. **Sensitive fields**
   - Which student fields must be masked or excluded from particular reports?
5. **Export formats**
   - Which export formats are required?
6. **Export limits**
   - What maximum row/file size limits should apply?
7. **Filtering**
   - Which filters are required for each report?
8. **Date ranges**
   - Which reports require date-range filtering?
9. **User-activity reporting**
   - Which Identity/Audit events should be included?
10. **Performance thresholds**
    - At what measured query/load level should a derived reporting projection be considered?

These are not defined sufficiently in the architecture and therefore should be finalized as feature requirements rather than guessed.

---

# 12. Dependencies

### Upstream

1. **Student Management**
   - Student reporting query interface.
   - Student population data.
2. **Academic Foundation**
   - Academic query data.
3. **Verification**
   - Verification reporting data.
4. **Finance**
   - Finance reporting interface.
5. **Results & Eligibility**
   - Results and eligibility reporting interface.
6. **Identity & Access**
   - Authentication and authorization.
   - User activity information where applicable.
7. **Audit**
   - Audit information required for administrative activity analytics.

### Downstream

Reporting is primarily a consumer/read capability and does not define a downstream operational bounded context.

### Exact implementation dependency order

**Reporting Query-Contract Foundation → Student Management Interface + Finance Interface + Results/Eligibility Interface → Analytics → Filtering/Sorting/Pagination/Export.**

This follows the task graph's defined Reporting & Analytics dependency structure.
