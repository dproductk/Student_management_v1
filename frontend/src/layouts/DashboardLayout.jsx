import React from 'react';
import { Outlet, Navigate, useLocation } from 'react-router-dom';
import { Navbar } from './Navbar';
import { Sidebar } from './Sidebar';
import { useAuth } from '../context/AuthContext';
import collegeLogo from '../assets/college-logo.jpg';

/**
 * EDVANA Dashboard Layout
 * - Sticky blue Navbar at top
 * - Profile sidebar on left
 * - Main content area with blue banner header (breadcrumb + page title + college crest)
 * - Content cards in light #F4F6FB area
 */

// Map routes to page titles and breadcrumbs
const getPageMeta = (pathname) => {
  const routeMap = {
    '/dashboard': { title: 'Dashboard', breadcrumb: ['Home'], subtitle: 'Welcome to your student portal' },
    '/profile': { title: 'Student Profile', breadcrumb: ['Home', 'Student Profile'] },
    '/payment-history': { title: 'Payment History', breadcrumb: ['Home', 'Payment History'] },
    '/students': { title: 'Student Directory', breadcrumb: ['Home', 'Students'] },
    '/faculty': { title: 'Faculty & Teaching', breadcrumb: ['Home', 'Faculty'] },
    '/academic/departments': { title: 'Departments & Programs', breadcrumb: ['Home', 'Academic', 'Departments'] },
    '/academic/calendar': { title: 'Calendar & Batches', breadcrumb: ['Home', 'Academic', 'Calendar'] },
    '/academic/curriculum': { title: 'Schemes & Subjects', breadcrumb: ['Home', 'Academic', 'Curriculum'] },
    '/assessments': { title: 'Assessments & Unit Tests', breadcrumb: ['Home', 'Assessments'] },
    '/results': { title: 'Results & Gazette', breadcrumb: ['Home', 'Results'] },
    '/credits-eligibility': { title: 'Credits & Eligibility', breadcrumb: ['Home', 'Credits'] },
    '/finance': { title: 'Fees & Payment Ledger', breadcrumb: ['Home', 'Finance'] },
    '/reporting': { title: 'Executive Analytics', breadcrumb: ['Home', 'Reporting'] },
    '/verification': { title: 'Verification Queue', breadcrumb: ['Home', 'Verification'] },
    '/services': { title: 'Services & Requests', breadcrumb: ['Home', 'Services'] },
    '/register': { title: 'Register & Analytics', breadcrumb: ['Home', 'Register'] },
    '/onboarding/batches': { title: 'Government Import', breadcrumb: ['Home', 'Onboarding'] },
  };

  // Exact match
  if (routeMap[pathname]) return routeMap[pathname];

  // Faculty detail page
  if (pathname.startsWith('/faculty/')) {
    return { title: 'Faculty Profile', breadcrumb: ['Home', 'Faculty', 'Profile'] };
  }
  // Student profile page
  if (pathname.startsWith('/students/')) {
    return { title: 'Student Profile', breadcrumb: ['Home', 'Students', 'Profile'] };
  }

  return { title: 'Dashboard', breadcrumb: ['Home'], subtitle: 'Welcome to your student portal' };
};

