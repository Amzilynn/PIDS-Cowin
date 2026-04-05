import React from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, 
  AreaChart, Area, PieChart, Pie, Cell 
} from 'recharts';
import { 
  Users, 
  TrendingUp, 
  Target, 
  Award, 
  Search, 
  Filter, 
  MoreHorizontal,
  ChevronRight,
  Download,
  Calendar
} from 'lucide-react';
import { motion } from 'framer-motion';

const performanceData = [
  { name: 'Mon', engagement: 4000, compliance: 2400 },
  { name: 'Tue', engagement: 3000, compliance: 1398 },
  { name: 'Wed', engagement: 2000, compliance: 9800 },
  { name: 'Thu', engagement: 2780, compliance: 3908 },
  { name: 'Fri', engagement: 1890, compliance: 4800 },
  { name: 'Sat', engagement: 2390, compliance: 3800 },
  { name: 'Sun', engagement: 3490, compliance: 4300 },
];

const delegates = [
  { id: 1, name: "Dr. Sarah Khalil", role: "Medical Delegate", score: 94, status: "Active", region: "North Zone" },
  { id: 2, name: "Youssef Amari", role: "Commercial Rep", score: 88, status: "Active", region: "South Coast" },
  { id: 3, name: "Leila Ben Salah", role: "Medical Delegate", score: 76, status: "Training", region: "Capital District" },
  { id: 4, name: "Ahmed Mansouri", role: "Commercial Rep", score: 91, status: "Active", region: "West Valley" },
];

const KPI_COLORS = ['#4E8C8A', '#0B1B2B', '#3B82F6', '#6366f1'];

