from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional
import sys
import os
import time
import argparse
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
import numpy as np

from edge_pipeline.config.settings import PipelineSettings
from edge_pipeline.perception.detector import YOLODetector
from edge_pipeline.perception.tracker import ByteTracker
from edge_pipeline.domain.behaviour import BehaviourClassifier
from edge_pipeline.domain.alpr import ALPR
from edge_pipeline.domain.occupancy import OccupancyEstimator
from edge_pipeline.intelligence.event_engine import EventIntelligenceLayer
from edge_pipeline.utils.api_client import BufferedAPIClient
from edge_pipeline.utils.visualizer import FrameAnnotator
from edge_pipeline.utils.types import PerceptionFrame, SecurityEvent, EventType


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/pipeline.log"),
    ],
)
os.makedirs("logs", exist_ok=True)


@dataclass
class PipelineStats:
    frames_processed: int = 0
    detection_time_ms: float = 0.0
    tracking_time_ms: float = 0.0
    domain_time_ms: float = 0.0
    event_time_ms: float = 0.0
    events_emitted: int = 0


class SurveillancePipeline:
    def __init__(self, settings: Optional[PipelineSettings] = None) -> None:
        self.settings = settings or PipelineSettings()
        self.logger = logging.getLogger("SurveillancePipeline")
        self.stats = PipelineStats()

        self.detector = YOLODetector(
            model_path=self.settings.detection_model,
            conf=self.settings.detection_confidence,
            classes=self.settings.detection_classes,
            imgsz=self.settings.imgsz,
            device=self.settings.device,
        )
        self.tracker = ByteTracker(track_buffer=self.settings.track_buffer)
        self.behaviour = BehaviourClassifier(
            walking_threshold=self.settings.walking_speed_px_s,
            running_threshold=self.settings.running_speed_px_s,
            history_len=self.settings.behaviour_history_len,
        )
        self.alpr: Optional[ALPR] = None
        if self.settings.alpr_enabled:
            try:
                self.alpr = ALPR(
                    ocr_interval_frames=self.settings.alpr_ocr_interval_frames,
                    min_vehicle_area=self.settings.alpr_min_vehicle_area,
                )
            except Exception as e:
                self.logger.warning(f"ALPR disabled (init failed): {e}")
        self.occupancy: Optional[OccupancyEstimator] = None
        if self.settings.occupancy_enabled:
            try:
                self.occupancy = OccupancyEstimator(
                    interval_frames=self.settings.occupancy_interval_frames,
                )
            except Exception as e:
                self.logger.warning(f"Occupancy disabled (init failed): {e}")

        self.event_engine = EventIntelligenceLayer(
            rois=self.settings.rois,
            cooldown_sec=self.settings.event_cooldown_sec,
        )
        self.annotator = FrameAnnotator(rois=self.settings.rois)
        self.api_client = BufferedAPIClient(
            base_url=self.settings.api_base_url,
            timeout_sec=self.settings.api_timeout_sec,
            retry_attempts=self.settings.api_retry_attempts,
            buffer_path=self.settings.local_buffer_path,
            buffer_max=self.settings.local_buffer_max_entries,
        )
        self._last_hb = 0.0

    def _send_heartbeat(self, fps: float) -> None:
        now = time.time()
        if now - self._last_hb < 30.0:
            return
        self._last_hb = now
        self.api_client.send_event(SecurityEvent(
            event_type=EventType.SYSTEM_HEARTBEAT,
            explanation=f"Pipeline OK | fps={fps:.1f} | processed={self.stats.frames_processed}",
            metadata={
                "fps": round(fps, 2),
                "frames_processed": self.stats.frames_processed,
            },
            severity="info",
        ))

    def process_frame(self, frame: np.ndarray, frame_id: int, fps: float) -> tuple[np.ndarray, List[SecurityEvent]]:
        h, w = frame.shape[:2]
        ts = time.time()

        t0 = time.perf_counter()
        if self.settings.frame_skip > 0 and frame_id % (self.settings.frame_skip + 1) != 0:
            detections = []
        else:
            detections = self.detector.detect(frame)
        self.stats.detection_time_ms += (time.perf_counter() - t0) * 1000

        t1 = time.perf_counter()
        detections = self.tracker.update(detections, fps=fps)
        tracks = self.tracker.all_states()
        self.stats.tracking_time_ms += (time.perf_counter() - t1) * 1000

        t2 = time.perf_counter()
        for st in tracks.values():
            self.behaviour.classify(st, fps=fps)
        alpr_out = {}
        occ_out = {}
        if self.alpr is not None:
            alpr_out = self.alpr.process(frame, detections, frame_id)
        if self.occupancy is not None:
            occ_out = self.occupancy.process(frame, detections, frame_id)
        self.stats.domain_time_ms += (time.perf_counter() - t2) * 1000

        pframe = PerceptionFrame(
            frame_id=frame_id, timestamp=ts,
            detections=detections, fps=fps, width=w, height=h,
        )
        t3 = time.perf_counter()
        events = self.event_engine.process_frame(pframe, detections, tracks)
        for tid, plate in alpr_out.items():
            events.append(SecurityEvent(
                event_type=EventType.ALPR_RESULT,
                camera_id="cam_001",
                track_ids=[tid] if tid else [],
                explanation=f"License plate recognized: {plate}",
                metadata={"plate": plate, "track_id": tid},
                severity="info",
            ))
        for tid, occ in occ_out.items():
            events.append(SecurityEvent(
                event_type=EventType.OCCUPANCY_ESTIMATE,
                camera_id="cam_001",
                track_ids=[tid] if tid else [],
                explanation=f"Vehicle occupancy: {occ} occupants",
                metadata={"occupancy": occ, "track_id": tid},
                severity="info",
            ))
        self.stats.event_time_ms += (time.perf_counter() - t3) * 1000

        for ev in events:
            self.api_client.send_event(ev)
        self.stats.events_emitted += len(events)
        self._send_heartbeat(fps)

        annotated = self.annotator.draw(
            frame, detections, tracks, fps, alpr_out, occ_out, events,
        )
        self.stats.frames_processed += 1
        return annotated, events

    def run(self, source: str, display: bool = True, record_path: Optional[str] = None) -> None:
        self.logger.info(f"Opening video source: {source}")
        cap = cv2.VideoCapture(source)
        if not cap.isOpened():
            self.logger.error(f"Failed to open source: {source}")
            return
        writer = None
        if record_path:
            os.makedirs(os.path.dirname(record_path) or ".", exist_ok=True)
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps_src = max(1.0, cap.get(cv2.CAP_PROP_FPS) or 25.0)
            writer = cv2.VideoWriter(record_path, fourcc, fps_src, (w, h))

        frame_id = 0
        prev_time = time.perf_counter()
        fps_ema = 25.0
        try:
            with self.api_client:
                while True:
                    ok, frame = cap.read()
                    if not ok:
                        self.logger.info("End of stream / read error")
                        break
                    now = time.perf_counter()
                    delta = now - prev_time
                    prev_time = now
                    inst_fps = 1.0 / delta if delta > 0 else 0.0
                    fps_ema = fps_ema * 0.9 + inst_fps * 0.1

                    annotated, _ = self.process_frame(frame, frame_id, fps_ema)
                    if writer:
                        writer.write(annotated)
                    if display:
                        cv2.imshow("AI Edge Surveillance", annotated)
                        if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
                            break
                    frame_id += 1
                    if frame_id % 300 == 0:
                        self.logger.info(
                            f"Frames={frame_id} fps={fps_ema:.1f} "
                            f"events={self.stats.events_emitted} "
                            f"avg_det_ms={self.stats.detection_time_ms / max(1, self.stats.frames_processed):.1f}"
                        )
        finally:
            cap.release()
            if writer:
                writer.release()
            cv2.destroyAllWindows()
            self.api_client.flush_buffer()
            self.logger.info("Pipeline shutdown complete")


def main() -> None:
    parser = argparse.ArgumentParser(description="AI-Driven Edge Surveillance Pipeline")
    parser.add_argument("--source", type=str, required=True, help="Video file, RTSP URL, or camera index")
    parser.add_argument("--config", type=str, default=None, help="JSON config file path")
    parser.add_argument("--no-display", action="store_true", help="Run headless")
    parser.add_argument("--record", type=str, default=None, help="Record annotated output to .mp4")
    args = parser.parse_args()

    settings = PipelineSettings.load(args.config)
    try:
        src = int(args.source)
    except ValueError:
        src = args.source
    pipeline = SurveillancePipeline(settings)
    pipeline.run(source=src, display=not args.no_display, record_path=args.record)


if __name__ == "__main__":
    main()
