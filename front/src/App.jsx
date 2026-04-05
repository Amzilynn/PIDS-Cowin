import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './views/auth/LoginPage';
import MainLayout from './components/MainLayout';

// Admin Pages
import AdminDashboard from './views/admin/AdminDashboard';

// Delegate Pages
import DelegateHome from './views/delegate/DelegateHome';
import TrainingRoom from './views/delegate/TrainingRoom';
import VisitPlanner from './views/delegate/VisitPlanner';
import EvaluationResults from './views/delegate/EvaluationResults';

// Doctor Pages
import DoctorView from './views/doctor/DoctorView';

/**
 * MedDelegate Pro - Root Application
 * Role-based routing system with premium layout wrapping
 */
export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Authentication */}
        <Route path="/" element={<LoginPage />} />
        <Route path="/login" element={<Navigate to="/" replace />} />

        {/* Admin Workspace */}
        <Route path="/admin" element={<MainLayout role="admin" />}>
          <Route index element={<Navigate to="dashboard" replace />} />
          <Route path="dashboard" element={<AdminDashboard />} />
          <Route path="delegates" element={<div className="p-10 text-brand-navy font-black">Delegate Management View (Planned)</div>} />
          <Route path="reports" element={<div className="p-10 text-brand-navy font-black">Analytics Reports View (Planned)</div>} />
        </Route>

        {/* Delegate Workspace */}
        <Route path="/delegate" element={<MainLayout role="delegate" />}>
          <Route index element={<Navigate to="home" replace />} />
          <Route path="home" element={<DelegateHome />} />
          <Route path="training" element={<TrainingRoom />} />
          <Route path="planner" element={<VisitPlanner />} />
          <Route path="results" element={<EvaluationResults />} />
        </Route>

        {/* Doctor Workspace */}
        <Route path="/doctor" element={<MainLayout role="doctor" />}>
          <Route index element={<Navigate to="receiver" replace />} />
          <Route path="receiver" element={<DoctorView />} />
        </Route>

        {/* Global Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
