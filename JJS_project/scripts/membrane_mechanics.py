# -*- coding: utf-8 -*-
"""
悬浮薄膜力学参数反推（JJS 系列批量分析）
基于圆形薄膜中心点载荷模型

关键修正：NanoScope Analysis 文件按 z 从大到小存储（倒序接近曲线），
需反转后再分析。

可靠性约束（v2 增加）：
- repulsive 数据点 ≥ 5
- 接触后压入深度 ≥ 3 nm
- 实测斜率 k_meas 不得超过悬臂刚度的 60%（避免串联公式发散）
- 预应力 σ₀ 物理合理范围 0.1–1000 MPa（聚合物典型值）
- Hamaker A 合理范围 1e-21–1e-18 J
"""
import sys, json, numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from parser import AFMForceCurve, load_all_curves

# 物理参数
R_PROBE = 8.0          # 探针半径 nm
T_FILM = 10.0          # 薄膜厚度 nm
A_HOLE = 10_000.0      # 孔半径 nm (20 um diameter)
K_CANTILEVER = 7.0     # RTESPA-150 悬臂刚度 N/m (标称值)
POISSON = 0.25         # 泊松比假设

# 可靠性阈值
MIN_REP_POINTS = 5
MIN_DELTA_NM = 3.0
K_MEAS_MAX_FRAC = 0.6  # k_meas 不得超过 0.6*k_c
SIGMA_MIN_MPA = 0.1
SIGMA_MAX_MPA = 2000.0
HAMAKER_MIN = 1e-21
HAMAKER_MAX = 1e-18


