# -*- coding: utf-8 -*-
"""
综合对比绘图脚本
生成 7 张 publication-quality 对比图
"""
import sys, json, numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from parser import AFMForceCurve, load_all_curves

plt.rcParams['font.size'] = 12
plt.rcParams['axes.labelsize'] = 13
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['legend.fontsize'] = 10

def load_features():
    with open('results/extracted_features.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def load_curve_data(rel_path):
    """加载单条曲线的校正后数据"""
    curve = AFMForceCurve(rel_path)
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
    
    # 匹配 extracted_features.json 中的校正逻辑
    has_attraction = np.any(force < 0)
    if has_attraction:
        mask = (z >= 0) & (z <= 100)
        count = int(np.sum(mask))
        if count >= 5:
            z_fit = z[mask]
            f_fit = force[mask]
            coeffs = np.polyfit(z_fit, f_fit, 1)
            a, b = coeffs[0], coeffs[1]
            f_corr = force - (a * z + b)
        elif count >= 3:
            offset = np.mean(force[mask])
            f_corr = force - offset
        else:
            f_corr = force  # fallback
    else:
        f_corr = force
    
    return z, f_corr, curve


def plot_group(ax, files, title, xlabel='Z Position (nm)', ylabel='Force (nN)', 
               xlim=None, ylim=None, align_zero=False, legend_title=None):
    """在 ax 上绘制一组曲线"""
    colors = plt.cm.tab10(np.linspace(0, 1, len(files)))
    for i, (rel, label) in enumerate(files):
        try:
            z, f, curve = load_curve_data(rel)
            if align_zero and len(z) > 0:
                z = z - z.max()  # 以最大 z 为参考零点
            ax.plot(z, f, color=colors[i], label=label, linewidth=1.5)
        except Exception as e:
            print(f"[skip] {rel}: {e}")
    
    ax.axhline(0, color='black', linestyle='--', linewidth=0.8)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title, fontweight='bold')
    if xlim:
        ax.set_xlim(xlim)
    if ylim:
        ax.set_ylim(ylim)
    if legend_title:
        ax.legend(title=legend_title, loc='best')
    else:
        ax.legend(loc='best')
    ax.grid(True, alpha=0.3)


def fig_A1_JJS():
    """A1: JJS 悬浮薄膜总图"""
    curves = load_all_curves('.')
    jjs_files = [(rel, rel) for rel, c in sorted(curves.items()) 
                 if 'JJS' in rel and '20260409' in rel]
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    groups = {
        '454/500nm': [f for f in jjs_files if '454nm' in f[0] or '500nm' in f[0]],
        '1000nm': [f for f in jjs_files if '1000nm' in f[0]],
        '1500nm': [f for f in jjs_files if '1500nm' in f[0]],
    }
    
    for ax, (name, files) in zip(axes.flat, groups.items()):
        plot_group(ax, files, f'JJS {name}', ylim=(-180, 60))
    
    # 第4个 subplot: 跨位移对比（对齐到 snap-in 位置）
    ax = axes.flat[3]
    for rel, _ in jjs_files:
        try:
            z, f, curve = load_curve_data(rel)
            snap_idx = np.argmin(f)
            z_align = z - z[snap_idx]
            ax.plot(z_align, f, alpha=0.7, linewidth=1.2)
        except Exception as e:
            pass
    ax.axhline(0, color='black', linestyle='--', linewidth=0.8)
    ax.set_xlabel('Relative Z (nm)')
    ax.set_ylabel('Force (nN)')
    ax.set_title('JJS All Curves Aligned at Snap-in', fontweight='bold')
    ax.set_ylim(-180, 60)
    ax.grid(True, alpha=0.3)
    
    fig.suptitle('A1: JJS Suspended Film Snap-in (Baseline-Corrected)', 
                 fontsize=16, fontweight='bold', y=1.02)
    fig.tight_layout()
    fig.savefig('figures/A1_JJS_total_snapin.png', dpi=200, bbox_inches='tight')
    plt.close(fig)
    print("Saved A1_JJS_total_snapin.png")


