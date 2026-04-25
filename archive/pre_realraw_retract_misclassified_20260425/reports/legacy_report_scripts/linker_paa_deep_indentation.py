# %%
"""
linker1-paa & linker2-paa 深压入 AFM 力学分析
============================================
目标：从深压入数据中提取二维杨氏模量 E_2D 和预应力 σ_0

物理模型：点载荷下二维薄膜大变形
  F = k1 * D + k3 * D^3
  k1 ≈ π · σ_0      → σ_0 = k1 / π
  k3 ≈ E_2D / R²    → E_2D = k3 · R²

参数：
  k_lever = 80 N/m      (DDESP-V2 标称刚度)
  R = 8 nm              (探针尖端半径)
  t = 50 nm             (膜厚)
  D = (Z - Z_cp) - F/k_lever   (真实压深)

QC 规则：
  1. 无 snap-in（无负力区）→ 丢弃
  2. post-contact 正力区 < 5 点 → 丢弃
  3. 滑移/破裂：F>0 区有断崖式下降 → 丢弃

输出：
  results/summary_mechanics.csv
  reports/linker1_paa_best_fit.pdf
  reports/linker2_paa_best_fit.pdf
  reports/linker_paa_comparison.pdf
"""

import sys
sys.path.insert(0, "/Users/kejunliu/Desktop/Research_Data/AFM/JJS_project/scripts")

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from glob import glob
from scipy.optimize import curve_fit

from cleaning import load_raw, correct_baseline, segment_curve

# %%
# ── 配置 ──────────────────────────────────────────────────────────
DATASET_DIR = Path("/Users/kejunliu/Desktop/Research_Data/AFM/JJS_project/20260416原始数据")
RESULTS_DIR = Path("/Users/kejunliu/Desktop/Research_Data/AFM/JJS_project/results")
REPORTS_DIR = Path("/Users/kejunliu/Desktop/Research_Data/AFM/JJS_project/reports")

K_LEVER = 89.0          # N/m, DDESP-V2 标称刚度
PROBE_RADIUS_NM = 100.0   # nm
FILM_THICKNESS_NM = 50  # nm

# QC 阈值
MIN_POSITIVE_POINTS = 5     # post-contact F>=0 最少点数
MIN_MAX_FORCE_NN = 2.0      # nN, 全局最大力至少 2 nN（确保有接触）
SLIP_THRESHOLD_NN_PER_NM = -0.05  # nN/nm, F>0 区 dF/dZ 小于此值视为滑移

# 拟合约束
MIN_FIT_POINTS = 5
MAX_INITIAL_D_NM = 500.0    # nm, 初始线性区最大压深（用于 k1 初估）

# %%
# ── 核心函数 ──────────────────────────────────────────────────────

def find_contact_point(z, f, seg, min_consecutive=3):
    """
    在 snap 之后找到 F 稳定为正的接触点 Z_cp。
    策略：找 snap 后 F 连续 >= 0 至少 min_consecutive 个点的起始位置。
    这避免了 contact 初期的力值振荡。
    """
    snap_z = seg['snap_z']
    post_snap = z >= snap_z
    z_post = z[post_snap]
    f_post = f[post_snap]
    
    # 找到连续 F >= 0 的区域
    positive = f_post >= 0
    if not np.any(positive):
        return None, None
    
    # 找连续正力的起始点
    for i in range(len(f_post) - min_consecutive + 1):
        if np.all(f_post[i:i+min_consecutive] >= 0):
            z_cp = z_post[i]
            f_cp = f_post[i]
            return z_cp, f_cp
    
    # 如果没有连续正力，取第一个正力点作为 fallback
    first_pos_idx = np.where(positive)[0][0]
    return z_post[first_pos_idx], f_post[first_pos_idx]


