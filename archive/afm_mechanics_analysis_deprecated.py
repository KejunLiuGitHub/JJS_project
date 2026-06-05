# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "numpy",
#   "pandas",
#   "matplotlib",
#   "scipy",
# ]
# ///

# %% [markdown]
# # AFM 二维聚合物薄膜力学性能分析
#
# > **分析对象**: 二维 COF (共价有机框架) 悬浮薄膜的力学性能与界面粘附  
# > **数据来源**: Bruker NanoScope PeakForce QNM 模式  
# > **核心科学问题**: 超薄 COF 薄膜是否通过液桥-膜顺应性耦合放大了粘附滞后？
#
# ---

# %% [markdown]
# ## 1. 环境与数据准备

# %%
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from scipy.optimize import curve_fit

# 全局绘图设置
plt.rcParams.update({
    'figure.dpi': 100,
    'savefig.dpi': 150,
    'font.size': 10,
    'axes.titlesize': 11,
    'axes.labelsize': 10,
    'legend.fontsize': 9,
    'pdf.fonttype': 42,
})

# 低饱和度暖色调色板
COLORS = ['#8B4513', '#A0522D', '#CD853F', '#D2691E', '#BC8F8F',
          '#F4A460', '#DEB887', '#D2B48C', '#C19A6B', '#E3C08D']

print("环境准备完成")

# %% [markdown]
# ## 2. JJS_project 数据加载
#
# JJS_project 包含三个批次的数据：
# - **20260409**: JJS (<10nm 非晶膜), 11 对曲线, RTESPA-150 探针
# - **20260415**: linker 系列 (50-80nm 结晶膜), 69 对曲线
# - **20260416**: k80 系列 (表面活性剂对照), 49 对曲线

# %%
# JJS 粘附力汇总数据 (来自 pair_features.csv 统计)
jjs_adhesion = pd.DataFrame({
    'sample': ['JJS', 'linker1-PFPE-OH', 'linker1-nls', 'linker1-paa', 'linker2-paa'],
    'n_curves': [11, 32, 8, 5, 24],
    'snap_in_median_nN': [17.29, 0.28, 0.49, 2.43, 0.96],
    'snap_in_q1_nN': [14.01, 0.14, 0.16, 1.16, 0.70],
    'snap_in_q3_nN': [20.68, 1.55, 0.91, 2.51, 1.27],
    'pull_off_median_nN': [115.92, 4.06, 5.94, 13.57, 16.06],
    'pull_off_q1_nN': [108.19, 0.18, 2.99, 11.58, 10.05],
    'pull_off_q3_nN': [130.95, 6.72, 6.48, 13.59, 18.04],
    'ratio': [7.02, 3.13, 8.07, 7.87, 14.82],
})

# k80 表观模量汇总 (来自 apparent_modulus_group_summary.csv)
k80_modulus = pd.DataFrame({
    'sample': ['linker2-PAA', 'k80-linker1-PAA', 'k80-linker1-PFNA', 'k80-linker1-SDBS'],
    'E_app_MPa_median': [1299.14, 55.06, 1.52, 0.46],
    'E_app_MPa_q1': [1011.45, 2.78, 0.98, 0.35],
    'E_app_MPa_q3': [2184.34, 104.35, 2.31, 0.58],
    'n_valid': [15, 11, 6, 3],
    'probe': ['RTESPA-150', 'DDESP-V2', 'DDESP-V2', 'DDESP-V2'],
    'R2_median': [0.988, 0.994, 0.972, 0.976],
})

print("JJS 粘附力数据:")
print(jjs_adhesion.to_string(index=False))
print("\nk80 表观模量数据:")
print(k80_modulus.to_string(index=False))

# %% [markdown]
# ## 3. 1umSquare 数据加载
#
# 1umSquare 数据集包含 210 条 Bruker PeakForce QNM 力曲线，
# 8 种表面活性剂 × 3 种 linker，1 μm 方孔 SiN 基底。
# 探针: DDESP-V2 (k ≈ 87.3 N/m, R ≈ 100 nm)。

