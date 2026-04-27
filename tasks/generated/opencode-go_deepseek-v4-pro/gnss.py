from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np

from tasks.gnss.nmea import GgaFix, iter_gga_fixes

A_WGS84 = 6378137.0
E2 = 6.69437999014e-3


def lla2ecef(lat_deg: float, lon_deg: float, h_m: float) -> Tuple[float, float, float]:
    lat, lon = math.radians(lat_deg), math.radians(lon_deg)
    n = A_WGS84 / math.sqrt(1.0 - E2 * math.sin(lat) ** 2)
    x = (n + h_m) * math.cos(lat) * math.cos(lon)
    y = (n + h_m) * math.cos(lat) * math.sin(lon)
    z = (n * (1.0 - E2) + h_m) * math.sin(lat)
    return (x, y, z)


def lla2enu(
    lat_deg: float, lon_deg: float, h_m: float,
    lat0: float, lon0: float, h0: float,
) -> Tuple[float, float, float]:
    x, y, z = lla2ecef(lat_deg, lon_deg, h_m)
    x0, y0, z0 = lla2ecef(lat0, lon0, h0)
    dx, dy, dz = x - x0, y - y0, z - z0
    lon0r, lat0r = math.radians(lon0), math.radians(lat0)
    e = -math.sin(lon0r) * dx + math.cos(lon0r) * dy
    n = (
        -math.sin(lat0r) * math.cos(lon0r) * dx
        - math.sin(lat0r) * math.sin(lon0r) * dy
        + math.cos(lat0r) * dz
    )
    u = (
        math.cos(lat0r) * math.cos(lon0r) * dx
        + math.cos(lat0r) * math.sin(lon0r) * dy
        + math.sin(lat0r) * dz
    )
    return (e, n, u)


def _apply_noise_enu(enu: List[Dict[str, float]], sigma: float) -> None:
    if sigma <= 0:
        return
    rng = np.random.default_rng(0)
    for p in enu:
        p["e_m"] = float(p["e_m"] + rng.normal(0, sigma))
        p["n_m"] = float(p["n_m"] + rng.normal(0, sigma))
        p["u_m"] = float(p["u_m"] + rng.normal(0, sigma))


def _rts_smooth_1d(t: np.ndarray, y: np.ndarray, q: float = 1.0, r: float = 0.01) -> np.ndarray:
    """Rauch-Tung-Striebel smoother for constant-velocity 1D model."""
    n = len(y)
    if n < 3:
        return y.copy()

    x_f = np.zeros((n, 2))
    P_f = np.zeros((n, 2, 2))
    x_p = np.zeros((n, 2))
    P_p = np.zeros((n, 2, 2))

    x_f[0, 0] = y[0]
    x_f[0, 1] = 0.0
    P_f[0] = np.eye(2) * r

    for k in range(1, n):
        dt = max(t[k] - t[k - 1], 1e-3)
        F = np.array([[1.0, dt], [0.0, 1.0]])
        G = np.array([[0.5 * dt * dt], [dt]])
        Qk = q * (G @ G.T)

        x_p[k] = F @ x_f[k - 1]
        P_p[k] = F @ P_f[k - 1] @ F.T + Qk

        H = np.array([[1.0, 0.0]])
        innovation = y[k] - (H @ x_p[k])
        S = float((H @ P_p[k] @ H.T) + r)
        K = (P_p[k] @ H.T) / S

        x_f[k] = x_p[k] + K.flatten() * innovation
        P_f[k] = P_p[k] - np.outer(K.flatten(), (H @ P_p[k]).flatten())

    x_s = np.zeros((n, 2))
    x_s[-1] = x_f[-1]

    for k in range(n - 2, -1, -1):
        dt = max(t[k + 1] - t[k], 1e-3)
        F = np.array([[1.0, dt], [0.0, 1.0]])
        C = np.linalg.solve(P_p[k + 1], F @ P_f[k]).T
        x_s[k] = x_f[k] + C @ (x_s[k + 1] - x_p[k + 1])

    return x_s[:, 0]


