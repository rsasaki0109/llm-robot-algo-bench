from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple


def _iou_xywh(a: Tuple[float, float, float, float], b: Tuple[float, float, float, float]) -> float:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    ax2, ay2, bx2, by2 = ax + aw, ay + ah, bx + bw, by + bh
    ix1, iy1 = max(ax, bx), max(ay, by)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0, ix2 - ix1), max(0, iy2 - iy1)
    inter = iw * ih
    union = aw * ah + bw * bh - inter + 1e-9
    return inter / union


def _greedy_match(
    det: List[Tuple[float, float, float, float, float]], gts: List[Tuple[float, float, float, float]]
) -> Tuple[int, int, int, List[Tuple[int, int, float]]]:
    """
    検出は (x,y,w,h,score) 降順想定。GT は xywh。
    各検出を最も IoU 大の未使用 GT へ割当（1対1、IoU>=0.5）
    戻り: TP, FP, FN, マッチ列
    """
    det_sorted = sorted(det, key=lambda d: d[4], reverse=True) if det else []
    used_gt: set = set()
    matches: List[Tuple[int, int, float]] = []
    tp = 0
    for j, d in enumerate(det_sorted):
        best_i, best_iou = -1, 0.0
        dbox = (d[0], d[1], d[2], d[3])
        for i, g in enumerate(gts):
            if i in used_gt:
                continue
            iou = _iou_xywh(dbox, g)
            if iou > best_iou:
                best_iou, best_i = iou, i
        if best_iou >= 0.5 and best_i >= 0:
            used_gt.add(best_i)
            matches.append((best_i, j, best_iou))
            tp += 1
    fp = len(det_sorted) - tp
    fn = len(gts) - len(used_gt)
    return tp, fp, fn, matches


def evaluate_vision(
    pred: Dict[str, Any], ground_truth: Dict[str, Any]
) -> Dict[str, float]:
    """
    簡易 mAP@0.5 風: 1画像・1クラス想定
    - precision@0.5 = TP / max(len(dets),1)
    - recall@0.5    = TP / max(len(gts),1)
    - map50_simple: sqrt(precision * recall)（PR の幾何平均）
    - mean_iou: マッチしたペアの IoU 平均
    """
    dets: List[Dict[str, float]] = pred.get("detections", [])
    gts: List[Dict[str, float]] = ground_truth.get("boxes", [])
    det_tuples: List[Tuple[float, float, float, float, float]] = []
    for d in dets:
        det_tuples.append(
            (
                float(d.get("x", 0.0)),
                float(d.get("y", 0.0)),
                float(d.get("w", 0.0)),
                float(d.get("h", 0.0)),
                float(d.get("score", 1.0)),
            )
        )
    gt_tuples: List[Tuple[float, float, float, float]] = []
    for g in gts:
        if "w" in g:
            gt_tuples.append(
                (float(g["x"]), float(g["y"]), float(g["w"]), float(g["h"]))
            )
        else:
            x1, y1, x2, y2 = float(g["x1"]), float(g["y1"]), float(g["x2"]), float(g["y2"])
            gt_tuples.append((x1, y1, x2 - x1, y2 - y1))
    if not gt_tuples and not det_tuples:
        return {"map50_simple": 1.0, "precision@0.5": 1.0, "recall@0.5": 1.0, "mean_iou_matched": 1.0}
    if not gt_tuples:
        return {"map50_simple": 0.0, "precision@0.5": 0.0, "recall@0.5": 0.0, "mean_iou_matched": 0.0}
    tp, fp, fn, matches = _greedy_match(det_tuples, gt_tuples)
    prec = tp / max(len(det_tuples), 1)
    rec = tp / max(len(gt_tuples), 1)
    map_simple = 0.0 if prec * rec <= 0 else math.sqrt(prec * rec)
    mean_ious = [m[2] for m in matches] if matches else []
    mean_iou = float(sum(mean_ious) / max(len(mean_ious), 1)) if mean_ious else 0.0
    return {
        "map50_simple": map_simple,
        "precision@0.5": prec,
        "recall@0.5": rec,
        "mean_iou_matched": mean_iou,
    }
