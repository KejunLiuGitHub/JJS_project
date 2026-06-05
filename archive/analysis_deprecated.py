# %% [markdown]
# # AFM 力曲线分析 — 1μm 方孔 COF 悬浮薄膜
#
# **数据**: 210 条 Bruker PeakForce QNM 力曲线，8 种表面活性剂 × 3 种 linker，
# 1 μm 方孔 SiN 基底，探针 DDESP-V2 (k ≈ 87.3 N/m, R ≈ 100 nm)。
#
# 首次运行解析所有文件 + 计算 → 存缓存。之后再跑直接读缓存，秒出结果。
# `python analysis.py --force` 强制重算。

# %% Imports & cache setup
import sys, pickle
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from scipy.optimize import curve_fit

sys.path.insert(0, str(Path(__file__).parent))
from bruker_parser import parse_bruker_force_curve

# Parse --force
FORCE = "--force" in sys.argv

plt.rcParams.update({
    'figure.dpi': 100, 'savefig.dpi': 150,
    'font.size': 10, 'axes.titlesize': 11,
    'pdf.fonttype': 42,
})
COLORS = ['#0C5DA5', '#E8204E', '#00B945', '#FF9500', '#845B97', '#474747', '#00BCD4', '#FF5722']

# Cache paths
CACHE_DIR = Path(__file__).parent / "results"
CACHE_DIR.mkdir(exist_ok=True)
CURVES_PKL = CACHE_DIR / "curves.pkl"
FEATURES_CSV = CACHE_DIR / "features.csv"
MECHANICS_CSV = CACHE_DIR / "contact_mechanics.csv"
FIG_DIR = CACHE_DIR / "figures"
FIG_DIR.mkdir(exist_ok=True)

print("Imports ready. Cache:", "FORCE" if FORCE else "enabled")

# %% [markdown]
# ## 1. 数据加载（带缓存）

# %% Load data (cached)
DATA_DIR = Path("/Users/kejunliu/Desktop/Research_Data/AFM/1umSquare/data_1um/one micrometer/extend")

def load_or_parse():
    if not FORCE and CURVES_PKL.exists():
        print(f"Loading cached parses: {CURVES_PKL}")
        with open(CURVES_PKL, 'rb') as f:
            return pickle.load(f)

    print(f"Parsing {len(list(DATA_DIR.iterdir()))} files...")
    curves, errors = [], []
    for fp in sorted(DATA_DIR.iterdir()):
        try:
            curves.append(parse_bruker_force_curve(str(fp)))
        except Exception as e:
            errors.append((fp.name, str(e)))
    print(f"  Parsed: {len(curves)}, Errors: {len(errors)}")

    with open(CURVES_PKL, 'wb') as f:
        pickle.dump(curves, f)
    print(f"  Cached → {CURVES_PKL}")
    return curves

all_curves = load_or_parse()

# %% [markdown]
# ## 2. 特征提取

# %% Feature extraction
def extract_features(curve):
    f, z, fr = curve['force_nn'], curve['z_nm'], curve['force_retract_nn']
    snap_idx = np.argmin(f)
    snap_f, snap_z = f[snap_idx], z[snap_idx]

    pull_idx = np.argmin(fr)
    name = curve['filename']
    parts = name.split('-')
    return {
        'filename': name,
        'surfactant': parts[0] if len(parts) > 0 else '?',
        'linker': parts[1] if len(parts) > 1 else '?',
        'snap_f_nn': snap_f, 'snap_z_nm': snap_z,
        'pulloff_f_nn': fr[pull_idx],
        'max_force_nn': np.max(f),
        'adhesion_hysteresis_nn': abs(fr[pull_idx]) - abs(snap_f) if snap_f < 0 else abs(fr[pull_idx]),
    }

features = [extract_features(c) for c in all_curves]
df = pd.DataFrame(features)

print(f"Curves: {len(df)}")
print(f"Snap-in median: {df['snap_f_nn'].median():.1f} nN")
print(f"Pull-off median: {df['pulloff_f_nn'].median():.1f} nN")
print(f"Linkers: {sorted(df['linker'].unique())}")