def detect_slip(z, f, z_cp):
    """
    检测 F > 0 区域是否有严重断崖式下降（破裂/脱接触）。
    只对力值 > 100 nN 的区域检测，避免噪声干扰。
    返回 True 如果力值在短距离内下降超过 80%。
    """
    post = z >= z_cp
    z_post = z[post]
    f_post = f[post]
    
    # 只考虑 F > 100 nN 的区域（避免噪声）
    pos = f_post > 100
    if sum(pos) < 3:
        return False
    
    z_pos = z_post[pos]
    f_pos = f_post[pos]
    
    df = np.diff(f_pos)
    dz = np.diff(z_pos)
    if len(dz) == 0:
        return False
    
    # 检测断崖：单次下降超过当前力值的 80%
    for i in range(len(df)):
        rel_drop = -df[i] / f_pos[i]
        if rel_drop > 0.8 and dz[i] < 200:
            return True
    
    return False


def compute_indentation_depth(z, f, z_cp):
    """
    计算真实压深 D = (Z - Z_cp) - F/k_lever
    单位：nm
    """
    post = z >= z_cp
    z_post = z[post]
    f_post = f[post]
    
    # D = Z - Z_cp - F/k_lever
    # F 单位 nN = 1e-9 N, k_lever 单位 N/m
    # F/k_lever 单位 m = (nN * 1e-9) / (N/m) = 1e-9 * m/N * N/m = m
    # 转换为 nm: * 1e9
    # 所以 F(nN) / k_lever(N/m) * 1e9 = F / k_lever * 1e0 = F/k_lever (nm when F in nN and k in N/m?)
    # 验证: 2000 nN / 80 N/m = 2000e-9 / 80 = 25e-9 m = 25 nm
    # 所以 F(nN) / k(N/m) = 2000/80 = 25，单位确实是 nm！
    D = (z_post - z_cp) - f_post / K_LEVER
    
    return D, z_post, f_post


def model_f_d(D, k1, k3):
    """F = k1 * D + k3 * D^3"""
    return k1 * D + k3 * D**3


def fit_mechanics(D, F):
    """
    对 (D, F) 数据进行非线性拟合 F = k1*D + k3*D^3
    返回 k1, k3, r_squared, popt, pcov
    """
    if len(D) < MIN_FIT_POINTS:
        return None, None, None, None, None
    
    # 只使用 D >= 0 的点（物理压深）
    valid = D >= 0
    if sum(valid) < MIN_FIT_POINTS:
        return None, None, None, None, None
    
    Dv = D[valid]
    Fv = F[valid]
    
    try:
        # 初值估计
        # 小变形区：F ≈ k1 * D
        small = Dv <= min(MAX_INITIAL_D_NM, 0.2 * max(Dv))
        if sum(small) >= 3:
            k1_init = np.polyfit(Dv[small], Fv[small], 1)[0]
        else:
            k1_init = Fv[0] / Dv[0] if Dv[0] > 0 else 0.01
        
        # k3 初值：从整个数据估计
        k3_init = 1e-15  # 很小的初始值
        
        popt, pcov = curve_fit(
            model_f_d, Dv, Fv,
            p0=[max(k1_init, 0.001), k3_init],
            bounds=([0, 0], [np.inf, np.inf]),
            maxfev=10000
        )
        
        k1, k3 = popt
        F_pred = model_f_d(Dv, k1, k3)
        ss_res = np.sum((Fv - F_pred)**2)
        ss_tot = np.sum((Fv - np.mean(Fv))**2)
        r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0
        
        return k1, k3, r_squared, popt, pcov
    except Exception as e:
        print(f"  Fit failed: {e}")
        return None, None, None, None, None


# %%
# ── 主分析流程 ────────────────────────────────────────────────────

