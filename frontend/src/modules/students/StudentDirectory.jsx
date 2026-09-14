import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import {
  Search,
  Plus,
  Users,
  ChevronRight,
  ChevronLeft,
  KeyRound,
  RotateCcw,
} from 'lucide-react';

const DIVISION_OPTIONS = ['A', 'B', 'C', 'D', 'E'];

export const StudentDirectory = () => {
  const { hasRole, user } = useAuth();
  const canProvisionLogins =
    hasRole('SYSTEM_ADMIN') || hasRole('COLLEGE_ADMIN') || user?.is_superuser;

  const [students, setStudents] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [search, setSearch] = useState('');
  const [deptFilter, setDeptFilter] = useState('');
  const [divisionFilter, setDivisionFilter] = useState('');
  const [genderFilter, setGenderFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [loginFilter, setLoginFilter] = useState('');

  // Pagination (server-side — no long list)
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const [provisioning, setProvisioning] = useState(false);
  const [provisionOneId, setProvisionOneId] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [studentForm, setStudentForm] = useState({
    candidate_name: '',
    gender: 'MALE',
    date_of_birth: '',
    enrollment_no: '',
    application_id: '',
    email: '',
    student_mobile: '',
    aadhaar_number: '',
  });
  const [error, setError] = useState('');

  const fetchStudents = async (opts = {}) => {
    try {
      setLoading(true);
      const p = opts.page ?? page;
      const ps = opts.pageSize ?? pageSize;
      const params = new URLSearchParams();
      if (search.trim()) params.set('search', search.trim());
      if (statusFilter) params.set('status', statusFilter);
      if (deptFilter) params.set('department', deptFilter);
      if (divisionFilter) params.set('division', divisionFilter);
      if (genderFilter) params.set('gender', genderFilter);
      if (loginFilter) params.set('has_login', loginFilter);
      params.set('limit', String(ps));
      params.set('offset', String((p - 1) * ps));

      const res = await api.get(`/students/?${params.toString()}`);
      const data = res.data;
      if (Array.isArray(data)) {
        setStudents(data);
        setTotalCount(data.length);
      } else {
        setStudents(data.results || []);
        setTotalCount(data.count ?? (data.results || []).length);
      }
    } catch (err) {
      console.error('Failed to load students', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchDepartments = async () => {
    try {
      const res = await api.get('/academic/departments/?limit=200');
      const d = res.data;
      setDepartments(Array.isArray(d) ? d : d.results || []);
    } catch (err) {
      console.error('Failed to load departments', err);
    }
  };

  useEffect(() => {
    fetchDepartments();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Debounced search; immediate for other filters/page
  useEffect(() => {
    const timer = setTimeout(() => {
      fetchStudents();
    }, 300);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search, statusFilter, deptFilter, divisionFilter, genderFilter, loginFilter, page, pageSize]);

  const resetFilters = () => {
    setSearch('');
    setDeptFilter('');
    setDivisionFilter('');
    setGenderFilter('');
    setStatusFilter('');
    setLoginFilter('');
    setPage(1);
  };

  const activeFilterCount = [deptFilter, divisionFilter, genderFilter, statusFilter, loginFilter].filter(Boolean).length;

  const handleCreateStudent = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await api.post('/students/', studentForm);
      setShowCreateModal(false);
      setStudentForm({
        candidate_name: '',
        gender: 'MALE',
        date_of_birth: '',
        enrollment_no: '',
        application_id: '',
        email: '',
        student_mobile: '',
        aadhaar_number: '',
      });
      setPage(1);
      fetchStudents({ page: 1 });
    } catch (err) {
      setError(err.response?.data?.message || err.response?.data?.detail || 'Failed to create student.');
    }
  };

  // Default login = Enrollment No (or Application ID) as BOTH username and password.
  // Student logs in at /login, then must change password on first login.
  const provisionPayload = (s) => ({
    enrollment_number: s.enrollment_no || '',
    application_id: s.application_id || '',
    email: s.email || '',
  });

  const handleProvisionOne = async (s) => {
    if (!s.enrollment_no && !s.application_id) {
      alert('This student has no Enrollment No / Application ID, so a login cannot be created.');
      return;
    }
    const id = s.enrollment_no || s.application_id;
    if (!window.confirm(`Create login for ${s.candidate_name}?\nUsername = ${id}\nPassword = ${id} (must change on first login)`)) return;
    try {
      setProvisionOneId(s.id);
      await api.post('/auth/users/provision-student/bulk/', { students: [provisionPayload(s)] });
      alert(`Login ready.\nUsername: ${id}\nDefault password: ${id}\nStudent must change it on first login.`);
      fetchStudents();
    } catch (err) {
      alert(err.response?.data?.error || err.response?.data?.detail || 'Failed. Need SysAdmin / College Admin permission.');
    } finally {
      setProvisionOneId(null);
    }
  };

  const handleBulkCreateLogins = async () => {
    const targets = students.filter((s) => !s.has_login && (s.enrollment_no || s.application_id));
    if (targets.length === 0) {
      alert('Everyone on this page already has a login (or has no enrollment/application ID).');
      return;
    }
    if (!window.confirm(`Create logins for ${targets.length} students on this page?\nUsername = Enrollment No, default password = same value.`)) return;
    try {
      setProvisioning(true);
      const res = await api.post('/auth/users/provision-student/bulk/', {
        students: targets.map(provisionPayload),
      });
      const d = res.data || {};
      alert(`Logins: ${d.created_count || 0} created, ${d.existing_count || 0} already existed, ${d.failed_count || 0} failed.\nDefault password = Enrollment No (must change on first login).`);
      fetchStudents();
    } catch (err) {
      alert(err.response?.data?.error || err.response?.data?.detail || 'Bulk login creation failed. Need SysAdmin/College Admin permission.');
    } finally {
      setProvisioning(false);
    }
  };

  const safeDepartments = Array.isArray(departments) ? departments : [];
  const totalPages = Math.max(1, Math.ceil(totalCount / pageSize));
  const safePage = Math.min(page, totalPages);
  const from = totalCount === 0 ? 0 : (safePage - 1) * pageSize + 1;
  const to = Math.min(safePage * pageSize, totalCount);

  const pageNumbers = () => {
    const pages = [];
    const start = Math.max(1, safePage - 2);
    const end = Math.min(totalPages, start + 4);
    for (let i = start; i <= end; i++) pages.push(i);
    return pages;
  };

  const gotoPage = (p) => setPage(Math.min(Math.max(1, p), totalPages));

  const copyText = async (t) => {
    try {
      await navigator.clipboard.writeText(t);
    } catch {
      const ta = document.createElement('textarea');
      ta.value = t;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
    }
  };

  return (
    <div>
      {/* Banner */}
      <div className="edvana-banner">
        <div className="edvana-banner-breadcrumb">
          <span>Academics</span>
          <span>/</span>
          <span>Student Directory</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem' }}>
          <div>
            <h1 className="edvana-banner-title">Student Information Directory</h1>
            <p style={{ fontSize: '0.85rem', opacity: 0.9, marginTop: '0.35rem' }}>
              Search, filter, and inspect student profiles. Usernames are shown in the USERNAME / LOGIN column (click to copy).
            </p>
          </div>
          <div style={{ display: 'flex', gap: '0.6rem' }}>
            {canProvisionLogins && (
              <button
                className="edvana-btn"
                style={{ backgroundColor: 'rgba(255,255,255,0.2)', color: '#ffffff', border: '1px solid rgba(255,255,255,0.5)' }}
                onClick={handleBulkCreateLogins}
                disabled={provisioning}
                title="Username = Enrollment No, password = Enrollment No"
              >
                <KeyRound size={16} style={{ marginRight: '0.4rem' }} />
                <span>{provisioning ? 'Creating Logins...' : 'Create Logins'}</span>
              </button>
            )}
            <button
              className="edvana-btn"
              style={{ backgroundColor: '#ffffff', color: 'var(--edvana-brand)' }}
              onClick={() => setShowCreateModal(true)}
            >
              <Plus size={16} style={{ marginRight: '0.4rem' }} />
              <span>Register Student</span>
            </button>
          </div>
        </div>
      </div>

      <div className="edvana-banner-overlap">
        <div className="edvana-card">
          {/* Filter bar */}
          <div className="edvana-card-header" style={{ flexDirection: 'column', alignItems: 'stretch', gap: '0.7rem' }}>
            <div style={{ display: 'flex', gap: '0.6rem', flexWrap: 'wrap' }}>
              <div style={{ position: 'relative', minWidth: '220px', flex: '2 1 220px' }}>
                <Search size={15} color="var(--edvana-text-muted)" style={{ position: 'absolute', left: '10px', top: '10px' }} />
                <input
                  type="text"
                  className="edvana-input"
                  style={{ paddingLeft: '2.1rem' }}
                  placeholder="Search name, enrollment no, application ID, username, mobile..."
                  value={search}
                  onChange={(e) => { setSearch(e.target.value); setPage(1); }}
                />
              </div>
              <select className="edvana-select" value={deptFilter} onChange={(e) => { setDeptFilter(e.target.value); setPage(1); }} style={{ flex: '1 1 150px' }}>
                <option value="">All Departments</option>
                {safeDepartments.map((d) => (
                  <option key={d.id} value={d.id}>{d.code ? `${d.code} - ` : ''}{d.name}</option>
                ))}
              </select>
              <select className="edvana-select" value={divisionFilter} onChange={(e) => { setDivisionFilter(e.target.value); setPage(1); }} style={{ flex: '0 1 130px' }}>
                <option value="">All Divisions</option>
                {DIVISION_OPTIONS.map((d) => (
                  <option key={d} value={d}>Div {d}</option>
                ))}
              </select>
              <select className="edvana-select" value={genderFilter} onChange={(e) => { setGenderFilter(e.target.value); setPage(1); }} style={{ flex: '0 1 120px' }}>
                <option value="">All Genders</option>
                <option value="MALE">Male</option>
                <option value="FEMALE">Female</option>
                <option value="OTHER">Other</option>
              </select>
              <select className="edvana-select" value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }} style={{ flex: '0 1 130px' }}>
                <option value="">All Statuses</option>
                <option value="ACTIVE">Active</option>
                <option value="DETAINED">Detained</option>
                <option value="PASSED_OUT">Passed Out</option>
                <option value="DROPPED">Dropped</option>
              </select>
              <select className="edvana-select" value={loginFilter} onChange={(e) => { setLoginFilter(e.target.value); setPage(1); }} style={{ flex: '0 1 120px' }}>
                <option value="">Login: All</option>
                <option value="true">Has login</option>
                <option value="false">No login</option>
              </select>
              {activeFilterCount > 0 && (
                <button className="edvana-btn edvana-btn-outline" onClick={resetFilters} title="Clear all filters" style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                  <RotateCcw size={14} /> Reset ({activeFilterCount})
                </button>
              )}
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--edvana-text-muted)' }}>
              {loading ? 'Loading...' : <><b style={{ color: 'var(--edvana-text-primary)' }}>{totalCount}</b> result{totalCount === 1 ? '' : 's'} found</>}
            </div>
          </div>

          {/* Table — reference style: S.N. / ENROLL NO. / NAME / FATHER'S NAME / MOBILE */}
          <div className="edvana-card-body" style={{ padding: 0 }}>
            {loading ? (
              <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--edvana-text-muted)' }}>Loading students...</div>
            ) : students.length === 0 ? (
              <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--edvana-text-muted)' }}>
                <Users size={36} style={{ margin: '0 auto 0.75rem', opacity: 0.4 }} />
                <p>No students found matching current filters.</p>
                <button className="edvana-btn edvana-btn-outline" onClick={resetFilters} style={{ marginTop: '0.5rem' }}>Clear filters</button>
              </div>
            ) : (
              <>
                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.87rem', background: '#fff' }}>
                    <thead>
                      <tr style={{ background: '#f1f5f9', textAlign: 'left' }}>
                        <th style={{ padding: '10px 16px', fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.06em', color: '#64748b', width: '56px' }}>S.N.</th>
                        <th style={{ padding: '10px 16px', fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.06em', color: '#64748b' }}>ENROLL NO.</th>
                        <th style={{ padding: '10px 16px', fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.06em', color: '#64748b' }}>NAME</th>
                        <th style={{ padding: '10px 16px', fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.06em', color: '#64748b' }}>FATHER'S NAME</th>
                        <th style={{ padding: '10px 16px', fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.06em', color: '#64748b' }}>MOBILE</th>
                        <th style={{ padding: '10px 16px', fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.06em', color: '#64748b' }}>DIV</th>
                        <th style={{ padding: '10px 16px', fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.06em', color: '#64748b' }}>USERNAME / LOGIN</th>
                        <th style={{ padding: '10px 16px', fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.06em', color: '#64748b', textAlign: 'right' }}>ACTION</th>
                      </tr>
                    </thead>
                    <tbody>
                      {students.map((s, idx) => {
                        const sn = (safePage - 1) * pageSize + idx + 1;
                        const mainId = s.enrollment_no || s.application_id || '—';
                        const subId = s.enrollment_no && s.application_id && s.enrollment_no !== s.application_id
                          ? s.application_id
                          : '';
                        const username = s.username || (s.has_login ? (s.enrollment_no || s.application_id) : null);
                        return (
                          <tr key={s.id} style={{ borderTop: '1px solid #f1f5f9' }}>
                            <td style={{ padding: '12px 16px', color: '#94a3b8', fontWeight: 600 }}>{sn}</td>
                            <td style={{ padding: '12px 16px' }}>
                              <div style={{ fontWeight: 800, color: '#2563eb', fontSize: '0.88rem' }}>{mainId}</div>
                              {subId && <div style={{ fontSize: '0.72rem', color: '#64748b', fontFamily: 'monospace' }}>{subId}</div>}
                              {!s.enrollment_no && s.application_id && <div style={{ fontSize: '0.68rem', color: '#94a3b8' }}>App ID (no enroll no yet)</div>}
                            </td>
                            <td style={{ padding: '12px 16px' }}>
                              <div style={{ fontWeight: 800, color: '#0f172a', textTransform: 'uppercase', fontSize: '0.85rem' }}>{s.candidate_name}</div>
                              <div style={{ fontSize: '0.72rem', color: '#64748b', marginTop: '2px' }}>
                                {s.gender || '—'}{s.current_department ? ` • ${s.current_department}` : ''}{s.current_program ? ` • ${s.current_program}` : ''}
                              </div>
                            </td>
                            <td style={{ padding: '12px 16px', color: '#334155' }}>{s.father_name || '—'}</td>
                            <td style={{ padding: '12px 16px', fontFamily: 'monospace', color: '#0f172a' }}>{s.student_mobile || '—'}</td>
                            <td style={{ padding: '12px 16px' }}>
                              <span style={{ display: 'inline-block', minWidth: '30px', textAlign: 'center', fontWeight: 800, fontSize: '0.78rem', background: '#eff6ff', color: '#1d4ed8', border: '1px solid #bfdbfe', borderRadius: '6px', padding: '2px 8px' }}>
                                {s.current_division || '—'}
                              </span>
                            </td>
                            <td style={{ padding: '12px 16px' }}>
                              {s.has_login || username ? (
                                <div>
                                  <button
                                    onClick={() => username && copyText(username)}
                                    title={username ? `Click to copy username: ${username}` : 'Username'}
                                    style={{ background: 'none', border: 'none', padding: 0, cursor: username ? 'pointer' : 'default', fontFamily: 'monospace', fontSize: '0.8rem', fontWeight: 700, color: '#0f172a' }}
                                  >
                                    {username || '—'}
                                  </button>
                                  <div style={{ marginTop: '3px', display: 'flex', gap: '4px', alignItems: 'center' }}>
                                    <span className="edvana-badge edvana-badge-success">Yes</span>
                                    {username && (
                                      <button
                                        onClick={() => copyText(username)}
                                        title="Copy username"
                                        style={{ background: '#f1f5f9', border: '1px solid #e2e8f0', borderRadius: '5px', fontSize: '0.68rem', padding: '1px 6px', cursor: 'pointer', color: '#475569' }}
                                      >
                                        Copy
                                      </button>
                                    )}
                                  </div>
                                </div>
                              ) : canProvisionLogins ? (
                                <button
                                  className="edvana-btn edvana-btn-outline"
                                  style={{ padding: '0.2rem 0.55rem', fontSize: '0.72rem' }}
                                  disabled={provisionOneId === s.id}
                                  onClick={() => handleProvisionOne(s)}
                                  title={`Username = ${s.enrollment_no || s.application_id}, password = same`}
                                >
                                  {provisionOneId === s.id ? '...' : '+ Login'}
                                </button>
                              ) : (
                                <span className="edvana-badge" style={{ background: '#fef2f2', color: '#dc2626', border: '1px solid #fecaca' }}>No</span>
                              )}
                            </td>
                            <td style={{ padding: '12px 16px', textAlign: 'right', whiteSpace: 'nowrap' }}>
                              <Link to={`/students/${s.id}`} className="edvana-btn edvana-btn-outline" style={{ padding: '0.3rem 0.65rem', fontSize: '0.78rem' }}>
                                <span>Profile</span>
                                <ChevronRight size={14} />
                              </Link>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>

                {/* Footer: Showing X to Y of Z + pages */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem', padding: '0.8rem 1.1rem', borderTop: '1px solid #f1f5f9', background: '#fff' }}>
                  <div style={{ fontSize: '0.82rem', color: '#64748b' }}>
                    Showing {from} to {to} of {totalCount} students
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <select
                      className="edvana-select"
                      value={pageSize}
                      onChange={(e) => { setPageSize(Number(e.target.value)); setPage(1); }}
                      style={{ width: 'auto', padding: '0.3rem 0.5rem', fontSize: '0.8rem' }}
                    >
                      <option value={8}>8 / page</option>
                      <option value={10}>10 / page</option>
                      <option value={20}>20 / page</option>
                      <option value={50}>50 / page</option>
                    </select>
                    <button className="edvana-btn edvana-btn-outline" disabled={safePage <= 1} onClick={() => gotoPage(safePage - 1)} style={{ padding: '0.3rem 0.55rem' }}>
                      <ChevronLeft size={14} />
                    </button>
                    {pageNumbers().map((p) => (
                      <button
                        key={p}
                        onClick={() => gotoPage(p)}
                        style={{
                          minWidth: '30px', height: '30px', borderRadius: '7px', fontSize: '0.8rem', fontWeight: 700, cursor: 'pointer',
                          border: p === safePage ? '1px solid var(--edvana-brand)' : '1px solid #e2e8f0',
                          background: p === safePage ? 'var(--edvana-brand)' : '#fff',
                          color: p === safePage ? '#fff' : '#334155',
                        }}
                      >
                        {p}
                      </button>
                    ))}
                    <button className="edvana-btn edvana-btn-outline" disabled={safePage >= totalPages} onClick={() => gotoPage(safePage + 1)} style={{ padding: '0.3rem 0.55rem' }}>
                      <ChevronRight size={14} />
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Register Student Modal */}
      {showCreateModal && (
        <div className="modal-overlay">
          <div className="edvana-card modal-content" style={{ padding: '1.75rem', maxWidth: '580px' }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: '700', marginBottom: '0.4rem', color: 'var(--edvana-text-primary)' }}>
              Register New Student Record
            </h2>
            <p style={{ fontSize: '0.83rem', color: 'var(--edvana-text-muted)', marginTop: 0 }}>
              Step 1 creates the student record. Step 2 (Create Logins) gives them a login: username = Enrollment No, password = Enrollment No.
            </p>
            {error && (
              <div className="edvana-badge-danger" style={{ padding: '0.5rem 0.75rem', borderRadius: 'var(--edvana-radius-sm)', marginBottom: '1rem', width: '100%', boxSizing: 'border-box' }}>
                {error}
              </div>
            )}
            <form onSubmit={handleCreateStudent} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label className="edvana-detail-label">Full Candidate Name</label>
                <input
                  type="text"
                  className="edvana-input"
                  placeholder="First Middle Last"
                  value={studentForm.candidate_name}
                  onChange={(e) => setStudentForm({ ...studentForm, candidate_name: e.target.value })}
                  required
                />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <label className="edvana-detail-label">Gender</label>
                  <select
                    className="edvana-select"
                    value={studentForm.gender}
                    onChange={(e) => setStudentForm({ ...studentForm, gender: e.target.value })}
                  >
                    <option value="MALE">Male</option>
                    <option value="FEMALE">Female</option>
                    <option value="OTHER">Other</option>
                  </select>
                </div>
                <div>
                  <label className="edvana-detail-label">Date of Birth</label>
                  <input
                    type="date"
                    className="edvana-input"
                    value={studentForm.date_of_birth}
                    onChange={(e) => setStudentForm({ ...studentForm, date_of_birth: e.target.value })}
                    required
                  />
                </div>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <label className="edvana-detail-label">Enrollment Number</label>
                  <input
                    type="text"
                    className="edvana-input"
                    placeholder="ENR2026..."
                    value={studentForm.enrollment_no}
                    onChange={(e) => setStudentForm({ ...studentForm, enrollment_no: e.target.value })}
                  />
                </div>
                <div>
                  <label className="edvana-detail-label">Application ID</label>
                  <input
                    type="text"
                    className="edvana-input"
                    placeholder="APP2026..."
                    value={studentForm.application_id}
                    onChange={(e) => setStudentForm({ ...studentForm, application_id: e.target.value })}
                  />
                </div>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <label className="edvana-detail-label">Mobile Number</label>
                  <input
                    type="text"
                    className="edvana-input"
                    placeholder="98XXXXXXXX"
                    value={studentForm.student_mobile}
                    onChange={(e) => setStudentForm({ ...studentForm, student_mobile: e.target.value })}
                  />
                </div>
                <div>
                  <label className="edvana-detail-label">Email Address</label>
                  <input
                    type="email"
                    className="edvana-input"
                    placeholder="student@example.com"
                    value={studentForm.email}
                    onChange={(e) => setStudentForm({ ...studentForm, email: e.target.value })}
                  />
                </div>
              </div>
              <div>
                <label className="edvana-detail-label">Aadhaar Number (Stored Encrypted & Masked)</label>
                <input
                  type="text"
                  className="edvana-input"
                  placeholder="12-digit Aadhaar Number"
                  value={studentForm.aadhaar_number}
                  onChange={(e) => setStudentForm({ ...studentForm, aadhaar_number: e.target.value })}
                />
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem' }}>
                <button type="button" className="edvana-btn edvana-btn-outline" onClick={() => setShowCreateModal(false)}>Cancel</button>
                <button type="submit" className="edvana-btn edvana-btn-primary">Register Student</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