# %% [markdown]
# **数据概览**:
# - Snap-in ~ -2577 nN — 远超典型 vdW (~10-100 nN for R=8nm)，力标定待确认
# - Pull-off ~ -239 nN — 极均匀，不随 surfactant/linker 变化
# - 粘附滞后 ~ 2200-2500 nN，由 snap-in 主导

# %% [markdown]
# ## 3. 分组 Pivot 表

# %% Pivot tables
print(f"Groups:\n{df.groupby(['surfactant','linker']).size().to_string()}\n")

for col, label in [('snap_f_nn', 'Snap-in'), ('pulloff_f_nn', 'Pull-off'), ('adhesion_hysteresis_nn', 'Hysteresis')]:
    print(f"=== {label} (nN) ===")
    print(df.pivot_table(values=col, index='surfactant', columns='linker', aggfunc='median').to_string(), "\n")

# %% [markdown]
# **关键发现**:
# - Snap-in: SDBS 最大 (-2758 nN)，PFPE 最小 (-2448 nN)
# - Pull-off: 所有组几乎无差异（-223 ~ -239 nN）→ 探针-水膜界面属性
# - 滞后由 snap-in 贡献，pull-off 恒定

# %% [markdown]
# ## 4. 分组箱线图

# %% Group boxplots → save
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

surf_order = df.groupby('surfactant')['snap_f_nn'].median().sort_values().index

# Snap-in by surfactant
bp = axes[0,0].boxplot([df[df['surfactant']==s]['snap_f_nn'] for s in surf_order],
                        tick_labels=surf_order, patch_artist=True)
for p in bp['boxes']: p.set_facecolor('#0C5DA5'); p.set_alpha(0.6)
axes[0,0].set_title('Snap-in by Surfactant'); axes[0,0].set_ylabel('nN')
axes[0,0].tick_params(axis='x', rotation=45); axes[0,0].axhline(0, color='gray', ls='--', alpha=0.5)

# Snap-in by linker
for i, lnk in enumerate(sorted(df['linker'].unique())):
    d = df[df['linker']==lnk]['snap_f_nn']
    axes[0,1].boxplot([d], positions=[i], tick_labels=[lnk], patch_artist=True,
                       boxprops=dict(facecolor=COLORS[i], alpha=0.6))
axes[0,1].set_title('Snap-in by Linker'); axes[0,1].set_ylabel('nN')

# Pull-off by surfactant
bp3 = axes[1,0].boxplot([df[df['surfactant']==s]['pulloff_f_nn'] for s in surf_order],
                         tick_labels=surf_order, patch_artist=True)
for p in bp3['boxes']: p.set_facecolor('#E8204E'); p.set_alpha(0.6)
axes[1,0].set_title('Pull-off by Surfactant'); axes[1,0].set_ylabel('nN')
axes[1,0].tick_params(axis='x', rotation=45)

# Snap-in vs Pull-off scatter
for si, srf in enumerate(surf_order):
    sub = df[df['surfactant']==srf]
    axes[1,1].scatter(sub['snap_f_nn'], sub['pulloff_f_nn'], label=srf, alpha=0.6, s=20)
axes[1,1].set_xlabel('Snap-in (nN)'); axes[1,1].set_ylabel('Pull-off (nN)')
axes[1,1].set_title('Snap-in vs Pull-off'); axes[1,1].legend(fontsize=7, ncol=2)
axes[1,1].axhline(0, color='gray', ls='--', alpha=0.5); axes[1,1].axvline(0, color='gray', ls='--', alpha=0.5)

plt.tight_layout()
plt.savefig(FIG_DIR / "group_boxplots.png"); plt.savefig(FIG_DIR / "group_boxplots.pdf")
plt.show()

# %% [markdown]
# ## 5. 代表曲线