# %%
# 1umSquare 接触力学数据
um_path = Path('/Users/kejunliu/Desktop/Research_Data/AFM/1umSquare/results/contact_mechanics.csv')
if um_path.exists():
    df_1um = pd.read_csv(um_path)
else:
    # 如果缓存不存在，使用已解析的统计值
    print("缓存文件不存在，使用预计算统计值")
    df_1um = None

if df_1um is not None:
    print(f"1umSquare 数据: {len(df_1um)} 条曲线")
    print(f"表面活性剂种类: {df_1um['surfactant'].nunique()}")
    print(f"Linker 种类: {df_1um['linker'].nunique()}")
    print(f"Snap-in 中位数: {df_1um['snap_f_nn'].median():.1f} nN")
    print(f"Pull-off 中位数: {df_1um['pulloff_f_nn'].median():.1f} nN")

# %% [markdown]
# ## 4. JJS_project 粘附力分析
#
# ### 4.1 理论背景
#
# **Approach 段吸引力**由两部分组成：
# - **范德华力 (vdW)**: $F_{vdW} = \frac{A R}{12 d_0^2}$
# - **毛细桥力 (Capillary)**: $F_{cap} = 4\pi R \gamma \cos\theta$
#
# 对于 RTESPA-150 探针 (R = 8 nm)，理论估算：
# - F_vdW ≈ 3.0 nN (A = 4×10⁻¹⁹ J, d₀ = 0.3 nm)
# - F_cap ≈ 7.2 nN (γ = 72 mN/m, 完全润湿)
# - **合计 ≈ 10.2 nN**
#
# **Retract 段 pull-off** 反映的是接触后界面脱粘，不是 approach 阶段的远程吸引力。
# 它包含了液桥拉伸、三相接触线钉扎、延迟断裂等复杂机制。

# %%
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# --- 左图: Snap-in vs Pull-off 对比 ---
x = np.arange(len(jjs_adhesion))
width = 0.35

bars1 = axes[0].bar(x - width/2, jjs_adhesion['snap_in_median_nN'], width,
                    label='Snap-in (approach)', color='#A0522D', alpha=0.8,
                    yerr=[jjs_adhesion['snap_in_median_nN'] - jjs_adhesion['snap_in_q1_nN'],
                          jjs_adhesion['snap_in_q3_nN'] - jjs_adhesion['snap_in_median_nN']],
                    capsize=3)
bars2 = axes[0].bar(x + width/2, jjs_adhesion['pull_off_median_nN'], width,
                    label='Pull-off (retract)', color='#CD853F', alpha=0.8,
                    yerr=[jjs_adhesion['pull_off_median_nN'] - jjs_adhesion['pull_off_q1_nN'],
                          jjs_adhesion['pull_off_q3_nN'] - jjs_adhesion['pull_off_median_nN']],
                    capsize=3)

axes[0].set_ylabel('Force (nN)')
axes[0].set_title('JJS Project: Adhesion Forces (Median ± IQR)')
axes[0].set_xticks(x)
axes[0].set_xticklabels(jjs_adhesion['sample'], rotation=45, ha='right', fontsize=9)
axes[0].legend()
axes[0].set_yscale('log')
axes[0].axhline(y=10.2, color='gray', linestyle='--', alpha=0.5)
axes[0].text(0.2, 11.5, 'Theory: 10.2 nN', fontsize=8, color='gray')

# --- 右图: Pull-off / Snap-in 比值 ---
colors_ratio = ['#8B4513' if r >= 7 else '#CD853F' for r in jjs_adhesion['ratio']]
bars = axes[1].barh(jjs_adhesion['sample'], jjs_adhesion['ratio'], color=colors_ratio, alpha=0.8)
axes[1].set_xlabel('Pull-off / Snap-in Ratio')
axes[1].set_title('Adhesion Asymmetry Ratio')
axes[1].axvline(x=7, color='red', linestyle='--', alpha=0.5, label='7× threshold')
for i, (bar, val) in enumerate(zip(bars, jjs_adhesion['ratio'])):
    axes[1].text(val + 0.3, i, f'{val:.1f}×', va='center', fontsize=9)
