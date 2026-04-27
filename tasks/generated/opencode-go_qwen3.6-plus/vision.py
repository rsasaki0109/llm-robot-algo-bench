from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple

import cv2
import numpy as np


def _nms(
    boxes: List[Tuple[float, float, float, float, float]],
    iou_thresh: float = 0.3,
) -> List[Tuple[float, float, float, float, float]]:
    if not boxes:
        return []
    arr = np.array(boxes, dtype=np.float64)
    x1 = arr[:, 0]
    y1 = arr[:, 1]
    x2 = x1 + arr[:, 2]
    y2 = y1 + arr[:, 3]
    areas = arr[:, 2] * arr[:, 3]
    order = arr[:, 4].argsort()[::-1]
    keep: List[int] = []
    while order.size > 0:
        i = int(order[0])
        keep.append(i)
        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])
        iw = np.maximum(0.0, xx2 - xx1)
        ih = np.maximum(0.0, yy2 - yy1)
        inter = iw * ih
        iou = inter / (areas[i] + areas[order[1:]] - inter + 1e-9)
        remain = np.where(iou <= iou_thresh)[0]
        order = order[remain + 1]
    return [boxes[k] for k in keep]


def _hog_pass(gray: np.ndarray) -> List[Tuple[float, float, float, float, float]]:
    hog = cv2.HOGDescriptor()
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
    out: List[Tuple[float, float, float, float, float]] = []
    for ws, pad, sc in [
        ((8, 8), (16, 16), 1.05),
        ((4, 4), (8, 8), 1.03),
    ]:
        rects, weights = hog.detectMultiScale(
            gray, winStride=ws, padding=pad, scale=sc, hitThreshold=0.0,
        )
        if rects is not None and len(rects):
            for (x, y, w, h), s in zip(
                rects, weights if weights is not None else [1.0] * len(rects),
            ):
                out.append((float(x), float(y), float(w), float(h), float(s)))
    return _nms(out, iou_thresh=0.3)


def _contour_pass(
    gray: np.ndarray,
) -> List[Tuple[float, float, float, float, float]]:
    h, w = gray.shape[:2]
    area_img = h * w
    eq = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray)
    inv = 255 - eq
    _, th = cv2.threshold(inv, 45, 255, cv2.THRESH_BINARY)
    k = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    th = cv2.morphologyEx(th, cv2.MORPH_CLOSE, k, iterations=1)
    cs, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    out: List[Tuple[float, float, float, float, float]] = []
    for c in cs:
        x, y, bw, bh = cv2.boundingRect(c)
        a = bw * bh
        if a < 0.003 * area_img or a > 0.85 * area_img:
            continue
        ar = bh / max(bw, 1)
        if not (0.6 < ar < 6.0):
            continue
        score = min(a / area_img * 10.0, 0.5) * (1.0 - abs(ar - 3.0) / 3.0)
        out.append((float(x), float(y), float(bw), float(bh), float(score)))
    return sorted(out, key=lambda d: d[4], reverse=True)[:8]


def _edge_box_pass(
    gray: np.ndarray,
) -> List[Tuple[float, float, float, float, float]]:
    h, w = gray.shape[:2]
    area_img = h * w
    edges = cv2.Canny(gray, 50, 150)
    k = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    edges = cv2.dilate(edges, k, iterations=1)
    cs, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    out: List[Tuple[float, float, float, float, float]] = []
    for c in cs:
        x, y, bw, bh = cv2.boundingRect(c)
        a = bw * bh
        if a < 0.005 * area_img or a > 0.8 * area_img:
            continue
        ar = bh / max(bw, 1)
        if not (0.8 < ar < 5.0):
            continue
        score = min(a / area_img * 5.0, 0.3)
        out.append((float(x), float(y), float(bw), float(bh), float(score)))
    return sorted(out, key=lambda d: d[4], reverse=True)[:5]


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
    eq = cv2.equalizeHist(gray)
    gray_blend = cv2.addWeighted(gray, 0.4, eq, 0.6, 0)

    all_dets: List[Tuple[float, float, float, float, float]] = []

    hog_dets = _hog_pass(gray_blend)
    all_dets.extend(hog_dets)

    if len(hog_dets) < 3:
        ct_dets = _contour_pass(gray_blend)
        all_dets.extend(ct_dets)

    if len(all_dets) < 2:
        eb_dets = _edge_box_pass(gray_blend)
        all_dets.extend(eb_dets)

    if all_dets:
        all_dets = _nms(all_dets, iou_thresh=0.35)
        max_s = max(d[4] for d in all_dets)
        if max_s > 0:
            all_dets = [
                (d[0], d[1], d[2], d[3], d[4] / max_s) for d in all_dets
            ]
        all_dets = sorted(all_dets, key=lambda d: d[4], reverse=True)[:10]

    detections: List[Dict[str, float]] = [
        {"x": d[0], "y": d[1], "w": d[2], "h": d[3], "score": d[4]}
        for d in all_dets
    ]
    return {"detections": detections, "w": int(w), "h": int(h)}
