from __future__ import annotations

from typing import Optional

from fastapi import (
    APIRouter,
    HTTPException,
    Query,
)

from api_backend.core.db import db

from api_backend.models.schemas import (
    EventCreate,
    EventResponse,
    EventListResponse,
    EventAcknowledge,
)


router = APIRouter(
    prefix="/events",
    tags=["Events"],
)


# =========================================================
# HELPERS
# =========================================================

def serialize_event_row(row):

    if not row:
        return None

    data = dict(row)

    for field in (
        "timestamp",
        "created_at",
        "acknowledged_at",
    ):

        value = data.get(field)

        if value is not None:

            if hasattr(
                value,
                "timestamp",
            ):

                data[field] = (
                    value.timestamp()
                )

            else:

                data[field] = float(
                    value
                )

    return data


# =========================================================
# CREATE EVENT
# =========================================================

@router.post(
    "",
    response_model=EventResponse,
    status_code=201,
)
async def create_event(
    payload: EventCreate,
):

    try:

        with db.cursor() as cur:

            cur.execute(
                """
                INSERT INTO security_events
                (
                    event_id,
                    event_type,
                    camera_id,
                    roi_name,
                    track_ids,
                    explanation,
                    metadata,
                    severity,
                    timestamp
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    TO_TIMESTAMP(%s)
                )
                RETURNING
                    id,
                    event_id,
                    event_type,
                    camera_id,
                    roi_name,
                    track_ids,
                    explanation,
                    metadata,
                    severity,
                    acknowledged,
                    acknowledged_by,
                    acknowledged_at,
                    timestamp,
                    created_at
                """,
                (
                    payload.event_id,
                    payload.event_type,
                    payload.camera_id,
                    payload.roi_name,
                    list(
                        payload.track_ids
                    ),
                    payload.explanation,
                    payload.metadata,
                    payload.severity,
                    payload.timestamp,
                ),
            )


            row = cur.fetchone()


            if not row:

                raise HTTPException(
                    status_code=500,
                    detail=(
                        "Failed to insert event"
                    ),
                )


            data = (
                serialize_event_row(
                    row
                )
            )


            return EventResponse(
                **data
            )


    except HTTPException:

        raise


    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"DB error: {e}",
        )


# =========================================================
# LIST EVENTS
# =========================================================

@router.get(
    "",
    response_model=EventListResponse,
)
async def list_events(

    camera_id: Optional[str] = Query(
        None
    ),

    event_type: Optional[str] = Query(
        None
    ),

    severity: Optional[str] = Query(
        None
    ),

    roi_name: Optional[str] = Query(
        None
    ),

    acknowledged: Optional[bool] = Query(
        None
    ),

    hours: Optional[int] = Query(
        24,
        ge=1,
        le=24 * 30,
    ),

    limit: int = Query(
        200,
        ge=1,
        le=2000,
    ),

    offset: int = Query(
        0,
        ge=0,
    ),

):

    clauses = []

    params = []


    if camera_id:

        clauses.append(
            "camera_id = %s"
        )

        params.append(
            camera_id
        )


    if event_type:

        clauses.append(
            "event_type = %s"
        )

        params.append(
            event_type
        )


    if severity:

        clauses.append(
            "severity = %s"
        )

        params.append(
            severity
        )


    if roi_name:

        clauses.append(
            "roi_name = %s"
        )

        params.append(
            roi_name
        )


    if acknowledged is not None:

        clauses.append(
            "acknowledged = %s"
        )

        params.append(
            acknowledged
        )


    if hours:

        clauses.append(
            """
            timestamp >
            NOW() - (%s * INTERVAL '1 hour')
            """
        )

        params.append(
            hours
        )


    where = (
        "WHERE "
        +
        " AND ".join(
            clauses
        )
        if clauses
        else ""
    )


    count_sql = f"""
        SELECT
            COUNT(*) AS total
        FROM security_events
        {where}
    """


    data_sql = f"""
        SELECT
            id,
            event_id,
            event_type,
            camera_id,
            roi_name,
            track_ids,
            explanation,
            metadata,
            severity,
            acknowledged,
            acknowledged_by,
            acknowledged_at,
            timestamp,
            created_at
        FROM security_events
        {where}
        ORDER BY timestamp DESC
        LIMIT %s
        OFFSET %s
    """


    try:

        total_row = db.fetchone(
            count_sql,
            tuple(params),
        )


        total = (
            int(
                total_row.get(
                    "total",
                    0,
                )
            )
            if total_row
            else 0
        )


        rows = db.fetchall(
            data_sql,
            tuple(params)
            +
            (
                limit,
                offset,
            ),
        )


    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"DB error: {e}",
        )


    items = []


    for row in rows:

        data = serialize_event_row(
            row
        )

        items.append(
            EventResponse(
                **data
            )
        )


    return EventListResponse(
        total=total,
        items=items,
    )


