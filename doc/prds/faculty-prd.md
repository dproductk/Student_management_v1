# Feature: Faculty & Academic Assignment

## 1. Problem

The system needs to maintain faculty records and their academic teaching assignments without duplicating academic master data or losing historical assignment information.

Faculty owns faculty records, teaching assignments, subject assignments, and batch assignments. Academic entities such as departments, schemes, scheme-subjects, academic years, semesters, and batches remain owned by Academic Foundation and must be referenced rather than recreated.

Faculty visibility of student information must also be scoped according to historical academic assignments and backend authorization.

---

## 2. Goal

Build the **Faculty** bounded context to provide:

- Faculty profiles and lifecycle
- Faculty department/organizational information
- Faculty subject assignments
- Historical teaching assignments
- Historical assignments by academic year, semester, and batch
- Faculty/HOD/Class Teacher scoped student visibility
- Faculty academic information including publications, patents, books, awards, memberships, consultancy, and guidance

---

## 3. User Stories

- As an authorized user, I want to create and maintain faculty records.
- As an authorized user, I want to manage faculty lifecycle information.
- As an authorized user, I want to associate faculty with departments and organizational information.
- As an authorized user, I want to assign faculty to academic subjects and batches.
- As the system, I want teaching assignments to remain historically preserved.
- As an authorized faculty/HOD/Class Teacher, I want student visibility limited to the academic scope I am authorized to access.
- As an authorized user, I want to maintain faculty publications, patents, books, awards, memberships, consultancy, and guidance information.

---

## 4. Scope — Files/Modules Touched

### Faculty Module

The task graph defines:

### 4.1 Faculty

- **Faculty profile and faculty lifecycle vertical slice**
  - Depends on Identity authorization; Academic Foundation.
- **Faculty department and organizational information vertical slice**
  - Depends on Faculty profile and faculty lifecycle; Department management.

### 4.2 Academic Assignment

- **Faculty subject-assignment vertical slice**
  - Depends on Faculty profile and faculty lifecycle; Scheme-subject configuration.
- **Historical faculty assignment by academic year, semester, and batch vertical slice**
  - Depends on Faculty subject-assignment; Student academic enrollment.
- **Faculty/HOD/Class Teacher scoped student visibility vertical slice**
  - Depends on Historical faculty assignment by academic year, semester, and batch; Scoped authorization enforcement for protected application operations.

### 4.3 Faculty Academic Information

- **Faculty publications, patents, books, awards, memberships, consultancy, and guidance vertical slice**
  - Depends on Faculty profile and faculty lifecycle.

All listed tasks are marked **HUMAN REVIEW REQUIRED**.

---

## 5. Requirements

### 5.1 Faculty Ownership

1. Faculty owns faculty records.
2. Faculty owns teaching assignments.
3. Faculty owns subject assignments.
4. Faculty owns batch assignments.
5. Faculty must not duplicate Academic Foundation master data.
6. Faculty must reference authoritative academic entities through approved interfaces/contracts.

### 5.2 Faculty Profile and Lifecycle

7. The system must provide a faculty profile.
8. The system must support faculty lifecycle information.
9. Faculty authorization must be enforced server-side.
10. The architecture permits permanent, visiting, and contract faculty within the faculty model.

### 5.3 Department and Organizational Information

11. Faculty must support department and organizational information.
12. Department references must use the authoritative Department entity owned by Academic Foundation.
13. Faculty must not create a duplicate department master.

### 5.4 Subject Assignment

14. Faculty must support assignment to academic subjects.
15. Assignments must reference the authoritative **Scheme Subject** rather than duplicating subject definitions.
16. Assignments must support the relevant:

- Academic Year
- Semester
- Batch
- Scheme Subject.

17. Subjects taught must not be stored as comma-separated values.

### 5.5 Historical Assignments

18. Teaching assignments must be historical.
19. Historical faculty assignments must preserve the academic year, semester, and batch context.
20. Historical assignment information must remain explainable rather than being overwritten when assignments change.
21. Student academic enrollment remains the authoritative source for student enrollment context.

### 5.6 Scoped Student Visibility

22. Faculty/HOD/Class Teacher access to student information must be scoped according to authorized academic assignment.
23. Scoped visibility must be enforced by the backend.
24. Frontend filtering must not be treated as an authorization boundary.
25. Protected application operations must use the established scoped-authorization mechanism.
26. Historical assignments must be considered when determining the relevant academic scope.

### 5.7 Faculty Academic Information

27. The system must provide the faculty academic-information slice covering:

- Publications
- Patents
- Books
- Awards
- Memberships
- Consultancy
- Guidance.

28. These must remain faculty-owned information and must not be forced into unrelated academic entities.

### 5.8 Accountability

29. Important faculty administrative actions must identify the accountable actor where applicable.
30. Relevant actions must follow the common:

**Actor + Action + Target + Timestamp + Reason where applicable**

