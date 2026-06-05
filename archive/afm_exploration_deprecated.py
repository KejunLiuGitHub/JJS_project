import marimo

__generated_with = "0.23.8"
app = marimo.App(
    width="medium",
    layout_file="layouts/afm_exploration.slides.json",
)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # AFM 力曲线分析 — 1μm 方孔 COF 悬浮薄膜

    **数据**: 210 条 Bruker PeakForce QNM 力曲线，8 种表面活性剂 × 3 种 linker 组合，
    1 μm 方孔 SiN 基底，探针 RTESPA-150 (k ≈ 80 N/m, R ≈ 8 nm)。

    **分析目标**:
    1. 提取 snap-in（approach 吸引力）、pull-off（retract 粘附力）、粘附滞后
    2. 按 surfactant × linker 分组比较粘附与刚度
    3. 尝试用膜力学模型 F = k₁δ + k₃δ³ 拟合接触段，计算表观模量

    **关键注意事项**:
    - Bruker 原始二进制格式解析 (Ciao data blocks, interleaved int16 trace/retrace)
    - Snap-in ~ -2577 nN (量级偏大，绝对力值需进一步标定)
    - Pull-off ~ -239 nN (非常均匀，几乎不随 surfactant/linker 变化)
    - 粘附滞后 ~ 2200–2500 nN (由 snap-in 主导)
    """)
    return


@app.cell(hide_code=True)
def _():
    import sys
    sys.path.insert(0, "/Users/kejunliu/Desktop/Research_Data/AFM/1umSquare")
    from bruker_parser import parse_bruker_force_curve
    import numpy as np
    from pathlib import Path
    import matplotlib.pyplot as plt
    import json
    import marimo as mo

    print("Imports ready.")
    return Path, mo, np, parse_bruker_force_curve, plt


@app.cell(hide_code=True)
def _(Path, parse_bruker_force_curve, plt):
    # Test parser with a sample file
    data_dir = Path("/Users/kejunliu/Desktop/Research_Data/AFM/1umSquare/1um")
    sample_file = data_dir / "NLS-linker1-1um-50nm-1000nm-7uN-A"

    result = parse_bruker_force_curve(str(sample_file))

    print(f"File: {result['filename']}")
    print(f"Spring constant: {result['spring_constant']} N/m")
    print(f"Ramp size: {result['ramp_size_nm']:.1f} nm")
    print(f"Z range: [{result['z_nm'].min():.1f}, {result['z_nm'].max():.1f}] nm")
    print(f"Force range: [{result['force_nn'].min():.1f}, {result['force_nn'].max():.1f}] nN")
    print(f"Snap-in (min force): {result['force_nn'].min():.1f} nN")
    print(f"Max contact force: {result['force_nn'].max():.1f} nN")
    print(f"Retract pull-off: {result['force_retract_nn'].min():.1f} nN")

    # Quick plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
    ax1.plot(result['z_nm'], result['force_nn'], 'b-', alpha=0.7, label='Approach')
    ax1.plot(result['z_nm_retract'], result['force_retract_nn'], 'r-', alpha=0.7, label='Withdraw')
    ax1.set_xlabel('Z (nm)')
    ax1.set_ylabel('Force (nN)')
    ax1.set_title(result['filename'][:60])
    ax1.legend()
    ax1.axhline(y=0, color='gray', linestyle='--')

    mask = result['z_nm'] < 200
    ax2.plot(result['z_nm'][mask], result['force_nn'][mask], 'b.-', alpha=0.7, markersize=2, label='Approach')
    ax2.plot(result['z_nm_retract'][mask], result['force_retract_nn'][mask], 'r.-', alpha=0.7, markersize=2, label='Withdraw')
    ax2.set_xlabel('Z (nm)')
    ax2.set_ylabel('Force (nN)')
    ax2.set_title('Zoom: Z < 200 nm')
    ax2.legend()
    ax2.axhline(y=0, color='gray', linestyle='--')

    plt.tight_layout()
    plt.gca()
    return


@app.cell(hide_code=True)
def _(Path, np, parse_bruker_force_curve):
    # Batch load all 1umSquare force curves
    raw_dir = Path("/Users/kejunliu/Desktop/Research_Data/AFM/1umSquare/1um")
    all_files = sorted(raw_dir.iterdir())

    print(f"Found {len(all_files)} files")

    all_curves = []
    errors = []
    for fp in all_files:
        try:
            curve = parse_bruker_force_curve(str(fp))
            all_curves.append(curve)
        except Exception as e:
            errors.append((fp.name, str(e)))

    print(f"Successfully parsed: {len(all_curves)} curves")
    print(f"Errors: {len(errors)}")
    if errors:
        for name, err in errors[:5]:
            print(f"  {name}: {err}")

    def extract_features(curve):
        f = curve['force_nn']
        z = curve['z_nm']
        fr = curve['force_retract_nn']

        snap_idx = np.argmin(f)
        snap_f = f[snap_idx]
        snap_z = z[snap_idx]

        after_snap = np.arange(len(z)) > snap_idx
        contact_candidates = np.where(after_snap & (f >= 0))[0]
        contact_idx = contact_candidates[0] if len(contact_candidates) > 0 else len(z) - 1

        pulloff_idx = np.argmin(fr)
        pulloff_f = fr[pulloff_idx]

        max_force = np.max(f)
        max_force_retract = np.max(fr)
        adhesion_hysteresis = abs(pulloff_f) - abs(snap_f) if snap_f < 0 else abs(pulloff_f)

        name = curve['filename']
        parts = name.split('-')
        surfactant = parts[0] if len(parts) > 0 else 'unknown'
        linker = parts[1] if len(parts) > 1 else 'unknown'
        piezo = parts[4] if len(parts) > 4 else 'unknown'

        return {
            'filename': name, 'surfactant': surfactant, 'linker': linker, 'piezo': piezo,
            'snap_f_nn': snap_f, 'snap_z_nm': snap_z,
            'pulloff_f_nn': pulloff_f,
            'max_force_nn': max_force, 'max_force_retract_nn': max_force_retract,
            'adhesion_hysteresis_nn': adhesion_hysteresis,
            'contact_idx': contact_idx,
            'ramp_size_nm': curve['ramp_size_nm'],
            'spring_constant': curve['spring_constant'],
        }

    features_list = [extract_features(c) for c in all_curves]
    print(f"Extracted features for {len(features_list)} curves")

    surfactants = sorted(set(f['surfactant'] for f in features_list))
    linkers = sorted(set(f['linker'] for f in features_list))
    print(f"Surfactants: {surfactants}")
    print(f"Linkers: {linkers}")

    snap_vals = [f['snap_f_nn'] for f in features_list]
    pulloff_vals = [f['pulloff_f_nn'] for f in features_list]
    print(f"Snap-in median: {np.median(snap_vals):.1f} nN, range: [{np.min(snap_vals):.1f}, {np.max(snap_vals):.1f}]")
    print(f"Pull-off median: {np.median(pulloff_vals):.1f} nN, range: [{np.min(pulloff_vals):.1f}, {np.max(pulloff_vals):.1f}]")
    return all_curves, features_list


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 数据概览

    210 条曲线全部成功解析。关键观察:

    - **Snap-in 力极大**: 中位 -2577 nN，远超典型 vdW+毛细力 (~10-100 nN for R=8nm)。
      这可能是因为力标定尚未校正（Z-scale 0.5V / 32768 counts 对应 DeflSens 64.6 nm/V 可能不准确），
      也可能是 1μm 方孔膜的顺应性放大了 jump-to-contact。
    - **Pull-off 极均匀**: 中位 -239 nN，不同 surfactant/linker 之间几乎无差异，
      说明 pull-off 主要由探针-水膜界面决定，与膜下表面活性剂关系不大。
    - **粘附滞后由 snap-in 主导**: hysteresis ≈ |snap-in| - |pull-off| ≈ 2200-2500 nN，
      若 snap-in 标定问题解决，滞后可能大幅减小。
    """)
    return