def fig_A4_cross_batch():
    """A4: 跨批次 snap-in 对比柱状图"""
    feats = load_features()
    
    groups = {
        'JJS (suspended)': [],
        'linker1 Cu grid': [],
        'linker2 Cu grid': [],
        'k80-linker1 Cu grid': [],
        'k80-linker2 Cu grid': [],
    }
    
    for r in feats:
        if r['snap_in_force_nN'] is None:
            continue
        f = r['snap_in_force_nN']
        name = r['file']
        if 'JJS' in name:
            groups['JJS (suspended)'].append(f)
        elif 'k80-linker1' in name and 'k80-linker2' not in name:
            groups['k80-linker1 Cu grid'].append(f)
        elif 'k80-linker2' in name:
            groups['k80-linker2 Cu grid'].append(f)
        elif 'linker1' in name and 'k80' not in name:
            groups['linker1 Cu grid'].append(f)
        elif 'linker2' in name and 'k80' not in name:
            groups['linker2 Cu grid'].append(f)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(groups))
    means = [np.mean(v) if v else 0 for v in groups.values()]
    stds = [np.std(v) if v else 0 for v in groups.values()]
    mins = [np.min(v) if v else 0 for v in groups.values()]
    
    bars = ax.bar(x, means, yerr=stds, capsize=5, color=['#e74c3c','#3498db','#2ecc71','#f39c12','#9b59b6'],
                  edgecolor='black', linewidth=1.2)
    ax.scatter(np.repeat(x, [len(v) for v in groups.values()]), 
               [item for sublist in groups.values() for item in sublist],
               color='black', zorder=5, s=30, alpha=0.6)
    
    ax.set_xticks(x)
    ax.set_xticklabels(groups.keys(), rotation=15, ha='right')
    ax.set_ylabel('Snap-in Force (nN)')
    ax.set_title('A4: Cross-Batch Snap-in Comparison (Baseline-Corrected)', fontweight='bold')
    ax.axhline(0, color='black', linestyle='-', linewidth=0.5)
    ax.grid(axis='y', alpha=0.3)
    fig.tight_layout()
    fig.savefig('figures/A4_cross_batch_snapin_comparison.png', dpi=200, bbox_inches='tight')
    plt.close(fig)
    print("Saved A4_cross_batch_snapin_comparison.png")


def fig_B1_paa_deep():
    """B1: k80-linker1-paa 深压系列"""
    curves = load_all_curves('.')
    files = sorted([(rel, f"{c.piezo_displacement}{c.z_unit}") 
                    for rel, c in curves.items() 
                    if 'k80-linker1-paa' in rel])
    
    fig, ax = plt.subplots(figsize=(10, 7))
    colors = plt.cm.plasma(np.linspace(0.2, 0.9, len(files)))
    for i, (rel, label) in enumerate(files):
        try:
            z, f, curve = load_curve_data(rel)
            ax.plot(z, f, color=colors[i], label=label, linewidth=1.5)
        except Exception as e:
            print(f"[skip] {rel}: {e}")
    
    ax.axhline(0, color='black', linestyle='--', linewidth=0.8)
    ax.set_xlabel('Z Position (nm)')
    ax.set_ylabel('Force (nN)')
    ax.set_title('B1: k80-linker1-paa Deep Pressing (3uN/10uN setpoint)\n(Baseline-Corrected)', fontweight='bold')
    ax.legend(title='Displacement', loc='best', ncol=2)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig('figures/B1_paa_deep_press.png', dpi=200, bbox_inches='tight')
    plt.close(fig)
    print("Saved B1_paa_deep_press.png")


