import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';

import LoginPage from './views/auth/LoginPage';
import AdminApp from './views/admin/AdminApp';
import DelegateLayout from './views/delegate/DelegateLayout';
import EvaluationPage from './views/delegate/EvaluationPage';
import TrainingPage from './views/delegate/TrainingPage';
import AssistantPage from './views/delegate/AssistantPage';
import DoctorGuestPage from './views/doctor/DoctorGuestPage';
import DSO1Page from './views/dso/DSO1Page';
import DSO2Page from './views/dso/DSO2Page';
import DSO3Page from './views/dso/DSO3Page';
import DSO4Page from './views/dso/DSO4Page';

function ProtectedRoute({ children, allowedRole }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/" replace />;
  if (allowedRole && user.role !== allowedRole) return <Navigate to="/" replace />;
  return children;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<LoginPage />} />

      {/* Admin */}
      <Route path="/admin/*" element={
        <ProtectedRoute allowedRole="admin"><AdminApp /></ProtectedRoute>
      } />

      {/* Delegate */}
      <Route path="/delegate" element={
        <ProtectedRoute allowedRole="delegate"><DelegateLayout /></ProtectedRoute>
      }>
        <Route index element={<Navigate to="evaluation" replace />} />
        <Route path="evaluation" element={<EvaluationPage />} />
        <Route path="training" element={<TrainingPage />} />
        <Route path="assistant" element={<AssistantPage />} />
      </Route>

      {/* Doctor guest */}
      <Route path="/doctor" element={<DoctorGuestPage />} />

      {/* DSO */}
      <Route path="/dso/1" element={<DSO1Page />} />
      <Route path="/dso/2" element={<DSO2Page />} />
      <Route path="/dso/3" element={<DSO3Page />} />
      <Route path="/dso/4" element={<DSO4Page />} />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}
