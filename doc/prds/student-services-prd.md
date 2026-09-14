# PRD: Student Services

## 1. Problem

The system needs a reusable mechanism through which students can submit administrative service requests and authorized administrative staff can process, approve/reject, track, and resolve those requests.

The architecture defines **Services** as the bounded context responsible for:

- Student Service Requests
- Service Request Workflow
- Status
- Resolution

The service-request model is intentionally reusable, while exact service-specific workflows remain to be defined.

---

# 2. Goal

Provide a production-grade Student Services capability that:

- Provides a reusable service-request foundation.
- Allows students to submit service requests.
- Tracks request status through an explicit workflow.
- Allows authorized administrative staff to process requests.
- Supports approval/rejection.
- Records resolution/status information.
- Supports documents attached to service requests where applicable.
- Maintains accountable-actor history.
- Enforces backend authorization and scoped access.
- Preserves request history rather than silently rewriting important administrative actions.

---

# 3. User Stories

### Service Requests

- As a student, I want to submit a service request so that I can request an administrative service.
- As a student, I want to see the status of my service request so that I know whether it is being processed.
- As an administrative staff member, I want to view service requests that I am authorized to process.
- As an administrative staff member, I want to process a service request and update its status.
- As an authorized administrative user, I want to approve or reject a request.
- As an administrative user, I want to record the resolution of a request.
- As an auditor, I want important service-request actions to identify the responsible actor.

### Documents

- As a student or authorized user, I want to attach supporting documents to a service request where the service permits them.
- As an authorized user, I want service-request attachments to follow the existing secure document-storage and access rules.

---

# 4. Scope — Files/Modules Touched

## Primary bounded context

**Services**

Services owns:

- Service types.
- Student service requests.
- Service-request workflow.
- Status.
- Resolution.

The service-request model is intended to be reusable rather than hardcoded around one particular request type.

## Dependencies

### Identity & Access

Provides:

- Authentication.
- Authorization.
- Scoped authorization for protected operations.

### Student Management

Provides:

- Authoritative student identity/core student record.

Services must not become a second student-information source.

### Documents

Provides the existing document capability for service-request attachments.

Documents remains responsible for document metadata, lifecycle, storage, and access.

### Audit

Provides accountable-actor audit capability.

## Exact task scope

The task graph defines:

1. Service type and reusable service-request foundation.
2. Student service-request submission and status.
3. Administrative service-request processing.
4. Service-request approve/reject workflow.
5. Service-request document attachment.
6. Service-request accountable-actor audit.

All are **HUMAN REVIEW REQUIRED**.

---

# 5. Requirements

## 5.1 Service Framework

### R-001 — Service Type

The system shall provide a service-type foundation from which individual student services can be represented.

### R-002 — Reusable Request Model

The system shall provide a reusable service-request model rather than creating a separate implementation for every service.

### R-003 — Student Association

A service request shall be associated with the student who submitted it.

Student identity remains owned by Student Management.

### R-004 — Request Status

A service request shall have an explicit status representing its current workflow state.

The system shall not rely solely on unstructured text to represent request status.

---

## 5.2 Request Submission

### R-005 — Student Submission

An authorized student shall be able to submit a service request for an available service type.

### R-006 — Submission Validation

The system shall validate service-request input at the API/application boundary before creating the request.

### R-007 — Request Ownership

A student shall only be able to access or operate on service requests they are authorized to access.

### R-008 — Submission History

The system shall preserve the submitted request information required for the service workflow.

---

## 5.3 Administrative Processing

### R-009 — Administrative Visibility

Authorized administrative users shall be able to view service requests within their permitted scope.

### R-010 — Processing

Authorized administrative users shall be able to process service requests.

Authorization shall be enforced by the backend rather than relying on frontend visibility.

### R-011 — Status Updates

Processing shall use the defined service-request workflow and explicit status changes.

### R-012 — Resolution

The system shall support recording the resolution of a service request.

The Services bounded context explicitly owns request resolution.

---

## 5.4 Approval / Rejection

### R-013 — Approval

An authorized administrative user shall be able to approve a service request where the applicable service workflow permits approval.

### R-014 — Rejection

An authorized administrative user shall be able to reject a service request where the applicable service workflow permits rejection.

### R-015 — Explicit Workflow

Approval and rejection shall be explicit workflow operations rather than implicit consequences of arbitrary status editing.

The architecture's example service flow is:

**Student submits request → Administrative Staff → Process Request → Approve / Reject → Status → Resolution.**

---

## 5.5 Documents

### R-016 — Document Attachment

The system shall support document attachments to service requests where applicable.

### R-017 — Existing Document Boundary

Service requests shall use the established Documents capability rather than implementing an independent file-storage system.

### R-018 — Secure Document Handling

Attachments shall follow the established document security requirements, including secure storage and controlled access.

Actual files must not be stored directly as PostgreSQL binary data.

---

## 5.6 Accountability

### R-019 — Accountable Actor

Important administrative service-request actions shall identify the responsible actor.

### R-020 — Audit

Relevant service-request approval/rejection and processing actions shall generate appropriate audit records.

The task graph explicitly requires a **service-request accountable-actor audit** capability.

### R-021 — Historical Actions

Important workflow actions shall remain traceable rather than being silently rewritten.

---

## 5.7 Security

### R-022 — Authentication

Protected service operations shall require authenticated users.

### R-023 — Authorization

The backend shall enforce authorization for:

- Student request access.
- Administrative processing.
- Approval/rejection.
- Document access.
- Other protected service operations.

### R-024 — Scoped Authorization

Administrative users shall only receive service-request visibility and actions permitted by their authorization scope.

The exact scope/role matrix is not defined in the supplied architecture.

