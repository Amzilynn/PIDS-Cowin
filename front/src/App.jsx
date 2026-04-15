import React from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import MainLayout from './components/MainLayout';
import LoginPage from './views/auth/LoginPage';
import AdminDashboard from './views/admin/AdminDashboard';
import DelegateHome from './views/delegate/DelegateHome';
import TrainingRoom from './views/delegate/TrainingRoom';
import PresentationRoom from './views/delegate/PresentationRoom';
import VisitPlanner from './views/delegate/VisitPlanner';
import EvaluationResults from './views/delegate/EvaluationResults';
import ProductRecommendations from './views/delegate/ProductRecommendations';
import PractitionerView from './views/practitioner/PractitionerView';

// Utilitaire pour extraire les paramètres de rôle de l'URL
function useQuery() {
  return new URLSearchParams(useLocation().search);
}

export default function App() {
  const location = useLocation();
  const query = new URLSearchParams(location.search);
  const subRoleParam = query.get('sub') || 'medical';
  const searchStr = location.search;

  return (
    <Routes>
      {/* Page de Connexion sans Sidebar */}
      <Route path="/" element={<LoginPage />} />

      {/* Routes Administrateur */}
      <Route path="/admin" element={<MainLayout role="admin" />}>
        <Route index element={<Navigate to={`dashboard${searchStr}`} replace />} />
        <Route path="dashboard" element={<AdminDashboard />} />
        <Route path="stats" element={<AdminDashboard />} />
        <Route path="delegues" element={<AdminDashboard />} />
      </Route>

      {/* Routes Délégué (Médical ou Commercial) */}
      <Route path="/delegate" element={<MainLayout role="delegate" subRole={subRoleParam} />}>
        <Route index element={<Navigate to={`home${searchStr}`} replace />} />
        <Route path="home" element={<DelegateHome subRole={subRoleParam} />} />
        <Route path="training" element={<TrainingRoom type={subRoleParam} />} />
        <Route path="presentation" element={<PresentationRoom subRole={subRoleParam} />} />
        <Route path="produits" element={<ProductRecommendations subRole={subRoleParam} />} />
        <Route path="planner" element={<VisitPlanner />} />
        <Route path="results" element={<EvaluationResults />} />
        <Route path="profil" element={<DelegateHome subRole={subRoleParam} />} />
      </Route>

      {/* Routes Praticien (Médecin ou Pharmacien) */}
      <Route path="/medecin" element={<MainLayout role="medecin" subRole={subRoleParam} />}>
        <Route index element={<Navigate to={`presentations${searchStr}`} replace />} />
        <Route path="home" element={<PractitionerView roleType="doctor" />} />
        <Route path="presentations" element={<PractitionerView roleType="doctor" />} />
        <Route path="agenda" element={<VisitPlanner />} /> {/* Réutilisation du Planner compatible */}
        <Route path="profil" element={<PractitionerView roleType="doctor" />} />
      </Route>

      {/* Alias legacy */}
      <Route path="/practitioner" element={<Navigate to={`/medecin/presentations${searchStr}`} replace />}>
        <Route path="*" element={<Navigate to={`/medecin/presentations${searchStr}`} replace />} />
      </Route>

      {/* Redirection par défaut */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
