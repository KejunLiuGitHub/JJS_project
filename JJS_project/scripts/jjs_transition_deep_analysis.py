# -*- coding: utf-8 -*-
"""
JJS 过渡区深度分析 — 5 模块综合分析
输出 JSON 结果供 PDF 生成脚本使用
"""
import sys, json, numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from parser import AFMForceCurve

R_PROBE = 8.0e-9  # m
GAMMA_WATER = 0.072  # N/m
H_BAR = 1.055e-34  # J·s
C_LIGHT = 3.0e8  # m/s


def load_and_correct(fpath):
    """加载单条曲线并做基线校正"""
    c = AFMForceCurve(fpath)
    z_raw = np.array(c.z, dtype=float)
    f_raw = np.array(c.force, dtype=float)
    if c.z_unit in ('um', 'μm'):
        z_raw = z_raw * 1000.0
    if c.force_unit in ('uN', 'μN'):
        f_raw = f_raw * 1000.0
    
    z = z_raw[::-1].copy()
    f = f_raw[::-1].copy()
    
    mask_far = (z >= 0) & (z <= 100)
    if np.sum(mask_far) >= 5:
        a, b = np.polyfit(z[mask_far], f[mask_far], 1)
        f_corr = f - (a * z + b)
    elif np.sum(mask_far) >= 3:
        offset = np.mean(f[mask_far])
        f_corr = f - offset
    else:
        f_corr = f
    
    return z, f_corr, c


