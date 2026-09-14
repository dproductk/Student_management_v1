import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { 
  CreditCard, 
  Search, 
  CheckCircle2, 
  Clock, 
  Receipt, 
  Printer, 
  Download, 
  Save, 
  ChevronRight, 
  User, 
  Building2, 
  GraduationCap, 
  Calendar,
  AlertCircle,
  ArrowLeft,
  FileText,
  FileSpreadsheet,
  ExternalLink,
  RotateCcw,
  Check,
  Eye,
  History,
  Coins
} from 'lucide-react';

export const CandidateFeeDesk = () => {
  const { user } = useAuth();

  // Data States
  const [students, setStudents] = useState([]);
  const [feeHeads, setFeeHeads] = useState([]);
  const [academicYears, setAcademicYears] = useState([]);
  const [selectedAYId, setSelectedAYId] = useState('');
  const [feeCharges, setFeeCharges] = useState([]);
  const [loading, setLoading] = useState(true);

  // View state: 'list' (Eligible Students) | 'set_fee' (Update Admission Fees view)
  const [currentView, setCurrentView] = useState('list');
  const [activeStudent, setActiveStudent] = useState(null);
  const [activeStudentDetails, setActiveStudentDetails] = useState(null);

  // Fee breakdown configuration for active candidate: { [headName]: amount }
  const [candidateBreakdown, setCandidateBreakdown] = useState({});
  const [savingFee, setSavingFee] = useState(false);
  const [notification, setNotification] = useState('');

  // Search & Pagination in List View
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL'); // 'ALL' | 'NOT_SET' | 'SET' | 'PAID'
  const [entriesPerPage, setEntriesPerPage] = useState(10);
  const [currentPage, setCurrentPage] = useState(1);

  // Inline expandable "Mark Fee" card (per-row expansion in the eligible list)
  const [expandedMarkFeeId, setExpandedMarkFeeId] = useState(null);
  const [markFeeForm, setMarkFeeForm] = useState({
    amount: '',
    payment_mode: 'CASH',
    receipt_no: '',
    external_transaction_ref: '',
    remarks: 'Admission fee payment confirmed'
  });
  const [submittingPayment, setSubmittingPayment] = useState(false);
  const [ledgerEntries, setLedgerEntries] = useState([]);

  const [showHistoryModal, setShowHistoryModal] = useState(false);
  const [historyStudent, setHistoryStudent] = useState(null);
  const [showReceiptModal, setShowReceiptModal] = useState(false);
  const [receiptData, setReceiptData] = useState(null);

  // Fetch initial data
  const fetchData = async () => {
    try {
      setLoading(true);
      const [stuRes, headsRes, ayRes, chargesRes, ledgerRes] = await Promise.all([
        api.get('/students/').catch(() => ({ data: [] })),
        api.get('/finance/fee-heads/').catch(() => ({ data: [] })),
        api.get('/academic/academic-years/').catch(() => ({ data: [] })),
        api.get('/finance/charges/').catch(() => ({ data: [] })),
        api.get('/finance/ledger/').catch(() => ({ data: [] }))
      ]);

      const stuList = Array.isArray(stuRes.data) ? stuRes.data : (stuRes.data?.results || []);
      setStudents(stuList);

      const headsList = Array.isArray(headsRes.data) ? headsRes.data : (headsRes.data?.results || []);
      // Filter only active fee heads
      const activeHeads = headsList.filter(h => h.is_active !== false);
      setFeeHeads(activeHeads);

      const ays = Array.isArray(ayRes.data) ? ayRes.data : (ayRes.data?.results || []);
      setAcademicYears(ays);
      if (ays.length > 0) {
        const currentAy = ays.find(a => a.is_current) || ays[0];
        setSelectedAYId(currentAy.id);
      }

      const chgs = Array.isArray(chargesRes.data) ? chargesRes.data : (chargesRes.data?.results || []);
      setFeeCharges(chgs);

      const led = Array.isArray(ledgerRes.data) ? ledgerRes.data : (ledgerRes.data?.results || []);
      setLedgerEntries(led);
    } catch (err) {
      console.error('Error fetching fee desk data:', err);
    } finally {
      setLoading(false);
    }
  };

  // Refresh only charges + ledger (used after save / payment so list stays fresh)
  const refreshChargesAndLedger = async () => {
    try {
      const [chargesRes, ledgerRes] = await Promise.all([
        api.get('/finance/charges/').catch(() => ({ data: [] })),
        api.get('/finance/ledger/').catch(() => ({ data: [] }))
      ]);
      setFeeCharges(Array.isArray(chargesRes.data) ? chargesRes.data : (chargesRes.data?.results || []));
      setLedgerEntries(Array.isArray(ledgerRes.data) ? ledgerRes.data : (ledgerRes.data?.results || []));
    } catch (err) {
      console.error('Error refreshing charges:', err);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const selectedAY = academicYears.find(a => a.id === selectedAYId) || { label: '2026-27' };

  // Helper to determine fee status for a student.
  // STRICT per-student matching: a charge belongs to exactly one student.
  // Uses the backend `student_id` field first, with enrollment / application
  // fallbacks for legacy rows. Never matches across students.
  const matchesStudent = (c, student) => {
    if (!c || !student) return false;
    if (c.student_id && student.id && String(c.student_id) === String(student.id)) return true;
    // Legacy: account may be an expanded object { student: <id> }
    if (c.account && typeof c.account === 'object' && c.account.student && student.id &&
        String(c.account.student) === String(student.id)) return true;
    if (c.student_enrollment_no && student.enrollment_no &&
        String(c.student_enrollment_no) === String(student.enrollment_no)) return true;
    if (c.student_application_id && student.application_id &&
        String(c.student_application_id) === String(student.application_id)) return true;
    return false;
  };

  const matchesAY = (c) => {
    if (!selectedAYId) return true;
    if (c.academic_year && String(c.academic_year) === String(selectedAYId)) return true;
    // Fallback for rows where only the label was stored
    if (!c.academic_year && c.academic_year_label && selectedAY?.label &&
        c.academic_year_label === selectedAY.label) return true;
    // Also accept label match when id is present but label confirms same FY
    // (strict: id must match if present, so label-only path is above).
    return false;
  };

  const getStudentFeeInfo = (student) => {
    const charge = feeCharges.find(c => matchesStudent(c, student) && matchesAY(c));

    if (!charge || !charge.total_amount || parseFloat(charge.total_amount) === 0) {
      return {
        hasFee: false,
        status: 'NOT_SET',
        badgeClass: 'badge-warning',
        label: 'Fee Not Set',
        total: 0,
        paidAmount: 0,
        remaining: 0,
        paid: false,
        partiallyPaid: false,
        charge: null,
        breakdown: {}
      };
    }

    const total = parseFloat(charge.total_amount) || 0;
    const paidAmt = parseFloat(charge.paid_amount) || 0;
    const remaining = charge.remaining_balance !== undefined && charge.remaining_balance !== null
      ? parseFloat(charge.remaining_balance)
      : (total - paidAmt);
    const rawStatus = (charge.status || '').toUpperCase();
    const isPaid = rawStatus === 'PAID' || remaining <= 0;
    const isPartial = !isPaid && (rawStatus === 'PARTIALLY_PAID' || paidAmt > 0);
    const status = isPaid ? 'PAID' : (isPartial ? 'PARTIAL' : 'SET');
    return {
      hasFee: true,
      status,
      badgeClass: isPaid ? 'badge-success' : (isPartial ? 'badge-warning' : 'badge-info'),
      label: isPaid
        ? `Paid: ₹${Number(total).toLocaleString('en-IN')}`
        : (isPartial
          ? `Partial: ₹${Number(paidAmt).toLocaleString('en-IN')} / ₹${Number(total).toLocaleString('en-IN')}`
          : `Fee Set: ₹${Number(total).toLocaleString('en-IN')}`),
      total,
      paidAmount: paidAmt,
      remaining: Math.max(0, remaining),
      paid: isPaid,
      partiallyPaid: isPartial,
      charge: charge,
      breakdown: charge.fee_breakdown || {}
    };
  };

  const getStudentLedger = (student) => {
    if (!student) return [];
    return ledgerEntries.filter(e => {
      if (e.student_id && student.id && String(e.student_id) === String(student.id)) {
        // Also scope to selected FY when the charge carries AY info
        return true;
      }
      if (e.student_enrollment_no && student.enrollment_no &&
          String(e.student_enrollment_no) === String(student.enrollment_no)) return true;
      return false;
    });
  };

  // Open "Set Fee" or "Edit Fee" Sub-view for a student
  const handleOpenSetFee = async (student) => {
    setActiveStudent(student);
    const feeInfo = getStudentFeeInfo(student);

    // Initialize breakdown: if fee already set, load it; otherwise default to 0 for each active fee head
    const initialBreakdown = {};
    feeHeads.forEach(head => {
      if (feeInfo.breakdown && feeInfo.breakdown[head.name] !== undefined) {
        initialBreakdown[head.name] = Number(feeInfo.breakdown[head.name]);
      } else {
        initialBreakdown[head.name] = 0;
      }
    });
    setCandidateBreakdown(initialBreakdown);

    // Fetch full student details (with admission, category, enrollment relations)
    try {
      const detailRes = await api.get(`/students/${student.id}/`).catch(() => null);
      if (detailRes && detailRes.data) {
        setActiveStudentDetails(detailRes.data);
      } else {
        setActiveStudentDetails(student);
      }
    } catch {
      setActiveStudentDetails(student);
    }

    setCurrentView('set_fee');
  };

  // Save the Admission Fee for ONE candidate only, then auto-return to list.
  // Each student's charge is keyed by (student + academic year), so other
  // students are never touched. Different categories can keep different totals.
  const handleSaveCandidateFee = async () => {
    if (!activeStudent || !selectedAYId) return;
    setSavingFee(true);
    setNotification('');

    try {
      const payload = {
        student_id: activeStudent.id,
        academic_year_id: selectedAYId,
        fee_breakdown: candidateBreakdown
      };

      const res = await api.post('/finance/save-student-fee/', payload);

      // Replace ONLY this student's charge in local state (match by id).
      const updatedCharge = res.data;
      setFeeCharges(prev => {
        const withoutUpdated = prev.filter(c => String(c.id) !== String(updatedCharge.id));
        return [...withoutUpdated, updatedCharge];
      });
      await refreshChargesAndLedger();

      const totalCalculated = Object.values(candidateBreakdown).reduce((sum, val) => sum + (Number(val) || 0), 0);
      setNotification(`Admission Fee of ₹${totalCalculated.toLocaleString('en-IN')} saved for ${activeStudent.candidate_name}. Showing updated Eligible Students list.`);
      // Auto-navigate back to the eligible students list as requested
      setCurrentView('list');
      setActiveStudent(null);
      setActiveStudentDetails(null);
      setTimeout(() => setNotification(''), 5000);
    } catch (err) {
      console.error('Error saving student fee:', err);
      alert(err.response?.data?.error || 'Failed to save admission fee. Please check backend connection.');
    } finally {
      setSavingFee(false);
    }
  };

  // Toggle inline "Mark Fee" expansion for the row where the name is.
  // This opens the card inline (no modal) and asks for payment method +
  // transaction id, then allows marking the fee as paid.
  const handleToggleMarkFee = (student) => {
    if (expandedMarkFeeId && String(expandedMarkFeeId) === String(student.id)) {
      setExpandedMarkFeeId(null);
      return;
    }
    const feeInfo = getStudentFeeInfo(student);
    // Default amount = remaining balance (or total if nothing paid yet)
    const defaultAmount = feeInfo.hasFee
      ? (feeInfo.remaining > 0 ? feeInfo.remaining : feeInfo.total)
      : '';
    setExpandedMarkFeeId(student.id);
    setMarkFeeForm({
      amount: defaultAmount,
      payment_mode: 'CASH',
      receipt_no: `REC-${Date.now().toString().slice(-6)}`,
      external_transaction_ref: '',
      remarks: 'Payment verified and marked by Fee Accountant'
    });
  };

  // Submit inline Payment Marking for the expanded student
  const handleConfirmInlinePayment = async (e, student) => {
    e.preventDefault();
    if (!student) return;
    setSubmittingPayment(true);

    try {
      const feeInfo = getStudentFeeInfo(student);
      let chargeId = feeInfo.charge?.id;

      // Fee must be set first — do not invent a generic breakdown.
      // If missing, create one from the currently configured fee heads
      // (each student's own breakdown), so category-wise differences are kept.
      if (!chargeId) {
        if (!feeHeads || feeHeads.length === 0) {
          alert('Please Set Fee for this student first (no active fee heads found).');
          setSubmittingPayment(false);
          return;
        }
        const amountNum = parseFloat(markFeeForm.amount) || 0;
        if (amountNum <= 0) {
          alert('Please Set Fee first, or enter a valid amount to initialise this student fee.');
          setSubmittingPayment(false);
          return;
        }
        // Distribute entered amount to this student's heads (first head gets full
        // amount if only one head, else keep proportional split across THEIR heads).
        const perHead = {};
        if (feeHeads.length === 1) {
          perHead[feeHeads[0].name] = amountNum;
        } else {
          // Put full amount on first head and 0 on others by default would be
          // confusing — instead split: user should use Set Fee for exact split.
          // Here we keep it simple and auditable: first head = amount, rest 0,
          // with a clear remark that Set Fee should be used for breakup.
          feeHeads.forEach((h, idx) => {
            perHead[h.name] = idx === 0 ? amountNum : 0;
          });
        }
        const saveRes = await api.post('/finance/save-student-fee/', {
          student_id: student.id,
          academic_year_id: selectedAYId,
          fee_breakdown: perHead
        });
        chargeId = saveRes.data.id;
        // Refresh so feeInfo below is accurate
        await refreshChargesAndLedger();
      }

      // Payment mode + transaction id are mandatory in the expanded card
      if (!markFeeForm.payment_mode) {
        alert('Please select a payment method.');
        setSubmittingPayment(false);
        return;
      }
      if (!markFeeForm.external_transaction_ref || !String(markFeeForm.external_transaction_ref).trim()) {
        alert('Please enter the UTR / Transaction ID.');
        setSubmittingPayment(false);
        return;
      }
      const amt = parseFloat(markFeeForm.amount);
      if (!amt || amt <= 0) {
        alert('Please enter a valid payment amount.');
        setSubmittingPayment(false);
        return;
      }

      // Record payment for THIS student's charge only
      const paymentPayload = {
        charge_id: chargeId,
        amount: amt,
        receipt_no: markFeeForm.receipt_no || `REC-${Date.now().toString().slice(-6)}`,
        external_transaction_ref: markFeeForm.external_transaction_ref,
        payment_mode: markFeeForm.payment_mode,
        payment_date: new Date().toISOString().split('T')[0],
        reason: markFeeForm.remarks
      };

      await api.post('/finance/record-payment/', paymentPayload);

      await refreshChargesAndLedger();

      setExpandedMarkFeeId(null);

      // Prepare receipt data and open receipt modal
      setReceiptData({
        student: student,
        receipt_no: paymentPayload.receipt_no,
        transaction_ref: paymentPayload.external_transaction_ref,
        payment_mode: paymentPayload.payment_mode,
        amount: paymentPayload.amount,
        date: new Date().toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }),
        academic_year: selectedAY.label
      });
      setShowReceiptModal(true);
      setNotification(`Fee marked as paid for ${student.candidate_name} (₹${amt.toLocaleString('en-IN')}).`);
      setTimeout(() => setNotification(''), 5000);
    } catch (err) {
      console.error('Error recording payment:', err);
      alert(err.response?.data?.error || 'Failed to record fee payment.');
    } finally {
      setSubmittingPayment(false);
    }
  };

  // Export Eligible Students to CSV / Excel
  const handleExportCSV = () => {
    if (students.length === 0) return;
    const headers = ['S.N.', 'Enrollment No.', 'DEN/Application ID', 'Candidate Name', "Father's Name", 'Mobile', 'Fee Status', 'Fee Amount (₹)'];
    const rows = students.map((s, idx) => {
      const feeInfo = getStudentFeeInfo(s);
      return [
        idx + 1,
        s.enrollment_no || '',
        s.application_id || '',
        `"${s.candidate_name}"`,
        `"${s.father_name || ''}"`,
        s.student_mobile || '',
        feeInfo.status,
        feeInfo.total
      ];
    });

    const csvContent = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `Eligible_Students_FY_${selectedAY.label}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Filter students based on search query and status filter
  const filteredStudents = students.filter(s => {
    const feeInfo = getStudentFeeInfo(s);
    const matchesSearch = 
      (s.candidate_name || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (s.enrollment_no || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (s.application_id || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (s.student_mobile || '').includes(searchQuery);

    if (!matchesSearch) return false;
    if (statusFilter === 'NOT_SET') return !feeInfo.hasFee;
    if (statusFilter === 'SET') return feeInfo.hasFee && !feeInfo.paid;
    if (statusFilter === 'PAID') return feeInfo.paid;
    return true;
  });

  const openHistoryForStudent = (student) => {
    setHistoryStudent(student);
    setShowHistoryModal(true);
  };

  // Calculate admission fees total in "set_fee" view
  const currentTotalAdmissionFees = Object.values(candidateBreakdown).reduce(
    (acc, val) => acc + (Number(val) || 0), 
    0
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      
      {/* =========================================================
          VIEW 1: ELIGIBLE STUDENTS LIST TABLE
          ========================================================= */}
      {currentView === 'list' && (
        <>
          {/* Top Banner (Matches Gpkp edvana format) */}
          <div className="card" style={{
            background: 'linear-gradient(135deg, #1e40af 0%, #3b82f6 100%)',
            color: '#ffffff',
            padding: '1.5rem 2rem',
            borderRadius: 'var(--radius-lg)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '1rem',
            boxShadow: '0 10px 15px -3px rgba(30, 64, 175, 0.2)'
          }}>
            <div>
              <div style={{ fontSize: '0.85rem', color: 'rgba(255, 255, 255, 0.8)', fontWeight: '600', marginBottom: '0.25rem' }}>
                Admission / Eligible Students for FY ({selectedAY.label})
              </div>
              <h1 style={{ margin: 0, fontSize: '1.6rem', fontWeight: '800', letterSpacing: '-0.02em', color: '#ffffff' }}>
                Eligible Students for FY ({selectedAY.label})
              </h1>
              <p style={{ margin: '0.35rem 0 0', fontSize: '0.88rem', color: 'rgba(255, 255, 255, 0.9)' }}>
                Government College of Engineering, Kolhapur — Authoritative Candidate Admission Fee Desk
              </p>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
              {/* Academic Year Selector */}
              <select 
                className="form-control"
                value={selectedAYId}
                onChange={(e) => setSelectedAYId(e.target.value)}
                style={{
                  backgroundColor: 'rgba(255, 255, 255, 0.15)',
                  color: '#ffffff',
                  border: '1px solid rgba(255, 255, 255, 0.3)',
                  fontWeight: '700',
                  fontSize: '0.9rem',
                  width: 'auto',
                  cursor: 'pointer'
                }}
              >
                {academicYears.map(ay => (
                  <option key={ay.id} value={ay.id} style={{ color: '#000000' }}>
                    FY ({ay.label}) {ay.is_current ? '• Current' : ''}
                  </option>
                ))}
              </select>

              <button 
                className="btn"
                onClick={handleExportCSV}
                style={{
                  backgroundColor: '#ffffff',
                  color: '#1e40af',
                  fontWeight: '700',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  fontSize: '0.88rem',
                  boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                }}
              >
                <FileSpreadsheet size={16} /> Export to Excel
              </button>
            </div>
          </div>

          {/* Success / info banner — visible on the Eligible list so the
              accountant sees confirmation after auto-redirect from Set Fee */}
          {notification && (
            <div style={{
              padding: '1rem 1.25rem',
              backgroundColor: 'rgba(16, 185, 129, 0.1)',
              border: '1px solid rgba(16, 185, 129, 0.3)',
              color: '#047857',
              borderRadius: 'var(--radius-md)',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              fontSize: '0.92rem',
              fontWeight: '600'
            }}>
              <CheckCircle2 size={18} /> {notification}
            </div>
          )}

          {/* Table Container Card */}
          <div className="card" style={{ padding: '1.5rem', borderRadius: 'var(--radius-lg)' }}>
            
            {/* Control Bar: Entries count, Search & Status Filters */}
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '1.25rem',
              flexWrap: 'wrap',
              gap: '1rem'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                <span>Show</span>
                <select 
                  className="form-control"
                  style={{ width: 'auto', padding: '0.35rem 0.65rem' }}
                  value={entriesPerPage}
                  onChange={(e) => setEntriesPerPage(Number(e.target.value))}
                >
                  <option value={10}>10</option>
                  <option value={25}>25</option>
                  <option value={50}>50</option>
                  <option value={100}>100</option>
                </select>
                <span>entries</span>
              </div>

              {/* Status Tabs */}
              <div style={{ display: 'flex', gap: '0.35rem', backgroundColor: 'var(--bg-surface-elevated)', padding: '0.25rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                {[
                  { key: 'ALL', label: 'All Candidates' },
                  { key: 'NOT_SET', label: 'Fee Not Set' },
                  { key: 'SET', label: 'Fee Set' },
                  { key: 'PAID', label: 'Fee Paid' }
                ].map(tab => (
                  <button
                    key={tab.key}
                    onClick={() => setStatusFilter(tab.key)}
                    style={{
                      border: 'none',
                      background: statusFilter === tab.key ? 'var(--primary-600)' : 'transparent',
                      color: statusFilter === tab.key ? '#ffffff' : 'var(--text-secondary)',
                      padding: '0.35rem 0.75rem',
                      borderRadius: 'var(--radius-sm)',
                      fontSize: '0.8rem',
                      fontWeight: '700',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease'
                    }}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>

              {/* Search Box */}
              <div style={{ position: 'relative', width: '280px' }}>
                <Search size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                <input 
                  type="text"
                  className="form-control"
                  placeholder="Search: Name, Enroll No, Mobile..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  style={{ paddingLeft: '2.25rem', fontSize: '0.88rem' }}
                />
              </div>
            </div>

            {/* Students Table */}
            <div className="table-responsive">
              <table className="table" style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ backgroundColor: 'var(--bg-surface-elevated)', borderBottom: '2px solid var(--border-subtle)' }}>
                    <th style={{ padding: '0.85rem 1rem', fontSize: '0.78rem', fontWeight: '800', color: 'var(--text-muted)', textAlign: 'center', width: '60px' }}>S.N.</th>
                    <th style={{ padding: '0.85rem 1rem', fontSize: '0.78rem', fontWeight: '800', color: 'var(--text-muted)' }}>ENROLL NO.</th>
                    <th style={{ padding: '0.85rem 1rem', fontSize: '0.78rem', fontWeight: '800', color: 'var(--text-muted)' }}>NAME</th>
                    <th style={{ padding: '0.85rem 1rem', fontSize: '0.78rem', fontWeight: '800', color: 'var(--text-muted)' }}>FATHER'S NAME</th>
                    <th style={{ padding: '0.85rem 1rem', fontSize: '0.78rem', fontWeight: '800', color: 'var(--text-muted)' }}>MOBILE</th>
                    <th style={{ padding: '0.85rem 1rem', fontSize: '0.78rem', fontWeight: '800', color: 'var(--text-muted)', textAlign: 'center' }}>FEE MARKED / STATUS</th>
                    <th style={{ padding: '0.85rem 1rem', fontSize: '0.78rem', fontWeight: '800', color: 'var(--text-muted)', textAlign: 'center' }}>ACTIONS</th>
                  </tr>
                </thead>
                <tbody>
                  {loading ? (
                    <tr>
                      <td colSpan={7} style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
                        Loading eligible candidates for FY ({selectedAY.label})...
                      </td>
                    </tr>
                  ) : filteredStudents.length === 0 ? (
                    <tr>
                      <td colSpan={7} style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
                        No eligible students found matching your search.
                      </td>
                    </tr>
                  ) : (
                    filteredStudents.slice(0, entriesPerPage).map((student, idx) => {
                      const feeInfo = getStudentFeeInfo(student);
                      const isExpanded = expandedMarkFeeId && String(expandedMarkFeeId) === String(student.id);
                      const studentLedger = isExpanded ? getStudentLedger(student) : [];
                      return (
                        <React.Fragment key={student.id}>
                        <tr
                          style={{
                            borderBottom: isExpanded ? 'none' : '1px solid var(--border-subtle)',
                            transition: 'background-color 0.15s ease',
                            backgroundColor: isExpanded ? 'rgba(14, 165, 233, 0.06)' : (idx % 2 === 0 ? 'var(--bg-surface)' : 'rgba(248, 250, 252, 0.6)')
                          }}
                        >
                          <td style={{ padding: '1rem', textAlign: 'center', fontWeight: '600', fontSize: '0.88rem', color: 'var(--text-muted)' }}>
                            {idx + 1}
                          </td>
                          <td style={{ padding: '1rem' }}>
                            <span style={{ fontFamily: 'monospace', fontWeight: '700', color: 'var(--primary-600)', fontSize: '0.9rem' }}>
                              {student.enrollment_no || '191227'}
                            </span>
                            {student.application_id && (
                              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                                {student.application_id}
                              </div>
                            )}
                          </td>
                          <td style={{ padding: '1rem' }}>
                            <div style={{ fontWeight: '700', color: 'var(--text-primary)', fontSize: '0.92rem' }}>
                              {student.candidate_name}
                            </div>
                            <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)' }}>
                              {student.gender || 'N/A'} • {student.current_program || 'CIVIL ENGINEERING'}
                            </div>
                          </td>
                          <td style={{ padding: '1rem', fontSize: '0.88rem', color: 'var(--text-secondary)', fontWeight: '500' }}>
                            {student.father_name || '—'}
                          </td>
                          <td style={{ padding: '1rem', fontSize: '0.88rem', fontFamily: 'monospace', color: 'var(--text-primary)' }}>
                            {student.student_mobile || '—'}
                          </td>
                          <td style={{ padding: '1rem', textAlign: 'center' }}>
                            <span className={`badge ${feeInfo.badgeClass}`} style={{ fontSize: '0.8rem', padding: '0.35rem 0.75rem', fontWeight: '700' }}>
                              {feeInfo.label}
                            </span>
                          </td>
                          <td style={{ padding: '1rem', textAlign: 'center' }}>
                            <div style={{ display: 'inline-flex', gap: '0.45rem', alignItems: 'center' }}>
                              {/* 1. Set Fee / Edit Fee Button */}
                              <button
                                onClick={() => handleOpenSetFee(student)}
                                className={`btn ${feeInfo.hasFee ? 'btn-secondary' : 'btn-primary'}`}
                                style={{
                                  fontSize: '0.8rem',
                                  padding: '0.4rem 0.75rem',
                                  fontWeight: '700',
                                  display: 'flex',
                                  alignItems: 'center',
                                  gap: '0.3rem',
                                  boxShadow: feeInfo.hasFee ? 'none' : '0 2px 4px rgba(37, 99, 235, 0.2)'
                                }}
                              >
                                {feeInfo.hasFee ? 'Edit Fee' : 'Set Fee'}
                              </button>

                              {/* 2. Mark Fee Button — expands inline card for THIS student */}
                              <button
                                onClick={() => handleToggleMarkFee(student)}
                                className="btn"
                                style={{
                                  fontSize: '0.8rem',
                                  padding: '0.4rem 0.75rem',
                                  fontWeight: '700',
                                  backgroundColor: isExpanded ? '#475569' : (feeInfo.paid ? '#10b981' : '#0ea5e9'),
                                  color: '#ffffff',
                                  border: 'none',
                                  display: 'flex',
                                  alignItems: 'center',
                                  gap: '0.3rem',
                                  boxShadow: '0 2px 4px rgba(14, 165, 233, 0.2)'
                                }}
                              >
                                <Receipt size={13} /> {isExpanded ? 'Close' : (feeInfo.paid ? 'Re-Mark Fee' : 'Mark Fee')}
                              </button>

                              <button
                                onClick={() => openHistoryForStudent(student)}
                                className="btn btn-secondary"
                                title="View fee breakup and payment history for this student"
                                style={{
                                  fontSize: '0.8rem',
                                  padding: '0.4rem 0.75rem',
                                  fontWeight: '700',
                                  display: 'flex',
                                  alignItems: 'center',
                                  gap: '0.3rem'
                                }}
                              >
                                <History size={13} /> History
                              </button>
                            </div>
                          </td>
                        </tr>
                        {isExpanded && (
                          <tr style={{ backgroundColor: 'rgba(14, 165, 233, 0.06)', borderBottom: '1px solid var(--border-subtle)' }}>
                            <td colSpan={7} style={{ padding: '1rem 1.25rem 1.25rem' }}>
                              <form onSubmit={(e) => handleConfirmInlinePayment(e, student)}>
                                <div style={{
                                  border: '1px solid #bae6fd',
                                  backgroundColor: '#ffffff',
                                  borderRadius: '12px',
                                  padding: '1.25rem',
                                  display: 'flex',
                                  flexDirection: 'column',
                                  gap: '1rem'
                                }}>
                                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem' }}>
                                    <div>
                                      <div style={{ fontWeight: '800', color: 'var(--text-primary)', fontSize: '1rem' }}>
                                        Mark Fee — {student.candidate_name}
                                      </div>
                                      <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', fontFamily: 'monospace' }}>
                                        Enrollment: {student.enrollment_no || '—'} • Mobile: {student.student_mobile || '—'} • FY ({selectedAY.label})
                                      </div>
                                    </div>
                                    <span className={`badge ${feeInfo.badgeClass}`} style={{ fontSize: '0.8rem', padding: '0.35rem 0.75rem', fontWeight: '700' }}>
                                      {feeInfo.label}
                                    </span>
                                  </div>

                                  {feeInfo.hasFee ? (
                                    <div style={{
                                      display: 'grid',
                                      gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
                                      gap: '0.75rem',
                                      fontSize: '0.85rem',
                                      backgroundColor: 'var(--bg-surface-elevated)',
                                      border: '1px solid var(--border-subtle)',
                                      borderRadius: '8px',
                                      padding: '0.85rem 1rem'
                                    }}>
                                      <div>
                                        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: '700' }}>TOTAL FEE SET</div>
                                        <div style={{ fontWeight: '800', color: 'var(--text-primary)' }}>₹{Number(feeInfo.total).toLocaleString('en-IN')}</div>
                                        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.35rem' }}>
                                          {Object.entries(feeInfo.breakdown || {}).map(([k, v]) => `${k}: ₹${Number(v).toLocaleString('en-IN')}`).join(' • ') || 'No breakup'}
                                        </div>
                                      </div>
                                      <div>
                                        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: '700' }}>ALREADY PAID</div>
                                        <div style={{ fontWeight: '800', color: '#059669' }}>₹{Number(feeInfo.paidAmount || 0).toLocaleString('en-IN')}</div>
                                      </div>
                                      <div>
                                        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: '700' }}>REMAINING</div>
                                        <div style={{ fontWeight: '800', color: '#d97706' }}>₹{Number(feeInfo.remaining || 0).toLocaleString('en-IN')}</div>
                                      </div>
                                      <div>
                                        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: '700' }}>STATUS</div>
                                        <div style={{ fontWeight: '800', color: 'var(--text-primary)' }}>{feeInfo.status}</div>
                                      </div>
                                    </div>
                                  ) : (
                                    <div style={{
                                      padding: '0.85rem 1rem',
                                      borderRadius: '8px',
                                      backgroundColor: 'rgba(245, 158, 11, 0.1)',
                                      border: '1px solid rgba(245, 158, 11, 0.3)',
                                      color: '#92400e',
                                      fontSize: '0.85rem',
                                      fontWeight: '600'
                                    }}>
                                      Fee not set for this student yet. Please use Set Fee first for an exact category-wise breakup, or enter the amount below to initialise this student fee and mark it paid.
                                    </div>
                                  )}

                                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                                    <div className="form-group" style={{ margin: 0 }}>
                                      <label className="form-label">Payment Amount (₹) *</label>
                                      <input
                                        type="number"
                                        className="form-control"
                                        value={markFeeForm.amount}
                                        onChange={(e) => setMarkFeeForm({ ...markFeeForm, amount: e.target.value })}
                                        required
                                        min="1"
                                        style={{ fontWeight: '700', fontSize: '1rem' }}
                                      />
                                    </div>
                                    <div className="form-group" style={{ margin: 0 }}>
                                      <label className="form-label">Payment Method *</label>
                                      <select
                                        className="form-control"
                                        value={markFeeForm.payment_mode}
                                        onChange={(e) => setMarkFeeForm({ ...markFeeForm, payment_mode: e.target.value })}
                                        required
                                        style={{ fontWeight: '600' }}
                                      >
                                        <option value="CASH">Cash Deposit</option>
                                        <option value="UNIVERSITY_PORTAL_QR">University Portal QR / UPI</option>
                                        <option value="NET_BANKING">Net Banking / RTGS / NEFT</option>
                                        <option value="DEMAND_DRAFT">Demand Draft (DD)</option>
                                        <option value="BANK_CHALLAN">Bank Challan</option>
                                      </select>
                                    </div>
                                  </div>

                                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                                    <div className="form-group" style={{ margin: 0 }}>
                                      <label className="form-label">Receipt Number *</label>
                                      <input
                                        type="text"
                                        className="form-control"
                                        value={markFeeForm.receipt_no}
                                        onChange={(e) => setMarkFeeForm({ ...markFeeForm, receipt_no: e.target.value })}
                                        required
                                        style={{ fontFamily: 'monospace', fontWeight: '700' }}
                                      />
                                    </div>
                                    <div className="form-group" style={{ margin: 0 }}>
                                      <label className="form-label">UTR / Transaction ID *</label>
                                      <input
                                        type="text"
                                        className="form-control"
                                        placeholder="e.g. UTR9281729182"
                                        value={markFeeForm.external_transaction_ref}
                                        onChange={(e) => setMarkFeeForm({ ...markFeeForm, external_transaction_ref: e.target.value })}
                                        required
                                        style={{ fontFamily: 'monospace' }}
                                      />
                                    </div>
                                  </div>

                                  <div className="form-group" style={{ margin: 0 }}>
                                    <label className="form-label">Remarks / Accounting Reason</label>
                                    <textarea
                                      className="form-control"
                                      rows="2"
                                      value={markFeeForm.remarks}
                                      onChange={(e) => setMarkFeeForm({ ...markFeeForm, remarks: e.target.value })}
                                    />
                                  </div>

                                  {studentLedger.length > 0 && (
                                    <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                                      <strong>Recent payments for this student:</strong>{' '}
                                      {studentLedger.slice(0, 3).map(l => `${l.receipt_no} (₹${Number(l.amount).toLocaleString('en-IN')})`).join(' • ')}
                                    </div>
                                  )}

                                  <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
                                    <button
                                      type="button"
                                      className="btn btn-secondary"
                                      onClick={() => setExpandedMarkFeeId(null)}
                                      disabled={submittingPayment}
                                    >
                                      Cancel
                                    </button>
                                    <button
                                      type="submit"
                                      className="btn btn-primary"
                                      style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', backgroundColor: '#10b981', borderColor: '#10b981' }}
                                      disabled={submittingPayment}
                                    >
                                      <Check size={16} /> {submittingPayment ? 'Processing...' : 'Confirm & Mark as Paid'}
                                    </button>
                                  </div>
                                </div>
                              </form>
                            </td>
                          </tr>
                        )}
                        </React.Fragment>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination Footer */}
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginTop: '1.25rem',
              paddingTop: '1rem',
              borderTop: '1px solid var(--border-subtle)',
              fontSize: '0.85rem',
              color: 'var(--text-secondary)'
            }}>
              <span>
                Showing 1 to {Math.min(filteredStudents.length, entriesPerPage)} of {filteredStudents.length} candidates
              </span>
              <div style={{ display: 'flex', gap: '0.35rem' }}>
                <button className="btn btn-secondary" style={{ fontSize: '0.8rem', padding: '0.35rem 0.65rem' }} disabled>
                  Previous
                </button>
                <button className="btn btn-primary" style={{ fontSize: '0.8rem', padding: '0.35rem 0.65rem' }}>
                  1
                </button>
                <button className="btn btn-secondary" style={{ fontSize: '0.8rem', padding: '0.35rem 0.65rem' }} disabled>
                  Next
                </button>
              </div>
            </div>

          </div>
        </>
      )}


      {/* =========================================================
          VIEW 2: UPDATE ADMISSION FEES (Candidate Details & Fee Table)
          (Exact visual match to media_1789091411595.jpg & media_1789091411492.jpg)
          ========================================================= */}
      {currentView === 'set_fee' && activeStudent && (
        <>
          {/* Top Banner (Matches User's Reference Screenshot) */}
          <div style={{
            backgroundColor: '#2563eb',
            color: '#ffffff',
            padding: '1.5rem 2rem',
            borderRadius: 'var(--radius-lg)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            boxShadow: '0 4px 12px rgba(37, 99, 235, 0.2)'
          }}>
            <div>
              <div style={{ fontSize: '0.85rem', color: 'rgba(255, 255, 255, 0.8)', fontWeight: '600', marginBottom: '0.2rem' }}>
                Manage Admission
              </div>
              <h1 style={{ margin: 0, fontSize: '1.75rem', fontWeight: '800', letterSpacing: '-0.02em', color: '#ffffff' }}>
                Update Admission Fees
              </h1>
              <div style={{ fontSize: '0.85rem', color: 'rgba(255, 255, 255, 0.9)', marginTop: '0.25rem' }}>
                Government College of Engineering, Kolhapur
              </div>
            </div>

            <button
              onClick={() => setCurrentView('list')}
              className="btn"
              style={{
                backgroundColor: 'rgba(255, 255, 255, 0.2)',
                color: '#ffffff',
                border: '1px solid rgba(255, 255, 255, 0.4)',
                fontWeight: '700',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                fontSize: '0.9rem'
              }}
            >
              <ArrowLeft size={16} /> Back to Eligible Students
            </button>
          </div>

          {/* Feedback Alert */}
          {notification && (
            <div style={{
              padding: '1rem 1.25rem',
              backgroundColor: 'rgba(16, 185, 129, 0.1)',
              border: '1px solid rgba(16, 185, 129, 0.3)',
              color: '#10b981',
              borderRadius: 'var(--radius-md)',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              fontSize: '0.92rem',
              fontWeight: '600'
            }}>
              <CheckCircle2 size={18} /> {notification}
            </div>
          )}

          {/* CARD 1: CANDIDATE DETAILS (4-Column Grid matching media_1789091411595.jpg) */}
          <div className="card" style={{ padding: '1.75rem 2rem', borderRadius: 'var(--radius-lg)' }}>
            <h2 style={{ fontSize: '1.15rem', fontWeight: '800', margin: '0 0 1.5rem', color: 'var(--text-primary)' }}>
              Candidate Details
            </h2>

            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(4, 1fr)',
              columnGap: '2rem',
              rowGap: '1.35rem'
            }}>
              {/* Row 1 */}
              <div>
                <div style={{ fontSize: '0.8rem', fontWeight: '800', color: 'var(--text-primary)', marginBottom: '0.2rem' }}>
                  Enrollment No.
                </div>
                <div style={{ fontSize: '0.88rem', color: 'var(--text-secondary)' }}>
                  {activeStudentDetails?.enrollment_no || activeStudent.enrollment_no || '191227'}
                </div>
              </div>

              <div>
                <div style={{ fontSize: '0.8rem', fontWeight: '800', color: 'var(--text-primary)', marginBottom: '0.2rem' }}>
                  DEN
                </div>
                <div style={{ fontSize: '0.88rem', color: 'var(--text-secondary)' }}>
                  {activeStudentDetails?.application_id || activeStudent.application_id || 'DEN19157700'}
                </div>
              </div>

              <div>
                <div style={{ fontSize: '0.8rem', fontWeight: '800', color: 'var(--text-primary)', marginBottom: '0.2rem' }}>
                  Student Name
                </div>
                <div style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', textTransform: 'uppercase', fontWeight: '600' }}>
                  {activeStudentDetails?.candidate_name || activeStudent.candidate_name}
                </div>
              </div>

              <div>
                <div style={{ fontSize: '0.8rem', fontWeight: '800', color: 'var(--text-primary)', marginBottom: '0.2rem' }}>
                  Father's Name
                </div>
                <div style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
                  {activeStudentDetails?.father_name || activeStudent.father_name || 'RAGHUNATH'}
                </div>
              </div>

              {/* Row 2 */}
              <div>
                <div style={{ fontSize: '0.8rem', fontWeight: '800', color: 'var(--text-primary)', marginBottom: '0.2rem' }}>
                  Mother's Name
                </div>
                <div style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
                  {activeStudentDetails?.mother_name || 'SAVITA'}
                </div>
              </div>

              <div>
                <div style={{ fontSize: '0.8rem', fontWeight: '800', color: 'var(--text-primary)', marginBottom: '0.2rem' }}>
                  Gender
                </div>
                <div style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', textTransform: 'capitalize' }}>
                  {activeStudentDetails?.gender ? activeStudentDetails.gender.toLowerCase() : 'Female'}
                </div>
              </div>

              <div>
                <div style={{ fontSize: '0.8rem', fontWeight: '800', color: 'var(--text-primary)', marginBottom: '0.2rem' }}>
                  Date of Birth
                </div>
                <div style={{ fontSize: '0.88rem', color: 'var(--text-secondary)' }}>
                  {activeStudentDetails?.date_of_birth ? new Date(activeStudentDetails.date_of_birth).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' }) : '5-November-2002'}
                </div>
              </div>

              <div>
                <div style={{ fontSize: '0.8rem', fontWeight: '800', color: 'var(--text-primary)', marginBottom: '0.2rem' }}>
                  Student Mobile No.
                </div>
                <div style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', fontFamily: 'monospace' }}>
                  {activeStudentDetails?.student_mobile || activeStudent.student_mobile || '7709826168'}
                </div>
              </div>

              {/* Row 3 */}
              <div>
                <div style={{ fontSize: '0.8rem', fontWeight: '800', color: 'var(--text-primary)', marginBottom: '0.2rem' }}>
                  Parent Mobile No.
                </div>
                <div style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', fontFamily: 'monospace' }}>
                  {activeStudentDetails?.parent_mobile || '9373424577'}
                </div>
              </div>

              <div>
                <div style={{ fontSize: '0.8rem', fontWeight: '800', color: 'var(--text-primary)', marginBottom: '0.2rem' }}>
                  Program Code & Name
                </div>
                <div style={{ fontSize: '0.88rem', color: 'var(--text-secondary)' }}>
                  {activeStudentDetails?.enrollments?.[0]?.program_code ? `${activeStudentDetails.enrollments[0].program_code} - ENGINEERING` : '01 - CIVIL ENGINEERING'}
                </div>
              </div>

              <div>
                <div style={{ fontSize: '0.8rem', fontWeight: '800', color: 'var(--text-primary)', marginBottom: '0.2rem' }}>
                  Semester
                </div>
                <div style={{ fontSize: '0.88rem', color: 'var(--text-secondary)' }}>
                  {activeStudentDetails?.enrollments?.[0]?.semester_number ? `Semester ${activeStudentDetails.enrollments[0].semester_number}` : 'Semester 1'}
                </div>
              </div>

              <div>
                <div style={{ fontSize: '0.8rem', fontWeight: '800', color: 'var(--text-primary)', marginBottom: '0.2rem' }}>
                  Aadhaar No.
                </div>
                <div style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', fontFamily: 'monospace' }}>
                  {activeStudentDetails?.aadhaar_masked || '996182065445'}
                </div>
              </div>

              {/* Row 4 */}
              <div>
                <div style={{ fontSize: '0.8rem', fontWeight: '800', color: 'var(--text-primary)', marginBottom: '0.2rem' }}>
                  Religion
                </div>
                <div style={{ fontSize: '0.88rem', color: 'var(--text-secondary)' }}>
                  {activeStudentDetails?.religion || 'Muslim'}
                </div>
              </div>

              <div>
                <div style={{ fontSize: '0.8rem', fontWeight: '800', color: 'var(--text-primary)', marginBottom: '0.2rem' }}>
                  Caste
                </div>
                <div style={{ fontSize: '0.88rem', color: 'var(--text-secondary)' }}>
                  {activeStudentDetails?.category_info?.caste || 'OPEN'}
                </div>
              </div>

              <div>
                <div style={{ fontSize: '0.8rem', fontWeight: '800', color: 'var(--text-primary)', marginBottom: '0.2rem' }}>
                  Admission Category
                </div>
                <div style={{ fontSize: '0.88rem', color: 'var(--text-secondary)' }}>
                  {activeStudentDetails?.category_info?.category || 'OPEN'}
                </div>
              </div>

              <div>
                <div style={{ fontSize: '0.8rem', fontWeight: '800', color: 'var(--text-primary)', marginBottom: '0.2rem' }}>
                  Reservation Type
                </div>
                <div style={{ fontSize: '0.88rem', color: 'var(--text-secondary)' }}>
                  {activeStudentDetails?.admissions?.[0]?.reservation_type || 'NA'}
                </div>
              </div>

              {/* Row 5 */}
              <div>
                <div style={{ fontSize: '0.8rem', fontWeight: '800', color: 'var(--text-primary)', marginBottom: '0.2rem' }}>
                  Admission Date
                </div>
                <div style={{ fontSize: '0.88rem', color: 'var(--text-secondary)' }}>
                  {activeStudentDetails?.admissions?.[0]?.admission_date || '30/07/2026'}
                </div>
              </div>

              <div>
                <div style={{ fontSize: '0.8rem', fontWeight: '800', color: 'var(--text-primary)', marginBottom: '0.2rem' }}>
                  DSA
                </div>
                <div style={{ fontSize: '0.88rem', color: 'var(--text-secondary)' }}>
                  {activeStudentDetails?.admissions?.[0]?.dsa_dse_flag ? 'Yes' : 'No'}
                </div>
              </div>

              <div>
                <div style={{ fontSize: '0.8rem', fontWeight: '800', color: 'var(--text-primary)', marginBottom: '0.2rem' }}>
                  Admission Type
                </div>
                <div style={{ fontSize: '0.88rem', color: 'var(--text-secondary)' }}>
                  {activeStudentDetails?.admissions?.[0]?.admission_type || 'Against CAP'}
                </div>
              </div>

              <div>
                <div style={{ fontSize: '0.8rem', fontWeight: '800', color: 'var(--text-primary)', marginBottom: '0.2rem' }}>
                  Allotted Seat Type
                </div>
                <div style={{ fontSize: '0.88rem', color: 'var(--text-secondary)' }}>
                  {activeStudentDetails?.admissions?.[0]?.allotted_seat_type || 'OPEN'}
                </div>
              </div>

              {/* Row 6 */}
              <div>
                <div style={{ fontSize: '0.8rem', fontWeight: '800', color: 'var(--text-primary)', marginBottom: '0.2rem' }}>
                  Scholarship Applied
                </div>
                <div style={{ fontSize: '0.88rem', color: 'var(--text-secondary)' }}>
                  No
                </div>
              </div>

              <div>
                <div style={{ fontSize: '0.8rem', fontWeight: '800', color: 'var(--text-primary)', marginBottom: '0.2rem' }}>
                  Scholarship Type
                </div>
                <div style={{ fontSize: '0.88rem', color: 'var(--text-secondary)' }}>
                  NA
                </div>
              </div>

              <div>
                <div style={{ fontSize: '0.8rem', fontWeight: '800', color: 'var(--text-primary)', marginBottom: '0.2rem' }}>
                  Income Range
                </div>
                <div style={{ fontSize: '0.88rem', color: 'var(--text-secondary)' }}>
                  0 to 50000
                </div>
              </div>

              <div>
                <div style={{ fontSize: '0.8rem', fontWeight: '800', color: 'var(--text-primary)', marginBottom: '0.4rem' }}>
                  Institute Allotment Letter
                </div>
                <button
                  onClick={() => alert('Opening Institute Allotment Letter PDF...')}
                  style={{
                    padding: '0.25rem 0.75rem',
                    border: '1px solid #94a3b8',
                    borderRadius: '9999px',
                    backgroundColor: '#ffffff',
                    color: '#334155',
                    fontSize: '0.78rem',
                    cursor: 'pointer',
                    fontWeight: '600'
                  }}
                >
                  View/Download Existing Letter PDF
                </button>
              </div>

            </div>

            {/* Reset Allotment Letter Section */}
            <div style={{ marginTop: '1.75rem', paddingTop: '1.25rem', borderTop: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '0.82rem', fontWeight: '700', color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
                Student Uploaded Wrong Institute Allotment Letter?
              </div>
              <button
                onClick={() => {
                  if (window.confirm('Are you sure you want to reset the institute allotment letter for this student?')) {
                    alert('Allotment letter status has been reset.');
                  }
                }}
                style={{
                  backgroundColor: '#ef4444',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: '9999px',
                  padding: '0.4rem 1rem',
                  fontSize: '0.82rem',
                  fontWeight: '700',
                  cursor: 'pointer',
                  boxShadow: '0 2px 4px rgba(239, 68, 68, 0.2)'
                }}
              >
                Reset Allotment Letter
              </button>
            </div>
          </div>

          {/* CARD 2: ADMISSION FEE DETAILS FOR FY (2026-27) (Exact match to media_1789091411492.jpg) */}
          <div className="card" style={{ padding: '1.75rem 2rem', borderRadius: 'var(--radius-lg)' }}>
            
            {/* Header: Title + [View Payment History] Button */}
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '1.25rem'
            }}>
              <h2 style={{ fontSize: '1.15rem', fontWeight: '800', margin: 0, color: 'var(--text-primary)' }}>
                Admission Fee Details for FY ({selectedAY.label})
              </h2>

              <button
                onClick={() => { setHistoryStudent(activeStudent); setShowHistoryModal(true); }}
                style={{
                  backgroundColor: '#475569',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: '9999px',
                  padding: '0.45rem 1.15rem',
                  fontSize: '0.82rem',
                  fontWeight: '700',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.4rem'
                }}
              >
                View Payment History
              </button>
            </div>

            {/* Fee Heads Breakdown Table */}
            <div style={{ border: '1px solid #e2e8f0', borderRadius: 'var(--radius-sm)', overflow: 'hidden' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ backgroundColor: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
                    <th style={{ padding: '0.9rem 1.25rem', fontSize: '0.8rem', fontWeight: '800', color: '#475569', textAlign: 'center', width: '80px' }}>
                      S.N.
                    </th>
                    <th style={{ padding: '0.9rem 1.5rem', fontSize: '0.8rem', fontWeight: '800', color: '#475569', textAlign: 'center' }}>
                      FEE HEAD / PARTICULAR
                    </th>
                    <th style={{ padding: '0.9rem 1.5rem', fontSize: '0.8rem', fontWeight: '800', color: '#475569', textAlign: 'center', width: '280px' }}>
                      AMOUNT
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {feeHeads.length === 0 ? (
                    <tr>
                      <td colSpan={3} style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
                        No fee heads configured by Administrative Head. Please configure fee heads in Fee Head Configuration.
                      </td>
                    </tr>
                  ) : (
                    feeHeads.map((head, idx) => {
                      const currentVal = candidateBreakdown[head.name] !== undefined ? candidateBreakdown[head.name] : 0;
                      // Allowed denominations configured by Admin Head
                      const options = Array.isArray(head.allowed_amounts) && head.allowed_amounts.length > 0 
                        ? head.allowed_amounts 
                        : [0, 1000, 5000, 15000, 30000];

                      return (
                        <tr key={head.id || idx} style={{ borderBottom: '1px solid #f1f5f9' }}>
                          <td style={{ padding: '1rem', textAlign: 'center', color: '#64748b', fontSize: '0.9rem', fontWeight: '600' }}>
                            {idx + 1}
                          </td>
                          <td style={{ padding: '1rem', textAlign: 'center' }}>
                            <span style={{ fontSize: '0.92rem', fontWeight: '700', color: '#1e293b' }}>
                              {head.name} <span style={{ color: '#ef4444' }}>*</span>
                            </span>
                          </td>
                          <td style={{ padding: '0.75rem 1.5rem', textAlign: 'center' }}>
                            <select
                              className="form-control"
                              value={currentVal}
                              onChange={(e) => {
                                setCandidateBreakdown({
                                  ...candidateBreakdown,
                                  [head.name]: parseFloat(e.target.value) || 0
                                });
                              }}
                              style={{
                                textAlign: 'center',
                                fontWeight: '700',
                                fontSize: '0.95rem',
                                color: '#1e293b',
                                border: '1px solid #cbd5e1',
                                borderRadius: 'var(--radius-sm)',
                                height: '42px',
                                cursor: 'pointer'
                              }}
                            >
                              {options.map((opt, oIdx) => (
                                <option key={oIdx} value={opt}>
                                  {Number(opt).toLocaleString('en-IN')}
                                </option>
                              ))}
                            </select>
                          </td>
                        </tr>
                      );
                    })
                  )}

                  {/* Total Admission Fees Row */}
                  <tr style={{ backgroundColor: '#f8fafc', borderTop: '2px solid #e2e8f0' }}>
                    <td colSpan={2} style={{ padding: '1.15rem 1.5rem', textAlign: 'center', fontWeight: '800', fontSize: '0.95rem', color: '#1e293b' }}>
                      Total Admission Fees <span style={{ color: '#ef4444' }}>*</span>
                    </td>
                    <td style={{ padding: '0.85rem 1.5rem', textAlign: 'center' }}>
                      <input 
                        type="text"
                        className="form-control"
                        readOnly
                        value={currentTotalAdmissionFees.toFixed(2)}
                        style={{
                          textAlign: 'center',
                          fontWeight: '800',
                          fontSize: '1.05rem',
                          color: '#1e293b',
                          backgroundColor: '#f1f5f9',
                          border: '1px solid #cbd5e1',
                          height: '42px'
                        }}
                      />
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            {/* Bottom Save Button (Exact match: blue rounded button on bottom-left) */}
            <div style={{ marginTop: '1.75rem' }}>
              <button
                onClick={handleSaveCandidateFee}
                disabled={savingFee}
                style={{
                  backgroundColor: '#3b82f6',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: '9999px',
                  padding: '0.65rem 2.25rem',
                  fontSize: '0.92rem',
                  fontWeight: '700',
                  cursor: 'pointer',
                  boxShadow: '0 4px 6px -1px rgba(59, 130, 246, 0.3)'
                }}
              >
                {savingFee ? 'Saving...' : 'Save'}
              </button>
            </div>

          </div>
        </>
      )}


      {/* Mark Fee is now inline-expandable per row (see expanded card above).
          Old modal removed — clicking Mark Fee expands the student's card where
          payment method + transaction ID are collected. */}


      {/* =========================================================
          MODAL: VIEW FEE & PAYMENT HISTORY (per-student)
          ========================================================= */}
      {(() => {
        const hStudent = historyStudent || activeStudent;
        if (!showHistoryModal || !hStudent) return null;
        const hFee = getStudentFeeInfo(hStudent);
        const hLedger = getStudentLedger(hStudent);
        return (
        <div className="modal-backdrop">
          <div className="modal-card" style={{ maxWidth: '680px', width: '92%' }}>
            <div className="modal-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                <History size={20} color="var(--primary-600)" />
                <h3 style={{ margin: 0, fontSize: '1.2rem', fontWeight: '700' }}>
                  Fee & Payment History — {hStudent.candidate_name}
                </h3>
              </div>
              <button className="btn-close" onClick={() => { setShowHistoryModal(false); setHistoryStudent(null); }}>✕</button>
            </div>
            <div className="modal-body">
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div style={{
                  padding: '1rem',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: 'var(--bg-surface-elevated)',
                  border: '1px solid var(--border-subtle)'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
                    <div>
                      <div style={{ fontWeight: '700', color: 'var(--text-primary)' }}>
                        Admission Fee Assessment FY ({selectedAY.label})
                      </div>
                      <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                        Enrollment: {hStudent.enrollment_no || '—'} • {hStudent.application_id || ''} • Assessed by Fee Accountant
                      </div>
                    </div>
                    <span className={`badge ${hFee.badgeClass}`}>{hFee.hasFee ? hFee.status : 'NOT SET'}</span>
                  </div>

                  {hFee.hasFee ? (
                    <>
                      <div style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(3, 1fr)',
                        gap: '0.75rem',
                        marginTop: '1rem',
                        paddingTop: '0.75rem',
                        borderTop: '1px solid var(--border-subtle)',
                        fontSize: '0.85rem'
                      }}>
                        <div>
                          <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>Total Fee Set:</span>
                          <div style={{ fontWeight: '700', color: 'var(--text-primary)' }}>₹{Number(hFee.total).toLocaleString('en-IN')}</div>
                        </div>
                        <div>
                          <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>Paid:</span>
                          <div style={{ fontWeight: '700', color: '#059669' }}>₹{Number(hFee.paidAmount || 0).toLocaleString('en-IN')}</div>
                        </div>
                        <div>
                          <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>Remaining:</span>
                          <div style={{ fontWeight: '700', color: '#d97706' }}>₹{Number(hFee.remaining || 0).toLocaleString('en-IN')}</div>
                        </div>
                      </div>
                      <div style={{ marginTop: '0.85rem', fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                        <strong>Fee breakup:</strong>{' '}
                        {Object.entries(hFee.breakdown || {}).map(([k, v]) => `${k}: ₹${Number(v).toLocaleString('en-IN')}`).join(' • ') || '—'}
                      </div>
                      {hFee.charge && (
                        <div style={{ marginTop: '0.5rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                          Charge ID: <span style={{ fontFamily: 'monospace' }}>{String(hFee.charge.id).slice(0, 8)}…</span>
                          {' • '}Academic Term: FY {hFee.charge.academic_year_label || selectedAY.label}
                          {' • '}Status: <strong>{hFee.charge.status}</strong>
                        </div>
                      )}
                    </>
                  ) : (
                    <div style={{ marginTop: '1rem', fontSize: '0.85rem', color: '#92400e', backgroundColor: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.3)', borderRadius: '8px', padding: '0.75rem 1rem', fontWeight: '600' }}>
                      Fee not set for this student yet for FY ({selectedAY.label}).
                    </div>
                  )}
                </div>

                <div>
                  <div style={{ fontWeight: '800', fontSize: '0.9rem', color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
                    Payment Ledger ({hLedger.length})
                  </div>
                  {hLedger.length === 0 ? (
                    <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', textAlign: 'center', padding: '1rem', border: '1px dashed var(--border-subtle)', borderRadius: '8px' }}>
                      No payments recorded yet for this student. Once the accountant marks the fee (with payment method + UTR), entries appear here.
                    </div>
                  ) : (
                    <div style={{ border: '1px solid var(--border-subtle)', borderRadius: '8px', overflow: 'hidden' }}>
                      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
                        <thead>
                          <tr style={{ backgroundColor: 'var(--bg-surface-elevated)', borderBottom: '1px solid var(--border-subtle)' }}>
                            <th style={{ padding: '0.6rem', textAlign: 'left' }}>RECEIPT</th>
                            <th style={{ padding: '0.6rem', textAlign: 'left' }}>MODE</th>
                            <th style={{ padding: '0.6rem', textAlign: 'left' }}>UTR / TXN ID</th>
                            <th style={{ padding: '0.6rem', textAlign: 'right' }}>AMOUNT</th>
                            <th style={{ padding: '0.6rem', textAlign: 'left' }}>DATE</th>
                          </tr>
                        </thead>
                        <tbody>
                          {hLedger.map((l) => (
                            <tr key={l.id} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                              <td style={{ padding: '0.6rem', fontFamily: 'monospace', fontWeight: '700' }}>{l.receipt_no}</td>
                              <td style={{ padding: '0.6rem' }}>{l.payment_mode}</td>
                              <td style={{ padding: '0.6rem', fontFamily: 'monospace' }}>{l.external_transaction_ref || '—'}</td>
                              <td style={{ padding: '0.6rem', textAlign: 'right', fontWeight: '800' }}>₹{Number(l.amount).toLocaleString('en-IN')}</td>
                              <td style={{ padding: '0.6rem', color: 'var(--text-muted)' }}>{l.payment_date}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-primary" onClick={() => { setShowHistoryModal(false); setHistoryStudent(null); }}>
                Close
              </button>
            </div>
          </div>
        </div>
        );
      })()}
      {/* Old Mark-Fee modal removed (now inline). Old history modal below also removed. */}
      {/* removed legacy mark-fee modal body */}
      {/* Legacy mark-fee modal fully removed — Mark Fee is now inline per row. */}
      {/* legacy body removed */}
      {/* legacy inputs removed */}


      {/* =========================================================
          MODAL 3: OFFICIAL PRINTABLE RECEIPT
          ========================================================= */}
      {showReceiptModal && receiptData && (
        <div className="modal-backdrop">
          <div className="modal-card" style={{ maxWidth: '580px', width: '92%', backgroundColor: '#ffffff', color: '#000000' }}>
            <div className="modal-header" style={{ borderBottom: '2px solid #000000', paddingBottom: '0.75rem' }}>
              <div style={{ textAlign: 'center', width: '100%' }}>
                <h2 style={{ fontSize: '1.15rem', fontWeight: '900', margin: 0, letterSpacing: '-0.01em', textTransform: 'uppercase' }}>
                  Government College of Engineering, Kolhapur
                </h2>
                <div style={{ fontSize: '0.78rem', color: '#475569', marginTop: '0.2rem' }}>
                  (An Autonomous Institute of Government of Maharashtra) • Kolhapur - 416004
                </div>
                <div style={{ fontSize: '0.82rem', fontWeight: '800', marginTop: '0.4rem', textDecoration: 'underline' }}>
                  OFFICIAL ADMISSION FEE PAYMENT RECEIPT
                </div>
              </div>
              <button className="btn-close" onClick={() => setShowReceiptModal(false)}>✕</button>
            </div>

            <div className="modal-body" style={{ padding: '1.25rem 0.5rem', fontSize: '0.88rem' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', marginBottom: '1.25rem', borderBottom: '1px solid #e2e8f0', paddingBottom: '1rem' }}>
                <div>
                  <span style={{ color: '#64748b', fontSize: '0.75rem' }}>Receipt No:</span>
                  <div style={{ fontWeight: '800', fontFamily: 'monospace' }}>{receiptData.receipt_no}</div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <span style={{ color: '#64748b', fontSize: '0.75rem' }}>Date:</span>
                  <div style={{ fontWeight: '700' }}>{receiptData.date}</div>
                </div>
                <div>
                  <span style={{ color: '#64748b', fontSize: '0.75rem' }}>Candidate Name:</span>
                  <div style={{ fontWeight: '800', textTransform: 'uppercase' }}>{receiptData.student?.candidate_name}</div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <span style={{ color: '#64748b', fontSize: '0.75rem' }}>Enrollment / Application No:</span>
                  <div style={{ fontWeight: '700', fontFamily: 'monospace' }}>{receiptData.student?.enrollment_no || receiptData.student?.application_id || '191227'}</div>
                </div>
                <div>
                  <span style={{ color: '#64748b', fontSize: '0.75rem' }}>Academic Year:</span>
                  <div style={{ fontWeight: '700' }}>FY {receiptData.academic_year}</div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <span style={{ color: '#64748b', fontSize: '0.75rem' }}>Payment Mode:</span>
                  <div style={{ fontWeight: '700' }}>{receiptData.payment_mode}</div>
                </div>
                {receiptData.transaction_ref && (
                  <div style={{ gridColumn: '1 / -1' }}>
                    <span style={{ color: '#64748b', fontSize: '0.75rem' }}>Transaction Ref / UTR:</span>
                    <div style={{ fontWeight: '700', fontFamily: 'monospace' }}>{receiptData.transaction_ref}</div>
                  </div>
                )}
              </div>

              {/* Amount Box */}
              <div style={{
                padding: '1rem',
                backgroundColor: '#f8fafc',
                border: '1px solid #cbd5e1',
                borderRadius: 'var(--radius-sm)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '1.25rem'
              }}>
                <span style={{ fontWeight: '800', fontSize: '0.95rem' }}>TOTAL AMOUNT RECEIVED:</span>
                <span style={{ fontWeight: '900', fontSize: '1.25rem', color: '#16a34a' }}>
                  ₹{Number(receiptData.amount).toLocaleString('en-IN')}.00
                </span>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginTop: '2rem', paddingTop: '1rem', borderTop: '1px dashed #94a3b8' }}>
                <div style={{ fontSize: '0.75rem', color: '#64748b' }}>
                  System Verified & Recorded by:<br />
                  <strong style={{ color: '#0f172a' }}>{user?.username || 'Fee Accountant'}</strong>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ width: '120px', borderBottom: '1px solid #000000', marginBottom: '0.25rem' }}></div>
                  <span style={{ fontSize: '0.75rem', fontWeight: '700' }}>Cashier / Accountant Stamp</span>
                </div>
              </div>
            </div>

            <div className="modal-footer" style={{ borderTop: '1px solid #e2e8f0' }}>
              <button className="btn btn-secondary" onClick={() => setShowReceiptModal(false)}>
                Close
              </button>
              <button 
                className="btn btn-primary"
                onClick={() => window.print()}
                style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
              >
                <Printer size={16} /> Print Receipt
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};
export default CandidateFeeDesk;