export default function AdminDashboard() {
  return (
    <div className="space-y-8 animate-fade-in">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
           <h1 className="text-3xl font-black text-brand-navy tracking-tighter">Global <span className="text-brand-teal">Analytics</span> Hub</h1>
           <p className="text-slate-500 font-semibold text-sm">MedDelegate Pro Performance Overview • Q2 2026</p>
        </div>
        
        <div className="flex items-center gap-3">
           <div className="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 rounded-xl shadow-sm text-xs font-bold text-slate-600">
              <Calendar size={14} className="text-brand-teal" /> Last 30 Days
           </div>
           <button className="flex items-center gap-2 px-6 py-2.5 bg-brand-navy text-white rounded-xl font-bold text-xs uppercase tracking-widest shadow-xl shadow-brand-navy/20 hover:scale-105 transition-all">
              <Download size={14} /> Export Report
           </button>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {[
          { label: 'Active Delegates', value: '1,284', trend: '+12%', icon: Users },
          { label: 'Avg Detailing Score', value: '86.4%', trend: '+4.2%', icon: Target },
          { label: 'Compliance Rate', value: '99.2%', trend: 'Stable', icon: ShieldCheck },
          { label: 'Growth Velocity', value: '14.8%', trend: '+2.1%', icon: TrendingUp },
        ].map((kpi, i) => (
          <motion.div 
            key={i}
            whileHover={{ y: -4 }}
            className="p-6 bg-white rounded-4xl border border-slate-200 shadow-sm relative overflow-hidden"
          >
             <div className="flex items-center justify-between mb-4">
                <div className="w-10 h-10 rounded-2xl bg-slate-50 flex items-center justify-center text-brand-teal">
                   <kpi.icon size={20} />
                </div>
                <span className={`text-[10px] font-black uppercase tracking-widest ${kpi.trend.includes('+') ? 'text-emerald-500' : 'text-slate-400'}`}>
                   {kpi.trend}
                </span>
             </div>
             <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-1">{kpi.label}</p>
             <h3 className="text-2xl font-black text-brand-navy tracking-tight">{kpi.value}</h3>
             
             {/* Subtle background pulse animation indicator */}
             <div className="absolute -right-4 -bottom-4 w-20 h-20 bg-brand-teal/5 rounded-full blur-2xl" />
          </motion.div>
        ))}
      </div>

      {/* Main Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Performance Area Chart */}
        <div className="lg:col-span-2 p-8 bg-white rounded-4xl border border-slate-200 shadow-sm">
           <div className="flex items-center justify-between mb-10">
              <h3 className="text-lg font-extrabold text-brand-navy tracking-tight">System Utilization & Detailing Velocity</h3>
              <div className="flex gap-4">
                 <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-brand-teal" />
                    <span className="text-[10px] font-bold text-slate-400 uppercase">Engagement</span>
                 </div>
                 <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-brand-navy" />
                    <span className="text-[10px] font-bold text-slate-400 uppercase">Compliance</span>
                 </div>
              </div>
           </div>
           
           <div className="h-[300px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                 <AreaChart data={performanceData}>
                   <defs>
                     <linearGradient id="colorEngagement" x1="0" y1="0" x2="0" y2="1">
                       <stop offset="5%" stopColor="#4E8C8A" stopOpacity={0.3}/>
                       <stop offset="95%" stopColor="#4E8C8A" stopOpacity={0}/>
                     </linearGradient>
                   </defs>
                   <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                   <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 10, fontWeight: 700, fill: '#94a3b8' }} dy={10} />
                   <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 10, fontWeight: 700, fill: '#94a3b8' }} />
                   <Tooltip 
                      contentStyle={{ borderRadius: '16px', border: 'none', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)', padding: '12px' }}
                      labelStyle={{ fontWeight: 800, color: '#0B1B2B', marginBottom: '4px' }}
                   />
                   <Area type="monotone" dataKey="engagement" stroke="#4E8C8A" strokeWidth={3} fillOpacity={1} fill="url(#colorEngagement)" />
                   <Area type="monotone" dataKey="compliance" stroke="#0B1B2B" strokeWidth={3} fill="transparent" />
                 </AreaChart>
              </ResponsiveContainer>
           </div>
        </div>

        {/* Sector Allocation Pie Chart */}
        <div className="p-8 bg-white rounded-4xl border border-slate-200 shadow-sm flex flex-col">
           <h3 className="text-lg font-extrabold text-brand-navy tracking-tight mb-8">Business Object Health</h3>
           <div className="flex-1 min-h-[240px]">
              <ResponsiveContainer width="100%" height="100%">
                 <PieChart>
                    <Pie
                       data={[
                          { name: 'Simulator', value: 45 },
                          { name: 'Products', value: 25 },
                          { name: 'Planning', value: 30 }
                       ]}
                       innerRadius={60}
                       outerRadius={80}
                       paddingAngle={8}
                       dataKey="value"
                    >
                       {KPI_COLORS.map((color, index) => (
                          <Cell key={`cell-${index}`} fill={color} />
                       ))}
                    </Pie>
                    <Tooltip />
                 </PieChart>
              </ResponsiveContainer>
           </div>
           <div className="space-y-3 mt-6">
              {['Training Simulator', 'Product Recommender', 'Visit Strategy'].map((item, i) => (
                 <div key={item} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                       <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: KPI_COLORS[i] }} />
                       <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">{item}</span>
                    </div>
                    <span className="text-xs font-black text-brand-navy">Active</span>
                 </div>
              ))}
           </div>
        </div>
      </div>

      {/* Delegates Management Table */}
      <div className="p-8 bg-white rounded-4xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-10">
           <div>
              <h3 className="text-lg font-extrabold text-brand-navy tracking-tight">Active Professional Registry</h3>
              <p className="text-[10px] font-black text-brand-teal uppercase tracking-widest mt-1 underline underline-offset-4 decoration-2">Manage All 1,284 Profiles</p>
           </div>
           <div className="flex items-center gap-3">
              <div className="relative">
                 <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
                 <input type="text" placeholder="Search professionals..." className="pl-12 pr-6 py-2.5 bg-slate-50 border border-slate-100 rounded-xl text-xs font-bold font-sans outline-none focus:border-brand-teal transition-all w-64" />
              </div>
              <button className="p-2.5 bg-slate-50 border border-slate-100 rounded-xl text-slate-500 hover:text-brand-navy transition-colors">
                 <Filter size={18} />
              </button>
           </div>
        </div>

        <div className="overflow-x-auto shadow-inner rounded-3xl">
           <table className="w-full text-left">
              <thead className="bg-slate-50 text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">
                 <tr>
                    <th className="px-6 py-5">Professional Name</th>
                    <th className="px-6 py-5">Role Segment</th>
                    <th className="px-6 py-5">Territory Region</th>
                    <th className="px-6 py-5 text-center">Avg Rating</th>
                    <th className="px-6 py-5">Status</th>
                    <th className="px-6 py-5 text-right">Actions</th>
                 </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                 {delegates.map((d, i) => (
                    <tr key={i} className="group hover:bg-slate-50/50 transition-colors">
                       <td className="px-6 py-5">
                          <div className="flex items-center gap-3">
                             <div className="w-9 h-9 rounded-full bg-brand-navy/5 flex items-center justify-center text-brand-navy font-black text-xs uppercase">
                                {d.name.match(/\b\w/g).join('')}
                             </div>
                             <span className="text-sm font-extrabold text-brand-navy tracking-tight">{d.name}</span>
                          </div>
                       </td>
                       <td className="px-6 py-5">
                          <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">{d.role}</span>
                       </td>
                       <td className="px-6 py-5 font-bold text-slate-600 text-xs">
                          {d.region}
                       </td>
                       <td className="px-6 py-5 text-center">
                          <div className="inline-flex items-center gap-2 px-3 py-1 bg-emerald-50 text-emerald-600 rounded-full text-xs font-black">
                             <Award size={12} /> {d.score}%
                          </div>
                       </td>
                       <td className="px-6 py-5">
                          <div className="flex items-center gap-2 text-[10px] font-black text-emerald-600 uppercase tracking-widest">
                             <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse" /> {d.status}
                          </div>
                       </td>
                       <td className="px-6 py-5 text-right">
                          <button className="p-2 text-slate-300 hover:text-brand-navy transition-colors">
                             <MoreHorizontal size={18} />
                          </button>
                       </td>
                    </tr>
                 ))}
              </tbody>
           </table>
        </div>
      </div>
    </div>
  );
}

const ShieldCheck = ({ size, className }) => <Users size={size} className={className} />; // Fallback mock
