import React, { useState, useEffect } from 'react';
import { 
  ArrowLeft, 
  CheckCircle, 
  AlertCircle, 
  AlertTriangle, 
  Clock, 
  RefreshCw,
  UserCheck,
  UserPlus,
  Ban
} from 'lucide-react';

export const StagingRowViewer = ({ batchId, onBack }) => {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [selectedRow, setSelectedRow] = useState(null);
  const [resolvingRow, setResolvingRow] = useState(null);
  const [resolveAction, setResolveAction] = useState('FORCE_AS_NEW');
  const [chosenStudentId, setChosenStudentId] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  const fetchRows = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('access_token');
      const url = statusFilter 
        ? `/api/v1/onboarding/batches/${batchId}/staging-rows/?status=${statusFilter}`
        : `/api/v1/onboarding/batches/${batchId}/staging-rows/`;
      const res = await fetch(url, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      });
      if (res.ok) {
        const data = await res.json();
        const rowData = Array.isArray(data) ? data : (data?.results || []);
        setRows(rowData);
      }
    } catch (err) {
      console.error('Error fetching staging rows:', err);
      setRows([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRows();
  }, [batchId, statusFilter]);

  const handleResolve = async (e) => {
    e.preventDefault();
    if (!resolvingRow) return;
    try {
      setActionLoading(true);
      const token = localStorage.getItem('access_token');
      const payload = {
        action: resolveAction,
        chosen_student_id: resolveAction === 'LINK_TO_STUDENT' ? chosenStudentId : null
      };
      const res = await fetch(`/api/v1/onboarding/staging-rows/${resolvingRow.id}/resolve/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        setResolvingRow(null);
        fetchRows();
      } else {
        const err = await res.json();
        alert(`Resolution failed: ${err.detail || 'Unknown error'}`);
      }
    } catch (err) {
      alert('Error submitting resolution: ' + err.message);
    } finally {
      setActionLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'IMPORTED':
        return <span className="badge badge-success"><CheckCircle size={12} style={{ marginRight: '4px' }} /> Imported</span>;
      case 'VALIDATED':
        return <span className="badge badge-primary"><CheckCircle size={12} style={{ marginRight: '4px' }} /> Validated</span>;
      case 'CONFLICT':
        return <span className="badge badge-warning"><AlertTriangle size={12} style={{ marginRight: '4px' }} /> Conflict</span>;
      case 'INVALID':
        return <span className="badge badge-danger"><AlertCircle size={12} style={{ marginRight: '4px' }} /> Invalid</span>;
      case 'SKIPPED':
        return <span className="badge" style={{ backgroundColor: 'var(--bg-subtle)', color: 'var(--text-muted)' }}><Ban size={12} style={{ marginRight: '4px' }} /> Skipped</span>;
      default:
        return <span className="badge" style={{ backgroundColor: 'var(--bg-subtle)' }}><Clock size={12} style={{ marginRight: '4px' }} /> {status}</span>;
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <button 
            className="btn btn-secondary"
            onClick={onBack}
            style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
          >
            <ArrowLeft size={16} /> Back to Batches
          </button>
          <div>
            <h1 style={{ fontSize: '1.4rem', fontWeight: '700', color: 'var(--text-primary)', margin: 0 }}>
              Batch Staging Rows
            </h1>
            <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              Verbatim extraction, data cleaning, and deterministic matching review.
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <select 
            className="form-control"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            style={{ width: '180px' }}
          >
            <option value="">All Statuses</option>
            <option value="PENDING">Pending</option>
            <option value="VALIDATED">Validated</option>
            <option value="CONFLICT">Conflict</option>
            <option value="INVALID">Invalid</option>
            <option value="IMPORTED">Imported</option>
            <option value="SKIPPED">Skipped</option>
          </select>
          <button 
            className="btn btn-secondary"
            onClick={fetchRows}
            style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
          >
            <RefreshCw size={15} /> Refresh
          </button>
        </div>
      </div>

      {/* Main Table */}
      {(() => {
        const safeRows = Array.isArray(rows) ? rows : [];
        if (loading) {
          return (
            <div className="card" style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
              Loading staging rows...
            </div>
          );
        }
        if (safeRows.length === 0) {
          return (
            <div className="card" style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
              No staging rows found for this filter.
            </div>
          );
        }
        return (
          <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
            <div className="table-responsive">
              <table className="table" style={{ margin: 0 }}>
                <thead>
                  <tr>
                    <th style={{ width: '60px' }}>Row #</th>
                    <th>Candidate Name</th>
                    <th>Application / Enrollment</th>
                    <th>Choice Code → Branch</th>
                    <th>Gender & DOB</th>
                    <th>Match Result</th>
                    <th>Status</th>
                    <th style={{ textAlign: 'right' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {safeRows.map((r) => {
                  const norm = r.normalized_data || {};
                  return (
                    <tr key={r.id}>
                      <td style={{ fontWeight: '600', color: 'var(--text-muted)' }}>#{r.row_number}</td>
                      <td>
                        <div style={{ fontWeight: '600', color: 'var(--text-primary)' }}>
                          {norm.candidate_name || r.raw_data?.candidate_name || r.raw_data?.name || '—'}
                        </div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                          Mobile: {norm.student_mobile || '—'}
                        </div>
                      </td>
                      <td>
                        <div style={{ fontSize: '0.85rem' }}>
                          App ID: <span style={{ fontWeight: '500' }}>{norm.application_id || '—'}</span>
                        </div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                          Enrollment: {norm.enrollment_no || '—'}
                        </div>
                      </td>
                      <td>
                        <div style={{ fontSize: '0.85rem', fontWeight: '600', fontFamily: 'monospace' }}>
                          {norm.choice_code || norm.program_code || '—'}
                        </div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                          auto-mapped on import
                        </div>
                      </td>
                      <td>
                        <div style={{ fontSize: '0.85rem' }}>{norm.gender || '—'}</div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                          {norm.date_of_birth || '—'}
                        </div>
                      </td>
                      <td>
                        <div style={{ fontSize: '0.8rem', fontWeight: '500' }}>
                          {r.match_type === 'NEW' && <span style={{ color: 'var(--success-600)' }}>New Student</span>}
                          {r.match_type === 'APPLICATION_ID' && <span style={{ color: 'var(--primary-600)' }}>Matched (App ID)</span>}
                          {r.match_type === 'ENROLLMENT_NO' && <span style={{ color: 'var(--primary-600)' }}>Matched (Enrollment)</span>}
                          {r.match_type === 'BOARD_ENROLLMENT_NO' && <span style={{ color: 'var(--primary-600)' }}>Matched (Board Roll)</span>}
                          {r.match_type === 'CONFLICT' && <span style={{ color: 'var(--warning-600)' }}>Conflicting Identifiers</span>}
                          {!r.match_type && <span style={{ color: 'var(--text-muted)' }}>Unmatched</span>}
                        </div>
                      </td>
                      <td>{getStatusBadge(r.processing_status)}</td>
                      <td style={{ textAlign: 'right' }}>
                        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
                          <button
                            className="btn btn-secondary btn-sm"
                            onClick={() => setSelectedRow(r)}
                          >
                            Inspect
                          </button>
                          {r.processing_status === 'CONFLICT' && (
                            <button
                              className="btn btn-primary btn-sm"
                              onClick={() => {
                                setResolvingRow(r);
                                setResolveAction('FORCE_AS_NEW');
                              }}
                            >
                              Resolve
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      );
    })()}

      {/* Row Inspection Modal */}
      {selectedRow && (
        <div className="modal-backdrop">
          <div className="modal-card" style={{ maxWidth: '750px', width: '90%' }}>
            <div className="modal-header">
              <h3 style={{ margin: 0, fontSize: '1.15rem', fontWeight: '700' }}>
                Inspect Staging Row #{selectedRow.row_number}
              </h3>
              <button className="btn-close" onClick={() => setSelectedRow(null)}>✕</button>
            </div>
            <div className="modal-body" style={{ maxHeight: '70vh', overflowY: 'auto' }}>
              {selectedRow.validation_errors && selectedRow.validation_errors.length > 0 && (
                <div style={{
                  padding: '0.85rem 1rem',
                  backgroundColor: 'rgba(239, 68, 68, 0.1)',
                  border: '1px solid var(--danger-500)',
                  borderRadius: 'var(--radius-md)',
                  marginBottom: '1rem'
                }}>
                  <div style={{ fontWeight: '600', color: 'var(--danger-600)', marginBottom: '0.25rem' }}>
                    Validation Errors:
                  </div>
                  <ul style={{ margin: 0, paddingLeft: '1.25rem', color: 'var(--danger-700)', fontSize: '0.85rem' }}>
                    {selectedRow.validation_errors.map((err, idx) => (
                      <li key={idx}>{err}</li>
                    ))}
                  </ul>
                </div>
              )}

              {selectedRow.conflict_details && (
                <div style={{
                  padding: '0.85rem 1rem',
                  backgroundColor: 'rgba(245, 158, 11, 0.1)',
                  border: '1px solid var(--warning-500)',
                  borderRadius: 'var(--radius-md)',
                  marginBottom: '1rem'
                }}>
                  <div style={{ fontWeight: '600', color: 'var(--warning-700)', marginBottom: '0.25rem' }}>
                    Identity Conflict Alert:
                  </div>
                  <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--warning-800)' }}>
                    {selectedRow.conflict_details.message}
                  </p>
                </div>
              )}

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginTop: '0.5rem' }}>
                <div>
                  <h4 style={{ fontSize: '0.85rem', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
                    Raw Excel Data (Verbatim)
                  </h4>
                  <pre style={{
                    backgroundColor: 'var(--bg-subtle)',
                    padding: '0.75rem',
                    borderRadius: 'var(--radius-md)',
                    fontSize: '0.75rem',
                    overflowX: 'auto',
                    border: '1px solid var(--border-subtle)'
                  }}>
                    {JSON.stringify(selectedRow.raw_data, null, 2)}
                  </pre>
                </div>
                <div>
                  <h4 style={{ fontSize: '0.85rem', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
                    Normalized Canonical Data
                  </h4>
                  <pre style={{
                    backgroundColor: 'var(--bg-subtle)',
                    padding: '0.75rem',
                    borderRadius: 'var(--radius-md)',
                    fontSize: '0.75rem',
                    overflowX: 'auto',
                    border: '1px solid var(--border-subtle)'
                  }}>
                    {JSON.stringify(selectedRow.normalized_data, null, 2)}
                  </pre>
                </div>
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setSelectedRow(null)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Conflict Resolution Modal */}
      {resolvingRow && (
        <div className="modal-backdrop">
          <div className="modal-card" style={{ maxWidth: '550px', width: '90%' }}>
            <div className="modal-header">
              <h3 style={{ margin: 0, fontSize: '1.15rem', fontWeight: '700' }}>
                Resolve Identity Conflict (Row #{resolvingRow.row_number})
              </h3>
              <button className="btn-close" onClick={() => setResolvingRow(null)}>✕</button>
            </div>
            <form onSubmit={handleResolve}>
              <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: 0 }}>
                  Incoming record has identifiers pointing to divergent existing records in the database.
                  Choose an institutional resolution strategy:
                </p>

                <div className="form-group">
                  <label className="form-label">Resolution Action</label>
                  <select
                    className="form-control"
                    value={resolveAction}
                    onChange={(e) => setResolveAction(e.target.value)}
                  >
                    <option value="FORCE_AS_NEW">Create as New Student Record</option>
                    <option value="LINK_TO_STUDENT">Link to Specific Existing Student ID</option>
                    <option value="SKIP">Skip Row from Production Import</option>
                  </select>
                </div>

                {resolveAction === 'LINK_TO_STUDENT' && (
                  <div className="form-group">
                    <label className="form-label">Target Student UUID</label>
                    <input
                      type="text"
                      className="form-control"
                      placeholder="e.g. 123e4567-e89b-12d3-a456-426614174000"
                      value={chosenStudentId}
                      onChange={(e) => setChosenStudentId(e.target.value)}
                      required
                    />
                  </div>
                )}
              </div>
              <div className="modal-footer">
                <button 
                  type="button" 
                  className="btn btn-secondary" 
                  onClick={() => setResolvingRow(null)}
                >
                  Cancel
                </button>
                <button 
                  type="submit" 
                  className="btn btn-primary"
                  disabled={actionLoading}
                >
                  {actionLoading ? 'Saving...' : 'Apply Resolution'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
