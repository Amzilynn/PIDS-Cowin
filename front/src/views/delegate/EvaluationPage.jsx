import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useAuth } from '../../context/AuthContext';
import { TrendingUp, Star, Clock, Target, Award } from 'lucide-react';

const SERVER_URL = 'http://localhost:5000';

export default function EvaluationPage() {
  const { user } = useAuth();
  const [sessions, setSessions] = useState([]);
  const [kpis, setKpis] = useState([]);

  useEffect(() => {
    fetch(`${SERVER_URL}/api/simulate/history`)
      .then(r => r.json())
      .then(d => setSessions(Array.isArray(d) ? d : []));
    fetch(`${SERVER_URL}/api/kpis`)
      .then(r => r.json())
      .then(d => setKpis(Array.isArray(d) ? d : []));
  }, []);

  const doctorMsgs = sessions.filter(s => s.role === 'doctor');
  const delegateMsgs = sessions.filter(s => s.role === 'delegate');
  const completionScore = Math.min(delegateMsgs.length * 18, 100);

  const metrics = [
    { label: 'Eye Contact & Confidence', value: completionScore ? Math.min(completionScore + 5, 100) : 0, color: '#0A5C5C' },
    { label: 'Knowledge Accuracy', value: completionScore, color: '#E6B800' },
    { label: 'Objection Handling', value: completionScore ? Math.min(completionScore - 8, 100) : 0, color: '#6366f1' },
    { label: 'Clinical Clarity', value: completionScore ? Math.min(completionScore + 2, 100) : 0, color: '#10b981' },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-3xl font-black tracking-tighter text-slate-800">My Evaluation Report</h2>
        <p className="text-slate-500 font-medium mt-1">Performance overview for <span className="font-black text-indigo-600">{user?.name}</span></p>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-4 gap-5">
        {[
          { label: 'Sessions Done', value: delegateMsgs.length, icon: Clock, color: 'indigo' },
          { label: 'Overall Score', value: `${completionScore}%`, icon: Star, color: 'amber' },
          { label: 'Questions Answered', value: delegateMsgs.length, icon: Target, color: 'teal' },
          { label: 'Certification', value: completionScore >= 80 ? 'Passed' : 'In Progress', icon: Award, color: completionScore >= 80 ? 'emerald' : 'rose' },
        ].map((card, i) => (
          <motion.div key={i} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.08 }}
            className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm">
            <div className={`w-10 h-10 rounded-xl bg-${card.color}-100 flex items-center justify-center text-${card.color}-600 mb-4`}>
              <card.icon size={20} />
            </div>
            <p className="text-2xl font-black text-slate-900">{card.value}</p>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mt-1">{card.label}</p>
          </motion.div>
        ))}
      </div>

      {/* Skill bars */}
      <div className="bg-white border border-slate-200 rounded-3xl p-8 shadow-sm">
        <div className="flex items-center gap-3 mb-8">
          <TrendingUp className="text-indigo-600" size={22} />
          <h3 className="text-lg font-black">Competency Breakdown</h3>
        </div>
        <div className="space-y-6">
          {metrics.map((m, i) => (
            <div key={i}>
              <div className="flex justify-between mb-2.5">
                <span className="text-sm font-bold text-slate-700">{m.label}</span>
                <span className="text-sm font-black" style={{ color: m.color }}>{m.value}%</span>
              </div>
              <div className="h-3 bg-slate-100 rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${m.value}%` }}
                  transition={{ duration: 1.2, ease: 'easeOut', delay: i * 0.15 }}
                  className="h-full rounded-full"
                  style={{ background: m.color }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Session history */}
      <div className="bg-white border border-slate-200 rounded-3xl p-8 shadow-sm">
        <h3 className="text-lg font-black mb-6">Recent Training History</h3>
        <div className="space-y-3">
          {delegateMsgs.length > 0 ? delegateMsgs.slice(-5).reverse().map((msg, i) => (
            <div key={i} className="flex items-start gap-4 p-4 bg-slate-50 rounded-2xl border border-slate-100">
              <div className="w-8 h-8 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center text-xs font-black flex-shrink-0 mt-0.5">
                {user?.name?.[0]}
              </div>
              <p className="text-sm text-slate-600 font-medium leading-relaxed">{msg.message}</p>
            </div>
          )) : (
            <p className="text-slate-400 font-medium text-sm">No training sessions yet. Head to AI Training to begin.</p>
          )}
        </div>
      </div>
    </div>
  );
}
