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
    spec = json.loads(input_path.read_text(encoding="utf-8"))
    dt = float(spec["dt"])
    p_ref: List[float] = [float(x) for x in spec["p_ref"]]
    p0 = float(spec["p0"])
    K = float(spec.get("K", 4.0))
    u_max = float(spec.get("u_max", 1.0))
    rng = np.random.default_rng(11) if noise > 0.0 else None

    p = p0
    traj: List[float] = [p]

    if model == "baseline":
        # Deadbeat controller: optimal one-step tracking for a pure integrator.
        for k in range(len(p_ref) - 1):
            u = (p_ref[k + 1] - p) / dt
            if rng is not None:
                u += float(rng.normal(0, noise))
            u = max(-u_max, min(u_max, u))
            p += u * dt
            traj.append(p)

    elif model == "proportional":
        # Original proportional controller (backward compatibility).
        for k in range(len(p_ref) - 1):
            u = K * (p_ref[k] - p)
            if rng is not None:
                u += float(rng.normal(0, noise))
            u = max(-u_max, min(u_max, u))
            p += u * dt
            traj.append(p)

    elif model == "pid":
        # PID with anti-windup and feedforward reference velocity.
        Kp = K
        Ki = K * 0.5
        Kd = K * 0.1
        integral = 0.0
        prev_error = 0.0
        for k in range(len(p_ref) - 1):
            e = p_ref[k] - p
            integral += e * dt
            derivative = (e - prev_error) / dt if k > 0 else 0.0
            u = Kp * e + Ki * integral + Kd * derivative
            # Add feedforward for the reference velocity
            if k + 1 < len(p_ref):
                u += (p_ref[k + 1] - p_ref[k]) / dt
            if rng is not None:
                u += float(rng.normal(0, noise))
            u_sat = max(-u_max, min(u_max, u))
            # Anti-windup: do not integrate if saturated
            if u != u_sat:
                integral -= e * dt
            p += u_sat * dt
            traj.append(p)
            prev_error = e

    elif model == "mpc":
        # Receding-horizon MPC with quadratic control cost.
        N = min(20, len(p_ref) - 1)
        lambda_u = 0.01
        for k in range(len(p_ref) - 1):
            N_k = min(N, len(p_ref) - k - 1)
            if N_k <= 0:
                u = 0.0
            else:
                S = np.tril(np.ones((N_k, N_k)))
                R = np.array(p_ref[k + 1:k + 1 + N_k])
                ones = np.ones(N_k)
                H = dt * dt * (S.T @ S) + lambda_u * np.eye(N_k)
                g = dt * S.T @ (R - p * ones)
                U = np.linalg.solve(H, g)
                u = float(U[0])
            if rng is not None:
                u += float(rng.normal(0, noise))
            u = max(-u_max, min(u_max, u))
            p += u * dt
            traj.append(p)

    else:
        raise ValueError(f"Unknown model: {model}")

    return {
        "trajectory": traj,
        "p_ref": p_ref,
    }
