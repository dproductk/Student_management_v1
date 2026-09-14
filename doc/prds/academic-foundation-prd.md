# Feature: Academic Foundation

## 1. Problem

The system requires a single authoritative academic structure that other modules can depend on. Academic entities such as departments, programs, academic years, semesters, batches, schemes, subjects, and scheme-subject definitions must be owned by the Academic Foundation module rather than duplicated across Student Management, Faculty, Finance, or Results.

The academic structure must also preserve historical relationships so that introducing or changing a future scheme does not alter the academic context of historical student records or results.

## 2. Goal

Build the Academic Foundation bounded context as the authoritative source for:

- Departments
- Programs
- Academic Years
- Semesters
- Batches
- Schemes/curricula
- Subjects
- Scheme-subject definitions

It must provide the academic structure required by Student Management, Faculty, Results, Finance, and other dependent modules without duplicating academic master data.

## 3. User Stories

- As an authorized system actor, I want to manage departments so that the system has an authoritative organizational structure.
- As an authorized system actor, I want to manage programs associated with the academic structure.
- As an authorized system actor, I want to manage academic years and semesters.
- As an authorized system actor, I want to manage batches using the established academic structure.
- As an authorized system actor, I want to define schemes/curricula without destroying historical academic relationships.
- As an authorized system actor, I want to maintain reusable subject identities.
- As an authorized system actor, I want to configure how a subject applies under a particular scheme through a Scheme Subject.
- As an authorized system actor, I want to search, filter, and inspect academic master data.
- As a downstream module, I want to consume authoritative academic entities rather than maintaining duplicate copies.

## 4. Scope — Files/Modules Touched

### Bounded Context

**Academic Foundation**

Owns:

- Departments
- Programs
- Academic Years
- Semesters
- Batches
- Schemes
- Subjects
- Scheme Subjects
- Academic structure

### Implementation Scope

The task graph defines these vertical slices:

1. Department management
2. Program management
3. Academic year and semester management
4. Batch management
5. Scheme management
6. Subject identity management
7. Scheme-subject configuration
8. Academic master-data search/filter/detail
9. Historical academic-structure integrity tests

Exact source-file paths are **not specified in the supplied architecture/task documents**, so no implementation paths are invented here.

## 5. Requirements

### 5.1 Organizational Structure

1. The Academic Foundation module shall own Department records.
2. The Academic Foundation module shall own Program records.
3. Programs shall be established through the defined Department → Program dependency.
4. The Academic Foundation module shall own Academic Year records.
5. The Academic Foundation module shall own Semester records.
6. Academic year and semester management shall follow the dependency defined by the task graph.
7. The Academic Foundation module shall own Batch records.
8. Batch management shall depend on Program and Academic Year/Semester management.

### 5.2 Curriculum

9. The Academic Foundation module shall own Scheme/curriculum records.
10. Scheme management shall depend on Academic Year and Semester management.
11. The Academic Foundation module shall own reusable Subject identities.
12. Subject identity management shall depend on Scheme management according to the approved task graph.
13. A Subject shall represent the reusable subject identity.
14. A Scheme Subject shall represent that subject under a specific scheme and carry the scheme-specific academic definition.
15. Scheme-subject configuration shall depend on both Subject identity management and Scheme management.

### 5.3 Historical Integrity

16. Existing historical scheme relationships shall remain intact when a future scheme is introduced.
17. Historical scheme definitions shall not be changed in a way that changes historical results.
18. Academic structure changes shall preserve historical correctness.
19. Historical academic-structure integrity shall be covered by automated tests.
20. The system shall not replace historical academic relationships with only a current-state representation where historical context is required.

### 5.4 Ownership and Boundaries

21. Academic Foundation shall be the sole authoritative owner of academic master data within the defined scope.
22. Student Management shall not duplicate academic master-data definitions.
23. Faculty shall not duplicate academic master-data definitions.
24. Finance shall not duplicate academic master-data definitions.
25. Results shall not duplicate academic master-data definitions.
26. Other modules shall use approved interfaces/contracts rather than directly reaching into Academic Foundation persistence. The ownership rule requires the owning module to define business behavior and write its data directly.

### 5.5 Search and Validation

27. Academic master data shall support search, filtering, and detail views.
28. The search/filter/detail capability shall operate across the completed academic master-data components defined by the task dependency graph.
29. Validation shall occur at the API/domain boundaries appropriate to the architecture.
30. Academic business invariants shall be enforced by the domain/application layers and appropriate database constraints where applicable.
31. Queries shall remain bounded and must not introduce unbounded retrieval or N+1 access patterns.

## 6. Data Changes

The Academic Foundation owns the following domain entities:

- `Department`
- `Program`
- `AcademicYear`
- `Semester`
- `Batch`
- `Scheme`
- `Subject`
- `SchemeSubject`

