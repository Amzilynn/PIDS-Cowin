import { useState } from 'react';
import { Search, Database, Globe, Pill, TrendingUp, AlertTriangle, Send, Loader2, Sparkles } from 'lucide-react';
import { Card } from '../components/Card';
import { motion, AnimatePresence } from 'framer-motion';
import { useAvalifeController } from '../../controllers/useAvalifeController';

const clinicalData = [
  { label: 'EMPA-HEART', detail: '35% reduction in HF hospitalizations. Avalife Core data: 36.2%.', color: 'text-[#0A5C5C]', icon: Database },
  { label: 'ESC 2024 Guidelines', detail: 'SGLT2i recommended as first-line for CV-risk patients with T2D.', color: 'text-[#E6B800]', icon: Globe },
  { label: 'FDA Drug Interactions', detail: 'No major interactions with ACE inhibitors or beta-blockers in registry data.', color: 'text-indigo-500', icon: Pill },
  { label: 'Safety Alert', detail: 'DKA risk elevated with strict very-low calorie diets. Educate patients.', color: 'text-rose-500', icon: AlertTriangle },
];

export function MedicalAIView({ products, onQueryChange }) {
  const { state, actions } = useAvalifeController();
  const { chatMessages, chatInput, chatLoading } = state;
  const [query, setQuery] = useState('');
  
  const filtered = clinicalData.filter(d => !query || d.label.toLowerCase().includes(query.toLowerCase()) || d.detail.toLowerCase().includes(query.toLowerCase()));

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <Card>
        <div className="flex items-center gap-3 mb-6">
          <Sparkles className="text-[#E6B800]" size={22} />
          <h3 className="font-black text-lg text-slate-800">Ava Business — Clinical Insight AI</h3>
        </div>
        
        {/* AI Chat History */}
        <div className="h-48 overflow-y-auto mb-4 space-y-3 p-4 bg-slate-50 rounded-2xl border border-slate-100">
          <AnimatePresence>
            {chatMessages.map((msg, i) => (
              <motion.div key={i} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }}
                className={`text-sm font-medium p-3 rounded-xl ${msg.role === 'delegate' ? 'bg-indigo-50 text-indigo-700 ml-8' : 'bg-white text-slate-700 mr-8 shadow-sm border border-slate-100'}`}>
                <span className="font-black uppercase text-[10px] block mb-1 opacity-50">{msg.role === 'delegate' ? 'You' : 'Ava Business'}</span>
                {msg.message}
              </motion.div>
            ))}
          </AnimatePresence>
          {chatLoading && <div className="flex items-center gap-2 text-slate-400 text-xs mt-2 italic"><Loader2 size={12} className="animate-spin" /> Ava is analyzing clinical data...</div>}
        </div>

        {/* AI Input */}
        <div className="flex gap-2">
          <div className="relative flex-1">
             <Search className="absolute left-6 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
             <input
               type="text"
               placeholder="Ask Ava about clinical trials, DKA risks, or market trends..."
               className="w-full pl-14 pr-4 py-4 bg-slate-100/50 rounded-2xl border-none focus:ring-2 focus:ring-[#0A5C5C] outline-none font-bold text-sm"
               value={chatInput}
               onChange={(e) => actions.setChatInput(e.target.value)}
               onKeyDown={(e) => e.key === 'Enter' && actions.handleSendChat(chatInput)}
             />
          </div>
          <button onClick={() => actions.handleSendChat(chatInput)} disabled={!chatInput.trim() || chatLoading}
            className="px-6 bg-[#0A5C5C] text-white rounded-2xl font-black text-sm flex items-center gap-2 hover:bg-[#084A4A] transition-all disabled:opacity-50 shadow-lg shadow-teal-900/20">
            <Send size={16} />
          </button>
        </div>
      </Card>

      {/* Clinical Knowledge Cards */}
      <div className="grid grid-cols-2 gap-5">
        {filtered.map((item, i) => (
          <motion.div key={i} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}>
            <Card>
              <div className={`flex items-center gap-3 mb-4 ${item.color}`}>
                <item.icon size={20} />
                <h4 className="font-black uppercase text-xs tracking-widest">{item.label}</h4>
              </div>
              <p className="text-sm font-medium text-slate-500 leading-relaxed italic">{item.detail}</p>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Product Portfolio */}
      <Card>
        <div className="flex items-center gap-3 mb-6">
          <TrendingUp className="text-[#0A5C5C]" size={22} />
          <h3 className="font-black text-lg">Product Portfolio — Market Intelligence</h3>
        </div>
        <div className="grid grid-cols-3 gap-4">
          {(products || []).length > 0 ? (products || []).map((p, i) => (
            <div key={i} className="p-5 bg-slate-50 rounded-2xl border border-slate-100">
              <p className="font-black text-slate-900 text-base mb-1">{p.product_name}</p>
              <p className="text-xs text-slate-500 font-medium mb-4">{p.category}</p>
              <div className="space-y-2">
                <div className="flex justify-between text-xs font-bold uppercase text-slate-600">
                  <span>Market Share</span><span className="text-[#0A5C5C]">{p.market_share_pct}%</span>
                </div>
                <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                  <motion.div initial={{ width: 0 }} animate={{ width: `${p.market_share_pct}%` }} className="h-full bg-[#0A5C5C]" />
                </div>
                <div className="flex justify-between text-xs font-bold mt-3">
                  <span className="text-slate-500">Rx/Month</span>
                  <span className="text-slate-900">{p.prescriptions_this_month?.toLocaleString()}</span>
                </div>
                <div className="flex justify-between text-xs font-bold">
                  <span className="text-slate-500">Growth</span>
                  <span className="text-emerald-600">↑ {p.growth_pct}%</span>
                </div>
              </div>
            </div>
          )) : <p className="col-span-3 text-slate-400 font-medium text-sm">Loading product data from MySQL...</p>}
        </div>
      </Card>
    </div>
  );
}
