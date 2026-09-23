from __future__ import annotations
from typing import Dict, Any
import json
import logging
from fastapi import APIRouter, HTTPException

from api_backend.core.db import db
from api_backend.core.nlp_parser import NLPConfigParser
from api_backend.models.schemas import (
    NLPCommandRequest,
    NLPCommandResponse,
    PipelineConfigUpdate,
)

logger = logging.getLogger("nlp_router")

router = APIRouter(prefix="/nlp", tags=["NLP to Action"])


def _apply_payload(payload: Dict[str, Any]) -> tuple[bool, list[str]]:
    warnings: list[str] = []
    applied = False
    roi_name = payload.get("roi_name")
    camera_id = payload.get("camera_id", "cam_001")
    try:
        row = db.fetchone(
            "SELECT id, polygon, loitering_threshold_sec, crowd_threshold, color, active_hours, enabled "
            "FROM rois WHERE camera_id = %s AND name = %s",
            (camera_id, roi_name),
        )
    except Exception as e:
        warnings.append(f"DB lookup failed: {e}")
        return False, warnings
    if not row:
        warnings.append(f"ROI '{roi_name}' for camera {camera_id} not found — creating default polygon")
        default_poly = [[200, 100], [500, 100], [500, 400], [200, 400]]
        try:
            with db.cursor() as cur:
                cur.execute(
                    """INSERT INTO rois (camera_id, name, polygon, loitering_threshold_sec,
                                         crowd_threshold, color, active_hours, enabled)
                       VALUES (%s, %s, %s::jsonb, %s, %s, %s, %s::jsonb, %s)
                       RETURNING id""",
                    (camera_id, roi_name, default_poly,
                     payload.get("loitering_threshold_sec") or 30.0,
                     payload.get("crowd_threshold") or 5,
                     "#00ff00", payload.get("active_hours"), payload.get("enable", True)),
                )
            applied = True
        except Exception as e:
            warnings.append(f"Failed to create ROI: {e}")
            return False, warnings
        return applied, warnings

    d = dict(row)
    updates = []
    params: list = []
    if payload.get("loitering_threshold_sec") is not None:
        updates.append("loitering_threshold_sec = %s")
        params.append(float(payload["loitering_threshold_sec"]))
    if payload.get("crowd_threshold") is not None:
        updates.append("crowd_threshold = %s")
        params.append(int(payload["crowd_threshold"]))
    if payload.get("active_hours") is not None:
        updates.append("active_hours = %s::jsonb")
        params.append(payload["active_hours"])
    if payload.get("enable") is not None:
        updates.append("enabled = %s")
        params.append(bool(payload["enable"]))
    if not updates:
        warnings.append("No configurable fields recognized")
        return False, warnings
    updates.append("updated_at = NOW()")
    params.append(d["id"])
    sql = f"UPDATE rois SET {', '.join(updates)} WHERE id = %s"
    try:
        with db.cursor() as cur:
            cur.execute(sql, tuple(params))
        applied = True
    except Exception as e:
        warnings.append(f"Update failed: {e}")
    return applied, warnings


@router.post("/parse", response_model=NLPCommandResponse)
async def parse_command(req: NLPCommandRequest):
    try:
        parsed = NLPConfigParser.parse(req.command, req.camera_id)
    except Exception as e:
        raise HTTPException(500, f"NLP parser error: {e}")
    warnings = list(parsed.get("warnings", []))
    applied = False
    if parsed["confidence"] >= 0.45:
        try:
            applied, extra_warn = _apply_payload(parsed["json_payload"])
            warnings.extend(extra_warn)
        except Exception as e:
            warnings.append(f"Apply failed: {e}")
    else:
        warnings.append(f"Confidence {parsed['confidence']:.2f} < 0.45 — skipping auto-apply")
    return NLPCommandResponse(
        raw_command=parsed["raw_command"],
        parsed_action=parsed["parsed_action"],
        json_payload=parsed["json_payload"],
        confidence=parsed["confidence"],
        explanation=parsed["explanation"],
        applied=applied,
        warnings=warnings,
    )


@router.post("/parse-preview", response_model=NLPCommandResponse)
async def parse_command_preview(req: NLPCommandRequest):
    try:
        parsed = NLPConfigParser.parse(req.command, req.camera_id)
    except Exception as e:
        raise HTTPException(500, f"NLP parser error: {e}")
    return NLPCommandResponse(
        raw_command=parsed["raw_command"],
        parsed_action=parsed["parsed_action"],
        json_payload=parsed["json_payload"],
        confidence=parsed["confidence"],
        explanation=parsed["explanation"],
        applied=False,
        warnings=list(parsed.get("warnings", [])),
    )


@router.post("/apply")
async def apply_parsed(camera_id: str, payload: dict):
    ok, warnings = _apply_payload({**payload, "camera_id": camera_id})
    return {"applied": ok, "warnings": warnings}


router_config = APIRouter(prefix="/config", tags=["Pipeline Config"])


@router_config.get("/{camera_id}")
async def get_pipeline_config(camera_id: str):
    row = db.fetchone(
        "SELECT camera_id, config, updated_by, updated_at FROM pipeline_config WHERE camera_id = %s",
        (camera_id,),
    )
    if not row:
        return {"camera_id": camera_id, "config": {}, "updated_by": None, "updated_at": None}
    d = dict(row)
    d["config"] = dict(d.get("config") or {})
    d["updated_at"] = d["updated_at"].timestamp() if d.get("updated_at") else None
    return d


@router_config.put("")
async def upsert_pipeline_config(payload: PipelineConfigUpdate):
    try:
        with db.cursor() as cur:
            cur.execute(
                """
                INSERT INTO pipeline_config (camera_id, config, updated_by, updated_at)
                VALUES (%s, %s::jsonb, %s, NOW())
                ON CONFLICT (camera_id) DO UPDATE SET
                    config = EXCLUDED.config,
                    updated_by = EXCLUDED.updated_by,
                    updated_at = NOW()
                RETURNING camera_id, config, updated_by, updated_at
                """,
                (payload.camera_id, payload.config, payload.updated_by),
            )
            row = cur.fetchone()
    except Exception as e:
        raise HTTPException(500, f"DB error: {e}")
    d = dict(row)
    d["config"] = dict(d.get("config") or {})
    d["updated_at"] = d["updated_at"].timestamp() if d.get("updated_at") else None
    return d
