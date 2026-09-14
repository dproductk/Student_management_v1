import React, { useState } from 'react';
import { Info, Upload, CheckCircle, Image as ImageIcon } from 'lucide-react';

/**
 * Subpage 2: Photo
 * Matches Government Polytechnic Kolhapur EDVANA MIS design screenshots:
 * - Instructions for upload Photo (Amber callout)
 * - Upload Photo Form & Uploaded Photo Preview
 * - Instructions for upload Signature (Amber callout)
 * - Upload Signature Form & Uploaded Signature Preview
 */
export const PhotoPage = ({ student, isStaff }) => {
  const [selectedPhoto, setSelectedPhoto] = useState(null);
  const [photoPreview, setPhotoPreview] = useState(
    student?.avatar_url || null
  );

  const [selectedSign, setSelectedSign] = useState(null);
  const [signPreview, setSignPreview] = useState(
    student?.signature_url || null
  );

  const [uploadSuccess, setUploadSuccess] = useState('');

  const handlePhotoChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedPhoto(file);
      const reader = new FileReader();
      reader.onload = (loadEvt) => {
        setPhotoPreview(loadEvt.target.result);
        setUploadSuccess('Passport photo selected. Click submit or save to finalize.');
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSignChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedSign(file);
      const reader = new FileReader();
      reader.onload = (loadEvt) => {
        setSignPreview(loadEvt.target.result);
        setUploadSuccess('Signature selected. Click submit or save to finalize.');
      };
      reader.readAsDataURL(file);
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
    marginBottom: '1.75rem',
    boxShadow: '0 1px 2px rgba(0, 0, 0, 0.03)',
  };

  return (
    <div>
      {uploadSuccess && (
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
          <span>{uploadSuccess}</span>
        </div>
      )}

      {/* 1. Instructions for upload Photo */}
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
            Instructions for upload Photo
          </h4>
          <ul style={{
            margin: 0,
            paddingLeft: '1.25rem',
            fontSize: '0.84rem',
            color: '#78350F',
            lineHeight: 1.6,
          }}>
            <li>Recent colour photo of candidate taken within last three months.</li>
            <li>Photograph must be 3.5 cm in width by 4.5 cm in height without border.</li>
            <li>Photograph has to be taken full face without headgear (unless the applicant habitually wears a head gear in accordance with his/her racial/religious custom but the headgear should not hide the applicant's features).</li>
            <li>Paste the Photograph on Paper.</li>
            <li>Sign below the Photograph.</li>
            <li>Scan Photo with Signature using a good quality scanner with min. 100dpi so that the file size should not be more than 150kb.</li>
            <li>Save the image in .jpg format on local machine.</li>
            <li>Ensure that the scanned photo with signature are of good quality.</li>
          </ul>
        </div>
      </div>

      {/* 2. Upload Photo Card */}
      <div style={cardStyle}>
        <h3 style={{ fontSize: '1.05rem', fontWeight: '700', color: '#111827', margin: 0, marginBottom: '1.5rem' }}>
          Upload Photo
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'minmax(280px, 1.5fr) 1fr', gap: '2rem', alignItems: 'flex-start' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: '600', color: '#1f2937', marginBottom: '0.5rem' }}>
              Upload Latest Passport size Photo
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
                  accept="image/jpeg, image/png, image/jpg"
                  style={{ display: 'none' }}
                  onChange={handlePhotoChange}
                />
              </label>
              <span style={{ fontSize: '0.82rem', color: '#64748b' }}>
                {selectedPhoto ? selectedPhoto.name : 'No file chosen'}
              </span>
            </div>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: '600', color: '#1f2937', marginBottom: '0.5rem' }}>
              Uploaded Photo
            </label>
            <div style={{
              width: '120px',
              height: '145px',
              border: '1px solid #cbd5e1',
              borderRadius: '4px',
              overflow: 'hidden',
              backgroundColor: '#f1f5f9',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
            }}>
              {photoPreview ? (
                <img
                  src={photoPreview}
                  alt="Student Passport"
                  style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                />
              ) : (
                <div style={{ textAlign: 'center', color: '#94a3b8' }}>
                  <ImageIcon size={24} />
                  <div style={{ fontSize: '0.7rem', marginTop: '0.25rem' }}>No Photo</div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* 3. Instructions for upload Signature */}
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
            Instructions for upload Signature
          </h4>
          <ul style={{
            margin: 0,
            paddingLeft: '1.25rem',
            fontSize: '0.84rem',
            color: '#78350F',
            lineHeight: 1.6,
          }}>
            <li>Sign on a white paper with a black pen.</li>
            <li>Scan the signature using a good quality scanner with min. 100dpi so that the file size should not be more than 150kb.</li>
            <li>Save the image in .jpg format on local machine.</li>
          </ul>
        </div>
      </div>

      {/* 4. Upload Signature Card */}
      <div style={cardStyle}>
        <h3 style={{ fontSize: '1.05rem', fontWeight: '700', color: '#111827', margin: 0, marginBottom: '1.5rem' }}>
          Upload Signature
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'minmax(280px, 1.5fr) 1fr', gap: '2rem', alignItems: 'flex-start' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: '600', color: '#1f2937', marginBottom: '0.5rem' }}>
              Upload Signature
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
                  accept="image/jpeg, image/png, image/jpg"
                  style={{ display: 'none' }}
                  onChange={handleSignChange}
                />
              </label>
              <span style={{ fontSize: '0.82rem', color: '#64748b' }}>
                {selectedSign ? selectedSign.name : 'No file chosen'}
              </span>
            </div>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: '600', color: '#1f2937', marginBottom: '0.5rem' }}>
              Uploaded Signature
            </label>
            <div style={{
              width: '160px',
              height: '65px',
              border: '1px solid #cbd5e1',
              borderRadius: '4px',
              backgroundColor: '#ffffff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
              padding: '4px'
            }}>
              {signPreview ? (
                <img
                  src={signPreview}
                  alt="Student Signature"
                  style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain' }}
                />
              ) : (
                <div style={{
                  fontFamily: 'cursive',
                  fontSize: '1.1rem',
                  color: '#1e3a8a',
                  fontStyle: 'italic',
                  textDecoration: 'underline'
                }}>
                  {student?.candidate_name ? student.candidate_name.split(' ')[0] : 'Sign'}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
