<!-- Page 1 -->

Production Definition of Done Checklist
Run this checklist before every feature ships.
Code & Architecture
[ ] Requirements are understood
[ ] Feature is implemented as a vertical slice, tested end-to-end
[ ] Ownership is clear
[ ] Dependencies are understood
[ ] New logic lives in a deep module with a small public interface
[ ] No duplicated logic — checked against existing modules before writing new code
[ ] No unrelated files touched outside declared task scope
[ ] No unrelated architecture is introduced
[ ] Failure cases are handled
[ ] Historical behavior is correct
[ ] Queries are bounded
[ ] N+1 is avoided
[ ] Code has been self-reviewed
Security
[ ] Authentication is enforced
[ ] Authorization is enforced server-side
[ ] All inputs are validated server-side
[ ] No secrets are present in code or version control
[ ] Parameterized queries / ORM only, no string-built queries
[ ] Rate limiting is in place on sensitive endpoints
[ ] Sensitive data is protected
[ ] Audit requirements are satisfied
[ ] Idempotency is handled on state-changing/payment operations
Data
[ ] Every entity has exactly one source-of-truth table/service
[ ] Financial changes are recorded as immutable ledger entries, not overwritten fields
[ ] Historical behavior is correct
[ ] Migrations are safe, reversible, and tested
Testing
[ ] Unit tests are written before/alongside implementation
[ ] Integration tests are written before/alongside implementation
[ ] Critical flows are covered by end-to-end tests
[ ] Business rules are tested
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
•
•
1

---

<!-- Page 2 -->

[ ] Security-relevant test cases are included
[ ] A regression test is added for any bug fixed
[ ] Tests pass
CI/CD & Ops
[ ] Tests, types, and lint pass automatically before merge
[ ] The feature has been tested in a staging environment matching production
[ ] Rollback path is confirmed before deploying
[ ] Logging, monitoring, and alerts are in place for the new code path
Documentation
[ ] Non-obvious decisions are recorded as an ADR
[ ] Module README is updated
Human Checkpoint
[ ] If this task touches authentication/authorization, payments, database migrations, or
infrastructure/deployment configuration: it has been independently reviewed by a fresh-context AI
session and read by a human before shipping
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
2
