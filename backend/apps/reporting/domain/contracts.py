"""
Reporting Query Contract Foundation.

Defines standard read-only query parameter specifications, pagination bounds,
and structured result envelopes per Task 14.1.1.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import date
from common.exceptions import DomainException


class ReportingValidationError(DomainException):
    """Raised when query specifications violate bounds or validation rules."""
    pass


DEFAULT_PAGE_LIMIT = 50
MAX_PAGE_LIMIT = 500
MAX_EXPORT_LIMIT = 5000


@dataclass(frozen=True)
class ReportFilterSpec:
    """Standardized filter parameters applicable across reporting interfaces."""
    academic_year_id: Optional[str] = None
    department_id: Optional[str] = None
    program_id: Optional[str] = None
    batch_id: Optional[str] = None
    category_code: Optional[str] = None
    gender: Optional[str] = None
    status: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    search: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass(frozen=True)
class PaginationSpec:
    """Safe pagination parameters enforcing upper limits to prevent DoS."""
    limit: int = DEFAULT_PAGE_LIMIT
    offset: int = 0
    ordering: Optional[str] = None

    def __post_init__(self):
        if self.limit < 1:
            raise ReportingValidationError("Limit must be greater than 0.")
        if self.limit > MAX_EXPORT_LIMIT:
            raise ReportingValidationError(f"Limit exceeds maximum allowed bounds ({MAX_EXPORT_LIMIT}).")
        if self.offset < 0:
            raise ReportingValidationError("Offset cannot be negative.")


@dataclass
class ReportQueryResult:
    """Structured report output envelope."""
    total_count: int
    items: List[Dict[str, Any]]
    filters_applied: Dict[str, Any] = field(default_factory=dict)
    summary_metrics: Dict[str, Any] = field(default_factory=dict)
