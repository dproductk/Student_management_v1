import React, { useState, useEffect } from 'react';
import {
  BarChart3,
  TrendingUp,
  Users,
  CreditCard,
  GraduationCap,
  ShieldCheck,
  Download,
  Filter,
  RefreshCw,
  PieChart,
  FileSpreadsheet,
  AlertTriangle,
  ChevronRight,
  Sparkles,
  Layers,
  ArrowUpRight,
  Clock,
  CheckCircle2,
  XCircle,
  Award
} from 'lucide-react';
import api from '../../services/api';

export const AnalyticsDashboardPage = () => {
  const [activeTab, setActiveTab] = useState('overview'); // 'overview' | 'demographics' | 'finance' | 'academic' | 'verification' | 'export'
  const [kpis, setKpis] = useState(null);
  const [populationData, setPopulationData] = useState(null);
  const [demographicsData, setDemographicsData] = useState(null);
  const [financeData, setFinanceData] = useState(null);
  const [academicData, setAcademicData] = useState(null);
  const [verificationData, setVerificationData] = useState(null);
  const [activityData, setActivityData] = useState(null);
  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Filter state
  const [selectedDept, setSelectedDept] = useState('');

  // Export state
  const [exportType, setExportType] = useState('students');
  const [exportLimit, setExportLimit] = useState(1000);
  const [exportLoading, setExportLoading] = useState(false);

  const fetchAnalytics = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {};
      if (selectedDept) params.department_id = selectedDept;

      const [kpiRes, popRes, demoRes, finRes, acadRes, verifRes, actRes, deptRes] = await Promise.all([
        api.get('/reporting/analytics/kpis/', { params }),
        api.get('/reporting/analytics/population/', { params }),
        api.get('/reporting/analytics/demographics/', { params }),
        api.get('/reporting/analytics/fees/', { params }),
        api.get('/reporting/analytics/academic/', { params }),
        api.get('/reporting/analytics/verification/', { params }),
        api.get('/reporting/analytics/activity/', { params }),
        api.get('/academic/departments/').catch(() => ({ data: [] }))
      ]);

      setKpis(kpiRes.data);
      setPopulationData(popRes.data);
      setDemographicsData(demoRes.data);
      setFinanceData(finRes.data);
      setAcademicData(acadRes.data);
      setVerificationData(verifRes.data);
      setActivityData(actRes.data);
      setDepartments(deptRes.data.results || deptRes.data || []);
    } catch (err) {
      console.error('Failed to load reporting analytics:', err);
      setError('Failed to fetch reporting data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, [selectedDept]);

  const handleExport = async () => {
    setExportLoading(true);
    try {
      const params = new URLSearchParams({
        type: exportType,
        limit: exportLimit
      });
      if (selectedDept) params.append('department_id', selectedDept);

      const response = await api.get(`/reporting/export/?${params.toString()}`, {
        responseType: 'blob'
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `report_${exportType}_${new Date().toISOString().slice(0, 10)}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      alert('Export failed. Please check permissions and bounds.');
    } finally {
      setExportLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem'
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
            <BarChart3 size={24} color="var(--primary-400)" />
            <h1 style={{ fontSize: '1.75rem', fontWeight: '700', color: 'var(--text-primary)', margin: 0 }}>
              Executive Analytics & Institutional Intelligence
            </h1>
          </div>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', margin: 0 }}>
            Authoritative cross-module reporting: admissions, demographics, financial collection, results & accreditation
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <Filter size={15} color="var(--text-muted)" />
            <select
              value={selectedDept}
              onChange={(e) => setSelectedDept(e.target.value)}
              style={{
                padding: '0.55rem 0.85rem',
                backgroundColor: 'var(--bg-surface)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-md)',
                color: 'var(--text-primary)',
                fontSize: '0.85rem'
              }}
            >
              <option value="">All Departments</option>
              {departments.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name} ({d.code})
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={fetchAnalytics}
            disabled={loading}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.55rem 0.95rem',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-subtle)',
              backgroundColor: 'var(--bg-surface)',
              color: 'var(--text-secondary)',
              cursor: loading ? 'not-allowed' : 'pointer',
              fontSize: '0.85rem'
            }}
          >
            <RefreshCw size={15} className={loading ? 'animate-spin' : ''} />
            Refresh
          </button>

          <button
            onClick={() => setActiveTab('export')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.55rem 1.1rem',
              borderRadius: 'var(--radius-md)',
              border: 'none',
              backgroundColor: 'var(--primary-600)',
              color: '#ffffff',
              cursor: 'pointer',
              fontWeight: '600',
              fontSize: '0.875rem'
            }}
          >
            <Download size={16} />
            Export Data
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '1rem'
        }}
      >
        <div
          style={{
            backgroundColor: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-lg)',
            padding: '1.25rem'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: '500' }}>Total Students</span>
            <Users size={18} color="var(--primary-400)" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: '700', color: 'var(--text-primary)', marginTop: '0.5rem' }}>
            {kpis?.total_students ?? '-'}
          </div>
          <span style={{ fontSize: '0.75rem', color: '#34d399' }}>
            {kpis?.active_students ?? 0} active, {kpis?.total_enrolled ?? 0} enrolled
          </span>
        </div>

        <div
          style={{
            backgroundColor: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-lg)',
            padding: '1.25rem'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: '500' }}>Fee Collection Rate</span>
            <CreditCard size={18} color="#34d399" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: '700', color: '#34d399', marginTop: '0.5rem' }}>
            {kpis?.collection_percentage ?? 0}%
          </div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            ₹{Number(kpis?.total_collected_fees ?? 0).toLocaleString()} of ₹{Number(kpis?.total_billed_fees ?? 0).toLocaleString()}
          </span>
        </div>

        <div
          style={{
            backgroundColor: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-lg)',
            padding: '1.25rem'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: '500' }}>Academic Pass Rate</span>
            <GraduationCap size={18} color="#60a5fa" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: '700', color: '#60a5fa', marginTop: '0.5rem' }}>
            {kpis?.academic_pass_percentage ?? 0}%
          </div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Avg CGPA: {kpis?.average_cgpa ?? '0.00'} / 10.0
          </span>
        </div>

        <div
          style={{
            backgroundColor: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-lg)',
            padding: '1.25rem'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: '500' }}>Verification Throughput</span>
            <ShieldCheck size={18} color="#fbbf24" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: '700', color: '#fbbf24', marginTop: '0.5rem' }}>
            {kpis?.verification_approval_rate ?? 0}%
          </div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            {kpis?.pending_verifications ?? 0} pending in queue
          </span>
        </div>
      </div>

      {/* Tabs */}
      <div
        style={{
          display: 'flex',
          borderBottom: '1px solid var(--border-subtle)',
          gap: '0.5rem',
          overflowX: 'auto'
        }}
      >
        {[
          { key: 'overview', label: 'Executive Overview', icon: Layers },
          { key: 'demographics', label: 'Demographics & Population', icon: Users },
          { key: 'finance', label: 'Fees & Finance Ledger', icon: CreditCard },
          { key: 'academic', label: 'Academic & Results', icon: GraduationCap },
          { key: 'verification', label: 'Verification & Operations', icon: ShieldCheck },
          { key: 'export', label: 'Export Center', icon: Download }
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '0.75rem 1.25rem',
                backgroundColor: 'transparent',
                border: 'none',
                borderBottom: isActive ? '2px solid var(--primary-500)' : '2px solid transparent',
                color: isActive ? 'var(--primary-400)' : 'var(--text-secondary)',
                fontWeight: isActive ? '600' : '500',
                cursor: 'pointer',
                fontSize: '0.9rem',
                whiteSpace: 'nowrap',
                transition: 'all var(--transition-fast)'
              }}
            >
              <Icon size={16} />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Tab: Overview */}
      {activeTab === 'overview' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '1.25rem' }}>
          {/* Population Summary Card */}
          <div
            style={{
              backgroundColor: 'var(--bg-surface)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-lg)',
              padding: '1.5rem'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
              <Users size={18} color="var(--primary-400)" />
              <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: '600', color: 'var(--text-primary)' }}>
                Student Population Health
              </h3>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
              {[
                { label: 'Active Students', value: populationData?.active_students ?? 0, color: '#34d399' },
                { label: 'Enrolled in Current Session', value: populationData?.total_enrolled ?? 0, color: '#60a5fa' },
                { label: 'Detained Students', value: populationData?.detained_students ?? 0, color: '#f87171' },
                { label: 'Graduated / Passed Out', value: populationData?.passed_out_students ?? 0, color: '#a78bfa' },
                { label: 'Dropped / Withdrawn', value: populationData?.dropped_students ?? 0, color: '#9ca3af' }
              ].map((item, idx) => (
                <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.875rem' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>{item.label}</span>
                  <strong style={{ color: item.color }}>{item.value}</strong>
                </div>
              ))}
            </div>
          </div>

          {/* Finance Health Card */}
          <div
            style={{
              backgroundColor: 'var(--bg-surface)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-lg)',
              padding: '1.5rem'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
              <CreditCard size={18} color="#34d399" />
              <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: '600', color: 'var(--text-primary)' }}>
                Institutional Revenue Summary
              </h3>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Total Fee Assessment:</span>
                <strong style={{ color: 'var(--text-primary)' }}>
                  ₹{Number(financeData?.summary?.total_billed ?? 0).toLocaleString()}
                </strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Collected to Date:</span>
                <strong style={{ color: '#34d399' }}>
                  ₹{Number(financeData?.summary?.total_collected ?? 0).toLocaleString()}
                </strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Outstanding Deficit:</span>
                <strong style={{ color: '#f87171' }}>
                  ₹{Number(financeData?.summary?.total_outstanding ?? 0).toLocaleString()}
                </strong>
              </div>

              {/* Progress bar */}
              <div style={{ marginTop: '0.5rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.35rem' }}>
                  <span>Collection Progress</span>
                  <span>{financeData?.summary?.collection_percentage ?? 0}%</span>
                </div>
                <div style={{ width: '100%', height: '8px', backgroundColor: 'rgba(255, 255, 255, 0.05)', borderRadius: '4px', overflow: 'hidden' }}>
                  <div
                    style={{
                      width: `${Math.min(financeData?.summary?.collection_percentage ?? 0, 100)}%`,
                      height: '100%',
                      backgroundColor: '#34d399',
                      borderRadius: '4px',
                      transition: 'width 0.4s ease'
                    }}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab: Demographics */}
      {activeTab === 'demographics' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '1.25rem' }}>
          {/* Gender Distribution */}
          <div
            style={{
              backgroundColor: 'var(--bg-surface)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-lg)',
              padding: '1.25rem'
            }}
          >
            <h4 style={{ margin: '0 0 1rem', fontSize: '1rem', color: 'var(--text-primary)' }}>
              Gender Distribution
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
              {(demographicsData?.by_gender || []).map((g) => (
                <div key={g.gender} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>{g.gender}</span>
                  <strong style={{ color: 'var(--text-primary)' }}>{g.count}</strong>
                </div>
              ))}
            </div>
          </div>

          {/* Caste Category Distribution */}
          <div
            style={{
              backgroundColor: 'var(--bg-surface)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-lg)',
              padding: '1.25rem'
            }}
          >
            <h4 style={{ margin: '0 0 1rem', fontSize: '1rem', color: 'var(--text-primary)' }}>
              Social Category Distribution
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
              {(demographicsData?.by_category || []).map((c) => (
                <div key={c.category} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>{c.category || 'Unclassified'}</span>
                  <strong style={{ color: 'var(--text-primary)' }}>{c.count}</strong>
                </div>
              ))}
            </div>
          </div>

          {/* Department Breakdown */}
          <div
            style={{
              backgroundColor: 'var(--bg-surface)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-lg)',
              padding: '1.25rem'
            }}
          >
            <h4 style={{ margin: '0 0 1rem', fontSize: '1rem', color: 'var(--text-primary)' }}>
              Enrolled by Department
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
              {(demographicsData?.by_department || []).map((d, idx) => (
                <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>{d.department__name || 'Unknown'}</span>
                  <strong style={{ color: 'var(--primary-400)' }}>{d.count}</strong>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Tab: Finance */}
      {activeTab === 'finance' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div
            style={{
              backgroundColor: 'var(--bg-surface)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-lg)',
              padding: '1.25rem'
            }}
          >
            <h4 style={{ margin: '0 0 1rem', fontSize: '1.05rem', color: 'var(--text-primary)' }}>
              Fee Head Allocation & Contribution
            </h4>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
              {(financeData?.fee_heads || []).map((h) => (
                <div
                  key={h.code}
                  style={{
                    backgroundColor: 'rgba(255, 255, 255, 0.02)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-md)',
                    padding: '1rem'
                  }}
                >
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{h.code}</div>
                  <div style={{ fontWeight: '600', color: 'var(--text-primary)', marginTop: '0.2rem' }}>{h.name}</div>
                  <div style={{ fontSize: '1.2rem', fontWeight: '700', color: '#34d399', marginTop: '0.5rem' }}>
                    ₹{h.amount.toLocaleString()}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Tab: Academic */}
      {activeTab === 'academic' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.25rem' }}>
          {/* Performance Summary */}
          <div
            style={{
              backgroundColor: 'var(--bg-surface)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-lg)',
              padding: '1.25rem'
            }}
          >
            <h4 style={{ margin: '0 0 1rem', fontSize: '1rem', color: 'var(--text-primary)' }}>
              Grading & Class Distribution
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem', fontSize: '0.85rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Distinction (&ge;75%):</span>
                <strong style={{ color: '#34d399' }}>{academicData?.performance?.distinction_count ?? 0}</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-secondary)' }}>First Class (60-74%):</span>
                <strong style={{ color: '#60a5fa' }}>{academicData?.performance?.first_class_count ?? 0}</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Second Class (50-59%):</span>
                <strong style={{ color: '#fbbf24' }}>{academicData?.performance?.second_class_count ?? 0}</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Pass Class (&lt;50%):</span>
                <strong style={{ color: 'var(--text-secondary)' }}>{academicData?.performance?.pass_class_count ?? 0}</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderTop: '1px solid var(--border-subtle)', paddingTop: '0.5rem' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Failed / ATKT:</span>
                <strong style={{ color: '#f87171' }}>
                  {(academicData?.performance?.failed_count ?? 0) + (academicData?.performance?.atkt_count ?? 0)}
                </strong>
              </div>
            </div>
          </div>

          {/* Eligibility Standing */}
          <div
            style={{
              backgroundColor: 'var(--bg-surface)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-lg)',
              padding: '1.25rem'
            }}
          >
            <h4 style={{ margin: '0 0 1rem', fontSize: '1rem', color: 'var(--text-primary)' }}>
              Promotion Standing & Eligibility
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem', fontSize: '0.85rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Eligible for Promotion:</span>
                <strong style={{ color: '#34d399' }}>{academicData?.eligibility?.eligible_count ?? 0}</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Not Eligible (Pending):</span>
                <strong style={{ color: '#fbbf24' }}>{academicData?.eligibility?.not_eligible_count ?? 0}</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Detained:</span>
                <strong style={{ color: '#f87171' }}>{academicData?.eligibility?.detained_count ?? 0}</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderTop: '1px solid var(--border-subtle)', paddingTop: '0.5rem' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Promotion Rate:</span>
                <strong style={{ color: 'var(--primary-400)' }}>{academicData?.eligibility?.eligibility_rate ?? 0}%</strong>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab: Verification */}
      {activeTab === 'verification' && (
        <div
          style={{
            backgroundColor: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-lg)',
            padding: '1.25rem'
          }}
        >
          <h4 style={{ margin: '0 0 1rem', fontSize: '1rem', color: 'var(--text-primary)' }}>
            Verification Pipeline Throughput
          </h4>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
            {[
              { label: 'Pending Queue', value: verificationData?.pending_count ?? 0, color: '#fbbf24' },
              { label: 'Verified & Approved', value: verificationData?.approved_count ?? 0, color: '#34d399' },
              { label: 'Rejected', value: verificationData?.rejected_count ?? 0, color: '#f87171' },
              { label: 'Correction Requested', value: verificationData?.correction_requested_count ?? 0, color: '#60a5fa' }
            ].map((item, idx) => (
              <div
                key={idx}
                style={{
                  backgroundColor: 'rgba(255, 255, 255, 0.02)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-md)',
                  padding: '1rem'
                }}
              >
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{item.label}</div>
                <div style={{ fontSize: '1.5rem', fontWeight: '700', color: item.color, marginTop: '0.35rem' }}>
                  {item.value}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab: Export Center */}
      {activeTab === 'export' && (
        <div
          style={{
            backgroundColor: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-lg)',
            padding: '1.5rem',
            maxWidth: '600px'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
            <Download size={20} color="var(--primary-400)" />
            <h3 style={{ margin: 0, fontSize: '1.15rem', fontWeight: '600', color: 'var(--text-primary)' }}>
              Bounded Institutional Report Export
            </h3>
          </div>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '1.5rem' }}>
            Download authorized CSV reports. Enforces upper limit guardrails (maximum 5,000 records) to protect database performance.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: '500', color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>
                Report Dataset *
              </label>
              <select
                value={exportType}
                onChange={(e) => setExportType(e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.6rem 0.75rem',
                  backgroundColor: 'var(--bg-main)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-md)',
                  color: 'var(--text-primary)',
                  fontSize: '0.85rem'
                }}
              >
                <option value="students">Student Population & Enrolled Register</option>
                <option value="fee_defaulters">Fee Defaulters & Outstanding Balances</option>
                <option value="academic_results">Published Academic Results & GPAs</option>
              </select>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: '500', color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>
                Maximum Row Ceiling (Bounded Limit: 1 - 5000)
              </label>
              <input
                type="number"
                min="1"
                max="5000"
                value={exportLimit}
                onChange={(e) => setExportLimit(Number(e.target.value))}
                style={{
                  width: '100%',
                  padding: '0.6rem 0.75rem',
                  backgroundColor: 'var(--bg-main)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-md)',
                  color: 'var(--text-primary)',
                  fontSize: '0.85rem'
                }}
              />
            </div>

            <button
              onClick={handleExport}
              disabled={exportLoading}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.5rem',
                padding: '0.65rem 1.25rem',
                backgroundColor: 'var(--primary-600)',
                color: '#ffffff',
                border: 'none',
                borderRadius: 'var(--radius-md)',
                cursor: exportLoading ? 'not-allowed' : 'pointer',
                fontWeight: '600',
                fontSize: '0.9rem',
                marginTop: '0.5rem'
              }}
            >
              <Download size={16} />
              {exportLoading ? 'Generating Export...' : 'Download CSV Report'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