---

# 6. Data Changes

The Services bounded context requires data structures representing:

- Service types.
- Student service requests.
- Request status/workflow.
- Request resolution.
- Request processing/approval/rejection information.
- Service-request document associations where applicable.
- Accountable actor information/audit references.

### Ownership

**Services owns:**

- Service definitions.
- Service requests.
- Request workflow/status.
- Resolution.

**Student Management owns:**

- Student identity and student information.

**Documents owns:**

- Document metadata.
- Document lifecycle.
- Storage references.
- Document versions.

**Identity owns:**

- Users.
- Roles.
- Permissions.

**Audit owns:**

- Cross-cutting audit capability.

No module should duplicate these ownership responsibilities.

### Schema intentionally not finalized

The supplied architecture does not define:

- Exact service table names.
- Exact request fields.
- Exact status values beyond the workflow concepts.
- Exact resolution schema.
- Exact attachment relationship.
- Exact database constraints/indexes.

These must be finalized during implementation/design without inventing institutional service requirements.

---

# 7. API Changes

The Services module will require API operations corresponding to:

- Service-type access.
- Service-request submission.
- Student request listing/detail.
- Administrative request listing/detail.
- Request processing.
- Status transitions.
- Approval.
- Rejection.
- Resolution.
- Document attachment/access where applicable.

The API layer shall handle:

- Authentication extraction.
- Boundary validation.
- Authorization coordination.
- Serialization.
- HTTP status codes.
- Pagination.
- Bounded responses.
- Safe error responses.

The application/domain layer shall own:

- Service-request workflow.
- State transitions.
- Authorization policy coordination.
- Approval/rejection behavior.
- Resolution behavior.

### API details intentionally open

The architecture does not specify:

- Exact routes.
- HTTP methods.
- Request/response schemas.
- Status-code mapping.
- Permission names.
- Pagination contract.
- Exact service-specific fields.

These must not be invented in this PRD.

---

# 8. Security Notes

### Backend authority

Frontend controls must never be treated as authorization.

The backend must independently validate that the authenticated actor is allowed to access or modify a request.

### Student isolation

Students must not be able to access another student's service requests.

### Administrative scope

Administrative staff access must follow the established scoped-authorization model.

### Documents

Service-request attachments are untrusted input and must use the existing secure document boundary.

### Sensitive data

Service-request APIs must not expose unrelated sensitive student information.

### Audit

Approval, rejection, processing, and other important administrative actions must be attributable to an accountable actor.

### Logging

Logs must not contain sensitive student information or document contents.

---

# 9. Definition of Done

-  Service type foundation implemented.
-  Reusable service-request foundation implemented.
-  Student service-request submission implemented.
-  Request status implemented.
-  Student request access implemented.
-  Administrative request processing implemented.
-  Approval workflow implemented.
-  Rejection workflow implemented.
-  Resolution handling implemented.
-  Service-request document attachment implemented where applicable.
-  Existing Documents boundary reused rather than duplicated.
-  Backend authentication enforced.
-  Backend authorization enforced.
-  Scoped administrative access enforced.
-  Service-request workflow/state transitions tested.
-  Student access isolation tested.
-  Administrative authorization tested.
-  Approval/rejection behavior tested.
-  Document-access security tested.
-  Accountable-actor audit implemented.
-  Failure and invalid-input behavior tested.
-  Queries are bounded and avoid N+1 behavior.
-  Database migrations are safe.
-  End-to-end request submission → processing → approval/rejection → status/resolution flow tested.
-  **Human review completed for every Student Services task.**

---

# 10. Out of Scope

- Inventing individual service-specific workflows.
- Inventing service-specific approval authorities.
- Inventing service-specific statuses not defined by the architecture.
- Building separate modules for individual services.
- Creating a generic cross-domain Correction module.
- Creating a second student-information source.
- Creating a separate document-storage system.
- Direct access to another bounded context's internal tables.
- Unspecified integrations with external college/government systems.
- Advanced workflow automation not defined by the architecture.

The source explicitly states that **exact service-specific workflows are TBD and need the PRD**.

---

# 11. Open Questions

1. **Service types**
   - Which services are included in the initial release?
2. **Service-specific workflows**
   - What workflow applies to each service type?
3. **Statuses**
   - What exact status values are required for each service?
4. **Approval authority**
   - Which roles may approve or reject each service type?
5. **Administrative scope**
   - Which administrative users may view/process which requests?
6. **Resolution**
   - What information must be recorded when a request is resolved?
7. **Documents**
   - Which service types require supporting documents?
   - Which document types are permitted for each service?
8. **Correction/reopening**
   - Can an already processed request be reopened or corrected?
   - If so, what is the required workflow?
9. **Notifications**
   - Are students notified when request status changes?
   - If so, which notification mechanism is required?
10. **Service-specific fields**
    - What additional data must each service request collect?

These questions remain open because the architecture intentionally defines the reusable framework but does not define the exact service-specific workflows. The architecture requires unresolved business rules to be clarified rather than guessed.

---

# 12. Dependencies

### Upstream

1. **Identity & Access**
   - Authentication.
   - Authorization.
   - Scoped authorization.
2. **Student Management**
   - Student identity/core record.
3. **Documents**
   - Document attachment and secure document handling.
4. **Audit**
   - Accountable-actor audit capability.

### Downstream

No specific downstream bounded context is required by the defined service-request workflow.

### Exact implementation dependency order

**Service Type & Request Foundation → Student Submission & Status → Administrative Processing → Approve/Reject Workflow → Document Attachment → Accountable-Actor Audit.**

This follows the task graph and keeps the implementation within the existing **Services** bounded context.