accountability pattern.

---

## 6. Data Changes

The Faculty context requires data representing:

- Faculty profiles
- Faculty lifecycle information
- Department/organizational information
- Faculty subject assignments
- Academic-year/semester/batch assignment context
- Historical teaching assignments
- Faculty academic information:
  - Publications
  - Patents
  - Books
  - Awards
  - Memberships
  - Consultancy
  - Guidance

Academic Foundation remains authoritative for:

- Department
- Program
- Academic Year
- Semester
- Batch
- Scheme
- Subject
- Scheme Subject

Student Management remains authoritative for student enrollment.

The exact physical schema, field names, constraints, indexes, and table structure are not fully defined by the source material and must not be invented.

---

## 7. API Changes

The Faculty module must provide capabilities for:

- Faculty profile management
- Faculty lifecycle management
- Department/organizational information
- Faculty subject assignment
- Faculty batch assignment
- Historical assignment retrieval
- Faculty/HOD/Class Teacher scoped student visibility
- Faculty academic-information management

APIs must enforce:

- Authentication
- Authorization
- Scoped access
- Input validation
- Ownership boundaries
- Safe errors
- Bounded queries/responses
- Appropriate pagination for collections

Exact API routes, request/response schemas, permission names, and status codes remain unspecified.

---

## 8. Security Notes

- Faculty operations require backend authentication and authorization.
- Student visibility must be enforced server-side.
- A faculty user's UI must never be treated as the security boundary.
- Faculty/HOD/Class Teacher access must respect their authorized academic scope.
- Sensitive student information accessed through faculty workflows must follow the system-wide sensitive-data protection model.
- Faculty assignments and administrative changes should be auditable where applicable.
- Faculty must not bypass Student Management to modify student records.
- Faculty must not bypass Academic Foundation to modify academic master data.

---

## 9. Definition of Done

-  Faculty profile and lifecycle vertical slice is implemented.
-  Faculty department and organizational information is implemented.
-  Faculty subject assignment is implemented.
-  Faculty batch assignment is represented through the defined assignment model.
-  Historical faculty assignments are preserved.
-  Assignments retain academic year, semester, and batch context.
-  Scheme Subject is referenced rather than duplicated.
-  Subjects taught are not stored as comma-separated values.
-  Faculty/HOD/Class Teacher student visibility is scoped.
-  Scoped visibility is enforced server-side.
-  Faculty academic information is implemented.
-  Academic Foundation remains the owner of academic master data.
-  Student Management remains the owner of student enrollment/data.
-  Authentication and authorization are enforced.
-  Unauthorized student access is rejected.
-  Historical assignment behavior is tested.
-  Scoped authorization behavior is tested.
-  Cross-module ownership boundaries are tested.
-  Queries remain bounded and avoid N+1/unbounded access.
-  Relevant accountability/audit behavior is tested.
-  Required human review is completed.

---

## 10. Out of Scope

- Academic Foundation master-data management.
- Student identity/admission/enrollment ownership.
- Faculty-owned result processing.
- Assessment/result implementation.
- Finance.
- Verification.
- Documents.
- Reporting implementation.
- Generic authorization redesign.
- Division-based academic grouping; Division is explicitly deferred in v1.
- Timetable/scheduling engine.
- Hostel/library/gymkhana or broader ERP functionality.
- Any faculty functionality not represented in the task graph.

---

## 11. Open Questions

1. What exact faculty lifecycle states are required?
2. What exact faculty profile fields are required?
3. What exact department/organizational fields are required?
4. What exact permissions apply to faculty, HOD, and Class Teacher?
5. What exact rules determine the student scope visible to each of those roles?
6. What exact rules govern assignment creation, modification, and ending?
7. What exact API routes and request/response contracts are required?
8. What exact physical schema and constraints are required for historical assignments?
9. What exact faculty academic-information fields are required?
10. What additional institutional rules govern faculty assignments that are not defined in the architecture?

No assumptions should be introduced for these areas until the corresponding requirements are finalized.

---

## 12. Dependencies

### Direct task dependencies

**Identity authorization + Academic Foundation**
→ Faculty profile and faculty lifecycle

**Faculty profile/lifecycle + Department management**
→ Faculty department and organizational information

**Faculty profile/lifecycle + Scheme-subject configuration**
→ Faculty subject assignment

**Faculty subject assignment + Student academic enrollment**
→ Historical faculty assignment by academic year, semester, and batch

**Historical faculty assignment + Scoped authorization enforcement**
→ Faculty/HOD/Class Teacher scoped student visibility

**Faculty profile/lifecycle**
→ Faculty publications, patents, books, awards, memberships, consultancy, and guidance

The core assignment model is:

**Faculty → Scheme Subject + Academic Year + Semester + Batch → Teaching Assignment**

and teaching assignments remain historical.

**Status:** PRD #7 — `PRD-faculty.md`