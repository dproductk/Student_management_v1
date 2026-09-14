import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  GraduationCap, 
  ArrowLeft, 
  Building2, 
  BookOpen, 
  Award, 
  Calendar, 
  Clock, 
  Users, 
  Plus, 
  Archive, 
  FileText, 
  CheckCircle2, 
  AlertCircle,
  ExternalLink,
  X
} from 'lucide-react';
import api from '../../services/api';

export const FacultyDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [faculty, setFaculty] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview'); // 'overview', 'assignments', 'portfolio', 'students'
  
  // Assignment modal & state
  const [academicYears, setAcademicYears] = useState([]);
  const [semesters, setSemesters] = useState([]);
  const [batches, setBatches] = useState([]);
  const [schemeSubjects, setSchemeSubjects] = useState([]);
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [assignForm, setAssignForm] = useState({
    academic_year: '',
    semester: '',
    scheme_subject: '',
    batch: '',
    role: 'PRIMARY_INSTRUCTOR',
    remarks: ''
  });
  const [assignSubmitting, setAssignSubmitting] = useState(false);
  const [assignError, setAssignError] = useState('');

  // Academic item modal & state
  const [showItemModal, setShowItemModal] = useState(false);
  const [itemCategoryFilter, setItemCategoryFilter] = useState('ALL');
  const [itemForm, setItemForm] = useState({
    item_type: 'PUBLICATION',
    title: '',
    year: new Date().getFullYear(),
    reference_url: '',
    meta_field_1: '', // Journal / Publisher / Granting Body
    meta_field_2: '', // DOI / ISBN / Patent Number / Degree
  });
  const [itemSubmitting, setItemSubmitting] = useState(false);
  const [itemError, setItemError] = useState('');

  // Status transition modal
  const [showStatusModal, setShowStatusModal] = useState(false);
  const [newStatus, setNewStatus] = useState('ACTIVE');
  const [relievingDate, setRelievingDate] = useState('');

  // Scoped students
  const [scopedStudents, setScopedStudents] = useState([]);
  const [loadingStudents, setLoadingStudents] = useState(false);

  const fetchFacultyDetail = async () => {
    try {
      setLoading(true);
      const res = await api.get(`/faculty/members/${id}/`);
      setFaculty(res.data);
      setNewStatus(res.data.status);
    } catch (err) {
      console.error('Failed to load faculty detail', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchAcademicData = async () => {
    try {
      const [ayRes, batchRes, subjRes] = await Promise.all([
        api.get('/academic/academic-years/'),
        api.get('/academic/batches/'),
        api.get('/academic/scheme-subjects/')
      ]);
      const ays = Array.isArray(ayRes.data) ? ayRes.data : (ayRes.data?.results || []);
      const batchesData = Array.isArray(batchRes.data) ? batchRes.data : (batchRes.data?.results || []);
      const subjectsData = Array.isArray(subjRes.data) ? subjRes.data : (subjRes.data?.results || []);

      setAcademicYears(ays);
      setBatches(batchesData);
      setSchemeSubjects(subjectsData);

      if (ays.length > 0) {
        const curAy = ays.find(y => y.is_current) || ays[0];
        setAssignForm(prev => ({ ...prev, academic_year: curAy.id }));
        // Load semesters for this AY
        const semRes = await api.get(`/academic/semesters/?academic_year=${curAy.id}`);
        const sems = Array.isArray(semRes.data) ? semRes.data : (semRes.data?.results || []);
        setSemesters(sems);
        if (sems.length > 0) {
          setAssignForm(prev => ({ ...prev, semester: sems[0].id }));
        }
      }
      if (subjectsData.length > 0) {
        setAssignForm(prev => ({ ...prev, scheme_subject: subjectsData[0].id }));
      }
    } catch (err) {
      console.error('Failed to load academic data', err);
    }
  };

  const fetchScopedStudents = async () => {
    try {
      setLoadingStudents(true);
      const res = await api.get('/faculty/scoped-students/');
      const stdData = Array.isArray(res.data) ? res.data : (res.data?.results || []);
      setScopedStudents(stdData);
    } catch (err) {
      console.error('Failed to load scoped students', err);
      setScopedStudents([]);
    } finally {
      setLoadingStudents(false);
    }
  };

  useEffect(() => {
    fetchFacultyDetail();
    fetchAcademicData();
  }, [id]);

  useEffect(() => {
    if (activeTab === 'students') {
      fetchScopedStudents();
    }
  }, [activeTab]);

  const handleYearChange = async (yearId) => {
    setAssignForm(prev => ({ ...prev, academic_year: yearId, semester: '' }));
    try {
      const res = await api.get(`/academic/semesters/?academic_year=${yearId}`);
      const sems = Array.isArray(res.data) ? res.data : (res.data?.results || []);
      setSemesters(sems);
      if (sems.length > 0) {
        setAssignForm(prev => ({ ...prev, semester: sems[0].id }));
      }
    } catch (err) {
      console.error('Failed to load semesters for academic year', err);
      setSemesters([]);
    }
  };

  const handleCreateAssignment = async (e) => {
    e.preventDefault();
    setAssignError('');
    setAssignSubmitting(true);
    try {
      const payload = {
        faculty: id,
        academic_year: assignForm.academic_year,
        semester: assignForm.semester,
        scheme_subject: assignForm.scheme_subject,
        batch: assignForm.batch || null,
        role: assignForm.role,
        remarks: assignForm.remarks
      };
      await api.post('/faculty/assignments/', payload);
      setShowAssignModal(false);
      fetchFacultyDetail();
    } catch (err) {
      setAssignError(err.response?.data?.detail || 'Failed to create assignment.');
    } finally {
      setAssignSubmitting(false);
    }
  };

  const handleRetireAssignment = async (assignmentId) => {
    if (!window.confirm('Retire this teaching assignment? It will be archived historically.')) return;
    try {
      await api.post(`/faculty/assignments/${assignmentId}/retire/`, {
        end_date: new Date().toISOString().split('T')[0]
      });
      fetchFacultyDetail();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to retire assignment.');
    }
  };

  const handleCreateAcademicItem = async (e) => {
    e.preventDefault();
    setItemError('');
    setItemSubmitting(true);
    try {
      const details = {};
      if (itemForm.item_type === 'PUBLICATION') {
        details.journal = itemForm.meta_field_1;
        details.doi = itemForm.meta_field_2;
      } else if (itemForm.item_type === 'PATENT') {
        details.patent_number = itemForm.meta_field_1;
        details.status = itemForm.meta_field_2 || 'GRANTED';
      } else if (itemForm.item_type === 'BOOK') {
        details.publisher = itemForm.meta_field_1;
        details.isbn = itemForm.meta_field_2;
      } else if (itemForm.item_type === 'AWARD') {
        details.awarding_body = itemForm.meta_field_1;
      } else if (itemForm.item_type === 'MEMBERSHIP') {
        details.organization = itemForm.meta_field_1;
        details.membership_id = itemForm.meta_field_2;
      } else if (itemForm.item_type === 'CONSULTANCY') {
        details.client = itemForm.meta_field_1;
        details.grant_amount = itemForm.meta_field_2;
      } else if (itemForm.item_type === 'GUIDANCE') {
        details.degree = itemForm.meta_field_1;
        details.student_name = itemForm.meta_field_2;
      }

      await api.post(`/faculty/members/${id}/academic-items/`, {
        item_type: itemForm.item_type,
        title: itemForm.title,
        year: itemForm.year ? parseInt(itemForm.year, 10) : null,
        reference_url: itemForm.reference_url,
        details
      });
      setShowItemModal(false);
      setItemForm({
        item_type: 'PUBLICATION',
        title: '',
        year: new Date().getFullYear(),
        reference_url: '',
        meta_field_1: '',
        meta_field_2: '',
      });
      fetchFacultyDetail();
    } catch (err) {
      setItemError(err.response?.data?.detail || 'Failed to add academic item.');
    } finally {
      setItemSubmitting(false);
    }
  };

  const handleTransitionStatus = async (e) => {
    e.preventDefault();
    try {
      await api.post(`/faculty/members/${id}/transition-status/`, {
        status: newStatus,
        relieving_date: relievingDate || null
      });
      setShowStatusModal(false);
      fetchFacultyDetail();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to update faculty status.');
    }
  };

  if (loading) {
    return (
      <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--edvana-text-muted)' }}>
        Loading faculty details...
      </div>
    );
  }

  if (!faculty) {
    return (
      <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--edvana-text-muted)' }}>
        Faculty record not found.
      </div>
    );
  }

  const activeAssignments = (faculty.assignments || []).filter(a => a.is_active);
  const historicalAssignments = (faculty.assignments || []).filter(a => !a.is_active);

  const filteredPortfolio = (faculty.academic_items || []).filter(item => {
    if (itemCategoryFilter === 'ALL') return true;
    return item.item_type === itemCategoryFilter;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>

      {/* Header Info Bar */}
      <div className="edvana-card" style={{ padding: '1.25rem 1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
          <span style={{ fontWeight: '600', fontSize: '1rem', color: 'var(--edvana-text-primary)' }}>
            {faculty.full_name}
          </span>
          {faculty.is_hod && (
            <span className="edvana-badge edvana-badge-brand">HOD</span>
          )}
          <span style={{ color: 'var(--edvana-text-muted)', fontSize: '0.85rem' }}>•</span>
          <span style={{ fontSize: '0.85rem', color: 'var(--edvana-text-secondary)' }}>{faculty.designation}</span>
          <span className="edvana-badge edvana-badge-info">{faculty.department_code}</span>
          <span style={{ fontFamily: 'var(--edvana-font-mono)', fontSize: '0.8rem', color: 'var(--edvana-text-muted)' }}>ID: {faculty.faculty_id}</span>
        </div>

        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <span className={`edvana-badge ${faculty.status === 'ACTIVE' ? 'edvana-badge-success' : 'edvana-badge-warning'}`}>
            {faculty.status}
          </span>
          <button 
            onClick={() => setShowStatusModal(true)}
            className="edvana-btn edvana-btn-ghost"
            style={{ fontSize: '0.8rem', padding: '0.35rem 0.75rem' }}
          >
            Change Status
          </button>
        </div>
      </div>

      {/* EDVANA Horizontal Tabs — underline style */}
      <div className="edvana-card" style={{ padding: 0, overflow: 'visible', marginBottom: 0 }}>
        <div style={{ display: 'flex', borderBottom: '2px solid var(--edvana-border)', overflowX: 'auto' }}>
          {[
            { key: 'overview', label: 'Profile Information', icon: Building2 },
            { key: 'assignments', label: 'Teaching Assignments', icon: BookOpen },
            { key: 'portfolio', label: 'Academic Portfolio', icon: Award },
            { key: 'students', label: 'Scoped Students', icon: Users },
          ].map(tab => {
            const TabIcon = tab.icon;
            const isActive = activeTab === tab.key;
            return (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.85rem 1.25rem',
                  fontSize: '0.85rem',
                  fontWeight: isActive ? '600' : '500',
                  color: isActive ? '#2563eb' : 'var(--edvana-text-muted)',
                  background: 'transparent',
                  border: 'none',
                  borderBottom: isActive ? '2px solid #2563eb' : '2px solid transparent',
                  marginBottom: '-2px',
                  cursor: 'pointer',
                  whiteSpace: 'nowrap',
                  transition: 'all 0.15s ease',
                }}
              >
                <TabIcon size={16} />
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Tab 1: Overview & Organizational Info */}
      {activeTab === 'overview' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.25rem' }}>
          <div className="edvana-card" style={{ padding: '1.5rem' }}>
            <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.1rem', fontWeight: '600', color: 'var(--edvana-text-primary)' }}>
              Organizational Information
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem', fontSize: '0.9rem' }}>
              <div>
                <span style={{ color: 'var(--edvana-text-secondary)', display: 'block', fontSize: '0.75rem', textTransform: 'uppercase' }}>Department</span>
                <span style={{ fontWeight: '500' }}>{faculty.department_code} - {faculty.department_name}</span>
              </div>
              <div>
                <span style={{ color: 'var(--edvana-text-secondary)', display: 'block', fontSize: '0.75rem', textTransform: 'uppercase' }}>Cabin / Office</span>
                <span style={{ fontWeight: '500' }}>{faculty.cabin_number || 'Not Assigned'}</span>
              </div>
              <div>
                <span style={{ color: 'var(--edvana-text-secondary)', display: 'block', fontSize: '0.75rem', textTransform: 'uppercase' }}>Official Contact Email</span>
                <span style={{ fontWeight: '500' }}>{faculty.contact_email || faculty.email}</span>
              </div>
              <div>
                <span style={{ color: 'var(--edvana-text-secondary)', display: 'block', fontSize: '0.75rem', textTransform: 'uppercase' }}>Administrative Responsibilities</span>
                <span style={{ fontWeight: '500' }}>{faculty.responsibilities || 'None recorded'}</span>
              </div>
            </div>
          </div>

          <div className="edvana-card" style={{ padding: '1.5rem' }}>
            <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.1rem', fontWeight: '600', color: 'var(--edvana-text-primary)' }}>
              Faculty Lifecycle & Credentials
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem', fontSize: '0.9rem' }}>
              <div>
                <span style={{ color: 'var(--edvana-text-secondary)', display: 'block', fontSize: '0.75rem', textTransform: 'uppercase' }}>Employment Type</span>
                <span style={{ fontWeight: '500' }}>{faculty.employment_type}</span>
              </div>
              <div>
                <span style={{ color: 'var(--edvana-text-secondary)', display: 'block', fontSize: '0.75rem', textTransform: 'uppercase' }}>Date of Joining</span>
                <span style={{ fontWeight: '500' }}>{faculty.date_of_joining}</span>
              </div>
              {faculty.date_of_relieving && (
                <div>
                  <span style={{ color: 'var(--edvana-text-secondary)', display: 'block', fontSize: '0.75rem', textTransform: 'uppercase' }}>Date of Relieving</span>
                  <span style={{ fontWeight: '500', color: 'var(--edvana-danger)' }}>{faculty.date_of_relieving}</span>
                </div>
              )}
              <div>
                <span style={{ color: 'var(--edvana-text-secondary)', display: 'block', fontSize: '0.75rem', textTransform: 'uppercase' }}>Highest Qualification</span>
                <span style={{ fontWeight: '500' }}>{faculty.qualification || 'Not Recorded'}</span>
              </div>
              <div>
                <span style={{ color: 'var(--edvana-text-secondary)', display: 'block', fontSize: '0.75rem', textTransform: 'uppercase' }}>Specialization Area</span>
                <span style={{ fontWeight: '500' }}>{faculty.specialization || 'Not Recorded'}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Teaching & Subject Assignments */}
      {activeTab === 'assignments' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h3 style={{ margin: 0, fontSize: '1.15rem', fontWeight: '600' }}>Active Teaching Assignments</h3>
              <p style={{ margin: '0.2rem 0 0 0', fontSize: '0.85rem', color: 'var(--edvana-text-secondary)' }}>
                Teaching subjects, batch allocations, and pedagogical responsibilities for current terms.
              </p>
            </div>
            <button 
              onClick={() => setShowAssignModal(true)}
              className="edvana-btn edvana-btn-primary"
              style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}
            >
              <Plus size={16} /> Assign Subject / Batch
            </button>
          </div>

          {/* Active Assignments Table */}
          <div className="edvana-card" style={{ overflow: 'hidden' }}>
            {activeAssignments.length === 0 ? (
              <div style={{ padding: '2.5rem', textAlign: 'center', color: 'var(--edvana-text-muted)' }}>
                No active teaching assignments currently allocated.
              </div>
            ) : (
              <div className="edvana-table-container">
                <table className="edvana-table">
                  <thead>
                    <tr>
                      <th>Subject</th>
                      <th>Academic Term</th>
                      <th>Batch</th>
                      <th>Teaching Role</th>
                      <th>Start Date</th>
                      <th style={{ textAlign: 'right' }}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {activeAssignments.map(a => (
                      <tr key={a.id}>
                        <td>
                          <div style={{ display: 'flex', flexDirection: 'column' }}>
                            <span style={{ fontWeight: '600' }}>{a.subject_name}</span>
                            <span style={{ fontSize: '0.75rem', color: 'var(--edvana-text-muted)', fontFamily: 'var(--edvana-font-mono)' }}>
                              Code: {a.subject_code}
                            </span>
                          </div>
                        </td>
                        <td>
                          <span className="edvana-badge edvana-badge-info">
                            {a.academic_year_label} • {a.semester_label}
                          </span>
                        </td>
                        <td>
                          {a.batch_name ? (
                            <span style={{ fontWeight: '500' }}>Batch {a.batch_name}</span>
                          ) : (
                            <span style={{ color: 'var(--edvana-text-muted)' }}>Entire Class</span>
                          )}
                        </td>
                        <td>
                          <span className="edvana-badge edvana-badge-brand">
                            {a.role_display}
                          </span>
                        </td>
                        <td style={{ fontSize: '0.85rem', color: 'var(--edvana-text-secondary)' }}>
                          {a.effective_start_date || 'Current'}
                        </td>
                        <td style={{ textAlign: 'right' }}>
                          <button 
                            onClick={() => handleRetireAssignment(a.id)}
                            className="edvana-btn edvana-btn-ghost"
                            style={{ padding: '0.35rem 0.5rem', color: 'var(--edvana-danger)' }}
                            title="Retire Assignment"
                          >
                            <Archive size={16} /> Archive
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Historical Assignments Section */}
          {historicalAssignments.length > 0 && (
            <div style={{ marginTop: '1rem' }}>
              <h3 style={{ margin: '0 0 0.75rem 0', fontSize: '1.05rem', fontWeight: '600', color: 'var(--edvana-text-secondary)' }}>
                Historical Teaching Archive ({historicalAssignments.length})
              </h3>
              <div className="edvana-card" style={{ overflow: 'hidden' }}>
                <div className="edvana-table-container">
                  <table className="edvana-table">
                    <thead>
                      <tr>
                        <th>Subject</th>
                        <th>Academic Term</th>
                        <th>Batch</th>
                        <th>Teaching Role</th>
                        <th>Period</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {historicalAssignments.map(a => (
                        <tr key={a.id} style={{ opacity: 0.85 }}>
                          <td>
                            <div style={{ display: 'flex', flexDirection: 'column' }}>
                              <span style={{ fontWeight: '500' }}>{a.subject_name}</span>
                              <span style={{ fontSize: '0.75rem', color: 'var(--edvana-text-muted)' }}>{a.subject_code}</span>
                            </div>
                          </td>
                          <td>{a.academic_year_label} • {a.semester_label}</td>
                          <td>{a.batch_name || 'All'}</td>
                          <td>{a.role_display}</td>
                          <td style={{ fontSize: '0.8rem', color: 'var(--edvana-text-muted)' }}>
                            {a.effective_start_date} to {a.effective_end_date || 'End of Term'}
                          </td>
                          <td>
                            <span className="edvana-badge">Archived</span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tab 3: Academic Portfolio */}
      {activeTab === 'portfolio' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
            <div>
              <h3 style={{ margin: 0, fontSize: '1.15rem', fontWeight: '600' }}>Academic Portfolio & Research</h3>
              <p style={{ margin: '0.2rem 0 0 0', fontSize: '0.85rem', color: 'var(--edvana-text-secondary)' }}>
                Publications, patents, books, awards, professional memberships, consultancy, and guidance records.
              </p>
            </div>
            <button 
              onClick={() => setShowItemModal(true)}
              className="edvana-btn edvana-btn-primary"
              style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}
            >
              <Plus size={16} /> Add Portfolio Item
            </button>
          </div>

          {/* Category Filter Pills */}
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            {['ALL', 'PUBLICATION', 'PATENT', 'BOOK', 'AWARD', 'MEMBERSHIP', 'CONSULTANCY', 'GUIDANCE'].map(cat => (
              <button
                key={cat}
                onClick={() => setItemCategoryFilter(cat)}
                className={`edvana-btn ${itemCategoryFilter === cat ? 'edvana-btn-primary' : 'edvana-btn-ghost'}`}
                style={{ fontSize: '0.8rem', padding: '0.35rem 0.75rem' }}
              >
                {cat === 'ALL' ? 'All Activities' : cat}
              </button>
            ))}
          </div>

          {/* Portfolio Grid */}
          {filteredPortfolio.length === 0 ? (
            <div className="edvana-card" style={{ padding: '3rem', textAlign: 'center', color: 'var(--edvana-text-muted)' }}>
              No portfolio items found in this category.
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '1rem' }}>
              {filteredPortfolio.map(item => (
                <div key={item.id} className="edvana-card" style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                      <span className="edvana-badge edvana-badge-brand" style={{ fontSize: '0.7rem' }}>
                        {item.item_type}
                      </span>
                      {item.year && (
                        <span style={{ fontSize: '0.8rem', fontWeight: '600', color: 'var(--edvana-text-muted)' }}>
                          {item.year}
                        </span>
                      )}
                    </div>
                    <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '1rem', fontWeight: '600', color: 'var(--edvana-text-primary)' }}>
                      {item.title}
                    </h4>

                    {/* Meta Details */}
                    <div style={{ fontSize: '0.85rem', color: 'var(--edvana-text-secondary)', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                      {Object.entries(item.details || {}).map(([k, v]) => (
                        <div key={k} style={{ textTransform: 'capitalize' }}>
                          <span style={{ color: 'var(--edvana-text-muted)' }}>{k.replace('_', ' ')}: </span>
                          <span style={{ fontWeight: '500' }}>{String(v)}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {item.reference_url && (
                    <div style={{ marginTop: '1rem', paddingTop: '0.75rem', borderTop: '1px solid var(--edvana-border)' }}>
                      <a 
                        href={item.reference_url} 
                        target="_blank" 
                        rel="noreferrer"
                        style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.8rem', color: 'var(--edvana-brand)', textDecoration: 'none' }}
                      >
                        <ExternalLink size={14} /> View Reference / DOI
                      </a>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tab 4: Scoped Students View */}
      {activeTab === 'students' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <div>
            <h3 style={{ margin: 0, fontSize: '1.15rem', fontWeight: '600' }}>Scoped Student Directory</h3>
            <p style={{ margin: '0.2rem 0 0 0', fontSize: '0.85rem', color: 'var(--edvana-text-secondary)' }}>
              Server-side verified student visibility governed by authorized academic assignments and roles.
            </p>
          </div>

          <div className="edvana-card" style={{ overflow: 'hidden' }}>
            {loadingStudents ? (
              <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--edvana-text-muted)' }}>
                Evaluating backend scoped permissions and retrieving authorized student records...
              </div>
            ) : scopedStudents.length === 0 ? (
              <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--edvana-text-muted)' }}>
                No students currently in your authorized academic scope.
              </div>
            ) : (
              <div className="edvana-table-container">
                <table className="edvana-table">
                  <thead>
                    <tr>
                      <th>Student Candidate</th>
                      <th>Enrollment No</th>
                      <th>Department</th>
                      <th>Batch</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {scopedStudents.map(student => (
                      <tr key={student.id}>
                        <td style={{ fontWeight: '600' }}>{student.candidate_name}</td>
                        <td style={{ fontFamily: 'var(--edvana-font-mono)' }}>{student.enrollment_no || 'Pending'}</td>
                        <td>{student.current_department || 'N/A'}</td>
                        <td>{student.current_batch || 'N/A'}</td>
                        <td>
                          <span className="edvana-badge edvana-badge-success">{student.status}</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Modal: Assign Subject / Batch */}
      {showAssignModal && (
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
          <div className="edvana-card" style={{ width: '100%', maxWidth: '560px', padding: '1.75rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
              <h2 style={{ margin: 0, fontSize: '1.25rem', fontWeight: '700' }}>Assign Subject & Batch</h2>
              <button onClick={() => setShowAssignModal(false)} className="edvana-btn edvana-btn-ghost" style={{ padding: '0.35rem' }}>
                <X size={18} />
              </button>
            </div>

            {assignError && (
              <div style={{ padding: '0.75rem', background: 'var(--edvana-danger-soft)', border: '1px solid var(--edvana-danger-border)', borderRadius: 'var(--edvana-radius-md)', color: 'var(--edvana-danger)', marginBottom: '1rem', fontSize: '0.85rem' }}>
                {assignError}
              </div>
            )}

            <form onSubmit={handleCreateAssignment} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label className="edvana-label">Academic Year *</label>
                <select 
                  required
                  className="edvana-input"
                  value={assignForm.academic_year}
                  onChange={(e) => handleYearChange(e.target.value)}
                >
                  {academicYears.map(y => (
                    <option key={y.id} value={y.id}>{y.label} {y.is_current ? '(Current)' : ''}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="edvana-label">Semester *</label>
                <select 
                  required
                  className="edvana-input"
                  value={assignForm.semester}
                  onChange={(e) => setAssignForm({ ...assignForm, semester: e.target.value })}
                >
                  {semesters.map(s => (
                    <option key={s.id} value={s.id}>{s.label || `Semester ${s.number}`}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="edvana-label">Scheme Subject *</label>
                <select 
                  required
                  className="edvana-input"
                  value={assignForm.scheme_subject}
                  onChange={(e) => setAssignForm({ ...assignForm, scheme_subject: e.target.value })}
                >
                  {schemeSubjects.map(ss => (
                    <option key={ss.id} value={ss.id}>
                      {ss.subject?.code} - {ss.subject?.name} (Sem {ss.semester_number})
                    </option>
                  ))}
                </select>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <label className="edvana-label">Batch (Optional)</label>
                  <select 
                    className="edvana-input"
                    value={assignForm.batch}
                    onChange={(e) => setAssignForm({ ...assignForm, batch: e.target.value })}
                  >
                    <option value="">All Batches</option>
                    {batches.map(b => (
                      <option key={b.id} value={b.id}>{b.department_code || ''} {b.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="edvana-label">Teaching Role *</label>
                  <select 
                    className="edvana-input"
                    value={assignForm.role}
                    onChange={(e) => setAssignForm({ ...assignForm, role: e.target.value })}
                  >
                    <option value="PRIMARY_INSTRUCTOR">Primary Instructor</option>
                    <option value="CO_INSTRUCTOR">Co-Instructor</option>
                    <option value="LAB_INSTRUCTOR">Lab Instructor</option>
                    <option value="CLASS_TEACHER">Class Teacher / Mentor</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="edvana-label">Remarks / Description</label>
                <input 
                  type="text" 
                  className="edvana-input"
                  placeholder="e.g. Course Coordinator, Theory Lectures"
                  value={assignForm.remarks}
                  onChange={(e) => setAssignForm({ ...assignForm, remarks: e.target.value })}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '0.5rem' }}>
                <button type="button" onClick={() => setShowAssignModal(false)} className="edvana-btn edvana-btn-ghost">
                  Cancel
                </button>
                <button type="submit" disabled={assignSubmitting} className="edvana-btn edvana-btn-primary">
                  {assignSubmitting ? 'Assigning...' : 'Confirm Assignment'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Add Academic Portfolio Item */}
      {showItemModal && (
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
          <div className="edvana-card" style={{ width: '100%', maxWidth: '560px', padding: '1.75rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
              <h2 style={{ margin: 0, fontSize: '1.25rem', fontWeight: '700' }}>Add Portfolio Item</h2>
              <button onClick={() => setShowItemModal(false)} className="edvana-btn edvana-btn-ghost" style={{ padding: '0.35rem' }}>
                <X size={18} />
              </button>
            </div>

            {itemError && (
              <div style={{ padding: '0.75rem', background: 'var(--edvana-danger-soft)', border: '1px solid var(--edvana-danger-border)', borderRadius: 'var(--edvana-radius-md)', color: 'var(--edvana-danger)', marginBottom: '1rem', fontSize: '0.85rem' }}>
                {itemError}
              </div>
            )}

            <form onSubmit={handleCreateAcademicItem} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <label className="edvana-label">Category *</label>
                  <select 
                    className="edvana-input"
                    value={itemForm.item_type}
                    onChange={(e) => setItemForm({ ...itemForm, item_type: e.target.value })}
                  >
                    <option value="PUBLICATION">Publication</option>
                    <option value="PATENT">Patent</option>
                    <option value="BOOK">Book / Chapter</option>
                    <option value="AWARD">Award / Honor</option>
                    <option value="MEMBERSHIP">Membership</option>
                    <option value="CONSULTANCY">Consultancy</option>
                    <option value="GUIDANCE">Research Guidance</option>
                  </select>
                </div>
                <div>
                  <label className="edvana-label">Year</label>
                  <input 
                    type="number" 
                    className="edvana-input"
                    value={itemForm.year}
                    onChange={(e) => setItemForm({ ...itemForm, year: e.target.value })}
                  />
                </div>
              </div>

              <div>
                <label className="edvana-label">Title / Description *</label>
                <input 
                  type="text" 
                  required
                  className="edvana-input"
                  placeholder="e.g. Paper title, Patent name, or Award title"
                  value={itemForm.title}
                  onChange={(e) => setItemForm({ ...itemForm, title: e.target.value })}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <label className="edvana-label">
                    {itemForm.item_type === 'PUBLICATION' ? 'Journal / Conference' :
                     itemForm.item_type === 'PATENT' ? 'Patent Application No.' :
                     itemForm.item_type === 'BOOK' ? 'Publisher' :
                     itemForm.item_type === 'AWARD' ? 'Awarding Body' :
                     itemForm.item_type === 'MEMBERSHIP' ? 'Organization' :
                     itemForm.item_type === 'CONSULTANCY' ? 'Client / Sponsor' : 'Degree / Program'}
                  </label>
                  <input 
                    type="text" 
                    className="edvana-input"
                    value={itemForm.meta_field_1}
                    onChange={(e) => setItemForm({ ...itemForm, meta_field_1: e.target.value })}
                  />
                </div>
                <div>
                  <label className="edvana-label">
                    {itemForm.item_type === 'PUBLICATION' ? 'DOI / Volume' :
                     itemForm.item_type === 'PATENT' ? 'Status (Granted/Filed)' :
                     itemForm.item_type === 'BOOK' ? 'ISBN' :
                     itemForm.item_type === 'MEMBERSHIP' ? 'Membership ID' :
                     itemForm.item_type === 'CONSULTANCY' ? 'Grant Amount' : 'Candidate Name / Details'}
                  </label>
                  <input 
                    type="text" 
                    className="edvana-input"
                    value={itemForm.meta_field_2}
                    onChange={(e) => setItemForm({ ...itemForm, meta_field_2: e.target.value })}
                  />
                </div>
              </div>

              <div>
                <label className="edvana-label">Reference URL (Optional)</label>
                <input 
                  type="url" 
                  className="edvana-input"
                  placeholder="https://doi.org/... or https://..."
                  value={itemForm.reference_url}
                  onChange={(e) => setItemForm({ ...itemForm, reference_url: e.target.value })}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '0.5rem' }}>
                <button type="button" onClick={() => setShowItemModal(false)} className="edvana-btn edvana-btn-ghost">
                  Cancel
                </button>
                <button type="submit" disabled={itemSubmitting} className="edvana-btn edvana-btn-primary">
                  {itemSubmitting ? 'Saving...' : 'Add Item'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Change Status */}
      {showStatusModal && (
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
          <div className="edvana-card" style={{ width: '100%', maxWidth: '440px', padding: '1.5rem' }}>
            <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.2rem', fontWeight: '700' }}>Update Faculty Status</h3>
            <form onSubmit={handleTransitionStatus} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label className="edvana-label">New Status</label>
                <select 
                  className="edvana-input"
                  value={newStatus}
                  onChange={(e) => setNewStatus(e.target.value)}
                >
                  <option value="ACTIVE">Active</option>
                  <option value="ON_LEAVE">On Leave</option>
                  <option value="RESIGNED">Resigned</option>
                  <option value="RETIRED">Retired</option>
                  <option value="TERMINATED">Terminated</option>
                </select>
              </div>

              {['RESIGNED', 'RETIRED', 'TERMINATED'].includes(newStatus) && (
                <div>
                  <label className="edvana-label">Relieving Date *</label>
                  <input 
                    type="date"
                    required
                    className="edvana-input"
                    value={relievingDate}
                    onChange={(e) => setRelievingDate(e.target.value)}
                  />
                </div>
              )}

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '0.5rem' }}>
                <button type="button" onClick={() => setShowStatusModal(false)} className="edvana-btn edvana-btn-ghost">
                  Cancel
                </button>
                <button type="submit" className="edvana-btn edvana-btn-primary">
                  Update Status
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