def analyze_curve(rel_path):
    """分析单条曲线的全部过渡区参数"""
    z, f_corr, c = load_and_correct(rel_path)
    
    snap_idx = int(np.argmin(f_corr))
    snap_z, snap_f = float(z[snap_idx]), float(f_corr[snap_idx])
    
    # contact 点
    after_snap = np.arange(snap_idx + 1, len(z))
    cc = after_snap[f_corr[after_snap] >= 0]
    if len(cc) > 0:
        contact_idx = int(cc[0])
        contact_z = float(z[contact_idx])
        contact_f = float(f_corr[contact_idx])
    else:
        contact_idx = len(z) - 1
        contact_z = float(z[-1])
        contact_f = float(f_corr[-1])
    
    # snap-in 前起始点（f > -2 nN 的最后一个点）
    before = np.arange(0, snap_idx)
    sc = before[f_corr[before] > -2.0]
    if len(sc) > 0:
        start_idx = int(sc[-1])
    else:
        start_idx = max(0, snap_idx - 5)
    start_z = float(z[start_idx])
    start_f = float(f_corr[start_idx])
    
    # ===================== 模块 1：不对称性 =====================
    # 下降段
    drop_z = z[start_idx:snap_idx+1]
    drop_f = f_corr[start_idx:snap_idx+1]
    n_before = int(snap_idx - start_idx)
    
    if len(drop_z) >= 2:
        drop_slopes = np.diff(drop_f) / np.diff(drop_z)
        max_drop_slope = float(np.min(drop_slopes))  # 最负 = 下降最快
        avg_drop_slope = float((snap_f - start_f) / (snap_z - start_z)) if snap_z > start_z else 0.0
    else:
        max_drop_slope = avg_drop_slope = 0.0
    
    # 上升段
    rise_z = z[snap_idx:contact_idx+1]
    rise_f = f_corr[snap_idx:contact_idx+1]
    n_after = int(contact_idx - snap_idx)
    
    if len(rise_z) >= 2:
        rise_slopes = np.diff(rise_f) / np.diff(rise_z)
        max_rise_slope = float(np.max(rise_slopes))
        avg_rise_slope = float((contact_f - snap_f) / (contact_z - snap_z)) if contact_z > snap_z else 0.0
    else:
        max_rise_slope = avg_rise_slope = 0.0
    
    # 面积（功）
    if len(drop_z) >= 2:
        drop_area = float(-np.trapezoid(drop_f, drop_z))  # 负功（吸引力做功）
    else:
        drop_area = 0.0
    
    if len(rise_z) >= 2:
        rise_area_pos = rise_f[rise_f >= 0]
        rise_z_pos = rise_z[rise_f >= 0]
        if len(rise_z_pos) >= 2:
            rise_area = float(np.trapezoid(rise_f[rise_f < 0], rise_z[rise_f < 0]))  # 恢复段的负功部分
        else:
            rise_area = 0.0
    else:
        rise_area = 0.0
    
    # 能量耗散 = 下降段负功 + 上升段负功（恢复不完全的部分）
    energy_dissipated = float(drop_area + rise_area) if rise_area < 0 else drop_area
    
    asymmetry_ratio = abs(max_rise_slope / max_drop_slope) if max_drop_slope != 0 else 0.0
    
    # ===================== 模块 2：Snap-in 前 vdW 拟合（仅数据充足的曲线） =====================
    vdw_fit = None
    if n_before >= 10:  # 只有 1000nm-8nN 和 1500nm-8nN 满足
        # 选取 f < -2 的吸引区（避免噪声）
        valid = drop_f < -2.0
        if np.sum(valid) >= 5:
            vd_z = drop_z[valid]
            vd_f = np.abs(drop_f[valid])
            
            # 距离估计：d = contact_z - z
            d_est = contact_z - vd_z
            d_est = d_est[d_est > 0.5]  # 排除过近距离
            vd_f = vd_f[d_est > 0.5]
            
            if len(d_est) >= 5:
                log_d = np.log(d_est)
                log_f = np.log(vd_f)
                
                # 线性拟合 log|F| = C - n*log(d)
                coeffs = np.polyfit(log_d, log_f, 1)
                n_power = float(-coeffs[0])
                logC = float(coeffs[1])
                r2 = float(1 - np.sum((log_f - np.polyval(coeffs, log_d))**2) / np.sum((log_f - np.mean(log_f))**2))
                
                # 反推 Hamaker A（假设非延迟 vdW）
                # F = A*R/(6*d^2) => A = 6*F*d^2/R
                if n_power > 1.5:
                    A_fit = 6.0 * np.exp(logC) * 1e-9 / (R_PROBE * 1e9)  # 简化为 nm 单位
                else:
                    A_fit = 0.0
                
                vdw_fit = {
                    'n_power': n_power,
                    'logC': logC,
                    'R2': r2,
                    'A_fit_J': A_fit,
                    'n_points': int(len(d_est)),
                    'd_range_nm': [float(np.min(d_est)), float(np.max(d_est))],
                }
    
    # ===================== 模块 3：恢复行为与毛细桥判断 =====================
    recovery = {}
    if len(rise_z) >= 3:
        # 局部斜率
        local_slopes = np.diff(rise_f) / np.diff(rise_z)
        local_z = (rise_z[:-1] + rise_z[1:]) / 2
        
        # 检查 plateau（斜率接近 0 的连续区域）
        plateau_mask = np.abs(local_slopes) < 0.5  # N/m
        plateau_fraction = float(np.sum(plateau_mask) / len(local_slopes)) if len(local_slopes) > 0 else 0.0
        
        # 检查突然断裂（斜率突变）
        if len(local_slopes) >= 3:
            slope_diff = np.diff(local_slopes)
            max_slope_jump = float(np.max(np.abs(slope_diff)))
        else:
            max_slope_jump = 0.0
        
        # 非线性度：二阶差分
        if len(rise_f) >= 3:
            second_deriv = np.diff(rise_f, 2) / np.diff(rise_z[:-1])**2
            max_curvature = float(np.max(np.abs(second_deriv)))
        else:
            max_curvature = 0.0
        
        recovery = {
            'plateau_fraction': plateau_fraction,
            'max_slope_jump': max_slope_jump,
            'max_curvature': max_curvature,
            'local_slopes': local_slopes.tolist(),
            'local_z': local_z.tolist(),
        }
    
    # ===================== 模块 4：延迟 vdW 检验（间接） =====================
    # 理论值计算
    d0 = 0.3e-9  # 截断距离 0.3 nm
    A_typical = 4e-19  # J
    
    # 非延迟 vdW（DMT）
    F_vdw_nonret = A_typical * R_PROBE / (12 * d0**2)  # N
    F_vdw_nonret_nN = F_vdw_nonret * 1e9
    
    # 需要解释实测力所需的 Hamaker
    F_meas = abs(snap_f) * 1e-9  # N
    A_required = F_meas * 12 * d0**2 / R_PROBE
    
    # 延迟 vdW（Casimir-Polder）
    eta = 0.4
    F_cp = (np.pi**3 * H_BAR * C_LIGHT * R_PROBE / (360 * d0**3)) * eta
    F_cp_nN = F_cp * 1e9
    
    # 理论毛细力（球-平面）
    F_cap_theory = 4 * np.pi * R_PROBE * GAMMA_WATER
    F_cap_theory_nN = F_cap_theory * 1e9
    
    vdW_check = {
        'F_vdw_nonret_nN': float(F_vdw_nonret_nN),
        'A_required_J': float(A_required),
        'A_required_vs_typical': float(A_required / A_typical),
        'F_casimir_nN': float(F_cp_nN),
        'F_capillary_theory_nN': float(F_cap_theory_nN),
        'F_measured_nN': abs(snap_f),
        'F_vdw_plus_cap_nN': float(F_vdw_nonret_nN + F_cap_theory_nN),
    }
    
    return {
        'file': Path(rel_path).name,
        'disp_nm': float(c.piezo_displacement) if c.piezo_displacement else None,
        'setpoint': f"{c.setpoint_force}{c.setpoint_unit}",
        'snap_f_nN': snap_f,
        'snap_z_nm': snap_z,
        'contact_z_nm': contact_z,
        'n_before': n_before,
        'n_after': n_after,
        'max_drop_slope': max_drop_slope,
        'avg_drop_slope': avg_drop_slope,
        'max_rise_slope': max_rise_slope,
        'avg_rise_slope': avg_rise_slope,
        'asymmetry_ratio': asymmetry_ratio,
        'drop_area_nN_nm': drop_area,
        'energy_dissipated_nN_nm': energy_dissipated,
        'vdw_fit': vdw_fit,
        'recovery': recovery,
        'vdW_check': vdW_check,
        'drop_z': drop_z.tolist(),
        'drop_f': drop_f.tolist(),
        'rise_z': rise_z.tolist(),
        'rise_f': rise_f.tolist(),
    }


def main():
    root = Path(__file__).parent.parent / '20260409'
    results = []
    
    for fpath in sorted(root.glob('JJS*.txt')):
        rel = str(fpath.relative_to(Path(__file__).parent.parent))
        res = analyze_curve(rel)
        results.append(res)
        
        # 打印摘要
        fit_str = ""
        if res['vdw_fit']:
            fit = res['vdw_fit']
            fit_str = f" | vdW n={fit['n_power']:.2f} R2={fit['R2']:.3f}"
        fname = res['file'][:25]
        print(f"{fname:25s}  asym={res['asymmetry_ratio']:.2f}  "
              f"drop={res['max_drop_slope']:8.1f}  rise={res['max_rise_slope']:7.2f}  "
              f"n_before={res['n_before']:3d}  n_after={res['n_after']:3d}{fit_str}")
    
    # 保存 JSON
    out = Path('results') / 'jjs_transition_deep_analysis.json'
    out.parent.mkdir(exist_ok=True)
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nSaved: {out}")


if __name__ == '__main__':
    main()