# =========================================================
# STATS
#
# IMPORTANT:
# Keep this BEFORE /{event_id}
# =========================================================

@router.get(
    "/stats/summary"
)
async def event_stats(

    hours: int = Query(
        24,
        ge=1,
        le=24 * 30,
    ),

):

    try:

        type_rows = db.fetchall(
            """
            SELECT
                event_type,
                COUNT(*) AS cnt
            FROM security_events
            WHERE
                timestamp >
                NOW() - (
                    %s * INTERVAL '1 hour'
                )
            GROUP BY event_type
            ORDER BY cnt DESC
            """,
            (
                hours,
            ),
        )


        severity_rows = db.fetchall(
            """
            SELECT
                severity,
                COUNT(*) AS cnt
            FROM security_events
            WHERE
                timestamp >
                NOW() - (
                    %s * INTERVAL '1 hour'
                )
            GROUP BY severity
            ORDER BY cnt DESC
            """,
            (
                hours,
            ),
        )


        total_row = db.fetchone(
            """
            SELECT
                COUNT(*) AS total
            FROM security_events
            WHERE
                timestamp >
                NOW() - (
                    %s * INTERVAL '1 hour'
                )
            """,
            (
                hours,
            ),
        )


        by_type = {
            row["event_type"]:
                int(row["cnt"])
            for row in type_rows
            if row.get(
                "event_type"
            )
        }


        by_severity = {
            row["severity"]:
                int(row["cnt"])
            for row in severity_rows
            if row.get(
                "severity"
            )
        }


        total = (
            int(
                total_row.get(
                    "total",
                    0,
                )
            )
            if total_row
            else 0
        )


        return {
            "hours": hours,
            "total": total,
            "by_type": by_type,
            "by_severity": (
                by_severity
            ),
        }


    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"DB error: {e}",
        )


# =========================================================
# GET ONE EVENT
# =========================================================

@router.get(
    "/{event_id}",
    response_model=EventResponse,
)
async def get_event(
    event_id: str,
):

    try:

        row = db.fetchone(
            """
            SELECT
                id,
                event_id,
                event_type,
                camera_id,
                roi_name,
                track_ids,
                explanation,
                metadata,
                severity,
                acknowledged,
                acknowledged_by,
                acknowledged_at,
                timestamp,
                created_at
            FROM security_events
            WHERE event_id = %s
            """,
            (
                event_id,
            ),
        )


    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"DB error: {e}",
        )


    if not row:

        raise HTTPException(
            status_code=404,
            detail="Event not found",
        )


    data = serialize_event_row(
        row
    )


    return EventResponse(
        **data
    )


# =========================================================
# ACKNOWLEDGE EVENT
# =========================================================

@router.post(
    "/{event_id}/acknowledge",
    response_model=EventResponse,
)
async def acknowledge_event(
    event_id: str,
    payload: EventAcknowledge,
):

    try:

        with db.cursor() as cur:

            cur.execute(
                """
                UPDATE security_events
                SET
                    acknowledged = TRUE,
                    acknowledged_by = %s,
                    acknowledged_at = NOW()
                WHERE event_id = %s
                RETURNING
                    id,
                    event_id,
                    event_type,
                    camera_id,
                    roi_name,
                    track_ids,
                    explanation,
                    metadata,
                    severity,
                    acknowledged,
                    acknowledged_by,
                    acknowledged_at,
                    timestamp,
                    created_at
                """,
                (
                    payload.acknowledged_by,
                    event_id,
                ),
            )


            row = cur.fetchone()


    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"DB error: {e}",
        )


    if not row:

        raise HTTPException(
            status_code=404,
            detail="Event not found",
        )


    data = serialize_event_row(
        row
    )


    return EventResponse(
        **data
    )