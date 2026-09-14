# Feature: Assessments / Unit Test Marks

## 1. Problem

The system needs to allow faculty to upload unit-test marks, validate the uploaded information, persist structured marks, and make the marks available to students.

The assessment capability must be connected to the authoritative academic structure, faculty assignments, and student enrollments. The architecture also requires the assessment model to remain extensible rather than being hardcoded exclusively around Unit Tests.

---

## 2. Goal

Build the **Assessments** capability to provide:

- Assessment types and definitions
- Assessment-mark storage
- Student/subject association
- Faculty unit-test mark upload
- Unit-test extraction and validation
- Mark persistence
- Student mark viewing
- Duplicate/import/error handling

---

## 3. User Stories

- As an authorized faculty member, I want to upload unit-test marks.
- As the system, I want to extract and validate uploaded marks before storing them.
- As the system, I want marks associated with the correct student and academic subject context.
- As a student, I want to view my stored unit-test marks.
- As the system, I want duplicate or invalid imports to be handled safely.
- As the system, I want the assessment model to support future assessment types rather than being limited to Unit Tests.

---

## 4. Scope — Files/Modules Touched

### 4.1 Assessment Foundation

1. **Assessment type and assessment definition vertical slice**
   - Depends on Academic Foundation and Faculty assignment.
2. **Assessment marks storage and student/subject association vertical slice**
   - Depends on Assessment type/definition and Student academic enrollment.

### 4.2 Unit Test Flow

3. **Faculty unit-test marks upload vertical slice**
   - Depends on Assessment marks storage/student-subject association and Faculty/HOD/Class Teacher scoped student visibility.
4. **Unit-test extraction and validation vertical slice**
   - Depends on Faculty unit-test marks upload.
5. **Unit-test persistence and student-view vertical slice**
   - Depends on Unit-test extraction and validation.
6. **Unit-test duplicate/import/error-handling end-to-end tests**
   - Depends on Unit-test persistence and student-view.

All tasks are marked **HUMAN REVIEW REQUIRED**.

---

## 5. Requirements

### 5.1 Assessment Foundation

1. The system must provide an assessment type/definition capability.
2. Assessment definitions must be associated with the established academic context.
3. Assessment definitions must be associated with the relevant faculty assignment where required.
4. The assessment architecture must remain extensible and must not be designed exclusively around Unit Tests.

### 5.2 Assessment Marks

5. The system must store assessment marks as structured data.
6. Marks must be associated with the relevant student.
7. Marks must be associated with the relevant subject/academic context.
8. Student academic enrollment must provide the authoritative enrollment context.
9. Assessment data must not duplicate Academic Foundation's subject or academic master data.

### 5.3 Faculty Unit-Test Upload

10. Authorized faculty must be able to upload Unit Test marks.
11. Uploads must pass through the defined extraction and validation flow.
12. Faculty access must respect the faculty assignment and scoped-student-visibility rules.
13. The backend must enforce authorization; frontend restrictions are insufficient.

The defined flow is:

**Teacher → Upload Unit Test Marks → System Extracts Data → Validate → Store Marks → Student Views Marks.**

### 5.4 Extraction and Validation

14. Uploaded Unit Test data must be extracted before persistence.
15. Extracted data must be validated before becoming stored assessment marks.
16. Invalid input must not silently become authoritative assessment data.
17. Validation failures must be represented through safe, actionable errors.
18. The exact validation rules must be based on finalized assessment requirements rather than invented rules.

### 5.5 Persistence and Student View

19. Validated marks must be persisted as structured assessment records.
20. Students must be able to view their stored marks.
21. Student views must only expose the student's authorized assessment information.
22. Faculty must not gain unrestricted access to unrelated students through the assessment interface.

### 5.6 Duplicate and Failure Handling

23. Duplicate imports must be handled explicitly.
24. Import failures must not result in partially corrupted assessment records.
25. Retry behavior must be considered wherever repeated processing could create duplicate marks.
26. End-to-end tests must cover duplicate, import, and error-handling scenarios.

---

## 6. Data Changes

The Assessments context requires data representing:

