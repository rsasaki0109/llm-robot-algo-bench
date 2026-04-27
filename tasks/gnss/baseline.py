from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

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
    lat_deg: float, lon_deg: float, h_m: float, lat0: float, lon0: float, h0: float
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


def run_gnss(
    input_path: Path,
    model: str = "baseline",
    noise_m: float = 0.0,
) -> Dict[str, Any]:
    """
    LLM 差替え用フック: 現状は WGS84 LLH->ENU（第1 GGA 原点）+ 時刻差分速度。
    """
    _ = model  # 将来: model に応じた生成コード
    text = input_path.read_text(encoding="utf-8", errors="replace")
    fixes: List[GgaFix] = iter_gga_fixes(text)
    if not fixes:
        return {
            "enu_trajectory": [],
            "speed_m_s": [],
        }
    r = fixes[0]
    enu: List[Dict[str, float]] = []
    for f in fixes:
        e, n, u = lla2enu(f.lat_deg, f.lon_deg, f.height_m, r.lat_deg, r.lon_deg, r.height_m)
        enu.append(
            {
                "t_s": f.t_s,
                "e_m": e,
                "n_m": n,
                "u_m": u,
            }
        )
    _apply_noise_enu(enu, noise_m)
    speed: List[float] = []
    for i in range(len(enu)):
        if i == 0:
            speed.append(0.0)
        else:
            de = enu[i]["e_m"] - enu[i - 1]["e_m"]
            dn = enu[i]["n_m"] - enu[i - 1]["n_m"]
            du = enu[i]["u_m"] - enu[i - 1]["u_m"]
            dt = enu[i]["t_s"] - enu[i - 1]["t_s"]
            if abs(dt) < 1e-6:
                dt = 1.0
            speed.append(math.hypot(math.hypot(de, dn), du) / abs(dt))
    if speed:
        speed[0] = 0.0
    return {
        "enu_trajectory": enu,
        "speed_m_s": speed,
    }
