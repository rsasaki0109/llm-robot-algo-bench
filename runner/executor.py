from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from utils.timing import Timer
from runner.model_registry import (
    get_control_runner,
    get_gnss_runner,
    get_lidar_runner,
    get_planning_runner,
    get_vision_runner,
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
            pred = get_gnss_runner(model)(input_path, model=model, noise_m=noise)
        elif tname == "lidar":
            pred = get_lidar_runner(model)(input_path, model=model, noise_std=noise)
        elif tname == "vision":
            pred = get_vision_runner(model)(input_path, model=model, noise_std=noise)
        elif tname == "planning":
            pred = get_planning_runner(model)(input_path, model=model, noise=noise)
        else:
            pred = get_control_runner(model)(input_path, model=model, noise=noise)

    out: Dict[str, Any] = {
        "task": tname,
        "model": model,
        "input": str(input_path.resolve()),
        "predictions": pred,
        "runtime_ms": round(timer.last_ms(), 3),
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
    return out
