import { AlertTriangle, Users, ShieldCheck, CarFront, Clock } from 'lucide-react';
import { useStats } from '../hooks/useData';

export default function StatsCards({ hours = 24 }) {
  const { stats, loading } = useStats(hours);
  const cards = [
    {
      label: 'Total Events', value: stats.total,
      icon: AlertTriangle, tint: 'from-accent-violet',
      sub: `Last ${hours}h`,
    },
    {
      label: 'Crowd Alerts', value: stats.by_type?.crowd || 0,
      icon: Users, tint: 'from-accent-amber',
      sub: 'Crowd threshold breaches',
    },
    {
      label: 'Loitering Alerts', value: stats.by_type?.loitering || 0,
      icon: Clock, tint: 'from-accent-red',
      sub: 'Sustained ROI presence',
    },
    {
      label: 'Vehicle / ALPR Events',
      value: (stats.by_type?.alpr_result || 0) + (stats.by_type?.vehicle_detected || 0),
      icon: CarFront, tint: 'from-accent-cyan',
      sub: 'Plates + occupancy',
    },
    {
      label: 'High Severity',
      value: (stats.by_severity?.high || 0) + (stats.by_severity?.critical || 0),
      icon: ShieldCheck, tint: 'from-accent-green',
      sub: 'High + critical events',
    },
  ];
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
      {cards.map(({ label, value, icon: Icon, tint, sub }) => (
        <div key={label} className="card p-5 animate-slide_in relative overflow-hidden group">
          <div className={`absolute -top-8 -right-8 w-28 h-28 rounded-full bg-gradient-to-br ${tint} to-transparent opacity-20 group-hover:opacity-30 blur-2xl transition-opacity`} />
          <div className="flex items-start justify-between relative">
            <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${tint} to-transparent flex items-center justify-center`}>
              <Icon className="text-white" size={20} />
            </div>
          </div>
          <div className="mt-4">
            <p className="text-3xl font-bold text-white tabular-nums">
              {loading ? <span className="text-white/30">—</span> : value.toLocaleString()}
            </p>
            <p className="text-sm text-white/60 mt-1">{label}</p>
            <p className="text-[11px] text-white/35 mt-1">{sub}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
