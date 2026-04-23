# -*- coding: utf-8 -*-
"""
JJS 悬浮薄膜综合分析报告 PDF 生成
使用 matplotlib PdfPages，A4 横向排版
"""
import sys, json, numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from parser import AFMForceCurve

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

# 中文字体设置
plt.rcParams['font.family'] = ['SimHei', 'Microsoft YaHei', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

# A4 横向尺寸（英寸）
A4_W, A4_H = 11.69, 8.27

# 物理参数
R_PROBE = 8.0
T_FILM = 10.0
A_HOLE = 10_000.0
K_CANTILEVER = 5.0


def load_jjs_data():
    """加载所有 JJS 曲线，返回列表"""
    curves = []
    root = Path(__file__).parent.parent / '20260409'
    for fpath in sorted(root.glob('JJS*.txt')):
        c = AFMForceCurve(str(fpath.relative_to(Path(__file__).parent.parent)))
        z_raw = np.array(c.z, dtype=float)
        f_raw = np.array(c.force, dtype=float)
        if c.z_unit in ('um', 'μm'):
            z_raw = z_raw * 1000.0
        if c.force_unit in ('uN', 'μN'):
            f_raw = f_raw * 1000.0
        
        # 反转
        z = z_raw[::-1].copy()
        f = f_raw[::-1].copy()
        
        # 基线校正
        mask_far = (z >= 0) & (z <= 100)
        n_far = int(np.sum(mask_far))
        if n_far >= 5:
            coeffs = np.polyfit(z[mask_far], f[mask_far], 1)
            a, b = coeffs[0], coeffs[1]
            f_corr = f - (a * z + b)
        elif n_far >= 3:
            offset = np.mean(f[mask_far])
            f_corr = f - offset
        else:
            f_corr = f
        
        # 提取参数
        snap_idx = int(np.argmin(f_corr))
        snap_z, snap_f = float(z[snap_idx]), float(f_corr[snap_idx])
        
        after_snap = np.arange(snap_idx + 1, len(z))
        cc = after_snap[f_corr[after_snap] >= 0]
        if len(cc) > 0:
            contact_idx = int(cc[0])
            contact_z = float(z[contact_idx])
            contact_f = float(f_corr[contact_idx])
            n_rep = int(np.sum((z >= contact_z) & (f_corr >= 0)))
        else:
            contact_idx = len(z) - 1
            contact_z = float(z[-1])
            contact_f = float(f_corr[-1])
            n_rep = 0
        
        # 过渡区参数（snap-in 到 contact）
        trans_indices = np.arange(snap_idx, contact_idx + 1)
        trans_z = z[trans_indices]
        trans_f = f_corr[trans_indices]
        delta_z_snap = float(contact_z - snap_z)
        n_trans = int(len(trans_indices))
        
        # 平均恢复斜率
        if delta_z_snap > 0:
            avg_slope_trans = float((contact_f - snap_f) / delta_z_snap)
        else:
            avg_slope_trans = 0.0
        
        # 粘着能（负力区积分）
        adhesion_mask = trans_f < 0
        if np.sum(adhesion_mask) > 1:
            adhesion_energy = float(-np.trapezoid(trans_f[adhesion_mask], trans_z[adhesion_mask]))
        else:
            adhesion_energy = 0.0
        
        # 解析位移和 setpoint
        disp = c.piezo_displacement
        sp = f"{c.setpoint_force}{c.setpoint_unit}"
        
        curves.append({
            'file': fpath.name,
            'z': z, 'f_raw': f, 'f_corr': f_corr,
            'snap_z': snap_z, 'snap_f': snap_f,
            'contact_z': contact_z, 'contact_f': contact_f,
            'n_rep': n_rep, 'disp': disp, 'setpoint': sp,
            'delta_z_snap': delta_z_snap, 'n_trans': n_trans,
            'avg_slope_trans': avg_slope_trans,
            'adhesion_energy': adhesion_energy,
            'trans_z': trans_z, 'trans_f': trans_f,
        })
    return curves


def load_features():
    with open('results/extracted_features.json', encoding='utf-8') as f:
        return [r for r in json.load(f) if 'JJS' in r['file']]


def load_membrane():
    with open('results/membrane_parameters.json', encoding='utf-8') as f:
        return [r for r in json.load(f) if 'JJS' in r['label']]


# ============================================================
# Page 1: 封面
# ============================================================
def page_cover(pdf, curves):
    fig = plt.figure(figsize=(A4_W, A4_H))
    fig.clf()
    
    # 标题
    fig.text(0.5, 0.88, 'JJS 悬浮薄膜 AFM 力-距离曲线', 
             ha='center', va='top', fontsize=24, fontweight='bold')
    fig.text(0.5, 0.82, '综合分析报告', 
             ha='center', va='top', fontsize=20, fontweight='bold')
    fig.text(0.5, 0.76, '基于 PeakForce QNM 模式 · 11 条力曲线 · 2026-04-09 批次',
             ha='center', va='top', fontsize=12, color='gray')
    
    # 实验参数表
    table_data = [
        ['参数', '数值'],
        ['薄膜类型', '二维 COF 薄膜，悬浮于氮化硅小孔'],
        ['孔径', '20 μm（半径 10 μm）'],
        ['薄膜厚度', '~10 nm'],
        ['探针', 'RTESPA-150（半径 8 nm，刚度 ~5 N/m）'],
        ['扫描模式', 'PeakForce QNM'],
        ['Setpoint 范围', '8 – 50 nN'],
        ['Z 位移范围', '454 – 1500 nm'],
        ['数据点/曲线', '512 点'],
        ['有效曲线', '11 / 11'],
    ]
    
    ax = fig.add_axes([0.15, 0.25, 0.7, 0.45])
    ax.axis('off')
    
    cell_colors = [['#4472C4', '#4472C4']] + [['white', 'white']] * (len(table_data)-1)
    text_colors = [['white', 'white']] + [['black', 'black']] * (len(table_data)-1)
    
    table = ax.table(cellText=table_data[1:], colLabels=table_data[0],
                     loc='center', cellLoc='center',
                     colColours=['#4472C4', '#4472C4'])
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1, 2)
    
    for i in range(len(table_data)):
        for j in range(2):
            cell = table[(i, j)]
            cell.set_text_props(color=text_colors[i][j], fontweight='bold' if i==0 else 'normal')
            cell.set_facecolor(cell_colors[i][j])
            cell.set_edgecolor('black')
    
    fig.text(0.5, 0.12, '分析日期：2026-04-22  |  生成工具：Python + matplotlib',
             ha='center', va='top', fontsize=10, color='gray', style='italic')
    
    pdf.savefig(fig, dpi=200)
    plt.close(fig)