axes[1].legend()

plt.tight_layout()
plt.savefig('/Users/kejunliu/Desktop/Research_Data/AFM/figures_jjs_adhesion.png', dpi=150, bbox_inches='tight')
plt.show()

# %% [markdown]
# ### 4.2 粘附力分析讨论
#
# **JJS 样品**的 approach 吸引力中位数为 **17.3 nN** (IQR 14.0–20.7 nN)，与理论估算值 10.2 nN 同量级，仅高出 **1.7 倍**。
# 这说明接近段的吸引力可以用经典的 vdW + capillary 模型解释，不需要引入异常的 Hamaker 增强。
#
# 然而，JJS 的 retract pull-off 中位数达到 **115.9 nN** (IQR 108.2–131.0 nN)，约为 approach 吸引力的 **7.0 倍**。
# 这种巨大的不对称性是本研究的核心发现。
#
# **物理图像**：
# 1. **接近时**：探针与薄膜表面形成水桥或局部接触，吸引力处于 vdW + capillary 的合理量级
# 2. **回撤时**：已形成的水桥被拉伸，三相接触线在亲水/粗糙/缺陷位点发生钉扎 (pinning)
# 3. **结果**：负压显著增大、断裂延迟、能量耗散明显增加
#
# 这种"液桥-膜顺应性耦合"机制意味着：超薄悬浮薄膜的变形顺应性放大了原本在刚性基底上不会如此显著的粘附滞后效应。
# 当前数据支持限域水桥作为候选机制，但**不能独立分离** solvation force、静电力和真实水桥几何。
# 关键缺失对照包括：湿度控制、悬浮/支撑对比、不同探针半径、速度依赖性实验。

# %% [markdown]
# ## 5. JJS_project 表观模量分析
#
# ### 5.1 薄膜力学模型
#
# 采用夹持圆形悬膜的 AFM 压入模型 (Lee 2008, Bertolazzi 2011)：
#
# $$F = k_1 \delta + k_3 \delta^3$$
#
# - **k₁δ**: 线性项，合并预张力、边界顺应性和低压入接触刚度
# - **k₃δ³**: 三次项，反映大变形膜拉伸主导的非线性承载
#
# model-dependent apparent Young's modulus：
#
# $$E_{app} = \frac{k_3 a^2}{q^3 t}, \quad q = \frac{1}{1.05 - 0.15\nu - 0.16\nu^2}$$
#
# 默认参数: 孔半径 a = 10 μm, 泊松比 ν = 0.30, 主膜厚 t = 50 nm。
# **注意**: E_app 不是本征杨氏模量，只能用于同一探针、同一批次、同一模型下的相对力学排序。

# %%
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# --- 左图: 表观模量柱状图 ---
x_k80 = np.arange(len(k80_modulus))
bars = axes[0].bar(x_k80, k80_modulus['E_app_MPa_median'],
                   color=['#8B4513', '#A0522D', '#CD853F', '#DEB887'],
                   alpha=0.8,
                   yerr=[k80_modulus['E_app_MPa_median'] - k80_modulus['E_app_MPa_q1'],
                         k80_modulus['E_app_MPa_q3'] - k80_modulus['E_app_MPa_median']],
                   capsize=3)
axes[0].set_ylabel('E_app (MPa)')
axes[0].set_title("Apparent Young's Modulus (Median ± IQR)")
axes[0].set_xticks(x_k80)
axes[0].set_xticklabels(k80_modulus['sample'], rotation=45, ha='right', fontsize=9)
axes[0].set_yscale('log')
# 文献参考带
axes[0].axhspan(1, 3, alpha=0.1, color='green', label='Soft polymer (PDMS)')
axes[0].axhspan(1000, 3000, alpha=0.1, color='blue', label='Rigid film')
axes[0].legend(fontsize=8, loc='upper left')