def analyze_file(fpath, material):
    """分析单个文件，返回结果字典"""
    result = {
        'filename': Path(fpath).name,
        'material': material,
        'k1_N_m': np.nan,
        'k3_N_m3': np.nan,
        'sigma_0_MPa': np.nan,
        'E_2D_N_m': np.nan,
        'R_squared': np.nan,
        'QC_Status': 'Unknown',
        'max_D_nm': np.nan,
        'max_F_nN': np.nan,
        'n_fit_points': 0,
        'snap_depth_nm': np.nan,
    }
    
    try:
        rc = load_raw(fpath)
        z, f = rc['z'], rc['f']
        
        # 全局最大力检查（QC-1：无接触）
        f_max = np.max(f)
        f_min = np.min(f)
        result['max_F_nN'] = f_max
        
        if f_max < MIN_MAX_FORCE_NN:
            result['QC_Status'] = 'Discard-1: No contact'
            return result, None, None, None
        
        # Baseline correction
        baseline_result = correct_baseline(z, f)
        if baseline_result[0] is None:
            result['QC_Status'] = 'Discard: Baseline fail'
            return result, None, None, None
        
        f_corr = baseline_result[0]
        
        # Segment curve
        seg = segment_curve(z, f_corr)
        snap_z = seg['snap_z']
        snap_f = seg['snap_f']
        result['snap_depth_nm'] = abs(snap_f) / K_LEVER  # 近似 snap depth
        
        # 找到接触点
        z_cp, f_cp = find_contact_point(z, f_corr, seg)
        if z_cp is None:
            result['QC_Status'] = 'Discard: No positive force region'
            return result, None, None, None
        
        # 计算压深
        D, z_post, f_post = compute_indentation_depth(z, f_corr, z_cp)
        
        # 只保留 D >= 0 且 F >= 0 的点用于拟合
        valid = (D >= 0) & (f_post >= 0)
        n_valid = sum(valid)
        result['n_fit_points'] = n_valid
        
        if n_valid < MIN_POSITIVE_POINTS:
            result['QC_Status'] = f'Discard-3: Only {n_valid} positive points'
            return result, D, f_post, z_post
        
        # 滑移检测（QC-2）
        if detect_slip(z, f_corr, z_cp):
            result['QC_Status'] = 'Discard-2: Slip or rupture detected'
            return result, D, f_post, z_post
        
        # 拟合
        D_fit = D[valid]
        F_fit = f_post[valid]
        result['max_D_nm'] = max(D_fit)
        
        k1, k3, r2, popt, pcov = fit_mechanics(D_fit, F_fit)
        
        if k1 is None:
            result['QC_Status'] = 'Discard: Fit failed'
            return result, D, f_post, z_post
        
        # 计算物理参数
        sigma_0 = k1 / np.pi  # Pa (N/m²)，因为 k1 单位 N/m，D 单位 m？
        # 等等，D 的单位是 nm，F 的单位是 nN
        # F = k1 * D + k3 * D^3
        # nN = k1 * nm + k3 * nm^3
        # 所以 k1 单位 = nN/nm = N/m （因为 1 nN/nm = 1e-9 N / 1e-9 m = 1 N/m）
        # k3 单位 = nN/nm^3 = N/m^3 （因为 1e-9 / 1e-27 = 1e18... 不对）
        
        # 仔细计算：
        # F [nN] = k1 [?] * D [nm] + k3 [?] * D [nm]^3
        # 1 nN = 1e-9 N, 1 nm = 1e-9 m
        # F [N] = F[nN] * 1e-9 = k1 * D[nm] * 1e-9 + k3 * D[nm]^3 * 1e-27
        # 所以 k1 的单位 = N/m （当 D 用 m，F 用 N 时）
        # 但 F[nN] = k1 * D[nm] 意味着 k1 = nN/nm = (1e-9 N)/(1e-9 m) = N/m
        # k3 = nN/nm^3 = (1e-9 N)/(1e-27 m^3) = 1e18 N/m^3
        
        # 所以 k1 已经是 N/m！
        # σ_0 = k1 / π [N/m] = [N/m] / [无量纲] = N/m = J/m²
        # 但预应力应该是 Pa = N/m²
        # 问题：k1 的单位到底是什么？
        
        # 从量纲分析：
        # 二维薄膜的点载荷模型：
        # F = (2πσ_0) * δ   (小变形，中心挠度 δ)
        # 或 F = πσ_0 * D  (不同几何定义)
        # 这里 σ_0 是预应力 [N/m]（薄膜张力，单位长度上的力）
        # 所以 k1 = π * σ_0 [N/m] → σ_0 = k1/π [N/m]
        
        # 如果要转换成 MPa（三维应力），需要除以膜厚：
        # σ_0_3D = σ_0 / t [N/m / m = N/m² = Pa]
        
        # E_2D = k3 * R²
        # k3 [nN/nm^3] = [N/m^3] * 1e18? 
        # 不，nN/nm^3 = 1e-9 N / 1e-27 m^3 = 1e18 N/m^3
        # R [nm] = 8 nm = 8e-9 m
        # R² [nm²] = 64 nm² = 64e-18 m² = 6.4e-17 m²
        # E_2D = k3 [nN/nm^3] * R² [nm²] = k3 * R² [nN/nm]
        # 1 nN/nm = 1e-9 N / 1e-9 m = 1 N/m
        # 所以 E_2D 单位 = N/m
        
        # 三维杨氏模量 E_3D = E_2D / t [N/m / m = N/m² = Pa]
        
        sigma_0_N_m = k1 / np.pi  # N/m (二维预应力/张力)
        E_2D = k3 * (PROBE_RADIUS_NM ** 2)  # N/m (二维杨氏模量)
        
        result['k1_N_m'] = k1
        result['k3_N_m3'] = k3
        result['sigma_0_MPa'] = sigma_0_N_m / (FILM_THICKNESS_NM * 1e-9) / 1e6  # MPa
        result['E_2D_N_m'] = E_2D
        result['R_squared'] = r2
        result['QC_Status'] = 'Pass'
        
        return result, D, f_post, z_post
        
    except Exception as e:
        result['QC_Status'] = f'Error: {str(e)[:50]}'
        return result, None, None, None


