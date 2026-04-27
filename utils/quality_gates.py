"""
同梱デモ用の**粗い**合格基準。本番用データは閾値を要調整。

主目的: 「実装が**基本的に**要件を満たしたか」に yes/no 相当のフラグを付す。
主指標は常に生の `metrics`。
厳密な判定は**複数ケース＋ evaluator 一貫**が本筋（docs/BENCH_JUDGE.md の AtCoder 型）。
"""
from __future__ import annotations

from typing import Any, Mapping, Optional

def metrics_pass_for_task(
    task: str, metrics: Optional[Mapping[str, Any]], *, on_missing: str = "fail"
) -> bool:
    """
    `metrics` が None / 空なら: on_missing "fail" → False, "pass" → True, "na" → False
    """
    t = task.lower()
    if not metrics:
        if on_missing == "pass":
            return True
        if on_missing == "na":
            return False
        return False
    m = dict(metrics)
    try:
        if t == "gnss":
            r = float(m.get("rmse", 999))
            s = float(m.get("speed_error", 999))
            return r < 0.1 and s < 0.1
        if t == "lidar":
            c = float(m.get("cluster_count_score", 0))
            iou = float(m.get("mean_iou", 0))
            return c > 0.5 and iou > 0.3
        if t == "vision":
            ap = float(m.get("map50_simple", 0))
            return ap > 0.3
        if t == "planning":
            return (
                float(m.get("reaches_goal", 0)) > 0.5
                and float(m.get("collision_free", 0)) > 0.5
            )
        if t == "control":
            rm = float(m.get("rmse", 999))
            mx = float(m.get("max_abs", 999))
            return rm < 0.5 and mx < 0.5
    except (TypeError, ValueError):
        return False
    return False
