<!-- Page 1 -->

RUNBOOK.md
Student Management System — Production
Incident Runbook
Purpose
This runbook provides literal incident-response procedures for the production Student Management &
Administrative Data System.
The system is a single-college modular monolith using:
Django
Django REST Framework
PostgreSQL
React
JWT authentication
Object storage
The objective during an incident is:
Stop further damage.
Preserve evidence.
Establish what happened.
Restore safe service.
Correct the underlying data using the owning module's correction/reversal mechanism.
Record the incident and actions taken.
Do not destroy historical evidence merely to make the current state look correct.
The system's trust model is:
Authenticated actor → Authorized operation → Guarded state transition → Persistent history →
Audit visibility → Correction/reversal when necessary.
1. Rollback a Bad Deploy
Use this procedure when a newly deployed application version causes errors, incorrect behavior, broken
workflows, or unsafe data operations.
•
•
•
•
•
•
1.
2.
3.
4.
5.
6.
1

---

<!-- Page 2 -->

Steps
1.1 Confirm the incident
Confirm that the problem began after the latest deployment.
Identify the currently deployed application version/commit.
Identify the last known-good application version/commit.
Record:
Current version
Last known-good version
Deployment time
Approximate incident start time
Observed symptoms
Person performing the rollback
Do not modify database records while establishing the incident.
1.2 Assess database impact
Determine whether the bad deployment executed database migrations.
Determine whether it performed any data writes.
Check application logs and audit records for affected operations.
If the deployment changed database structure or data, do not immediately downgrade
migrations.
Escalate to the technical lead before reversing database changes.
Application rollback and database rollback are separate decisions.
1.3 Stop unsafe application activity
If the application is actively corrupting data, stop or isolate the affected application instance.
Prevent users from performing the affected operation.
If necessary, temporarily put the application into maintenance mode.
Do not delete or edit suspicious records simply because they appear incorrect.
1.4 Roll back application code
Deploy the last known-good application version.
Use the existing production deployment mechanism.
Confirm that the application starts successfully.
Confirm Django can connect to PostgreSQL.
Confirm object-storage access works.
Confirm JWT authentication works.
Confirm health checks pass.
1.
2.
3.
4.
5.
6.
7.
8.
9.
10.
1.
2.
3.
4.
5.
1.
2.
3.
4.
1.
2.
3.
4.
5.
6.
7.
2

---

<!-- Page 3 -->

1.5 Handle migrations carefully
If the bad deployment introduced a migration:
Identify the migration that was applied.
Determine whether the migration changed only schema or also changed data.
Check whether the migration is compatible with the last known-good application version.
Do not blindly run a migration downgrade.
If schema rollback is safe and explicitly approved, perform it using the project's migration procedure.
If data was transformed or deleted, use the database recovery procedure instead of attempting an
unsafe manual reversal.
1.6 Validate the rollback
After the previous application version is running:
Test login.
Test role/permission enforcement.
Test student search and detail.
Test the affected workflow.
Test database connectivity.
Test object-storage access if documents are involved.
Check application errors.
Confirm no new integrity problems are appearing.
Confirm audit events are still being recorded.
1.7 Close the rollback
Keep the incident under observation.
Preserve logs from the failed deployment.
Preserve the failed application version and deployment information.
Record exactly what was rolled back.
Do not redeploy the failed version until the cause has been understood and reviewed.
2. Restore from Database Backup
Use this procedure when PostgreSQL data is corrupted, deleted, or otherwise needs to be recovered.
The preferred approach is to restore the backup to a separate staging/recovery PostgreSQL instance
first.
1.
2.
3.
4.
5.
6.
1.
2.
3.
4.
5.
6.
7.
8.
9.
1.
2.
3.
4.
5.
3

---

<!-- Page 4 -->

