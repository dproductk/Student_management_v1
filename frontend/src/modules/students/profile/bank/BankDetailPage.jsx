import React, { useState } from 'react';
import { Eye, CheckCircle2, AlertCircle, Building2, Save } from 'lucide-react';
import api from '../../../../services/api';

/**
 * Subpage 4: Bank Detail
 * Matches Government Polytechnic Kolhapur EDVANA MIS design screenshot:
 * - Update your bank details:
 *   - Full Name of the Candidate *
 *   - Bank Name *
 *   - Branch Name *
 *   - Account No * (with sensitive reveal if masked)
 *   - IFSC Code *
 */
export const BankDetailPage = ({ 
  student, 
  isStaff, 
  onRevealBank, 
  revealedAccount 
}) => {
  const bank = student?.bank_account || {};

  const [candidateName, setCandidateName] = useState(
    bank?.account_holder_name || student?.candidate_name || ''
  );
  const [bankName, setBankName] = useState(
    bank?.bank_name || ''
  );
  const [branchName, setBranchName] = useState(
    bank?.branch_name || ''
  );
  const [accountNo, setAccountNo] = useState(
    revealedAccount || bank?.account_number_masked || ''
  );
  const [ifscCode, setIfscCode] = useState(
    bank?.ifsc_code || ''
  );

  const [saving, setSaving] = useState(false);
  const [statusMsg, setStatusMsg] = useState({ type: '', text: '' });

  const handleSave = async (e) => {
    e.preventDefault();
    if (!student?.id) return;
    setStatusMsg({ type: '', text: '' });
    setSaving(true);

    try {
      await api.post(`/students/${student.id}/bank-account/`, {
        account_holder_name: candidateName,
        bank_name: bankName,
        branch_name: branchName,
        account_number: accountNo,
        ifsc_code: ifscCode
      });
      setStatusMsg({ type: 'success', text: 'Bank details successfully updated in official register.' });
    } catch (err) {
      console.error(err);
      setStatusMsg({
        type: 'error',
        text: err.response?.data?.detail || 'Failed to update bank details. Controlled permission required.'
      });
    } finally {
      setSaving(false);
    }
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
      {statusMsg.text && (
        <div style={{
          backgroundColor: statusMsg.type === 'success' ? '#ECFDF5' : '#FEF2F2',
          border: `1px solid ${statusMsg.type === 'success' ? '#A7F3D0' : '#FECACA'}`,
          color: statusMsg.type === 'success' ? '#065F46' : '#991B1B',
          padding: '0.75rem 1rem',
          borderRadius: '8px',
          marginBottom: '1.25rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          fontSize: '0.85rem'
        }}>
          {statusMsg.type === 'success' ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />}
          <span>{statusMsg.text}</span>
        </div>
      )}

      {/* Update your bank details Card */}
      <div style={cardStyle}>
        <h3 style={{ fontSize: '1.05rem', fontWeight: '700', color: '#111827', margin: 0, marginBottom: '1.5rem' }}>
          Update your bank details
        </h3>

        <form onSubmit={handleSave}>
          {/* Row 1 */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.5rem', marginBottom: '1.5rem' }}>
            <div>
              <label style={labelStyle}>
                Full Name of the Candidate <span style={{ color: '#dc2626' }}>*</span>
              </label>
              <input
                type="text"
                style={{ ...inputStyle, textTransform: 'uppercase' }}
                value={candidateName}
                onChange={(e) => setCandidateName(e.target.value)}
                required
              />
            </div>

            <div>
              <label style={labelStyle}>
                Bank Name <span style={{ color: '#dc2626' }}>*</span>
              </label>
              <input
                type="text"
                style={{ ...inputStyle, textTransform: 'uppercase' }}
                value={bankName}
                onChange={(e) => setBankName(e.target.value)}
                required
              />
            </div>

            <div>
              <label style={labelStyle}>
                Branch Name <span style={{ color: '#dc2626' }}>*</span>
              </label>
              <input
                type="text"
                style={{ ...inputStyle, textTransform: 'uppercase' }}
                value={branchName}
                onChange={(e) => setBranchName(e.target.value)}
                required
              />
            </div>
          </div>

          {/* Row 2 */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.5rem', marginBottom: '1.5rem' }}>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.45rem' }}>
                <label style={labelStyle}>
                  Account No <span style={{ color: '#dc2626' }}>*</span>
                </label>
                {isStaff && !revealedAccount && (
                  <button
                    type="button"
                    onClick={onRevealBank}
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
                style={inputStyle}
                value={revealedAccount || accountNo}
                onChange={(e) => setAccountNo(e.target.value)}
                required
              />
            </div>

            <div>
              <label style={labelStyle}>
                IFSC Code <span style={{ color: '#dc2626' }}>*</span>
              </label>
              <input
                type="text"
                style={{ ...inputStyle, textTransform: 'uppercase' }}
                value={ifscCode}
                onChange={(e) => setIfscCode(e.target.value)}
                required
              />
            </div>
          </div>

          {/* Action Button */}
          <div style={{ display: 'flex', justifyContent: 'flex-start', borderTop: '1px solid #f1f5f9', paddingTop: '1.25rem' }}>
            <button
              type="submit"
              disabled={saving}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.5rem',
                backgroundColor: '#2563eb',
                color: '#ffffff',
                border: 'none',
                borderRadius: '6px',
                padding: '0.6rem 1.5rem',
                fontSize: '0.85rem',
                fontWeight: '600',
                cursor: saving ? 'not-allowed' : 'pointer',
                opacity: saving ? 0.7 : 1,
                boxShadow: '0 1px 2px rgba(37, 99, 235, 0.2)'
              }}
            >
              <Save size={16} />
              <span>{saving ? 'Updating...' : 'Update Bank Details'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
