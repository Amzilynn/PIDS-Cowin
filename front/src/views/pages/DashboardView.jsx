import { motion } from 'framer-motion';
import { Activity, Thermometer, CalendarCheck, FileText, CheckCircle2, Clock, XCircle } from 'lucide-react';
import { Stat } from '../components/Stat';
import { Card } from '../components/Card';

export function DashboardView({ stats, streamLogs, visits, roleType }) {
  // Filter stats based on sector (fail-safe: if sector is missing, show it)
  const filteredStats = (stats || []).filter(s => !s.sector || s.sector === roleType);
  
  // Guard against undefined props before API data loads
  const todayVisits = (visits || []).slice(0, 4); 

  const getStatusIcon = (status) => {
    switch(status) {
      case 'Completed': return <CheckCircle2 className="text-emerald-500" size={16} />;
      case 'Pending': return <Clock className="text-amber-500" size={16} />;
      case 'Cancelled': return <XCircle className="text-rose-500" size={16} />;
      default: return <Clock className="text-slate-400" size={16} />;
    }
  };

  return (
    <div className="space-y-6">
      {/* KPI Stats */}
      <div className="grid grid-cols-4 gap-6">
        {filteredStats.length > 0 ? filteredStats.map((stat, i) => (
          <Stat key={i} label={stat.label} value={stat.value} trend={stat.trend} />
        )) : <div className="col-span-4 text-slate-400 font-medium">No {roleType} metrics available.</div>}
      </div>

      {/* Quick Actions for Medical Rep */}
      <div className="grid grid-cols-3 gap-6">
        <motion.button whileHover={{ scale: 1.02 }} className="p-4 bg-gradient-to-r from-[#0A5C5C] to-teal-700 text-white rounded-2xl flex items-center justify-center gap-3 font-bold shadow-lg shadow-teal-900/20">
          <CalendarCheck size={20} /> Log Physician Visit
        </motion.button>
        <motion.button whileHover={{ scale: 1.02 }} className="p-4 bg-gradient-to-r from-indigo-600 to-indigo-800 text-white rounded-2xl flex items-center justify-center gap-3 font-bold shadow-lg shadow-indigo-900/20">
          <Thermometer size={20} /> Request Samples
        </motion.button>
        <motion.button whileHover={{ scale: 1.02 }} className="p-4 bg-gradient-to-r from-rose-600 to-rose-800 text-white rounded-2xl flex items-center justify-center gap-3 font-bold shadow-lg shadow-rose-900/20">
          <FileText size={20} /> Report AE (Adverse Event)
        </motion.button>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Today's Itinerary */}
        <Card className="col-span-2">
          <h3 className="text-lg font-black mb-6">Today's Itinerary</h3>
          <div className="space-y-4">
            {todayVisits.length > 0 ? todayVisits.map((visit, i) => (
              <motion.div 
                key={visit.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.1 }}
                className="flex items-center justify-between p-4 bg-slate-50 border border-slate-100 rounded-xl hover:bg-white hover:shadow-md transition-all"
              >
                <div className="flex flex-col">
                  <span className="font-bold text-slate-900 text-base">{visit.doctor_name}</span>
                  <span className="text-xs font-medium text-slate-500">{visit.specialty} • {visit.hospital}</span>
                </div>
                <div className="flex items-center gap-4">
                  <span className="text-sm font-black font-mono bg-slate-200 text-slate-700 px-3 py-1 rounded-md">
                    {visit.scheduled_time.slice(0, 5)}
                  </span>
                  <div className="flex items-center gap-2 bg-white px-3 py-1 rounded-full border border-slate-200 shadow-sm">
                    {getStatusIcon(visit.status)}
                    <span className="text-xs font-bold text-slate-700">{visit.status}</span>
                  </div>
                </div>
              </motion.div>
            )) : <div className="text-sm font-medium text-slate-400">Loading your visits for today...</div>}
          </div>
        </Card>
        
        {/* AI Stream */}
        <div className="bg-[#0F172A] rounded-[32px] p-8 text-white flex flex-col">
          <div className="flex items-center gap-2 text-[#E6B800] mb-6">
            <Activity size={18} />
            <span className="text-xs font-black uppercase tracking-widest">Delegation AI Stream</span>
          </div>
          <div className="space-y-4 font-mono text-sm text-emerald-400 overflow-hidden">
            {streamLogs.length > 0 ? streamLogs.map((log, i) => (
              <p key={log.id} className={log.type === 'DATA' ? 'text-slate-500' : ''}>
                {log.message}
              </p>
            )) : <p className="text-slate-500">Connecting to MySQL backend stream...</p>}
          </div>
        </div>
      </div>
    </div>
  );
}
