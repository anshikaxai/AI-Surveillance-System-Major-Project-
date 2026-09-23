from __future__ import annotations
from typing import List, Optional, Tuple
import numpy as np

try:
    from ultralytics import YOLO
    from ultralytics.engine.results import Results
except ImportError:
    YOLO = None
    Results = None

from edge_pipeline.utils.types import Detection, ObjectClass


class YOLODetector:
    def __init__(
        self,
        model_path: str = "yolov8s.pt",
        conf: float = 0.45,
        classes: Optional[List[int]] = None,
        imgsz: int = 640,
        device: str = "cpu",
    ) -> None:
        if YOLO is None:
            raise ImportError("ultralytics not installed. Run: pip install ultralytics")
        self.model = YOLO(model_path)
        self.conf = conf
        self.classes = classes if classes is not None else [
            ObjectClass.PERSON, ObjectClass.BICYCLE,
            ObjectClass.CAR, ObjectClass.MOTORCYCLE,
            ObjectClass.BUS, ObjectClass.TRUCK,
        ]
        self.imgsz = imgsz
        self.device = device

    def detect(self, frame: np.ndarray) -> List[Detection]:
        results: List[Results] = self.model.predict(
            source=frame,
            conf=self.conf,
            classes=self.classes,
            imgsz=self.imgsz,
            device=self.device,
            verbose=False,
        )
        detections: List[Detection] = []
        if not results:
            return detections
        r = results[0]
        if r.boxes is None:
            return detections
        boxes = r.boxes.xyxy.cpu().numpy() if hasattr(r.boxes.xyxy, "cpu") else np.array(r.boxes.xyxy)
        confs = r.boxes.conf.cpu().numpy() if hasattr(r.boxes.conf, "cpu") else np.array(r.boxes.conf)
        clss = r.boxes.cls.cpu().numpy() if hasattr(r.boxes.cls, "cpu") else np.array(r.boxes.cls)
        for box, conf, cls in zip(boxes, confs, clss):
            c = int(cls)
            if c not in self.classes:
                continue
            detections.append(Detection(
                xyxy=(float(box[0]), float(box[1]), float(box[2]), float(box[3])),
                cls=c,
                conf=float(conf),
            ))
        return detections
