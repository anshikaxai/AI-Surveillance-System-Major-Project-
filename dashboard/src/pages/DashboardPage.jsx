import { useState } from 'react';
import StatsCards from '../components/StatsCards';
import EventFeed from '../components/EventFeed';
import EventsChart from '../components/EventsChart';
import NLPCommandPanel from '../components/NLPCommandPanel';
import { useLiveEvents } from '../hooks/useData';

const STAGE_STYLES = [
  { border: 'border-slate-500/40', bg: 'bg-slate-600/20', text: 'text-slate-300' },
  { border: 'border-cyan-500/40', bg: 'bg-cyan-500/15', text: 'text-cyan-400' },
  { border: 'border-violet-500/40', bg: 'bg-violet-500/15', text: 'text-violet-400' },
  { border: 'border-amber-500/40', bg: 'bg-amber-500/15', text: 'text-amber-400' },
  { border: 'border-emerald-500/40', bg: 'bg-emerald-500/15', text: 'text-emerald-400' },
];

export default function DashboardPage({ refreshKey }) {
  const [hours, setHours] = useState(24);
  const { events, total, loading, acknowledge } = useLiveEvents({ hours });

  const stages = [
    ['Video In', 'RTSP / File / Webcam'],
    ['Perception', 'YOLOv8s + ByteTrack'],
    ['Domain', 'Behaviour · ALPR · Occupancy'],
    ['Event Intel', 'ROI · Thresholds · Cooldowns'],
    ['Explainable Alerts', 'JSONB → PostgreSQL'],
  ];

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-white">Command Center</h1>
          <p className="text-sm text-white/50 mt-1">Real-time perception → explainable event intelligence</p>
        </div>
        <div className="flex items-center gap-2 text-xs">
          {[1, 6, 24, 72].map(h => (
            <button key={h} onClick={() => setHours(h)}
              className={`btn !py-1.5 !px-3 ${hours === h ? 'bg-accent-green text-base-900' : 'btn-secondary'}`}>
              {h}h
            </button>
          ))}
        </div>
      </div>

      <StatsCards hours={hours} />

      <div className="grid lg:grid-cols-5 gap-5">
        <div className="lg:col-span-2 space-y-5">
          <EventFeed
            events={events}
            total={total}
            loading={loading}
            onAck={(id) => acknowledge(id, 'operator@university')}
          />
        </div>
        <div className="lg:col-span-3 space-y-5">
          <EventsChart hours={hours} />
          <NLPCommandPanel />
          <div className="card p-5 animate-slide_in">
            <h3 className="font-semibold text-white mb-3">Pipeline Flow (Layered Architecture)</h3>
            <div className="relative flex flex-wrap items-stretch gap-3 text-xs">
              {stages.map(([name, sub], i, arr) => {
                const s = STAGE_STYLES[i] || STAGE_STYLES[0];
                return (
                  <div key={name} className="flex-1 min-w-[160px] relative">
                    <div className={`rounded-xl border ${s.border} ${s.bg} p-3 h-full`}>
                      <p className={`font-semibold uppercase tracking-wider text-[10px] ${s.text}`}>{name}</p>
                      <p className="text-white/80 mt-1 font-medium">{sub}</p>
                    </div>
                    {i < arr.length - 1 && (
                      <div className="hidden lg:block absolute top-1/2 -right-3 -translate-y-1/2 z-10 text-white/40 font-bold">→</div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
