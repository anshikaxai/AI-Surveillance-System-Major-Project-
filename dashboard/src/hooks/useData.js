import {
  useEffect,
  useRef,
  useState,
  useCallback,
} from 'react';

import { api } from '../services/api';


export function useLiveEvents({
  hours = 24,
  intervalMs = 3000,
} = {}) {

  const [events, setEvents] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const seen = useRef(new Set());

  const fetch = useCallback(async () => {

    try {

      // ---------------------------------------------
      // EXISTING DATABASE EVENTS
      // ---------------------------------------------
      const data = await api.events.list({
        hours,
        limit: 100,
      });

      const fresh = [];

      for (const e of data.items || []) {

        if (!seen.current.has(e.event_id)) {
          fresh.push(e);
        }

        seen.current.add(e.event_id);
      }


      // ---------------------------------------------
      // CCTV 2 ALERTS
      // ---------------------------------------------
      try {

        const cctv2Data =
          await api.cctv2.alerts();

        const alerts =
          cctv2Data.alerts || [];

        for (const alert of alerts) {

          const eventId =
            `cctv2-${alert.event_type}-${alert.track_id ?? 'global'}-${alert.timestamp}`;

          if (seen.current.has(eventId)) {
            continue;
          }

          seen.current.add(eventId);

          fresh.push({
            event_id: eventId,

            camera_id:
              alert.camera_id || 'CAM-002',

            event_type:
              alert.event_type || 'behaviour_alert',

            severity:
              alert.severity || 'medium',

            explanation:
              alert.message ||
              'CCTV 2 activity alert',

            timestamp:
              alert.timestamp,

            track_ids:
              alert.track_id !== null &&
                alert.track_id !== undefined
                ? [alert.track_id]
                : [],

            roi_name:
              alert.event_type ===
                'restricted_zone_entry'
                ? 'Restricted Zone'
                : alert.event_type ===
                  'loitering'
                  ? 'Lobby ROI'
                  : null,

            acknowledged: false,

            metadata: {
              source: 'CAM-002',
              analytics: 'human-activity',
            },
          });
        }

      } catch (cctv2Err) {

        console.warn(
          'CCTV 2 alert fetch failed:',
          cctv2Err
        );

      }


      // ---------------------------------------------
      // MERGE EVENTS
      // ---------------------------------------------
      if (fresh.length > 0) {

        setEvents((prev) => {

          const merged = [
            ...fresh,
            ...prev,
          ];

          return merged
            .sort((a, b) => {

              const ta =
                typeof a.timestamp === 'number'
                  ? a.timestamp
                  : new Date(
                    a.timestamp || 0
                  ).getTime() / 1000;

              const tb =
                typeof b.timestamp === 'number'
                  ? b.timestamp
                  : new Date(
                    b.timestamp || 0
                  ).getTime() / 1000;

              return tb - ta;
            })
            .slice(0, 300);

        });
      }


      const cctv2Count =
        Array.from(
          seen.current
        ).filter((id) =>
          String(id).startsWith(
            'cctv2-'
          )
        ).length;


      setTotal(
        (data.total || 0)
        + cctv2Count
      );

      setError(null);

    } catch (err) {

      setError(
        err.message ||
        'Fetch failed'
      );

    } finally {

      setLoading(false);

    }

  }, [hours]);


  useEffect(() => {

    fetch();

    const t = setInterval(
      fetch,
      intervalMs
    );

    return () => {
      clearInterval(t);
    };

  }, [fetch, intervalMs]);


  const acknowledge =
    async (id, by) => {

      // CCTV2 demo alert:
      // acknowledge locally
      if (
        String(id).startsWith(
          'cctv2-'
        )
      ) {

        setEvents((prev) =>
          prev.map((e) =>
            e.event_id === id
              ? {
                ...e,
                acknowledged: true,
              }
              : e
          )
        );

        return;
      }


      // Existing DB event
      const updated =
        await api.events.ack(
          id,
          by
        );

      setEvents((prev) =>
        prev.map((e) =>
          e.event_id === id
            ? updated
            : e
        )
      );

      return updated;
    };


  return {
    events,
    total,
    loading,
    error,
    refresh: fetch,
    acknowledge,
  };
}


// =========================================================
// STATS
// =========================================================

export function useStats(hours = 24) {

  const [stats, setStats] =
    useState({
      total: 0,
      by_type: {},
      by_severity: {},
    });

  const [loading, setLoading] =
    useState(true);


  useEffect(() => {

    let cancel = false;

    const run = async () => {

      try {

        const s =
          await api.events.stats(
            hours
          );

        if (!cancel) {
          setStats(s);
        }

      } finally {

        if (!cancel) {
          setLoading(false);
        }

      }

    };


    run();

    const t =
      setInterval(
        run,
        5000
      );


    return () => {

      cancel = true;

      clearInterval(t);

    };

  }, [hours]);


  return {
    stats,
    loading,
  };
}


// =========================================================
// CAMERAS
// =========================================================

export function useCameras() {

  const [cameras, setCameras] =
    useState([]);

  const [loading, setLoading] =
    useState(true);


  const refresh =
    useCallback(async () => {

      try {

        const data =
          await api.cameras.list();

        setCameras(data);

      } finally {

        setLoading(false);

      }

    }, []);


  useEffect(() => {

    refresh();

  }, [refresh]);


  return {
    cameras,
    loading,
    refresh,
  };
}


// =========================================================
// ROIS
// =========================================================

export function useROIs(cameraId) {

  const [rois, setRois] =
    useState([]);

  const [loading, setLoading] =
    useState(true);


  const refresh =
    useCallback(async () => {

      setLoading(true);

      try {

        const data =
          await api.rois.list(
            cameraId
          );

        setRois(data);

      } finally {

        setLoading(false);

      }

    }, [cameraId]);


  useEffect(() => {

    refresh();

  }, [refresh]);


  const save =
    async (payload, id) => {

      if (id) {
        return api.rois.update(
          id,
          payload
        );
      }

      return api.rois.create(
        payload
      );
    };


  const remove =
    async (id) => {

      return api.rois.delete(id);

    };


  return {
    rois,
    loading,
    refresh,
    save,
    remove,
  };
}