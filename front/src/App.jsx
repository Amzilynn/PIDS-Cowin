import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import MainLayout from './components/MainLayout';

// Pages Auth
import LoginPage from './views/auth/LoginPage';

// Pages Admin
import AdminDashboard from './views/admin/AdminDashboard';

// Pages Délégué
import DelegateHome from './views/delegate/DelegateHome';
import TrainingRoom from './views/delegate/TrainingRoom';
import ProductSelection from './views/delegate/ProductSelection';
import PresentationRoom from './views/delegate/PresentationRoom';
import VisitPlanner from './views/delegate/VisitPlanner';
import EvaluationResults from './views/delegate/EvaluationResults';
import ProductRecommendations from './views/delegate/ProductRecommendations';

// Pages Praticien (médecin / pharmacien)
import PractitionerView from './views/practitioner/PractitionerView';

// ─────────────────────────────────────────────────────────────────────────────
// Route protégée : redirige vers / si pas connecté
// ─────────────────────────────────────────────────────────────────────────────
function ProtectedRoute({ children, allowedTypes }) {
  const { isAuthenticated, user, loading } = useAuth();

  if (loading) {
    // Pendant la vérification du localStorage, on n'affiche rien
    return (
      <div className="h-screen flex items-center justify-center bg-md-surface">
        <div className="animate-spin w-8 h-8 border-4 border-md-primary border-t-transparent rounded-full" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  // Si des types sont spécifiés, vérifier que l'utilisateur a le bon type
  if (allowedTypes && !allowedTypes.includes(user?.type)) {
    // Redirige vers la page adéquate selon son vrai rôle
    return <Navigate to={user?.redirect_to || '/'} replace />;
  }

  return children;
}

// ─────────────────────────────────────────────────────────────────────────────
// App principale
// ─────────────────────────────────────────────────────────────────────────────
export default function App() {
  const { user } = useAuth();

  // Le sub_role vient maintenant du JWT stocké en contexte
  const subRole = user?.sub_role || 'medical';

  return (
    <Routes>
      {/* ── Page de Connexion (publique) ────────────────────── */}
      <Route path="/" element={<LoginPage />} />

      {/* ── Routes Administrateur ───────────────────────────── */}
      <Route
        path="/admin"
        element={
          <ProtectedRoute allowedTypes={['admin']}>
            <MainLayout role="admin" />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="dashboard" replace />} />
        <Route path="dashboard" element={<AdminDashboard />} />
        <Route path="stats"     element={<AdminDashboard />} />
        <Route path="delegues"  element={<AdminDashboard />} />
      </Route>

      {/* ── Routes Délégué (Medical / Commercial) ───────────── */}
      <Route
        path="/delegate"
        element={
          <ProtectedRoute allowedTypes={['delegue']}>
            <MainLayout role="delegate" subRole={subRole} />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="home" replace />} />
        <Route path="home"             element={<DelegateHome subRole={subRole} />} />
        <Route path="training"         element={<ProductSelection />} />
        <Route path="training/session" element={<TrainingRoom type={subRole} />} />
        <Route path="presentation"     element={<PresentationRoom subRole={subRole} />} />
        <Route path="produits"         element={<ProductRecommendations subRole={subRole} />} />
        <Route path="planner"          element={<VisitPlanner />} />
        <Route path="results"          element={<EvaluationResults />} />
        <Route path="profil"           element={<DelegateHome subRole={subRole} />} />
      </Route>

      {/* ── Routes Praticien (Médecin / Pharmacien) ─────────── */}
      <Route
        path="/practitioner"
        element={
          <ProtectedRoute allowedTypes={['medecin', 'pharmacien']}>
            <MainLayout
              role="practitioner"
              subRole={subRole}
            />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="presentations" replace />} />
        <Route
          path="home"
          element={
            <PractitionerView
              roleType={subRole === 'doctor' ? 'doctor' : 'pharmacist'}
            />
          }
        />
        <Route
          path="presentations"
          element={
            <PractitionerView
              roleType={subRole === 'doctor' ? 'doctor' : 'pharmacist'}
            />
          }
        />
        <Route path="agenda" element={<VisitPlanner />} />
        <Route
          path="profil"
          element={
            <PractitionerView
              roleType={subRole === 'doctor' ? 'doctor' : 'pharmacist'}
            />
          }
        />
      </Route>

      {/* ── Fallback ─────────────────────────────────────────── */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