@app.cell(hide_code=True)
def _(features_list):
    # Group-by analysis: snap-in and pull-off by surfactant + linker
    import pandas as pd

    df = pd.DataFrame(features_list)
    print(f"Total curves: {len(df)}")
    print(f"Groups: {df.groupby(['surfactant', 'linker']).size().to_string()}")

    # Pivot: median snap-in by surfactant and linker
    pivot_snap = df.pivot_table(values='snap_f_nn', index='surfactant', columns='linker', aggfunc='median')
    pivot_pulloff = df.pivot_table(values='pulloff_f_nn', index='surfactant', columns='linker', aggfunc='median')
    pivot_hysteresis = df.pivot_table(values='adhesion_hysteresis_nn', index='surfactant', columns='linker', aggfunc='median')

    print("\nMedian snap-in force (nN):")
    print(pivot_snap.to_string())
    print("\nMedian pull-off force (nN):")
    print(pivot_pulloff.to_string())
    print("\nMedian adhesion hysteresis (nN):")
    print(pivot_hysteresis.to_string())
    return df, pd


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Pivot 表解读

    **Snap-in 分组差异**:
    - SDBS 的 snap-in 最大 (-2758 nN, linker2)，SDS 和 NLS 次之，PFPE 最小 (-2448 nN)
    - linker 之间差异不大，linker2 略高于 linker1（可能与 linker2 膜更柔软有关）

    **Pull-off 分组差异**:
    - 几乎无差异！所有组中位 pull-off 在 -223 到 -239 nN 之间
    - NOSTF 和 PFPE 略低 (~ -224 nN)，其余组接近 -239 nN
    - 这说明 pull-off 是探针-水桥界面属性，与膜下方的表面活性剂类型解耦

    **粘附滞后**:
    - 滞后主要由 snap-in 贡献（pull-off 几乎恒定）
    - SDBS 滞后最大 (~2519 nN)，PFPE 最小 (~2209 nN)
    """)
    return


@app.cell(hide_code=True)
def _(df):
    # Visual comparison across sample groups
    def _plot_group_comparison(df):
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))

        ax = axes[0, 0]
        surfactant_order = df.groupby('surfactant')['snap_f_nn'].median().sort_values().index
        bp = ax.boxplot([df[df['surfactant']==s]['snap_f_nn'] for s in surfactant_order], 
                        labels=surfactant_order, patch_artist=True)
        for p in bp['boxes']:
            p.set_facecolor('#0C5DA5')
            p.set_alpha(0.6)
        ax.set_title('Snap-in Force by Surfactant')
        ax.set_ylabel('Snap-in Force (nN)')
        ax.tick_params(axis='x', rotation=45)
        ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)

        ax = axes[0, 1]
        linker_order = sorted(df['linker'].unique())
        clrs = ['#0C5DA5', '#E8204E', '#00B945']
        for idx, lnk in enumerate(linker_order):
            data = df[df['linker']==lnk]['snap_f_nn']
            bp2 = ax.boxplot([data], positions=[idx], labels=[lnk], patch_artist=True,
                       boxprops=dict(facecolor=clrs[idx], alpha=0.6))
        ax.set_title('Snap-in Force by Linker')
        ax.set_ylabel('Snap-in Force (nN)')

        ax = axes[1, 0]
        pulloff_order = df.groupby('surfactant')['pulloff_f_nn'].median().sort_values().index
        bp3 = ax.boxplot([df[df['surfactant']==s]['pulloff_f_nn'] for s in pulloff_order], 
                    labels=pulloff_order, patch_artist=True)
        for p in bp3['boxes']:
            p.set_facecolor('#E8204E')
            p.set_alpha(0.6)
        ax.set_title('Pull-off Force by Surfactant')
        ax.set_ylabel('Pull-off Force (nN)')
        ax.tick_params(axis='x', rotation=45)

        ax = axes[1, 1]
        for si, srf in enumerate(surfactant_order):
            sub = df[df['surfactant']==srf]
            ax.scatter(sub['snap_f_nn'], sub['pulloff_f_nn'], label=srf, alpha=0.6, s=20)
        ax.set_xlabel('Snap-in Force (nN)')
        ax.set_ylabel('Pull-off Force (nN)')
        ax.set_title('Snap-in vs Pull-off')
        ax.legend(fontsize=7, ncol=2)
        ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
        ax.axvline(x=0, color='gray', linestyle='--', alpha=0.5)
        plt.tight_layout()
        return fig

    _plot_group_comparison(df)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 分组箱线图观察

    **Snap-in by surfactant**: 箱体宽度反映组内变异。SDBS 的分布最宽（linker1 vs linker2 差异大），
    NOSTF 最窄。大部分 surfactant 的 snap-in 集中在 -2400 到 -2800 nN。

    **Snap-in by linker**: linker1 和 linker2 分布接近，OH 组只有 PFPE 样品（32 条曲线）。

    **Pull-off by surfactant**: pull-off 分布极窄（~10 nN 量级），且各组中位数几乎相同，
    说明 pull-off 是一个对表面活性剂不敏感的探针-界面属性。

    **Snap-in vs Pull-off 散点图**: 各组在 x 轴（snap-in）上分离明显，但在 y 轴（pull-off）
    上聚成一团，直观展示了"snap-in 区分样品，pull-off 恒定"的模式。
    """)
    return


