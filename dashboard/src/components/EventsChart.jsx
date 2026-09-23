import { useStats } from '../hooks/useData';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend } from 'recharts';

const COLORS = ['#06B6D4', '#F59E0B', '#EF4444', '#10B981', '#8B5CF6'];

export default function EventsChart({ hours = 24 }) {
  const { stats } = useStats(hours);
  const typeData = Object.entries(stats.by_type || {}).map(([name, value]) => ({ name: name.replace(/_/g, ' '), value }));
  const sevData = Object.entries(stats.by_severity || {}).map(([name, value]) => ({ name, value }));

  return (
    <div className="card p-5 animate-slide_in">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="font-semibold text-white">Event Analytics ({hours}h)</h3>
          <p className="text-xs text-white/45 mt-0.5">Distribution by event type × severity</p>
        </div>
      </div>
      <div className="grid md:grid-cols-2 gap-6 h-[260px]">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={typeData} dataKey="value" nameKey="name" cx="50%" cy="50%"
              outerRadius={82} innerRadius={46} paddingAngle={3}>
              {typeData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
            </Pie>
            <Tooltip contentStyle={{ background: '#111A2E', border: '1px solid #253053', borderRadius: 12, color: '#fff' }} />
            <Legend wrapperStyle={{ color: '#cbd5e1', fontSize: 11 }} />
          </PieChart>
        </ResponsiveContainer>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={sevData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} />
            <YAxis stroke="#94a3b8" fontSize={11} allowDecimals={false} />
            <Tooltip contentStyle={{ background: '#111A2E', border: '1px solid #253053', borderRadius: 12, color: '#fff' }} />
            <Bar dataKey="value" fill="#10B981" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
