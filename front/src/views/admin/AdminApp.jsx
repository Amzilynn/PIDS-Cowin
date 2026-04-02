import { Routes, Route, Navigate } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import { useAvalifeController } from '../../controllers/useAvalifeController';
import { Sidebar } from '../components/Sidebar';
import { Header } from '../components/Header';
import { pageVariants, springTransition } from '../components/Card';
import { useAuth } from '../../context/AuthContext';

import { DashboardView } from '../pages/DashboardView';
import { TerritoryView } from '../pages/TerritoryView';
import { TrainingView } from '../pages/TrainingView';
import { MedicalAIView } from '../pages/MedicalAIView';
import { AnalyticsView } from '../pages/AnalyticsView';

export default function AdminApp() {
  const { user, logout } = useAuth();
  const { state, actions } = useAvalifeController();
  const {
    activeTab, selectedRegion, simData,
    stats, regionsData, streamLogs, visits, kpis, products,
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
            {activeTab === 'Dashboard' && (
              <DashboardView stats={stats} streamLogs={streamLogs} visits={visits} kpis={kpis} roleType={roleType} />
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
              <AnalyticsView kpis={kpis} visits={visits} products={products} roleType={roleType} />
            )}
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  );
}
