import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { Layout } from './components/layout/Layout';

import { DashboardPage } from './pages/DashboardPage';
import { CareersPage } from './pages/CareersPage';
import { SkillGapPage } from './pages/SkillGapPage';
import { SkillsPage } from './pages/SkillsPage';
import { LearningPage } from './pages/LearningPage';
import { ResumePage } from './pages/ResumePage';
import { CareerComparisonPage } from './pages/CareerComparisonPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { JobOpportunityPage } from './pages/JobOpportunityPage';
import { PracticalTaskPage } from './pages/PracticalTaskPage';
import { ProfilePage } from './pages/ProfilePage';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';

export function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<DashboardPage />} />
            <Route path="careers" element={<CareersPage />} />
            <Route path="jobs" element={<JobOpportunityPage />} />
            <Route path="practical-tasks" element={<PracticalTaskPage />} />
            <Route path="skill-gap" element={<SkillGapPage />} />
            <Route path="skills" element={<SkillsPage />} />
            <Route path="learning" element={<LearningPage />} />
            <Route path="resume" element={<ResumePage />} />
            <Route path="compare" element={<CareerComparisonPage />} />
            <Route path="analytics" element={<AnalyticsPage />} />
            <Route path="profile" element={<ProfilePage />} />
            <Route path="login" element={<LoginPage />} />
            <Route path="register" element={<RegisterPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
