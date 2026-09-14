## Feature: Register / Administrative Dashboards

### 1. Problem

Administrative users need a read-oriented way to search, filter, review, and export student information across academic and administrative dimensions without creating a second source of truth.

The Register capability must consume authoritative data from Student Management, Academic Foundation, and Verification rather than owning duplicate student or academic records.

---

### 2. Goal

Provide an administrative student register and dashboard capability supporting:

- Student register search and detail
- Department/program/year/batch filtering
- Category/gender/verification views
- Student-status dashboard information
- Export/printable register data

---

### 3. User Stories

- As an authorized administrative user, I want to search and view student records.
- As an authorized administrative user, I want to filter students by department, program, academic year, and batch.
- As an authorized administrative user, I want to view students by category, gender, and verification status.
- As an authorized administrative user, I want a dashboard showing student-status information.
- As an authorized administrative user, I want to export or print filtered register data.

---

### 4. Scope — Files/Modules Touched

The task graph defines these Register vertical slices:

1. **Administrative student register query**
   - Depends on Student search/filter/pagination/detail and Historical enrollment/enrollment-status.
2. **Department/program/year/batch student register filtering**
   - Depends on Administrative student register query and Academic master-data search/filter/detail.
3. **Category/gender/verification administrative register views**
   - Depends on department/program/year/batch filtering and Verification review/approval.
4. **Administrative dashboard student-status**
   - Depends on the administrative register query and category/gender/verification views.
5. **Register export/printable-data**
   - Depends on department/program/year/batch filtering.

All five tasks are marked **HUMAN REVIEW REQUIRED**.

Register is a read-oriented capability; it must not become a new owner of student or academic master data.

---

### 5. Requirements

#### 5.1 Administrative Student Register

1. Provide an administrative student register query.
2. Support student search using the authoritative Student Management query capability.
3. Support pagination and bounded result sets.
4. Display historical enrollment context where required.
5. Student information must come from Student Management rather than duplicated Register data.

#### 5.2 Academic Filtering

6. Support filtering by:
   - Department
   - Program
   - Academic Year
   - Batch
7. Academic filter values must come from Academic Foundation.
8. Register must not create duplicate academic entities.
9. Filtering must respect the authoritative student enrollment relationship.

#### 5.3 Administrative Views

10. Provide administrative views for:

- Category
- Gender
- Verification status

11. Verification status must come from Verification's authoritative decision/workflow data.
12. Register must not become the owner of verification decisions.

#### 5.4 Student Status Dashboard

13. Provide administrative student-status dashboard information.
14. Dashboard information must be derived from authoritative module-owned data.
15. Dashboard queries must remain bounded and suitable for the expected student-record volume.
16. Dashboard calculations must not create a competing source of truth.

#### 5.5 Export / Printable Data

17. Provide export/printable register data based on the applicable filtered register view.
18. Export must respect the same authorization boundaries as the underlying register.
19. Exported data must not expose information the requesting user is not authorized to access.
20. Large exports must be handled in a bounded/resource-safe manner.

---

### 6. Data Changes

Register should primarily operate as a **query/read capability**.

It does not become authoritative for:

- Student identity → Student Management
- Student enrollment → Student Management
- Department/program/year/batch → Academic Foundation
- Verification decisions → Verification

Reporting and read-oriented capabilities must use module-owned query interfaces rather than directly querying module tables.

No new authoritative Register data model is defined by the source architecture.

---

### 7. API Changes

APIs/capabilities are required for:

- Administrative student register search
- Student register filtering
- Category/gender/verification views
- Student-status dashboard
- Register export/printable data

APIs must enforce:

- Authentication
- Authorization
- Appropriate scope
- Input validation
- Pagination/bounded responses
- Safe error handling

Exact routes, request/response structures, permissions, export format, and implementation mechanism are not defined and must not be invented.

---

### 8. Security Notes

- Register is an administrative read capability, not an authorization bypass.
- Backend authorization is mandatory.
- Sensitive student information must follow the system-wide masking/restricted-access model.
- Register must not expose full sensitive values merely because a user can access a student register.
- Export authorization must be enforced server-side.
- Queries must not allow unbounded access to the student population.
- Register must use approved module query interfaces rather than direct cross-module ORM/model access.
- Relevant access and administrative actions should follow the system's accountability/audit requirements.

---

### 9. Definition of Done

- Administrative student register query is implemented.
- Student search/filter/pagination uses authoritative Student Management data.
- Historical enrollment context is available where required.
- Department filtering works.
- Program filtering works.
- Academic year filtering works.
- Batch filtering works.
- Category view/filter works.
- Gender view/filter works.
- Verification view/filter works.
- Student-status dashboard is implemented.
- Register export/printable-data capability is implemented.
- Authorization is enforced server-side.
- Sensitive information remains protected.
- Register does not duplicate ownership of student, academic, or verification data.
- Queries are bounded and avoid N+1/unbounded access.
- Pagination limits are enforced.
- Authorization and scope tests are implemented.
- Filtering and historical-enrollment behavior are tested.
- Export authorization is tested.
- Relevant audit/accountability behavior is tested.
- Required human review is completed.

---

### 10. Out of Scope

- Student Management ownership or editing.
- Academic Foundation master-data management.
- Verification decision management.
- Finance management.
- Results/eligibility processing.
- Faculty management.
- Creating a separate Register source of truth.
- Direct cross-module database ownership.
- Multi-tenant reporting.
- Unbounded analytics infrastructure.
- Any dashboard functionality not represented in the task graph.

---

### 11. Open Questions

1. What exact administrative roles can access the Register?
2. What exact fields should appear in the register?
3. What exact student-status categories should the dashboard display?
4. What exact verification statuses should be filterable/displayed?
5. What exact export formats are required?
6. What exact columns are permitted in exports?
7. What exact sensitive fields must be masked or excluded from exports?
8. What are the exact pagination/page-size limits?
9. What exact dashboard metrics are required?
10. What exact API routes and response contracts are required?

These should be finalized before implementation rather than inferred.

---

### 12. Dependencies

**Student search/filter/pagination/detail + Historical enrollment/status**
→ Administrative student register query

**Administrative register query + Academic master-data search/filter/detail**
→ Department/program/year/batch filtering

**Academic filtering + Verification review/approval**
→ Category/gender/verification views

**Register query + Category/gender/verification views**
→ Administrative student-status dashboard

**Department/program/year/batch filtering**
→ Register export/printable data

**Status:** PRD #8 — `PRD-register-dashboard.md`
