import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  LayoutDashboard,
  UserCircle,
  Building2,
  Calendar,
  BookOpen,
  Users,
  ShieldCheck,
  FileText,
  FileSpreadsheet,
  CheckSquare,
  GraduationCap,
  BarChart3,
  CreditCard,
  Award,
  Sparkles,
  ClipboardList,
  Layers,
  Phone,
  Mail,
  KeyRound
} from 'lucide-react';

/**
 * EDVANA Sidebar — profile card + role-aware navigation
 * Matches the EDVANA design screenshots: white bg, user profile at top,
 * flat navigation items with blue active state + left accent bar.
 */
export const Sidebar = () => {
  const { user, hasRole } = useAuth();

  const userName = user?.full_name || user?.username || 'User';
  const userInitials = (() => {
    const parts = userName.split(' ');
    if (parts.length >= 2) return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    return userName.substring(0, 2).toUpperCase();
  })();

  // Determine role flags
  const isSysAdmin = hasRole('SYSTEM_ADMIN') || user?.is_superuser;
  const isCollegeAdmin = hasRole('COLLEGE_ADMIN');
  const isHOD = hasRole('HOD');
  const isFaculty = hasRole('FACULTY');
  const isVerification = hasRole('VERIFICATION_OFFICER');
  const isAccountant = hasRole('ACCOUNTANT');
  const isExamCell = hasRole('EXAM_CELL');
  const isStudent = hasRole('STUDENT');

  const userRole = (() => {
    if (isSysAdmin) return 'System Admin';
    if (isCollegeAdmin) return 'Administrative Head';
    if (isHOD) return 'Head of Department';
    if (isFaculty) return 'Faculty Member';
    if (isVerification) return 'Verification Officer';
    if (isAccountant) return 'Accountant';
    if (isExamCell) return 'Exam Cell Officer';
    if (isStudent) return 'Student';
    if (user?.roles && user.roles.length > 0) {
      return user.roles[0].role__name || user.roles[0].name;
    }
    return 'User';
  })();

  const userId = user?.faculty_id || user?.enrollment_no || user?.username || '—';
  const userEmail = user?.email || '';
  const userPhone = user?.phone || '';

  // Build navigation based on role
  const getNavItems = () => {
    // 1. Student Navigation (Strictly student-scoped per user requirements)
    if (isStudent && !isSysAdmin && !isCollegeAdmin) {
      return [
        {
          label: 'STUDENT PORTAL',
          items: [
            { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
            { to: '/profile', label: 'View/Update Profile', icon: UserCircle },
            { to: '/payment-history', label: 'Payment History', icon: CreditCard },
            { to: '/services', label: 'Examination Form', icon: FileText, hasChildren: true },
            { to: '/results', label: 'Result (Summer 2026)', icon: Award },
          ]
        }
      ];
    }

    // 2. Accountant Navigation (Finance-scoped)
    if (isAccountant && !isSysAdmin && !isCollegeAdmin) {
      return [
        {
          label: 'FEES & FINANCE',
          items: [
            { to: '/finance', label: 'Candidate Fee Desk & Ledger', icon: CreditCard },
            { to: '/students', label: 'Student Directory', icon: Users },
          ]
        },
        {
          label: 'REPORTING',
          items: [
            { to: '/reporting', label: 'Financial Analytics', icon: BarChart3 },
          ]
        }
      ];
    }

    // 3. Verification Officer Navigation (Admissions & Verification)
    if (isVerification && !isSysAdmin && !isCollegeAdmin) {
      return [
        {
          label: 'VERIFICATION QUEUE',
          items: [
            { to: '/verification', label: 'Verification Queue & Audit', icon: CheckSquare },
            { to: '/students', label: 'Student Directory', icon: Users },
            { to: '/services', label: 'Services & Requests', icon: FileText },
          ]
        }
      ];
    }

    // 4. Exam Cell Navigation (Results & Assessments)
    if (isExamCell && !isSysAdmin && !isCollegeAdmin) {
      return [
        {
          label: 'EXAMINATION & RESULTS',
          items: [
            { to: '/results', label: 'Results & Gazette', icon: FileSpreadsheet },
            { to: '/assessments', label: 'Assessments & Tests', icon: Award },
            { to: '/credits-eligibility', label: 'Credits & Eligibility', icon: Sparkles },
            { to: '/students', label: 'Student Directory', icon: Users },
          ]
        },
        {
          label: 'REPORTING',
          items: [
            { to: '/reporting', label: 'Exam Analytics', icon: BarChart3 },
          ]
        }
      ];
    }

    // 5. Faculty Member Navigation (Teaching & Result entry)
    if (isFaculty && !isHOD && !isSysAdmin && !isCollegeAdmin) {
      return [
        {
          label: 'INSTRUCTION & TEACHING',
          items: [
            { to: '/faculty', label: 'Faculty & Teaching', icon: GraduationCap },
            { to: '/students', label: 'Student Directory', icon: Users },
            { to: '/assessments', label: 'Assessments & Tests', icon: ClipboardList },
            { to: '/results', label: 'Result History', icon: FileSpreadsheet },
          ]
        },
        {
          label: 'RESULT ANALYSIS',
          items: [
            { to: '/reporting', label: 'Result Analysis', icon: BarChart3 },
          ]
        }
      ];
    }

    // 6. HOD Navigation (Department-scoped management)
    if (isHOD && !isSysAdmin && !isCollegeAdmin) {
      return [
        {
          label: 'DEPARTMENT MANAGEMENT',
          items: [
            { to: '/academic/divisions', label: 'Student Divisions & Batches', icon: Layers },
            { to: '/faculty', label: 'Faculty & Teaching', icon: GraduationCap },
            { to: '/students', label: 'Department Students', icon: Users },
            { to: '/assessments', label: 'Workload & Tests', icon: ClipboardList },
            { to: '/results', label: 'Results & Performance', icon: FileSpreadsheet },
          ]
        },
        {
          label: 'CURRICULUM (READ-ONLY)',
          items: [
            { to: '/academic/curriculum', label: 'Schemes & Subjects', icon: BookOpen },
            { to: '/academic/calendar', label: 'Calendar & Sessions', icon: Calendar },
          ]
        },
        {
          label: 'REPORTING',
          items: [
            { to: '/reporting', label: 'Department Analytics', icon: BarChart3 },
          ]
        }
      ];
    }

    // 7. Administrative Head Navigation
    if (isCollegeAdmin && !isSysAdmin) {
      return [
        {
          label: 'STUDENTS & ADMISSIONS',
          items: [
            { to: '/onboarding/batches', label: 'Government Excel Ingestion', icon: FileSpreadsheet },
            { to: '/students', label: 'Student Directory & Filters', icon: Users },
            { to: '/academic/divisions', label: 'Class Divisions & Batches', icon: Layers },
            { to: '/verification', label: 'Verification Audit Trail', icon: CheckSquare },
            { to: '/services', label: 'Services & Requests', icon: FileText },
          ]
        },
        {
          label: 'FEES & FINANCE',
          items: [
            { to: '/finance/fee-heads', label: 'Fee Head Configuration', icon: CreditCard },
            { to: '/finance', label: 'Fee Desk & Payment Ledger', icon: CreditCard },
          ]
        },
        {
          label: 'ACADEMIC STRUCTURE (READ-ONLY)',
          items: [
            { to: '/academic/departments', label: 'Departments & Programs', icon: Building2 },
            { to: '/academic/calendar', label: 'Academic Calendar & Sessions', icon: Calendar },
            { to: '/academic/curriculum', label: 'Curriculum Schemes & Subjects', icon: BookOpen },
            { to: '/faculty', label: 'Faculty Roster', icon: GraduationCap },
            { to: '/results', label: 'Results & Eligibility Overview', icon: Award },
          ]
        },
        {
          label: 'INSTITUTIONAL REPORTING',
          items: [
            { to: '/reporting', label: 'Executive Analytics', icon: BarChart3 },
          ]
        }
      ];
    }

    // 8. System Admin (Full unrestricted access including Administration)
    return [
      {
        label: 'ACADEMIC STRUCTURE',
        items: [
          { to: '/academic/departments', label: 'Departments & Programs', icon: Building2 },
          { to: '/academic/calendar', label: 'Calendar & Batches', icon: Calendar },
          { to: '/academic/curriculum', label: 'Schemes & Subjects', icon: BookOpen },
          { to: '/faculty', label: 'Faculty & Teaching', icon: GraduationCap },
          { to: '/assessments', label: 'Assessments & Tests', icon: Award },
          { to: '/results', label: 'Results & Gazette', icon: FileSpreadsheet },
          { to: '/credits-eligibility', label: 'Credits & Eligibility', icon: Sparkles },
        ]
      },
      {
        label: 'STUDENTS & ENROLLMENT',
        items: [
          { to: '/students', label: 'Student Directory', icon: Users },
          { to: '/services', label: 'Services & Requests', icon: FileText },
          { to: '/register', label: 'Register & Analytics', icon: BarChart3 },
          { to: '/verification', label: 'Verification Queue', icon: CheckSquare },
          { to: '/onboarding/batches', label: 'Government Import', icon: FileSpreadsheet },
        ]
      },
      {
        label: 'FEES & FINANCE',
        items: [
          { to: '/finance', label: 'Fees & Payment Ledger', icon: CreditCard },
        ]
      },
      {
        label: 'REPORTING',
        items: [
          { to: '/reporting', label: 'Executive Analytics', icon: BarChart3 },
        ]
      },
      {
        label: 'ADMINISTRATION',
        items: [
          { to: '/admin/users', label: 'Users & Roles', icon: Users },
          { to: '/admin/audit', label: 'Security Audit Log', icon: ShieldCheck },
        ]
      }
    ];
  };

  const navGroups = getNavItems();

  return (
    <aside style={{
      width: '270px',
      minWidth: '270px',
      backgroundColor: '#ffffff',
      borderRight: '1px solid var(--border-subtle)',
      display: 'flex',
      flexDirection: 'column',
      minHeight: 'calc(100vh - 56px)',
      overflowY: 'auto',
    }}>
      {/* Profile Card */}
      <div style={{
        padding: '1.5rem 1.25rem',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        textAlign: 'center',
        borderBottom: '1px solid var(--border-subtle)',
      }}>
        {/* Avatar */}
        <div style={{
          width: '80px',
          height: '80px',
          borderRadius: '50%',
          background: 'linear-gradient(135deg, #bfdbfe, #93c5fd)',
          border: '3px solid #dbeafe',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '1.5rem',
          fontWeight: '700',
          color: '#1e40af',
          marginBottom: '0.75rem',
        }}>
          {userInitials}
        </div>

        {/* Name & ID */}
        <h3 style={{
          fontSize: '0.95rem',
          fontWeight: '700',
          color: 'var(--text-primary)',
          margin: 0,
          marginBottom: '0.15rem',
        }}>
          {userName.toUpperCase()}
        </h3>
        <div style={{
          fontSize: '0.72rem',
          fontWeight: '600',
          color: '#2563eb',
          marginBottom: '0.35rem',
        }}>
          {userRole}
        </div>
        <p style={{
          fontSize: '0.75rem',
          color: 'var(--text-muted)',
          marginBottom: '0.5rem',
        }}>
          ID: {userId}
        </p>

        {/* Status Badge */}
        <span style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '0.3rem',
          fontSize: '0.7rem',
          fontWeight: '600',
          color: '#059669',
          background: '#ecfdf5',
          padding: '0.2rem 0.65rem',
          borderRadius: 'var(--radius-full)',
          border: '1px solid #a7f3d0',
          marginBottom: '1rem',
        }}>
          <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#059669' }}></span>
          Active
        </span>

        {/* Contact Info */}
        <div style={{
          width: '100%',
          borderTop: '1px solid var(--border-subtle)',
          paddingTop: '0.75rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.5rem',
          textAlign: 'left',
        }}>
          {userPhone && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              <Phone size={14} style={{ color: 'var(--text-muted)' }} />
              {userPhone}
            </div>
          )}
          {userEmail && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem', color: 'var(--text-secondary)', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              <Mail size={14} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
              <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{userEmail}</span>
            </div>
          )}
        </div>
      </div>

      {/* Navigation */}
      <nav style={{ padding: '0.75rem 0.5rem', flex: 1 }}>
        {navGroups.map((group, groupIdx) => (
          <div key={groupIdx} style={{ marginBottom: '0.75rem' }}>
            {group.label && (
              <span style={{
                display: 'block',
                fontSize: '0.65rem',
                fontWeight: '700',
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
                color: 'var(--text-muted)',
                padding: '0.5rem 0.85rem 0.35rem',
              }}>
                {group.label}
              </span>
            )}
            {group.items.map((item, itemIdx) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={itemIdx}
                  to={item.to}
                  end={item.to === '/faculty'}
                  style={({ isActive }) => ({
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    gap: '0.65rem',
                    padding: '0.6rem 0.85rem',
                    borderRadius: 'var(--radius-md)',
                    fontSize: '0.85rem',
                    fontWeight: isActive ? '600' : '500',
                    color: isActive ? '#2563eb' : 'var(--text-secondary)',
                    backgroundColor: isActive ? '#eff6ff' : 'transparent',
                    borderLeft: isActive ? '3px solid #2563eb' : '3px solid transparent',
                    transition: 'all 0.15s ease',
                    textDecoration: 'none',
                    marginBottom: '0.1rem',
                  })}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                    <Icon size={18} />
                    <span>{item.label}</span>
                  </div>
                  {item.hasChildren && (
                    <span style={{ fontSize: '0.75rem', opacity: 0.5 }}>›</span>
                  )}
                </NavLink>
              );
            })}
          </div>
        ))}
      </nav>
    </aside>
  );
};