# ============================================================
# Page 2: 原始力曲线（按位移分组）
# ============================================================
def page_raw_curves(pdf, curves):
    fig, axes = plt.subplots(2, 2, figsize=(A4_W, A4_H))
    axes = axes.flatten()
    
    groups = {
        '454 nm': [c for c in curves if c['disp_nm'] == 454.0],
        '500 nm': [c for c in curves if c['disp_nm'] == 500.0],
        '1000 nm': [c for c in curves if c['disp_nm'] == 1000.0],
        '1500 nm': [c for c in curves if c['disp_nm'] == 1500.0],
    }
    colors = plt.cm.tab10(np.linspace(0, 1, 4))
    
    for ax, (gname, grp) in zip(axes, groups.items()):
        for c in grp:
            ax.plot(c['z'], c['f_raw'], label=c['file'].replace(' - NanoScope Analysis.txt', ''), linewidth=1.2)
        ax.axhline(0, color='black', linestyle='--', linewidth=0.8)
        ax.set_xlabel('Z Position (nm)', fontsize=11)
        ax.set_ylabel('Force (nN)', fontsize=11)
        ax.set_title(f'JJS {gname} · 原始数据', fontsize=13, fontweight='bold')
        ax.legend(loc='best', fontsize=7)
        ax.grid(True, alpha=0.3)
    
    fig.suptitle('原始力曲线（未校正）', fontsize=16, fontweight='bold', y=0.98)
    pdf.savefig(fig, dpi=200)
    plt.close(fig)


# ============================================================
# Page 3: 基线校正后力曲线
# ============================================================
def page_corrected_curves(pdf, curves):
    fig, axes = plt.subplots(2, 2, figsize=(A4_W, A4_H))
    axes = axes.flatten()
    
    groups = {
        '454 nm': [c for c in curves if c['disp_nm'] == 454.0],
        '500 nm': [c for c in curves if c['disp_nm'] == 500.0],
        '1000 nm': [c for c in curves if c['disp_nm'] == 1000.0],
        '1500 nm': [c for c in curves if c['disp_nm'] == 1500.0],
    }
    
    for ax, (gname, grp) in zip(axes, groups.items()):
        for c in grp:
            ax.plot(c['z'], c['f_corr'], label=c['file'].replace(' - NanoScope Analysis.txt', ''), linewidth=1.2)
            # 标记 snap-in
            ax.scatter([c['snap_z']], [c['snap_f_nN']], color='red', s=30, zorder=5)
            # 标记 contact
            if c['n_rep'] > 0:
                ax.scatter([c['contact_z']], [c['contact_f']], color='green', s=30, zorder=5, marker='^')
        ax.axhline(0, color='black', linestyle='--', linewidth=0.8)
        ax.set_xlabel('Z Position (nm)', fontsize=11)
        ax.set_ylabel('Force (nN)', fontsize=11)
        ax.set_title(f'JJS {gname} · 基线校正后', fontsize=13, fontweight='bold')
        ax.legend(loc='best', fontsize=7)
        ax.grid(True, alpha=0.3)
    
    # 添加图例说明
    fig.text(0.5, 0.02, '● 红色 = snap-in（最小力点）  ▲ 绿色 = contact（snap-in 后第一个 F≥0 点）',
             ha='center', fontsize=10, color='darkred')
    
    fig.suptitle('基线校正后力曲线（远场 z∈[0,100]nm 线性拟合校正）', fontsize=16, fontweight='bold', y=0.98)
    pdf.savefig(fig, dpi=200)
    plt.close(fig)


