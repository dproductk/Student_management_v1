import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { 
  Building2, 
  Plus, 
  Layers, 
  Search, 
  CheckCircle2, 
  XCircle, 
  ChevronRight, 
  BookOpen,
  ShieldAlert
} from 'lucide-react';

export const DepartmentList = () => {
  const { user, hasRole } = useAuth();
  const canManage = hasRole('SYSTEM_ADMIN') || user?.is_superuser;

  const [departments, setDepartments] = useState([]);
  const [selectedDept, setSelectedDept] = useState(null);
  const [programs, setPrograms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  // Modal states
  const [showDeptModal, setShowDeptModal] = useState(false);
  const [deptForm, setDeptForm] = useState({ name: '', code: '', choice_codes: '' });
  const [deptCodesInput, setDeptCodesInput] = useState('');
  const [savingCodes, setSavingCodes] = useState(false);
  const [showProgModal, setShowProgModal] = useState(false);
  const [progForm, setProgForm] = useState({ name: '', code: '', duration_years: 4, degree_type: 'B.Tech' });
  const [actionError, setActionError] = useState('');

  const fetchDepartments = async () => {
    try {
      setLoading(true);
      const res = await api.get('/academic/departments/');
      const data = res.data.results || res.data;
      setDepartments(data);
      if (data.length > 0 && !selectedDept) {
        setSelectedDept(data[0]);
      }
    } catch (err) {
      console.error('Failed to fetch departments', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchPrograms = async (deptId) => {
    try {
      const res = await api.get(`/academic/programs/?department=${deptId}`);
      setPrograms(res.data.results || res.data);
    } catch (err) {
      console.error('Failed to fetch programs', err);
    }
  };

  useEffect(() => {
    fetchDepartments();
  }, []);

  useEffect(() => {
    if (selectedDept) {
      fetchPrograms(selectedDept.id);
    }
  }, [selectedDept]);

  const parseCodes = (s) => (s || '').split(/[,\s]+/).map((c) => c.trim().toUpperCase()).filter(Boolean);

  const handleCreateDept = async (e) => {
    e.preventDefault();
    setActionError('');
    try {
      await api.post('/academic/departments/', {
        name: deptForm.name,
        code: deptForm.code,
        choice_codes: parseCodes(deptForm.choice_codes),
      });
      setDeptForm({ name: '', code: '', choice_codes: '' });
      setShowDeptModal(false);
      fetchDepartments();
    } catch (err) {
      setActionError(err.response?.data?.message || JSON.stringify(err.response?.data) || 'Failed to create department.');
    }
  };

  const handleAddCodesToDept = async (e) => {
    e.preventDefault();
    if (!selectedDept) return;
    const codes = parseCodes(deptCodesInput);
    if (!codes.length) return;
    try {
      setSavingCodes(true);
      const existing = (selectedDept.choice_codes || []).map((c) => String(c).toUpperCase());
      const merged = Array.from(new Set([...existing, ...codes]));
      const res = await api.patch(`/academic/departments/${selectedDept.id}/`, { choice_codes: merged });
      setSelectedDept(res.data);
      setDeptCodesInput('');
      fetchDepartments();
    } catch (err) {
      setActionError(err.response?.data?.detail || 'Failed to save choice codes.');
    } finally {
      setSavingCodes(false);
    }
  };

  const handleCreateProg = async (e) => {
    e.preventDefault();
    setActionError('');
    try {
      await api.post('/academic/programs/', {
        ...progForm,
        department: selectedDept.id
      });
      setProgForm({ name: '', code: '', duration_years: 4, degree_type: 'B.Tech' });
      setShowProgModal(false);
      fetchPrograms(selectedDept.id);
      fetchDepartments();
    } catch (err) {
      setActionError(err.response?.data?.message || 'Failed to create program.');
    }
  };

  const filteredDepts = departments.filter((d) => 
    d.name.toLowerCase().includes(search.toLowerCase()) || 
    d.code.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: '700', color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
            Departments & Programs
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '0.25rem' }}>
            Manage organizational divisions and academic degree curricula offerings.
          </p>
        </div>
        {canManage ? (
          <button 
            className="btn btn-primary"
            onClick={() => { setShowDeptModal(true); setActionError(''); }}
          >
            <Plus size={16} />
            <span>Add Department</span>
          </button>
        ) : (
          <span className="badge badge-secondary" style={{ padding: '0.5rem 0.85rem', fontSize: '0.85rem' }}>
            Read-Only (Managed by SysAdmin)
          </span>
        )}
      </div>

      {/* Main Grid: Left Departments, Right Programs */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.25fr', gap: '1.5rem', alignItems: 'start' }}>
        {/* Left Column: Department List */}
        <div className="card" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
            <div style={{ position: 'relative', flex: 1 }}>
              <Search size={16} color="var(--text-muted)" style={{ position: 'absolute', left: '10px', top: '11px' }} />
              <input
                type="text"
                className="form-control"
                style={{ paddingLeft: '2.2rem', width: '100%', fontSize: '0.85rem' }}
                placeholder="Search departments..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {loading ? (
              <p style={{ color: 'var(--text-muted)', padding: '1rem', textAlign: 'center' }}>Loading departments...</p>
            ) : filteredDepts.length === 0 ? (
              <p style={{ color: 'var(--text-muted)', padding: '1.5rem', textAlign: 'center' }}>No departments found. Click "Add Department" to create one.</p>
            ) : (
              filteredDepts.map((dept) => {
                const isSelected = selectedDept?.id === dept.id;
                return (
                  <div
                    key={dept.id}
                    onClick={() => setSelectedDept(dept)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '0.85rem 1rem',
                      borderRadius: 'var(--radius-md)',
                      backgroundColor: isSelected ? 'var(--bg-surface-hover)' : 'transparent',
                      border: `1px solid ${isSelected ? 'var(--primary-500)' : 'var(--border-subtle)'}`,
                      cursor: 'pointer',
                      transition: 'all var(--transition-fast)'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
                      <div style={{
                        width: '36px',
                        height: '36px',
                        borderRadius: 'var(--radius-md)',
                        background: 'var(--bg-surface-elevated)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'var(--primary-500)',
                        fontWeight: '700',
                        fontSize: '0.8rem'
                      }}>
                        {dept.code}
                      </div>
                      <div>
                        <h3 style={{ fontSize: '0.9rem', fontWeight: '600', color: 'var(--text-primary)' }}>
                          {dept.name}
                        </h3>
                        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                          {dept.program_count || 0} Programs offered
                        </p>
                      </div>
                    </div>
                    <ChevronRight size={18} color={isSelected ? 'var(--primary-500)' : 'var(--text-muted)'} />
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Right Column: Selected Department's Programs */}
        <div className="card" style={{ padding: '1.5rem' }}>
          {selectedDept ? (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '1rem' }}>
                <div>
                  <span className="badge badge-info" style={{ marginBottom: '0.4rem' }}>{selectedDept.code}</span>
                  <h2 style={{ fontSize: '1.25rem', fontWeight: '700', color: 'var(--text-primary)' }}>
                    {selectedDept.name} Programs
                  </h2>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem', marginTop: '0.5rem' }}>
                    {(selectedDept.choice_codes || []).map((c) => (
                      <code key={c} style={{ fontSize: '0.72rem', background: 'var(--bg-surface-elevated)', border: '1px solid var(--border-subtle)', borderRadius: '6px', padding: '0.15rem 0.45rem' }}>{c}</code>
                    ))}
                    {(!selectedDept.choice_codes || selectedDept.choice_codes.length === 0) && (
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>No choice codes marked yet</span>
                    )}
                  </div>
                  {canManage && (
                    <form onSubmit={handleAddCodesToDept} style={{ display: 'flex', gap: '0.5rem', marginTop: '0.6rem' }}>
                      <input
                        type="text"
                        className="form-control"
                        placeholder="Add codes: 0603624211T, 603624210"
                        value={deptCodesInput}
                        onChange={(e) => setDeptCodesInput(e.target.value)}
                        style={{ fontSize: '0.8rem', maxWidth: '320px' }}
                      />
                      <button type="submit" className="btn btn-secondary" disabled={savingCodes} style={{ fontSize: '0.8rem' }}>
                        {savingCodes ? 'Saving...' : 'Add Codes'}
                      </button>
                    </form>
                  )}
                </div>
                {canManage && (
                  <button 
                    className="btn btn-secondary" 
                    style={{ fontSize: '0.8rem' }}
                    onClick={() => { setShowProgModal(true); setActionError(''); }}
                  >
                    <Plus size={14} />
                    <span>Add Program</span>
                  </button>
                )}
              </div>

              {programs.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '3rem 1rem', color: 'var(--text-muted)' }}>
                  <BookOpen size={40} style={{ margin: '0 auto 1rem', opacity: 0.4 }} />
                  <p style={{ fontSize: '0.95rem' }}>No degree programs registered for this department.</p>
                  <p style={{ fontSize: '0.8rem', marginTop: '0.25rem' }}>
                    {canManage ? 'Click "Add Program" above to create B.Tech, M.Tech, or Diploma programs.' : 'Contact the System Administrator to register programs for this department.'}
                  </p>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  {programs.map((prog) => (
                    <div
                      key={prog.id}
                      style={{
                        padding: '1rem',
                        borderRadius: 'var(--radius-md)',
                        background: 'var(--bg-surface-elevated)',
                        border: '1px solid var(--border-subtle)',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center'
                      }}
                    >
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                          <span style={{ fontWeight: '700', color: 'var(--primary-100)', fontSize: '0.95rem' }}>
                            {prog.name}
                          </span>
                          <span className="badge badge-success" style={{ fontSize: '0.65rem' }}>
                            {prog.degree_type}
                          </span>
                        </div>
                        <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                          Program Code: <code style={{ color: 'var(--primary-500)' }}>{prog.code}</code> • Duration: {prog.duration_years} Years
                        </p>
                      </div>
                      <span className="badge badge-info" style={{ fontSize: '0.7rem' }}>
                        Active
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '3rem 1rem', color: 'var(--text-muted)' }}>
              Select a department on the left to view its programs.
            </div>
          )}
        </div>
      </div>

      {/* Add Department Modal */}
      {showDeptModal && (
        <div className="modal-overlay">
          <div className="modal-content" style={{ padding: '1.75rem' }}>
            <h2 style={{ fontSize: '1.2rem', fontWeight: '700', marginBottom: '1.25rem', color: 'var(--text-primary)' }}>
              Create Department
            </h2>
            {actionError && (
              <p style={{ color: 'var(--danger-text)', background: 'var(--danger-bg)', padding: '0.5rem 0.75rem', borderRadius: 'var(--radius-sm)', marginBottom: '1rem', fontSize: '0.85rem' }}>
                {actionError}
              </p>
            )}
            <form onSubmit={handleCreateDept}>
              <div className="form-group">
                <label className="form-label">Department Code (e.g. CSE, ECE, MECH)</label>
                <input
                  type="text"
                  className="form-control"
                  placeholder="CSE"
                  value={deptForm.code}
                  onChange={(e) => setDeptForm({ ...deptForm, code: e.target.value.toUpperCase() })}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Department Name</label>
                <input
                  type="text"
                  className="form-control"
                  placeholder="Computer Science & Engineering"
                  value={deptForm.name}
                  onChange={(e) => setDeptForm({ ...deptForm, name: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Choice Codes (comma-separated, e.g. 0603624211T, 603624210)</label>
                <input
                  type="text"
                  className="form-control"
                  placeholder="0603624211T, 603624210"
                  value={deptForm.choice_codes}
                  onChange={(e) => setDeptForm({ ...deptForm, choice_codes: e.target.value })}
                />
                <small style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                  One department holds many codes (different seat types map to the same dept).
                </small>
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1.5rem' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setShowDeptModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Create Department
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Program Modal */}
      {showProgModal && (
        <div className="modal-overlay">
          <div className="modal-content" style={{ padding: '1.75rem' }}>
            <h2 style={{ fontSize: '1.2rem', fontWeight: '700', marginBottom: '1.25rem', color: 'var(--text-primary)' }}>
              Add Program to {selectedDept?.code}
            </h2>
            {actionError && (
              <p style={{ color: 'var(--danger-text)', background: 'var(--danger-bg)', padding: '0.5rem 0.75rem', borderRadius: 'var(--radius-sm)', marginBottom: '1rem', fontSize: '0.85rem' }}>
                {actionError}
              </p>
            )}
            <form onSubmit={handleCreateProg}>
              <div className="form-group">
                <label className="form-label">Program Name</label>
                <input
                  type="text"
                  className="form-control"
                  placeholder="Bachelor of Technology in Computer Science"
                  value={progForm.name}
                  onChange={(e) => setProgForm({ ...progForm, name: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Program Code</label>
                <input
                  type="text"
                  className="form-control"
                  placeholder="BTECH-CS"
                  value={progForm.code}
                  onChange={(e) => setProgForm({ ...progForm, code: e.target.value.toUpperCase() })}
                  required
                />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="form-group">
                  <label className="form-label">Degree Type</label>
                  <select
                    className="form-control"
                    value={progForm.degree_type}
                    onChange={(e) => setProgForm({ ...progForm, degree_type: e.target.value })}
                  >
                    <option value="B.Tech">B.Tech</option>
                    <option value="M.Tech">M.Tech</option>
                    <option value="BCA">BCA</option>
                    <option value="MCA">MCA</option>
                    <option value="Diploma">Diploma</option>
                    <option value="Ph.D">Ph.D</option>
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Duration (Years)</label>
                  <input
                    type="number"
                    className="form-control"
                    min="1"
                    max="6"
                    value={progForm.duration_years}
                    onChange={(e) => setProgForm({ ...progForm, duration_years: parseInt(e.target.value) })}
                    required
                  />
                </div>
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1.5rem' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setShowProgModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Add Program
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