Steps
2.1 Stop further writes
Put the application into maintenance mode if continued writes could worsen the incident.
Stop background workers or import processing that can write to PostgreSQL.
Do not attempt manual corrections while the recovery point is being established.
Preserve the current database before replacing or restoring anything.
2.2 Identify the recovery target
Determine the approximate time immediately before the corruption occurred.
Identify the latest valid base backup before that point.
Identify available WAL archives covering the required period.
Determine the desired recovery timestamp.
Record the selected recovery point.
Prefer the latest safe point before corruption, not simply the newest available backup.
2.3 Restore to a staging/recovery PostgreSQL instance
Provision or select an isolated PostgreSQL recovery instance.
Restore the latest known-good base backup.
Configure WAL recovery.
Replay archived WAL up to the selected recovery timestamp.
Allow recovery to complete.
Do not point the production application at this database yet.
2.4 Verify the recovered database
Check:
PostgreSQL starts normally.
Expected tables exist.
Foreign-key relationships are intact.
Expected row counts are plausible.
Student records are present.
Academic enrollments are present.
Documents metadata is present.
Finance records are present.
Results and historical versions are present.
Audit records covering the incident period are present.
For a suspected corruption incident, compare the recovered state with the current production state.
1.
2.
3.
4.
1.
2.
3.
4.
5.
1.
2.
3.
4.
5.
6.
1.
2.
3.
4.
5.
6.
7.
8.
9.
10.
4

---

<!-- Page 5 -->

2.5 Validate application compatibility
Against the recovered database:
Start the last known-good application version.
Test authentication.
Test representative read operations.
Test representative write operations in a safe recovery environment.
Test document metadata and object-storage references.
Test finance read paths.
Test results read paths.
Test audit visibility.
Do not perform production writes until the recovery state is approved.
2.6 Decide the recovery strategy
There are two possible outcomes:
A. Full database replacement
Use when the production database must be restored to the selected recovery point.
B. Targeted recovery
Use when only specific records require recovery and replacing the entire database would unnecessarily
discard valid post-incident activity.
Targeted recovery must preserve existing valid history and must be performed through the owning
module's correction/recovery mechanism where possible.
2.7 Promote the recovered database
Only after verification and approval:
Stop production application writes.
Take a final backup of the current production database.
Confirm the recovered database is the approved recovery point.
Promote the recovered database.
Update the application database configuration.
Start the application.
Run health checks.
Verify authentication.
Verify representative student, document, finance, and result operations.
Confirm audit logging works.
Re-enable normal traffic.
1.
2.
3.
4.
5.
6.
7.
8.
1.
2.
3.
4.
5.
6.
7.
8.
9.
10.
11.
5

---

<!-- Page 6 -->

2.8 After recovery
Record the exact recovery timestamp.
Record the backup and WAL sources used.
Record data potentially lost after the recovery point.
Identify operations that must be reconstructed.
Use controlled correction/reversal workflows rather than silently recreating history.
Preserve the original incident evidence.
3. Rotate a Leaked Secret
Use this procedure when a JWT signing key, database credential, object-storage credential, or other
application secret may have been exposed.
Secrets must never be hardcoded or exposed in logs, source code, browser code, or configuration
committed to the repository.
3.1 Immediate containment
Treat the secret as compromised.
Do not investigate by repeatedly using the leaked secret.
Identify where the secret was exposed.
Record the exposure location and approximate exposure time.
Remove the exposed secret from the exposed location where appropriate.
Preserve evidence before deleting logs or artifacts.
3.2 Rotate JWT signing key
Generate a new strong JWT signing key using the approved secret-management mechanism.
Do not generate or store the new key in source control.
Update the production secret configuration.
Restart/redeploy the Django application using the normal deployment process.
Confirm new authentication tokens are signed with the new key.
Confirm old tokens behave according to the application's approved JWT rotation policy.
If the old key may have been used by an attacker, invalidate/revoke affected sessions or tokens
according to the application's supported mechanism.
Test:
Login
Token refresh
Protected API access
Logout/session invalidation
Role enforcement
1.
2.
3.
4.
5.
6.
1.
2.
3.
4.
5.
6.
1.
2.
3.
4.
5.
6.
7.
8.
9.
10.
11.
12.
13.
6

