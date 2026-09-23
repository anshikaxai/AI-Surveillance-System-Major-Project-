from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Any, Dict
from enum import Enum
import time
import uuid
import json


class ObjectClass(int, Enum):
    PERSON = 0
    BICYCLE = 1
    CAR = 2
    MOTORCYCLE = 3
    BUS = 5
    TRUCK = 7

    @classmethod
    def is_vehicle(cls, c: int) -> bool:
        return c in (cls.CAR, cls.MOTORCYCLE, cls.BUS, cls.TRUCK)

    @classmethod
    def is_person(cls, c: int) -> bool:
        return c == cls.PERSON


class BehaviourLabel(str, Enum):
    STANDING = "standing"
    WALKING = "walking"
    RUNNING = "running"
    UNKNOWN = "unknown"


class EventType(str, Enum):
    LOITERING = "loitering"
    CROWD = "crowd"
    VEHICLE_DETECTED = "vehicle_detected"
    ALPR_RESULT = "alpr_result"
    OCCUPANCY_ESTIMATE = "occupancy_estimate"
    BEHAVIOUR_ALERT = "behaviour_alert"
    SYSTEM_HEARTBEAT = "system_heartbeat"


@dataclass
class Detection:
    xyxy: Tuple[float, float, float, float]
    cls: int
    conf: float
    track_id: Optional[int] = None

    @property
    def center(self) -> Tuple[float, float]:
        x1, y1, x2, y2 = self.xyxy
        return ((x1 + x2) / 2, (y1 + y2) / 2)

    @property
    def bottom_center(self) -> Tuple[float, float]:
        x1, y1, x2, y2 = self.xyxy
        return ((x1 + x2) / 2, y2)

    @property
    def area(self) -> float:
        x1, y1, x2, y2 = self.xyxy
        return max(0, x2 - x1) * max(0, y2 - y1)

    @property
    def width(self) -> float:
        x1, _, x2, _ = self.xyxy
        return x2 - x1

    @property
    def height(self) -> float:
        _, y1, _, y2 = self.xyxy
        return y2 - y1


@dataclass
class TrackState:
    track_id: int
    cls: int
    history: List[Tuple[float, float]] = field(default_factory=list)
    first_seen: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    roi_entry_times: Dict[str, float] = field(default_factory=dict)
    behaviour: BehaviourLabel = BehaviourLabel.UNKNOWN
    speed_px_s: float = 0.0

    def update(self, detection: Detection, timestamp: Optional[float] = None) -> None:
        ts = timestamp or time.time()
        self.last_seen = ts
        self.history.append(detection.bottom_center)
        if len(self.history) > 60:
            self.history.pop(0)

    def compute_speed(self, fps: float = 10.0) -> float:
        if len(self.history) < 2:
            self.speed_px_s = 0.0
            return 0.0
        p1 = self.history[-1]
        p2 = self.history[-min(len(self.history), 5)]
        dx = p1[0] - p2[0]
        dy = p1[1] - p2[1]
        dist = (dx * dx + dy * dy) ** 0.5
        dt = max(1e-6, min(len(self.history) - 1, 5) / max(fps, 1e-6))
        self.speed_px_s = dist / dt
        return self.speed_px_s


@dataclass
class PerceptionFrame:
    frame_id: int
    timestamp: float
    detections: List[Detection]
    fps: float
    width: int
    height: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "frame_id": self.frame_id,
            "timestamp": self.timestamp,
            "fps": self.fps,
            "width": self.width,
            "height": self.height,
            "detections": [
                {
                    "xyxy": list(d.xyxy),
                    "cls": d.cls,
                    "conf": d.conf,
                    "track_id": d.track_id,
                }
                for d in self.detections
            ],
        }


@dataclass
class SecurityEvent:
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    event_type: EventType = EventType.LOITERING
    timestamp: float = field(default_factory=time.time)
    camera_id: str = "cam_001"
    roi_name: Optional[str] = None
    track_ids: List[int] = field(default_factory=list)
    explanation: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    severity: str = "medium"

    def to_json(self) -> str:
        return json.dumps(self.__dict__, default=str)

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__.copy()
