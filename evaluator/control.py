from __future__ import annotations

import math
from typing import Any, Dict, List


def evaluate_control(pred: Dict[str, Any], ground_truth: Dict[str, Any]) -> Dict[str, float]:
    """
    1次系追従: 位置 RMSE, 最大誤差, 参照との整合。
    """
    y: List[float] = pred.get("trajectory", [])
    ref: List[float] = ground_truth.get("ref_trajectory", ground_truth.get("p_ref", []))
    y = [float(x) for x in y]
    ref = [float(x) for x in ref]
    if not y or not ref or len(y) != len(ref):
        return {"rmse": float("inf"), "max_abs": float("inf"), "mean_abs": float("inf")}

    err = [y[i] - ref[i] for i in range(len(ref))]
    mse = sum(e * e for e in err) / len(err)
    rmse = math.sqrt(mse)
    max_abs = max(abs(e) for e in err)
    mean_abs = sum(abs(e) for e in err) / len(err)
    return {
        "rmse": float(rmse),
        "max_abs": float(max_abs),
        "mean_abs": float(mean_abs),
    }
