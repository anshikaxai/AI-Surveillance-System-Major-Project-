from __future__ import annotations
from typing import Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query, Depends

from api_backend.core.db import db
from api_backend.models.schemas import (
    EventCreate,
    EventResponse,
    EventListResponse,
    EventAcknowledge,
)

router = APIRouter(prefix="/events", tags=["Events"])


@router.post("", response_model=EventResponse, status_code=201)
async def create_event(payload: EventCreate):
    try:
        with db.cursor() as cur:
            cur.execute(
                """
                INSERT INTO security_events
                    (event_id, event_type, camera_id, roi_name, track_ids,
                     explanation, metadata, severity, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s,
                        TO_TIMESTAMP(%s) AT TIME ZONE 'UTC')
                RETURNING id, event_id, event_type, camera_id, roi_name, track_ids,
                          explanation, metadata, severity, acknowledged,
                          acknowledged_by, acknowledged_at, timestamp, created_at
                """,
                (
                    payload.event_id,
                    payload.event_type,
                    payload.camera_id,
                    payload.roi_name,
                    list(payload.track_ids),
                    payload.explanation,
                    payload.metadata,
                    payload.severity,
                    payload.timestamp,
                ),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(500, "Failed to insert event")
            d = dict(row)
            for ts_field in ("timestamp", "created_at", "acknowledged_at"):
                if d.get(ts_field) is not None:
                    d[ts_field] = d[ts_field].timestamp() if hasattr(d[ts_field], "timestamp") else float(d[ts_field])
            return EventResponse(**d)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"DB error: {e}")


@router.get("", response_model=EventListResponse)
async def list_events(
    camera_id: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    roi_name: Optional[str] = Query(None),
    acknowledged: Optional[bool] = Query(None),
    hours: Optional[int] = Query(24, ge=1, le=24 * 30),
    limit: int = Query(200, ge=1, le=2000),
    offset: int = Query(0, ge=0),
):
    clauses = []
    params: list = []
    if camera_id:
        clauses.append("camera_id = %s")
        params.append(camera_id)
    if event_type:
        clauses.append("event_type = %s")
        params.append(event_type)
    if severity:
        clauses.append("severity = %s")
        params.append(severity)
    if roi_name:
        clauses.append("roi_name = %s")
        params.append(roi_name)
    if acknowledged is not None:
        clauses.append("acknowledged = %s")
        params.append(acknowledged)
    if hours:
        clauses.append(f"timestamp > NOW() - INTERVAL '%s hours'")
        params.append(hours)

    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    count_sql = f"SELECT COUNT(*) FROM security_events {where}"
    data_sql = f"""
        SELECT id, event_id, event_type, camera_id, roi_name, track_ids,
               explanation, metadata, severity, acknowledged, acknowledged_by,
               acknowledged_at, timestamp, created_at
        FROM security_events {where}
        ORDER BY timestamp DESC
        LIMIT %s OFFSET %s
    """
    try:
        total_row = db.fetchone(count_sql, tuple(params))
        total = int(list(total_row.values())[0]) if total_row else 0
        rows = db.fetchall(data_sql, tuple(params) + (limit, offset))
    except Exception as e:
        raise HTTPException(500, f"DB error: {e}")

    items = []
    for r in rows:
        d = dict(r)
        for ts_field in ("timestamp", "created_at", "acknowledged_at"):
            if d.get(ts_field) is not None:
                d[ts_field] = d[ts_field].timestamp() if hasattr(d[ts_field], "timestamp") else float(d[ts_field])
        items.append(EventResponse(**d))
    return EventListResponse(total=total, items=items)


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(event_id: str):
    row = db.fetchone(
        """SELECT id, event_id, event_type, camera_id, roi_name, track_ids,
                  explanation, metadata, severity, acknowledged, acknowledged_by,
                  acknowledged_at, timestamp, created_at
           FROM security_events WHERE event_id = %s""",
        (event_id,),
    )
    if not row:
        raise HTTPException(404, "Event not found")
    d = dict(row)
    for ts_field in ("timestamp", "created_at", "acknowledged_at"):
        if d.get(ts_field) is not None:
            d[ts_field] = d[ts_field].timestamp() if hasattr(d[ts_field], "timestamp") else float(d[ts_field])
    return EventResponse(**d)


@router.post("/{event_id}/acknowledge", response_model=EventResponse)
async def acknowledge_event(event_id: str, payload: EventAcknowledge):
    try:
        with db.cursor() as cur:
            cur.execute(
                """
                UPDATE security_events
                SET acknowledged = TRUE, acknowledged_by = %s, acknowledged_at = NOW()
                WHERE event_id = %s
                RETURNING id, event_id, event_type, camera_id, roi_name, track_ids,
                          explanation, metadata, severity, acknowledged,
                          acknowledged_by, acknowledged_at, timestamp, created_at
                """,
                (payload.acknowledged_by, event_id),
            )
            row = cur.fetchone()
    except Exception as e:
        raise HTTPException(500, f"DB error: {e}")
    if not row:
        raise HTTPException(404, "Event not found")
    d = dict(row)
    for ts_field in ("timestamp", "created_at", "acknowledged_at"):
        if d.get(ts_field) is not None:
            d[ts_field] = d[ts_field].timestamp() if hasattr(d[ts_field], "timestamp") else float(d[ts_field])
    return EventResponse(**d)


@router.get("/stats/summary")
async def event_stats(hours: int = Query(24, ge=1, le=24 * 30)):
    try:
        rows = db.fetchall(
            f"""
            SELECT event_type, severity, COUNT(*) AS cnt
            FROM security_events
            WHERE timestamp > NOW() - INTERVAL '%s hours'
            GROUP BY GROUPING SETS ((event_type), (severity))
            """,
            (hours,),
        )
        by_type = {}
        by_severity = {}
        for r in rows:
            d = dict(r)
            if d.get("event_type"):
                by_type[d["event_type"]] = d["cnt"]
            elif d.get("severity"):
                by_severity[d["severity"]] = d["cnt"]
        total = sum(by_type.values())
        return {"hours": hours, "total": total, "by_type": by_type, "by_severity": by_severity}
    except Exception as e:
        raise HTTPException(500, f"DB error: {e}")
