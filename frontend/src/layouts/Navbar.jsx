import React from 'react';
import { useAuth } from '../context/AuthContext';
import { Menu, Sun, LogOut } from 'lucide-react';
import collegeLogo from '../assets/college-logo.jpg';

export const Navbar = () => {
  const { user, logout } = useAuth();

  const getInitials = () => {
    if (!user) return '?';
    const name = user.full_name || user.username || '';
    const parts = name.split(' ');
    if (parts.length >= 2) return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    return name.substring(0, 2).toUpperCase();
  };

  return (
    <header style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 1.5rem',
      height: '56px',
      backgroundColor: '#2563eb',
      color: '#ffffff',
      position: 'sticky',
      top: 0,
      zIndex: 50,
    }}>
      {/* Left: Institution Branding */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
        <div style={{
          width: '38px',
          height: '38px',
          borderRadius: '50%',
          backgroundColor: '#ffffff',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          overflow: 'hidden',
          padding: '2px',
          boxShadow: '0 1px 3px rgba(0,0,0,0.2)'
        }}>
          <img
            src={collegeLogo}
            alt="College Emblem"
            style={{ width: '100%', height: '100%', objectFit: 'contain' }}
          />
        </div>
        <div style={{ lineHeight: 1.15 }}>
          <div style={{ fontSize: '0.78rem', fontWeight: '800', letterSpacing: '0.02em' }}>
            GOVERNMENT COLLEGE OF ENGINEERING
          </div>
          <div style={{ fontSize: '0.68rem', opacity: 0.9, fontWeight: '600', letterSpacing: '0.04em' }}>
            KOLHAPUR (AUTONOMOUS)
          </div>
        </div>
      </div>

      {/* Center: Title */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <Menu size={20} style={{ cursor: 'pointer', opacity: 0.9 }} />
        <span style={{ fontSize: '0.95rem', fontWeight: '600', letterSpacing: '-0.01em' }}>
          Government College of Engineering, Kolhapur
        </span>
      </div>

      {/* Right: Term + Theme + Avatar */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <div style={{
          fontSize: '0.75rem',
          fontWeight: '600',
          display: 'flex',
          alignItems: 'center',
          gap: '0.4rem',
        }}>
          <span style={{ opacity: 0.8 }}>Term:</span>
          <span style={{
            background: 'rgba(255,255,255,0.2)',
            padding: '0.2rem 0.6rem',
            borderRadius: 'var(--radius-full)',
            fontSize: '0.7rem',
            fontWeight: '700',
            letterSpacing: '0.04em',
          }}>
            SUMMER 2026
          </span>
        </div>

        <Sun size={18} style={{ cursor: 'pointer', opacity: 0.85 }} />

        {/* User Avatar */}
        <div
          onClick={logout}
          title={`Sign out (${user?.username || 'user'})`}
          style={{
            width: '34px',
            height: '34px',
            borderRadius: '50%',
            background: 'rgba(255,255,255,0.9)',
            color: '#2563eb',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '0.75rem',
            fontWeight: '700',
            cursor: 'pointer',
            transition: 'transform 0.15s ease',
            border: '2px solid rgba(255,255,255,0.5)',
          }}
        >
          {getInitials()}
        </div>
      </div>
    </header>
  );
};
