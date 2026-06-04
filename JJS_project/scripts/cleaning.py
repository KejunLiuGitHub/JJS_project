# -*- coding: utf-8 -*-
"""
AFM Force-Distance Curve Cleaning Module
从原始 Bruker NanoScope Analysis .txt 出发，完成解析、基线校正、分段、验证。
所有输出可追溯到原始文件。
"""
import re
import numpy as np
from pathlib import Path

# ── Physical constants for vdW checks ──────────────────────────────
R_TIP_NM = 8.0
D0_NM = 0.3
A_HAMAKER_J = 4e-19
GAMMA_MN_M = 72.0
HBAR_C_J_M = 1.98644586e-25
ETA_CP = 0.4
EPS0_F_M = 8.854e-12


def _detect_direction(z):
    """Return inc/dec/mixed/empty for a numeric Z array."""
    if len(z) < 2:
        return "empty"
    dz = np.diff(z)
    if np.all(dz > 0):
        return "inc"
    if np.all(dz < 0):
        return "dec"
    return "mixed"


def load_raw(filepath, encoding=None, branch=None, preserve_time=False):
    """
    解析单个 Bruker txt 文件。
    尝试 utf-8 优先，失败则回退 latin-1。
    返回 dict: {filepath, filename, z_raw, f_raw, z, f, meta}

    branch:
        None      旧行为：默认将采集数组反转，兼容历史脚本。
        "extend" 伸出/approach/loading，保留采集顺序作为分析顺序。
        "retract" 缩回/unloading，保留采集顺序作为分析顺序。

    preserve_time=True 时，即便 branch=None 也保留采集顺序为 z/f。
    所有返回都会额外包含 z_time/f_time、z_nm/force_nN、direction、branch、source_path。
    """
    filepath = Path(filepath)
    if encoding is None:
        for enc in ("utf-8", "latin-1"):
            try:
                with open(filepath, "r", encoding=enc) as f:
                    lines = f.readlines()
                break
            except UnicodeDecodeError:
                continue
        else:
            raise UnicodeDecodeError(f"Cannot decode {filepath} with utf-8 or latin-1")
    else:
        with open(filepath, "r", encoding=encoding) as f:
            lines = f.readlines()

    if len(lines) < 3:
        raise ValueError(f"{filepath.name}: 数据行数不足")

    line1 = lines[0].strip()
    line2 = lines[1].strip()

    # ── 解析元数据 ──────────────────────────────────────────────────
    meta = {"instrument": None, "mode": None, "scan_size": None,
            "piezo_displacement": None, "setpoint_force": None,
            "setpoint_unit": "nN", "probe_model": None,
            "material": None, "substrate": None}

    m = re.search(r"实验仪器为(.+?)，", line1)
    if m:
        meta["instrument"] = m.group(1).strip()
    m = re.search(r"所用模式为(.+?)，", line1)
    if m:
        meta["mode"] = m.group(1).strip()
    m = re.search(r"扫描范围[（(]scan size[）)]为(\d+)nm×(\d+)nm", line1)
    if m:
        meta["scan_size"] = (int(m.group(1)), int(m.group(2)))
    m = re.search(r"压电陶瓷总位移为([\d.]+)(nm|um|μm)", line1)
    if m:
        meta["piezo_displacement"] = float(m.group(1))
    m = re.search(r"下压力为([\d.]+)(nN|uN|μN|pN)", line1)
    if m:
        meta["setpoint_force"] = float(m.group(1))
        meta["setpoint_unit"] = m.group(2)

    m = re.search(r"AFM探针型号为(.+?)，", line2)
    if m:
        meta["probe_model"] = m.group(1).strip()
    m = re.search(r"所测材料为(.+?)，", line2)
    if m:
        meta["material"] = m.group(1).strip()
    m = re.search(r"基底为(.+?)，", line2)
    if m:
        meta["substrate"] = m.group(1).strip()

    # ── 解析数据 ────────────────────────────────────────────────────
    z_vals, f_vals = [], []
    z_unit, f_unit = "nm", "nN"

    # 尝试从前几行提取单位。RealRaw 有些导出没有中文 header，
    # 第一行就是 "nm uN" 这样的列标题。
    for unit_line in [ln.strip() for ln in lines[:5]]:
        unit_m = re.search(r"(nm|um|μm)\s+(nN|uN|μN)\s*$", unit_line)
        if unit_m:
            z_unit = unit_m.group(1)
            f_unit = unit_m.group(2)
            break

    for line in lines:
        line = line.strip()
        if not line:
            continue
        # 跳过列标题重复行
        if re.search(r"(nm|um|μm)\s+(nN|uN|μN|pN)\s*$", line, re.IGNORECASE):
            continue
        parts = line.split()
        if len(parts) >= 2:
            try:
                z_vals.append(float(parts[0]))
                f_vals.append(float(parts[1]))
            except ValueError:
                continue

    z_raw = np.array(z_vals, dtype=float)
    f_raw = np.array(f_vals, dtype=float)

    # 单位统一为 nN / nm
    if z_unit in ("um", "μm"):
        z_raw = z_raw * 1000.0
    if f_unit in ("uN", "μN"):
        f_raw = f_raw * 1000.0
    elif f_unit == "pN":
        f_raw = f_raw * 1e-3

    branch_norm = branch.lower() if isinstance(branch, str) else None
    if branch_norm not in (None, "extend", "retract"):
        raise ValueError(f"Unsupported branch: {branch!r}; expected extend/retract/None")

    # 历史脚本假设 NanoScope 导出需要反转。RealRaw 已经按 extend/retract
    # 拆分，分支文件的采集顺序本身就是物理分支顺序，因此显式 branch 时不反转。
    if branch_norm is None and not preserve_time:
        z = z_raw[::-1].copy()
        f = f_raw[::-1].copy()
        analysis_direction = _detect_direction(z)
    else:
        z = z_raw.copy()
        f = f_raw.copy()
        analysis_direction = _detect_direction(z)

    return {
        "filepath": str(filepath),
        "source_path": str(filepath),
        "filename": filepath.name,
        "branch": branch_norm,
        "z_raw": z_raw,
        "f_raw": f_raw,
        "z_time": z_raw.copy(),
        "f_time": f_raw.copy(),
        "z": z,
        "f": f,
        "z_nm": z,
        "force_nN": f,
        "direction": analysis_direction,
        "time_direction": _detect_direction(z_raw),
        "meta": meta,
    }


