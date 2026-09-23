from __future__ import annotations
from typing import Optional
import numpy as np

from edge_pipeline.utils.types import BehaviourLabel, TrackState


class BehaviourClassifier:
    def __init__(
        self,
        walking_threshold: float = 80.0,
        running_threshold: float = 200.0,
        history_len: int = 10,
    ) -> None:
        self.walking_threshold = walking_threshold
        self.running_threshold = running_threshold
        self.history_len = history_len

    def classify(self, track: TrackState, fps: float = 10.0) -> BehaviourLabel:
        if len(track.history) < 3:
            track.behaviour = BehaviourLabel.UNKNOWN
            return BehaviourLabel.UNKNOWN
        speed = track.compute_speed(fps)
        if speed < self.walking_threshold * 0.3 and len(track.history) >= self.history_len:
            recent = track.history[-self.history_len:]
            xs = [p[0] for p in recent]
            ys = [p[1] for p in recent]
            spread = ((max(xs) - min(xs)) ** 2 + (max(ys) - min(ys)) ** 2) ** 0.5
            if spread < 20:
                label = BehaviourLabel.STANDING
            else:
                label = BehaviourLabel.WALKING
        elif speed >= self.running_threshold:
            label = BehaviourLabel.RUNNING
        elif speed >= self.walking_threshold:
            label = BehaviourLabel.WALKING
        else:
            label = BehaviourLabel.STANDING if len(track.history) >= 5 else BehaviourLabel.UNKNOWN
        track.behaviour = label
        return label
