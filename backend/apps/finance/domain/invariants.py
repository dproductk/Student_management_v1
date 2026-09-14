"""
Finance domain invariants and business rules.
Implements:
- Historical fee structure protection (ADR-010)
- Duplicate-payment protection and paid-charge state transition guards
- Append-only ledger rules and reversal validation
"""

from decimal import Decimal
from common.exceptions import InvariantViolationError


def validate_fee_structure_lock(is_locked: bool) -> None:
    """
    Prevents modifying historical fee structures once locked / charges generated.
    """
    if is_locked:
        raise InvariantViolationError(
            "Historical fee structure is locked because student charges have been generated from it. Changes are rejected."
        )


def validate_fee_amount(amount: Decimal) -> None:
    """
    Validates positive fee and charge amounts.
    """
    if amount is None or amount <= Decimal('0.00'):
        raise InvariantViolationError("Fee amount must be strictly greater than zero.")


def validate_payment_recording(charge_status: str, remaining_balance: Decimal, payment_amount: Decimal) -> None:
    """
    Guards payment recording:
    - Rejects recording payment on an already-paid charge (Task 9.3.2)
    - Rejects payment amounts exceeding outstanding charge balance
    - Rejects non-positive payments
    """
    validate_fee_amount(payment_amount)

    if charge_status == 'PAID' or remaining_balance <= Decimal('0.00'):
        raise InvariantViolationError(
            "Attempting to mark an already-paid charge as paid again is rejected."
        )

    if payment_amount > remaining_balance:
        raise InvariantViolationError(
            f"Payment amount ({payment_amount}) exceeds the remaining charge balance ({remaining_balance})."
        )


def validate_reversal(original_entry, reversal_reason: str) -> None:
    """
    Guards payment reversal:
    - Must reference a valid PAYMENT entry
    - Cannot reverse an already reversed payment
    - Reversal reason must be explicitly provided
    """
    if not original_entry:
        raise InvariantViolationError("A financial reversal must reference an existing original payment entry.")

    if original_entry.entry_type != 'PAYMENT':
        raise InvariantViolationError("Only standard payment ledger entries can be reversed.")

    if original_entry.reversals.exists():
        raise InvariantViolationError("This payment entry has already been reversed.")

    if not reversal_reason or not reversal_reason.strip():
        raise InvariantViolationError("A financial reversal requires an accountable justification/reason.")
