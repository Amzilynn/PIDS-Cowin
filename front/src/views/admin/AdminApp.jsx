import { Routes, Route, Navigate } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import { useAvalifeController } from '../../controllers/useAvalifeController';
import Sidebar from '../components/Sidebar';
import { Header } from '../components/Header';
import { pageVariants, springTransition } from '../components/Card';
import { useAuth } from '../../context/AuthContext';

import AdminDashboard from './AdminDashboard';
import { TerritoryView } from '../pages/TerritoryView';
import { TrainingView } from '../pages/TrainingView';
import { MedicalAIView } from '../pages/MedicalAIView';
import { AnalyticsView } from '../pages/AnalyticsView';

export default function AdminApp() {
  const { user, logout } = useAuth();
  const { state, actions } = useAvalifeController();
  const {
    activeTab, selectedRegion, simData,
    regionsData, products,
    chatMessages, chatInput, chatLoading, roleType
  } = state;

  return (
    <div className="flex h-screen bg-[#F8FAFC] text-slate-900 overflow-hidden font-sans">
      <Sidebar activeTab={activeTab} onTabChange={actions.handleTabChange} onLogout={logout} userLabel={user?.name} />

      <main className="flex-1 overflow-y-auto p-10 relative">
        <Header activeTab={activeTab} roleType={roleType} onRoleChange={actions.setRoleType} />

        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            variants={pageVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            transition={springTransition}
          >
            {/* Unified Dashboard Tab */}
            {activeTab === 'Dashboard' && (
              <AdminDashboard initialTab="synthèse" />
            )}

            {/* Direct access to specific management tabs if needed via sidebar mapping */}
            {activeTab === 'produits' && (
              <AdminDashboard initialTab="produits" />
            )}

            {activeTab === 'Territory' && (
              <TerritoryView selectedRegion={selectedRegion} regionsData={regionsData} onRegionSelect={actions.handleRegionSelect} />
            )}

            {activeTab === 'Training' && (
              <TrainingView simData={simData} chatMessages={chatMessages} chatInput={chatInput} chatLoading={chatLoading} onSendChat={actions.handleSendChat} setChatInput={actions.setChatInput} />
            )}

            {activeTab === 'Medical AI' && (
              <MedicalAIView products={products} onQueryChange={actions.handleMedQueryChange} />
            )}

            {activeTab === 'Analytics' && (
              <AdminDashboard initialTab="stats" />
            )}
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  );
}
