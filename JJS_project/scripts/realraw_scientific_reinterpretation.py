#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scientific reinterpretation of branch-aware RealRaw AFM results.

This script rewrites the scientific narrative after separating extend
(approach/loading) from retract (unloading/pull-off). It deliberately keeps the
new outputs separate from the historical JJS report.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results" / "realraw"
REPORT_DIR = ROOT / "reports" / "realraw" / "scientific_reinterpretation"

PAIR_CSV = RESULTS_DIR / "pair_features.csv"
CURVE_CSV = RESULTS_DIR / "curve_features.csv"

A_HAMAKER_J = 4e-19
D0_M = 0.3e-9
GAMMA_N_M = 72e-3
HBAR_C_J_M = 1.98644586e-25
ETA_CP = 0.4

COLORS = {
    "extend": "#0C5DA5",
    "retract": "#E8204E",
    "theory": "#474747",
    "work": "#00B945",
    "warn": "#FF9500",
}


def theory_for_radius(radius_nm: float) -> dict[str, float]:
    radius_m = radius_nm * 1e-9
    f_vdw = A_HAMAKER_J * radius_m / (12 * D0_M**2) * 1e9
    f_cap = 4 * np.pi * radius_m * GAMMA_N_M * 1e9
    f_cp = (np.pi**3 * HBAR_C_J_M * radius_m / (360 * D0_M**3)) * ETA_CP * 1e9
    return {
        "radius_nm": radius_nm,
        "F_vdW_nN": float(f_vdw),
        "F_capillary_nN": float(f_cap),
        "F_vdW_plus_capillary_nN": float(f_vdw + f_cap),
        "F_Casimir_Polder_formal_nN": float(f_cp),
    }


def group_label(row: pd.Series) -> str:
    sample = row.get("sample")
    linker = row.get("linker")
    surfactant = row.get("surfactant")
    if isinstance(sample, str) and sample == "JJS":
        return "JJS"
    parts = [x for x in (sample, linker, surfactant) if isinstance(x, str) and x and x != "nan"]
    if len(parts) >= 3 and parts[0] == parts[1]:
        parts = [parts[0], parts[2]]
    return "-".join(parts) if parts else "unknown"


