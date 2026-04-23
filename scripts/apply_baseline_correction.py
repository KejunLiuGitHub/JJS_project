# -*- coding: utf-8 -*-
"""
AFM 力曲线基线校正：线性拟合法（v2）
取 z ∈ [0, 100] nm 的数据段拟合直线 F = a*z + b，整条曲线减去该直线
自动处理 nm/um 单位差异，标记无远离端的异常文件
"""

import json
from pathlib import Path
from parser import AFMForceCurve, load_all_curves


def linear_baseline_correction(z, force, z_unit='nm', force_unit='nN', z_range_nm=(0, 100)):
    """
    在指定 z 范围内拟合直线基线，并返回校正后的力
    z_range_nm: 以 nm 为单位的范围
    返回：校正后的力数组、基线参数 (a, b)、参与拟合的点数、状态信息
    """
    z_min, z_max = z_range_nm
    
    # 统一转换为 nm（如果单位是 um，z 值需要乘以 1000）
    is_um = (z_unit == 'um')
    
    if is_um:
        z_converted = [zi * 1000 for zi in z]
    else:
        z_converted = list(z)
    
    # 选取 z 在范围内的数据点
    selected_z = []
    selected_f = []
    for zi, fi in zip(z_converted, force):
        if z_min <= zi <= z_max:
            selected_z.append(zi)
            selected_f.append(fi)
    
    n = len(selected_z)
    
    # 如果没有点在范围内，尝试放宽到 [0, 200] nm
    if n < 3:
        for zi, fi in zip(z_converted, force):
            if z_min <= zi <= 200:
                selected_z.append(zi)
                selected_f.append(fi)
        n = len(selected_z)
    
    if n < 3:
        return None, None, n, 'no_far_end', is_um
    
    # 检查远离端是否平缓（标准差小）
    mean_f = sum(selected_f) / len(selected_f)
    std_f = (sum((f - mean_f)**2 for f in selected_f) / len(selected_f)) ** 0.5
    
    # 如果远离端标准差 > 阈值，说明远离端已经有显著的力变化（非平台区）
    # 可能的原因：1) 数据不含远离端；2) 基线有强漂移
    if std_f > 5.0 and n < 10:
        return None, None, n, 'unstable_far_end', is_um
    
    # 线性回归 F = a*z + b
    sum_z = sum(selected_z)
    sum_f = sum(selected_f)
    sum_z2 = sum(zi**2 for zi in selected_z)
    sum_zf = sum(zi * fi for zi, fi in zip(selected_z, selected_f))
    
    denominator = n * sum_z2 - sum_z**2
    if abs(denominator) < 1e-12:
        a = 0.0
        b = sum_f / n
    else:
        a = (n * sum_zf - sum_z * sum_f) / denominator
        b = (sum_f - a * sum_z) / n
    
    # 基线质量检查：如果截距 b 的绝对值 > 300 nN，或斜率 a 的绝对值 > 10 nN/nm，
    # 说明 z∈[0,100] 范围内力变化剧烈，可能不是远离端
    if abs(b) > 300 or abs(a) > 10:
        return None, None, n, 'invalid_baseline', is_um
    
    # 校正：F_corrected = F_raw - (a*z_converted + b)
    corrected_force = [fi - (a * zi + b) for zi, fi in zip(z_converted, force)]
    
    return corrected_force, (a, b), n, 'ok', is_um


def main():
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    curves = load_all_curves(project_root)
    
    print("=" * 120)
    print("AFM 力曲线线性基线校正 v2 (z ∈ [0, 100] nm 拟合)")
    print("=" * 120)
    print(f"{'文件名':<55} {'单位':>5} {'点数':>5} {'斜率a':>10} {'截距b':>10} {'原始min':>10} {'校正后min':>12} {'状态':>12}")
    print("-" * 120)
    
    corrected_metadata = []
    discard_list = []
    
    for rel, c in sorted(curves.items()):
        # 从 parser 的 force_unit 推断 z 的单位
        # 注意：z 的单位与力的单位是独立的。这里通过数值范围判断
        corrected_f, params, n_pts, status, is_um = linear_baseline_correction(
            c.z, c.force, c.z_unit, c.force_unit, z_range_nm=(0, 100)
        )
        
        unit_str = 'um' if is_um else 'nm'
        
        if corrected_f is None:
            reason = {
                'no_far_end': '无远离端',
                'unstable_far_end': '远离端不稳',
                'invalid_baseline': '基线异常'
            }.get(status, status)
            print(f"{rel:<55} {unit_str:>5} {n_pts:>5} {'N/A':>10} {'N/A':>10} {c.min_force:>10.2f} {'N/A':>12} {reason:>12}")
            discard_list.append({'file': rel, 'reason': reason, 'points_in_range': n_pts, 'is_um': is_um})
            continue
        
        a, b = params
        raw_min = c.min_force
        corr_min = min(corrected_f)
        
        # 计算校正后的 snap-in 位置
        snap_in_idx = corrected_f.index(corr_min)
        snap_in_z = c.z[snap_in_idx]
        if is_um:
            snap_in_z = snap_in_z * 1000
        
        print(f"{rel:<55} {unit_str:>5} {n_pts:>5} {a:>10.4f} {b:>10.2f} {raw_min:>10.2f} {corr_min:>12.2f} {'OK':>12}")
        
        corrected_metadata.append({
            'file': rel,
            'probe': c.probe_model,
            'material': c.material,
            'substrate': c.substrate,
            'piezo_displacement_nm': c.piezo_displacement,
            'setpoint_force': c.setpoint_force,
            'setpoint_unit': c.setpoint_unit,
            'force_unit': c.force_unit,
            'is_um': is_um,
            'baseline_slope_nN_per_nm': a,
            'baseline_intercept_nN': b,
            'baseline_fit_points': n_pts,
            'raw_min_force_nN': raw_min,
            'corrected_min_force_nN': corr_min,
            'snap_in_z_nm': snap_in_z,
            'data_points': len(c.z)
        })
    
    # 保存结果
    out_dir = project_root / 'results'
    out_dir.mkdir(parents=True, exist_ok=True)
    
    with open(out_dir / 'metadata_baseline_corrected.json', 'w', encoding='utf-8') as f:
        json.dump(corrected_metadata, f, ensure_ascii=False, indent=2)
    
    with open(out_dir / 'discarded_files.json', 'w', encoding='utf-8') as f:
        json.dump(discard_list, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*120}")
    print(f"校正成功: {len(corrected_metadata)} 条")
    print(f"舍弃文件: {len(discard_list)} 条 (原因: 无远离端 / 基线异常)")
    print(f"结果保存: results/metadata_baseline_corrected.json")
    print(f"舍弃列表: results/discarded_files.json")


if __name__ == '__main__':
    main()