def analyze_JJS(z_raw, f_raw, label=""):
    """
    分析单条 JJS 曲线
    z_raw: 原始 z 数组（文件存储顺序，从大到小）
    f_raw: 原始力数组
    """
    warnings = []
    
    # 1. 反转数据：使 z 从小到大 = 物理接近过程 (far-end -> contact)
    z = z_raw[::-1].copy()
    f = f_raw[::-1].copy()
    
    # 2. 基线校正：在 z∈[0, 100] nm 远场区拟合
    mask_far = (z >= 0) & (z <= 100)
    n_far = int(np.sum(mask_far))
    if n_far >= 5:
        coeffs = np.polyfit(z[mask_far], f[mask_far], 1)
        a, b = coeffs[0], coeffs[1]
        f_corr = f - (a * z + b)
        baseline_method = "linear"
    elif n_far >= 3:
        offset = np.mean(f[mask_far])
        f_corr = f - offset
        a, b = 0.0, offset
        baseline_method = "const"
    else:
        f_corr = f
        a, b = 0.0, 0.0
        baseline_method = "none"
        warnings.append("insufficient_far_end")
    
    # 3. 检测 snap-in: 最小力（最负值）
    snap_idx = int(np.argmin(f_corr))
    snap_z = float(z[snap_idx])
    snap_f = float(f_corr[snap_idx])
    
    # 4. 检测接触点: snap-in 之后第一个 F >= 0 的点
    after_snap = np.arange(snap_idx + 1, len(z))
    contact_candidates = after_snap[f_corr[after_snap] >= 0]
    if len(contact_candidates) > 0:
        contact_idx = int(contact_candidates[0])
        contact_z = float(z[contact_idx])
        contact_f = float(f_corr[contact_idx])
    else:
        contact_idx = len(z) - 1
        contact_z = float(z[-1])
        contact_f = float(f_corr[-1])
        warnings.append("no_contact_found")
    
    # 5. 接触后段 (F >= 0 且 z >= contact_z)
    rep_mask = (z >= contact_z) & (f_corr >= 0)
    n_rep = int(np.sum(rep_mask))
    
    # 压入深度计算
    if n_rep >= 2:
        rep_z = z[rep_mask]
        rep_f = f_corr[rep_mask]
        delta_raw = rep_z - contact_z  # nm
        probe_deflection_nm = rep_f / (K_CANTILEVER * 1e3)  # nN / (N/m * 1000) = nm
        delta = delta_raw - probe_deflection_nm
        max_delta = float(np.max(delta))
        max_rep_f = float(np.max(rep_f))
    else:
        max_delta = 0.0
        max_rep_f = 0.0
        delta = np.array([])
    
    # 可靠性检查 #1: repulsive 点数
    if n_rep < MIN_REP_POINTS:
        warnings.append(f"too_few_repulsive_points({n_rep})")
    
    # 可靠性检查 #2: 压入深度
    if max_delta < MIN_DELTA_NM:
        warnings.append(f"insufficient_indentation({max_delta:.1f}nm)")
    
    # 6. 反推预应力 sigma_0
    if n_rep >= 3:
        k_meas_nN_per_nm = float(np.polyfit(z[rep_mask], f_corr[rep_mask], 1)[0])
    else:
        k_meas_nN_per_nm = 0.0
    
    k_meas = k_meas_nN_per_nm  # N/m (因为 nN/nm = N/m)
    
    # 可靠性检查 #3: 斜率不能超过悬臂刚度太多
    if k_meas >= K_CANTILEVER * K_MEAS_MAX_FRAC:
        warnings.append(f"k_meas_near_kc({k_meas:.3f}/{K_CANTILEVER})")
    
    # 串联公式：k_meas = k_c * k_m / (k_c + k_m)
    if 0 < k_meas < K_CANTILEVER:
        k_m = (K_CANTILEVER * k_meas) / (K_CANTILEVER - k_meas)
    else:
        k_m = 0.0
        if k_meas > 0:
            warnings.append("k_meas_exceeds_kc")
    
    # Hertzian 接触半径估算 (假设 E_eff ~ 1 GPa)
    E_eff_guess = 1e9
    F_mean_N = abs(np.mean(f_corr[snap_idx:contact_idx])) * 1e-9 if contact_idx > snap_idx else 1e-9
    r_c = ((3 * F_mean_N * R_PROBE * 1e-9) / (4 * E_eff_guess)) ** (1/3) * 1e9
    r_c = max(r_c, 1.0)  # 不小于 1 nm
    
    if k_m > 0:
        sigma_0 = k_m * np.log(A_HOLE / r_c) / (2 * np.pi * T_FILM * 1e-9)
    else:
        sigma_0 = 0.0
    
    # 可靠性检查 #4: sigma_0 物理合理范围
    if sigma_0 > 0:
        if sigma_0 / 1e6 < SIGMA_MIN_MPA:
            warnings.append(f"sigma_too_low({sigma_0/1e6:.3f}MPa)")
        if sigma_0 / 1e6 > SIGMA_MAX_MPA:
            warnings.append(f"sigma_too_high({sigma_0/1e6:.1f}MPa)")
    
    # 7. Hamaker 常数 (DMT + snap-in 判据)
    k_eff = (K_CANTILEVER * k_m) / (K_CANTILEVER + k_m) if k_m > 0 else 0.0
    d_c = 0.4e-9  # 临界距离 0.4 nm (含吸附层)
    A = (3 * k_eff * d_c**3) / (R_PROBE * 1e-9) if k_eff > 0 else 0.0
    
    # 可靠性检查 #5: Hamaker 范围
    if A > 0:
        if A < HAMAKER_MIN:
            warnings.append(f"Hamaker_too_low({A:.2e})")
        if A > HAMAKER_MAX:
            warnings.append(f"Hamaker_too_high({A:.2e})")
    
    # 综合可靠性评级
    if len(warnings) == 0:
        reliability = "high"
    elif any("too_few" in w or "insufficient" in w or "no_contact" in w for w in warnings):
        reliability = "low"
    elif any("sigma_too_high" in w or "Hamaker_too_high" in w or "k_meas_near" in w for w in warnings):
        reliability = "low"
    else:
        reliability = "medium"
    
    return {
        "label": label,
        "baseline_slope": float(a),
        "baseline_intercept": float(b),
        "baseline_method": baseline_method,
        "snap_z_nm": snap_z,
        "snap_f_nN": snap_f,
        "contact_z_nm": contact_z,
        "contact_f_nN": contact_f,
        "repulsive_points": n_rep,
        "k_meas_N_m": float(k_meas),
        "k_m_N_m": float(k_m),
        "sigma_0_Pa": float(sigma_0),
        "sigma_0_MPa": float(sigma_0 / 1e6),
        "r_contact_nm": float(r_c),
        "Hamaker_J": float(A),
        "d_c_nm": float(d_c * 1e9),
        "k_eff_N_m": float(k_eff),
        "max_delta_nm": max_delta,
        "max_repulsive_f_nN": max_rep_f,
        "delta_over_t": float(max_delta / T_FILM) if max_delta > 0 else 0.0,
        "warnings": warnings,
        "reliability": reliability,
        "raw_z": z.tolist(),
        "raw_f_corr": f_corr.tolist(),
    }