def _local_velocity(t: np.ndarray, y: np.ndarray, half_win: int = 3) -> np.ndarray:
    """Velocity via local linear regression through origin at each point."""
    n = len(y)
    v = np.zeros(n)
    if n < 2:
        return v
    if n == 2:
        dt = max(abs(t[1] - t[0]), 1e-6)
        v[1] = (y[1] - y[0]) / dt
        return v

    for i in range(n):
        lo = max(0, i - half_win)
        hi = min(n - 1, i + half_win)
        if hi - lo < 1:
            if i > 0:
                dt = max(abs(t[i] - t[i - 1]), 1e-6)
                v[i] = (y[i] - y[i - 1]) / dt
            continue
        tau = t[lo:hi + 1] - t[i]
        y_win = y[lo:hi + 1]
        num = float(np.dot(tau, y_win))
        den = float(np.dot(tau, tau))
        v[i] = num / den if abs(den) > 1e-12 else 0.0
    return v


def _compute_speed_fd(enu: List[Dict[str, float]]) -> List[float]:
    """Finite-difference speed (same as baseline)."""
    spd: List[float] = []
    for i in range(len(enu)):
        if i == 0:
            spd.append(0.0)
        else:
            de = enu[i]["e_m"] - enu[i - 1]["e_m"]
            dn = enu[i]["n_m"] - enu[i - 1]["n_m"]
            du = enu[i]["u_m"] - enu[i - 1]["u_m"]
            dt = enu[i]["t_s"] - enu[i - 1]["t_s"]
            if abs(dt) < 1e-6:
                dt = 1.0
            spd.append(math.hypot(math.hypot(de, dn), du) / abs(dt))
    if spd:
        spd[0] = 0.0
    return spd


def _compute_speed_local(enu: List[Dict[str, float]], half_win: int = 3) -> List[float]:
    """Speed magnitude via local linear regression per axis."""
    n = len(enu)
    if n < 4:
        return _compute_speed_fd(enu)

    t = np.array([p["t_s"] for p in enu])
    e = np.array([p["e_m"] for p in enu])
    n_arr = np.array([p["n_m"] for p in enu])
    u = np.array([p["u_m"] for p in enu])

    ve = _local_velocity(t, e, half_win)
    vn = _local_velocity(t, n_arr, half_win)
    vu = _local_velocity(t, u, half_win)

    speed = np.sqrt(ve ** 2 + vn ** 2 + vu ** 2)
    speed[0] = 0.0
    return speed.tolist()


def run_gnss(
    input_path: Path,
    model: str = "baseline",
    noise_m: float = 0.0,
) -> Dict[str, Any]:
    text = input_path.read_text(encoding="utf-8", errors="replace")
    fixes: List[GgaFix] = iter_gga_fixes(text)
    if not fixes:
        return {"enu_trajectory": [], "speed_m_s": []}

    ref = fixes[0]
    enu: List[Dict[str, float]] = []
    for f in fixes:
        e, n, u = lla2enu(
            f.lat_deg, f.lon_deg, f.height_m,
            ref.lat_deg, ref.lon_deg, ref.height_m,
        )
        enu.append({"t_s": f.t_s, "e_m": e, "n_m": n, "u_m": u})

    _apply_noise_enu(enu, noise_m)

    if model == "baseline":
        speed = _compute_speed_fd(enu)
    else:
        if len(enu) >= 3:
            t = np.array([p["t_s"] for p in enu])
            e_a = np.array([p["e_m"] for p in enu])
            n_a = np.array([p["n_m"] for p in enu])
            u_a = np.array([p["u_m"] for p in enu])

            var_meas = max(0.0001, noise_m * noise_m) if noise_m > 0 else 0.001
            e_s = _rts_smooth_1d(t, e_a, q=0.1, r=var_meas)
            n_s = _rts_smooth_1d(t, n_a, q=0.1, r=var_meas)
            u_s = _rts_smooth_1d(t, u_a, q=0.1, r=var_meas)

            for i in range(len(enu)):
                enu[i]["e_m"] = float(e_s[i])
                enu[i]["n_m"] = float(n_s[i])
                enu[i]["u_m"] = float(u_s[i])

        speed = _compute_speed_local(enu)

    return {"enu_trajectory": enu, "speed_m_s": speed}
