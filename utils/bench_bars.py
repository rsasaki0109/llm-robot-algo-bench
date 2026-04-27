"""ASCII 横棒（runtime などの相対比較用）。等幅想定のテキストブロックを返す。"""
from __future__ import annotations


def _bar_fill(value: float, vmax: float, width: int) -> str:
    if vmax <= 0:
        vmax = 1.0
    n = int(round(width * (max(0.0, value) / vmax)))
    n = min(max(n, 0), width)
    return "█" * n + "·" * (width - n)


def _fmt_ms(val: float) -> str:
    if val < 1:
        return f"{val:.2f} ms"
    if val < 10:
        return f"{val:.1f} ms"
    return f"{val:.0f} ms"


def runtime_bars_code_block(
    items: list[tuple[str, float]],
    *,
    bar_width: int = 22,
    caption: str = "",
) -> str:
    """`items`: (左ラベル, 数値[ms])。最長=フル幅に正規化。空なら空文字。"""
    if not items:
        return ""
    values = [v for _, v in items if v is not None]
    if not values:
        return ""
    vmax = max(max(values), 1e-12)
    wlab = min(max(len(lab) for lab, _ in items), 36)
    lines: list[str] = []
    if caption:
        lines.append(caption)
    for lab, val in items:
        bar = _bar_fill(val, vmax, bar_width)
        sval = _fmt_ms(float(val)) if val is not None else "—"
        lines.append(f"{lab:<{wlab}}  {bar}  {sval}")
    body = "\n".join(lines)
    return f"```\n{body}\n```\n"
