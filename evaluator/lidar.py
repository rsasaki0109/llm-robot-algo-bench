from __future__ import annotations

from typing import Any, Dict, List, Set, Tuple

import numpy as np
from scipy.optimize import linear_sum_assignment


def _cluster_sets(labels: np.ndarray) -> List[Set[int]]:
    ids = set(int(x) for x in np.unique(labels) if int(x) >= 0)
    return [set(np.where(labels == c)[0].tolist()) for c in sorted(ids)]


def _pairwise_iou(a: Set[int], b: Set[int]) -> float:
    if not a and not b:
        return 1.0
    u = len(a | b)
    if u == 0:
        return 0.0
    return len(a & b) / u


def evaluate_lidar(
    pred: Dict[str, Any], ground_truth: Dict[str, Any]
) -> Dict[str, float]:
    """
    クラスタ数一致率: 1 - |K_pred - K_true| / max(K_true,1)
    IoU: 最適割当（Hungarian）でクラスタ点集合同士の IoU を平均
    """
    l_pred = pred.get("cluster_labels", [])
    l_true = ground_truth.get("cluster_labels", [])
    if l_pred is None or l_true is None or len(l_pred) != len(l_true):
        return {"cluster_count_score": 0.0, "mean_iou": 0.0, "n_pred_clusters": 0, "n_true_clusters": 0}

    p = np.asarray(l_pred, dtype=int)
    t = np.asarray(l_true, dtype=int)
    sets_p = _cluster_sets(p)
    sets_t = _cluster_sets(t)
    kp, kt = len(sets_p), len(sets_t)
    if kt == 0 and kp == 0:
        return {"cluster_count_score": 1.0, "mean_iou": 1.0, "n_pred_clusters": 0, "n_true_clusters": 0}
    count_score = 1.0 - abs(kp - kt) / max(kt, 1)

    if kp == 0 or kt == 0:
        return {
            "cluster_count_score": count_score,
            "mean_iou": 0.0,
            "n_pred_clusters": float(kp),
            "n_true_clusters": float(kt),
        }

    cost = np.zeros((kt, kp), dtype=float)
    for i in range(kt):
        for j in range(kp):
            cost[i, j] = 1.0 - _pairwise_iou(sets_t[i], sets_p[j])
    r, c = linear_sum_assignment(cost)
    ious = [1.0 - cost[ri, ci] for ri, ci in zip(r, c)]
    mean_iou = float(np.mean(ious)) if ious else 0.0
    return {
        "cluster_count_score": count_score,
        "mean_iou": mean_iou,
        "n_pred_clusters": float(kp),
        "n_true_clusters": float(kt),
    }
