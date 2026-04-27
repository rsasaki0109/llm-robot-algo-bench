from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import numpy as np


def run_control(
    input_path: Path,
    model: str = "baseline",
    noise: float = 0.0,
) -> Dict[str, Any]:
    _ = model
    spec = json.loads(input_path.read_text(encoding="utf-8"))
    dt = float(spec["dt"])
    p_ref: List[float] = [float(x) for x in spec["p_ref"]]
    p0 = float(spec["p0"])
    K = float(spec.get("K", 4.0))
    u_max = float(spec.get("u_max", 1.0))
    rng = np.random.default_rng(11) if noise > 0.0 else None

    p = p0
    traj: List[float] = [p]
    for k in range(len(p_ref) - 1):
        r = p_ref[k]
        u = K * (r - p)
        if rng is not None:
            u += float(rng.normal(0, noise))
        u = max(-u_max, min(u_max, u))
        p = p + u * dt
        traj.append(p)
    return {
        "trajectory": traj,
        "p_ref": p_ref,
    }
