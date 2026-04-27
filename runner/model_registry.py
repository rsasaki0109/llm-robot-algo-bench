"""
model 名 → 各タスクの実装関数。

Cursor では **Composer（2 Fast 等）** / **Opus 4.7** を選んでコード生成し、
同じ文字列をここに登録する想定（対応表は docs/CURSOR.md）。

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

import importlib.util
from pathlib import Path
from typing import Any, Callable, Dict, Optional, cast

from tasks.control.baseline import run_control
from tasks.gnss.baseline import run_gnss
from tasks.lidar.baseline import run_lidar
from tasks.planning.baseline import run_planning
from tasks.vision.baseline import run_vision

DEFAULT = "baseline"
_GEN_DIR = Path(__file__).resolve().parents[1] / "tasks" / "generated"

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
PlanningRun = Callable[..., Any]
ControlRun = Callable[..., Any]

PLANNING: Dict[str, PlanningRun] = {
    "baseline": run_planning,
}
CONTROL: Dict[str, ControlRun] = {
    "baseline": run_control,
}


def _load_generated(task: str, model: str) -> Optional[Callable[..., Any]]:
    """
    tasks/generated/<model>/<task>.py があれば動的 import して run_* を返す。

    例: tasks/generated/opencode-go_kimi-k2.6/gnss.py の run_gnss
    """
    t = task.lower()
    m = model.strip()
    if not t or not m:
        return None
    p = _GEN_DIR / m / f"{t}.py"
    if not p.is_file():
        return None
    mod_name = f"tasks.generated.{m}.{t}".replace("-", "_").replace("/", "_").replace(".", "_")
    spec = importlib.util.spec_from_file_location(mod_name, str(p))
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    fn = getattr(module, f"run_{t}", None)
    if callable(fn):
        def _wrapped(*args: Any, **kwargs: Any) -> Any:
            # 生成コードが `model` 値で分岐して壊れるのを避ける（bench の `--model` は識別子）。
            # 実装側が `model` を使うべき場合は、生成プロンプト/実装の方を直す。
            kwargs["model"] = "baseline"
            return fn(*args, **kwargs)

        return cast(Callable[..., Any], _wrapped)
    return None


def is_registered(task: str, model: str) -> bool:
    """レジストリに `model` があり、フォールバックでない。"""
    m = model.strip()
    t = task.lower()
    if t == "gnss":
        return m in GNSS or (_GEN_DIR / m / "gnss.py").is_file()
    if t == "lidar":
        return m in LIDAR or (_GEN_DIR / m / "lidar.py").is_file()
    if t == "vision":
        return m in VISION or (_GEN_DIR / m / "vision.py").is_file()
    if t == "planning":
        return m in PLANNING or (_GEN_DIR / m / "planning.py").is_file()
    if t == "control":
        return m in CONTROL or (_GEN_DIR / m / "control.py").is_file()
    return False


def get_gnss_runner(name: str) -> GnssRun:
    if name in GNSS:
        return GNSS[name]
    g = _load_generated("gnss", name)
    if g is not None:
        return cast(GnssRun, g)
    return cast(GnssRun, GNSS[DEFAULT])


def get_lidar_runner(name: str) -> LidarRun:
    if name in LIDAR:
        return LIDAR[name]
    g = _load_generated("lidar", name)
    if g is not None:
        return cast(LidarRun, g)
    return cast(LidarRun, LIDAR[DEFAULT])


def get_vision_runner(name: str) -> VisionRun:
    if name in VISION:
        return VISION[name]
    g = _load_generated("vision", name)
    if g is not None:
        return cast(VisionRun, g)
    return cast(VisionRun, VISION[DEFAULT])


def get_planning_runner(name: str) -> PlanningRun:
    if name in PLANNING:
        return PLANNING[name]
    g = _load_generated("planning", name)
    if g is not None:
        return cast(PlanningRun, g)
    return cast(PlanningRun, PLANNING[DEFAULT])


def get_control_runner(name: str) -> ControlRun:
    if name in CONTROL:
        return CONTROL[name]
    g = _load_generated("control", name)
    if g is not None:
        return cast(ControlRun, g)
    return cast(ControlRun, CONTROL[DEFAULT])