# %% Representative curves → save
fig, axes = plt.subplots(3, 3, figsize=(15, 12))
for si, srf in enumerate(sorted(df['surfactant'].unique())[:8]):
    ax = axes.flat[si]
    for fj, fn in enumerate(df[df['surfactant']==srf]['filename'].values[:3]):
        cv = [c for c in all_curves if c['filename']==fn][0]
        ax.plot(cv['z_nm'], cv['force_nn'], color=COLORS[fj], alpha=0.5, lw=0.8)
        ax.plot(cv['z_nm_retract'], cv['force_retract_nn'], color=COLORS[fj], alpha=0.3, lw=0.5, ls='--')
    ax.set_title(srf, fontsize=9); ax.set_xlabel('Z (nm)'); ax.set_xlim(0, 200)
    ax.axhline(0, color='gray', ls=':', alpha=0.5)
axes.flat[8].set_visible(False)
plt.suptitle('Representative Curves: Approach (solid) + Withdraw (dashed)', fontsize=12)
plt.tight_layout()
plt.savefig(FIG_DIR / "representative_curves.png"); plt.savefig(FIG_DIR / "representative_curves.pdf")
plt.show()

# %% [markdown]
# ## 6. 接触力学分析（带缓存）
#
# 模型: 周边固支圆膜 $F = k_1\delta + k_3\delta^3$
# $E_{app} = k_3 a^2 / (q^3 t)$，其中 $q = 1/(1.05-0.15\nu-0.16\nu^2)$

# %% Contact mechanics (cached)
PORE_RADIUS_UM, FILM_THICKNESS_NM, NU = 0.5, 50.0, 0.30

def q_factor(nu=NU):
    return 1.0 / (1.05 - 0.15*nu - 0.16*nu**2)

def membrane_model(delta, k1, k3):
    return k1*delta + k3*delta**3

def E_app_mpa(k3):
    if k3 <= 0 or np.isnan(k3): return np.nan
    return (k3*1e18 * (PORE_RADIUS_UM*1e-6)**2 / (q_factor()**3 * FILM_THICKNESS_NM*1e-9)) / 1e6

def analyze_contact(curve):
    f, z, fr = curve['force_nn'], curve['z_nm'], curve['force_retract_nn']
    snap_idx = np.argmin(f)
    snap_f, snap_z = f[snap_idx], z[snap_idx]

    post = slice(snap_idx, None)
    delta = snap_z - z[post]  # Z↓ during approach → δ = snap_z - z
    f_post = f[post]

    if len(delta) < 8 or delta.max() < 1.0: return None
    early = delta <= 2.0
    if np.sum(early) < 4: return None
    k_lin = np.polyfit(delta[early], f_post[early] - snap_f, 1)[0]

    try:
        popt, _ = curve_fit(membrane_model, delta, f_post - snap_f,
                            p0=[max(k_lin, 0.01), 1e-4], maxfev=10000)
        k1, k3 = popt
        pred = membrane_model(delta, k1, k3)
        ss_res = np.sum((f_post - snap_f - pred)**2)
        ss_tot = np.sum((f_post - snap_f - np.mean(f_post - snap_f))**2)
        r2 = 1 - ss_res/ss_tot if ss_tot > 0 else 0.0
    except Exception:
        k1, k3, r2 = np.nan, np.nan, np.nan

    parts = curve['filename'].split('-')
    return {
        'filename': curve['filename'],
        'surfactant': parts[0], 'linker': parts[1],
        'snap_f_nn': snap_f, 'pulloff_f_nn': fr[np.argmin(fr)],
        'k_linear_nn_per_nm': k_lin,
        'k1_nn_per_nm': k1, 'k3_nn_per_nm3': k3, 'r_squared': r2,
        'E_app_mpa': E_app_mpa(k3),
        'max_delta_nm': delta.max(),
    }

if not FORCE and MECHANICS_CSV.exists():
    print(f"Loading cached mechanics: {MECHANICS_CSV}")
    dfm = pd.read_csv(MECHANICS_CSV)
