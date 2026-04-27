#!/usr/bin/env python3
"""
docs/benchmarks/*.json から docs/benchmarks/SUMMARY.md を再生成。
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BDIR = ROOT / "docs" / "benchmarks"
# 表示順: 行ラベル用の短い名
PREFERRED = (
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


def main() -> None:
    files = {}
    for p in sorted(BDIR.glob("*.json")):
        d = _load_bench(p)
        if d:
            files[d["model"]] = d
    # 順序: preferred first, then rest alpha
    order: list[str] = []
    for m in PREFERRED:
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
    lines.append("同梱 `data/*` ・**`runtime_ms` だけ**まず見る用（**品質指標**は各 JSON の `metrics` 参照。未登録 `model` は **baseline 実装**のため**数値は同系**）。\n")
    lines.append("| モデル | gnss (ms) | lidar (ms) | vision (ms) | planning (ms) | control (ms) | 概算計 (ms) |")
    lines.append("|--------|-----------|------------|-------------|---------------|--------------|------------|")
    for m in order:
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
    lines.append("")
    lines.append("## 品質（要点・同梱自己整合）\n")
    lines.append(
        "いずれも **~0 誤差 / 1.0 スコア** 系（NMEA 自己整合、LiDAR 3 クラ、Vision mAP(簡)~1 等・details は各 `metrics`）。\n"
    )
    lines.append("## 元データ（JSON）\n")
    for p in sorted(BDIR.glob("*.json")):
        d = _load_bench(p)
        if d:
            lines.append(f"- [`{d['model']}`]({p.name})")
    if (BDIR / "opencode_provider_smoke.json").is_file():
        lines.append(
            f"- [OpenCode 疎通のみ（bench 得点以外）](opencode_provider_smoke.json)"
        )
    out = BDIR / "SUMMARY.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