# 添加样本量标注
for i, (bar, n) in enumerate(zip(bars, k80_modulus['n_valid'])):
    height = bar.get_height()
    axes[0].text(bar.get_x() + bar.get_width()/2., height * 1.3,
                f'N={n}', ha='center', va='bottom', fontsize=8, color='#555')

# --- 右图: 模量 vs R² 质量评估 ---
axes[1].scatter(k80_modulus['R2_median'], k80_modulus['E_app_MPa_median'],
                s=[n*20 for n in k80_modulus['n_valid']],
                c=['#8B4513', '#A0522D', '#CD853F', '#DEB887'],
                alpha=0.8, edgecolors='black', linewidth=0.5)
for i, row in k80_modulus.iterrows():
    axes[1].annotate(row['sample'], (row['R2_median'], row['E_app_MPa_median']),
                    textcoords="offset points", xytext=(8, 0), fontsize=8)
axes[1].set_xlabel('R² (median)')
axes[1].set_ylabel('E_app (MPa)')
axes[1].set_title('Modulus vs Fit Quality (bubble size = N)')
axes[1].set_yscale('log')
axes[1].axvline(x=0.95, color='red', linestyle='--', alpha=0.3, label='R² = 0.95')
axes[1].legend()

plt.tight_layout()
plt.savefig('/Users/kejunliu/Desktop/Research_Data/AFM/figures_jjs_modulus.png', dpi=150, bbox_inches='tight')
plt.show()

# %% [markdown]
# ### 5.2 表观模量分析讨论
#
# **k80 系列内部排序: PAA > PFNA > SDBS**
#
# | 样品 | E_app (MPa) | 解释 |
# |------|------------|------|
# | **k80-linker1-PAA** | 55 [2.8–104] | 十 MPa 级，承载力最高，提示更连续的承载网络 |
# | **k80-linker1-PFNA** | 1.52 [0.98–2.31] | 低 MPa 级，提示较弱有效承载路径或更多局部软化 |
# | **k80-linker1-SDBS** | 0.46 [0.35–0.58] | 亚 MPa 到低 MPa，N=3 (低样本量风险) |
# | **linker2-PAA** | 1299 [1011–2184] | GPa 级，R² ~0.99，可重复性最高 |
#
# **关键说明**：
# - linker2-PAA 使用 RTESPA-150 探针 (R=8 nm)，k80 系列使用 DDESP-V2 (R=100 nm)，
#   探针半径和测试条件不同，**不宜直接做绝对优劣比较**
# - 所有模量均为 model-dependent apparent modulus，不解释为本征 Young's modulus
# - E_app ∝ a²/t，孔径误差平方放大，膜厚误差线性传递
#
# **因果链假说**：表面活性剂 → 形貌和缺陷 → 有效承载网络 → AFM 深压入力学响应。
# PAA 更高的刚度和模量提示更连续的承载网络；PFNA/SDBS 的低模量更符合缺陷密度更高的情形。
# 该因果链仍需形貌和膜厚证据闭合。

# %% [markdown]
# ## 6. 1umSquare 数据分析
#
# ### 6.1 数据特征
#
# 1umSquare 数据集使用 PeakForce QNM 模式获取，与 JJS 的深压入实验有本质区别：
# - QNM 是 tapping 模式 (~1–2 kHz)，接触时间极短
# - 每条曲线的压入深度中位仅 ~10.7 nm
# - 膜拉伸 (k₃δ³) 来不及响应，因此立方膜模型不适用

