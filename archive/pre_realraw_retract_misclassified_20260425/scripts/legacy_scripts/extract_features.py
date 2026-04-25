# -*- coding: utf-8 -*-
"""
AFM 力曲线特征批量提取（含基线校正与单位统一）
输出: results/extracted_features.json

策略:
- 有吸引段(F<0): 标准基线校正(z∈[0,100]nm远场线性拟合, >=5点)
  若远场点3-4个: 退化为常量偏移(均值)
- 全排斥段(F>=0): 不做线性基线校正，仅记录原始力值
"""
import sys, json, numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from parser import AFMForceCurve, load_all_curves


def baseline_correction(z, force):
    """
    基线校正策略:
    1. z∈[0,100]nm 点数 >= 5: 线性拟合 F = a*z + b
    2. 点数 3-4: 常量偏移 (减去均值)
    3. 点数 < 3: 失败
    返回: (f_corr, slope, intercept, count, status)
    """
    mask = (z >= 0) & (z <= 100)
    count = int(np.sum(mask))
    
    if count >= 5:
        z_fit = z[mask]
        f_fit = force[mask]
        coeffs = np.polyfit(z_fit, f_fit, 1)
        a, b = float(coeffs[0]), float(coeffs[1])
        f_corr = force - (a * z + b)
        if abs(b) > 200:
            status = f"discarded: intercept {b:.1f} > 200"
        else:
            status = "OK"
        return f_corr, a, b, count, status
    elif count >= 3:
        # 常量偏移
        offset = float(np.mean(force[mask]))
        f_corr = force - offset
        status = "OK_const"
        return f_corr, 0.0, offset, count, status
    else:
        return None, 0.0, 0.0, count, "discarded: far-end points < 3"


def extract_one(curve: AFMForceCurve):
    """提取单条曲线的关键特征，全部统一为 nN / nm"""
    z_raw = np.array(curve.z, dtype=float)
    if curve.z_unit in ('um', 'μm'):
        z = z_raw * 1000.0
    else:
        z = z_raw
    
    force_raw = np.array(curve.force, dtype=float)
    if curve.force_unit in ('uN', 'μN'):
        force = force_raw * 1000.0
    elif curve.force_unit == 'pN':
        force = force_raw * 1e-3
    else:
        force = force_raw
    
    has_attraction = np.any(force < 0)
    
    if has_attraction:
        f_corr, a, b, count, status = baseline_correction(z, force)
        if status.startswith("discarded"):
            return None
        
        snapin_idx = int(np.argmin(f_corr))
        snapin_force = float(f_corr[snapin_idx])
        snapin_z = float(z[snapin_idx])
        
        # 原始顺序中 z 递减，snap-in 后区在索引 < snapin_idx 的位置
        # 接触点：snap-in 之前最接近 snap-in 且 f_corr > 0 的点
        after_snap_mask = np.arange(len(z)) < snapin_idx
        rep_candidates = np.where(after_snap_mask & (f_corr > 0))[0]
        if len(rep_candidates) > 0:
            # 取最接近 snap-in 的（索引最大）
            contact_idx = int(rep_candidates[-1])
            contact_z = float(z[contact_idx])
            contact_f = float(f_corr[contact_idx])
        else:
            contact_idx = None
            contact_z = None
            contact_f = None
        
        # 吸引起始力：snap-in 之前最后一个 f_corr > -2 的点
        before_snap = np.where((np.arange(len(z)) > snapin_idx) & (f_corr > -2.0))[0]
        onset_f = float(f_corr[int(before_snap[0])]) if len(before_snap) > 0 else None
        
        baseline_slope = a
        baseline_intercept = b
        far_end_points = count
    else:
        f_corr = force
        snapin_force = None
        snapin_z = None
        contact_idx = None
        contact_z = None
        contact_f = None
        onset_f = None
        baseline_slope = 0.0
        baseline_intercept = float(np.mean(force[(z >= 0) & (z <= 100)])) if np.any(z <= 100) else 0.0
        far_end_points = int(np.sum((z >= 0) & (z <= 100)))
        status = "repulsive_only"
    
    # 对于有吸引段的曲线，只取 snap-in 之后的 repulsive 区，避免混入远场正偏差
    if has_attraction and contact_idx is not None:
        rep_mask = after_snap_mask & (f_corr > 0)
    else:
        rep_mask = f_corr > 0
    if np.sum(rep_mask) >= 3:
        rep_z = z[rep_mask]
        rep_f = f_corr[rep_mask]
        rep_slope = float(np.polyfit(rep_z, rep_f, 1)[0])
    else:
        rep_slope = None
    
    # parser 已从文件名/第1行将位移解析为 nm，无需再用 z_unit 转换
    disp_nm = curve.piezo_displacement
    
    max_force = float(np.max(f_corr))
    min_force = float(np.min(f_corr))
    
    return {
        "file": str(curve.filepath.relative_to(Path(__file__).parent.parent)),
        "probe": curve.probe_model,
        "material": curve.material,
        "substrate": curve.substrate,
        "displacement_nm": float(disp_nm) if disp_nm else None,
        "setpoint": f"{curve.setpoint_force}{curve.setpoint_unit}",
        "has_attraction": bool(has_attraction),
        "baseline_slope_nN_per_nm": float(baseline_slope),
        "baseline_intercept_nN": float(baseline_intercept),
        "baseline_status": status,
        "far_end_points": far_end_points,
        "snap_in_force_nN": snapin_force,
        "snap_in_z_nm": snapin_z,
        "contact_z_nm": contact_z,
        "contact_f_nN": contact_f,
        "onset_f_nN": onset_f,
        "repulsive_slope_nN_per_nm": rep_slope,
        "max_force_nN": max_force,
        "min_force_nN": min_force,
    }


def main():
    root = Path(__file__).parent.parent
    curves = load_all_curves(root)
    results = []
    discarded = []
    
    for rel, curve in sorted(curves.items()):
        feat = extract_one(curve)
        if feat is None:
            z_raw = np.array(curve.z, dtype=float)
            if curve.z_unit in ('um', 'μm'):
                z = z_raw * 1000.0
            else:
                z = z_raw
            force_raw = np.array(curve.force, dtype=float)
            if curve.force_unit in ('uN', 'μN'):
                force = force_raw * 1000.0
            elif curve.force_unit == 'pN':
                force = force_raw * 1e-3
            else:
                force = force_raw
            _, a, b, count, status = baseline_correction(z, force)
            discarded.append({
                "file": rel,
                "reason": status,
                "intercept": float(b),
                "far_end_points": count,
            })
        else:
            results.append(feat)
    
    out = root / 'results' / 'extracted_features.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Done: {len(results)} valid, {len(discarded)} discarded -> {out}")
    
    disc_out = root / 'results' / 'discarded_files.json'
    with open(disc_out, 'w', encoding='utf-8') as f:
        json.dump(discarded, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    main()
