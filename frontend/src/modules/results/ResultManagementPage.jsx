import React, { useState } from 'react';
import { 
  FileSpreadsheet, 
  Upload, 
  CheckCircle2, 
  Clock, 
  AlertCircle, 
  ShieldCheck, 
  Search, 
  Eye, 
  FileText, 
  RefreshCw, 
  Send, 
  ArrowRight, 
  Sparkles, 
  ChevronRight, 
  X, 
  Check, 
  BookOpen, 
  Calendar, 
  Building2, 
  GraduationCap, 
  Layers, 
  Award,
  AlertTriangle,
  History
} from 'lucide-react';

import { EligibilityDashboard } from './EligibilityDashboard';
import { useAuth } from '../../context/AuthContext';

export const ResultManagementPage = () => {
  const { user, hasRole } = useAuth();
  const isSysAdmin = hasRole('SYSTEM_ADMIN') || user?.is_superuser;
  const isExamCell = hasRole('EXAM_CELL');
  const isCollegeAdmin = hasRole('COLLEGE_ADMIN');
  const canUpload = isSysAdmin || isExamCell;

  const [activeTab, setActiveTab] = useState(isCollegeAdmin ? 'results' : 'batches'); // 'batches' | 'results' | 'corrections' | 'eligibility' | 'student_portal'
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');

  // Modals state
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showRowsModal, setShowRowsModal] = useState(false);
  const [showMarksheetModal, setShowMarksheetModal] = useState(false);
  const [showCorrectionModal, setShowCorrectionModal] = useState(false);
  const [selectedBatch, setSelectedBatch] = useState(null);
  const [selectedResult, setSelectedResult] = useState(null);

  // Upload form state
  const [uploadForm, setUploadForm] = useState({
    academic_year: '2024-2025',
    semester: 'Semester 4',
    department: 'Computer Engineering',
    program: 'B.Tech Computer Engineering',
    file_name: 'sem4_final_results.csv',
    remarks: 'Annual examination results upload',
    csv_content: `student_identifier,subject_code,internal_marks,external_marks\nENR2024401,CS401,36,52\nENR2024401,CS402,34,50\nENR2024402,CS401,38,56\nENR2024402,CS402,35,48\nENR2024403,CS401,25,30\nENR2024403,CS402,12,20`
  });

  // Correction form state
  const [correctionForm, setCorrectionForm] = useState({
    reason: '',
    subject_code: 'CS401',
    new_external_marks: '45'
  });

  // Mock Batches
  const [batches, setBatches] = useState([
    {
      id: 'batch-101',
      file_name: 'ce_sem4_results_gazette.csv',
      academic_year: '2024-2025',
      semester: 'Semester 4',
      department: 'Computer Engineering',
      program: 'B.Tech Computer Engineering',
      status: 'PUBLISHED',
      total_rows: 4,
      valid_rows: 4,
      error_rows: 0,
      uploaded_by: 'exam_controller',
      uploaded_at: '2026-09-04 10:30',
      approved_by: 'dean_academics',
      approved_at: '2026-09-04 14:15',
      published_by: 'dean_academics',
      published_at: '2026-09-04 15:00',
      rows: [
        { row_num: 1, identifier: 'ENR2024401', student_name: 'Rohan Sharma', subject: 'CS401', internal: 36, external: 52, total: 88, grade: 'A+', status: 'VALID' },
        { row_num: 2, identifier: 'ENR2024401', student_name: 'Rohan Sharma', subject: 'CS402', internal: 34, external: 50, total: 84, grade: 'A+', status: 'VALID' },
        { row_num: 3, identifier: 'ENR2024402', student_name: 'Priya Patel', subject: 'CS401', internal: 38, external: 56, total: 94, grade: 'O', status: 'VALID' },
        { row_num: 4, identifier: 'ENR2024402', student_name: 'Priya Patel', subject: 'CS402', internal: 35, external: 48, total: 83, grade: 'A+', status: 'VALID' },
      ]
    },
    {
      id: 'batch-102',
      file_name: 'me_sem3_provisional.csv',
      academic_year: '2024-2025',
      semester: 'Semester 3',
      department: 'Mechanical Engineering',
      program: 'B.Tech Mechanical',
      status: 'VALIDATED',
      total_rows: 2,
      valid_rows: 2,
      error_rows: 0,
      uploaded_by: 'faculty_user',
      uploaded_at: '2026-09-06 09:10',
      approved_by: null,
      published_by: null,
      rows: [
        { row_num: 1, identifier: 'ENR2024301', student_name: 'Aakash Verma', subject: 'ME301', internal: 36, external: 54, total: 90, grade: 'O', status: 'VALID' },
        { row_num: 2, identifier: 'ENR2024302', student_name: 'Siddharth Rao', subject: 'ME301', internal: 30, external: 45, total: 75, grade: 'A', status: 'VALID' },
      ]
    },
    {
      id: 'batch-103',
      file_name: 'ee_sem6_upload_draft.csv',
      academic_year: '2024-2025',
      semester: 'Semester 6',
      department: 'Electrical Engineering',
      program: 'B.Tech Electrical',
      status: 'PROCESSING',
      total_rows: 3,
      valid_rows: 0,
      error_rows: 0,
      uploaded_by: 'controller',
      uploaded_at: '2026-09-07 04:45',
      approved_by: null,
      published_by: null,
      rows: [
        { row_num: 1, identifier: 'ENR2024601', student_name: 'Vikram Malhotra', subject: 'EE601', internal: 35, external: 50, total: 85, grade: 'A+', status: 'PENDING' },
      ]
    }
  ]);

  // Mock Published Results
  const [results, setResults] = useState([
    {
      id: 'res-001',
      student_name: 'Rohan Sharma',
      enrollment_no: 'ENR2024401',
      department: 'Computer Engineering',
      program: 'B.Tech Computer Engineering',
      academic_year: '2024-2025',
      semester: 'Semester 4',
      version: 1,
      is_latest: true,
      status: 'PUBLISHED',
      total_marks_obtained: 172.0,
      total_max_marks: 200.0,
      percentage: 86.0,
      sgpa: 9.0,
      result_status: 'PASS',
      published_at: '2026-09-04 15:00',
      details: [
        { subject_code: 'CS401', subject_name: 'Data Structures & Algorithms', internal: 36, external: 52, total: 88, max: 100, grade: 'A+', points: 9.0, credits: 4, status: 'PASS' },
        { subject_code: 'CS402', subject_name: 'Computer Networks', internal: 34, external: 50, total: 84, max: 100, grade: 'A+', points: 9.0, credits: 4, status: 'PASS' },
      ]
    },
    {
      id: 'res-002',
      student_name: 'Priya Patel',
      enrollment_no: 'ENR2024402',
      department: 'Computer Engineering',
      program: 'B.Tech Computer Engineering',
      academic_year: '2024-2025',
      semester: 'Semester 4',
      version: 1,
      is_latest: true,
      status: 'PUBLISHED',
      total_marks_obtained: 177.0,
      total_max_marks: 200.0,
      percentage: 88.5,
      sgpa: 9.5,
      result_status: 'PASS',
      published_at: '2026-09-04 15:00',
      details: [
        { subject_code: 'CS401', subject_name: 'Data Structures & Algorithms', internal: 38, external: 56, total: 94, max: 100, grade: 'O', points: 10.0, credits: 4, status: 'PASS' },
        { subject_code: 'CS402', subject_name: 'Computer Networks', internal: 35, external: 48, total: 83, max: 100, grade: 'A+', points: 9.0, credits: 4, status: 'PASS' },
      ]
    },
    {
      id: 'res-003-v1',
      student_name: 'Neha Singh',
      enrollment_no: 'ENR2024501',
      department: 'Civil Engineering',
      program: 'B.Tech Civil',
      academic_year: '2024-2025',
      semester: 'Semester 5',
      version: 1,
      is_latest: false,
      status: 'SUPERSEDED',
      total_marks_obtained: 55.0,
      total_max_marks: 100.0,
      percentage: 55.0,
      sgpa: 6.0,
      result_status: 'PASS',
      published_at: '2026-08-20 11:00',
      details: [
        { subject_code: 'CE501', subject_name: 'Structural Analysis', internal: 35, external: 20, total: 55, max: 100, grade: 'B', points: 6.0, credits: 4, status: 'PASS' },
      ]
    },
    {
      id: 'res-003-v2',
      student_name: 'Neha Singh',
      enrollment_no: 'ENR2024501',
      department: 'Civil Engineering',
      program: 'B.Tech Civil',
      academic_year: '2024-2025',
      semester: 'Semester 5',
      version: 2,
      is_latest: true,
      status: 'PUBLISHED',
      total_marks_obtained: 80.0,
      total_max_marks: 100.0,
      percentage: 80.0,
      sgpa: 9.0,
      result_status: 'PASS',
      published_at: '2026-09-02 16:30',
      details: [
        { subject_code: 'CE501', subject_name: 'Structural Analysis', internal: 35, external: 45, total: 80, max: 100, grade: 'A+', points: 9.0, credits: 4, status: 'PASS' },
      ]
    }
  ]);

  // Mock Correction Requests
  const [corrections, setCorrections] = useState([
    {
      id: 'corr-01',
      student_name: 'Neha Singh',
      enrollment_no: 'ENR2024501',
      target_version: 1,
      reason: 'Official university revaluation answer-sheet verification: external marks corrected to 45.',
      status: 'APPROVED',
      requested_by: 'faculty_user',
      reviewed_by: 'dean_academics',
      reviewed_at: '2026-09-02 16:30',
      review_remarks: 'Approved as per university revaluation gazette.',
      superseding_version: 2
    }
  ]);

  // Handlers
  const handleCreateBatch = (e) => {
    e.preventDefault();
    const newBatch = {
      id: `batch-${Date.now().toString().slice(-4)}`,
      file_name: uploadForm.file_name,
      academic_year: uploadForm.academic_year,
      semester: uploadForm.semester,
      department: uploadForm.department,
      program: uploadForm.program,
      status: 'PROCESSING',
      total_rows: 3,
      valid_rows: 0,
      error_rows: 0,
      uploaded_by: 'exam_controller',
      uploaded_at: new Date().toISOString().replace('T', ' ').slice(0, 16),
      approved_by: null,
      published_by: null,
      rows: [
        { row_num: 1, identifier: 'ENR2024401', student_name: 'Rohan Sharma', subject: 'CS401', internal: 36, external: 52, total: 88, grade: 'A+', status: 'PENDING' },
        { row_num: 2, identifier: 'ENR2024401', student_name: 'Rohan Sharma', subject: 'CS402', internal: 34, external: 50, total: 84, grade: 'A+', status: 'PENDING' },
        { row_num: 3, identifier: 'ENR2024402', student_name: 'Priya Patel', subject: 'CS401', internal: 38, external: 56, total: 94, grade: 'O', status: 'PENDING' },
      ]
    };
    setBatches([newBatch, ...batches]);
    setShowUploadModal(false);
  };

  const handleValidateBatch = (batchId) => {
    setBatches(batches.map(b => {
      if (b.id === batchId) {
        return {
          ...b,
          status: 'VALIDATED',
          valid_rows: b.total_rows,
          error_rows: 0,
          rows: b.rows.map(r => ({ ...r, status: 'VALID' }))
        };
      }
      return b;
    }));
  };

  const handleApproveBatch = (batchId) => {
    setBatches(batches.map(b => {
      if (b.id === batchId) {
        return {
          ...b,
          status: 'APPROVED',
          approved_by: 'dean_academics',
          approved_at: new Date().toISOString().replace('T', ' ').slice(0, 16)
        };
      }
      return b;
    }));
  };

  const handlePublishBatch = (batchId) => {
    setBatches(batches.map(b => {
      if (b.id === batchId) {
        return {
          ...b,
          status: 'PUBLISHED',
          published_by: 'dean_academics',
          published_at: new Date().toISOString().replace('T', ' ').slice(0, 16)
        };
      }
      return b;
    }));
  };

  const handleRequestCorrection = (e) => {
    e.preventDefault();
    if (!selectedResult || !correctionForm.reason.trim()) return;

    const newCorr = {
      id: `corr-${Date.now().toString().slice(-4)}`,
      student_name: selectedResult.student_name,
      enrollment_no: selectedResult.enrollment_no,
      target_version: selectedResult.version,
      reason: correctionForm.reason.trim(),
      status: 'PENDING',
      requested_by: 'exam_controller',
      reviewed_by: null,
      reviewed_at: null,
      review_remarks: '',
      proposed: {
        subject_code: correctionForm.subject_code,
        new_external_marks: correctionForm.new_external_marks
      }
    };
    setCorrections([newCorr, ...corrections]);
    setShowCorrectionModal(false);
    setCorrectionForm({ reason: '', subject_code: 'CS401', new_external_marks: '45' });
  };

  const handleApproveCorrection = (corrId) => {
    setCorrections(corrections.map(c => {
      if (c.id === corrId) {
        // Supersede V1 and spawn V2
        const targetRes = results.find(r => r.enrollment_no === c.enrollment_no && r.is_latest);
        if (targetRes) {
          const v2Res = {
            ...targetRes,
            id: `${targetRes.id}-v${targetRes.version + 1}`,
            version: targetRes.version + 1,
            is_latest: true,
            status: 'PUBLISHED',
            total_marks_obtained: targetRes.total_marks_obtained + 15,
            percentage: Math.min(100, targetRes.percentage + 7.5),
            sgpa: Math.min(10, targetRes.sgpa + 0.5),
            published_at: new Date().toISOString().replace('T', ' ').slice(0, 16)
          };

          // Mark previous as superseded
          setResults(results.map(r => {
            if (r.id === targetRes.id) {
              return { ...r, is_latest: false, status: 'SUPERSEDED' };
            }
            return r;
          }).concat(v2Res));
        }

        return {
          ...c,
          status: 'APPROVED',
          reviewed_by: 'dean_academics',
          reviewed_at: new Date().toISOString().replace('T', ' ').slice(0, 16),
          review_remarks: 'Approved by academic council; Result V2 published.'
        };
      }
      return c;
    }));
  };

  // Filtered results
  const filteredResults = results.filter(r => {
    const matchesSearch = r.student_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          r.enrollment_no.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          r.program.toLowerCase().includes(searchQuery.toLowerCase());
    if (statusFilter === 'ALL') return matchesSearch;
    if (statusFilter === 'LATEST') return matchesSearch && r.is_latest;
    if (statusFilter === 'SUPERSEDED') return matchesSearch && r.status === 'SUPERSEDED';
    return matchesSearch && r.status === statusFilter;
  });

  return (
    <div style={{ padding: '2rem', maxWidth: '1400px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      
      {/* Page Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
            <div style={{
              width: '42px',
              height: '42px',
              borderRadius: 'var(--radius-lg)',
              backgroundColor: 'rgba(99, 102, 241, 0.12)',
              color: 'var(--primary-600)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <Award size={24} />
            </div>
            <h1 style={{ fontSize: '1.75rem', fontWeight: '700', color: 'var(--text-primary)', letterSpacing: '-0.02em', margin: 0 }}>
              Academic Results & Gazette Management
            </h1>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', margin: 0 }}>
            Controlled ingestion, multi-stage approval, immutable published gazettes & versioned supersession (ADR-016).
          </p>
        </div>

        {canUpload && (
          <button
            onClick={() => setShowUploadModal(true)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              backgroundColor: 'var(--primary-600)',
              color: '#ffffff',
              border: 'none',
              borderRadius: 'var(--radius-md)',
              padding: '0.7rem 1.25rem',
              fontSize: '0.9rem',
              fontWeight: '600',
              cursor: 'pointer',
              boxShadow: 'var(--shadow-sm)',
              transition: 'all var(--transition-fast)'
            }}
          >
            <Upload size={18} />
            <span>Upload Results CSV / Gazette</span>
          </button>
        )}
        {isCollegeAdmin && (
          <span className="badge badge-primary" style={{ padding: '0.5rem 0.85rem', fontSize: '0.85rem' }}>
            Academic Performance & Eligibility Overview
          </span>
        )}
      </div>

      {/* Metrics Strip */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
        gap: '1.25rem'
      }}>
        {isCollegeAdmin ? (
          <>
            <div style={{
              backgroundColor: 'var(--bg-surface)',
              padding: '1.25rem',
              borderRadius: 'var(--radius-lg)',
              border: '1px solid var(--border-subtle)',
              boxShadow: 'var(--shadow-sm)'
            }}>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: '600', textTransform: 'uppercase' }}>Total Assessed</span>
              <div style={{ fontSize: '1.85rem', fontWeight: '700', color: 'var(--text-primary)', marginTop: '0.35rem' }}>
                {results.length}
              </div>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '0.3rem', marginTop: '0.35rem' }}>
                <GraduationCap size={14} /> Total evaluated candidates
              </span>
            </div>

            <div style={{
              backgroundColor: 'var(--bg-surface)',
              padding: '1.25rem',
              borderRadius: 'var(--radius-lg)',
              border: '1px solid var(--border-subtle)',
              boxShadow: 'var(--shadow-sm)'
            }}>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: '600', textTransform: 'uppercase' }}>Passed Students</span>
              <div style={{ fontSize: '1.85rem', fontWeight: '700', color: '#10b981', marginTop: '0.35rem' }}>
                {results.filter(r => r.result_status === 'PASS').length}
              </div>
              <span style={{ fontSize: '0.8rem', color: '#10b981', display: 'flex', alignItems: 'center', gap: '0.3rem', marginTop: '0.35rem' }}>
                <CheckCircle2 size={14} /> {results.length > 0 ? `${((results.filter(r => r.result_status === 'PASS').length / results.length) * 100).toFixed(1)}% Pass Rate` : '0%'}
              </span>
            </div>

            <div style={{
              backgroundColor: 'var(--bg-surface)',
              padding: '1.25rem',
              borderRadius: 'var(--radius-lg)',
              border: '1px solid var(--border-subtle)',
              boxShadow: 'var(--shadow-sm)'
            }}>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: '600', textTransform: 'uppercase' }}>Eligible for Progression</span>
              <div style={{ fontSize: '1.85rem', fontWeight: '700', color: 'var(--primary-600)', marginTop: '0.35rem' }}>
                {results.filter(r => (r.sgpa || 0) >= 5.0 && r.result_status !== 'FAIL').length}
              </div>
              <span style={{ fontSize: '0.8rem', color: 'var(--primary-600)', display: 'flex', alignItems: 'center', gap: '0.3rem', marginTop: '0.35rem' }}>
                <Sparkles size={14} /> Satisfies credit progression criteria
              </span>
            </div>

            <div style={{
              backgroundColor: 'var(--bg-surface)',
              padding: '1.25rem',
              borderRadius: 'var(--radius-lg)',
              border: '1px solid var(--border-subtle)',
              boxShadow: 'var(--shadow-sm)'
            }}>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: '600', textTransform: 'uppercase' }}>Failed / Backlogs</span>
              <div style={{ fontSize: '1.85rem', fontWeight: '700', color: '#ef4444', marginTop: '0.35rem' }}>
                {results.filter(r => r.result_status === 'FAIL').length}
              </div>
              <span style={{ fontSize: '0.8rem', color: '#ef4444', display: 'flex', alignItems: 'center', gap: '0.3rem', marginTop: '0.35rem' }}>
                <AlertTriangle size={14} /> Remedial / ATKT candidates
              </span>
            </div>
          </>
        ) : (
          <>
            <div style={{
              backgroundColor: 'var(--bg-surface)',
              padding: '1.25rem',
              borderRadius: 'var(--radius-lg)',
              border: '1px solid var(--border-subtle)',
              boxShadow: 'var(--shadow-sm)'
            }}>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: '600', textTransform: 'uppercase' }}>Published Records</span>
              <div style={{ fontSize: '1.85rem', fontWeight: '700', color: 'var(--text-primary)', marginTop: '0.35rem' }}>
                {results.filter(r => r.status === 'PUBLISHED' && r.is_latest).length}
              </div>
              <span style={{ fontSize: '0.8rem', color: '#10b981', display: 'flex', alignItems: 'center', gap: '0.3rem', marginTop: '0.35rem' }}>
                <CheckCircle2 size={14} /> Immutable historical evidence
              </span>
            </div>

            <div style={{
              backgroundColor: 'var(--bg-surface)',
              padding: '1.25rem',
              borderRadius: 'var(--radius-lg)',
              border: '1px solid var(--border-subtle)',
              boxShadow: 'var(--shadow-sm)'
            }}>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: '600', textTransform: 'uppercase' }}>Ingestion Batches</span>
              <div style={{ fontSize: '1.85rem', fontWeight: '700', color: 'var(--text-primary)', marginTop: '0.35rem' }}>
                {batches.length}
              </div>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '0.3rem', marginTop: '0.35rem' }}>
                <FileSpreadsheet size={14} /> Controlled staging pipelines
              </span>
            </div>

            <div style={{
              backgroundColor: 'var(--bg-surface)',
              padding: '1.25rem',
              borderRadius: 'var(--radius-lg)',
              border: '1px solid var(--border-subtle)',
              boxShadow: 'var(--shadow-sm)'
            }}>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: '600', textTransform: 'uppercase' }}>Awaiting Approval</span>
              <div style={{ fontSize: '1.85rem', fontWeight: '700', color: '#f59e0b', marginTop: '0.35rem' }}>
                {batches.filter(b => b.status === 'VALIDATED').length}
              </div>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '0.3rem', marginTop: '0.35rem' }}>
                <Clock size={14} /> Require authorized Dean approval
              </span>
            </div>

            <div style={{
              backgroundColor: 'var(--bg-surface)',
              padding: '1.25rem',
              borderRadius: 'var(--radius-lg)',
              border: '1px solid var(--border-subtle)',
              boxShadow: 'var(--shadow-sm)'
            }}>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: '600', textTransform: 'uppercase' }}>Superseded (V2) Revisions</span>
              <div style={{ fontSize: '1.85rem', fontWeight: '700', color: '#6366f1', marginTop: '0.35rem' }}>
                {results.filter(r => r.version > 1).length}
              </div>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '0.3rem', marginTop: '0.35rem' }}>
                <History size={14} /> ADR-016 Additive corrections
              </span>
            </div>
          </>
        )}
      </div>

      {/* Main Navigation Tabs */}
      <div style={{
        display: 'flex',
        borderBottom: '1px solid var(--border-subtle)',
        gap: '2rem'
      }}>
        {[
          { id: 'batches', label: 'Import Batches & Lifecycle', icon: FileSpreadsheet },
          { id: 'results', label: 'Official Published Results', icon: Award },
          { id: 'corrections', label: 'Correction & Supersession (ADR-016)', icon: ShieldCheck },
          { id: 'eligibility', label: 'Credits & Eligibility (ADR-028)', icon: Sparkles },
          { id: 'student_portal', label: 'Student Portal Preview', icon: Eye }
        ].map(tab => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.6rem',
                padding: '0.85rem 0.25rem',
                border: 'none',
                backgroundColor: 'transparent',
                borderBottom: isActive ? '2px solid var(--primary-600)' : '2px solid transparent',
                color: isActive ? 'var(--primary-600)' : 'var(--text-secondary)',
                fontWeight: isActive ? '600' : '500',
                fontSize: '0.95rem',
                cursor: 'pointer',
                transition: 'all var(--transition-fast)'
              }}
            >
              <Icon size={18} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* TAB 1: BATCHES & INGESTION */}
      {activeTab === 'batches' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: '600', color: 'var(--text-primary)', margin: 0 }}>
              Batch Ingestion & State Machine Pipeline
            </h2>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              Flow: <strong>PENDING &rarr; PROCESSING &rarr; VALIDATED &rarr; APPROVED &rarr; PUBLISHED</strong>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {batches.map(batch => {
              const statusColors = {
                PENDING: { bg: 'rgba(156, 163, 175, 0.15)', text: '#6b7280', border: '#d1d5db' },
                PROCESSING: { bg: 'rgba(59, 130, 246, 0.15)', text: '#2563eb', border: '#93c5fd' },
                VALIDATED: { bg: 'rgba(245, 158, 11, 0.15)', text: '#d97706', border: '#fcd34d' },
                APPROVED: { bg: 'rgba(16, 185, 129, 0.15)', text: '#059669', border: '#6ee7b7' },
                PUBLISHED: { bg: 'rgba(99, 102, 241, 0.15)', text: '#4f46e5', border: '#a5b4fc' },
                FAILED: { bg: 'rgba(239, 68, 68, 0.15)', text: '#dc2626', border: '#fca5a5' }
              };
              const c = statusColors[batch.status] || statusColors.PENDING;

              return (
                <div
                  key={batch.id}
                  style={{
                    backgroundColor: 'var(--bg-surface)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-lg)',
                    padding: '1.5rem',
                    boxShadow: 'var(--shadow-sm)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '1.25rem'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                      <div style={{
                        width: '44px',
                        height: '44px',
                        borderRadius: 'var(--radius-md)',
                        backgroundColor: 'rgba(99, 102, 241, 0.1)',
                        color: 'var(--primary-600)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                      }}>
                        <FileSpreadsheet size={22} />
                      </div>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                          <span style={{ fontSize: '1.1rem', fontWeight: '700', color: 'var(--text-primary)' }}>
                            {batch.file_name}
                          </span>
                          <span style={{
                            padding: '0.2rem 0.65rem',
                            borderRadius: '9999px',
                            fontSize: '0.75rem',
                            fontWeight: '600',
                            backgroundColor: c.bg,
                            color: c.text,
                            border: `1px solid ${c.border}`
                          }}>
                            {batch.status}
                          </span>
                        </div>
                        <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                          {batch.department} &bull; {batch.program} &bull; {batch.semester} ({batch.academic_year})
                        </div>
                      </div>
                    </div>

                    {/* Action buttons based on lifecycle state */}
                    <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                      <button
                        onClick={() => {
                          setSelectedBatch(batch);
                          setShowRowsModal(true);
                        }}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.4rem',
                          backgroundColor: 'transparent',
                          color: 'var(--text-secondary)',
                          border: '1px solid var(--border-subtle)',
                          borderRadius: 'var(--radius-md)',
                          padding: '0.5rem 0.85rem',
                          fontSize: '0.85rem',
                          fontWeight: '500',
                          cursor: 'pointer'
                        }}
                      >
                        <Eye size={16} />
                        <span>Inspect Rows ({batch.total_rows})</span>
                      </button>

                      {batch.status === 'PROCESSING' && (
                        <button
                          onClick={() => handleValidateBatch(batch.id)}
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.4rem',
                            backgroundColor: 'var(--primary-600)',
                            color: '#ffffff',
                            border: 'none',
                            borderRadius: 'var(--radius-md)',
                            padding: '0.5rem 0.85rem',
                            fontSize: '0.85rem',
                            fontWeight: '600',
                            cursor: 'pointer'
                          }}
                        >
                          <CheckCircle2 size={16} />
                          <span>Run Validation</span>
                        </button>
                      )}

                      {batch.status === 'VALIDATED' && (
                        <button
                          onClick={() => handleApproveBatch(batch.id)}
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.4rem',
                            backgroundColor: '#059669',
                            color: '#ffffff',
                            border: 'none',
                            borderRadius: 'var(--radius-md)',
                            padding: '0.5rem 0.85rem',
                            fontSize: '0.85rem',
                            fontWeight: '600',
                            cursor: 'pointer'
                          }}
                        >
                          <ShieldCheck size={16} />
                          <span>Approve Batch</span>
                        </button>
                      )}

                      {batch.status === 'APPROVED' && (
                        <button
                          onClick={() => handlePublishBatch(batch.id)}
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.4rem',
                            backgroundColor: '#4f46e5',
                            color: '#ffffff',
                            border: 'none',
                            borderRadius: 'var(--radius-md)',
                            padding: '0.5rem 0.85rem',
                            fontSize: '0.85rem',
                            fontWeight: '600',
                            cursor: 'pointer'
                          }}
                        >
                          <Send size={16} />
                          <span>Publish Official Gazette</span>
                        </button>
                      )}

                      {batch.status === 'PUBLISHED' && (
                        <span style={{ fontSize: '0.8rem', color: '#059669', display: 'flex', alignItems: 'center', gap: '0.3rem', fontWeight: '500' }}>
                          <Check size={16} /> Published to Students
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Audit Trail Metadata */}
                  <div style={{
                    display: 'flex',
                    gap: '2rem',
                    flexWrap: 'wrap',
                    paddingTop: '0.85rem',
                    borderTop: '1px solid var(--border-subtle)',
                    fontSize: '0.8rem',
                    color: 'var(--text-muted)'
                  }}>
                    <div>Uploaded by: <strong style={{ color: 'var(--text-secondary)' }}>{batch.uploaded_by}</strong> on {batch.uploaded_at}</div>
                    {batch.approved_by && (
                      <div>Approved by: <strong style={{ color: 'var(--text-secondary)' }}>{batch.approved_by}</strong> on {batch.approved_at}</div>
                    )}
                    {batch.published_by && (
                      <div>Published by: <strong style={{ color: 'var(--text-secondary)' }}>{batch.published_by}</strong> on {batch.published_at}</div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* TAB 2: OFFICIAL PUBLISHED RESULTS */}
      {activeTab === 'results' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          
          {/* Controls & Filter */}
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem', flexWrap: 'wrap' }}>
            <div style={{
              position: 'relative',
              flex: '1',
              minWidth: '280px'
            }}>
              <Search size={18} style={{ position: 'absolute', left: '0.85rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
              <input
                type="text"
                placeholder="Search student by name, enrollment number, program..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.65rem 0.85rem 0.65rem 2.4rem',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-subtle)',
                  backgroundColor: 'var(--bg-surface)',
                  color: 'var(--text-primary)',
                  fontSize: '0.9rem',
                  outline: 'none'
                }}
              />
            </div>

            <div style={{ display: 'flex', gap: '0.5rem' }}>
              {['ALL', 'LATEST', 'SUPERSEDED'].map(f => (
                <button
                  key={f}
                  onClick={() => setStatusFilter(f)}
                  style={{
                    padding: '0.55rem 0.95rem',
                    borderRadius: 'var(--radius-md)',
                    fontSize: '0.85rem',
                    fontWeight: statusFilter === f ? '600' : '500',
                    border: '1px solid var(--border-subtle)',
                    backgroundColor: statusFilter === f ? 'var(--primary-600)' : 'var(--bg-surface)',
                    color: statusFilter === f ? '#ffffff' : 'var(--text-secondary)',
                    cursor: 'pointer'
                  }}
                >
                  {f === 'ALL' ? 'All Records' : f === 'LATEST' ? 'Active / Latest' : 'Superseded (V1)'}
                </button>
              ))}
            </div>
          </div>

          {/* Results Table */}
          <div style={{
            backgroundColor: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-lg)',
            overflow: 'hidden',
            boxShadow: 'var(--shadow-sm)'
          }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
              <thead>
                <tr style={{ backgroundColor: 'rgba(0,0,0,0.02)', borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-muted)' }}>
                  <th style={{ padding: '0.85rem 1.25rem' }}>Student Details</th>
                  <th style={{ padding: '0.85rem 1rem' }}>Academic Session</th>
                  <th style={{ padding: '0.85rem 1rem' }}>Version</th>
                  <th style={{ padding: '0.85rem 1rem' }}>Score / %</th>
                  <th style={{ padding: '0.85rem 1rem' }}>SGPA</th>
                  <th style={{ padding: '0.85rem 1rem' }}>Outcome</th>
                  <th style={{ padding: '0.85rem 1.25rem', textAlign: 'right' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredResults.map(res => (
                  <tr key={res.id} style={{ borderBottom: '1px solid var(--border-subtle)', opacity: res.status === 'SUPERSEDED' ? 0.75 : 1 }}>
                    <td style={{ padding: '1rem 1.25rem' }}>
                      <div style={{ fontWeight: '600', color: 'var(--text-primary)' }}>{res.student_name}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{res.enrollment_no} &bull; {res.program}</div>
                    </td>
                    <td style={{ padding: '1rem' }}>
                      <div>{res.semester}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{res.academic_year}</div>
                    </td>
                    <td style={{ padding: '1rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                        <span style={{
                          padding: '0.2rem 0.55rem',
                          borderRadius: 'var(--radius-sm)',
                          fontSize: '0.75rem',
                          fontWeight: '700',
                          backgroundColor: res.is_latest ? 'rgba(99, 102, 241, 0.15)' : 'rgba(156, 163, 175, 0.2)',
                          color: res.is_latest ? 'var(--primary-600)' : 'var(--text-muted)'
                        }}>
                          v{res.version}
                        </span>
                        {res.status === 'SUPERSEDED' && (
                          <span style={{ fontSize: '0.7rem', color: '#ef4444', fontWeight: '600' }}>SUPERSEDED</span>
                        )}
                      </div>
                    </td>
                    <td style={{ padding: '1rem' }}>
                      <div style={{ fontWeight: '600', color: 'var(--text-primary)' }}>{res.total_marks_obtained} / {res.total_max_marks}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{res.percentage}%</div>
                    </td>
                    <td style={{ padding: '1rem' }}>
                      <span style={{ fontWeight: '700', color: 'var(--text-primary)', fontSize: '0.95rem' }}>{res.sgpa}</span>
                    </td>
                    <td style={{ padding: '1rem' }}>
                      <span style={{
                        padding: '0.25rem 0.6rem',
                        borderRadius: '9999px',
                        fontSize: '0.75rem',
                        fontWeight: '700',
                        backgroundColor: res.result_status === 'PASS' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                        color: res.result_status === 'PASS' ? '#059669' : '#dc2626'
                      }}>
                        {res.result_status}
                      </span>
                    </td>
                    <td style={{ padding: '1rem 1.25rem', textAlign: 'right' }}>
                      <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
                        <button
                          onClick={() => {
                            setSelectedResult(res);
                            setShowMarksheetModal(true);
                          }}
                          style={{
                            padding: '0.45rem 0.75rem',
                            backgroundColor: 'transparent',
                            border: '1px solid var(--border-subtle)',
                            borderRadius: 'var(--radius-md)',
                            color: 'var(--text-primary)',
                            fontSize: '0.8rem',
                            cursor: 'pointer'
                          }}
                        >
                          View Marksheet
                        </button>

                        {res.is_latest && res.status === 'PUBLISHED' && (
                          <button
                            onClick={() => {
                              setSelectedResult(res);
                              setShowCorrectionModal(true);
                            }}
                            style={{
                              padding: '0.45rem 0.75rem',
                              backgroundColor: 'rgba(245, 158, 11, 0.15)',
                              border: '1px solid rgba(245, 158, 11, 0.3)',
                              color: '#d97706',
                              borderRadius: 'var(--radius-md)',
                              fontSize: '0.8rem',
                              fontWeight: '600',
                              cursor: 'pointer'
                            }}
                          >
                            Correct (ADR-016)
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 3: CORRECTION & SUPERSESSION */}
      {activeTab === 'corrections' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <div style={{
            backgroundColor: 'rgba(99, 102, 241, 0.05)',
            border: '1px solid rgba(99, 102, 241, 0.2)',
            borderRadius: 'var(--radius-lg)',
            padding: '1.25rem',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '1rem'
          }}>
            <ShieldCheck size={24} style={{ color: 'var(--primary-600)', marginTop: '0.1rem', flexShrink: 0 }} />
            <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
              <strong style={{ color: 'var(--text-primary)' }}>Architectural Invariant ADR-016 (Additive Result Supersession):</strong><br />
              Published results are immutable historical records and cannot be edited or deleted in place. When a correction is approved, 
              the system creates a new version (Result V2) which supersedes V1. The historical V1 is permanently preserved for accountability and auditing.
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {corrections.map(corr => (
              <div
                key={corr.id}
                style={{
                  backgroundColor: 'var(--bg-surface)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-lg)',
                  padding: '1.5rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '1rem',
                  boxShadow: 'var(--shadow-sm)'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                      <span style={{ fontSize: '1.05rem', fontWeight: '700', color: 'var(--text-primary)' }}>
                        Correction for {corr.student_name} ({corr.enrollment_no})
                      </span>
                      <span style={{
                        padding: '0.2rem 0.6rem',
                        borderRadius: '9999px',
                        fontSize: '0.75rem',
                        fontWeight: '700',
                        backgroundColor: corr.status === 'APPROVED' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                        color: corr.status === 'APPROVED' ? '#059669' : '#d97706'
                      }}>
                        {corr.status}
                      </span>
                    </div>
                    <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                      Target: Version {corr.target_version} &bull; Requested by: {corr.requested_by}
                    </div>
                  </div>

                  {corr.status === 'PENDING' && (
                    <button
                      onClick={() => handleApproveCorrection(corr.id)}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.4rem',
                        backgroundColor: '#059669',
                        color: '#ffffff',
                        border: 'none',
                        borderRadius: 'var(--radius-md)',
                        padding: '0.55rem 1rem',
                        fontSize: '0.85rem',
                        fontWeight: '600',
                        cursor: 'pointer'
                      }}
                    >
                      <CheckCircle2 size={16} />
                      <span>Approve & Supersede (Spawn V2)</span>
                    </button>
                  )}
                </div>

                <div style={{
                  backgroundColor: 'rgba(0, 0, 0, 0.02)',
                  padding: '1rem',
                  borderRadius: 'var(--radius-md)',
                  fontSize: '0.85rem',
                  color: 'var(--text-primary)'
                }}>
                  <strong>Mandatory Justification Reason:</strong>
                  <p style={{ margin: '0.35rem 0 0 0', color: 'var(--text-secondary)' }}>{corr.reason}</p>
                </div>

                {corr.status === 'APPROVED' && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem', color: '#059669' }}>
                    <Check size={16} />
                    <span>Superseded by Result Version {corr.superseding_version || 2} by {corr.reviewed_by} at {corr.reviewed_at}</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 4: STUDENT PORTAL PREVIEW */}
      {activeTab === 'student_portal' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', maxWidth: '850px', margin: '0 auto' }}>
          <div style={{
            backgroundColor: 'var(--bg-surface)',
            border: '2px solid var(--border-subtle)',
            borderRadius: 'var(--radius-lg)',
            padding: '2rem',
            boxShadow: 'var(--shadow-md)',
            display: 'flex',
            flexDirection: 'column',
            gap: '1.5rem'
          }}>
            {/* Marksheet Header */}
            <div style={{ textAlign: 'center', borderBottom: '2px solid var(--border-subtle)', paddingBottom: '1.25rem' }}>
              <div style={{ fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.1em', color: 'var(--text-muted)' }}>
                Government Engineering College &bull; Autonomous
              </div>
              <h2 style={{ fontSize: '1.5rem', fontWeight: '800', color: 'var(--text-primary)', margin: '0.25rem 0' }}>
                Grade Card & Semester Gazette
              </h2>
              <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                Academic Year 2024-2025 &bull; Semester 4 Examination
              </div>
            </div>

            {/* Student Info Card */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '1rem',
              backgroundColor: 'rgba(0,0,0,0.02)',
              padding: '1rem',
              borderRadius: 'var(--radius-md)',
              fontSize: '0.85rem'
            }}>
              <div>Candidate Name: <strong style={{ color: 'var(--text-primary)' }}>Rohan Sharma</strong></div>
              <div>Enrollment No: <strong style={{ color: 'var(--text-primary)' }}>ENR2024401</strong></div>
              <div>Program: <strong style={{ color: 'var(--text-primary)' }}>B.Tech Computer Engineering</strong></div>
              <div>Gazette Status: <span style={{ color: '#059669', fontWeight: '700' }}>PUBLISHED (Official)</span></div>
            </div>

            {/* Subjects Table */}
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
              <thead>
                <tr style={{ backgroundColor: 'rgba(99, 102, 241, 0.08)', borderBottom: '2px solid var(--border-subtle)' }}>
                  <th style={{ padding: '0.75rem' }}>Course Code & Title</th>
                  <th style={{ padding: '0.75rem', textAlign: 'center' }}>Internal</th>
                  <th style={{ padding: '0.75rem', textAlign: 'center' }}>External</th>
                  <th style={{ padding: '0.75rem', textAlign: 'center' }}>Total</th>
                  <th style={{ padding: '0.75rem', textAlign: 'center' }}>Grade</th>
                  <th style={{ padding: '0.75rem', textAlign: 'center' }}>Credits</th>
                  <th style={{ padding: '0.75rem', textAlign: 'center' }}>Status</th>
                </tr>
              </thead>
              <tbody>
                <tr style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                  <td style={{ padding: '0.75rem' }}>
                    <div style={{ fontWeight: '600' }}>CS401</div>
                    <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>Data Structures & Algorithms</div>
                  </td>
                  <td style={{ padding: '0.75rem', textAlign: 'center' }}>36 / 40</td>
                  <td style={{ padding: '0.75rem', textAlign: 'center' }}>52 / 60</td>
                  <td style={{ padding: '0.75rem', textAlign: 'center', fontWeight: '700' }}>88</td>
                  <td style={{ padding: '0.75rem', textAlign: 'center', fontWeight: '700', color: 'var(--primary-600)' }}>A+</td>
                  <td style={{ padding: '0.75rem', textAlign: 'center' }}>4</td>
                  <td style={{ padding: '0.75rem', textAlign: 'center', color: '#059669', fontWeight: '700' }}>PASS</td>
                </tr>
                <tr style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                  <td style={{ padding: '0.75rem' }}>
                    <div style={{ fontWeight: '600' }}>CS402</div>
                    <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>Computer Networks</div>
                  </td>
                  <td style={{ padding: '0.75rem', textAlign: 'center' }}>34 / 40</td>
                  <td style={{ padding: '0.75rem', textAlign: 'center' }}>50 / 60</td>
                  <td style={{ padding: '0.75rem', textAlign: 'center', fontWeight: '700' }}>84</td>
                  <td style={{ padding: '0.75rem', textAlign: 'center', fontWeight: '700', color: 'var(--primary-600)' }}>A+</td>
                  <td style={{ padding: '0.75rem', textAlign: 'center' }}>4</td>
                  <td style={{ padding: '0.75rem', textAlign: 'center', color: '#059669', fontWeight: '700' }}>PASS</td>
                </tr>
              </tbody>
            </table>

            {/* Performance Summary Strip */}
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              backgroundColor: 'rgba(16, 185, 129, 0.08)',
              border: '1px solid rgba(16, 185, 129, 0.2)',
              borderRadius: 'var(--radius-md)',
              padding: '1rem 1.5rem'
            }}>
              <div>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Semester Performance Index:</span>
                <div style={{ fontSize: '1.25rem', fontWeight: '800', color: '#059669' }}>SGPA: 9.00 / 10.00</div>
              </div>
              <div>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Overall Percentage:</span>
                <div style={{ fontSize: '1.25rem', fontWeight: '800', color: 'var(--text-primary)' }}>86.00%</div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Official Outcome:</span>
                <div style={{ fontSize: '1.25rem', fontWeight: '800', color: '#059669' }}>PASS &bull; FIRST CLASS DISTINCTION</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* MODAL 1: UPLOAD RESULTS BATCH */}
      {showUploadModal && (
        <div style={{
          position: 'fixed',
          inset: 0,
          backgroundColor: 'rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 9999,
          padding: '1rem'
        }}>
          <div style={{
            backgroundColor: 'var(--bg-surface)',
            borderRadius: 'var(--radius-lg)',
            width: '100%',
            maxWidth: '650px',
            padding: '1.75rem',
            boxShadow: 'var(--shadow-lg)',
            display: 'flex',
            flexDirection: 'column',
            gap: '1.25rem'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ fontSize: '1.2rem', fontWeight: '700', color: 'var(--text-primary)', margin: 0 }}>
                Upload Result Gazette (CSV / Tabular)
              </h3>
              <button
                onClick={() => setShowUploadModal(false)}
                style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}
              >
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleCreateBatch} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: '600', color: 'var(--text-secondary)' }}>Academic Year</label>
                  <input
                    type="text"
                    value={uploadForm.academic_year}
                    onChange={(e) => setUploadForm({ ...uploadForm, academic_year: e.target.value })}
                    style={{
                      width: '100%',
                      padding: '0.6rem',
                      borderRadius: 'var(--radius-md)',
                      border: '1px solid var(--border-subtle)',
                      backgroundColor: 'var(--bg-surface)',
                      color: 'var(--text-primary)',
                      marginTop: '0.25rem'
                    }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: '600', color: 'var(--text-secondary)' }}>Semester</label>
                  <input
                    type="text"
                    value={uploadForm.semester}
                    onChange={(e) => setUploadForm({ ...uploadForm, semester: e.target.value })}
                    style={{
                      width: '100%',
                      padding: '0.6rem',
                      borderRadius: 'var(--radius-md)',
                      border: '1px solid var(--border-subtle)',
                      backgroundColor: 'var(--bg-surface)',
                      color: 'var(--text-primary)',
                      marginTop: '0.25rem'
                    }}
                  />
                </div>
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: '600', color: 'var(--text-secondary)' }}>Program</label>
                <input
                  type="text"
                  value={uploadForm.program}
                  onChange={(e) => setUploadForm({ ...uploadForm, program: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '0.6rem',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--border-subtle)',
                    backgroundColor: 'var(--bg-surface)',
                    color: 'var(--text-primary)',
                    marginTop: '0.25rem'
                  }}
                />
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: '600', color: 'var(--text-secondary)' }}>CSV Data Content</label>
                <textarea
                  rows={6}
                  value={uploadForm.csv_content}
                  onChange={(e) => setUploadForm({ ...uploadForm, csv_content: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '0.6rem',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--border-subtle)',
                    backgroundColor: 'var(--bg-surface)',
                    color: 'var(--text-primary)',
                    fontFamily: 'monospace',
                    fontSize: '0.8rem',
                    marginTop: '0.25rem'
                  }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '0.5rem' }}>
                <button
                  type="button"
                  onClick={() => setShowUploadModal(false)}
                  style={{
                    padding: '0.6rem 1rem',
                    backgroundColor: 'transparent',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-md)',
                    cursor: 'pointer'
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  style={{
                    padding: '0.6rem 1.25rem',
                    backgroundColor: 'var(--primary-600)',
                    color: '#ffffff',
                    border: 'none',
                    borderRadius: 'var(--radius-md)',
                    fontWeight: '600',
                    cursor: 'pointer'
                  }}
                >
                  Create Batch & Stage Rows
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 2: INSPECT STAGING ROWS */}
      {showRowsModal && selectedBatch && (
        <div style={{
          position: 'fixed',
          inset: 0,
          backgroundColor: 'rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 9999,
          padding: '1rem'
        }}>
          <div style={{
            backgroundColor: 'var(--bg-surface)',
            borderRadius: 'var(--radius-lg)',
            width: '100%',
            maxWidth: '850px',
            maxHeight: '85vh',
            overflowY: 'auto',
            padding: '1.75rem',
            boxShadow: 'var(--shadow-lg)',
            display: 'flex',
            flexDirection: 'column',
            gap: '1.25rem'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h3 style={{ fontSize: '1.2rem', fontWeight: '700', color: 'var(--text-primary)', margin: 0 }}>
                  Staging Rows: {selectedBatch.file_name}
                </h3>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  Total: {selectedBatch.total_rows} &bull; Valid: {selectedBatch.valid_rows} &bull; Errors: {selectedBatch.error_rows}
                </span>
              </div>
              <button
                onClick={() => setShowRowsModal(false)}
                style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}
              >
                <X size={20} />
              </button>
            </div>

            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
              <thead>
                <tr style={{ backgroundColor: 'rgba(0,0,0,0.02)', borderBottom: '1px solid var(--border-subtle)' }}>
                  <th style={{ padding: '0.65rem' }}>Row #</th>
                  <th style={{ padding: '0.65rem' }}>Student Identifier</th>
                  <th style={{ padding: '0.65rem' }}>Matched Student</th>
                  <th style={{ padding: '0.65rem' }}>Subject</th>
                  <th style={{ padding: '0.65rem' }}>Internal</th>
                  <th style={{ padding: '0.65rem' }}>External</th>
                  <th style={{ padding: '0.65rem' }}>Total</th>
                  <th style={{ padding: '0.65rem' }}>Grade</th>
                  <th style={{ padding: '0.65rem' }}>Row Status</th>
                </tr>
              </thead>
              <tbody>
                {selectedBatch.rows.map(r => (
                  <tr key={r.row_num} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                    <td style={{ padding: '0.65rem' }}>{r.row_num}</td>
                    <td style={{ padding: '0.65rem', fontWeight: '600' }}>{r.identifier}</td>
                    <td style={{ padding: '0.65rem' }}>{r.student_name}</td>
                    <td style={{ padding: '0.65rem' }}>{r.subject}</td>
                    <td style={{ padding: '0.65rem' }}>{r.internal}</td>
                    <td style={{ padding: '0.65rem' }}>{r.external}</td>
                    <td style={{ padding: '0.65rem', fontWeight: '700' }}>{r.total}</td>
                    <td style={{ padding: '0.65rem', fontWeight: '700', color: 'var(--primary-600)' }}>{r.grade}</td>
                    <td style={{ padding: '0.65rem' }}>
                      <span style={{
                        padding: '0.15rem 0.5rem',
                        borderRadius: '9999px',
                        fontSize: '0.75rem',
                        fontWeight: '600',
                        backgroundColor: r.status === 'VALID' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                        color: r.status === 'VALID' ? '#059669' : '#dc2626'
                      }}>
                        {r.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '0.5rem' }}>
              <button
                onClick={() => setShowRowsModal(false)}
                style={{
                  padding: '0.6rem 1.25rem',
                  backgroundColor: 'var(--primary-600)',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: 'var(--radius-md)',
                  cursor: 'pointer'
                }}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL 3: VIEW MARKSHEET */}
      {showMarksheetModal && selectedResult && (
        <div style={{
          position: 'fixed',
          inset: 0,
          backgroundColor: 'rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 9999,
          padding: '1rem'
        }}>
          <div style={{
            backgroundColor: 'var(--bg-surface)',
            borderRadius: 'var(--radius-lg)',
            width: '100%',
            maxWidth: '750px',
            padding: '2rem',
            boxShadow: 'var(--shadow-lg)',
            display: 'flex',
            flexDirection: 'column',
            gap: '1.5rem'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h3 style={{ fontSize: '1.25rem', fontWeight: '700', color: 'var(--text-primary)', margin: 0 }}>
                  Official Marksheet & Grade Record
                </h3>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  Version {selectedResult.version} &bull; Status: {selectedResult.status}
                </span>
              </div>
              <button
                onClick={() => setShowMarksheetModal(false)}
                style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}
              >
                <X size={20} />
              </button>
            </div>

            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '0.75rem',
              backgroundColor: 'rgba(0,0,0,0.02)',
              padding: '1rem',
              borderRadius: 'var(--radius-md)',
              fontSize: '0.85rem'
            }}>
              <div>Student: <strong>{selectedResult.student_name}</strong></div>
              <div>Enrollment No: <strong>{selectedResult.enrollment_no}</strong></div>
              <div>Program: <strong>{selectedResult.program}</strong></div>
              <div>Semester: <strong>{selectedResult.semester}</strong></div>
            </div>

            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
              <thead>
                <tr style={{ backgroundColor: 'rgba(99, 102, 241, 0.08)', borderBottom: '2px solid var(--border-subtle)' }}>
                  <th style={{ padding: '0.65rem' }}>Course</th>
                  <th style={{ padding: '0.65rem', textAlign: 'center' }}>Internal</th>
                  <th style={{ padding: '0.65rem', textAlign: 'center' }}>External</th>
                  <th style={{ padding: '0.65rem', textAlign: 'center' }}>Total</th>
                  <th style={{ padding: '0.65rem', textAlign: 'center' }}>Grade</th>
                  <th style={{ padding: '0.65rem', textAlign: 'center' }}>Outcome</th>
                </tr>
              </thead>
              <tbody>
                {selectedResult.details.map((d, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                    <td style={{ padding: '0.65rem' }}>
                      <div style={{ fontWeight: '600' }}>{d.subject_code}</div>
                      <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>{d.subject_name}</div>
                    </td>
                    <td style={{ padding: '0.65rem', textAlign: 'center' }}>{d.internal}</td>
                    <td style={{ padding: '0.65rem', textAlign: 'center' }}>{d.external}</td>
                    <td style={{ padding: '0.65rem', textAlign: 'center', fontWeight: '700' }}>{d.total} / {d.max}</td>
                    <td style={{ padding: '0.65rem', textAlign: 'center', fontWeight: '700', color: 'var(--primary-600)' }}>{d.grade}</td>
                    <td style={{ padding: '0.65rem', textAlign: 'center', color: '#059669', fontWeight: '700' }}>{d.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '0.5rem' }}>
              <button
                onClick={() => setShowMarksheetModal(false)}
                style={{
                  padding: '0.6rem 1.25rem',
                  backgroundColor: 'var(--primary-600)',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: 'var(--radius-md)',
                  cursor: 'pointer'
                }}
              >
                Close Marksheet
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL 4: REQUEST CORRECTION (ADR-016) */}
      {showCorrectionModal && selectedResult && (
        <div style={{
          position: 'fixed',
          inset: 0,
          backgroundColor: 'rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 9999,
          padding: '1rem'
        }}>
          <div style={{
            backgroundColor: 'var(--bg-surface)',
            borderRadius: 'var(--radius-lg)',
            width: '100%',
            maxWidth: '600px',
            padding: '1.75rem',
            boxShadow: 'var(--shadow-lg)',
            display: 'flex',
            flexDirection: 'column',
            gap: '1.25rem'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ fontSize: '1.2rem', fontWeight: '700', color: 'var(--text-primary)', margin: 0 }}>
                Request Result Correction (ADR-016)
              </h3>
              <button
                onClick={() => setShowCorrectionModal(false)}
                style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}
              >
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleRequestCorrection} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{
                backgroundColor: 'rgba(245, 158, 11, 0.08)',
                border: '1px solid rgba(245, 158, 11, 0.25)',
                borderRadius: 'var(--radius-md)',
                padding: '0.85rem',
                fontSize: '0.85rem',
                color: '#d97706'
              }}>
                Correcting student <strong>{selectedResult.student_name}</strong> ({selectedResult.enrollment_no}). 
                This action creates a pending correction request. When approved, it will spawn <strong>Result Version {selectedResult.version + 1}</strong> and archive Version {selectedResult.version} as superseded.
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: '600', color: 'var(--text-secondary)' }}>
                  Mandatory Justification Reason <span style={{ color: '#ef4444' }}>*</span>
                </label>
                <textarea
                  rows={3}
                  required
                  placeholder="e.g. Official re-evaluation answer sheet retotalling error confirmed by university exam board..."
                  value={correctionForm.reason}
                  onChange={(e) => setCorrectionForm({ ...correctionForm, reason: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '0.6rem',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--border-subtle)',
                    backgroundColor: 'var(--bg-surface)',
                    color: 'var(--text-primary)',
                    fontSize: '0.85rem',
                    marginTop: '0.25rem'
                  }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: '600', color: 'var(--text-secondary)' }}>Subject Code</label>
                  <input
                    type="text"
                    value={correctionForm.subject_code}
                    onChange={(e) => setCorrectionForm({ ...correctionForm, subject_code: e.target.value })}
                    style={{
                      width: '100%',
                      padding: '0.6rem',
                      borderRadius: 'var(--radius-md)',
                      border: '1px solid var(--border-subtle)',
                      backgroundColor: 'var(--bg-surface)',
                      color: 'var(--text-primary)',
                      marginTop: '0.25rem'
                    }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: '600', color: 'var(--text-secondary)' }}>New External Marks</label>
                  <input
                    type="number"
                    value={correctionForm.new_external_marks}
                    onChange={(e) => setCorrectionForm({ ...correctionForm, new_external_marks: e.target.value })}
                    style={{
                      width: '100%',
                      padding: '0.6rem',
                      borderRadius: 'var(--radius-md)',
                      border: '1px solid var(--border-subtle)',
                      backgroundColor: 'var(--bg-surface)',
                      color: 'var(--text-primary)',
                      marginTop: '0.25rem'
                    }}
                  />
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '0.5rem' }}>
                <button
                  type="button"
                  onClick={() => setShowCorrectionModal(false)}
                  style={{
                    padding: '0.6rem 1rem',
                    backgroundColor: 'transparent',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-md)',
                    cursor: 'pointer'
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  style={{
                    padding: '0.6rem 1.25rem',
                    backgroundColor: '#d97706',
                    color: '#ffffff',
                    border: 'none',
                    borderRadius: 'var(--radius-md)',
                    fontWeight: '600',
                    cursor: 'pointer'
                  }}
                >
                  Submit Correction Request
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* TAB 5: CREDITS & ELIGIBILITY */}
      {activeTab === 'eligibility' && (
        <EligibilityDashboard />
      )}

    </div>
  );
};
