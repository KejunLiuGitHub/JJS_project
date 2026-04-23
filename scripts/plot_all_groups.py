# -*- coding: utf-8 -*-
"""
批量绘制所有分析图组
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from matplotlib import cm
from analysis_plotter import load_and_correct_all, plot_group, extract_snap_in_features

plt.rcParams['font.size'] = 10
plt.rcParams['axes.labelsize'] = 11
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['legend.fontsize'] = 8
plt.rcParams['figure.dpi'] = 200


def get_jjs_color(label, displacement):
    """JJS系列按位移分配颜色"""
    disp = displacement or 0
    if disp <= 500:
        return '#D32F2F'  # 深红（小位移，强snap-in）
    elif disp <= 1000:
        return '#F57C00'  # 橙
    else:
        return '#1976D2'  # 蓝（大位移，弱snap-in）


def group_a1_jjs_total(corrected, outdir):
    """图组A-1：JJS悬浮薄膜总图"""
    jjs = {k: v for k, v in corrected.items() if k.startswith('20260409')}
    
    curves = {}
    for rel, (z, f, c) in sorted(jjs.items()):
        label = rel.replace('20260409\\', '').replace(' - NanoScope Analysis.txt', '')
        color = get_jjs_color(label, c.piezo_displacement)
        curves[label] = (z, f, color)
    
    snap_data = plot_group(
        curves,
        title='JJS Free-Standing COF Film: Snap-in Across Displacements & Setpoints\n(Baseline-Corrected)',
        outpath=outdir / 'A1_JJS_total_snapin.png',
        figsize=(11, 7),
        xlim=(1050, -50),
        ylim=(-170, 30),
        highlight_regions=True
    )
    
    return snap_data


def group_a2_pfpe_oh_series(corrected, outdir):
    """图组A-2：linker1-PFPE-OH位移系列"""
    pfpe = {k: v for k, v in corrected.items() 
            if 'linker1-PFPE-OH' in k and '20260415' in k}
    
    # 按位移排序，选取代表性文件
    selected = {}
    colors = plt.cm.viridis(np.linspace(0, 1, 10))
    
    disp_files = sorted(pfpe.items(), key=lambda x: x[1][2].piezo_displacement or 0)
    step = max(1, len(disp_files) // 10)
    
    for i, (rel, (z, f, c)) in enumerate(disp_files[::step][:10]):
        label = f"{int(c.piezo_displacement or 0)}nm"
        selected[label] = (z, f, colors[i])
    
    plot_group(
        selected,
        title='linker1-PFPE-OH on Cu Grid: Displacement Dependence\n(Baseline-Corrected)',
        outpath=outdir / 'A2_PFPE_OH_displacement_series.png',
        figsize=(11, 7),
        xlim=(13000, -200),
        ylim=(-30, 40),
        highlight_regions=True
    )


def group_a3_linker2_paa(corrected, outdir):
    """图组A-3：linker2-paa异常粘附"""
    l2 = {k: v for k, v in corrected.items() 
          if 'linker2' in k.lower() and '20260415' in k}
    
    curves = {}
    colors = {'150nm': '#C62828', '300nm': '#E53935', '500nm': '#FB8C00', 
              '1000nm': '#FDD835', '1500nm': '#43A047', '2000nm': '#1E88E5',
              '2500nm': '#8E24AA'}
    
    for rel, (z, f, c) in sorted(l2.items()):
        disp = str(int(c.piezo_displacement or 0))
        label = f"{disp}nm"
        color = colors.get(disp, '#757575')
        curves[label] = (z, f, color)
    
    plot_group(
        curves,
        title='linker2-paa on Cu Grid: Anomalous Adhesion at 1500nm\n(Baseline-Corrected)',
        outpath=outdir / 'A3_linker2_paa_anomalous.png',
        figsize=(11, 7),
        xlim=(1600, -100),
        ylim=(-140, 50),
        highlight_regions=True
    )


def group_a4_snap_in_bar(corrected, outdir):
    """图组A-4：跨批次snap-in强度对比柱状图"""
    snap_data = []
    
    for rel, (z, f, c) in corrected.items():
        min_idx = np.argmin(f)
        si_f = f[min_idx]
        if si_f < -1:
            folder = rel.split('\\')[0]
            snap_data.append({
                'file': rel,
                'folder': folder,
                'displacement': c.piezo_displacement,
                'setpoint': f"{c.setpoint_force}{c.setpoint_unit}",
                'snap_in_nN': float(si_f),
                'probe': c.probe_model,
            })
    
    # 按批次分组取最强snap-in
    batch_max = {}
    for d in snap_data:
        folder = d['folder']
        if folder not in batch_max or d['snap_in_nN'] < batch_max[folder]['snap_in_nN']:
            batch_max[folder] = d
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    folders = sorted(batch_max.keys())
    vals = [batch_max[f]['snap_in_nN'] for f in folders]
    colors = ['#D32F2F', '#F57C00', '#1976D2']
    
    bars = ax.bar(range(len(folders)), vals, color=colors[:len(folders)], width=0.6, edgecolor='black')
    
    for bar, f in zip(bars, folders):
        d = batch_max[f]
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() - 5, 
                f"{d['snap_in_nN']:.1f} nN\n{d['probe']}", 
                ha='center', va='top', fontsize=9, color='white', fontweight='bold')
    
    ax.set_xticks(range(len(folders)))
    ax.set_xticklabels(['JJS\n(Free-standing)', 'linker1\n(Cu grid)', 'k80-linker1\n(Cu grid)'])
    ax.set_ylabel('Maximum Snap-in Force (nN)', fontsize=12)
    ax.set_title('Cross-Batch Snap-in Comparison (Baseline-Corrected)\nStrongest Event per Batch', fontsize=13, fontweight='bold')
    ax.axhline(0, color='k', linewidth=0.8)
    
    fig.tight_layout()
    fig.savefig(outdir / 'A4_cross_batch_snapin_comparison.png', dpi=200, bbox_inches='tight')
    plt.close(fig)
    print(f"[已绘图] {outdir / 'A4_cross_batch_snapin_comparison.png'}")
    
    return snap_data


def group_b1_paa_deep_press(corrected, outdir):
    """图组B-1：k80-linker1-paa深压系列"""
    paa = {k: v for k, v in corrected.items() 
           if 'k80-linker1-paa' in k and '3uN' in k and '20260416' in k}
    
    curves = {}
    colors = plt.cm.plasma(np.linspace(0.2, 0.9, len(paa)))
    
    for i, (rel, (z, f, c)) in enumerate(sorted(paa.items(), key=lambda x: x[1][2].piezo_displacement or 0)):
        disp = int(c.piezo_displacement or 0)
        label = f"{disp}nm"
        curves[label] = (z, f, colors[i])
    
    plot_group(
        curves,
        title='k80-linker1-paa Deep Pressing (3uN setpoint)\nRepulsive Regime = Film Mechanics\n(Baseline-Corrected)',
        outpath=outdir / 'B1_paa_deep_press.png',
        figsize=(11, 7),
        xlim=(5500, -200),
        ylim=(-10, 8),
        highlight_regions=True
    )


def group_b2_pfna_vs_sdbs(corrected, outdir):
    """图组B-2：PFNA vs SDBS深压对比"""
    pfna = {k: v for k, v in corrected.items() 
            if 'k80-linker1-PFNA' in k and '20260416' in k}
    sdbs = {k: v for k, v in corrected.items() 
            if 'k80-linker1-SDBS' in k and '20260416' in k}
    
    # 选取相同位移的代表性文件
    curves = {}
    
    for rel, (z, f, c) in sorted(pfna.items(), key=lambda x: x[1][2].piezo_displacement or 0)[:5]:
        disp = int(c.piezo_displacement or 0)
        label = f"PFNA {disp}nm"
        curves[label] = (z, f, '#1976D2')
    
    for rel, (z, f, c) in sorted(sdbs.items(), key=lambda x: x[1][2].piezo_displacement or 0)[:5]:
        disp = int(c.piezo_displacement or 0)
        label = f"SDBS {disp}nm"
        curves[label] = (z, f, '#D32F2F')
    
    plot_group(
        curves,
        title='PFNA vs SDBS Surface Modification: Mechanical Response\n(Baseline-Corrected)',
        outpath=outdir / 'B2_PFNA_vs_SDBS.png',
        figsize=(11, 7),
        xlim=(5500, -200),
        ylim=(-10, 8),
        highlight_regions=True
    )


def group_b3_jjs_repulsive(corrected, outdir):
    """图组B-3：JJS悬浮薄膜深压段"""
    jjs = {k: v for k, v in corrected.items() if k.startswith('20260409')}
    
    curves = {}
    colors = plt.cm.coolwarm(np.linspace(0, 1, len(jjs)))
    
    for i, (rel, (z, f, c)) in enumerate(sorted(jjs.items(), key=lambda x: x[1][2].piezo_displacement or 0)):
        label = f"{int(c.piezo_displacement or 0)}nm"
        curves[label] = (z, f, colors[i])
    
    plot_group(
        curves,
        title='JJS Free-Standing Film: Repulsive Regime (Contact Mechanics)\n(Baseline-Corrected)',
        outpath=outdir / 'B3_JJS_repulsive_regime.png',
        figsize=(11, 7),
        xlim=(1050, 920),
        ylim=(-5, 20),
        highlight_regions=False
    )


def main():
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    outdir = project_root / 'figures'
    outdir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("AFM 分析图组批量绘制")
    print("=" * 60)
    
    corrected, metadata = load_and_correct_all(project_root)
    
    print("\n--- 图组 A: Snap-in 异常吸引区 ---")
    snap_jjs = group_a1_jjs_total(corrected, outdir)
    group_a2_pfpe_oh_series(corrected, outdir)
    group_a3_linker2_paa(corrected, outdir)
    snap_all = group_a4_snap_in_bar(corrected, outdir)
    
    print("\n--- 图组 B: 薄膜深压力学性能 ---")
    group_b1_paa_deep_press(corrected, outdir)
    group_b2_pfna_vs_sdbs(corrected, outdir)
    group_b3_jjs_repulsive(corrected, outdir)
    
    print(f"\n全部完成，图片保存在: {outdir}")
    
    # 保存snap-in汇总
    with open(project_root / 'results' / 'snap_in_summary.json', 'w', encoding='utf-8') as f:
        json.dump(snap_all, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    main()