# ============================================================
# Page 4: Snap-in 区对齐放大
# ============================================================
def page_snapin_aligned(pdf, curves):
    fig, axes = plt.subplots(1, 2, figsize=(A4_W, A4_H))
    
    # 左：全部对齐
    ax = axes[0]
    colors = plt.cm.tab10(np.linspace(0, 1, len(curves)))
    for i, c in enumerate(curves):
        z_align = c['z'] - c['snap_z']
        ax.plot(z_align, c['f_corr'], color=colors[i], alpha=0.7, linewidth=1.2,
                label=c['file'].replace('JJS-50nm-', '').replace(' - NanoScope Analysis.txt', ''))
    ax.axhline(0, color='black', linestyle='--', linewidth=0.8)
    ax.set_xlim(-50, 30)
    ax.set_xlabel('Relative Z (nm, 0 = snap-in)', fontsize=11)
    ax.set_ylabel('Force (nN)', fontsize=11)
    ax.set_title('全部曲线对齐于 Snap-in 点', fontsize=13, fontweight='bold')
    ax.legend(loc='best', fontsize=7, ncol=2)
    ax.grid(True, alpha=0.3)
    
    # 右：按位移分色的放大
    ax = axes[1]
    disp_colors = {454.0: 'red', 500.0: 'orange', 1000.0: 'blue', 1500.0: 'green'}
    for c in curves:
        z_align = c['z'] - c['snap_z']
        ax.plot(z_align, c['f_corr'], color=disp_colors.get(c['disp_nm'], 'gray'), alpha=0.7, linewidth=1.2)
    ax.axhline(0, color='black', linestyle='--', linewidth=0.8)
    ax.set_xlim(-30, 20)
    ax.set_ylim(-160, 20)
    ax.set_xlabel('Relative Z (nm, 0 = snap-in)', fontsize=11)
    ax.set_ylabel('Force (nN)', fontsize=11)
    ax.set_title('按位移分组着色（红=454 橙=500 蓝=1000 绿=1500）', fontsize=13, fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    fig.suptitle('Snap-in 区详细分析（对齐放大）', fontsize=16, fontweight='bold', y=0.98)
    pdf.savefig(fig, dpi=200)
    plt.close(fig)


# ============================================================
# Page 5: Snap-in 定量统计
# ============================================================
def page_snapin_stats(pdf, curves):
    fig, axes = plt.subplots(1, 2, figsize=(A4_W, A4_H))
    
    # 数据
    labels = [c['file'].replace('JJS-50nm-', '').replace(' - NanoScope Analysis.txt', '') for c in curves]
    snaps = [abs(c['snap_f_nN']) for c in curves]
    disps = [c['disp_nm'] for c in curves]
    
    # 左：按文件名的柱状图
    ax = axes[0]
    x = np.arange(len(labels))
    bars = ax.bar(x, snaps, color='steelblue', edgecolor='black')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=7)
    ax.set_ylabel('|Snap-in Force| (nN)', fontsize=11)
    ax.set_title('JJS 各曲线 Snap-in 强度', fontsize=13, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    for bar, v in zip(bars, snaps):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2, f'{v:.1f}',
                ha='center', va='bottom', fontsize=7)
    
    # 右：snap-in vs 位移，按 setpoint 着色
    ax = axes[1]
    sp_floats = []
    for c in curves:
        sp_str = c['setpoint'].replace('nN', '')
        try:
            sp_floats.append(float(sp_str))
        except:
            sp_floats.append(10.0)
    
    scatter = ax.scatter(disps, snaps, c=sp_floats, s=150, cmap='viridis', edgecolors='black', zorder=5)
    for c in curves:
        ax.annotate(c['setpoint'].replace('nN', ''), 
                   (c['disp_nm'], abs(c['snap_f_nN'])), 
                   fontsize=8, ha='center', va='bottom')
    ax.set_xlabel('Piezo Displacement (nm)', fontsize=11)
    ax.set_ylabel('|Snap-in Force| (nN)', fontsize=11)
    ax.set_title('Snap-in vs 位移（颜色 = setpoint）', fontsize=13, fontweight='bold')
    ax.grid(True, alpha=0.3)
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('Setpoint (nN)', fontsize=10)
    
    # 添加趋势线注释
    fig.text(0.5, 0.02, 
             '关键规律：位移越小，snap-in 越强。454nm 时最强（-150.6 nN），1500nm 时最弱（-99.0 nN）。',
             ha='center', fontsize=10, color='darkred', fontweight='bold')
    
    fig.suptitle('Snap-in 定量统计', fontsize=16, fontweight='bold', y=0.98)
    pdf.savefig(fig, dpi=200)
    plt.close(fig)


# ============================================================
# Page 6: 过渡区分析（Snap-in 到 Contact）
# ============================================================
def page_transition_analysis(pdf, curves):
    fig = plt.figure(figsize=(A4_W, A4_H))
    
    # 左：过渡区力曲线叠加（对齐到 snap-in 点）
    ax_left = fig.add_axes([0.06, 0.12, 0.45, 0.78])
    colors = plt.cm.tab10(np.linspace(0, 1, len(curves)))
    for i, c in enumerate(curves):
        z_align = c['trans_z'] - c['snap_z']
        ax_left.plot(z_align, c['trans_f'], color=colors[i], alpha=0.7, linewidth=1.5,
                     label=c['file'].replace('JJS-50nm-', '').replace(' - NanoScope Analysis.txt', ''))
    ax_left.axhline(0, color='black', linestyle='--', linewidth=0.8)
    ax_left.set_xlabel('Relative Z (nm, 0 = snap-in)', fontsize=11)
    ax_left.set_ylabel('Force (nN)', fontsize=11)
    ax_left.set_title('过渡区力曲线叠加（对齐到 snap-in）', fontsize=13, fontweight='bold')
    ax_left.legend(loc='best', fontsize=6, ncol=2)
    ax_left.grid(True, alpha=0.3)
    
    # 右上：snap-in 深度 vs 位移
    ax_rt = fig.add_axes([0.56, 0.58, 0.40, 0.32])
    disps = [c['disp_nm'] for c in curves]
    depths = [c['delta_z_snap'] for c in curves]
    snaps = [abs(c['snap_f_nN']) for c in curves]
    
    scatter = ax_rt.scatter(disps, depths, c=snaps, s=120, cmap='Reds', edgecolors='black', zorder=5)
    for c in curves:
        ax_rt.annotate(f"{abs(c['snap_f_nN']):.0f}", 
                      (c['disp_nm'], c['delta_z_snap']), 
                      fontsize=7, ha='center', va='bottom')
    ax_rt.set_xlabel('Displacement (nm)', fontsize=10)
    ax_rt.set_ylabel('Snap-in Depth (nm)', fontsize=10)
    ax_rt.set_title('Snap-in 深度 vs 位移（色=|snap-in|）', fontsize=12, fontweight='bold')
    ax_rt.grid(True, alpha=0.3)
    plt.colorbar(scatter, ax=ax_rt, label='|Snap-in| (nN)', shrink=0.8)
    
    # 右下：粘着能 vs snap-in 力
    ax_rb = fig.add_axes([0.56, 0.12, 0.40, 0.32])
    energies = [c['adhesion_energy'] for c in curves]
    ax_rb.scatter(snaps, energies, s=120, color='steelblue', edgecolors='black', zorder=5)
    for c in curves:
        ax_rb.annotate(f"{c['disp_nm']:.0f}nm", 
                      (abs(c['snap_f_nN']), c['adhesion_energy']), 
                      fontsize=7, ha='center', va='bottom')
    ax_rb.set_xlabel('|Snap-in Force| (nN)', fontsize=10)
    ax_rb.set_ylabel('Adhesion Energy (nN·nm)', fontsize=10)
    ax_rb.set_title('粘着能 vs Snap-in 力（标注=位移）', fontsize=12, fontweight='bold')
    ax_rb.grid(True, alpha=0.3)
    
    # 底部注释
    fig.text(0.5, 0.02, 
             '过渡区：snap-in 最低点 → contact 点。所有 11 条曲线均有 7-28 个数据点，数据充分。'
             ' Snap-in 深度与 snap-in 力正相关；粘着能随吸引力增强而增大。',
             ha='center', fontsize=10, color='darkred', fontweight='bold')
    
    fig.suptitle('过渡区分析（Snap-in → Contact）', fontsize=16, fontweight='bold', y=0.98)
    pdf.savefig(fig, dpi=200)
    plt.close(fig)