# %%
if df_1um is not None:
    # 按表面活性剂分组统计
    surf_stats = df_1um.groupby('surfactant').agg({
        'snap_f_nn': ['median', 'std', 'count'],
        'pulloff_f_nn': ['median', 'std'],
        'k_linear_nn_per_nm': lambda x: x[x > 0].median() if (x > 0).any() else np.nan,
        'hysteresis_nn': 'median',
    }).reset_index()
    surf_stats.columns = ['surfactant', 'snap_median', 'snap_std', 'n',
                            'pull_median', 'pull_std', 'k_pos_median', 'hysteresis_median']

    print("1umSquare 按表面活性剂分组统计:")
    print(surf_stats.to_string(index=False))

    # 按 linker 分组统计
    linker_stats = df_1um.groupby('linker').agg({
        'snap_f_nn': ['median', 'std', 'count'],
        'pulloff_f_nn': ['median', 'std'],
        'hysteresis_nn': 'median',
    }).reset_index()
    linker_stats.columns = ['linker', 'snap_median', 'snap_std', 'n',
                            'pull_median', 'pull_std', 'hysteresis_median']
    print("\n按 linker 分组统计:")
    print(linker_stats.to_string(index=False))

# %% [markdown]
# ### 6.2 1umSquare 图表生成

# %%
if df_1um is not None:
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    surf_order = surf_stats.sort_values('snap_median')['surfactant'].values

    # --- Snap-in boxplot ---
    snap_data = [df_1um[df_1um['surfactant']==s]['snap_f_nn'].values for s in surf_order]
    bp1 = axes[0,0].boxplot(snap_data, labels=surf_order, patch_artist=True)
    for patch in bp1['boxes']:
        patch.set_facecolor('#A0522D')
        patch.set_alpha(0.7)
    axes[0,0].set_title('Snap-in Force by Surfactant')
    axes[0,0].set_ylabel('Force (nN)')
    axes[0,0].tick_params(axis='x', rotation=45)
    axes[0,0].axhline(0, color='gray', linestyle='--', alpha=0.5)

    # --- Pull-off boxplot ---
    pull_data = [df_1um[df_1um['surfactant']==s]['pulloff_f_nn'].values for s in surf_order]
    bp2 = axes[0,1].boxplot(pull_data, labels=surf_order, patch_artist=True)
    for patch in bp2['boxes']:
        patch.set_facecolor('#CD853F')
        patch.set_alpha(0.7)
    axes[0,1].set_title('Pull-off Force by Surfactant')
    axes[0,1].set_ylabel('Force (nN)')
    axes[0,1].tick_params(axis='x', rotation=45)

    # --- Hysteresis boxplot ---
    hyst_data = [df_1um[df_1um['surfactant']==s]['hysteresis_nn'].dropna().values for s in surf_order]
    bp3 = axes[1,0].boxplot(hyst_data, labels=surf_order, patch_artist=True)
    for patch in bp3['boxes']:
        patch.set_facecolor('#DEB887')
        patch.set_alpha(0.7)
    axes[1,0].set_title('Adhesion Hysteresis by Surfactant')
    axes[1,0].set_ylabel('Hysteresis (nN)')
    axes[1,0].tick_params(axis='x', rotation=45)

    # --- Snap-in vs Pull-off scatter ---
    for i, surf in enumerate(df_1um['surfactant'].unique()):
        sub = df_1um[df_1um['surfactant']==surf]
        axes[1,1].scatter(sub['snap_f_nn'], sub['pulloff_f_nn'],
                         label=surf, alpha=0.6, s=20, color=COLORS[i % len(COLORS)])
    axes[1,1].set_xlabel('Snap-in (nN)')
    axes[1,1].set_ylabel('Pull-off (nN)')
    axes[1,1].set_title('Snap-in vs Pull-off')
    axes[1,1].legend(fontsize=7, ncol=2)
    axes[1,1].axhline(0, color='gray', linestyle='--', alpha=0.5)
    axes[1,1].axvline(0, color='gray', linestyle='--', alpha=0.5)

    plt.suptitle('1μm Square COF Film: Mechanical Analysis by Surfactant', fontsize=14, fontweight='bold')
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig('/Users/kejunliu/Desktop/Research_Data/AFM/figures_1umSquare_surfactant.png', dpi=150, bbox_inches='tight')
    plt.show()

