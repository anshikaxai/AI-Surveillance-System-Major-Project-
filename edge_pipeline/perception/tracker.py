from __future__ import annotations
from typing import Dict, List, Optional, Tuple
from collections import OrderedDict
import time
import numpy as np

from edge_pipeline.utils.types import Detection, TrackState, BehaviourLabel


class ByteTracker:
    def __init__(self, track_buffer: int = 30, match_thresh: float = 0.8) -> None:
        self.tracks: "OrderedDict[int, TrackState]" = OrderedDict()
        self.track_buffer = track_buffer
        self.match_thresh = match_thresh
        self._next_id: int = 1
        self._lost: Dict[int, int] = {}

    def _iou_matrix(self, a: List[Tuple[float, float, float, float]], b: List[Tuple[float, float, float, float]]) -> np.ndarray:
        if not a or not b:
            return np.zeros((0, 0))
        na, nb = len(a), len(b)
        A = np.array(a)
        B = np.array(b)
        A = np.tile(A[:, None, :], (1, nb, 1))
        B = np.tile(B[None, :, :], (na, 1, 1))
        x1 = np.maximum(A[..., 0], B[..., 0])
        y1 = np.maximum(A[..., 1], B[..., 1])
        x2 = np.minimum(A[..., 2], B[..., 2])
        y2 = np.minimum(A[..., 3], B[..., 3])
        inter = np.maximum(0, x2 - x1) * np.maximum(0, y2 - y1)
        area_a = (A[..., 2] - A[..., 0]) * (A[..., 3] - A[..., 1])
        area_b = (B[..., 2] - B[..., 0]) * (B[..., 3] - B[..., 1])
        union = area_a + area_b - inter
        return inter / np.maximum(union, 1e-9)

    def update(self, detections: List[Detection], fps: float = 10.0) -> List[Detection]:
        ts = time.time()
        current_ids: set = set()

        if self.tracks and detections:
            track_boxes: List[Tuple[float, float, float, float]] = []
            track_id_list: List[int] = []
            for tid, state in self.tracks.items():
                if state.history:
                    last = state.history[-1]
                    h = state.height_est if hasattr(state, "height_est") else 120.0
                    w = state.width_est if hasattr(state, "width_est") else 60.0
                    track_boxes.append((last[0] - w / 2, last[1] - h, last[0] + w / 2, last[1]))
                else:
                    track_boxes.append((0, 0, 0, 0))
                track_id_list.append(tid)

            det_boxes = [d.xyxy for d in detections]
            iou_mat = self._iou_matrix(track_boxes, det_boxes)

            used_det = set()
            if iou_mat.size > 0:
                order = np.argsort(-iou_mat.max(axis=1)) if iou_mat.shape[1] > 0 else []
                for ti in order:
                    if iou_mat.shape[1] == 0:
                        break
                    best_di = int(np.argmax(iou_mat[ti]))
                    if iou_mat[ti, best_di] >= self.match_thresh and best_di not in used_det:
                        tid = track_id_list[ti]
                        detections[best_di].track_id = tid
                        self.tracks[tid].update(detections[best_di], ts)
                        det = detections[best_di]
                        self.tracks[tid].width_est = det.width
                        self.tracks[tid].height_est = det.height
                        self.tracks[tid].compute_speed(fps)
                        current_ids.add(tid)
                        used_det.add(best_di)

            for di, det in enumerate(detections):
                if det.track_id is None:
                    new_id = self._next_id
                    self._next_id += 1
                    det.track_id = new_id
                    state = TrackState(track_id=new_id, cls=det.cls)
                    state.update(det, ts)
                    state.width_est = det.width
                    state.height_est = det.height
                    self.tracks[new_id] = state
                    current_ids.add(new_id)
        else:
            for det in detections:
                new_id = self._next_id
                self._next_id += 1
                det.track_id = new_id
                state = TrackState(track_id=new_id, cls=det.cls)
                state.update(det, ts)
                state.width_est = det.width
                state.height_est = det.height
                self.tracks[new_id] = state
                current_ids.add(new_id)

        to_remove: List[int] = []
        for tid in self.tracks:
            if tid not in current_ids:
                self._lost[tid] = self._lost.get(tid, 0) + 1
                if self._lost[tid] > self.track_buffer:
                    to_remove.append(tid)
            else:
                self._lost[tid] = 0
        for tid in to_remove:
            self.tracks.pop(tid, None)
            self._lost.pop(tid, None)

        return detections

    def get_state(self, track_id: int) -> Optional[TrackState]:
        return self.tracks.get(track_id)

    def all_states(self) -> Dict[int, TrackState]:
        return dict(self.tracks)