---

<!-- Page 7 -->

If the current JWT architecture does not provide selective token revocation, treat the key rotation as
requiring broad token invalidation according to the application's configured JWT policy.
3.3 Rotate database credentials
Create or obtain a replacement PostgreSQL credential.
Grant it only the permissions required by the application.
Update the production secret configuration.
Confirm the Django application can connect using the new credential.
Restart/redeploy the application.
Confirm database operations work.
Revoke the compromised credential.
Verify that no application process still depends on the old credential.
Do not expose database credentials in logs while testing.
3.4 Rotate object-storage credentials
Create replacement object-storage credentials with the minimum required permissions.
Update the server-side configuration.
Restart/redeploy the application.
Test:
Document upload
Document retrieval
Secure document access
Replacement/versioning
Revoke the compromised object-storage credentials.
Confirm credentials were never sent to the React frontend.
Object-storage credentials must not be exposed to the frontend.
3.5 Investigate possible use of the leaked secret
Identify the exposure period.
Review authentication logs where available.
Review audit records for unusual privileged activity.
Review sensitive-data reveal events.
Review role/permission changes.
Review financial operations.
Review student-data corrections.
Review document operations.
Review result approval/publication/correction activity.
Treat unexplained sensitive actions as potential security incidents.
Do not assume that rotating the secret alone resolves unauthorized actions that already occurred.
1.
2.
3.
4.
5.
6.
7.
8.
1.
2.
3.
4.
5.
6.
7.
8.
9.
10.
1.
2.
3.
4.
5.
6.
7.
8.
9.
10.
7

---

<!-- Page 8 -->

4. Respond to a Suspected Data-Integrity Incident
Examples:
Duplicate student records
Duplicate payment
Incorrect student correction
Incorrect verification decision
Incorrect document replacement
Incorrect result publication
The first rule is:
Do not immediately edit or delete the suspicious record.
The architecture deliberately preserves original history and uses additive correction, reversal, replacement,
and supersession.
4.1 Contain the incident
Confirm the reported problem.
Identify the affected student, payment, result, document, or other record.
Identify the approximate incident time.
If the operation is still occurring, stop the affected workflow.
Do not modify the affected records yet.
4.2 Preserve evidence
Collect:
Audit records.
Application logs.
Database transaction timestamps where available.
Actor information.
Request identifiers where available.
Import-batch information if imports are involved.
Relevant document/version information if documents are involved.
Relevant payment/result/version information if finance/results are involved.
Never put sensitive values into the incident report.
•
•
•
•
•
•
1.
2.
3.
4.
5.
1.
2.
3.
4.
5.
6.
7.
8.
8

---

<!-- Page 9 -->

4.3 Establish the timeline
Build a simple timeline:
What existed before the incident?
Which actor performed the operation?
What operation was performed?
Which target record was affected?
When did it occur?
Was a second operation performed?
Was there a retry?
Was there an import or background operation involved?
Was the operation authorized?
What state transitions occurred?
The accountable-actor model requires Actor + Action + Target + Timestamp + Reason where applicable.
4.4 Investigate duplicate students
For duplicate student records:
Identify all potentially duplicated student records.
Compare authoritative identifiers.
Check Application ID.
Check Enrollment Number.
Check Board/University Enrollment Number.
Check the relevant import batch and staging rows.
Review matching decisions.
Review whether the same source row was processed more than once.
Review audit history.
Determine whether the records are actually duplicates or legitimately separate students.
Do not merge automatically.
The established matching order is:
Application ID → Enrollment Number → Board/University Enrollment Number.
Conflicting matches require manual review and explicit resolution.
4.5 Investigate duplicate payments
For a suspected duplicate payment:
Identify the affected charge.
List all payment ledger entries associated with that charge.
Record each payment's actor and timestamp.
1.
2.
3.
4.
5.
6.
7.
8.
9.
10.
1.
2.
3.
4.
5.
6.
7.
8.
9.
10.
1.
2.
3.
9

---

<!-- Page 10 -->