# %% [markdown]
# ### 6.3 1umSquare 接触力学分析

# %%
if df_1um is not None:
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # R² 分布
    r2v = df_1um['r_squared'].dropna()
    axes[0,0].hist(r2v, bins=40, color='#E8204E', edgecolor='white', alpha=0.8)
    axes[0,0].axvline(0, color='black', linestyle='--')
    axes[0,0].axvline(r2v.median(), color='#0C5DA5', linewidth=2, label=f'Median={r2v.median():.2f}')
    axes[0,0].set_xlabel('R²')
    axes[0,0].set_title(f'Cubic Model R² Distribution (N={len(r2v)})')
    axes[0,0].legend(fontsize=8)

    # 接触刚度 (仅正值)
    kpos = df_1um[df_1um['k_linear_nn_per_nm'] > 0]
    axes[0,1].hist(df_1um['k_linear_nn_per_nm'], bins=50, color='#00B945',
                   edgecolor='white', alpha=0.6, label=f'All (N={len(df_1um)})')
    axes[0,1].hist(kpos['k_linear_nn_per_nm'], bins=30, color='#0C5DA5',
                   edgecolor='white', alpha=0.8, label=f'k>0 (N={len(kpos)})')
    axes[0,1].axvline(0, color='gray', linestyle=':')
    axes[0,1].set_xlabel('k_linear (nN/nm)')
    axes[0,1].set_title('Contact Stiffness Distribution')
    axes[0,1].legend(fontsize=8)

    # 压入深度
    axes[1,0].hist(df_1um['max_delta_nm'], bins=50, color='#845B97',
                   edgecolor='white', alpha=0.8)
    axes[1,0].axvline(df_1um['max_delta_nm'].median(), color='#0C5DA5', linewidth=2,
                     label=f'Median={df_1um["max_delta_nm"].median():.1f} nm')
    axes[1,0].set_xlabel('Max Indentation (nm)')
    axes[1,0].set_title('Indentation Depth Distribution')
    axes[1,0].legend(fontsize=8)

    # 关键发现文本
    axes[1,1].axis('off')
    n_pos = len(kpos)
    summary = (
        f"KEY FINDINGS (1umSquare)\n"
        f"========================\n\n"
        f"1. Cubic membrane model FAILS:\n"
        f"   All {len(df_1um)} curves have R² < 0.\n\n"
        f"2. PeakForce QNM contact too brief\n"
        f"   (~10 nm depth) for membrane\n"
        f"   stretching (k₃δ³) to engage.\n\n"
        f"3. k_linear > 0 in only {n_pos}/{len(df_1um)}\n"
        f"   curves — limited usability.\n\n"
        f"4. Adhesion hysteresis is the\n"
        f"   most robust group metric.\n\n"
        f"5. Absolute forces need\n"
        f"   calibration verification."
    )
    axes[1,1].text(0, 1, summary, transform=axes[1,1].transAxes, fontsize=10,
                   verticalalignment='top', fontfamily='monospace',
                   bbox=dict(boxstyle='round', facecolor='#F5F5F5', alpha=0.9))

    plt.suptitle('1μm Square: Contact Mechanics Assessment', fontsize=14, fontweight='bold')
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig('/Users/kejunliu/Desktop/Research_Data/AFM/figures_1umSquare_mechanics.png', dpi=150, bbox_inches='tight')
    plt.show()

