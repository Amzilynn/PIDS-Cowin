import React from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import { motion, AnimatePresence } from 'framer-motion';
import { ShieldCheck, Globe, Activity } from 'lucide-react';

export default function MainLayout({ role = 'delegate', subRole = 'medical' }) {
  const location = useLocation();
  const isTheaterView = location.pathname.includes('/training') || location.pathname.includes('/presentation');

  return (
    <div className="flex bg-md3-surface min-h-screen font-sans overflow-hidden">
      {/* Persistent Animated Background Elements */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute top-[10%] right-[15%] w-[600px] h-[600px] organic-glow bg-md3-primary/10" />
        <div className="absolute bottom-[10%] left-[20%] w-[400px] h-[400px] organic-glow bg-md3-tertiary/10 scale-150" />
        <div className="absolute top-[50%] left-[50%] w-[800px] h-[800px] organic-glow bg-md3-secondary-container/5 -translate-x-1/2 -translate-y-1/2" />
      </div>

      <Sidebar role={role} subRole={subRole} />
      
      <main className={`flex-1 lg:ml-80 h-screen overflow-y-auto relative flex flex-col ${isTheaterView ? '!p-0 !gap-0' : 'p-8 gap-10'}`}>
        {/* Page Content with Transition */}
        <motion.div 
           initial={{ opacity: 0, x: 20 }}
           animate={{ opacity: 1, x: 0 }}
           transition={{ duration: 0.6, ease: "easeOut" }}
           className={`relative z-10 flex-1 w-full ${isTheaterView ? '!max-w-none' : 'max-w-7xl mx-auto'}`}
        >
           <Outlet />
        </motion.div>
        
        {/* System Monitoring Footer */}
        <footer className="relative z-10 border-t border-md3-outline/10 pt-10 pb-4 flex flex-col md:flex-row items-center justify-between gap-6">
           <div className="flex flex-wrap items-center gap-8">
              <div className="flex items-center gap-3">
                 <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse shadow-[0_0_8px_#10b981]" />
                 <span className="text-[10px] font-black text-md3-on-surface-variant uppercase tracking-widest leading-none">Cœur Vision IA : Connecté</span>
              </div>
              <div className="flex items-center gap-3 border-l border-md3-outline/10 pl-8">
                  <div className="w-2 h-2 bg-md3-primary rounded-full animate-pulse" />
                  <span className="text-[10px] font-black text-md3-on-surface-variant uppercase tracking-widest leading-none">Synchronisation Carte v4.1 : Active</span>
              </div>
              <div className="flex items-center gap-3 border-l border-md3-outline/10 pl-8">
                  <Activity size={14} className="text-md3-tertiary" />
                  <span className="text-[10px] font-black text-md3-on-surface-variant uppercase tracking-widest leading-none">Diagnostic temps réel : OPTIMAL</span>
              </div>
           </div>
           
           <div className="flex items-center gap-6 text-md3-outline/40">
              <span className="text-[9px] font-black uppercase tracking-[0.4em] text-center border ring-1 ring-md3-outline/10 px-4 py-2 rounded-pill">
                MedDelegate Pro — Propriété Intellectuelle Avalive 2026
              </span>
           </div>
        </footer>
      </main>

      <style jsx>{`
        ::-webkit-scrollbar {
          width: 6px;
        }
        ::-webkit-scrollbar-track {
          background: transparent;
        }
        ::-webkit-scrollbar-thumb {
          background: rgba(121, 116, 126, 0.1);
          border-radius: 10px;
        }
        ::-webkit-scrollbar-thumb:hover {
          background: rgba(121, 116, 126, 0.2);
        }
      `}</style>
    </div>
  );
}
