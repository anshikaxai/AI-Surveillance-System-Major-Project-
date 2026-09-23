import { format } from 'date-fns';
import { Check, Eye, Car, Users, Clock, CarFront, ShieldAlert, Activity, Radio } from 'lucide-react';

const ICONS = {
  loitering: Clock,
  crowd: Users,
  alpr_result: Car,
  vehicle_detected: CarFront,
  occupancy_estimate: Users,
  behaviour_alert: Activity,
  system_heartbeat: Radio,
};

function sevCls(s) {
  return `severity-${s || 'medium'}`;
}

export default function EventFeed({ events, total, loading, onAck, limit = 50 }) {
  const list = (events || []).slice(0, limit);
  return (
    <div className="card overflow-hidden flex flex-col h-full">
      <div className="px-5 py-4 border-b border-base-600/40 flex items-center justify-between">
        <div>
          <h3 className="font-semibold text-white">Live Event Feed</h3>
          <p className="text-xs text-white/45 mt-0.5">
            {loading ? 'Loading…' : `${list.length} shown of ${total} total events`}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent-green opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-accent-green"></span>
          </span>
          <span className="text-[11px] uppercase tracking-wider text-white/50">live</span>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto divide-y divide-base-600/20 max-h-[560px]">
        {!list.length && !loading && (
          <div className="p-10 text-center text-white/40 text-sm">
            <ShieldAlert size={36} className="mx-auto mb-3 opacity-40" />
            No events yet — waiting for pipeline output…
          </div>
        )}
        {list.map((e, i) => {
          const Ic = ICONS[e.event_type] || Activity;
          return (
            <div key={e.event_id} style={{ animationDelay: `${i * 15}ms` }}
              className="px-5 py-4 hover:bg-base-700/30 animate-slide_in transition-colors group">
              <div className="flex items-start gap-3">
                <div className={`w-9 h-9 rounded-lg bg-gradient-to-br
                    ${e.event_type === 'loitering' ? 'from-accent-red/50 to-transparent'
                      : e.event_type === 'crowd' ? 'from-accent-amber/50 to-transparent'
                      : e.event_type === 'alpr_result' ? 'from-accent-cyan/50 to-transparent'
                      : 'from-accent-violet/50 to-transparent'}
                    flex items-center justify-center shrink-0`}>
                  <Ic size={16} className="text-white" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-semibold capitalize text-white text-sm">{e.event_type.replace(/_/g, ' ')}</span>
                    <span className={sevCls(e.severity)}>{e.severity}</span>
                    {e.roi_name && <span className="chip bg-base-600/40 text-white/70 border-white/10">{e.roi_name}</span>}
                    {e.acknowledged && <span className="chip bg-accent-green/15 text-accent-green border-accent-green/30"><Check size={10} /> ACK</span>}
                  </div>
                  <p className="text-sm text-white/70 mt-1 line-clamp-2">{e.explanation}</p>
                  <div className="mt-2 flex items-center justify-between gap-3 text-[11px] text-white/40 font-mono">
                    <div className="flex items-center gap-3 flex-wrap">
                      <span>#{e.camera_id}</span>
                      {e.track_ids?.length > 0 && <span>tracks: [{e.track_ids.join(', ')}]</span>}
                      <span>{format(e.timestamp * 1000, 'HH:mm:ss')}</span>
                    </div>
                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button className="p-1.5 rounded-md hover:bg-base-600/70 text-white/60" title="Details">
                        <Eye size={14} />
                      </button>
                      {!e.acknowledged && (
                        <button onClick={() => onAck?.(e.event_id)}
                          className="chip bg-accent-green/15 text-accent-green border-accent-green/30 hover:bg-accent-green/25">
                          <Check size={11} /> Ack
                        </button>
                      )}
                    </div>
                  </div>
                  {e.metadata && Object.keys(e.metadata).length > 0 && (
                    <details className="mt-2">
                      <summary className="text-[11px] text-white/30 cursor-pointer hover:text-white/60 select-none">metadata</summary>
                      <pre className="mt-1 text-[10px] font-mono text-white/55 bg-base-900/60 rounded-md p-2 overflow-x-auto border border-base-600/30">
{JSON.stringify(e.metadata, null, 2)}
                      </pre>
                    </details>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
