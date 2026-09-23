from __future__ import annotations
from typing import Dict, List, Tuple
import numpy as np
import cv2

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None


class OccupancyEstimator:
    def __init__(
        self,
        interval_frames: int = 60,
        face_model_path: str = "yolov8n.pt",
    ) -> None:
        self.interval = interval_frames
        self._face_model = None
        if YOLO is not None:
            try:
                self._face_model = YOLO(face_model_path)
            except Exception:
                self._face_model = None
        self._cache: Dict[int, Tuple[int, int]] = {}
        self._last_frame: Dict[int, int] = {}

    def _estimate_face_count_heuristic(self, vehicle_crop: np.ndarray) -> int:
        h, w = vehicle_crop.shape[:2]
        win_top = int(h * 0.15)
        win_bottom = int(h * 0.55)
        win_crop = vehicle_crop[win_top:win_bottom, :]
        if win_crop.size == 0:
            return 0
        gray = cv2.cvtColor(win_crop, cv2.COLOR_BGR2GRAY) if len(win_crop.shape) == 3 else win_crop
        gray = cv2.equalizeHist(gray)
        skin_mask = cv2.inRange(
            cv2.cvtColor(win_crop, cv2.COLOR_BGR2YCrCb) if len(win_crop.shape) == 3 else win_crop,
            (0, 133, 77),
            (255, 173, 127),
        )
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        contours, _ = cv2.findContours(skin_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        min_area = (h * w) * 0.004
        max_area = (h * w) * 0.06
        count = 0
        for c in contours:
            a = cv2.contourArea(c)
            if min_area <= a <= max_area:
                count += 1
        return min(max(count, 0), 7)

    def process(
        self,
        frame: np.ndarray,
        detections,
        frame_id: int,
    ) -> Dict[int, int]:
        results: Dict[int, int] = {}
        h, w = frame.shape[:2]
        for det in detections:
            from edge_pipeline.utils.types import ObjectClass
            if not ObjectClass.is_vehicle(det.cls):
                continue
            tid = det.track_id or 0
            if tid in self._last_frame and (frame_id - self._last_frame[tid]) < self.interval:
                if tid in self._cache:
                    results[tid] = self._cache[tid][0]
                continue
            self._last_frame[tid] = frame_id
            x1, y1, x2, y2 = (
                max(0, int(det.xyxy[0])),
                max(0, int(det.xyxy[1])),
                min(w, int(det.xyxy[2])),
                min(h, int(det.xyxy[3])),
            )
            if x2 <= x1 or y2 <= y1:
                continue
            vehicle_crop = frame[y1:y2, x1:x2]
            count = 0
            if self._face_model is not None:
                try:
                    r = self._face_model.predict(
                        vehicle_crop, conf=0.25, classes=[0], imgsz=320, verbose=False,
                    )
                    if r and r[0].boxes is not None:
                        count = len(r[0].boxes)
                except Exception:
                    count = 0
            if count == 0:
                count = self._estimate_face_count_heuristic(vehicle_crop)
            self._cache[tid] = (count, frame_id)
            results[tid] = count
        return results
