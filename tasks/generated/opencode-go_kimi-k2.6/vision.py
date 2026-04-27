from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple

import cv2
import numpy as np


def _nms(
    boxes: List[Tuple[float, float, float, float, float]], threshold: float = 0.3
) -> List[Tuple[float, float, float, float, float]]:
    if not boxes:
        return []
    boxes_arr = np.array(boxes, dtype=np.float32)
    x1 = boxes_arr[:, 0]
    y1 = boxes_arr[:, 1]
    x2 = boxes_arr[:, 0] + boxes_arr[:, 2]
    y2 = boxes_arr[:, 1] + boxes_arr[:, 3]
    scores = boxes_arr[:, 4]
    areas = (x2 - x1) * (y2 - y1)
    order = scores.argsort()[::-1]
    keep = []
    while order.size > 0:
        i = order[0]
        keep.append(i)
        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])
        w = np.maximum(0.0, xx2 - xx1)
        h = np.maximum(0.0, yy2 - yy1)
        inter = w * h
        iou = inter / (areas[i] + areas[order[1:]] - inter + 1e-6)
        inds = np.where(iou <= threshold)[0]
        order = order[inds + 1]
    return [boxes[i] for i in keep]


def _detect_hog(gray: np.ndarray) -> List[Tuple[float, float, float, float, float]]:
    hog = cv2.HOGDescriptor()
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
    all_dets: List[Tuple[float, float, float, float, float]] = []
    for scale in (1.03, 1.05, 1.07):
        rects, weights = hog.detectMultiScale(
            gray, winStride=(4, 4), padding=(8, 8), scale=scale
        )
        if weights is not None and len(weights) > 0:
            for (x, y, w, h), s in zip(rects, weights):
                all_dets.append((float(x), float(y), float(w), float(h), float(s)))
    return _nms(all_dets, threshold=0.3)


def _detect_contour(gray: np.ndarray) -> List[Tuple[float, float, float, float, float]]:
    inv = 255 - gray
    _, th = cv2.threshold(inv, 40, 255, cv2.THRESH_BINARY)
    k = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    th = cv2.morphologyEx(th, cv2.MORPH_CLOSE, k, iterations=2)
    cs, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    h, w = gray.shape[:2]
    dets: List[Tuple[float, float, float, float, float]] = []
    for c in cs:
        x, y, bw, bh = cv2.boundingRect(c)
        if bw * bh < 0.005 * w * h:
            continue
        ar = bh / max(bw, 1)
        if 0.3 < ar < 10.0:
            score = float(bh * bw / (h * w + 1e-6))
            person_score = score * (1.0 + abs(ar - 3.0) / 3.0)
            dets.append((float(x), float(y), float(bw), float(bh), person_score))
    return sorted(dets, key=lambda d: d[4], reverse=True)[:5]


def run_vision(
    input_path: Path,
    model: str = "baseline",
    noise_std: float = 0.0,
) -> Dict[str, Any]:
    _ = model
    img = cv2.imread(str(input_path), cv2.IMREAD_COLOR)
    if img is None:
        return {"detections": [], "w": 0, "h": 0}
    h, w = img.shape[:2]
    if noise_std > 0.0:
        rng = np.random.default_rng(2)
        n = rng.normal(0, noise_std, size=img.shape)
        img = np.clip(np.round(img.astype(float) + n), 0, 255).astype(np.uint8)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    dets = _detect_hog(gray)
    if not dets:
        dets = _detect_contour(gray)
    if dets:
        max_score = max(d[4] for d in dets)
        if max_score > 0:
            dets = [(d[0], d[1], d[2], d[3], d[4] / max_score) for d in dets]
    return {
        "detections": [
            {"x": d[0], "y": d[1], "w": d[2], "h": d[3], "score": d[4]}
            for d in dets[:10]
        ],
        "w": int(w),
        "h": int(h),
    }
