import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import api from '../../services/api';
import { CorrectionModal } from './CorrectionModal';
import { StudentDocumentList } from '../documents/StudentDocumentList';
import { useAuth } from '../../context/AuthContext';
import { 
  GraduationCap, 
  Image as ImageIcon, 
  CreditCard, 
  Building2, 
  FileText, 
  CheckCircle2, 
  History, 
  Edit3, 
  Eye, 
  ShieldCheck,
  Layers,
  Sparkles
} from 'lucide-react';

// Import the 4 dedicated subpage components from their folders
import { 
  RegistrationDetail, 
  PhotoPage, 
  AadhaarDetailPage, 
  BankDetailPage 
} from './profile';

export const StudentProfile = () => {
  const { id } = useParams();
  const { user, hasRole } = useAuth();
  const isStaff = hasRole('SYSTEM_ADMIN') || hasRole('COLLEGE_ADMIN') || hasRole('HOD') || hasRole('VERIFICATION_OFFICER');

  const [student, setStudent] = useState(null);
  const [activeTab, setActiveTab] = useState('registration'); // 'registration', 'photo', 'aadhaar', 'bank', or staff tabs
  const [loading, setLoading] = useState(true);
  const [showCorrectionModal, setShowCorrectionModal] = useState(false);

  // Sensitive Reveal state (ADR-015)
  const [showRevealModal, setShowRevealModal] = useState(false);
  const [revealField, setRevealField] = useState('aadhaar');
  const [revealReason, setRevealReason] = useState('');
  const [revealedData, setRevealedData] = useState({});
  const [revealLoading, setRevealLoading] = useState(false);
  const [revealError, setRevealError] = useState('');

  const fetchStudent = async () => {
    try {
      setLoading(true);
      let res;
      if (id && id !== 'me') {
        res = await api.get(`/students/${id}/`);
      } else {
        // Find matching student record for current user or default to first
        const searchRes = await api.get(`/students/?search=${user?.username || ''}`);
        const results = Array.isArray(searchRes.data) ? searchRes.data : (searchRes.data?.results || []);
        if (results.length > 0) {
          res = await api.get(`/students/${results[0].id}/`);
        } else {
          const allRes = await api.get('/students/');
          const allData = Array.isArray(allRes.data) ? allRes.data : (allRes.data?.results || []);
          if (allData.length > 0) {
            res = await api.get(`/students/${allData[0].id}/`);
          }
        }
      }
      if (res) setStudent(res.data);
    } catch (err) {
      console.error('Failed to load student profile', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStudent();
  }, [id]);

  const handleReveal = async (e) => {
    e.preventDefault();
    setRevealError('');
    setRevealLoading(true);

    try {
      const studentId = student?.id || id;
      const res = await api.post(`/students/${studentId}/reveal-sensitive/`, {
        field_name: revealField,
        reason: revealReason,
      });
      setRevealedData((prev) => ({
        ...prev,
        [revealField]: res.data.value,
      }));
      setShowRevealModal(false);
      setRevealReason('');
    } catch (err) {
      setRevealError(err.response?.data?.message || err.response?.data?.detail || 'Failed to decrypt sensitive data.');
    } finally {
      setRevealLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ padding: '3rem', textAlign: 'center', color: '#64748b' }}>
        Loading student profile...
      </div>
    );
  }

  if (!student) {
    return (
      <div style={{ padding: '3rem', textAlign: 'center', color: '#64748b' }}>
        Student record not found.
      </div>
    );
  }

  // 4 Core Subpages matching EDVANA screenshots
  const coreTabs = [
    { id: 'registration', label: 'Registration Detail', icon: GraduationCap },
    { id: 'photo', label: 'Photo', icon: ImageIcon },
    { id: 'aadhaar', label: 'Aadhaar Detail', icon: CreditCard },
    { id: 'bank', label: 'Bank Detail', icon: Building2 },
  ];

  // Administrative / Staff tabs
  const staffTabs = [
    { id: 'enrollments', label: 'Semester Enrollments', icon: Layers },
    { id: 'documents', label: 'Documents & Storage', icon: FileText },
    { id: 'corrections', label: 'Correction Audit Trail', icon: History },
  ];

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
      {/* Top Action Bar for Staff */}
      {isStaff && (
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          backgroundColor: '#eff6ff',
          border: '1px solid #bfdbfe',
          borderRadius: '8px',
          padding: '0.65rem 1.25rem',
          marginBottom: '1.25rem',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#1e40af', fontSize: '0.85rem', fontWeight: '600' }}>
            <ShieldCheck size={18} />
            <span>Administrative View — Government College of Engineering, Kolhapur MIS</span>
          </div>
          <button
            type="button"
            onClick={() => setShowCorrectionModal(true)}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.4rem',
              backgroundColor: '#2563eb',
              color: '#ffffff',
              border: 'none',
              borderRadius: '6px',
              padding: '0.45rem 0.9rem',
              fontSize: '0.82rem',
              fontWeight: '600',
              cursor: 'pointer',
              boxShadow: '0 1px 2px rgba(37, 99, 235, 0.2)'
            }}
          >
            <Edit3 size={14} />
            <span>Controlled Correction</span>
          </button>
        </div>
      )}

      {/* 4-Tab Navigation Header (Exact EDVANA MIS Style) */}
      <div style={{
        backgroundColor: '#ffffff',
        borderRadius: '8px',
        border: '1px solid #e5e7eb',
        padding: '0.25rem 0.5rem',
        marginBottom: '1.5rem',
        boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          overflowX: 'auto',
        }}>
          {coreTabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveTab(tab.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.55rem',
                  padding: '0.85rem 1.25rem',
                  background: 'transparent',
                  border: 'none',
                  borderBottom: isActive ? '3px solid #2563eb' : '3px solid transparent',
                  color: isActive ? '#2563eb' : '#4b5563',
                  fontWeight: isActive ? '700' : '500',
                  fontSize: '0.88rem',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                  whiteSpace: 'nowrap'
                }}
              >
                <Icon size={18} color={isActive ? '#2563eb' : '#64748b'} />
                <span>{tab.label}</span>
              </button>
            );
          })}

          {/* Additional staff tabs if privileged */}
          {isStaff && (
            <>
              <div style={{ width: '1px', height: '24px', backgroundColor: '#e2e8f0', margin: '0 0.5rem' }} />
              {staffTabs.map((tab) => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    type="button"
                    onClick={() => setActiveTab(tab.id)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem',
                      padding: '0.85rem 1rem',
                      background: 'transparent',
                      border: 'none',
                      borderBottom: isActive ? '3px solid #475569' : '3px solid transparent',
                      color: isActive ? '#1e293b' : '#64748b',
                      fontWeight: isActive ? '600' : '500',
                      fontSize: '0.84rem',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                      whiteSpace: 'nowrap'
                    }}
                  >
                    <Icon size={16} />
                    <span>{tab.label}</span>
                  </button>
                );
              })}
            </>
          )}
        </div>
      </div>

      {/* Subpage 1: Registration Detail */}
      {activeTab === 'registration' && (
        <RegistrationDetail
          student={student}
          isStaff={isStaff}
          onSave={fetchStudent}
        />
      )}

      {/* Subpage 2: Photo */}
      {activeTab === 'photo' && (
        <PhotoPage
          student={student}
          isStaff={isStaff}
        />
      )}

      {/* Subpage 3: Aadhaar Detail */}
      {activeTab === 'aadhaar' && (
        <AadhaarDetailPage
          student={student}
          isStaff={isStaff}
          revealedAadhaar={revealedData['aadhaar']}
          onRevealAadhaar={() => {
            setRevealField('aadhaar');
            setShowRevealModal(true);
          }}
        />
      )}

      {/* Subpage 4: Bank Detail */}
      {activeTab === 'bank' && (
        <BankDetailPage
          student={student}
          isStaff={isStaff}
          revealedAccount={revealedData['bank_account']}
          onRevealBank={() => {
            setRevealField('bank_account');
            setShowRevealModal(true);
          }}
        />
      )}

      {/* Staff Tab: Semester Enrollments */}
      {activeTab === 'enrollments' && (
        <div style={{ background: '#ffffff', borderRadius: '10px', border: '1px solid #e5e7eb', padding: '1.5rem', boxShadow: '0 1px 2px rgba(0,0,0,0.03)' }}>
          <h3 style={{ fontSize: '1.05rem', fontWeight: '700', color: '#111827', margin: 0, marginBottom: '1.25rem' }}>
            Authoritative Academic Enrollments (ADR-005)
          </h3>
          {(!student.enrollments || student.enrollments.length === 0) ? (
            <p style={{ color: '#64748b' }}>No semester enrollments recorded.</p>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.88rem' }}>
                <thead>
                  <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0', textAlign: 'left' }}>
                    <th style={{ padding: '0.75rem 1rem' }}>Academic Year</th>
                    <th style={{ padding: '0.75rem 1rem' }}>Semester</th>
                    <th style={{ padding: '0.75rem 1rem' }}>Department</th>
                    <th style={{ padding: '0.75rem 1rem' }}>Program</th>
                    <th style={{ padding: '0.75rem 1rem' }}>Batch</th>
                    <th style={{ padding: '0.75rem 1rem' }}>Scheme</th>
                    <th style={{ padding: '0.75rem 1rem' }}>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {student.enrollments.map((enr) => (
                    <tr key={enr.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                      <td style={{ padding: '0.75rem 1rem', fontWeight: '600' }}>{enr.academic_year_label}</td>
                      <td style={{ padding: '0.75rem 1rem' }}>Sem {enr.semester_number}</td>
                      <td style={{ padding: '0.75rem 1rem' }}>{enr.department_code}</td>
                      <td style={{ padding: '0.75rem 1rem' }}>{enr.program_code}</td>
                      <td style={{ padding: '0.75rem 1rem' }}>{enr.batch_name}</td>
                      <td style={{ padding: '0.75rem 1rem' }}><code>{enr.scheme_code}</code></td>
                      <td style={{ padding: '0.75rem 1rem' }}>
                        <span style={{ backgroundColor: '#ecfdf5', color: '#065f46', padding: '0.2rem 0.5rem', borderRadius: '4px', fontSize: '0.75rem', fontWeight: '600' }}>
                          {enr.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Staff Tab: Documents & Storage */}
      {activeTab === 'documents' && (
        <StudentDocumentList studentId={student.id} />
      )}

      {/* Staff Tab: Correction Audit Trail */}
      {activeTab === 'corrections' && (
        <div style={{ background: '#ffffff', borderRadius: '10px', border: '1px solid #e5e7eb', padding: '1.5rem', boxShadow: '0 1px 2px rgba(0,0,0,0.03)' }}>
          <h3 style={{ fontSize: '1.05rem', fontWeight: '700', color: '#111827', margin: 0, marginBottom: '1.25rem' }}>
            Additive Government Correction History (ADR-007)
          </h3>
          {(!student.corrections || student.corrections.length === 0) ? (
            <p style={{ color: '#64748b' }}>No historical corrections on record. Data matches government intake source.</p>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.88rem' }}>
                <thead>
                  <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0', textAlign: 'left' }}>
                    <th style={{ padding: '0.75rem 1rem' }}>Field Name</th>
                    <th style={{ padding: '0.75rem 1rem' }}>Original Value</th>
                    <th style={{ padding: '0.75rem 1rem' }}>Corrected Value</th>
                    <th style={{ padding: '0.75rem 1rem' }}>Reason</th>
                    <th style={{ padding: '0.75rem 1rem' }}>Approved By</th>
                    <th style={{ padding: '0.75rem 1rem' }}>Timestamp</th>
                  </tr>
                </thead>
                <tbody>
                  {student.corrections.map((c) => (
                    <tr key={c.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                      <td style={{ padding: '0.75rem 1rem' }}><code>{c.field_name}</code></td>
                      <td style={{ padding: '0.75rem 1rem', color: '#dc2626' }}>{c.original_value || '—'}</td>
                      <td style={{ padding: '0.75rem 1rem', color: '#16a34a', fontWeight: '600' }}>{c.corrected_value}</td>
                      <td style={{ padding: '0.75rem 1rem' }}>{c.correction_reason}</td>
                      <td style={{ padding: '0.75rem 1rem' }}>{c.approved_by_username}</td>
                      <td style={{ padding: '0.75rem 1rem', color: '#64748b' }}>{new Date(c.approved_at).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Controlled Correction Modal */}
      {showCorrectionModal && (
        <CorrectionModal
          studentId={student.id}
          onClose={() => setShowCorrectionModal(false)}
          onCorrectionApplied={fetchStudent}
        />
      )}

      {/* Sensitive Reveal Modal (ADR-015) */}
      {showRevealModal && (
        <div className="modal-overlay" style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
        }}>
          <div style={{
            background: '#ffffff',
            borderRadius: '12px',
            padding: '1.75rem',
            maxWidth: '480px',
            width: '90%',
            boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1), 0 10px 10px -5px rgba(0,0,0,0.04)'
          }}>
            <h2 style={{ fontSize: '1.2rem', fontWeight: '700', margin: 0, marginBottom: '0.5rem', color: '#111827' }}>
              Audited Sensitive Data Reveal
            </h2>
            <p style={{ fontSize: '0.82rem', color: '#64748b', marginBottom: '1.25rem', lineHeight: 1.5 }}>
              Revealing cleartext {revealField.replace('_', ' ')} will record an immutable entry in the compliance access log with your username, timestamp, and IP address (ADR-015).
            </p>
            {revealError && (
              <div style={{
                backgroundColor: '#FEF2F2',
                border: '1px solid #FECACA',
                color: '#991B1B',
                padding: '0.5rem 0.75rem',
                borderRadius: '6px',
                marginBottom: '1rem',
                fontSize: '0.85rem'
              }}>
                {revealError}
              </div>
            )}
            <form onSubmit={handleReveal}>
              <div style={{ marginBottom: '1.25rem' }}>
                <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: '600', color: '#1f2937', marginBottom: '0.45rem' }}>
                  Mandatory Audit Justification
                </label>
                <textarea
                  rows={3}
                  placeholder="State the legal or operational purpose for viewing cleartext..."
                  value={revealReason}
                  onChange={(e) => setRevealReason(e.target.value)}
                  required
                  style={{
                    width: '100%',
                    padding: '0.62rem 0.85rem',
                    borderRadius: '6px',
                    border: '1px solid #d1d5db',
                    fontSize: '0.88rem',
                    color: '#1e293b',
                    outline: 'none',
                    boxSizing: 'border-box'
                  }}
                />
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
                <button
                  type="button"
                  onClick={() => setShowRevealModal(false)}
                  style={{
                    padding: '0.5rem 1rem',
                    borderRadius: '6px',
                    border: '1px solid #d1d5db',
                    background: '#ffffff',
                    color: '#374151',
                    fontSize: '0.85rem',
                    fontWeight: '500',
                    cursor: 'pointer'
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={revealLoading}
                  style={{
                    padding: '0.5rem 1.25rem',
                    borderRadius: '6px',
                    border: 'none',
                    background: '#2563eb',
                    color: '#ffffff',
                    fontSize: '0.85rem',
                    fontWeight: '600',
                    cursor: revealLoading ? 'not-allowed' : 'pointer',
                    opacity: revealLoading ? 0.7 : 1
                  }}
                >
                  {revealLoading ? 'Decrypting...' : 'Confirm & Reveal'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