A Subject is the reusable identity; Scheme Subject carries the scheme-specific academic definition. The supplied database design identifies possible scheme-specific properties such as semester, subject type, credits, marks structure, and passing requirements, but the PRD does **not** add fields beyond what the approved requirements ultimately establish.

No exact physical table names, columns, indexes, or migrations are invented because the supplied architectural material does not provide a finalized `FILE_MAP.md` or complete physical schema for this PRD.

## 7. API Changes

The Academic Foundation vertical slices require API capabilities for:

- Department management
- Program management
- Academic year management
- Semester management
- Batch management
- Scheme management
- Subject management
- Scheme-subject configuration
- Academic master-data search/filter/detail

The exact endpoint paths, HTTP methods, request schemas, response schemas, and pagination parameters are **not defined by the supplied architecture/task documents** and therefore are intentionally left unspecified.

All APIs must follow the established boundary rules:

- authenticate the actor
- authorize the operation server-side
- validate input
- enforce domain/business rules
- return safe errors
- use bounded responses
- avoid exposing database implementation details

## 8. Security Notes

- Academic Foundation operations require backend authentication and authorization.
- Authorization is enforced by Identity together with application policy.
- Frontend authorization must never be treated as the security boundary.
- Client-supplied role, permission, ownership, or scope information must not be trusted.
- Academic master-data changes are important administrative actions and must follow the project's accountable-actor/audit model.
- Audit capability remains owned by the cross-cutting Audit module rather than duplicated inside Academic Foundation.
- No sensitive-data handling is introduced by this PRD.
- No new authentication mechanism, service, infrastructure component, or bounded context may be introduced.

**Human review is required** because every Academic Foundation task in the implementation graph is explicitly marked `[HUMAN REVIEW REQUIRED]`.

## 9. Definition of Done

-  Department management vertical slice complete.
-  Program management vertical slice complete.
-  Academic year and semester management vertical slice complete.
-  Batch management vertical slice complete.
-  Scheme management vertical slice complete.
-  Subject identity management vertical slice complete.
-  Scheme-subject configuration vertical slice complete.
-  Academic master-data search/filter/detail complete.
-  Historical academic-structure integrity tests complete.
-  Academic Foundation remains the authoritative owner of its defined data.
-  No duplicate academic master data is introduced into dependent modules.
-  Backend authentication and authorization are enforced.
-  Input and business validation are implemented.
-  Queries are bounded and free of known N+1 access patterns.
-  Historical academic relationships remain intact.
-  Automated tests cover relevant domain rules and historical-integrity behavior.
-  Audit/accountability requirements are satisfied.
-  Human review is completed.
-  No unrelated architectural changes are introduced.

## 10. Out of Scope

- Student identity or student records
- Student enrollment implementation
- Faculty records or assignments
- Finance/fee structures
- Results and eligibility
- Government Excel import
- Verification workflows
- Documents
- Reporting implementation
- Student services
- Authentication/role implementation itself
- University examination systems
- Timetable engine
- Hostel/library/gymkhana systems
- Multi-tenant architecture
- Microservices or distributed infrastructure
- Any new bounded context

**Division management is also out of scope for this PRD.** The accepted architecture decision explicitly keeps Batch in v1 and defers Division.

## 11. Open Questions

No new business questions are introduced by the supplied architecture.

The following implementation details remain unspecified and must not be guessed:

1. Exact API routes and request/response contracts.
2. Exact physical database fields and constraints where not already finalized elsewhere.
3. Exact role-permission matrix for individual academic-management operations, if not established by the Identity/authorization requirements.
4. Any institutional academic rules not explicitly defined in the approved architecture.

The two architecture-level open decisions concerning verification policy and sensitive-data retention do not directly define Academic Foundation behavior and should remain open rather than being incorporated into this PRD.

## 12. Dependencies

### Task Dependency Order

1. **Department management**
   - Depends on: Roles and permissions vertical slice
2. **Program management**
   - Depends on: Department management
3. **Academic year and semester management**
   - Depends on: Program management
4. **Batch management**
   - Depends on: Program management; Academic year and semester management
5. **Scheme management**
   - Depends on: Academic year and semester management
6. **Subject identity management**
   - Depends on: Scheme management
7. **Scheme-subject configuration**
   - Depends on: Subject identity management; Scheme management
8. **Academic master-data search/filter/detail**
   - Depends on: Department management; Program management; Academic year and semester management; Batch management; Scheme-subject configuration
9. **Historical academic-structure integrity tests**
   - Depends on: Scheme-subject configuration

### Downstream Dependency

Academic Foundation must be completed before dependent academic relationships are implemented. The task graph explicitly states that students, faculty assignments, results, eligibility, and finance structures must reference established academic entities rather than recreating them.

**This PRD stays within the approved Academic Foundation task graph and does not introduce additional business rules.**