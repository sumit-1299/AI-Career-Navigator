import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Layout } from './components/layout/Layout';
import { AuthLayout } from './components/auth/AuthLayout';
import { RequireAuth, PublicOnly } from './components/auth/RouteGuards';
import { PublicJobsLayout } from './components/jobs/PublicJobsLayout';

import { LandingPage } from './pages/LandingPage';
import { DashboardPage } from './pages/DashboardPage';
import { CareersPage } from './pages/CareersPage';
import { SkillGapPage } from './pages/SkillGapPage';
import { PracticalTasksPage } from './pages/PracticalTasksPage';
import { SkillsPage } from './pages/SkillsPage';
import { LearningPage } from './pages/LearningPage';
import { ResumePage } from './pages/ResumePage';
import { CareerComparisonPage } from './pages/CareerComparisonPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { ProfilePage } from './pages/ProfilePage';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { ForgotPasswordPage } from './pages/ForgotPasswordPage';
import { ResetPasswordPage } from './pages/ResetPasswordPage';
import { TechJobsPage } from './pages/TechJobsPage';
import { JobAlignmentPage } from './pages/JobAlignmentPage';

function HomeGate() {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? <DashboardPage /> : <LandingPage />;
}

export function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<PublicOnly><AuthLayout /></PublicOnly>}>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />
            <Route path="/app" element={<ResetPasswordPage />} />
            <Route path="/reset-password" element={<ResetPasswordPage />} />
          </Route>

          <Route element={<PublicJobsLayout />}>
            <Route path="/jobs" element={<TechJobsPage />} />
            <Route
              path="/jobs/:sourceKey/:providerId"
              element={<JobAlignmentPage />}
            />
          </Route>

          <Route path="/" element={<HomeGate />} />

          <Route
            path="/workspace"
            element={
              <RequireAuth>
                <Layout />
              </RequireAuth>
            }
          >
            <Route index element={<DashboardPage />} />
            <Route path="careers" element={<CareersPage />} />
            <Route path="skill-gap" element={<SkillGapPage />} />
            <Route path="tasks" element={<PracticalTasksPage />} />
            <Route path="skills" element={<SkillsPage />} />
            <Route path="learning" element={<LearningPage />} />
            <Route path="resume" element={<ResumePage />} />
            <Route path="compare" element={<CareerComparisonPage />} />
            <Route path="analytics" element={<AnalyticsPage />} />
            <Route path="profile" element={<ProfilePage />} />
          </Route>

          {[
            ['careers', CareersPage],
            ['skill-gap', SkillGapPage],
            ['tasks', PracticalTasksPage],
            ['skills', SkillsPage],
            ['learning', LearningPage],
            ['resume', ResumePage],
            ['compare', CareerComparisonPage],
            ['analytics', AnalyticsPage],
            ['profile', ProfilePage],
          ].map(([path, Page]) => (
            <Route
              key={path}
              path={`/${path}`}
              element={
                <RequireAuth>
                  <Layout />
                </RequireAuth>
              }
            >
              <Route index element={<Page />} />
            </Route>
          ))}

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
