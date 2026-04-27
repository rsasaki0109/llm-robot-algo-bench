"""
実装**ソース**の難易度の目安（静的・参考値）。

- `loc` / `n_functions` / `approx_decision_nodes` など
- 速さ（runtime）とは独立
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Any, Dict, Optional

_DECISION = (
    ast.If,
    ast.For,
    ast.While,
    ast.ExceptHandler,
    ast.With,
    ast.Assert,
    ast.Match,
    ast.Try,
)


def analyze_python_path(path: str | Path) -> Optional[Dict[str, Any]]:
    p = Path(path)
    if not p.is_file() or p.suffix != ".py":
        return None
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    loc = max(0, len([line for line in text.splitlines() if line.strip()]))
    try:
        tree = ast.parse(text, filename=str(p))
    except SyntaxError:
        return {"file": str(p), "loc": loc, "parse_ok": False}

    n_fn = 0
    n_async = 0
    n_decision = 0
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            n_fn += 1
        if isinstance(n, ast.AsyncFunctionDef):
            n_async += 1
        if isinstance(n, _DECISION):
            n_decision += 1
    return {
        "file": str(p.resolve()),
        "loc": loc,
        "parse_ok": True,
        "n_functions": n_fn,
        "n_async_functions": n_async,
        "approx_decision_nodes": n_decision,
    }
