from __future__ import annotations
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query

from api_backend.core.db import db
from api_backend.models.schemas import ROICreate, ROIResponse

router = APIRouter(prefix="/rois", tags=["ROIs"])


@router.get("", response_model=List[ROIResponse])
async def list_rois(camera_id: Optional[str] = Query(None)):
    sql = """SELECT id, camera_id, name, polygon, loitering_threshold_sec,
                    crowd_threshold, color, active_hours, enabled,
                    created_at, updated_at FROM rois"""
    params: tuple = ()
    if camera_id:
        sql += " WHERE camera_id = %s"
        params = (camera_id,)
    sql += " ORDER BY id"
    try:
        rows = db.fetchall(sql, params)
    except Exception as e:
        raise HTTPException(500, f"DB error: {e}")
    out = []
    for r in rows:
        d = dict(r)
        d["polygon"] = list(d.get("polygon") or [])
        d["active_hours"] = list(d.get("active_hours")) if d.get("active_hours") else None
        d["loitering_threshold_sec"] = float(d["loitering_threshold_sec"])
        d["created_at"] = d["created_at"].timestamp()
        d["updated_at"] = d["updated_at"].timestamp()
        out.append(ROIResponse(**d))
    return out


@router.post("", response_model=ROIResponse, status_code=201)
async def create_roi(payload: ROICreate):
    try:
        with db.cursor() as cur:
            cur.execute(
                """
                INSERT INTO rois (camera_id, name, polygon, loitering_threshold_sec,
                                  crowd_threshold, color, active_hours, enabled)
                VALUES (%s, %s, %s::jsonb, %s, %s, %s, %s::jsonb, %s)
                RETURNING id, camera_id, name, polygon, loitering_threshold_sec,
                          crowd_threshold, color, active_hours, enabled,
                          created_at, updated_at
                """,
                (
                    payload.camera_id, payload.name, payload.polygon,
                    payload.loitering_threshold_sec, payload.crowd_threshold,
                    payload.color, payload.active_hours, payload.enabled,
                ),
            )
            row = cur.fetchone()
    except Exception as e:
        raise HTTPException(500, f"DB error: {e}")
    if not row:
        raise HTTPException(500, "Insert failed")
    d = dict(row)
    d["polygon"] = list(d.get("polygon") or [])
    d["active_hours"] = list(d.get("active_hours")) if d.get("active_hours") else None
    d["loitering_threshold_sec"] = float(d["loitering_threshold_sec"])
    d["created_at"] = d["created_at"].timestamp()
    d["updated_at"] = d["updated_at"].timestamp()
    return ROIResponse(**d)


@router.put("/{roi_id}", response_model=ROIResponse)
async def update_roi(roi_id: int, payload: ROICreate):
    try:
        with db.cursor() as cur:
            cur.execute(
                """
                UPDATE rois SET
                    camera_id = %s, name = %s, polygon = %s::jsonb,
                    loitering_threshold_sec = %s, crowd_threshold = %s,
                    color = %s, active_hours = %s::jsonb, enabled = %s,
                    updated_at = NOW()
                WHERE id = %s
                RETURNING id, camera_id, name, polygon, loitering_threshold_sec,
                          crowd_threshold, color, active_hours, enabled,
                          created_at, updated_at
                """,
                (
                    payload.camera_id, payload.name, payload.polygon,
                    payload.loitering_threshold_sec, payload.crowd_threshold,
                    payload.color, payload.active_hours, payload.enabled,
                    roi_id,
                ),
            )
            row = cur.fetchone()
    except Exception as e:
        raise HTTPException(500, f"DB error: {e}")
    if not row:
        raise HTTPException(404, "ROI not found")
    d = dict(row)
    d["polygon"] = list(d.get("polygon") or [])
    d["active_hours"] = list(d.get("active_hours")) if d.get("active_hours") else None
    d["loitering_threshold_sec"] = float(d["loitering_threshold_sec"])
    d["created_at"] = d["created_at"].timestamp()
    d["updated_at"] = d["updated_at"].timestamp()
    return ROIResponse(**d)


@router.delete("/{roi_id}", status_code=204)
async def delete_roi(roi_id: int):
    try:
        with db.cursor() as cur:
            cur.execute("DELETE FROM rois WHERE id = %s RETURNING id", (roi_id,))
            row = cur.fetchone()
    except Exception as e:
        raise HTTPException(500, f"DB error: {e}")
    if not row:
        raise HTTPException(404, "ROI not found")
    return None
