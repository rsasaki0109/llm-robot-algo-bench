from __future__ import annotations

import inspect
from pathlib import Path
from typing import Any, Dict, Optional

from utils.timing import Timer
from utils.code_complexity import analyze_python_path
from utils.quality_gates import metrics_pass_for_task
from utils.task_spec import get_task_spec
from runner.model_registry import (
    get_control_runner,
    get_gnss_runner,
    get_lidar_runner,
    get_planning_runner,
    get_vision_runner,
    is_registered,
)

from evaluator.common import load_json, resolve_ground_truth_path
from evaluator.control import evaluate_control
from evaluator.gnss import evaluate_gnss
from evaluator.lidar import evaluate_lidar
from evaluator.planning import evaluate_planning
from evaluator.vision import evaluate_vision

_TASKS: tuple[str, ...] = ("gnss", "lidar", "vision", "planning", "control")


def _default_gt_path(repo_root: Path, task: str) -> Path:
    return repo_root / "data" / task / "ground_truth.json"


def run_task(
    task: str,
    input_path: Path,
    model: str,
    repo_root: Path,
    ground_truth: Optional[Path] = None,
    noise: float = 0.0,
) -> Dict[str, Any]:
    tname = task.lower()
    if tname not in _TASKS:
        raise ValueError(f"未知のタスク: {task}")

    timer = Timer()
    with timer.block():
        if tname == "gnss":
            runner = get_gnss_runner(model)
            pred = runner(input_path, model=model, noise_m=noise)
        elif tname == "lidar":
            runner = get_lidar_runner(model)
            pred = runner(input_path, model=model, noise_std=noise)
        elif tname == "vision":
            runner = get_vision_runner(model)
            pred = runner(input_path, model=model, noise_std=noise)
        elif tname == "planning":
            runner = get_planning_runner(model)
            pred = runner(input_path, model=model, noise=noise)
        else:
            runner = get_control_runner(model)
            pred = runner(input_path, model=model, noise=noise)

    out: Dict[str, Any] = {
        "task": tname,
        "model": model,
        "input": str(input_path.resolve()),
        "predictions": pred,
        "runtime_ms": round(timer.last_ms(), 3),
        "task_spec": get_task_spec(tname),
    }
    _src = inspect.getfile(runner)
    try:
        _rel = str(Path(_src).resolve().relative_to(repo_root.resolve()))
    except ValueError:
        _rel = _src
    _cm = analyze_python_path(_src)
    if _cm and "file" in _cm:
        try:
            _cm["file"] = str(Path(_cm["file"]).resolve().relative_to(repo_root.resolve()))
        except ValueError:
            pass
    out["impl"] = {
        "source_file": _rel,
        "code_metrics": _cm,
        "registry_hit": is_registered(tname, model),
        "used_fallback": not is_registered(tname, model),
    }

    gt_p = resolve_ground_truth_path(_default_gt_path(repo_root, tname), ground_truth)
    if gt_p.is_file():
        gt = load_json(gt_p)
        if tname == "gnss":
            m = evaluate_gnss(pred, gt)
        elif tname == "lidar":
            lidar_gt: Dict[str, Any] = {
                "cluster_labels": gt.get("cluster_labels", []),
            }
            m = evaluate_lidar(pred, lidar_gt)
        elif tname == "vision":
            m = evaluate_vision(pred, gt)
        elif tname == "planning":
            m = evaluate_planning(pred, gt)
        else:
            m = evaluate_control(pred, gt)
        out["metrics"] = m
        out["ground_truth_path"] = str(gt_p.resolve())
        out["quality_pass"] = metrics_pass_for_task(tname, m)
    return out
