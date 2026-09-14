# Feature: Student Documents

## 1. Problem

Students and authorized users need to submit documents such as marksheets, Aadhaar-related documents, photographs, signatures, allotment letters, bank-related documents, certificates, and service-request documents.

The system must manage these documents without storing large binary files in PostgreSQL, while preserving metadata, storage references, document history, replacements, and controlled access. Documents also interact with Verification, but **Documents owns the document itself and its lifecycle; Verification owns the verification decision**.

---

## 2. Goal

Build the **Documents** bounded context to provide:

- Document types and metadata
- Secure object/file storage integration
- Student document upload
- Document listing and controlled access
- Document versioning
- Current/superseded lifecycle
- Controlled allotment-letter replacement/reset
- Sensitive-document masking and restricted access
- Explicit sensitive-data reveal with authorization and audit

Actual document files remain outside PostgreSQL; PostgreSQL stores document metadata and storage references.

---

## 3. User Stories

- As a student or authorized user, I want to upload a required document so that it is associated with my student record.
- As an authorized user, I want to view a student's document metadata and available documents according to my permissions.
- As an authorized user, I want controlled access to stored documents.
- As an authorized user, I want document replacements to create a new version rather than silently overwrite the previous document.
- As an authorized user, I want the current and superseded document versions to remain explainable.
- As an authorized user, I want sensitive documents to remain masked/restricted by default.
- As an authorized user with appropriate permission, I want to explicitly reveal sensitive information when required.
- As the system, I want every sensitive-data reveal to produce an audit event.
- As Verification, I want access to submitted documents where verification is required without taking ownership of document storage or lifecycle.

---

## 4. Scope — Files/Modules Touched

### Documents Module

The task graph defines these vertical slices:

### 4.1 Document System

- **Document type and document metadata vertical slice**
  - Depends on Student identity and core student record.
- **Object-storage integration and secure document upload vertical slice**
  - Depends on Document type and document metadata.
- **Student document listing, metadata, and controlled access vertical slice**
  - Depends on Object-storage integration and secure document upload.

### 4.2 Versioning and Replacement

- **Document versioning and current/superseded lifecycle vertical slice**
  - Depends on Student document listing, metadata, and controlled access.
- **Controlled allotment-letter replacement/reset vertical slice**
  - Depends on Document versioning and current/superseded lifecycle.

### 4.3 Sensitive Documents

- **Sensitive-document masking and restricted-access vertical slice**
  - Depends on Student document listing, metadata, and controlled access; Scoped authorization enforcement for protected application operations.
- **Explicit sensitive-data reveal and audit vertical slice**
  - Depends on Sensitive-document masking and restricted-access; Identity authorization; Audit capability.

All listed tasks are marked **HUMAN REVIEW REQUIRED**.

---

## 5. Requirements

### 5.1 Document Ownership

1. Documents owns:
   - Document metadata
   - Document versions
   - Storage references
   - Document lifecycle.
2. Documents must not become the owner of student information.
3. Student Management remains the owner of actual student data.
4. Verification owns verification decisions rather than creating another document/student source of truth.

### 5.2 Document Storage

5. Actual document files MUST be stored outside PostgreSQL.
6. PostgreSQL must store document metadata and storage references.
7. Object-storage credentials MUST remain server-side and must never be exposed to the React frontend.
8. Document upload must use secure storage integration.
9. Uploaded files must be treated as untrusted input.

### 5.3 Document Types and Metadata

10. The system must support reusable document types and associated document metadata.
11. The architecture identifies examples including:
    - Student Photo
    - Signature
    - Aadhaar
    - SSC Result
    - HSC Result
    - Bank-related Document
    - Allotment Letter
    - Other Required Certificates
    - Service-request Documents.
12. The exact required-document catalogue may evolve; the PRD must not invent additional institutional requirements.

### 5.4 Upload and Access

13. Students and authorized users may upload documents according to authorization rules.
14. Document access must be controlled server-side.
15. Normal document/student-detail operations must not bypass document access controls.
16. Document metadata and storage references must remain associated with the appropriate student/document ownership context.

### 5.5 Document Lifecycle

17. Documents must support explicit lifecycle states rather than silently replacing historical information.
18. Document replacement must preserve the previous version.
19. A replacement must create a new document version.
20. The previous version becomes `SUPERSEDED`.
21. The replacement becomes `CURRENT`.

The defined flow is:

```text
Existing Document V1
        ↓
Replacement / Reset
        ↓
New Document V2
        ↓
V1 = SUPERSEDED
V2 = CURRENT
```

Documents must not be silently overwritten, and historical versions must remain explainable.

### 5.6 Allotment-Letter Replacement

22. A controlled allotment-letter replacement/reset workflow must be provided.
23. The workflow must follow the document versioning/current-superseded lifecycle.
24. The previous allotment-letter version must remain historically preserved.

### 5.7 Sensitive Documents

25. Sensitive documents must be masked/restricted by default.
26. Sensitive information must not automatically be returned in normal student-detail APIs.
27. Access to protected documents must be governed by backend authorization.
28. Sensitive document access must use scoped authorization where required.

The architecture specifically identifies Aadhaar and bank-related documents among potentially sensitive documents.

### 5.8 Explicit Sensitive Reveal

29. Full sensitive information must require an explicit reveal action.
30. The reveal workflow must include:

- Explicit reveal action
- Permission check
- Sensitive-data decryption where applicable
- Temporary display
- Audit event.

31. Every sensitive-data reveal must itself be auditable.
32. Audit records must capture the accountable actor, action, target/resource, timestamp, and reason where applicable.

