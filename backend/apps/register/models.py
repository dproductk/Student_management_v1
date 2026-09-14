"""
Register & Administrative Dashboards module.
Per ARCHITECTURE.md Section 12 and PRD-8:
Register operates as a read-oriented projection capability that queries authoritative
entities from Student Management, Academic Foundation, and Verification.
It does not own or duplicate database tables.
"""

from django.db import models

# No persistent tables owned by Register.
