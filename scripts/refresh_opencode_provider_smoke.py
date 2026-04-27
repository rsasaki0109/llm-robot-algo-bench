#!/usr/bin/env python3
"""
`opencode run` を複数 model で実行し、docs/benchmarks/opencode_provider_smoke.json を上書き。
**既定は OpenCode Go**（`opencode-go/...`）。続けて `gen_benchmark_summary.py` で [SUMMARY.md](docs/benchmarks/SUMMARY.md) の疎通行を更新。API / 契約 / ネット必須。

  python3 scripts/refresh_opencode_provider_smoke.py
  OPENCODE_MODELS=opencode-go/kimi-k2.6,opencode-go/qwen3.6-plus  python3 ...
  OPENCODE_RUN_TIMEOUT=300  # 秒（60〜3600。既定 900。shell の bench_opencode_smoke と同趣旨）
"""
from __future__ import annotations

import json
import os
import platform
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "benchmarks" / "opencode_provider_smoke.json"

PROMPT = "Reply in exactly 5 words: provider smoke test OK"
# OpenCode Go: 2.5 / flash 等の旧行は廃止し、2.6・qwen3.6+・v4 pro を既定に
DEFAULT_MODELS = (
    "opencode-go/kimi-k2.6",
    "opencode-go/qwen3.6-plus",
    "opencode-go/deepseek-v4-pro",
)
ANSI_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")


def _strip_ansi(s: str) -> str:
    return ANSI_RE.sub("", s)


def _excerpt(s: str, n: int = 280) -> str:
    t = _strip_ansi(s).strip()
    if len(t) <= n:
        return t
    return t[: n - 1] + "…"


def _coerce_timeout() -> float:
    raw = os.environ.get("OPENCODE_RUN_TIMEOUT", "900")
    try:
        t = int(raw)
    except ValueError:
        t = 900
    if t == 0:
        t = 900
    t = max(60, min(t, 3600))
    return float(t)


def _run_one(model: str, timeout: float) -> dict[str, Any]:
    t0 = time.perf_counter()
    try:
        p = subprocess.run(
            ["opencode", "run", "-m", model, PROMPT],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
        )
    except subprocess.TimeoutExpired as e:
        wall = (time.perf_counter() - t0) * 1000.0
        return {
            "model": model,
            "exit_code": -9,
            "ok": False,
            "wall_ms": round(wall, 1),
            "stdout_excerpt": _excerpt(e.stdout or ""),
            "stderr_excerpt": _excerpt("timeout: " + (e.stderr or "")),
        }
    except FileNotFoundError:
        return {
            "model": model,
            "exit_code": 127,
            "ok": False,
            "wall_ms": 0.0,
            "stdout_excerpt": "",
            "stderr_excerpt": "opencode コマンドが見つかりません。PATH を確認。",
        }
    except OSError as e:
        return {
            "model": model,
            "exit_code": 1,
            "ok": False,
            "wall_ms": 0.0,
            "stdout_excerpt": "",
            "stderr_excerpt": _excerpt(str(e)),
        }
    wall = (time.perf_counter() - t0) * 1000.0
    return {
        "model": model,
        "exit_code": p.returncode,
        "ok": p.returncode == 0,
        "wall_ms": round(wall, 1),
        "stdout_excerpt": _excerpt(p.stdout or ""),
        "stderr_excerpt": _excerpt(p.stderr or ""),
    }


def main() -> int:
    raw = os.environ.get("OPENCODE_MODELS", ",".join(DEFAULT_MODELS))
    models = [m.strip() for m in raw.split(",") if m.strip()]
    if not models:
        print("OPENCODE_MODELS / 既定 model が空です", file=sys.stderr)
        return 2
    to = _coerce_timeout()
    ex = os.environ.get(
        "BENCH_EXECUTED_BY",
        f"scripts/refresh_opencode_provider_smoke.py @ {platform.node()}",
    )
    doc: dict[str, Any] = {
        "kind": "opencode_run_smoke",
        "date_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "executed_by": ex,
        "prompt": PROMPT,
        "note": "bench の --model とは無関係。OpenCode CLI の疎通確認用。",
        "models": [],
    }
    for m in models:
        print(f"opencode run -m {m!r} ... (timeout {int(to)}s)", file=sys.stderr)
        row = _run_one(m, to)
        doc["models"].append(row)
        print(f"  -> ok={row['ok']} wall_ms={row['wall_ms']}", file=sys.stderr)
    out_path = OUT
    out_path.write_text(
        json.dumps(doc, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {out_path.relative_to(ROOT)}")
    return 0 if all(x.get("ok") for x in doc["models"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
