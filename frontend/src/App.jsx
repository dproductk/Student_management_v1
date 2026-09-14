import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { DashboardLayout } from './layouts/DashboardLayout';
import { LoginPage } from './modules/auth/LoginPage';
import { DepartmentList } from './modules/academic/DepartmentList';
import { AcademicCalendarPage } from './modules/academic/AcademicCalendarPage';
import { CurriculumPage } from './modules/academic/CurriculumPage';
import { StudentDirectory } from './modules/students/StudentDirectory';
import { StudentProfile } from './modules/students/StudentProfile';
import { StudentDashboard } from './modules/students/StudentDashboard';
import { StudentPaymentHistory } from './modules/students/StudentPaymentHistory';
import { ImportBatchList } from './modules/onboarding/ImportBatchList';
import { VerificationQueue } from './modules/verification/VerificationQueue';
import { FacultyList } from './modules/faculty/FacultyList';
import { FacultyDetail } from './modules/faculty/FacultyDetail';
import { StudentRegister } from './modules/register/StudentRegister';
import { FeeManagementPage } from './modules/finance/FeeManagementPage';
import { FeeHeadConfigPage } from './modules/finance/FeeHeadConfigPage';
import { CandidateFeeDesk } from './modules/finance/CandidateFeeDesk';
import { DivisionBatchManagement } from './modules/faculty/DivisionBatchManagement';
import { AssessmentManagementPage } from './modules/assessments/AssessmentManagementPage';
import { ResultManagementPage } from './modules/results/ResultManagementPage';
import { EligibilityDashboard } from './modules/results/EligibilityDashboard';
import { StudentServicesPage } from './modules/services/StudentServicesPage';
import { AnalyticsDashboardPage } from './modules/reporting/AnalyticsDashboardPage';

const isStudentOnly = (user, hasRole) => {
  return hasRole('STUDENT') && !hasRole('SYSTEM_ADMIN') && !hasRole('COLLEGE_ADMIN');
};

// Students land on Dashboard, staff land on Directory
const IndexRedirect = () => {
  const { user, hasRole } = useAuth();
  if (isStudentOnly(user, hasRole)) {
    return <Navigate to="/dashboard" replace />;
  }
  return <Navigate to="/students" replace />;
};

// Route students to dedicated StudentPaymentHistory and staff to FeeManagementPage
const FinanceRoute = () => {
  const { user, hasRole } = useAuth();
  if (isStudentOnly(user, hasRole)) {
    return <StudentPaymentHistory />;
  }
  return <FeeManagementPage />;
};

// Block pure STUDENT role from accessing the full directory
const RequireStaff = ({ children }) => {
  const { user, hasRole } = useAuth();
  if (isStudentOnly(user, hasRole)) {
    return <Navigate to="/dashboard" replace />;
  }
  return children;
};

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={<DashboardLayout />}>
            <Route index element={<IndexRedirect />} />
            <Route path="dashboard" element={<StudentDashboard />} />
            <Route path="students" element={<RequireStaff><StudentDirectory /></RequireStaff>} />
            <Route path="students/:id" element={<RequireStaff><StudentProfile /></RequireStaff>} />
            <Route path="profile" element={<StudentProfile />} />
            <Route path="payment-history" element={<StudentPaymentHistory />} />
            <Route path="services" element={<StudentServicesPage />} />
            <Route path="register" element={<StudentRegister />} />
            <Route path="assessments" element={<AssessmentManagementPage />} />
            <Route path="results" element={<ResultManagementPage />} />
            <Route path="credits-eligibility" element={<EligibilityDashboard />} />
            <Route path="finance" element={<FinanceRoute />} />
            <Route path="finance/fee-heads" element={<FeeHeadConfigPage />} />
            <Route path="finance/candidate-fee" element={<CandidateFeeDesk />} />
            <Route path="reporting" element={<AnalyticsDashboardPage />} />
            <Route path="faculty" element={<FacultyList />} />
            <Route path="faculty/:id" element={<FacultyDetail />} />
            <Route path="verification" element={<VerificationQueue />} />
            <Route path="onboarding/batches" element={<ImportBatchList />} />
            <Route path="academic/departments" element={<DepartmentList />} />
            <Route path="academic/calendar" element={<AcademicCalendarPage />} />
            <Route path="academic/curriculum" element={<CurriculumPage />} />
            <Route path="academic/divisions" element={<DivisionBatchManagement />} />
            {/* Fallback */}
            <Route path="*" element={<IndexRedirect />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
