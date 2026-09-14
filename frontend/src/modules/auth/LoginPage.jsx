import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { GraduationCap, Lock, User, AlertCircle } from 'lucide-react';
import collegeLogo from '../../assets/college-logo.jpg';

export const LoginPage = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const res = await login(username, password);
      if (res.must_change_password) {
        navigate('/change-password');
        return;
      }
      const roles = (res.user?.roles || []).map(r => r.role__name || r.name);
      if (roles.includes('STUDENT')) {
        navigate('/profile');
      } else if (roles.includes('FACULTY') || roles.includes('HOD')) {
        navigate('/faculty');
      } else if (roles.includes('VERIFICATION_OFFICER')) {
        navigate('/verification');
      } else if (roles.includes('ACCOUNTANT')) {
        navigate('/finance');
      } else if (roles.includes('EXAM_CELL')) {
        navigate('/results');
      } else {
        navigate('/academic/departments');
      }
    } catch (err) {
      const msg = err.response?.data?.error || err.response?.data?.message || err.response?.data?.detail || 'Invalid username or password.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const fillDemo = (userVal, passVal = 'Edvana@2026') => {
    setUsername(userVal);
    setPassword(passVal);
    setError('');
  };

  const demoRoles = [
    { label: 'Sys Admin', user: 'sysadmin', color: '#1e40af' },
    { label: 'Admin Head', user: 'administrative_head', color: '#0d9488' },
    { label: 'HOD', user: 'hod_cs', color: '#7c3aed' },
    { label: 'Faculty', user: 'faculty_cs', color: '#2563eb' },
    { label: 'Verifier', user: 'verifier', color: '#d97706' },
    { label: 'Accountant', user: 'accountant', color: '#059669' },
    { label: 'Exam Cell', user: 'examcell', color: '#ea580c' },
    { label: 'Student', user: 'student01', color: '#4b5563' },
  ];

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #1e40af 0%, #2563eb 50%, #3b82f6 100%)',
      padding: '1.5rem'
    }}>
      <div className="card" style={{
        maxWidth: '460px',
        width: '100%',
        padding: '2.25rem 2rem',
        border: '1px solid var(--border-subtle)',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
        borderRadius: 'var(--radius-xl)',
        background: '#ffffff',
      }}>
        <div style={{ textAlign: 'center', marginBottom: '1.75rem' }}>
          <div style={{
            width: '54px',
            height: '54px',
            borderRadius: '50%',
            background: 'linear-gradient(135deg, #2563eb, #1e40af)',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: 'var(--shadow-glow)',
            marginBottom: '0.75rem',
            overflow: 'hidden',
            backgroundColor: '#ffffff',
            border: '2px solid #e2e8f0',
            padding: '2px'
          }}>
            <img src={collegeLogo} alt="GCE Kolhapur Logo" style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
          </div>
          <h2 style={{ fontSize: '1.4rem', fontWeight: '700', letterSpacing: '-0.02em', color: 'var(--text-primary)', margin: 0 }}>
            EDVANA MIS
          </h2>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.25rem', marginBottom: 0, fontWeight: '600' }}>
            Government College of Engineering, Kolhapur
          </p>
        </div>

        {error && (
          <div style={{
            background: 'var(--danger-bg)',
            border: '1px solid var(--danger-border)',
            color: 'var(--danger-text)',
            padding: '0.75rem 1rem',
            borderRadius: 'var(--radius-md)',
            display: 'flex',
            alignItems: 'center',
            gap: '0.6rem',
            fontSize: '0.85rem',
            marginBottom: '1.25rem'
          }}>
            <AlertCircle size={18} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.1rem' }}>
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="form-label" htmlFor="username" style={{ fontSize: '0.82rem', fontWeight: 600 }}>
              Username / ID
            </label>
            <div style={{ position: 'relative' }}>
              <User size={16} color="var(--text-muted)" style={{ position: 'absolute', left: '12px', top: '13px' }} />
              <input
                id="username"
                type="text"
                className="form-control"
                style={{ paddingLeft: '2.5rem', width: '100%', height: '42px', fontSize: '0.9rem' }}
                placeholder="Enter username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="form-label" htmlFor="password" style={{ fontSize: '0.82rem', fontWeight: 600 }}>
              Password
            </label>
            <div style={{ position: 'relative' }}>
              <Lock size={16} color="var(--text-muted)" style={{ position: 'absolute', left: '12px', top: '13px' }} />
              <input
                id="password"
                type="password"
                className="form-control"
                style={{ paddingLeft: '2.5rem', width: '100%', height: '42px', fontSize: '0.9rem' }}
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: '100%', padding: '0.75rem', marginTop: '0.25rem', fontSize: '0.95rem', fontWeight: 600 }}
            disabled={loading}
          >
            {loading ? 'Authenticating...' : 'Sign In to Portal'}
          </button>
        </form>

        {/* Quick Demo Logins Pill Strip */}
        <div style={{
          marginTop: '1.5rem',
          paddingTop: '1.25rem',
          borderTop: '1px solid var(--border-subtle)'
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: '0.6rem'
          }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Quick Demo Logins (PW: Edvana@2026)
            </span>
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(4, 1fr)',
            gap: '0.4rem'
          }}>
            {demoRoles.map((dr) => (
              <button
                key={dr.user}
                type="button"
                onClick={() => fillDemo(dr.user)}
                style={{
                  padding: '0.4rem 0.2rem',
                  fontSize: '0.72rem',
                  fontWeight: 600,
                  borderRadius: '6px',
                  border: username === dr.user ? '1.5px solid var(--brand-primary)' : '1px solid var(--border-subtle)',
                  background: username === dr.user ? '#eff6ff' : '#f8fafc',
                  color: username === dr.user ? 'var(--brand-primary)' : 'var(--text-secondary)',
                  cursor: 'pointer',
                  textAlign: 'center',
                  transition: 'all 0.15s ease'
                }}
              >
                {dr.label}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

