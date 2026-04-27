"""
タスク定義上の分類（出題上の性質・難易度の目安）。

**実装の良し悪し**は `metrics` と `quality_pass` 別途。ここは「どの系統の課題か」用。
"""
from __future__ import annotations

from typing import Any, Dict

# 1=比較的短い/局所、2=中、3=多段階・探索や時系列
TASK_SPEC: Dict[str, Dict[str, Any]] = {
    "gnss": {
        "family": "sensors/geometry",
        "difficulty_tier": 1,
        "blurb": "NMEA パース＋自己整合。局所的な幾何・時系列内挿。",
    },
    "lidar": {
        "family": "point_cloud/clustering",
        "difficulty_tier": 2,
        "blurb": "点群からクラスタ。ラベリング/IoU 系。",
    },
    "vision": {
        "family": "image/detection",
        "difficulty_tier": 2,
        "blurb": "bbox 検出と mAP(簡易)。前処理・重なり。",
    },
    "planning": {
        "family": "grid_path/graph",
        "difficulty_tier": 3,
        "blurb": "格子・障害・経路。探索/制約の扱い。",
    },
    "control": {
        "family": "ode/tracking",
        "difficulty_tier": 2,
        "blurb": "1 次系＋目標追従。制御則＋積分。",
    },
}


def get_task_spec(task: str) -> Dict[str, Any]:
    t = task.lower()
    if t in TASK_SPEC:
        return {**TASK_SPEC[t], "task": t}
    return {"task": t, "family": "unknown", "difficulty_tier": 0, "blurb": ""}
