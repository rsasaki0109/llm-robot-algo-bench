#!/usr/bin/env python3
"""
docs/benchmarks/*.json から docs/benchmarks/SUMMARY.md を再生成。

スナップショット JSON 自体を同梱データで取り直す場合は
`scripts/refresh_benchmark_docs.py`（このスクリプトを続けて実行）。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils.bench_bars import runtime_bars_code_block

BDIR = ROOT / "docs" / "benchmarks"
# 表示順: bench
BENCH_PREFERRED = (
    "baseline",
    "composer-2-fast",
    "opus-4.7",
)
# 表示順: OpenCode **Go** 疎通（[opencode_provider_smoke.json](...) の `opencode-go/...` 行。更新は下記スクリプト）
OPENCODE_PREFERRED = (
    "opencode-go/kimi-k2.6",
    "opencode-go/qwen3.6-plus",
    "opencode-go/deepseek-v4-pro",
)
OPENCODE_SMOKE_PATH = "opencode_provider_smoke.json"


def _load_bench(path: Path) -> dict:
    d = json.loads(path.read_text(encoding="utf-8"))
    if d.get("kind") == "opencode_run_smoke" or "tasks" not in d or "model" not in d:
        return {}
    return d


def _load_opencode_smoke(path: Path) -> dict[str, float]:
    if not path.is_file():
        return {}
    d = json.loads(path.read_text(encoding="utf-8"))
    if d.get("kind") != "opencode_run_smoke" or not isinstance(d.get("models"), list):
        return {}
    out: dict[str, float] = {}
    for e in d["models"]:
        if not isinstance(e, dict):
            continue
        m = e.get("model")
        w = e.get("wall_ms")
        if m and isinstance(m, str) and w is not None:
            try:
                out[m] = float(w)
            except (TypeError, ValueError):
                continue
    return out


def _fmt_ms(x: object) -> str:
    try:
        v = float(x)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return "—"
    if v < 1:
        return f"{v:.2f}"
    if v < 10:
        return f"{v:.1f}"
    return f"{v:.0f}"


def _order_opencode_ids(oc: dict[str, float]) -> list[str]:
    out: list[str] = []
    for m in OPENCODE_PREFERRED:
        if m in oc and m not in out:
            out.append(m)
    for m in sorted(oc):
        if m not in out:
            out.append(m)
    return out


def main() -> None:
    files: dict[str, dict] = {}
    for p in sorted(BDIR.glob("*.json")):
        d = _load_bench(p)
        if d:
            files[d["model"]] = d
    opencode_smoke: dict[str, float] = _load_opencode_smoke(
        BDIR / OPENCODE_SMOKE_PATH
    )
    # 順序: bench preferred → 残り → opencode preferred → 残り
    order: list[str] = []
    for m in BENCH_PREFERRED:
        if m in files:
            order.append(m)
    for m in sorted(files):
        if m not in order:
            order.append(m)
    for m in _order_opencode_ids(opencode_smoke):
        if m not in order:
            order.append(m)
    if not order:
        print("no benchmark json found")
        return

    lines: list[str] = []
    lines.append("# ベンチ結果（一覧）\n")
    lines.append(
        "同梱 `data/*` の **`bench run` → `runtime_ms` の一覧**（**品質**は各 JSON の `metrics` 参照。未登録 `model` は **baseline 実装**のため**数値は同系**）。\n"
    )
    if opencode_smoke:
        lines.append(
            f"**OpenCode Go** 行（`opencode-go/...`）は 5 タスク未実施（`—`）。"
            f" 最右列 *疎通* は [docs/benchmarks/{OPENCODE_SMOKE_PATH}]({OPENCODE_SMOKE_PATH}) の"
            f" `opencode run` **1 回**の `wall_ms`（**Go 枠**のモデルID・API/ネット依存）。"
            f" 更新: `OPENCODE_MODELS=opencode-go/...` で `python3 scripts/refresh_opencode_provider_smoke.py`"
            f" → 本 SUMMARY 再生成。\n"
        )
    lines.append("| モデル | gnss (ms) | lidar (ms) | vision (ms) | planning (ms) | control (ms) | 5 タスク計 / *疎通* (ms) |")
    lines.append("|--------|-----------|------------|-------------|---------------|--------------|------------|")
    for m in order:
        if m in files:
            t = files[m].get("tasks", {})
            acc = 0.0
            rts = []
            for k in ("gnss", "lidar", "vision", "planning", "control"):
                ms = t.get(k, {}).get("runtime_ms")
                if ms is not None:
                    acc += float(ms)
                rts.append(_fmt_ms(ms) if ms is not None else "—")
            lines.append(
                f"| `{m}` | {rts[0]} | {rts[1]} | {rts[2]} | {rts[3]} | {rts[4]} | **~{_fmt_ms(acc)}** |"
            )
        elif m in opencode_smoke:
            w = opencode_smoke[m]
            lines.append(
                f"| `{m}` | — | — | — | — | — | *疎通 ~{_fmt_ms(w)}* |"
            )
        else:
            continue
    lines.append("")

    # 横棒（`█` = 最長比、`·` = 空き。コードブロックは等幅表示向け）
    tot_items: list[tuple[str, float]] = []
    for m in order:
        if m not in files:
            continue
        t = files[m].get("tasks", {})
        acc = 0.0
        for k in ("gnss", "lidar", "vision", "planning", "control"):
            ms = t.get(k, {}).get("runtime_ms")
            if ms is not None:
                acc += float(ms)
        tot_items.append((f"`{m}`", acc))
    lines.append("## `runtime_ms` 横棒（5 タスク合計、相対）\n")
    lines.append(
        "最長行をフル幅（`█`）に合わせた**相対比**（**絶対速度の主張ではない**）。"
        " 合計は 5 タスク `runtime_ms` の和。**OpenCode Go 行はここに含まない**（疎通は下の専用図）。\n"
    )
    if tot_items:
        lines.append(runtime_bars_code_block(tot_items))
    if opencode_smoke:
        oc_bars: list[tuple[str, float]] = [
            (f"`{k}`", opencode_smoke[k]) for k in _order_opencode_ids(opencode_smoke)
        ]
        lines.append("## OpenCode Go 疎通 `wall_ms` 横棒（1 回 `opencode run`、相対）\n")
        lines.append(
            "5 タスク `bench` とは**別物**（`opencode-go/...`）。最長 `wall_ms` をフル幅（`█`）に合わせた**相対比**。\n"
        )
        lines.append(runtime_bars_code_block(oc_bars))

    task_names = (
        "gnss",
        "lidar",
        "vision",
        "planning",
        "control",
    )
    lines.append("## タスク別 `runtime_ms` 横棒\n")
    lines.append(
        "各タスク内で**モデル同士**を比較（タスク横ではスケールが違うので縦の表と併用）。\n"
    )
    for tk in task_names:
        t_items: list[tuple[str, float]] = []
        for m in order:
            if m not in files:
                continue
            t = files[m].get("tasks", {})
            ms = t.get(tk, {}).get("runtime_ms")
            if ms is not None:
                t_items.append((f"`{m}`", float(ms)))
        if len(t_items) < 1:
            continue
        lines.append(f"### {tk}\n")
        lines.append(runtime_bars_code_block(t_items))

    lines.append("## 品質（要点・同梱自己整合）\n")
    q = (
        "上表の **bench 行**はいずれも **~0 誤差 / 1.0 スコア** 系（NMEA 自己整合、"
        "LiDAR 3 クラ、Vision mAP(簡)~1 等・details は各 `metrics`）。**OpenCode Go 行**に品質指標はない。"
    )
    lines.append(f"{q}\n")
    lines.append("## 元データ（JSON）\n")
    for p in sorted(BDIR.glob("*.json")):
        d = _load_bench(p)
        if d:
            lines.append(f"- [`{d['model']}`]({p.name})")
    if (BDIR / OPENCODE_SMOKE_PATH).is_file():
        lines.append(
            f"- [OpenCode **Go** 疎通（`opencode run` ・上表の `opencode-go/...` 行）]({OPENCODE_SMOKE_PATH})"
        )
    out = BDIR / "SUMMARY.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
