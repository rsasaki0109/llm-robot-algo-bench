from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class GgaFix:
    t_s: float
    lat_deg: float
    lon_deg: float
    quality: int
    height_m: float


def _parse_nmea_time_to_seconds(t: str) -> float:
    """NMEA 時刻 HHMMSS.ss -> 1日内秒（0〜86400 付近）。"""
    t = t.strip()
    if not t or len(t) < 4:
        return 0.0
    h = int(t[0:2]) if len(t) >= 2 else 0
    m = int(t[2:4]) if len(t) >= 4 else 0
    s = 0.0
    if len(t) > 4:
        try:
            s = float(t[4:])
        except ValueError:
            s = 0.0
    return h * 3600.0 + m * 60.0 + s


def _nmea_latlon_to_deg(raw: str, hemi: str, is_lat: bool) -> float:
    """
    GGA: 緯度は ddmm.mmmm 形式、経度は dddmm.mmmm 形式（NMEA 9.1）。
    """
    if not raw or not hemi:
        return float("nan")
    raw = raw.strip()
    if is_lat:
        if len(raw) < 3:
            return float("nan")
        deg = int(raw[0:2])
        minutes = float(raw[2:])
    else:
        if len(raw) < 4:
            return float("nan")
        deg = int(raw[0:3])
        minutes = float(raw[3:])
    d = abs(deg) + minutes / 60.0
    if hemi in ("S", "W"):
        d = -d
    return d


def _parse_gga(pieces: List[str]) -> Optional[GgaFix]:
    if len(pieces) < 10:
        return None
    t_s = _parse_nmea_time_to_seconds(pieces[0])
    lat = _nmea_latlon_to_deg(pieces[1], pieces[2], is_lat=True)
    lon = _nmea_latlon_to_deg(pieces[3], pieces[4], is_lat=False)
    try:
        q = int(pieces[5] or 0)
    except ValueError:
        q = 0
    if math.isnan(lat) or math.isnan(lon):
        return None
    h_str = pieces[8]
    try:
        h = float(h_str) if h_str else 0.0
    except ValueError:
        h = 0.0
    return GgaFix(t_s=t_s, lat_deg=lat, lon_deg=lon, quality=q, height_m=h)


def iter_gga_fixes(nmea_text: str) -> List[GgaFix]:
    out: List[GgaFix] = []
    for line in nmea_text.splitlines():
        line = line.strip()
        if not line.startswith("$") or "GGA" not in line:
            continue
        body, _, csum = line[1:].partition("*")
        parts = body.split(",")
        # $..GGA,1field empty -> parts[0] is talker+GGA
        if "GGA" not in parts[0] and "gga" not in parts[0].lower():
            continue
        # Standard: GPGGA,time,lat,N,lon,E,fix,sats,hdop,alt,...
        # parts[0] e.g. GNGGA
        fields = parts[1:]
        if len(fields) < 5:
            continue
        g = _parse_gga(fields)
        if g and g.quality > 0:
            out.append(g)
    return out
