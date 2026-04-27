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
from utils.task_spec import TASK_SPEC

BDIR = ROOT / "docs" / "benchmarks"
# 表示順: bench
BENCH_PREFERRED = (
    "baseline",
    "composer-2-fast",
    "opus-4.7",
)


def _load_bench(path: Path) -> dict:
    d = json.loads(path.read_text(encoding="utf-8"))
    if d.get("kind") == "opencode_run_smoke" or "tasks" not in d or "model" not in d:
        return {}
    return d


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


def _ac_summary(tasks: dict) -> tuple[str, str]:
    """
    returns:
      - ac: 例 "4/5"
      - impl: 例 "3/5"（フォールバック無し=自前実装が動いたタスク数）
    """
    total = 0
    ac = 0
    impl = 0
    for k in ("gnss", "lidar", "vision", "planning", "control"):
        t = tasks.get(k, {})
        if not isinstance(t, dict):
            continue
        total += 1
        if t.get("quality_pass") is True:
            ac += 1
        im = t.get("impl", {})
        if isinstance(im, dict) and im.get("used_fallback") is False:
            impl += 1
    if total <= 0:
        return ("—", "—")
    return (f"{ac}/{total}", f"{impl}/{total}")

def _priority_section() -> str:
    return """## 評価の優先順位（このリポ）

1. **`metrics` / `quality_pass`** … 同梱データで**仕様を満たしたか**（主指標）
2. **`impl.code_metrics`** … 実際に走った実装の**ソース規模・分岐の目安**（アルゴリズム/コード難易の補助。**`runtime_ms` とは独立**）
3. **`task_spec.difficulty_tier`** … **出題上**の段階（1=軽め 3=重め。タスク種別の違い）
4. **`runtime_ms`** … 参考（再現比較には使えるが、主目的ではない）

"""


def _task_tier_table() -> str:
    lines: list[str] = [
        "## タスク別・出題上の難易度（`task_spec`）\n",
        "| タスク | tier | 系統 | メモ |",
        "|--------|------|------|------|",
    ]
    for t in ("gnss", "lidar", "vision", "planning", "control"):
        s = TASK_SPEC[t]
        lines.append(
            f"| `{t}` | {s['difficulty_tier']} | {s['family']} | {s['blurb']} |"
        )
    lines.append("")
    return "\n".join(lines) + "\n"


def main() -> None:
    files: dict[str, dict] = {}
    for p in sorted(BDIR.glob("*.json")):
        d = _load_bench(p)
        if d:
            files[d["model"]] = d
    # 順序: bench preferred → 残り
    order: list[str] = []
    for m in BENCH_PREFERRED:
        if m in files:
            order.append(m)
    for m in sorted(files):
        if m not in order:
            order.append(m)
    if not order:
        print("no benchmark json found")
        return

    lines: list[str] = []
    lines.append("# ベンチ結果（一覧）\n")
    lines.append(_priority_section())
    lines.append(_task_tier_table())
    lines.append(
        "同梱 `data/*` で `bench run` した**クイック表**。"
        " **正しさ・合格**は各 `docs/benchmarks/<model>.json` の `metrics` / `quality_pass`、**コードの重さ**は `impl.code_metrics` を見る。"
        " 未登録 `model` は **baseline 実装**にフォールバック（`impl.used_fallback`）。\n"
    )
    lines.append("| モデル | AC (`quality_pass`) | Impl (`!fallback`) | gnss (ms) | lidar (ms) | vision (ms) | planning (ms) | control (ms) | 5 タスク計 (ms) |")
    lines.append("|--------|--------------------|-------------------|-----------|------------|-------------|---------------|--------------|------------|")
    for m in order:
        if m in files:
            t = files[m].get("tasks", {})
            ac_s, impl_s = _ac_summary(t if isinstance(t, dict) else {})
            acc = 0.0
            rts = []
            for k in ("gnss", "lidar", "vision", "planning", "control"):
                ms = t.get(k, {}).get("runtime_ms")
                if ms is not None:
                    acc += float(ms)
                rts.append(_fmt_ms(ms) if ms is not None else "—")
            lines.append(
                f"| `{m}` | **{ac_s}** | {impl_s} | {rts[0]} | {rts[1]} | {rts[2]} | {rts[3]} | {rts[4]} | **~{_fmt_ms(acc)}** |"
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
        " 合計は 5 タスク `runtime_ms` の和。\n"
    )
    if tot_items:
        lines.append(runtime_bars_code_block(tot_items))

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

    lines.append("## 品質・合格（`quality_pass` と `metrics`）\n")
    q = (
        "同梱デモでは **bench** 系は `quality_pass` が真になりやすい（各 JSON → `tasks.<task>.quality_pass`）。"
        " 精査は**生の** `metrics`。**出題難易**は `task_spec`、**実装の重さ**は `impl.code_metrics`（速さとは別）。"
        " **OpenCode Go 行**に品質指標はない。"
    )
    lines.append(f"{q}\n")
    lines.append("## 元データ（JSON）\n")
    for p in sorted(BDIR.glob("*.json")):
        d = _load_bench(p)
        if d:
            lines.append(f"- [`{d['model']}`]({p.name})")
    out = BDIR / "SUMMARY.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