def fig_B2_PFNA_SDBS():
    """B2: PFNA vs SDBS 表面修饰对比"""
    curves = load_all_curves('.')
    pfna = sorted([(rel, f"PFNA {c.piezo_displacement}{c.z_unit}") 
                   for rel, c in curves.items() 
                   if 'k80-linker1-PFNA' in rel])
    sdbs = sorted([(rel, f"SDBS {c.piezo_displacement}{c.z_unit}") 
                   for rel, c in curves.items() 
                   if 'k80-linker1-SDBS' in rel])
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    for ax, files, title in zip(axes, [pfna, sdbs], ['PFNA', 'SDBS']):
        colors = plt.cm.viridis(np.linspace(0.2, 0.9, len(files)))
        for i, (rel, label) in enumerate(files):
            try:
                z, f, curve = load_curve_data(rel)
                ax.plot(z, f, color=colors[i], label=label, linewidth=1.5)
            except Exception as e:
                print(f"[skip] {rel}: {e}")
        ax.axhline(0, color='black', linestyle='--', linewidth=0.8)
        ax.set_xlabel('Z Position (nm)')
        ax.set_ylabel('Force (nN)')
        ax.set_title(f'{title} (10uN setpoint)', fontweight='bold')
        ax.legend(title='Displacement', loc='best', ncol=2)
        ax.grid(True, alpha=0.3)
    
    fig.suptitle('B2: Surface Modification Deep Press Comparison\n(Baseline-Corrected)', 
                 fontsize=14, fontweight='bold')
    fig.tight_layout()
    fig.savefig('figures/B2_PFNA_vs_SDBS.png', dpi=200, bbox_inches='tight')
    plt.close(fig)
    print("Saved B2_PFNA_vs_SDBS.png")


def fig_B3_JJS_repulsive():
    """B3: JJS 排斥段刚度（修正：仅取 snap-in 之后的 repulsive 区）"""
    curves = load_all_curves('.')
    files = sorted([(rel, rel.split('\\')[-1].replace(' - NanoScope Analysis.txt','')) 
                    for rel, c in curves.items() 
                    if 'JJS' in rel])
    
    fig, ax = plt.subplots(figsize=(10, 7))
    colors = plt.cm.tab10(np.linspace(0, 1, len(files)))
    slopes = []
    labels = []
    for i, (rel, label) in enumerate(files):
        try:
            z, f, curve = load_curve_data(rel)
            # 反转使 z 递增，匹配物理接近过程
            z_rev = z[::-1]
            f_rev = f[::-1]
            snap_idx = int(np.argmin(f_rev))
            after_snap = np.arange(snap_idx + 1, len(z_rev))
            cc = after_snap[f_rev[after_snap] >= 0]
            if len(cc) >= 3:
                contact_idx = int(cc[0])
                rep_mask = (np.arange(len(z_rev)) >= contact_idx) & (f_rev >= 0)
                if np.sum(rep_mask) >= 3:
                    rep_z = z_rev[rep_mask]
                    rep_f = f_rev[rep_mask]
                    slope = np.polyfit(rep_z, rep_f, 1)[0]
                    slopes.append(slope)
                    labels.append(label)
                    ax.plot(rep_z, rep_f, color=colors[i], label=f"{label} (k={slope:.3f})", linewidth=1.5, marker='o', markersize=3)
        except Exception as e:
            print(f"[skip] {rel}: {e}")
    
    ax.set_xlabel('Z Position (nm)')
    ax.set_ylabel('Force (nN)')
    ax.set_title('B3: JJS Repulsive Regime Contact Stiffness\n(Snap-in之后, Baseline-Corrected)', fontweight='bold')
    ax.legend(loc='best', ncol=2, fontsize=8)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig('figures/B3_JJS_repulsive_regime.png', dpi=200, bbox_inches='tight')
    plt.close(fig)
    print("Saved B3_JJS_repulsive_regime.png")


def main():
    Path('figures').mkdir(exist_ok=True)
    fig_A1_JJS()
    fig_A4_cross_batch()
    fig_B1_paa_deep()
    fig_B2_PFNA_SDBS()
    fig_B3_JJS_repulsive()
    print("\nAll figures generated.")


if __name__ == '__main__':
    main()