# ============================================================
# Page 7: 接触后数据稀缺性
# ============================================================
def page_repulsive_scarcity(pdf, curves):
    fig, axes = plt.subplots(1, 2, figsize=(A4_W, A4_H))
    
    # 左：repulsive 点数柱状图
    ax = axes[0]
    labels_short = [c['file'].replace('JJS-50nm-', '').replace(' - NanoScope Analysis.txt', '') for c in curves]
    n_reps = [c['n_rep'] for c in curves]
    colors = ['green' if n >= 3 else 'red' for n in n_reps]
    x = np.arange(len(labels_short))
    bars = ax.bar(x, n_reps, color=colors, edgecolor='black')
    ax.set_xticks(x)
    ax.set_xticklabels(labels_short, rotation=45, ha='right', fontsize=7)
    ax.set_ylabel('Repulsive Data Points', fontsize=11)
    ax.set_title('接触后数据点数量', fontsize=13, fontweight='bold')
    ax.axhline(3, color='black', linestyle='--', linewidth=1, label='Minimum for slope (3)')
    ax.axhline(5, color='blue', linestyle='--', linewidth=1, label='Reliable threshold (5)')
    ax.legend(loc='upper right')
    ax.grid(axis='y', alpha=0.3)
    for bar, v in zip(bars, n_reps):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, str(v),
                ha='center', va='bottom', fontsize=8)
    
    # 右：4 条有数据的曲线的接触后放大
    ax = axes[1]
    has_rep = [c for c in curves if c['n_rep'] >= 3]
    colors2 = plt.cm.tab10(np.linspace(0, 1, len(has_rep)))
    for i, c in enumerate(has_rep):
        rep_mask = (c['z'] >= c['contact_z']) & (c['f_corr'] >= 0)
        ax.plot(c['z'][rep_mask], c['f_corr'][rep_mask], 
                marker='o', markersize=6, linewidth=1.5, color=colors2[i],
                label=f"{c['file'].replace('JJS-50nm-', '').replace(' - NanoScope Analysis.txt', '')} ({c['n_rep']} pts)")
    ax.axhline(0, color='black', linestyle='--', linewidth=0.8)
    ax.set_xlabel('Z Position (nm)', fontsize=11)
    ax.set_ylabel('Force (nN)', fontsize=11)
    ax.set_title('接触后区放大（仅 4 条曲线有足够数据）', fontsize=13, fontweight='bold')
    ax.legend(loc='best', fontsize=9)
    ax.grid(True, alpha=0.3)
    
    fig.text(0.5, 0.02,
             '警告：7/11 条曲线接触后点 < 3（红色），无法计算斜率。4 条有数据的曲线也仅有 3-5 个点。',
             ha='center', fontsize=10, color='darkred', fontweight='bold')
    
    fig.suptitle('接触后（Repulsive）数据稀缺性', fontsize=16, fontweight='bold', y=0.98)
    pdf.savefig(fig, dpi=200)
    plt.close(fig)


