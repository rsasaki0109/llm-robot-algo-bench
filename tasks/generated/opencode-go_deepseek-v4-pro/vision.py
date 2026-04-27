from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple

import cv2
import numpy as np


def _non_max_suppression(
    boxes: np.ndarray, scores: np.ndarray, iou_threshold: float = 0.3
) -> List[int]:
    if len(boxes) == 0:
        return []
    x1 = boxes[:, 0]
    y1 = boxes[:, 1]
    x2 = x1 + boxes[:, 2]
    y2 = y1 + boxes[:, 3]
    areas = boxes[:, 2] * boxes[:, 3]
    order = scores.argsort()[::-1]
    keep: List[int] = []
    while order.size > 0:
        i = order[0]
        keep.append(int(i))
        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])
        w = np.maximum(0.0, xx2 - xx1)
        h = np.maximum(0.0, yy2 - yy1)
        inter = w * h
        ovr = inter / (areas[i] + areas[order[1:]] - inter + 1e-8)
        inds = np.where(ovr <= iou_threshold)[0]
        order = order[inds + 1]
    return keep


def _hog_detect(
    gray: np.ndarray, img_h: int, img_w: int
) -> Tuple[List[List[float]], List[float]]:
    hog = cv2.HOGDescriptor()
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
    boxes: List[List[float]] = []
    scores: List[float] = []
    configs = [
        {"winStride": (8, 8), "padding": (16, 16), "scale": 1.05, "hitThreshold": 0.0},
        {"winStride": (4, 4), "padding": (16, 16), "scale": 1.02, "hitThreshold": 0.1},
    ]
    for cfg in configs:
        rects, weights = hog.detectMultiScale(
            gray,
            winStride=cfg["winStride"],
            padding=cfg["padding"],
            scale=cfg["scale"],
            hitThreshold=cfg["hitThreshold"],
        )
        if rects is not None and len(rects) > 0:
            for (rx, ry, rw, rh), s in zip(
                rects,
                weights if weights is not None else [1.0] * len(rects),
            ):
                x0 = float(rx)
                y0 = float(ry)
                w0 = float(rw)
                h0 = float(rh)
                s0 = float(s)
                if x0 < 0 or y0 < 0 or w0 <= 0 or h0 <= 0:
                    continue
                if x0 + w0 > img_w:
                    w0 = img_w - x0
                if y0 + h0 > img_h:
                    h0 = img_h - y0
                if w0 < 4 or h0 < 4:
                    continue
                boxes.append([x0, y0, w0, h0])
                scores.append(s0)
    return boxes, scores


def _contour_detect(
    gray: np.ndarray, img_h: int, img_w: int
) -> Tuple[List[List[float]], List[float]]:
    inv = 255 - gray
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    inv = clahe.apply(inv)
    _, th = cv2.threshold(inv, 50, 255, cv2.THRESH_BINARY)
    k = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    th = cv2.morphologyEx(th, cv2.MORPH_CLOSE, k, iterations=1)
    cs, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes: List[List[float]] = []
    scores: List[float] = []
    area_img = img_h * img_w
    for c in cs:
        x, y, bw, bh = cv2.boundingRect(c)
        area = bw * bh
        if area < 0.003 * area_img or area > 0.9 * area_img:
            continue
        ar = bh / max(bw, 1)
        if not (0.6 < ar < 6.0):
            continue
        boxes.append([float(x), float(y), float(bw), float(bh)])
        scores.append(min(area / area_img * 10.0, 0.5))
    return boxes, scores


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
    gray = cv2.addWeighted(gray, 0.5, eq, 0.5, 0)

    all_boxes: List[List[float]] = []
    all_scores: List[float] = []

    hog_boxes, hog_scores = _hog_detect(gray, h, w)
    all_boxes.extend(hog_boxes)
    all_scores.extend(hog_scores)

    if len(all_boxes) < 2:
        ct_boxes, ct_scores = _contour_detect(gray, h, w)
        all_boxes.extend(ct_boxes)
        all_scores.extend(ct_scores)

    if all_boxes:
        boxes_arr = np.array(all_boxes, dtype=np.float32)
        scores_arr = np.array(all_scores, dtype=np.float32)
        keep = _non_max_suppression(boxes_arr, scores_arr, iou_threshold=0.35)
        boxes_arr = boxes_arr[keep]
        scores_arr = scores_arr[keep]
        sort_idx = scores_arr.argsort()[::-1]
        boxes_arr = boxes_arr[sort_idx]
        scores_arr = scores_arr[sort_idx]
    else:
        boxes_arr = np.empty((0, 4), dtype=np.float32)
        scores_arr = np.empty((0,), dtype=np.float32)

    detections: List[Dict[str, float]] = []
    for i in range(min(len(boxes_arr), 10)):
        b = boxes_arr[i]
        detections.append({
            "x": float(b[0]),
            "y": float(b[1]),
            "w": float(b[2]),
            "h": float(b[3]),
            "score": float(scores_arr[i]),
        })

    return {
        "detections": detections,
        "w": int(w),
        "h": int(h),
    }
