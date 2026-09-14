import React, { useState, useEffect } from 'react';
import { 
  CreditCard, 
  QrCode, 
  CheckCircle2, 
  Clock, 
  AlertTriangle, 
  Search, 
  Filter, 
  Receipt, 
  History, 
  Lock, 
  Unlock, 
  Plus, 
  RefreshCw, 
  FileText, 
  ExternalLink,
  ChevronRight,
  ShieldCheck,
  RotateCcw,
  ArrowUpRight,
  DollarSign
} from 'lucide-react';
import { CandidateFeeDesk } from './CandidateFeeDesk';

export const FeeManagementPage = () => {
  const [activeTab, setActiveTab] = useState('candidate_desk'); // 'candidate_desk' | 'accounts' | 'structures' | 'ledger'
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [loading, setLoading] = useState(false);

  // Modals state
  const [showQrModal, setShowQrModal] = useState(false);
  const [showRecordModal, setShowRecordModal] = useState(false);
  const [showAssessModal, setShowAssessModal] = useState(false);
  const [showReversalModal, setShowReversalModal] = useState(false);
  const [selectedAccount, setSelectedAccount] = useState(null);
  const [selectedLedgerEntry, setSelectedLedgerEntry] = useState(null);

  // Form states
  const [paymentForm, setPaymentForm] = useState({
    charge_id: '',
    amount: '',
    receipt_no: '',
    external_transaction_ref: '',
    payment_mode: 'UNIVERSITY_PORTAL_QR',
    reason: ''
  });

  const [reversalForm, setReversalForm] = useState({
    payment_entry_id: '',
    reason: '',
    reversal_receipt_no: ''
  });

  const [assessForm, setAssessForm] = useState({
    academic_year_id: '',
    department_id: '',
    program_id: '',
    due_date: '2024-10-31'
  });

  // Mock initial state data representing live institutional records
  const [accounts, setAccounts] = useState([
    {
      id: 'acc-1',
      student_id: 'stu-1',
      candidate_name: 'Rahul Sharma',
      enrollment_no: 'ENR2024001',
      application_id: 'APP2024001',
      category: 'OPEN',
      department_name: 'Mechanical Engineering',
      program_name: 'B.Tech Mechanical',
      total_billed: 80000.0,
      total_paid: 80000.0,
      outstanding_balance: 0.0,
      charges: [
        {
          id: 'chg-1',
          fee_structure_name: 'B.Tech ME Open 2024-25',
          academic_year_label: '2024-25',
          total_amount: 80000.0,
          paid_amount: 80000.0,
          remaining_balance: 0.0,
          status: 'PAID',
          due_date: '2024-09-30'
        }
      ]
    },
    {
      id: 'acc-2',
      student_id: 'stu-2',
      candidate_name: 'Amit Kamble',
      enrollment_no: 'ENR2024002',
      application_id: 'APP2024002',
      category: 'SC',
      department_name: 'Mechanical Engineering',
      program_name: 'B.Tech Mechanical',
      total_billed: 10000.0,
      total_paid: 0.0,
      outstanding_balance: 10000.0,
      charges: [
        {
          id: 'chg-2',
          fee_structure_name: 'B.Tech ME SC 2024-25',
          academic_year_label: '2024-25',
          total_amount: 10000.0,
          paid_amount: 0.0,
          remaining_balance: 10000.0,
          status: 'UNPAID',
          due_date: '2024-09-30'
        }
      ]
    },
    {
      id: 'acc-3',
      student_id: 'stu-3',
      candidate_name: 'Pooja Patil',
      enrollment_no: 'ENR2024099',
      application_id: 'APP2024099',
      category: 'OBC',
      department_name: 'Civil Engineering',
      program_name: 'B.Tech Civil',
      total_billed: 50000.0,
      total_paid: 25000.0,
      outstanding_balance: 25000.0,
      charges: [
        {
          id: 'chg-3',
          fee_structure_name: 'Civil Annual 2024-25',
          academic_year_label: '2024-25',
          total_amount: 50000.0,
          paid_amount: 25000.0,
          remaining_balance: 25000.0,
          status: 'PARTIALLY_PAID',
          due_date: '2024-10-15'
        }
      ]
    }
  ]);

  const [structures, setStructures] = useState([
    {
      id: 'st-1',
      name: 'B.Tech ME Open Annual Fee 2024-25',
      academic_year_label: '2024-25',
      department_name: 'Mechanical Engineering',
      category: 'OPEN',
      total_amount: 80000.0,
      is_locked: true,
      items: [
        { fee_head_name: 'Tuition Fee', amount: 70000.0 },
        { fee_head_name: 'Development Fee', amount: 10000.0 }
      ]
    },
    {
      id: 'st-2',
      name: 'B.Tech ME SC/ST Annual Fee 2024-25',
      academic_year_label: '2024-25',
      department_name: 'Mechanical Engineering',
      category: 'SC',
      total_amount: 10000.0,
      is_locked: true,
      items: [
        { fee_head_name: 'Development Fee', amount: 10000.0 }
      ]
    },
    {
      id: 'st-3',
      name: 'Civil Engineering General 2024-25',
      academic_year_label: '2024-25',
      department_name: 'Civil Engineering',
      category: 'ALL',
      total_amount: 50000.0,
      is_locked: true,
      items: [
        { fee_head_name: 'College Annual Fee', amount: 50000.0 }
      ]
    }
  ]);

  const [ledgerEntries, setLedgerEntries] = useState([
    {
      id: 'led-1',
      receipt_no: 'REC-2024-001',
      entry_type: 'PAYMENT',
      student_name: 'Rahul Sharma',
      student_enrollment_no: 'ENR2024001',
      fee_structure_name: 'B.Tech ME Open 2024-25',
      amount: 80000.0,
      external_transaction_ref: 'UTR9876543210',
      payment_mode: 'UNIVERSITY_PORTAL_QR',
      payment_date: '2024-08-15',
      recorded_by_name: 'fee_accountant',
      reason: 'Confirmed via University NetBanking portal receipt'
    },
    {
      id: 'led-2',
      receipt_no: 'REC-2024-002',
      entry_type: 'PAYMENT',
      student_name: 'Pooja Patil',
      student_enrollment_no: 'ENR2024099',
      fee_structure_name: 'Civil Annual 2024-25',
      amount: 25000.0,
      external_transaction_ref: 'UPI-UNIV-452109',
      payment_mode: 'UNIVERSITY_PORTAL_QR',
      payment_date: '2024-08-20',
      recorded_by_name: 'fee_accountant',
      reason: 'First installment verified via university portal QR scan'
    }
  ]);

  // Aggregate Metrics
  const totalBilled = accounts.reduce((acc, a) => acc + a.total_billed, 0);
  const totalPaid = accounts.reduce((acc, a) => acc + a.total_paid, 0);
  const totalOutstanding = accounts.reduce((acc, a) => acc + a.outstanding_balance, 0);
  const collectionRate = totalBilled > 0 ? ((totalPaid / totalBilled) * 100).toFixed(1) : 0;

  // Filtered Accounts
  const filteredAccounts = accounts.filter(acc => {
    const matchesSearch = 
      acc.candidate_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      acc.enrollment_no.toLowerCase().includes(searchQuery.toLowerCase()) ||
      acc.application_id.toLowerCase().includes(searchQuery.toLowerCase());
    
    if (!matchesSearch) return false;

    if (statusFilter === 'PAID') return acc.outstanding_balance === 0 && acc.total_billed > 0;
    if (statusFilter === 'UNPAID') return acc.outstanding_balance > 0 && acc.total_paid === 0;
    if (statusFilter === 'PARTIAL') return acc.outstanding_balance > 0 && acc.total_paid > 0;
    return true;
  });

  // Handle Recording Payment
  const openRecordPaymentModal = (account) => {
    setSelectedAccount(account);
    const activeCharge = account.charges.find(c => c.status !== 'PAID') || account.charges[0];
    setPaymentForm({
      charge_id: activeCharge?.id || '',
      amount: activeCharge?.remaining_balance || '',
      receipt_no: `REC-${Date.now().toString().slice(-6)}`,
      external_transaction_ref: '',
      payment_mode: 'UNIVERSITY_PORTAL_QR',
      reason: 'Verified against university payment portal receipt'
    });
    setShowRecordModal(true);
  };

  const handleRecordPaymentSubmit = (e) => {
    e.preventDefault();
    if (!selectedAccount) return;

    const paymentAmount = parseFloat(paymentForm.amount);
    if (isNaN(paymentAmount) || paymentAmount <= 0) {
      alert('Please enter a valid positive payment amount.');
      return;
    }

    // Update internal state
    const updatedAccounts = accounts.map(acc => {
      if (acc.id === selectedAccount.id) {
        const updatedCharges = acc.charges.map(chg => {
          if (chg.id === paymentForm.charge_id) {
            const newPaid = chg.paid_amount + paymentAmount;
            const newBal = chg.total_amount - newPaid;
            const newStatus = newBal <= 0 ? 'PAID' : 'PARTIALLY_PAID';
            return {
              ...chg,
              paid_amount: newPaid,
              remaining_balance: Math.max(0, newBal),
              status: newStatus
            };
          }
          return chg;
        });

        const newTotalPaid = acc.total_paid + paymentAmount;
        const newOutstanding = Math.max(0, acc.total_billed - newTotalPaid);
        return {
          ...acc,
          charges: updatedCharges,
          total_paid: newTotalPaid,
          outstanding_balance: newOutstanding
        };
      }
      return acc;
    });

    const newLedgerEntry = {
      id: `led-${Date.now()}`,
      receipt_no: paymentForm.receipt_no,
      entry_type: 'PAYMENT',
      student_name: selectedAccount.candidate_name,
      student_enrollment_no: selectedAccount.enrollment_no,
      fee_structure_name: selectedAccount.charges[0]?.fee_structure_name || 'Annual Fee',
      amount: paymentAmount,
      external_transaction_ref: paymentForm.external_transaction_ref,
      payment_mode: paymentForm.payment_mode,
      payment_date: new Date().toISOString().split('T')[0],
      recorded_by_name: 'fee_accountant',
      reason: paymentForm.reason
    };

    setAccounts(updatedAccounts);
    setLedgerEntries([newLedgerEntry, ...ledgerEntries]);
    setShowRecordModal(false);
    alert(`Payment of ₹${paymentAmount.toLocaleString()} recorded successfully for ${selectedAccount.candidate_name}! Status marked accordingly.`);
  };

  // Handle Controlled Reversal
  const openReversalModal = (entry) => {
    setSelectedLedgerEntry(entry);
    setReversalForm({
      payment_entry_id: entry.id,
      reason: '',
      reversal_receipt_no: `REV-${Date.now().toString().slice(-6)}`
    });
    setShowReversalModal(true);
  };

  const handleReversalSubmit = (e) => {
    e.preventDefault();
    if (!selectedLedgerEntry || !reversalForm.reason.trim()) {
      alert('A valid reason is required for financial reversals.');
      return;
    }

    const reversalEntry = {
      id: `rev-${Date.now()}`,
      receipt_no: reversalForm.reversal_receipt_no,
      entry_type: 'REVERSAL',
      student_name: selectedLedgerEntry.student_name,
      student_enrollment_no: selectedLedgerEntry.student_enrollment_no,
      fee_structure_name: selectedLedgerEntry.fee_structure_name,
      amount: selectedLedgerEntry.amount,
      external_transaction_ref: selectedLedgerEntry.external_transaction_ref,
      payment_mode: selectedLedgerEntry.payment_mode,
      payment_date: new Date().toISOString().split('T')[0],
      recorded_by_name: 'fee_accountant',
      reason: `REVERSAL: ${reversalForm.reason}`
    };

    // Readjust accounts
    const updatedAccounts = accounts.map(acc => {
      if (acc.enrollment_no === selectedLedgerEntry.student_enrollment_no) {
        const newPaid = Math.max(0, acc.total_paid - selectedLedgerEntry.amount);
        const newOutstanding = acc.total_billed - newPaid;
        const updatedCharges = acc.charges.map(chg => {
          const chgPaid = Math.max(0, chg.paid_amount - selectedLedgerEntry.amount);
          const chgBal = chg.total_amount - chgPaid;
          return {
            ...chg,
            paid_amount: chgPaid,
            remaining_balance: chgBal,
            status: chgPaid === 0 ? 'UNPAID' : 'PARTIALLY_PAID'
          };
        });
        return {
          ...acc,
          total_paid: newPaid,
          outstanding_balance: newOutstanding,
          charges: updatedCharges
        };
      }
      return acc;
    });

    setLedgerEntries([reversalEntry, ...ledgerEntries]);
    setAccounts(updatedAccounts);
    setShowReversalModal(false);
    alert(`Reversal recorded in append-only ledger for ${selectedLedgerEntry.student_name}. Charge status adjusted.`);
  };

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
              <CreditCard size={24} />
            </div>
            <div>
              <h1 style={{ fontSize: '1.75rem', fontWeight: '700', color: 'var(--text-primary)', margin: 0 }}>
                College Fees & Finance Monitoring
              </h1>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', margin: '0.25rem 0 0 0' }}>
                Annual fee assessment & internal payment confirmation tracking via University Portal QR
              </p>
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <button
            onClick={() => setShowQrModal(true)}
            className="btn btn-secondary"
            style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
          >
            <QrCode size={18} />
            Show University QR & Portal
          </button>
          <button
            onClick={() => setShowAssessModal(true)}
            className="btn btn-primary"
            style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
          >
            <Plus size={18} />
            Assess Annual Fees (Once/Year)
          </button>
        </div>
      </div>

      {/* Institutional Workflow Card */}
      <div style={{
        backgroundColor: 'rgba(59, 130, 246, 0.05)',
        border: '1px solid rgba(59, 130, 246, 0.2)',
        borderRadius: '12px',
        padding: '1.25rem 1.5rem',
        marginBottom: '2rem',
        display: 'flex',
        alignItems: 'center',
        gap: '1.25rem'
      }}>
        <div style={{
          backgroundColor: 'rgba(59, 130, 246, 0.2)',
          color: 'var(--brand-primary)',
          padding: '0.75rem',
          borderRadius: '50%'
        }}>
          <ShieldCheck size={28} />
        </div>
        <div style={{ flex: 1 }}>
          <h4 style={{ margin: '0 0 0.25rem 0', color: 'var(--text-primary)', fontSize: '0.95rem', fontWeight: '600' }}>
            College Internal Record-Keeping Workflow
          </h4>
          <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
            <strong>1. Annual Assessment:</strong> Fee Accountant assesses fees once a year for enrolled cohorts. &bull; 
            <strong> 2. External Payment:</strong> Students scan the QR code to pay on the University Portal. &bull; 
            <strong> 3. Confirmation:</strong> Accountant verifies the UTR receipt and records the payment to update student status to <span style={{ color: 'var(--success-text)', fontWeight: '600' }}>PAID</span>.
          </p>
        </div>
      </div>

      {/* Financial Metrics Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
        gap: '1.25rem',
        marginBottom: '2rem'
      }}>
        <div className="card" style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Total Assessed Fees
          </span>
          <span style={{ fontSize: '1.8rem', fontWeight: '700', color: 'var(--text-primary)' }}>
            ₹{totalBilled.toLocaleString()}
          </span>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Across all enrolled student accounts
          </span>
        </div>

        <div className="card" style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Total Verified & Paid
          </span>
          <span style={{ fontSize: '1.8rem', fontWeight: '700', color: 'var(--success-text)' }}>
            ₹{totalPaid.toLocaleString()}
          </span>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Confirmed via University Portal UTR
          </span>
        </div>

        <div className="card" style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Outstanding College Dues
          </span>
          <span style={{ fontSize: '1.8rem', fontWeight: '700', color: totalOutstanding > 0 ? 'var(--warning-text)' : 'var(--text-primary)' }}>
            ₹{totalOutstanding.toLocaleString()}
          </span>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Pending student submission
          </span>
        </div>

        <div className="card" style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Collection Rate
          </span>
          <span style={{ fontSize: '1.8rem', fontWeight: '700', color: 'var(--brand-primary)' }}>
            {collectionRate}%
          </span>
          <div style={{ width: '100%', height: '6px', backgroundColor: 'var(--border-subtle)', borderRadius: '3px', overflow: 'hidden', marginTop: '0.25rem' }}>
            <div style={{ width: `${collectionRate}%`, height: '100%', backgroundColor: 'var(--brand-primary)' }} />
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div style={{
        display: 'flex',
        gap: '1rem',
        borderBottom: '1px solid var(--border-subtle)',
        marginBottom: '1.5rem',
        flexWrap: 'wrap'
      }}>
        <button
          onClick={() => setActiveTab('candidate_desk')}
          style={{
            padding: '0.75rem 1.25rem',
            background: 'none',
            border: 'none',
            borderBottom: activeTab === 'candidate_desk' ? '2px solid var(--brand-primary)' : '2px solid transparent',
            color: activeTab === 'candidate_desk' ? 'var(--brand-primary)' : 'var(--text-secondary)',
            fontWeight: activeTab === 'candidate_desk' ? '700' : '500',
            cursor: 'pointer',
            fontSize: '0.95rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}
        >
          <CreditCard size={18} />
          Candidate Admission Fee Desk
        </button>

        <button
          onClick={() => setActiveTab('accounts')}
          style={{
            padding: '0.75rem 1.25rem',
            background: 'none',
            border: 'none',
            borderBottom: activeTab === 'accounts' ? '2px solid var(--brand-primary)' : '2px solid transparent',
            color: activeTab === 'accounts' ? 'var(--brand-primary)' : 'var(--text-secondary)',
            fontWeight: activeTab === 'accounts' ? '600' : '400',
            cursor: 'pointer',
            fontSize: '0.95rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}
        >
          <Receipt size={18} />
          Student Fee Registry ({accounts.length})
        </button>

        <button
          onClick={() => setActiveTab('structures')}
          style={{
            padding: '0.75rem 1.25rem',
            background: 'none',
            border: 'none',
            borderBottom: activeTab === 'structures' ? '2px solid var(--brand-primary)' : '2px solid transparent',
            color: activeTab === 'structures' ? 'var(--brand-primary)' : 'var(--text-secondary)',
            fontWeight: activeTab === 'structures' ? '600' : '400',
            cursor: 'pointer',
            fontSize: '0.95rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}
        >
          <Lock size={18} />
          Annual Fee Structures ({structures.length})
        </button>

        <button
          onClick={() => setActiveTab('ledger')}
          style={{
            padding: '0.75rem 1.25rem',
            background: 'none',
            border: 'none',
            borderBottom: activeTab === 'ledger' ? '2px solid var(--brand-primary)' : '2px solid transparent',
            color: activeTab === 'ledger' ? 'var(--brand-primary)' : 'var(--text-secondary)',
            fontWeight: activeTab === 'ledger' ? '600' : '400',
            cursor: 'pointer',
            fontSize: '0.95rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}
        >
          <History size={18} />
          Append-Only Financial Ledger ({ledgerEntries.length})
        </button>
      </div>

      {/* TAB 0: Candidate Admission Fee Desk */}
      {activeTab === 'candidate_desk' && (
        <CandidateFeeDesk />
      )}

      {/* TAB 1: Student Fee Registry */}
      {activeTab === 'accounts' && (
        <div className="card" style={{ padding: '1.5rem' }}>
          {/* Filters Bar */}
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '1.25rem',
            gap: '1rem',
            flexWrap: 'wrap'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flex: 1, minWidth: '280px' }}>
              <div style={{ position: 'relative', width: '100%' }}>
                <Search size={18} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                <input
                  type="text"
                  className="input"
                  placeholder="Search student by name, enrollment no, application ID..."
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
                <option value="PAID">Paid (Zero Due)</option>
                <option value="PARTIAL">Partially Paid</option>
                <option value="UNPAID">Unpaid</option>
              </select>
            </div>
          </div>

          {/* Accounts Table */}
          <div style={{ overflowX: 'auto' }}>
            <table className="table" style={{ width: '100%', textAlign: 'left', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                  <th style={{ padding: '0.75rem 1rem' }}>STUDENT</th>
                  <th style={{ padding: '0.75rem 1rem' }}>ENROLLMENT / PRN</th>
                  <th style={{ padding: '0.75rem 1rem' }}>PROGRAM & CATEGORY</th>
                  <th style={{ padding: '0.75rem 1rem' }}>TOTAL BILLED</th>
                  <th style={{ padding: '0.75rem 1rem' }}>TOTAL PAID</th>
                  <th style={{ padding: '0.75rem 1rem' }}>OUTSTANDING</th>
                  <th style={{ padding: '0.75rem 1rem' }}>STATUS</th>
                  <th style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>ACTION</th>
                </tr>
              </thead>
              <tbody>
                {filteredAccounts.length === 0 ? (
                  <tr>
                    <td colSpan="8" style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                      No student fee accounts found matching your filter criteria.
                    </td>
                  </tr>
                ) : (
                  filteredAccounts.map(acc => {
                    const isPaid = acc.outstanding_balance === 0 && acc.total_billed > 0;
                    const isPartial = acc.outstanding_balance > 0 && acc.total_paid > 0;
                    return (
                      <tr key={acc.id} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                        <td style={{ padding: '1rem', fontWeight: '600', color: 'var(--text-primary)' }}>
                          {acc.candidate_name}
                        </td>
                        <td style={{ padding: '1rem', color: 'var(--text-secondary)', fontFamily: 'monospace' }}>
                          {acc.enrollment_no}
                        </td>
                        <td style={{ padding: '1rem' }}>
                          <div style={{ fontSize: '0.85rem', color: 'var(--text-primary)' }}>{acc.program_name}</div>
                          <span style={{
                            fontSize: '0.75rem',
                            padding: '0.15rem 0.5rem',
                            backgroundColor: 'rgba(255,255,255,0.06)',
                            borderRadius: '4px',
                            color: 'var(--text-muted)'
                          }}>
                            {acc.category}
                          </span>
                        </td>
                        <td style={{ padding: '1rem', fontWeight: '600', color: 'var(--text-primary)' }}>
                          ₹{acc.total_billed.toLocaleString()}
                        </td>
                        <td style={{ padding: '1rem', color: 'var(--success-text)', fontWeight: '600' }}>
                          ₹{acc.total_paid.toLocaleString()}
                        </td>
                        <td style={{ padding: '1rem', color: acc.outstanding_balance > 0 ? 'var(--warning-text)' : 'var(--text-muted)', fontWeight: '600' }}>
                          ₹{acc.outstanding_balance.toLocaleString()}
                        </td>
                        <td style={{ padding: '1rem' }}>
                          {isPaid ? (
                            <span style={{
                              backgroundColor: 'rgba(34, 197, 94, 0.15)',
                              color: 'var(--success-text)',
                              padding: '0.25rem 0.6rem',
                              borderRadius: '20px',
                              fontSize: '0.75rem',
                              fontWeight: '600',
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '0.35rem'
                            }}>
                              <CheckCircle2 size={13} /> PAID
                            </span>
                          ) : isPartial ? (
                            <span style={{
                              backgroundColor: 'rgba(234, 179, 8, 0.15)',
                              color: 'var(--warning-text)',
                              padding: '0.25rem 0.6rem',
                              borderRadius: '20px',
                              fontSize: '0.75rem',
                              fontWeight: '600',
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '0.35rem'
                            }}>
                              <Clock size={13} /> PARTIAL
                            </span>
                          ) : (
                            <span style={{
                              backgroundColor: 'rgba(239, 68, 68, 0.15)',
                              color: 'var(--danger-text)',
                              padding: '0.25rem 0.6rem',
                              borderRadius: '20px',
                              fontSize: '0.75rem',
                              fontWeight: '600',
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '0.35rem'
                            }}>
                              <AlertTriangle size={13} /> UNPAID
                            </span>
                          )}
                        </td>
                        <td style={{ padding: '1rem', textAlign: 'right' }}>
                          {isPaid ? (
                            <button
                              disabled
                              className="btn btn-secondary"
                              style={{ padding: '0.4rem 0.75rem', fontSize: '0.8rem', opacity: 0.5, cursor: 'not-allowed' }}
                              title="Student has zero outstanding dues. Duplicate payment prevented."
                            >
                              Fully Paid
                            </button>
                          ) : (
                            <button
                              onClick={() => openRecordPaymentModal(acc)}
                              className="btn btn-primary"
                              style={{ padding: '0.4rem 0.85rem', fontSize: '0.8rem' }}
                            >
                              Record Payment
                            </button>
                          )}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 2: Annual Fee Structures */}
      {activeTab === 'structures' && (
        <div>
          <div style={{
            backgroundColor: 'rgba(234, 179, 8, 0.08)',
            border: '1px solid rgba(234, 179, 8, 0.25)',
            borderRadius: '10px',
            padding: '1rem 1.25rem',
            marginBottom: '1.5rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem'
          }}>
            <Lock size={20} style={{ color: 'var(--warning-text)' }} />
            <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              <strong>Historical Fee Structure Protection (ADR-010):</strong> Fee structures are permanently locked once student charges are assessed for that academic year to prevent retroactive modifications.
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))', gap: '1.5rem' }}>
            {structures.map(st => (
              <div key={st.id} className="card" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <h3 style={{ margin: '0 0 0.25rem 0', fontSize: '1.1rem', color: 'var(--text-primary)' }}>
                      {st.name}
                    </h3>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      {st.department_name} &bull; Category: <strong>{st.category}</strong>
                    </span>
                  </div>
                  <span style={{
                    backgroundColor: 'rgba(239, 68, 68, 0.15)',
                    color: 'var(--danger-text)',
                    padding: '0.2rem 0.6rem',
                    borderRadius: '4px',
                    fontSize: '0.7rem',
                    fontWeight: '600',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.25rem'
                  }}>
                    <Lock size={12} /> LOCKED
                  </span>
                </div>

                <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '0.75rem' }}>
                  <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
                    Fee Line Items
                  </div>
                  {st.items.map((itm, i) => (
                    <div key={i} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '0.35rem' }}>
                      <span style={{ color: 'var(--text-secondary)' }}>{itm.fee_head_name}</span>
                      <span style={{ fontWeight: '500', color: 'var(--text-primary)' }}>₹{itm.amount.toLocaleString()}</span>
                    </div>
                  ))}
                </div>

                <div style={{
                  marginTop: 'auto',
                  borderTop: '1px solid var(--border-subtle)',
                  paddingTop: '0.75rem',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}>
                  <span style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Total Annual Amount:</span>
                  <span style={{ fontSize: '1.3rem', fontWeight: '700', color: 'var(--brand-primary)' }}>
                    ₹{st.total_amount.toLocaleString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 3: Append-Only Financial Ledger */}
      {activeTab === 'ledger' && (
        <div className="card" style={{ padding: '1.5rem' }}>
          <div style={{ marginBottom: '1.25rem' }}>
            <h3 style={{ margin: '0 0 0.25rem 0', fontSize: '1.15rem', color: 'var(--text-primary)' }}>
              Append-Only Payment Ledger & Audit Trail
            </h3>
            <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              All financial entries are immutable. Accidental or incorrect records are adjusted strictly via linked reversal entries (ADR-011).
            </p>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table className="table" style={{ width: '100%', textAlign: 'left', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                  <th style={{ padding: '0.75rem 1rem' }}>RECEIPT NO</th>
                  <th style={{ padding: '0.75rem 1rem' }}>ENTRY TYPE</th>
                  <th style={{ padding: '0.75rem 1rem' }}>STUDENT</th>
                  <th style={{ padding: '0.75rem 1rem' }}>AMOUNT</th>
                  <th style={{ padding: '0.75rem 1rem' }}>UNIV. PORTAL UTR / REF</th>
                  <th style={{ padding: '0.75rem 1rem' }}>RECORDED BY</th>
                  <th style={{ padding: '0.75rem 1rem' }}>DATE</th>
                  <th style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>ACTION</th>
                </tr>
              </thead>
              <tbody>
                {ledgerEntries.map(entry => (
                  <tr key={entry.id} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                    <td style={{ padding: '1rem', fontFamily: 'monospace', fontWeight: '600', color: 'var(--brand-primary)' }}>
                      {entry.receipt_no}
                    </td>
                    <td style={{ padding: '1rem' }}>
                      <span style={{
                        backgroundColor: entry.entry_type === 'PAYMENT' ? 'rgba(34, 197, 94, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                        color: entry.entry_type === 'PAYMENT' ? 'var(--success-text)' : 'var(--danger-text)',
                        padding: '0.2rem 0.5rem',
                        borderRadius: '4px',
                        fontSize: '0.75rem',
                        fontWeight: '600'
                      }}>
                        {entry.entry_type}
                      </span>
                    </td>
                    <td style={{ padding: '1rem' }}>
                      <div style={{ fontWeight: '500', color: 'var(--text-primary)' }}>{entry.student_name}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{entry.student_enrollment_no}</div>
                    </td>
                    <td style={{ padding: '1rem', fontWeight: '700', color: entry.entry_type === 'PAYMENT' ? 'var(--text-primary)' : 'var(--danger-text)' }}>
                      {entry.entry_type === 'PAYMENT' ? '+' : '-'}₹{entry.amount.toLocaleString()}
                    </td>
                    <td style={{ padding: '1rem', fontFamily: 'monospace', color: 'var(--text-secondary)' }}>
                      {entry.external_transaction_ref || 'N/A'}
                    </td>
                    <td style={{ padding: '1rem', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                      {entry.recorded_by_name}
                    </td>
                    <td style={{ padding: '1rem', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                      {entry.payment_date}
                    </td>
                    <td style={{ padding: '1rem', textAlign: 'right' }}>
                      {entry.entry_type === 'PAYMENT' && (
                        <button
                          onClick={() => openReversalModal(entry)}
                          className="btn btn-secondary"
                          style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem', color: 'var(--danger-text)' }}
                          title="Reverse this transaction with required reason"
                        >
                          <RotateCcw size={13} style={{ marginRight: '4px' }} />
                          Reverse
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* MODAL 1: University Payment QR Code */}
      {showQrModal && (
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
          <div className="card" style={{ maxWidth: '480px', width: '100%', padding: '2rem', textAlign: 'center' }}>
            <div style={{
              backgroundColor: 'rgba(59, 130, 246, 0.15)',
              color: 'var(--brand-primary)',
              width: '56px',
              height: '56px',
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 1rem auto'
            }}>
              <QrCode size={30} />
            </div>

            <h2 style={{ margin: '0 0 0.5rem 0', color: 'var(--text-primary)', fontSize: '1.4rem' }}>
              University Fee Payment Portal
            </h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '1.5rem' }}>
              Students scan this QR code or navigate to the university payment portal to complete their tuition and academic fees.
            </p>

            {/* Visual QR Code Display */}
            <div style={{
              backgroundColor: '#ffffff',
              padding: '1.5rem',
              borderRadius: '12px',
              display: 'inline-block',
              margin: '0 auto 1.5rem auto',
              border: '2px solid rgba(255,255,255,0.1)'
            }}>
              <svg width="180" height="180" viewBox="0 0 100 100" fill="none">
                {/* QR Code Pattern Mock */}
                <rect width="100" height="100" fill="white" />
                <rect x="10" y="10" width="25" height="25" fill="#0f172a" />
                <rect x="15" y="15" width="15" height="15" fill="white" />
                <rect x="18" y="18" width="9" height="9" fill="#0f172a" />
                <rect x="65" y="10" width="25" height="25" fill="#0f172a" />
                <rect x="70" y="15" width="15" height="15" fill="white" />
                <rect x="73" y="18" width="9" height="9" fill="#0f172a" />
                <rect x="10" y="65" width="25" height="25" fill="#0f172a" />
                <rect x="15" y="70" width="15" height="15" fill="white" />
                <rect x="18" y="73" width="9" height="9" fill="#0f172a" />
                <rect x="42" y="10" width="16" height="8" fill="#0f172a" />
                <rect x="42" y="24" width="8" height="14" fill="#0f172a" />
                <rect x="10" y="42" width="12" height="14" fill="#0f172a" />
                <rect x="28" y="42" width="14" height="8" fill="#0f172a" />
                <rect x="48" y="45" width="12" height="12" fill="#0f172a" />
                <rect x="65" y="42" width="10" height="10" fill="#0f172a" />
                <rect x="80" y="45" width="10" height="18" fill="#0f172a" />
                <rect x="42" y="65" width="18" height="8" fill="#0f172a" />
                <rect x="42" y="80" width="8" height="10" fill="#0f172a" />
                <rect x="58" y="75" width="12" height="15" fill="#0f172a" />
                <rect x="75" y="72" width="15" height="18" fill="#0f172a" />
              </svg>
            </div>

            <div style={{
              backgroundColor: 'rgba(255,255,255,0.04)',
              borderRadius: '8px',
              padding: '0.85rem',
              marginBottom: '1.5rem',
              textAlign: 'left',
              fontSize: '0.8rem',
              color: 'var(--text-secondary)'
            }}>
              <div style={{ fontWeight: '600', color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
                University Payment Portal URL:
              </div>
              <a 
                href="https://fees.university.ac.in/portal/pay" 
                target="_blank" 
                rel="noreferrer"
                style={{ color: 'var(--brand-primary)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.35rem' }}
              >
                https://fees.university.ac.in/portal/pay <ExternalLink size={13} />
              </a>
              <div style={{ marginTop: '0.5rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                *Note: Our college has no direct gateway API access. Student must present the UTR confirmation slip to the Accountant to mark their status as PAID.
              </div>
            </div>

            <button
              onClick={() => setShowQrModal(false)}
              className="btn btn-primary"
              style={{ width: '100%' }}
            >
              Close
            </button>
          </div>
        </div>
      )}

      {/* MODAL 2: Record Payment Modal (Accountant confirmation) */}
      {showRecordModal && selectedAccount && (
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
          <div className="card" style={{ maxWidth: '520px', width: '100%', padding: '2rem' }}>
            <h2 style={{ margin: '0 0 0.5rem 0', color: 'var(--text-primary)', fontSize: '1.3rem' }}>
              Confirm Payment: {selectedAccount.candidate_name}
            </h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '1.25rem' }}>
              Enter the student's University Portal UTR / Receipt reference to mark charge as PAID.
            </p>

            <form onSubmit={handleRecordPaymentSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
                  Student Enrollment No:
                </label>
                <input
                  type="text"
                  className="input"
                  disabled
                  value={selectedAccount.enrollment_no}
                  style={{ width: '100%', opacity: 0.8 }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
                  Payment Amount (₹): *
                </label>
                <input
                  type="number"
                  className="input"
                  required
                  min="1"
                  max={selectedAccount.outstanding_balance}
                  value={paymentForm.amount}
                  onChange={(e) => setPaymentForm({ ...paymentForm, amount: e.target.value })}
                  style={{ width: '100%' }}
                />
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  Max payable balance: ₹{selectedAccount.outstanding_balance.toLocaleString()}
                </span>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
                  Internal Receipt No: *
                </label>
                <input
                  type="text"
                  className="input"
                  required
                  value={paymentForm.receipt_no}
                  onChange={(e) => setPaymentForm({ ...paymentForm, receipt_no: e.target.value })}
                  style={{ width: '100%' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
                  University Portal UTR / Transaction Reference: *
                </label>
                <input
                  type="text"
                  className="input"
                  required
                  placeholder="e.g. UTR-9821374659 or UPI Ref"
                  value={paymentForm.external_transaction_ref}
                  onChange={(e) => setPaymentForm({ ...paymentForm, external_transaction_ref: e.target.value })}
                  style={{ width: '100%' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
                  Payment Mode:
                </label>
                <select
                  className="input"
                  value={paymentForm.payment_mode}
                  onChange={(e) => setPaymentForm({ ...paymentForm, payment_mode: e.target.value })}
                  style={{ width: '100%' }}
                >
                  <option value="UNIVERSITY_PORTAL_QR">University Portal (QR / NetBanking)</option>
                  <option value="BANK_CHALLAN">Bank Challan</option>
                  <option value="DEMAND_DRAFT">Demand Draft (DD)</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
                  Accountant Verification Note:
                </label>
                <textarea
                  className="input"
                  rows={2}
                  value={paymentForm.reason}
                  onChange={(e) => setPaymentForm({ ...paymentForm, reason: e.target.value })}
                  style={{ width: '100%' }}
                />
              </div>

              <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end', marginTop: '0.5rem' }}>
                <button
                  type="button"
                  onClick={() => setShowRecordModal(false)}
                  className="btn btn-secondary"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                >
                  Confirm & Mark Status
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 3: Trigger Annual Fee Assessment */}
      {showAssessModal && (
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
          <div className="card" style={{ maxWidth: '520px', width: '100%', padding: '2rem' }}>
            <h2 style={{ margin: '0 0 0.5rem 0', color: 'var(--text-primary)', fontSize: '1.3rem' }}>
              Assess Annual Fees to Student Cohort
            </h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '1.25rem' }}>
              Once a year, the fee accountant triggers annual fee assessment. Applicable fee structures will be automatically mapped to enrolled students and locked historically.
            </p>

            <form onSubmit={(e) => {
              e.preventDefault();
              setShowAssessModal(false);
              alert('Annual fees assessed successfully for enrolled cohort! Applied fee structures locked.');
            }} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
                  Academic Session / Year: *
                </label>
                <select className="input" required style={{ width: '100%' }}>
                  <option value="2024-25">2024-25 (Current)</option>
                  <option value="2025-26">2025-26</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
                  Department (Optional):
                </label>
                <select className="input" style={{ width: '100%' }}>
                  <option value="">All Departments</option>
                  <option value="ME">Mechanical Engineering</option>
                  <option value="CE">Civil Engineering</option>
                  <option value="IT">Information Technology</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
                  Payment Due Date:
                </label>
                <input
                  type="date"
                  className="input"
                  defaultValue="2024-10-31"
                  style={{ width: '100%' }}
                />
              </div>

              <div style={{
                backgroundColor: 'rgba(234, 179, 8, 0.1)',
                borderRadius: '8px',
                padding: '0.75rem',
                fontSize: '0.75rem',
                color: 'var(--warning-text)'
              }}>
                <Lock size={14} style={{ display: 'inline', marginRight: '4px' }} />
                Warning: Re-running will safely skip students already assessed and will lock any matching fee structures permanently.
              </div>

              <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end', marginTop: '0.5rem' }}>
                <button
                  type="button"
                  onClick={() => setShowAssessModal(false)}
                  className="btn btn-secondary"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                >
                  Run Annual Assessment
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 4: Controlled Reversal Modal */}
      {showReversalModal && selectedLedgerEntry && (
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
          <div className="card" style={{ maxWidth: '500px', width: '100%', padding: '2rem' }}>
            <h2 style={{ margin: '0 0 0.5rem 0', color: 'var(--danger-text)', fontSize: '1.3rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <RotateCcw size={20} />
              Controlled Financial Reversal
            </h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '1.25rem' }}>
              Per ADR-011, records are immutable. Reversing receipt <strong>{selectedLedgerEntry.receipt_no}</strong> will create a linked audit correction entry.
            </p>

            <form onSubmit={handleReversalSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
                  Original Amount to Reverse:
                </label>
                <input
                  type="text"
                  className="input"
                  disabled
                  value={`₹${selectedLedgerEntry.amount.toLocaleString()} (${selectedLedgerEntry.student_name})`}
                  style={{ width: '100%', opacity: 0.8 }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
                  Reversal Entry Receipt No: *
                </label>
                <input
                  type="text"
                  className="input"
                  required
                  value={reversalForm.reversal_receipt_no}
                  onChange={(e) => setReversalForm({ ...reversalForm, reversal_receipt_no: e.target.value })}
                  style={{ width: '100%' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
                  Mandatory Accountable Justification: *
                </label>
                <textarea
                  className="input"
                  required
                  rows={3}
                  placeholder="State the exact reason (e.g. Student submitted duplicate slip from another semester / mistaken entry)"
                  value={reversalForm.reason}
                  onChange={(e) => setReversalForm({ ...reversalForm, reason: e.target.value })}
                  style={{ width: '100%' }}
                />
              </div>

              <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end', marginTop: '0.5rem' }}>
                <button
                  type="button"
                  onClick={() => setShowReversalModal(false)}
                  className="btn btn-secondary"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  style={{ backgroundColor: 'var(--danger-border)', borderColor: 'var(--danger-border)' }}
                >
                  Execute Reversal Entry
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
export default FeeManagementPage;
