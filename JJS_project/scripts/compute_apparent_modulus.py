#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Model-dependent apparent modulus analysis for deep-indentation AFM curves.

This script intentionally works downstream of stitch_deep_indentation.py. It
uses the stitched loading curves as an analysis view, keeps raw force columns
untouched, and reports relative/comparative membrane mechanics rather than an
intrinsic Young's modulus.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from dataset_registry import get_config  # noqa: E402


RESULTS_DIR = ROOT / "results" / "realraw"
REPORT_DIR = ROOT / "reports" / "realraw" / "apparent_modulus"
MECHANICS_CSV = RESULTS_DIR / "deep_stitched_mechanics.csv"
POINTS_CSV = RESULTS_DIR / "deep_stitched_points.csv"

DEFAULT_INCLUDE_DATES = (20260415, 20260416)
DEFAULT_NU = 0.30
DEFAULT_THICKNESS_NM = 50.0
DEFAULT_THICKNESS_MAX_NM = 80.0
DEFAULT_PORE_DIAMETER_UM = 20.0
DEFAULT_MIN_R2 = 0.85
DEFAULT_MIN_FIT_POINTS = 8

COLORS = {
    "linker1-paa": "#FF9500",
    "linker2-paa": "#00B945",
    "k80-linker1-PFNA": "#0C5DA5",
    "k80-linker1-SDBS": "#845B97",
    "k80-linker1-paa": "#E8204E",
    "k80-linker2-paa": "#00B945",
}


def q_factor(nu: float = DEFAULT_NU) -> float:
    """Dimensionless clamped circular membrane factor."""
    return 1.0 / (1.05 - 0.15 * nu - 0.16 * nu**2)


def k3_nN_nm3_to_N_m3(k3_nN_per_nm3: float | np.ndarray | pd.Series) -> float | np.ndarray:
    """Convert cubic force coefficient from nN/nm^3 to N/m^3."""
    return np.asarray(k3_nN_per_nm3, dtype=float) * 1e18


def apparent_modulus_pa(
    k3_nN_per_nm3: float | np.ndarray | pd.Series,
    pore_radius_um: float = DEFAULT_PORE_DIAMETER_UM / 2.0,
    thickness_nm: float = DEFAULT_THICKNESS_NM,
    nu: float = DEFAULT_NU,
) -> float | np.ndarray:
    """Compute model-dependent E_app from F = k1*d + k3*d^3."""
    k3_si = k3_nN_nm3_to_N_m3(k3_nN_per_nm3)
    pore_radius_m = pore_radius_um * 1e-6
    thickness_m = thickness_nm * 1e-9
    return k3_si * pore_radius_m**2 / (q_factor(nu) ** 3 * thickness_m)


def apparent_modulus_mpa(
    k3_nN_per_nm3: float | np.ndarray | pd.Series,
    pore_radius_um: float = DEFAULT_PORE_DIAMETER_UM / 2.0,
    thickness_nm: float = DEFAULT_THICKNESS_NM,
    nu: float = DEFAULT_NU,
) -> float | np.ndarray:
    """Compute model-dependent E_app in MPa."""
    return apparent_modulus_pa(k3_nN_per_nm3, pore_radius_um, thickness_nm, nu) / 1e6


def k3_from_apparent_modulus_mpa(
    e_app_mpa: float,
    pore_radius_um: float = DEFAULT_PORE_DIAMETER_UM / 2.0,
    thickness_nm: float = DEFAULT_THICKNESS_NM,
    nu: float = DEFAULT_NU,
) -> float:
    """Inverse of apparent_modulus_mpa, useful for tests and calibration."""
    pore_radius_m = pore_radius_um * 1e-6
    thickness_m = thickness_nm * 1e-9
    k3_si = e_app_mpa * 1e6 * q_factor(nu) ** 3 * thickness_m / pore_radius_m**2
    return float(k3_si / 1e18)


