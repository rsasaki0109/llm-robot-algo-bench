from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.neighbors import NearestNeighbors

from tasks.lidar.io import load_point_cloud


def _statistical_outlier_removal(
    pts: np.ndarray,
    k: int = 20,
    std_mul: float = 2.0,
) -> np.ndarray:
    """Remove points whose mean distance to k nearest neighbors exceeds mean + std_mul*std."""
    if pts.shape[0] <= k:
        return pts
    nbrs = NearestNeighbors(n_neighbors=k, metric="euclidean", algorithm="auto")
    nbrs.fit(pts)
    distances, _ = nbrs.kneighbors(pts)
    mean_dists = distances[:, 1:].mean(axis=1)
    threshold = mean_dists.mean() + std_mul * mean_dists.std()
    mask = mean_dists <= threshold
    return pts[mask]


def run_lidar(
    input_path: Path,
    model: str = "baseline",
    eps: float = 0.4,
    min_samples: int = 5,
    noise_std: float = 0.0,
) -> Dict[str, Any]:
    pts = load_point_cloud(input_path)
    pts = np.asarray(pts, dtype=np.float64)

    if noise_std > 0.0:
        rng = np.random.default_rng(42)
        pts = pts + rng.normal(0.0, noise_std, size=pts.shape)

    if pts.shape[0] > 100:
        pts = _statistical_outlier_removal(pts, k=min(20, pts.shape[0] - 1))

    if pts.shape[0] == 0:
        return {
            "cluster_labels": [],
            "n_points": 0,
        }

    clustering = DBSCAN(eps=eps, min_samples=min_samples, metric="euclidean")
    labels = clustering.fit_predict(pts)

    return {
        "cluster_labels": labels.tolist(),
        "n_points": int(pts.shape[0]),
    }
