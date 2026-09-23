from __future__ import annotations
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict
import time

from edge_pipeline.config.settings import ROIConfig
from edge_pipeline.utils.types import (
    Detection,
    TrackState,
    SecurityEvent,
    EventType,
    ObjectClass,
    PerceptionFrame,
    BehaviourLabel,
)
from edge_pipeline.utils.geometry import point_in_polygon, box_intersects_polygon


class EventIntelligenceLayer:
    def __init__(self, rois: List[ROIConfig], cooldown_sec: float = 15.0) -> None:
        self.rois = rois
        self.cooldown_sec = cooldown_sec
        self._last_event: Dict[Tuple[str, str], float] = {}
        self._roi_people_cache: Dict[str, Set[int]] = defaultdict(set)

    def _cooled_down(self, key: Tuple[str, str]) -> bool:
        now = time.time()
        last = self._last_event.get(key, 0.0)
        if now - last >= self.cooldown_sec:
            self._last_event[key] = now
            return True
        return False

    def _in_active_hours(self, roi: ROIConfig) -> bool:
        if roi.active_hours is None:
            return True
        start_h, end_h = roi.active_hours
        hour = time.localtime().tm_hour
        if start_h <= end_h:
            return start_h <= hour <= end_h
        return hour >= start_h or hour <= end_h

    def _people_in_roi(
        self,
        roi: ROIConfig,
        detections: List[Detection],
        tracks: Dict[int, TrackState],
    ) -> List[int]:
        ids: List[int] = []
        for d in detections:
            if not ObjectClass.is_person(d.cls) or d.track_id is None:
                continue
            if point_in_polygon(d.bottom_center, roi.polygon):
                ids.append(d.track_id)
        return ids

    def process_frame(
        self,
        pframe: PerceptionFrame,
        detections: List[Detection],
        tracks: Dict[int, TrackState],
        camera_id: str = "cam_001",
    ) -> List[SecurityEvent]:
        events: List[SecurityEvent] = []
        now = time.time()

        for roi in self.rois:
            if not self._in_active_hours(roi):
                continue
            person_tids = self._people_in_roi(roi, detections, tracks)
            person_set = set(person_tids)

            for tid in person_tids:
                st = tracks.get(tid)
                if not st:
                    continue
                if roi.name not in st.roi_entry_times:
                    st.roi_entry_times[roi.name] = now
                duration = now - st.roi_entry_times[roi.name]
                if duration >= roi.loitering_threshold_sec:
                    key = ("loitering", f"{roi.name}:{tid}")
                    if self._cooled_down(key):
                        events.append(SecurityEvent(
                            event_type=EventType.LOITERING,
                            camera_id=camera_id,
                            roi_name=roi.name,
                            track_ids=[tid],
                            explanation=(
                                f"Track #{tid} stayed in ROI '{roi.name}' for "
                                f"{duration:.1f}s (threshold {roi.loitering_threshold_sec}s)"
                            ),
                            metadata={
                                "duration_sec": round(duration, 2),
                                "threshold_sec": roi.loitering_threshold_sec,
                                "behaviour": st.behaviour.value,
                                "speed_px_s": round(st.speed_px_s, 1),
                            },
                            severity="high",
                        ))

            current_count = len(person_set)
            self._roi_people_cache[roi.name] = person_set
            if current_count >= roi.crowd_threshold:
                key = ("crowd", roi.name)
                if self._cooled_down(key):
                    events.append(SecurityEvent(
                        event_type=EventType.CROWD,
                        camera_id=camera_id,
                        roi_name=roi.name,
                        track_ids=list(person_tids),
                        explanation=(
                            f"{current_count} distinct persons in ROI '{roi.name}' "
                            f"(threshold {roi.crowd_threshold})"
                        ),
                        metadata={
                            "count": current_count,
                            "threshold": roi.crowd_threshold,
                        },
                        severity="medium",
                    ))

            for st in tracks.values():
                if not ObjectClass.is_person(st.cls):
                    continue
                if st.behaviour == BehaviourLabel.RUNNING:
                    key = ("behaviour", f"running:{st.track_id}")
                    if self._cooled_down(key):
                        inside_roi = point_in_polygon(
                            st.history[-1] if st.history else (0, 0), roi.polygon
                        )
                        if inside_roi:
                            events.append(SecurityEvent(
                                event_type=EventType.BEHAVIOUR_ALERT,
                                camera_id=camera_id,
                                roi_name=roi.name,
                                track_ids=[st.track_id],
                                explanation=f"Track #{st.track_id} is running in ROI '{roi.name}'",
                                metadata={
                                    "behaviour": st.behaviour.value,
                                    "speed_px_s": round(st.speed_px_s, 1),
                                },
                                severity="medium",
                            ))
        return events
