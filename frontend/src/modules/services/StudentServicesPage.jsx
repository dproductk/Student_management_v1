import React, { useState, useEffect, useMemo } from 'react';
import {
  FileText,
  Clock,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Search,
  Filter,
  Plus,
  RefreshCw,
  Send,
  User,
  Paperclip,
  ShieldCheck,
  History,
  Eye,
  ArrowRight,
  Inbox,
  Sparkles,
  ChevronRight,
  Check,
  X,
  FileCheck,
  AlertCircle
} from 'lucide-react';
import api from '../../services/api';

export const StudentServicesPage = () => {
  const [activeTab, setActiveTab] = useState('requests'); // 'requests' | 'queue' | 'types' | 'audit'
  const [requests, setRequests] = useState([]);
  const [serviceTypes, setServiceTypes] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');

  // Modals
  const [showSubmitModal, setShowSubmitModal] = useState(false);
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [showAttachModal, setShowAttachModal] = useState(false);
  const [selectedRequest, setSelectedRequest] = useState(null);

  // Form states
  const [submitForm, setSubmitForm] = useState({
    service_type_id: '',
    student_id: '',
    description: '',
    document_id: ''
  });

  const [rejectReason, setRejectReason] = useState('');
  const [attachDocumentId, setAttachDocumentId] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  // Fetch data
  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [typesRes, requestsRes, auditRes] = await Promise.all([
        api.get('/services/types/'),
        api.get('/services/requests/'),
        api.get('/services/audits/')
      ]);
      setServiceTypes(typesRes.data.results || typesRes.data || []);
      setRequests(requestsRes.data.results || requestsRes.data || []);
      setAuditLogs(auditRes.data.results || auditRes.data || []);
    } catch (err) {
      console.error('Failed to load services data:', err);
      setError('Failed to fetch services data. Check connection.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Filtered requests
  const filteredRequests = useMemo(() => {
    return requests.filter((r) => {
      const matchesSearch =
        r.ticket_number?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        r.student_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        r.student_enrollment_no?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        r.service_type_name?.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesStatus = statusFilter === 'ALL' || r.status === statusFilter;
      return matchesSearch && matchesStatus;
    });
  }, [requests, searchQuery, statusFilter]);

  // Statistics
  const stats = useMemo(() => {
    const total = requests.length;
    const submitted = requests.filter((r) => r.status === 'SUBMITTED').length;
    const inProgress = requests.filter((r) => r.status === 'IN_PROGRESS').length;
    const approved = requests.filter((r) => r.status === 'APPROVED').length;
    const completed = requests.filter((r) => r.status === 'COMPLETED').length;
    const rejected = requests.filter((r) => r.status === 'REJECTED').length;

    return { total, submitted, inProgress, approved, completed, rejected };
  }, [requests]);

  // Workflow action handlers
  const handleProcess = async (reqId) => {
    setActionLoading(true);
    try {
      await api.post(`/services/requests/${reqId}/process/`);
      await fetchData();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to start processing request.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleApprove = async (reqId) => {
    setActionLoading(true);
    try {
      await api.post(`/services/requests/${reqId}/approve/`);
      await fetchData();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to approve request.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleRejectSubmit = async (e) => {
    e.preventDefault();
    if (!rejectReason.trim()) {
      alert('A rejection reason is mandatory.');
      return;
    }
    setActionLoading(true);
    try {
      await api.post(`/services/requests/${selectedRequest.id}/reject/`, {
        reason: rejectReason
      });
      setShowRejectModal(false);
      setSelectedRequest(null);
      setRejectReason('');
      await fetchData();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to reject request.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleComplete = async (reqId) => {
    setActionLoading(true);
    try {
      await api.post(`/services/requests/${reqId}/complete/`);
      await fetchData();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to complete request.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleAttachSubmit = async (e) => {
    e.preventDefault();
    if (!attachDocumentId) {
      alert('Document ID is required.');
      return;
    }
    setActionLoading(true);
    try {
      await api.post(`/services/requests/${selectedRequest.id}/attach_document/`, {
        document_id: attachDocumentId
      });
      setShowAttachModal(false);
      setSelectedRequest(null);
      setAttachDocumentId('');
      await fetchData();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to attach document.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleSubmitNewRequest = async (e) => {
    e.preventDefault();
    if (!submitForm.service_type_id) {
      alert('Please select a service type.');
      return;
    }
    setActionLoading(true);
    try {
      await api.post('/services/requests/submit/', {
        service_type_id: submitForm.service_type_id,
        student_id: submitForm.student_id || undefined,
        description: submitForm.description,
        document_id: submitForm.document_id || undefined
      });
      setShowSubmitModal(false);
      setSubmitForm({
        service_type_id: '',
        student_id: '',
        description: '',
        document_id: ''
      });
      await fetchData();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to submit service request.');
    } finally {
      setActionLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    const map = {
      SUBMITTED: { bg: 'rgba(59, 130, 246, 0.15)', text: '#60a5fa', border: '#2563eb', label: 'Submitted' },
      IN_PROGRESS: { bg: 'rgba(245, 158, 11, 0.15)', text: '#fbbf24', border: '#d97706', label: 'In Progress' },
      APPROVED: { bg: 'rgba(16, 185, 129, 0.15)', text: '#34d399', border: '#059669', label: 'Approved' },
      REJECTED: { bg: 'rgba(239, 68, 68, 0.15)', text: '#f87171', border: '#dc2626', label: 'Rejected' },
      COMPLETED: { bg: 'rgba(139, 92, 246, 0.15)', text: '#a78bfa', border: '#7c3aed', label: 'Completed' },
      CANCELLED: { bg: 'rgba(107, 114, 128, 0.15)', text: '#9ca3af', border: '#4b5563', label: 'Cancelled' }
    };
    const s = map[status] || map.SUBMITTED;
    return (
      <span
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '0.35rem',
          padding: '0.2rem 0.6rem',
          borderRadius: '9999px',
          fontSize: '0.75rem',
          fontWeight: '600',
          backgroundColor: s.bg,
          color: s.text,
          border: `1px solid ${s.border}`
        }}
      >
        <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: s.text }} />
        {s.label}
      </span>
    );
  };

  const selectedServiceType = useMemo(() => {
    return serviceTypes.find((st) => String(st.id) === String(submitForm.service_type_id));
  }, [serviceTypes, submitForm.service_type_id]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem'
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
            <Sparkles size={22} color="var(--primary-400)" />
            <h1 style={{ fontSize: '1.75rem', fontWeight: '700', color: 'var(--text-primary)', margin: 0 }}>
              Student Services & Requests
            </h1>
          </div>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', margin: 0 }}>
            Unified student request lifecycle: document issuance, verifications, concessions & approval workflows
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button
            onClick={fetchData}
            disabled={loading}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.55rem 0.95rem',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-subtle)',
              backgroundColor: 'var(--bg-surface)',
              color: 'var(--text-secondary)',
              cursor: loading ? 'not-allowed' : 'pointer',
              fontSize: '0.85rem'
            }}
          >
            <RefreshCw size={15} className={loading ? 'animate-spin' : ''} />
            Refresh
          </button>
          <button
            onClick={() => setShowSubmitModal(true)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.55rem 1.1rem',
              borderRadius: 'var(--radius-md)',
              border: 'none',
              backgroundColor: 'var(--primary-600)',
              color: '#ffffff',
              cursor: 'pointer',
              fontWeight: '600',
              fontSize: '0.875rem'
            }}
          >
            <Plus size={16} />
            Submit Service Request
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: '1rem'
        }}
      >
        <div
          style={{
            backgroundColor: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-lg)',
            padding: '1.25rem'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: '500' }}>Total Requests</span>
            <Inbox size={18} color="var(--primary-400)" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: '700', color: 'var(--text-primary)', marginTop: '0.5rem' }}>
            {stats.total}
          </div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>All time submissions</span>
        </div>

        <div
          style={{
            backgroundColor: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-lg)',
            padding: '1.25rem'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: '500' }}>In Queue / Processing</span>
            <Clock size={18} color="#fbbf24" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: '700', color: '#fbbf24', marginTop: '0.5rem' }}>
            {stats.submitted + stats.inProgress}
          </div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            {stats.submitted} pending, {stats.inProgress} processing
          </span>
        </div>

        <div
          style={{
            backgroundColor: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-lg)',
            padding: '1.25rem'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: '500' }}>Approved & Ready</span>
            <CheckCircle2 size={18} color="#34d399" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: '700', color: '#34d399', marginTop: '0.5rem' }}>
            {stats.approved}
          </div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Awaiting completion / pickup</span>
        </div>

        <div
          style={{
            backgroundColor: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-lg)',
            padding: '1.25rem'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: '500' }}>Completed Lifecycle</span>
            <FileCheck size={18} color="#a78bfa" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: '700', color: '#a78bfa', marginTop: '0.5rem' }}>
            {stats.completed}
          </div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Archived fulfilled requests</span>
        </div>

        <div
          style={{
            backgroundColor: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-lg)',
            padding: '1.25rem'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: '500' }}>Rejected</span>
            <XCircle size={18} color="#f87171" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: '700', color: '#f87171', marginTop: '0.5rem' }}>
            {stats.rejected}
          </div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>With reason recorded</span>
        </div>
      </div>

      {/* Tabs */}
      <div
        style={{
          display: 'flex',
          borderBottom: '1px solid var(--border-subtle)',
          gap: '0.5rem'
        }}
      >
        {[
          { key: 'requests', label: 'Student Requests Queue', icon: Inbox },
          { key: 'types', label: 'Service Types Catalog', icon: FileText },
          { key: 'audit', label: 'Audit Trail & Accountability', icon: History }
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '0.75rem 1.25rem',
                backgroundColor: 'transparent',
                border: 'none',
                borderBottom: isActive ? '2px solid var(--primary-500)' : '2px solid transparent',
                color: isActive ? 'var(--primary-400)' : 'var(--text-secondary)',
                fontWeight: isActive ? '600' : '500',
                cursor: 'pointer',
                fontSize: '0.9rem',
                transition: 'all var(--transition-fast)'
              }}
            >
              <Icon size={16} />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Tab 1: Requests & Processing Queue */}
      {activeTab === 'requests' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {/* Controls */}
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: '1rem'
            }}
          >
            <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flex: 1, maxWidth: '500px' }}>
              <div
                style={{
                  position: 'relative',
                  width: '100%',
                  display: 'flex',
                  alignItems: 'center'
                }}
              >
                <Search size={16} style={{ position: 'absolute', left: '0.75rem', color: 'var(--text-muted)' }} />
                <input
                  type="text"
                  placeholder="Search by ticket #, student name, enrollment, or service..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.55rem 0.75rem 0.55rem 2.25rem',
                    backgroundColor: 'var(--bg-surface)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-md)',
                    color: 'var(--text-primary)',
                    fontSize: '0.85rem'
                  }}
                />
              </div>
            </div>

            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
              <Filter size={15} color="var(--text-muted)" />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                style={{
                  padding: '0.55rem 0.85rem',
                  backgroundColor: 'var(--bg-surface)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-md)',
                  color: 'var(--text-primary)',
                  fontSize: '0.85rem'
                }}
              >
                <option value="ALL">All Statuses</option>
                <option value="SUBMITTED">Submitted</option>
                <option value="IN_PROGRESS">In Progress</option>
                <option value="APPROVED">Approved</option>
                <option value="REJECTED">Rejected</option>
                <option value="COMPLETED">Completed</option>
                <option value="CANCELLED">Cancelled</option>
              </select>
            </div>
          </div>

          {/* Table */}
          <div
            style={{
              backgroundColor: 'var(--bg-surface)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-lg)',
              overflowX: 'auto'
            }}
          >
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
              <thead>
                <tr
                  style={{
                    borderBottom: '1px solid var(--border-subtle)',
                    backgroundColor: 'rgba(255, 255, 255, 0.02)',
                    fontSize: '0.75rem',
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                    color: 'var(--text-muted)'
                  }}
                >
                  <th style={{ padding: '0.85rem 1rem' }}>Ticket / Service</th>
                  <th style={{ padding: '0.85rem 1rem' }}>Student</th>
                  <th style={{ padding: '0.85rem 1rem' }}>Status</th>
                  <th style={{ padding: '0.85rem 1rem' }}>Document</th>
                  <th style={{ padding: '0.85rem 1rem' }}>Assigned To</th>
                  <th style={{ padding: '0.85rem 1rem' }}>Submitted At</th>
                  <th style={{ padding: '0.85rem 1rem', textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredRequests.length === 0 ? (
                  <tr>
                    <td colSpan={7} style={{ padding: '3rem 1rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                      <Inbox size={32} style={{ margin: '0 auto 0.5rem', opacity: 0.5 }} />
                      <div>No service requests found matching your filter criteria.</div>
                    </td>
                  </tr>
                ) : (
                  filteredRequests.map((req) => (
                    <tr
                      key={req.id}
                      style={{
                        borderBottom: '1px solid var(--border-subtle)',
                        fontSize: '0.85rem',
                        transition: 'background-color var(--transition-fast)'
                      }}
                    >
                      <td style={{ padding: '0.85rem 1rem' }}>
                        <div style={{ fontWeight: '600', color: 'var(--text-primary)' }}>{req.ticket_number}</div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{req.service_type_name}</div>
                        {req.rejection_reason && (
                          <div
                            style={{
                              marginTop: '0.35rem',
                              fontSize: '0.75rem',
                              color: '#f87171',
                              backgroundColor: 'rgba(239, 68, 68, 0.1)',
                              padding: '0.2rem 0.4rem',
                              borderRadius: '4px',
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '0.25rem'
                            }}
                          >
                            <AlertCircle size={12} /> Reason: {req.rejection_reason}
                          </div>
                        )}
                      </td>
                      <td style={{ padding: '0.85rem 1rem' }}>
                        <div style={{ fontWeight: '500', color: 'var(--text-primary)' }}>{req.student_name}</div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                          {req.student_enrollment_no || 'Pending Enr.'}
                        </div>
                      </td>
                      <td style={{ padding: '0.85rem 1rem' }}>{getStatusBadge(req.status)}</td>
                      <td style={{ padding: '0.85rem 1rem' }}>
                        {req.attached_document_name ? (
                          <div
                            style={{
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '0.35rem',
                              padding: '0.2rem 0.5rem',
                              borderRadius: '4px',
                              backgroundColor: 'rgba(59, 130, 246, 0.1)',
                              color: '#60a5fa',
                              fontSize: '0.75rem'
                            }}
                          >
                            <Paperclip size={12} />
                            <span>{req.attached_document_type}</span>
                          </div>
                        ) : (
                          <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>None</span>
                        )}
                      </td>
                      <td style={{ padding: '0.85rem 1rem' }}>
                        {req.assigned_to_name ? (
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                            <User size={13} color="var(--text-muted)" />
                            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                              {req.assigned_to_name}
                            </span>
                          </div>
                        ) : (
                          <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>Unassigned</span>
                        )}
                      </td>
                      <td style={{ padding: '0.85rem 1rem', color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                        {req.created_at ? new Date(req.created_at).toLocaleDateString() : '-'}
                      </td>
                      <td style={{ padding: '0.85rem 1rem', textAlign: 'right' }}>
                        <div style={{ display: 'flex', gap: '0.4rem', justifyContent: 'flex-end', flexWrap: 'wrap' }}>
                          {/* Process action */}
                          {req.status === 'SUBMITTED' && (
                            <button
                              onClick={() => handleProcess(req.id)}
                              disabled={actionLoading}
                              title="Start Processing"
                              style={{
                                padding: '0.3rem 0.6rem',
                                borderRadius: '4px',
                                border: '1px solid #d97706',
                                backgroundColor: 'rgba(245, 158, 11, 0.1)',
                                color: '#fbbf24',
                                cursor: 'pointer',
                                fontSize: '0.75rem',
                                fontWeight: '600'
                              }}
                            >
                              Process
                            </button>
                          )}

                          {/* Approve action */}
                          {req.status === 'IN_PROGRESS' && (
                            <button
                              onClick={() => handleApprove(req.id)}
                              disabled={actionLoading}
                              title="Approve Request"
                              style={{
                                padding: '0.3rem 0.6rem',
                                borderRadius: '4px',
                                border: '1px solid #059669',
                                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                                color: '#34d399',
                                cursor: 'pointer',
                                fontSize: '0.75rem',
                                fontWeight: '600'
                              }}
                            >
                              Approve
                            </button>
                          )}

                          {/* Reject action */}
                          {(req.status === 'SUBMITTED' || req.status === 'IN_PROGRESS') && (
                            <button
                              onClick={() => {
                                setSelectedRequest(req);
                                setRejectReason('');
                                setShowRejectModal(true);
                              }}
                              disabled={actionLoading}
                              title="Reject Request"
                              style={{
                                padding: '0.3rem 0.6rem',
                                borderRadius: '4px',
                                border: '1px solid #dc2626',
                                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                                color: '#f87171',
                                cursor: 'pointer',
                                fontSize: '0.75rem',
                                fontWeight: '600'
                              }}
                            >
                              Reject
                            </button>
                          )}

                          {/* Complete action */}
                          {req.status === 'APPROVED' && (
                            <button
                              onClick={() => handleComplete(req.id)}
                              disabled={actionLoading}
                              title="Mark Completed"
                              style={{
                                padding: '0.3rem 0.6rem',
                                borderRadius: '4px',
                                border: '1px solid #7c3aed',
                                backgroundColor: 'rgba(139, 92, 246, 0.1)',
                                color: '#a78bfa',
                                cursor: 'pointer',
                                fontSize: '0.75rem',
                                fontWeight: '600'
                              }}
                            >
                              Complete
                            </button>
                          )}

                          {/* Attach document action */}
                          {!req.attached_document && ['SUBMITTED', 'IN_PROGRESS'].includes(req.status) && (
                            <button
                              onClick={() => {
                                setSelectedRequest(req);
                                setAttachDocumentId('');
                                setShowAttachModal(true);
                              }}
                              title="Attach Document"
                              style={{
                                padding: '0.3rem 0.5rem',
                                borderRadius: '4px',
                                border: '1px solid var(--border-subtle)',
                                backgroundColor: 'var(--bg-surface)',
                                color: 'var(--text-secondary)',
                                cursor: 'pointer',
                                fontSize: '0.75rem'
                              }}
                            >
                              <Paperclip size={12} />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 2: Service Types Catalog */}
      {activeTab === 'types' && (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
            gap: '1.25rem'
          }}
        >
          {serviceTypes.map((type) => (
            <div
              key={type.id}
              style={{
                backgroundColor: 'var(--bg-surface)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-lg)',
                padding: '1.25rem',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                gap: '1rem'
              }}
            >
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: '600', color: 'var(--text-primary)' }}>
                    {type.name}
                  </h3>
                  <span
                    style={{
                      padding: '0.15rem 0.5rem',
                      borderRadius: '4px',
                      fontSize: '0.7rem',
                      fontWeight: '600',
                      backgroundColor: type.is_active ? 'rgba(16, 185, 129, 0.15)' : 'rgba(107, 114, 128, 0.15)',
                      color: type.is_active ? '#34d399' : '#9ca3af'
                    }}
                  >
                    {type.is_active ? 'ACTIVE' : 'INACTIVE'}
                  </span>
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                  Code: <span style={{ fontFamily: 'monospace' }}>{type.code}</span> | Category: {type.category}
                </div>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.75rem' }}>
                  {type.description || 'General administrative service request for university records.'}
                </p>
              </div>

              <div
                style={{
                  borderTop: '1px solid var(--border-subtle)',
                  paddingTop: '0.75rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.4rem',
                  fontSize: '0.8rem'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Target SLA:</span>
                  <span style={{ fontWeight: '500', color: 'var(--text-primary)' }}>{type.sla_days} business days</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Processing Fee:</span>
                  <span style={{ fontWeight: '500', color: 'var(--text-primary)' }}>
                    {Number(type.fee_amount) > 0 ? `₹${Number(type.fee_amount).toLocaleString()}` : 'Free'}
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Requires Document:</span>
                  <span
                    style={{
                      fontWeight: '600',
                      color: type.requires_document ? '#fbbf24' : 'var(--text-secondary)'
                    }}
                  >
                    {type.requires_document ? 'Yes (Mandatory)' : 'No'}
                  </span>
                </div>
                {type.requires_document && type.allowed_document_types?.length > 0 && (
                  <div style={{ marginTop: '0.25rem' }}>
                    <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>Accepted Documents:</span>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.25rem', marginTop: '0.25rem' }}>
                      {type.allowed_document_types.map((docType) => (
                        <span
                          key={docType}
                          style={{
                            fontSize: '0.7rem',
                            backgroundColor: 'rgba(59, 130, 246, 0.15)',
                            color: '#60a5fa',
                            padding: '0.1rem 0.4rem',
                            borderRadius: '3px'
                          }}
                        >
                          {docType}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Tab 3: Audit Trail & Accountability */}
      {activeTab === 'audit' && (
        <div
          style={{
            backgroundColor: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-lg)',
            padding: '1.25rem'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
            <ShieldCheck size={18} color="var(--primary-400)" />
            <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: '600', color: 'var(--text-primary)' }}>
              Service Request Immutable Audit Trail
            </h3>
          </div>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '1.5rem' }}>
            Permanent record of every state transition, actor identity, timestamp, and rejection reason for regulatory compliance.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {auditLogs.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                No audit events recorded yet.
              </div>
            ) : (
              auditLogs.map((log) => (
                <div
                  key={log.id}
                  style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '1rem',
                    padding: '0.85rem',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-md)',
                    backgroundColor: 'rgba(255, 255, 255, 0.01)'
                  }}
                >
                  <div
                    style={{
                      width: '32px',
                      height: '32px',
                      borderRadius: '50%',
                      backgroundColor: 'rgba(59, 130, 246, 0.1)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexShrink: 0
                    }}
                  >
                    <History size={16} color="#60a5fa" />
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontWeight: '600', color: 'var(--text-primary)', fontSize: '0.85rem' }}>
                        {log.action} — Ticket #{log.service_request}
                      </span>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        {new Date(log.created_at).toLocaleString()}
                      </span>
                    </div>
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem',
                        marginTop: '0.35rem',
                        fontSize: '0.8rem'
                      }}
                    >
                      <span style={{ color: 'var(--text-muted)' }}>
                        Transition:{' '}
                        <span style={{ fontFamily: 'monospace', color: 'var(--text-secondary)' }}>
                          {log.old_status || 'INITIAL'}
                        </span>{' '}
                        &rarr;{' '}
                        <span style={{ fontFamily: 'monospace', color: 'var(--primary-400)' }}>
                          {log.new_status}
                        </span>
                      </span>
                      <span style={{ color: 'var(--text-muted)' }}>•</span>
                      <span style={{ color: 'var(--text-muted)' }}>
                        Actor:{' '}
                        <strong style={{ color: 'var(--text-primary)' }}>{log.actor_name || 'System'}</strong>
                      </span>
                    </div>
                    {log.notes && (
                      <div
                        style={{
                          marginTop: '0.35rem',
                          fontSize: '0.75rem',
                          color: 'var(--text-secondary)',
                          backgroundColor: 'rgba(255, 255, 255, 0.03)',
                          padding: '0.3rem 0.6rem',
                          borderRadius: '4px'
                        }}
                      >
                        Notes: {log.notes}
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* MODAL: Submit Request */}
      {showSubmitModal && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.75)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '1rem'
          }}
        >
          <div
            style={{
              backgroundColor: 'var(--bg-surface)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-lg)',
              maxWidth: '520px',
              width: '100%',
              padding: '1.5rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '1.25rem'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Send size={18} color="var(--primary-400)" />
                <h3 style={{ margin: 0, fontSize: '1.2rem', fontWeight: '600', color: 'var(--text-primary)' }}>
                  Submit Service Request
                </h3>
              </div>
              <button
                onClick={() => setShowSubmitModal(false)}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--text-muted)',
                  cursor: 'pointer',
                  padding: '0.2rem'
                }}
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleSubmitNewRequest} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: '500', color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>
                  Service Type *
                </label>
                <select
                  value={submitForm.service_type_id}
                  onChange={(e) => setSubmitForm({ ...submitForm, service_type_id: e.target.value })}
                  required
                  style={{
                    width: '100%',
                    padding: '0.6rem 0.75rem',
                    backgroundColor: 'var(--bg-main)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-md)',
                    color: 'var(--text-primary)',
                    fontSize: '0.85rem'
                  }}
                >
                  <option value="">Select a service type...</option>
                  {serviceTypes
                    .filter((st) => st.is_active)
                    .map((st) => (
                      <option key={st.id} value={st.id}>
                        {st.name} ({st.code}) — {st.sla_days}d SLA
                      </option>
                    ))}
                </select>
              </div>

              {selectedServiceType?.requires_document && (
                <div
                  style={{
                    backgroundColor: 'rgba(245, 158, 11, 0.1)',
                    border: '1px solid #d97706',
                    borderRadius: 'var(--radius-md)',
                    padding: '0.75rem',
                    fontSize: '0.8rem',
                    color: '#fbbf24',
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '0.5rem'
                  }}
                >
                  <AlertTriangle size={16} style={{ flexShrink: 0, marginTop: '0.1rem' }} />
                  <div>
                    <strong>Mandatory Document Required:</strong> This service requires an attached student document of type:{' '}
                    {selectedServiceType.allowed_document_types?.join(', ') || 'Any document'}.
                  </div>
                </div>
              )}

              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: '500', color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>
                  Attached Document ID {selectedServiceType?.requires_document && '*'}
                </label>
                <input
                  type="text"
                  placeholder="e.g. Document UUID from Student Documents store"
                  value={submitForm.document_id}
                  onChange={(e) => setSubmitForm({ ...submitForm, document_id: e.target.value })}
                  required={selectedServiceType?.requires_document}
                  style={{
                    width: '100%',
                    padding: '0.6rem 0.75rem',
                    backgroundColor: 'var(--bg-main)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-md)',
                    color: 'var(--text-primary)',
                    fontSize: '0.85rem'
                  }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: '500', color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>
                  Description / Specific Requirements
                </label>
                <textarea
                  rows={3}
                  placeholder="Describe your request details or reason..."
                  value={submitForm.description}
                  onChange={(e) => setSubmitForm({ ...submitForm, description: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '0.6rem 0.75rem',
                    backgroundColor: 'var(--bg-main)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-md)',
                    color: 'var(--text-primary)',
                    fontSize: '0.85rem',
                    resize: 'vertical'
                  }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '0.5rem' }}>
                <button
                  type="button"
                  onClick={() => setShowSubmitModal(false)}
                  style={{
                    padding: '0.55rem 1rem',
                    backgroundColor: 'transparent',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-md)',
                    color: 'var(--text-secondary)',
                    cursor: 'pointer',
                    fontSize: '0.85rem'
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  style={{
                    padding: '0.55rem 1.25rem',
                    backgroundColor: 'var(--primary-600)',
                    border: 'none',
                    borderRadius: 'var(--radius-md)',
                    color: '#ffffff',
                    cursor: actionLoading ? 'not-allowed' : 'pointer',
                    fontWeight: '600',
                    fontSize: '0.85rem'
                  }}
                >
                  {actionLoading ? 'Submitting...' : 'Submit Request'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: Reject Request */}
      {showRejectModal && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.75)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '1rem'
          }}
        >
          <div
            style={{
              backgroundColor: 'var(--bg-surface)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-lg)',
              maxWidth: '480px',
              width: '100%',
              padding: '1.5rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '1.25rem'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#f87171' }}>
                <XCircle size={20} />
                <h3 style={{ margin: 0, fontSize: '1.2rem', fontWeight: '600', color: 'var(--text-primary)' }}>
                  Reject Service Request
                </h3>
              </div>
              <button
                onClick={() => setShowRejectModal(false)}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--text-muted)',
                  cursor: 'pointer',
                  padding: '0.2rem'
                }}
              >
                <X size={18} />
              </button>
            </div>

            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              Rejecting Ticket <strong>{selectedRequest?.ticket_number}</strong> for student{' '}
              <strong>{selectedRequest?.student_name}</strong>.
            </div>

            <form onSubmit={handleRejectSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: '500', color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>
                  Rejection Reason * (Mandatory by Governance Policy)
                </label>
                <textarea
                  rows={4}
                  required
                  placeholder="State the explicit justification (e.g., Incomplete documentation, ineligible category, duplicate request)..."
                  value={rejectReason}
                  onChange={(e) => setRejectReason(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.6rem 0.75rem',
                    backgroundColor: 'var(--bg-main)',
                    border: '1px solid #dc2626',
                    borderRadius: 'var(--radius-md)',
                    color: 'var(--text-primary)',
                    fontSize: '0.85rem',
                    resize: 'vertical'
                  }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
                <button
                  type="button"
                  onClick={() => setShowRejectModal(false)}
                  style={{
                    padding: '0.55rem 1rem',
                    backgroundColor: 'transparent',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-md)',
                    color: 'var(--text-secondary)',
                    cursor: 'pointer',
                    fontSize: '0.85rem'
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  style={{
                    padding: '0.55rem 1.25rem',
                    backgroundColor: '#dc2626',
                    border: 'none',
                    borderRadius: 'var(--radius-md)',
                    color: '#ffffff',
                    cursor: actionLoading ? 'not-allowed' : 'pointer',
                    fontWeight: '600',
                    fontSize: '0.85rem'
                  }}
                >
                  {actionLoading ? 'Rejecting...' : 'Confirm Rejection'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: Attach Document */}
      {showAttachModal && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.75)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '1rem'
          }}
        >
          <div
            style={{
              backgroundColor: 'var(--bg-surface)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-lg)',
              maxWidth: '460px',
              width: '100%',
              padding: '1.5rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '1.25rem'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Paperclip size={18} color="var(--primary-400)" />
                <h3 style={{ margin: 0, fontSize: '1.2rem', fontWeight: '600', color: 'var(--text-primary)' }}>
                  Attach Canonical Document
                </h3>
              </div>
              <button
                onClick={() => setShowAttachModal(false)}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--text-muted)',
                  cursor: 'pointer',
                  padding: '0.2rem'
                }}
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleAttachSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: '500', color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>
                  Student Document UUID *
                </label>
                <input
                  type="text"
                  required
                  placeholder="Enter StudentDocument UUID"
                  value={attachDocumentId}
                  onChange={(e) => setAttachDocumentId(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.6rem 0.75rem',
                    backgroundColor: 'var(--bg-main)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-md)',
                    color: 'var(--text-primary)',
                    fontSize: '0.85rem'
                  }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
                <button
                  type="button"
                  onClick={() => setShowAttachModal(false)}
                  style={{
                    padding: '0.55rem 1rem',
                    backgroundColor: 'transparent',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-md)',
                    color: 'var(--text-secondary)',
                    cursor: 'pointer',
                    fontSize: '0.85rem'
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  style={{
                    padding: '0.55rem 1.25rem',
                    backgroundColor: 'var(--primary-600)',
                    border: 'none',
                    borderRadius: 'var(--radius-md)',
                    color: '#ffffff',
                    cursor: actionLoading ? 'not-allowed' : 'pointer',
                    fontWeight: '600',
                    fontSize: '0.85rem'
                  }}
                >
                  {actionLoading ? 'Attaching...' : 'Attach Document'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
