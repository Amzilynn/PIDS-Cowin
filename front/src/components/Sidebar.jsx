import React from 'react';
import { 
  LayoutDashboard, 
  BrainCircuit, 
  Map as MapIcon, 
  BarChart3, 
  LogOut, 
  User,
  Settings,
  ShieldCheck,
  ChevronRight
} from 'lucide-react';
import { NavLink, useNavigate } from 'react-router-dom';
import Logo from './Logo';

export default function Sidebar({ role = 'delegate' }) {
  const navigate = useNavigate();

  const menuItems = {
    admin: [
      { to: '/admin/dashboard', icon: LayoutDashboard, label: 'Analytics Hub' },
      { to: '/admin/delegates', icon: User, label: 'Professionals' },
      { to: '/admin/reports', icon: BarChart3, label: 'Sector Reports' },
    ],
    delegate: [
      { to: '/delegate/home', icon: LayoutDashboard, label: 'Command Center' },
      { to: '/delegate/training', icon: BrainCircuit, label: 'Skill Simulator' },
      { to: '/delegate/planner', icon: MapIcon, label: 'Visit Optimizer' },
      { to: '/delegate/results', icon: BarChart3, label: 'Performance' },
    ],
    doctor: [
      { to: '/doctor/receiver', icon: LayoutDashboard, label: 'Receiver Mode' },
    ]
  };

  const activeMenu = menuItems[role] || menuItems.delegate;

  return (
    <div className="w-80 h-screen bg-brand-navy flex flex-col p-8 border-r border-white/5 relative overflow-hidden">
      {/* Background Decorative Glow */}
      <div className="absolute top-0 left-0 w-full h-full bg-brand-teal/5 blur-[80px] -translate-x-1/2 -translate-y-1/2" />
      
      <div className="relative z-10 mb-16 px-2">
         <Logo showText={true} />
      </div>

      <nav className="relative z-10 flex-1 space-y-3">
         {activeMenu.map((item) => (
            <NavLink
               key={item.to}
               to={item.to}
               className={({ isActive }) => 
                  `flex items-center justify-between px-6 py-4 rounded-2xl font-black text-xs uppercase tracking-widest transition-all group ${
                     isActive 
                        ? 'bg-brand-teal text-white shadow-xl shadow-brand-teal/20' 
                        : 'text-white/40 hover:text-white hover:bg-white/5'
                  }`
               }
            >
               {({ isActive }) => (
                  <>
                     <div className="flex items-center gap-4">
                        <item.icon size={18} strokeWidth={isActive ? 3 : 2} />
                        <span>{item.label}</span>
                     </div>
                     <ChevronRight size={14} className={`transition-opacity ${isActive ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'}`} />
                  </>
               )}
            </NavLink>
         ))}
      </nav>

      <div className="relative z-10 mt-auto space-y-6">
         {/* User Quick Info */}
         <div className="p-6 bg-white/5 border border-white/10 rounded-3xl flex items-center gap-4">
            <div className="w-10 h-10 rounded-2xl bg-brand-teal flex items-center justify-center text-white shadow-lg">
               <User size={18} />
            </div>
            <div>
               <p className="text-white font-black text-xs tracking-tight">Sarah Khalil</p>
               <p className="text-[10px] font-bold text-brand-teal uppercase opacity-60 tracking-widest">{role} Unit</p>
            </div>
         </div>

         <div className="flex items-center gap-2">
            <button 
              onClick={() => navigate('/')}
              className="flex-1 flex items-center justify-center gap-3 py-4 bg-white/5 hover:bg-rose-500/10 border border-white/10 hover:border-rose-500/20 text-white/40 hover:text-rose-500 rounded-2xl font-black text-[10px] uppercase tracking-widest transition-all"
            >
               <LogOut size={16} /> Sign Out
            </button>
            <button className="p-4 bg-white/5 border border-white/10 text-white/40 hover:text-white rounded-2xl transition-all">
               <Settings size={18} />
            </button>
         </div>
      </div>
    </div>
  );
}
