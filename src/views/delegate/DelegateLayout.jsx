import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { BarChart3, Brain, MessageCircle, LogOut } from 'lucide-react';
import { motion } from 'framer-motion';

const navItems = [
  { to: 'evaluation', label: 'My Evaluation', icon: BarChart3 },
  { to: 'training', label: 'Ava Train', icon: Brain },
  { to: 'assistant', label: 'Ava Assistant', icon: MessageCircle },
];

export default function DelegateLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => { logout(); navigate('/'); };

  return (
    <div className="flex h-screen bg-[#F8FAFC] font-sans overflow-hidden">
      {/* Sidebar */}
      <nav className="w-72 bg-white border-r border-slate-200 p-6 flex flex-col z-50">
        <div className="flex items-center gap-3 mb-10 px-2">
          <div className="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center text-white font-black text-xl">
            {user?.name?.[0] || 'D'}
          </div>
          <div>
            <p className="font-black text-slate-900 text-sm">{user?.name}</p>
            <p className="text-[10px] font-bold text-indigo-500 uppercase tracking-widest">Medical Delegate</p>
          </div>
        </div>

        <div className="space-y-2">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `w-full flex items-center gap-4 px-4 py-3.5 rounded-xl font-bold text-sm transition-all duration-300 ${
                  isActive
                    ? 'bg-indigo-600 text-white shadow-xl shadow-indigo-900/20'
                    : 'text-slate-500 hover:bg-slate-50 hover:text-indigo-600'
                }`
              }
            >
              <item.icon size={20} />
              {item.label}
            </NavLink>
          ))}
        </div>

        <div className="mt-auto">
          <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100 mb-4">
            <p className="text-[10px] font-bold text-slate-400 uppercase mb-2">Session</p>
            <div className="flex items-center gap-2 text-xs font-bold text-emerald-600">
              <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
              Active — {new Date().toLocaleDateString('en-GB', { month: 'short', day: 'numeric' })}
            </div>
          </div>
          <button onClick={handleLogout} className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-slate-500 hover:bg-rose-50 hover:text-rose-600 font-bold text-sm transition-all">
            <LogOut size={18} /> Sign Out
          </button>
        </div>
      </nav>

      {/* Content */}
      <main className="flex-1 overflow-y-auto p-10">
        <Outlet />
      </main>
    </div>
  );
}
