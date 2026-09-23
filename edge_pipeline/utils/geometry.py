from __future__ import annotations
from typing import List, Tuple, Optional
from shapely.geometry import Point, Polygon


def point_in_polygon(point: Tuple[float, float], polygon: List[Tuple[int, int]]) -> bool:
    if len(polygon) < 3:
        return False
    p = Point(point[0], point[1])
    poly = Polygon(polygon)
    return poly.contains(p) or poly.touches(p)


def box_intersects_polygon(
    xyxy: Tuple[float, float, float, float], polygon: List[Tuple[int, int]]
) -> bool:
    if len(polygon) < 3:
        return False
    x1, y1, x2, y2 = xyxy
    corners = [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
    center = ((x1 + x2) / 2, (y1 + y2) / 2)
    poly = Polygon(polygon)
    for c in corners + [center]:
        if poly.contains(Point(c[0], c[1])):
            return True
    return False


def point_to_point_dist(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    dx = a[0] - b[0]
    dy = a[1] - b[1]
    return (dx * dx + dy * dy) ** 0.5


def iou(box_a: Tuple[float, float, float, float], box_b: Tuple[float, float, float, float]) -> float:
    x1a, y1a, x2a, y2a = box_a
    x1b, y1b, x2b, y2b = box_b
    x1i = max(x1a, x1b)
    y1i = max(y1a, y1b)
    x2i = min(x2a, x2b)
    y2i = min(y2a, y2b)
    inter = max(0, x2i - x1i) * max(0, y2i - y1i)
    area_a = (x2a - x1a) * (y2a - y1a)
    area_b = (x2b - x1b) * (y2b - y1b)
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def crop_box(
    xyxy: Tuple[float, float, float, float],
    img_w: int,
    img_h: int,
    pad_ratio: float = 0.05,
) -> Tuple[int, int, int, int]:
    x1, y1, x2, y2 = xyxy
    w = x2 - x1
    h = y2 - y1
    px = w * pad_ratio
    py = h * pad_ratio
    return (
        max(0, int(x1 - px)),
        max(0, int(y1 - py)),
        min(img_w, int(x2 + px)),
        min(img_h, int(y2 + py)),
    )