Review the audit trail.
Determine whether the same payment operation was submitted twice.
Determine whether the charge was already paid when the second operation occurred.
Determine whether a retry or concurrency problem occurred.
Preserve both financial events.
Do not delete one of the payment records.
The Finance model treats payment as an append-only financial event. An erroneous payment is corrected
with a reversal/correction entry rather than by editing or deleting the original payment.
4.6 Correct the incident
Once the cause is established:
Identify the owning bounded context.
Use that module's correction mechanism.
Record the accountable actor.
Record the reason.
Preserve the original record.
Create the appropriate correction/reversal/replacement/supersession.
Verify the resulting state.
Confirm the audit trail records the corrective action.
Examples:
Student data → Student Management correction
Payment → Finance reversal
Published result → Result supersession
Document → Document replacement
Verification → New decision/state transition
Do not create a generic cross-domain correction mechanism.
4.7 Close the integrity incident
Verify that the current state is correct.
Verify historical records remain intact.
Verify the correction is auditable.
Verify the underlying defect has been contained.
Add regression coverage for the failure where appropriate.
Record the incident cause and corrective action.
5. Respond to a Failed Government Import Batch
Government data must pass through:
4.
5.
6.
7.
8.
9.
1.
2.
3.
4.
5.
6.
7.
8.
•
•
•
•
•
1.
2.
3.
4.
5.
6.
10

---

<!-- Page 11 -->

Source File → Import Batch → Staging Rows → Validation → Normalization → Deduplication →
Production Records
The import pipeline must preserve original rows and support explicit processing states.
5.1 Identify the batch
Obtain the import batch ID.
Identify the uploaded source file.
Record:
Batch ID
Upload time
Uploading actor
Source filename
Current batch state
Do not re-upload the file immediately.
5.2 Determine the batch state
Check the import state:
UPLOADED
VALIDATING
VALIDATED
IMPORTING
COMPLETED
FAILED
PARTIALLY_COMPLETED
CANCELLED
Do not infer completion merely from the existence of some student records.
5.3 Inspect staging rows
For the affected batch:
Count total staging rows.
Count rows successfully validated.
Count rows with validation errors.
Count rows awaiting processing.
Count rows associated with existing students.
Count rows that resulted in new students.
Count rows marked as conflicts.
Count rows that failed processing.
1.
2.
3.
4.
5.
6.
7.
8.
9.
•
•
•
•
•
•
•
•
1.
2.
3.
4.
5.
6.
7.
8.
11

---

<!-- Page 12 -->

Identify the resulting student IDs where available.
The staging layer should preserve:
Original row
Row number
Raw data
Normalized values
Validation errors
Processing status
Resulting student ID
5.4 Determine what succeeded
For each successfully processed row:
Identify the resulting student.
Confirm the student record exists.
Confirm the relevant academic enrollment exists where applicable.
Confirm the source association is recorded.
Confirm no duplicate student was created.
Confirm the audit trail contains the relevant operation.
Do not assume every successful staging row created a new student. A valid row may have matched an
existing student.
5.5 Determine what failed
For failed rows:
Read the staging-row error.
Classify the failure:
Validation failure
Normalization failure
Matching conflict
Database/integrity failure
Processing failure
External/storage failure
Preserve the original source row.
Do not manually alter the source row to hide the failure.
Record the affected row numbers.
9.
•
•
•
•
•
•
•
1.
2.
3.
4.
5.
6.
1.
2.
3.
4.
5.
6.
7.
8.
9.
10.
11.
12

---

<!-- Page 13 -->

