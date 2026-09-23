import sys
import traceback
sys.path.insert(0, '.')

modules = [
    ('edge_pipeline.config.settings', 'PipelineSettings + ROIConfig'),
    ('edge_pipeline.utils.types', 'Detection, TrackState, SecurityEvent, EventType, ObjectClass, BehaviourLabel, PerceptionFrame'),
    ('edge_pipeline.utils.geometry', 'geometry helpers'),
    ('edge_pipeline.perception.tracker', 'ByteTracker (fallback tracker - no ultralytics dep)'),
    ('edge_pipeline.domain.behaviour', 'BehaviourClassifier'),
    ('edge_pipeline.intelligence.event_engine', 'EventIntelligenceLayer'),
    ('api_backend.models.schemas', 'Pydantic schemas (V2 - check compatible)'),
    ('api_backend.core.nlp_parser', 'NLPConfigParser'),
]

failed = []
for m, desc in modules:
    try:
        __import__(m)
        print(f"  OK   {m}")
    except Exception as e:
        print(f"  FAIL {m} :: {e}")
        traceback.print_exc()
        failed.append((m, str(e)))

print()
if failed:
    print(f"FAILED: {len(failed)}/{len(modules)}")
    sys.exit(1)
else:
    print(f"All {len(modules)} base modules imported OK.")

print()
print("Testing NLP parser output...")
from api_backend.core.nlp_parser import NLPConfigParser
for cmd in [
    "Monitor main gate after 8 PM",
    "Loitering threshold 2 minutes on parking zone",
    "Alert crowd if more than 10 people at entrance",
    "Watch parking during night hours",
]:
    r = NLPConfigParser.parse(cmd)
    print(f"  {cmd} -> conf={r['confidence']:.2f} payload={r['json_payload']['roi_name']} hours={r['json_payload']['active_hours']}")

print()
print("Testing geometry + types...")
from edge_pipeline.utils.geometry import point_in_polygon
poly = [[200,100],[500,100],[500,400],[200,400]]
assert point_in_polygon((300, 250), poly) is True
assert point_in_polygon((10, 10), poly) is False
print("  point_in_polygon: OK")

from edge_pipeline.utils.types import Detection, TrackState, EventType
d = Detection(xyxy=(0,0,100,100), cls=0, conf=0.9, track_id=1)
assert d.area == 10000
t = TrackState(track_id=1, cls=0)
t.update(d)
assert len(t.history) == 1
print("  Detection + TrackState: OK")

from edge_pipeline.domain.behaviour import BehaviourClassifier
bc = BehaviourClassifier()
# add points to simulate standing
for i in range(10):
    d2 = Detection(xyxy=(300+i, 200, 400+i, 300), cls=0, conf=0.9, track_id=1)
    t.update(d2)
label = bc.classify(t, fps=10.0)
print(f"  BehaviourClassifier -> {label}")

from edge_pipeline.intelligence.event_engine import EventIntelligenceLayer
from edge_pipeline.config.settings import ROIConfig
from edge_pipeline.utils.types import PerceptionFrame
roi = ROIConfig(name="Test", polygon=poly, loitering_threshold_sec=0.01, crowd_threshold=2)
engine = EventIntelligenceLayer([roi], cooldown_sec=0)
# Simulate two persons in ROI
dets = [
    Detection(xyxy=(210,110,250,190), cls=0, conf=0.9, track_id=10),
    Detection(xyxy=(310,150,350,230), cls=0, conf=0.9, track_id=11),
]
# Need track states
from edge_pipeline.perception.tracker import ByteTracker
bt = ByteTracker()
bt.update(dets, fps=10.0)
# Make sure we register them staying via fake "entry time" injection via process_frame
import time as _t
before = _t.time() - 10  # simulate 10s ago
for tid in (10,11):
    st = bt.tracks[tid]
    st.roi_entry_times["Test"] = before

pframe = PerceptionFrame(frame_id=1, timestamp=_t.time(), detections=dets, fps=10.0, width=800, height=600)
evts = engine.process_frame(pframe, dets, bt.all_states())
types_got = sorted([e.event_type.value for e in evts])
print(f"  EventIntelligenceLayer events: {types_got}")
# Should get both crowd (2>=2) and loitering (10s > 0.01s)
assert "crowd" in types_got and "loitering" in types_got, f"Expected crowd+loitering, got {types_got}"
print("  EventIntelligenceLayer: OK (loitering + crowd triggers)")

print()
print("=== ALL TESTS PASSED ===")