def robust_stats(values: pd.Series | np.ndarray) -> dict[str, float | int]:
    vals = pd.to_numeric(pd.Series(values), errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    if vals.empty:
        return {"n": 0, "mean": np.nan, "std": np.nan, "median": np.nan, "q25": np.nan, "q75": np.nan, "min": np.nan, "max": np.nan}
    return {
        "n": int(len(vals)),
        "mean": float(vals.mean()),
        "std": float(vals.std(ddof=1)) if len(vals) > 1 else np.nan,
        "median": float(vals.median()),
        "q25": float(vals.quantile(0.25)),
        "q75": float(vals.quantile(0.75)),
        "min": float(vals.min()),
        "max": float(vals.max()),
    }


def fmt(value: float, digits: int = 1) -> str:
    if value is None or pd.isna(value):
        return "NA"
    return f"{value:.{digits}f}"


def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    pair = pd.read_csv(PAIR_CSV)
    curve = pd.read_csv(CURVE_CSV)
    pair["group"] = pair.apply(group_label, axis=1)
    curve["group"] = curve.apply(group_label, axis=1)
    pair["abs_extend_snap_nN"] = pair["extend_snap_f_nN"].abs()
    pair["abs_retract_pull_off_nN"] = pair["retract_pull_off_f_nN"].abs()
    pair["pull_to_snap_ratio"] = pair["abs_retract_pull_off_nN"] / pair["abs_extend_snap_nN"].replace(0, np.nan)
    curve["abs_snap_nN"] = curve["snap_f_nN"].abs()
    curve["abs_pull_off_nN"] = curve["pull_off_f_nN"].abs()
    return pair, curve


def build_group_summary(pair: pd.DataFrame, curve: pd.DataFrame) -> pd.DataFrame:
    valid_curve = curve[curve["valid"] == True].copy()  # noqa: E712
    rows = []
    for (date, group), grp in pair.groupby(["date", "group"], sort=True):
        ext_valid = valid_curve[(valid_curve["date"] == date) & (valid_curve["group"] == group) & (valid_curve["branch"] == "extend")]
        ret_valid = valid_curve[(valid_curve["date"] == date) & (valid_curve["group"] == group) & (valid_curve["branch"] == "retract")]
        ext_stats = robust_stats(grp["abs_extend_snap_nN"])
        ret_stats = robust_stats(grp["abs_retract_pull_off_nN"])
        ratio_stats = robust_stats(grp["pull_to_snap_ratio"])
        work_stats = robust_stats(grp["hysteresis_work_nN_nm"])
        ext_valid_stats = robust_stats(ext_valid["abs_snap_nN"])
        ret_valid_stats = robust_stats(ret_valid["abs_pull_off_nN"])
        rows.append(
            {
                "date": int(date),
                "group": group,
                "n_pairs": int(len(grp)),
                "extend_snap_median_nN": ext_stats["median"],
                "extend_snap_iqr_low_nN": ext_stats["q25"],
                "extend_snap_iqr_high_nN": ext_stats["q75"],
                "retract_pull_off_median_nN": ret_stats["median"],
                "retract_pull_off_iqr_low_nN": ret_stats["q25"],
                "retract_pull_off_iqr_high_nN": ret_stats["q75"],
                "pull_to_snap_ratio_median": ratio_stats["median"],
                "hysteresis_work_median_nN_nm": work_stats["median"],
                "valid_extend_n": ext_valid_stats["n"],
                "valid_extend_snap_median_nN": ext_valid_stats["median"],
                "valid_retract_n": ret_valid_stats["n"],
                "valid_retract_pull_off_median_nN": ret_valid_stats["median"],
            }
        )
    return pd.DataFrame(rows)


def build_extractability_table() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "category": "Can extract robustly",
                "quantity": "Approach attraction scale",
                "evidence": "extend branch minimum force after branch-aware baseline correction",
                "interpretation": "vdW + capillary + modest dynamic/interface enhancement",
            },
            {
                "category": "Can extract robustly",
                "quantity": "Pull-off adhesion",
                "evidence": "retract branch minimum force",
                "interpretation": "water bridge/contact-line pinning/adhesion hysteresis",
            },
            {
                "category": "Can extract robustly",
                "quantity": "Hysteresis and sample ranking",
                "evidence": "paired extend/retract work and pull-off ratios",
                "interpretation": "relative confined-water/adhesion strength across chemistries",
            },
            {
                "category": "Semi-quantitative",
                "quantity": "Effective capillary radius or Hamaker upper bound",
                "evidence": "force magnitude mapped onto simple sphere-plane models",
                "interpretation": "diagnostic scale only, not unique microscopic geometry",
            },
            {
                "category": "Not reliable from JJS snap/pull-off",
                "quantity": "Intrinsic Young's modulus, tension, or stress",
                "evidence": "too few post-contact points and shallow indentation",
                "interpretation": "old N/m-scale apparent tension is capillary-water-film coupling, not intrinsic film tension",
            },
            {
                "category": "Not independently separable",
                "quantity": "Solvation force or true water bridge geometry",
                "evidence": "no humidity, dry-N2, KPFM, or probe-radius control series",
                "interpretation": "confined water is a plausible mechanism, not a uniquely fitted component",
            },
        ]
    )


def plot_extend_vs_retract(pair: pd.DataFrame, outpath: Path) -> None:
    fig, ax = plt.subplots(figsize=(7.0, 4.6))
    plot_df = pair.copy()
    order = (
        plot_df.groupby("group")["abs_retract_pull_off_nN"]
        .median()
        .sort_values(ascending=False)
        .index.tolist()
    )
    positions = np.arange(len(order))
    ext = [robust_stats(plot_df[plot_df["group"] == g]["abs_extend_snap_nN"]) for g in order]
    ret = [robust_stats(plot_df[plot_df["group"] == g]["abs_retract_pull_off_nN"]) for g in order]
    width = 0.36
    ax.bar(positions - width / 2, [s["median"] for s in ext], width, color=COLORS["extend"], label="extend snap")
    ax.bar(positions + width / 2, [s["median"] for s in ret], width, color=COLORS["retract"], label="retract pull-off")
    for i, stats in enumerate(ext):
        ax.vlines(i - width / 2, stats["q25"], stats["q75"], color="black", lw=0.8)
    for i, stats in enumerate(ret):
        ax.vlines(i + width / 2, stats["q25"], stats["q75"], color="black", lw=0.8)
    ax.set_yscale("log")
    ax.set_ylabel("Force magnitude (nN, median with IQR)")
    ax.set_xticks(positions)
    ax.set_xticklabels(order, rotation=35, ha="right")
    ax.set_title("Approach attraction vs. retract adhesion")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(outpath)
    plt.close(fig)


