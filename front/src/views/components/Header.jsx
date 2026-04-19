import { motion } from 'framer-motion';
import { Zap } from 'lucide-react';

export function Header({ activeTab, roleType, onRoleChange }) {
  return (
    <header className="flex justify-between items-center mb-10">
      <motion.div initial={{ x: -20, opacity: 0 }} animate={{ x: 0, opacity: 1 }}>
        <h2 className="text-3xl font-black tracking-tighter uppercase italic text-slate-800">{activeTab}</h2>
        <p className="text-slate-500 font-medium tracking-tight">Intelligence Command Center v3.0</p>
      </motion.div>
      
      <div className="flex items-center gap-6">
        {/* Animated Segmented Control */}
        <div className="relative flex bg-slate-200/50 p-1 rounded-2xl border border-slate-200/60 shadow-inner w-72">
          {/* Slider Background */}
          <motion.div 
            layoutId="roleSlider"
            className="absolute bg-[#0A5C5C] rounded-xl shadow-lg h-[calc(100%-8px)]"
            initial={false}
            animate={{ 
              x: roleType === 'Medical' ? 0 : '100%',
              width: '50%'
            }}
            transition={{ type: "spring", stiffness: 400, damping: 30 }}
          />
          
          {['Medical', 'Commercial'].map(r => (
            <button 
              key={r} 
              onClick={() => onRoleChange?.(r)}
              className={`relative flex-1 py-2 rounded-xl font-black text-[10px] uppercase tracking-widest transition-colors duration-200 z-10 ${roleType === r ? 'text-white' : 'text-slate-400 hover:text-slate-600'}`}
            >
              {r}
            </button>
          ))}
        </div>

        <div className="px-5 py-2.5 bg-white border border-slate-200 rounded-full text-sm font-bold shadow-sm">
          <span className="text-slate-400 mr-2 font-medium">MARCH 2026</span>
        </div>
        <button className="flex items-center gap-2 px-6 py-2.5 bg-[#0A5C5C] text-white rounded-full font-bold text-sm shadow-lg shadow-teal-900/20 hover:scale-105 transition-transform">
          <Zap size={16} fill="currentColor" /> Live Sync
        </button>
      </div>
    </header>
  );
}
