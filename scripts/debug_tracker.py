import sys; sys.path.insert(0, '.')
from edge_pipeline.perception.tracker import ByteTracker
from edge_pipeline.utils.types import Detection

dets = [
    Detection(xyxy=(210,110,250,190), cls=0, conf=0.9, track_id=None),
    Detection(xyxy=(310,150,350,230), cls=0, conf=0.9, track_id=None),
]
bt = ByteTracker(track_buffer=30, match_thresh=0.05)  # low threshold for test
out = bt.update(dets, fps=10.0)
for d in out:
    print(f"  det {d.xyxy} -> track_id={d.track_id}  (history={bt.tracks[d.track_id].history})")
print("tracks dict:", list(bt.tracks.keys()))
assert len(bt.tracks) == 2, f"Expected 2 tracks, got {len(bt.tracks)}"
print("PASS")