def plot_theory_comparison(group_summary: pd.DataFrame, outpath: Path) -> None:
    fig, ax = plt.subplots(figsize=(6.6, 4.4))
    rows = group_summary[group_summary["date"].isin([20260409, 20260415])].copy()
    rows = rows.sort_values("extend_snap_median_nN", ascending=False)
    x = np.arange(len(rows))
    ax.bar(x, rows["extend_snap_median_nN"], color=COLORS["extend"], label="extend median")
    theory = theory_for_radius(8.0)
    ax.axhline(theory["F_vdW_nN"], color="#888888", ls=":", lw=1.2, label="vdW, R=8 nm")
    ax.axhline(theory["F_vdW_plus_capillary_nN"], color=COLORS["theory"], ls="--", lw=1.3, label="vdW + capillary, R=8 nm")
    ax.set_ylabel("Approach attraction magnitude (nN)")
    ax.set_xticks(x)
    ax.set_xticklabels(rows["group"], rotation=35, ha="right")
    ax.set_title("Extend forces are near classic vdW + capillary scale")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(outpath)
    plt.close(fig)


def plot_ratio_work(pair: pd.DataFrame, outpath: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 4.2))
    order = (
        pair.groupby("group")["pull_to_snap_ratio"]
        .median()
        .replace([np.inf, -np.inf], np.nan)
        .dropna()
        .sort_values(ascending=False)
        .index.tolist()
    )
    ratio_stats = [robust_stats(pair[pair["group"] == g]["pull_to_snap_ratio"]) for g in order]
    work_stats = [robust_stats(pair[pair["group"] == g]["hysteresis_work_nN_nm"].abs()) for g in order]
    x = np.arange(len(order))
    axes[0].bar(x, [s["median"] for s in ratio_stats], color=COLORS["retract"])
    axes[0].set_yscale("log")
    axes[0].set_ylabel("Retract / extend force ratio")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(order, rotation=35, ha="right")
    axes[0].set_title("Adhesion hysteresis ratio")
    axes[1].bar(x, [s["median"] for s in work_stats], color=COLORS["work"])
    axes[1].set_yscale("symlog", linthresh=100)
    axes[1].set_ylabel("|paired work difference| (nN nm)")
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(order, rotation=35, ha="right")
    axes[1].set_title("Energy dissipation scale")
    fig.tight_layout()
    fig.savefig(outpath)
    plt.close(fig)


def plot_adhesion_ranking(group_summary: pd.DataFrame, outpath: Path) -> None:
    fig, ax = plt.subplots(figsize=(6.8, 4.4))
    rows = group_summary.sort_values("retract_pull_off_median_nN", ascending=True)
    colors = [COLORS["warn"] if r["date"] == 20260416 else COLORS["retract"] for _, r in rows.iterrows()]
    ax.barh(rows["group"], rows["retract_pull_off_median_nN"], color=colors)
    ax.set_xscale("log")
    ax.set_xlabel("Median retract pull-off magnitude (nN)")
    ax.set_title("Adhesion ranking across chemistries")
    ax.text(
        0.98,
        0.02,
        "orange: k80/DDESP-V2, baseline QC risk",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=8,
        color="#555555",
    )
    fig.tight_layout()
    fig.savefig(outpath)
    plt.close(fig)


