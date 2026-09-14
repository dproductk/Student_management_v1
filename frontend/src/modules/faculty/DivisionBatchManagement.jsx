import React, { useState, useEffect, useMemo } from 'react';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import {
  Users,
  Search,
  Download,
  CheckCircle2,
  Edit3,
  Save,
} from 'lucide-react';

// Fetch ALL pages from a paginated DRF endpoint.
// Backend uses LimitOffsetPagination with PAGE_SIZE=20, so a plain
// GET /students/ only returns the first 20. We follow `next` until done.
const fetchAllPages = async (baseUrl) => {
  let all = [];
  let url = baseUrl.includes('?') ? `${baseUrl}&limit=100` : `${baseUrl}?limit=100`;
  // Safety cap: 50 pages x 100 = 5000 records max
  for (let i = 0; i < 50; i++) {
    const res = await api.get(url).catch(() => null);
    if (!res) break;
    const data = res.data;
    if (Array.isArray(data)) {
      all = all.concat(data);
      break;
    }
    const results = data?.results || [];
    all = all.concat(results);
    if (!data?.next) break;
    url = data.next; // absolute URL works fine with axios
  }
  return all;
};

const toArray = (data) => (Array.isArray(data) ? data : data?.results || []);

export const DivisionBatchManagement = () => {
  const { user } = useAuth();
  const [students, setStudents] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [departments, setDepartments] = useState([]);
  const [selectedDeptId, setSelectedDeptId] = useState('all');
  const [facultyList, setFacultyList] = useState([]);
  const [cohortBatches, setCohortBatches] = useState([]);

  // Simple controls
  const [searchQuery, setSearchQuery] = useState('');
  const [divisionFilter, setDivisionFilter] = useState('All');
  const [studentsPerDiv, setStudentsPerDiv] = useState(60);
  const [studentsPerBatch, setStudentsPerBatch] = useState(20);
  const [working, setWorking] = useState(false);
  const [workingMsg, setWorkingMsg] = useState('');
  const [notification, setNotification] = useState('');

  // Assign teacher (kept simple, collapsed by default via <details>)
  const [teacherDiv, setTeacherDiv] = useState('A');
  const [teacherFacultyId, setTeacherFacultyId] = useState('');
  const [teacherBatchId, setTeacherBatchId] = useState('');

  // Edit one student
  const [editingStudent, setEditingStudent] = useState(null);
  const [editDiv, setEditDiv] = useState('A');
  const [editBatch, setEditBatch] = useState('A1');

  const STORAGE_KEY = 'edvana_student_division_allocations';
  const loadAllocations = () => {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
    } catch {
      return {};
    }
  };
  const saveAllocations = (a) => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(a));
    } catch (e) {
      console.error('Failed to persist allocations', e);
    }
  };

  const showMsg = (msg) => {
    setNotification(msg);
    setTimeout(() => setNotification(''), 4000);
  };

  const fetchInitialData = async () => {
    try {
      setLoading(true);
      const [depts, facs, batches, allStudents] = await Promise.all([
        fetchAllPages('/academic/departments/').catch(() => []),
        fetchAllPages('/faculty/members/').catch(() => []),
        fetchAllPages('/academic/batches/').catch(() => []),
        fetchAllPages('/students/').catch(() => []),
      ]);

      setDepartments(depts);
      setFacultyList(facs);
      setCohortBatches(batches);
      if (facs.length > 0) setTeacherFacultyId((v) => v || facs[0].id);
      if (batches.length > 0) setTeacherBatchId((v) => v || batches[0].id);

      // Pre-select HOD's own department if we can detect it
      if (depts.length > 0 && selectedDeptId === 'all' && user?.department) {
        const match = depts.find(
          (d) =>
            d.id === user.department ||
            d.code === user.department ||
            (d.name || '').toLowerCase().includes(String(user.department).toLowerCase())
        );
        if (match) setSelectedDeptId(match.id);
      }

      const stored = loadAllocations();
      const merged = allStudents.map((s, idx) => {
        const st = stored[s.id] || {};
        return {
          ...s,
          division: s.current_division || st.division || s.division || 'A',
          practical_batch: st.practical_batch || s.practical_batch || 'A1',
          _index: idx,
        };
      });

      setStudents(merged);
      setTotalCount(merged.length);
    } catch (err) {
      console.error('Error loading division data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInitialData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const persistDivisions = async (list) => {
    setWorkingMsg('Saving to server...');
    // Save in small chunks so 43 students don't hammer the server at once
    const chunk = 10;
    for (let i = 0; i < list.length; i += chunk) {
      const slice = list.slice(i, i + chunk);
      setWorkingMsg(`Saving ${Math.min(i + chunk, list.length)} of ${list.length}...`);
      await Promise.allSettled(
        slice.map((s) =>
          api.post(`/students/${s.id}/set-division/`, { division: s.division || 'A' })
        )
      );
    }
    setWorkingMsg('');
  };

  // Step 1: split students into divisions
  const handleAutoDivisions = async () => {
    if (students.length === 0) return;
    setWorking(true);
    setWorkingMsg('Creating divisions...');
    const labels = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'];
    const perDiv = parseInt(studentsPerDiv, 10) || 60;
    const stored = loadAllocations();
    const sorted = [...students].sort((a, b) =>
      (a.candidate_name || '').localeCompare(b.candidate_name || '')
    );
    const updated = sorted.map((s, index) => {
      const div = labels[Math.floor(index / perDiv)] || `D${Math.floor(index / perDiv) + 1}`;
      stored[s.id] = { ...(stored[s.id] || {}), division: div };
      return { ...s, division: div };
    });
    saveAllocations(stored);
    setStudents(updated);
    await persistDivisions(updated);
    setWorking(false);
    showMsg(`Done! ${updated.length} students split into ${new Set(updated.map((s) => s.division)).size} division(s).`);
  };

  // Step 2: split each division into lab batches
  const handleAutoBatches = () => {
    if (students.length === 0) return;
    setWorking(true);
    const perBatch = parseInt(studentsPerBatch, 10) || 20;
    const stored = loadAllocations();
    const groups = {};
    students.forEach((s) => {
      const div = s.division || 'A';
      if (!groups[div]) groups[div] = [];
      groups[div].push(s);
    });
    const batchFor = {};
    Object.keys(groups).forEach((div) => {
      const sorted = groups[div].sort((a, b) =>
        (a.candidate_name || '').localeCompare(b.candidate_name || '')
      );
      sorted.forEach((s, idx) => {
        const name = `${div}${Math.floor(idx / perBatch) + 1}`;
        stored[s.id] = { ...(stored[s.id] || {}), practical_batch: name };
        batchFor[s.id] = name;
      });
    });
    const updated = students.map((s) => ({
      ...s,
      practical_batch: batchFor[s.id] || s.practical_batch || 'A1',
    }));
    saveAllocations(stored);
    setStudents(updated);
    setWorking(false);
    showMsg(`Done! Lab batches created (${perBatch} students per batch).`);
  };

  const handleSaveEdit = async (e) => {
    e.preventDefault();
    if (!editingStudent) return;
    const stored = loadAllocations();
    stored[editingStudent.id] = {
      ...(stored[editingStudent.id] || {}),
      division: editDiv,
      practical_batch: editBatch,
    };
    saveAllocations(stored);
    setStudents((prev) =>
      prev.map((s) =>
        s.id === editingStudent.id ? { ...s, division: editDiv, practical_batch: editBatch } : s
      )
    );
    try {
      await api.post(`/students/${editingStudent.id}/set-division/`, { division: editDiv });
    } catch (err) {
      console.error('Failed to persist division', err);
    }
    setEditingStudent(null);
    showMsg(`Moved ${editingStudent.candidate_name} to Division ${editDiv}, Batch ${editBatch}.`);
  };

  const handleAssignTeacher = async (e) => {
    e.preventDefault();
    if (!teacherFacultyId) {
      alert('Please select a teacher.');
      return;
    }
    try {
      setWorking(true);
      setWorkingMsg('Assigning teacher...');
      const [yearRes, semRes, subjRes] = await Promise.all([
        api.get('/academic/academic-years/').catch(() => ({ data: [] })),
        api.get('/academic/semesters/').catch(() => ({ data: [] })),
        api.get('/academic/scheme-subjects/').catch(() => ({ data: [] })),
      ]);
      const years = toArray(yearRes.data);
      const sems = toArray(semRes.data);
      const subjs = toArray(subjRes.data);
      if (!years.length || !sems.length || !subjs.length || !teacherBatchId) {
        alert('Need an academic year, semester, batch and subject before assigning.');
        return;
      }
      await api.post('/faculty/assignments/', {
        faculty: teacherFacultyId,
        academic_year: years[0].id,
        semester: sems[0].id,
        scheme_subject: subjs[0].id,
        batch: teacherBatchId,
        role: 'CLASS_TEACHER',
        is_active: true,
        remarks: `Class Teacher - Division ${teacherDiv}`,
      });
      showMsg(`Teacher assigned for Division ${teacherDiv}.`);
    } catch (err) {
      alert(err.response?.data?.detail || 'Could not assign teacher.');
    } finally {
      setWorking(false);
      setWorkingMsg('');
    }
  };

  const handleExport = () => {
    const headers = ['No', 'Enrollment No', 'Name', 'Mobile', 'Division', 'Batch'];
    const rows = filtered.map((s, idx) => [
      idx + 1,
      s.enrollment_no || s.application_id || '',
      `"${(s.candidate_name || '').replace(/"/g, '')}"`,
      s.student_mobile || '',
      s.division || 'A',
      s.practical_batch || 'A1',
    ]);
    const csv = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const link = document.createElement('a');
    link.setAttribute('href', encodeURI(csv));
    link.setAttribute('download', `Divisions_${new Date().getFullYear()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Department + division + search filtering (client side, works on full list)
  const selectedDept = departments.find((d) => String(d.id) === String(selectedDeptId));
  const filtered = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    return students.filter((s) => {
      if (selectedDept && selectedDeptId !== 'all') {
        const code = s.current_department || s.department || '';
        const matchCode = code === selectedDept.code;
        const matchEnrollDept =
          s.enrollments?.some?.((en) => String(en.department) === String(selectedDept.id)) || false;
        // If student has dept info, enforce it; otherwise keep (older records lack dept)
        if ((code || matchEnrollDept) && !matchCode && !matchEnrollDept) return false;
        if (code && !matchCode) return false;
      }
      if (divisionFilter !== 'All' && s.division !== divisionFilter) return false;
      if (!q) return true;
      return (
        (s.candidate_name || '').toLowerCase().includes(q) ||
        (s.enrollment_no || '').toLowerCase().includes(q) ||
        (s.application_id || '').toLowerCase().includes(q) ||
        (s.student_mobile || '').includes(q)
      );
    });
  }, [students, searchQuery, divisionFilter, selectedDept, selectedDeptId]);

  const divisions = useMemo(
    () => Array.from(new Set(students.map((s) => s.division).filter(Boolean))).sort(),
    [students]
  );
  const divisionCounts = useMemo(() => {
    const c = {};
    students.forEach((s) => {
      const d = s.division || 'A';
      c[d] = (c[d] || 0) + 1;
    });
    return c;
  }, [students]);
  const batchCount = useMemo(
    () => new Set(students.map((s) => s.practical_batch).filter(Boolean)).size,
    [students]
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', maxWidth: '1100px' }}>
      {/* Simple header */}
      <div className="card" style={{ padding: '1.25rem 1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', gap: '0.9rem', alignItems: 'center' }}>
            <div style={{ width: '46px', height: '46px', borderRadius: '12px', background: 'rgba(59,130,246,.12)', color: 'var(--primary-600)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Users size={24} />
            </div>
            <div>
              <h1 style={{ margin: 0, fontSize: '1.3rem', fontWeight: 800 }}>Divisions</h1>
              <p style={{ margin: '2px 0 0', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                {loading ? 'Loading students...' : `${totalCount} students found. Split them into divisions and lab batches.`}
              </p>
            </div>
          </div>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button className="btn btn-secondary" onClick={fetchInitialData} disabled={loading}>
              Refresh
            </button>
            <button className="btn btn-secondary" onClick={handleExport} disabled={filtered.length === 0}>
              <Download size={15} style={{ marginRight: '0.35rem' }} /> Excel
            </button>
          </div>
        </div>

        {/* Department picker */}
        <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1rem', flexWrap: 'wrap', alignItems: 'center' }}>
          <label style={{ fontSize: '0.85rem', fontWeight: 600 }}>Department:</label>
          <select
            className="form-control"
            value={selectedDeptId}
            onChange={(e) => setSelectedDeptId(e.target.value)}
            style={{ maxWidth: '280px' }}
          >
            <option value="all">All departments ({totalCount})</option>
            {departments.map((d) => (
              <option key={d.id} value={d.id}>
                {d.code ? `${d.code} - ` : ''}{d.name}
              </option>
            ))}
          </select>
          {divisions.length > 0 && (
            <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap', marginLeft: 'auto' }}>
              {divisions.map((d) => (
                <button
                  key={d}
                  onClick={() => setDivisionFilter((f) => (f === d ? 'All' : d))}
                  title={`Show only Division ${d}`}
                  style={{
                    border: divisionFilter === d ? '2px solid var(--primary-600)' : '1px solid var(--border-subtle)',
                    background: divisionFilter === d ? 'rgba(59,130,246,.12)' : 'var(--bg-surface-elevated)',
                    borderRadius: '20px',
                    padding: '0.25rem 0.75rem',
                    fontSize: '0.8rem',
                    fontWeight: 700,
                    cursor: 'pointer',
                  }}
                >
                  Div {d} ({divisionCounts[d] || 0})
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {notification && (
        <div style={{ padding: '0.8rem 1rem', borderRadius: '10px', background: 'rgba(16,185,129,.1)', border: '1px solid rgba(16,185,129,.3)', color: '#059669', display: 'flex', gap: '0.5rem', alignItems: 'center', fontSize: '0.9rem' }}>
          <CheckCircle2 size={16} /> {notification}
        </div>
      )}

      {/* 3 numbers at a glance */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '0.75rem' }}>
        <div className="card" style={{ padding: '1rem' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 700 }}>TOTAL STUDENTS</div>
          <div style={{ fontSize: '1.6rem', fontWeight: 800 }}>{loading ? '...' : totalCount}</div>
        </div>
        <div className="card" style={{ padding: '1rem' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 700 }}>DIVISIONS</div>
          <div style={{ fontSize: '1.6rem', fontWeight: 800 }}>{divisions.length || '—'}</div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>{divisions.map((d) => `${d} (${divisionCounts[d]})`).join('  •  ')}</div>
        </div>
        <div className="card" style={{ padding: '1rem' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 700 }}>LAB BATCHES</div>
          <div style={{ fontSize: '1.6rem', fontWeight: 800 }}>{batchCount || '—'}</div>
        </div>
      </div>

      {/* Steps */}
      <div className="card" style={{ padding: '1.25rem 1.5rem' }}>
        <h3 style={{ margin: '0 0 0.75rem', fontSize: '1rem' }}>Setup in 2 steps</h3>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
          <div style={{ border: '1px solid var(--border-subtle)', borderRadius: '10px', padding: '1rem' }}>
            <div style={{ fontWeight: 800, marginBottom: '0.25rem' }}>Step 1 — Make divisions</div>
            <p style={{ fontSize: '0.83rem', color: 'var(--text-secondary)', margin: '0 0 0.75rem' }}>
              Example: 60 per division puts all 43 students in Division A.
            </p>
            <div style={{ display: 'flex', gap: '0.6rem', alignItems: 'flex-end' }}>
              <div style={{ flex: 1 }}>
                <label style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Students per division</label>
                <input type="number" className="form-control" value={studentsPerDiv} min="1" max="200"
                  onChange={(e) => setStudentsPerDiv(e.target.value)} />
              </div>
              <button className="btn btn-primary" onClick={handleAutoDivisions} disabled={working || students.length === 0}>
                Create divisions
              </button>
            </div>
          </div>

          <div style={{ border: '1px solid var(--border-subtle)', borderRadius: '10px', padding: '1rem' }}>
            <div style={{ fontWeight: 800, marginBottom: '0.25rem' }}>Step 2 — Make lab batches</div>
            <p style={{ fontSize: '0.83rem', color: 'var(--text-secondary)', margin: '0 0 0.75rem' }}>
              Splits each division into small groups like A1, A2, A3.
            </p>
            <div style={{ display: 'flex', gap: '0.6rem', alignItems: 'flex-end' }}>
              <div style={{ flex: 1 }}>
                <label style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Students per batch</label>
                <input type="number" className="form-control" value={studentsPerBatch} min="1" max="60"
                  onChange={(e) => setStudentsPerBatch(e.target.value)} />
              </div>
              <button className="btn btn-secondary" onClick={handleAutoBatches} disabled={working || students.length === 0}>
                Create batches
              </button>
            </div>
          </div>
        </div>

        {(working || workingMsg) && (
          <div style={{ marginTop: '0.75rem', fontSize: '0.85rem', color: 'var(--primary-600)', fontWeight: 600 }}>
            {workingMsg || 'Working...'}
          </div>
        )}

        <details style={{ marginTop: '1rem', border: '1px solid var(--border-subtle)', borderRadius: '10px', padding: '0.75rem 1rem' }}>
          <summary style={{ cursor: 'pointer', fontWeight: 700, fontSize: '0.9rem' }}>
            Optional: Assign a class teacher
          </summary>
          <form onSubmit={handleAssignTeacher} style={{ display: 'flex', gap: '0.6rem', flexWrap: 'wrap', alignItems: 'flex-end', marginTop: '0.75rem' }}>
            <div>
              <label style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Division</label>
              <select className="form-control" value={teacherDiv} onChange={(e) => setTeacherDiv(e.target.value)} style={{ width: '120px' }}>
                {['A', 'B', 'C', 'D', 'E'].map((d) => <option key={d} value={d}>{d}</option>)}
              </select>
            </div>
            <div>
              <label style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Teacher</label>
              <select className="form-control" value={teacherFacultyId} onChange={(e) => setTeacherFacultyId(e.target.value)} style={{ minWidth: '200px' }}>
                {facultyList.map((f) => (
                  <option key={f.id} value={f.id}>{f.full_name || `${f.first_name || ''} ${f.last_name || ''}`}</option>
                ))}
              </select>
            </div>
            <div>
              <label style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Batch</label>
              <select className="form-control" value={teacherBatchId} onChange={(e) => setTeacherBatchId(e.target.value)} style={{ minWidth: '160px' }}>
                {cohortBatches.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
              </select>
            </div>
            <button type="submit" className="btn btn-primary" disabled={working}>Assign</button>
          </form>
        </details>
      </div>

      {/* Search + list */}
      <div className="card" style={{ padding: '1rem 1.25rem', display: 'flex', gap: '0.75rem', flexWrap: 'wrap', alignItems: 'center' }}>
        <div style={{ position: 'relative', flex: 1, minWidth: '220px' }}>
          <Search size={16} color="var(--text-muted)" style={{ position: 'absolute', left: '12px', top: '10px' }} />
          <input
            className="form-control"
            placeholder="Search name, enrollment no, mobile..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{ paddingLeft: '2.3rem' }}
          />
        </div>
        <select className="form-control" value={divisionFilter} onChange={(e) => setDivisionFilter(e.target.value)} style={{ width: '150px' }}>
          <option value="All">All divisions</option>
          {divisions.map((d) => <option key={d} value={d}>Division {d}</option>)}
        </select>
        <span style={{ fontSize: '0.83rem', color: 'var(--text-secondary)', marginLeft: 'auto' }}>
          Showing <b>{filtered.length}</b> of <b>{students.length}</b> students
        </span>
      </div>

      {/* Table */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        {loading ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' }}>Loading all students...</div>
        ) : filtered.length === 0 ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
            No students found. Try clearing the search or choosing “All divisions”.
          </div>
        ) : (
          <div className="table-responsive">
            <table className="table" style={{ margin: 0 }}>
              <thead>
                <tr>
                  <th style={{ width: '50px' }}>No</th>
                  <th>Student</th>
                  <th>Mobile</th>
                  <th>Division</th>
                  <th>Batch</th>
                  <th style={{ textAlign: 'right' }}>Change</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((s, idx) => (
                  <tr key={s.id}>
                    <td style={{ color: 'var(--text-muted)' }}>{idx + 1}</td>
                    <td>
                      <div style={{ fontWeight: 700 }}>{s.candidate_name}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--primary-600)', fontFamily: 'monospace' }}>
                        {s.enrollment_no || s.application_id || '—'}
                      </div>
                    </td>
                    <td style={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>{s.student_mobile || '—'}</td>
                    <td><span className="badge badge-primary">Div {s.division || 'A'}</span></td>
                    <td><span className="badge badge-info">{s.practical_batch || 'A1'}</span></td>
                    <td style={{ textAlign: 'right' }}>
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={() => {
                          setEditingStudent(s);
                          setEditDiv(s.division || 'A');
                          setEditBatch(s.practical_batch || 'A1');
                        }}
                      >
                        <Edit3 size={12} style={{ marginRight: '0.25rem' }} /> Move
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {editingStudent && (
        <div className="modal-backdrop">
          <div className="modal-card" style={{ maxWidth: '400px', width: '90%' }}>
            <div className="modal-header">
              <h3 style={{ margin: 0, fontSize: '1.05rem' }}>Move student</h3>
              <button className="btn-close" onClick={() => setEditingStudent(null)}>✕</button>
            </div>
            <form onSubmit={handleSaveEdit}>
              <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: '0.9rem' }}>
                <div style={{ fontWeight: 700 }}>{editingStudent.candidate_name}</div>
                <div>
                  <label className="form-label">Division</label>
                  <select className="form-control" value={editDiv} onChange={(e) => setEditDiv(e.target.value)}>
                    {['A', 'B', 'C', 'D', 'E', 'F'].map((d) => (
                      <option key={d} value={d}>Division {d}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="form-label">Lab batch (e.g. A1, A2)</label>
                  <input className="form-control" value={editBatch} onChange={(e) => setEditBatch(e.target.value)} required />
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setEditingStudent(null)}>Cancel</button>
                <button type="submit" className="btn btn-primary"><Save size={14} style={{ marginRight: '0.3rem' }} /> Save</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
