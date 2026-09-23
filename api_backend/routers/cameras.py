from __future__ import annotations
from typing import List
from fastapi import APIRouter, HTTPException

from api_backend.core.db import db
from api_backend.models.schemas import CameraCreate, CameraResponse

router = APIRouter(prefix="/cameras", tags=["Cameras"])


@router.get("", response_model=List[CameraResponse])
async def list_cameras():
    try:
        rows = db.fetchall(
            """SELECT id, name, location, stream_url, status, created_at, updated_at
               FROM cameras ORDER BY id"""
        )
    except Exception as e:
        raise HTTPException(500, f"DB error: {e}")
    out = []
    for r in rows:
        d = dict(r)
        d["created_at"] = d["created_at"].timestamp()
        d["updated_at"] = d["updated_at"].timestamp()
        out.append(CameraResponse(**d))
    return out


@router.post("", response_model=CameraResponse, status_code=201)
async def create_camera(payload: CameraCreate):
    try:
        with db.cursor() as cur:
            cur.execute(
                """
                INSERT INTO cameras (id, name, location, stream_url, status)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    location = EXCLUDED.location,
                    stream_url = EXCLUDED.stream_url,
                    status = EXCLUDED.status,
                    updated_at = NOW()
                RETURNING id, name, location, stream_url, status, created_at, updated_at
                """,
                (payload.id, payload.name, payload.location, payload.stream_url, payload.status),
            )
            row = cur.fetchone()
    except Exception as e:
        raise HTTPException(500, f"DB error: {e}")
    if not row:
        raise HTTPException(500, "Insert failed")
    d = dict(row)
    d["created_at"] = d["created_at"].timestamp()
    d["updated_at"] = d["updated_at"].timestamp()
    return CameraResponse(**d)


@router.get("/{camera_id}", response_model=CameraResponse)
async def get_camera(camera_id: str):
    row = db.fetchone(
        """SELECT id, name, location, stream_url, status, created_at, updated_at
           FROM cameras WHERE id = %s""",
        (camera_id,),
    )
    if not row:
        raise HTTPException(404, "Camera not found")
    d = dict(row)
    d["created_at"] = d["created_at"].timestamp()
    d["updated_at"] = d["updated_at"].timestamp()
    return CameraResponse(**d)


@router.put("/{camera_id}/status")
async def set_status(camera_id: str, status: str):
    try:
        with db.cursor() as cur:
            cur.execute(
                """UPDATE cameras SET status = %s, updated_at = NOW()
                   WHERE id = %s RETURNING id, status""",
                (status, camera_id),
            )
            row = cur.fetchone()
    except Exception as e:
        raise HTTPException(500, f"DB error: {e}")
    if not row:
        raise HTTPException(404, "Camera not found")
    return dict(row)
