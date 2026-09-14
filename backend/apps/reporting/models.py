"""
Reporting Models.

Per Architecture Section 12 and PRD Section 6:
Reporting does not own operational business database tables.
It consumes authoritative domain data via module-owned query interfaces.
Derived materialized projections are only introduced if actual query/load
evidence demonstrates necessity.
"""
# No operational tables owned.
