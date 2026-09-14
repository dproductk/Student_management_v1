import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import { 
  CreditCard, 
  Plus, 
  Edit3, 
  Trash2, 
  CheckCircle2, 
  XCircle, 
  AlertCircle, 
  Coins, 
  Layers, 
  Save, 
  X,
  Sparkles,
  Tag,
  RefreshCw,
  ToggleLeft,
  ToggleRight
} from 'lucide-react';

export const FeeHeadConfigPage = () => {
  const [feeHeads, setFeeHeads] = useState([]);
  const [academicYears, setAcademicYears] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedAY, setSelectedAY] = useState('');

  // Modal State
  const [showModal, setShowModal] = useState(false);
  const [editingHead, setEditingHead] = useState(null);
  const [newAmountInput, setNewAmountInput] = useState('');
  const [formData, setFormData] = useState({
    name: '',
    code: '',
    description: '',
    academic_year: '',
    allowed_amounts: [],
    display_order: 1,
    is_active: true
  });
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [saving, setSaving] = useState(false);

  const extractError = (err) => {
    if (err.response?.data) {
      const data = err.response.data;
      if (typeof data === 'string') return data;
      if (data.detail) return data.detail;
      if (data.error) return data.error;
      if (typeof data === 'object') {
        return Object.entries(data)
          .map(([k, v]) => `${k.toUpperCase()}: ${Array.isArray(v) ? v.join(', ') : v}`)
          .join(' | ');
      }
    }
    return err.message || 'Failed to complete request.';
  };

  const fetchFeeHeads = async () => {
    try {
      setLoading(true);
      const [headsRes, ayRes] = await Promise.all([
        api.get('/finance/fee-heads/'),
        api.get('/academic/academic-years/').catch(() => ({ data: [] }))
      ]);
      let heads = Array.isArray(headsRes.data) ? headsRes.data : (headsRes.data?.results || []);
      setFeeHeads(heads);

      const ays = Array.isArray(ayRes.data) ? ayRes.data : (ayRes.data?.results || []);
      setAcademicYears(ays);

      // Auto-seed if empty
      if (heads.length === 0) {
        await seedDefaultFeeHeads();
      }
    } catch (err) {
      console.error('Error fetching fee heads:', err);
      setErrorMsg('Failed to load fee heads. Please refresh the page.');
    } finally {
      setLoading(false);
    }
  };

  const seedDefaultFeeHeads = async () => {
    const defaults = [
      { name: 'Tuition Fee', code: 'TF', description: 'Annual course instruction & faculty fee', allowed_amounts: [0, 15000, 30000, 60000], display_order: 1, is_active: true },
      { name: 'Development Fee', code: 'DF', description: 'Institutional development & lab upkeep fee', allowed_amounts: [0, 3000, 6000, 10000], display_order: 2, is_active: true },
      { name: 'Other Fee', code: 'OTHER', description: 'Gymkhana, student activity and miscellaneous institutional fee', allowed_amounts: [0, 500, 1000, 1500], display_order: 3, is_active: true },
    ];

    try {
      for (const item of defaults) {
        await api.post('/finance/fee-heads/', item).catch(() => {});
      }
      const refreshed = await api.get('/finance/fee-heads/');
      setFeeHeads(Array.isArray(refreshed.data) ? refreshed.data : (refreshed.data?.results || []));
    } catch (e) {
      console.warn('Auto-seed completed or skipped');
    }
  };

  useEffect(() => {
    fetchFeeHeads();
  }, []);

  const openCreateModal = () => {
    setEditingHead(null);
    setFormData({
      name: '',
      code: '',
      description: '',
      academic_year: selectedAY || '',
      allowed_amounts: [0, 1000, 5000, 15000],
      display_order: feeHeads.length + 1,
      is_active: true
    });
    setNewAmountInput('');
    setErrorMsg('');
    setShowModal(true);
  };

  const openEditModal = (head) => {
    setEditingHead(head);
    setFormData({
      name: head.name,
      code: head.code,
      description: head.description || '',
      academic_year: head.academic_year || '',
      allowed_amounts: Array.isArray(head.allowed_amounts) ? [...head.allowed_amounts] : [],
      display_order: head.display_order || 1,
      is_active: head.is_active !== false
    });
    setNewAmountInput('');
    setErrorMsg('');
    setShowModal(true);
  };

  // Helper to add denomination(s)
  const handleAddAmount = () => {
    if (!newAmountInput.trim()) return;

    // Support comma-separated inputs: e.g. "0, 15000, 30000"
    const rawParts = newAmountInput.split(',').map(s => s.trim()).filter(Boolean);
    const validNumbers = [];

    for (const part of rawParts) {
      const num = parseFloat(part);
      if (!isNaN(num) && num >= 0 && !validNumbers.includes(num)) {
        validNumbers.push(num);
      }
    }

    if (validNumbers.length > 0) {
      const merged = Array.from(new Set([...formData.allowed_amounts, ...validNumbers])).sort((a, b) => a - b);
      setFormData({
        ...formData,
        allowed_amounts: merged
      });
      setNewAmountInput('');
    }
  };

  const addPresetAmount = (amount) => {
    if (!formData.allowed_amounts.includes(amount)) {
      setFormData({
        ...formData,
        allowed_amounts: [...formData.allowed_amounts, amount].sort((a, b) => a - b)
      });
    }
  };

  const handleRemoveAmount = (amountToRemove) => {
    setFormData({
      ...formData,
      allowed_amounts: formData.allowed_amounts.filter(a => a !== amountToRemove)
    });
  };

  const handleNameChange = (val) => {
    // If user is typing name and code is not explicitly modified in new modal, suggest code
    const updated = { ...formData, name: val };
    if (!editingHead && (!formData.code || formData.code === generateCode(formData.name))) {
      updated.code = generateCode(val);
    }
    setFormData(updated);
  };

  const generateCode = (str) => {
    if (!str) return '';
    const words = str.trim().split(/\s+/);
    if (words.length === 1) return words[0].slice(0, 4).toUpperCase();
    return words.map(w => w[0]).join('').toUpperCase();
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setErrorMsg('');

    if (!formData.name.trim()) {
      setErrorMsg('Fee Head Name is required.');
      return;
    }
    if (!formData.code.trim()) {
      setErrorMsg('Fee Head Code is required.');
      return;
    }

    setSaving(true);
    try {
      const payload = {
        name: formData.name.trim(),
        code: formData.code.trim().toUpperCase(),
        description: formData.description.trim(),
        academic_year: formData.academic_year || null,
        allowed_amounts: formData.allowed_amounts,
        display_order: parseInt(formData.display_order) || 1,
        is_active: formData.is_active
      };

      if (editingHead) {
        await api.patch(`/finance/fee-heads/${editingHead.id}/`, payload);
        setSuccessMsg(`Fee head "${payload.name}" updated successfully.`);
      } else {
        await api.post('/finance/fee-heads/', payload);
        setSuccessMsg(`Fee head "${payload.name}" created successfully.`);
      }

      setShowModal(false);
      fetchFeeHeads();
      setTimeout(() => setSuccessMsg(''), 4000);
    } catch (err) {
      setErrorMsg(extractError(err));
    } finally {
      setSaving(false);
    }
  };

  const handleToggleActive = async (head) => {
    try {
      const updatedStatus = !head.is_active;
      await api.patch(`/finance/fee-heads/${head.id}/`, { is_active: updatedStatus });
      setFeeHeads(feeHeads.map(h => h.id === head.id ? { ...h, is_active: updatedStatus } : h));
      setSuccessMsg(`Fee head "${head.name}" is now ${updatedStatus ? 'Active' : 'Inactive'}.`);
      setTimeout(() => setSuccessMsg(''), 3000);
    } catch (err) {
      alert(extractError(err));
    }
  };

  const handleDelete = async (head) => {
    if (!window.confirm(`Are you sure you want to delete fee head "${head.name}" (${head.code})?`)) return;
    try {
      await api.delete(`/finance/fee-heads/${head.id}/`);
      setFeeHeads(feeHeads.filter(h => h.id !== head.id));
      setSuccessMsg(`Fee head "${head.name}" deleted.`);
      setTimeout(() => setSuccessMsg(''), 3000);
    } catch (err) {
      alert(extractError(err));
    }
  };

  const filteredHeads = selectedAY 
    ? feeHeads.filter(h => !h.academic_year || h.academic_year === selectedAY)
    : feeHeads;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
      
      {/* Header Banner */}
      <div className="card" style={{
        background: 'linear-gradient(135deg, var(--bg-surface) 0%, rgba(99, 102, 241, 0.08) 100%)',
        border: '1px solid var(--border-subtle)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '1.5rem 2rem',
        flexWrap: 'wrap',
        gap: '1rem'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
          <div style={{
            width: '52px',
            height: '52px',
            borderRadius: 'var(--radius-lg)',
            backgroundColor: 'rgba(99, 102, 241, 0.12)',
            color: 'var(--primary-600)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Coins size={28} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
              <h1 style={{ fontSize: '1.5rem', fontWeight: '800', color: 'var(--text-primary)', margin: 0 }}>
                Fee Head Configuration
              </h1>
              <span className="badge badge-primary">Administrative Head Portal</span>
            </div>
            <p style={{ margin: '0.25rem 0 0', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
              Government College of Engineering, Kolhapur — Configure fee heads and selectable denomination values for the Accountant fee marking desk.
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          {/* Academic Year Filter */}
          <select 
            className="form-control"
            style={{ width: 'auto', minWidth: '180px', fontSize: '0.88rem' }}
            value={selectedAY}
            onChange={(e) => setSelectedAY(e.target.value)}
          >
            <option value="">All Academic Years</option>
            {academicYears.map(ay => (
              <option key={ay.id} value={ay.id}>
                FY {ay.label} {ay.is_current ? '(Current)' : ''}
              </option>
            ))}
          </select>

          <button 
            className="btn btn-secondary"
            onClick={fetchFeeHeads}
            title="Refresh Fee Heads"
            style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', padding: '0.55rem 0.85rem' }}
          >
            <RefreshCw size={15} />
          </button>

          <button 
            className="btn btn-primary"
            onClick={openCreateModal}
            style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.55rem 1.15rem' }}
          >
            <Plus size={16} /> Add Fee Head
          </button>
        </div>
      </div>

      {/* Feedback Messages */}
      {successMsg && (
        <div style={{
          padding: '0.85rem 1.25rem',
          borderRadius: 'var(--radius-md)',
          backgroundColor: 'rgba(16, 185, 129, 0.1)',
          border: '1px solid rgba(16, 185, 129, 0.3)',
          color: '#10b981',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          fontSize: '0.9rem'
        }}>
          <CheckCircle2 size={16} /> {successMsg}
        </div>
      )}

      {/* Fee Heads Card List */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))', gap: '1.25rem' }}>
        {loading ? (
          <div className="card" style={{ gridColumn: '1 / -1', padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
            Loading fee heads...
          </div>
        ) : filteredHeads.length === 0 ? (
          <div className="card" style={{ gridColumn: '1 / -1', padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
            No fee heads found. Click "Add Fee Head" to create your first fee category.
          </div>
        ) : (
          filteredHeads.map((head) => (
            <div 
              key={head.id} 
              className="card"
              style={{
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-lg)',
                padding: '1.35rem',
                backgroundColor: 'var(--bg-surface)',
                boxShadow: 'var(--shadow-sm)',
                opacity: head.is_active ? 1 : 0.75
              }}
            >
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span className="badge badge-info" style={{ fontWeight: '700', fontSize: '0.78rem' }}>{head.code}</span>
                    <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: '700', color: 'var(--text-primary)' }}>
                      {head.name}
                    </h3>
                  </div>
                  <button 
                    onClick={() => handleToggleActive(head)}
                    style={{
                      border: 'none',
                      background: 'none',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.35rem',
                      fontSize: '0.78rem',
                      fontWeight: '600',
                      color: head.is_active ? '#10b981' : 'var(--text-muted)'
                    }}
                    title={head.is_active ? 'Click to deactivate' : 'Click to activate'}
                  >
                    {head.is_active ? (
                      <span className="badge badge-success" style={{ cursor: 'pointer' }}>Active</span>
                    ) : (
                      <span className="badge badge-secondary" style={{ cursor: 'pointer' }}>Inactive</span>
                    )}
                  </button>
                </div>

                {head.academic_year_label && (
                  <div style={{ fontSize: '0.78rem', color: 'var(--primary-600)', fontWeight: '600', marginBottom: '0.4rem' }}>
                    Academic Year: FY {head.academic_year_label}
                  </div>
                )}

                {head.description && (
                  <p style={{ fontSize: '0.84rem', color: 'var(--text-secondary)', margin: '0 0 1rem', lineHeight: '1.4' }}>
                    {head.description}
                  </p>
                )}

                {/* Configured Dropdown Denomination Values */}
                <div style={{
                  backgroundColor: 'var(--bg-surface-elevated)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-md)',
                  padding: '0.85rem 1rem',
                  marginTop: '0.75rem'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                    <span style={{ fontSize: '0.75rem', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                      Allowed Dropdown Amounts (Accountant)
                    </span>
                    <span style={{ fontSize: '0.72rem', color: 'var(--primary-600)', fontWeight: '600' }}>
                      {(head.allowed_amounts || []).length} Presets
                    </span>
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
                    {(!head.allowed_amounts || head.allowed_amounts.length === 0) ? (
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                        No fixed amounts configured. Default 0 will apply.
                      </span>
                    ) : (
                      head.allowed_amounts.map((amt, idx) => (
                        <span 
                          key={idx}
                          style={{
                            padding: '0.25rem 0.6rem',
                            borderRadius: 'var(--radius-sm)',
                            backgroundColor: amt === 0 ? 'rgba(100, 116, 139, 0.12)' : 'rgba(59, 130, 246, 0.12)',
                            color: amt === 0 ? 'var(--text-secondary)' : 'var(--primary-600)',
                            fontSize: '0.8rem',
                            fontWeight: '700',
                            fontFamily: 'monospace'
                          }}
                        >
                          ₹{Number(amt).toLocaleString('en-IN')}
                        </span>
                      ))
                    )}
                  </div>
                </div>
              </div>

              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                borderTop: '1px solid var(--border-subtle)',
                marginTop: '1.25rem',
                paddingTop: '0.75rem'
              }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  Order #{head.display_order || 1}
                </span>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <button 
                    className="btn btn-secondary"
                    style={{ fontSize: '0.82rem', padding: '0.4rem 0.85rem' }}
                    onClick={() => openEditModal(head)}
                  >
                    <Edit3 size={13} style={{ marginRight: '4px' }} /> Configure
                  </button>
                  <button 
                    className="btn btn-danger"
                    style={{ fontSize: '0.82rem', padding: '0.4rem 0.65rem' }}
                    onClick={() => handleDelete(head)}
                    title="Delete fee head"
                  >
                    <Trash2 size={13} />
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Add / Edit Fee Head Modal */}
      {showModal && (
        <div className="modal-backdrop">
          <div className="modal-card" style={{ maxWidth: '580px', width: '92%' }}>
            <div className="modal-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                <Coins size={20} color="var(--primary-600)" />
                <h3 style={{ margin: 0, fontSize: '1.2rem', fontWeight: '700' }}>
                  {editingHead ? `Configure ${editingHead.name}` : 'Create New Fee Head'}
                </h3>
              </div>
              <button className="btn-close" onClick={() => setShowModal(false)}>✕</button>
            </div>
            <form onSubmit={handleSave}>
              <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: '1.15rem' }}>
                {errorMsg && (
                  <div style={{
                    padding: '0.75rem 1rem',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    border: '1px solid rgba(239, 68, 68, 0.3)',
                    color: '#ef4444',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: '0.85rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem'
                  }}>
                    <AlertCircle size={16} style={{ flexShrink: 0 }} />
                    <span>{errorMsg}</span>
                  </div>
                )}

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 140px', gap: '1rem' }}>
                  <div className="form-group" style={{ margin: 0 }}>
                    <label className="form-label">Fee Head / Particular Name *</label>
                    <input 
                      type="text" 
                      className="form-control" 
                      placeholder="e.g. Tuition Fee, Development Fee"
                      value={formData.name}
                      onChange={(e) => handleNameChange(e.target.value)}
                      required
                    />
                  </div>
                  <div className="form-group" style={{ margin: 0 }}>
                    <label className="form-label">Code *</label>
                    <input 
                      type="text" 
                      className="form-control" 
                      placeholder="e.g. TF, DF"
                      value={formData.code}
                      onChange={(e) => setFormData({ ...formData, code: e.target.value.toUpperCase() })}
                      required
                    />
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                  <div className="form-group" style={{ margin: 0 }}>
                    <label className="form-label">Academic Year Scope</label>
                    <select 
                      className="form-control"
                      value={formData.academic_year}
                      onChange={(e) => setFormData({ ...formData, academic_year: e.target.value })}
                    >
                      <option value="">All Academic Years (Global)</option>
                      {academicYears.map(ay => (
                        <option key={ay.id} value={ay.id}>
                          FY {ay.label} {ay.is_current ? '(Current)' : ''}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="form-group" style={{ margin: 0 }}>
                    <label className="form-label">Display Sequence Order</label>
                    <input 
                      type="number" 
                      className="form-control" 
                      value={formData.display_order}
                      onChange={(e) => setFormData({ ...formData, display_order: e.target.value })}
                      min="1"
                    />
                  </div>
                </div>

                <div className="form-group" style={{ margin: 0 }}>
                  <label className="form-label">Description / Remarks</label>
                  <textarea 
                    className="form-control" 
                    rows="2"
                    placeholder="Brief description of fee breakdown and purpose..."
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  />
                </div>

                {/* Allowed Amounts Tag / Chip Editor */}
                <div className="form-group" style={{ margin: 0 }}>
                  <label className="form-label" style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>Accountant Allowed Dropdown Denominations (₹)</span>
                    <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: 'normal' }}>
                      (e.g., 0, 15000, 30000, 60000)
                    </span>
                  </label>
                  
                  {/* Quick Preset Buttons */}
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem', marginBottom: '0.6rem' }}>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', alignSelf: 'center', marginRight: '0.25rem' }}>
                      Quick Add:
                    </span>
                    {[0, 500, 1000, 1500, 3000, 6000, 10000, 15000, 30000, 60000].map(val => (
                      <button
                        key={val}
                        type="button"
                        onClick={() => addPresetAmount(val)}
                        disabled={formData.allowed_amounts.includes(val)}
                        style={{
                          fontSize: '0.72rem',
                          padding: '0.2rem 0.45rem',
                          borderRadius: 'var(--radius-sm)',
                          border: '1px solid var(--border-subtle)',
                          backgroundColor: formData.allowed_amounts.includes(val) ? 'var(--bg-surface-elevated)' : 'var(--bg-surface)',
                          color: formData.allowed_amounts.includes(val) ? 'var(--text-muted)' : 'var(--primary-600)',
                          cursor: formData.allowed_amounts.includes(val) ? 'default' : 'pointer',
                          fontWeight: '600'
                        }}
                      >
                        + ₹{val.toLocaleString('en-IN')}
                      </button>
                    ))}
                  </div>

                  <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem' }}>
                    <input 
                      type="text"
                      className="form-control"
                      placeholder="Enter amount or comma-separated list (e.g. 15000, 30000)"
                      value={newAmountInput}
                      onChange={(e) => setNewAmountInput(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          e.preventDefault();
                          handleAddAmount();
                        }
                      }}
                    />
                    <button 
                      type="button" 
                      className="btn btn-secondary"
                      onClick={handleAddAmount}
                      style={{ whiteSpace: 'nowrap' }}
                    >
                      <Plus size={14} style={{ marginRight: '4px' }} /> Add
                    </button>
                  </div>

                  <div style={{
                    display: 'flex',
                    flexWrap: 'wrap',
                    gap: '0.4rem',
                    minHeight: '44px',
                    padding: '0.55rem',
                    borderRadius: 'var(--radius-md)',
                    border: '1px dashed var(--border-subtle)',
                    backgroundColor: 'var(--bg-surface-elevated)',
                    alignItems: 'center'
                  }}>
                    {formData.allowed_amounts.length === 0 ? (
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                        No denomination values added yet.
                      </span>
                    ) : (
                      formData.allowed_amounts.map((amt, i) => (
                        <span 
                          key={i}
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '0.35rem',
                            padding: '0.25rem 0.65rem',
                            borderRadius: 'var(--radius-sm)',
                            backgroundColor: amt === 0 ? 'rgba(100, 116, 139, 0.15)' : 'rgba(59, 130, 246, 0.15)',
                            color: amt === 0 ? 'var(--text-secondary)' : 'var(--primary-600)',
                            fontSize: '0.84rem',
                            fontWeight: '700',
                            fontFamily: 'monospace'
                          }}
                        >
                          ₹{Number(amt).toLocaleString('en-IN')}
                          <X 
                            size={13} 
                            style={{ cursor: 'pointer', opacity: 0.7 }}
                            onClick={() => handleRemoveAmount(amt)} 
                          />
                        </span>
                      ))
                    )}
                  </div>
                </div>

                <div className="form-group" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', margin: 0 }}>
                  <input 
                    type="checkbox"
                    id="is_active_checkbox"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                    style={{ width: '18px', height: '18px', accentColor: 'var(--primary-600)', cursor: 'pointer' }}
                  />
                  <label htmlFor="is_active_checkbox" style={{ fontSize: '0.9rem', fontWeight: '600', cursor: 'pointer' }}>
                    Active and selectable for fee assessments
                  </label>
                </div>
              </div>

              <div className="modal-footer" style={{ marginTop: '1.25rem' }}>
                <button 
                  type="button" 
                  className="btn btn-secondary" 
                  onClick={() => setShowModal(false)}
                  disabled={saving}
                >
                  Cancel
                </button>
                <button 
                  type="submit" 
                  className="btn btn-primary"
                  style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
                  disabled={saving}
                >
                  <Save size={16} /> {saving ? 'Saving...' : 'Save Fee Head'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};
export default FeeHeadConfigPage;
