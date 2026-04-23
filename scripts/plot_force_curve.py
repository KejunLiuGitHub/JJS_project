# -*- coding: utf-8 -*-
"""
力曲线绘图脚本
优先使用 matplotlib；如果未安装，则输出 ASCII/文本图表到终端
"""

import sys
from pathlib import Path
from parser import AFMForceCurve, load_all_curves

# 尝试导入 matplotlib
HAS_MPL = False
try:
    import matplotlib
    matplotlib.use('Agg')  # 无头后端
    import matplotlib.pyplot as plt
    HAS_MPL = True
except ImportError:
    pass


def plot_single(curve, outdir=None, show_text=True):
    """绘制单条力曲线"""
    if outdir is None:
        script_dir = Path(__file__).parent
        project_root = script_dir.parent
        outdir = project_root / 'figures'
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    
    # 清理文件名作为输出名
    safe_name = curve.filename.replace('.txt', '.png').replace(' ', '_')
    outpath = outdir / safe_name
    
    # 统一转换为 nN
    force_nN = curve.to_si_units()
    z = curve.z
    
    if HAS_MPL:
        fig, ax = plt.subplots(figsize=(6, 5))
        ax.plot(z, force_nN, 'b-', linewidth=1.2)
        
        # 标注 snap-in
        if curve.min_force is not None and curve.min_force < -5:
            snap_idx = curve.snap_in_index
            ax.plot(z[snap_idx], force_nN[snap_idx], 'ro', markersize=6, label=f"Snap-in: {curve.min_force:.1f} nN")
            ax.legend()
        
        ax.axhline(0, color='k', linewidth=0.5)
        ax.set_xlabel('Z Position (nm)')
        ax.set_ylabel('Force (nN)')
        ax.set_title(f"{curve.filename}\n{curve.probe_model} | {curve.piezo_displacement}nm | Setpoint {curve.setpoint_force}{curve.setpoint_unit}")
        ax.invert_xaxis()  # AFM 惯例：探针向下为右到左
        fig.tight_layout()
        fig.savefig(outpath, dpi=150)
        plt.close(fig)
        print(f"[已绘图] {outpath}")
    else:
        # ASCII 简易图
        print(f"\n{'='*60}")
        print(f"{curve.filename}")
        print(f"Probe: {curve.probe_model} | Disp: {curve.piezo_displacement}nm")
        print(f"Force range: {min(force_nN):.2f} ~ {max(force_nN):.2f} nN (SI)")
        print(f"Data points: {len(z)}")
        _ascii_plot(z, force_nN)


def _ascii_plot(x, y, width=60, height=12):
    """简易 ASCII 折线图"""
    if not x or not y:
        return
    x_min, x_max = min(x), max(x)
    y_min, y_max = min(y), max(y)
    if y_max == y_min:
        y_max += 1
    
    grid = [[' ' for _ in range(width)] for _ in range(height)]
    
    for xi, yi in zip(x, y):
        ix = int((xi - x_min) / (x_max - x_min) * (width - 1))
        iy = int((yi - y_min) / (y_max - y_min) * (height - 1))
        iy = height - 1 - iy  # 翻转 Y
        grid[iy][ix] = '*'
    
    # 画零线
    if y_min <= 0 <= y_max:
        zero_y = height - 1 - int((0 - y_min) / (y_max - y_min) * (height - 1))
        for i in range(width):
            if grid[zero_y][i] == ' ':
                grid[zero_y][i] = '-'
    
    for row in grid:
        print(''.join(row))
    print(f"{x_min:.1f}{' '* (width-20)} {x_max:.1f}")


def plot_all(curves, outdir=None, limit=None):
    """批量绘图"""
    items = list(curves.items())
    if limit:
        items = items[:limit]
    for rel, c in items:
        plot_single(c, outdir)
    
    if HAS_MPL:
        outdir_path = outdir if outdir is not None else Path(__file__).parent.parent / 'figures'
        print(f"\n所有图片已保存到 {Path(outdir_path).resolve()}")
    else:
        print("\n提示: 安装 matplotlib 可生成高质量 PNG 图片。")
        print("  pip install matplotlib")


if __name__ == '__main__':
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    curves = load_all_curves(project_root)
    # 默认绘制前 10 条，避免终端被 ASCII 图淹没
    plot_all(curves, limit=10)
