# -*- coding: utf-8 -*-
"""
AFM 力曲线分析与绘图核心模块
功能：基线校正、多曲线叠加、双区高亮、关键参数自动提取
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from parser import AFMForceCurve, load_all_curves


def baseline_correct(curve, z_range_nm=(0, 100)):
    """对单条曲线进行线性基线校正"""
    z = np.array(curve.z)
    f = np.array(curve.force)
    
    # um -> nm 转换
    if curve.z_unit == 'um':
        z = z * 1000.0
    
    z_min, z_max = z_range_nm
    mask = (z >= z_min) & (z <= z_max)
    
    if mask.sum() < 3:
        return None, None
    
    z_baseline = z[mask]
    f_baseline = f[mask]
    
    # 线性拟合
    A = np.vstack([z_baseline, np.ones(len(z_baseline))]).T
    a, b = np.linalg.lstsq(A, f_baseline, rcond=None)[0]
    
    f_corrected = f - (a * z + b)
    
    return z, f_corrected, (a, b)


def extract_snap_in_features(z, f):
    """提取 snap-in 关键参数"""
    # 寻找最小力（最负值）
    min_idx = np.argmin(f)
    snap_in_force = float(f[min_idx])
    snap_in_z = float(z[min_idx])
    
    # 接触点：snap-in 后第一个 F > 0 的点（或力反弹点）
    contact_candidates = np.where((z < snap_in_z) & (f > 0))[0]
    if len(contact_candidates) > 0:
        contact_idx = contact_candidates[0]
        contact_z = float(z[contact_idx])
        contact_f = float(f[contact_idx])
    else:
        contact_idx = None
        contact_z = None
        contact_f = None
    
    # 从 snap-in 起始到最低点的平均力梯度（近似）
    # 寻找 snap-in 起始点：F 从接近 0 开始快速下降的位置
    pre_snap = f[z > snap_in_z + 10]  # snap-in 前 10nm
    if len(pre_snap) > 0:
        onset_f = np.median(pre_snap[-5:]) if len(pre_snap) >= 5 else pre_snap[-1]
    else:
        onset_f = 0.0
    
    # 力梯度估计
    dz = snap_in_z - np.min(z[z > snap_in_z]) if np.any(z > snap_in_z) else 1.0
    if dz > 0 and contact_idx is not None:
        df = contact_f - snap_in_force
        gradient = abs(df / dz)
    else:
        gradient = None
    
    return {
        'snap_in_force_nN': snap_in_force,
        'snap_in_z_nm': snap_in_z,
        'contact_z_nm': contact_z,
        'contact_f_nN': contact_f,
        'onset_f_nN': onset_f,
        'gradient_nN_per_nm': gradient,
    }


def extract_mechanical_features(z, f):
    """提取深压段力学参数"""
    # 接触点：F > 0 的起始位置
    contact_mask = f > 0
    if not np.any(contact_mask):
        return None
    
    contact_idx = np.where(contact_mask)[0][0]
    contact_z = z[contact_idx]
    
    # 深压段：F > 0 的区域
    z_rep = z[contact_mask]
    f_rep = f[contact_mask]
    
    if len(z_rep) < 3:
        return None
    
    # 有效刚度：深压段线性拟合斜率 dF/dz
    A = np.vstack([z_rep, np.ones(len(z_rep))]).T
    k_eff, offset = np.linalg.lstsq(A, f_rep, rcond=None)[0]
    
    # 最大压入深度
    max_indent = float(np.max(z_rep) - contact_z) if len(z_rep) > 0 else 0
    
    # 最大排斥力
    max_force = float(np.max(f))
    
    return {
        'contact_z_nm': float(contact_z),
        'effective_stiffness_nN_per_nm': float(k_eff),
        'max_indent_nm': max_indent,
        'max_force_nN': max_force,
    }


def plot_group(curves_dict, title, outpath, figsize=(10, 7), 
               xlim=None, ylim=None, show_legend=True, 
               highlight_regions=True, annotate_snapin=True):
    """
    绘制多曲线叠加图
    curves_dict: {label: (z_array, f_array, color), ...}
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    snap_in_data = []
    
    for label, (z, f, color) in curves_dict.items():
        ax.plot(z, f, color=color, linewidth=1.5, label=label, alpha=0.85)
        
        if annotate_snapin:
            min_idx = np.argmin(f)
            si_z, si_f = z[min_idx], f[min_idx]
            if si_f < -5:
                ax.plot(si_z, si_f, 'o', color=color, markersize=6)
                snap_in_data.append((label, si_f, si_z))
    
    ax.axhline(0, color='k', linewidth=0.8, linestyle='--')
    
    if highlight_regions:
        # 吸引区背景（淡红色）
        ax.axhspan(ylim[0] if ylim else -200, 0, alpha=0.05, color='red')
        # 排斥区背景（淡蓝色）
        ax.axhspan(0, ylim[1] if ylim else 200, alpha=0.05, color='blue')
    
    if xlim:
        ax.set_xlim(xlim)
    if ylim:
        ax.set_ylim(ylim)
    
    ax.invert_xaxis()  # AFM 惯例：z 减小 = 探针下压
    ax.set_xlabel('Z Position (nm)', fontsize=12)
    ax.set_ylabel('Force (nN)', fontsize=12)
    ax.set_title(title, fontsize=13, fontweight='bold')
    
    if show_legend and len(curves_dict) > 1:
        ax.legend(loc='best', fontsize=9, framealpha=0.9)
    
    fig.tight_layout()
    fig.savefig(outpath, dpi=200, bbox_inches='tight')
    plt.close(fig)
    print(f"[已绘图] {outpath}")
    
    return snap_in_data


def load_and_correct_all(project_root):
    """加载所有曲线并进行基线校正"""
    curves = load_all_curves(project_root)
    corrected = {}
    metadata = []
    
    for rel, c in sorted(curves.items()):
        result = baseline_correct(c)
        if result[0] is None:
            continue
        z, f_corr, (a, b) = result
        
        # 舍弃基线截距绝对值 > 200 nN 的文件
        if abs(b) > 200:
            print(f"[舍弃] {rel}: baseline intercept {b:.1f} nN too large")
            continue
        
        corrected[rel] = (z, f_corr, c)
        
        snap = extract_snap_in_features(z, f_corr)
        mech = extract_mechanical_features(z, f_corr)
        
        meta = {
            'file': rel,
            'probe': c.probe_model,
            'material': c.material,
            'substrate': c.substrate,
            'displacement_nm': c.piezo_displacement,
            'setpoint': f"{c.setpoint_force}{c.setpoint_unit}",
            'baseline_slope_nN_per_nm': float(a),
            'baseline_intercept_nN': float(b),
        }
        if snap:
            meta.update(snap)
        if mech:
            meta.update(mech)
        metadata.append(meta)
    
    return corrected, metadata


if __name__ == '__main__':
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    corrected, metadata = load_and_correct_all(project_root)
    
    # 保存提取的参数
    with open(project_root / 'results' / 'extracted_features.json', 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    print(f"\n基线校正完成: {len(corrected)} 条曲线")
    print(f"参数已保存: results/extracted_features.json")
