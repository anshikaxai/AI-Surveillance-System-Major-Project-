import sys
sys.path.insert(0, '.')
from edge_pipeline.config.settings import ROIConfig
from edge_pipeline.intelligence.event_engine import EventIntelligenceLayer
from edge_pipeline.perception.tracker import ByteTracker
from edge_pipeline.utils.types import PerceptionFrame, Detection
import time as _t

poly = [[200,100],[500,100],[500,400],[200,400]]
roi = ROIConfig(name="Test", polygon=poly, loitering_threshold_sec=0.01, crowd_threshold=2)
engine = EventIntelligenceLayer([roi], cooldown_sec=0)

dets = [
    Detection(xyxy=(210,110,250,190), cls=0, conf=0.9),
    Detection(xyxy=(310,150,350,230), cls=0, conf=0.9),
]
bt = ByteTracker(track_buffer=30, match_thresh=0.05)
bt.update(dets, fps=10.0)
track_ids = list(bt.tracks.keys())
print("Tracks created:", track_ids)

# Inject old entry times
before = _t.time() - 10
for tid in track_ids:
    bt.tracks[tid].roi_entry_times["Test"] = before

pframe = PerceptionFrame(frame_id=1, timestamp=_t.time(), detections=dets, fps=10.0, width=800, height=600)
# set track_id in detections from output
updated_dets = bt.update(dets, fps=10.0)

evts = engine.process_frame(pframe, updated_dets, bt.all_states())
types_got = sorted([e.event_type.value for e in evts])
print(f"Events fired: {types_got}")
print([(e.event_type.value, e.explanation[:80]) for e in evts])
assert "crowd" in types_got and "loitering" in types_got, f"FAIL: {types_got}"
print("Event Engine: FULLY PASSED")
