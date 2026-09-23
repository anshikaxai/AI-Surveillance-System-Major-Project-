from __future__ import annotations
from typing import Any, Dict, List, Tuple, Optional
import re
import logging

logger = logging.getLogger("nlp")


TIME_PATTERNS = [
    (re.compile(r"(after|from|starting\s+at|at)\s+(\d{1,2})(:?\d{0,2})\s*(am|pm|AM|PM|hrs|hours|o'clock)?"), "time"),
    (re.compile(r"between\s+(\d{1,2})\s*(am|pm)?\s*and\s+(\d{1,2})\s*(am|pm)?"), "between"),
    (re.compile(r"(\d{1,2})\s*(am|pm|AM|PM|hrs)"), "simple_time"),
]

ROI_PATTERNS = [
    re.compile(r"(main\s*gate|parking|entrance|exit|lobby|hall|zone|area|region)\s*(#?\d*)", re.IGNORECASE),
    re.compile(r"roi\s*[:\-]?\s*(['\"]?)([a-zA-Z0-9_\s]+)\1", re.IGNORECASE),
]

LOITER_WORDS = ["loiter", "linger", "stay", "wait", "hang around", "suspicious"]
CROWD_WORDS = ["crowd", "gather", "group", "people count", "too many", "congregat"]
THRESH_PATTERN = re.compile(r"(\d+)\s*(sec|second|seconds|min|minute|minutes|person|people|persons)", re.IGNORECASE)


def _parse_hour(match_str: str, ampm: Optional[str]) -> Optional[int]:
    try:
        h = int(match_str)
    except ValueError:
        return None
    ampm = (ampm or "").lower()
    if ampm in ("pm",) and h < 12:
        h += 12
    elif ampm in ("am",) and h == 12:
        h = 0
    return h if 0 <= h <= 23 else None


class NLPConfigParser:
    KNOWN_ROI_MAPPING: Dict[str, str] = {
        "main gate": "Main Gate",
        "maingate": "Main Gate",
        "gate": "Main Gate",
        "entrance": "Main Gate",
        "parking": "Parking Zone",
        "parking zone": "Parking Zone",
        "parking lot": "Parking Zone",
        "lobby": "Lobby",
    }

    @classmethod
    def parse(cls, command: str, camera_id: str = "cam_001") -> Dict[str, Any]:
        cmd_lower = command.lower()
        result: Dict[str, Any] = {
            "action": "config_update",
            "target": "roi",
            "camera_id": camera_id,
            "roi_name": None,
            "loitering_threshold_sec": None,
            "crowd_threshold": None,
            "active_hours": None,
            "enable": True,
        }
        confidence = 0.0
        explanation_parts: List[str] = []
        warnings: List[str] = []

        roi_name: Optional[str] = None
        for pat in ROI_PATTERNS:
            m = pat.search(command)
            if m:
                if "roi" in pat.pattern.lower():
                    candidate = m.group(2).strip()
                else:
                    key = f"{m.group(1)}{m.group(2)}".strip().lower().rstrip()
                    candidate = cls.KNOWN_ROI_MAPPING.get(m.group(1).strip().lower(), m.group(1).strip())
                if candidate:
                    roi_name = candidate
                    confidence += 0.25
                    explanation_parts.append(f"Target ROI: {roi_name}")
                    break
        if roi_name is None:
            roi_name = "Main Gate"
            warnings.append("No ROI explicitly named, defaulted to 'Main Gate'")
        result["roi_name"] = roi_name

        is_loiter = any(w in cmd_lower for w in LOITER_WORDS)
        is_crowd = any(w in cmd_lower for w in CROWD_WORDS)
        if is_loiter and not is_crowd:
            result["feature"] = "loitering"
            confidence += 0.2
            explanation_parts.append("Configuring loitering detection")
        elif is_crowd and not is_loiter:
            result["feature"] = "crowd"
            confidence += 0.2
            explanation_parts.append("Configuring crowd detection")
        else:
            result["feature"] = "both"
            confidence += 0.1
            explanation_parts.append("Configuring both loitering and crowd detection")

        thr_matches = THRESH_PATTERN.findall(command)
        for num, unit in thr_matches:
            try:
                n = int(num)
            except ValueError:
                continue
            unit_lower = unit.lower()
            if unit_lower.startswith("sec") or unit_lower.startswith("second"):
                result["loitering_threshold_sec"] = float(n)
                confidence += 0.15
                explanation_parts.append(f"Loitering threshold: {n}s")
            elif unit_lower.startswith("min"):
                result["loitering_threshold_sec"] = float(n * 60)
                confidence += 0.15
                explanation_parts.append(f"Loitering threshold: {n}min ({n*60}s)")
            elif unit_lower.startswith("person") or unit_lower.startswith("people"):
                result["crowd_threshold"] = n
                confidence += 0.15
                explanation_parts.append(f"Crowd threshold: {n} people")

        active_hours: Optional[List[int]] = None
        for pat, kind in TIME_PATTERNS:
            m = pat.search(command)
            if not m:
                continue
            if kind == "time":
                h = _parse_hour(m.group(2), m.group(4))
                if h is not None:
                    active_hours = [h, 23]
                    confidence += 0.15
                    explanation_parts.append(f"Active from {h:02d}:00 to end of day")
                break
            elif kind == "between":
                h1 = _parse_hour(m.group(1), m.group(2))
                h2 = _parse_hour(m.group(3), m.group(4))
                if h1 is not None and h2 is not None:
                    active_hours = [h1, h2]
                    confidence += 0.2
                    explanation_parts.append(f"Active hours: {h1:02d}:00 - {h2:02d}:00")
                break
            elif kind == "simple_time":
                h = _parse_hour(m.group(1), m.group(2))
                if h is not None:
                    active_hours = [h, 23]
                    confidence += 0.15
                    explanation_parts.append(f"Active from {h:02d}:00")
                break
        if active_hours is None and ("night" in cmd_lower or "evening" in cmd_lower):
            active_hours = [18, 6]
            confidence += 0.1
            explanation_parts.append("Active hours inferred: 18:00 - 06:00 (night)")
        if active_hours is None and ("day" in cmd_lower or "business" in cmd_lower or "working" in cmd_lower):
            active_hours = [8, 18]
            confidence += 0.1
            explanation_parts.append("Active hours inferred: 08:00 - 18:00 (business)")
        result["active_hours"] = active_hours

        if "monitor" in cmd_lower or "enable" in cmd_lower or "start" in cmd_lower or "watch" in cmd_lower:
            result["enable"] = True
            confidence += 0.05
        elif "disable" in cmd_lower or "stop" in cmd_lower or "ignore" in cmd_lower:
            result["enable"] = False
            confidence += 0.05

        if "disable" in cmd_lower:
            result["enable"] = False

        confidence = max(0.0, min(1.0, confidence + 0.3))
        return {
            "raw_command": command,
            "parsed_action": result["action"],
            "json_payload": result,
            "confidence": round(confidence, 3),
            "explanation": " | ".join(explanation_parts) or "No recognized patterns",
            "warnings": warnings,
        }
