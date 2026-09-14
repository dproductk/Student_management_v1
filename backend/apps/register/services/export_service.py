"""
Register Export Service.
Implements Task 8.5: Register export/printable-data vertical slice.
Generates bounded, authorized CSV and printable export data with sensitive fields strictly masked.
"""

import csv
import io
from typing import Dict, Any, Optional
from apps.register.services.register_query_service import RegisterQueryService


class RegisterExportService:
    """Handles bounded administrative exports conforming to data protection boundaries."""

    MAX_EXPORT_ROWS = 5000

    CSV_HEADERS = [
        'Application ID',
        'Enrollment No',
        'Candidate Name',
        'Gender',
        'Date of Birth',
        'Category',
        'Department Code',
        'Department Name',
        'Program Code',
        'Batch',
        'Academic Year',
        'Semester',
        'Student Status',
        'Verification Status',
        'Masked Aadhaar',
        'Email',
        'Mobile'
    ]

    @classmethod
    def export_register_csv(
        cls,
        user,
        filters: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generates a CSV string representation of filtered register records.
        Enforces MAX_EXPORT_ROWS safety bound and sensitive-data protection.
        """
        result_data = RegisterQueryService.query_student_register(
            user=user,
            filters=filters,
            limit=cls.MAX_EXPORT_ROWS,
            offset=0
        )

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(cls.CSV_HEADERS)

        for row in result_data['results']:
            writer.writerow([
                row.get('application_id') or '',
                row.get('enrollment_no') or '',
                row.get('candidate_name') or '',
                row.get('gender') or '',
                row.get('date_of_birth') or '',
                row.get('category') or '',
                row.get('department_code') or '',
                row.get('department_name') or '',
                row.get('program_code') or '',
                row.get('batch_name') or '',
                row.get('academic_year') or '',
                row.get('semester_number') or '',
                row.get('status') or '',
                row.get('verification_status') or '',
                row.get('aadhaar_masked') or '',
                row.get('email') or '',
                row.get('student_mobile') or '',
            ])

        return output.getvalue()
