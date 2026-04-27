from __future__ import annotations

from pathlib import Path

import numpy as np


def load_point_cloud(path: Path) -> np.ndarray:
    """
    点群: .npy (N,3+)、テキスト PCD (VERSION 7, DATA ascii のみ)
    """
    s = str(path)
    if s.lower().endswith(".npy"):
        arr = np.load(path, allow_pickle=False)
        if arr.ndim != 2 or arr.shape[1] < 3:
            raise ValueError("npy は (N,>=3) 形状を想定")
        return arr[:, :3].astype(float)
    if s.lower().endswith(".pcd"):
        return _load_pcd_ascii(path)
    raise ValueError(f"未サポート拡張子: {path}")


def _load_pcd_ascii(path: Path) -> np.ndarray:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    n = 0
    data_i = 0
    for i, ln in enumerate(lines):
        if ln.upper().startswith("POINTS"):
            n = int(ln.split()[1])
        if ln.upper().startswith("DATA"):
            data_i = i + 1
            break
    pts: list = []
    for j in range(data_i, data_i + n):
        if j >= len(lines):
            break
        p = lines[j].split()
        if len(p) < 3:
            continue
        pts.append((float(p[0]), float(p[1]), float(p[2])))
    if not pts:
        raise ValueError("PCD から有効点が読めません（ascii / POINTS 付き想定）")
    return np.array(pts, dtype=float)