5.6 Handle conflicts
If the import reports conflicting student matches:
Identify the conflicting identifiers.
Review the Application ID.
Review Enrollment Number.
Review Board/University Enrollment Number.
Compare the candidate student records.
Review the audit trail.
Manually resolve the conflict.
Record the resolution and accountable actor.
Do not automatically merge records.
5.7 Handle PARTIALLY_COMPLETED
If the batch is PARTIALLY_COMPLETED :
Treat successfully processed rows as already processed.
Do not blindly rerun the entire source file.
Identify failed/unprocessed rows.
Verify the import's idempotency behavior.
Resolve the underlying failure.
Reprocess only through the approved import mechanism.
Confirm previously successful rows are not duplicated.
Re-uploading the same source data must not create duplicate students.
5.8 Handle FAILED
If the batch is FAILED :
Determine whether any rows were processed before failure.
Inspect staging-row statuses.
Inspect application errors.
Inspect database errors.
Inspect audit records.
Determine whether the failure occurred before or after production writes.
Do not assume FAILED  means zero records were created.
Verify the database state before retrying.
5.9 Retry
Only after investigation:
Resolve the underlying problem.
Confirm the import mechanism is safe to retry.
Confirm idempotency protections are functioning.
1.
2.
3.
4.
5.
6.
7.
8.
9.
1.
2.
3.
4.
5.
6.
7.
1.
2.
3.
4.
5.
6.
7.
8.
1.
2.
3.
13

---

<!-- Page 14 -->

Retry through the approved import workflow.
Monitor the batch state.
Verify successful and failed row counts afterward.
Verify no duplicates were introduced.
5.10 Close the import incident
Confirm the final batch state.
Confirm every source row has a known outcome.
Confirm conflicts have explicit resolutions.
Confirm production records are correct.
Confirm audit history exists.
Preserve the original failed batch for investigation.
6. Handle a Suspected Unauthorized Sensitive-
Data Reveal
Sensitive information includes:
Aadhaar
Bank details
Sensitive personal information
Sensitive documents
The default is masked information. Full values require an explicit authorized reveal action, permission
check, decryption, temporary access, and audit event.
6.1 Contain the incident
Treat the reveal as potentially unauthorized until verified.
Identify the affected sensitive resource.
Identify the approximate reveal time.
Identify the user/account involved if known.
If unauthorized access may still be occurring, temporarily disable the affected account or permission
according to the authorization procedure.
Do not delete the user's account before preserving audit evidence.
6.2 Check the reveal audit trail
Search the audit trail for the sensitive resource and time period.
Confirm:
Actor.
4.
5.
6.
7.
1.
2.
3.
4.
5.
6.
•
•
•
•
1.
2.
3.
4.
5.
6.
1.
14

---

<!-- Page 15 -->

Action.
Target/resource.
Timestamp.
Context/reason where recorded.
Authorization information where available.
Related request/session information where available.
Every sensitive-data reveal must itself be an audit event.
6.3 Determine whether the reveal was authorized
Compare the audit event with the actor's effective permissions at the time.
Check:
User identity.
Role.
Permission.
Scope.
Target student/resource.
Reason/context.
Whether the actor should have had access.
Whether the request originated through the expected application path.
Do not rely on frontend visibility or hidden UI controls when determining authorization. Authorization is
enforced server-side.
6.4 Check for repeated or broader access
Search the audit trail for:
Other sensitive reveals by the same actor.
Other reveals against the same student.
Other reveals of the same sensitive data type.
Unusual access immediately before or after the incident.
Role/permission changes.
Login anomalies where available.
Other administrative actions performed by the same account.
Do not assume a single suspicious event is isolated until the relevant audit window has been reviewed.
6.5 If the reveal was authorized
Record the investigation result.
Confirm the actor had the required permission.
Confirm the resource was within the actor's scope.
Confirm the reveal was correctly audited.
Close the security alert if no other evidence indicates misuse.
2.
3.
4.
5.
6.
7.
1.
2.
3.
4.
5.
6.
7.
8.
1.
2.
3.
4.
5.
6.
7.
1.
2.
3.
4.
5.
15

---

<!-- Page 16 -->