def fit_membrane_terms(delta_nm: np.ndarray, force_nN: np.ndarray) -> dict[str, float]:
    """Least-squares fit for F = k1*d + k3*d^3 using nm and nN units."""
    x = np.asarray(delta_nm, dtype=float)
    y = np.asarray(force_nN, dtype=float)
    keep = np.isfinite(x) & np.isfinite(y) & (x > 0)
    x = x[keep]
    y = y[keep]
    if len(x) < 3 or np.ptp(x) <= 0:
        return {"k1_N_m": np.nan, "k3_nN_per_nm3": np.nan, "r2": np.nan}
    design = np.column_stack([x, x**3])
    coeffs, *_ = np.linalg.lstsq(design, y, rcond=None)
    pred = design @ coeffs
    ss_res = float(np.sum((y - pred) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else np.nan
    return {
        "k1_N_m": float(coeffs[0]),
        "k3_nN_per_nm3": float(coeffs[1]),
        "r2": float(r2) if np.isfinite(r2) else np.nan,
    }


def dataset_params(date: int) -> dict[str, float | str]:
    """Read probe and film defaults from the RealRaw dataset registry."""
    try:
        cfg = get_config(f"RealRaw/{int(date)}")
    except KeyError:
        cfg = {}
    pore_diameter_um = float(cfg.get("pore_diameter_um", DEFAULT_PORE_DIAMETER_UM))
    return {
        "probe_model": cfg.get("probe_model", "unknown"),
        "probe_radius_nm": float(cfg.get("probe_radius_nm", np.nan)),
        "registry_film_thickness_nm": float(cfg.get("film_thickness_nm", DEFAULT_THICKNESS_NM)),
        "pore_diameter_um": pore_diameter_um,
        "pore_radius_um": pore_diameter_um / 2.0,
    }


def filter_analysis_rows(
    mechanics_df: pd.DataFrame,
    include_dates: tuple[int, ...] = DEFAULT_INCLUDE_DATES,
    include_jjs: bool = False,
) -> pd.DataFrame:
    """Default to non-JJS deep indentation mechanics only."""
    df = mechanics_df.copy()
    df["date"] = df["date"].astype(int)
    if not include_jjs:
        df = df[df["date"] != 20260409]
        df = df[~df["group"].astype(str).str.contains("JJS", case=False, na=False)]
    if include_dates:
        df = df[df["date"].isin([int(d) for d in include_dates])]
    return df.reset_index(drop=True)


def curve_warnings(row: pd.Series, valid: bool, min_r2: float, min_fit_points: int) -> str:
    warnings: list[str] = []
    if not np.isfinite(row.get("membrane_k3_nN_per_nm3", np.nan)):
        warnings.append("missing_k3")
    elif float(row["membrane_k3_nN_per_nm3"]) <= 0:
        warnings.append("negative_or_zero_k3")
    if not np.isfinite(row.get("membrane_r2", np.nan)) or float(row["membrane_r2"]) < min_r2:
        warnings.append("low_membrane_r2")
    if not np.isfinite(row.get("fit_points", np.nan)) or int(row["fit_points"]) < min_fit_points:
        warnings.append("too_few_fit_points")
    if int(row.get("n_slip_events", 0)) > 0:
        warnings.append("stitched_recoverable_slip")
    if int(row.get("date", 0)) == 20260416:
        warnings.append("blunt_tip_comparative_scope")
    if not valid and not warnings:
        warnings.append("invalid_model")
    return "|".join(warnings)


def build_curve_table(
    mechanics_df: pd.DataFrame,
    include_dates: tuple[int, ...] = DEFAULT_INCLUDE_DATES,
    include_jjs: bool = False,
    thickness_nm: float = DEFAULT_THICKNESS_NM,
    thickness_max_nm: float = DEFAULT_THICKNESS_MAX_NM,
    nu: float = DEFAULT_NU,
    min_r2: float = DEFAULT_MIN_R2,
    min_fit_points: int = DEFAULT_MIN_FIT_POINTS,
) -> pd.DataFrame:
    df = filter_analysis_rows(mechanics_df, include_dates=include_dates, include_jjs=include_jjs)
    if df.empty:
        return df

    param_rows = [dataset_params(int(d)) for d in df["date"]]
    params = pd.DataFrame(param_rows)
    df = pd.concat([df.reset_index(drop=True), params.reset_index(drop=True)], axis=1)
    df["thickness_assumed_nm"] = float(thickness_nm)
    df["thickness_sensitivity_max_nm"] = float(thickness_max_nm)
    df["poisson_ratio"] = float(nu)
    df["q_factor"] = q_factor(nu)
    df["k3_SI_N_per_m3"] = k3_nN_nm3_to_N_m3(df["membrane_k3_nN_per_nm3"])

    valid = (
        np.isfinite(df["membrane_k3_nN_per_nm3"])
        & (df["membrane_k3_nN_per_nm3"] > 0)
        & np.isfinite(df["membrane_r2"])
        & (df["membrane_r2"] >= min_r2)
        & np.isfinite(df["fit_points"])
        & (df["fit_points"] >= min_fit_points)
    )
    df["valid_model"] = valid
    df["E_app_MPa"] = np.where(
        valid,
        apparent_modulus_mpa(df["membrane_k3_nN_per_nm3"], df["pore_radius_um"], thickness_nm, nu),
        np.nan,
    )
    df["E_app_50nm_MPa"] = np.where(
        valid,
        apparent_modulus_mpa(df["membrane_k3_nN_per_nm3"], df["pore_radius_um"], 50.0, nu),
        np.nan,
    )
    df["E_app_80nm_MPa"] = np.where(
        valid,
        apparent_modulus_mpa(df["membrane_k3_nN_per_nm3"], df["pore_radius_um"], 80.0, nu),
        np.nan,
    )

    pore_radius_m = df["pore_radius_um"].astype(float) * 1e-6
    probe_radius_m = df["probe_radius_nm"].astype(float) * 1e-9
    ln_ratio = np.log(pore_radius_m / probe_radius_m)
    thickness_m = thickness_nm * 1e-9
    df["T_app_N_m"] = np.where(
        valid,
        df["membrane_k1_N_m"].astype(float) * ln_ratio / (2 * np.pi),
        np.nan,
    )
    df["sigma_app_MPa"] = df["T_app_N_m"] / thickness_m / 1e6
    df["legacy_log_corrected_E_MPa"] = np.where(
        valid,
        df["k3_SI_N_per_m3"] * pore_radius_m**2 * (1.0 - nu) * ln_ratio / (np.pi * thickness_m) / 1e6,
        np.nan,
    )
    df["qc_warnings"] = [curve_warnings(row, bool(v), min_r2, min_fit_points) for (_, row), v in zip(df.iterrows(), valid)]
    return df


def q1(x: pd.Series) -> float:
    return float(x.quantile(0.25)) if len(x.dropna()) else np.nan


def q3(x: pd.Series) -> float:
    return float(x.quantile(0.75)) if len(x.dropna()) else np.nan


def summarize_groups(curves: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    if curves.empty:
        return pd.DataFrame(rows)
    metrics = [
        "E_app_MPa",
        "E_app_50nm_MPa",
        "E_app_80nm_MPa",
        "high_stiffness_N_m",
        "low_stiffness_N_m",
        "stiffening_ratio",
        "power_law_n",
        "membrane_r2",
        "T_app_N_m",
        "sigma_app_MPa",
        "legacy_log_corrected_E_MPa",
        "fit_delta_max_nm",
        "fit_force_max_nN",
    ]
    for (date, group), g in curves.groupby(["date", "group"], dropna=False):
        valid = g[g["valid_model"]].copy()
        row = {
            "date": int(date),
            "group": group,
            "sample": g["sample"].dropna().iloc[0] if g["sample"].notna().any() else "",
            "linker": g["linker"].dropna().iloc[0] if g["linker"].notna().any() else "",
            "surfactant": g["surfactant"].dropna().iloc[0] if g["surfactant"].notna().any() else "",
            "probe_model": g["probe_model"].dropna().iloc[0] if g["probe_model"].notna().any() else "",
            "probe_radius_nm": float(g["probe_radius_nm"].dropna().iloc[0]) if g["probe_radius_nm"].notna().any() else np.nan,
            "pore_radius_um": float(g["pore_radius_um"].dropna().iloc[0]) if g["pore_radius_um"].notna().any() else np.nan,
            "thickness_assumed_nm": float(g["thickness_assumed_nm"].dropna().iloc[0]),
            "n_curves": int(len(g)),
            "n_valid_model": int(len(valid)),
            "valid_model_fraction": float(len(valid) / len(g)) if len(g) else np.nan,
        }
        for metric in metrics:
            s = valid[metric].replace([np.inf, -np.inf], np.nan).dropna()
            row[f"{metric}_median"] = float(s.median()) if len(s) else np.nan
            row[f"{metric}_q1"] = q1(s)
            row[f"{metric}_q3"] = q3(s)
        warnings = []
        if len(valid) < 3:
            warnings.append("low_N")
        invalid_count = len(g) - len(valid)
        if invalid_count:
            warnings.append(f"invalid_models={invalid_count}")
        if int(g.get("n_slip_events", pd.Series(dtype=float)).fillna(0).sum()) > 0:
            warnings.append("contains_stitched_slip")
        if int(date) == 20260416:
            warnings.append("compare_within_k80_only")
        row["qc_warnings"] = "|".join(warnings)
        rows.append(row)
    summary = pd.DataFrame(rows)
    if not summary.empty:
        summary = summary.sort_values(["date", "E_app_MPa_median"], ascending=[True, False], na_position="last")
    return summary


def save_csv_outputs(curves: pd.DataFrame, summary: pd.DataFrame) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    curves.to_csv(RESULTS_DIR / "apparent_modulus_curves.csv", index=False)
    summary.to_csv(RESULTS_DIR / "apparent_modulus_group_summary.csv", index=False)


def _valid_k80(curves: pd.DataFrame) -> pd.DataFrame:
    return curves[(curves["date"] == 20260416) & (curves["valid_model"])].copy()


def plot_k80_boxplot(curves: pd.DataFrame, outpath: Path) -> None:
    df = _valid_k80(curves)
    if df.empty:
        return
    groups = df.groupby("group")["E_app_MPa"].median().sort_values(ascending=False).index.tolist()
    data = [df[df["group"] == g]["E_app_MPa"].dropna().to_numpy(float) for g in groups]
    fig, ax = plt.subplots(figsize=(7.6, 4.8))
    bp = ax.boxplot(data, tick_labels=groups, patch_artist=True, showfliers=False)
    for patch, group in zip(bp["boxes"], groups):
        patch.set_facecolor(COLORS.get(group, "#777777"))
        patch.set_alpha(0.55)
    for i, group in enumerate(groups, start=1):
        vals = df[df["group"] == group]["E_app_MPa"].dropna().to_numpy(float)
        jitter = np.linspace(-0.08, 0.08, len(vals)) if len(vals) else []
        ax.scatter(np.full(len(vals), i) + jitter, vals, s=24, color=COLORS.get(group, "#555555"), edgecolor="white", linewidth=0.4)
    ax.set_yscale("log")
    ax.set_ylabel("Model-dependent E_app (MPa, t=50 nm)")
    ax.set_title("k80 surfactant comparison: apparent membrane modulus")
    ax.tick_params(axis="x", rotation=25)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(outpath, dpi=240)
    plt.close(fig)


def plot_stiffness_vs_modulus(curves: pd.DataFrame, outpath: Path) -> None:
    df = _valid_k80(curves)
    if df.empty:
        return
    fig, ax = plt.subplots(figsize=(6.5, 4.8))
    for group, g in df.groupby("group"):
        ax.scatter(
            g["high_stiffness_N_m"],
            g["E_app_MPa"],
            s=42,
            color=COLORS.get(group, "#555555"),
            alpha=0.8,
            label=group,
            edgecolor="white",
            linewidth=0.4,
        )
    ax.set_yscale("log")
    ax.set_xlabel("High-force apparent stiffness (N/m)")
    ax.set_ylabel("Model-dependent E_app (MPa)")
    ax.set_title("Stiffness tracks apparent membrane modulus")
    ax.legend(frameon=False, fontsize=7)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(outpath, dpi=240)
    plt.close(fig)


def plot_thickness_sensitivity(summary: pd.DataFrame, outpath: Path) -> None:
    df = summary[(summary["date"] == 20260416) & (summary["n_valid_model"] > 0)].copy()
    if df.empty:
        return
    df = df.sort_values("E_app_50nm_MPa_median", ascending=False)
    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    y = np.arange(len(df))
    left = df["E_app_80nm_MPa_median"].to_numpy(float)
    right = df["E_app_50nm_MPa_median"].to_numpy(float)
    ax.hlines(y, left, right, color="#777777", lw=2)
    ax.scatter(left, y, color="#777777", s=36, label="t=80 nm")
    ax.scatter(right, y, color="#111111", s=36, label="t=50 nm")
    ax.set_xscale("log")
    ax.set_yticks(y)
    ax.set_yticklabels(df["group"])
    ax.invert_yaxis()
    ax.set_xlabel("E_app median (MPa)")
    ax.set_title("Thickness sensitivity of apparent modulus")
    ax.legend(frameon=False)
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    fig.savefig(outpath, dpi=240)
    plt.close(fig)


def plot_model_fit_examples(curves: pd.DataFrame, points: pd.DataFrame, outpath: Path) -> None:
    valid = curves[curves["valid_model"]].copy()
    if valid.empty or points.empty:
        return
    examples = []
    for _, g in valid.groupby("group"):
        med = g["E_app_MPa"].median()
        idx = (g["E_app_MPa"] - med).abs().sort_values().index[0]
        examples.append(valid.loc[idx])
    examples = sorted(examples, key=lambda r: (int(r["date"]), str(r["group"])))[:6]
    if not examples:
        return
    ncols = 2
    nrows = int(np.ceil(len(examples) / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(10, 3.2 * nrows), squeeze=False)
    axes = axes.ravel()
    for ax, row in zip(axes, examples):
        pts = points[(points["curve_id"] == row["curve_id"]) & (points["used_for_fit"])].copy()
        pts = pts[(pts["delta_nm"] > 0) & (pts["stitched_force_nN"] > 0)]
        if pts.empty:
            ax.axis("off")
            continue
        x = pts["delta_nm"].to_numpy(float)
        y_fit = row["membrane_k1_N_m"] * x + row["membrane_k3_nN_per_nm3"] * x**3
        ax.plot(x, pts["stitched_force_nN"], color="#888888", lw=1.0, label="stitched loading")
        ax.plot(x, y_fit, color=COLORS.get(row["group"], "#E8204E"), lw=1.4, label="membrane fit")
        ax.set_title(f"{row['group']} E_app={row['E_app_MPa']:.2g} MPa", fontsize=8)
        ax.set_xlabel("Indentation (nm)")
        ax.set_ylabel("Force (nN)")
        ax.grid(alpha=0.2)
    for ax in axes[len(examples) :]:
        ax.axis("off")
    axes[0].legend(frameon=False, fontsize=7)
    fig.tight_layout()
    fig.savefig(outpath, dpi=240)
    plt.close(fig)


def plot_mechanics_ranking(summary: pd.DataFrame, outpath: Path) -> None:
    df = summary[(summary["date"] == 20260416) & (summary["n_valid_model"] > 0)].copy()
    if df.empty:
        return
    df = df.sort_values("E_app_MPa_median")
    fig, axes = plt.subplots(1, 2, figsize=(10.2, 4.6))
    axes[0].barh(df["group"], df["E_app_MPa_median"], color=[COLORS.get(g, "#777777") for g in df["group"]])
    axes[0].set_xscale("log")
    axes[0].set_xlabel("Median E_app (MPa, t=50 nm)")
    axes[0].set_title("Apparent modulus ranking")
    axes[0].grid(axis="x", alpha=0.25)
    axes[1].barh(df["group"], df["high_stiffness_N_m_median"], color=[COLORS.get(g, "#777777") for g in df["group"]])
    axes[1].set_xlabel("Median high-force stiffness (N/m)")
    axes[1].set_title("Measured loading stiffness")
    axes[1].grid(axis="x", alpha=0.25)
    fig.tight_layout()
    fig.savefig(outpath, dpi=240)
    plt.close(fig)


def write_plots(curves: pd.DataFrame, summary: pd.DataFrame, points: pd.DataFrame) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    plot_k80_boxplot(curves, REPORT_DIR / "k80_surfactant_Eapp_boxplot.png")
    plot_stiffness_vs_modulus(curves, REPORT_DIR / "k80_surfactant_stiffness_vs_Eapp.png")
    plot_thickness_sensitivity(summary, REPORT_DIR / "thickness_sensitivity_Eapp.png")
    plot_model_fit_examples(curves, points, REPORT_DIR / "model_fit_examples.png")
    plot_mechanics_ranking(summary, REPORT_DIR / "surfactant_mechanics_ranking.png")


def fmt(value: float, digits: int = 3) -> str:
    if not np.isfinite(value):
        return "NA"
    if abs(value) >= 100:
        return f"{value:.0f}"
    if abs(value) >= 10:
        return f"{value:.1f}"
    return f"{value:.{digits}g}"


def markdown_table(df: pd.DataFrame, columns: list[tuple[str, str]]) -> str:
    if df.empty:
        return "No valid groups.\n"
    header = "| " + " | ".join(label for _, label in columns) + " |"
    sep = "| " + " | ".join("---" for _ in columns) + " |"
    lines = [header, sep]
    for _, row in df.iterrows():
        vals = []
        for col, _ in columns:
            val = row.get(col, "")
            if isinstance(val, (float, np.floating)):
                vals.append(fmt(float(val)))
            else:
                vals.append(str(val))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines) + "\n"


def write_report(curves: pd.DataFrame, summary: pd.DataFrame) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    k80 = summary[(summary["date"] == 20260416) & (summary["n_valid_model"] > 0)].copy()
    k80 = k80.sort_values("E_app_MPa_median", ascending=False)
    ref = summary[summary["date"] == 20260415].copy()
    leader = k80.iloc[0]["group"] if not k80.empty else "NA"
    leader_e = float(k80.iloc[0]["E_app_MPa_median"]) if not k80.empty else np.nan
    second_e = float(k80.iloc[1]["E_app_MPa_median"]) if len(k80) > 1 else np.nan
    ratio = leader_e / second_e if np.isfinite(leader_e) and np.isfinite(second_e) and second_e > 0 else np.nan

    text = f"""# Deep Indentation Apparent Modulus Report

## Scope

This analysis excludes JJS, snap-in, pull-off, adhesion, and confined-water interpretation. It uses only stitched deep-indentation extend/loading curves from `20260415` and `20260416`.

The reported modulus is a model-dependent apparent Young's modulus for relative comparison, not an intrinsic material constant.

## Model

The loading branch is fitted as:

```text
F = k1 * delta + k3 * delta^3
E_app = k3 * a^2 / (q^3 * t)
q = 1 / (1.05 - 0.15 nu - 0.16 nu^2)
```

Defaults: pore diameter = 20 um, pore radius `a` = 10 um, `nu` = 0.30, main thickness `t` = 50 nm. The 80 nm column shows the thickness sensitivity; because `E_app` scales as `1/t`, the 80 nm value is 0.625x the 50 nm value.

## Main k80 Ranking

Within the same `20260416` DDESP-V2/k80 probe set, `{leader}` has the highest median apparent modulus. Its median `E_app` is `{fmt(leader_e)} MPa`, about `{fmt(ratio, 2)}x` the next strongest valid k80 group.

{markdown_table(k80, [
    ("group", "group"),
    ("n_valid_model", "N valid"),
    ("E_app_50nm_MPa_median", "E_app 50 nm MPa"),
    ("E_app_80nm_MPa_median", "E_app 80 nm MPa"),
    ("high_stiffness_N_m_median", "high-k N/m"),
    ("power_law_n_median", "power n"),
    ("membrane_r2_median", "fit R2"),
    ("qc_warnings", "QC"),
])}

## 20260415 Reference

The `20260415` RTESPA-150 data are kept as a same-workflow reference, but they should not be ranked directly against k80 because probe radius and force range differ.

{markdown_table(ref, [
    ("group", "group"),
    ("n_valid_model", "N valid"),
    ("E_app_50nm_MPa_median", "E_app 50 nm MPa"),
    ("E_app_80nm_MPa_median", "E_app 80 nm MPa"),
    ("high_stiffness_N_m_median", "high-k N/m"),
    ("power_law_n_median", "power n"),
    ("membrane_r2_median", "fit R2"),
    ("qc_warnings", "QC"),
])}

## Interpretation

- Use the k80 ranking as the strongest surfactant comparison because probe, cantilever, and force range are internally consistent.
- `E_app`, `T_app`, and `sigma_app` are comparative quantities. Their absolute values depend on assumed film thickness, pore radius, boundary condition, and the stitched loading reconstruction.
- Groups with `low_N` or invalid model fits should be treated as screening-level evidence only.
"""
    (REPORT_DIR / "apparent_modulus_report.md").write_text(text, encoding="utf-8")


def run(args: argparse.Namespace) -> tuple[pd.DataFrame, pd.DataFrame]:
    mechanics = pd.read_csv(args.mechanics_csv)
    points = pd.read_csv(args.points_csv) if Path(args.points_csv).exists() else pd.DataFrame()
    include_dates = tuple(int(d) for d in args.include_date) if args.include_date else DEFAULT_INCLUDE_DATES
    curves = build_curve_table(
        mechanics,
        include_dates=include_dates,
        include_jjs=args.include_jjs,
        thickness_nm=args.thickness_nm,
        thickness_max_nm=args.thickness_max_nm,
        nu=args.poisson,
        min_r2=args.min_r2,
        min_fit_points=args.min_fit_points,
    )
    summary = summarize_groups(curves)
    save_csv_outputs(curves, summary)
    write_plots(curves, summary, points)
    write_report(curves, summary)
    manifest = {
        "curve_rows": int(len(curves)),
        "group_rows": int(len(summary)),
        "include_dates": list(include_dates),
        "include_jjs": bool(args.include_jjs),
        "thickness_nm": float(args.thickness_nm),
        "thickness_sensitivity_max_nm": float(args.thickness_max_nm),
        "poisson_ratio": float(args.poisson),
        "min_r2": float(args.min_r2),
        "min_fit_points": int(args.min_fit_points),
        "note": "E_app is model-dependent and comparative, not intrinsic Young's modulus.",
    }
    (RESULTS_DIR / "apparent_modulus_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote {RESULTS_DIR / 'apparent_modulus_curves.csv'}")
    print(f"Wrote {RESULTS_DIR / 'apparent_modulus_group_summary.csv'}")
    print(f"Wrote {REPORT_DIR / 'apparent_modulus_report.md'}")
    print(f"Wrote figures to {REPORT_DIR}")
    return curves, summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute model-dependent apparent modulus from stitched deep indentation curves.")
    parser.add_argument("--all", action="store_true", help="Analyze default non-JJS deep indentation datasets.")
    parser.add_argument("--mechanics-csv", default=str(MECHANICS_CSV))
    parser.add_argument("--points-csv", default=str(POINTS_CSV))
    parser.add_argument("--include-date", action="append", help="Date to include; defaults to 20260415 and 20260416.")
    parser.add_argument("--include-jjs", action="store_true", help="Include 20260409/JJS for diagnostic use.")
    parser.add_argument("--thickness-nm", type=float, default=DEFAULT_THICKNESS_NM)
    parser.add_argument("--thickness-max-nm", type=float, default=DEFAULT_THICKNESS_MAX_NM)
    parser.add_argument("--poisson", type=float, default=DEFAULT_NU)
    parser.add_argument("--min-r2", type=float, default=DEFAULT_MIN_R2)
    parser.add_argument("--min-fit-points", type=int, default=DEFAULT_MIN_FIT_POINTS)
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
