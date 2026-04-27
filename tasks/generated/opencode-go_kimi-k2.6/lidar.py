from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import numpy as np

from tasks.lidar.io import load_point_cloud


def run_lidar(
    input_path: Path,
    model: str = "baseline",
    eps: float = 0.4,
    min_samples: int = 5,
    noise_std: float = 0.0,
) -> Dict[str, Any]:
    _ = model
    pts = load_point_cloud(input_path)
    if noise_std and noise_std > 0.0:
        rng = np.random.default_rng(1)
        pts = np.asarray(pts, dtype=float) + rng.normal(0.0, noise_std, size=pts.shape)
    labels = _spatial_dbscan(pts, eps, min_samples)
    return {
        "cluster_labels": labels.tolist(),
        "n_points": int(pts.shape[0]),
    }


def _spatial_dbscan(pts: np.ndarray, eps: float, min_samples: int) -> np.ndarray:
    n = pts.shape[0]
    labels = np.full(n, -1, dtype=int)
    cell_size = eps
    grid: dict[tuple[int, ...], list[int]] = {}
    for i, p in enumerate(pts):
        cell = tuple(np.floor(p / cell_size).astype(int))
        grid.setdefault(cell, []).append(i)
    dim = pts.shape[1]
    offsets = np.array(list(np.ndindex(*([3] * dim))), dtype=int) - 1
    eps2 = eps * eps

    def _neighbors(idx: int) -> list[int]:
        p = pts[idx]
        cell = np.floor(p / cell_size).astype(int)
        result: list[int] = []
        for off in offsets:
            c = tuple(cell + off)
            if c in grid:
                for j in grid[c]:
                    if j != idx and ((pts[j] - p) ** 2).sum() <= eps2:
                        result.append(j)
        return result

    cluster_id = 0
    for i in range(n):
        if labels[i] != -1:
            continue
        nbrs = _neighbors(i)
        if len(nbrs) < min_samples - 1:
            continue
        labels[i] = cluster_id
        seeds = nbrs[:]
        for j in nbrs:
            labels[j] = cluster_id
        q = 0
        while q < len(seeds):
            cur = seeds[q]
            q += 1
            cur_nbrs = _neighbors(cur)
            if len(cur_nbrs) >= min_samples - 1:
                for k in cur_nbrs:
                    if labels[k] == -1:
                        labels[k] = cluster_id
                        seeds.append(k)
        cluster_id += 1
    return labels
