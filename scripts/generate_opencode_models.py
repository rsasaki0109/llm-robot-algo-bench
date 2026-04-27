#!/usr/bin/env python3
"""
OpenCode の provider/model を使って各タスク実装を生成し、bench に載せる。

- 生成先: tasks/generated/<bench_model>/<task>.py
- bench 側では `--model <bench_model>` を指定すると動的 import で呼ばれる（runner/model_registry.py）

例:
  OPENCODE_MODEL=opencode-go/kimi-k2.6 python3 scripts/generate_opencode_models.py
  OPENCODE_MODEL=opencode-go/qwen3.6-plus OPENCODE_RUN_TIMEOUT=600 python3 scripts/generate_opencode_models.py
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / "tasks" / "generated"

TASKS: dict[str, str] = {
    "gnss": "tasks/gnss/baseline.py",
    "lidar": "tasks/lidar/baseline.py",
    "vision": "tasks/vision/baseline.py",
    "planning": "tasks/planning/baseline.py",
    "control": "tasks/control/baseline.py",
}


def _coerce_timeout() -> int:
    raw = os.environ.get("OPENCODE_RUN_TIMEOUT", "600")
    try:
        t = int(raw)
    except ValueError:
        t = 600
    t = max(60, min(t, 3600))
    return t


def _bench_slug(opencode_model: str) -> str:
    # `bench --model` にそのまま使うので / を _ に潰す
    s = opencode_model.strip()
    s = s.replace("/", "_")
    s = re.sub(r"[^a-zA-Z0-9_.-]+", "-", s)
    return s


def _extract_python(text: str) -> str:
    # ```python ... ``` or ``` ... ```
    m = re.search(r"```python\\s*(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
    if not m:
        m = re.search(r"```\\s*(.*?)```", text, flags=re.DOTALL)
    if m:
        return m.group(1).strip() + "\n"
    # fallback: drop leading non-code chatter by finding first code-looking line
    lines = text.splitlines()
    start: int | None = None
    for i, line in enumerate(lines):
        s = line.lstrip()
        if s.startswith(("from ", "import ", "def ", "class ")):
            start = i
            break
    if start is None:
        return text.strip() + "\n"
    return "\n".join(lines[start:]).strip() + "\n"


def _is_valid_python(path: Path) -> bool:
    try:
        src = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    try:
        ast.parse(src, filename=str(path))
        return True
    except SyntaxError:
        return False


def _prompt_for(task: str, baseline_path: str) -> str:
    # 重要: “モジュール全文を出力”を強制（JSON/説明は不要）
    header = (
        "Output MUST start with exactly this line:\n"
        "from __future__ import annotations\n\n"
    )
    if task == "gnss":
        return header + (
            "You will write a new implementation for the GNSS task.\n"
            "Keep the same public API as run_gnss in the attached baseline file.\n"
            "Return a single self-contained Python module body ONLY.\n"
            "- Signature: run_gnss(input_path: Path, model: str='baseline', noise_m: float=0.0) -> dict\n"
            "- Output keys: enu_trajectory(list of {t_s,e_m,n_m,u_m}), speed_m_s(list)\n"
            "- You may reuse tasks.gnss.nmea.\n"
            "Do not include Markdown fences or explanations.\n"
        )
    if task == "lidar":
        return header + (
            "Write a new implementation for the LiDAR task.\n"
            "Keep the same public API as run_lidar in the attached baseline file.\n"
            "Return a single self-contained Python module body ONLY.\n"
            "- Signature: run_lidar(input_path: Path, model: str='baseline', eps: float=0.4, min_samples: int=5, noise_std: float=0.0) -> dict\n"
            "- Output keys: cluster_labels(list[int]), n_points(int)\n"
            "Do not include Markdown fences or explanations.\n"
        )
    if task == "vision":
        return header + (
            "Write a new implementation for the vision task.\n"
            "Keep the same public API as run_vision in the attached baseline file.\n"
            "Return a single self-contained Python module body ONLY.\n"
            "- Signature: run_vision(input_path: Path, model: str='baseline', noise_std: float=0.0) -> dict\n"
            "- Output keys: detections(list of {x,y,w,h,score})\n"
            "Do not include Markdown fences or explanations.\n"
        )
    if task == "planning":
        return header + (
            "Write a new implementation for the planning task.\n"
            "Keep the same public API as run_planning in the attached baseline file.\n"
            "Return a single self-contained Python module body ONLY.\n"
            "- Signature: run_planning(input_path: Path, model: str='baseline', noise: float=0.0) -> dict\n"
            "- Output keys: path(list of [row,col])\n"
            "Do not include Markdown fences or explanations.\n"
        )
    if task == "control":
        return header + (
            "Write a new implementation for the control task.\n"
            "Keep the same public API as run_control in the attached baseline file.\n"
            "Return a single self-contained Python module body ONLY.\n"
            "- Signature: run_control(input_path: Path, model: str='baseline', noise: float=0.0) -> dict\n"
            "- Output keys: trajectory(list[float]), p_ref(list[float])\n"
            "Do not include Markdown fences or explanations.\n"
        )
    raise ValueError(task)


def main() -> int:
    opencode_model = os.environ.get("OPENCODE_MODEL", "").strip()
    if not opencode_model:
        print("OPENCODE_MODEL が必要です（例: opencode-go/kimi-k2.6）", file=sys.stderr)
        return 2
    if not shutil.which("opencode"):
        print("opencode が PATH にありません", file=sys.stderr)
        return 2
    timeout_s = _coerce_timeout()
    bench_model = _bench_slug(opencode_model)
    out_dir = GEN / bench_model
    out_dir.mkdir(parents=True, exist_ok=True)

    for task, baseline_rel in TASKS.items():
        baseline = ROOT / baseline_rel
        if not baseline.is_file():
            print(f"missing: {baseline}", file=sys.stderr)
            return 2
        out_path = out_dir / f"{task}.py"
        if out_path.is_file() and out_path.stat().st_size > 0 and _is_valid_python(out_path):
            print(f"skip (exists): {bench_model} / {task}", file=sys.stderr)
            continue
        prompt = _prompt_for(task, baseline_rel)
        print(f"generate: {bench_model} / {task}", file=sys.stderr)
        try:
            p = subprocess.run(
                ["opencode", "run", "-m", opencode_model, "-f", str(baseline), "--", prompt],
                capture_output=True,
                text=True,
                timeout=timeout_s,
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
            )
        except subprocess.TimeoutExpired:
            print(f"timeout: {task}", file=sys.stderr)
            return 1
        if p.returncode != 0:
            print(p.stderr, file=sys.stderr)
            return p.returncode
        out_text = p.stdout or ""
        m = re.search(r"Solution written to `([^`]+)`", out_text)
        if m:
            written = (ROOT / m.group(1)).resolve()
            try:
                mod = written.read_text(encoding="utf-8", errors="replace")
            except OSError:
                mod = _extract_python(out_text)
        else:
            mod = _extract_python(out_text)
        try:
            ast.parse(mod, filename=str(out_path))
        except SyntaxError:
            dbg = out_path.with_suffix(".raw.txt")
            dbg.write_text(out_text, encoding="utf-8")
            print(f"invalid python output: {task} (saved {dbg})", file=sys.stderr)
            return 1
        out_path.write_text(mod, encoding="utf-8")
    print(bench_model)
    return 0


if __name__ == "__main__":
    import shutil

    raise SystemExit(main())

