import React, { useState } from 'react';
import {
  Award,
  BookOpen,
  Calendar,
  Building2,
  GraduationCap,
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  Search,
  Filter,
  Plus,
  RefreshCw,
  FileText,
  Sparkles,
  ChevronRight,
  X,
  Check,
  Layers,
  ShieldCheck,
  Users,
  Printer,
  Download,
  Info
} from 'lucide-react';

export const EligibilityDashboard = () => {
  const [subTab, setSubTab] = useState('decisions'); // 'decisions' | 'rules' | 'credits' | 'promotion'
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [selectedProgram, setSelectedProgram] = useState('ALL');

  // Modals
  const [showRuleModal, setShowRuleModal] = useState(false);
  const [showEvaluateModal, setShowEvaluateModal] = useState(false);
  const [showPromotionModal, setShowPromotionModal] = useState(false);
  const [bannerNotice, setBannerNotice] = useState(null);

  // Mock Active Rules (matching backend model)
  const [rules, setRules] = useState([
    {
      id: 'rule-001',
      name: 'B.Tech General Promotion Rule',
      code: 'RULE_BT_GEN',
      version: 1,
      program_name: 'B.Tech Computer Science',
      academic_year_name: '2024-2025',
      min_credits_required: '18.0',
      min_attendance_percentage: '75.00',
      max_backlogs_allowed: 2,
      detention_max_backlogs: 4,
      detention_min_attendance: '50.00',
      is_active: true,
      updated_at: '2026-09-06T10:00:00Z'
    },
    {
      id: 'rule-002',
      name: 'B.Tech Electrical Stricter Standard',
      code: 'RULE_BTEE_24',
      version: 2,
      program_name: 'B.Tech Electrical Engineering',
      academic_year_name: '2024-2025',
      min_credits_required: '20.0',
      min_attendance_percentage: '80.00',
      max_backlogs_allowed: 1,
      detention_max_backlogs: 3,
      detention_min_attendance: '60.00',
      is_active: true,
      updated_at: '2026-09-06T14:30:00Z'
    }
  ]);

  // Mock Student Credits
  const [credits, setCredits] = useState([
    {
      id: 'cred-1',
      student_enrollment_no: 'ENR2024401',
      student_name: 'Aakash Verma',
      program_name: 'B.Tech Computer Science',
      semester_number: 4,
      credits_attempted: '22.0',
      credits_earned: '22.0',
      sgpa: '8.85',
      cgpa: '8.72',
      backlogs_count: 0,
      version: 1,
      is_latest: true
    },
    {
      id: 'cred-2',
      student_enrollment_no: 'ENR2024402',
      student_name: 'Priya Sharma',
      program_name: 'B.Tech Computer Science',
      semester_number: 4,
      credits_attempted: '22.0',
      credits_earned: '16.0',
      sgpa: '6.40',
      cgpa: '7.10',
      backlogs_count: 2,
      version: 1,
      is_latest: true
    },
    {
      id: 'cred-3',
      student_enrollment_no: 'ENR2024403',
      student_name: 'Vikram Malhotra',
      program_name: 'B.Tech Electrical Engineering',
      semester_number: 4,
      credits_attempted: '22.0',
      credits_earned: '4.0',
      sgpa: '3.10',
      cgpa: '4.80',
      backlogs_count: 5,
      version: 1,
      is_latest: true
    },
    {
      id: 'cred-4',
      student_enrollment_no: 'ENR2024404',
      student_name: 'Sneha Joshi',
      program_name: 'B.Tech Electrical Engineering',
      semester_number: 4,
      credits_attempted: '22.0',
      credits_earned: '22.0',
      sgpa: '9.20',
      cgpa: '9.05',
      backlogs_count: 0,
      version: 1,
      is_latest: true
    }
  ]);

  // Mock Eligibility Decisions
  const [decisions, setDecisions] = useState([
    {
      id: 'dec-1',
      student_enrollment_no: 'ENR2024401',
      student_name: 'Aakash Verma',
      program_name: 'B.Tech Computer Science',
      semester_number: 4,
      rule_code: 'RULE_BT_GEN',
      rule_version: 1,
      credits_earned: '22.0',
      credits_attempted: '22.0',
      backlogs_count: 0,
      attendance_percentage: '92.00',
      decision: 'ELIGIBLE',
      detention_reason: '',
      remarks: 'Meets all credit, attendance, and backlog requirements.',
      decided_at: '2026-09-06T15:00:00Z'
    },
    {
      id: 'dec-2',
      student_enrollment_no: 'ENR2024402',
      student_name: 'Priya Sharma',
      program_name: 'B.Tech Computer Science',
      semester_number: 4,
      rule_code: 'RULE_BT_GEN',
      rule_version: 1,
      credits_earned: '16.0',
      credits_attempted: '22.0',
      backlogs_count: 2,
      attendance_percentage: '78.00',
      decision: 'NOT_ELIGIBLE',
      detention_reason: '',
      remarks: 'Earned credits (16.0) below required minimum (18.0).',
      decided_at: '2026-09-06T15:00:00Z'
    },
    {
      id: 'dec-3',
      student_enrollment_no: 'ENR2024403',
      student_name: 'Vikram Malhotra',
      program_name: 'B.Tech Electrical Engineering',
      semester_number: 4,
      rule_code: 'RULE_BTEE_24',
      rule_version: 2,
      credits_earned: '4.0',
      credits_attempted: '22.0',
      backlogs_count: 5,
      attendance_percentage: '44.00',
      decision: 'DETAINED',
      detention_reason: 'Backlogs (5) exceeded detention threshold (3); Attendance (44.00%) below detention minimum (60.00%)',
      remarks: 'Detained under rule RULE_BTEE_24 (v2).',
      decided_at: '2026-09-06T15:10:00Z'
    },
    {
      id: 'dec-4',
      student_enrollment_no: 'ENR2024404',
      student_name: 'Sneha Joshi',
      program_name: 'B.Tech Electrical Engineering',
      semester_number: 4,
      rule_code: 'RULE_BTEE_24',
      rule_version: 2,
      credits_earned: '22.0',
      credits_attempted: '22.0',
      backlogs_count: 0,
      attendance_percentage: '88.00',
      decision: 'ELIGIBLE',
      detention_reason: '',
      remarks: 'Meets all credit, attendance, and backlog requirements.',
      decided_at: '2026-09-06T15:10:00Z'
    }
  ]);

  // Mock Promotion Register Lists
  const [promotionLists, setPromotionLists] = useState([
    {
      id: 'promo-1',
      program_name: 'B.Tech Computer Science',
      academic_year_name: '2024-2025',
      semester_number: 4,
      target_semester_number: 5,
      total_students: 2,
      eligible_count: 1,
      not_eligible_count: 1,
      detained_count: 0,
      generated_at: '2026-09-06T16:00:00Z'
    }
  ]);

  // Rule Form State
  const [ruleForm, setRuleForm] = useState({
    name: '',
    code: '',
    program_name: 'B.Tech Computer Science',
    min_credits_required: '18.0',
    min_attendance_percentage: '75.0',
    max_backlogs_allowed: '2',
    detention_max_backlogs: '4',
    detention_min_attendance: '50.0'
  });

  const handleCreateRule = (e) => {
    e.preventDefault();
    const newRule = {
      id: `rule-${Date.now()}`,
      name: ruleForm.name,
      code: ruleForm.code,
      version: 1,
      program_name: ruleForm.program_name,
      academic_year_name: '2024-2025',
      min_credits_required: ruleForm.min_credits_required,
      min_attendance_percentage: ruleForm.min_attendance_percentage,
      max_backlogs_allowed: parseInt(ruleForm.max_backlogs_allowed),
      detention_max_backlogs: parseInt(ruleForm.detention_max_backlogs),
      detention_min_attendance: ruleForm.detention_min_attendance,
      is_active: true,
      updated_at: new Date().toISOString()
    };
    setRules([newRule, ...rules]);
    setShowRuleModal(false);
    setBannerNotice(`Successfully defined configurable rule: ${newRule.name} (v1)`);
    setTimeout(() => setBannerNotice(null), 5000);
  };

  const handleGeneratePromotion = () => {
    const newList = {
      id: `promo-${Date.now()}`,
      program_name: 'B.Tech Computer Science',
      academic_year_name: '2024-2025',
      semester_number: 4,
      target_semester_number: 5,
      total_students: decisions.length,
      eligible_count: decisions.filter(d => d.decision === 'ELIGIBLE').length,
      not_eligible_count: decisions.filter(d => d.decision === 'NOT_ELIGIBLE').length,
      detained_count: decisions.filter(d => d.decision === 'DETAINED').length,
      generated_at: new Date().toISOString()
    };
    setPromotionLists([newList, ...promotionLists]);
    setShowPromotionModal(false);
    setBannerNotice('Generated official promotion register snapshot for next-year admission.');
    setTimeout(() => setBannerNotice(null), 5000);
  };

  // Filtered decisions
  const filteredDecisions = decisions.filter(d => {
    const matchesSearch = d.student_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          d.student_enrollment_no.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'ALL' || d.decision === statusFilter;
    const matchesProgram = selectedProgram === 'ALL' || d.program_name === selectedProgram;
    return matchesSearch && matchesStatus && matchesProgram;
  });

  const getBadgeStyle = (status) => {
    switch (status) {
      case 'ELIGIBLE':
        return { backgroundColor: 'rgba(16, 185, 129, 0.15)', color: '#10b981', border: '1px solid rgba(16, 185, 129, 0.3)' };
      case 'NOT_ELIGIBLE':
        return { backgroundColor: 'rgba(245, 158, 11, 0.15)', color: '#f59e0b', border: '1px solid rgba(245, 158, 11, 0.3)' };
      case 'DETAINED':
        return { backgroundColor: 'rgba(239, 68, 68, 0.15)', color: '#ef4444', border: '1px solid rgba(239, 68, 68, 0.3)' };
      default:
        return { backgroundColor: 'rgba(148, 163, 184, 0.15)', color: '#94a3b8', border: '1px solid rgba(148, 163, 184, 0.3)' };
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header Notification Banner */}
      {bannerNotice && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          padding: '12px 18px',
          borderRadius: '10px',
          backgroundColor: 'rgba(16, 185, 129, 0.12)',
          border: '1px solid rgba(16, 185, 129, 0.3)',
          color: '#10b981',
          fontSize: '14px',
          fontWeight: '500'
        }}>
          <CheckCircle2 size={18} />
          <span>{bannerNotice}</span>
        </div>
      )}

      {/* Top Controls & Sub-tabs */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '16px',
        padding: '18px 24px',
        backgroundColor: 'var(--bg-surface)',
        borderRadius: '14px',
        border: '1px solid var(--border-subtle)'
      }}>
        <div style={{ display: 'flex', gap: '8px' }}>
          {[
            { id: 'decisions', label: 'Decision Matrix', icon: ShieldCheck },
            { id: 'rules', label: 'Eligibility Rules', icon: BookOpen },
            { id: 'credits', label: 'Calculated Credits', icon: Award },
            { id: 'promotion', label: 'Next-Year Promotion Lists', icon: Users },
          ].map((tab) => {
            const Icon = tab.icon;
            const active = subTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setSubTab(tab.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '10px 18px',
                  borderRadius: '10px',
                  fontSize: '13px',
                  fontWeight: active ? '600' : '500',
                  color: active ? '#ffffff' : 'var(--text-muted)',
                  backgroundColor: active ? '#6366f1' : 'transparent',
                  border: 'none',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease'
                }}
              >
                <Icon size={16} />
                {tab.label}
              </button>
            );
          })}
        </div>

        <div style={{ display: 'flex', gap: '12px' }}>
          {subTab === 'rules' && (
            <button
              onClick={() => setShowRuleModal(true)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '10px 18px',
                borderRadius: '10px',
                backgroundColor: '#6366f1',
                color: '#ffffff',
                border: 'none',
                fontWeight: '600',
                fontSize: '13px',
                cursor: 'pointer'
              }}
            >
              <Plus size={16} />
              Define New Rule
            </button>
          )}

          {subTab === 'decisions' && (
            <button
              onClick={() => {
                setBannerNotice('Cohort evaluated successfully. All student eligibility states updated.');
                setTimeout(() => setBannerNotice(null), 4000);
              }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '10px 18px',
                borderRadius: '10px',
                backgroundColor: '#6366f1',
                color: '#ffffff',
                border: 'none',
                fontWeight: '600',
                fontSize: '13px',
                cursor: 'pointer'
              }}
            >
              <Sparkles size={16} />
              Evaluate Cohort
            </button>
          )}

          {subTab === 'promotion' && (
            <button
              onClick={() => setShowPromotionModal(true)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '10px 18px',
                borderRadius: '10px',
                backgroundColor: '#10b981',
                color: '#ffffff',
                border: 'none',
                fontWeight: '600',
                fontSize: '13px',
                cursor: 'pointer'
              }}
            >
              <Users size={16} />
              Generate Promotion List
            </button>
          )}
        </div>
      </div>

      {/* SUBTAB 1: DECISION MATRIX */}
      {subTab === 'decisions' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Metrics summary */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
            <div style={{ padding: '20px', borderRadius: '12px', backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '13px', color: 'var(--text-muted)' }}>Total Students Evaluated</div>
              <div style={{ fontSize: '28px', fontWeight: '700', color: 'var(--text-main)', marginTop: '6px' }}>{decisions.length}</div>
            </div>
            <div style={{ padding: '20px', borderRadius: '12px', backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '13px', color: '#10b981' }}>Eligible for Promotion</div>
              <div style={{ fontSize: '28px', fontWeight: '700', color: '#10b981', marginTop: '6px' }}>
                {decisions.filter(d => d.decision === 'ELIGIBLE').length}
              </div>
            </div>
            <div style={{ padding: '20px', borderRadius: '12px', backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '13px', color: '#f59e0b' }}>Not Eligible (Credit Deficit)</div>
              <div style={{ fontSize: '28px', fontWeight: '700', color: '#f59e0b', marginTop: '6px' }}>
                {decisions.filter(d => d.decision === 'NOT_ELIGIBLE').length}
              </div>
            </div>
            <div style={{ padding: '20px', borderRadius: '12px', backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '13px', color: '#ef4444' }}>Detained (Backlog/Attendance)</div>
              <div style={{ fontSize: '28px', fontWeight: '700', color: '#ef4444', marginTop: '6px' }}>
                {decisions.filter(d => d.decision === 'DETAINED').length}
              </div>
            </div>
          </div>

          {/* Filters Bar */}
          <div style={{
            display: 'flex',
            gap: '16px',
            alignItems: 'center',
            padding: '16px 20px',
            backgroundColor: 'var(--bg-surface)',
            borderRadius: '12px',
            border: '1px solid var(--border-subtle)',
            flexWrap: 'wrap'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: 1, minWidth: '240px' }}>
              <Search size={16} color="var(--text-muted)" />
              <input
                type="text"
                placeholder="Search candidate name or enrollment no..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{
                  width: '100%',
                  background: 'transparent',
                  border: 'none',
                  outline: 'none',
                  color: 'var(--text-main)',
                  fontSize: '13px'
                }}
              />
            </div>
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>Status:</span>
              {['ALL', 'ELIGIBLE', 'NOT_ELIGIBLE', 'DETAINED'].map((st) => (
                <button
                  key={st}
                  onClick={() => setStatusFilter(st)}
                  style={{
                    padding: '6px 12px',
                    borderRadius: '6px',
                    fontSize: '12px',
                    fontWeight: statusFilter === st ? '600' : '400',
                    backgroundColor: statusFilter === st ? '#6366f1' : 'var(--bg-base)',
                    color: statusFilter === st ? '#ffffff' : 'var(--text-muted)',
                    border: '1px solid var(--border-subtle)',
                    cursor: 'pointer'
                  }}
                >
                  {st.replace('_', ' ')}
                </button>
              ))}
            </div>
          </div>

          {/* Decisions Table */}
          <div style={{
            backgroundColor: 'var(--bg-surface)',
            borderRadius: '14px',
            border: '1px solid var(--border-subtle)',
            overflow: 'hidden'
          }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-subtle)', backgroundColor: 'var(--bg-base)', color: 'var(--text-muted)' }}>
                  <th style={{ padding: '14px 18px' }}>Student</th>
                  <th style={{ padding: '14px 18px' }}>Program / Sem</th>
                  <th style={{ padding: '14px 18px' }}>Credits Earned</th>
                  <th style={{ padding: '14px 18px' }}>Backlogs</th>
                  <th style={{ padding: '14px 18px' }}>Attendance</th>
                  <th style={{ padding: '14px 18px' }}>Rule Version</th>
                  <th style={{ padding: '14px 18px' }}>Decision</th>
                  <th style={{ padding: '14px 18px' }}>Justification</th>
                </tr>
              </thead>
              <tbody>
                {filteredDecisions.map((d) => (
                  <tr key={d.id} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                    <td style={{ padding: '14px 18px' }}>
                      <div style={{ fontWeight: '600', color: 'var(--text-main)' }}>{d.student_name}</div>
                      <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{d.student_enrollment_no}</div>
                    </td>
                    <td style={{ padding: '14px 18px' }}>
                      <div style={{ color: 'var(--text-main)' }}>{d.program_name}</div>
                      <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Semester {d.semester_number}</div>
                    </td>
                    <td style={{ padding: '14px 18px', fontWeight: '600' }}>
                      {d.credits_earned} / {d.credits_attempted}
                    </td>
                    <td style={{ padding: '14px 18px' }}>
                      <span style={{
                        padding: '3px 8px',
                        borderRadius: '4px',
                        fontWeight: '600',
                        backgroundColor: d.backlogs_count > 0 ? 'rgba(239, 68, 68, 0.15)' : 'rgba(16, 185, 129, 0.15)',
                        color: d.backlogs_count > 0 ? '#ef4444' : '#10b981'
                      }}>
                        {d.backlogs_count}
                      </span>
                    </td>
                    <td style={{ padding: '14px 18px' }}>
                      {d.attendance_percentage}%
                    </td>
                    <td style={{ padding: '14px 18px' }}>
                      <span style={{ padding: '2px 8px', borderRadius: '4px', backgroundColor: 'var(--bg-base)', border: '1px solid var(--border-subtle)', fontSize: '12px' }}>
                        {d.rule_code} (v{d.rule_version})
                      </span>
                    </td>
                    <td style={{ padding: '14px 18px' }}>
                      <span style={{
                        padding: '4px 10px',
                        borderRadius: '6px',
                        fontWeight: '600',
                        fontSize: '11px',
                        display: 'inline-block',
                        ...getBadgeStyle(d.decision)
                      }}>
                        {d.decision.replace('_', ' ')}
                      </span>
                    </td>
                    <td style={{ padding: '14px 18px', maxWidth: '280px', fontSize: '12px', color: 'var(--text-muted)' }}>
                      {d.detention_reason || d.remarks}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* SUBTAB 2: CONFIGURABLE RULES */}
      {subTab === 'rules' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '20px' }}>
            {rules.map((rule) => (
              <div
                key={rule.id}
                style={{
                  backgroundColor: 'var(--bg-surface)',
                  borderRadius: '14px',
                  border: '1px solid var(--border-subtle)',
                  padding: '24px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '16px'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <h3 style={{ fontSize: '16px', fontWeight: '700', color: 'var(--text-main)', margin: '0 0 4px 0' }}>
                      {rule.name}
                    </h3>
                    <span style={{ fontSize: '12px', color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                      {rule.code}
                    </span>
                  </div>
                  <div style={{ display: 'flex', gap: '6px' }}>
                    <span style={{
                      padding: '3px 8px',
                      borderRadius: '4px',
                      fontSize: '11px',
                      fontWeight: '600',
                      backgroundColor: 'rgba(99, 102, 241, 0.15)',
                      color: '#6366f1'
                    }}>
                      v{rule.version}
                    </span>
                    <span style={{
                      padding: '3px 8px',
                      borderRadius: '4px',
                      fontSize: '11px',
                      fontWeight: '600',
                      backgroundColor: rule.is_active ? 'rgba(16, 185, 129, 0.15)' : 'rgba(148, 163, 184, 0.15)',
                      color: rule.is_active ? '#10b981' : '#94a3b8'
                    }}>
                      {rule.is_active ? 'ACTIVE' : 'HISTORICAL'}
                    </span>
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', fontSize: '12px', backgroundColor: 'var(--bg-base)', padding: '14px', borderRadius: '10px' }}>
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Min Credits:</span>
                    <div style={{ fontWeight: '600', color: 'var(--text-main)', fontSize: '14px' }}>{rule.min_credits_required}</div>
                  </div>
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Min Attendance:</span>
                    <div style={{ fontWeight: '600', color: 'var(--text-main)', fontSize: '14px' }}>{rule.min_attendance_percentage}%</div>
                  </div>
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Max Backlogs:</span>
                    <div style={{ fontWeight: '600', color: 'var(--text-main)', fontSize: '14px' }}>{rule.max_backlogs_allowed}</div>
                  </div>
                  <div>
                    <span style={{ color: '#ef4444' }}>Detention Threshold:</span>
                    <div style={{ fontWeight: '600', color: '#ef4444', fontSize: '14px' }}>
                      &gt; {rule.detention_max_backlogs} backlogs or &lt; {rule.detention_min_attendance}%
                    </div>
                  </div>
                </div>

                <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                  Program: <strong style={{ color: 'var(--text-main)' }}>{rule.program_name}</strong>
                </div>

                <button
                  onClick={() => {
                    const newVer = {
                      ...rule,
                      id: `rule-${Date.now()}`,
                      version: rule.version + 1,
                      updated_at: new Date().toISOString()
                    };
                    setRules([newVer, ...rules.map(r => r.id === rule.id ? { ...r, is_active: false } : r)]);
                    setBannerNotice(`Created new immutable version v${newVer.version} for ${rule.name}`);
                    setTimeout(() => setBannerNotice(null), 4000);
                  }}
                  style={{
                    padding: '8px 14px',
                    borderRadius: '8px',
                    backgroundColor: 'var(--bg-base)',
                    border: '1px solid var(--border-subtle)',
                    color: 'var(--text-main)',
                    fontSize: '12px',
                    fontWeight: '600',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '6px'
                  }}
                >
                  <RefreshCw size={14} />
                  Increment Rule Version
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* SUBTAB 3: CALCULATED CREDITS */}
      {subTab === 'credits' && (
        <div style={{
          backgroundColor: 'var(--bg-surface)',
          borderRadius: '14px',
          border: '1px solid var(--border-subtle)',
          overflow: 'hidden'
        }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-subtle)', backgroundColor: 'var(--bg-base)', color: 'var(--text-muted)' }}>
                <th style={{ padding: '14px 18px' }}>Student</th>
                <th style={{ padding: '14px 18px' }}>Program / Sem</th>
                <th style={{ padding: '14px 18px' }}>Attempted</th>
                <th style={{ padding: '14px 18px' }}>Earned</th>
                <th style={{ padding: '14px 18px' }}>Backlogs</th>
                <th style={{ padding: '14px 18px' }}>SGPA</th>
                <th style={{ padding: '14px 18px' }}>CGPA</th>
                <th style={{ padding: '14px 18px' }}>Version</th>
              </tr>
            </thead>
            <tbody>
              {credits.map((c) => (
                <tr key={c.id} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                  <td style={{ padding: '14px 18px' }}>
                    <div style={{ fontWeight: '600', color: 'var(--text-main)' }}>{c.student_name}</div>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{c.student_enrollment_no}</div>
                  </td>
                  <td style={{ padding: '14px 18px' }}>
                    <div style={{ color: 'var(--text-main)' }}>{c.program_name}</div>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Sem {c.semester_number}</div>
                  </td>
                  <td style={{ padding: '14px 18px' }}>{c.credits_attempted}</td>
                  <td style={{ padding: '14px 18px', fontWeight: '600', color: '#10b981' }}>{c.credits_earned}</td>
                  <td style={{ padding: '14px 18px' }}>{c.backlogs_count}</td>
                  <td style={{ padding: '14px 18px', fontWeight: '600' }}>{c.sgpa}</td>
                  <td style={{ padding: '14px 18px', fontWeight: '600' }}>{c.cgpa}</td>
                  <td style={{ padding: '14px 18px' }}>
                    <span style={{ padding: '2px 8px', borderRadius: '4px', backgroundColor: 'var(--bg-base)', border: '1px solid var(--border-subtle)', fontSize: '12px' }}>
                      v{c.version} {c.is_latest && '• Latest'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* SUBTAB 4: NEXT-YEAR PROMOTION LISTS */}
      {subTab === 'promotion' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}>
            {promotionLists.map((p) => (
              <div
                key={p.id}
                style={{
                  backgroundColor: 'var(--bg-surface)',
                  borderRadius: '14px',
                  border: '1px solid var(--border-subtle)',
                  padding: '24px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '14px'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: '600' }}>{p.academic_year_name}</span>
                  <span style={{
                    padding: '3px 8px',
                    borderRadius: '4px',
                    fontSize: '11px',
                    fontWeight: '600',
                    backgroundColor: 'rgba(16, 185, 129, 0.15)',
                    color: '#10b981'
                  }}>
                    OFFICIAL REGISTER
                  </span>
                </div>

                <h3 style={{ fontSize: '16px', fontWeight: '700', color: 'var(--text-main)', margin: 0 }}>
                  {p.program_name} (Sem {p.semester_number} &rarr; Sem {p.target_semester_number})
                </h3>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px', textAlign: 'center', backgroundColor: 'var(--bg-base)', padding: '12px', borderRadius: '10px' }}>
                  <div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Total</div>
                    <div style={{ fontSize: '16px', fontWeight: '700', color: 'var(--text-main)' }}>{p.total_students}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: '11px', color: '#10b981' }}>Eligible</div>
                    <div style={{ fontSize: '16px', fontWeight: '700', color: '#10b981' }}>{p.eligible_count}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: '11px', color: '#f59e0b' }}>Ineligible</div>
                    <div style={{ fontSize: '16px', fontWeight: '700', color: '#f59e0b' }}>{p.not_eligible_count}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: '11px', color: '#ef4444' }}>Detained</div>
                    <div style={{ fontSize: '16px', fontWeight: '700', color: '#ef4444' }}>{p.detained_count}</div>
                  </div>
                </div>

                <div style={{ display: 'flex', gap: '8px', marginTop: '6px' }}>
                  <button
                    onClick={() => window.print()}
                    style={{
                      flex: 1,
                      padding: '8px 12px',
                      borderRadius: '8px',
                      border: '1px solid var(--border-subtle)',
                      backgroundColor: 'transparent',
                      color: 'var(--text-main)',
                      fontSize: '12px',
                      fontWeight: '600',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '6px'
                    }}
                  >
                    <Printer size={14} />
                    Print Register
                  </button>
                  <button
                    onClick={() => {
                      setBannerNotice('Exported next-year promotion gazette CSV.');
                      setTimeout(() => setBannerNotice(null), 3000);
                    }}
                    style={{
                      flex: 1,
                      padding: '8px 12px',
                      borderRadius: '8px',
                      border: '1px solid var(--border-subtle)',
                      backgroundColor: 'transparent',
                      color: 'var(--text-main)',
                      fontSize: '12px',
                      fontWeight: '600',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '6px'
                    }}
                  >
                    <Download size={14} />
                    Export CSV
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* MODAL: DEFINE NEW RULE */}
      {showRuleModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.65)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div style={{
            backgroundColor: 'var(--bg-surface)',
            borderRadius: '16px',
            border: '1px solid var(--border-subtle)',
            padding: '28px',
            width: '100%',
            maxWidth: '520px'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h3 style={{ fontSize: '18px', fontWeight: '700', color: 'var(--text-main)', margin: 0 }}>
                Configure Institutional Eligibility Rule
              </h3>
              <button
                onClick={() => setShowRuleModal(false)}
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
              >
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleCreateRule} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>Rule Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. B.Tech Semester 4 Promotion Standard"
                  value={ruleForm.name}
                  onChange={(e) => setRuleForm({ ...ruleForm, name: e.target.value })}
                  style={{ width: '100%', padding: '10px 14px', borderRadius: '8px', border: '1px solid var(--border-subtle)', backgroundColor: 'var(--bg-base)', color: 'var(--text-main)' }}
                />
              </div>

              <div>
                <label style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>Rule Code</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. RULE_BT_SEM4"
                  value={ruleForm.code}
                  onChange={(e) => setRuleForm({ ...ruleForm, code: e.target.value })}
                  style={{ width: '100%', padding: '10px 14px', borderRadius: '8px', border: '1px solid var(--border-subtle)', backgroundColor: 'var(--bg-base)', color: 'var(--text-main)' }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>Min Credits</label>
                  <input
                    type="number"
                    step="0.5"
                    required
                    value={ruleForm.min_credits_required}
                    onChange={(e) => setRuleForm({ ...ruleForm, min_credits_required: e.target.value })}
                    style={{ width: '100%', padding: '10px 14px', borderRadius: '8px', border: '1px solid var(--border-subtle)', backgroundColor: 'var(--bg-base)', color: 'var(--text-main)' }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>Min Attendance (%)</label>
                  <input
                    type="number"
                    step="0.1"
                    required
                    value={ruleForm.min_attendance_percentage}
                    onChange={(e) => setRuleForm({ ...ruleForm, min_attendance_percentage: e.target.value })}
                    style={{ width: '100%', padding: '10px 14px', borderRadius: '8px', border: '1px solid var(--border-subtle)', backgroundColor: 'var(--bg-base)', color: 'var(--text-main)' }}
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>Max Backlogs Allowed</label>
                  <input
                    type="number"
                    required
                    value={ruleForm.max_backlogs_allowed}
                    onChange={(e) => setRuleForm({ ...ruleForm, max_backlogs_allowed: e.target.value })}
                    style={{ width: '100%', padding: '10px 14px', borderRadius: '8px', border: '1px solid var(--border-subtle)', backgroundColor: 'var(--bg-base)', color: 'var(--text-main)' }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '12px', color: '#ef4444', display: 'block', marginBottom: '6px' }}>Detention Backlog Limit</label>
                  <input
                    type="number"
                    required
                    value={ruleForm.detention_max_backlogs}
                    onChange={(e) => setRuleForm({ ...ruleForm, detention_max_backlogs: e.target.value })}
                    style={{ width: '100%', padding: '10px 14px', borderRadius: '8px', border: '1px solid var(--border-subtle)', backgroundColor: 'var(--bg-base)', color: 'var(--text-main)' }}
                  />
                </div>
              </div>

              <div>
                <label style={{ fontSize: '12px', color: '#ef4444', display: 'block', marginBottom: '6px' }}>Detention Min Attendance (%)</label>
                <input
                  type="number"
                  step="0.1"
                  required
                  value={ruleForm.detention_min_attendance}
                  onChange={(e) => setRuleForm({ ...ruleForm, detention_min_attendance: e.target.value })}
                  style={{ width: '100%', padding: '10px 14px', borderRadius: '8px', border: '1px solid var(--border-subtle)', backgroundColor: 'var(--bg-base)', color: 'var(--text-main)' }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '14px' }}>
                <button
                  type="button"
                  onClick={() => setShowRuleModal(false)}
                  style={{ padding: '10px 16px', borderRadius: '8px', border: '1px solid var(--border-subtle)', backgroundColor: 'transparent', color: 'var(--text-muted)', cursor: 'pointer' }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  style={{ padding: '10px 20px', borderRadius: '8px', backgroundColor: '#6366f1', color: '#ffffff', border: 'none', fontWeight: '600', cursor: 'pointer' }}
                >
                  Save & Activate Rule
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: GENERATE PROMOTION LIST */}
      {showPromotionModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.65)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div style={{
            backgroundColor: 'var(--bg-surface)',
            borderRadius: '16px',
            border: '1px solid var(--border-subtle)',
            padding: '28px',
            width: '100%',
            maxWidth: '480px'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h3 style={{ fontSize: '18px', fontWeight: '700', color: 'var(--text-main)', margin: 0 }}>
                Generate Promotion Register
              </h3>
              <button
                onClick={() => setShowPromotionModal(false)}
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
              >
                <X size={20} />
              </button>
            </div>

            <p style={{ fontSize: '13px', color: 'var(--text-muted)', lineHeight: '1.5', margin: '0 0 16px 0' }}>
              This will query active <strong>StudentEnrollment</strong> records from Student Management, apply the latest eligibility decision for each student, and compile the official next-year promotion list.
            </p>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <button
                onClick={() => setShowPromotionModal(false)}
                style={{ padding: '10px 16px', borderRadius: '8px', border: '1px solid var(--border-subtle)', backgroundColor: 'transparent', color: 'var(--text-muted)', cursor: 'pointer' }}
              >
                Cancel
              </button>
              <button
                onClick={handleGeneratePromotion}
                style={{ padding: '10px 20px', borderRadius: '8px', backgroundColor: '#10b981', color: '#ffffff', border: 'none', fontWeight: '600', cursor: 'pointer' }}
              >
                Confirm Generation
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
