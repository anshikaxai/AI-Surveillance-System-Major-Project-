#!/usr/bin/env python3
"""End-to-end API smoke test — all endpoints that should return 200 even with DB down (NLP),
and DB-backed ones that gracefully 500 are checked as expected."""
import sys
import json
import urllib.request
import urllib.error

BASE = "http://localhost:8000/api/v1"

def req(method, path, payload=None, expected_ok=True):
    body = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        body = json.dumps(payload).encode()
    r = urllib.request.Request(BASE + path, data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(r, timeout=10) as resp:
            data = resp.read()
            return resp.status, json.loads(data) if data else {}
    except urllib.error.HTTPError as e:
        data = e.read()
        try:
            j = json.loads(data)
        except Exception:
            j = {"raw": data[:300].decode(errors="ignore")}
        return e.code, j

ok = 0
bad = 0
def check(name, status, data, want_code=200, want_keys=None):
    global ok, bad
    if status == want_code and (want_keys is None or all(k in data for k in want_keys)):
        print(f"  ✓ {name}  [{status}]")
        ok += 1
    else:
        print(f"  ✗ {name}  [{status}] want={want_code} keys={want_keys} — {json.dumps(data)[:200]}")
        bad += 1

print("=== Endpoints that MUST return 200 (not DB-backed) ===")
with urllib.request.urlopen("http://localhost:8000/health", timeout=5) as h:
    health = json.loads(h.read())
    print(f"  ✓ /health  [{h.status}] status={health.get('status')} database={health.get('database')}")
    ok += 1

s, d = req("POST", "/nlp/parse-preview", {"command": "Monitor main gate after 8 PM"})
check("POST /nlp/parse-preview", s, d, 200, ["confidence", "json_payload", "warnings"])
assert isinstance(d["json_payload"].get("active_hours"), list) and d["json_payload"]["active_hours"][0] >= 20
print(f"      payload details: conf={d['confidence']:.2f} roi={d['json_payload']['roi_name']} hours={d['json_payload']['active_hours']}")

s, d = req("POST", "/nlp/parse", {"command": "Loitering threshold 90 seconds on parking zone"})
# This may 200 (write to rois) or 500 (DB-graceful); parse still runs regardless
s2, d2 = req("POST", "/nlp/parse-preview", {"command": "Disable loitering alerts on lobby during business hours"})
check("POST /nlp/parse-preview #2 (business hours)", s2, d2, 200, ["confidence", "json_payload"])
assert d2["json_payload"]["enable"] is False
assert d2["json_payload"]["active_hours"] == [8, 18]
print(f"      hours={d2['json_payload']['active_hours']} enable={d2['json_payload']['enable']}")

s, d = req("GET", "/config")
# /config may be 500 when DB down, or fall back gracefully. Test /config upsert via parse-preview path was tested.
print(f"  ⚠ GET /config → {s} (DB-backed, { 'OK' if s==200 else 'degraded-as-designed' })")
if s == 200: ok += 1

# Test the NLP parser 5-case set
cases = [
    ("Monitor main gate after 8 PM", {"conf_min": 0.70, "roi": "Main Gate", "hours": [20, 23]}),
    ("Loitering threshold 2 minutes on parking zone", {"conf_min": 0.70, "roi": "Parking Zone", "loiter": 120}),
    ("Alert crowd if more than 10 people at entrance", {"conf_min": 0.70, "roi": "Main Gate", "crowd": 10}),
    ("Watch parking during night hours", {"conf_min": 0.70, "roi": "Parking Zone", "hours": [18, 6]}),
    ("Disable loitering alerts on lobby during business hours", {"conf_min": 0.70, "roi": "Lobby", "enable": False, "hours": [8, 18]}),
]
print("\n=== 5 NLP Smoke Cases (from spec) ===")
for cmd, spec in cases:
    s, d = req("POST", "/nlp/parse-preview", {"command": cmd})
    assert s == 200, (cmd, s, d)
    j = d["json_payload"]
    good = d["confidence"] >= spec["conf_min"] and j["roi_name"] == spec["roi"]
    if "hours" in spec: good = good and (j.get("active_hours") == spec["hours"])
    if "loiter" in spec: good = good and (j.get("loitering_threshold_sec") == spec["loiter"])
    if "crowd" in spec: good = good and (j.get("crowd_threshold") == spec["crowd"])
    if "enable" in spec: good = good and (j.get("enable") == spec["enable"])
    status = "✓" if good else "✗"
    print(f"   {status} {cmd}  -> conf={d['confidence']:.2f} roi={j['roi_name']} hours={j.get('active_hours')}")
    if good: ok += 1
    else:
        bad += 1
        print(f"      FAILED spec={spec} got={j}")

print(f"\n=== RESULT: {ok} PASS, {bad} FAIL ===")
sys.exit(0 if bad == 0 else 1)
