import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { ArrowRight, UserCheck, CreditCard, Award, FileText } from 'lucide-react';

/**
 * Student Dashboard View
 * Matches the official EDVANA MIS design:
 * - Card with Welcome header
 * - Academic hub description & bullet items
 * - Architectural college illustration with quote & blue accent line
 */
export const StudentDashboard = () => {
  const { user } = useAuth();
  const collegeName = "Government College of Engineering, Kolhapur";

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
      {/* Welcome Hero Card */}
      <div style={{
        backgroundColor: '#ffffff',
        borderRadius: '12px',
        border: '1px solid #e5e7eb',
        padding: '2.25rem 2.5rem',
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.04)',
        display: 'flex',
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '2.5rem',
        marginBottom: '2rem'
      }}>
        {/* Left: Text & Features List */}
        <div style={{ flex: '1 1 500px', maxWidth: '620px' }}>
          <h2 style={{
            fontSize: '1.45rem',
            fontWeight: '800',
            color: '#111827',
            margin: 0,
            marginBottom: '0.65rem',
            letterSpacing: '-0.01em',
            lineHeight: 1.3
          }}>
            Welcome to {collegeName}
          </h2>
          <p style={{
            fontSize: '0.95rem',
            color: '#4b5563',
            margin: 0,
            marginBottom: '1.35rem',
            lineHeight: 1.5
          }}>
            This is your centralized hub for managing your academic activities.
          </p>

          <ul style={{
            margin: 0,
            paddingLeft: '1.25rem',
            color: '#374151',
            fontSize: '0.92rem',
            lineHeight: 1.85,
            listStyleType: 'disc'
          }}>
            <li>View and update your registration information, address, contact details, and bank details</li>
            <li>Register for your exams</li>
            <li>Download hall ticket</li>
            <li>Print your fee receipts</li>
            <li>Access your results and academic records</li>
            <li>And more</li>
          </ul>

          <div style={{ marginTop: '1.75rem', display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
            <Link
              to="/profile"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.5rem',
                backgroundColor: '#2563eb',
                color: '#ffffff',
                padding: '0.65rem 1.25rem',
                borderRadius: '6px',
                fontSize: '0.88rem',
                fontWeight: '600',
                textDecoration: 'none',
                boxShadow: '0 1px 2px rgba(37, 99, 235, 0.25)',
                transition: 'background-color 0.15s ease'
              }}
            >
              <span>View Student Profile</span>
              <ArrowRight size={16} />
            </Link>
          </div>
        </div>

        {/* Right: Architectural Illustration & Motto */}
        <div style={{
          flex: '1 1 340px',
          display: 'flex',
          flexDirection: 'row',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '1.5rem',
          minWidth: '320px'
        }}>
          {/* Stylized College Campus Vector Artwork */}
          <div style={{ width: '220px', height: '160px', position: 'relative' }}>
            <svg
              viewBox="0 0 240 180"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              style={{ width: '100%', height: '100%' }}
            >
              {/* Soft clouds backdrop */}
              <path d="M40 70 Q55 55 70 70 Q85 60 100 70 Z" fill="#eff6ff" opacity="0.8" />
              <path d="M140 65 Q160 50 180 65 Q195 55 210 65 Z" fill="#eff6ff" opacity="0.8" />

              {/* Background Foliage / Trees */}
              <circle cx="45" cy="115" r="20" fill="#93c5fd" opacity="0.85" />
              <circle cx="30" cy="125" r="16" fill="#60a5fa" opacity="0.75" />
              <circle cx="60" cy="128" r="14" fill="#3b82f6" opacity="0.85" />

              <circle cx="195" cy="115" r="20" fill="#93c5fd" opacity="0.85" />
              <circle cx="210" cy="125" r="16" fill="#60a5fa" opacity="0.75" />
              <circle cx="180" cy="128" r="14" fill="#3b82f6" opacity="0.85" />

              {/* Central Dome / Cupola */}
              <path d="M108 58 Q120 42 132 58 Z" fill="#60a5fa" />
              <rect x="113" y="58" width="14" height="12" fill="#93c5fd" rx="1" />
              <line x1="120" y1="42" x2="120" y2="34" stroke="#2563eb" strokeWidth="2" strokeLinecap="round" />
              {/* Flag */}
              <path d="M120 34 L129 38 L120 42 Z" fill="#2563eb" />

              {/* Triangular Pediment */}
              <polygon points="68,70 120,48 172,70" fill="#bfdbfe" stroke="#93c5fd" strokeWidth="1" />
              <circle cx="120" cy="62" r="4" fill="#2563eb" opacity="0.8" />

              {/* Roof Entablature */}
              <rect x="64" y="70" width="112" height="6" fill="#93c5fd" rx="1" />

              {/* Classical Columns (6 columns) */}
              <rect x="74" y="76" width="6" height="52" fill="#dbeafe" rx="1" />
              <rect x="91" y="76" width="6" height="52" fill="#dbeafe" rx="1" />
              <rect x="108" y="76" width="6" height="52" fill="#dbeafe" rx="1" />
              <rect x="126" y="76" width="6" height="52" fill="#dbeafe" rx="1" />
              <rect x="143" y="76" width="6" height="52" fill="#dbeafe" rx="1" />
              <rect x="160" y="76" width="6" height="52" fill="#dbeafe" rx="1" />

              {/* Building Facade Windows */}
              <rect x="83" y="86" width="5" height="10" fill="#3b82f6" opacity="0.6" rx="1" />
              <rect x="83" y="104" width="5" height="10" fill="#3b82f6" opacity="0.6" rx="1" />
              <rect x="117" y="98" width="6" height="24" fill="#1d4ed8" opacity="0.8" rx="2" />
              <rect x="152" y="86" width="5" height="10" fill="#3b82f6" opacity="0.6" rx="1" />
              <rect x="152" y="104" width="5" height="10" fill="#3b82f6" opacity="0.6" rx="1" />

              {/* Base / Stairs */}
              <rect x="62" y="128" width="116" height="5" fill="#93c5fd" rx="1" />
              <rect x="54" y="133" width="132" height="5" fill="#bfdbfe" rx="1" />
              <rect x="46" y="138" width="148" height="5" fill="#cbd5e1" rx="1" />

              {/* Ground line */}
              <line x1="20" y1="143" x2="220" y2="143" stroke="#e2e8f0" strokeWidth="2" strokeLinecap="round" />
            </svg>
          </div>

          {/* College Motto */}
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', maxWidth: '130px' }}>
            <span style={{
              fontStyle: 'italic',
              fontSize: '0.95rem',
              color: '#64748b',
              fontWeight: '500',
              lineHeight: 1.4,
              marginBottom: '0.75rem'
            }}>
              "Engineering for a Better Tomorrow"
            </span>
            <div style={{
              width: '36px',
              height: '3px',
              backgroundColor: '#2563eb',
              borderRadius: '2px'
            }} />
          </div>
        </div>
      </div>
    </div>
  );
};
