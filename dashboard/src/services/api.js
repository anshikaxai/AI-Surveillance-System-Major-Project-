import axios from 'axios';

const BASE = (
  import.meta.env.VITE_API_URL ||
  '/api/v1'
);

const http = axios.create({
  baseURL: BASE,
  timeout: 8000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const api = {

  // ---------------------------------------------
  // EVENTS
  // ---------------------------------------------
  events: {
    create: (payload) =>
      http
        .post('/events', payload)
        .then((r) => r.data),

    list: (params = {}) =>
      http
        .get('/events', { params })
        .then((r) => r.data),

    get: (id) =>
      http
        .get(`/events/${id}`)
        .then((r) => r.data),

    ack: (id, by) =>
      http
        .post(
          `/events/${id}/acknowledge`,
          {
            acknowledged_by: by,
          }
        )
        .then((r) => r.data),

    stats: (hours = 24) =>
      http
        .get('/events/stats/summary', {
          params: { hours },
        })
        .then((r) => r.data),
  },


  // ---------------------------------------------
  // CAMERAS
  // ---------------------------------------------
  cameras: {
    list: () =>
      http
        .get('/cameras')
        .then((r) => r.data),

    create: (p) =>
      http
        .post('/cameras', p)
        .then((r) => r.data),

    get: (id) =>
      http
        .get(`/cameras/${id}`)
        .then((r) => r.data),

    status: (id, status) =>
      http
        .put(
          `/cameras/${id}/status?status=${encodeURIComponent(
            status
          )}`
        )
        .then((r) => r.data),
  },


  // ---------------------------------------------
  // ROI
  // ---------------------------------------------
  rois: {
    list: (camera_id) =>
      http
        .get('/rois', {
          params: camera_id
            ? { camera_id }
            : {},
        })
        .then((r) => r.data),

    create: (p) =>
      http
        .post('/rois', p)
        .then((r) => r.data),

    update: (id, p) =>
      http
        .put(`/rois/${id}`, p)
        .then((r) => r.data),

    delete: (id) =>
      http.delete(`/rois/${id}`),
  },


  // ---------------------------------------------
  // NLP
  // ---------------------------------------------
  nlp: {
    parse: (
      command,
      camera_id = 'cam_001'
    ) =>
      http
        .post('/nlp/parse', {
          command,
          camera_id,
        })
        .then((r) => r.data),

    preview: (
      command,
      camera_id = 'cam_001'
    ) =>
      http
        .post('/nlp/parse-preview', {
          command,
          camera_id,
        })
        .then((r) => r.data),
  },


  // ---------------------------------------------
  // CONFIG
  // ---------------------------------------------
  config: {
    get: (camera_id) =>
      http
        .get(`/config/${camera_id}`)
        .then((r) => r.data),

    upsert: (payload) =>
      http
        .put('/config', payload)
        .then((r) => r.data),
  },


  // ---------------------------------------------
  // CCTV 2 HUMAN ACTIVITY ALERTS
  // IMPORTANT:
  // This endpoint is NOT under /api/v1,
  // so we use axios directly.
  // ---------------------------------------------
  cctv2: {
    alerts: () =>
      axios
        .get('/api/cctv2/alerts')
        .then((r) => r.data),
  },


  // ---------------------------------------------
  // HEALTH
  // ---------------------------------------------
  health: () =>
    axios
      .get('/health')
      .then((r) => r.data),
};

export default http;
