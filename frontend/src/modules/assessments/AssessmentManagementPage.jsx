import React, { useState } from 'react';
import { 
  Award, 
  FileSpreadsheet, 
  Upload, 
  CheckCircle2, 
  Lock, 
  Eye, 
  Plus, 
  Search, 
  Filter, 
  AlertTriangle, 
  BookOpen, 
  Calendar, 
  Users, 
  Send,
  X,
  FileText
} from 'lucide-react';

export const AssessmentManagementPage = () => {
  const [activeTab, setActiveTab] = useState('faculty'); // 'faculty' | 'student'
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');

  // Modals state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showViewMarksModal, setShowViewMarksModal] = useState(false);
  const [selectedAssessment, setSelectedAssessment] = useState(null);

  // Form states
  const [createForm, setCreateForm] = useState({
    title: '',
    assessment_type: 'UNIT_TEST_1',
    department: 'Computer Engineering',
    subject: 'CS301 - Data Structures & Algorithms',
    max_marks: '25',
    passing_marks: '10',
    assessment_date: '2024-09-20'
  });

  // Marks upload spreadsheet/grid state
  const [uploadRows, setUploadRows] = useState([
    { enrollment_no: 'ENR2024501', student_name: 'Aarav Patel', marks_obtained: '22.5', is_absent: false, remarks: 'Excellent' },
    { enrollment_no: 'ENR2024601', student_name: 'Neha Kulkarni', marks_obtained: '19.0', is_absent: false, remarks: 'Good' },
    { enrollment_no: 'ENR2024602', student_name: 'Rohan Joshi', marks_obtained: '', is_absent: true, remarks: 'Medical leave' },
    { enrollment_no: 'ENR2024701', student_name: 'Priya Nair', marks_obtained: '24.0', is_absent: false, remarks: 'Top score' },
  ]);

  // Mock assessments state
  const [assessments, setAssessments] = useState([
    {
      id: 'as-1',
      title: 'Unit Test 1 - Data Structures & Algorithms',
      assessment_type_name: 'Unit Test 1',
      assessment_type_code: 'UNIT_TEST_1',
      subject_name: 'Data Structures & Algorithms',
      subject_code: 'CS301',
      department_name: 'Computer Engineering',
      academic_year_label: '2024-25',
      semester_label: 'Semester 3',
      batch_name: 'CE-Batch-A',
      max_marks: 25.0,
      passing_marks: 10.0,
      status: 'PUBLISHED',
      marks_count: 32,
      assessment_date: '2024-09-15',
      marks: [
        { enrollment_no: 'ENR2024501', student_name: 'Aarav Patel', marks_obtained: 22.5, is_absent: false, remarks: 'Excellent' },
        { enrollment_no: 'ENR2024601', student_name: 'Neha Kulkarni', marks_obtained: 19.0, is_absent: false, remarks: 'Good' },
        { enrollment_no: 'ENR2024602', student_name: 'Rohan Joshi', marks_obtained: null, is_absent: true, remarks: 'Medical Leave' },
      ]
    },
    {
      id: 'as-2',
      title: 'Unit Test 1 - Basic Electrical Engineering',
      assessment_type_name: 'Unit Test 1',
      assessment_type_code: 'UNIT_TEST_1',
      subject_name: 'Basic Electrical Engineering',
      subject_code: 'EE101',
      department_name: 'Electronics Engineering',
      academic_year_label: '2024-25',
      semester_label: 'Semester 1',
      batch_name: 'EXTC-Batch-1',
      max_marks: 20.0,
      passing_marks: 8.0,
      status: 'DRAFT',
      marks_count: 4,
      assessment_date: '2024-09-22',
      marks: [
        { enrollment_no: 'ENR2024601', student_name: 'Neha Kulkarni', marks_obtained: 18.5, is_absent: false, remarks: 'Good' },
        { enrollment_no: 'ENR2024602', student_name: 'Rohan Joshi', marks_obtained: null, is_absent: true, remarks: 'Absent' },
      ]
    },
    {
      id: 'as-3',
      title: 'Unit Test 1 - Web Technologies',
      assessment_type_name: 'Unit Test 1',
      assessment_type_code: 'UNIT_TEST_1',
      subject_name: 'Web Technologies',
      subject_code: 'IT501',
      department_name: 'Information Technology',
      academic_year_label: '2024-25',
      semester_label: 'Semester 5',
      batch_name: 'IT-Batch-A',
      max_marks: 25.0,
      passing_marks: 10.0,
      status: 'LOCKED',
      marks_count: 28,
      assessment_date: '2024-08-30',
      marks: [
        { enrollment_no: 'ENR2024701', student_name: 'Priya Nair', marks_obtained: 23.5, is_absent: false, remarks: 'Consistent' }
      ]
    }
  ]);

  // Student portal view state (Aarav Patel)
  const studentMyMarks = [
    {
      id: 'm-1',
      assessment_title: 'Unit Test 1 - Data Structures & Algorithms',
      subject_name: 'Data Structures & Algorithms',
      subject_code: 'CS301',
      academic_year: '2024-25',
      semester: 'Semester 3',
      max_marks: 25.0,
      passing_marks: 10.0,
      marks_obtained: 22.5,
      is_absent: false,
      status: 'PASSED',
      remarks: 'Excellent performance in binary trees'
    },
    {
      id: 'm-2',
      assessment_title: 'Unit Test 1 - Operating Systems',
      subject_name: 'Operating Systems',
      subject_code: 'CS302',
      academic_year: '2024-25',
      semester: 'Semester 3',
      max_marks: 25.0,
      passing_marks: 10.0,
      marks_obtained: 21.5,
      is_absent: false,
      status: 'PASSED',
      remarks: 'Good understanding of processes'
    }
  ];

  // Actions
  const handlePublish = (assessmentId) => {
    setAssessments(assessments.map(a => 
      a.id === assessmentId ? { ...a, status: 'PUBLISHED' } : a
    ));
    alert('Assessment marks published successfully! Students can now view their marks in the student portal.');
  };

  const handleLock = (assessmentId) => {
    setAssessments(assessments.map(a => 
      a.id === assessmentId ? { ...a, status: 'LOCKED' } : a
    ));
    alert('Assessment is now permanently locked. Historical marks cannot be modified.');
  };

  const openUploadModal = (assessment) => {
    setSelectedAssessment(assessment);
    setShowUploadModal(true);
  };

  const openViewMarksModal = (assessment) => {
    setSelectedAssessment(assessment);
    setShowViewMarksModal(true);
  };

  const handleUploadSubmit = (e) => {
    e.preventDefault();
    if (!selectedAssessment) return;

    // Validate rows
    for (const r of uploadRows) {
      if (!r.is_absent && r.marks_obtained !== '') {
        const val = parseFloat(r.marks_obtained);
        if (isNaN(val) || val < 0 || val > selectedAssessment.max_marks) {
          alert(`Marks for student ${r.enrollment_no} must be between 0 and ${selectedAssessment.max_marks}`);
          return;
        }
      }
    }

    setAssessments(assessments.map(a => {
      if (a.id === selectedAssessment.id) {
        return {
          ...a,
          marks_count: uploadRows.length,
          marks: uploadRows.map(r => ({
            enrollment_no: r.enrollment_no,
            student_name: r.student_name,
            marks_obtained: r.is_absent ? null : parseFloat(r.marks_obtained),
            is_absent: r.is_absent,
            remarks: r.remarks
          }))
        };
      }
      return a;
    }));

    setShowUploadModal(false);
    alert(`Successfully extracted, validated, and saved ${uploadRows.length} unit test mark records!`);
  };

  const filteredAssessments = assessments.filter(a => {
    const matchesSearch = 
      a.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      a.subject_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      a.subject_code.toLowerCase().includes(searchQuery.toLowerCase());
    if (!matchesSearch) return false;

    if (statusFilter !== 'ALL' && a.status !== statusFilter) return false;
    return true;
  });

  return (
    <div style={{ padding: '2rem', maxWidth: '1400px', margin: '0 auto' }}>
      {/* Header Banner */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        marginBottom: '2rem',
        flexWrap: 'wrap',
        gap: '1.5rem'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
            <div style={{
              backgroundColor: 'rgba(59, 130, 246, 0.15)',
              color: 'var(--brand-primary)',
              padding: '0.6rem',
              borderRadius: '10px'
            }}>
              <Award size={24} />
            </div>
            <div>
              <h1 style={{ fontSize: '1.75rem', fontWeight: '700', color: 'var(--text-primary)', margin: 0 }}>
                Assessments & Unit Test Marks
              </h1>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', margin: '0.25rem 0 0 0' }}>
                Faculty unit-test mark uploads, validation, scoped student publishing, and lock lifecycle
              </p>
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <button
            onClick={() => setShowCreateModal(true)}
            className="btn btn-primary"
            style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
          >
            <Plus size={18} />
            Create New Assessment
          </button>
        </div>
      </div>

      {/* Role Navigation Toggle */}
      <div style={{
        display: 'flex',
        gap: '1rem',
        borderBottom: '1px solid var(--border-subtle)',
        marginBottom: '1.5rem'
      }}>
        <button
          onClick={() => setActiveTab('faculty')}
          style={{
            padding: '0.75rem 1.25rem',
            background: 'none',
            border: 'none',
            borderBottom: activeTab === 'faculty' ? '2px solid var(--brand-primary)' : '2px solid transparent',
            color: activeTab === 'faculty' ? 'var(--brand-primary)' : 'var(--text-secondary)',
            fontWeight: activeTab === 'faculty' ? '600' : '400',
            cursor: 'pointer',
            fontSize: '0.95rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}
        >
          <BookOpen size={18} />
          Faculty Assessment Workspace ({assessments.length})
        </button>

        <button
          onClick={() => setActiveTab('student')}
          style={{
            padding: '0.75rem 1.25rem',
            background: 'none',
            border: 'none',
            borderBottom: activeTab === 'student' ? '2px solid var(--brand-primary)' : '2px solid transparent',
            color: activeTab === 'student' ? 'var(--brand-primary)' : 'var(--text-secondary)',
            fontWeight: activeTab === 'student' ? '600' : '400',
            cursor: 'pointer',
            fontSize: '0.95rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}
        >
          <Users size={18} />
          Student Portal Preview (Published Marks)
        </button>
      </div>

      {/* TAB 1: Faculty Assessment Workspace */}
      {activeTab === 'faculty' && (
        <div>
          {/* Filters Bar */}
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '1.5rem',
            gap: '1rem',
            flexWrap: 'wrap'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flex: 1, minWidth: '280px' }}>
              <div style={{ position: 'relative', width: '100%' }}>
                <Search size={18} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                <input
                  type="text"
                  className="input"
                  placeholder="Search assessment by title, subject code, or subject name..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  style={{ paddingLeft: '2.5rem', width: '100%' }}
                />
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Status:</span>
              <select
                className="input"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                style={{ minWidth: '140px' }}
              >
                <option value="ALL">All Statuses</option>
                <option value="DRAFT">Draft (Editing)</option>
                <option value="PUBLISHED">Published</option>
                <option value="LOCKED">Locked</option>
              </select>
            </div>
          </div>

          {/* Assessment Cards Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '1.5rem' }}>
            {filteredAssessments.map(as => {
              const isDraft = as.status === 'DRAFT';
              const isPublished = as.status === 'PUBLISHED';
              const isLocked = as.status === 'LOCKED';

              return (
                <div key={as.id} className="card" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div>
                      <span style={{
                        fontSize: '0.75rem',
                        fontWeight: '600',
                        color: 'var(--brand-primary)',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        padding: '0.15rem 0.5rem',
                        borderRadius: '4px',
                        display: 'inline-block',
                        marginBottom: '0.35rem'
                      }}>
                        {as.assessment_type_name}
                      </span>
                      <h3 style={{ margin: '0 0 0.25rem 0', fontSize: '1.15rem', color: 'var(--text-primary)' }}>
                        {as.title}
                      </h3>
                      <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                        {as.subject_code} &bull; {as.subject_name}
                      </div>
                    </div>

                    <span style={{
                      padding: '0.25rem 0.6rem',
                      borderRadius: '20px',
                      fontSize: '0.75rem',
                      fontWeight: '600',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.3rem',
                      backgroundColor: isLocked 
                        ? 'rgba(239, 68, 68, 0.15)' 
                        : isPublished 
                        ? 'rgba(34, 197, 94, 0.15)' 
                        : 'rgba(234, 179, 8, 0.15)',
                      color: isLocked 
                        ? 'var(--danger-text)' 
                        : isPublished 
                        ? 'var(--success-text)' 
                        : 'var(--warning-text)'
                    }}>
                      {isLocked && <Lock size={12} />}
                      {isPublished && <CheckCircle2 size={12} />}
                      {as.status}
                    </span>
                  </div>

                  <div style={{
                    backgroundColor: 'rgba(255,255,255,0.03)',
                    padding: '0.85rem',
                    borderRadius: '8px',
                    display: 'grid',
                    gridTemplateColumns: 'repeat(2, 1fr)',
                    gap: '0.5rem',
                    fontSize: '0.8rem'
                  }}>
                    <div>
                      <span style={{ color: 'var(--text-muted)' }}>Max Marks:</span>
                      <strong style={{ marginLeft: '6px', color: 'var(--text-primary)' }}>{as.max_marks}</strong>
                    </div>
                    <div>
                      <span style={{ color: 'var(--text-muted)' }}>Passing:</span>
                      <strong style={{ marginLeft: '6px', color: 'var(--text-primary)' }}>{as.passing_marks}</strong>
                    </div>
                    <div>
                      <span style={{ color: 'var(--text-muted)' }}>Cohort:</span>
                      <strong style={{ marginLeft: '6px', color: 'var(--text-primary)' }}>{as.batch_name}</strong>
                    </div>
                    <div>
                      <span style={{ color: 'var(--text-muted)' }}>Marks Logged:</span>
                      <strong style={{ marginLeft: '6px', color: 'var(--brand-primary)' }}>{as.marks_count}</strong>
                    </div>
                  </div>

                  <div style={{
                    marginTop: 'auto',
                    borderTop: '1px solid var(--border-subtle)',
                    paddingTop: '1rem',
                    display: 'flex',
                    gap: '0.5rem',
                    justifyContent: 'flex-end',
                    flexWrap: 'wrap'
                  }}>
                    <button
                      onClick={() => openViewMarksModal(as)}
                      className="btn btn-secondary"
                      style={{ padding: '0.4rem 0.75rem', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}
                    >
                      <Eye size={14} /> View Marks
                    </button>

                    {!isLocked && (
                      <button
                        onClick={() => openUploadModal(as)}
                        className="btn btn-secondary"
                        style={{ padding: '0.4rem 0.75rem', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}
                      >
                        <Upload size={14} /> Upload Marks
                      </button>
                    )}

                    {isDraft && (
                      <button
                        onClick={() => handlePublish(as.id)}
                        className="btn btn-primary"
                        style={{ padding: '0.4rem 0.75rem', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}
                      >
                        <Send size={14} /> Publish to Students
                      </button>
                    )}

                    {isPublished && (
                      <button
                        onClick={() => handleLock(as.id)}
                        className="btn btn-secondary"
                        style={{ padding: '0.4rem 0.75rem', fontSize: '0.8rem', color: 'var(--danger-text)', display: 'flex', alignItems: 'center', gap: '0.35rem' }}
                      >
                        <Lock size={14} /> Lock Historical
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* TAB 2: Student Portal Preview */}
      {activeTab === 'student' && (
        <div className="card" style={{ padding: '1.5rem' }}>
          <div style={{ marginBottom: '1.5rem' }}>
            <h3 style={{ margin: '0 0 0.25rem 0', fontSize: '1.2rem', color: 'var(--text-primary)' }}>
              My Assessment & Unit Test Marks
            </h3>
            <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              Student Self-View: Only published and locked assessment marks are visible to enrolled students.
            </p>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table className="table" style={{ width: '100%', textAlign: 'left', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                  <th style={{ padding: '0.75rem 1rem' }}>SUBJECT</th>
                  <th style={{ padding: '0.75rem 1rem' }}>ASSESSMENT</th>
                  <th style={{ padding: '0.75rem 1rem' }}>MAX MARKS</th>
                  <th style={{ padding: '0.75rem 1rem' }}>PASSING</th>
                  <th style={{ padding: '0.75rem 1rem' }}>OBTAINED</th>
                  <th style={{ padding: '0.75rem 1rem' }}>RESULT</th>
                  <th style={{ padding: '0.75rem 1rem' }}>REMARKS</th>
                </tr>
              </thead>
              <tbody>
                {studentMyMarks.map(m => (
                  <tr key={m.id} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                    <td style={{ padding: '1rem' }}>
                      <div style={{ fontWeight: '600', color: 'var(--text-primary)' }}>{m.subject_name}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{m.subject_code} &bull; {m.semester}</div>
                    </td>
                    <td style={{ padding: '1rem', color: 'var(--text-secondary)' }}>
                      {m.assessment_title}
                    </td>
                    <td style={{ padding: '1rem', color: 'var(--text-primary)' }}>
                      {m.max_marks}
                    </td>
                    <td style={{ padding: '1rem', color: 'var(--text-muted)' }}>
                      {m.passing_marks}
                    </td>
                    <td style={{ padding: '1rem', fontSize: '1.1rem', fontWeight: '700', color: 'var(--brand-primary)' }}>
                      {m.is_absent ? 'ABSENT' : m.marks_obtained}
                    </td>
                    <td style={{ padding: '1rem' }}>
                      <span style={{
                        backgroundColor: 'rgba(34, 197, 94, 0.15)',
                        color: 'var(--success-text)',
                        padding: '0.2rem 0.6rem',
                        borderRadius: '4px',
                        fontSize: '0.75rem',
                        fontWeight: '600'
                      }}>
                        {m.status}
                      </span>
                    </td>
                    <td style={{ padding: '1rem', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                      {m.remarks}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* MODAL 1: Upload Unit Test Marks */}
      {showUploadModal && selectedAssessment && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.7)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          padding: '1.5rem'
        }}>
          <div className="card" style={{ maxWidth: '800px', width: '100%', maxHeight: '90vh', overflowY: 'auto', padding: '2rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
              <div>
                <h2 style={{ margin: '0 0 0.25rem 0', color: 'var(--text-primary)', fontSize: '1.3rem' }}>
                  Upload Marks: {selectedAssessment.title}
                </h2>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                  Max Marks: <strong>{selectedAssessment.max_marks}</strong> &bull; Passing Marks: <strong>{selectedAssessment.passing_marks}</strong>
                </span>
              </div>
              <button onClick={() => setShowUploadModal(false)} className="btn btn-secondary" style={{ padding: '0.3rem' }}>
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleUploadSubmit}>
              <div style={{
                backgroundColor: 'rgba(59, 130, 246, 0.08)',
                border: '1px solid rgba(59, 130, 246, 0.2)',
                borderRadius: '8px',
                padding: '0.75rem 1rem',
                marginBottom: '1.25rem',
                fontSize: '0.8rem',
                color: 'var(--text-secondary)'
              }}>
                Enter student marks below or toggle "Absent". Values are validated against max marks ({selectedAssessment.max_marks}) and committed atomically.
              </div>

              <div style={{ overflowX: 'auto', marginBottom: '1.5rem' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-secondary)' }}>
                      <th style={{ padding: '0.5rem', textAlign: 'left' }}>ENROLLMENT NO</th>
                      <th style={{ padding: '0.5rem', textAlign: 'left' }}>STUDENT NAME</th>
                      <th style={{ padding: '0.5rem', textAlign: 'center' }}>ABSENT?</th>
                      <th style={{ padding: '0.5rem', textAlign: 'left' }}>MARKS (MAX {selectedAssessment.max_marks})</th>
                      <th style={{ padding: '0.5rem', textAlign: 'left' }}>REMARKS</th>
                    </tr>
                  </thead>
                  <tbody>
                    {uploadRows.map((row, idx) => (
                      <tr key={idx} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                        <td style={{ padding: '0.5rem', fontFamily: 'monospace' }}>{row.enrollment_no}</td>
                        <td style={{ padding: '0.5rem', fontWeight: '500' }}>{row.student_name}</td>
                        <td style={{ padding: '0.5rem', textAlign: 'center' }}>
                          <input
                            type="checkbox"
                            checked={row.is_absent}
                            onChange={(e) => {
                              const updated = [...uploadRows];
                              updated[idx].is_absent = e.target.checked;
                              if (e.target.checked) updated[idx].marks_obtained = '';
                              setUploadRows(updated);
                            }}
                          />
                        </td>
                        <td style={{ padding: '0.5rem' }}>
                          <input
                            type="number"
                            className="input"
                            disabled={row.is_absent}
                            placeholder={row.is_absent ? 'ABSENT' : 'Marks'}
                            value={row.marks_obtained}
                            step="0.5"
                            min="0"
                            max={selectedAssessment.max_marks}
                            onChange={(e) => {
                              const updated = [...uploadRows];
                              updated[idx].marks_obtained = e.target.value;
                              setUploadRows(updated);
                            }}
                            style={{ width: '100px', padding: '0.3rem 0.5rem' }}
                          />
                        </td>
                        <td style={{ padding: '0.5rem' }}>
                          <input
                            type="text"
                            className="input"
                            value={row.remarks}
                            onChange={(e) => {
                              const updated = [...uploadRows];
                              updated[idx].remarks = e.target.value;
                              setUploadRows(updated);
                            }}
                            placeholder="Optional remark"
                            style={{ width: '100%', padding: '0.3rem 0.5rem' }}
                          />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
                <button
                  type="button"
                  onClick={() => setShowUploadModal(false)}
                  className="btn btn-secondary"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
                >
                  <CheckCircle2 size={16} /> Validate & Save Marks
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 2: View Marks Details */}
      {showViewMarksModal && selectedAssessment && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.7)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          padding: '1.5rem'
        }}>
          <div className="card" style={{ maxWidth: '750px', width: '100%', maxHeight: '90vh', overflowY: 'auto', padding: '2rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.25rem' }}>
              <div>
                <h2 style={{ margin: '0 0 0.25rem 0', color: 'var(--text-primary)', fontSize: '1.3rem' }}>
                  Recorded Marks: {selectedAssessment.title}
                </h2>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                  Subject: {selectedAssessment.subject_code} &bull; Max Marks: {selectedAssessment.max_marks}
                </span>
              </div>
              <button onClick={() => setShowViewMarksModal(false)} className="btn btn-secondary" style={{ padding: '0.3rem' }}>
                <X size={18} />
              </button>
            </div>

            <div style={{ overflowX: 'auto', marginBottom: '1.5rem' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-secondary)' }}>
                    <th style={{ padding: '0.6rem 0.75rem', textAlign: 'left' }}>STUDENT</th>
                    <th style={{ padding: '0.6rem 0.75rem', textAlign: 'left' }}>ENROLLMENT</th>
                    <th style={{ padding: '0.6rem 0.75rem', textAlign: 'left' }}>MARKS OBTAINED</th>
                    <th style={{ padding: '0.6rem 0.75rem', textAlign: 'left' }}>STATUS</th>
                    <th style={{ padding: '0.6rem 0.75rem', textAlign: 'left' }}>REMARKS</th>
                  </tr>
                </thead>
                <tbody>
                  {selectedAssessment.marks.map((m, i) => (
                    <tr key={i} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                      <td style={{ padding: '0.6rem 0.75rem', fontWeight: '500' }}>{m.student_name}</td>
                      <td style={{ padding: '0.6rem 0.75rem', fontFamily: 'monospace' }}>{m.enrollment_no}</td>
                      <td style={{ padding: '0.6rem 0.75rem', fontWeight: '700', color: m.is_absent ? 'var(--danger-text)' : 'var(--brand-primary)' }}>
                        {m.is_absent ? 'ABSENT' : `${m.marks_obtained} / ${selectedAssessment.max_marks}`}
                      </td>
                      <td style={{ padding: '0.6rem 0.75rem' }}>
                        <span style={{
                          backgroundColor: m.is_absent 
                            ? 'rgba(239, 68, 68, 0.15)' 
                            : (m.marks_obtained >= selectedAssessment.passing_marks ? 'rgba(34, 197, 94, 0.15)' : 'rgba(239, 68, 68, 0.15)'),
                          color: m.is_absent 
                            ? 'var(--danger-text)' 
                            : (m.marks_obtained >= selectedAssessment.passing_marks ? 'var(--success-text)' : 'var(--danger-text)'),
                          padding: '0.15rem 0.5rem',
                          borderRadius: '4px',
                          fontSize: '0.75rem',
                          fontWeight: '600'
                        }}>
                          {m.is_absent ? 'ABSENT' : (m.marks_obtained >= selectedAssessment.passing_marks ? 'PASS' : 'FAIL')}
                        </span>
                      </td>
                      <td style={{ padding: '0.6rem 0.75rem', color: 'var(--text-muted)' }}>{m.remarks || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setShowViewMarksModal(false)}
                className="btn btn-secondary"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL 3: Create Assessment Definition */}
      {showCreateModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.7)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          padding: '1.5rem'
        }}>
          <div className="card" style={{ maxWidth: '540px', width: '100%', padding: '2rem' }}>
            <h2 style={{ margin: '0 0 0.5rem 0', color: 'var(--text-primary)', fontSize: '1.3rem' }}>
              Create Assessment Definition
            </h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '1.25rem' }}>
              Define a new unit test or in-semester assessment tied to academic curriculum and faculty assignment.
            </p>

            <form onSubmit={(e) => {
              e.preventDefault();
              const newAssessment = {
                id: `as-${Date.now()}`,
                title: createForm.title,
                assessment_type_name: 'Unit Test 1',
                assessment_type_code: 'UNIT_TEST_1',
                subject_name: createForm.subject.split(' - ')[1] || 'Subject',
                subject_code: createForm.subject.split(' - ')[0] || 'SUB',
                department_name: createForm.department,
                academic_year_label: '2024-25',
                semester_label: 'Semester 3',
                batch_name: 'CE-Batch-A',
                max_marks: parseFloat(createForm.max_marks),
                passing_marks: parseFloat(createForm.passing_marks),
                status: 'DRAFT',
                marks_count: 0,
                assessment_date: createForm.assessment_date,
                marks: []
              };
              setAssessments([newAssessment, ...assessments]);
              setShowCreateModal(false);
              alert('Assessment created in DRAFT status! Faculty can now upload marks.');
            }} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
                  Assessment Title: *
                </label>
                <input
                  type="text"
                  className="input"
                  required
                  placeholder="e.g. Unit Test 1 - Computer Networks"
                  value={createForm.title}
                  onChange={(e) => setCreateForm({ ...createForm, title: e.target.value })}
                  style={{ width: '100%' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
                  Assessment Type:
                </label>
                <select className="input" style={{ width: '100%' }}>
                  <option value="UNIT_TEST_1">Unit Test 1</option>
                  <option value="UNIT_TEST_2">Unit Test 2</option>
                  <option value="ASSIGNMENT">Continuous Assignment</option>
                  <option value="PRACTICAL">Practical Continuous Evaluation</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
                  Subject / Curriculum Mapping: *
                </label>
                <select className="input" style={{ width: '100%' }}>
                  <option value="CS301">CS301 - Data Structures & Algorithms</option>
                  <option value="CS302">CS302 - Operating Systems</option>
                  <option value="EE101">EE101 - Basic Electrical Engineering</option>
                  <option value="IT501">IT501 - Web Technologies</option>
                </select>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
                    Max Marks: *
                  </label>
                  <input
                    type="number"
                    className="input"
                    required
                    value={createForm.max_marks}
                    onChange={(e) => setCreateForm({ ...createForm, max_marks: e.target.value })}
                    style={{ width: '100%' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
                    Passing Marks: *
                  </label>
                  <input
                    type="number"
                    className="input"
                    required
                    value={createForm.passing_marks}
                    onChange={(e) => setCreateForm({ ...createForm, passing_marks: e.target.value })}
                    style={{ width: '100%' }}
                  />
                </div>
              </div>

              <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end', marginTop: '0.5rem' }}>
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="btn btn-secondary"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                >
                  Create Assessment
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
export default AssessmentManagementPage;
