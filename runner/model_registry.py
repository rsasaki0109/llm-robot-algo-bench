"""
model 名 → 各タスクの実装関数。

未登録の model は従来どおり baseline にフォールバックする。
新しい手法を足すには、下記の辞書に `実装名` → `tasks.*` の run 関数を追加する。

例（将来）::

    from tasks.gnss import experimental
    GNSS: Dict[str, GnssRun] = {
        "baseline": run_gnss,
        "v2": experimental.run_gnss,
    }
"""

from __future__ import annotations

from typing import Any, Callable, Dict, cast

from tasks.gnss.baseline import run_gnss
from tasks.lidar.baseline import run_lidar
from tasks.vision.baseline import run_vision

DEFAULT = "baseline"

# タスク実装: (Path, model, ノイズ) → predictions dict
GnssRun = Callable[..., Any]
LidarRun = Callable[..., Any]
VisionRun = Callable[..., Any]

GNSS: Dict[str, GnssRun] = {
    "baseline": run_gnss,
}
LIDAR: Dict[str, LidarRun] = {
    "baseline": run_lidar,
}
VISION: Dict[str, VisionRun] = {
    "baseline": run_vision,
}


def get_gnss_runner(name: str) -> GnssRun:
    if name in GNSS:
        return GNSS[name]
    return cast(GnssRun, GNSS[DEFAULT])


def get_lidar_runner(name: str) -> LidarRun:
    if name in LIDAR:
        return LIDAR[name]
    return cast(LidarRun, LIDAR[DEFAULT])


def get_vision_runner(name: str) -> VisionRun:
    if name in VISION:
        return VISION[name]
    return cast(VisionRun, VISION[DEFAULT])