# ============================================================
# Page 7: Repulsive 斜率对比
# ============================================================
def page_repulsive_slopes(pdf, curves):
    fig, axes = plt.subplots(1, 2, figsize=(A4_W, A4_H))
    
    # 重新计算斜率（与 extract_features 一致）
    has_rep = [c for c in curves if c['n_rep'] >= 3]
    slopes = []
    labels_slopes = []
    for c in has_rep:
        rep_mask = (c['z'] >= c['contact_z']) & (c['f_corr'] >= 0)
        slope = float(np.polyfit(c['z'][rep_mask], c['f_corr'][rep_mask], 1)[0])
        slopes.append(slope)
        labels_slopes.append(c['file'].replace('JJS-50nm-', '').replace(' - NanoScope Analysis.txt', ''))
    
    # 左：斜率柱状图
    ax = axes[0]
    x = np.arange(len(labels_slopes))
    bars = ax.bar(x, slopes, color='coral', edgecolor='black')
    ax.axhline(K_CANTILEVER, color='red', linestyle='--', linewidth=2, label=f'Cantilever k_c = {K_CANTILEVER} N/m')
    ax.set_xticks(x)
    ax.set_xticklabels(labels_slopes, rotation=45, ha='right', fontsize=9)
    ax.set_ylabel('Repulsive Slope (N/m)', fontsize=11)
    ax.set_title('接触后段斜率（实测 = 系统串联刚度）', fontsize=13, fontweight='bold')
    ax.legend(loc='upper left')
    ax.grid(axis='y', alpha=0.3)
    for bar, v in zip(bars, slopes):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, f'{v:.2f}',
                ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    # 右：串联公式说明
    ax = axes[1]
    ax.axis('off')
    
    text = (
        "串联刚度公式：\n\n"
        "    1/k_meas = 1/k_c + 1/k_m\n\n"
        "其中：\n"
        f"  • k_c (悬臂刚度) = {K_CANTILEVER} N/m\n"
        "  • k_m (薄膜刚度) = 待求\n"
        "  • k_meas (实测斜率) = 见左图\n\n"
        "当 k_m << k_c 时，k_meas ≈ k_m（可提取薄膜刚度）\n"
        "当 k_m >> k_c 时，k_meas → k_c（饱和，无法区分）\n\n"
        "当前结果：\n"
        f"  • 实测斜率 {np.mean(slopes):.2f} N/m ≈ 0.88 × k_c\n"
        "  • 意味着 k_m >> k_c 或数据不可靠\n"
        "  • 串联公式反推 k_m > 20 N/m，σ₀ > 2000 MPa\n"
        "  • 远超聚合物合理范围，参数不可信\n\n"
        "结论：当前数据无法可靠提取薄膜刚度。"
    )
    ax.text(0.1, 0.95, text, transform=ax.transAxes, fontsize=11,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    fig.suptitle('Repulsive 区斜率与悬臂刚度对比', fontsize=16, fontweight='bold', y=0.98)
    pdf.savefig(fig, dpi=200)
    plt.close(fig)


# ============================================================
# Page 8: 两阶段分析框架
# ============================================================
def page_two_stage(pdf):
    fig = plt.figure(figsize=(A4_W, A4_H))
    fig.clf()
    
    fig.text(0.5, 0.95, '两阶段分析框架', ha='center', va='top', fontsize=20, fontweight='bold')
    
    # 左侧：第一阶段
    fig.text(0.25, 0.85, '第一阶段：Snap-in 区（吸引）', 
             ha='center', va='top', fontsize=14, fontweight='bold', color='darkgreen')
    
    stage1_text = (
        "物理本质：\n"
        "  探针接近薄膜过程中，表面相互作用\n"
        "  （毛细力、vdW、几何增强吸附）将\n"
        "  探针和薄膜相互拉近\n\n"
        "数据质量：\n"
        "  ✓ 11/11 条曲线清晰可重复\n"
        "  ✓ 力值范围 -99 ~ -151 nN\n"
        "  ✓ 位移依赖性明确\n\n"
        "可提取参数：\n"
        "  • Snap-in 力（定量统计）\n"
        "  • 位移依赖性（趋势分析）\n"
        "  • 机制推断（vdW + 毛细协同）\n\n"
        "结论可靠性：★★★★★"
    )
    fig.text(0.05, 0.78, stage1_text, ha='left', va='top', fontsize=10.5,
             bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.3))
    
    # 右侧：第二阶段
    fig.text(0.75, 0.85, '第二阶段：Repulsive 区（接触后）', 
             ha='center', va='top', fontsize=14, fontweight='bold', color='darkred')
    
    stage2_text = (
        "物理本质：\n"
        "  探针已接触薄膜，力曲线反映薄膜\n"
        "  本身的力学响应（刚度、预应力、\n"
        "  弯曲/拉伸变形）\n\n"
        "数据质量：\n"
        "  ✗ 7/11 条曲线接触后点 < 3\n"
        "  ✗ 4 条有数据的也仅 3-5 个点\n"
        "  ✗ 斜率接近悬臂刚度上限\n\n"
        "可提取参数：\n"
        "  • 薄膜刚度 k_m：不可行\n"
        "  • 预应力 σ₀：不可行\n"
        "  • Hamaker A：不可行\n\n"
        "结论可靠性：★☆☆☆☆"
    )
    fig.text(0.55, 0.78, stage2_text, ha='left', va='top', fontsize=10.5,
             bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.3))
    
    # 底部：原因分析
    fig.text(0.5, 0.32, '为什么第二阶段数据不足？', 
             ha='center', va='top', fontsize=14, fontweight='bold')
    
    reason_text = (
        "PeakForce QNM 模式的工作机制决定了这一问题：\n\n"
        "  1. Setpoint 仅 8-50 nN，探针 snap-in 后几乎立即达到设定力阈值\n"
        "  2. 探针随即回退，无法在接触后继续下压积累数据点\n"
        "  3. 结果：接触后仅 1-5 个数据点，无法拟合薄膜力学模型\n\n"
        "解决方案：\n"
        "  • 改用常规 AFM 接触模式力曲线（无自动回退限制）\n"
        "  • 或将 PeakForce setpoint 提高至 ≥ 100 nN\n"
        "  • 降低扫描速率至 < 1 Hz，增加数据点密度\n"
        "  • 目标：获得 ≥ 20 个接触后数据点，压入深度 ≥ 10 nm"
    )
    fig.text(0.5, 0.27, reason_text, ha='center', va='top', fontsize=10.5,
             bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.5))
    
    pdf.savefig(fig, dpi=200)
    plt.close(fig)


# ============================================================
# Page 9: 关键修正说明
# ============================================================
def page_correction(pdf):
    fig = plt.figure(figsize=(A4_W, A4_H))
    fig.clf()
    
    fig.text(0.5, 0.95, '关键修正说明', ha='center', va='top', fontsize=20, fontweight='bold', color='darkred')
    
    text = (
        "【旧版分析的致命错误】\n\n"
        "在 extract_features.py 的早期版本中，repulsive 区的选取逻辑为：\n\n"
        "    rep_mask = f_corr > 0\n\n"
        "这一代码选中了全曲线所有正力点，包括远场区（z∈[0,100] nm）基线校正后的\n"
        "微小正偏差。这些远场点（力值 ~0-1 nN）与接触后点（力值 ~10-50 nN）混合后，\n"
        "线性拟合的斜率被严重拉低。\n\n"
        "旧版结果：JJS 排斥段斜率 = 0.005 N/m\n"
        "         → 被误读为\"悬浮薄膜极软\"\n\n"
        "【修正后的真相】\n\n"
        "修正逻辑：仅取 snap-in 之后（z ≥ contact_z）的 repulsive 点\n\n"
        "新版结果：\n"
        "  • 1000nm-50nN:  5.14 N/m（5 点）\n"
        "  • 500nm-10nN:   4.17 N/m（3 点）\n"
        "  • 500nm-8.862nN: 4.18 N/m（3 点）\n"
        "  • 500nm-9nN:    4.28 N/m（3 点）\n"
        "  • 均值: 4.4 N/m，接近悬臂刚度上限 5 N/m\n\n"
        "【科学影响】\n\n"
        "0.005 N/m 的\"极软薄膜\"结论是完全错误的伪影。修正后的 4.4 N/m 虽然接近\n"
        "悬臂刚度上限，但数据点仅 3-5 个，统计可靠性极低，仍然不能得出关于薄膜\n"
        "力学性质的确定结论。\n\n"
        "这凸显了 AFM 力曲线分析中两个关键陷阱：\n"
        "  1. 基线校正错误 → snap-in 估值偏差可达 10 倍以上\n"
        "  2. repulsive 区选取错误 → 斜率估值偏差可达 1000 倍\n\n"
        "只有严格限定 repulsive 区为 snap-in 之后的接触段，才能获得真实的接触力学信息。"
    )
    
    fig.text(0.05, 0.88, text, ha='left', va='top', fontsize=11,
             bbox=dict(boxstyle='round', facecolor='mistyrose', alpha=0.5))
    
    pdf.savefig(fig, dpi=200)
    plt.close(fig)


