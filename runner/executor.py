from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Literal, Optional

from utils.timing import Timer
from runner.model_registry import get_gnss_runner, get_lidar_runner, get_vision_runner

from evaluator.common import load_json, resolve_ground_truth_path
from evaluator.gnss import evaluate_gnss
from evaluator.lidar import evaluate_lidar
from evaluator.vision import evaluate_vision

TaskName = Literal["gnss", "lidar", "vision"]


def _default_gt_path(repo_root: Path, task: TaskName) -> Path:
    if task == "gnss":
        return repo_root / "data" / "gnss" / "ground_truth.json"
    if task == "lidar":
        return repo_root / "data" / "lidar" / "ground_truth.json"
    if task == "vision":
        return repo_root / "data" / "vision" / "ground_truth.json"
    raise ValueError(task)


def run_task(
    task: str,
    input_path: Path,
    model: str,
    repo_root: Path,
    ground_truth: Optional[Path] = None,
    noise: float = 0.0,
) -> Dict[str, Any]:
    tname = task.lower()  # type: ignore[assignment]
    if tname not in ("gnss", "lidar", "vision"):
        raise ValueError(f"未知のタスク: {task}")

    timer = Timer()
    with timer.block():
        if tname == "gnss":
            pred = get_gnss_runner(model)(input_path, model=model, noise_m=noise)
        elif tname == "lidar":
            pred = get_lidar_runner(model)(input_path, model=model, noise_std=noise)
        else:
            pred = get_vision_runner(model)(input_path, model=model, noise_std=noise)

    out: Dict[str, Any] = {
        "task": tname,
        "model": model,
        "input": str(input_path.resolve()),
        "predictions": pred,
        "runtime_ms": round(timer.last_ms(), 3),
    }

    gt_p = resolve_ground_truth_path(_default_gt_path(repo_root, tname), ground_truth)  # type: ignore
    if gt_p.is_file():
        gt = load_json(gt_p)
        if tname == "gnss":
            m = evaluate_gnss(pred, gt)
            out["metrics"] = m
        elif tname == "lidar":
            lidar_gt: Dict[str, Any] = {
                "cluster_labels": gt.get("cluster_labels", []),
            }
            m = evaluate_lidar(pred, lidar_gt)
            out["metrics"] = m
        else:
            m = evaluate_vision(pred, gt)
            out["metrics"] = m
        out["ground_truth_path"] = str(gt_p.resolve())
    return out
