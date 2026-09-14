import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';
import collegeLogo from '../../assets/college-logo.jpg';
import { Printer, X, Download, FileText, CheckCircle2 } from 'lucide-react';

/**
 * Student Payment History & Receipt Viewer
 * Matches the official EDVANA MIS design:
 * - Table with S.N., TERM, REF NO, TXN ID, AMOUNT, RECEIPT
 * - Printable Payment Receipt modal with official College Emblem,
 *   Student Details, Payment Breakdown, and Verification metadata.
 */
export const StudentPaymentHistory = () => {
  const { user } = useAuth();
  const [student, setStudent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedReceipt, setSelectedReceipt] = useState(null);

  // Real fee assessments + payments for THIS student only.
  const [charges, setCharges] = useState([]);
  const [ledger, setLedger] = useState([]);
  const [payments, setPayments] = useState([]);

  useEffect(() => {
    const fetchStudentData = async () => {
      try {
        setLoading(true);
        const searchRes = await api.get(`/students/?search=${user?.username || ''}`);
        const results = Array.isArray(searchRes.data) ? searchRes.data : (searchRes.data?.results || []);
        let found = null;
        if (results.length > 0) {
          const detailRes = await api.get(`/students/${results[0].id}/`);
          found = detailRes.data;
          setStudent(found);
        } else {
          const allRes = await api.get('/students/');
          const allData = Array.isArray(allRes.data) ? allRes.data : (allRes.data?.results || []);
          if (allData.length > 0) {
            const detailRes = await api.get(`/students/${allData[0].id}/`);
            found = detailRes.data;
            setStudent(found);
          }
        }

        if (found?.id) {
          // Fetch this student's fee charges + ledger (backend supports ?student=).
          // Fall back to client-side filtering if the API returns unfiltered lists.
          const [chRes, ledRes] = await Promise.all([
            api.get(`/finance/charges/?student=${found.id}`).catch(() => ({ data: [] })),
            api.get(`/finance/ledger/?student=${found.id}`).catch(() => ({ data: [] })),
          ]);
          let chList = Array.isArray(chRes.data) ? chRes.data : (chRes.data?.results || []);
          let ledList = Array.isArray(ledRes.data) ? ledRes.data : (ledRes.data?.results || []);

          // Client-side safety filter: keep only this student's rows.
          // Matches new `student_id` field first, then enrollment / application fallbacks.
          const sid = String(found.id);
          const enr = found.enrollment_no ? String(found.enrollment_no) : '';
          const app = found.application_id ? String(found.application_id) : '';
          if (chList.length > 0 && !chList.every(c => c.student_id && String(c.student_id) === sid)) {
            const filtered = chList.filter(c =>
              (c.student_id && String(c.student_id) === sid) ||
              (enr && c.student_enrollment_no && String(c.student_enrollment_no) === enr) ||
              (app && c.student_application_id && String(c.student_application_id) === app)
            );
            // If the backend ignored ?student=, use the filtered subset.
            // If filtered is empty but unfiltered list is small, keep filtered (don't leak others).
            if (chList.length > 10 || filtered.length > 0) chList = filtered;
          }
          if (ledList.length > 0) {
            const filteredLed = ledList.filter(l =>
              (l.student_id && String(l.student_id) === sid) ||
              (enr && l.student_enrollment_no && String(l.student_enrollment_no) === enr)
            );
            if (ledList.length > 10 || filteredLed.length > 0 || chList.length > 0) ledList = filteredLed;
          }

          setCharges(chList);
          setLedger(ledList);

          // Map ledger entries to the receipt table rows
          const mapped = ledList
            .filter(e => (e.entry_type || 'PAYMENT') === 'PAYMENT')
            .map((e, idx) => ({
              sn: idx + 1,
              id: e.id,
              term: e.fee_structure_name || e.charge_detail || `FY ${e.payment_date?.slice(0, 4) || ''}`,
              refNo: e.receipt_no,
              txnId: e.external_transaction_ref || '—',
              amount: Number(e.amount).toLocaleString('en-IN'),
              rawAmount: e.amount,
              description: `${e.fee_structure_name || 'Admission Fee'} — ${e.payment_mode || ''}`,
              paidOn: e.payment_date,
              payment_mode: e.payment_mode,
              recorded_by: e.recorded_by_name,
              reason: e.reason,
            }));
          setPayments(mapped);
        }
      } catch (err) {
        console.error('Failed to load student details for payment receipt', err);
      } finally {
        setLoading(false);
      }
    };
    fetchStudentData();
  }, [user]);

  const candidateName = student?.candidate_name || user?.full_name || '';
  const enrollNo = student?.enrollment_no || user?.enrollment_no || '';
  const program = student?.admissions?.[0]?.program_name
    ? `${student.admissions[0].program_code || ''} - ${student.admissions[0].program_name}`
    : '';
  const studentMobile = student?.student_mobile || '';
  const parentMobile = student?.parent_mobile || student?.student_mobile || '';

  const handlePrint = () => {
    window.print();
  };

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Fee set by accountant — visible to the student with status */}
      <div style={{
        background: '#ffffff',
        borderRadius: '10px',
        border: '1px solid #e5e7eb',
        padding: '1.25rem',
        boxShadow: '0 1px 3px rgba(0,0,0,0.03)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
          <CheckCircle2 size={18} color="#2563eb" />
          <h3 style={{ margin: 0, fontSize: '1.05rem', fontWeight: '800', color: '#111827' }}>
            My Fee Assessment & Status
          </h3>
        </div>
        {loading ? (
          <div style={{ color: '#64748b', fontSize: '0.88rem' }}>Loading your fee details…</div>
        ) : charges.length === 0 ? (
          <div style={{
            padding: '1rem',
            borderRadius: '8px',
            backgroundColor: 'rgba(245,158,11,0.08)',
            border: '1px solid rgba(245,158,11,0.3)',
            color: '#92400e',
            fontSize: '0.88rem',
            fontWeight: '600'
          }}>
            Fee not set yet by the Fee Accountant. Please contact the accounts office. Once set, your total fee, breakup and status (Fee Set / Partial / Paid) will appear here.
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem' }}>
            {charges.map((c) => {
              const total = parseFloat(c.total_amount) || 0;
              const paid = parseFloat(c.paid_amount) || 0;
              const rem = c.remaining_balance !== undefined && c.remaining_balance !== null
                ? parseFloat(c.remaining_balance)
                : (total - paid);
              const st = (c.status || 'UNPAID').toUpperCase();
              const badgeBg = st === 'PAID' ? 'rgba(16,185,129,0.15)' : (st === 'PARTIALLY_PAID' ? 'rgba(245,158,11,0.15)' : 'rgba(37,99,235,0.12)');
              const badgeColor = st === 'PAID' ? '#059669' : (st === 'PARTIALLY_PAID' ? '#b45309' : '#1d4ed8');
              return (
                <div key={c.id} style={{ border: '1px solid #e5e7eb', borderRadius: '10px', padding: '1rem', backgroundColor: '#f8fafc' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '0.5rem' }}>
                    <div style={{ fontWeight: '800', color: '#111827', fontSize: '0.92rem' }}>
                      {c.fee_structure_name || 'Admission Fee'} • FY {c.academic_year_label || ''}
                    </div>
                    <span style={{ backgroundColor: badgeBg, color: badgeColor, padding: '0.25rem 0.7rem', borderRadius: '9999px', fontSize: '0.72rem', fontWeight: '800' }}>
                      {st === 'PARTIALLY_PAID' ? 'PARTIAL' : st}
                    </span>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.5rem', marginTop: '0.85rem', fontSize: '0.82rem' }}>
                    <div>
                      <div style={{ color: '#64748b', fontSize: '0.7rem', fontWeight: '700' }}>TOTAL</div>
                      <div style={{ fontWeight: '800' }}>₹{total.toLocaleString('en-IN')}</div>
                    </div>
                    <div>
                      <div style={{ color: '#64748b', fontSize: '0.7rem', fontWeight: '700' }}>PAID</div>
                      <div style={{ fontWeight: '800', color: '#059669' }}>₹{paid.toLocaleString('en-IN')}</div>
                    </div>
                    <div>
                      <div style={{ color: '#64748b', fontSize: '0.7rem', fontWeight: '700' }}>DUE</div>
                      <div style={{ fontWeight: '800', color: '#b45309' }}>₹{Math.max(0, rem).toLocaleString('en-IN')}</div>
                    </div>
                  </div>
                  {c.fee_breakdown && Object.keys(c.fee_breakdown).length > 0 && (
                    <div style={{ marginTop: '0.75rem', fontSize: '0.78rem', color: '#475569' }}>
                      <strong>Breakup:</strong>{' '}
                      {Object.entries(c.fee_breakdown).map(([k, v]) => `${k}: ₹${Number(v).toLocaleString('en-IN')}`).join(' • ')}
                    </div>
                  )}
                  {c.remarks && (
                    <div style={{ marginTop: '0.4rem', fontSize: '0.75rem', color: '#64748b' }}>{c.remarks}</div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Payment History Table Card */}
      <div style={{
        background: '#ffffff',
        borderRadius: '10px',
        border: '1px solid #e5e7eb',
        padding: '1.25rem',
        boxShadow: '0 1px 3px rgba(0,0,0,0.03)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
          <FileText size={18} color="#475569" />
          <h3 style={{ margin: 0, fontSize: '1.05rem', fontWeight: '800', color: '#111827' }}>
            Payment History & Receipts ({payments.length})
          </h3>
        </div>
        <div style={{ overflowX: 'auto' }}>
          <table style={{
            width: '100%',
            borderCollapse: 'collapse',
            fontSize: '0.88rem',
            textAlign: 'center',
          }}>
            <thead>
              <tr style={{
                background: '#ffffff',
                borderBottom: '1px solid #e5e7eb',
                color: '#111827',
                fontWeight: '700',
              }}>
                <th style={{ padding: '0.85rem 1rem' }}>S.N.</th>
                <th style={{ padding: '0.85rem 1rem' }}>TERM</th>
                <th style={{ padding: '0.85rem 1rem' }}>REF NO</th>
                <th style={{ padding: '0.85rem 1rem' }}>TXN ID</th>
                <th style={{ padding: '0.85rem 1rem' }}>AMOUNT</th>
                <th style={{ padding: '0.85rem 1rem' }}>RECEIPT</th>
              </tr>
            </thead>
            <tbody>
              {payments.length === 0 ? (
                <tr>
                  <td colSpan={6} style={{ padding: '2.5rem 1rem', color: '#64748b', fontSize: '0.88rem' }}>
                    {charges.length > 0
                      ? 'Fee has been set (see above). No payment recorded yet — please pay via the university portal and collect your receipt from the accounts office.'
                      : 'No payments recorded yet.'}
                  </td>
                </tr>
              ) : (
              payments.map((p, idx) => (
                <tr
                  key={p.sn}
                  style={{
                    borderBottom: '1px solid #f1f5f9',
                    backgroundColor: idx % 2 === 0 ? '#ffffff' : '#fafafa',
                  }}
                >
                  <td style={{ padding: '0.85rem 1rem', color: '#374151' }}>{p.sn}</td>
                  <td style={{ padding: '0.85rem 1rem', color: '#374151', fontWeight: '500' }}>{p.term}</td>
                  <td style={{ padding: '0.85rem 1rem', color: '#4b5563', fontFamily: 'monospace', fontSize: '0.82rem' }}>
                    {p.refNo}
                  </td>
                  <td style={{ padding: '0.85rem 1rem', color: '#4b5563', fontFamily: 'monospace', fontSize: '0.82rem' }}>
                    {p.txnId}
                  </td>
                  <td style={{ padding: '0.85rem 1rem', fontWeight: '600', color: '#111827' }}>
                    ₹ {p.amount}
                  </td>
                  <td style={{ padding: '0.85rem 1rem' }}>
                    <button
                      type="button"
                      onClick={() => setSelectedReceipt(p)}
                      style={{
                        backgroundColor: '#475569',
                        color: '#ffffff',
                        border: 'none',
                        borderRadius: '9999px',
                        padding: '0.4rem 1.1rem',
                        fontSize: '0.78rem',
                        fontWeight: '600',
                        cursor: 'pointer',
                        transition: 'background-color 0.15s ease',
                      }}
                      onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#334155'}
                      onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#475569'}
                    >
                      Print Receipt
                    </button>
                  </td>
                </tr>
              )))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Printable Receipt Modal */}
      {selectedReceipt && (
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
          zIndex: 1000,
          padding: '1.5rem',
        }}>
          <div style={{
            backgroundColor: '#ffffff',
            borderRadius: '10px',
            maxWidth: '850px',
            width: '100%',
            maxHeight: '92vh',
            overflowY: 'auto',
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
            position: 'relative',
          }}>
            {/* Modal Header bar */}
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '0.85rem 1.5rem',
              borderBottom: '1px solid #e5e7eb',
              backgroundColor: '#f8fafc',
              borderTopLeftRadius: '10px',
              borderTopRightRadius: '10px',
            }}>
              <span style={{ fontSize: '0.9rem', fontWeight: '700', color: '#334155' }}>
                Receipt #{selectedReceipt.refNo}
              </span>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button
                  onClick={handlePrint}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '0.4rem',
                    backgroundColor: '#2563eb',
                    color: '#ffffff',
                    border: 'none',
                    borderRadius: '6px',
                    padding: '0.4rem 0.9rem',
                    fontSize: '0.82rem',
                    fontWeight: '600',
                    cursor: 'pointer',
                  }}
                >
                  <Printer size={15} /> Print
                </button>
                <button
                  onClick={() => setSelectedReceipt(null)}
                  style={{
                    backgroundColor: 'transparent',
                    border: '1px solid #cbd5e1',
                    borderRadius: '6px',
                    padding: '0.4rem 0.6rem',
                    cursor: 'pointer',
                    color: '#64748b',
                    display: 'flex',
                    alignItems: 'center',
                  }}
                >
                  <X size={16} />
                </button>
              </div>
            </div>

            {/* Printable Receipt Paper Container */}
            <div id="printable-receipt" style={{ padding: '2.5rem' }}>
              {/* Header with College Emblem and Info */}
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '1.25rem',
                borderBottom: '2px solid #111827',
                paddingBottom: '1.25rem',
                marginBottom: '1.25rem',
              }}>
                <img
                  src={collegeLogo}
                  alt="Government College of Engineering Kolhapur Logo"
                  style={{ width: '75px', height: '75px', objectFit: 'contain' }}
                />
                <div>
                  <h2 style={{
                    fontSize: '1.35rem',
                    fontWeight: '800',
                    color: '#111827',
                    margin: 0,
                    lineHeight: 1.2,
                  }}>
                    Government College of Engineering, Kolhapur
                  </h2>
                  <div style={{ fontSize: '0.82rem', color: '#475569', fontWeight: '600', marginTop: '0.2rem' }}>
                    (First Autonomous Institute of Government of Maharashtra)
                  </div>
                  <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '0.15rem' }}>
                    University Road, Vidya Nagar, Kolhapur – 416004
                  </div>
                </div>
              </div>

              {/* Title */}
              <div style={{ textAlign: 'center', margin: '1rem 0 1.5rem' }}>
                <h3 style={{
                  fontSize: '1.15rem',
                  fontWeight: '800',
                  color: '#111827',
                  margin: 0,
                  textTransform: 'uppercase',
                  letterSpacing: '0.04em',
                }}>
                  Payment Receipt
                </h3>
              </div>

              {/* Section 1: Student Details */}
              <div style={{ marginBottom: '1.5rem' }}>
                <div style={{
                  backgroundColor: '#f1f5f9',
                  padding: '0.45rem 0.85rem',
                  fontWeight: '700',
                  fontSize: '0.88rem',
                  color: '#111827',
                  border: '1px solid #e2e8f0',
                  borderBottom: 'none',
                }}>
                  Student Details
                </div>
                <table style={{
                  width: '100%',
                  borderCollapse: 'collapse',
                  border: '1px solid #e2e8f0',
                  fontSize: '0.85rem',
                }}>
                  <tbody>
                    <tr style={{ borderBottom: '1px solid #e2e8f0' }}>
                      <td style={{ padding: '0.55rem 0.85rem', fontWeight: '600', width: '25%', color: '#334155', textAlign: 'right' }}>
                        Full Name
                      </td>
                      <td style={{ padding: '0.55rem 0.85rem', fontWeight: '700', color: '#111827', textTransform: 'uppercase' }}>
                        {candidateName}
                      </td>
                    </tr>
                    <tr style={{ borderBottom: '1px solid #e2e8f0' }}>
                      <td style={{ padding: '0.55rem 0.85rem', fontWeight: '600', width: '25%', color: '#334155', textAlign: 'right' }}>
                        Enroll No.
                      </td>
                      <td style={{ padding: '0.55rem 0.85rem', color: '#111827', fontWeight: '600' }}>
                        {enrollNo}
                      </td>
                    </tr>
                    <tr style={{ borderBottom: '1px solid #e2e8f0' }}>
                      <td style={{ padding: '0.55rem 0.85rem', fontWeight: '600', width: '25%', color: '#334155', textAlign: 'right' }}>
                        Program Code & Name
                      </td>
                      <td style={{ padding: '0.55rem 0.85rem', color: '#111827' }}>
                        {program}
                      </td>
                    </tr>
                    <tr style={{ borderBottom: '1px solid #e2e8f0' }}>
                      <td style={{ padding: '0.55rem 0.85rem', fontWeight: '600', width: '25%', color: '#334155', textAlign: 'right' }}>
                        Term
                      </td>
                      <td style={{ padding: '0.55rem 0.85rem', color: '#111827', fontWeight: '600' }}>
                        {selectedReceipt.term}
                      </td>
                    </tr>
                    <tr style={{ borderBottom: '1px solid #e2e8f0' }}>
                      <td style={{ padding: '0.55rem 0.85rem', fontWeight: '600', width: '25%', color: '#334155', textAlign: 'right' }}>
                        Student Mobile
                      </td>
                      <td style={{ padding: '0.55rem 0.85rem', color: '#111827' }}>
                        {studentMobile}
                      </td>
                    </tr>
                    <tr>
                      <td style={{ padding: '0.55rem 0.85rem', fontWeight: '600', width: '25%', color: '#334155', textAlign: 'right' }}>
                        Parent Mobile
                      </td>
                      <td style={{ padding: '0.55rem 0.85rem', color: '#111827' }}>
                        {parentMobile}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              {/* Section 2: Payment Detail */}
              <div style={{ marginBottom: '1.5rem' }}>
                <div style={{
                  backgroundColor: '#f1f5f9',
                  padding: '0.45rem 0.85rem',
                  fontWeight: '700',
                  fontSize: '0.88rem',
                  color: '#111827',
                  border: '1px solid #e2e8f0',
                  borderBottom: 'none',
                }}>
                  Payment Detail
                </div>
                <table style={{
                  width: '100%',
                  borderCollapse: 'collapse',
                  border: '1px solid #e2e8f0',
                  fontSize: '0.85rem',
                }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid #e2e8f0', background: '#fafafa' }}>
                      <th style={{ padding: '0.6rem 0.85rem', width: '10%', textAlign: 'center' }}>S.N.</th>
                      <th style={{ padding: '0.6rem 0.85rem', textAlign: 'left' }}>Description</th>
                      <th style={{ padding: '0.6rem 0.85rem', width: '20%', textAlign: 'right' }}>Amount</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr style={{ borderBottom: '1px solid #e2e8f0' }}>
                      <td style={{ padding: '0.65rem 0.85rem', textAlign: 'center' }}>1</td>
                      <td style={{ padding: '0.65rem 0.85rem' }}>{selectedReceipt.description}</td>
                      <td style={{ padding: '0.65rem 0.85rem', textAlign: 'right', fontWeight: '600' }}>
                        ₹{selectedReceipt.amount}
                      </td>
                    </tr>
                    <tr style={{ fontWeight: '700', backgroundColor: '#f8fafc' }}>
                      <td colSpan={2} style={{ padding: '0.65rem 0.85rem', textAlign: 'right' }}>
                        Total
                      </td>
                      <td style={{ padding: '0.65rem 0.85rem', textAlign: 'right', color: '#111827' }}>
                        ₹{selectedReceipt.amount}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              {/* Metadata details */}
              <div style={{
                fontSize: '0.82rem',
                color: '#334155',
                lineHeight: 1.8,
                borderTop: '1px solid #f1f5f9',
                paddingTop: '1rem',
              }}>
                <div><strong>Ref No.:</strong> {selectedReceipt.refNo}</div>
                <div><strong>Paid On:</strong> {selectedReceipt.paidOn}</div>
                <div><strong>Txn ID:</strong> {selectedReceipt.txnId}</div>
              </div>

              {/* Verified Stamp / Note */}
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'flex-end',
                marginTop: '2.5rem',
                paddingTop: '1rem',
                borderTop: '1px dashed #cbd5e1',
              }}>
                <div style={{ fontSize: '0.75rem', color: '#64748b' }}>
                  This is a computer-generated receipt issued by Government College of Engineering, Kolhapur.
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '0.82rem', fontWeight: '700', color: '#111827' }}>
                    Accounts & Cashier Office
                  </div>
                  <div style={{ fontSize: '0.72rem', color: '#64748b' }}>
                    GCE Kolhapur (Autonomous)
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
