# %%
"""
linker1-paa & linker2-paa (20260415数据集) 力学分析
=====================================================
用户指定文件：
  linker1: 100nN-500nm + 所有 linker1-paa-*.spm 文件
  linker2: 1500nm-2(重点), 2000nm-2, 2000nm, 2500nm-2, 2500nm

探针: RTESPA-150, k_lever = 5 N/m, R = 8 nm
模型: F = k1*D + k3*D^3 (点载荷二维薄膜大变形)
"""

import sys
sys.path.insert(0, "/Users/kejunliu/Desktop/Research_Data/AFM/JJS_project/scripts")

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from scipy.optimize import curve_fit

from cleaning import load_raw, correct_baseline, segment_curve

# %%
# ── 配置 ──────────────────────────────────────────────────────────
DATASET_DIR = Path("/Users/kejunliu/Desktop/Research_Data/AFM/JJS_project/20260415原始数据")
RESULTS_DIR = Path("/Users/kejunliu/Desktop/Research_Data/AFM/JJS_project/results")
REPORTS_DIR = Path("/Users/kejunliu/Desktop/Research_Data/AFM/JJS_project/reports")

K_LEVER = 7.0           # N/m, RTESPA-150 标称刚度
PROBE_RADIUS_NM = 8.0   # nm
FILM_THICKNESS_NM = 50  # nm

# 用户指定的文件
TARGET_FILES = {
    'linker1': [
        'linker1-paa-100nN-500nm.spm - NanoScope Analysis.txt',
        'linker1-paa-500nm.spm - NanoScope Analysis.txt',
        'linker1-paa-500nm-2.spm - NanoScope Analysis.txt',
        'linker1-paa-1000nm.spm - NanoScope Analysis.txt',
        'linker1-paa-1000nm-2.spm - NanoScope Analysis.txt',
    ],
    'linker2': [
        'linker2-paa-.1500nm-2.spm - NanoScope Analysis.txt',
        'linker2-paa-.2000nm-2.spm - NanoScope Analysis.txt',
        'linker2-paa-.2000nm.spm - NanoScope Analysis.txt',
        'linker2-paa-.2500nm-2.spm - NanoScope Analysis.txt',
        'linker2-paa-.2500nm.spm - NanoScope Analysis.txt',
    ]
}

# %%
# ── 核心函数 ──────────────────────────────────────────────────────

def find_stable_contact(z, f, seg, min_consecutive=3):
    """找 snap 后 F 连续 >= 0 的起始点"""
    snap_z = seg['snap_z']
    post_snap = z >= snap_z
    z_post = z[post_snap]
    f_post = f[post_snap]
    
    for i in range(len(f_post) - min_consecutive + 1):
        if np.all(f_post[i:i+min_consecutive] >= 0):
            return z_post[i], f_post[i]
    
    # fallback
    positive = f_post >= 0
    if np.any(positive):
        idx = np.where(positive)[0][0]
        return z_post[idx], f_post[idx]
    return None, None


def model_f_d(D, k1, k3):
    """F = k1 * D + k3 * D^3"""
    return k1 * D + k3 * D**3