export const DashboardLayout = () => {
  const { user, loading } = useAuth();
  const location = useLocation();
  const { title, breadcrumb, subtitle } = getPageMeta(location.pathname);

  if (loading) {
    return (
      <div style={{
        height: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'var(--bg-app)',
        color: 'var(--text-secondary)'
      }}>
        Loading session...
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <Navbar />
      <div style={{ display: 'flex', flex: 1 }}>
        <Sidebar />
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          {/* Blue Banner Header with College Emblem Badge */}
          <div style={{
            background: 'linear-gradient(135deg, #1d4ed8 0%, #2563eb 60%, #3b82f6 100%)',
            padding: '1.25rem 2rem 3.5rem 2rem',
            color: '#ffffff',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            position: 'relative',
            overflow: 'hidden',
          }}>
            {/* Background subtle watermark emblem */}
            <div style={{
              position: 'absolute',
              right: '-15px',
              top: '-15px',
              width: '160px',
              height: '160px',
              opacity: 0.07,
              pointerEvents: 'none',
              filter: 'invert(1)',
            }}>
              <img src={collegeLogo} alt="" style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
            </div>

            <div style={{ position: 'relative', zIndex: 2 }}>
              {/* Breadcrumb */}
              <div style={{
                fontSize: '0.8rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.35rem',
                opacity: 0.85,
                marginBottom: '0.4rem',
              }}>
                {breadcrumb.map((item, idx) => (
                  <span key={idx} style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                    {idx > 0 && <span>›</span>}
                    <span style={{ fontWeight: idx === breadcrumb.length - 1 ? '600' : '400' }}>
                      {item}
                    </span>
                  </span>
                ))}
              </div>

              {/* Page Title */}
              <h1 style={{
                fontSize: '1.75rem',
                fontWeight: '700',
                margin: 0,
                letterSpacing: '-0.02em',
                lineHeight: 1.2,
              }}>
                {title}
              </h1>
              {subtitle && (
                <p style={{
                  fontSize: '0.92rem',
                  opacity: 0.9,
                  marginTop: '0.3rem',
                  marginBottom: 0,
                  fontWeight: '400'
                }}>
                  {subtitle}
                </p>
              )}
            </div>

            {/* Official College Crest Banner Badge */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.85rem',
              position: 'relative',
              zIndex: 2,
              backgroundColor: 'rgba(255, 255, 255, 0.14)',
              backdropFilter: 'blur(8px)',
              padding: '0.45rem 1rem 0.45rem 0.5rem',
              borderRadius: '9999px',
              border: '1px solid rgba(255, 255, 255, 0.25)',
              boxShadow: '0 4px 12px rgba(0, 0, 0, 0.06)',
            }}>
              <div style={{
                width: '42px',
                height: '42px',
                borderRadius: '50%',
                backgroundColor: '#ffffff',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                overflow: 'hidden',
                padding: '2px',
                boxShadow: '0 2px 6px rgba(0, 0, 0, 0.15)',
                flexShrink: 0
              }}>
                <img
                  src={collegeLogo}
                  alt="Government College of Engineering Kolhapur Logo"
                  style={{ width: '100%', height: '100%', objectFit: 'contain' }}
                />
              </div>
              <div style={{ textAlign: 'left', lineHeight: 1.2 }}>
                <div style={{ fontSize: '0.78rem', fontWeight: '800', letterSpacing: '0.02em' }}>
                  GCE KOLHAPUR
                </div>
                <div style={{ fontSize: '0.68rem', opacity: 0.85, fontWeight: '500' }}>
                  Autonomous Institute
                </div>
              </div>
            </div>
          </div>

          {/* Content Area — overlapping the blue banner */}
          <main style={{
            flex: 1,
            marginTop: '-2.5rem',
            padding: '0 2rem 2rem 2rem',
            position: 'relative',
            zIndex: 10,
            backgroundColor: 'var(--bg-app)',
            borderTopLeftRadius: 'var(--radius-lg)',
            borderTopRightRadius: 'var(--radius-lg)',
            overflowY: 'auto',
          }}>
            <div style={{ paddingTop: '1.5rem' }}>
              <Outlet />
            </div>
          </main>

          {/* Footer */}
          <footer style={{
            padding: '0.75rem 2rem',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            fontSize: '0.75rem',
            color: 'var(--text-muted)',
            borderTop: '1px solid var(--border-subtle)',
            background: '#ffffff',
          }}>
            <span>Design & Developed by Patio Digital Pvt. Ltd.</span>
            <span>© 2026. All rights reserved.</span>
          </footer>
        </div>
      </div>
    </div>
  );
};
