CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS cameras (
    id            VARCHAR(64) PRIMARY KEY,
    name          VARCHAR(255) NOT NULL,
    location      TEXT,
    stream_url    TEXT,
    status        VARCHAR(32) DEFAULT 'offline',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS rois (
    id            SERIAL PRIMARY KEY,
    camera_id     VARCHAR(64) NOT NULL REFERENCES cameras(id) ON DELETE CASCADE,
    name          VARCHAR(128) NOT NULL,
    polygon       JSONB NOT NULL,
    loitering_threshold_sec NUMERIC(10,2) NOT NULL DEFAULT 30.0,
    crowd_threshold INTEGER NOT NULL DEFAULT 5,
    color         VARCHAR(16) DEFAULT '#00ff00',
    active_hours  JSONB,
    enabled       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rois_camera ON rois(camera_id);

CREATE TABLE IF NOT EXISTS security_events (
    id            BIGSERIAL PRIMARY KEY,
    event_id      VARCHAR(32) NOT NULL UNIQUE,
    event_type    VARCHAR(64) NOT NULL,
    camera_id     VARCHAR(64) NOT NULL REFERENCES cameras(id) ON DELETE SET DEFAULT DEFAULT 'cam_001',
    roi_name      VARCHAR(128),
    track_ids     INTEGER[] DEFAULT '{}',
    explanation   TEXT,
    metadata      JSONB DEFAULT '{}'::jsonb,
    severity      VARCHAR(16) DEFAULT 'medium',
    acknowledged  BOOLEAN NOT NULL DEFAULT FALSE,
    acknowledged_by VARCHAR(128),
    acknowledged_at TIMESTAMPTZ,
    timestamp     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_events_type      ON security_events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_camera    ON security_events(camera_id);
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON security_events(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_events_severity  ON security_events(severity);
CREATE INDEX IF NOT EXISTS idx_events_roi       ON security_events(roi_name);
CREATE INDEX IF NOT EXISTS idx_events_metadata  ON security_events USING GIN (metadata jsonb_path_ops);

CREATE TABLE IF NOT EXISTS pipeline_config (
    id            SERIAL PRIMARY KEY,
    camera_id     VARCHAR(64) NOT NULL REFERENCES cameras(id) ON DELETE CASCADE UNIQUE,
    config        JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_by    VARCHAR(128),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS detection_snapshots (
    id            BIGSERIAL PRIMARY KEY,
    event_id      VARCHAR(32) REFERENCES security_events(event_id) ON DELETE CASCADE,
    frame_id      INTEGER,
    detections    JSONB DEFAULT '[]'::jsonb,
    image_path    TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO cameras (id, name, location, status)
VALUES ('cam_001', 'Main Gate Camera', 'Main Entrance', 'online')
ON CONFLICT (id) DO NOTHING;
