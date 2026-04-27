from __future__ import annotations

import math
from collections import deque
from pathlib import Path
from typing import Any, Dict, List, Tuple

from tasks.gnss.nmea import GgaFix, iter_gga_fixes

A_WGS84 = 6378137.0
E2_WGS84 = 6.69437999014e-3


def _lla2ecef(lat_deg: float, lon_deg: float, h_m: float) -> Tuple[float, float, float]:
    lat = math.radians(lat_deg)
    lon = math.radians(lon_deg)
    sin_lat = math.sin(lat)
    cos_lat = math.cos(lat)
    sin_lon = math.sin(lon)
    cos_lon = math.cos(lon)
    N = A_WGS84 / math.sqrt(1.0 - E2_WGS84 * sin_lat * sin_lat)
    x = (N + h_m) * cos_lat * cos_lon
    y = (N + h_m) * cos_lat * sin_lon
    z = (N * (1.0 - E2_WGS84) + h_m) * sin_lat
    return x, y, z


def _ecef2enu(
    x: float,
    y: float,
    z: float,
    lat0_deg: float,
    lon0_deg: float,
    h0_m: float,
) -> Tuple[float, float, float]:
    x0, y0, z0 = _lla2ecef(lat0_deg, lon0_deg, h0_m)
    dx = x - x0
    dy = y - y0
    dz = z - z0
    lat0 = math.radians(lat0_deg)
    lon0 = math.radians(lon0_deg)
    sin_lat0 = math.sin(lat0)
    cos_lat0 = math.cos(lat0)
    sin_lon0 = math.sin(lon0)
    cos_lon0 = math.cos(lon0)
    e = -sin_lon0 * dx + cos_lon0 * dy
    n = -sin_lat0 * cos_lon0 * dx - sin_lat0 * sin_lon0 * dy + cos_lat0 * dz
    u = cos_lat0 * cos_lon0 * dx + cos_lat0 * sin_lon0 * dy + sin_lat0 * dz
    return e, n, u


def _add_gaussian_noise(
    points: List[Dict[str, float]],
    sigma: float,
    seed: int = 42,
) -> None:
    import random

    rng = random.Random(seed)
    for pt in points:
        pt["e_m"] += rng.gauss(0.0, sigma)
        pt["n_m"] += rng.gauss(0.0, sigma)
        pt["u_m"] += rng.gauss(0.0, sigma)


def _median_filter_1d(values: List[float], half_win: int) -> List[float]:
    n = len(values)
    if n == 0 or half_win <= 0:
        return list(values)
    result: List[float] = []
    window: deque[float] = deque()
    for i in range(n):
        window.append(values[i])
        if len(window) > 2 * half_win + 1:
            window.popleft()
        sorted_win = sorted(window)
        mid = len(sorted_win) // 2
        result.append(sorted_win[mid])
    return result


def _ema_smooth(values: List[float], alpha: float) -> List[float]:
    if not values:
        return []
    result = [values[0]]
    for i in range(1, len(values)):
        result.append(alpha * values[i] + (1.0 - alpha) * result[-1])
    return result


def _ema_smooth_backward(values: List[float], alpha: float) -> List[float]:
    if not values:
        return []
    result = [0.0] * len(values)
    result[-1] = values[-1]
    for i in range(len(values) - 2, -1, -1):
        result[i] = alpha * values[i] + (1.0 - alpha) * result[i + 1]
    return result


def _bidi_ema_smooth(values: List[float], alpha: float) -> List[float]:
    fwd = _ema_smooth(values, alpha)
    bwd = _ema_smooth_backward(values, alpha)
    return [(f + b) * 0.5 for f, b in zip(fwd, bwd)]


def _compute_speeds_central(
    times: List[float],
    e: List[float],
    n: List[float],
    u: List[float],
) -> List[float]:
    n_pts = len(times)
    speeds: List[float] = []
    for i in range(n_pts):
        if i == 0:
            dt = times[1] - times[0] if n_pts > 1 else 1.0
            de = e[1] - e[0]
            dn = n[1] - n[0]
            du = u[1] - u[0]
        elif i == n_pts - 1:
            dt = times[i] - times[i - 1]
            de = e[i] - e[i - 1]
            dn = n[i] - n[i - 1]
            du = u[i] - u[i - 1]
        else:
            dt = times[i + 1] - times[i - 1]
            de = e[i + 1] - e[i - 1]
            dn = n[i + 1] - n[i - 1]
            du = u[i + 1] - u[i - 1]
        if dt <= 1e-9:
            speeds.append(0.0)
        else:
            speeds.append(math.sqrt(de * de + dn * dn + du * du) / dt)
    return speeds


def run_gnss(
    input_path: Path,
    model: str = "baseline",
    noise_m: float = 0.0,
) -> Dict[str, Any]:
    _ = model
    text = input_path.read_text(encoding="utf-8", errors="replace")
    fixes: List[GgaFix] = iter_gga_fixes(text)

    if not fixes:
        return {"enu_trajectory": [], "speed_m_s": []}

    ref = fixes[0]
    enu_points: List[Dict[str, float]] = []
    for f in fixes:
        e, n, u = _ecef2enu(
            *_lla2ecef(f.lat_deg, f.lon_deg, f.height_m),
            ref.lat_deg,
            ref.lon_deg,
            ref.height_m,
        )
        enu_points.append({"t_s": f.t_s, "e_m": e, "n_m": n, "u_m": u})

    _add_gaussian_noise(enu_points, noise_m)

    n_pts = len(enu_points)
    if n_pts == 1:
        return {"enu_trajectory": [dict(enu_points[0])], "speed_m_s": [0.0]}

    half_win = max(1, min(n_pts // 10, 5))
    alpha = 0.3

    e_raw = [p["e_m"] for p in enu_points]
    n_raw = [p["n_m"] for p in enu_points]
    u_raw = [p["u_m"] for p in enu_points]

    e_med = _median_filter_1d(e_raw, half_win)
    n_med = _median_filter_1d(n_raw, half_win)
    u_med = _median_filter_1d(u_raw, half_win)

    e_s = _bidi_ema_smooth(e_med, alpha)
    n_s = _bidi_ema_smooth(n_med, alpha)
    u_s = _bidi_ema_smooth(u_med, alpha)

    times = [p["t_s"] for p in enu_points]
    speeds = _compute_speeds_central(times, e_s, n_s, u_s)

    traj: List[Dict[str, float]] = []
    for i in range(n_pts):
        traj.append(
            {
                "t_s": times[i],
                "e_m": e_s[i],
                "n_m": n_s[i],
                "u_m": u_s[i],
            }
        )

    return {"enu_trajectory": traj, "speed_m_s": speeds}

