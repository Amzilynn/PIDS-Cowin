import { useNavigate } from 'react-router-dom';
import { Layers, Database, Lock } from 'lucide-react';

export default function DSO4Page() {
  const navigate = useNavigate();
  return (
    <div className="min-h-screen bg-[#0F172A] flex flex-col items-center justify-center p-10 font-sans overflow-hidden">
      {/* Background glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-slate-800/20 rounded-full blur-[120px] pointer-events-none" />

      <div className="w-full max-w-4xl bg-slate-900/50 rounded-[40px] border border-slate-800 backdrop-blur-xl shadow-2xl relative z-10">
        <div className="p-16 text-center">
          <div className="w-24 h-24 bg-slate-800 rounded-[30px] flex items-center justify-center text-slate-500 mx-auto mb-10 border border-slate-700">
            <Layers size={48} />
          </div>
          <h1 className="text-4xl font-black text-white mb-6 tracking-tighter">DSO4 <span className="text-slate-700 uppercase">Registry</span></h1>
          <p className="text-xl text-slate-400 font-medium leading-relaxed max-w-lg mx-auto mb-12">The medical delegate data sync registry is undergoing maintenance. Real-time logging is disabled for DSO4 node.</p>
          
          <div className="grid grid-cols-2 gap-6 max-w-xl mx-auto mb-12">
            <div className="bg-slate-800/40 border border-slate-700/50 p-8 rounded-3xl text-left hover:bg-slate-800 transition-all border-dashed">
               <Database className="text-slate-600 mb-4" size={24} />
               <p className="font-black text-slate-400 text-sm">ENCRYPTED DATA</p>
               <p className="text-[10px] font-black text-slate-600 uppercase mt-1 tracking-widest">Awaiting Key...</p>
            </div>
            <div className="bg-slate-800/40 border border-slate-700/50 p-8 rounded-3xl text-left hover:bg-slate-800 transition-all border-dashed">
               <Lock className="text-slate-600 mb-4" size={24} />
               <p className="font-black text-slate-400 text-sm">SECURE TUNNEL</p>
               <p className="text-[10px] font-black text-slate-600 uppercase mt-1 tracking-widest">Connection: Closed</p>
            </div>
          </div>

          <button onClick={() => navigate('/')} className="px-10 py-4 bg-white text-slate-900 font-black text-sm uppercase tracking-widest rounded-2xl hover:bg-slate-100 transition-all shadow-xl shadow-white/10">
            System Exit
          </button>
        </div>
        <div className="bg-slate-950 p-6 text-center border-t border-slate-800 rounded-b-[40px]">
          <p className="text-[10px] font-black text-slate-700 uppercase tracking-[0.5em]">Avalife Bio-Medical Node 004 — Maintenance Mode</p>
        </div>
      </div>
    </div>
  );
}
