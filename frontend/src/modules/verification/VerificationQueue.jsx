import React, { useState, useEffect } from 'react';
import { 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  Clock, 
  RefreshCw, 
  FileText, 
  User, 
  History,
  CheckSquare,
  Search,
  Filter
} from 'lucide-react';
import api from '../../services/api';

export const VerificationQueue = () => {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('PENDING');
  const [entityFilter, setEntityFilter] = useState('');
  
  // Tabs: 'queue' | 'audit_trail'
  const [activeTab, setActiveTab] = useState('queue');

  // Decision modal state
  const [activeRequest, setActiveRequest] = useState(null);
  const [decisionType, setDecisionType] = useState('APPROVED');
  const [decisionReason, setDecisionReason] = useState('');
  const [decisionNotes, setDecisionNotes] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  // Delete modal state
  const [deletingRequest, setDeletingRequest] = useState(null);
  const [deleteReason, setDeleteReason] = useState('');
  const [deleting, setDeleting] = useState(false);

  // Audit log records
  const [auditLogs, setAuditLogs] = useState([]);
  const [auditLoading, setAuditLoading] = useState(false);

  // History modal state
  const [historyRequest, setHistoryRequest] = useState(null);

  const fetchRequests = async () => {
    try {
      setLoading(true);
      let url = '/verification/requests/';
      const params = [];
      if (statusFilter) params.push(`status=${statusFilter}`);
      if (entityFilter) params.push(`entity_type=${entityFilter}`);
      if (params.length > 0) url += `?${params.join('&')}`;

      const res = await api.get(url);
      setRequests(Array.isArray(res.data) ? res.data : (res.data?.results || []));
    } catch (err) {
      console.error('Failed to load verification requests', err);
      setRequests([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchAuditLogs = async () => {
    try {
      setAuditLoading(true);
      const res = await api.get('/verification/requests/audit-trail/');
      setAuditLogs(Array.isArray(res.data) ? res.data : []);
    } catch (err) {
      console.error('Failed to load audit trail', err);
      setAuditLogs([]);
    } finally {
      setAuditLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'audit_trail') {
      fetchAuditLogs();
    } else {
      fetchRequests();
    }
  }, [activeTab, statusFilter, entityFilter]);

  const handleDecision = async (e) => {
    e.preventDefault();
    if (!activeRequest) return;

    try {
      setActionLoading(true);
      await api.post(`/verification/requests/${activeRequest.id}/decide/`, {
        decision: decisionType,
        rejection_reason: decisionReason,
        notes: decisionNotes,
      });

      setActiveRequest(null);
      setDecisionReason('');
      setDecisionNotes('');
      fetchRequests();
    } catch (err) {
      alert('Decision failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setActionLoading(false);
    }
  };

  const handleDeleteRequest = async (e) => {
    e.preventDefault();
    if (!deletingRequest) return;

    try {
      setDeleting(true);
      await api.delete(`/verification/requests/${deletingRequest.id}/`);
      setDeletingRequest(null);
      setDeleteReason('');
      fetchRequests();
    } catch (err) {
      alert('Delete failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setDeleting(false);
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'APPROVED':
        return <span className="badge badge-success"><CheckCircle2 size={12} style={{ marginRight: '4px' }} /> Approved</span>;
      case 'REJECTED':
        return <span className="badge badge-danger"><XCircle size={12} style={{ marginRight: '4px' }} /> Rejected</span>;
      case 'NEEDS_CORRECTION':
        return <span className="badge badge-warning"><AlertTriangle size={12} style={{ marginRight: '4px' }} /> Needs Correction</span>;
      case 'PENDING':
        return <span className="badge" style={{ backgroundColor: 'var(--primary-100)', color: 'var(--primary-700)' }}><Clock size={12} style={{ marginRight: '4px' }} /> Pending Review</span>;
      default:
        return <span className="badge">{status}</span>;
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header Banner */}
      <div className="card" style={{
        background: 'linear-gradient(135deg, var(--bg-surface) 0%, rgba(59, 130, 246, 0.05) 100%)',
        border: '1px solid var(--border-subtle)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '1.5rem 2rem'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
          <div style={{
            width: '52px',
            height: '52px',
            borderRadius: 'var(--radius-lg)',
            backgroundColor: 'rgba(59, 130, 246, 0.12)',
            color: 'var(--primary-600)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <CheckSquare size={28} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <h1 style={{ fontSize: '1.5rem', fontWeight: '800', color: 'var(--text-primary)', margin: 0 }}>
                Verification & Official Records
              </h1>
              <span className="badge badge-primary">Deliverable D.5</span>
            </div>
            <p style={{ margin: '0.25rem 0 0', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
              Guarded verification state-machine, document approvals, and authoritative student-record correction updates.
            </p>
          </div>
        </div>

        <button 
          className="btn btn-secondary"
          onClick={activeTab === 'audit_trail' ? fetchAuditLogs : fetchRequests}
          style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
        >
          <RefreshCw size={16} /> Refresh
        </button>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '1rem', borderBottom: '1px solid var(--border-subtle)' }}>
        <button
          onClick={() => setActiveTab('queue')}
          style={{
            padding: '0.75rem 1rem',
            background: 'none',
            border: 'none',
            borderBottom: activeTab === 'queue' ? '2px solid var(--primary-600)' : '2px solid transparent',
            color: activeTab === 'queue' ? 'var(--primary-600)' : 'var(--text-secondary)',
            fontWeight: '600',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}
        >
          <CheckSquare size={16} /> Verification Queue
        </button>
        <button
          onClick={() => setActiveTab('audit_trail')}
          style={{
            padding: '0.75rem 1rem',
            background: 'none',
            border: 'none',
            borderBottom: activeTab === 'audit_trail' ? '2px solid var(--primary-600)' : '2px solid transparent',
            color: activeTab === 'audit_trail' ? 'var(--primary-600)' : 'var(--text-secondary)',
            fontWeight: '600',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}
        >
          <History size={16} /> Audit Trail & Verifier Activity Log
        </button>
      </div>

      {activeTab === 'queue' ? (
        <>
      {/* Filter Toolbar */}
      <div className="card" style={{ padding: '1rem 1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        {/* Status Pill Filters */}
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          {[
            { id: 'PENDING', label: 'Pending Review' },
            { id: 'APPROVED', label: 'Approved' },
            { id: 'NEEDS_CORRECTION', label: 'Needs Correction' },
            { id: 'REJECTED', label: 'Rejected' },
            { id: '', label: 'All Records' },
          ].map((item) => (
            <button
              key={item.id}
              className={`btn btn-sm ${statusFilter === item.id ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setStatusFilter(item.id)}
            >
              {item.label}
            </button>
          ))}
        </div>

        {/* Entity Type Filter */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Entity Type:</span>
          <select 
            className="form-control"
            value={entityFilter}
            onChange={(e) => setEntityFilter(e.target.value)}
            style={{ width: '180px', fontSize: '0.85rem' }}
          >
            <option value="">All Types</option>
            <option value="DOCUMENT">Document</option>
            <option value="GOVERNMENT_CORRECTION">Govt Correction</option>
            <option value="PERSONAL_INFO">Personal Info</option>
            <option value="ADDRESS">Address</option>
            <option value="BANK_DETAILS">Bank Details</option>
          </select>
        </div>
      </div>

      {/* Verification Queue Table */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        {loading ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
            Loading verification queue...
          </div>
        ) : requests.length === 0 ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
            No verification requests found for this filter.
          </div>
        ) : (
          <div className="table-responsive">
            <table className="table" style={{ margin: 0 }}>
              <thead>
                <tr>
                  <th>Student</th>
                  <th>Submission Type</th>
                  <th>Field / Reference</th>
                  <th>Submitted Value</th>
                  <th>Version</th>
                  <th>Status</th>
                  <th>Submitted</th>
                  <th style={{ textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {requests.map((req) => (
                  <tr key={req.id}>
                    <td>
                      <div style={{ fontWeight: '600', color: 'var(--text-primary)' }}>
                        {req.student_name}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        ID: {req.student.substring(0, 8)}...
                      </div>
                    </td>
                    <td>
                      <span className="badge" style={{ backgroundColor: 'var(--bg-subtle)', fontSize: '0.75rem' }}>
                        {req.entity_type}
                      </span>
                    </td>
                    <td>
                      <div style={{ fontSize: '0.85rem', fontWeight: '500' }}>
                        {req.field_name || (req.entity_id ? `Document Ref` : '—')}
                      </div>
                    </td>
                    <td>
                      <div style={{ fontSize: '0.85rem', maxWidth: '200px', wordBreak: 'break-word' }}>
                        {req.submitted_value ? <code>{req.submitted_value}</code> : 'File Asset'}
                      </div>
                    </td>
                    <td>
                      <span style={{ fontSize: '0.8rem', fontWeight: '600', color: 'var(--text-muted)' }}>
                        v{req.current_version}
                      </span>
                    </td>
                    <td>{getStatusBadge(req.status)}</td>
                    <td>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                        {new Date(req.submitted_at).toLocaleDateString()}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        by {req.submitted_by_username || 'User'}
                      </div>
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
                        <button
                          className="btn btn-secondary btn-sm"
                          onClick={() => setHistoryRequest(req)}
                          style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}
                        >
                          <History size={13} /> Decisions ({req.decisions?.length || 0})
                        </button>
                        {req.status === 'PENDING' && (
                          <>
                            <button
                              className="btn btn-primary btn-sm"
                              onClick={() => {
                                setActiveRequest(req);
                                setDecisionType('APPROVED');
                              }}
                            >
                              Verify
                            </button>
                            <button
                              className="btn btn-warning btn-sm"
                              onClick={() => {
                                setActiveRequest(req);
                                setDecisionType('REJECTED');
                              }}
                              title="Reject submission"
                            >
                              Reject
                            </button>
                            <button
                              className="btn btn-danger btn-sm"
                              onClick={() => {
                                setDeletingRequest(req);
                                setDeleteReason('');
                              }}
                              title="Delete unwanted request"
                            >
                              Delete
                            </button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
      </>
      ) : (
        /* AUDIT TRAIL TAB */
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ padding: '1.25rem 1.5rem', borderBottom: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: '700', color: 'var(--text-primary)' }}>
                Authoritative Decision Log & Audit Trail
              </h3>
              <p style={{ margin: '0.2rem 0 0', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                Immutable historical trail of all verifier reviews, approvals, rejections, and administrative actions.
              </p>
            </div>
            <span className="badge badge-info">{auditLogs.length} Total Audit Records</span>
          </div>

          {auditLoading ? (
            <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
              Loading audit logs...
            </div>
          ) : auditLogs.length === 0 ? (
            <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
              No audit decisions recorded yet.
            </div>
          ) : (
            <div className="table-responsive">
              <table className="table" style={{ margin: 0 }}>
                <thead>
                  <tr>
                    <th>Timestamp</th>
                    <th>Candidate</th>
                    <th>Item Verified</th>
                    <th>Action</th>
                    <th>Reviewing Officer</th>
                    <th>Reason / Notes</th>
                  </tr>
                </thead>
                <tbody>
                  {auditLogs.map((log) => (
                    <tr key={log.id}>
                      <td style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
                        {log.timestamp ? new Date(log.timestamp).toLocaleString() : '—'}
                      </td>
                      <td>
                        <div style={{ fontWeight: '600', color: 'var(--text-primary)' }}>{log.candidate_name}</div>
                        {log.application_id && (
                          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>App: {log.application_id}</div>
                        )}
                      </td>
                      <td>
                        <span className="badge" style={{ backgroundColor: 'var(--bg-subtle)', fontSize: '0.72rem' }}>
                          {log.entity_type}
                        </span>
                        <div style={{ fontSize: '0.8rem', marginTop: '0.2rem' }}>{log.field_name || 'Document Record'}</div>
                      </td>
                      <td>
                        <span className={`badge ${log.action === 'APPROVED' ? 'badge-success' : log.action === 'REJECTED' ? 'badge-danger' : 'badge-warning'}`}>
                          {log.action}
                        </span>
                      </td>
                      <td>
                        <div style={{ fontWeight: '500', fontSize: '0.85rem' }}>{log.actor}</div>
                        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{log.actor_role}</div>
                      </td>
                      <td style={{ fontSize: '0.82rem', maxWidth: '280px' }}>
                        {log.rejection_reason && (
                          <div style={{ color: 'var(--danger-600)', fontWeight: '500' }}>
                            {log.rejection_reason}
                          </div>
                        )}
                        {log.notes && (
                          <div style={{ color: 'var(--text-secondary)' }}>
                            {log.notes}
                          </div>
                        )}
                        {!log.rejection_reason && !log.notes && <span style={{ color: 'var(--text-muted)' }}>—</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Review Decision Modal */}
      {activeRequest && (
        <div className="modal-backdrop">
          <div className="modal-card" style={{ maxWidth: '540px', width: '90%' }}>
            <div className="modal-header">
              <h3 style={{ margin: 0, fontSize: '1.2rem', fontWeight: '700' }}>
                Review Verification Request (v{activeRequest.current_version})
              </h3>
              <button className="btn-close" onClick={() => setActiveRequest(null)}>✕</button>
            </div>
            <form onSubmit={handleDecision}>
              <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div style={{ padding: '0.75rem 1rem', borderRadius: 'var(--radius-md)', backgroundColor: 'var(--bg-subtle)' }}>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Student:</div>
                  <div style={{ fontWeight: '600' }}>{activeRequest.student_name}</div>
                  <div style={{ fontSize: '0.85rem', marginTop: '0.35rem' }}>
                    <strong>{activeRequest.entity_type}:</strong> {activeRequest.field_name || 'Asset'}
                  </div>
                  {activeRequest.submitted_value && (
                    <div style={{ fontSize: '0.85rem', marginTop: '0.25rem' }}>
                      <strong>Submitted Value:</strong> <code>{activeRequest.submitted_value}</code>
                    </div>
                  )}
                </div>

                <div className="form-group">
                  <label className="form-label">Review Decision *</label>
                  <select
                    className="form-control"
                    value={decisionType}
                    onChange={(e) => setDecisionType(e.target.value)}
                  >
                    <option value="APPROVED">Approve (Accept for official student record)</option>
                    <option value="NEEDS_CORRECTION">Needs Correction (Return to student for re-submission)</option>
                    <option value="REJECTED">Reject (Decline submission permanently)</option>
                  </select>
                </div>

                {decisionType !== 'APPROVED' && (
                  <div className="form-group">
                    <label className="form-label">Mandatory Reason *</label>
                    <textarea
                      className="form-control"
                      rows="3"
                      placeholder="Specify why the item is rejected or what needs correction..."
                      value={decisionReason}
                      onChange={(e) => setDecisionReason(e.target.value)}
                      required
                    />
                  </div>
                )}

                <div className="form-group">
                  <label className="form-label">Verification Notes (Optional)</label>
                  <input
                    type="text"
                    className="form-control"
                    placeholder="e.g. Cross-verified with government merit register"
                    value={decisionNotes}
                    onChange={(e) => setDecisionNotes(e.target.value)}
                  />
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setActiveRequest(null)}>
                  Cancel
                </button>
                <button 
                  type="submit" 
                  className={`btn ${decisionType === 'APPROVED' ? 'btn-primary' : decisionType === 'REJECTED' ? 'btn-danger' : 'btn-warning'}`}
                  disabled={actionLoading}
                >
                  {actionLoading ? 'Recording...' : `Confirm ${decisionType}`}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Decision History Modal (Task 6.2.2) */}
      {historyRequest && (
        <div className="modal-backdrop">
          <div className="modal-card" style={{ maxWidth: '640px', width: '90%' }}>
            <div className="modal-header">
              <h3 style={{ margin: 0, fontSize: '1.2rem', fontWeight: '700' }}>
                Verification Decision History & Audit Trail
              </h3>
              <button className="btn-close" onClick={() => setHistoryRequest(null)}>✕</button>
            </div>
            <div className="modal-body">
              {!historyRequest.decisions || historyRequest.decisions.length === 0 ? (
                <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                  No decisions recorded yet. This item is pending initial review.
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  {historyRequest.decisions.map((d) => (
                    <div 
                      key={d.id}
                      style={{
                        padding: '1rem',
                        borderRadius: 'var(--radius-md)',
                        border: '1px solid var(--border-subtle)',
                        backgroundColor: d.decision === 'APPROVED' ? 'rgba(34, 197, 94, 0.05)' : 'rgba(239, 68, 68, 0.05)'
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <span style={{ fontWeight: '700' }}>Version {d.version}</span>
                          {getStatusBadge(d.decision)}
                        </div>
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                          {new Date(d.reviewed_at).toLocaleString()}
                        </span>
                      </div>

                      <div style={{ fontSize: '0.85rem', marginTop: '0.4rem' }}>
                        <strong>Reviewer:</strong> {d.reviewer_username}
                      </div>

                      {d.rejection_reason && (
                        <div style={{ fontSize: '0.85rem', color: 'var(--danger-600)', marginTop: '0.25rem' }}>
                          <strong>Reason:</strong> {d.rejection_reason}
                        </div>
                      )}

                      {d.notes && (
                        <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
                          <strong>Notes:</strong> {d.notes}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setHistoryRequest(null)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Request Modal */}
      {deletingRequest && (
        <div className="modal-backdrop">
          <div className="modal-card" style={{ maxWidth: '480px', width: '90%' }}>
            <div className="modal-header">
              <h3 style={{ margin: 0, fontSize: '1.2rem', fontWeight: '700', color: 'var(--danger-600)' }}>
                Delete Verification Request
              </h3>
              <button className="btn-close" onClick={() => setDeletingRequest(null)}>✕</button>
            </div>
            <form onSubmit={handleDeleteRequest}>
              <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <p style={{ margin: 0, fontSize: '0.9rem', color: 'var(--text-primary)' }}>
                  Are you sure you want to permanently remove this verification item for <strong>{deletingRequest.student_name}</strong>?
                </p>

                <div style={{
                  padding: '0.75rem 1rem',
                  backgroundColor: 'rgba(239, 68, 68, 0.08)',
                  border: '1px solid rgba(239, 68, 68, 0.2)',
                  borderRadius: 'var(--radius-md)',
                  fontSize: '0.82rem'
                }}>
                  <div><strong>Item:</strong> {deletingRequest.entity_type} {deletingRequest.field_name ? `(${deletingRequest.field_name})` : ''}</div>
                  {deletingRequest.submitted_value && <div><strong>Value:</strong> <code>{deletingRequest.submitted_value}</code></div>}
                </div>

                <div className="form-group">
                  <label className="form-label">Deletion Audit Reason *</label>
                  <textarea
                    className="form-control"
                    rows="2"
                    placeholder="e.g. Erroneous government duplicate submission / Unwanted request..."
                    value={deleteReason}
                    onChange={(e) => setDeleteReason(e.target.value)}
                    required
                  />
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setDeletingRequest(null)}>
                  Cancel
                </button>
                <button 
                  type="submit" 
                  className="btn btn-danger"
                  disabled={deleting}
                >
                  {deleting ? 'Deleting...' : 'Confirm Delete'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
