from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from evaluator.common import load_json, save_json
from evaluator.control import evaluate_control
from evaluator.gnss import evaluate_gnss
from evaluator.lidar import evaluate_lidar
from evaluator.planning import evaluate_planning
from evaluator.vision import evaluate_vision
from runner.executor import run_task


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _save_viz(root: Path, task: str, res: Dict[str, Any], inp: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    out_dir = root / "results" / "figs"
    out_dir.mkdir(parents=True, exist_ok=True)
    pred = res.get("predictions", {})
    if task == "gnss":
        traj = pred.get("enu_trajectory", [])
        if not traj:
            return
        e = [p.get("e_m", 0) for p in traj]
        n = [p.get("n_m", 0) for p in traj]
        fig, ax = plt.subplots()
        ax.plot(e, n, "o-")
        ax.set_xlabel("E [m]")
        ax.set_ylabel("N [m]")
        ax.set_title("ENU trajectory (pred)")
        fig.savefig(out_dir / f"gnss_{inp.stem}.png", dpi=120)
        plt.close(fig)
    elif task == "lidar" and str(inp).endswith(".npy"):
        import numpy as np

        pts = np.load(inp)[:, :3]
        fig = plt.figure()
        ax = fig.add_subplot(111, projection="3d")
        ax.scatter(pts[:, 0], pts[:, 1], pts[:, 2], s=2, c="C0", alpha=0.6)
        ax.set_title("LiDAR points")
        fig.savefig(out_dir / f"lidar_{inp.stem}.png", dpi=120)
        plt.close(fig)
    elif task == "vision":
        import cv2

        bgr = cv2.imread(str(inp))
        if bgr is None:
            return
        for d in pred.get("detections", []):
            x, y, w, h = int(d["x"]), int(d["y"]), int(d["w"]), int(d["h"])
            cv2.rectangle(bgr, (x, y), (x + w, y + h), (0, 200, 0), 2)
        cv2.imwrite(str(out_dir / f"vision_{inp.stem}.jpg"), bgr)
    elif task == "planning":
        import json
        import numpy as np

        spec = json.loads(inp.read_text())
        g = np.array(spec.get("grid", []), dtype=float)
        path = res.get("predictions", {}).get("path", [])
        fig, ax = plt.subplots()
        if g.size:
            ax.imshow(g, cmap="gray_r", origin="upper")
        if path:
            ys = [p[0] for p in path]
            xs = [p[1] for p in path]
            ax.plot(xs, ys, "r.-", linewidth=2, markersize=6)
        ax.set_title("Grid path (pred)")
        fig.savefig(out_dir / f"planning_{inp.stem}.png", dpi=120)
        plt.close(fig)
    elif task == "control":
        pred = res.get("predictions", {})
        pr = [float(x) for x in pred.get("p_ref", [])]
        y = [float(x) for x in pred.get("trajectory", [])]
        if pr and y and len(pr) == len(y):
            fig, ax = plt.subplots()
            ax.plot(pr, "k--", label="p_ref")
            ax.plot(y, "C0-", label="traj")
            ax.legend()
            ax.set_title("1D tracking")
            fig.savefig(out_dir / f"control_{inp.stem}.png", dpi=120)
            plt.close(fig)


def _resolve_out_path(
    args: argparse.Namespace, root: Path, res: Dict[str, Any]
) -> Path:
    if args.out:
        return Path(args.out)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    name = f"result_{res['task']}_{res.get('model', 'm')}_{ts}.json"
    return (root / "results" / name).resolve()


def cmd_run(args: argparse.Namespace) -> int:
    root = _repo_root()
    inp = Path(args.input)
    if not inp.is_file():
        print(f"入力が見つかりません: {inp}", file=sys.stderr)
        return 2
    gt_path = Path(args.ground_truth) if args.ground_truth else None
    res = run_task(
        task=args.task,
        input_path=inp,
        model=args.model,
        repo_root=root,
        ground_truth=gt_path,
        noise=args.noise,
    )
    if args.viz and args.task in (
        "gnss",
        "vision",
        "lidar",
        "planning",
        "control",
    ):
        _save_viz(root, args.task, res, inp)
    out_path = _resolve_out_path(args, root, res)
    save_json(out_path, res)
    print(str(out_path.resolve()))
    return 0


def cmd_eval(args: argparse.Namespace) -> int:
    root = _repo_root()
    p = Path(args.result)
    if not p.is_file():
        print(f"result が見つかりません: {p}", file=sys.stderr)
        return 2
    data = load_json(p)
    task = (args.task or data.get("task", "")).lower()
    if task not in ("gnss", "lidar", "vision", "planning", "control"):
        print("タスク名が不正、または result に task がありません", file=sys.stderr)
        return 2
    def_gt = _default_gt_for_task(root, task)
    gt_path = Path(args.ground_truth) if args.ground_truth else def_gt
    if not gt_path.is_file():
        print(f"ground truth が見つかりません: {gt_path}", file=sys.stderr)
        return 2
    gt = load_json(gt_path)
    pred = data.get("predictions", data)
    if task == "gnss":
        m = evaluate_gnss(pred, gt)
    elif task == "lidar":
        m = evaluate_lidar(pred, {"cluster_labels": gt.get("cluster_labels", [])})
    elif task == "vision":
        m = evaluate_vision(pred, gt)
    elif task == "planning":
        m = evaluate_planning(pred, gt)
    else:
        m = evaluate_control(pred, gt)
    data["metrics"] = m
    data["ground_truth_path"] = str(gt_path.resolve())
    save_path = Path(args.out) if args.out else p
    save_json(save_path, data)
    print(json.dumps(m, ensure_ascii=False, indent=2))
    return 0


def _default_gt_for_task(root: Path, task: str) -> Path:
    return root / "data" / task / "ground_truth.json"


def cmd_compare(args: argparse.Namespace) -> int:
    d = Path(args.dir)
    if not d.is_dir():
        print(f"ディレクトリが見つかりません: {d}", file=sys.stderr)
        return 2
    rows: List[Dict[str, Any]] = []
    for p in sorted(d.glob("*.json")):
        if p.name.startswith("leaderboard"):
            continue
        try:
            j = load_json(p)
        except (json.JSONDecodeError, OSError):
            continue
        if "metrics" not in j:
            continue
        m = j["metrics"]
        row = {
            "file": p.name,
            "task": j.get("task", ""),
            "model": j.get("model", ""),
            "runtime_ms": j.get("runtime_ms", ""),
        }
        if isinstance(m, dict):
            row.update(m)
        rows.append(row)
    if not rows:
        print("比較可能な .json がありません", file=sys.stderr)
        return 1
    all_keys: List[str] = []
    for r in rows:
        for k in r:
            if k not in all_keys and k not in ("file",):
                all_keys.append(k)
    key_order = ["file", "task", "model", "runtime_ms"] + [
        k for k in all_keys if k not in ("file", "task", "model", "runtime_ms")
    ]
    md = d / "leaderboard.md"
    with open(md, "w", encoding="utf-8") as f:
        f.write("# Leaderboard\n\n")
        f.write("| " + " | ".join(key_order) + " |\n")
        f.write("|" + "|".join(["---"] * len(key_order)) + "|\n")
        for r in rows:
            f.write(
                "| " + " | ".join(str(r.get(k, "")) for k in key_order) + " |\n"
            )
    csvp = d / "leaderboard.csv"
    with open(csvp, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=key_order, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(str(md.resolve()))
    print(str(csvp.resolve()))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="bench",
        description="LLM ロボティクス・アルゴリズム ベンチマーク (MVP)",
    )
    sp = p.add_subparsers(dest="command", required=True)
    r = sp.add_parser("run", help="推論（baseline/将来は生成コード）と評価")
    r.add_argument(
        "--task",
        required=True,
        choices=["gnss", "lidar", "vision", "planning", "control"],
    )
    r.add_argument("--input", required=True, type=str)
    r.add_argument("--model", default="baseline", type=str)
    r.add_argument("--out", type=str, default=None, help="出力 JSON パス（省略時 results/）")
    r.add_argument("--ground-truth", type=str, default=None, dest="ground_truth")
    r.add_argument(
        "--noise", type=float, default=0.0, help="ノイズ強度（タスク依存有: GNSS[m], LiDAR/vision 正規化）"
    )
    r.add_argument("--viz", action="store_true", help="matplotlib 等で簡易可視化を保存")
    e = sp.add_parser("eval", help="result.json から再評価")
    e.add_argument("--task", type=str, default=None)
    e.add_argument("--result", required=True, type=str)
    e.add_argument("--out", type=str, default=None, help="上書き保存先（省略時 result と同じ）")
    e.add_argument("--ground-truth", type=str, default=None, dest="ground_truth")
    c = sp.add_parser("compare", help="results 配下の JSON を比較表に")
    c.add_argument("--dir", required=True, type=str, help="*.json を列挙するディレクトリ")
    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "run":
        return cmd_run(args)
    if args.command == "eval":
        return cmd_eval(args)
    if args.command == "compare":
        return cmd_compare(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
