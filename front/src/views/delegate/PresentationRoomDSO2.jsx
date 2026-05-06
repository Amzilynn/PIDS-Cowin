import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ChevronLeft, 
  PlusSquare, 
  Package, 
  CheckCircle2, 
  Clock, 
  ArrowRight,
  ShieldCheck,
  Star,
  Activity
} from 'lucide-react';
import Avatar3DDSO2 from '../../components/Avatar3DDSO2';
import CameraPanelDSO2 from '../../components/CameraPanelDSO2';
import ChatPanelDSO2 from '../../components/ChatPanelDSO2';
import { useAuth } from '../../context/AuthContext';

export default function PresentationRoomDSO2() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const location = useLocation();
  const query = new URLSearchParams(location.search);
  const subRole = query.get('sub') || 'medical';
  const isMedical = subRole === 'medical' || subRole === 'doctor';
  
  const establishmentName = isMedical ? 'CENTRE HOSPITALIER UNIVERSITAIRE' : 'PHARMACIE VALÉRIE BERNARD';
  
  const [isActive, setIsActive] = useState(false);

  const handleConnect = () => setIsActive(true);
  const handleDisconnect = () => {
    setIsActive(false);
  };

  return (
    <div className="relative h-screen bg-[#f8fafb] flex flex-col font-sans overflow-hidden">
      
      {/* ── Top Bar (Minimalist as per Image) ── */}
      <div className="h-16 border-b border-slate-100 bg-white flex items-center justify-between px-8 relative z-50">
        <div className="flex items-center gap-6">
           <button 
             onClick={() => navigate(-1)}
             className="w-8 h-8 rounded-lg bg-slate-50 flex items-center justify-center text-slate-400 hover:text-slate-600 transition-all"
           >
              <ChevronLeft size={18} />
           </button>
           
           <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
                 <Activity size={16} />
              </div>
              <h1 className="text-[12px] font-black text-slate-800 uppercase tracking-widest">{establishmentName}</h1>
           </div>
        </div>

        <div className="flex items-center gap-2">
           <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
           <span className="text-[10px] font-black text-emerald-600 uppercase tracking-widest">En direct</span>
        </div>
      </div>

      {/* ── Main Layout (3 Balanced Panels) ── */}
      <div className="flex-1 flex overflow-hidden p-6 gap-6">
        
        {/* PANEL 1 : Avatar (Left) */}
        <div className="flex-1 h-full relative">
           <Avatar3DDSO2 
             isActive={isActive} 
             onConnect={handleConnect}
             onDisconnect={handleDisconnect}
           />
        </div>

        {/* PANEL 2 : Practitioner Feed (Middle) */}
        <div className="flex-1 h-full relative rounded-[32px] overflow-hidden bg-white shadow-sm border border-slate-50">
           <CameraPanelDSO2 label="FLUX PRATICIEN" />
        </div>

        {/* PANEL 3 : Chat Panel (Right) */}
        <div className="flex-1 h-full relative rounded-[32px] overflow-hidden bg-white shadow-sm border border-slate-50">
           <ChatPanelDSO2 isActive={isActive} />
        </div>

      </div>

      {/* Decorative Signature Glows */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-emerald-500/5 blur-[120px] rounded-full -z-10 pointer-events-none" />
    </div>
  );
}
