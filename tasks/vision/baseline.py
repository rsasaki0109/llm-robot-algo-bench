from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple

import cv2
import numpy as np


def _person_boxes_contour(gray: np.ndarray) -> List[Dict[str, float]]:
    """
    簡易: 最も大きい暗い塊（縦長）を1候補として返す。GPU 不要のデモ用。
    本番は HOG/NN に差し替え可能。
    """
    inv = 255 - gray
    _, th = cv2.threshold(inv, 40, 255, cv2.THRESH_BINARY)
    k = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    th = cv2.morphologyEx(th, cv2.MORPH_CLOSE, k, iterations=1)
    cs, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    dets: List[Tuple[float, float, float, float, float]] = []
    h, w = gray.shape[:2]
    for c in cs:
        x, y, bw, bh = cv2.boundingRect(c)
        if bw * bh < 0.01 * w * h:
            continue
        ar = bh / max(bw, 1)
        if 0.5 < ar < 8.0:
            dets.append(
                (float(x), float(y), float(bw), float(bh), float(bh * bw / (h * w + 1e-6)))
            )
    if not dets:
        h_hog, w_h = gray.shape[:2]
        hog = cv2.HOGDescriptor()
        hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        (rects, weights) = hog.detectMultiScale(
            gray, winStride=(8, 8), padding=(8, 8), scale=1.04
        )
        for (x, y, w1, h1), s in zip(rects, weights if weights is not None else [1.0] * len(rects)):
            dets.append((float(x), float(y), float(w1), float(h1), float(s)))
    dets = sorted(dets, key=lambda d: d[4], reverse=True)[:5]
    return [
        {
            "x": d[0],
            "y": d[1],
            "w": d[2],
            "h": d[3],
            "score": d[4],
        }
        for d in dets
    ]


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
    dets = _person_boxes_contour(gray)
    return {
        "detections": dets,
        "w": int(w),
        "h": int(h),
    }
