import { motion } from 'framer-motion';
import { Card } from '../components/Card';
import { Target, Pill, TrendingUp, BarChart2, Users, PackageCheck } from 'lucide-react';

export function AnalyticsView({ kpis, visits, products, roleType }) {
  const safeVisits = visits || [];
  const safeKpis = (kpis || []).filter(k => !k.sector || k.sector === roleType);
  const safeProducts = (products || []).filter(p => !p.sector || p.sector === roleType);

  const completedVisits = safeVisits.filter(v => v.status === 'Completed').length;
  const pendingVisits = safeVisits.filter(v => v.status === 'Pending').length;
  const totalVisits = safeVisits.length;
  const completionRate = totalVisits ? Math.round((completedVisits / totalVisits) * 100) : 0;

  return (
    <div className="space-y-6">
      {/* Top Row: KPI Tracking + Donut Ring */}
      <div className="grid grid-cols-3 gap-6">
        {/* KPI Target Progress */}
        <div className="col-span-2">
          <Card>
            <div className="flex items-center justify-between mb-8">
              <h3 className="text-lg font-black uppercase tracking-tight text-slate-800">Delegate KPI vs Targets</h3>
              <Target className="text-[#E6B800]" size={22} />
            </div>
            <div className="space-y-6">
              {safeKpis.length > 0 ? safeKpis.map((kpi, i) => {
                const pct = Math.min(((kpi.current_value / kpi.target_value) * 100).toFixed(0), 100);
                return (
                  <div key={kpi.id}>
                    <div className="flex justify-between mb-2 font-bold text-xs uppercase tracking-wider text-slate-600">
                      <span>{kpi.metric_name}</span>
                      <span className={pct >= 80 ? 'text-emerald-600' : 'text-amber-600'}>{kpi.current_value} / {kpi.target_value} {kpi.unit}</span>
                    </div>
                    <div className="h-4 bg-slate-100 rounded-full overflow-hidden border border-slate-200">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${pct}%` }}
                        transition={{ duration: 1, ease: 'easeOut', delay: i * 0.2 }}
                        className={`h-full ${pct >= 80 ? 'bg-emerald-500' : 'bg-[#0A5C5C]'}`}
                      />
                    </div>
                  </div>
                );
              }) : <p className="text-slate-400 font-medium text-sm">Loading KPIs...</p>}
            </div>
          </Card>
        </div>

        {/* Completion Score Ring */}
        <Card className="flex flex-col items-center justify-center text-center">
          <div className="relative w-40 h-40 mb-5">
            <svg viewBox="0 0 100 100" className="rotate-[-90deg] w-full h-full">
              <circle cx="50" cy="50" r="40" fill="none" stroke="#f1f5f9" strokeWidth="12" />
              <motion.circle
                cx="50" cy="50" r="40" fill="none"
                stroke="#0A5C5C" strokeWidth="12"
                strokeLinecap="round"
                strokeDasharray={`${2 * Math.PI * 40}`}
                initial={{ strokeDashoffset: 2 * Math.PI * 40 }}
                animate={{ strokeDashoffset: 2 * Math.PI * 40 * (1 - completionRate / 100) }}
                transition={{ duration: 1.2, ease: 'easeOut' }}
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <p className="text-4xl font-black">{completionRate}%</p>
              <p className="text-[10px] font-bold text-slate-400 uppercase">Completion</p>
            </div>
          </div>
          <h4 className="font-black text-slate-900">Visit Goal Rate</h4>
          <p className="text-xs text-slate-500 mt-1">{completedVisits} done · {pendingVisits} remaining</p>
        </Card>
      </div>

      {/* Bottom Row: Product Mix + Visit Breakdown */}
      <div className="grid grid-cols-2 gap-6">
        {/* Product Market Share */}
        <Card>
          <div className="flex items-center gap-3 mb-6">
            <BarChart2 className="text-[#0A5C5C]" size={20} />
            <h3 className="text-base font-black uppercase text-slate-800">Product Market Displacement</h3>
          </div>
          <div className="space-y-5">
            {safeProducts.length > 0 ? safeProducts.map((p, i) => (
              <div key={i}>
                <div className="flex justify-between mb-2 font-bold text-xs uppercase text-slate-600">
                  <span>{p.product_name}</span>
                  <span className="text-[#0A5C5C]">{p.market_share_pct}% · ↑{p.growth_pct}%</span>
                </div>
                <div className="h-5 bg-slate-100 rounded-lg overflow-hidden border border-slate-200">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${p.market_share_pct}%` }}
                    transition={{ duration: 0.8, delay: i * 0.15, ease: 'easeOut' }}
                    className="h-full bg-[#0A5C5C]"
                  />
                </div>
              </div>
            )) : <p className="text-slate-400 text-sm">Loading products...</p>}
          </div>
        </Card>

        {/* Visit Stats by Specialty */}
        <Card>
          <div className="flex items-center gap-3 mb-6">
            <Users className="text-indigo-500" size={20} />
            <h3 className="text-base font-black uppercase text-slate-800">Today's Routing Summary</h3>
          </div>
          <div className="space-y-3">
            {safeVisits.length > 0 ? safeVisits.map((v, i) => (
              <div key={i} className="flex items-center justify-between p-3 bg-slate-50 rounded-xl border border-slate-100">
                <div>
                  <p className="font-bold text-sm text-slate-800">{v.doctor_name}</p>
                  <p className="text-xs text-slate-500">{v.specialty}</p>
                </div>
                <span className={`text-xs font-black px-3 py-1 rounded-full ${
                  v.status === 'Completed' ? 'bg-emerald-100 text-emerald-700' :
                  v.status === 'Pending' ? 'bg-amber-100 text-amber-700' :
                  'bg-rose-100 text-rose-700'
                }`}>{v.status}</span>
              </div>
            )) : <p className="text-slate-400 text-sm">Loading visit data...</p>}
          </div>
        </Card>
      </div>
    </div>
  );
}
