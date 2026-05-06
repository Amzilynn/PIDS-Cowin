import Reat, { useState, useEffect } from 'react';
import {
  Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ResponsiveContainer, RadialBarChart, RadialBar, Legend, Tooltip
} from 'recharts';
import {
  Award,
  TrendingUp,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
  Star,
  BrainCircuit,
  MessageSquare,
  Zap,
  Activity,
  UserCheck,
  ShieldCheck,
  Target,
  Download
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';

export default function EvaluationResults() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [resultsData, setResultsData] = useState(null);

  // 📡 Polling the backend status until the report is fully generated
  useEffect(() => {
    let interval = setInterval(async () => {
      try {
        const res = await fetch('http://127.0.0.1:8001/api/training/status');
        const data = await res.json();
        if (data.status === 'stopped' && data.results) {
          clearInterval(interval);
          setResultsData(data); // We store the whole response (status, results, report_pdf)
          setLoading(false);
        }
      } catch (e) {
        console.error('Error fetching status', e);
      }
    }, 1500);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-[calc(100vh-100px)] space-y-8 animate-fade-in">
        <div className="relative">
          <div className="w-20 h-20 border-4 border-md-primary/20 rounded-full"></div>
          <div className="absolute top-0 left-0 w-20 h-20 border-4 border-md-primary border-t-transparent rounded-full animate-spin"></div>
        </div>
        <div className="text-center space-y-4">
          <h2 className="text-2xl font-black text-md-on-background tracking-tighter uppercase">Génération du rapport IA en cours...</h2>
          <p className="text-md-on-surface-variant font-bold opacity-60 max-w-sm mx-auto uppercase tracking-widest text-[10px]">
            Analyse biométrique et fact-checking du discours en cours. Veuillez patienter environ 15 secondes.
          </p>
        </div>
      </div>
    );
  }

  const results = resultsData?.results || {};
  const averages = results?.averages || {};
  const nlp = results?.nlp || {};
  const reportFileName = resultsData?.report_pdf;

  // Helper for 0.0-1.0 to 0-100 conversion
  const parseScore = (val, fallback) => (val !== undefined && val !== null) ? Math.round(val * 100) : fallback;

  const globalScore = parseScore(averages.performance, 0);
  const radialData = [
    { name: 'Score Global', value: globalScore, fill: 'var(--color-md-primary)' }
  ];

  const competenceData = [
    { subject: 'Attention', A: parseScore(averages.engagement, 0), fullMark: 100 },
    { subject: 'Confiance', A: parseScore(averages.confidence, 0), fullMark: 100 },
    { subject: 'Ouverture', A: parseScore(averages.openness, 0), fullMark: 100 },
    { subject: 'Sérénité', A: parseScore(1.0 - (averages.stress || 0), 0), fullMark: 100 },
    { subject: 'Performance', A: globalScore, fullMark: 100 },
  ];

  const pillMetrics = [
    { label: 'Attention', value: parseScore(averages.engagement, 0), icon: MessageSquare, color: 'bg-md-primary' },
    { label: 'Confiance', value: parseScore(averages.confidence, 0), icon: TrendingUp, color: 'bg-indigo-500' },
    { label: 'Posture', value: parseScore(averages.posture, 0), icon: UserCheck, color: 'bg-md-on-background' },
    { label: 'Fluidité', value: parseScore(1.0 - (averages.pause_ratio || 0), 0), icon: AlertCircle, color: 'bg-rose-500' },
  ];

  return (
    <div className="space-y-12 animate-fade-in pb-20 relative z-10">
      {/* Background Decor */}
      <div className="fixed bottom-0 left-0 w-[800px] h-[800px] bg-md-primary/5 blur-[120px] rounded-full -translate-x-1/2 translate-y-1/2 pointer-events-none -z-10" />
      <div className="fixed top-0 right-0 w-[600px] h-[600px] bg-indigo-500/5 blur-[100px] rounded-full translate-x-1/2 -translate-y-1/2 pointer-events-none -z-10" />

      {/* Header Résultat */}
      <div className="flex flex-col md:flex-row items-center justify-between gap-12">
        <div className="space-y-6 text-center md:text-left flex-1">
          <div className="flex items-center justify-center md:justify-start gap-4">
            <div className="w-12 h-12 rounded-2xl bg-md-primary/10 text-md-primary flex items-center justify-center shadow-lg shadow-md-primary/5">
              <Award size={24} />
            </div>
            <span className="text-[11px] font-black text-md-primary uppercase tracking-[0.5em] leading-none">Certification de Session v2.4</span>
          </div>
          <h1 className="text-7xl font-black text-md-on-background tracking-tighter leading-[0.9] uppercase">Analyse de <br /><span className="text-md-primary italic lowercase">performance.</span></h1>
          <p className="text-md-on-surface-variant font-bold text-xl leading-relaxed max-w-xl italic opacity-70 tracking-tight">
            Évaluation haute-fidélité de votre session simulator. Vos scores DSO reflètent une excellente maîtrise du protocole clinique.
          </p>
          <div className="flex flex-wrap items-center justify-center md:justify-start gap-4 pt-4">
            <div className="px-6 py-3 bg-emerald-500/10 border border-emerald-500/20 rounded-full flex items-center gap-3">
              <ShieldCheck size={18} className="text-emerald-500" />
              <span className="text-xs font-black text-emerald-500 uppercase tracking-widest leading-none">Profil Validé DSO1</span>
            </div>
            <div className="px-6 py-3 bg-md-primary/10 border border-md-primary/20 rounded-full flex items-center gap-3">
              <Target size={18} className="text-md-primary" />
              <span className="text-xs font-black text-md-primary uppercase tracking-widest leading-none">+12% vs Moyenne</span>
            </div>
          </div>
        </div>

        {/* Radial Score Gauge */}
        <div className="relative w-80 h-80 flex items-center justify-center group">
          <div className="absolute inset-0 bg-md-primary/5 rounded-full blur-3xl animate-pulse group-hover:bg-md-primary/10 transition-all duration-1000" />
          <ResponsiveContainer width="100%" height="100%">
            <RadialBarChart
              cx="50%" cy="50%"
              innerRadius="75%" outerRadius="100%"
              barSize={18}
              data={radialData}
              startAngle={90} endAngle={-270}
            >
              <RadialBar
                minAngle={15}
                background={{ fill: 'var(--color-md-surface-container-low)' }}
                clockWise={true}
                dataKey="value"
                cornerRadius={20}
                className="drop-shadow-2xl"
              />
            </RadialBarChart>
          </ResponsiveContainer>
          <div className="absolute inset-0 flex flex-col items-center justify-center transform group-hover:scale-110 transition-transform duration-700">
            <motion.span
              initial={{ opacity: 0, scale: 0.5 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ type: 'spring', stiffness: 100, damping: 10 }}
              className="text-7xl font-black text-md-on-background tracking-tighter"
            >
              {globalScore}<span className="text-3xl text-md-primary font-bold">/100</span>
            </motion.span>
            <span className="text-[11px] font-black text-md-primary uppercase tracking-[0.4em] mt-3 opacity-60">Score Évalué</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
        {/* Detailed Metrics */}
        <div className="lg:col-span-12 grid grid-cols-1 md:grid-cols-4 gap-8">
          {pillMetrics.map((metric, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1, duration: 0.6 }}
              className="md-card p-8 flex flex-col gap-8 group hover:translate-y-[-10px] bg-white border-none shadow-xl hover:shadow-2xl transition-all duration-500 relative overflow-hidden"
            >
              <div className="absolute top-0 right-0 w-24 h-24 bg-md-primary/5 rounded-full blur-2xl -translate-y-1/2 translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity" />
              <div className={`w-14 h-14 rounded-[20px] ${metric.color} text-white flex items-center justify-center shadow-lg relative z-10 transition-transform group-hover:rotate-12`}>
                <metric.icon size={26} strokeWidth={2.5} />
              </div>
              <div className="space-y-4 relative z-10">
                <div className="flex items-center justify-between">
                  <p className="text-[10px] font-black uppercase text-md-on-surface-variant tracking-[0.2em] opacity-60 leading-none">{metric.label}</p>
                  <span className="text-base font-black text-md-on-background tracking-tighter">{metric.value}%</span>
                </div>
                <div className="w-full h-2 bg-md-surface-container-low rounded-pill overflow-hidden shadow-inner">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${metric.value}%` }}
                    transition={{ duration: 2, ease: "easeOut", delay: 0.8 }}
                    className={`h-full ${metric.color} rounded-pill shadow-lg opacity-80`}
                  />
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        {/* NLP Analysis & Improvement Axes */}
        <div className="lg:col-span-12 flex flex-col gap-10">
          <div className="md-card p-12 flex flex-col gap-10 bg-md-on-background text-white rounded-[40px] shadow-2xl relative overflow-hidden border border-white/5">
            <div className="absolute top-0 right-0 w-[400px] h-[400px] bg-rose-500/10 blur-[100px] pointer-events-none -z-10" />

            <div className="relative z-10 flex items-center gap-5 mb-4">
              <div className="w-12 h-12 rounded-2xl bg-rose-500 flex items-center justify-center text-white shadow-xl shadow-rose-500/30 animate-pulse">
                <AlertCircle size={28} />
              </div>
              <h3 className="text-2xl font-black text-white tracking-tighter leading-none uppercase italic">Axe de Progrès</h3>
            </div>

            <div className="relative z-10 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {/* Bilan Scientifique */}
              <div className="flex gap-6 group cursor-default bg-white/5 p-6 rounded-3xl border border-white/10 hover:bg-white/10 transition-colors">
                <div className="mt-1 flex-shrink-0 group-hover:scale-125 transition-transform duration-500 text-md-primary">
                  <BrainCircuit size={22} strokeWidth={2.5} />
                </div>
                <div className="space-y-3">
                  <h4 className="text-base font-black text-white uppercase tracking-tight leading-none">Bilan Global</h4>
                  <p className="text-xs font-bold text-white/60 leading-relaxed uppercase tracking-widest leading-relaxed">
                    {nlp.feedback_summary || "Analyse scientifique du discours en cours..."}
                  </p>
                </div>
              </div>

              {/* Points Positifs */}
              {(nlp.correct_points || []).map((point, i) => (
                <div key={`correct-${i}`} className="flex gap-6 group cursor-default bg-emerald-500/5 p-6 rounded-3xl border border-emerald-500/10 hover:bg-emerald-500/10 transition-colors">
                  <div className="mt-1 flex-shrink-0 group-hover:scale-125 transition-transform duration-500 text-emerald-500">
                    <ShieldCheck size={22} strokeWidth={2.5} />
                  </div>
                  <div className="space-y-3">
                    <h4 className="text-base font-black text-white uppercase tracking-tight leading-none">Argument Validé</h4>
                    <p className="text-[10px] font-bold text-emerald-100/60 leading-relaxed uppercase tracking-widest">{point}</p>
                  </div>
                </div>
              ))}

              {/* Erreurs / Omissions */}
              {(nlp.mistakes || []).length > 0 ? (
                nlp.mistakes.map((mistake, i) => (
                  <div key={`mistake-${i}`} className="flex gap-6 group cursor-default bg-rose-500/5 p-6 rounded-3xl border border-rose-500/10 hover:bg-rose-500/10 transition-colors">
                    <div className="mt-1 flex-shrink-0 group-hover:scale-125 transition-transform duration-500 text-rose-500">
                      <AlertCircle size={22} strokeWidth={2.5} />
                    </div>
                    <div className="space-y-3">
                      <h4 className="text-base font-black text-white uppercase tracking-tight leading-none">Omission / Erreur</h4>
                      <p className="text-[10px] font-bold text-rose-200/70 leading-relaxed uppercase tracking-widest">{mistake}</p>
                    </div>
                  </div>
                ))
              ) : (
                <div className="flex gap-6 group cursor-default bg-amber-500/5 p-6 rounded-3xl border border-amber-500/10 hover:bg-amber-500/10 transition-colors">
                  <div className="mt-1 flex-shrink-0 group-hover:scale-125 transition-transform duration-500 text-amber-500">
                    <Activity size={22} strokeWidth={2.5} />
                  </div>
                  <div className="space-y-3">
                    <h4 className="text-base font-black text-white uppercase tracking-tight leading-none">Factualité Parfaite</h4>
                    <p className="text-[10px] font-bold text-amber-100/60 leading-relaxed uppercase tracking-widest">Aucune erreur grave détectée par le NLP sur vos allégations.</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Radar Map */}
        <div className="lg:col-span-12 md-card p-12 flex flex-col gap-10 bg-white border-none shadow-2xl relative overflow-hidden rounded-[40px]">
          <div className="absolute top-0 left-0 w-full h-full bg-md-primary/[0.02] pointer-events-none -z-10" />
          <div className="space-y-1">
            <h3 className="text-2xl font-black text-md-on-background tracking-tighter text-center uppercase leading-none">Cartographie des Compétences</h3>
            <p className="text-xs font-bold text-md-on-surface-variant opacity-60 text-center uppercase tracking-widest mt-2 underline underline-offset-8 decoration-2 decoration-md-primary/20">Analyse pluridimensionnelle IA</p>
          </div>
          <div className="h-[450px] w-full mt-6 flex justify-center">
            <div className="w-full max-w-2xl h-full">
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart cx="50%" cy="50%" outerRadius="80%" data={competenceData}>
                  <PolarGrid stroke="var(--color-md-outline)" strokeOpacity={0.1} />
                  <PolarAngleAxis dataKey="subject" tick={{ fontSize: 11, fontWeight: 900, fill: 'var(--color-md-on-surface-variant)', textTransform: 'uppercase', tracking: '2px' }} />
                  <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                  <Radar
                    name="Ma Performance"
                    dataKey="A"
                    stroke="var(--color-md-primary)"
                    fill="var(--color-md-primary)"
                    fillOpacity={0.5}
                    strokeWidth={6}
                    animationDuration={2500}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Actions Section */}
        <div className="lg:col-span-12 flex flex-col md:flex-row items-center justify-center gap-6 mt-8 pb-12">
          {!reportFileName ? (
            <div className="px-12 h-16 bg-slate-100 text-slate-400 rounded-pill text-[12px] font-black uppercase tracking-[0.2em] flex items-center justify-center gap-3 border border-slate-200 animate-pulse">
              <Activity size={20} className="animate-spin" /> Génération du rapport...
            </div>
          ) : (
            <a
              href={`http://127.0.0.1:8001/reports/${reportFileName}`}
              target="_blank"
              rel="noreferrer"
              className="px-12 h-16 bg-emerald-600 text-white rounded-pill text-[12px] font-black uppercase tracking-[0.2em] flex items-center justify-center gap-3 hover:bg-emerald-700 hover:scale-105 transition-all shadow-2xl shadow-emerald-500/30"
            >
              <Download size={20} /> Télécharger Rapport PDF
            </a>
          )}
          <button
            onClick={() => navigate('/delegate/home')}
            className="px-14 h-16 bg-md-primary text-white rounded-pill text-[12px] font-black uppercase tracking-[0.4em] flex items-center justify-center gap-6 shadow-2xl shadow-md-primary/40 group hover:scale-105 active:scale-95 transition-all relative overflow-hidden"
          >
            <span className="relative z-10">Nouvelle Session</span>
            <ArrowRight size={24} className="relative z-10 group-hover:translate-x-3 transition-transform duration-500" />
            <div className="absolute inset-0 shimmer-anim opacity-20 pointer-events-none" />
          </button>
        </div>
      </div>
    </div>
  );
}
