#!/usr/bin/env python3
"""
同梱 data で `bench run` x5 → docs/benchmarks/<model>.json を上書きし、
任意で `gen_benchmark_summary.py` で SUMMARY.md を再生成。

例:
  BENCH_EXECUTED_BY="CI $(hostname)" python3 scripts/refresh_benchmark_docs.py
  python3 scripts/refresh_benchmark_docs.py --models baseline
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import platform
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# `scripts/*.py` から repo root を解決
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TASKS: list[tuple[str, str]] = [
    ("gnss", "data/gnss/sample.nmea"),
    ("lidar", "data/lidar/points.npy"),
    ("vision", "data/vision/sample.jpg"),
    ("planning", "data/planning/scenario.json"),
    ("control", "data/control/scenario.json"),
]

# 既定は「実装が実際に動く」モデルを優先（Impl が 0/5 になる行は主要扱いしない）
DEFAULT_MODELS = (
    "baseline",
    "opencode-go_kimi-k2.6",
    "opencode-go_qwen3.6-plus",
    "opencode-go_deepseek-v4-pro",
)


def _rel_to_repo(root: Path, abs_p: str) -> str:
    if not abs_p:
        return ""
    p = Path(abs_p).resolve()
    try:
        return str(p.relative_to(root.resolve()))
    except ValueError:
        return str(p)


def _model_filename(model: str) -> str:
    s = model.replace("\\", "-").replace("/", "-")
    if not s or s == "." or s == "..":
        raise ValueError(f"invalid model: {model!r}")
    return f"{s}.json"


def _invoke_bench(argv: list[str]) -> int:
    import cli.main

    with contextlib.redirect_stdout(io.StringIO()):
        return cli.main.main(argv)


def _one_model_snapshot(model: str, tmp: Path) -> dict[str, Any]:
    out: dict[str, Any] = {"tasks": {}}
    for task, inp_rel in TASKS:
        inp = ROOT / inp_rel
        if not inp.is_file():
            raise FileNotFoundError(f"missing: {inp}")
        outj = tmp / f"{model}_{task}.json"
        code = _invoke_bench(
            [
                "run",
                "--task",
                task,
                "--input",
                str(inp),
                "--model",
                model,
                "--out",
                str(outj),
            ]
        )
        if code != 0:
            raise RuntimeError(f"bench run failed: model={model!r} task={task!r} code={code}")
        d = json.loads(outj.read_text(encoding="utf-8"))
        abs_in = d.get("input", "")
        tblock: dict[str, Any] = {
            "input": _rel_to_repo(ROOT, str(abs_in)) or inp_rel,
            "runtime_ms": d.get("runtime_ms"),
            "metrics": d.get("metrics", {}),
        }
        for k in ("quality_pass", "task_spec", "impl"):
            if k in d:
                tblock[k] = d[k]
        out["tasks"][task] = tblock
    return out


def _wrap_snapshot(
    model: str,
    tasks_block: dict[str, Any],
    *,
    date_utc: str,
) -> dict[str, Any]:
    host_note = os.environ.get(
        "BENCH_HOST_NOTE",
        "model_registry 未登録の model は baseline 実装（指標は同梱デモ自己整合）",
    )
    ex = os.environ.get(
        "BENCH_EXECUTED_BY",
        f"scripts/refresh_benchmark_docs.py @ {platform.node()}",
    )
    return {
        "model": model,
        "date_utc": date_utc,
        "executed_by": ex,
        "host_note": host_note,
        "bench_version_hint": "llm-robot-algo-bench: repo data/* snapshot",
        "tasks": tasks_block["tasks"],
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description="docs/benchmarks の正式スナップショットを bench run で再取得する",
    )
    ap.add_argument(
        "--models",
        type=str,
        default=",".join(DEFAULT_MODELS),
        help=f"カンマ区切り（既定: {','.join(DEFAULT_MODELS)}）",
    )
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "docs" / "benchmarks",
        help="JSON 保存先",
    )
    ap.add_argument(
        "--no-summary",
        action="store_true",
        help="gen_benchmark_summary.py を走らせない",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="書き出しとサマリをスキップ（検証用）",
    )
    args = ap.parse_args()
    models = [m.strip() for m in args.models.split(",") if m.strip()]
    if not models:
        print("--models が空です", file=sys.stderr)
        return 2
    out_dir: Path = args.out_dir
    if not out_dir.is_dir():
        print(f"out-dir はディレクトリにしてください: {out_dir}", file=sys.stderr)
        return 2
    now = datetime.now(timezone.utc)
    date_utc = now.strftime("%Y-%m-%d")
    for model in models:
        fn = _model_filename(model)
        with tempfile.TemporaryDirectory(prefix="bench_snap_") as td:
            tmp = Path(td)
            snap = _one_model_snapshot(model, tmp)
            doc = _wrap_snapshot(model, snap, date_utc=date_utc)
            target = (out_dir / fn).resolve()
        if not args.dry_run:
            target.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {target.relative_to(ROOT)}" if not args.dry_run else f"[dry-run] would write {target}")
    if not args.dry_run and not args.no_summary:
        g = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "gen_benchmark_summary.py")],
            cwd=ROOT,
            check=False,
        )
        if g.returncode != 0:
            return g.returncode
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        try:
            sys.stdout.close()
        except Exception:
            pass
        raise SystemExit(0)
