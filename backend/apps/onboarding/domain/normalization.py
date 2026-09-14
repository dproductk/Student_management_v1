"""
Data normalization utilities for student onboarding imports.
"""

import re
from datetime import datetime


def clean_header_key(key: str) -> str:
    """Normalize Excel header names to snake_case identifier."""
    k = str(key).strip().lower()
    k = re.sub(r'[\s\.\-\/\(\)]+', '_', k)
    k = re.sub(r'[^a-z0-9_]', '', k)
    return k.strip('_')


KEY_MAPPINGS = {
    'candidate_name': ['candidate_name', 'name', 'student_name', 'full_name', 'applicant_name'],
    'father_name': ['father_name', 'fathers_name', 'father_s_name', 'fathername'],
    'mother_name': ['mother_name', 'mothers_name', 'mother_s_name', 'mothername'],
    'gender': ['gender', 'sex'],
    'date_of_birth': ['date_of_birth', 'dob', 'birth_date'],
    'application_id': ['application_id', 'app_id', 'application_no', 'merit_no', 'seat_allotment_id'],
    'enrollment_no': ['enrollment_no', 'enrollment_number', 'prn', 'registration_no'],
    'board_enrollment_no': ['board_enrollment_no', 'board_roll_no', 'msbte_enrollment_no'],
    'student_mobile': ['student_mobile', 'mobile', 'phone', 'contact_no', 'mobile_no'],
    'parent_mobile': ['parent_mobile', 'father_mobile', 'guardian_mobile', 'phone_no'],
    'email': ['email', 'email_id', 'e_mail_id', 'student_email'],
    'category': ['category', 'admission_category', 'caste_category'],
    'religion': ['religion'],
    'mother_tongue': ['mother_tongue', 'mothertongue', 'mother_language'],
    'candidature_type': ['candidature_type', 'candidature', 'candidaturetype'],
    'address_line_1': ['address_line_1', 'addressline1'],
    'address_line_2': ['address_line_2', 'addressline2'],
    'address_line_3': ['address_line_3', 'addressline3'],
    'state': ['state'],
    'district': ['district', 'dist'],
    'taluka': ['taluka', 'tehsil', 'taluk'],
    'village': ['village'],
    'pincode': ['pincode', 'pin_code', 'postal_code', 'zip'],
    'seat_type': ['seat_type', 'allotted_seat_type', 'quota'],
    'choice_code': ['choice_code', 'choicecode', 'choice_code_of_allotment', 'allotted_choice_code'],
    'program_code': ['program_code', 'course_code', 'branch_code', 'program'],
    'aadhaar_number': ['aadhaar_number', 'aadhaar', 'uidai_no', 'aadhar_no'],
    'region': ['region'],
    'merit_marks': ['merit_marks', 'marks', 'aggregate_marks', 'total_marks', 'merit_no'],
    'annual_family_income': ['annual_family_income', 'family_income', 'income', 'annual_income'],
    'admission_date': ['admission_date', 'date_of_admission', 'doa'],
    'address': ['address', 'full_address', 'permanent_address', 'correspondence_address'],
}


def normalize_row_dict(raw_row: dict) -> dict:
    """Map raw Excel key-value pairs into normalized student dictionary."""
    normalized = {}
    cleaned_raw = {clean_header_key(k): v for k, v in raw_row.items() if k is not None}

    for target_key, aliases in KEY_MAPPINGS.items():
        for alias in aliases:
            if alias in cleaned_raw and cleaned_raw[alias] is not None:
                val = str(cleaned_raw[alias]).strip()
                if val:
                    normalized[target_key] = val
                    break

    # 1. Normalize Gender
    if 'gender' in normalized:
        g = normalized['gender'].upper()
        if g.startswith('M'):
            normalized['gender'] = 'MALE'
        elif g.startswith('F'):
            normalized['gender'] = 'FEMALE'
        else:
            normalized['gender'] = 'OTHER'

    # 2. Normalize Date of Birth to YYYY-MM-DD
    if 'date_of_birth' in normalized:
        dob_str = str(normalized['date_of_birth']).strip()
        parsed_date = None
        for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d', '%d.%m.%Y'):
            try:
                parsed_date = datetime.strptime(dob_str.split('T')[0].split(' ')[0], fmt).date()
                break
            except ValueError:
                continue
        if parsed_date:
            normalized['date_of_birth'] = parsed_date.strftime('%Y-%m-%d')

    # 3. Clean numeric identifiers
    if 'student_mobile' in normalized:
        normalized['student_mobile'] = re.sub(r'[^0-9]', '', normalized['student_mobile'])[-10:]
    if 'parent_mobile' in normalized:
        normalized['parent_mobile'] = re.sub(r'[^0-9]', '', normalized['parent_mobile'])[-10:]
    if 'aadhaar_number' in normalized:
        normalized['aadhaar_number'] = re.sub(r'[^0-9]', '', normalized['aadhaar_number'])[-12:]
    if 'pincode' in normalized:
        digits = re.sub(r'[^0-9]', '', normalized['pincode'])
        if digits:
            normalized['pincode'] = digits[-6:]

    # 4. Normalize admission date to YYYY-MM-DD (Excel uses DD/MM/YYYY)
    if 'admission_date' in normalized:
        ad_str = str(normalized['admission_date']).strip()
        parsed_ad = None
        for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d', '%d.%m.%Y'):
            try:
                parsed_ad = datetime.strptime(ad_str.split('T')[0].split(' ')[0], fmt).date()
                break
            except ValueError:
                continue
        if parsed_ad:
            normalized['admission_date'] = parsed_ad.strftime('%Y-%m-%d')

    # 4. Standardize text uppercase identifiers
    for id_field in ['application_id', 'enrollment_no', 'board_enrollment_no', 'program_code', 'choice_code']:
        if id_field in normalized:
            normalized[id_field] = normalized[id_field].upper()

    return normalized