def correct_baseline(z, f, z_far_max=100.0):
    """
    远场基线校正。
    区域: z ∈ [0, z_far_max] nm（反转后的远场，即数组开头）
    策略:
        >= 5 点: 线性拟合 F = a*z + b
        3-4 点:  常量偏移（均值）
        < 3 点:  失败
    返回: (f_corr, slope, intercept, n_points, status)
    """
    mask = (z >= 0) & (z <= z_far_max)
    count = int(np.sum(mask))

    if count >= 5:
        coeffs = np.polyfit(z[mask], f[mask], 1)
        a, b = float(coeffs[0]), float(coeffs[1])
        f_corr = f - (a * z + b)
        if abs(b) > 200:
            status = f"discarded: intercept {b:.1f} > 200"
        else:
            status = "OK"
        return f_corr, a, b, count, status
    elif count >= 3:
        offset = float(np.mean(f[mask]))
        f_corr = f - offset
        status = "OK_const"
        return f_corr, 0.0, offset, count, status
    else:
        return None, 0.0, 0.0, count, "discarded: far-end points < 3"


def segment_curve(z, f_corr):
    """
    检测 snap-in、contact、drop/rise 分段。
    假设 z 已反转（递增），f_corr 已基线校正。
    返回 dict 包含所有分段信息。
    """
    snap_idx = int(np.argmin(f_corr))
    snap_f = float(f_corr[snap_idx])
    snap_z = float(z[snap_idx])

    # Contact: snap 之后首个 f_corr >= 0
    after_snap = np.arange(len(z)) > snap_idx
    rep_candidates = np.where(after_snap & (f_corr >= 0))[0]
    if len(rep_candidates) > 0:
        contact_idx = int(rep_candidates[0])  # 最接近 snap 的（索引最小）
        contact_z = float(z[contact_idx])
        contact_f = float(f_corr[contact_idx])
    else:
        contact_idx = len(z) - 1
        contact_z = float(z[contact_idx])
        contact_f = float(f_corr[contact_idx])

    # Drop start: snap 之前最后一个 f_corr > -2.0 的点
    before_snap = np.where((np.arange(len(z)) < snap_idx) & (f_corr > -2.0))[0]
    if len(before_snap) > 0:
        drop_start_idx = int(before_snap[-1])
    else:
        drop_start_idx = max(0, snap_idx - 5)

    # Drop / Rise 分段
    drop_z = z[drop_start_idx:snap_idx + 1].copy()
    drop_f = f_corr[drop_start_idx:snap_idx + 1].copy()
    rise_z = z[snap_idx:contact_idx + 1].copy()
    rise_f = f_corr[snap_idx:contact_idx + 1].copy()

    # 斜率计算
    if len(drop_z) >= 2:
        drop_slopes = np.diff(drop_f) / np.diff(drop_z)
        max_drop_slope = float(np.min(drop_slopes))  # 最负 = 最大下降速率
        avg_drop_slope = float(np.mean(drop_slopes))
    else:
        max_drop_slope = 0.0
        avg_drop_slope = 0.0

    if len(rise_z) >= 2:
        rise_slopes = np.diff(rise_f) / np.diff(rise_z)
        max_rise_slope = float(np.max(rise_slopes))
        avg_rise_slope = float(np.mean(rise_slopes))
    else:
        max_rise_slope = 0.0
        avg_rise_slope = 0.0

    # 不对称性
    if abs(max_drop_slope) > 1e-12:
        asymmetry_ratio = abs(max_rise_slope / max_drop_slope)
    else:
        asymmetry_ratio = 0.0

    # 能量耗散（transition zone 面积，approach 从 drop_start 到 snap）
    if len(drop_z) >= 2:
        energy_dissipated = float(np.trapezoid(drop_f, drop_z))
    else:
        energy_dissipated = 0.0

    # Recovery 分析（rise 段）
    if len(rise_z) >= 2:
        local_slopes = []
        local_z = []
        for i in range(len(rise_z) - 1):
            local_slopes.append(float((rise_f[i + 1] - rise_f[i]) / (rise_z[i + 1] - rise_z[i])))
            local_z.append(float((rise_z[i] + rise_z[i + 1]) / 2))
        max_slope_jump = max(local_slopes) - min(local_slopes) if len(local_slopes) > 1 else 0
        # 简单曲率估计
        if len(local_slopes) > 1:
            curvatures = np.diff(local_slopes) / np.diff(local_z) if len(local_z) > 1 else [0]
            max_curvature = float(np.max(np.abs(curvatures))) if len(curvatures) > 0 else 0
        else:
            max_curvature = 0
        # plateau: 连续 3 个 slope 接近（变化 < 10%）视为平台
        plateau_count = 0
        for i in range(len(local_slopes) - 2):
            s0, s1, s2 = local_slopes[i], local_slopes[i + 1], local_slopes[i + 2]
            if abs(s1 - s0) < 0.1 * max(abs(s0), 1e-6) and abs(s2 - s1) < 0.1 * max(abs(s1), 1e-6):
                plateau_count += 1
        plateau_fraction = plateau_count / max(len(local_slopes) - 2, 1)
    else:
        local_slopes = []
        local_z = []
        max_slope_jump = 0
        max_curvature = 0
        plateau_fraction = 0.0

    return {
        "snap_idx": snap_idx,
        "snap_f": snap_f,
        "snap_z": snap_z,
        "contact_idx": contact_idx,
        "contact_z": contact_z,
        "contact_f": contact_f,
        "drop_start_idx": drop_start_idx,
        "drop_z": drop_z.tolist(),
        "drop_f": drop_f.tolist(),
        "rise_z": rise_z.tolist(),
        "rise_f": rise_f.tolist(),
        "max_drop_slope": max_drop_slope,
        "avg_drop_slope": avg_drop_slope,
        "max_rise_slope": max_rise_slope,
        "avg_rise_slope": avg_rise_slope,
        "asymmetry_ratio": asymmetry_ratio,
        "energy_dissipated": energy_dissipated,
        "recovery": {
            "plateau_fraction": plateau_fraction,
            "max_slope_jump": max_slope_jump,
            "max_curvature": max_curvature,
            "local_slopes": local_slopes,
            "local_z": local_z,
        },
    }