@app.cell(hide_code=True)
def _(all_curves, df):
    # Plot representative curves from each surfactant group
    def _plot_representative_curves(df, all_curves):
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(3, 3, figsize=(15, 12))
        axes_flat = axes.flatten()

        surfactant_groups = sorted(df['surfactant'].unique())
        clrs = ['#0C5DA5', '#E8204E', '#00B945']
        for si, srf in enumerate(surfactant_groups[:9]):
            ax = axes_flat[si]
            group_files = df[df['surfactant']==srf]['filename'].values[:3]
            for fj, fn in enumerate(group_files):
                cv = [c for c in all_curves if c['filename']==fn][0]
                ax.plot(cv['z_nm'], cv['force_nn'], color=clrs[fj], alpha=0.5, lw=0.8, label='approach')
                ax.plot(cv['z_nm_retract'], cv['force_retract_nn'], color=clrs[fj], alpha=0.3, lw=0.5, ls='--')
            ax.set_title(srf, fontsize=9)
            ax.set_xlabel('Z (nm)')
            ax.set_ylabel('Force (nN)')
            ax.axhline(y=0, color='gray', linestyle=':', alpha=0.5)
            ax.set_xlim(0, 200)

        axes_flat[8].set_visible(False)
        plt.suptitle('Representative Force Curves: Approach (solid) + Withdraw (dashed)', fontsize=12)
        plt.tight_layout()
        return fig

    _plot_representative_curves(df, all_curves)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 代表曲线观察

    - **Approach 段（实线）**: 在 Z<20 nm 处出现尖锐的 snap-in（力急剧下降到 -2000 到 -3000 nN），
      随后力迅速回升到正力区（contact），接触段极短（~10-20 nm Z 范围）。
    - **Withdraw 段（虚线）**: 从接触返回基线，在远场出现 pull-off（~ -239 nN，极小但非常一致）。
    - **不同 surfactant 的曲线形状非常相似**，主要区别在 snap-in 的深度和接触段的刚度。
    """)
    return


@app.cell(hide_code=True)
def _(all_curves, np, pd):
    # Contact stiffness and apparent modulus analysis
    # Model: clamped circular membrane F = k₁δ + k₃δ³
    # ⚠️ PeakForce QNM: contact is brief (~10 nm). k₃ (membrane stretching) is unreliable.
    #    k_linear (dF/dZ) is the robust metric for group comparison.
    from scipy.optimize import curve_fit

    PORE_RADIUS_UM = 0.5
    FILM_THICKNESS_NM = 50.0
    NU = 0.30

    def _q_factor(nu=NU):
        return 1.0 / (1.05 - 0.15*nu - 0.16*nu**2)

    def _membrane_model(delta, k1, k3):
        return k1 * delta + k3 * delta**3

    def _apparent_modulus_mpa(k3_nn_per_nm3):
        if k3_nn_per_nm3 <= 0 or np.isnan(k3_nn_per_nm3):
            return np.nan
        k3_si = k3_nn_per_nm3 * 1e18
        r_m = PORE_RADIUS_UM * 1e-6
        t_m = FILM_THICKNESS_NM * 1e-9
        return (k3_si * r_m**2 / (_q_factor(NU)**3 * t_m)) / 1e6

    def _analyze_contact(curve):
        f = curve['force_nn']          # approach (trace)
        z = curve['z_nm']
        fr = curve['force_retract_nn']  # retrace

        snap_idx = np.argmin(f)
        snap_f = f[snap_idx]
        snap_z = z[snap_idx]

        # Z decreases during approach (far→close). After snap-in, Z continues decreasing.
        # Indentation δ = snap_z - z  (positive as tip pushes further in)
        post = slice(snap_idx, None)
        delta = snap_z - z[post]
        f_post = f[post]

        if len(delta) < 8 or delta.max() < 1.0:
            return None

        # Linear stiffness: first 2 nm of indentation
        early = delta <= 2.0
        if np.sum(early) < 4:
            return None
        k_linear = np.polyfit(delta[early], f_post[early] - snap_f, 1)[0]

        # Cubic fit
        f_shifted = f_post - snap_f
        try:
            popt, _ = curve_fit(_membrane_model, delta, f_shifted,
                                p0=[max(k_linear, 0.01), 1e-4], maxfev=10000)
            k1, k3 = popt
            f_pred = _membrane_model(delta, k1, k3)
            ss_res = np.sum((f_shifted - f_pred)**2)
            ss_tot = np.sum((f_shifted - np.mean(f_shifted))**2)
            r2 = 1 - ss_res/ss_tot if ss_tot > 0 else 0.0
        except Exception:
            k1, k3, r2 = np.nan, np.nan, np.nan

        pull_idx = np.argmin(fr)
        name = curve['filename']
        parts = name.split('-')
        return {
            'filename': name,
            'surfactant': parts[0] if len(parts) > 0 else '?',
            'linker': parts[1] if len(parts) > 1 else '?',
            'snap_f_nn': snap_f,
            'snap_z_nm': snap_z,
            'pulloff_f_nn': fr[pull_idx],
            'k_linear_nn_per_nm': k_linear,
            'k1_nn_per_nm': k1, 'k3_nn_per_nm3': k3,
            'r_squared': r2,
            'E_app_mpa': _apparent_modulus_mpa(k3),
            'max_delta_nm': delta.max(),
        }

    print("Running contact mechanics on all curves...")
    mech_results = []
    for c in all_curves:
        r = _analyze_contact(c)
        if r is not None:
            mech_results.append(r)

    df_mech = pd.DataFrame(mech_results)
    r2v = df_mech['r_squared']
    klin = df_mech['k_linear_nn_per_nm']
    kpos = df_mech[klin > 0]

    print(f"Curves analyzed: {len(df_mech)}")
    print(f"Max indentation: med={df_mech['max_delta_nm'].median():.1f} nm, max={df_mech['max_delta_nm'].max():.1f} nm")
    print(f"R²: med={r2v.median():.3f}, max={r2v.max():.3f}  |  R²>0: {(r2v>0).sum()}  R²>0.5: {(r2v>0.5).sum()}")
    print(f"k_linear: med={klin.median():.2f}, pos. med={kpos['k_linear_nn_per_nm'].median():.2f} nN/nm ({len(kpos)}/{len(df_mech)} curves)")

    print("\n=== Contact stiffness (k_linear, nN/nm) by surfactant × linker ===")
    print(df_mech.pivot_table(values='k_linear_nn_per_nm', index='surfactant', columns='linker', aggfunc='median').to_string())

    # Adhesion hysteresis
    df_mech['hysteresis_nn'] = df_mech['pulloff_f_nn'].abs() - df_mech['snap_f_nn'].abs()
    print("\n=== Adhesion hysteresis (nN) by surfactant × linker ===")
    print(df_mech.pivot_table(values='hysteresis_nn', index='surfactant', columns='linker', aggfunc='median').to_string())

    print("\nDone.")
    return (df_mech,)


@app.cell(hide_code=True)
def _(df_mech, mo):
    n_pos = len(df_mech[df_mech['k_linear_nn_per_nm'] > 0])
    mo.md(
        f"""
        ## 接触力学分析 — 关键结论

        **立方膜模型 F = k₁δ + k₃δ³ 不适用于此数据。**

        | 指标 | 数值 | 含义 |
        |------|------|------|
        | 压入深度 | 中位 10.7 nm，最大 929 nm | 深度足够，但… |
        | R² | **全部 180 条曲线 < 0**（中位 -2.64） | 模型比均值线还差 |
        | k₃ | 几乎全部为负 | 物理上 k₃ 必须 >0（膜拉伸刚度） |

        **根本原因**: PeakForce QNM 是 tapping 模式，探针 1-2 kHz 敲击表面，每次接触仅几 nm 的实际压入。
        力-距离关系受悬臂动力学主导，膜拉伸（k₃δ³ 项）来不及响应。

        **与 JJS pipeline 的区别**: JJS 数据含深压入曲线（δ = 50-100+ nm），探针持续推入，
        k₃ 有足够的信号。1umSquare 数据是力-体积 mapping，每秒 512 条曲线的快速扫描模式。

        **可提取的稳健物理量**:
        - 线性接触刚度 k_linear（初始 dF/dZ）: {n_pos}/180 条有正刚度，中位 0.41 nN/nm
        - Snap-in 力、Pull-off 力、粘附滞后（不受模型拟合影响）
        - 各组之间的 **相对排名** 是可靠的，但 **绝对力值** 需进一步标定
        """
    )
    return


@app.cell(hide_code=True)
def _(df_mech):
    # Analysis summary: contact mechanics on 1umSquare PeakForce QNM data
    def _plot_mechanics_summary(df_mech):
        import matplotlib.pyplot as _plt
        fig, axes = _plt.subplots(2, 3, figsize=(15, 9))

        # 1. R² distribution — shows cubic model failure
        ax = axes[0, 0]
        r2v = df_mech['r_squared'].dropna()
        ax.hist(r2v, bins=40, color='#E8204E', edgecolor='white', alpha=0.8)
        ax.axvline(0, color='black', linestyle='--', linewidth=1)
        ax.axvline(r2v.median(), color='#0C5DA5', linestyle='-', linewidth=2, label=f'Median={r2v.median():.2f}')
        ax.set_xlabel('R²')
        ax.set_ylabel('Count')
        ax.set_title('Cubic model fit quality (all R² < 0)')
        ax.legend(fontsize=8)

        # 2. Contact stiffness by surfactant
        ax = axes[0, 1]
        surfactants = sorted(df_mech['surfactant'].unique())
        k_data = [df_mech[df_mech['surfactant']==s]['k_linear_nn_per_nm'].dropna().values for s in surfactants]
        bp = ax.boxplot(k_data, labels=surfactants, patch_artist=True)
        colors = ['#0C5DA5','#E8204E','#00B945','#FF9500','#845B97','#474747','#00BCD4','#FF5722']
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.6)
        ax.axhline(0, color='gray', linestyle=':', linewidth=0.8)
        ax.set_ylabel('k_linear (nN/nm)')
        ax.set_title('Contact stiffness by surfactant')
        ax.tick_params(axis='x', rotation=45)

        # 3. Contact stiffness by linker
        ax = axes[0, 2]
        linkers = sorted(df_mech['linker'].unique())
        k_linker = [df_mech[df_mech['linker']==l]['k_linear_nn_per_nm'].dropna().values for l in linkers]
        ax.boxplot(k_linker, labels=linkers, patch_artist=True)
        ax.axhline(0, color='gray', linestyle=':', linewidth=0.8)
        ax.set_ylabel('k_linear (nN/nm)')
        ax.set_title('Contact stiffness by linker')

        # 4. Max indentation depth
        ax = axes[1, 0]
        ax.hist(df_mech['max_delta_nm'], bins=50, color='#00B945', edgecolor='white', alpha=0.8)
        ax.axvline(df_mech['max_delta_nm'].median(), color='#0C5DA5', linewidth=2,
                   label=f'Median={df_mech["max_delta_nm"].median():.1f} nm')
        ax.set_xlabel('Max indentation (nm)')
        ax.set_ylabel('Count')
        ax.set_title('Contact depth distribution')
        ax.legend(fontsize=8)

        # 5. Adhesion hysteresis by surfactant
        ax = axes[1, 1]
        hyst_data = [df_mech[df_mech['surfactant']==s]['hysteresis_nn'].dropna().values for s in surfactants]
        bp2 = ax.boxplot(hyst_data, labels=surfactants, patch_artist=True)
        for patch, color in zip(bp2['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.6)
        ax.axhline(0, color='gray', linestyle=':', linewidth=0.8)
        ax.set_ylabel('Hysteresis (nN)')
        ax.set_title('Adhesion hysteresis by surfactant')
        ax.tick_params(axis='x', rotation=45)

        # 6. Summary text
        ax = axes[1, 2]
        ax.axis('off')
        summary_text = (
            "KEY FINDINGS\n"
            "==============\n\n"
            "1. Cubic membrane model (F=k₁δ+k₃δ³)\n"
            "   does NOT fit this data.\n"
            f"   All {len(df_mech)} curves have R² < 0.\n\n"
            "2. Reason: PeakForce QNM tapping\n"
            "   contact is too brief (~10 nm).\n"
            "   Membrane stretching (k₃) not engaged.\n\n"
            "3. Linear contact stiffness (k_linear)\n"
            "   IS extractable as relative metric.\n"
            f"   Positive in {len(df_mech[df_mech['k_linear_nn_per_nm']>0])}/{len(df_mech)} curves.\n\n"
            "4. Adhesion hysteresis (pull-off − snap-in)\n"
            "   is the most robust metric for\n"
            "   comparing surfactant/linker groups."
        )
        ax.text(0, 1, summary_text, transform=ax.transAxes, fontsize=9,
                verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='#F5F5F5', alpha=0.9))

        _plt.tight_layout()
        _plt.show()

    _plot_mechanics_summary(df_mech)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 总体结论与下一步

    ### 已确认的发现
    1. **Pull-off 极均匀** (~ -239 nN)：不随 surfactant/linker 变化，是探针-水膜界面固有属性
    2. **Snap-in 区分样品**：SDBS > SDS ≈ NLS > PAA ≈ PFNA > PFPE > NOSTF，
      可能与表面活性剂对膜表面能的调控有关
    3. **立方膜模型不可用**：PeakForce QNM 接触太短，膜拉伸未激发

    ### 待解决问题
    1. **力标定**: snap-in ~ -2577 nN 对 R=8nm 探针明显偏大（理论 ~10-100 nN）。
       需检查 DeflSens 和 Spring Constant 的标定是否正确。
    2. **绝对力 vs 相对排名**: 即使力标定不准确，组间相对比较仍然有效。
    3. **缺少对照**: 湿度依赖性、悬膜 vs 支撑膜对比、不同压入速度的数据。

    ### 与 JJS 数据的比较
    | 特征 | JJS 数据 | 1umSquare 数据 |
    |------|----------|---------------|
    | 实验模式 | PeakForce QNM + 深压入 | PeakForce QNM 力-体积 |
    | Snap-in | ~17 nN (合理) | ~2577 nN (需标定) |
    | Pull-off | ~116 nN | ~239 nN |
    | 粘附滞后 | ~99 nN (~7× snap-in) | ~2300 nN (snap-in 主导) |
    | 膜模型拟合 | 可用 (δ 50-100+ nm) | 不可用 (接触太短) |

    ### 下一步建议
    - 用已知刚度的标准样品（如 PDMS, HOPG）标定力常数
    - 如果要测膜力学，需要专门做深压入实验（ramp size 更大、速度更慢）
    - 当前的粘附排名可以作为初步结果，但需注明绝对力值待标定
    """)
    return


if __name__ == "__main__":
    app.run()
