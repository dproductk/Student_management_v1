import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  GraduationCap, 
  Search, 
  Filter, 
  Plus, 
  Building2, 
  UserCheck, 
  BookOpen, 
  Award,
  ChevronRight,
  Mail,
  Phone,
  Briefcase,
  X
} from 'lucide-react';
import api from '../../services/api';

export const FacultyList = () => {
  const navigate = useNavigate();
  const [facultyList, setFacultyList] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDept, setSelectedDept] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('');
  const [hodFilter, setHodFilter] = useState('');

  // Modal State
  const [showAddModal, setShowAddModal] = useState(false);
  const [formData, setFormData] = useState({
    faculty_id: '',
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    department: '',
    designation: 'Assistant Professor',
    employment_type: 'PERMANENT',
    status: 'ACTIVE',
    date_of_joining: new Date().toISOString().split('T')[0],
    cabin_number: '',
    is_hod: false,
    responsibilities: '',
    qualification: '',
    specialization: ''
  });
  const [formError, setFormError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const fetchFaculty = async () => {
    try {
      setLoading(true);
      let url = '/faculty/members/';
      const params = [];
      if (searchTerm) params.push(`search=${encodeURIComponent(searchTerm)}`);
      if (selectedDept) params.push(`department=${selectedDept}`);
      if (selectedStatus) params.push(`status=${selectedStatus}`);
      if (hodFilter) params.push(`is_hod=${hodFilter}`);
      if (params.length > 0) url += `?${params.join('&')}`;

      const res = await api.get(url);
      const data = Array.isArray(res.data) ? res.data : (res.data?.results || []);
      setFacultyList(data);
    } catch (err) {
      console.error('Failed to load faculty records', err);
      setFacultyList([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchDepartments = async () => {
    try {
      const res = await api.get('/academic/departments/');
      const data = Array.isArray(res.data) ? res.data : (res.data?.results || []);
      setDepartments(data);
      if (data.length > 0 && !formData.department) {
        setFormData(prev => ({ ...prev, department: data[0].id }));
      }
    } catch (err) {
      console.error('Failed to load departments', err);
      setDepartments([]);
    }
  };

  useEffect(() => {
    fetchDepartments();
  }, []);

  useEffect(() => {
    fetchFaculty();
  }, [searchTerm, selectedDept, selectedStatus, hodFilter]);

  const handleCreateFaculty = async (e) => {
    e.preventDefault();
    setFormError('');
    setSubmitting(true);
    try {
      await api.post('/faculty/members/', formData);
      setShowAddModal(false);
      setFormData({
        faculty_id: '',
        first_name: '',
        last_name: '',
        email: '',
        phone: '',
        department: departments[0]?.id || '',
        designation: 'Assistant Professor',
        employment_type: 'PERMANENT',
        status: 'ACTIVE',
        date_of_joining: new Date().toISOString().split('T')[0],
        cabin_number: '',
        is_hod: false,
        responsibilities: '',
        qualification: '',
        specialization: ''
      });
      fetchFaculty();
    } catch (err) {
      setFormError(err.response?.data?.detail || 'Failed to create faculty record.');
    } finally {
      setSubmitting(false);
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'ACTIVE':
        return <span className="edvana-badge edvana-badge-success">Active</span>;
      case 'ON_LEAVE':
        return <span className="edvana-badge edvana-badge-warning">On Leave</span>;
      case 'RESIGNED':
      case 'RETIRED':
      case 'TERMINATED':
        return <span className="edvana-badge edvana-badge-danger">{status}</span>;
      default:
        return <span className="edvana-badge">{status}</span>;
    }
  };

  // Stats calculation
  const safeFacultyList = Array.isArray(facultyList) ? facultyList : [];
  const totalFaculty = safeFacultyList.length;
  const hodCount = safeFacultyList.filter(f => f.is_hod).length;
  const activeCount = safeFacultyList.filter(f => f.status === 'ACTIVE').length;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Action Bar */}
      <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center' }}>
        <button 
          onClick={() => setShowAddModal(true)}
          className="edvana-btn edvana-btn-primary"
          style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
        >
          <Plus size={16} />
          Add Faculty Member
        </button>
      </div>

      {/* Metrics Row */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: '1rem'
      }}>
        <div className="edvana-card" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
            <div style={{ padding: '0.5rem', borderRadius: 'var(--edvana-radius-md)', background: 'var(--edvana-brand-soft)', color: 'var(--edvana-brand)' }}>
              <GraduationCap size={20} />
            </div>
            <span style={{ fontSize: '0.85rem', fontWeight: '600', color: 'var(--edvana-text-secondary)' }}>Total Faculty</span>
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: '700', color: 'var(--edvana-text-primary)' }}>{totalFaculty}</div>
        </div>

        <div className="edvana-card" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
            <div style={{ padding: '0.5rem', borderRadius: 'var(--edvana-radius-md)', background: 'var(--edvana-success-soft)', color: 'var(--edvana-success)' }}>
              <UserCheck size={20} />
            </div>
            <span style={{ fontSize: '0.85rem', fontWeight: '600', color: 'var(--edvana-text-secondary)' }}>Active Teaching</span>
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: '700', color: 'var(--edvana-text-primary)' }}>{activeCount}</div>
        </div>

        <div className="edvana-card" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
            <div style={{ padding: '0.5rem', borderRadius: 'var(--edvana-radius-md)', background: 'var(--edvana-warning-soft)', color: 'var(--edvana-warning)' }}>
              <Building2 size={20} />
            </div>
            <span style={{ fontSize: '0.85rem', fontWeight: '600', color: 'var(--edvana-text-secondary)' }}>Department HODs</span>
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: '700', color: 'var(--edvana-text-primary)' }}>{hodCount}</div>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="edvana-card" style={{ padding: '1rem', display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flex: '1', minWidth: '220px', background: 'var(--edvana-page-bg)', padding: '0.5rem 0.75rem', borderRadius: 'var(--edvana-radius-md)', border: '1px solid var(--edvana-border)' }}>
          <Search size={16} color="var(--edvana-text-muted)" />
          <input 
            type="text" 
            placeholder="Search by name, ID, or email..." 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{ border: 'none', background: 'transparent', outline: 'none', width: '100%', fontSize: '0.9rem' }}
          />
        </div>

        <select 
          value={selectedDept}
          onChange={(e) => setSelectedDept(e.target.value)}
          className="edvana-input"
          style={{ width: 'auto', minWidth: '180px' }}
        >
          <option value="">All Departments</option>
          {departments.map(d => (
            <option key={d.id} value={d.id}>{d.code} - {d.name}</option>
          ))}
        </select>

        <select 
          value={selectedStatus}
          onChange={(e) => setSelectedStatus(e.target.value)}
          className="edvana-input"
          style={{ width: 'auto', minWidth: '140px' }}
        >
          <option value="">All Statuses</option>
          <option value="ACTIVE">Active</option>
          <option value="ON_LEAVE">On Leave</option>
          <option value="RESIGNED">Resigned</option>
          <option value="RETIRED">Retired</option>
        </select>

        <select 
          value={hodFilter}
          onChange={(e) => setHodFilter(e.target.value)}
          className="edvana-input"
          style={{ width: 'auto', minWidth: '140px' }}
        >
          <option value="">Role: All</option>
          <option value="true">HOD Only</option>
        </select>
      </div>

      {/* Faculty Directory Table */}
      <div className="edvana-card" style={{ overflow: 'hidden' }}>
        {loading ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--edvana-text-muted)' }}>
            Loading faculty records...
          </div>
        ) : safeFacultyList.length === 0 ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--edvana-text-muted)' }}>
            No faculty members found matching current criteria.
          </div>
        ) : (
          <div className="edvana-table-container">
            <table className="edvana-table">
              <thead>
                <tr>
                  <th>Faculty Member</th>
                  <th>Department</th>
                  <th>Designation</th>
                  <th>Cabin & Contact</th>
                  <th>Status</th>
                  <th style={{ textAlign: 'right' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {safeFacultyList.map(faculty => (
                  <tr 
                    key={faculty.id} 
                    onClick={() => navigate(`/faculty/${faculty.id}`)}
                    style={{ cursor: 'pointer' }}
                  >
                    <td>
                      <div style={{ display: 'flex', flexDirection: 'column' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <span style={{ fontWeight: '600', color: 'var(--edvana-text-primary)' }}>
                            {faculty.full_name}
                          </span>
                          {faculty.is_hod && (
                            <span className="edvana-badge edvana-badge-brand" style={{ fontSize: '0.65rem' }}>
                              HOD
                            </span>
                          )}
                        </div>
                        <span style={{ fontSize: '0.75rem', color: 'var(--edvana-text-muted)', fontFamily: 'var(--edvana-font-mono)' }}>
                          {faculty.faculty_id} • {faculty.employment_type}
                        </span>
                      </div>
                    </td>
                    <td>
                      <span className="edvana-badge edvana-badge-info">
                        {faculty.department_code}
                      </span>
                    </td>
                    <td>
                      <span style={{ fontSize: '0.85rem', fontWeight: '500', color: 'var(--edvana-text-primary)' }}>
                        {faculty.designation}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.15rem', fontSize: '0.8rem', color: 'var(--edvana-text-secondary)' }}>
                        {faculty.cabin_number && <span>Cabin: {faculty.cabin_number}</span>}
                        <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                          <Mail size={12} /> {faculty.email}
                        </span>
                      </div>
                    </td>
                    <td>
                      {getStatusBadge(faculty.status)}
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      <button 
                        className="edvana-btn edvana-btn-ghost"
                        style={{ padding: '0.35rem 0.5rem' }}
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/faculty/${faculty.id}`);
                        }}
                      >
                        <ChevronRight size={16} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Add Faculty Modal */}
      {showAddModal && (
        <div style={{
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
          padding: '1.5rem'
        }}>
          <div className="edvana-card" style={{ width: '100%', maxWidth: '640px', maxHeight: '90vh', overflowY: 'auto', padding: '1.75rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
              <h2 style={{ margin: 0, fontSize: '1.25rem', fontWeight: '700' }}>Add Faculty Member</h2>
              <button 
                onClick={() => setShowAddModal(false)}
                className="edvana-btn edvana-btn-ghost" 
                style={{ padding: '0.35rem' }}
              >
                <X size={18} />
              </button>
            </div>

            {formError && (
              <div style={{ padding: '0.75rem', background: 'var(--edvana-danger-soft)', border: '1px solid var(--edvana-danger-border)', borderRadius: 'var(--edvana-radius-md)', color: 'var(--edvana-danger)', marginBottom: '1rem', fontSize: '0.85rem' }}>
                {formError}
              </div>
            )}

            <form onSubmit={handleCreateFaculty} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <label className="edvana-label">Faculty ID *</label>
                  <input 
                    type="text" 
                    required 
                    className="edvana-input"
                    placeholder="e.g. FAC-2026-001"
                    value={formData.faculty_id}
                    onChange={(e) => setFormData({ ...formData, faculty_id: e.target.value })}
                  />
                </div>
                <div>
                  <label className="edvana-label">Department *</label>
                  <select 
                    required
                    className="edvana-input"
                    value={formData.department}
                    onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                  >
                    {departments.map(d => (
                      <option key={d.id} value={d.id}>{d.code} - {d.name}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <label className="edvana-label">First Name *</label>
                  <input 
                    type="text" 
                    required 
                    className="edvana-input"
                    value={formData.first_name}
                    onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                  />
                </div>
                <div>
                  <label className="edvana-label">Last Name *</label>
                  <input 
                    type="text" 
                    required 
                    className="edvana-input"
                    value={formData.last_name}
                    onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <label className="edvana-label">Institutional Email *</label>
                  <input 
                    type="email" 
                    required 
                    className="edvana-input"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  />
                </div>
                <div>
                  <label className="edvana-label">Phone Number</label>
                  <input 
                    type="text" 
                    className="edvana-input"
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <label className="edvana-label">Designation *</label>
                  <input 
                    type="text" 
                    required 
                    className="edvana-input"
                    value={formData.designation}
                    onChange={(e) => setFormData({ ...formData, designation: e.target.value })}
                  />
                </div>
                <div>
                  <label className="edvana-label">Employment Type *</label>
                  <select 
                    className="edvana-input"
                    value={formData.employment_type}
                    onChange={(e) => setFormData({ ...formData, employment_type: e.target.value })}
                  >
                    <option value="PERMANENT">Permanent</option>
                    <option value="CONTRACT">Contract</option>
                    <option value="VISITING">Visiting</option>
                    <option value="ADJUNCT">Adjunct</option>
                  </select>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <label className="edvana-label">Date of Joining *</label>
                  <input 
                    type="date" 
                    required 
                    className="edvana-input"
                    value={formData.date_of_joining}
                    onChange={(e) => setFormData({ ...formData, date_of_joining: e.target.value })}
                  />
                </div>
                <div>
                  <label className="edvana-label">Cabin / Office Number</label>
                  <input 
                    type="text" 
                    className="edvana-input"
                    placeholder="e.g. CS-302"
                    value={formData.cabin_number}
                    onChange={(e) => setFormData({ ...formData, cabin_number: e.target.value })}
                  />
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.75rem', background: 'var(--edvana-page-bg)', borderRadius: 'var(--edvana-radius-md)' }}>
                <input
                  type="checkbox"
                  id="is_hod_cb"
                  checked={formData.is_hod}
                  onChange={(e) => setFormData({ ...formData, is_hod: e.target.checked })}
                />
                <label htmlFor="is_hod_cb" style={{ fontSize: '0.85rem', fontWeight: '600', cursor: 'pointer' }}>
                  Assign as Head of Department (HOD) — dept taken from Department above
                </label>
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--edvana-text-muted)', background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: '8px', padding: '0.6rem 0.8rem' }}>
                Login auto-created: username = Faculty ID, default password = <code>Edvana@2026</code>. HOD gets dept-scoped HOD role, others get FACULTY role.
              </div>

              <div>
                <label className="edvana-label">Administrative Responsibilities</label>
                <input 
                  type="text" 
                  className="edvana-input"
                  placeholder="e.g. Lab In-Charge, NBA Coordinator"
                  value={formData.responsibilities}
                  onChange={(e) => setFormData({ ...formData, responsibilities: e.target.value })}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '0.5rem' }}>
                <button 
                  type="button" 
                  onClick={() => setShowAddModal(false)}
                  className="edvana-btn edvana-btn-ghost"
                >
                  Cancel
                </button>
                <button 
                  type="submit" 
                  disabled={submitting}
                  className="edvana-btn edvana-btn-primary"
                >
                  {submitting ? 'Saving...' : 'Create Faculty Profile'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
