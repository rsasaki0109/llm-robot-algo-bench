from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple


def _interpolate(
    t_pred: List[float], v_pred: List[float], t_ref: List[float]
) -> List[float]:
    """線形補間（境界は端でクリップ）。"""
    if not t_pred or not t_ref:
        return [0.0] * len(t_ref)
    out = []
    for t in t_ref:
        if t <= t_pred[0]:
            out.append(v_pred[0])
        elif t >= t_pred[-1]:
            out.append(v_pred[-1])
        else:
            for i in range(len(t_pred) - 1):
                if t_pred[i] <= t <= t_pred[i + 1]:
                    a = (t - t_pred[i]) / (t_pred[i + 1] - t_pred[i] + 1e-12)
                    out.append((1 - a) * v_pred[i] + a * v_pred[i + 1])
                    break
            else:
                out.append(v_pred[-1])
    return out


def evaluate_gnss(
    pred: Dict[str, Any], ground_truth: Dict[str, Any]
) -> Dict[str, float]:
    """
    位置: ENU 各軸差の二乗平均の平方根（RMSE）
    速度: 参照時刻に揃えた |v_pred - v_gt| の平均
    """
    gpts = ground_truth.get("points", [])
    p_traj: List[Dict[str, float]] = pred.get("enu_trajectory", [])
    t_gt = [float(p.get("t_s", i)) for i, p in enumerate(gpts)]
    e_gt = [float(p.get("e_m", 0.0)) for p in gpts]
    n_gt = [float(p.get("n_m", 0.0)) for p in gpts]
    u_gt = [float(p.get("u_m", 0.0)) for p in gpts]
    sp_gt = [float(p.get("speed_m_s", 0.0)) for p in gpts]

    if not p_traj:
        return {"rmse": float("nan"), "speed_error": float("nan")}

    t_pred = [float(p.get("t_s", 0.0)) for p in p_traj]
    e_p = [float(p.get("e_m", 0.0)) for p in p_traj]
    n_p = [float(p.get("n_m", 0.0)) for p in p_traj]
    u_p = [float(p.get("u_m", 0.0)) for p in p_traj]

    # 参照時刻上で pred を線形補間
    def interp_axis(vp: List[float], t0: List[float], t1: List[float]) -> List[float]:
        if len(t0) != len(vp) or not t0:
            return [0.0] * len(t1)
        return [float(x) for x in _interpolate(t0, vp, t1)]

    ei = interp_axis(e_p, t_pred, t_gt)
    ni = interp_axis(n_p, t_pred, t_gt)
    ui = interp_axis(u_p, t_pred, t_gt)
    sq = [(ei[i] - e_gt[i]) ** 2 + (ni[i] - n_gt[i]) ** 2 + (ui[i] - u_gt[i]) ** 2
          for i in range(len(t_gt))]
    rmse = math.sqrt(sum(sq) / max(len(sq), 1))

    sp = pred.get("speed_m_s", [])
    if isinstance(sp, list) and sp and t_pred:
        spi = [float(x) for x in _interpolate(t_pred, [float(s) for s in sp], t_gt)]
        se = [abs(spi[i] - sp_gt[i]) for i in range(len(sp_gt))]
        speed_error = float(sum(se) / max(len(se), 1))
    else:
        # 速度未提供時は ENU から数値微分
        de = [ei[i] - ei[i - 1] for i in range(1, len(t_gt))]
        dn = [ni[i] - ni[i - 1] for i in range(1, len(t_gt))]
        dt = [t_gt[i] - t_gt[i - 1] for i in range(1, len(t_gt))]
        spi = [0.0]
        for i in range(len(de)):
            dti = dt[i] if abs(dt[i]) > 1e-9 else 1.0
            spi.append(math.hypot(de[i] / dti, dn[i] / dti))
        se = [abs(spi[i] - sp_gt[i]) for i in range(min(len(spi), len(sp_gt)))]
        speed_error = float(sum(se) / max(len(se), 1))
    return {"rmse": rmse, "speed_error": speed_error}