def build_markdown(group_summary: pd.DataFrame, pair: pd.DataFrame, curve: pd.DataFrame) -> str:
    theory8 = theory_for_radius(8.0)
    theory100 = theory_for_radius(100.0)
    jjs = group_summary[(group_summary["date"] == 20260409) & (group_summary["group"] == "JJS")].iloc[0]
    jjs_pair = pair[(pair["date"] == 20260409) & (pair["group"] == "JJS")]
    jjs_ratio = robust_stats(jjs_pair["pull_to_snap_ratio"])
    old_mean = 120.7
    effective_a_extend = 12 * D0_M**2 * jjs["extend_snap_median_nN"] * 1e-9 / (8e-9)
    effective_a_retract = 12 * D0_M**2 * jjs["retract_pull_off_median_nN"] * 1e-9 / (8e-9)
    effective_r_cap_extend = jjs["extend_snap_median_nN"] * 1e-9 / (4 * np.pi * GAMMA_N_M) * 1e9
    effective_r_cap_retract = jjs["retract_pull_off_median_nN"] * 1e-9 / (4 * np.pi * GAMMA_N_M) * 1e9

    summary_table = group_summary.copy()
    display_cols = [
        "date",
        "group",
        "n_pairs",
        "extend_snap_median_nN",
        "retract_pull_off_median_nN",
        "pull_to_snap_ratio_median",
        "hysteresis_work_median_nN_nm",
    ]
    table_md = summary_table[display_cols].to_markdown(index=False, floatfmt=".2f")
    qc = pd.read_csv(RESULTS_DIR / "qc_summary.csv").to_markdown(index=False)

    return f"""# RealRaw Branch-Aware Scientific Reinterpretation

Generated from `results/realraw/pair_features.csv` and `results/realraw/curve_features.csv`.

## Executive Summary

The previous JJS narrative treated the large `~{old_mean:.0f} nN` negative force as an approach snap-in anomaly. The RealRaw branch separation changes the scientific interpretation. In the actual `extend` branch, JJS approach attraction is `{fmt(jjs['extend_snap_median_nN'])} nN` median with an IQR of `{fmt(jjs['extend_snap_iqr_low_nN'])}` to `{fmt(jjs['extend_snap_iqr_high_nN'])} nN`. This is close to the classic RTESPA-150 `R=8 nm` estimate: `F_vdW = {fmt(theory8['F_vdW_nN'])} nN`, `F_cap = {fmt(theory8['F_capillary_nN'])} nN`, and `F_vdW + F_cap = {fmt(theory8['F_vdW_plus_capillary_nN'])} nN`.

The large force is instead a retract phenomenon: JJS pull-off is `{fmt(jjs['retract_pull_off_median_nN'])} nN` median with IQR `{fmt(jjs['retract_pull_off_iqr_low_nN'])}` to `{fmt(jjs['retract_pull_off_iqr_high_nN'])} nN`. The median retract/extend force ratio is `{fmt(jjs_ratio['median'])}`. The robust physical picture is therefore water-bridge/contact hysteresis: the approach branch forms contact or a capillary bridge at a near-classical force scale, while the retract branch stretches and pins a confined water/adhesion junction until delayed rupture.

## Revised Physical Interpretation

### 1. van der Waals and capillary force scale

For the sharp RTESPA-150 probe (`R=8 nm`), the nominal sphere-plane estimates are:

- `F_vdW = AR/(12 d0^2) = {fmt(theory8['F_vdW_nN'])} nN`
- `F_cap = 4 pi R gamma = {fmt(theory8['F_capillary_nN'])} nN`
- `F_vdW + F_cap = {fmt(theory8['F_vdW_plus_capillary_nN'])} nN`

JJS extend median `{fmt(jjs['extend_snap_median_nN'])} nN` is only `{fmt(jjs['extend_snap_median_nN'] / theory8['F_vdW_plus_capillary_nN'], 2)}x` the nominal sum. It does not require a 40x Hamaker enhancement. If mapped onto vdW alone, the effective Hamaker constant is `{effective_a_extend:.2e} J`, about `{fmt(effective_a_extend / A_HAMAKER_J, 1)}x` the nominal value; if mapped onto capillarity alone, the effective capillary radius is `{fmt(effective_r_cap_extend)} nm`. These are diagnostic scales, not unique fitted microscopic parameters.

By contrast, mapping the retract median `{fmt(jjs['retract_pull_off_median_nN'])} nN` onto the same simple formulas gives `A_eff = {effective_a_retract:.2e} J` or `R_cap,eff = {fmt(effective_r_cap_retract)} nm`, which is physically a pull-off/contact-line hysteresis signature rather than a pre-contact vdW fit.

### 2. Confined water and adhesion hysteresis

The RealRaw result supports a capillary-confined-water hysteresis model:

- approach attraction is moderate and near the classic vdW + capillary scale;
- after contact/bridge formation, the retract branch has much larger negative force;
- the pull-off/extend ratio is several-fold for JJS and many linker/PAA cases;
- the large negative force should be interpreted as bridge stretching, contact-line pinning, delayed rupture, and possible confined-water structuring.

The data are consistent with confined water contributing to high dissipation and strong adhesion, but they do not independently isolate a solvation-force term. A separate humidity/dry-N2/KPFM/probe-radius series would be needed to separate capillary, electrostatic, and solvation components.

### 3. Sample comparison

The `20260415` linker series has much weaker extend attraction, typically sub-nN to a few nN, while retract pull-off rises to several nN or tens of nN. PAA-containing samples rank higher in adhesion than PFPE-OH/NLS, especially `linker2-PAA`.

The `20260416` k80 series uses a much larger and stiffer DDESP-V2 probe (`R≈100 nm`, `k=89 N/m`). The nominal force scale is correspondingly larger: `F_vdW + F_cap ≈ {fmt(theory100['F_vdW_plus_capillary_nN'])} nN`. However, baseline QC flags are frequent in this dataset, so k80 should be treated as deep-indentation/tip-geometry evidence rather than clean pre-contact force fitting.

### 4. Film mechanics

JJS intrinsic Young's modulus, membrane tension, and stress cannot be reliably extracted from these snap/pull-off branches. The post-contact segment is too short and the indentation depth is too shallow. The old `N/m`-scale apparent tension and hundreds-MPa apparent stress should be reinterpreted as a coupled capillary-water-film apparent stiffness, not as intrinsic film pre-tension.

For membrane mechanics, use only curves with sufficient deep post-contact indentation and analyze them separately from adhesion. This is most plausible for selected 20260415/20260416 curves after QC, cantilever correction, and a model appropriate to the probe radius.

## Group Statistics

{table_md}

## QC Context

{qc}

## What Can and Cannot Be Extracted

{build_extractability_table().to_markdown(index=False)}

## Figures

- `extend_vs_retract_pull_off.pdf`: approach attraction versus retract adhesion.
- `extend_vs_theory.pdf`: extend force compared with classic vdW + capillary scale.
- `hysteresis_ratio_work.pdf`: retract/extend ratio and paired work difference.
- `adhesion_ranking.pdf`: sample-level adhesion ranking.
"""