def analyze_single(fpath, material):
    """分析单个文件"""
    result = {
        'filename': Path(fpath).name,
        'material': material,
        'status': 'OK',
        'n_points': 0,
        'max_D_nm': np.nan,
        'max_F_nN': np.nan,
        'k1_N_m': np.nan,
        'k3_N_m3': np.nan,
        'sigma_0_MPa': np.nan,
        'E_2D_N_m': np.nan,
        'R_squared': np.nan,
        'k3_reliable': False,
    }
    
    try:
        rc = load_raw(fpath)
        z, f = rc['z'], rc['f']
        
        # Baseline
        baseline = correct_baseline(z, f)
        if baseline[0] is None:
            result['status'] = 'Baseline fail'
            return result, None, None
        f_corr = baseline[0]
        
        # Segment
        seg = segment_curve(z, f_corr)
        
        # Find contact
        z_cp, f_cp = find_stable_contact(z, f_corr, seg)
        if z_cp is None:
            result['status'] = 'No positive force'
            return result, None, None
        
        # Post-contact data
        post = z >= z_cp
        z_post = z[post]
        f_post = f_corr[post]
        
        # Only F >= 0
        valid = f_post >= 0
        if sum(valid) < 3:
            result['status'] = f'Only {sum(valid)} positive points'
            return result, None, None
        
        z_fit = z_post[valid]
        f_fit = f_post[valid]
        
        # Compute indentation depth D = (Z - Z_cp) - F/k_lever
        # F[nN] / k[N/m] = F/k [nm]  (since 1 nN / 1 N/m = 1e-9/1 = 1e-9 m = 1 nm)
        D = (z_fit - z_cp) - f_fit / K_LEVER
        
        result['n_points'] = len(D)
        result['max_D_nm'] = float(max(D))
        result['max_F_nN'] = float(max(f_fit))
        
        # Fit strategy based on number of points
        if len(D) >= 8:
            # Nonlinear fit with bounds
            try:
                # Initial guess
                k1_init = max(np.polyfit(D[:min(5,len(D))], f_fit[:min(5,len(D))], 1)[0], 0.001)
                popt, _ = curve_fit(model_f_d, D, f_fit, p0=[k1_init, 1e-10],
                                    bounds=([0, 0], [np.inf, np.inf]), maxfev=10000)
                k1, k3 = popt
                result['k3_reliable'] = True
            except Exception as e:
                # Fallback to linear
                k1 = np.polyfit(D, f_fit, 1)[0]
                k3 = 0.0
                result['k3_reliable'] = False
                result['status'] = f'Nonlinear fit failed, linear only'
        else:
            # Linear fit only
            k1 = np.polyfit(D, f_fit, 1)[0]
            k3 = 0.0
            result['k3_reliable'] = False
            result['status'] = f'Linear only ({len(D)} pts)'
        
        # Compute predictions
        f_pred = model_f_d(D, k1, k3)
        ss_res = np.sum((f_fit - f_pred)**2)
        ss_tot = np.sum((f_fit - np.mean(f_fit))**2)
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0
        
        result['k1_N_m'] = float(k1)
        result['k3_N_m3'] = float(k3)
        result['sigma_0_MPa'] = float(k1 / np.pi / (FILM_THICKNESS_NM * 1e-9) / 1e6)
        result['E_2D_N_m'] = float(k3 * PROBE_RADIUS_NM**2)
        result['R_squared'] = float(r2)
        
        return result, D, f_fit
        
    except Exception as e:
        result['status'] = f'Error: {str(e)[:40]}'
        return result, None, None


# %%
# ── 批量分析 ──────────────────────────────────────────────────────

print("=" * 70)
print("linker1-paa & linker2-paa (20260415) 力学分析")
print(f"k_lever = {K_LEVER} N/m, R = {PROBE_RADIUS_NM} nm")
print("=" * 70)

all_results = []
fit_data = {}

for material, fnames in TARGET_FILES.items():
    print(f"\n--- {material} ---")
    for fname in fnames:
        fpath = DATASET_DIR / fname
        print(f"\n{fname}")
        result, D, f_fit = analyze_single(str(fpath), material)
        all_results.append(result)
        fit_data[fname] = (D, f_fit, result)
        
        print(f"  Status: {result['status']}, n={result['n_points']}, max_D={result['max_D_nm']:.0f}nm")
        print(f"  k1={result['k1_N_m']:.4f} N/m, k3={result['k3_N_m3']:.2e} N/m³, R²={result['R_squared']:.3f}")
        print(f"  σ₀={result['sigma_0_MPa']:.2f} MPa, E₂D={result['E_2D_N_m']:.4f} N/m")

# %%
# ── 保存 CSV ──────────────────────────────────────────────────────

