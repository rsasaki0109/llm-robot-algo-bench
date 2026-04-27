from __future__ import annotations

from typing import Any, Dict, List


def evaluate_planning(pred: Dict[str, Any], ground_truth: Dict[str, Any]) -> Dict[str, float]:
    """
    グリッド上の 4 近傍経路: 到達, 超過ステップ, 衝突なし, 参照経路点との平均 L1 誤差。
    """
    path: List[List[int]] = pred.get("path", [])
    ref: List[List[int]] = ground_truth.get("ref_path", ground_truth.get("path", []))
    grid: List[List[int]] = ground_truth.get("grid", [])

    if not ref:
        return {
            "reaches_goal": 0.0,
            "length_excess": float("inf"),
            "collision_free": 0.0,
            "waypoint_mae": float("inf"),
        }

    goal = [int(x) for x in ref[-1]]
    start = [int(x) for x in ref[0]]
    reaches = 0.0
    if path and [int(p) for p in path[0]] == start and [int(p) for p in path[-1]] == goal:
        reaches = 1.0
    if not path or [int(p) for p in path[-1]] != goal:
        reaches = 0.0

    ref_len = max(len(ref) - 1, 0)
    pred_len = max(len(path) - 1, 0) if path else 0
    length_excess = float(pred_len - ref_len)

    collision = 1.0
    if path and grid:
        h, w = len(grid), len(grid[0])
        for p in path:
            r, c = int(p[0]), int(p[1])
            if r < 0 or c < 0 or r >= h or c >= w or grid[r][c] != 0:
                collision = 0.0
                break
    elif not path:
        collision = 0.0

    wmae = 0.0
    if path and ref:
        ref_t = [tuple(int(x) for x in p) for p in ref]
        for pt in path:
            pr, pc = int(pt[0]), int(pt[1])
            dmin = min(abs(pr - a) + abs(pc - b) for a, b in ref_t)
            wmae += dmin
        wmae /= len(path)
    else:
        wmae = float("inf") if not path else 0.0

    return {
        "reaches_goal": float(reaches),
        "length_excess": length_excess,
        "collision_free": float(collision),
        "waypoint_mae": float(wmae) if wmae != float("inf") else wmae,
    }
