# Feature: Fees & Finance

## 1. Problem

The system needs an internal fee-management capability that allows the college to configure fee structures, determine applicable fees for students, record charges and payments, and preserve financial history.

Finance is the authoritative source of truth for fee status. The architecture explicitly does **not** include reconciliation with an external payment system. Payments are append-only financial events, and corrections are performed through reversal/correction entries rather than editing or deleting the original payment.

---

## 2. Goal

Build the **Finance** bounded context to provide:

- Fee-head configuration
- Fee structures and fee-structure items
- Historical fee-structure protection
- Student fee accounts
- Applicable-fee determination and charge generation
- Accountant fee-status search and student fee detail
- Append-only payment recording
- Duplicate-payment protection
- Paid-charge state transition
- Financial reversal/correction
- Accountable financial history and audit

---

## 3. User Stories

- As an authorized administrator, I want to configure fee heads.
- As an authorized administrator, I want to define fee structures for applicable academic contexts.
- As the system, I want historical fee structures to remain protected when new structures are introduced.
- As an authorized accountant, I want to see a student's applicable fees and charges.
- As an authorized accountant, I want to record a student's payment.
- As the system, I want to prevent duplicate payment recording.
- As an authorized user, I want mistaken payments corrected through a controlled reversal rather than destructive editing.
- As an authorized user, I want financial actions to remain attributable and historically explainable.

---

## 4. Scope — Files/Modules Touched

### 4.1 Fee Configuration

1. **Fee-head configuration vertical slice**
   - Depends on Academic Foundation and Identity authorization.
2. **Fee-structure and fee-structure-item vertical slice**
   - Depends on Fee-head configuration and Academic year/semester management.
3. **Historical fee-structure protection vertical slice**
   - Depends on Fee-structure and fee-structure-item.

### 4.2 Student Charges

4. **Student fee-account vertical slice**
   - Depends on Student academic enrollment and Fee-structure/fee-structure-item.
5. **Applicable-fee and charge-generation vertical slice**
   - Depends on Student fee-account and Student category/admission-category information.
6. **Accountant fee-status search and student fee-detail vertical slice**
   - Depends on Applicable-fee/charge generation and scoped authorization.

### 4.3 Payments

7. **Append-only payment recording vertical slice**
8. **Duplicate-payment protection and paid-charge state transition vertical slice**
9. **Financial reversal/correction vertical slice**
10. **Finance accountable-actor audit and historical-ledger integrity vertical slice**

All tasks are marked **HUMAN REVIEW REQUIRED**.

---

## 5. Requirements

### 5.1 Fee Configuration

1. Finance must own fee heads.
2. Fee heads must be configurable rather than hardcoded.
3. Finance must support fee structures and fee-structure items.
4. Fee structures must reference the authoritative Academic Foundation entities where required.
5. Fee structures must support applicable academic context.
6. Historical fee structures must remain protected when new fee structures are introduced.
7. Historical student financial records must not be silently changed because a newer fee structure exists.

The source context explicitly requires fee structures to change by academic year/category/etc. without modifying historical records.

### 5.2 Student Fee Account

8. Finance must provide a student fee-account capability.
9. Student fee accounts must be associated with authoritative Student Management academic enrollment.
10. Applicable fees must be determined using the configured fee structure and relevant student information.
11. Student category/admission-category information must be obtained from Student Management rather than duplicated as Finance ownership.

### 5.3 Charges

12. Finance must generate/manage applicable student charges.
13. Charges must belong to the Finance domain.
14. Fee status must be derived from Finance's authoritative charge/payment records.
15. Finance must provide an accountant-facing student fee-status/detail capability.
16. Protected finance operations must enforce appropriate scoped authorization.

### 5.4 Payments

17. Finance must record payments as append-only financial events.
18. A payment must not be edited or deleted as a means of correction.
19. Attempting to mark an already-paid charge as paid again must be rejected.
20. Duplicate-payment protection must be implemented.
21. The appropriate charge state transition must occur when a valid payment is recorded.
22. Payment records must retain relevant payment information.
23. Payment records must identify the accountable actor and timestamp.

The authoritative flow is:

**Fee Structure → Applicable Fee → Charge → Payment Ledger Entry**

with the payment ledger serving as the financial history.

### 5.5 Financial Corrections

24. Mistaken payments must be corrected through a reversal/correction entry.
25. Original payment records must remain preserved.
26. A reversal/correction must reference the relevant original financial record.
27. Reversal/correction must record the accountable actor, timestamp, reason where applicable, and audit information.
28. Financial correction must never silently rewrite historical financial activity.

Finance-specific reversal behavior is part of the shared additive-correction architecture, while remaining owned by Finance.

### 5.6 Source of Truth

