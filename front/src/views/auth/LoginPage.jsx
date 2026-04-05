import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { 
  ShieldCheck, 
  User, 
  Stethoscope, 
  ChevronRight, 
  Eye, 
  EyeOff, 
  ArrowRight,
  Lock,
  Globe
} from 'lucide-react';
import Logo from '../../components/Logo';

const roles = [
  {
    id: 'admin',
    label: 'Healthcare Admin',
    desc: 'System analytics & oversight',
    icon: ShieldCheck,
    color: 'from-brand-navy to-brand-slate',
    activeColor: 'ring-brand-navy',
    cred: 'admin@avalive.com'
  },
  {
    id: 'delegate',
    label: 'Medical Delegate',
    desc: 'Training & field intelligence',
    icon: User,
    color: 'from-brand-teal to-brand-aqua',
    activeColor: 'ring-brand-teal',
    cred: 'sarah@avalive.com'
  },
  {
    id: 'doctor',
    label: 'Health Professional',
    desc: 'Presentation receiver mode',
    icon: Stethoscope,
    color: 'from-blue-600 to-indigo-700',
    activeColor: 'ring-blue-600',
    cred: 'dr_khalil@avalive.com'
  }
];

export default function LoginPage() {
  const navigate = useNavigate();
  const [selectedRole, setSelectedRole] = useState(roles[1]); // Default to Delegate
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleLogin = (e) => {
    e.preventDefault();
    setLoading(true);
    
    // REDIRECT LOGIC: Wait 1s and navigate to the selected role path
    setTimeout(() => {
      setLoading(false);
      navigate(`/${selectedRole.id}`);
    }, 1500);
  };

  return (
    <div className="min-h-screen bg-brand-navy flex flex-col md:flex-row overflow-hidden font-sans">
      {/* Left Decoration / Info */}
      <div className="hidden md:flex md:w-1/2 relative flex-col justify-between p-16 overflow-hidden">
        {/* Background Gradients */}
        <div className="absolute top-0 right-0 w-[800px] h-[800px] bg-brand-teal/20 blur-[120px] rounded-full translate-x-1/2 -translate-y-1/2" />
        <div className="absolute bottom-0 left-0 w-[600px] h-[600px] bg-blue-600/10 blur-[100px] rounded-full -translate-x-1/2 translate-y-1/2" />
        
        <div className="relative z-10 animate-fade-in-up">
           <Logo className="w-12 h-12 mb-20" />
           
           <h1 className="text-6xl font-black text-white leading-[1.1] tracking-tighter mb-8 max-w-lg">
             The Intelligence <span className="text-brand-teal">Engine</span> for Pharma Excellence.
           </h1>
           
           <p className="text-lg text-white/40 font-medium max-w-md leading-relaxed mb-12">
             Empower your medical delegates with Computer Vision-driven simulations and Smart Visit Optimization.
           </p>
           
           <div className="flex items-center gap-12">
              <div className="flex flex-col gap-1 border-l-2 border-brand-teal pl-6">
                 <span className="text-3xl font-black text-white">98%</span>
                 <span className="text-[10px] font-bold text-white/40 uppercase tracking-widest">Accuracy Rate</span>
              </div>
              <div className="flex flex-col gap-1 border-l-2 border-brand-teal pl-6">
                 <span className="text-3xl font-black text-white">2.4k+</span>
                 <span className="text-[10px] font-bold text-white/40 uppercase tracking-widest">Delegates Trained</span>
              </div>
           </div>
        </div>

        <div className="relative z-10 flex items-center gap-6 text-white/30 text-[10px] font-black uppercase tracking-[0.2em]">
           <span className="flex items-center gap-2"><Globe size={14} /> Global Compliance v4.2</span>
           <span>Privacy & Security Ready</span>
        </div>
      </div>

      {/* Right Login Form */}
      <div className="w-full md:w-1/2 bg-white flex flex-col items-center justify-center p-8 md:p-24 relative">
        <div className="w-full max-w-md">
          <motion.div 
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="mb-12"
          >
            <h2 className="text-4xl font-extrabold text-brand-navy tracking-tight mb-2">Welcome Back.</h2>
            <p className="text-slate-500 font-semibold">Select your professional role to continue</p>
          </motion.div>

          {/* Role Choice Cards */}
          <div className="grid grid-cols-3 gap-3 mb-10">
            {roles.map((role) => (
              <button
                key={role.id}
                onClick={() => setSelectedRole(role)}
                className={`flex flex-col items-center p-4 rounded-3xl border-2 transition-all group ${
                  selectedRole.id === role.id 
                    ? `bg-white ${role.activeColor} border-current ring-4 ring-current/10 border-brand-teal` 
                    : 'bg-slate-50 border-transparent hover:bg-white hover:border-slate-200 shadow-transparent'
                }`}
              >
                <div className={`w-12 h-12 rounded-2xl bg-gradient-to-br ${role.color} flex items-center justify-center text-white mb-3 shadow-lg group-hover:scale-110 transition-transform`}>
                  <role.icon size={22} />
                </div>
                <p className={`text-[10px] font-black uppercase tracking-widest ${selectedRole.id === role.id ? 'text-brand-navy' : 'text-slate-400'}`}>
                  {role.id}
                </p>
              </button>
            ))}
          </div>

          {/* Credential Fields */}
          <form onSubmit={handleLogin} className="space-y-5 animate-fade-in-up">
            <div className="relative group">
              <div className="absolute left-5 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-brand-teal transition-colors">
                <Globe size={18} />
              </div>
              <input 
                type="text" 
                placeholder="Professional Workspace / ID" 
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-slate-100 border-2 border-transparent focus:border-brand-teal focus:bg-white rounded-2xl pl-14 pr-6 py-4.5 text-sm font-bold text-brand-navy outline-none transition-all placeholder:text-slate-400"
                required
              />
            </div>

            <div className="relative group">
              <div className="absolute left-5 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-brand-teal transition-colors">
                <Lock size={18} />
              </div>
              <input 
                type={showPassword ? "text" : "password"} 
                placeholder="Secure Access Key" 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-slate-100 border-2 border-transparent focus:border-brand-teal focus:bg-white rounded-2xl pl-14 pr-14 py-4.5 text-sm font-bold text-brand-navy outline-none transition-all placeholder:text-slate-400"
                required
              />
              <button 
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-brand-navy transition-colors"
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>

            <div className="flex items-center justify-between px-1">
               <div className="text-[10px] font-bold text-brand-teal uppercase tracking-widest bg-brand-teal/5 px-3 py-1 rounded-full">
                  Hint: {selectedRole.cred}
               </div>
               <button type="button" className="text-xs font-bold text-brand-teal hover:underline tracking-tight">Recover Key</button>
            </div>

            <button 
              type="submit"
              disabled={loading}
              className="w-full py-5 bg-brand-navy text-white rounded-2xl font-black text-xs uppercase tracking-[0.25em] shadow-2xl shadow-brand-navy/30 hover:scale-[1.02] active:scale-[0.98] transition-all flex items-center justify-center gap-3 decoration-white disabled:grayscale disabled:opacity-50 mt-4"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-white/20 border-t-white rounded-full animate-spin" />
              ) : (
                <>Enter Professional Secure Workspace <ArrowRight size={16} /></>
              )}
            </button>
          </form>

          <p className="mt-12 text-center text-xs font-bold text-slate-400 uppercase tracking-widest">
            Licensed to <span className="text-brand-navy">Global Pharma Group LP</span>
          </p>
        </div>
      </div>

      <style jsx>{`
        .animate-fade-in-up {
          animation: fade-up 0.8s ease-out forwards;
        }
        @keyframes fade-up {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}