6.6 If the reveal was unauthorized
Disable or restrict the affected account if appropriate.
Preserve all relevant audit records.
Preserve application/security logs.
Review role and permission changes.
Rotate credentials if compromise is suspected.
Determine which sensitive resources may have been exposed.
Determine the exposure window.
Escalate according to the organization's security/privacy incident process.
Do not expose the sensitive values again during investigation.
Do not place sensitive values in incident tickets, logs, screenshots, or debugging output.
Sensitive values must never appear in logs, debug output, exception messages, analytics payloads,
unnecessary API responses, or committed test fixtures.
6.7 After containment
Identify the authorization or application failure.
Correct the permission/configuration/code defect.
Test that unauthorized users cannot reveal the data.
Test that authorized users can still perform legitimate reveals.
Confirm every legitimate reveal generates an audit event.
Review whether additional accounts or resources were affected.
Record the incident and corrective actions.
7. General Incident Rules
Use these rules during every incident.
7.1 Preserve evidence
Never:
Delete audit records
Delete suspicious financial records
Delete duplicate student records before investigation
Overwrite published results
Overwrite document versions
Rewrite government-source history
Remove evidence simply to make the current state appear correct
The architecture explicitly requires historical evidence to remain accessible.
1.
2.
3.
4.
5.
6.
7.
8.
9.
10.
1.
2.
3.
4.
5.
6.
7.
•
•
•
•
•
•
•
16

---

<!-- Page 17 -->

7.2 Identify the owner
Before making a correction, identify which bounded context owns the affected business fact.
Use the owning module's correction semantics:
Incident
Owner
Corrective pattern
Student data
Student Management
Controlled data correction
Government-source data
Student Management
Additive correction
Verification decision
Verification
New state/decision
Document
Documents
Replacement/versioning
Payment
Finance
Reversal/correction
Published result
Results
Result supersession
User/permission change
Identity
Controlled administrative change
Service request
Services
New accountable state/action
7.3 Never "fix" history by overwriting it
The correct sequence is generally:
Original evidence → Investigation → Authorized corrective action → New state/value/event → Audit
record
Not:
Wrong record → DELETE/overwrite → pretend it never happened
7.4 Protect sensitive information
During incidents:
Use masked values wherever possible.
Do not copy Aadhaar numbers or bank account numbers into tickets.
Do not paste sensitive values into chat or email.
Do not include sensitive values in screenshots.
Do not add sensitive values to logs while debugging.
Use student IDs or other non-sensitive internal references where sufficient.
1.
2.
3.
4.
5.
6.
17

---

<!-- Page 18 -->

7.5 Escalate when uncertain
Stop and escalate to the technical lead when:
Database history may need to be changed.
A migration may need to be reversed.
A payment may need correction.
Published academic history may be affected.
A government-source value may need correction.
A secret may have been compromised.
Sensitive data may have been exposed.
Audit evidence appears incomplete.
The correct recovery point is unclear.
A proposed fix would destroy historical evidence.
When uncertain, preserve the current evidence and investigate before changing the data.
8. Incident Closure Checklist
Before declaring an incident closed, confirm:
[ ] Immediate damage has been contained.
[ ] Evidence has been preserved.
[ ] The affected records have been identified.
[ ] The audit trail has been reviewed.
[ ] The accountable actor has been identified where applicable.
[ ] The owning bounded context has been identified.
[ ] The corrective action uses the owning module's semantics.
[ ] Historical evidence remains intact.
[ ] No sensitive information was exposed during investigation.
[ ] Database integrity has been verified.
[ ] Application health has been verified.
[ ] Authentication and authorization have been tested.
[ ] Relevant workflows have been tested.
[ ] Monitoring/logs show the incident has stopped.
[ ] Regression coverage has been added where appropriate.
[ ] The incident cause has been documented.
[ ] The corrective action has been documented.
[ ] Any required human/security/operational escalation has been completed.
9. Core Operating Principle
When production data looks wrong:
•
•
•
•
•
•
•
•
•
•
•
•
•
•
•
•
•
•
•
•
•
•
•
•
•
•
•
•
18

---

<!-- Page 19 -->

Do not immediately make it look right.
First:
Preserve → Identify → Audit → Investigate → Authorize → Correct/Revert → Verify → Record
The system is designed around accountability, detectability, and recoverability, not silent rewriting of
history.
19