df = pd.DataFrame(all_results)
csv_path = RESULTS_DIR / "summary_mechanics_v2.csv"
df.to_csv(csv_path, index=False)
print(f"\n\nSaved CSV: {csv_path}")
print(f"\nSummary by material:")
for mat in ['linker1', 'linker2']:
    sub = df[df['material'] == mat]
    passed = sub[sub['status'].isin(['OK', 'Linear only (3 pts)', 'Linear only (4 pts)', 
                                      'Linear only (6 pts)', 'Linear only (8 pts)',
                                      'Linear only (9 pts)', 'Linear only (13 pts)',
                                      'Linear only (15 pts)'])]
    print(f"\n{mat}: {len(passed)}/{len(sub)} files analyzed")
    if len(passed) > 0:
        print(f"  σ₀ = {passed['sigma_0_MPa'].mean():.2f} ± {passed['sigma_0_MPa'].std():.2f} MPa")
        if any(passed['k3_reliable']):
            e2d = passed[passed['k3_reliable']]['E_2D_N_m']
            print(f"  E₂D = {e2d.mean():.4f} ± {e2d.std():.4f} N/m (n={len(e2d)})")

# %%
# ── 高精度拟合图 ──────────────────────────────────────────────────

def plot_fit(fname, D, f_fit, result, highlight=False):
    """为单个文件绘制拟合图"""
    if D is None or len(D) < 3:
        return
    
    k1 = result['k1_N_m']
    k3 = result['k3_N_m3']
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # F vs D
    ax = axes[0]
    ax.scatter(D, f_fit, s=30, alpha=0.7, c='blue', edgecolors='black', linewidth=0.5, zorder=3)
    
    # Prediction curve
    D_smooth = np.linspace(0, max(D), 300)
    f_pred = model_f_d(D_smooth, k1, k3)
    ax.plot(D_smooth, f_pred, 'r-', lw=2.5, label=f'Fit: $F = k_1 D + k_3 D^3$')
    
    # Components
    ax.plot(D_smooth, k1 * D_smooth, 'g--', lw=1.5, alpha=0.7, label=f'Linear: $k_1 D$ ({k1:.3f} N/m)')
    if result['k3_reliable']:
        ax.plot(D_smooth, k3 * D_smooth**3, 'm--', lw=1.5, alpha=0.7, label=f'Cubic: $k_3 D^3$')
    
    ax.set_xlabel('Indentation Depth $D$ (nm)', fontsize=13)
    ax.set_ylabel('Force $F$ (nN)', fontsize=13)
    title = f"{result['material']} - {fname[:40]}...\n"
    title += f"$k_1$={k1:.3f} N/m, $k_3$={k3:.2e} N/m³, $R^2$={result['R_squared']:.3f}"
    if not result['k3_reliable']:
        title += "\n(k₃ not reliable - linear fit only)"
    ax.set_title(title, fontsize=11)
    ax.legend(loc='upper left', fontsize=10)
    ax.grid(True, alpha=0.3)
    
    # F/D vs D^2 (linearized)
    ax = axes[1]
    with np.errstate(divide='ignore', invalid='ignore'):
        f_over_d = f_fit / D
    d2 = D**2
    ax.scatter(d2, f_over_d, s=30, alpha=0.7, c='blue', edgecolors='black', linewidth=0.5, zorder=3)
    
    if len(d2) > 2 and result['k3_reliable']:
        coeffs = np.polyfit(d2, f_over_d, 1)
        d2_smooth = np.linspace(0, max(d2), 100)
        ax.plot(d2_smooth, np.polyval(coeffs, d2_smooth), 'r-', lw=2.5,
                label=f'Slope={coeffs[0]:.2e}, Int={coeffs[1]:.3f}')
        ax.set_title(f"Linearized: $F/D = k_1 + k_3 D^2$", fontsize=13)
    else:
        ax.set_title(f"Linearized: $F/D$ vs $D^2$ (insufficient data)", fontsize=13)
    
    ax.set_xlabel('$D^2$ (nm²)', fontsize=13)
    ax.set_ylabel('$F/D$ (N/m)', fontsize=13)
    ax.legend(loc='upper right', fontsize=10)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    prefix = "HIGHLIGHT_" if highlight else ""
    pdf_path = REPORTS_DIR / f"{prefix}{result['material']}_{Path(fname).stem[:30]}_fit.pdf"
    png_path = REPORTS_DIR / f"{prefix}{result['material']}_{Path(fname).stem[:30]}_fit.png"
    plt.savefig(pdf_path, dpi=300, bbox_inches='tight')
    plt.savefig(png_path, dpi=300, bbox_inches='tight')
    plt.show()
    print(f"Saved: {pdf_path}")

