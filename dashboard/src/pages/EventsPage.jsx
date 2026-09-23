import { useState } from 'react';
import EventFeed from '../components/EventFeed';
import { useLiveEvents } from '../hooks/useData';
import { api } from '../services/api';

export default function EventsPage() {
  const [filters, setFilters] = useState({ hours: 72, severity: '', event_type: '', acknowledged: '' });
  const { events, total, loading, acknowledge, refresh } = useLiveEvents({ hours: filters.hours });
  const [exportLoading, setExportLoading] = useState(false);

  const filtered = events.filter(e => {
    if (filters.severity && e.severity !== filters.severity) return false;
    if (filters.event_type && e.event_type !== filters.event_type) return false;
    if (filters.acknowledged === 'true' && !e.acknowledged) return false;
    if (filters.acknowledged === 'false' && e.acknowledged) return false;
    return true;
  });

  const exportJSON = async () => {
    setExportLoading(true);
    try {
      const data = await api.events.list({ hours: filters.hours, limit: 5000 });
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `surveillance-events-${Date.now()}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      setExportLoading(false);
    }
  };

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-white">Events Explorer</h1>
          <p className="text-sm text-white/50 mt-1">Full audit log with filters, acknowledgements, and JSON export.</p>
        </div>
        <div className="flex items-center gap-2">
          <select className="input !py-2 !px-3 text-xs w-auto"
            value={filters.hours} onChange={e => setFilters({ ...filters, hours: Number(e.target.value) })}>
            {[1, 6, 24, 72, 168, 720].map(h => <option key={h} value={h}>{h}h window</option>)}
          </select>
          <select className="input !py-2 !px-3 text-xs w-auto"
            value={filters.severity} onChange={e => setFilters({ ...filters, severity: e.target.value })}>
            <option value="">All severities</option>
            {['info', 'low', 'medium', 'high', 'critical'].map(s => <option key={s} value={s}>{s}</option>)}
          </select>
          <select className="input !py-2 !px-3 text-xs w-auto"
            value={filters.event_type} onChange={e => setFilters({ ...filters, event_type: e.target.value })}>
            <option value="">All types</option>
            {['loitering','crowd','alpr_result','occupancy_estimate','behaviour_alert','vehicle_detected','system_heartbeat'].map(s =>
              <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>
            )}
          </select>
          <select className="input !py-2 !px-3 text-xs w-auto"
            value={filters.acknowledged} onChange={e => setFilters({ ...filters, acknowledged: e.target.value })}>
            <option value="">All</option>
            <option value="false">Unacknowledged</option>
            <option value="true">Acknowledged</option>
          </select>
          <button onClick={exportJSON} disabled={exportLoading} className="btn-secondary !py-1.5 !px-3 text-xs">
            {exportLoading ? '…' : 'Export JSON'}
          </button>
        </div>
      </div>
      <EventFeed
        events={filtered}
        total={total}
        loading={loading}
        limit={1000}
        onAck={(id) => acknowledge(id, 'operator@university')}
      />
    </div>
  );
}