else:
    print("Running contact mechanics (this takes ~2 min)...")
    mech = [r for c in all_curves if (r := analyze_contact(c)) is not None]
    dfm = pd.DataFrame(mech)
    dfm['hysteresis_nn'] = dfm['pulloff_f_nn'].abs() - dfm['snap_f_nn'].abs()
    dfm.to_csv(MECHANICS_CSV, index=False)
    print(f"  Cached → {MECHANICS_CSV}")

r2v = dfm['r_squared']
kpos = dfm[dfm['k_linear_nn_per_nm'] > 0]
print(f"Curves: {len(dfm)}")
print(f"Indentation: med={dfm['max_delta_nm'].median():.1f} nm, max={dfm['max_delta_nm'].max():.1f} nm")
print(f"R²: med={r2v.median():.3f}, max={r2v.max():.3f} | R²>0: {(r2v>0).sum()} | R²>0.5: {(r2v>0.5).sum()}")
print(f"k_linear: med={dfm['k_linear_nn_per_nm'].median():.2f}, pos_med={kpos['k_linear_nn_per_nm'].median():.2f} nN/nm ({len(kpos)}/{len(dfm)})")

print("\n=== Contact stiffness (nN/nm) ===")
print(dfm.pivot_table(values='k_linear_nn_per_nm', index='surfactant', columns='linker', aggfunc='median').to_string())

print("\n=== Adhesion hysteresis (nN) ===")
print(dfm.pivot_table(values='hysteresis_nn', index='surfactant', columns='linker', aggfunc='median').to_string())

# %% [markdown]
# ### 接触力学 — 关键结论
#
# **立方膜模型 F = k₁δ + k₃δ³ 不适用于此数据。**
#
# | 指标 | 数值 | 含义 |
# |------|------|------|
# | 压入深度 | 中位 10.7 nm | 深度浅但不是主要问题 |
# | R² | **全部 180 条 < 0**（中位 -2.64） | 模型比均值线还差 |
# | k₃ | 几乎全部为负 | 物理上 k₃ 必须 >0 |
#
# **原因**: PeakForce QNM 是 tapping 模式（1-2 kHz），接触段受悬臂动力学主导，
# 膜拉伸（k₃δ³）来不及响应。JJS 的深压入曲线（δ 50-100+ nm）才有足够的 k₃ 信号。
#
# **可用的稳健指标**: 线性接触刚度 k_linear（74/180 正刚度）、snap-in、pull-off、粘附滞后。

# %% [markdown]
# ## 7. 总结图

# %% Summary figure → save
fig, axes = plt.subplots(2, 3, figsize=(15, 9))
surfs = sorted(dfm['surfactant'].unique())

# R² distribution
axes[0,0].hist(r2v.dropna(), bins=40, color='#E8204E', edgecolor='white', alpha=0.8)
axes[0,0].axvline(0, color='black', ls='--'); axes[0,0].axvline(r2v.median(), color='#0C5DA5', lw=2, label=f'Median={r2v.median():.2f}')
axes[0,0].set_xlabel('R²'); axes[0,0].set_title('Cubic model: all R² < 0'); axes[0,0].legend(fontsize=8)

# Stiffness by surfactant
bp = axes[0,1].boxplot([dfm[dfm['surfactant']==s]['k_linear_nn_per_nm'].dropna() for s in surfs],
                        tick_labels=surfs, patch_artist=True)
for p, c in zip(bp['boxes'], COLORS): p.set_facecolor(c); p.set_alpha(0.6)
axes[0,1].axhline(0, color='gray', ls=':', lw=0.8); axes[0,1].set_title('Contact stiffness by surfactant')
axes[0,1].set_ylabel('k_linear (nN/nm)'); axes[0,1].tick_params(axis='x', rotation=45)

# Stiffness by linker
for i, lnk in enumerate(sorted(dfm['linker'].unique())):
    d = dfm[dfm['linker']==lnk]['k_linear_nn_per_nm'].dropna()
    axes[0,2].boxplot([d], positions=[i], tick_labels=[lnk], patch_artist=True)
axes[0,2].axhline(0, color='gray', ls=':', lw=0.8); axes[0,2].set_title('Contact stiffness by linker')