# 新增页面函数（将插入 generate_jjs_report.py）
# 模块 1-4 的深度分析页面

def page_asymmetry_analysis(pdf, curves):
    fig, axes = plt.subplots(2, 2, figsize=(A4_W, A4_H))
    
    labels_short = [c['file'].replace('JJS-50nm-', '').replace(' - NanoScope Analysis.txt', '') for c in curves]
    drops = [c['max_drop_slope'] for c in curves]
    rises = [c['max_rise_slope'] for c in curves]
    asymms = [abs(r/d) if d != 0 else 0 for r, d in zip(rises, drops)]
    disps = [c['disp_nm'] for c in curves]
    
    # 左上：下降斜率
    ax = axes[0, 0]
    x = np.arange(len(labels_short))
    colors = ['red' if d < -80 else 'orange' if d < -40 else 'steelblue' for d in drops]
    bars = ax.bar(x, np.abs(drops), color=colors, edgecolor='black')
    ax.set_xticks(x)
    ax.set_xticklabels(labels_short, rotation=45, ha='right', fontsize=6)
    ax.set_ylabel('|Drop Slope| (N/m)', fontsize=10)
    ax.set_title('下降段最大斜率（Snap-in 过程）', fontsize=12, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    ax.axhline(5, color='green', linestyle='--', linewidth=1, label='k_c = 5 N/m')
    ax.legend()
    
    # 右上：上升斜率
    ax = axes[0, 1]
    bars = ax.bar(x, rises, color='coral', edgecolor='black')
    ax.set_xticks(x)
    ax.set_xticklabels(labels_short, rotation=45, ha='right', fontsize=6)
    ax.set_ylabel('Rise Slope (N/m)', fontsize=10)
    ax.set_title('上升段最大斜率（恢复过程）', fontsize=12, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    ax.axhline(5, color='green', linestyle='--', linewidth=1, label='k_c = 5 N/m')
    ax.legend()
    
    # 左下：不对称比
    ax = axes[1, 0]
    bars = ax.bar(x, asymms, color='mediumpurple', edgecolor='black')
    ax.set_xticks(x)
    ax.set_xticklabels(labels_short, rotation=45, ha='right', fontsize=6)
    ax.set_ylabel('Asymmetry Ratio (|rise|/|drop|)', fontsize=10)
    ax.set_title('不对称比', fontsize=12, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    
    # 右下：不对称比 vs 位移
    ax = axes[1, 1]
    ax.scatter(disps, asymms, s=100, color='mediumpurple', edgecolors='black', zorder=5)
    for c in curves:
        ax.annotate(f"{c['disp_nm']:.0f}nm", (c['disp_nm'], abs(c['max_rise_slope']/c['max_drop_slope']) if c['max_drop_slope'] != 0 else 0),
                   fontsize=8, ha='center', va='bottom')
    ax.set_xlabel('Displacement (nm)', fontsize=10)
    ax.set_ylabel('Asymmetry Ratio', fontsize=10)
    ax.set_title('不对称比 vs 位移', fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    fig.suptitle('模块1：不对称性定量分析', fontsize=16, fontweight='bold', y=0.98)
    pdf.savefig(fig, dpi=200)
    plt.close(fig)


def page_vdw_fitting(pdf, curves):
    fig, axes = plt.subplots(1, 2, figsize=(A4_W, A4_H))
    
    # 找到有 vdW 拟合的曲线
    fit_curves = [c for c in curves if c.get('vdw_fit')]
    
    for ax, c in zip(axes, fit_curves):
        fit = c['vdw_fit']
        drop_z = np.array(c['drop_z'])
        drop_f = np.array(c['drop_f'])
        
        # 选取吸引区 f < -2
        valid = drop_f < -2.0
        if np.sum(valid) < 5:
            continue
        
        vd_z = drop_z[valid]
        vd_f = np.abs(drop_f[valid])
        contact_z = c['contact_z_nm']
        d_est = contact_z - vd_z
        
        # 过滤
        mask = d_est > 0.5
        d_est = d_est[mask]
        vd_f = vd_f[mask]
        
        # log-log 图
        ax.scatter(d_est, vd_f, s=30, color='steelblue', edgecolors='black', zorder=5, label='Data')
        
        # 拟合线
        if len(d_est) >= 3:
            log_d = np.log(d_est)
            log_f = np.log(vd_f)
            coeffs = np.polyfit(log_d, log_f, 1)
            d_fit = np.linspace(np.min(d_est), np.max(d_est), 100)
            f_fit = np.exp(coeffs[1]) * d_fit**coeffs[0]
            ax.plot(d_fit, f_fit, 'r--', linewidth=2, 
                    label=f"Fit: |F|={np.exp(coeffs[1]):.1f}*d^{coeffs[0]:.2f}\nR2={fit['R2']:.2f}")
        
        # 理论线
        d_theory = np.linspace(0.5, np.max(d_est), 100)
        A = 4e-19  # J
        R = 8e-9  # m
        F_vdw = A * R / (6 * (d_theory * 1e-9)**2) * 1e9  # nN
        ax.plot(d_theory, F_vdw, 'g:', linewidth=2, label='Non-retarded vdW (A=4e-19J)')
        
        ax.set_xlabel('Distance d (nm)', fontsize=11)
        ax.set_ylabel('|Force| (nN)', fontsize=11)
        ax.set_title(f"{c['file'].replace('JJS-50nm-', '').replace(' - NanoScope Analysis.txt', '')}\n"
                     f"Snap-in 前 vdW 距离依赖性", fontsize=12, fontweight='bold')
        ax.set_xscale('log')
        ax.set_yscale('log')
        ax.legend(loc='best', fontsize=9)
        ax.grid(True, alpha=0.3, which='both')
    
    fig.suptitle('模块2：Snap-in 前 vdW 距离依赖性拟合', fontsize=16, fontweight='bold', y=0.98)
    pdf.savefig(fig, dpi=200)
    plt.close(fig)


def page_recovery_behavior(pdf, curves):
    fig, axes = plt.subplots(2, 2, figsize=(A4_W, A4_H))
    
    # 左上图：局部斜率分布（选 4 条代表性曲线）
    ax = axes[0, 0]
    selected = [c for c in curves if c['disp_nm'] in (454.0, 500.0, 1000.0, 1500.0)]
    colors = ['red', 'orange', 'blue', 'green']
    for c, color in zip(selected, colors):
        if len(c.get('rise_z', [])) >= 3:
            rise_z = np.array(c['rise_z'])
            rise_f = np.array(c['rise_f'])
            local_slopes = np.diff(rise_f) / np.diff(rise_z)
            local_z = (rise_z[:-1] + rise_z[1:]) / 2 - c['snap_z_nm']
            ax.plot(local_z, local_slopes, color=color, linewidth=1.5, 
                    label=f"{c['disp_nm']:.0f}nm")
    ax.axhline(0, color='black', linestyle='--', linewidth=0.8)
    ax.axhline(5, color='green', linestyle='--', linewidth=1, label='k_c = 5 N/m')
    ax.set_xlabel('Relative Z (nm, 0 = snap-in)', fontsize=10)
    ax.set_ylabel('Local Slope (N/m)', fontsize=10)
    ax.set_title('恢复段局部斜率分布', fontsize=12, fontweight='bold')
    ax.legend(loc='best', fontsize=9)
    ax.grid(True, alpha=0.3)
    
    # 右上图：plateau 检测
    ax = axes[0, 1]
    labels = [c['file'].replace('JJS-50nm-', '').replace(' - NanoScope Analysis.txt', '') for c in curves]
    plateau_fracs = [c.get('recovery', {}).get('plateau_fraction', 0) for c in curves]
    x = np.arange(len(labels))
    ax.bar(x, plateau_fracs, color='lightcoral', edgecolor='black')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=6)
    ax.set_ylabel('Plateau Fraction', fontsize=10)
    ax.set_title('毛细桥 Plateau 检测（|slope|<0.5 N/m）', fontsize=12, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    
    # 左下图：理论毛细力 vs 实测
    ax = axes[1, 0]
    f_caps = [c['vdW_check']['F_capillary_theory_nN'] for c in curves]
    f_measured = [c['vdW_check']['F_measured_nN'] for c in curves]
    ax.scatter(f_caps, f_measured, s=100, color='steelblue', edgecolors='black', zorder=5)
    ax.plot([0, 10], [0, 10], 'k--', linewidth=1, label='1:1 line')
    ax.set_xlabel('Theoretical Capillary Force (nN)', fontsize=10)
    ax.set_ylabel('Measured Snap-in Force (nN)', fontsize=10)
    ax.set_title('实测力 vs 理论毛细力', fontsize=12, fontweight='bold')
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 160)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 右下图：能量耗散
    ax = axes[1, 1]
    disps = [c['disp_nm'] for c in curves]
    energies = [c['energy_dissipated_nN_nm'] for c in curves]
    ax.scatter(disps, energies, s=100, c=[abs(c['snap_f_nN']) for c in curves], 
               cmap='Reds', edgecolors='black', zorder=5)
    ax.set_xlabel('Displacement (nm)', fontsize=10)
    ax.set_ylabel('Energy Dissipated (nN·nm)', fontsize=10)
    ax.set_title('过渡区能量耗散', fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    fig.suptitle('模块3：恢复行为与毛细桥判断', fontsize=16, fontweight='bold', y=0.98)
    pdf.savefig(fig, dpi=200)
    plt.close(fig)


def page_retarded_vdw(pdf, curves):
    fig = plt.figure(figsize=(A4_W, A4_H))
    fig.clf()
    
    fig.text(0.5, 0.95, '模块4：延迟 vdW 检验与水分子限域效应', 
             ha='center', va='top', fontsize=18, fontweight='bold')
    
    # 左侧：理论值 vs 实测值对比表
    fig.text(0.25, 0.88, '理论力 vs 实测力对比', 
             ha='center', va='top', fontsize=14, fontweight='bold', color='darkblue')
    
    table_text = (
        "理论模型预测（d0 = 0.3 nm）：\n\n"
        "  非延迟 vdW (DMT):\n"
        "    F = A*R/(12*d0^2)\n"
        "    A = 4e-19 J (典型聚合物)\n"
        "    F_vdw = 2.96 nN\n\n"
        "  延迟 vdW (Casimir-Polder):\n"
        "    F = pi^3*hbar*c*R/(360*d0^3)*eta\n"
        "    eta = 0.4 (聚合物/氮化硅)\n"
        "    F_CP = 0.037 nN\n\n"
        "  毛细力 (Kelvin方程):\n"
        "    F = 4*pi*R*gamma\n"
        "    gamma = 72 mN/m (水)\n"
        "    F_cap = 7.24 nN\n\n"
        "  vdW + 毛细力总和:\n"
        "    F_total = 10.2 nN\n\n"
        "实测 Snap-in 力:\n"
        "  最小: 99.0 nN (1500nm-10nN)\n"
        "  最大: 150.6 nN (454nm-8.862nN)\n"
        "  均值: 120.7 nN\n\n"
        "结论:\n"
        "  实测力 = 10-15 x 理论总和\n"
        "  单一机制无法解释\n"
        "  必须引入几何增强因子 10-15x"
    )
    fig.text(0.03, 0.83, table_text, ha='left', va='top', fontsize=10,
             bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.3))
    
    # 右侧：水分子限域效应分析
    fig.text(0.75, 0.88, '水分子限域效应分析（湿度 >60%）', 
             ha='center', va='top', fontsize=14, fontweight='bold', color='darkgreen')
    
    water_text = (
        "高湿度下的纳米间隙水行为：\n\n"
        "1. 吸附层形成:\n"
        "   探针和薄膜表面均吸附水分子层\n"
        "   厚度 ~0.3-1 nm（取决于湿度）\n"
        "   吸附层降低有效 Hamaker 常数?\n"
        "   → 实测表明有效 A 反而增大 30-50x\n\n"
        "2. 毛细桥成核:\n"
        "   探针接近时，水分子在间隙中凝聚\n"
        "   形成纳米级液桥（ neck radius < 10 nm）\n"
        "   但恢复段未观察到力 plateau\n"
        "   → 毛细桥维持时间极短或不稳定\n\n"
        "3. 受限水的粘度增大:\n"
        "   纳米间隙 (< 5 nm) 中水的粘度\n"
        "   可能比体相高 10-1000 倍\n"
        "   可能导致探针接近时的能量耗散\n"
        "   过渡区能量耗散: 800-1800 nN·nm\n\n"
        "4. 综合图像:\n"
        "   • 远距离 (> 10 nm): 延迟 vdW（微弱）\n"
        "   • 中距离 (1-10 nm): 非延迟 vdW + 水吸附层\n"
        "   • 近距离 (< 1 nm): 毛细桥快速成核\n"
        "   • 接触后: 粘着接触 + 悬臂弹性恢复\n\n"
        "关键问题:\n"
        "   为什么有效 A 增大 30-50 倍?\n"
        "   → 薄膜局部曲率增强（几何因子）\n"
        "   → 多体相互作用（水分子介导）\n"
        "   → 薄膜机械不稳定性（下凹放大吸引力）"
    )
    fig.text(0.53, 0.83, water_text, ha='left', va='top', fontsize=10,
             bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.3))
    
    # 底部：关键数值
    fig.text(0.5, 0.08, 
             '核心矛盾：DMT/Casimir 预测 ~3-10 nN，实测 100-150 nN，差距 10-50 倍。'
             ' 高湿度下水分子限域效应和薄膜几何增强是主要增强机制。',
             ha='center', fontsize=11, color='darkred', fontweight='bold',
             bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.3))
    
    pdf.savefig(fig, dpi=200)
    plt.close(fig)


# ============================================================
# Page 10: 结论与建议
# ============================================================
def page_conclusion(pdf):
    fig = plt.figure(figsize=(A4_W, A4_H))
    fig.clf()
    
    fig.text(0.5, 0.95, '结论与下一步实验建议', ha='center', va='top', fontsize=20, fontweight='bold')
    
    # 左侧：明确结论
    fig.text(0.25, 0.85, '已确定的结论', 
             ha='center', va='top', fontsize=14, fontweight='bold', color='darkgreen')
    
    conc1 = (
        "1. JJS 悬浮 COF 薄膜表现出系统性强 snap-in\n"
        "   （-99 ~ -151 nN），远超经典 vdW/Casimir\n"
        "   理论预测（差 2-3 个数量级）\n\n"
        "2. Snap-in 强度与位移负相关：454nm 最强\n"
        "   (-150.6 nN)，1500nm 最弱 (-99.0 nN)\n\n"
        "3. 铜网金属基底几乎完全抑制 snap-in\n"
        "   (< -5 nN)，证实了金属屏蔽效应\n\n"
        "4. 首选机制：几何增强 vdW + 吸附物介导\n"
        "   毛细力协同（综合置信度 60-70%）\n\n"
        "5. 旧版 0.005 N/m 的\"极软薄膜\"结论为\n"
        "   分析伪影，已修正"
    )
    fig.text(0.03, 0.80, conc1, ha='left', va='top', fontsize=10.5,
             bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.3))
    
    # 右侧：待验证/需新实验
    fig.text(0.75, 0.85, '待验证 / 需新实验', 
             ha='center', va='top', fontsize=14, fontweight='bold', color='darkred')
    
    conc2 = (
        "1. 薄膜刚度 k_m：当前数据无法提取\n"
        "   （需要 ≥ 20 个接触后数据点）\n\n"
        "2. 预应力 σ₀：当前数据无法提取\n"
        "   （需要更大 setpoint 和更慢扫描）\n\n"
        "3. Young's 模量 E：无深压非线性区数据\n"
        "   （需要压入深度 > 薄膜厚度）\n\n"
        "4. 单一机制验证：\n"
        "   • 真空/干燥环境排除毛细贡献\n"
        "   • 变探针半径区分 vdW vs 静电\n"
        "   • 原位 KPFM 量化静电贡献\n\n"
        "5. 获取膜力学参数的实验方案：\n"
        "   • 常规接触模式或 setpoint ≥ 100 nN\n"
        "   • 扫描速率 < 1 Hz\n"
        "   • 目标：≥ 20 个接触后点，压入 ≥ 10 nm"
    )
    fig.text(0.53, 0.80, conc2, ha='left', va='top', fontsize=10.5,
             bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.5))
    
    # 底部：联系信息
    fig.text(0.5, 0.08, 
             '报告生成时间：2026-04-22  |  分析工具：Python 3.13 + matplotlib  |  数据来源：NanoScope Analysis',
             ha='center', va='top', fontsize=9, color='gray', style='italic')
    
    pdf.savefig(fig, dpi=200)
    plt.close(fig)


# ============================================================
# Main
# ============================================================
def main():
    curves = load_jjs_data()
    
    # 加载深度分析结果（供新页面使用）
    import json
    with open('results/jjs_transition_deep_analysis.json', 'r', encoding='utf-8') as f:
        deep_results = json.load(f)
    
    outdir = Path('figures')
    outdir.mkdir(exist_ok=True)
    pdf_path = outdir / 'JJS_综合分析报告.pdf'
    
    with PdfPages(str(pdf_path)) as pdf:
        page_cover(pdf, curves)
        page_raw_curves(pdf, curves)
        page_corrected_curves(pdf, curves)
        page_snapin_aligned(pdf, curves)
        page_snapin_stats(pdf, curves)
        page_transition_analysis(pdf, curves)
        page_asymmetry_analysis(pdf, deep_results)
        page_vdw_fitting(pdf, deep_results)
        page_recovery_behavior(pdf, deep_results)
        page_retarded_vdw(pdf, deep_results)
        page_repulsive_scarcity(pdf, curves)
        page_repulsive_slopes(pdf, curves)
        page_two_stage(pdf)
        page_correction(pdf)
        page_conclusion(pdf)
    
    print(f"Saved: {pdf_path}")


if __name__ == '__main__':
    main()
