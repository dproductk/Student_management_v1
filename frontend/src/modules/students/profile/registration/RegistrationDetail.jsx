import React, { useState } from 'react';
import { Download, FileText, Check } from 'lucide-react';

/**
 * Subpage 1: Registration Detail
 * Matches Government Polytechnic Kolhapur EDVANA MIS design screenshots:
 * - Academic Header (Program & Enrollment No)
 * - Personal Details
 * - Admission Details
 * - Permanent Address
 * - Correspondence Address (with toggle)
 * - Personal Information
 * - Details of Qualifying Examination for admission to GPK
 * - Receipt Cum Acknowledgement Letter Upload & Download
 */
export const RegistrationDetail = ({ student, isStaff, onSave }) => {
  const admission = student?.admissions?.[0] || {};
  const address = student?.address || {};
  const category = student?.category_info || {};
  const scholarship = student?.scholarships?.[0] || {};

  // Form State — empty until real data exists (filled by import or by the student).
  // Never show invented demo values here.
  const [formData, setFormData] = useState({
    // Academic Header
    program: admission?.program_name || '',
    enrollmentNo: student?.enrollment_no || '',

    // Personal Details
    candidateName: student?.candidate_name || '',
    applicationId: student?.application_id || '',
    fatherName: student?.father_name || '',
    motherName: student?.mother_name || '',
    placeOfBirth: student?.place_of_birth || '',
    dobDay: student?.date_of_birth ? new Date(student.date_of_birth).getDate().toString() : '',
    dobMonth: student?.date_of_birth ? new Date(student.date_of_birth).toLocaleString('en-US', { month: 'long' }) : '',
    dobYear: student?.date_of_birth ? new Date(student.date_of_birth).getFullYear().toString() : '',
    gender: student?.gender === 'FEMALE' ? 'Female' : student?.gender === 'MALE' ? 'Male' : '',

    // Admission Details
    admissionDate: admission?.admission_date || '',
    admissionType: admission?.admission_type || '',
    allottedSeatType: admission?.allotted_seat_type || admission?.seat_type || '',
    scholarshipApplied: student?.scholarships?.length > 0 ? 'Yes' : '',
    scholarshipType: scholarship?.scholarship_type || '',
    annualIncome: scholarship?.income_slab || '',

    // Permanent Address
    permAddress: address?.address_line || '',
    permDistrict: address?.district || '',
    permState: address?.state || '',
    permPincode: address?.pincode || '',

    // Correspondence Address (empty until the student provides it)
    sameAsPermanent: false,
    corrAddress: '',
    corrDistrict: '',
    corrState: '',
    corrPincode: '',

    // Personal Information
    studentEmail: student?.email || '',
    studentMobile: student?.student_mobile || '',
    parentEmail: '',
    parentMobile: student?.parent_mobile || '',
    fatherProfession: '',
    nationality: '',
    domicileState: '',
    religion: student?.religion || '',
    constitutionalCategory: category?.category || '',
    specialReservation: '',

    // Qualifying Exam (empty until the student provides it)
    examBoard: '',
    lastSchool: '',
    monthOfPassing: '',
    yearOfPassing: '',
    percentageMarks: ''
  });

  const handleToggleSameAddress = () => {
    const nextVal = !formData.sameAsPermanent;
    setFormData(prev => ({
      ...prev,
      sameAsPermanent: nextVal,
      ...(nextVal ? {
        corrAddress: prev.permAddress,
        corrDistrict: prev.permDistrict,
        corrState: prev.permState,
        corrPincode: prev.permPincode
      } : {})
    }));
  };

  const months = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];

  // Dropdown options always include the stored real value (e.g. SEBC, GOPENH,
  // Solapur) even when it is not in the default list — otherwise real data
  // would render as blank. Empty stays empty.
  const withCurrent = (value, list) =>
    value && !list.includes(value) ? [value, ...list] : list;

  const days = Array.from({ length: 31 }, (_, i) => (i + 1).toString());
  const years = Array.from({ length: 40 }, (_, i) => (2025 - i).toString());

  const cardStyle = {
    background: '#ffffff',
    borderRadius: '10px',
    border: '1px solid #e5e7eb',
    padding: '1.5rem',
    marginBottom: '1.5rem',
    boxShadow: '0 1px 2px rgba(0, 0, 0, 0.03)',
  };

  const labelStyle = {
    display: 'block',
    fontSize: '0.82rem',
    fontWeight: '600',
    color: '#1f2937',
    marginBottom: '0.45rem',
  };

  const inputStyle = {
    width: '100%',
    padding: '0.62rem 0.85rem',
    borderRadius: '6px',
    border: '1px solid #d1d5db',
    backgroundColor: '#f8fafc',
    fontSize: '0.88rem',
    color: '#1e293b',
    outline: 'none',
    boxSizing: 'border-box',
    transition: 'border-color 0.15s ease',
  };

  const headerTableStyle = {
    width: '100%',
    borderCollapse: 'collapse',
    marginBottom: '1.25rem',
    fontSize: '0.9rem',
  };

  return (
    <div>
      {/* 1. Academic Info Header Card */}
      <div style={cardStyle}>
        <h3 style={{ fontSize: '1.05rem', fontWeight: '700', color: '#111827', margin: 0, marginBottom: '1.25rem' }}>
          Student Profile
        </h3>
        <table style={headerTableStyle}>
          <tbody>
            <tr style={{ borderTop: '1px solid #f1f5f9', borderBottom: '1px solid #f1f5f9' }}>
              <td style={{ padding: '0.85rem 1.25rem', fontWeight: '700', width: '35%', color: '#111827', textAlign: 'right' }}>
                Program:
              </td>
              <td style={{ padding: '0.85rem 1.25rem', color: '#334155', fontWeight: '500' }}>
                {formData.program}
              </td>
            </tr>
            <tr style={{ borderBottom: '1px solid #f1f5f9' }}>
              <td style={{ padding: '0.85rem 1.25rem', fontWeight: '700', width: '35%', color: '#111827', textAlign: 'right' }}>
                Enrollment Number:
              </td>
              <td style={{ padding: '0.85rem 1.25rem', color: '#334155', fontWeight: '500' }}>
                {formData.enrollmentNo}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* 2. Personal Details Card */}
      <div style={cardStyle}>
        <h3 style={{ fontSize: '1.05rem', fontWeight: '700', color: '#111827', margin: 0, marginBottom: '1.25rem' }}>
          Personal Details
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.25rem', marginBottom: '1.25rem' }}>
          <div>
            <label style={labelStyle}>Full Name of the candidate <span style={{ color: '#dc2626' }}>*</span></label>
            <input
              type="text"
              readOnly
              style={{ ...inputStyle, textTransform: 'uppercase' }}
              value={formData.candidateName}
            />
          </div>
          <div>
            <label style={labelStyle}>DTE Application ID <span style={{ color: '#dc2626' }}>*</span></label>
            <input
              type="text"
              readOnly
              style={inputStyle}
              value={formData.applicationId}
            />
            <div style={{ fontSize: '0.72rem', color: '#64748b', marginTop: '0.25rem' }}>For Eg. DEN18146293</div>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.25rem', marginBottom: '1.25rem' }}>
          <div>
            <label style={labelStyle}>Father's Name <span style={{ color: '#dc2626' }}>*</span></label>
            <input
              type="text"
              readOnly
              style={{ ...inputStyle, textTransform: 'uppercase' }}
              value={formData.fatherName}
            />
          </div>
          <div>
            <label style={labelStyle}>Mother's Name (FIRST) <span style={{ color: '#dc2626' }}>*</span></label>
            <input
              type="text"
              readOnly
              style={{ ...inputStyle, textTransform: 'uppercase' }}
              value={formData.motherName}
            />
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.25rem', marginBottom: '1.25rem' }}>
          <div>
            <label style={labelStyle}>Place of Birth <span style={{ color: '#dc2626' }}>*</span></label>
            <input
              type="text"
              readOnly
              style={{ ...inputStyle, textTransform: 'uppercase' }}
              value={formData.placeOfBirth}
            />
          </div>
          <div>
            <label style={labelStyle}>Date of Birth <span style={{ color: '#dc2626' }}>*</span></label>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr 1fr', gap: '0.5rem' }}>
              <select disabled style={inputStyle} value={formData.dobDay}>
                {days.map(d => <option key={d} value={d}>{d}</option>)}
              </select>
              <select disabled style={inputStyle} value={formData.dobMonth}>
                {months.map(m => <option key={m} value={m}>{m}</option>)}
              </select>
              <select disabled style={inputStyle} value={formData.dobYear}>
                {years.map(y => <option key={y} value={y}>{y}</option>)}
              </select>
            </div>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.25rem' }}>
          <div>
            <label style={labelStyle}>Gender <span style={{ color: '#dc2626' }}>*</span></label>
            <select disabled style={inputStyle} value={formData.gender}>
              <option value="Male">Male</option>
              <option value="Female">Female</option>
              <option value="Other">Other</option>
            </select>
          </div>
        </div>
      </div>

      {/* 3. Admission Details Card */}
      <div style={cardStyle}>
        <h3 style={{ fontSize: '1.05rem', fontWeight: '700', color: '#111827', margin: 0, marginBottom: '1.25rem' }}>
          Admission Details
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1.25rem', marginBottom: '1.25rem' }}>
          <div>
            <label style={labelStyle}>Date of Admission <span style={{ color: '#dc2626' }}>*</span></label>
            <input
              type="text"
              readOnly
              style={inputStyle}
              value={formData.admissionDate}
            />
          </div>
          <div>
            <label style={labelStyle}>Admission Type <span style={{ color: '#dc2626' }}>*</span></label>
            <select disabled style={inputStyle} value={formData.admissionType}>
              {withCurrent(formData.admissionType, ['CAP', 'Against CAP', 'Institute Level', 'Direct Second Year']).map(o => <option key={o} value={o}>{o}</option>)}
            </select>
          </div>
          <div>
            <label style={labelStyle}>Allotted Seat Type <span style={{ color: '#dc2626' }}>*</span></label>
            <select disabled style={inputStyle} value={formData.allottedSeatType}>
              {withCurrent(formData.allottedSeatType, ['NT-C', 'OPEN', 'OBC', 'SC', 'ST', 'EWS']).map(o => <option key={o} value={o}>{o}</option>)}
            </select>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1.25rem' }}>
          <div>
            <label style={labelStyle}>Scholarship Applied <span style={{ color: '#dc2626' }}>*</span></label>
            <select disabled style={inputStyle} value={formData.scholarshipApplied}>
              <option value="Yes">Yes</option>
              <option value="No">No</option>
            </select>
          </div>
          <div>
            <label style={labelStyle}>Scholarship Type <span style={{ color: '#dc2626' }}>*</span></label>
            <select disabled style={inputStyle} value={formData.scholarshipType}>
              <option value="NT-C">NT-C</option>
              <option value="EBC">EBC</option>
              <option value="Post-Matric">Post-Matric</option>
              <option value="None">None</option>
            </select>
          </div>
          <div>
            <label style={labelStyle}>Father's /Guardian's Annual Income (from all sources)</label>
            <select disabled style={inputStyle} value={formData.annualIncome}>
              <option value="600000 to 700000">600000 to 700000</option>
              <option value="0 to 50000">0 to 50000</option>
              <option value="50001 to 100000">50001 to 100000</option>
              <option value="100001 to 250000">100001 to 250000</option>
              <option value="250001 to 600000">250001 to 600000</option>
              <option value="Above 800000">Above 800000</option>
            </select>
          </div>
        </div>
      </div>

      {/* 4. Permanent Address Card */}
      <div style={cardStyle}>
        <h3 style={{ fontSize: '1.05rem', fontWeight: '700', color: '#111827', margin: 0, marginBottom: '1.25rem' }}>
          Permanent Address
        </h3>
        <div style={{ marginBottom: '1.25rem' }}>
          <label style={labelStyle}>Address <span style={{ color: '#dc2626' }}>*</span></label>
          <textarea
            readOnly
            rows={3}
            style={{ ...inputStyle, resize: 'vertical' }}
            value={formData.permAddress}
          />
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.25rem' }}>
          <div>
            <label style={labelStyle}>District <span style={{ color: '#dc2626' }}>*</span></label>
            <select disabled style={inputStyle} value={formData.permDistrict}>
              {withCurrent(formData.permDistrict, ['Satara', 'Kolhapur', 'Pune', 'Sangli', 'Solapur']).map(o => <option key={o} value={o}>{o}</option>)}
            </select>
          </div>
          <div>
            <label style={labelStyle}>State <span style={{ color: '#dc2626' }}>*</span></label>
            <select disabled style={inputStyle} value={formData.permState}>
              {withCurrent(formData.permState, ['Maharashtra', 'Goa', 'Karnataka']).map(o => <option key={o} value={o}>{o}</option>)}
            </select>
          </div>
          <div>
            <label style={labelStyle}>Pincode <span style={{ color: '#dc2626' }}>*</span></label>
            <input
              type="text"
              readOnly
              style={inputStyle}
              value={formData.permPincode}
            />
          </div>
        </div>
      </div>

      {/* 5. Correspondence Address Card */}
      <div style={cardStyle}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '0.75rem' }}>
          <h3 style={{ fontSize: '1.05rem', fontWeight: '700', color: '#111827', margin: 0 }}>
            Correspondence Address
          </h3>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', fontSize: '0.85rem', color: '#4b5563' }}>
            <input
              type="checkbox"
              checked={formData.sameAsPermanent}
              onChange={handleToggleSameAddress}
              style={{ width: '16px', height: '16px', accentColor: '#2563eb' }}
            />
            <span>Correspondence Address is same as Permanent Address</span>
          </label>
        </div>
        <div style={{ marginBottom: '1.25rem' }}>
          <label style={labelStyle}>Address <span style={{ color: '#dc2626' }}>*</span></label>
          <textarea
            readOnly={formData.sameAsPermanent}
            rows={3}
            style={{ ...inputStyle, resize: 'vertical' }}
            value={formData.corrAddress}
            onChange={(e) => setFormData(prev => ({ ...prev, corrAddress: e.target.value }))}
          />
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.25rem' }}>
          <div>
            <label style={labelStyle}>District <span style={{ color: '#dc2626' }}>*</span></label>
            <select
              disabled={formData.sameAsPermanent}
              style={inputStyle}
              value={formData.corrDistrict}
              onChange={(e) => setFormData(prev => ({ ...prev, corrDistrict: e.target.value }))}
            >
              {withCurrent(formData.corrDistrict, ['Satara', 'Kolhapur', 'Pune', 'Sangli', 'Solapur']).map(o => <option key={o} value={o}>{o}</option>)}
            </select>
          </div>
          <div>
            <label style={labelStyle}>State <span style={{ color: '#dc2626' }}>*</span></label>
            <select
              disabled={formData.sameAsPermanent}
              style={inputStyle}
              value={formData.corrState}
              onChange={(e) => setFormData(prev => ({ ...prev, corrState: e.target.value }))}
            >
              {withCurrent(formData.corrState, ['Maharashtra', 'Goa', 'Karnataka']).map(o => <option key={o} value={o}>{o}</option>)}
            </select>
          </div>
          <div>
            <label style={labelStyle}>Pincode <span style={{ color: '#dc2626' }}>*</span></label>
            <input
              type="text"
              readOnly={formData.sameAsPermanent}
              style={inputStyle}
              value={formData.corrPincode}
              onChange={(e) => setFormData(prev => ({ ...prev, corrPincode: e.target.value }))}
            />
          </div>
        </div>
      </div>

      {/* 6. Personal Information Card */}
      <div style={cardStyle}>
        <h3 style={{ fontSize: '1.05rem', fontWeight: '700', color: '#111827', margin: 0, marginBottom: '1.25rem' }}>
          Personal Information
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1.25rem', marginBottom: '1.25rem' }}>
          <div>
            <label style={labelStyle}>Student Email ID <span style={{ color: '#dc2626' }}>*</span></label>
            <input type="email" readOnly style={inputStyle} value={formData.studentEmail} />
          </div>
          <div>
            <label style={labelStyle}>Student Mobile No. <span style={{ color: '#dc2626' }}>*</span></label>
            <input type="text" readOnly style={inputStyle} value={formData.studentMobile} />
          </div>
          <div>
            <label style={labelStyle}>Parent / Guardian E-mail ID <span style={{ color: '#dc2626' }}>*</span></label>
            <input type="email" readOnly style={inputStyle} value={formData.parentEmail} />
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1.25rem', marginBottom: '1.25rem' }}>
          <div>
            <label style={labelStyle}>Parent /Guardian Mobile No. <span style={{ color: '#dc2626' }}>*</span></label>
            <input type="text" readOnly style={inputStyle} value={formData.parentMobile} />
          </div>
          <div>
            <label style={labelStyle}>Profession of Father /Guardian <span style={{ color: '#dc2626' }}>*</span></label>
            <input type="text" readOnly style={{ ...inputStyle, textTransform: 'uppercase' }} value={formData.fatherProfession} />
          </div>
          <div>
            <label style={labelStyle}>Nationality <span style={{ color: '#dc2626' }}>*</span></label>
            <select disabled style={inputStyle} value={formData.nationality}>
              <option value="Indian">Indian</option>
            </select>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1.25rem', marginBottom: '1.25rem' }}>
          <div>
            <label style={labelStyle}>Domicile State <span style={{ color: '#dc2626' }}>*</span></label>
            <select disabled style={inputStyle} value={formData.domicileState}>
              <option value="Maharashtra State">Maharashtra State</option>
              <option value="Other">Other</option>
            </select>
          </div>
          <div>
            <label style={labelStyle}>Religion <span style={{ color: '#dc2626' }}>*</span></label>
            <select disabled style={inputStyle} value={formData.religion}>
              {withCurrent(formData.religion, ['Hindu', 'Muslim', 'Christian', 'Jain', 'Buddhist', 'Sikh']).map(o => <option key={o} value={o}>{o}</option>)}
            </select>
          </div>
          <div>
            <label style={labelStyle}>Constitutional Category of Admission <span style={{ color: '#dc2626' }}>*</span></label>
            <select disabled style={inputStyle} value={formData.constitutionalCategory}>
              {withCurrent(formData.constitutionalCategory, ['NT-C', 'OPEN', 'OBC', 'SC', 'ST']).map(o => <option key={o} value={o}>{o}</option>)}
            </select>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1.25rem' }}>
          <div>
            <label style={labelStyle}>Special Reservation, if any <span style={{ color: '#dc2626' }}>*</span></label>
            <select disabled style={inputStyle} value={formData.specialReservation}>
              <option value="Not Applicable">Not Applicable</option>
              <option value="Physically Handicapped">Physically Handicapped</option>
              <option value="Defense / Ex-Servicemen">Defense / Ex-Servicemen</option>
              <option value="Orphan">Orphan</option>
            </select>
          </div>
        </div>
      </div>

      {/* 7. Details of Qualifying Examination for admission to GCEK */}
      <div style={cardStyle}>
        <h3 style={{ fontSize: '1.05rem', fontWeight: '700', color: '#111827', margin: 0, marginBottom: '1.25rem' }}>
          Details of Qualifying Examination for admission to Government College of Engineering, Kolhapur
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr 1fr', gap: '1.25rem', marginBottom: '1.25rem' }}>
          <div>
            <label style={labelStyle}>Name of Board <span style={{ color: '#dc2626' }}>*</span></label>
            <input type="text" readOnly style={inputStyle} value={formData.examBoard} />
          </div>
          <div>
            <label style={labelStyle}>Name of Last School attended <span style={{ color: '#dc2626' }}>*</span></label>
            <input type="text" readOnly style={inputStyle} value={formData.lastSchool} />
          </div>
          <div>
            <label style={labelStyle}>Month of Passing <span style={{ color: '#dc2626' }}>*</span></label>
            <input type="text" readOnly style={inputStyle} value={formData.monthOfPassing} />
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem', marginBottom: '1.5rem', maxWidth: '600px' }}>
          <div>
            <label style={labelStyle}>Year of Passing <span style={{ color: '#dc2626' }}>*</span></label>
            <input type="text" readOnly style={inputStyle} value={formData.yearOfPassing} />
          </div>
          <div>
            <label style={labelStyle}>Percentage of marks <span style={{ color: '#dc2626' }}>*</span></label>
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <input
                type="text"
                readOnly
                style={{ ...inputStyle, borderTopRightRadius: 0, borderBottomRightRadius: 0 }}
                value={formData.percentageMarks}
              />
              <span style={{
                background: '#e2e8f0',
                border: '1px solid #d1d5db',
                borderLeft: 'none',
                padding: '0.62rem 0.85rem',
                borderTopRightRadius: '6px',
                borderBottomRightRadius: '6px',
                fontSize: '0.88rem',
                color: '#475569',
                fontWeight: '600'
              }}>
                %
              </span>
            </div>
          </div>
        </div>

        {/* File Upload Section */}
        <div style={{ borderTop: '1px solid #f1f5f9', paddingTop: '1.25rem' }}>
          <label style={{ ...labelStyle, fontSize: '0.85rem' }}>
            Upload Receipt Cum Acknowledgement Letter of Institute Reporting for admission to First/Second Year (As applicable)
          </label>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            border: '1px solid #d1d5db',
            borderRadius: '6px',
            backgroundColor: '#f8fafc',
            maxWidth: '650px',
            padding: '0.35rem',
            marginBottom: '0.5rem'
          }}>
            <button
              type="button"
              style={{
                background: '#e2e8f0',
                border: '1px solid #cbd5e1',
                padding: '0.4rem 0.9rem',
                borderRadius: '4px',
                fontSize: '0.82rem',
                fontWeight: '600',
                cursor: 'pointer',
                color: '#1e293b',
                marginRight: '0.75rem'
              }}
            >
              Choose File
            </button>
            <span style={{ fontSize: '0.82rem', color: '#64748b' }}>No file chosen</span>
          </div>
          <div style={{ fontSize: '0.75rem', color: '#dc2626', marginBottom: '1.25rem' }}>
            Accepted Format: PDF. Max file size: 200kb
          </div>

          <button
            type="button"
            onClick={() => alert('Downloading official Institute Allotment Letter...')}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.5rem',
              border: '1.5px solid #111827',
              borderRadius: '24px',
              padding: '0.5rem 1.25rem',
              fontSize: '0.82rem',
              fontWeight: '600',
              background: '#ffffff',
              color: '#111827',
              cursor: 'pointer',
              transition: 'all 0.15s ease'
            }}
          >
            <FileText size={15} />
            <span>View/Download existing letter PDF</span>
          </button>
        </div>
      </div>
    </div>
  );
};
