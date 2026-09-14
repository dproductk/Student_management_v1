import React, { useState, useEffect } from 'react';
import {
  CheckCircle2,
  AlertCircle,
  Play,
  Eye,
  Clock,
  CheckCircle,
  Trash2,
  Search,
  Upload,
  ChevronLeft,
  ChevronRight,
  X,
  Download
} from 'lucide-react';
import { StagingRowViewer } from './StagingRowViewer';
import api from '../../services/api';

export const ImportBatchList = () => {
  const [batches, setBatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeBatchId, setActiveBatchId] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 10;

  // Upload modal state
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadYearId, setUploadYearId] = useState('');
  const [uploading, setUploading] = useState(false);

  // Execute modal state — no branch/program selection: per-row choice-code mapping handles it
  const [executingBatch, setExecutingBatch] = useState(null);
  const [academicYears, setAcademicYears] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [semesters, setSemesters] = useState([]);
  const [schemes, setSchemes] = useState([]);
  const [batchCohorts, setBatchCohorts] = useState([]);

  const [execSemesterId, setExecSemesterId] = useState('');
  const [execSchemeId, setExecSchemeId] = useState('');
  const [execBatchCohortId, setExecBatchCohortId] = useState('');
  const [executing, setExecuting] = useState(false);

  // Delete state (available on every account that can view this table)
  const [batchToDelete, setBatchToDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);

  const fetchBatches = async () => {
    try {
      setLoading(true);
      const res = await api.get('/onboarding/batches/');
      const data = Array.isArray(res.data) ? res.data : (res.data?.results || []);
      setBatches(data);
    } catch (err) {
      console.error('Error fetching import batches:', err);
      setBatches([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchAcademicDropdowns = async () => {
    try {
      const [yRes, dRes, sRes, scRes, bRes] = await Promise.all([
        api.get('/academic/academic-years/').catch(() => ({ data: [] })),
        api.get('/academic/departments/').catch(() => ({ data: [] })),
        api.get('/academic/semesters/').catch(() => ({ data: [] })),
        api.get('/academic/schemes/').catch(() => ({ data: [] })),
        api.get('/academic/batches/').catch(() => ({ data: [] }))
      ]);
      const toArr = (res) => Array.isArray(res.data) ? res.data : (res.data?.results || []);
      setAcademicYears(toArr(yRes));
      setDepartments(toArr(dRes));
      setSemesters(toArr(sRes));
      setSchemes(toArr(scRes));
      setBatchCohorts(toArr(bRes));
    } catch (err) {
      console.error('Error fetching academic dropdowns:', err);
    }
  };

  useEffect(() => {
    fetchBatches();
    fetchAcademicDropdowns();
  }, []);

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!uploadFile) {
      alert('Please select an Excel file.');
      return;
    }

    try {
      setUploading(true);
      const formData = new FormData();
      formData.append('file', uploadFile);
      if (uploadYearId) formData.append('academic_year_id', uploadYearId);
      // No department_id: college-wide upload, per-row choice-code mapping handles branches.

      const token = localStorage.getItem('access_token');
      const res = await fetch('/api/v1/onboarding/batches/upload/', {
        method: 'POST',
        headers: token ? { 'Authorization': `Bearer ${token}` } : {},
        body: formData
      });

      if (res.ok) {
        setIsUploadOpen(false);
        setUploadFile(null);
        fetchBatches();
      } else {
        const err = await res.json();
        alert(`Upload failed: ${err.detail || 'Failed to upload file'}`);
      }
    } catch (err) {
      alert('Error uploading file: ' + err.message);
    } finally {
      setUploading(false);
    }
  };

  const handleValidate = async (batchId) => {
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(`/api/v1/onboarding/batches/${batchId}/validate/`, {
        method: 'POST',
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      });
      if (res.ok) {
        fetchBatches();
      } else {
        const err = await res.json();
        alert(`Validation error: ${err.detail || 'Validation failed'}`);
      }
    } catch (err) {
      alert('Error validating batch: ' + err.message);
    }
  };

  const handleExecute = async (e) => {
    e.preventDefault();
    if (!executingBatch) return;

    try {
      setExecuting(true);
      const token = localStorage.getItem('access_token');
      // No branch/program selection: backend maps each row via its choice code.
      const payload = {
        default_program_id: null,
        default_semester_id: execSemesterId || null,
        default_scheme_id: execSchemeId || null,
        default_batch_id: execBatchCohortId || null,
      };

      const res = await fetch(`/api/v1/onboarding/batches/${executingBatch.id}/execute/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        setExecutingBatch(null);
        fetchBatches();
      } else {
        const err = await res.json();
        alert(`Import execution error: ${err.detail || 'Import failed'}`);
      }
    } catch (err) {
      alert('Error executing import: ' + err.message);
    } finally {
      setExecuting(false);
    }
  };

  const handleDelete = async () => {
    if (!batchToDelete) return;
    try {
      setDeleting(true);
      await api.delete(`/onboarding/batches/${batchToDelete.id}/`);
      setBatchToDelete(null);
      fetchBatches();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to delete batch.');
    } finally {
      setDeleting(false);
    }
  };

  const getStatusBadge = (status) => {
    const base = {
      display: 'inline-flex',
      alignItems: 'center',
      gap: '5px',
      fontSize: '11px',
      fontWeight: '700',
      letterSpacing: '0.04em',
      padding: '4px 10px',
      borderRadius: '999px',
      border: '1px solid',
      whiteSpace: 'nowrap',
    };
    switch (status) {
      case 'COMPLETED':
        return (
          <span style={{ ...base, backgroundColor: '#ecfdf5', color: '#059669', borderColor: '#a7f3d0' }}>
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#059669' }} />
            COMPLETED
          </span>
        );
      case 'PARTIALLY_COMPLETED':
        return (
          <span style={{ ...base, backgroundColor: '#fffbeb', color: '#d97706', borderColor: '#fde68a' }}>
            <AlertCircle size={12} /> PARTIALLY COMPLETED
          </span>
        );
      case 'VALIDATED':
        return (
          <span style={{ ...base, backgroundColor: '#eff6ff', color: '#2563eb', borderColor: '#bfdbfe' }}>
            <CheckCircle2 size={12} /> VALIDATED
          </span>
        );
      case 'VALIDATING':
        return (
          <span style={{ ...base, backgroundColor: '#eff6ff', color: '#1d4ed8', borderColor: '#bfdbfe' }}>
            <Clock size={12} /> VALIDATING
          </span>
        );
      case 'IMPORTING':
        return (
          <span style={{ ...base, backgroundColor: '#faf5ff', color: '#7c3aed', borderColor: '#ddd6fe' }}>
            <Clock size={12} /> IMPORTING
          </span>
        );
      case 'UPLOADED':
        return (
          <span style={{ ...base, backgroundColor: '#eff6ff', color: '#2563eb', borderColor: '#bfdbfe' }}>
            <Download size={12} /> UPLOADED
          </span>
        );
      case 'FAILED':
        return (
          <span style={{ ...base, backgroundColor: '#fef2f2', color: '#dc2626', borderColor: '#fecaca' }}>
            <AlertCircle size={12} /> FAILED
          </span>
        );
      default:
        return (
          <span style={{ ...base, backgroundColor: '#f1f5f9', color: '#475569', borderColor: '#e2e8f0' }}>
            {status}
          </span>
        );
    }
  };

  const formatUploadedAt = (iso) => {
    if (!iso) return { date: '—', time: '' };
    const d = new Date(iso);
    if (isNaN(d.getTime())) return { date: '—', time: '' };
    const date = `${d.getMonth() + 1}/${d.getDate()}/${d.getFullYear()}`;
    const time = d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', second: '2-digit', hour12: true });
    return { date, time };
  };

  if (activeBatchId) {
    return (
      <StagingRowViewer
        batchId={activeBatchId}
        onBack={() => {
          setActiveBatchId(null);
          fetchBatches();
        }}
      />
    );
  }

  const safeBatches = Array.isArray(batches) ? batches : [];
  const q = searchQuery.trim().toLowerCase();
  const filtered = q
    ? safeBatches.filter((b) =>
        (b.source_file_name || '').toLowerCase().includes(q) ||
        (b.department_name || '').toLowerCase().includes(q) ||
        (b.academic_year_name || '').toLowerCase().includes(q)
      )
    : safeBatches;

  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
  const safePage = Math.min(currentPage, totalPages);
  const paged = filtered.slice((safePage - 1) * pageSize, safePage * pageSize);
  const from = filtered.length === 0 ? 0 : (safePage - 1) * pageSize + 1;
  const to = Math.min(safePage * pageSize, filtered.length);

  const btnBase = {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '5px',
    fontSize: '12px',
    fontWeight: '600',
    padding: '6px 12px',
    borderRadius: '6px',
    border: '1px solid',
    cursor: 'pointer',
    whiteSpace: 'nowrap',
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Breadcrumb */}
      <div style={{ fontSize: '12px', color: '#64748b', display: 'flex', alignItems: 'center', gap: '6px' }}>
        <span style={{ color: '#2563eb', fontWeight: '500' }}>Admissions</span>
        <span style={{ color: '#cbd5e1' }}>›</span>
        <span>Data Import</span>
      </div>

      {/* Title row */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '16px' }}>
        <div>
          <h1 style={{ fontSize: '20px', fontWeight: '800', color: '#0f172a', margin: 0, letterSpacing: '-0.01em' }}>
            Import Batches
          </h1>
          <p style={{ margin: '4px 0 0', fontSize: '13px', color: '#64748b' }}>
            View, validate and manage all uploaded candidate lists.
          </p>
        </div>
        <button
          onClick={() => setIsUploadOpen(true)}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '7px',
            backgroundColor: '#2563eb',
            color: '#ffffff',
            border: '1px solid #2563eb',
            borderRadius: '8px',
            padding: '9px 16px',
            fontSize: '13px',
            fontWeight: '600',
            cursor: 'pointer',
            boxShadow: '0 1px 2px rgba(37,99,235,0.3)',
          }}
        >
          <Upload size={15} /> Upload New File
        </button>
      </div>

      {/* Table card */}
      <div style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', overflow: 'hidden', boxShadow: '0 1px 2px rgba(15,23,42,0.04)' }}>
        {/* Card header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px 20px', borderBottom: '1px solid #f1f5f9' }}>
          <h2 style={{ margin: 0, fontSize: '15px', fontWeight: '700', color: '#0f172a' }}>Uploaded Batches</h2>
          <div style={{ position: 'relative' }}>
            <Search size={15} color="#94a3b8" style={{ position: 'absolute', left: '11px', top: '9px' }} />
            <input
              type="text"
              placeholder="Search by file name, department or year..."
              value={searchQuery}
              onChange={(e) => { setSearchQuery(e.target.value); setCurrentPage(1); }}
              style={{
                width: '300px',
                padding: '8px 12px 8px 34px',
                fontSize: '12.5px',
                border: '1px solid #e2e8f0',
                borderRadius: '8px',
                outline: 'none',
                color: '#0f172a',
                backgroundColor: '#ffffff',
              }}
            />
          </div>
        </div>

        {loading ? (
          <div style={{ padding: '48px', textAlign: 'center', color: '#64748b', fontSize: '13px' }}>
            Loading import batches...
          </div>
        ) : filtered.length === 0 ? (
          <div style={{ padding: '48px', textAlign: 'center', color: '#64748b', fontSize: '13px' }}>
            {safeBatches.length === 0
              ? 'No import batches recorded yet. Upload a government allotment Excel file to begin.'
              : 'No batches match your search.'}
          </div>
        ) : (
          <>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                <thead>
                  <tr style={{ backgroundColor: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
                    <th style={{ textAlign: 'left', padding: '10px 12px 10px 20px', fontSize: '11.5px', fontWeight: '600', color: '#475569', width: '36px' }}>#</th>
                    <th style={{ textAlign: 'left', padding: '10px 12px', fontSize: '11.5px', fontWeight: '600', color: '#475569' }}>Batch / Source File</th>
                    <th style={{ textAlign: 'left', padding: '10px 12px', fontSize: '11.5px', fontWeight: '600', color: '#475569' }}>Department & Session</th>
                    <th style={{ textAlign: 'left', padding: '10px 12px', fontSize: '11.5px', fontWeight: '600', color: '#475569' }}>Row Statistics</th>
                    <th style={{ textAlign: 'left', padding: '10px 12px', fontSize: '11.5px', fontWeight: '600', color: '#475569' }}>Status</th>
                    <th style={{ textAlign: 'left', padding: '10px 12px', fontSize: '11.5px', fontWeight: '600', color: '#475569' }}>Uploaded At</th>
                    <th style={{ textAlign: 'right', padding: '10px 20px 10px 12px', fontSize: '11.5px', fontWeight: '600', color: '#475569' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {paged.map((b, idx) => {
                    const n = (safePage - 1) * pageSize + idx + 1;
                    const { date, time } = formatUploadedAt(b.uploaded_at);
                    return (
                      <tr key={b.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                        <td style={{ padding: '14px 12px 14px 20px', color: '#64748b', fontSize: '12.5px' }}>{n}</td>
                        <td style={{ padding: '14px 12px' }}>
                          <div style={{ fontWeight: '600', color: '#0f172a', fontSize: '12.5px', lineHeight: 1.4 }}>{b.source_file_name}</div>
                          <div style={{ fontSize: '11px', color: '#94a3b8', fontFamily: 'monospace', marginTop: '2px' }}>
                            SHA: {(b.source_file_hash || '').substring(0, 16)}...
                          </div>
                        </td>
                        <td style={{ padding: '14px 12px' }}>
                          <div style={{ fontWeight: '500', color: '#0f172a', fontSize: '12.5px' }}>{b.department_name || 'All Departments'}</div>
                          <div style={{ fontSize: '12px', color: '#64748b', marginTop: '2px' }}>{b.academic_year_name || 'All Academic Years'}</div>
                        </td>
                        <td style={{ padding: '14px 12px', fontSize: '12.5px', color: '#334155' }}>
                          <div>Total: <strong style={{ color: '#0f172a' }}>{b.total_rows ?? '—'}</strong></div>
                          <div style={{ marginTop: '2px' }}>Imported: <strong style={{ color: '#0d9488' }}>{b.processed_rows ?? 0}</strong>
                            {(b.error_rows || 0) > 0 && (
                              <span style={{ color: '#dc2626' }}> · Errors: <strong>{b.error_rows}</strong></span>
                            )}
                          </div>
                        </td>
                        <td style={{ padding: '14px 12px' }}>{getStatusBadge(b.status)}</td>
                        <td style={{ padding: '14px 12px', fontSize: '12px', color: '#475569', lineHeight: 1.5 }}>
                          <div>{date},</div>
                          <div>{time}</div>
                        </td>
                        <td style={{ padding: '14px 20px 14px 12px', textAlign: 'right' }}>
                          <div style={{ display: 'inline-flex', gap: '8px' }}>
                            <button
                              onClick={() => setActiveBatchId(b.id)}
                              style={{ ...btnBase, backgroundColor: '#ffffff', color: '#334155', borderColor: '#e2e8f0' }}
                            >
                              <Eye size={13} /> View Rows
                            </button>
                            {b.status === 'UPLOADED' ? (
                              <button
                                onClick={() => handleValidate(b.id)}
                                style={{ ...btnBase, backgroundColor: '#2563eb', color: '#ffffff', borderColor: '#2563eb' }}
                              >
                                <CheckCircle2 size={13} /> Validate
                              </button>
                            ) : (b.status === 'VALIDATED' || b.status === 'PARTIALLY_COMPLETED') ? (
                              <button
                                onClick={() => setExecutingBatch(b)}
                                style={{ ...btnBase, backgroundColor: '#2563eb', color: '#ffffff', borderColor: '#2563eb' }}
                              >
                                <Play size={13} /> Import to Prod
                              </button>
                            ) : (
                              <button
                                onClick={() => handleValidate(b.id)}
                                style={{ ...btnBase, backgroundColor: '#2563eb', color: '#ffffff', borderColor: '#2563eb', opacity: 0.85 }}
                              >
                                <CheckCircle2 size={13} /> Validate
                              </button>
                            )}
                            <button
                              title={`Delete batch ${b.source_file_name}`}
                              onClick={() => setBatchToDelete(b)}
                              style={{ ...btnBase, backgroundColor: '#fef2f2', color: '#dc2626', borderColor: '#fecaca' }}
                            >
                              <Trash2 size={13} /> Delete
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            {/* Footer / pagination */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 20px', borderTop: '1px solid #f1f5f9' }}>
              <span style={{ fontSize: '12px', color: '#64748b' }}>
                Showing {from} to {to} of {filtered.length} batches
              </span>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <button
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                  disabled={safePage <= 1}
                  style={{
                    width: '28px', height: '28px', display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                    borderRadius: '6px', border: '1px solid #e2e8f0', backgroundColor: '#ffffff',
                    color: safePage <= 1 ? '#cbd5e1' : '#475569', cursor: safePage <= 1 ? 'not-allowed' : 'pointer',
                  }}
                >
                  <ChevronLeft size={14} />
                </button>
                <span style={{
                  minWidth: '28px', height: '28px', display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                  borderRadius: '6px', backgroundColor: '#2563eb', color: '#ffffff', fontSize: '12px', fontWeight: '700',
                }}>
                  {safePage}
                </span>
                <button
                  onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                  disabled={safePage >= totalPages}
                  style={{
                    width: '28px', height: '28px', display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                    borderRadius: '6px', border: '1px solid #e2e8f0', backgroundColor: '#ffffff',
                    color: safePage >= totalPages ? '#cbd5e1' : '#475569', cursor: safePage >= totalPages ? 'not-allowed' : 'pointer',
                  }}
                >
                  <ChevronRight size={14} />
                </button>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Upload Modal */}
      {isUploadOpen && (
        <div style={{ position: 'fixed', inset: 0, backgroundColor: 'rgba(15,23,42,0.45)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100, padding: '16px' }}>
          <div style={{ backgroundColor: '#ffffff', borderRadius: '12px', maxWidth: '520px', width: '100%', boxShadow: '0 20px 50px rgba(15,23,42,0.25)', overflow: 'hidden' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '18px 22px', borderBottom: '1px solid #f1f5f9' }}>
              <h3 style={{ margin: 0, fontSize: '16px', fontWeight: '700', color: '#0f172a' }}>Upload New File</h3>
              <button onClick={() => setIsUploadOpen(false)} style={{ border: 'none', background: 'none', cursor: 'pointer', color: '#64748b' }}><X size={18} /></button>
            </div>
            <form onSubmit={handleUpload}>
              <div style={{ padding: '20px 22px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
                <div>
                  <label style={{ fontSize: '12.5px', fontWeight: '600', color: '#334155', display: 'block', marginBottom: '6px' }}>Excel Spreadsheet (.xlsx, .xls) *</label>
                  <input
                    type="file"
                    accept=".xlsx,.xls"
                    onChange={(e) => setUploadFile(e.target.files[0])}
                    required
                    style={{ width: '100%', fontSize: '13px', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '9px 12px' }}
                  />
                  <small style={{ color: '#94a3b8', fontSize: '11.5px', marginTop: '6px', display: 'block' }}>
                    File is hashed via SHA-256 upon reception for idempotency and verbatim staging preservation.
                  </small>
                </div>
                <div>
                  <label style={{ fontSize: '12.5px', fontWeight: '600', color: '#334155', display: 'block', marginBottom: '6px' }}>Target Academic Year (Optional)</label>
                  <select
                    value={uploadYearId}
                    onChange={(e) => setUploadYearId(e.target.value)}
                    style={{ width: '100%', fontSize: '13px', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '9px 12px', color: '#0f172a' }}
                  >
                    <option value="">Select Academic Year...</option>
                    {academicYears.map((ay) => (
                      <option key={ay.id} value={ay.id}>{ay.label}</option>
                    ))}
                  </select>
                </div>
                <div style={{ padding: '10px 14px', backgroundColor: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: '8px', fontSize: '12.5px', color: '#1d4ed8' }}>
                  <strong>Auto-Department Mapping:</strong> Department and program are automatically detected for each student from their government choice code.
                </div>
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', padding: '16px 22px', borderTop: '1px solid #f1f5f9' }}>
                <button type="button" onClick={() => setIsUploadOpen(false)} style={{ ...btnBase, backgroundColor: '#ffffff', color: '#475569', borderColor: '#e2e8f0', padding: '8px 16px' }}>
                  Cancel
                </button>
                <button type="submit" disabled={uploading} style={{ ...btnBase, backgroundColor: '#2563eb', color: '#ffffff', borderColor: '#2563eb', padding: '8px 16px' }}>
                  {uploading ? 'Uploading...' : 'Upload & Stage'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Production Import Modal */}
      {executingBatch && (
        <div style={{ position: 'fixed', inset: 0, backgroundColor: 'rgba(15,23,42,0.45)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100, padding: '16px' }}>
          <div style={{ backgroundColor: '#ffffff', borderRadius: '12px', maxWidth: '580px', width: '100%', boxShadow: '0 20px 50px rgba(15,23,42,0.25)', overflow: 'hidden' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '18px 22px', borderBottom: '1px solid #f1f5f9' }}>
              <h3 style={{ margin: 0, fontSize: '16px', fontWeight: '700', color: '#0f172a' }}>Execute Production Student Import</h3>
              <button onClick={() => setExecutingBatch(null)} style={{ border: 'none', background: 'none', cursor: 'pointer', color: '#64748b' }}><X size={18} /></button>
            </div>
            <form onSubmit={handleExecute}>
              <div style={{ padding: '20px 22px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
                <p style={{ margin: 0, fontSize: '13px', color: '#64748b' }}>
                  This will idempotently migrate validated staging rows into canonical <strong>Students</strong>, create initial enrollments, and automatically provision user accounts per ADR-009.
                </p>
                <div style={{ padding: '10px 14px', backgroundColor: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: '8px', fontSize: '12.5px', color: '#1d4ed8', lineHeight: 1.6 }}>
                  <strong>No branch selection needed:</strong> each Excel row's choice code auto-maps to its department (one dept holds many codes, e.g. CSE: 0603624211T + 603624210 = same dept, T = TFWS seat type). Mixed-branch files are fully supported.
                  {(departments || []).filter((d) => (d.choice_codes || []).length).map((d) => (
                    <div key={d.id} style={{ marginTop: '4px' }}>
                      <strong>{d.code}</strong>: {(d.choice_codes || []).join(', ')}
                    </div>
                  ))}
                </div>
                {[
                  { label: 'Semester (optional fallback)', value: execSemesterId, set: setExecSemesterId, opts: semesters.map((s) => ({ id: s.id, label: s.label || `Semester ${s.number}` })), ph: 'Auto (first semester)...' },
                  { label: 'Curriculum Scheme (optional fallback)', value: execSchemeId, set: setExecSchemeId, opts: schemes.map((sc) => ({ id: sc.id, label: `${sc.name} (${sc.code})` })), ph: 'Auto (per-program default)...' },
                  { label: 'Batch Cohort (optional fallback)', value: execBatchCohortId, set: setExecBatchCohortId, opts: batchCohorts.map((bc) => ({ id: bc.id, label: bc.name })), ph: 'Auto (per-dept + year)...' },
                ].map((f) => (
                  <div key={f.label}>
                    <label style={{ fontSize: '12.5px', fontWeight: '600', color: '#334155', display: 'block', marginBottom: '6px' }}>{f.label}</label>
                    <select value={f.value} onChange={(e) => f.set(e.target.value)} style={{ width: '100%', fontSize: '13px', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '9px 12px', color: '#0f172a' }}>
                      <option value="">{f.ph}</option>
                      {f.opts.map((o) => (
                        <option key={o.id} value={o.id}>{o.label}</option>
                      ))}
                    </select>
                  </div>
                ))}
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', padding: '16px 22px', borderTop: '1px solid #f1f5f9' }}>
                <button type="button" onClick={() => setExecutingBatch(null)} style={{ ...btnBase, backgroundColor: '#ffffff', color: '#475569', borderColor: '#e2e8f0', padding: '8px 16px' }}>
                  Cancel
                </button>
                <button type="submit" disabled={executing} style={{ ...btnBase, backgroundColor: '#2563eb', color: '#ffffff', borderColor: '#2563eb', padding: '8px 16px' }}>
                  {executing ? 'Importing & Provisioning...' : 'Migrate to Production'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal — matches reference */}
      {batchToDelete && (
        <div style={{ position: 'fixed', inset: 0, backgroundColor: 'rgba(15,23,42,0.35)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100, padding: '16px' }}>
          <div style={{ backgroundColor: '#ffffff', borderRadius: '12px', maxWidth: '440px', width: '100%', boxShadow: '0 20px 50px rgba(15,23,42,0.25)', padding: '22px' }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
              <div style={{ width: '36px', height: '36px', borderRadius: '50%', backgroundColor: '#fef2f2', border: '1px solid #fecaca', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                <Trash2 size={16} color="#dc2626" />
              </div>
              <div style={{ flex: 1 }}>
                <h3 style={{ margin: 0, fontSize: '15px', fontWeight: '700', color: '#0f172a' }}>Delete Import Batch?</h3>
              </div>
              <button onClick={() => setBatchToDelete(null)} style={{ border: 'none', background: 'none', cursor: 'pointer', color: '#94a3b8', padding: 0 }}><X size={16} /></button>
            </div>
            <p style={{ margin: '12px 0 0', fontSize: '13px', color: '#0f172a' }}>
              Delete <strong>{batchToDelete.source_file_name}</strong>?
            </p>
            <p style={{ margin: '8px 0 0', fontSize: '12.5px', color: '#64748b', lineHeight: 1.6 }}>
              This removes the batch and its staging rows. Students already imported to production are preserved. This action is recorded in the internal audit log with your username and timestamp.
            </p>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '20px' }}>
              <button
                type="button"
                onClick={() => setBatchToDelete(null)}
                disabled={deleting}
                style={{ ...btnBase, backgroundColor: '#ffffff', color: '#334155', borderColor: '#e2e8f0', padding: '8px 18px' }}
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleDelete}
                disabled={deleting}
                style={{ ...btnBase, backgroundColor: '#dc2626', color: '#ffffff', borderColor: '#dc2626', padding: '8px 18px' }}
              >
                {deleting ? 'Deleting...' : 'Delete Batch'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
