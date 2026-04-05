import React from 'react';
import { 
  Award, 
  Target, 
  TrendingUp, 
  CheckCircle2, 
  AlertCircle, 
  ChevronRight,
  TrendingDown,
  Star,
  Activity,
  Download
} from 'lucide-react';
import { motion } from 'framer-motion';
import { 
  Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer 
} from 'recharts';

const radarData = [
  { subject: 'Clinical Knowledge', A: 92, fullMark: 100 },
  { subject: 'Pitch Confidence', A: 78, fullMark: 100 },
  { subject: 'Eye Contact', A: 85, fullMark: 100 },
  { subject: 'Objection Handling', A: 64, fullMark: 100 },
  { subject: 'Empathy', A: 88, fullMark: 100 },
  { subject: 'Compliance', A: 96, fullMark: 100 },
];

export default function EvaluationResults() {
  const overallScore = 84;
  const dsoRating = "DSO-A+";

  return (
    <div className="space-y-8 animate-fade-in-up">
      {/* Header with DSO Badge */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 p-10 bg-brand-navy rounded-[48px] border border-white/10 shadow-2xl relative overflow-hidden">
        {/* Background glow */}
        <div className="absolute top-0 right-0 w-[400px] h-[400px] bg-brand-teal/10 blur-[80px] rounded-full translate-x-1/3 -translate-y-1/3" />
        
        <div className="relative z-10">
           <div className="flex items-center gap-3 mb-2">
              <span className="text-[10px] font-black text-brand-teal uppercase tracking-[0.3em]">Session Identity: #SIM-2026-X42</span>
           </div>
           <h1 className="text-4xl font-black text-white tracking-tighter mb-2">Mission <span className="text-brand-teal">Evaluation</span> Complete.</h1>
           <p className="text-white/50 font-semibold text-lg">Your performance has been audited by Ava Intelligence v4.1</p>
        </div>

        <motion.div 
           initial={{ scale: 0.8, opacity: 0 }}
           animate={{ scale: 1, opacity: 1 }}
           className="relative z-10 flex flex-col items-center p-8 bg-white rounded-3xl shadow-xl shadow-brand-navy/20"
        >
           <div className="w-20 h-20 rounded-full bg-brand-teal/10 flex items-center justify-center text-brand-teal mb-4 relative">
              <Star size={40} className="fill-current animate-pulse" />
              <div className="absolute -top-1 -right-1 w-6 h-6 bg-emerald-500 rounded-full border-4 border-white" />
           </div>
           <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1 text-center font-sans leading-none">Global Certified Rating</p>
           <h2 className="text-2xl font-black text-brand-navy tracking-tight uppercase leading-none">{dsoRating}</h2>
        </motion.div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Radar Analysis Chart */}
        <div className="p-10 bg-white rounded-[40px] border border-slate-200 shadow-sm flex flex-col">
           <div className="flex items-center justify-between mb-8">
              <div>
                 <h3 className="text-xl font-extrabold text-brand-navy tracking-tight">Competency Architecture</h3>
                 <p className="text-[10px] font-black text-brand-teal uppercase tracking-widest">Normalized Audit Metrics</p>
              </div>
              <div className="w-12 h-12 rounded-2xl bg-slate-50 flex items-center justify-center text-brand-teal">
                 <Activity size={20} />
              </div>
           </div>
           
           <div className="flex-1 min-h-[360px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                 <RadarChart cx="50%" cy="50%" outerRadius="80%" data={radarData}>
                   <PolarGrid stroke="#e2e8f0" />
                   <PolarAngleAxis dataKey="subject" tick={{ fontSize: 10, fontWeight: 800, fill: '#64748b' }} />
                   <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                   <Radar 
                      name="SARAH" 
                      dataKey="A" 
                      stroke="#4E8C8A" 
                      fill="#4E8C8A" 
                      fillOpacity={0.2} 
                      strokeWidth={3}
                   />
                 </RadarChart>
              </ResponsiveContainer>
           </div>
           
           <div className="mt-6 flex items-center justify-center gap-8">
              <div className="flex items-center gap-2">
                 <div className="w-3 h-3 rounded-full bg-brand-teal/20 border-2 border-brand-teal" />
                 <span className="text-xs font-bold text-slate-500">Current Session</span>
              </div>
              <div className="flex items-center gap-2">
                 <div className="w-3 h-3 rounded-full bg-slate-100 border-2 border-slate-200" />
                 <span className="text-xs font-bold text-slate-400">Regional Average</span>
              </div>
           </div>
        </div>

        {/* Detailed Breakdown & Tips */}
        <div className="space-y-6 flex flex-col h-full">
           <div className="grid grid-cols-2 gap-6">
              {[
                 { label: 'Overall Progress', value: '84%', icon: TrendingUp, color: 'emerald' },
                 { label: 'Global Ranking', value: 'TOP 12%', icon: Award, color: 'brand-teal' }
              ].map((card, i) => (
                 <div key={i} className="p-6 bg-white rounded-4xl border border-slate-200 shadow-sm flex flex-col gap-4">
                    <div className={`w-10 h-10 rounded-2xl bg-brand-teal/5 flex items-center justify-center text-brand-teal`}>
                       <card.icon size={20} />
                    </div>
                    <div>
                       <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest leading-none mb-1">{card.label}</p>
                       <h4 className="text-2xl font-black text-brand-navy tracking-tight leading-none">{card.value}</h4>
                    </div>
                 </div>
              ))}
           </div>

           <div className="flex-1 p-10 bg-white rounded-[40px] border border-slate-200 shadow-sm overflow-hidden relative">
              <h3 className="text-xl font-extrabold text-brand-navy tracking-tight mb-8">Intelligence <span className="text-brand-teal">Insights</span> & Tips</h3>
              
              <div className="space-y-8">
                 {[
                    { type: 'SUCCESS', icon: CheckCircle2, color: 'text-emerald-500', msg: "Clinical depth on SGLT2i kidney data is consistent and accurate. You demonstrated high professionalism during objections." },
                    { type: 'IMPROVEMENT', icon: TrendingDown, color: 'text-brand-teal', msg: "Pitch confidence dropped by 14% when discussing ROI for the patient loyalty program. Suggest reviewing the Commercial Assets module." },
                    { type: 'ACTION', icon: AlertCircle, color: 'text-brand-navy', msg: "Schedule a BO1 simulation for 'Specialist Objections' to bridge the current handling gap." }
                 ].map((tip, i) => (
                    <motion.div 
                       key={i}
                       initial={{ x: 20, opacity: 0 }}
                       animate={{ x: 0, opacity: 1 }}
                       transition={{ delay: i * 0.1 }}
                       className="flex items-start gap-4"
                    >
                       <tip.icon size={20} className={`${tip.color} mt-1`} />
                       <div>
                          <p className={`text-[10px] font-black uppercase tracking-widest ${tip.color} mb-1`}>{tip.type}</p>
                          <p className="text-sm font-semibold text-slate-600 leading-relaxed">{tip.msg}</p>
                       </div>
                    </motion.div>
                 ))}
              </div>

              <div className="mt-12 flex flex-col gap-3">
                 <button className="w-full py-4 bg-brand-navy text-white rounded-2xl font-black text-xs uppercase tracking-[0.2em] shadow-xl shadow-brand-navy/20 active:scale-[0.98] transition-all flex items-center justify-center gap-3">
                    Download Official Cert <Download size={14} />
                 </button>
                 <button className="w-full py-4 border-2 border-slate-100 text-slate-400 rounded-2xl font-black text-xs uppercase tracking-[0.2em] hover:border-brand-teal hover:text-brand-teal transition-all flex items-center justify-center gap-3">
                    Review Simulation History <ChevronRight size={14} />
                 </button>
              </div>
              
              {/* Subtle background pulse animation in the corner */}
              <div className="absolute top-0 right-0 p-8 opacity-5">
                 <Target size={120} />
              </div>
           </div>
        </div>
      </div>

      <style jsx>{`
        @keyframes fade-in-up {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-fade-in-up {
          animation: fade-in-up 0.8s ease-out forwards;
        }
      `}</style>
    </div>
  );
}
