import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import { motion } from 'framer-motion';

export default function MainLayout({ role = 'delegate' }) {
  return (
    <div className="flex bg-slate-50 min-h-screen font-sans">
      <Sidebar role={role} />
      
      <main className="flex-1 h-screen overflow-y-auto p-12 relative flex flex-col gap-12">
        {/* Animated Background Mesh */}
        <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-brand-teal/5 blur-[120px] rounded-full translate-x-1/4 -translate-y-1/4 pointer-events-none" />
        <div className="absolute bottom-0 left-0 w-[400px] h-[400px] bg-brand-navy/5 blur-[100px] rounded-full -translate-x-1/4 translate-y-1/4 pointer-events-none" />
        
        <div className="relative z-10 flex-1">
           <Outlet />
        </div>
        
        {/* Global Footer / System Status */}
        <footer className="relative z-10 border-t border-slate-200/60 pt-8 flex items-center justify-between">
           <div className="flex items-center gap-6">
              <div className="flex items-center gap-2">
                 <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse" />
                 <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest leading-none">CV ANALYTICS CORE: ONLINE</span>
              </div>
              <div className="flex items-center gap-2 border-l border-slate-200 pl-6">
                  <div className="w-1.5 h-1.5 bg-brand-teal rounded-full animate-pulse" />
                  <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest leading-none">MAP SYNC v4.1: ACTIVE</span>
              </div>
           </div>
           
           <div className="flex items-center gap-4 text-slate-300">
              <span className="text-[9px] font-black uppercase tracking-[0.3em]">MedDelegate Pro — Avalive Intellectual Proprietary</span>
           </div>
        </footer>
      </main>
    </div>
  );
}
