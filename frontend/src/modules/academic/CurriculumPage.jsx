import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { 
  BookOpen, 
  Plus, 
  Layers, 
  CheckCircle, 
  Award, 
  Lock, 
  ChevronRight,
  FileCode
} from 'lucide-react';

export const CurriculumPage = () => {
  const { user, hasRole } = useAuth();
  const canManage = hasRole('SYSTEM_ADMIN') || user?.is_superuser;

  const [schemes, setSchemes] = useState([]);
  const [selectedScheme, setSelectedScheme] = useState(null);
  const [subjects, setSubjects] = useState([]);
  const [programs, setPrograms] = useState([]);
  const [academicYears, setAcademicYears] = useState([]);
  const [loading, setLoading] = useState(true);

  // Modals
  const [showSchemeModal, setShowSchemeModal] = useState(false);
  const [schemeForm, setSchemeForm] = useState({ program: '', effective_from_year: '', name: '', code: '', choice_codes: '' });
  const [showSubjectModal, setShowSubjectModal] = useState(false);
  const [subjectForm, setSubjectForm] = useState({ name: '', code: '' });
  const [showMapModal, setShowMapModal] = useState(false);
  const [mapForm, setMapForm] = useState({
    subject: '',
    semester_number: 1,
    subject_type: 'THEORY',
    credits: 3,
    max_marks: 100,
    passing_marks: 40,
    is_elective: false
  });
  const [actionError, setActionError] = useState('');

  const fetchCurriculumData = async () => {
    try {
      setLoading(true);
      const [schemeRes, subjRes, progRes, ayRes] = await Promise.all([
        api.get('/academic/schemes/'),
        api.get('/academic/subjects/'),
        api.get('/academic/programs/'),
        api.get('/academic/academic-years/')
      ]);
      const schemeList = schemeRes.data.results || schemeRes.data;
      setSchemes(schemeList);
      setSubjects(subjRes.data.results || subjRes.data);
      setPrograms(progRes.data.results || progRes.data);
      setAcademicYears(ayRes.data.results || ayRes.data);
      if (schemeList.length > 0 && !selectedScheme) {
        setSelectedScheme(schemeList[0]);
      }
    } catch (err) {
      console.error('Failed to load curriculum data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCurriculumData();
  }, []);

  const handleCreateScheme = async (e) => {
    e.preventDefault();
    setActionError('');
    try {
      const { choice_codes, ...schemePayload } = schemeForm;
      await api.post('/academic/schemes/', schemePayload);
      // Choice codes entered here are marked onto the scheme program's department master
      const codes = (choice_codes || '').split(/[,\s]+/).map((c) => c.trim().toUpperCase()).filter(Boolean);
      if (codes.length) {
        const prog = programs.find((p) => p.id === schemeForm.program);
        const deptId = prog?.department;
        if (deptId) {
          try {
            const deptRes = await api.get(`/academic/departments/${deptId}/`);
            const existing = (deptRes.data?.choice_codes || []).map((c) => String(c).toUpperCase());
            const merged = Array.from(new Set([...existing, ...codes]));
            await api.patch(`/academic/departments/${deptId}/`, { choice_codes: merged });
          } catch (codeErr) {
            console.error('Scheme created but choice-code marking failed', codeErr);
          }
        }
      }
      setShowSchemeModal(false);
      setSchemeForm({ program: '', effective_from_year: '', name: '', code: '', choice_codes: '' });
      fetchCurriculumData();
    } catch (err) {
      setActionError(err.response?.data?.message || JSON.stringify(err.response?.data) || 'Failed to create scheme.');
    }
  };

  const handleCreateSubject = async (e) => {
    e.preventDefault();
    setActionError('');
    try {
      await api.post('/academic/subjects/', subjectForm);
      setShowSubjectModal(false);
      setSubjectForm({ name: '', code: '' });
      fetchCurriculumData();
    } catch (err) {
      setActionError(err.response?.data?.message || 'Failed to create subject.');
    }
  };

  const handleMapSubject = async (e) => {
    e.preventDefault();
    setActionError('');
    try {
      await api.post('/academic/scheme-subjects/', {
        ...mapForm,
        scheme: selectedScheme.id
      });
      setShowMapModal(false);
      setMapForm({
        subject: '',
        semester_number: 1,
        subject_type: 'THEORY',
        credits: 3,
        max_marks: 100,
        passing_marks: 40,
        is_elective: false
      });
      // Refresh current scheme
      const res = await api.get(`/academic/schemes/${selectedScheme.id}/`);
      setSelectedScheme(res.data);
      fetchCurriculumData();
    } catch (err) {
      setActionError(err.response?.data?.message || 'Failed to map subject.');
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: '700', color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
            Curriculum, Schemes & Subjects
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '0.25rem' }}>
            Define credit frameworks, subject catalogues, and semester curriculum structures.
          </p>
        </div>
        <div>
          {canManage ? (
            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <button 
                className="btn btn-secondary"
                onClick={() => { setShowSubjectModal(true); setActionError(''); }}
              >
                <Plus size={14} />
                <span>New Subject</span>
              </button>
              <button 
                className="btn btn-primary"
                onClick={() => { setShowSchemeModal(true); setActionError(''); }}
              >
                <Plus size={16} />
                <span>New Scheme</span>
              </button>
            </div>
          ) : (
            <span className="badge badge-secondary" style={{ padding: '0.5rem 0.85rem', fontSize: '0.85rem' }}>
              Curriculum View (Managed by SysAdmin)
            </span>
          )}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.5fr', gap: '1.5rem', alignItems: 'start' }}>
        {/* Left Column: Schemes List */}
        <div className="card" style={{ padding: '1.25rem' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: '700', marginBottom: '1rem', color: 'var(--text-primary)' }}>
            Curriculum Schemes
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
            {schemes.length === 0 ? (
              <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '1.5rem' }}>No schemes defined yet.</p>
            ) : (
              schemes.map((s) => {
                const isSelected = selectedScheme?.id === s.id;
                return (
                  <div
                    key={s.id}
                    onClick={() => setSelectedScheme(s)}
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
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.25rem' }}>
                        <span className="badge badge-info" style={{ fontSize: '0.65rem' }}>{s.code}</span>
                        <span className="badge badge-success" style={{ fontSize: '0.65rem' }}>{s.program_code}</span>
                      </div>
                      <h4 style={{ fontSize: '0.95rem', fontWeight: '700', color: 'var(--text-primary)' }}>
                        {s.name}
                      </h4>
                      <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                        Effective from {s.effective_from_year_label} • {s.scheme_subjects?.length || 0} subjects
                      </p>
                    </div>
                    <ChevronRight size={18} color={isSelected ? 'var(--primary-500)' : 'var(--text-muted)'} />
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Right Column: Scheme Details & Scheme-Subjects Mapping */}
        <div className="card" style={{ padding: '1.5rem' }}>
          {selectedScheme ? (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '1rem' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.35rem' }}>
                    <h2 style={{ fontSize: '1.3rem', fontWeight: '700', color: 'var(--text-primary)' }}>
                      {selectedScheme.name}
                    </h2>
                    <span className="badge badge-info">{selectedScheme.code}</span>
                  </div>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    Program: {selectedScheme.program_name} ({selectedScheme.program_code})
                  </p>
                </div>
                {canManage && (
                  <button 
                    className="btn btn-secondary" 
                    style={{ fontSize: '0.8rem' }}
                    onClick={() => { setShowMapModal(true); setActionError(''); }}
                  >
                    <Plus size={14} />
                    <span>Map Subject</span>
                  </button>
                )}
              </div>

              {(!selectedScheme.scheme_subjects || selectedScheme.scheme_subjects.length === 0) ? (
                <div style={{ textAlign: 'center', padding: '3rem 1rem', color: 'var(--text-muted)' }}>
                  <Layers size={36} style={{ margin: '0 auto 1rem', opacity: 0.4 }} />
                  <p>No subjects mapped to this scheme yet.</p>
                  <p style={{ fontSize: '0.8rem', marginTop: '0.25rem' }}>
                    {canManage ? 'Click "Map Subject" above to assign courses with credits and passing criteria.' : 'Subjects will appear once mapped by the System Administrator.'}
                  </p>
                </div>
              ) : (
                <div className="data-table-wrapper">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Semester</th>
                        <th>Subject</th>
                        <th>Type</th>
                        <th>Credits</th>
                        <th>Evaluation</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedScheme.scheme_subjects.map((ss) => (
                        <tr key={ss.id}>
                          <td style={{ fontWeight: '700', color: 'var(--primary-100)' }}>
                            Sem {ss.semester_number}
                          </td>
                          <td>
                            <span style={{ fontWeight: '600', color: 'var(--text-primary)' }}>{ss.subject_name}</span>
                            <br />
                            <code style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{ss.subject_code}</code>
                          </td>
                          <td>
                            <span className="badge badge-info" style={{ fontSize: '0.65rem' }}>
                              {ss.subject_type}
                            </span>
                          </td>
                          <td style={{ fontWeight: '600' }}>{ss.credits} Cr</td>
                          <td style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                            Pass: {ss.passing_marks} / {ss.max_marks}
                          </td>
                          <td>
                            {ss.is_locked ? (
                              <span className="badge badge-warning" style={{ fontSize: '0.65rem', display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
                                <Lock size={10} /> Locked
                              </span>
                            ) : (
                              <span className="badge badge-success" style={{ fontSize: '0.65rem' }}>
                                Editable
                              </span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
              Select a scheme on the left to inspect its course mappings.
            </div>
          )}
        </div>
      </div>

      {/* New Scheme Modal */}
      {showSchemeModal && (
        <div className="modal-overlay">
          <div className="modal-content" style={{ padding: '1.75rem' }}>
            <h2 style={{ fontSize: '1.2rem', fontWeight: '700', marginBottom: '1.25rem' }}>
              Create Curriculum Scheme
            </h2>
            {actionError && (
              <p style={{ color: 'var(--danger-text)', background: 'var(--danger-bg)', padding: '0.5rem 0.75rem', borderRadius: 'var(--radius-sm)', marginBottom: '1rem', fontSize: '0.85rem' }}>
                {actionError}
              </p>
            )}
            <form onSubmit={handleCreateScheme}>
              <div className="form-group">
                <label className="form-label">Degree Program</label>
                <select
                  className="form-control"
                  value={schemeForm.program}
                  onChange={(e) => setSchemeForm({ ...schemeForm, program: e.target.value })}
                  required
                >
                  <option value="">Select Program</option>
                  {programs.map((p) => (
                    <option key={p.id} value={p.id}>{p.code} - {p.name}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Effective From Academic Session</label>
                <select
                  className="form-control"
                  value={schemeForm.effective_from_year}
                  onChange={(e) => setSchemeForm({ ...schemeForm, effective_from_year: e.target.value })}
                  required
                >
                  <option value="">Select Academic Year</option>
                  {academicYears.map((ay) => (
                    <option key={ay.id} value={ay.id}>{ay.label}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Scheme Name</label>
                <input
                  type="text"
                  className="form-control"
                  placeholder="2026 Choice Based Credit Scheme"
                  value={schemeForm.name}
                  onChange={(e) => setSchemeForm({ ...schemeForm, name: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Scheme Code</label>
                <input
                  type="text"
                  className="form-control"
                  placeholder="SCHEME-2026-CS"
                  value={schemeForm.code}
                  onChange={(e) => setSchemeForm({ ...schemeForm, code: e.target.value.toUpperCase() })}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Choice Codes to mark on department (optional, comma-separated)</label>
                <input
                  type="text"
                  className="form-control"
                  placeholder="0603624211T, 603624210"
                  value={schemeForm.choice_codes}
                  onChange={(e) => setSchemeForm({ ...schemeForm, choice_codes: e.target.value })}
                />
                <small style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                  Saved onto the selected program's department master (one dept holds many codes).
                </small>
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1.5rem' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setShowSchemeModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Create Scheme</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* New Subject Modal */}
      {showSubjectModal && (
        <div className="modal-overlay">
          <div className="modal-content" style={{ padding: '1.75rem' }}>
            <h2 style={{ fontSize: '1.2rem', fontWeight: '700', marginBottom: '1.25rem' }}>
              Add Course to Subject Catalogue
            </h2>
            {actionError && (
              <p style={{ color: 'var(--danger-text)', background: 'var(--danger-bg)', padding: '0.5rem 0.75rem', borderRadius: 'var(--radius-sm)', marginBottom: '1rem', fontSize: '0.85rem' }}>
                {actionError}
              </p>
            )}
            <form onSubmit={handleCreateSubject}>
              <div className="form-group">
                <label className="form-label">Subject Code (e.g. CS201, MATH101)</label>
                <input
                  type="text"
                  className="form-control"
                  placeholder="CS201"
                  value={subjectForm.code}
                  onChange={(e) => setSubjectForm({ ...subjectForm, code: e.target.value.toUpperCase() })}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Subject Name</label>
                <input
                  type="text"
                  className="form-control"
                  placeholder="Data Structures & Algorithms"
                  value={subjectForm.name}
                  onChange={(e) => setSubjectForm({ ...subjectForm, name: e.target.value })}
                  required
                />
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1.5rem' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setShowSubjectModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Add Subject</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Map Subject to Scheme Modal */}
      {showMapModal && (
        <div className="modal-overlay">
          <div className="modal-content" style={{ padding: '1.75rem' }}>
            <h2 style={{ fontSize: '1.2rem', fontWeight: '700', marginBottom: '1.25rem' }}>
              Map Subject to {selectedScheme?.code}
            </h2>
            {actionError && (
              <p style={{ color: 'var(--danger-text)', background: 'var(--danger-bg)', padding: '0.5rem 0.75rem', borderRadius: 'var(--radius-sm)', marginBottom: '1rem', fontSize: '0.85rem' }}>
                {actionError}
              </p>
            )}
            <form onSubmit={handleMapSubject}>
              <div className="form-group">
                <label className="form-label">Select Subject</label>
                <select
                  className="form-control"
                  value={mapForm.subject}
                  onChange={(e) => setMapForm({ ...mapForm, subject: e.target.value })}
                  required
                >
                  <option value="">Select a subject</option>
                  {subjects.map((s) => (
                    <option key={s.id} value={s.id}>{s.code} - {s.name}</option>
                  ))}
                </select>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="form-group">
                  <label className="form-label">Semester</label>
                  <input
                    type="number"
                    min="1"
                    max="10"
                    className="form-control"
                    value={mapForm.semester_number}
                    onChange={(e) => setMapForm({ ...mapForm, semester_number: parseInt(e.target.value) })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Course Type</label>
                  <select
                    className="form-control"
                    value={mapForm.subject_type}
                    onChange={(e) => setMapForm({ ...mapForm, subject_type: e.target.value })}
                  >
                    <option value="THEORY">Theory</option>
                    <option value="PRACTICAL">Practical</option>
                    <option value="PROJECT">Project</option>
                    <option value="SEMINAR">Seminar</option>
                    <option value="OTHER">Other</option>
                  </select>
                </div>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem' }}>
                <div className="form-group">
                  <label className="form-label">Credits</label>
                  <input
                    type="number"
                    min="1"
                    max="20"
                    className="form-control"
                    value={mapForm.credits}
                    onChange={(e) => setMapForm({ ...mapForm, credits: parseInt(e.target.value) })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Max Marks</label>
                  <input
                    type="number"
                    min="1"
                    className="form-control"
                    value={mapForm.max_marks}
                    onChange={(e) => setMapForm({ ...mapForm, max_marks: parseInt(e.target.value) })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Passing Marks</label>
                  <input
                    type="number"
                    min="0"
                    className="form-control"
                    value={mapForm.passing_marks}
                    onChange={(e) => setMapForm({ ...mapForm, passing_marks: parseInt(e.target.value) })}
                    required
                  />
                </div>
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1.5rem' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setShowMapModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Map Course</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