def compute_vdw_check(snap_f):
    """计算理论力对比，返回 vdW_check dict。"""
    R_m = R_TIP_NM * 1e-9
    d0_m = D0_NM * 1e-9
    gamma_N_m = GAMMA_MN_M * 1e-3

    F_vdw = A_HAMAKER_J * R_m / (12 * d0_m ** 2) * 1e9  # nN
    F_cap = 4 * np.pi * R_m * gamma_N_m * 1e9  # nN
    F_cp = (np.pi ** 3 * HBAR_C_J_M * R_m / (360 * d0_m ** 3)) * ETA_CP * 1e9
    F_measured = abs(snap_f)

    # 为匹配测量值所需的 Hamaker
    A_required = 12 * d0_m ** 2 * F_measured * 1e-9 / R_m

    return {
        "F_vdw_nonret": float(F_vdw),
        "F_capillary_theory": float(F_cap),
        "F_casimir": float(F_cp),
        "F_vdw_plus_cap": float(F_vdw + F_cap),
        "F_measured": float(F_measured),
        "A_required_J": float(A_required),
        "A_required_vs_typical": float(A_required / A_HAMAKER_J),
    }


def clean_and_validate(filepath, z_far_max=100.0):
    """
    完整清洗流程。成功返回标准化 dict；失败返回 None。
    """
    try:
        raw = load_raw(filepath)
    except Exception as e:
        print(f"[跳过] {filepath}: {e}")
        return None

    z = raw["z"]
    f = raw["f"]
    meta = raw["meta"]

    # 基线校正
    f_corr, slope, intercept, n_points, status = correct_baseline(z, f, z_far_max)
    if f_corr is None:
        return None

    # 分段
    seg = segment_curve(z, f_corr)

    # 验证（生成警告但不拒绝，保持与旧 JSON 11 条曲线兼容）
    warnings = []
    if seg["snap_f"] >= 0:
        warnings.append("no_negative_snapin")
    if len(seg["drop_z"]) < 3:
        warnings.append(f"short_drop:{len(seg['drop_z'])}")
    if len(seg["rise_z"]) < 2:
        warnings.append(f"short_rise:{len(seg['rise_z'])}")

    # 组装输出（与旧 JSON 语义等价，键名简化）
    result = {
        "file": raw["filename"],
        "filepath": raw["filepath"],
        "disp_nm": float(meta["piezo_displacement"]) if meta["piezo_displacement"] else None,
        "setpoint": f"{meta['setpoint_force']}{meta['setpoint_unit']}" if meta["setpoint_force"] else None,
        "probe": meta["probe_model"],
        "material": meta["material"],
        "substrate": meta["substrate"],
        "has_attraction": True,
        "baseline_slope": slope,
        "baseline_intercept": intercept,
        "baseline_status": status,
        "far_end_points": n_points,
        "snap_f": seg["snap_f"],
        "snap_z": seg["snap_z"],
        "contact_z": seg["contact_z"],
        "contact_f": seg["contact_f"],
        "n_before": len(seg["drop_z"]) - 1,  # snap 前的点数
        "n_after": len(seg["rise_z"]) - 1,   # snap 后的点数（不含 snap）
        "max_drop_slope": seg["max_drop_slope"],
        "avg_drop_slope": seg["avg_drop_slope"],
        "max_rise_slope": seg["max_rise_slope"],
        "avg_rise_slope": seg["avg_rise_slope"],
        "asymmetry_ratio": seg["asymmetry_ratio"],
        "drop_area": seg["energy_dissipated"],
        "energy_dissipated": seg["energy_dissipated"],
        "drop_z": seg["drop_z"],
        "drop_f": seg["drop_f"],
        "rise_z": seg["rise_z"],
        "rise_f": seg["rise_f"],
        "recovery": seg["recovery"],
        "vdW_check": compute_vdw_check(seg["snap_f"]),
        "warnings": warnings,
        "valid": len(warnings) == 0,
    }
    return result


def load_all_cleaned(data_dir, pattern="*.txt", discard_set=None):
    """
    批量加载目录下所有 txt，返回清洗后的 dict 列表（自动过滤 None）。
    按文件名排序。
    
    Args:
        data_dir: 数据目录
        pattern: 文件匹配模式
        discard_set: 可选，set of filenames to skip (from QC decisions)
    """
    data_dir = Path(data_dir)
    results = []
    skipped_discard = 0
    for fp in sorted(data_dir.glob(pattern)):
        if "NanoScope Analysis" not in fp.name:
            continue
        if discard_set and fp.name in discard_set:
            skipped_discard += 1
            continue
        item = clean_and_validate(fp)
        if item is not None:
            results.append(item)
    if skipped_discard:
        print(f"[QC] Skipped {skipped_discard} discarded file(s)")
    return results


if __name__ == "__main__":
    import json
    root = Path(__file__).parent.parent
    data = load_all_cleaned(root / "20260409")
    print(f"Loaded {len(data)} valid curves from raw txt.")
    for d in data[:3]:
        print(f"  {d['file']}: snap={d['snap_f']:.1f} nN, contact_z={d['contact_z']:.1f} nm")