# %%
# ── 批量处理 ──────────────────────────────────────────────────────

print("=" * 70)
print("linker1-paa & linker2-paa 深压入力学分析")
print("=" * 70)
print(f"k_lever = {K_LEVER} N/m, R = {PROBE_RADIUS_NM} nm, t = {FILM_THICKNESS_NM} nm")
print()

all_results = []
fit_data = {}  # 存储拟合数据用于作图

# linker1-paa
print("--- linker1-paa ---")
linker1_files = sorted(glob(str(DATASET_DIR / "k80-linker1-paa-*.txt")))
for fpath in linker1_files:
    print(f"\nProcessing: {Path(fpath).name}")
    result, D, f_post, z_post = analyze_file(fpath, 'linker1')
    all_results.append(result)
    fit_data[result['filename']] = (D, f_post, z_post, result)
    print(f"  QC: {result['QC_Status']}, max_D={result['max_D_nm']:.0f} nm, "
          f"max_F={result['max_F_nN']:.1f} nN")
    if result['QC_Status'] == 'Pass':
        print(f"  k1={result['k1_N_m']:.4f} N/m, k3={result['k3_N_m3']:.2e} N/m³, "
              f"R²={result['R_squared']:.3f}")
        print(f"  σ₀={result['sigma_0_MPa']:.2f} MPa, E_2D={result['E_2D_N_m']:.2f} N/m")

# linker2-paa
print("\n--- linker2-paa ---")
linker2_files = sorted(glob(str(DATASET_DIR / "k80-linker2-paa-*.txt")))
for fpath in linker2_files:
    print(f"\nProcessing: {Path(fpath).name}")
    result, D, f_post, z_post = analyze_file(fpath, 'linker2')
    all_results.append(result)
    fit_data[result['filename']] = (D, f_post, z_post, result)
    print(f"  QC: {result['QC_Status']}, max_D={result['max_D_nm']:.0f} nm, "
          f"max_F={result['max_F_nN']:.1f} nN")
    if result['QC_Status'] == 'Pass':
        print(f"  k1={result['k1_N_m']:.4f} N/m, k3={result['k3_N_m3']:.2e} N/m³, "
              f"R²={result['R_squared']:.3f}")
        print(f"  σ₀={result['sigma_0_MPa']:.2f} MPa, E_2D={result['E_2D_N_m']:.2f} N/m")

# %%
# ── 保存 CSV ──────────────────────────────────────────────────────

df = pd.DataFrame(all_results)
csv_path = RESULTS_DIR / "summary_mechanics.csv"
df.to_csv(csv_path, index=False)
print(f"\n\nSaved: {csv_path}")
print(f"Total files: {len(df)}")
print(f"Passed QC: {sum(df['QC_Status'] == 'Pass')}")
print(f"\nQC breakdown:")
print(df['QC_Status'].value_counts())

