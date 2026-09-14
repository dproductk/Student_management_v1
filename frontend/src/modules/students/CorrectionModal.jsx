import React, { useState } from 'react';
import api from '../../services/api';

export const CorrectionModal = ({ studentId, onClose, onCorrectionApplied }) => {
  const [field, setField] = useState('candidate_name');
  const [newValue, setNewValue] = useState('');
  const [reason, setReason] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const correctionFields = [
    { value: 'candidate_name', label: 'Candidate Name' },
    { value: 'father_name', label: "Father's Name" },
    { value: 'mother_name', label: "Mother's Name" },
    { value: 'student_mobile', label: 'Student Mobile' },
    { value: 'parent_mobile', label: 'Parent Mobile' },
    { value: 'email', label: 'Email Address' },
    { value: 'religion', label: 'Religion' },
    { value: 'mother_tongue', label: 'Mother Tongue' },
    { value: 'candidature_type', label: 'Candidature Type' },
    { value: 'admission_category', label: 'Admission Category' },
    { value: 'seat_type', label: 'Seat Type' },
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await api.post(`/students/${studentId}/corrections/`, {
        field_name: field,
        new_value: newValue,
        reason: reason,
      });
      onCorrectionApplied();
      onClose();
    } catch (err) {
      setError(err.response?.data?.message || err.response?.data?.detail || 'Failed to submit correction.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="edvana-card modal-content" style={{ padding: '1.75rem', maxWidth: '520px' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: '700', marginBottom: '0.5rem', color: 'var(--edvana-text-primary)' }}>
          Request Controlled Student Correction
        </h2>
        <p style={{ fontSize: '0.8rem', color: 'var(--edvana-text-muted)', marginBottom: '1.25rem' }}>
          Government-sourced data is preserved additively. All changes are permanently recorded in the student audit log (ADR-007).
        </p>

        {error && (
          <div className="edvana-badge-danger" style={{ padding: '0.5rem 0.75rem', borderRadius: 'var(--edvana-radius-sm)', marginBottom: '1rem', width: '100%', boxSizing: 'border-box' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div>
            <label className="edvana-detail-label">Field to Correct</label>
            <select
              className="edvana-select"
              value={field}
              onChange={(e) => setField(e.target.value)}
              required
            >
              {correctionFields.map((f) => (
                <option key={f.value} value={f.value}>{f.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="edvana-detail-label">New Authoritative Value</label>
            <input
              type="text"
              className="edvana-input"
              placeholder="Enter new corrected value"
              value={newValue}
              onChange={(e) => setNewValue(e.target.value)}
              required
            />
          </div>

          <div>
            <label className="edvana-detail-label">Administrative Justification / Reason</label>
            <textarea
              className="edvana-textarea"
              rows={3}
              placeholder="Legal affidavit, gazette notification, or document discrepancy justification..."
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              required
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '0.75rem' }}>
            <button type="button" className="edvana-btn edvana-btn-outline" onClick={onClose} disabled={loading}>
              Cancel
            </button>
            <button type="submit" className="edvana-btn edvana-btn-primary" disabled={loading}>
              {loading ? 'Submitting...' : 'Apply Correction'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
