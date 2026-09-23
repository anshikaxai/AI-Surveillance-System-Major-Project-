from __future__ import annotations
from typing import Dict, Optional, Tuple
import time
import numpy as np
import cv2

try:
    import easyocr
except ImportError:
    easyocr = None

from edge_pipeline.utils.types import Detection, ObjectClass
from edge_pipeline.utils.geometry import crop_box


class ALPR:
    def __init__(
        self,
        languages: Tuple[str, ...] = ("en",),
        ocr_interval_frames: int = 30,
        min_vehicle_area: int = 8000,
        use_gpu: bool = False,
    ) -> None:
        if easyocr is None:
            raise ImportError("easyocr not installed. Run: pip install easyocr")
        self.reader = easyocr.Reader(list(languages), gpu=use_gpu, verbose=False)
        self.ocr_interval = ocr_interval_frames
        self.min_vehicle_area = min_vehicle_area
        self._last_ocr_frame: Dict[int, int] = {}
        self._plate_cache: Dict[int, Tuple[str, float]] = {}

    @staticmethod
    def _preprocess_plate(crop: np.ndarray) -> np.ndarray:
        if crop.size == 0:
            return crop
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) if len(crop.shape) == 3 else crop
        gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return thresh

    @staticmethod
    def _validate_plate(text: str) -> Optional[str]:
        t = "".join(c for c in text.upper() if c.isalnum())
        if 4 <= len(t) <= 12:
            return t
        return None

    def process(
        self,
        frame: np.ndarray,
        detections,
        frame_id: int,
    ) -> Dict[int, str]:
        results: Dict[int, str] = {}
        h, w = frame.shape[:2]
        for det in detections:
            if not ObjectClass.is_vehicle(det.cls):
                continue
            if det.area < self.min_vehicle_area:
                continue
            tid = det.track_id or 0
            if tid in self._last_ocr_frame and (frame_id - self._last_ocr_frame[tid]) < self.ocr_interval:
                if tid in self._plate_cache:
                    results[tid] = self._plate_cache[tid][0]
                continue
            self._last_ocr_frame[tid] = frame_id
            x1, y1, x2, y2 = crop_box(det.xyxy, w, h, pad_ratio=0.02)
            if x2 <= x1 or y2 <= y1:
                continue
            vehicle_crop = frame[y1:y2, x1:x2]
            plate_region_y = int(vehicle_crop.shape[0] * 0.55)
            plate_h = int(vehicle_crop.shape[0] * 0.35)
            plate_region = vehicle_crop[plate_region_y:plate_region_y + plate_h, :]
            if plate_region.size == 0:
                continue
            processed = self._preprocess_plate(plate_region)
            try:
                ocr_raw = self.reader.readtext(processed, detail=0, allowlist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
            except Exception:
                ocr_raw = []
            best_plate: Optional[str] = None
            for raw in ocr_raw:
                validated = self._validate_plate(raw)
                if validated:
                    best_plate = validated
                    break
            if best_plate:
                self._plate_cache[tid] = (best_plate, time.time())
                results[tid] = best_plate
            elif tid in self._plate_cache:
                results[tid] = self._plate_cache[tid][0]
        return results