# %%
# ── 汇总统计 ──────────────────────────────────────────────────────

print("\n" + "=" * 70)
print("通过 QC 的统计结果")
print("=" * 70)

for material in ['linker1', 'linker2']:
    sub = df[(df['material'] == material) & (df['QC_Status'] == 'Pass')]
    if len(sub) == 0:
        print(f"\n{material}: No data passed QC")
        continue
    
    print(f"\n{material} (n={len(sub)}):")
    print(f"  σ₀ (MPa):  {sub['sigma_0_MPa'].mean():.2f} ± {sub['sigma_0_MPa'].std():.2f}")
    print(f"  E_2D (N/m): {sub['E_2D_N_m'].mean():.2f} ± {sub['E_2D_N_m'].std():.2f}")
    print(f"  k1 (N/m):   {sub['k1_N_m'].mean():.4f} ± {sub['k1_N_m'].std():.4f}")
    print(f"  k3 (N/m³):  {sub['k3_N_m3'].mean():.2e} ± {sub['k3_N_m3'].std():.2e}")
    print(f"  R²:         {sub['R_squared'].mean():.3f} ± {sub['R_squared'].std():.3f}")
    print(f"  Max D (nm): {sub['max_D_nm'].mean():.0f} ± {sub['max_D_nm'].std():.0f}")

# %%
# ── 最佳拟合曲线图 ────────────────────────────────────────────────

def plot_best_fit(material, fit_data, all_results):
    """为每个材料绘制最佳拟合曲线"""
    # 找到 R² 最高的通过 QC 的曲线
    sub = [r for r in all_results if r['material'] == material and r['QC_Status'] == 'Pass']
    if not sub:
        print(f"No {material} data passed QC for plotting")
        return
    
    best = max(sub, key=lambda x: x['R_squared'])
    fname = best['filename']
    D, f_post, z_post, _ = fit_data[fname]
    
    if D is None:
        return
    
    # 重新拟合以获取预测曲线
    valid = (D >= 0) & (f_post >= 0)
    D_fit = D[valid]
    F_fit = f_post[valid]
    
    k1 = best['k1_N_m']
    k3 = best['k3_N_m3']
    
    # 生成平滑预测曲线
    D_smooth = np.linspace(0, max(D_fit), 500)
    F_pred = model_f_d(D_smooth, k1, k3)
    F_linear = k1 * D_smooth
    F_cubic = k3 * D_smooth**3
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # 左图：F vs D
    ax = axes[0]
    ax.scatter(D_fit, F_fit, s=20, alpha=0.6, c='blue', label='Data (F≥0, D≥0)')
    ax.plot(D_smooth, F_pred, 'r-', lw=2, label=f'Fit: $F = k_1 D + k_3 D^3$')
    ax.plot(D_smooth, F_linear, 'g--', lw=1.5, alpha=0.7, label=f'Linear: $k_1 D$')
    ax.plot(D_smooth, F_cubic, 'm--', lw=1.5, alpha=0.7, label=f'Cubic: $k_3 D^3$')
    ax.set_xlabel('Indentation Depth D (nm)', fontsize=12)
    ax.set_ylabel('Force F (nN)', fontsize=12)
    ax.set_title(f'{material} - Best Fit (R² = {best["R_squared"]:.3f})\n{fname[:50]}...')
    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.3)
    
    # 右图：F/D vs D²（用于验证线性关系）
    ax = axes[1]
    # F/D = k1 + k3 * D^2
    with np.errstate(divide='ignore', invalid='ignore'):
        F_over_D = F_fit / D_fit
    D2 = D_fit**2
    ax.scatter(D2, F_over_D, s=20, alpha=0.6, c='blue')
    # 拟合直线
    if len(D2) > 2:
        coeffs = np.polyfit(D2, F_over_D, 1)
        D2_smooth = np.linspace(0, max(D2), 100)
        ax.plot(D2_smooth, np.polyval(coeffs, D2_smooth), 'r-', lw=2,
                label=f'Slope = {coeffs[0]:.2e}, Intercept = {coeffs[1]:.4f}')
    ax.set_xlabel('$D^2$ (nm²)', fontsize=12)
    ax.set_ylabel('F/D (N/m)', fontsize=12)
    ax.set_title(f'{material} - Linearized: $F/D = k_1 + k_3 D^2$')
    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    pdf_path = REPORTS_DIR / f"{material}_paa_best_fit.pdf"
    plt.savefig(pdf_path, dpi=300, bbox_inches='tight')
    plt.savefig(str(pdf_path).replace('.pdf', '.png'), dpi=300, bbox_inches='tight')
    plt.show()
    print(f"Saved: {pdf_path}")

