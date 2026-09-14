import React, { useState } from 'react';
import { Info, FileText, Eye, Download, CheckCircle } from 'lucide-react';

/**
 * Subpage 3: Aadhaar Detail
 * Matches Government Polytechnic Kolhapur EDVANA MIS design screenshots:
 * - Instructions to upload Aadhaar (Amber callout)
 * - Upload Aadhaar Card:
 *   - Aadhaar Number
 *   - Name As per Aadhaar
 *   - Mobile No. Linked to Aadhaar
 *   - Upload scanned copy of Aadhaar Card (Accepted Format: PDF)
 *   - View/Download existing Aadhaar PDF button
 */
export const AadhaarDetailPage = ({ 
  student, 
  isStaff, 
  onRevealAadhaar, 
  revealedAadhaar 
}) => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [aadhaarData, setAadhaarData] = useState({
    aadhaarNumber: revealedAadhaar || student?.aadhaar_masked || '',
    nameAsPerAadhaar: student?.candidate_name ?
      student.candidate_name.split(' ').map(w => w.charAt(0) + w.slice(1).toLowerCase()).join(' ')
      : '',
    linkedMobile: student?.student_mobile || ''
  });

  const [message, setMessage] = useState('');

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
      setMessage('Aadhaar PDF selected. File is ready for upload/verification.');
    }
  };

  const instructionBoxStyle = {
    backgroundColor: '#FFFBEB',
    border: '1px solid #FDE68A',
    borderRadius: '10px',
    padding: '1.25rem 1.5rem',
    marginBottom: '1.5rem',
    display: 'flex',
    gap: '1rem',
    alignItems: 'flex-start',
  };

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
  };

  return (
    <div>
      {message && (
        <div style={{
          backgroundColor: '#ECFDF5',
          border: '1px solid #A7F3D0',
          color: '#065F46',
          padding: '0.75rem 1rem',
          borderRadius: '8px',
          marginBottom: '1.25rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          fontSize: '0.85rem'
        }}>
          <CheckCircle size={16} />
          <span>{message}</span>
        </div>
      )}

      {/* 1. Instructions to upload Aadhaar */}
      <div style={instructionBoxStyle}>
        <div style={{
          width: '28px',
          height: '28px',
          borderRadius: '50%',
          backgroundColor: '#D97706',
          color: '#ffffff',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
          marginTop: '0.1rem'
        }}>
          <Info size={18} />
        </div>
        <div>
          <h4 style={{ margin: 0, fontSize: '0.95rem', fontWeight: '700', color: '#92400E', marginBottom: '0.5rem' }}>
            Instructions to upload Aadhaar
          </h4>
          <ul style={{
            margin: 0,
            paddingLeft: '1.25rem',
            fontSize: '0.84rem',
            color: '#78350F',
            lineHeight: 1.6,
          }}>
            <li>Scan Aadhaar using a good quality scanner with min. 100dpi so that the file size should not be more than 100kb.</li>
            <li>Save the file in .pdf format on local machine.</li>
            <li>Ensure that the scanned Aadhaar is of good quality./her racial/religious custom but the headgear should not hide the applicant's features).</li>
          </ul>
        </div>
      </div>

      {/* 2. Upload Aadhaar Card */}
      <div style={cardStyle}>
        <h3 style={{ fontSize: '1.05rem', fontWeight: '700', color: '#111827', margin: 0, marginBottom: '1.5rem' }}>
          Upload Aadhaar
        </h3>

        {/* Row 1 */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.5rem', marginBottom: '1.5rem' }}>
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.45rem' }}>
              <label style={labelStyle}>Aadhaar Number</label>
              {isStaff && !revealedAadhaar && (
                <button
                  type="button"
                  onClick={onRevealAadhaar}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: '#2563eb',
                    cursor: 'pointer',
                    fontSize: '0.75rem',
                    fontWeight: '600',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.2rem'
                  }}
                >
                  <Eye size={12} /> Audited Reveal
                </button>
              )}
            </div>
            <input
              type="text"
              readOnly
              style={inputStyle}
              value={revealedAadhaar || aadhaarData.aadhaarNumber}
            />
          </div>

          <div>
            <label style={labelStyle}>Name As per Aadhaar</label>
            <input
              type="text"
              readOnly
              style={inputStyle}
              value={aadhaarData.nameAsPerAadhaar}
            />
          </div>
        </div>

        {/* Row 2 */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.5rem', marginBottom: '1.5rem' }}>
          <div>
            <label style={labelStyle}>Mobile No. Linked to Aadhaar</label>
            <input
              type="text"
              readOnly
              style={inputStyle}
              value={aadhaarData.linkedMobile}
            />
          </div>

          <div>
            <label style={labelStyle}>
              Upload scanned copy of Aadhaar Card <span style={{ fontSize: '0.75rem', fontWeight: 'normal', color: '#64748b' }}>(Accepted Format: PDF)</span>
            </label>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              border: '1px solid #d1d5db',
              borderRadius: '6px',
              backgroundColor: '#f8fafc',
              padding: '0.35rem',
            }}>
              <label style={{
                background: '#e2e8f0',
                border: '1px solid #cbd5e1',
                padding: '0.45rem 1rem',
                borderRadius: '4px',
                fontSize: '0.82rem',
                fontWeight: '600',
                cursor: 'pointer',
                color: '#1e293b',
                marginRight: '0.75rem'
              }}>
                Choose File
                <input
                  type="file"
                  accept="application/pdf"
                  style={{ display: 'none' }}
                  onChange={handleFileChange}
                />
              </label>
              <span style={{ fontSize: '0.82rem', color: '#64748b' }}>
                {selectedFile ? selectedFile.name : 'No file chosen'}
              </span>
            </div>
          </div>
        </div>

        {/* Row 3: Action Button */}
        <div>
          <button
            type="button"
            onClick={() => alert('Downloading existing encrypted Aadhaar PDF for ' + aadhaarData.nameAsPerAadhaar)}
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
              transition: 'all 0.15s ease',
              boxShadow: '0 1px 2px rgba(0,0,0,0.04)'
            }}
          >
            <FileText size={15} />
            <span>View/Download existing Aadhaar PDF</span>
          </button>
        </div>
      </div>
    </div>
  );
};
