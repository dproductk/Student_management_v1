import React, { useState, useEffect } from 'react';
import { 
  FileSpreadsheet, 
  Search, 
  Filter, 
  Download, 
  Printer, 
  BarChart3, 
  CheckCircle2, 
  Clock, 
  AlertTriangle, 
  XCircle, 
  Building2, 
  Users, 
  ShieldCheck,
  RotateCcw,
  Eye,
  Layers
} from 'lucide-react';
import api from '../../services/api';

export const StudentRegister = () => {
  const [activeTab, setActiveTab] = useState('register'); // 'register' or 'dashboard'
  
  // Register state
  const [students, setStudents] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const pageSize = 25;

  // Filter options from Academic Foundation
  const [departments, setDepartments] = useState([]);
  const [programs, setPrograms] = useState([]);
  const [academicYears, setAcademicYears] = useState([]);
  const [batches, setBatches] = useState([]);

  // Active filter values
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDept, setSelectedDept] = useState('');
  const [selectedProg, setSelectedProg] = useState('');
  const [selectedYear, setSelectedYear] = useState('');
  const [selectedBatch, setSelectedBatch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedGender, setSelectedGender] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('');
  const [selectedVerif, setSelectedVerif] = useState('');

  // Dashboard state
  const [dashboardData, setDashboardData] = useState(null);
  const [dashboardLoading, setDashboardLoading] = useState(false);

  // Fetch filter metadata
  const fetchMetadata = async () => {
    try {
      const [deptRes, progRes, ayRes, batchRes] = await Promise.all([
        api.get('/academic/departments/'),
        api.get('/academic/programs/'),
        api.get('/academic/academic-years/'),
        api.get('/academic/batches/')
      ]);
      setDepartments(deptRes.data);
      setPrograms(progRes.data);
      setAcademicYears(ayRes.data);
      setBatches(batchRes.data);
    } catch (err) {
      console.error('Failed to load filter metadata', err);
    }
  };

  useEffect(() => {
    fetchMetadata();
  }, []);

  // Fetch register data
  const fetchRegister = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (searchTerm) params.append('search', searchTerm);
      if (selectedDept) params.append('department', selectedDept);
      if (selectedProg) params.append('program', selectedProg);
      if (selectedYear) params.append('academic_year', selectedYear);
      if (selectedBatch) params.append('batch', selectedBatch);
      if (selectedCategory) params.append('category', selectedCategory);
      if (selectedGender) params.append('gender', selectedGender);
      if (selectedStatus) params.append('status', selectedStatus);
      if (selectedVerif) params.append('verification_status', selectedVerif);
      
      params.append('limit', pageSize);
      params.append('offset', (page - 1) * pageSize);

      const res = await api.get(`/register/students/?${params.toString()}`);
      setStudents(res.data.results);
      setTotalCount(res.data.total_count);
    } catch (err) {
      console.error('Failed to load register data', err);
    } finally {
      setLoading(false);
    }
  };

  // Fetch dashboard data
  const fetchDashboard = async () => {
    try {
      setDashboardLoading(true);
      const params = new URLSearchParams();
      if (selectedDept) params.append('department', selectedDept);
      if (selectedYear) params.append('academic_year', selectedYear);

      const res = await api.get(`/register/dashboard/?${params.toString()}`);
      setDashboardData(res.data);
    } catch (err) {
      console.error('Failed to load dashboard data', err);
    } finally {
      setDashboardLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'register') {
      fetchRegister();
    } else {
      fetchDashboard();
    }
  }, [
    activeTab,
    page,
    searchTerm,
    selectedDept,
    selectedProg,
    selectedYear,
    selectedBatch,
    selectedCategory,
    selectedGender,
    selectedStatus,
    selectedVerif
  ]);

  const handleResetFilters = () => {
    setSearchTerm('');
    setSelectedDept('');
    setSelectedProg('');
    setSelectedYear('');
    setSelectedBatch('');
    setSelectedCategory('');
    setSelectedGender('');
    setSelectedStatus('');
    setSelectedVerif('');
    setPage(1);
  };

  const handleExportCSV = () => {
    const params = new URLSearchParams();
    if (searchTerm) params.append('search', searchTerm);
    if (selectedDept) params.append('department', selectedDept);
    if (selectedProg) params.append('program', selectedProg);
    if (selectedYear) params.append('academic_year', selectedYear);
    if (selectedBatch) params.append('batch', selectedBatch);
    if (selectedCategory) params.append('category', selectedCategory);
    if (selectedGender) params.append('gender', selectedGender);
    if (selectedStatus) params.append('status', selectedStatus);
    if (selectedVerif) params.append('verification_status', selectedVerif);

    window.open(`/api/v1/register/export/?${params.toString()}`, '_blank');
  };

  const handlePrint = () => {
    window.print();
  };

  const getVerificationPill = (status) => {
    switch (status) {
      case 'APPROVED':
        return <span className="edvana-badge edvana-badge-success" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}><CheckCircle2 size={12} /> Approved</span>;
      case 'PENDING':
        return <span className="edvana-badge edvana-badge-warning" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}><Clock size={12} /> Pending</span>;
      case 'NEEDS_CORRECTION':
        return <span className="edvana-badge edvana-badge-brand" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}><AlertTriangle size={12} /> Needs Correction</span>;
      case 'REJECTED':
        return <span className="edvana-badge edvana-badge-danger" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}><XCircle size={12} /> Rejected</span>;
      default:
        return <span className="edvana-badge" style={{ color: 'var(--edvana-text-muted)' }}>Unsubmitted</span>;
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header with Print & Export Actions */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '1.6rem', fontWeight: '700', color: 'var(--edvana-text-primary)' }}>
            Administrative Register & Dashboards
          </h1>
          <p style={{ margin: '0.25rem 0 0 0', color: 'var(--edvana-text-secondary)', fontSize: '0.9rem' }}>
            Multi-dimensional institutional queries, demographic breakdowns, verification tracking, and printable registers.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <button 
            onClick={handleExportCSV}
            className="edvana-btn edvana-btn-ghost"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem' }}
          >
            <Download size={16} /> Export CSV
          </button>
          <button 
            onClick={handlePrint}
            className="edvana-btn edvana-btn-ghost"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem' }}
          >
            <Printer size={16} /> Printable Sheet
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '0.5rem', borderBottom: '1px solid var(--edvana-border)', paddingBottom: '0.25rem' }}>
        <button 
          onClick={() => setActiveTab('register')}
          className={`edvana-btn ${activeTab === 'register' ? 'edvana-btn-primary' : 'edvana-btn-ghost'}`}
          style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}
        >
          <FileSpreadsheet size={16} /> Student Register Query
        </button>
        <button 
          onClick={() => setActiveTab('dashboard')}
          className={`edvana-btn ${activeTab === 'dashboard' ? 'edvana-btn-primary' : 'edvana-btn-ghost'}`}
          style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}
        >
          <BarChart3 size={16} /> Status & Analytics Dashboard
        </button>
      </div>

      {/* Filter Control Drawer */}
      <div className="edvana-card" style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'center' }}>
          {/* Search */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flex: '1', minWidth: '240px', background: 'var(--edvana-page-bg)', padding: '0.5rem 0.75rem', borderRadius: 'var(--edvana-radius-md)', border: '1px solid var(--edvana-border)' }}>
            <Search size={16} color="var(--edvana-text-muted)" />
            <input 
              type="text" 
              placeholder="Search by candidate name, enrollment no, app ID..." 
              value={searchTerm}
              onChange={(e) => { setSearchTerm(e.target.value); setPage(1); }}
              style={{ border: 'none', background: 'transparent', outline: 'none', width: '100%', fontSize: '0.9rem' }}
            />
          </div>

          <button 
            onClick={handleResetFilters}
            className="edvana-btn edvana-btn-ghost"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem' }}
            title="Clear all filters"
          >
            <RotateCcw size={14} /> Reset Filters
          </button>
        </div>

        {/* Academic & Administrative Filter Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '0.75rem' }}>
          {/* Department */}
          <div>
            <label className="edvana-label" style={{ fontSize: '0.75rem' }}>Department</label>
            <select 
              className="edvana-input"
              style={{ fontSize: '0.85rem', padding: '0.45rem' }}
              value={selectedDept}
              onChange={(e) => { setSelectedDept(e.target.value); setPage(1); }}
            >
              <option value="">All Departments</option>
              {departments.map(d => (
                <option key={d.id} value={d.id}>{d.code} - {d.name}</option>
              ))}
            </select>
          </div>

          {/* Program */}
          <div>
            <label className="edvana-label" style={{ fontSize: '0.75rem' }}>Program</label>
            <select 
              className="edvana-input"
              style={{ fontSize: '0.85rem', padding: '0.45rem' }}
              value={selectedProg}
              onChange={(e) => { setSelectedProg(e.target.value); setPage(1); }}
            >
              <option value="">All Programs</option>
              {programs.map(p => (
                <option key={p.id} value={p.id}>{p.code} - {p.name}</option>
              ))}
            </select>
          </div>

          {/* Academic Year */}
          <div>
            <label className="edvana-label" style={{ fontSize: '0.75rem' }}>Academic Year</label>
            <select 
              className="edvana-input"
              style={{ fontSize: '0.85rem', padding: '0.45rem' }}
              value={selectedYear}
              onChange={(e) => { setSelectedYear(e.target.value); setPage(1); }}
            >
              <option value="">All Academic Years</option>
              {academicYears.map(y => (
                <option key={y.id} value={y.id}>{y.label} {y.is_current ? '(Current)' : ''}</option>
              ))}
            </select>
          </div>

          {/* Batch */}
          <div>
            <label className="edvana-label" style={{ fontSize: '0.75rem' }}>Batch</label>
            <select 
              className="edvana-input"
              style={{ fontSize: '0.85rem', padding: '0.45rem' }}
              value={selectedBatch}
              onChange={(e) => { setSelectedBatch(e.target.value); setPage(1); }}
            >
              <option value="">All Batches</option>
              {batches.map(b => (
                <option key={b.id} value={b.id}>{b.department_code || ''} {b.name}</option>
              ))}
            </select>
          </div>

          {/* Social Category */}
          <div>
            <label className="edvana-label" style={{ fontSize: '0.75rem' }}>Social Category</label>
            <select 
              className="edvana-input"
              style={{ fontSize: '0.85rem', padding: '0.45rem' }}
              value={selectedCategory}
              onChange={(e) => { setSelectedCategory(e.target.value); setPage(1); }}
            >
              <option value="">All Categories</option>
              <option value="OPEN">OPEN / General</option>
              <option value="OBC">OBC</option>
              <option value="SC">SC</option>
              <option value="ST">ST</option>
              <option value="EWS">EWS</option>
              <option value="VJNT">VJNT</option>
            </select>
          </div>

          {/* Gender */}
          <div>
            <label className="edvana-label" style={{ fontSize: '0.75rem' }}>Gender</label>
            <select 
              className="edvana-input"
              style={{ fontSize: '0.85rem', padding: '0.45rem' }}
              value={selectedGender}
              onChange={(e) => { setSelectedGender(e.target.value); setPage(1); }}
            >
              <option value="">All Genders</option>
              <option value="MALE">Male</option>
              <option value="FEMALE">Female</option>
              <option value="OTHER">Other</option>
            </select>
          </div>

          {/* Student Status */}
          <div>
            <label className="edvana-label" style={{ fontSize: '0.75rem' }}>Student Status</label>
            <select 
              className="edvana-input"
              style={{ fontSize: '0.85rem', padding: '0.45rem' }}
              value={selectedStatus}
              onChange={(e) => { setSelectedStatus(e.target.value); setPage(1); }}
            >
              <option value="">All Statuses</option>
              <option value="ACTIVE">Active</option>
              <option value="DETAINED">Detained</option>
              <option value="PASSED_OUT">Passed Out</option>
              <option value="DROPPED">Dropped</option>
              <option value="TRANSFERRED">Transferred</option>
              <option value="CANCELLED">Cancelled</option>
            </select>
          </div>

          {/* Verification Status */}
          <div>
            <label className="edvana-label" style={{ fontSize: '0.75rem' }}>Verification Status</label>
            <select 
              className="edvana-input"
              style={{ fontSize: '0.85rem', padding: '0.45rem' }}
              value={selectedVerif}
              onChange={(e) => { setSelectedVerif(e.target.value); setPage(1); }}
            >
              <option value="">All Verification</option>
              <option value="APPROVED">Approved</option>
              <option value="PENDING">Pending Review</option>
              <option value="NEEDS_CORRECTION">Needs Correction</option>
              <option value="REJECTED">Rejected</option>
              <option value="UNSUBMITTED">Unsubmitted</option>
            </select>
          </div>
        </div>
      </div>

      {/* TAB 1: Student Register View */}
      {activeTab === 'register' && (
        <div className="edvana-card" style={{ overflow: 'hidden' }}>
          <div style={{ padding: '1rem 1.25rem', borderBottom: '1px solid var(--edvana-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.9rem', fontWeight: '600', color: 'var(--edvana-text-secondary)' }}>
              Showing {students.length} of {totalCount} Registered Students
            </span>
            <span style={{ fontSize: '0.8rem', color: 'var(--edvana-text-muted)' }}>
              Page {page} of {Math.max(1, Math.ceil(totalCount / pageSize))}
            </span>
          </div>

          {loading ? (
            <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--edvana-text-muted)' }}>
              Loading administrative register records...
            </div>
          ) : students.length === 0 ? (
            <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--edvana-text-muted)' }}>
              No student records match the active filter criteria.
            </div>
          ) : (
            <div className="edvana-table-container">
              <table className="edvana-table">
                <thead>
                  <tr>
                    <th>Student Candidate</th>
                    <th>Enrollment & ID</th>
                    <th>Academic Allocation</th>
                    <th>Demographics</th>
                    <th>Status</th>
                    <th>Verification</th>
                    <th>Aadhaar (Protected)</th>
                  </tr>
                </thead>
                <tbody>
                  {students.map(s => (
                    <tr key={s.id}>
                      <td>
                        <div style={{ display: 'flex', flexDirection: 'column' }}>
                          <span style={{ fontWeight: '600', color: 'var(--edvana-text-primary)' }}>
                            {s.candidate_name}
                          </span>
                          <span style={{ fontSize: '0.75rem', color: 'var(--edvana-text-secondary)' }}>
                            {s.email || 'No email recorded'}
                          </span>
                        </div>
                      </td>
                      <td>
                        <div style={{ display: 'flex', flexDirection: 'column', fontFamily: 'var(--edvana-font-mono)', fontSize: '0.8rem' }}>
                          <span style={{ fontWeight: '500' }}>Enr: {s.enrollment_no || 'Pending'}</span>
                          <span style={{ color: 'var(--edvana-text-muted)', fontSize: '0.75rem' }}>App: {s.application_id || 'N/A'}</span>
                        </div>
                      </td>
                      <td>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
                          <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center' }}>
                            <span className="edvana-badge edvana-badge-info">{s.department_code || 'N/A'}</span>
                            {s.batch_name && <span style={{ fontSize: '0.75rem', fontWeight: '500' }}>{s.batch_name}</span>}
                          </div>
                          <span style={{ fontSize: '0.75rem', color: 'var(--edvana-text-muted)' }}>
                            {s.academic_year || 'Term unassigned'}
                          </span>
                        </div>
                      </td>
                      <td>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.15rem', fontSize: '0.8rem' }}>
                          <span>Gender: <strong>{s.gender}</strong></span>
                          <span>Category: <strong>{s.category}</strong></span>
                        </div>
                      </td>
                      <td>
                        <span className={`edvana-badge ${s.status === 'ACTIVE' ? 'edvana-badge-success' : 'edvana-badge-warning'}`}>
                          {s.status}
                        </span>
                      </td>
                      <td>
                        {getVerificationPill(s.verification_status)}
                      </td>
                      <td>
                        <span style={{ fontFamily: 'var(--edvana-font-mono)', fontSize: '0.8rem', color: 'var(--edvana-text-secondary)' }}>
                          {s.aadhaar_masked}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination Controls */}
          {totalCount > pageSize && (
            <div style={{ padding: '1rem', display: 'flex', justifyContent: 'flex-end', gap: '0.5rem', borderTop: '1px solid var(--edvana-border)' }}>
              <button 
                disabled={page === 1} 
                onClick={() => setPage(page - 1)}
                className="edvana-btn edvana-btn-ghost"
                style={{ fontSize: '0.85rem' }}
              >
                Previous
              </button>
              <button 
                disabled={page * pageSize >= totalCount}
                onClick={() => setPage(page + 1)}
                className="edvana-btn edvana-btn-ghost"
                style={{ fontSize: '0.85rem' }}
              >
                Next
              </button>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: Administrative Dashboard */}
      {activeTab === 'dashboard' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {dashboardLoading || !dashboardData ? (
            <div className="edvana-card" style={{ padding: '3rem', textAlign: 'center', color: 'var(--edvana-text-muted)' }}>
              Computing administrative analytics and status distributions...
            </div>
          ) : (
            <>
              {/* Summary KPIs */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
                <div className="edvana-card" style={{ padding: '1.25rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                    <div style={{ padding: '0.5rem', borderRadius: 'var(--edvana-radius-md)', background: 'var(--edvana-brand-soft)', color: 'var(--edvana-brand)' }}>
                      <Users size={20} />
                    </div>
                    <span style={{ fontSize: '0.85rem', fontWeight: '600', color: 'var(--edvana-text-secondary)' }}>Total Enrolled</span>
                  </div>
                  <div style={{ fontSize: '1.8rem', fontWeight: '700', color: 'var(--edvana-text-primary)' }}>
                    {dashboardData.total_students}
                  </div>
                </div>

                <div className="edvana-card" style={{ padding: '1.25rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                    <div style={{ padding: '0.5rem', borderRadius: 'var(--edvana-radius-md)', background: 'var(--edvana-success-soft)', color: 'var(--edvana-success)' }}>
                      <CheckCircle2 size={20} />
                    </div>
                    <span style={{ fontSize: '0.85rem', fontWeight: '600', color: 'var(--edvana-text-secondary)' }}>Active Students</span>
                  </div>
                  <div style={{ fontSize: '1.8rem', fontWeight: '700', color: 'var(--edvana-text-primary)' }}>
                    {dashboardData.active_students}
                  </div>
                </div>

                <div className="edvana-card" style={{ padding: '1.25rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                    <div style={{ padding: '0.5rem', borderRadius: 'var(--edvana-radius-md)', background: 'var(--edvana-warning-soft)', color: 'var(--edvana-warning)' }}>
                      <Clock size={20} />
                    </div>
                    <span style={{ fontSize: '0.85rem', fontWeight: '600', color: 'var(--edvana-text-secondary)' }}>Pending Verifications</span>
                  </div>
                  <div style={{ fontSize: '1.8rem', fontWeight: '700', color: 'var(--edvana-text-primary)' }}>
                    {dashboardData.verification_breakdown?.PENDING || 0}
                  </div>
                </div>

                <div className="edvana-card" style={{ padding: '1.25rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                    <div style={{ padding: '0.5rem', borderRadius: 'var(--edvana-radius-md)', background: 'var(--edvana-info-soft)', color: 'var(--edvana-info)' }}>
                      <ShieldCheck size={20} />
                    </div>
                    <span style={{ fontSize: '0.85rem', fontWeight: '600', color: 'var(--edvana-text-secondary)' }}>Approved Verifications</span>
                  </div>
                  <div style={{ fontSize: '1.8rem', fontWeight: '700', color: 'var(--edvana-text-primary)' }}>
                    {dashboardData.verification_breakdown?.APPROVED || 0}
                  </div>
                </div>
              </div>

              {/* Multi-Dimensional Analytics Grid */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.25rem' }}>
                {/* Department Enrollment Breakdown */}
                <div className="edvana-card" style={{ padding: '1.5rem' }}>
                  <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.1rem', fontWeight: '600', color: 'var(--edvana-text-primary)' }}>
                    Department Enrollment
                  </h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                    {dashboardData.department_distribution?.map(dept => {
                      const pct = dashboardData.total_students > 0 
                        ? Math.round((dept.student_count / dashboardData.total_students) * 100) 
                        : 0;
                      return (
                        <div key={dept.department_id} style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                            <span style={{ fontWeight: '500' }}>{dept.code} - {dept.name}</span>
                            <span style={{ color: 'var(--edvana-text-secondary)' }}>{dept.student_count} ({pct}%)</span>
                          </div>
                          <div style={{ height: '8px', background: 'var(--edvana-page-bg)', borderRadius: '4px', overflow: 'hidden' }}>
                            <div style={{ height: '100%', width: `${pct}%`, background: 'var(--edvana-brand)', borderRadius: '4px' }} />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Social Category Representation */}
                <div className="edvana-card" style={{ padding: '1.5rem' }}>
                  <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.1rem', fontWeight: '600', color: 'var(--edvana-text-primary)' }}>
                    Social Category Breakdown
                  </h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                    {Object.entries(dashboardData.category_distribution || {}).map(([cat, count]) => {
                      const pct = dashboardData.total_students > 0 
                        ? Math.round((count / dashboardData.total_students) * 100) 
                        : 0;
                      return (
                        <div key={cat} style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                            <span style={{ fontWeight: '500' }}>{cat}</span>
                            <span style={{ color: 'var(--edvana-text-secondary)' }}>{count} ({pct}%)</span>
                          </div>
                          <div style={{ height: '8px', background: 'var(--edvana-page-bg)', borderRadius: '4px', overflow: 'hidden' }}>
                            <div style={{ height: '100%', width: `${pct}%`, background: 'var(--edvana-success)', borderRadius: '4px' }} />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Gender Distribution */}
                <div className="edvana-card" style={{ padding: '1.5rem' }}>
                  <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.1rem', fontWeight: '600', color: 'var(--edvana-text-primary)' }}>
                    Gender Distribution
                  </h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                    {Object.entries(dashboardData.gender_distribution || {}).map(([gen, count]) => {
                      const pct = dashboardData.total_students > 0 
                        ? Math.round((count / dashboardData.total_students) * 100) 
                        : 0;
                      return (
                        <div key={gen} style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                            <span style={{ fontWeight: '500' }}>{gen}</span>
                            <span style={{ color: 'var(--edvana-text-secondary)' }}>{count} ({pct}%)</span>
                          </div>
                          <div style={{ height: '8px', background: 'var(--edvana-page-bg)', borderRadius: '4px', overflow: 'hidden' }}>
                            <div style={{ height: '100%', width: `${pct}%`, background: 'var(--edvana-warning)', borderRadius: '4px' }} />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
};
