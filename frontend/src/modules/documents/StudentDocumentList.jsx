import React, { useState, useEffect } from 'react';
import { 
  FileText, 
  UploadCloud, 
  ShieldAlert, 
  Eye, 
  Download, 
  History, 
  RefreshCw, 
  CheckCircle2, 
  AlertCircle, 
  Clock, 
  FileCheck,
  Lock,
  Layers,
  FileSpreadsheet
} from 'lucide-react';
import api from '../../services/api';

const DOCUMENT_TYPE_LABELS = {
  PHOTO: 'Student Photograph',
  SIGNATURE: 'Student Signature',
  AADHAAR_CARD: 'Aadhaar Card',
  SSC_MARKSHEET: 'SSC Marksheet (10th)',
  HSC_MARKSHEET: 'HSC Marksheet (12th)',
  ALLOTMENT_LETTER: 'Government Allotment Letter',
  BANK_PASSBOOK: 'Bank Passbook / Cheque',
  INCOME_CERTIFICATE: 'Income Certificate',
  CASTE_CERTIFICATE: 'Caste Certificate',
  OTHER: 'Other Certificate',
};

export const StudentDocumentList = ({ studentId }) => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);

  // Upload modal state
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadType, setUploadType] = useState('SSC_MARKSHEET');
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadLoading, setUploadLoading] = useState(false);

  // Replace Allotment Letter modal state
  const [showReplaceModal, setShowReplaceModal] = useState(false);
  const [replaceFile, setReplaceFile] = useState(null);
  const [replaceReason, setReplaceReason] = useState('');
  const [replaceLoading, setReplaceLoading] = useState(false);

  // Sensitive Reveal modal state
  const [revealDoc, setRevealDoc] = useState(null);
  const [revealReason, setRevealReason] = useState('');
  const [revealLoading, setRevealLoading] = useState(false);
  const [revealError, setRevealError] = useState('');

  // History modal state
  const [historyDoc, setHistoryDoc] = useState(null);
  const [historyList, setHistoryList] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      const res = await api.get(`/documents/?student_id=${studentId}`);
      const data = Array.isArray(res.data) ? res.data : (res.data?.results || []);
      setDocuments(data);
    } catch (err) {
      console.error('Failed to fetch documents', err);
      setDocuments([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (studentId) fetchDocuments();
  }, [studentId]);

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!uploadFile) return;

    try {
      setUploadLoading(true);
      const formData = new FormData();
      formData.append('student_id', studentId);
      formData.append('document_type', uploadType);
      formData.append('file', uploadFile);

      await api.post('/documents/upload/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      setShowUploadModal(false);
      setUploadFile(null);
      fetchDocuments();
    } catch (err) {
      alert('Upload failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setUploadLoading(false);
    }
  };

  const handleReplaceAllotment = async (e) => {
    e.preventDefault();
    if (!replaceFile) return;

    try {
      setReplaceLoading(true);
      const formData = new FormData();
      formData.append('file', replaceFile);
      formData.append('reason', replaceReason);

      await api.post(`/documents/students/${studentId}/allotment-letter/replace/`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      setShowReplaceModal(false);
      setReplaceFile(null);
      setReplaceReason('');
      fetchDocuments();
    } catch (err) {
      alert('Replacement failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setReplaceLoading(false);
    }
  };

  const handleReveal = async (e) => {
    e.preventDefault();
    if (!revealDoc) return;

    try {
      setRevealLoading(true);
      setRevealError('');

      // Request blob stream from reveal endpoint
      const res = await api.post(
        `/documents/${revealDoc.id}/reveal/`,
        { reason: revealReason },
        { responseType: 'blob' }
      );

      // Trigger client-side download
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', revealDoc.original_filename || `document_${revealDoc.id}`);
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);

      setRevealDoc(null);
      setRevealReason('');
    } catch (err) {
      setRevealError('Failed to reveal document. Check authorization or reason.');
    } finally {
      setRevealLoading(false);
    }
  };

  const openHistory = async (doc) => {
    setHistoryDoc(doc);
    try {
      setHistoryLoading(true);
      const res = await api.get(`/documents/${doc.id}/history/`);
      const list = Array.isArray(res.data) ? res.data : (res.data?.results || []);
      setHistoryList(list);
    } catch (err) {
      console.error('Failed to load version history', err);
      setHistoryList([]);
    } finally {
      setHistoryLoading(false);
    }
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return '—';
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Header Actions Card */}
      <div className="edvana-card" style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '1.25rem 1.5rem',
        background: 'linear-gradient(135deg, var(--bg-surface) 0%, rgba(59, 130, 246, 0.04) 100%)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{
            width: '44px',
            height: '44px',
            borderRadius: 'var(--edvana-radius-md)',
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
            color: 'var(--edvana-brand)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <FileText size={24} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: '700', color: 'var(--edvana-text-primary)' }}>
                Authoritative Student Documents
              </h3>
              <span className="badge badge-primary">ADR-011 Versioned</span>
            </div>
            <p style={{ margin: '0.2rem 0 0', fontSize: '0.8rem', color: 'var(--edvana-text-secondary)' }}>
              Server-side object store references, checksum verification, and ADR-015 sensitive document protection.
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button 
            className="edvana-btn edvana-btn-secondary"
            onClick={fetchDocuments}
            style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}
          >
            <RefreshCw size={15} /> Refresh
          </button>
          <button 
            className="edvana-btn edvana-btn-secondary"
            onClick={() => setShowReplaceModal(true)}
            style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}
          >
            <Layers size={15} /> Replace Allotment
          </button>
          <button 
            className="edvana-btn edvana-btn-primary"
            onClick={() => setShowUploadModal(true)}
            style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}
          >
            <UploadCloud size={15} /> Upload Document
          </button>
        </div>
      </div>

      {/* Sensitive Protection Warning Callout */}
      <div style={{
        padding: '0.85rem 1.25rem',
        borderRadius: 'var(--edvana-radius-md)',
        backgroundColor: 'rgba(245, 158, 11, 0.08)',
        border: '1px solid var(--edvana-warning)',
        display: 'flex',
        alignItems: 'center',
        gap: '0.85rem'
      }}>
        <ShieldAlert size={20} color="var(--edvana-warning)" />
        <div style={{ fontSize: '0.8rem', color: 'var(--edvana-text-primary)' }}>
          <strong>ADR-015 Sensitive Boundary Active:</strong> Aadhaar Cards and Bank Passbooks are masked by default. Downloading sensitive documents requires an explicit reveal action with a mandatory institutional business reason and is permanently recorded in the immutable audit log.
        </div>
      </div>

      {/* Documents Grid */}
      {(() => {
        const safeDocuments = Array.isArray(documents) ? documents : [];
        if (loading) {
          return (
            <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--edvana-text-muted)' }}>
              Loading document repository...
            </div>
          );
        }
        if (safeDocuments.length === 0) {
          return (
            <div className="edvana-card" style={{ padding: '3rem', textAlign: 'center', color: 'var(--edvana-text-muted)' }}>
              No documents uploaded for this student yet. Click "Upload Document" to register marksheets or identity records.
            </div>
          );
        }
        return (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '1rem' }}>
            {safeDocuments.map((doc) => {
            const isSens = doc.is_sensitive;
            return (
              <div 
                key={doc.id} 
                className="edvana-card" 
                style={{ 
                  display: 'flex', 
                  flexDirection: 'column', 
                  justifyContent: 'space-between',
                  border: isSens ? '1px solid rgba(245, 158, 11, 0.4)' : '1px solid var(--edvana-border)'
                }}
              >
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
                    <span style={{ 
                      fontSize: '0.75rem', 
                      fontWeight: '700', 
                      textTransform: 'uppercase',
                      color: isSens ? 'var(--edvana-warning)' : 'var(--edvana-brand)'
                    }}>
                      {DOCUMENT_TYPE_LABELS[doc.document_type] || doc.document_type}
                    </span>
                    <div style={{ display: 'flex', gap: '0.35rem' }}>
                      <span className="badge" style={{ backgroundColor: 'var(--bg-subtle)', fontSize: '0.7rem' }}>
                        v{doc.version}
                      </span>
                      {isSens && (
                        <span className="badge badge-warning" style={{ fontSize: '0.7rem' }}>
                          <Lock size={10} style={{ marginRight: '3px' }} /> Sensitive
                        </span>
                      )}
                    </div>
                  </div>

                  <div style={{ fontWeight: '600', fontSize: '0.9rem', color: 'var(--edvana-text-primary)', wordBreak: 'break-all' }}>
                    {doc.original_filename || 'Unnamed File'}
                  </div>

                  <div style={{ fontSize: '0.75rem', color: 'var(--edvana-text-muted)', marginTop: '0.4rem', display: 'flex', gap: '0.75rem' }}>
                    <span>Size: {formatFileSize(doc.file_size_bytes)}</span>
                    <span>Format: {doc.mime_type?.split('/')[1]?.toUpperCase() || 'FILE'}</span>
                  </div>

                  <div style={{ fontSize: '0.75rem', color: 'var(--edvana-text-muted)', marginTop: '0.25rem' }}>
                    Uploaded: {new Date(doc.uploaded_at).toLocaleDateString()} by {doc.uploaded_by_username || 'System'}
                  </div>
                </div>

                <div style={{ 
                  marginTop: '1rem', 
                  paddingTop: '0.75rem', 
                  borderTop: '1px solid var(--edvana-border)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}>
                  <button
                    className="edvana-btn edvana-btn-secondary"
                    style={{ fontSize: '0.75rem', padding: '0.35rem 0.65rem' }}
                    onClick={() => openHistory(doc)}
                  >
                    <History size={13} style={{ marginRight: '4px' }} /> History
                  </button>

                  {isSens ? (
                    <button
                      className="edvana-btn edvana-btn-primary"
                      style={{ fontSize: '0.75rem', padding: '0.35rem 0.65rem', backgroundColor: 'var(--edvana-warning)', borderColor: 'var(--edvana-warning)' }}
                      onClick={() => setRevealDoc(doc)}
                    >
                      <Eye size={13} style={{ marginRight: '4px' }} /> Reveal & Download
                    </button>
                  ) : (
                    <a
                      href={`/api/v1/documents/${doc.id}/download/`}
                      className="edvana-btn edvana-btn-primary"
                      style={{ fontSize: '0.75rem', padding: '0.35rem 0.65rem', textDecoration: 'none' }}
                      download
                    >
                      <Download size={13} style={{ marginRight: '4px' }} /> Download
                    </a>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      );
    })()}

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="modal-backdrop">
          <div className="modal-card" style={{ maxWidth: '520px', width: '90%' }}>
            <div className="modal-header">
              <h3 style={{ margin: 0, fontSize: '1.15rem', fontWeight: '700' }}>Upload Student Document</h3>
              <button className="btn-close" onClick={() => setShowUploadModal(false)}>✕</button>
            </div>
            <form onSubmit={handleUpload}>
              <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div className="form-group">
                  <label className="form-label">Document Category *</label>
                  <select
                    className="form-control"
                    value={uploadType}
                    onChange={(e) => setUploadType(e.target.value)}
                    required
                  >
                    {Object.entries(DOCUMENT_TYPE_LABELS).map(([k, label]) => (
                      <option key={k} value={k}>{label}</option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Binary File (PDF, JPEG, PNG, max 10MB) *</label>
                  <input
                    type="file"
                    className="form-control"
                    accept=".pdf,.jpg,.jpeg,.png"
                    onChange={(e) => setUploadFile(e.target.files[0])}
                    required
                  />
                  <small style={{ fontSize: '0.75rem', color: 'var(--edvana-text-muted)', marginTop: '0.35rem', display: 'block' }}>
                    Files are stored in secure object storage. Re-uploading an existing document type automatically supersedes the previous version (ADR-011).
                  </small>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="edvana-btn edvana-btn-secondary" onClick={() => setShowUploadModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="edvana-btn edvana-btn-primary" disabled={uploadLoading}>
                  {uploadLoading ? 'Uploading...' : 'Upload & Register'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Replace Allotment Letter Modal (Task 5.2.2) */}
      {showReplaceModal && (
        <div className="modal-backdrop">
          <div className="modal-card" style={{ maxWidth: '520px', width: '90%' }}>
            <div className="modal-header">
              <h3 style={{ margin: 0, fontSize: '1.15rem', fontWeight: '700' }}>Replace Government Allotment Letter</h3>
              <button className="btn-close" onClick={() => setShowReplaceModal(false)}>✕</button>
            </div>
            <form onSubmit={handleReplaceAllotment}>
              <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--edvana-text-secondary)' }}>
                  Controlled allotment-letter replacement enforces supersession lifecycle and records an accountable audit trail (Task 5.2.2).
                </p>

                <div className="form-group">
                  <label className="form-label">Replacement Allotment PDF *</label>
                  <input
                    type="file"
                    className="form-control"
                    accept=".pdf"
                    onChange={(e) => setReplaceFile(e.target.files[0])}
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Replacement Reason (Mandatory Audit) *</label>
                  <textarea
                    className="form-control"
                    rows="3"
                    placeholder="e.g. Upgraded seat allotment in CAP Round 2 under Home University quota"
                    value={replaceReason}
                    onChange={(e) => setReplaceReason(e.target.value)}
                    required
                  />
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="edvana-btn edvana-btn-secondary" onClick={() => setShowReplaceModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="edvana-btn edvana-btn-primary" disabled={replaceLoading}>
                  {replaceLoading ? 'Replacing...' : 'Replace Allotment Letter'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Sensitive Document Reveal Modal (Tasks 5.3.1 & 5.3.2) */}
      {revealDoc && (
        <div className="modal-backdrop">
          <div className="modal-card" style={{ maxWidth: '500px', width: '90%' }}>
            <div className="modal-header">
              <h3 style={{ margin: 0, fontSize: '1.15rem', fontWeight: '700' }}>
                Reveal Sensitive Document ({DOCUMENT_TYPE_LABELS[revealDoc.document_type]})
              </h3>
              <button className="btn-close" onClick={() => setRevealDoc(null)}>✕</button>
            </div>
            <form onSubmit={handleReveal}>
              <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div style={{
                  padding: '0.75rem 1rem',
                  borderRadius: 'var(--edvana-radius-md)',
                  backgroundColor: 'rgba(239, 68, 68, 0.08)',
                  border: '1px solid var(--edvana-danger)',
                  fontSize: '0.8rem',
                  color: 'var(--edvana-danger)'
                }}>
                  <strong>Security Accountability Notice:</strong> Unmasking and downloading sensitive identity/financial documents is monitored and immutably audited under ADR-015.
                </div>

                {revealError && (
                  <div style={{ color: 'var(--edvana-danger)', fontSize: '0.85rem' }}>
                    {revealError}
                  </div>
                )}

                <div className="form-group">
                  <label className="form-label">Institutional Access Justification *</label>
                  <textarea
                    className="form-control"
                    rows="3"
                    placeholder="e.g. Verifying Aadhaar details for government MahaDBT scholarship submission"
                    value={revealReason}
                    onChange={(e) => setRevealReason(e.target.value)}
                    required
                  />
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="edvana-btn edvana-btn-secondary" onClick={() => setRevealDoc(null)}>
                  Cancel
                </button>
                <button 
                  type="submit" 
                  className="edvana-btn" 
                  style={{ backgroundColor: 'var(--edvana-warning)', color: '#ffffff', border: 'none' }}
                  disabled={revealLoading}
                >
                  {revealLoading ? 'Decrypting & Auditing...' : 'Confirm Reveal & Download'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Version History Modal (Task 5.2.1) */}
      {historyDoc && (
        <div className="modal-backdrop">
          <div className="modal-card" style={{ maxWidth: '650px', width: '90%' }}>
            <div className="modal-header">
              <h3 style={{ margin: 0, fontSize: '1.15rem', fontWeight: '700' }}>
                Version Supersession History: {DOCUMENT_TYPE_LABELS[historyDoc.document_type]}
              </h3>
              <button className="btn-close" onClick={() => setHistoryDoc(null)}>✕</button>
            </div>
            <div className="modal-body">
              {historyLoading ? (
                <div style={{ padding: '2rem', textAlign: 'center' }}>Loading history...</div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  {historyList.map((h) => (
                    <div 
                      key={h.id}
                      style={{
                        padding: '0.85rem 1rem',
                        borderRadius: 'var(--edvana-radius-md)',
                        border: '1px solid var(--edvana-border)',
                        backgroundColor: h.version_status === 'CURRENT' ? 'rgba(59, 130, 246, 0.05)' : 'var(--bg-subtle)',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center'
                      }}
                    >
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <span style={{ fontWeight: '700', fontSize: '0.9rem' }}>Version {h.version}</span>
                          <span className={`badge ${h.version_status === 'CURRENT' ? 'badge-primary' : 'badge-secondary'}`}>
                            {h.version_status}
                          </span>
                        </div>
                        <div style={{ fontSize: '0.8rem', color: 'var(--edvana-text-secondary)', marginTop: '0.2rem' }}>
                          File: {h.original_filename} ({formatFileSize(h.file_size_bytes)})
                        </div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--edvana-text-muted)' }}>
                          Uploaded: {new Date(h.uploaded_at).toLocaleString()} by {h.uploaded_by_username || 'User'}
                        </div>
                      </div>

                      <div>
                        {h.is_sensitive ? (
                          <button
                            className="edvana-btn edvana-btn-secondary"
                            style={{ fontSize: '0.75rem' }}
                            onClick={() => {
                              setHistoryDoc(null);
                              setRevealDoc(h);
                            }}
                          >
                            <Lock size={12} style={{ marginRight: '4px' }} /> Reveal
                          </button>
                        ) : (
                          <a
                            href={`/api/v1/documents/${h.id}/download/`}
                            className="edvana-btn edvana-btn-secondary"
                            style={{ fontSize: '0.75rem', textDecoration: 'none' }}
                            download
                          >
                            <Download size={12} style={{ marginRight: '4px' }} /> Download
                          </a>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
            <div className="modal-footer">
              <button className="edvana-btn edvana-btn-secondary" onClick={() => setHistoryDoc(null)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