plot_best_fit('linker1', fit_data, all_results)
plot_best_fit('linker2', fit_data, all_results)

# %%
# ── 对比分布图 ────────────────────────────────────────────────────

def plot_comparison(df):
    """绘制 linker1 vs linker2 的对比图"""
    df_pass = df[df['QC_Status'] == 'Pass']
    
    if len(df_pass) == 0:
        print("No data passed QC for comparison plot")
        return
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    materials = ['linker1', 'linker2']
    colors = {'linker1': '#1f77b4', 'linker2': '#ff7f0e'}
    
    # E_2D
    ax = axes[0, 0]
    data_to_plot = [df_pass[df_pass['material'] == m]['E_2D_N_m'].dropna() for m in materials]
    bp = ax.boxplot(data_to_plot, labels=materials, patch_artist=True)
    for patch, mat in zip(bp['boxes'], materials):
        patch.set_facecolor(colors[mat])
    ax.set_ylabel('E₂D (N/m)', fontsize=12)
    ax.set_title('2D Young\'s Modulus', fontsize=13)
    ax.grid(True, alpha=0.3, axis='y')
    
    # σ_0
    ax = axes[0, 1]
    data_to_plot = [df_pass[df_pass['material'] == m]['sigma_0_MPa'].dropna() for m in materials]
    bp = ax.boxplot(data_to_plot, labels=materials, patch_artist=True)
    for patch, mat in zip(bp['boxes'], materials):
        patch.set_facecolor(colors[mat])
    ax.set_ylabel('σ₀ (MPa)', fontsize=12)
    ax.set_title('Pre-stress', fontsize=13)
    ax.grid(True, alpha=0.3, axis='y')
    
    # F-D 代表性曲线
    ax = axes[1, 0]
    for material in materials:
        sub = df_pass[df_pass['material'] == material]
        if len(sub) == 0:
            continue
        # 找最大压深的曲线
        best = sub.loc[sub['max_D_nm'].idxmax()]
        fname = best['filename']
        D, f_post, z_post, _ = fit_data[fname]
        if D is not None:
            valid = (D >= 0) & (f_post >= 0)
            ax.scatter(D[valid], f_post[valid], s=15, alpha=0.5, 
                      c=colors[material], label=f'{material} (D_max={best["max_D_nm"]:.0f} nm)')
    ax.set_xlabel('Indentation Depth D (nm)', fontsize=12)
    ax.set_ylabel('Force F (nN)', fontsize=12)
    ax.set_title('Representative F-D Curves', fontsize=13)
    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.3)
    
    # k1 vs k3 散点图
    ax = axes[1, 1]
    for material in materials:
        sub = df_pass[df_pass['material'] == material]
        ax.scatter(sub['k1_N_m'], sub['k3_N_m3'], s=80, alpha=0.7,
                  c=colors[material], label=material, edgecolors='black', linewidth=0.5)
    ax.set_xlabel('k₁ (N/m)', fontsize=12)
    ax.set_ylabel('k₃ (N/m³)', fontsize=12)
    ax.set_title('k₁ vs k₃', fontsize=13)
    ax.set_yscale('log')
    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    pdf_path = REPORTS_DIR / "linker_paa_comparison.pdf"
    plt.savefig(pdf_path, dpi=300, bbox_inches='tight')
    plt.savefig(str(pdf_path).replace('.pdf', '.png'), dpi=300, bbox_inches='tight')
    plt.show()
    print(f"Saved: {pdf_path}")

plot_comparison(df)

# %%
print("\n" + "=" * 70)
print("分析完成！")
print("=" * 70)
