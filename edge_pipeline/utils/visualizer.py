from __future__ import annotations
from typing import Dict, List, Optional, Tuple
import numpy as np
import cv2

from edge_pipeline.config.settings import ROIConfig
from edge_pipeline.utils.types import Detection, TrackState, BehaviourLabel, SecurityEvent, EventType
from edge_pipeline.utils.geometry import point_in_polygon


COLORS = [
    (255, 0, 0), (0, 255, 0), (0, 0, 255),
    (255, 255, 0), (255, 0, 255), (0, 255, 255),
    (128, 0, 255), (255, 128, 0), (0, 128, 255),
]

LABEL_COLORS = {
    BehaviourLabel.STANDING: (0, 200, 0),
    BehaviourLabel.WALKING: (0, 165, 255),
    BehaviourLabel.RUNNING: (0, 0, 255),
    BehaviourLabel.UNKNOWN: (128, 128, 128),
}


class FrameAnnotator:
    def __init__(self, rois: List[ROIConfig]) -> None:
        self.rois = rois

    def _track_color(self, track_id: int) -> Tuple[int, int, int]:
        return COLORS[int(track_id) % len(COLORS)]

    def draw(
        self,
        frame: np.ndarray,
        detections: List[Detection],
        tracks: Dict[int, TrackState],
        fps: float,
        alpr_results: Optional[Dict[int, str]] = None,
        occupancy_results: Optional[Dict[int, int]] = None,
        events: Optional[List[SecurityEvent]] = None,
    ) -> np.ndarray:
        out = frame.copy()
        h, w = out.shape[:2]
        alpr_results = alpr_results or {}
        occupancy_results = occupancy_results or {}
        events = events or []

        for roi in self.rois:
            pts = np.array(roi.polygon, dtype=np.int32)
            cv2.polylines(out, [pts], True, roi.color, 2)
            label = f"{roi.name} | Loiter:{roi.loitering_threshold_sec}s | Crowd:{roi.crowd_threshold}"
            top_left = pts[pts[:, 1].argmin()]
            cv2.putText(
                out, label,
                (int(top_left[0]), int(top_left[1]) - 8),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, roi.color, 1,
            )

        for d in detections:
            tid = d.track_id or 0
            color = self._track_color(tid)
            x1, y1, x2, y2 = [int(v) for v in d.xyxy]
            cv2.rectangle(out, (x1, y1), (x2, y2), color, 2)
            cls_name = d.cls
            track = tracks.get(tid)
            label = f"#{tid} cls={cls_name} ({d.conf:.2f})"
            if track and track.behaviour != BehaviourLabel.UNKNOWN:
                bcol = LABEL_COLORS[track.behaviour]
                label += f" {track.behaviour.value}"
                if track.speed_px_s:
                    label += f" {track.speed_px_s:.0f}px/s"
            else:
                bcol = color
            cv2.putText(out, label, (x1, y1 - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.5, bcol, 2)

            if track and track.behaviour != BehaviourLabel.UNKNOWN:
                bcol = LABEL_COLORS[track.behaviour]
                badge_y = y1 - 28
                cv2.rectangle(out, (x1, badge_y), (x1 + 110, badge_y + 18), bcol, -1)
                cv2.putText(out, track.behaviour.value.upper(), (x1 + 4, badge_y + 13),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            plate = alpr_results.get(tid)
            if plate:
                py = y2 + 20
                cv2.putText(out, f"LP: {plate}", (x1, py),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

            occ = occupancy_results.get(tid)
            if occ is not None:
                oy = y2 + 42 if plate else y2 + 20
                cv2.putText(out, f"Occ: {occ}", (x1, oy),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

            if track and len(track.history) > 2:
                pts = np.array([[int(p[0]), int(p[1])] for p in track.history[-20:]], dtype=np.int32)
                cv2.polylines(out, [pts], False, color, 2)

        hud_lines = [
            f"FPS: {fps:.1f}",
            f"Tracks: {len(tracks)}",
            f"Detections: {len(detections)}",
        ]
        for i, line in enumerate(hud_lines):
            cv2.putText(out, line, (10, 24 + i * 22),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        y_off = 24
        for ev in events[-5:]:
            text = f"ALERT [{ev.event_type.value}]: {ev.roi_name or ''} {ev.explanation[:60]}"
            cv2.putText(out, text, (10, h - 24 - y_off),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 2)
            y_off += 22
        return out