### 5.9 Verification Boundary

33. Documents may participate in the Verification workflow where required.
34. A submitted document and its verification decision are separate concepts.
35. The Documents module must not implement the institutional field/document verification policy.
36. The exact verification requirement for each document remains **TBD — needs PRD**.

---

## 6. Data Changes

The Documents context requires data representing:

- Document types
- Document metadata
- Student/document ownership relationship
- Storage references
- Document versions
- Document lifecycle/current-superseded state
- Relevant sensitive-document access information
- Replacement/reset history where required
- Metadata needed for controlled access and audit integration

The actual document binary/content must **not** be stored as large binary fields in PostgreSQL.

The exact physical table names, fields, constraints, storage-provider implementation, and indexes are not defined by the source architecture and must not be invented here.

---

## 7. API Changes

The Documents module must provide capabilities for:

- Document-type management/use
- Document metadata creation and retrieval
- Secure document upload
- Document listing
- Controlled document access
- Document metadata retrieval
- Document version retrieval
- Document replacement/reset
- Allotment-letter replacement/reset
- Sensitive-document masking
- Explicit sensitive-data reveal
- Audit integration for sensitive reveals

API behavior must enforce authentication, authorization, input validation, safe errors, bounded responses, and appropriate ownership checks.

The API must not expose raw storage credentials or internal storage implementation details.

**Exact routes, request/response schemas, status codes, permission names, and storage-provider contracts remain unspecified and must be finalized separately.**

---

## 8. Security Notes

- Backend authorization is mandatory.
- Document access must never rely solely on frontend restrictions.
- Uploaded files are untrusted input.
- Object-storage credentials must never reach the frontend.
- Sensitive documents are masked/restricted by default.
- Explicit reveal requires authorization and audit.
- Normal APIs must not automatically expose full sensitive values.
- Document replacements must preserve historical versions.
- Important document actions must identify an accountable actor.
- Audit records must not unnecessarily contain raw sensitive values.
- Document storage and retrieval must respect the owning student's authorization boundary.
- No destructive overwrite of historical document versions.

---

## 9. Definition of Done

-  All defined Document vertical slices are implemented.
-  Document metadata ownership is clearly established.
-  Actual files are stored outside PostgreSQL.
-  PostgreSQL stores document metadata and storage references.
-  Secure document upload is implemented.
-  Object-storage credentials are never exposed to the frontend.
-  Student document listing and controlled access work correctly.
-  Document versions are preserved.
-  Replacement creates a new version.
-  Previous versions become explicitly superseded rather than overwritten.
-  Current document state is explicit.
-  Allotment-letter replacement/reset uses the versioning lifecycle.
-  Sensitive documents are masked/restricted by default.
-  Sensitive reveal requires explicit authorization.
-  Sensitive reveals generate audit events.
-  Student Management remains the owner of student information.
-  Verification remains the owner of verification decisions.
-  Exact verification policy is not invented inside Documents.
-  Authentication and authorization are enforced server-side.
-  File upload and access failure cases are handled safely.
-  Historical document integrity is tested.
-  Access-control and sensitive-reveal behavior is tested.
-  Relevant audit/accountability behavior is tested.
-  Queries remain bounded and avoid N+1/unbounded access patterns.
-  Required human review is completed.

---

## 10. Out of Scope

- Student identity/admission/enrollment ownership.
- Verification decision ownership.
- Defining the institution's field-by-field/document verification matrix.
- Student correction workflows.
- Finance or payment documents as financial records.
- Results processing.
- Academic master-data management.
- Generic correction/replacement service outside Documents.
- Storing document binaries directly in PostgreSQL.
- Exposing object-storage credentials to clients.
- Defining unspecified institutional document requirements.
- Document retention periods, unless separately decided.

The verification matrix remains an explicit business-policy decision, and the architecture does not authorize the Documents PRD to invent it.

---

## 11. Open Questions

1. What exact document types are mandatory for the institution?
2. Which individual documents require Verification before becoming accepted/official?
3. Which documents can be used immediately after submission?
4. What exact roles/permissions can upload, view, replace, reset, or reveal each document category?
5. What exact storage provider and storage contract will be used?
6. What exact file-size, MIME-type, extension, and upload validation rules apply?
7. What exact document lifecycle states are required beyond `CURRENT` and `SUPERSEDED`?
8. What exact allotment-letter replacement/reset authorization and workflow rules apply?
9. What exact API routes and request/response contracts should be exposed?
10. What institutional retention requirements apply to documents and their historical versions?

The architecture explicitly leaves the verification matrix and sensitive-data retention policy open; these must not be hard-coded without the institutional decision.

---

## 12. Dependencies

### Direct task dependencies

**Student Management**
→ Document type and document metadata

**Document metadata**
→ Object-storage integration and secure document upload

**Object storage + secure upload**
→ Student document listing, metadata, and controlled access

**Document listing/access**
→ Document versioning and current/superseded lifecycle

**Versioning**
→ Controlled allotment-letter replacement/reset

**Document listing/access + Scoped authorization**
→ Sensitive-document masking and restricted access

**Sensitive masking + Identity authorization + Audit**
→ Explicit sensitive-data reveal and audit

### Cross-module relationships

The principal document flow is:

**Student → Document Upload → Document Storage → Document Metadata → Verification where required → Document Status**

The key ownership boundary is:

**Documents → document metadata/lifecycle**
**Verification → verification decision**
**Student Management → actual student information**

**Status:** PRD #5 — `PRD-documents.md`