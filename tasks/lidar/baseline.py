from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import numpy as np
from sklearn.cluster import DBSCAN

from tasks.lidar.io import load_point_cloud


def run_lidar(
    input_path: Path,
    model: str = "baseline",
    eps: float = 0.4,
    min_samples: int = 5,
    noise_std: float = 0.0,
) -> Dict[str, Any]:
    """
    DBSCAN クラスタリング。将来は model 差し替えで別アルゴを実行。
    """
    _ = model
    pts = load_point_cloud(input_path)
    if noise_std and noise_std > 0.0:
        rng = np.random.default_rng(1)
        pts = np.asarray(pts, dtype=float) + rng.normal(0.0, noise_std, size=pts.shape)
    dbs = DBSCAN(eps=eps, min_samples=min_samples)
    labels = dbs.fit_predict(pts).astype(int)
    return {
        "cluster_labels": labels.tolist(),
        "n_points": int(pts.shape[0]),
    }