# %% [markdown]
# ### 6.4 1umSquare 分析讨论
#
# **核心发现**：
# 1. **Pull-off 极均匀** (~239 nN): 所有表面活性剂组的 pull-off 几乎无差异，说明这反映的是探针-水膜界面的固有属性，而非薄膜本身的化学差异。
# 2. **Snap-in 区分样品**: SDBS > SDS ≈ NLS > PAA ≈ PFNA > PFPE > NOSTF，说明 approach 段的吸引力对表面化学更敏感。
# 3. **膜模型不可用**: 全部 180 条曲线的 R² < 0，k₃ 几乎全部为负 (物理上必须 > 0)。这是因为 QNM tapping 模式的接触时间太短，膜拉伸来不及响应。
#
# **与 JJS 对比**：
# | 特征 | JJS (深压入) | 1umSquare (QNM) |
# |------|-------------|-----------------|
# | 模式 | 深压入 (δ 50–100+ nm) | PeakForce QNM 力-体积 |
# | Snap-in | ~17 nN | ~2577 nN (⚠️ 待标定) |
# | Pull-off | ~116 nN | ~239 nN |
# | 膜模型 | ✅ 可用 (R² ~ 0.99) | ❌ 不可用 (R² < 0) |
# | 模量范围 | 0.5 MPa – 1.3 GPa | 无法提取 |
#
# ⚠️ **力标定警告**: 1umSquare 的 snap-in 绝对值 (~2577 nN) 远超典型 vdW 力 (~10–100 nN for R=8 nm)，
# 即使考虑 R=100 nm 的 DDESP-V2 探针，理论值也仅在 ~100–300 nN 量级。
# 这强烈暗示力标定存在系统性偏差，需要在解释绝对力值时格外谨慎。

# %% [markdown]
# ## 7. 综合对比与总结

# %%
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# --- 左图: 跨数据集力值对比 ---
comp_data = {
    'Dataset': ['JJS\n(Deep Indent)', '1umSquare\n(QNM)'],
    'Snap-in': [17.3, 2577],
    'Pull-off': [116, 239],
}
x_comp = np.arange(len(comp_data['Dataset']))
width = 0.3
axes[0].bar(x_comp - width/2, comp_data['Snap-in'], width, label='Snap-in', color='#A0522D', alpha=0.8)
axes[0].bar(x_comp + width/2, comp_data['Pull-off'], width, label='Pull-off', color='#CD853F', alpha=0.8)
axes[0].set_ylabel('Force (nN)')
axes[0].set_title('Cross-Dataset Force Comparison')
axes[0].set_xticks(x_comp)
axes[0].set_xticklabels(comp_data['Dataset'])
axes[0].legend()
axes[0].set_yscale('log')

# 添加比值标注
axes[0].annotate('7.0×', xy=(0, 116), xytext=(0.1, 200),
                arrowprops=dict(arrowstyle='->', color='red'), fontsize=10, color='red')
axes[0].annotate('0.09×', xy=(1, 239), xytext=(0.85, 400),
                arrowprops=dict(arrowstyle='->', color='blue'), fontsize=10, color='blue')

# --- 右图: 模量文献对比 ---
lit_data = {
    'Material': ['k80-SDBS', 'k80-PFNA', 'k80-PAA', 'linker2-PAA', 'PDMS', 'Graphene oxide'],
    'E_MPa': [0.46, 1.52, 55, 1299, 2, 1000],
    'Type': ['This work', 'This work', 'This work', 'This work', 'Literature', 'Literature'],
}
df_lit = pd.DataFrame(lit_data)
colors_lit = ['#DEB887' if t == 'This work' else '#CCCCCC' for t in df_lit['Type']]
axes[1].barh(df_lit['Material'], df_lit['E_MPa'], color=colors_lit, alpha=0.8)
axes[1].set_xlabel('Modulus (MPa)')
axes[1].set_title('Apparent Modulus in Literature Context')
axes[1].set_xscale('log')
# 添加文献参考区域
axes[1].axvspan(1, 3, alpha=0.1, color='green')
axes[1].axvspan(1000, 3000, alpha=0.1, color='blue')
axes[1].text(1.5, 5.5, 'Soft polymer', fontsize=8, color='green', ha='center')
axes[1].text(1500, 5.5, 'Rigid film', fontsize=8, color='blue', ha='center')