- Assessment types
- Assessment definitions
- Assessment marks
- Student/subject assessment associations
- Upload/import information required by the Unit Test workflow

Ownership:

- Assessment definitions and marks → Assessments
- Faculty assignments → Faculty
- Subjects/scheme subjects → Academic Foundation
- Student academic enrollment → Student Management
- Student identity → Student Management

The exact physical schema, field names, mark representation, constraints, and import-row structure are not finalized in the supplied architecture and must not be invented.

---

## 7. API Changes

The Assessments capability requires APIs for:

- Assessment type/definition management
- Assessment mark access
- Faculty Unit Test upload
- Upload validation/extraction
- Persisted mark retrieval
- Student mark viewing

APIs must enforce:

- Authentication
- Authorization
- Faculty/student scope
- Input validation
- Bounded responses
- Safe error handling
- Appropriate pagination for collections

Exact routes, payloads, response schemas, permissions, file formats, and HTTP status codes remain open.

---

## 8. Security Notes

- Faculty mark-upload operations require backend authorization.
- Faculty must only operate within their authorized academic/student scope.
- Students must only access their own applicable marks.
- Uploaded files/data are untrusted input and must undergo appropriate boundary validation.
- Assessment endpoints must not expose unrelated student records.
- Errors must not reveal sensitive implementation details.
- Important assessment actions should identify the accountable actor where applicable.
- Assessment data must not bypass Faculty, Academic Foundation, or Student Management ownership boundaries.

---

## 9. Definition of Done

-  Assessment type and definition capability is implemented.
-  Assessment model is extensible beyond Unit Tests.
-  Assessment marks are stored as structured data.
-  Marks are correctly associated with students.
-  Marks are correctly associated with subjects/academic context.
-  Faculty Unit Test upload is implemented.
-  Upload extraction is implemented.
-  Upload validation is implemented.
-  Validated marks are persisted.
-  Students can view their marks.
-  Faculty scope is enforced server-side.
-  Student access is enforced server-side.
-  Duplicate imports are handled safely.
-  Import failures are handled safely.
-  Retry/idempotency behavior is considered.
-  Assessment data does not duplicate academic/student ownership.
-  Unit-test extraction and validation tests exist.
-  Mark persistence tests exist.
-  Student-view authorization tests exist.
-  Duplicate/import/error-handling E2E tests exist.
-  Queries are bounded and avoid N+1/unbounded access.
-  Required human review is completed.

---

## 10. Out of Scope

- Full university examination management.
- University examination registration.
- University examination payment.
- Hall-ticket management.
- University examination processing.
- Complex paper setting.
- Complex paper checking.
- Timetable.
- Seating arrangement.
- Result Excel processing.
- Result calculation.
- Credits.
- Eligibility calculation.
- Published-result correction.

The source explicitly limits the current examination scope and identifies these broader examination capabilities as outside the current requirement.

---

## 11. Open Questions

1. What exact assessment types are required initially?
2. What exact Unit Test definition fields are required?
3. What exact mark fields and allowed values are required?
4. What exact Unit Test upload format/file structure is required?
5. What exact extraction rules are required?
6. What exact validation rules apply to uploaded marks?
7. What exact duplicate-detection rules are required?
8. What exact faculty permissions apply to mark uploads?
9. What exact student visibility rules apply?
10. Can marks be corrected after persistence, and if so, what correction workflow applies?
11. What exact API routes and contracts are required?
12. What exact assessment lifecycle/state model is required?

No additional assessment or examination rules should be invented until these are finalized.

---

## 12. Dependencies

**Academic Foundation + Faculty assignment**
→ Assessment type and assessment definition

**Assessment definition + Student academic enrollment**
→ Assessment marks storage and student/subject association

**Assessment marks + Faculty/HOD/Class Teacher scoped student visibility**
→ Faculty Unit Test marks upload

**Faculty Unit Test upload**
→ Unit-test extraction and validation

**Extraction and validation**
→ Unit-test persistence and student view

**Persistence and student view**
→ Duplicate/import/error-handling E2E tests

**Status:** PRD #10 — `PRD-assessments-unit-tests.md`