# Indentation depth
axes[1,0].hist(dfm['max_delta_nm'], bins=50, color='#00B945', edgecolor='white', alpha=0.8)
axes[1,0].axvline(dfm['max_delta_nm'].median(), color='#0C5DA5', lw=2, label=f'Median={dfm["max_delta_nm"].median():.1f} nm')
axes[1,0].set_xlabel('Max indentation (nm)'); axes[1,0].legend(fontsize=8)

# Hysteresis by surfactant
bp2 = axes[1,1].boxplot([dfm[dfm['surfactant']==s]['hysteresis_nn'].dropna() for s in surfs],
                         tick_labels=surfs, patch_artist=True)
for p, c in zip(bp2['boxes'], COLORS): p.set_facecolor(c); p.set_alpha(0.6)
axes[1,1].axhline(0, color='gray', ls=':', lw=0.8); axes[1,1].set_title('Adhesion hysteresis by surfactant')
axes[1,1].set_ylabel('Hysteresis (nN)'); axes[1,1].tick_params(axis='x', rotation=45)

# Key findings text
axes[1,2].axis('off')
n_pos = len(dfm[dfm['k_linear_nn_per_nm'] > 0])
summary = (
    f"KEY FINDINGS\n"
    f"==============\n\n"
    f"1. Cubic membrane model fails:\n"
    f"   all {len(dfm)} curves R² < 0.\n\n"
    f"2. PeakForce QNM contact too\n"
    f"   brief (~10 nm) for membrane\n"
    f"   stretching (k₃) to engage.\n\n"
    f"3. k_linear > 0 in {n_pos}/{len(dfm)}\n"
    f"   curves — usable for ranking.\n\n"
    f"4. Adhesion hysteresis is the\n"
    f"   most robust group metric.\n\n"
    f"5. Absolute forces need\n"
    f"   calibration verification."
)
axes[1,2].text(0, 1, summary, transform=axes[1,2].transAxes, fontsize=9,
               verticalalignment='top', fontfamily='monospace',
               bbox=dict(boxstyle='round', facecolor='#F5F5F5', alpha=0.9))

plt.tight_layout()
plt.savefig(FIG_DIR / "summary.png"); plt.savefig(FIG_DIR / "summary.pdf")
plt.show()

# %% [markdown]
# ## 8. 总体结论
#
# ### 已确认
# 1. **Pull-off 极均匀** (~239 nN): 探针-水膜界面固有属性
# 2. **Snap-in 区分样品**: SDBS > SDS ≈ NLS > PAA ≈ PFNA > PFPE > NOSTF
# 3. **膜模型不可用**: QNM tapping 不能替代深压入实验
#
# ### 与 JJS 对比
# | 特征 | JJS | 1umSquare |
# |------|-----|-----------|
# | 模式 | QNM + 深压入 | QNM 力-体积 |
# | Snap-in | ~17 nN | ~2577 nN (待标定) |
# | Pull-off | ~116 nN | ~239 nN |
# | 膜模型 | 可用 (δ 50-100+ nm) | 不可用 |
#
# ### 缓存文件
# 首次运行后，`results/` 目录下缓存了：
# - `curves.pkl` — 解析后的 210 条曲线
# - `contact_mechanics.csv` — 接触力学分析结果
# - `figures/*.png`, `figures/*.pdf` — 所有图表
# - `python analysis.py --force` 强制重算全部

print("\n=== Analysis complete ===")
print(f"Cache: {CACHE_DIR}")
print(f"  {CURVES_PKL.name}: {'✓' if CURVES_PKL.exists() else '✗'}")
print(f"  {FEATURES_CSV.name}: {'✓' if FEATURES_CSV.exists() else '✗ (not cached, fast to recompute)'}")
print(f"  {MECHANICS_CSV.name}: {'✓' if MECHANICS_CSV.exists() else '✗'}")
print(f"  figures/: {len(list(FIG_DIR.glob('*')))} files")
print("Re-run without --force to use cache.")
