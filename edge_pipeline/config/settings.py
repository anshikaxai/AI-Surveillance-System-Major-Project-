from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
import json
import os


@dataclass
class ROIConfig:
    name: str
    polygon: List[Tuple[int, int]]
    loitering_threshold_sec: float = 30.0
    crowd_threshold: int = 5
    color: Tuple[int, int, int] = (0, 255, 0)
    active_hours: Optional[Tuple[int, int]] = None


@dataclass
class PipelineSettings:
    detection_model: str = "yolov8s.pt"
    tracking_type: str = "bytetrack"
    detection_confidence: float = 0.45
    detection_classes: List[int] = field(default_factory=lambda: [0, 1, 2, 3, 5, 7])
    track_buffer: int = 30
    frame_skip: int = 0
    imgsz: int = 640
    device: str = "cpu"

    behaviour_enabled: bool = True
    walking_speed_px_s: float = 80.0
    running_speed_px_s: float = 200.0
    behaviour_history_len: int = 10

    alpr_enabled: bool = True
    alpr_ocr_interval_frames: int = 30
    alpr_min_vehicle_area: int = 8000

    occupancy_enabled: bool = True
    occupancy_interval_frames: int = 60

    rois: List[ROIConfig] = field(default_factory=lambda: [
        ROIConfig(
            name="Main Gate",
            polygon=[(200, 100), (500, 100), (500, 400), (200, 400)],
            loitering_threshold_sec=20.0,
            crowd_threshold=8,
            color=(0, 0, 255),
        ),
        ROIConfig(
            name="Parking Zone",
            polygon=[(550, 200), (800, 200), (800, 450), (550, 450)],
            loitering_threshold_sec=45.0,
            crowd_threshold=3,
            color=(255, 0, 0),
        ),
    ])

    event_cooldown_sec: float = 15.0

    api_base_url: str = "http://localhost:8000"
    api_timeout_sec: float = 3.0
    api_retry_attempts: int = 3
    local_buffer_path: str = "logs/local_event_buffer.jsonl"
    local_buffer_max_entries: int = 5000

    @classmethod
    def load(cls, path: Optional[str] = None) -> "PipelineSettings":
        if path and os.path.exists(path):
            with open(path, "r") as f:
                data = json.load(f)
            rois = [ROIConfig(**r) for r in data.get("rois", [])]
            data["rois"] = rois
            return cls(**data)
        return cls()

    def save(self, path: str) -> None:
        data = self.__dict__.copy()
        data["rois"] = [r.__dict__ for r in self.rois]
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)