29. Finance charges and payment records are the sole source of truth for fee status.
30. No external payment-system reconciliation is required by the current architecture.
31. No external dispute/reconciliation architecture should be introduced.
32. Other modules may query Finance but must not create competing fee-status ownership.

---

## 6. Data Changes

Finance requires data representing:

- Fee heads
- Fee structures
- Fee-structure items
- Student fee accounts
- Applicable fees
- Charges
- Payments
- Payment reversals/corrections
- Financial history

Ownership:

- Fee configuration → Finance
- Charges → Finance
- Payments → Finance
- Financial history → Finance
- Student enrollment → Student Management
- Student category/admission category → Student Management
- Academic year/semester and other academic masters → Academic Foundation

The exact physical schema, field names, constraints, indexes, and payment-information fields are not finalized in the supplied architecture and must not be invented.

---

## 7. API Changes

Finance must expose application capabilities for:

- Fee-head management
- Fee-structure management
- Fee-structure-item management
- Historical fee-structure access
- Student fee-account access
- Applicable-fee/charge generation
- Accountant fee-status search
- Student fee detail
- Payment recording
- Duplicate-payment handling
- Payment reversal/correction
- Financial history/audit access

All APIs must enforce:

- Authentication
- Authorization
- Scoped authorization where applicable
- Input validation
- State-transition rules
- Bounded responses
- Safe errors
- Appropriate pagination

Exact routes, request/response schemas, permission names, payment fields, and HTTP status codes remain open.

---

## 8. Security Notes

- Finance operations require authenticated users.
- Backend authorization is mandatory.
- Accountant operations must respect the defined scoped authorization model.
- Payment recording and reversal are sensitive business actions and require accountable actors.
- Sensitive student financial information must remain masked/restricted according to the system-wide sensitive-data policy.
- Financial records must not be exposed through unrestricted endpoints.
- Duplicate submissions must be safely rejected/idempotently handled where applicable.
- Financial history must be preserved.
- No secrets or sensitive payment information should be written to logs.

---

## 9. Definition of Done

-  Fee-head configuration is implemented.
-  Fee structures are implemented.
-  Fee-structure items are implemented.
-  Historical fee-structure protection is implemented.
-  Student fee accounts are implemented.
-  Applicable-fee and charge generation is implemented.
-  Accountant fee-status search is implemented.
-  Student fee detail is implemented.
-  Payments are append-only.
-  Duplicate-payment protection is implemented.
-  Paid-charge state transition is protected.
-  Financial reversal/correction is implemented.
-  Original payment history remains intact.
-  Finance remains the sole source of truth for fee status.
-  No external payment reconciliation is introduced.
-  Accountable actor information is preserved for financial actions.
-  Financial history is auditable.
-  Authorization tests are implemented.
-  Duplicate-payment tests are implemented.
-  Reversal/correction tests are implemented.
-  Historical fee-structure integrity is tested.
-  Transaction/concurrency behavior around payment recording is tested.
-  Queries are bounded and avoid N+1/unbounded access.
-  Required human review is completed.

---

## 10. Out of Scope

- External payment gateway integration.
- External payment reconciliation.
- External payment dispute architecture.
- University payment-system integration.
- Editing/deleting historical payments.
- A separate Correction Module.
- Student enrollment ownership.
- Student category ownership.
- Academic master-data ownership.
- Scholarship functionality beyond the separately defined minimal v1 scope.
- Any financial functionality not represented in the task graph.

---

## 11. Open Questions

1. What exact fee heads are required initially?
2. What exact fee-structure dimensions are required?
3. What exact fields belong to a fee-structure item?
4. What exact rules determine applicable fees?
5. What exact student categories/admission categories affect fee calculation?
6. What exact payment information must be recorded?
7. What exact roles may configure fees?
8. What exact roles may record payments?
9. What exact roles may perform reversals?
10. What exact duplicate-payment criteria should be enforced?
11. What exact charge states are required?
12. What exact API routes and contracts are required?
13. What exact financial reports/views are required?
14. What exact retention requirements apply to financial history?

No unsupported financial rules should be invented.

---

## 12. Dependencies

**Academic Foundation + Identity authorization**
→ Fee-head configuration

**Fee-head configuration + Academic year/semester management**
→ Fee structure and fee-structure items

**Fee structure/items**
→ Historical fee-structure protection

**Student academic enrollment + Fee structure/items**
→ Student fee account

**Student fee account + Student category/admission-category**
→ Applicable fee and charge generation

**Applicable fees/charges + Scoped authorization**
→ Accountant fee-status search and student fee detail

**Accountant fee detail**
→ Append-only payment recording

**Append-only payment recording**
→ Duplicate-payment protection + paid-charge transition

**Duplicate-payment protection**
→ Financial reversal/correction

**Financial reversal/correction**
→ Finance accountable-actor audit + historical-ledger integrity

**Status:** PRD #9 — `PRD-fees-finance.md`