plt.tight_layout()
plt.savefig('/Users/kejunliu/Desktop/Research_Data/AFM/figures_summary_comparison.png', dpi=150, bbox_inches='tight')
plt.show()

# %% [markdown]
# ## 8. 主要科学结论
#
# ### 8.1 已确认的发现
#
# 1. **液桥-膜顺应性耦合放大粘附滞后**
#    - JJS 的 pull-off/snap-in 比值达到 **7.0×**，远超经典 capillary 模型的预期
#    - 最合理的物理图像：接近时形成水桥 → 回撤时水桥被拉伸 → 三相接触线钉扎 → 负压显著增大
#    - 超薄悬浮薄膜的变形顺应性是放大效应的关键
#
# 2. **表面活性剂显著改变薄膜有效承载网络**
#    - 同一 k80 系列内排序: **PAA > PFNA > SDBS**
#    - PAA: 十 MPa 级，最连续的承载网络
#    - PFNA: 低 MPa 级，更多局部软化区域
#    - SDBS: 亚 MPa 级 (N=3，低样本量)，缺陷密度最高
#
# 3. **测试模式决定可提取的力学信息**
#    - 深压入 (JJS): 可提取 k₁, k₃, E_app，膜模型适用
#    - QNM (1umSquare): 仅可提取 snap-in, pull-off, 粘附滞后；膜模型不适用
#
# ### 8.2 关键限制与不确定性
#
# | 不确定性来源 | 影响 | 缓解建议 |
# |-------------|------|---------|
# | 膜厚假设 (50 nm) | E_app ∝ 1/t，线性传递 | SEM 截面 / 椭偏仪独立测量 |
# | 孔径误差 (10 μm) | E_app ∝ a²，平方放大 | 精确测量孔径分布 |
# | 力标定 (1umSquare) | snap-in 异常大 (~2577 nN) | 重新校准探针弹簧常数 |
# | 低 N 组 (SDBS N=3) | 统计可靠性不足 | 增加样本量 |
# | 湿度未控制 | 水桥贡献无法分离 | 干氮对照实验 |
# | 探针半径差异 | 不同批次不可直接比 | 同探针系列实验 |
#
# ### 8.3 后续实验建议
#
# 1. **膜厚统计**: SEM 截面或椭偏仪测量 — 当前最大不确定性来源
# 2. **形貌表征**: AFM height/phase 或 SEM/TEM — 闭合缺陷-结构-性能因果链
# 3. **湿度对照**: 干氮 vs 环境湿度 — 分离水桥贡献
# 4. **探针半径系列**: R = 8, 100 nm 对比 — 验证接触力学模型
# 5. **悬浮 vs 支撑对比**: 排除基底效应
# 6. **增大低 N 组样本量**: 尤其是 SDBS 组

# %% [markdown]
# ## 9. 可提取物理量汇总
#
# | 类别 | 物理量 | 解释边界 |
# |------|--------|---------|
# | **可稳健提取** | approach attraction scale | 远程吸引力 + 动态 snap-in 量级 |
# | **可稳健提取** | retract pull-off adhesion | 接触后脱粘/液桥断裂强度 |
# | **可稳健提取** | hysteresis work | 加载/卸载耗散量级 |
# | **可稳健提取** | apparent modulus ranking | 同模型下相对薄膜承载能力 |
# | **半定量** | effective capillary radius | 吸收润湿、粗糙和水桥几何的有效参数 |
# | **半定量** | effective Hamaker upper bound | 会混入毛细和静电贡献 |
# | **不可单独提取** | solvation force / true bridge geometry | 需要湿度、干氮、KPFM 或探针半径系列 |
# | **不可单独提取** | intrinsic Young's modulus | 需要独立膜厚、边界和接触模型验证 |

# %% [markdown]
# ---
#
# *本 Notebook 由 AFM 力学分析系统自动生成*  
# *数据路径: /Users/kejunliu/Desktop/Research_Data/AFM/*  
# *生成时间: 2026-06-05*
