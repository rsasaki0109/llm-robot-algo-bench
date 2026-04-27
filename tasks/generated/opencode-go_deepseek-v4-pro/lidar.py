from __future__ import annotations

from collections import deque
from pathlib import Path
from typing import Any, Dict

import numpy as np

from tasks.lidar.io import load_point_cloud


def _region_query(pts: np.ndarray, idx: int, eps: float) -> np.ndarray:
    diff = pts - pts[idx]
    sq_dists = np.sum(diff * diff, axis=1)
    return np.where(sq_dists <= eps * eps)[0]


def _euclidean_cluster(pts: np.ndarray, eps: float, min_samples: int) -> np.ndarray:
    n = pts.shape[0]
    labels = np.full(n, -1, dtype=int)
    if n == 0:
        return labels

    visited = np.zeros(n, dtype=bool)
    cluster_id = 0

    for i in range(n):
        if visited[i]:
            continue

        seed = _region_query(pts, i, eps)
        if seed.size < min_samples:
            visited[i] = True
            continue

        seed_set = deque(seed)
        for j in seed:
            visited[j] = True
            labels[j] = cluster_id

        while seed_set:
            idx = seed_set.popleft()
            candidates = _region_query(pts, idx, eps)
            candidates = candidates[~visited[candidates]]
            for cn in candidates:
                visited[cn] = True
                labels[cn] = cluster_id
                seed_set.append(cn)

        cluster_id += 1

    return labels


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

    labels = _euclidean_cluster(pts, eps, min_samples)
    return {
        "cluster_labels": labels.tolist(),
        "n_points": int(pts.shape[0]),
    }
