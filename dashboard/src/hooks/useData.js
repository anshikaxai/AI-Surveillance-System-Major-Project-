import { useEffect, useRef, useState, useCallback } from 'react';
import { api } from '../services/api';

export function useLiveEvents({ hours = 24, intervalMs = 3000 } = {}) {
  const [events, setEvents] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const seen = useRef(new Set());

  const fetch = useCallback(async () => {
    try {
      const data = await api.events.list({ hours, limit: 100 });
      const fresh = [];
      for (const e of data.items) {
        if (!seen.current.has(e.event_id)) fresh.push(e);
        seen.current.add(e.event_id);
      }
      if (fresh.length) {
        setEvents(prev => {
          const merged = [...fresh, ...prev];
          return merged.slice(0, 300);
        });
      }
      setTotal(data.total);
      setError(null);
    } catch (err) {
      setError(err.message || 'Fetch failed');
    } finally {
      setLoading(false);
    }
  }, [hours]);

  useEffect(() => {
    fetch();
    const t = setInterval(fetch, intervalMs);
    return () => clearInterval(t);
  }, [fetch, intervalMs]);

  return { events, total, loading, error, refresh: fetch,
    acknowledge: async (id, by) => {
      const updated = await api.events.ack(id, by);
      setEvents(prev => prev.map(e => (e.event_id === id ? updated : e)));
      return updated;
    },
  };
}

export function useStats(hours = 24) {
  const [stats, setStats] = useState({ total: 0, by_type: {}, by_severity: {} });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancel = false;
    const run = async () => {
      try {
        const s = await api.events.stats(hours);
        if (!cancel) setStats(s);
      } finally {
        if (!cancel) setLoading(false);
      }
    };
    run();
    const t = setInterval(run, 5000);
    return () => { cancel = true; clearInterval(t); };
  }, [hours]);

  return { stats, loading };
}

export function useCameras() {
  const [cameras, setCameras] = useState([]);
  const [loading, setLoading] = useState(true);
  const refresh = useCallback(async () => {
    try { setCameras(await api.cameras.list()); } finally { setLoading(false); }
  }, []);
  useEffect(() => { refresh(); }, [refresh]);
  return { cameras, loading, refresh };
}

export function useROIs(cameraId) {
  const [rois, setRois] = useState([]);
  const [loading, setLoading] = useState(true);
  const refresh = useCallback(async () => {
    setLoading(true);
    try { setRois(await api.rois.list(cameraId)); } finally { setLoading(false); }
  }, [cameraId]);
  useEffect(() => { refresh(); }, [refresh]);
  return { rois, loading, refresh,
    save: async (payload, id) => id ? api.rois.update(id, payload) : api.rois.create(payload),
    remove: async (id) => api.rois.delete(id),
  };
}