def write_outputs(group_summary: pd.DataFrame, extractability: pd.DataFrame, markdown: str, payload: dict) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    group_summary.to_csv(RESULTS_DIR / "scientific_reinterpretation_summary.csv", index=False)
    extractability.to_csv(RESULTS_DIR / "extractability_table.csv", index=False)
    (RESULTS_DIR / "scientific_reinterpretation_metrics.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (REPORT_DIR / "realraw_scientific_reinterpretation.md").write_text(markdown, encoding="utf-8")


def run() -> None:
    pair, curve = load_data()
    group_summary = build_group_summary(pair, curve)
    extractability = build_extractability_table()
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    plot_extend_vs_retract(pair, REPORT_DIR / "extend_vs_retract_pull_off.pdf")
    plot_theory_comparison(group_summary, REPORT_DIR / "extend_vs_theory.pdf")
    plot_ratio_work(pair, REPORT_DIR / "hysteresis_ratio_work.pdf")
    plot_adhesion_ranking(group_summary, REPORT_DIR / "adhesion_ranking.pdf")

    jjs = group_summary[(group_summary["date"] == 20260409) & (group_summary["group"] == "JJS")].iloc[0]
    jjs_pair = pair[(pair["date"] == 20260409) & (pair["group"] == "JJS")]
    payload = {
        "theory_R8_nm": theory_for_radius(8.0),
        "theory_R100_nm": theory_for_radius(100.0),
        "jjs": {
            "extend_snap_median_nN": float(jjs["extend_snap_median_nN"]),
            "extend_snap_iqr_nN": [float(jjs["extend_snap_iqr_low_nN"]), float(jjs["extend_snap_iqr_high_nN"])],
            "retract_pull_off_median_nN": float(jjs["retract_pull_off_median_nN"]),
            "retract_pull_off_iqr_nN": [
                float(jjs["retract_pull_off_iqr_low_nN"]),
                float(jjs["retract_pull_off_iqr_high_nN"]),
            ],
            "pull_to_snap_ratio_median": float(robust_stats(jjs_pair["pull_to_snap_ratio"])["median"]),
        },
        "caveat": "20260416 k80 statistics should be interpreted with baseline-QC warnings.",
    }
    markdown = build_markdown(group_summary, pair, curve)
    write_outputs(group_summary, extractability, markdown, payload)
    print(f"Wrote {RESULTS_DIR / 'scientific_reinterpretation_summary.csv'}")
    print(f"Wrote {RESULTS_DIR / 'extractability_table.csv'}")
    print(f"Wrote {RESULTS_DIR / 'scientific_reinterpretation_metrics.json'}")
    print(f"Wrote {REPORT_DIR / 'realraw_scientific_reinterpretation.md'}")
    print(f"Wrote PDF figures under {REPORT_DIR}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate branch-aware RealRaw scientific reinterpretation.")
    parser.parse_args()
    run()


if __name__ == "__main__":
    main()