def plot_JJS_comparison(results, outdir="figures"):
    """生成 JJS 跨样品对比图"""
    Path(outdir).mkdir(exist_ok=True)
    
    # 图 1: 力曲线叠加（反转+基线校正后）
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # 按位移分组
    groups = {
        "454/500nm": [r for r in results if r["label"].split("-")[2] in ("454nm", "500nm")],
        "1000nm": [r for r in results if "1000nm" in r["label"]],
        "1500nm": [r for r in results if "1500nm" in r["label"]],
    }
    
    colors = plt.cm.tab10(np.linspace(0, 1, len(results)))
    
    for ax, (gname, grp) in zip(axes.flat, groups.items()):
        for r in grp:
            z = np.array(r["raw_z"])
            f = np.array(r["raw_f_corr"])
            ax.plot(z, f, label=r["label"].split("-")[-1].replace("nN", "").replace(".txt", ""), linewidth=1.2)
        ax.axhline(0, color='black', linestyle='--', linewidth=0.8)
        ax.set_xlabel("Z Position (nm)")
        ax.set_ylabel("Force (nN)")
        ax.set_title(f"JJS {gname} (Baseline-Corrected)", fontweight='bold')
        ax.legend(loc='best', fontsize=8)
        ax.grid(True, alpha=0.3)
    
    # 第4个: 对齐到 snap-in
    ax = axes.flat[3]
    for i, r in enumerate(results):
        z = np.array(r["raw_z"])
        f = np.array(r["raw_f_corr"])
        z_align = z - r["snap_z_nm"]
        ax.plot(z_align, f, color=colors[i], alpha=0.7, linewidth=1.2)
    ax.axhline(0, color='black', linestyle='--', linewidth=0.8)
    ax.set_xlabel("Relative Z (nm)")
    ax.set_ylabel("Force (nN)")
    ax.set_title("JJS All Curves Aligned at Snap-in", fontweight='bold')
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(f"{outdir}/C1_JJS_mechanics_overview.png", dpi=200, bbox_inches='tight')
    plt.close(fig)
    print("Saved C1_JJS_mechanics_overview.png")
    
    # 图 2: 参数对比柱状图（仅显示 reliable 数据）
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    reliable = [r for r in results if r["reliability"] != "low"]
    labels = [r["label"].replace("JJS-50nm-", "").replace(" - NanoScope Analysis.txt", "") for r in reliable]
    x = np.arange(len(labels))
    
    # sigma_0
    ax = axes[0, 0]
    vals = [r["sigma_0_MPa"] for r in reliable]
    colors_bar = ['steelblue' if r["reliability"]=="high" else 'lightblue' for r in reliable]
    bars = ax.bar(x, vals, color=colors_bar, edgecolor='black')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=8)
    ax.set_ylabel("Pre-stress (MPa)")
    ax.set_title("Pre-stress σ₀ (reliable samples)", fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    for bar, v in zip(bars, vals):
        if v > 0:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(), f"{v:.1f}", ha='center', va='bottom', fontsize=7)
    
    # k_m
    ax = axes[0, 1]
    vals = [r["k_m_N_m"] * 1000 for r in reliable]  # mN/m
    bars = ax.bar(x, vals, color=colors_bar, edgecolor='black')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=8)
    ax.set_ylabel("Membrane stiffness (mN/m)")
    ax.set_title("Film stiffness k_m", fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    for bar, v in zip(bars, vals):
        if v > 0:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(), f"{v:.1f}", ha='center', va='bottom', fontsize=7)
    
    # Hamaker
    ax = axes[1, 0]
    vals = [r["Hamaker_J"] * 1e19 for r in reliable]  # 10^-19 J
    bars = ax.bar(x, vals, color=colors_bar, edgecolor='black')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=8)
    ax.set_ylabel("Hamaker constant (×10⁻¹⁹ J)")
    ax.set_title("Hamaker Constant A", fontweight='bold')
    ax.axhline(4.0, color='red', linestyle='--', linewidth=1, label="Typical polymer (~4e-19 J)")
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    
    # 可靠性分布饼图
    ax = axes[1, 1]
    rel_counts = {"high": 0, "medium": 0, "low": 0}
    for r in results:
        rel_counts[r["reliability"]] += 1
    ax.pie(rel_counts.values(), labels=[f"{k} (n={v})" for k, v in rel_counts.items()], 
           autopct='%1.0f%%', startangle=90, colors=['#2ca02c', '#ffbb78', '#d62728'])
    ax.set_title("Reliability Distribution", fontweight='bold')
    
    fig.tight_layout()
    fig.savefig(f"{outdir}/C2_JJS_parameters_comparison.png", dpi=200, bbox_inches='tight')
    plt.close(fig)
    print("Saved C2_JJS_parameters_comparison.png")
    
    # 图 3: 散点相关性（仅 reliable）
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    # sigma_0 vs snap-in force
    ax = axes[0]
    xvals = [abs(r["snap_f_nN"]) for r in reliable]
    yvals = [r["sigma_0_MPa"] for r in reliable]
    colors2 = ['red' if '454nm' in r["label"] or '500nm' in r["label"] else 'blue' if '1000nm' in r["label"] else 'green' for r in reliable]
    ax.scatter(xvals, yvals, c=colors2, s=100, edgecolors='black', zorder=5)
    for r in reliable:
        ax.annotate(r["label"].split("-")[2], (abs(r["snap_f_nN"]), r["sigma_0_MPa"]), fontsize=7, ha='center', va='bottom')
    ax.set_xlabel("|Snap-in force| (nN)")
    ax.set_ylabel("Pre-stress σ₀ (MPa)")
    ax.set_title("σ₀ vs Snap-in Force (reliable)", fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    # sigma_0 vs displacement
    ax = axes[1]
    def extract_disp(label):
        parts = label.split("-")
        for p in parts:
            if "nm" in p:
                return float(p.replace("nm", ""))
        return 0
    xvals = [extract_disp(r["label"]) for r in reliable]
    yvals = [r["sigma_0_MPa"] for r in reliable]
    ax.scatter(xvals, yvals, c=colors2, s=100, edgecolors='black', zorder=5)
    ax.set_xlabel("Piezo displacement (nm)")
    ax.set_ylabel("Pre-stress σ₀ (MPa)")
    ax.set_title("σ₀ vs Displacement (reliable)", fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    fig.tight_layout()
    fig.savefig(f"{outdir}/C3_JJS_correlations.png", dpi=200, bbox_inches='tight')
    plt.close(fig)
    print("Saved C3_JJS_correlations.png")


def main():
    root = Path(__file__).parent.parent
    curves = load_all_curves(root)
    results = []
    
    for rel, c in sorted(curves.items()):
        if 'JJS' not in rel:
            continue
        z_raw = np.array(c.z, dtype=float)
        f_raw = np.array(c.force, dtype=float)
        if c.z_unit in ('um', 'μm'):
            z_raw = z_raw * 1000.0
        
        res = analyze_JJS(z_raw, f_raw, label=rel)
        results.append(res)
        warn_str = ", ".join(res['warnings']) if res['warnings'] else "OK"
        print(f"{rel.split('\\')[-1]}: reliability={res['reliability']}, sigma_0={res['sigma_0_MPa']:.3f} MPa, k_m={res['k_m_N_m']:.4f} N/m, A={res['Hamaker_J']:.2e} J, rep_pts={res['repulsive_points']}, warnings=[{warn_str}]")
    
    # 保存 JSON
    out = root / 'results' / 'membrane_parameters.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    # 去掉 raw 数组以减小文件
    save_results = []
    for r in results:
        sr = {k: v for k, v in r.items() if k not in ('raw_z', 'raw_f_corr')}
        save_results.append(sr)
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(save_results, f, ensure_ascii=False, indent=2)
    print(f"\nSaved {out}")
    
    # 生成图
    plot_JJS_comparison(results, outdir=str(root / 'figures'))
    
    # 打印统计（仅 reliable 样本）
    reliable = [r for r in results if r["reliability"] != "low"]
    print(f"\n=== STATISTICS (reliable n={len(reliable)}/{len(results)}) ===")
    if reliable:
        sigmas = [r['sigma_0_MPa'] for r in reliable if r['sigma_0_MPa'] > 0]
        ks = [r['k_m_N_m'] for r in reliable if r['k_m_N_m'] > 0]
        As = [r['Hamaker_J'] for r in reliable if r['Hamaker_J'] > 0]
        if sigmas:
            print(f"sigma_0: {np.mean(sigmas):.3f} +/- {np.std(sigmas):.3f} MPa (n={len(sigmas)})")
        if ks:
            print(f"k_m: {np.mean(ks):.4f} +/- {np.std(ks):.4f} N/m (n={len(ks)})")
        if As:
            print(f"Hamaker A: {np.mean(As):.2e} +/- {np.std(As):.2e} J (n={len(As)})")
    else:
        print("No reliable samples found.")
    
    # 打印 low-reliability 样本明细
    low_rel = [r for r in results if r["reliability"] == "low"]
    if low_rel:
        print(f"\n=== LOW RELIABILITY SAMPLES (n={len(low_rel)}) ===")
        for r in low_rel:
            print(f"  {r['label'].split('\\')[-1]}: warnings={r['warnings']}")


if __name__ == '__main__':
    main()
