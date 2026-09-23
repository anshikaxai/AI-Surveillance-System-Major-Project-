import sys
sys.path.insert(0, '.')
from api_backend.core.nlp_parser import NLPConfigParser

tests = [
    ('Monitor main gate after 8 PM', 0.7, 'after 8PM'),
    ('Loitering threshold 2 minutes on parking zone', 0.7, 'parking 2min'),
    ('Alert crowd if more than 10 people at entrance', 0.7, 'crowd>10'),
    ('Watch parking during night hours', 0.7, 'night parking'),
    ('Disable loitering alerts on lobby during business hours', 0.7, 'disable business'),
]
for cmd, threshold, label in tests:
    r = NLPConfigParser.parse(cmd, 'cam_001')
    mark = 'OK' if r['confidence'] >= threshold else 'FAIL'
    p = r['json_payload']
    print(f'[{mark}] {label}')
    print(f'  confidence={r["confidence"]:.2f} | explanation: {r["explanation"]}')
    print(f'  json: roi={p.get("roi_name")} loiter_s={p.get("loitering_threshold_sec")} crowd={p.get("crowd_threshold")} hours={p.get("active_hours")} enable={p.get("enable")}')

print()
print('NLP parser smoke test complete.')
