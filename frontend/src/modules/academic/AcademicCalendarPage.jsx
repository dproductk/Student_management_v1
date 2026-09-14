import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { 
  Calendar, 
  Plus, 
  Clock, 
  Users, 
  CheckCircle2, 
  Layers, 
  ChevronRight 
} from 'lucide-react';

export const AcademicCalendarPage = () => {
  const { user, hasRole } = useAuth();
  const canManage = hasRole('SYSTEM_ADMIN') || user?.is_superuser;

  const [academicYears, setAcademicYears] = useState([]);
  const [selectedAY, setSelectedAY] = useState(null);
  const [batches, setBatches] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(true);

  // Modals
  const [showAYModal, setShowAYModal] = useState(false);
  const [ayForm, setAYForm] = useState({ label: '', start_date: '', end_date: '', is_current: false });
  const [showBatchModal, setShowBatchModal] = useState(false);
  const [batchForm, setBatchForm] = useState({ department: '', name: '' });
  const [showSemModal, setShowSemModal] = useState(false);
  const [semForm, setSemForm] = useState({ number: 1, label: '', start_date: '', end_date: '' });
  const [actionError, setActionError] = useState('');

  const fetchCalendarData = async () => {
    try {
      setLoading(true);
      const [ayRes, deptRes] = await Promise.all([
        api.get('/academic/academic-years/'),
        api.get('/academic/departments/')
      ]);
      const ays = ayRes.data.results || ayRes.data;
      setAcademicYears(ays);
      setDepartments(deptRes.data.results || deptRes.data);
      if (ays.length > 0 && !selectedAY) {
        setSelectedAY(ays[0]);
      }
    } catch (err) {
      console.error('Failed to load academic years', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchBatches = async (ayId) => {
    try {
      const res = await api.get(`/academic/batches/?academic_year=${ayId}`);
      setBatches(res.data.results || res.data);
    } catch (err) {
      console.error('Failed to load batches', err);
    }
  };

  useEffect(() => {
    fetchCalendarData();
  }, []);

  useEffect(() => {
    if (selectedAY) {
      fetchBatches(selectedAY.id);
    }
  }, [selectedAY]);

  const handleCreateAY = async (e) => {
    e.preventDefault();
    setActionError('');
    try {
      await api.post('/academic/academic-years/', ayForm);
      setShowAYModal(false);
      setAYForm({ label: '', start_date: '', end_date: '', is_current: false });
      fetchCalendarData();
    } catch (err) {
      setActionError(err.response?.data?.message || err.response?.data?.detail || 'Failed to create academic year.');
    }
  };

  const handleCreateBatch = async (e) => {
    e.preventDefault();
    setActionError('');
    try {
      await api.post('/academic/batches/', {
        ...batchForm,
        academic_year: selectedAY.id
      });
      setShowBatchModal(false);
      setBatchForm({ department: '', name: '' });
      fetchBatches(selectedAY.id);
    } catch (err) {
      setActionError(err.response?.data?.message || 'Failed to create batch.');
    }
  };

  const handleCreateSem = async (e) => {
    e.preventDefault();
    setActionError('');
    try {
      await api.post('/academic/semesters/', {
        ...semForm,
        academic_year: selectedAY.id
      });
      setShowSemModal(false);
      setSemForm({ number: 1, label: '', start_date: '', end_date: '' });
      fetchCalendarData();
    } catch (err) {
      setActionError(err.response?.data?.message || 'Failed to create semester.');
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: '700', color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
            Academic Calendar & Batches
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '0.25rem' }}>
            Configure institutional academic sessions, semesters, cohorts, and intakes.
          </p>
        </div>
        {canManage ? (
          <button 
            className="btn btn-primary"
            onClick={() => { setShowAYModal(true); setActionError(''); }}
          >
            <Plus size={16} />
            <span>New Academic Year</span>
          </button>
        ) : (
          <span className="badge badge-secondary" style={{ padding: '0.5rem 0.85rem', fontSize: '0.85rem' }}>
            Academic Calendar View (Managed by SysAdmin)
          </span>
        )}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.35fr', gap: '1.5rem', alignItems: 'start' }}>
        {/* Left Column: Academic Years List */}
        <div className="card" style={{ padding: '1.25rem' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: '700', marginBottom: '1rem', color: 'var(--text-primary)' }}>
            Academic Sessions
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {academicYears.length === 0 ? (
              <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '1.5rem' }}>No academic sessions configured.</p>
            ) : (
              academicYears.map((ay) => {
                const isSelected = selectedAY?.id === ay.id;
                return (
                  <div
                    key={ay.id}
                    onClick={() => setSelectedAY(ay)}
                    style={{
                      padding: '1rem',
                      borderRadius: 'var(--radius-md)',
                      background: isSelected ? 'var(--bg-surface-hover)' : 'var(--bg-surface-elevated)',
                      border: `1px solid ${isSelected ? 'var(--primary-500)' : 'var(--border-subtle)'}`,
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between'
                    }}
                  >
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <h4 style={{ fontSize: '1.05rem', fontWeight: '700', color: 'var(--text-primary)' }}>
                          {ay.label}
                        </h4>
                        {ay.is_current && (
                          <span className="badge badge-success" style={{ fontSize: '0.65rem' }}>
                            Current Session
                          </span>
                        )}
                      </div>
                      <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.3rem' }}>
                        {ay.start_date} to {ay.end_date}
                      </p>
                    </div>
                    <ChevronRight size={18} color={isSelected ? 'var(--primary-500)' : 'var(--text-muted)'} />
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Right Column: Semesters & Batches for selected session */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {selectedAY ? (
            <>
              {/* Semesters Card */}
              <div className="card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                  <div>
                    <h3 style={{ fontSize: '1.1rem', fontWeight: '700', color: 'var(--text-primary)' }}>
                      Semesters ({selectedAY.label})
                    </h3>
                    <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Instructional terms within this academic year</p>
                  </div>
                  {canManage && (
                    <button 
                      className="btn btn-secondary" 
                      style={{ fontSize: '0.8rem' }}
                      onClick={() => { setShowSemModal(true); setActionError(''); }}
                    >
                      <Plus size={14} />
                      <span>Add Semester</span>
                    </button>
                  )}
                </div>

                {(!selectedAY.semesters || selectedAY.semesters.length === 0) ? (
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No semesters defined yet for this session.</p>
                ) : (
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: '0.75rem' }}>
                    {selectedAY.semesters.map((sem) => (
                      <div
                        key={sem.id}
                        style={{
                          padding: '0.85rem',
                          background: 'var(--bg-surface-elevated)',
                          border: '1px solid var(--border-subtle)',
                          borderRadius: 'var(--radius-md)'
                        }}
                      >
                        <span className="badge badge-info" style={{ fontSize: '0.65rem', marginBottom: '0.3rem' }}>
                          Term {sem.number}
                        </span>
                        <h4 style={{ fontSize: '0.9rem', fontWeight: '600', color: 'var(--text-primary)' }}>
                          {sem.label || `Semester ${sem.number}`}
                        </h4>
                        {sem.start_date && (
                          <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                            {sem.start_date} - {sem.end_date}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Batches Card */}
              <div className="card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                  <div>
                    <h3 style={{ fontSize: '1.1rem', fontWeight: '700', color: 'var(--text-primary)' }}>
                      Student Batches / Cohorts
                    </h3>
                    <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Department cohorts enrolled in this academic year</p>
                  </div>
                  {canManage && (
                    <button 
                      className="btn btn-secondary" 
                      style={{ fontSize: '0.8rem' }}
                      onClick={() => { setShowBatchModal(true); setActionError(''); }}
                    >
                      <Plus size={14} />
                      <span>Add Batch</span>
                    </button>
                  )}
                </div>

                {batches.length === 0 ? (
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No student batches created for this session yet.</p>
                ) : (
                  <div className="data-table-wrapper">
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>Batch Name</th>
                          <th>Department</th>
                          <th>Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {batches.map((b) => (
                          <tr key={b.id}>
                            <td style={{ fontWeight: '600', color: 'var(--text-primary)' }}>{b.name}</td>
                            <td>{b.department_code} - {b.department_name}</td>
                            <td>
                              <span className="badge badge-success" style={{ fontSize: '0.65rem' }}>
                                Active
                              </span>
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
            <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
              Select an academic session to manage semesters and batches.
            </div>
          )}
        </div>
      </div>

      {/* New Academic Year Modal */}
      {showAYModal && (
        <div className="modal-overlay">
          <div className="modal-content" style={{ padding: '1.75rem' }}>
            <h2 style={{ fontSize: '1.2rem', fontWeight: '700', marginBottom: '1.25rem' }}>
              Create Academic Session
            </h2>
            {actionError && (
              <p style={{ color: 'var(--danger-text)', background: 'var(--danger-bg)', padding: '0.5rem 0.75rem', borderRadius: 'var(--radius-sm)', marginBottom: '1rem', fontSize: '0.85rem' }}>
                {actionError}
              </p>
            )}
            <form onSubmit={handleCreateAY}>
              <div className="form-group">
                <label className="form-label">Session Label (e.g. 2026-2027)</label>
                <input
                  type="text"
                  className="form-control"
                  placeholder="2026-2027"
                  value={ayForm.label}
                  onChange={(e) => setAYForm({ ...ayForm, label: e.target.value })}
                  required
                />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="form-group">
                  <label className="form-label">Start Date</label>
                  <input
                    type="date"
                    className="form-control"
                    value={ayForm.start_date}
                    onChange={(e) => setAYForm({ ...ayForm, start_date: e.target.value })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">End Date</label>
                  <input
                    type="date"
                    className="form-control"
                    value={ayForm.end_date}
                    onChange={(e) => setAYForm({ ...ayForm, end_date: e.target.value })}
                    required
                  />
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.5rem' }}>
                <input
                  type="checkbox"
                  id="is_current"
                  checked={ayForm.is_current}
                  onChange={(e) => setAYForm({ ...ayForm, is_current: e.target.checked })}
                />
                <label htmlFor="is_current" style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', cursor: 'pointer' }}>
                  Set as Current Academic Year
                </label>
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1.5rem' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setShowAYModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Create Session</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Batch Modal */}
      {showBatchModal && (
        <div className="modal-overlay">
          <div className="modal-content" style={{ padding: '1.75rem' }}>
            <h2 style={{ fontSize: '1.2rem', fontWeight: '700', marginBottom: '1.25rem' }}>
              Add Batch to {selectedAY?.label}
            </h2>
            {actionError && (
              <p style={{ color: 'var(--danger-text)', background: 'var(--danger-bg)', padding: '0.5rem 0.75rem', borderRadius: 'var(--radius-sm)', marginBottom: '1rem', fontSize: '0.85rem' }}>
                {actionError}
              </p>
            )}
            <form onSubmit={handleCreateBatch}>
              <div className="form-group">
                <label className="form-label">Department</label>
                <select
                  className="form-control"
                  value={batchForm.department}
                  onChange={(e) => setBatchForm({ ...batchForm, department: e.target.value })}
                  required
                >
                  <option value="">Select Department</option>
                  {departments.map((d) => (
                    <option key={d.id} value={d.id}>{d.code} - {d.name}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Batch Name (e.g. CSE-2026-A)</label>
                <input
                  type="text"
                  className="form-control"
                  placeholder="CSE-2026-A"
                  value={batchForm.name}
                  onChange={(e) => setBatchForm({ ...batchForm, name: e.target.value })}
                  required
                />
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1.5rem' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setShowBatchModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Add Batch</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Semester Modal */}
      {showSemModal && (
        <div className="modal-overlay">
          <div className="modal-content" style={{ padding: '1.75rem' }}>
            <h2 style={{ fontSize: '1.2rem', fontWeight: '700', marginBottom: '1.25rem' }}>
              Add Semester to {selectedAY?.label}
            </h2>
            {actionError && (
              <p style={{ color: 'var(--danger-text)', background: 'var(--danger-bg)', padding: '0.5rem 0.75rem', borderRadius: 'var(--radius-sm)', marginBottom: '1rem', fontSize: '0.85rem' }}>
                {actionError}
              </p>
            )}
            <form onSubmit={handleCreateSem}>
              <div className="form-group">
                <label className="form-label">Semester Number</label>
                <input
                  type="number"
                  min="1"
                  max="12"
                  className="form-control"
                  value={semForm.number}
                  onChange={(e) => setSemForm({ ...semForm, number: parseInt(e.target.value) })}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Label (e.g. Fall 2026 / Semester 1)</label>
                <input
                  type="text"
                  className="form-control"
                  placeholder="Fall 2026"
                  value={semForm.label}
                  onChange={(e) => setSemForm({ ...semForm, label: e.target.value })}
                />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="form-group">
                  <label className="form-label">Start Date</label>
                  <input
                    type="date"
                    className="form-control"
                    value={semForm.start_date}
                    onChange={(e) => setSemForm({ ...semForm, start_date: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">End Date</label>
                  <input
                    type="date"
                    className="form-control"
                    value={semForm.end_date}
                    onChange={(e) => setSemForm({ ...semForm, end_date: e.target.value })}
                  />
                </div>
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1.5rem' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setShowSemModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Add Semester</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
