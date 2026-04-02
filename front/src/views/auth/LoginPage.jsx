import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Shield, User, Stethoscope, Eye, EyeOff, ChevronRight, Loader2 } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useNavigate } from 'react-router-dom';

const roles = [
  {
    id: 'admin',
    label: 'Administrator',
    sublabel: 'Full system access',
    icon: Shield,
    gradient: 'from-[#0A5C5C] to-teal-800',
    glow: 'shadow-teal-900/40',
    fields: ['password'],
  },
  {
    id: 'delegate',
    label: 'Medical Delegate',
    sublabel: 'Your personal workspace',
    icon: User,
    gradient: 'from-indigo-600 to-indigo-900',
    glow: 'shadow-indigo-900/40',
    fields: ['username', 'password'],
  },
  {
    id: 'doctor',
    label: 'Doctor / Pharmacist',
    sublabel: 'Guest session — no login needed',
    icon: Stethoscope,
    gradient: 'from-rose-600 to-rose-900',
    glow: 'shadow-rose-900/40',
    fields: ['name'],
  },
];

export default function LoginPage() {
  const { loginAdmin, loginDelegate, loginDoctor } = useAuth();
  const navigate = useNavigate();

  const [activeRole, setActiveRole] = useState(null);
  const [form, setForm] = useState({ username: '', password: '', name: '' });
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSelect = (roleId) => {
    setActiveRole(roleId);
    setError('');
    setForm({ username: '', password: '', name: '' });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    await new Promise(r => setTimeout(r, 600));

    let ok = false;
    if (activeRole === 'admin') ok = loginAdmin(form.password);
    else if (activeRole === 'delegate') ok = loginDelegate(form.username, form.password);
    else if (activeRole === 'doctor') { loginDoctor(form.name); ok = true; }

    if (ok) {
      navigate(activeRole === 'admin' ? '/admin' : activeRole === 'delegate' ? '/delegate' : '/doctor');
    } else {
      setError('Invalid credentials. Please try again.');
    }
    setLoading(false);
  };

  const selectedRole = roles.find(r => r.id === activeRole);

  return (
    <div className="min-h-screen bg-[#0F172A] flex flex-col items-center justify-center p-8 relative overflow-hidden">
      {/* Background glow */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[400px] bg-teal-900/20 rounded-full blur-3xl pointer-events-none" />

      {/* Logo */}
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="mb-14 text-center">
        <div className="flex items-center justify-center gap-3 mb-4">
          <div className="w-14 h-14 bg-[#0A5C5C] rounded-2xl flex items-center justify-center text-white font-black text-2xl shadow-xl shadow-teal-900/50">A</div>
          <h1 className="text-4xl font-black tracking-tighter text-white uppercase italic">AVA<span className="text-[#E6B800]">LIVE</span></h1>
        </div>
        <p className="text-slate-500 font-medium tracking-wide text-sm mb-6">Intelligence Command Center — Select your role to continue</p>
        
        <motion.button 
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => { loginDoctor('Guest'); navigate('/doctor'); }}
          className="px-8 py-3 bg-white/5 border border-white/10 hover:bg-white/10 hover:border-rose-500/50 rounded-full text-rose-400 font-black text-xs uppercase tracking-[0.2em] transition-all flex items-center gap-3 mx-auto"
        >
          <div className="w-2 h-2 bg-rose-500 rounded-full animate-pulse" />
          Direct Guest Access
        </motion.button>
      </motion.div>

      {/* Role Cards */}
      <div className="grid grid-cols-3 gap-6 w-full max-w-4xl mb-8">
        {roles.map((role, i) => (
          <motion.button
            key={role.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            whileHover={{ y: -6, scale: 1.02 }}
            onClick={() => handleSelect(role.id)}
            className={`bg-gradient-to-br ${role.gradient} p-8 rounded-3xl text-white text-left flex flex-col gap-4 shadow-2xl ${role.glow} transition-all duration-200 border-2 ${activeRole === role.id ? 'border-white/40' : 'border-transparent'}`}
          >
            <role.icon size={32} />
            <div>
              <p className="font-black text-xl">{role.label}</p>
              <p className="text-white/60 text-sm font-medium mt-1">{role.sublabel}</p>
            </div>
            <div className="mt-auto flex items-center gap-2 text-white/70 text-sm font-bold">
              Enter <ChevronRight size={16} />
            </div>
          </motion.button>
        ))}
      </div>

      {/* Login Form */}
      <AnimatePresence mode="wait">
        {activeRole && (
          <motion.div
            key={activeRole}
            initial={{ opacity: 0, y: 16, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.98 }}
            className="w-full max-w-md bg-white/5 border border-white/10 rounded-3xl p-8 backdrop-blur-sm"
          >
            <p className="text-white font-black text-lg mb-6">
              Sign in as <span className={`bg-gradient-to-r ${selectedRole.gradient} bg-clip-text text-transparent`}>{selectedRole.label}</span>
            </p>
            <form onSubmit={handleSubmit} className="space-y-4">
              {selectedRole.fields.includes('username') && (
                <input
                  type="text"
                  placeholder="Username"
                  value={form.username}
                  onChange={e => setForm(f => ({ ...f, username: e.target.value }))}
                  className="w-full bg-white/10 border border-white/10 text-white placeholder:text-slate-600 rounded-xl px-5 py-3.5 text-sm font-medium outline-none focus:border-teal-500 transition-colors"
                  required
                />
              )}
              {selectedRole.fields.includes('password') && (
                <div className="relative">
                  <input
                    type={showPw ? 'text' : 'password'}
                    placeholder="Password"
                    value={form.password}
                    onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
                    className="w-full bg-white/10 border border-white/10 text-white placeholder:text-slate-600 rounded-xl px-5 py-3.5 pr-12 text-sm font-medium outline-none focus:border-teal-500 transition-colors"
                    required
                  />
                  <button type="button" onClick={() => setShowPw(p => !p)} className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-500 hover:text-white">
                    {showPw ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
              )}
              {selectedRole.fields.includes('name') && (
                <input
                  type="text"
                  placeholder="Your name (optional)"
                  value={form.name}
                  onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                  className="w-full bg-white/10 border border-white/10 text-white placeholder:text-slate-600 rounded-xl px-5 py-3.5 text-sm font-medium outline-none focus:border-teal-500 transition-colors"
                />
              )}
              {error && <p className="text-rose-400 text-sm font-bold">{error}</p>}
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                type="submit"
                disabled={loading}
                className={`w-full py-4 bg-gradient-to-r ${selectedRole.gradient} text-white font-black rounded-xl text-sm uppercase tracking-wider shadow-xl disabled:opacity-70 flex items-center justify-center gap-3 transition-all`}
              >
                {loading ? <Loader2 size={18} className="animate-spin" /> : null}
                {activeRole === 'doctor' ? 'Enter as Guest' : 'Sign In'}
              </motion.button>
            </form>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