# Plot all linker1 files
for fname in TARGET_FILES['linker1']:
    D, f_fit, result = fit_data[fname]
    plot_fit(fname, D, f_fit, result)

# Plot all linker2 files (highlight 1500nm-2)
for fname in TARGET_FILES['linker2']:
    D, f_fit, result = fit_data[fname]
    highlight = '1500nm-2' in fname
    plot_fit(fname, D, f_fit, result, highlight=highlight)

# %%
# ── 汇总对比图 ────────────────────────────────────────────────────

def plot_summary(df):
    df_ok = df[df['R_squared'].notna()]
    if len(df_ok) == 0:
        return
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    colors = {'linker1': '#1f77b4', 'linker2': '#ff7f0e'}
    
    # σ_0
    ax = axes[0, 0]
    for mat in ['linker1', 'linker2']:
        sub = df_ok[df_ok['material'] == mat]['sigma_0_MPa'].dropna()
        if len(sub) > 0:
            ax.scatter([mat]*len(sub), sub, s=100, c=colors[mat], alpha=0.7, edgecolors='black', linewidth=1)
    ax.set_ylabel('Pre-stress $\\sigma_0$ (MPa)', fontsize=12)
    ax.set_title('Pre-stress Comparison', fontsize=13)
    ax.grid(True, alpha=0.3, axis='y')
    
    # E_2D (only reliable k3)
    ax = axes[0, 1]
    for mat in ['linker1', 'linker2']:
        sub = df_ok[(df_ok['material'] == mat) & (df_ok['k3_reliable'] == True)]
        if len(sub) > 0:
            ax.scatter([mat]*len(sub), sub['E_2D_N_m'], s=100, c=colors[mat], alpha=0.7, edgecolors='black', linewidth=1)
    ax.set_ylabel("2D Young Modulus E_2D (N/m)", fontsize=12)
    ax.set_title('E₂D (k₃ reliable only)', fontsize=13)
    ax.grid(True, alpha=0.3, axis='y')
    
    # k1 vs max_D
    ax = axes[1, 0]
    for mat in ['linker1', 'linker2']:
        sub = df_ok[df_ok['material'] == mat]
        ax.scatter(sub['max_D_nm'], sub['k1_N_m'], s=100, c=colors[mat], alpha=0.7, 
                   edgecolors='black', linewidth=1, label=mat)
    ax.set_xlabel('Max Indentation Depth (nm)', fontsize=12)
    ax.set_ylabel('$k_1$ (N/m)', fontsize=12)
    ax.set_title('Linear Stiffness vs Max Depth', fontsize=13)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Representative F-D curves
    ax = axes[1, 1]
    for mat in ['linker1', 'linker2']:
        # Pick file with most points
        sub = df_ok[df_ok['material'] == mat]
        if len(sub) == 0:
            continue
        best = sub.loc[sub['n_points'].idxmax()]
        fname = best['filename']
        D, f_fit, _ = fit_data[fname]
        if D is not None:
            ax.plot(D, f_fit, 'o-', markersize=4, alpha=0.7, c=colors[mat], 
                   label=f"{mat} ({best['n_points']} pts, D_max={best['max_D_nm']:.0f}nm)")
    ax.set_xlabel('Indentation Depth $D$ (nm)', fontsize=12)
    ax.set_ylabel('Force $F$ (nN)', fontsize=12)
    ax.set_title('Representative F-D Curves', fontsize=13)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    pdf_path = REPORTS_DIR / "linker_paa_v2_summary.pdf"
    png_path = REPORTS_DIR / "linker_paa_v2_summary.png"
    plt.savefig(pdf_path, dpi=300, bbox_inches='tight')
    plt.savefig(png_path, dpi=300, bbox_inches='tight')
    plt.show()
    print(f"Saved: {pdf_path}")

plot_summary(df)

# %%
print("\n" + "=" * 70)
print("分析完成！")
print("=" * 70)
