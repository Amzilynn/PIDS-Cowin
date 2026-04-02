import { useNavigate } from 'react-router-dom';
import { Box, Code, Sliders } from 'lucide-react';

export default function DSO3Page() {
  const navigate = useNavigate();
  return (
    <div className="min-h-screen bg-[#F8FAFC] flex flex-col items-center justify-center p-10 font-sans">
      <div className="w-full max-w-4xl bg-white rounded-[40px] border border-slate-200 shadow-2xl overflow-hidden shadow-slate-200">
        <div className="p-16 text-center">
          <div className="w-24 h-24 bg-slate-50 border border-slate-100 rounded-[30px] flex items-center justify-center text-slate-300 mx-auto mb-10 shadow-sm">
            <Box size={48} />
          </div>
          <h1 className="text-4xl font-black text-slate-900 mb-6 tracking-tighter">DSO3 <span className="text-slate-400">INTERFACE</span></h1>
          <p className="text-xl text-slate-500 font-medium leading-relaxed max-w-lg mx-auto mb-12 italic">Target system architecture pending initialization. This interface is reserved for future AvalifeAI expansion modules.</p>
          
          <div className="grid grid-cols-2 gap-6 max-w-xl mx-auto mb-12">
            <div className="bg-slate-50 border border-slate-100 p-8 rounded-3xl text-left hover:border-slate-300 transition-colors cursor-pointer group">
               <Code className="text-slate-400 group-hover:text-slate-800 mb-4 transition-colors" size={24} />
               <p className="font-black text-slate-900 text-sm">DEVELOPMENT</p>
               <p className="text-[10px] font-black text-slate-400 uppercase mt-1">Status: Pending</p>
            </div>
            <div className="bg-slate-50 border border-slate-100 p-8 rounded-3xl text-left hover:border-slate-300 transition-colors cursor-pointer group">
               <Sliders className="text-slate-400 group-hover:text-slate-800 mb-4 transition-colors" size={24} />
               <p className="font-black text-slate-900 text-sm">CONFIGURATION</p>
               <p className="text-[10px] font-black text-slate-400 uppercase mt-1">Access: Restricted</p>
            </div>
          </div>

          <button onClick={() => navigate('/')} className="px-10 py-4 bg-slate-900 text-white font-black text-sm uppercase tracking-widest rounded-2xl hover:bg-slate-800 transition-all shadow-xl shadow-slate-900/30">
            Return to Command Center
          </button>
        </div>
        <div className="bg-slate-50 p-6 text-center border-t border-slate-100">
          <p className="text-[10px] font-black text-slate-300 uppercase tracking-[0.3em]">Avalife Protocol 1.0 — Node Locked</p>
        </div>
      </div>
    </div>
  );
}
