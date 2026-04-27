from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np

from tasks.gnss.nmea import GgaFix, iter_gga_fixes

A_WGS84 = 6378137.0
E2 = 6.69437999014e-3


def lla2ecef(lat_deg: float, lon_deg: float, h_m: float) -> Tuple[float, float, float]:
    """Convert geodetic latitude/longitude/height to ECEF Cartesian coordinates."""
    lat, lon = math.radians(lat_deg), math.radians(lon_deg)
    sin_lat = math.sin(lat)
    cos_lat = math.cos(lat)
    cos_lon = math.cos(lon)
    sin_lon = math.sin(lon)
    n = A_WGS84 / math.sqrt(1.0 - E2 * sin_lat * sin_lat)
    x = (n + h_m) * cos_lat * cos_lon
    y = (n + h_m) * cos_lat * sin_lon
    z = (n * (1.0 - E2) + h_m) * sin_lat
    return (x, y, z)


def lla2enu(
    lat_deg: float, lon_deg: float, h_m: float, lat0: float, lon0: float, h0: float
) -> Tuple[float, float, float]:
    """Convert geodetic coordinates to ENU using (lat0, lon0, h0) as the local origin."""
    x, y, z = lla2ecef(lat_deg, lon_deg, h_m)
    x0, y0, z0 = lla2ecef(lat0, lon0, h0)
    dx, dy, dz = x - x0, y - y0, z - z0
    lon0r, lat0r = math.radians(lon0), math.radians(lat0)
    sin_lon0 = math.sin(lon0r)
    cos_lon0 = math.cos(lon0r)
    sin_lat0 = math.sin(lat0r)
    cos_lat0 = math.cos(lat0r)
    e = -sin_lon0 * dx + cos_lon0 * dy
    n = -sin_lat0 * cos_lon0 * dx - sin_lat0 * sin_lon0 * dy + cos_lat0 * dz
    u = cos_lat0 * cos_lon0 * dx + cos_lat0 * sin_lon0 * dy + sin_lat0 * dz
    return (e, n, u)


def _apply_noise_enu(enu: List[Dict[str, float]], sigma: float) -> None:
    if sigma <= 0:
        return
    rng = np.random.default_rng(0)
    for p in enu:
        p["e_m"] = float(p["e_m"] + rng.normal(0.0, sigma))
        p["n_m"] = float(p["n_m"] + rng.normal(0.0, sigma))
        p["u_m"] = float(p["u_m"] + rng.normal(0.0, sigma))


def _compute_speed(enu: List[Dict[str, float]]) -> List[float]:
    """Compute 3-D speed from consecutive ENU samples."""
    if not enu:
        return []
    speed: List[float] = [0.0]
    for i in range(1, len(enu)):
        de = enu[i]["e_m"] - enu[i - 1]["e_m"]
        dn = enu[i]["n_m"] - enu[i - 1]["n_m"]
        du = enu[i]["u_m"] - enu[i - 1]["u_m"]
        dt = enu[i]["t_s"] - enu[i - 1]["t_s"]
        if abs(dt) < 1e-6:
            dt = 1.0
        speed.append(math.hypot(math.hypot(de, dn), du) / abs(dt))
    return speed


def run_gnss(
    input_path: Path,
    model: str = "baseline",
    noise_m: float = 0.0,
) -> Dict[str, Any]:
    """
    Parse NMEA GGA sentences, convert to a local ENU trajectory,
    and compute 3-D speed between consecutive fixes.

    Parameters
    ----------
    input_path:
        Path to a text file containing NMEA sentences.
    model:
        Reserved for future model selection (ignored).
    noise_m:
        Standard deviation of zero-mean Gaussian noise added to each
        ENU component (default 0.0 means no noise).

    Returns
    -------
    dict with keys:
        - "enu_trajectory": list of {"t_s": float, "e_m": float, "n_m": float, "u_m": float}
        - "speed_m_s": list of float (same length as trajectory)
    """
    _ = model
    text = input_path.read_text(encoding="utf-8", errors="replace")
    fixes: List[GgaFix] = iter_gga_fixes(text)
    if not fixes:
        return {
            "enu_trajectory": [],
            "speed_m_s": [],
        }
    origin = fixes[0]
    enu: List[Dict[str, float]] = []
    for f in fixes:
        e, n, u = lla2enu(f.lat_deg, f.lon_deg, f.height_m,
                          origin.lat_deg, origin.lon_deg, origin.height_m)
        enu.append({
            "t_s": f.t_s,
            "e_m": e,
            "n_m": n,
            "u_m": u,
        })
    _apply_noise_enu(enu, noise_m)
    speed = _compute_speed(enu)
    return {
        "enu_trajectory": enu,
        "speed_m_s": speed,
    }
