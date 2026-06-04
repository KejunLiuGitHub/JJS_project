#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate the A4 Chinese scientific AFM report and publication-sized figures."""

from __future__ import annotations

import json
import math
import os
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

CACHE_ROOT = Path("/tmp/jjs_project_scientific_report_cache")
CACHE_ROOT.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(CACHE_ROOT / "matplotlib"))
os.environ.setdefault("XDG_CACHE_HOME", str(CACHE_ROOT / "xdg"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "realraw"
OUT = ROOT / "reports" / "realraw" / "scientific_report"

PAIR_CSV = RESULTS / "pair_features.csv"
CURVE_CSV = RESULTS / "curve_features.csv"
POINTS_CSV = RESULTS / "deep_stitched_points.csv"
MOD_CURVES_CSV = RESULTS / "apparent_modulus_curves.csv"
MOD_GROUP_CSV = RESULTS / "apparent_modulus_group_summary.csv"
METRICS_JSON = RESULTS / "scientific_reinterpretation_metrics.json"

FIG_DPI = 300


def setup_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": [
                "Hiragino Sans GB",
                "Arial Unicode MS",
                "STHeiti",
                "DejaVu Sans",
            ],
            "axes.unicode_minus": False,
            "figure.dpi": FIG_DPI,
            "savefig.dpi": FIG_DPI,
            "font.size": 11,
            "axes.titlesize": 14,
            "axes.labelsize": 12,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "legend.fontsize": 10,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def read_data() -> dict[str, pd.DataFrame | dict]:
    pair = pd.read_csv(PAIR_CSV)
    curve = pd.read_csv(CURVE_CSV)
    points = pd.read_csv(POINTS_CSV)
    mod_curves = pd.read_csv(MOD_CURVES_CSV)
    mod_group = pd.read_csv(MOD_GROUP_CSV)
    metrics = json.loads(METRICS_JSON.read_text(encoding="utf-8"))

    pair["group"] = pair.apply(force_group_label, axis=1)
    pair["abs_extend_snap_nN"] = pair["extend_snap_f_nN"].abs()
    pair["abs_retract_pull_off_nN"] = pair["retract_pull_off_f_nN"].abs()
    pair["pull_to_snap_ratio"] = pair["abs_retract_pull_off_nN"] / pair[
        "abs_extend_snap_nN"
    ].replace(0, np.nan)
    pair["abs_hysteresis_work_nN_nm"] = pair["hysteresis_work_nN_nm"].abs()

    return {
        "pair": pair,
        "curve": curve,
        "points": points,
        "mod_curves": mod_curves,
        "mod_group": mod_group,
        "metrics": metrics,
    }


def force_group_label(row: pd.Series) -> str:
    sample = str(row.get("sample", "") or "")
    linker = str(row.get("linker", "") or "")
    surfactant = str(row.get("surfactant", "") or "")
    if sample == "JJS":
        return "JJS"
    if sample == "k80":
        return "-".join(x for x in [sample, linker, surfactant] if x and x != "nan")
    return "-".join(x for x in [linker or sample, surfactant] if x and x != "nan")


def fmt(value: float | int | str | None, digits: int = 1) -> str:
    if value is None:
        return "--"
    try:
        if not np.isfinite(float(value)):
            return "--"
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def quantile_text(values: pd.Series, digits: int = 1) -> str:
    vals = pd.to_numeric(values, errors="coerce").dropna()
    if vals.empty:
        return "--"
    med = vals.median()
    q1 = vals.quantile(0.25)
    q3 = vals.quantile(0.75)
    return f"{fmt(med, digits)} [{fmt(q1, digits)}, {fmt(q3, digits)}]"


def savefig(fig: plt.Figure, name: str) -> None:
    fig.tight_layout()
    fig.savefig(OUT / f"{name}.pdf", bbox_inches="tight")
    fig.savefig(OUT / f"{name}.png", bbox_inches="tight")
    plt.close(fig)


def plot_workflow() -> None:
    fig, ax = plt.subplots(figsize=(7.2, 3.3))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    boxes = [
        ("AFM force curves", "approach/loading\nretract/unloading"),
        ("Branch features", "baseline, contact,\nsnap-in, pull-off"),
        ("Deep loading", "slip stitching\npre-rupture window"),
        ("Scientific outputs", "adhesion, hysteresis,\napparent modulus"),
    ]
    x0s = [0.035, 0.28, 0.525, 0.77]
    colors = ["#E8F2FF", "#FFF4E6", "#EAF7EA", "#F2ECFA"]
    for i, ((title, body), x0, color) in enumerate(zip(boxes, x0s, colors, strict=True)):
        patch = FancyBboxPatch(
            (x0, 0.25),
            0.19,
            0.48,
            boxstyle="round,pad=0.02,rounding_size=0.025",
            linewidth=1.2,
            edgecolor="#333333",
            facecolor=color,
        )
        ax.add_patch(patch)
        ax.text(x0 + 0.095, 0.58, title, ha="center", va="center", weight="bold")
        ax.text(x0 + 0.095, 0.40, body, ha="center", va="center", fontsize=10)
        if i < 3:
            ax.add_patch(
                FancyArrowPatch(
                    (x0 + 0.205, 0.49),
                    (x0s[i + 1] - 0.015, 0.49),
                    arrowstyle="-|>",
                    mutation_scale=16,
                    linewidth=1.4,
                    color="#333333",
                )
            )
    ax.text(
        0.5,
        0.88,
        "Branch-aware AFM mechanics workflow",
        ha="center",
        va="center",
        fontsize=14,
        weight="bold",
    )
    savefig(fig, "workflow_scheme")


def plot_approach_theory(metrics: dict) -> None:
    jjs = metrics["jjs"]
    theory = metrics["theory_R8_nm"]
    fig, ax = plt.subplots(figsize=(7.2, 4.5))
    x = np.arange(3)
    values = [
        theory["F_vdW_nN"],
        theory["F_capillary_nN"],
        jjs["extend_snap_median_nN"],
    ]
    yerr = [
        [0.0, 0.0, jjs["extend_snap_median_nN"] - jjs["extend_snap_iqr_nN"][0]],
        [0.0, 0.0, jjs["extend_snap_iqr_nN"][1] - jjs["extend_snap_median_nN"]],
    ]
    colors = ["#808080", "#0C5DA5", "#E8204E"]
    ax.bar(x, values, color=colors, edgecolor="black", linewidth=0.8)
    ax.errorbar(x, values, yerr=np.asarray(yerr), fmt="none", ecolor="black", capsize=5)
    ax.axhline(
        theory["F_vdW_plus_capillary_nN"],
        color="#333333",
        linewidth=1.4,
        linestyle="--",
        label="vdW + capillary",
    )
    ax.set_xticks(x)
    ax.set_xticklabels(["vdW", "capillary", "measured approach"])
    ax.set_ylabel("Attractive force magnitude (nN)")
    ax.set_title("Approach attraction is close to vdW + capillary scale")
    ax.legend(frameon=False, loc="upper left")
    ax.set_ylim(0, max(values) * 1.45)
    ax.grid(axis="y", alpha=0.25)
    savefig(fig, "approach_theory_comparison")


def plot_branch_comparison(pair: pd.DataFrame) -> None:
    groups = ["JJS", "linker1-PFPE-OH", "linker1-nls", "linker1-paa", "linker2-paa"]
    df = pair[pair["group"].isin(groups)].copy()
    positions = np.arange(len(groups))

    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    width = 0.34
    ext = [df[df["group"] == g]["abs_extend_snap_nN"] for g in groups]
    ret = [df[df["group"] == g]["abs_retract_pull_off_nN"] for g in groups]
    bp1 = ax.boxplot(
        ext,
        positions=positions - width / 2,
        widths=0.25,
        patch_artist=True,
        showfliers=False,
    )
    bp2 = ax.boxplot(
        ret,
        positions=positions + width / 2,
        widths=0.25,
        patch_artist=True,
        showfliers=False,
    )
    for patch in bp1["boxes"]:
        patch.set_facecolor("#9CCAF2")
        patch.set_edgecolor("#0C5DA5")
    for patch in bp2["boxes"]:
        patch.set_facecolor("#F4A3A8")
        patch.set_edgecolor("#E8204E")
    for i, g in enumerate(groups):
        e = ext[i].dropna().to_numpy()
        r = ret[i].dropna().to_numpy()
        if len(e):
            ax.scatter(
                np.full(len(e), positions[i] - width / 2) + np.linspace(-0.04, 0.04, len(e)),
                e,
                s=18,
                color="#0C5DA5",
                alpha=0.6,
                zorder=3,
            )
        if len(r):
            ax.scatter(
                np.full(len(r), positions[i] + width / 2) + np.linspace(-0.04, 0.04, len(r)),
                r,
                s=18,
                color="#E8204E",
                alpha=0.6,
                zorder=3,
            )
    ax.set_yscale("log")
    ax.set_ylabel("Force magnitude (nN, log scale)")
    ax.set_xticks(positions)
    ax.set_xticklabels(groups, rotation=18, ha="right")
    ax.set_title("Loading attraction and unloading adhesion are strongly asymmetric")
    ax.grid(axis="y", alpha=0.25, which="both")
    ax.plot([], [], color="#0C5DA5", linewidth=8, label="approach snap-in")
    ax.plot([], [], color="#E8204E", linewidth=8, label="retract pull-off")
    ax.legend(frameon=False)
    savefig(fig, "branch_force_comparison")


def plot_adhesion_hysteresis(pair: pd.DataFrame) -> None:
    summary = (
        pair.groupby("group")
        .agg(
            n=("file", "size"),
            pull=("abs_retract_pull_off_nN", "median"),
            ratio=("pull_to_snap_ratio", "median"),
            work=("abs_hysteresis_work_nN_nm", "median"),
        )
        .reset_index()
    )
    summary = summary[summary["n"] >= 3].sort_values("pull", ascending=False)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.8, 4.4), gridspec_kw={"width_ratios": [1.25, 1]})
    colors = ["#E8204E" if g == "JJS" else "#0C5DA5" for g in summary["group"]]
    y = np.arange(len(summary))
    ax1.barh(y, summary["pull"], color=colors, edgecolor="black", linewidth=0.6)
    ax1.set_yticks(y)
    ax1.set_yticklabels(summary["group"])
    ax1.invert_yaxis()
    ax1.set_xlabel("Median pull-off (nN)")
    ax1.set_title("Adhesion ranking")
    ax1.grid(axis="x", alpha=0.25)
    ax2.scatter(summary["ratio"], summary["work"], s=58, color=colors, edgecolor="black")
    for _, row in summary.iterrows():
        ax2.annotate(row["group"], (row["ratio"], row["work"]), xytext=(4, 2), textcoords="offset points", fontsize=8)
    ax2.set_xscale("log")
    ax2.set_yscale("log")
    ax2.set_xlabel("Pull-off / snap-in")
    ax2.set_ylabel("Median |hysteresis work| (nN nm)")
    ax2.set_title("Dissipation map")
    ax2.grid(alpha=0.25, which="both")
    savefig(fig, "adhesion_hysteresis_ranking")


def plot_hysteresis_ratio_work(pair: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    groups = sorted(pair["group"].dropna().unique())
    palette = {
        "JJS": "#E8204E",
        "linker1-paa": "#FF9500",
        "linker2-paa": "#00B945",
        "k80-linker1-paa": "#E8204E",
        "k80-linker1-PFNA": "#0C5DA5",
        "k80-linker1-SDBS": "#845B97",
    }
    for group in groups:
        sub = pair[pair["group"] == group]
        if len(sub) < 3:
            continue
        ax.scatter(
            sub["pull_to_snap_ratio"],
            sub["abs_hysteresis_work_nN_nm"],
            s=34,
            alpha=0.62,
            edgecolor="black",
            linewidth=0.3,
            color=palette.get(group, "#777777"),
            label=group,
        )
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Pull-off / approach snap-in")
    ax.set_ylabel(r"$|W_{\mathrm{hys}}|$ (nN nm)")
    ax.set_title("Unloading adhesion produces large hysteresis")
    ax.grid(alpha=0.25, which="both")
    ax.legend(frameon=False, ncol=2, fontsize=8)
    savefig(fig, "hysteresis_ratio_work")


def plot_adhesion_ranking(pair: pd.DataFrame) -> None:
    summary = (
        pair.groupby("group")
        .agg(n=("file", "size"), pull=("abs_retract_pull_off_nN", "median"))
        .reset_index()
    )
    summary = summary[summary["n"] >= 3].sort_values("pull", ascending=True)
    colors = ["#E8204E" if g == "JJS" else "#0C5DA5" for g in summary["group"]]
    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    ax.barh(summary["group"], summary["pull"], color=colors, edgecolor="black", linewidth=0.6)
    ax.set_xlabel("Median retract pull-off (nN)")
    ax.set_title("Adhesion ranking across film chemistries")
    ax.grid(axis="x", alpha=0.25)
    savefig(fig, "adhesion_ranking")


def choose_representative_curves(curves: pd.DataFrame, groups: list[str]) -> list[str]:
    ids: list[str] = []
    valid = curves[curves["valid_model"] == True].copy()  # noqa: E712
    for group in groups:
        sub = valid[valid["group"] == group].copy()
        if sub.empty:
            continue
        med = sub["E_app_50nm_MPa"].median()
        idx = (sub["E_app_50nm_MPa"] - med).abs().idxmin()
        ids.append(str(sub.loc[idx, "curve_id"]))
    return ids


def plot_stitch_examples(points: pd.DataFrame, curves: pd.DataFrame) -> None:
    slip_curves = curves[curves["n_slip_events"] > 0].sort_values(["group", "fit_delta_max_nm"])
    if slip_curves.empty:
        slip_curves = curves.sort_values("fit_delta_max_nm", ascending=False).head(2)
    selected = list(slip_curves["curve_id"].head(3))
    fig, axes = plt.subplots(len(selected), 1, figsize=(7.3, 2.6 * len(selected)), sharex=False)
    if len(selected) == 1:
        axes = [axes]
    for ax, curve_id in zip(axes, selected, strict=True):
        sub = points[points["curve_id"] == curve_id].copy()
        sub = sub[sub["used_for_fit"] == True]  # noqa: E712
        sub = sub.sort_values("delta_nm")
        if sub.empty:
            continue
        label = str(sub["group"].iloc[0])
        max_points = 800
        if len(sub) > max_points:
            sub = sub.iloc[np.linspace(0, len(sub) - 1, max_points).astype(int)]
        ax.plot(sub["delta_nm"], sub["raw_force_nN"], color="#888888", linewidth=1.0, alpha=0.9, label="raw")
        ax.plot(sub["delta_nm"], sub["stitched_force_nN"], color="#E8204E", linewidth=1.3, label="stitched")
        ax.set_title(f"{label}: raw vs stitched loading")
        ax.set_xlabel("Indentation δ (nm)")
        ax.set_ylabel("Force (nN)")
        ax.grid(alpha=0.25)
        ax.legend(frameon=False, loc="upper left")
    savefig(fig, "stitch_raw_vs_stitched_examples")


def plot_slip_event_map(curves: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    sub = curves.copy()
    sizes = 36 + 55 * sub["n_slip_events"].fillna(0).clip(0, 3)
    colors = np.where(sub["n_terminal_cliffs"].fillna(0) > 0, "#E8204E", "#0C5DA5")
    ax.scatter(
        sub["fit_delta_max_nm"],
        sub["fit_force_max_nN"],
        s=sizes,
        c=colors,
        alpha=0.72,
        edgecolor="black",
        linewidth=0.4,
    )
    for group, grp in sub.groupby("group"):
        med_x = grp["fit_delta_max_nm"].median()
        med_y = grp["fit_force_max_nN"].median()
        if np.isfinite(med_x) and np.isfinite(med_y):
            ax.annotate(group, (med_x, med_y), xytext=(4, 3), textcoords="offset points", fontsize=8)
    ax.set_xlabel("Fit indentation span (nm)")
    ax.set_ylabel("Fit force maximum (nN)")
    ax.set_title("Slip and terminal-cliff QC map")
    ax.grid(alpha=0.25)
    ax.plot([], [], "o", color="#0C5DA5", markeredgecolor="black", label="pre-rupture usable")
    ax.plot([], [], "o", color="#E8204E", markeredgecolor="black", label="terminal cliff flagged")
    ax.legend(frameon=False, loc="best")
    savefig(fig, "slip_event_map")


def plot_model_fits(points: pd.DataFrame, curves: pd.DataFrame) -> None:
    groups = ["linker2-paa", "k80-linker1-paa", "k80-linker1-PFNA", "k80-linker1-SDBS"]
    ids = choose_representative_curves(curves, groups)
    fig, axes = plt.subplots(2, 2, figsize=(7.8, 6.6))
    axes_flat = axes.ravel()
    for ax, curve_id in zip(axes_flat, ids, strict=False):
        c = curves[curves["curve_id"] == curve_id].iloc[0]
        sub = points[(points["curve_id"] == curve_id) & (points["used_for_fit"] == True)].sort_values("delta_nm")
        if sub.empty:
            ax.axis("off")
            continue
        max_points = 600
        if len(sub) > max_points:
            sub_plot = sub.iloc[np.linspace(0, len(sub) - 1, max_points).astype(int)]
        else:
            sub_plot = sub
        x = sub_plot["delta_nm"].to_numpy(dtype=float)
        y = sub_plot["stitched_force_nN"].to_numpy(dtype=float)
        xfit = np.linspace(max(0, np.nanmin(x)), np.nanmax(x), 300)
        yfit = c["membrane_k1_N_m"] * xfit + c["membrane_k3_nN_per_nm3"] * xfit**3
        ax.scatter(x, y, s=7, color="#0C5DA5", alpha=0.55, label="stitched data")
        ax.plot(xfit, yfit, color="#E8204E", linewidth=1.8, label=r"$k_1\delta+k_3\delta^3$")
        ax.set_title(f"{c['group']}\nEapp={fmt(c['E_app_50nm_MPa'], 2)} MPa, R2={fmt(c['membrane_r2'], 3)}")
        ax.set_xlabel("δ (nm)")
        ax.set_ylabel("F (nN)")
        ax.grid(alpha=0.25)
        ax.legend(frameon=False)
    for ax in axes_flat[len(ids) :]:
        ax.axis("off")
    savefig(fig, "membrane_model_fit_examples")


def plot_modulus_ranking(curves: pd.DataFrame, group_summary: pd.DataFrame) -> None:
    groups = [
        "linker2-paa",
        "k80-linker1-paa",
        "k80-linker1-PFNA",
        "k80-linker1-SDBS",
    ]
    labels = ["linker2-PAA\n(RTESPA)", "k80-PAA", "k80-PFNA", "k80-SDBS"]
    valid = curves[(curves["valid_model"] == True) & (curves["group"].isin(groups))].copy()  # noqa: E712
    fig, ax = plt.subplots(figsize=(7.4, 4.8))
    x = np.arange(len(groups))
    for i, group in enumerate(groups):
        vals = valid[valid["group"] == group]["E_app_50nm_MPa"].dropna()
        if vals.empty:
            continue
        jitter = np.linspace(-0.07, 0.07, len(vals))
        ax.scatter(np.full(len(vals), i) + jitter, vals, color="#0C5DA5", s=28, alpha=0.65, zorder=3)
        med = vals.median()
        q1 = vals.quantile(0.25)
        q3 = vals.quantile(0.75)
        ax.errorbar(i, med, yerr=[[med - q1], [q3 - med]], fmt="o", color="black", capsize=6, markersize=7, zorder=4)
    ax.set_yscale("log")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel(r"$E_{\mathrm{app}}$ at 50 nm thickness (MPa)")
    ax.set_title("Model-dependent apparent modulus ranking")
    ax.grid(axis="y", alpha=0.25, which="both")
    savefig(fig, "apparent_modulus_ranking")

    fig, ax = plt.subplots(figsize=(7.2, 4.5))
    sub = group_summary[group_summary["group"].isin(groups)].copy()
    sub["label"] = sub["group"].map(dict(zip(groups, labels, strict=True)))
    sub = sub.set_index("group").loc[groups].reset_index()
    y50 = sub["E_app_50nm_MPa_median"].to_numpy(dtype=float)
    y80 = sub["E_app_80nm_MPa_median"].to_numpy(dtype=float)
    ax.plot(x, y50, "o-", color="#E8204E", label="t = 50 nm")
    ax.plot(x, y80, "s--", color="#0C5DA5", label="t = 80 nm")
    ax.set_yscale("log")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel(r"$E_{\mathrm{app}}$ median (MPa)")
    ax.set_title("Thickness sensitivity follows Eapp ∝ 1/t")
    ax.grid(axis="y", alpha=0.25, which="both")
    ax.legend(frameon=False)
    savefig(fig, "thickness_sensitivity")


def plot_stiffness_vs_modulus(curves: pd.DataFrame) -> None:
    valid = curves[curves["valid_model"] == True].copy()  # noqa: E712
    valid = valid[np.isfinite(valid["E_app_50nm_MPa"]) & np.isfinite(valid["high_stiffness_N_m"])]
    palette = {
        "linker2-paa": "#00B945",
        "k80-linker1-paa": "#E8204E",
        "k80-linker1-PFNA": "#0C5DA5",
        "k80-linker1-SDBS": "#845B97",
    }
    fig, ax = plt.subplots(figsize=(7.2, 4.7))
    for group, sub in valid.groupby("group"):
        ax.scatter(
            sub["high_stiffness_N_m"],
            sub["E_app_50nm_MPa"],
            s=44,
            alpha=0.72,
            edgecolor="black",
            linewidth=0.35,
            color=palette.get(group, "#777777"),
            label=display_group(group),
        )
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"High-force stiffness $k_{\mathrm{high}}$ (N/m)")
    ax.set_ylabel(r"$E_{\mathrm{app}}$ at 50 nm (MPa)")
    ax.set_title("Stiffness and apparent modulus are correlated but not identical")
    ax.grid(alpha=0.25, which="both")
    ax.legend(frameon=False, fontsize=8)
    savefig(fig, "stiffness_vs_modulus")


def plot_errorbar_statistics(curves: pd.DataFrame) -> None:
    groups = ["linker2-paa", "k80-linker1-paa", "k80-linker1-PFNA", "k80-linker1-SDBS"]
    valid = curves[(curves["valid_model"] == True) & (curves["group"].isin(groups))].copy()  # noqa: E712
    metrics = [
        ("E_app_50nm_MPa", r"$E_{\mathrm{app}}$ (MPa)", True),
        ("high_stiffness_N_m", r"$k_{\mathrm{high}}$ (N/m)", True),
    ]
    fig, axes = plt.subplots(1, 2, figsize=(7.8, 4.4))
    for ax, (col, ylabel, log_scale) in zip(axes, metrics, strict=True):
        for i, group in enumerate(groups):
            vals = valid[valid["group"] == group][col].dropna()
            if vals.empty:
                continue
            jitter = np.linspace(-0.06, 0.06, len(vals))
            ax.scatter(np.full(len(vals), i) + jitter, vals, s=22, color="#0C5DA5", alpha=0.6)
            med = vals.median()
            q1 = vals.quantile(0.25)
            q3 = vals.quantile(0.75)
            ax.errorbar(i, med, yerr=[[med - q1], [q3 - med]], fmt="o", color="black", capsize=5, markersize=6)
        ax.set_xticks(range(len(groups)))
        ax.set_xticklabels([display_group(g).replace("k80-", "") for g in groups], rotation=20, ha="right")
        ax.set_ylabel(ylabel)
        if log_scale:
            ax.set_yscale("log")
        ax.grid(axis="y", alpha=0.25, which="both")
    fig.suptitle("Error bars use median and interquartile range")
    savefig(fig, "median_iqr_errorbars")


def plot_literature_comparison(metrics: dict) -> None:
    jjs = metrics["jjs"]
    ranges = [
        ("hydrogels", 0.001, 5.5, "#B9E3C6"),
        ("PDMS elastomers", 1.0, 3.0, "#AED6F1"),
        ("this work: k80-SDBS", 0.349, 0.584, "#845B97"),
        ("this work: k80-PFNA", 0.982, 2.308, "#0C5DA5"),
        ("this work: k80-PAA", 2.778, 104.348, "#E8204E"),
        ("this work: linker2-PAA", 1011.447, 2184.340, "#00B945"),
        ("PMMA/PS-like rigid polymers", 1000, 4000, "#C0C0C0"),
        ("reported 2D COF films", 1450, 25900, "#FFB000"),
        ("MoS2 monolayer", 170000, 370000, "#999999"),
        ("graphene", 1000000, 1000000, "#222222"),
    ]
    fig, ax = plt.subplots(figsize=(7.8, 5.4))
    y = np.arange(len(ranges))
    for i, (label, lo, hi, color) in enumerate(ranges):
        if math.isclose(lo, hi):
            ax.scatter(lo, i, s=70, color=color, edgecolor="black", zorder=3)
        else:
            ax.plot([lo, hi], [i, i], color=color, linewidth=7, solid_capstyle="round")
            ax.scatter([lo, hi], [i, i], s=36, color=color, edgecolor="black", zorder=3)
    ax.set_xscale("log")
    ax.set_yticks(y)
    ax.set_yticklabels([r[0] for r in ranges])
    ax.invert_yaxis()
    ax.set_xlabel("Young's modulus or apparent modulus (MPa, log scale)")
    ax.set_title("Material-scale context for apparent membrane modulus")
    ax.grid(axis="x", alpha=0.25, which="both")
    ax.text(
        0.0012,
        len(ranges) - 0.35,
        f"JJS adhesion median: {fmt(jjs['retract_pull_off_median_nN'], 1)} nN (not a modulus)",
        fontsize=9,
        color="#555555",
    )
    savefig(fig, "literature_modulus_context")


def build_summary_tables(data: dict[str, pd.DataFrame | dict]) -> dict[str, str]:
    pair = data["pair"]
    mod_group = data["mod_group"]
    metrics = data["metrics"]
    assert isinstance(pair, pd.DataFrame)
    assert isinstance(mod_group, pd.DataFrame)
    assert isinstance(metrics, dict)

    group_rows = []
    for group in ["JJS", "linker1-PFPE-OH", "linker1-nls", "linker1-paa", "linker2-paa"]:
        sub = pair[pair["group"] == group]
        group_rows.append(
            (
                group,
                len(sub),
                quantile_text(sub["abs_extend_snap_nN"], 2),
                quantile_text(sub["abs_retract_pull_off_nN"], 2),
                quantile_text(sub["pull_to_snap_ratio"], 2),
            )
        )
    adhesion_table = "\n".join(
        f"{g} & {n} & {e} & {r} & {ratio} \\\\" for g, n, e, r, ratio in group_rows
    )

    mech_rows = []
    for group in ["linker2-paa", "k80-linker1-paa", "k80-linker1-PFNA", "k80-linker1-SDBS", "k80-linker2-paa"]:
        sub = mod_group[mod_group["group"] == group]
        if sub.empty:
            continue
        row = sub.iloc[0]
        mech_rows.append(
            (
                int(row["date"]),
                display_group(group),
                int(row["n_valid_model"]),
                f"{fmt(row['E_app_50nm_MPa_median'], 3)} [{fmt(row['E_app_50nm_MPa_q1'], 3)}, {fmt(row['E_app_50nm_MPa_q3'], 3)}]",
                f"{fmt(row['E_app_80nm_MPa_median'], 3)}",
                f"{fmt(row['high_stiffness_N_m_median'], 3)}",
                f"{fmt(row['membrane_r2_median'], 3)}",
            )
        )
    mechanics_table = "\n".join(
        f"{date} & {group} & {n} & {e50} & {e80} & {khigh} & {r2} \\\\"
        for date, group, n, e50, e80, khigh, r2 in mech_rows
    )

    return {
        "adhesion_table": adhesion_table,
        "mechanics_table": mechanics_table,
        "jjs_extend": fmt(metrics["jjs"]["extend_snap_median_nN"], 1),
        "jjs_extend_iqr": f"{fmt(metrics['jjs']['extend_snap_iqr_nN'][0], 1)}--{fmt(metrics['jjs']['extend_snap_iqr_nN'][1], 1)}",
        "jjs_retract": fmt(metrics["jjs"]["retract_pull_off_median_nN"], 1),
        "jjs_retract_iqr": f"{fmt(metrics['jjs']['retract_pull_off_iqr_nN'][0], 1)}--{fmt(metrics['jjs']['retract_pull_off_iqr_nN'][1], 1)}",
        "jjs_ratio": fmt(metrics["jjs"]["pull_to_snap_ratio_median"], 1),
        "theory_vdw": fmt(metrics["theory_R8_nm"]["F_vdW_nN"], 1),
        "theory_cap": fmt(metrics["theory_R8_nm"]["F_capillary_nN"], 1),
        "theory_sum": fmt(metrics["theory_R8_nm"]["F_vdW_plus_capillary_nN"], 1),
    }


def display_group(group: str) -> str:
    return {
        "linker2-paa": "linker2-PAA",
        "k80-linker1-paa": "k80-linker1-PAA",
        "k80-linker1-PFNA": "k80-linker1-PFNA",
        "k80-linker1-SDBS": "k80-linker1-SDBS",
        "k80-linker2-paa": "k80-linker2-PAA",
    }.get(group, group)


PROGRESS_MD = ROOT.parent / "progress.md"
REPORT_MD = OUT / "afm_scientific_report.md"


def generate_markdown_report(data, tables):
    """Write standalone Markdown report in reports/realraw/scientific_report/."""
    pair = data["pair"]
    assert isinstance(pair, pd.DataFrame)
    assert isinstance(tables, dict)

    lines = []
    def w(s=""):
        lines.append(s)

    w("# 二维聚合物薄膜的 AFM 力学测试、界面粘附与表观模量分析")
    w()
    w(f"> 自动生成于 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    w()

    w("## 摘要")
    w()
    w(f"本报告基于二维聚合物薄膜的 AFM 力学测试数据，分别分析探针接近过程中的吸引力、回撤"
      f"过程中的粘附与滞后行为，以及深压入加载曲线所反映的模型依赖表观膜力学性能。结果显示，"
      f"JJS 样品在 approach/loading 段的吸引力中位数为 **{tables['jjs_extend']} nN**，"
      f"四分位范围为 {tables['jjs_extend_iqr']} nN，与半径 8 nm 探针下范德华力和毛细力的"
      f"经典估算值 **{tables['theory_sum']} nN** 同量级。相比之下，retract/unloading 段 "
      f"pull-off 粘附力中位数达到 **{tables['jjs_retract']} nN**，约为 approach 吸引力的 "
      f"**{tables['jjs_ratio']} 倍**，说明强信号主要来自接触后液桥/界面钉扎导致的回撤粘附"
      f"和耗散。深压入结果进一步表明，不同表面活性剂或后处理会显著改变薄膜的有效承载网络："
      f"在同一 k80 系列内部，model-dependent apparent modulus 的排序为 PAA > PFNA > SDBS；"
      f"linker2-PAA 在其测试条件下呈现更高且更稳定的 GPa 级表观膜模量。所有模量均解释为"
      f"模型依赖的 apparent modulus，用于相对力学比较。")
    w()

    w("## 1. 研究目标与数据概述")
    w()
    w("### 1.1 AFM 力曲线分析目标")
    w("本文关注三个相互关联但物理来源不同的问题：")
    w("1. 二维聚合物薄膜在 AFM 探针接近时产生多大的吸引力，以及该吸引力是否可由范德华力和毛细力的经典量级解释")
    w("2. 探针回撤时的 pull-off 粘附力和能量滞后有多强，它们反映的是接触后液桥拉伸、界面钉扎还是薄膜本身的弹性")
    w("3. 在排除 snap-in、pull-off 和明显不可恢复破裂后，深压入 loading 段能否给出表面活性剂依赖的相对薄膜力学性能")
    w()
    w("### 1.2 AFM 力曲线结构：approach/loading 与 retract/unloading")
    w("每条 AFM 力曲线按加载和卸载分支分别处理。approach/loading 分支用于接近段吸引力、接触点和深压入力学；retract/unloading 分支用于 pull-off 粘附力、回撤面积和滞后功。")
    w()
    w("### 1.3 样品体系与表面处理组")
    w()
    w("| 日期 | 主要样品 | 探针 | 半径 | 弹簧常数 | 主要用途 |")
    w("|------|---------|------|------|---------|---------|")
    w("| 20260409 | JJS | RTESPA-150 | 8 nm | 7 N/m | approach 吸引力、retract 粘附、滞后与限域水桥候选机制 |")
    w("| 20260415 | linker1/linker2 | RTESPA-150 | 8 nm | 7 N/m | linker 系列粘附差异；linker2-PAA 深压入力学对照 |")
    w("| 20260416 | k80 系列 | DDESP-V2 | 100 nm | 89 N/m | PAA/PFNA/SDBS 表面活性剂 apparent mechanics 对比 |")
    w()
    w("![workflow](workflow_scheme.pdf)")
    w("*图 1: AFM 力曲线分析流程图。加载分支用于接近段吸引力和深压入力学；卸载分支用于 pull-off 粘附和滞后功。*")
    w()

    w("## 2. 力曲线处理方法")
    w()
    w("### 2.1 原始 Z-force 数据读取")
    w("原始数据保留采集顺序，并记录源文件、分支、位移、setpoint、探针半径和弹簧常数。力统一转换为 nN，位移和压入深度统一为 nm；对于 uN 量级深压入曲线，先完成单位转换再进入同一套特征提取和拟合流程。")
    w()
    w("### 2.2 extend 作为 approach/loading 曲线")
    w("approach/loading 曲线用于 baseline 校正、snap-in/吸引力识别、接触点定位和 post-contact loading 分析。接近段吸引力以负力最小值的绝对值表示；深压入力学只取接触点之后的正力加载段。")
    w()
    w("### 2.3 retract 作为 unloading/pull-off 曲线")
    w("retract/unloading 曲线用于 pull-off 粘附力和回撤面积。pull-off force 定义为回撤分支中最强负力，其物理意义是接触形成之后的脱粘或液桥断裂强度，而不是接近段吸引力。")
    w()
    w("### 2.4 baseline、contact、snap-in 与 pull-off 定义")
    w("baseline 用远离表面的低相互作用区拟合并扣除。contact point 由基线后正力上升和局部斜率变化确定。snap-in 是 approach 分支中接触前后出现的负力极小值；pull-off 是 retract 分支中卸载阶段的负力极小值。work area 由相应曲线积分得到。")
    w()
    w("### 2.5 有效曲线筛选与 QC 标准")
    w("QC 标准包括 baseline 是否稳定、曲线点数是否足够、单位是否一致、深压入是否达到最小压入深度和正力阈值、膜模型拟合 R² 是否达标。含明显 baseline 风险或无足够 post-contact 点的曲线可用于定性查看，但不进入 apparent modulus 统计。")
    w()

    w("## 3. Approach 吸引力：范德华力与毛细力")
    w()
    w("### 3.1 范德华吸引力模型")
    w()
    w("探针靠近薄膜表面时，最基本的吸引力之一是球-平面范德华相互作用：")
    w()
    w("$$F_{vdW} = \\frac{A R}{12 d_0^2}$$")
    w()
    w("其中 A 为有效 Hamaker 常数，R 为探针半径，d₀ 为最小有效间距。该式适合做量级估算，不应在未知表面粗糙度和真实接触几何时过度反演 A。")
    w()
    w("### 3.2 毛细桥力模型")
    w("在空气湿度或亲水界面存在时，探针和薄膜之间可形成纳米水桥。完全润湿上限下，毛细力可写为：")
    w()
    w("$$F_{cap} = 4\\pi R \\gamma \\cos\\theta$$")
    w()
    w("其中 γ 是水/空气界面张力，θ 为有效接触角。真实毛细力会受湿度、粗糙度、接触线钉扎和动态成核影响 [Butt 2005, Israelachvili 2011]。")
    w()
    w("### 3.3 理论量级估算")
    w(f"对 8 nm 半径探针，取 A = 4×10⁻¹⁹ J、d₀ = 0.3 nm、γ = 72 mN/m，得到 F_vdW ≈ **{tables['theory_vdw']} nN**、F_cap ≈ **{tables['theory_cap']} nN**，二者合计约 **{tables['theory_sum']} nN**。")
    w()
    w("### 3.4 JJS extend 吸引力与理论模型对比")
    w(f"JJS 样品 approach/loading 段吸引力中位数为 **{tables['jjs_extend']} nN**，四分位范围为 {tables['jjs_extend_iqr']} nN。这个实测值只比经典 F_vdW + F_cap 估算高约 1-2 倍，因此一个稍大的有效润湿半径、较强亲水界面、局部水桥成核或动态 snap-in 就足以解释观测量级。")
    w()
    w("### 3.5 有效毛细半径与 Hamaker upper bound 的半定量解释")
    w("如果把全部吸引力都写入 F_cap = 4πR_eff·γ，得到的是有效毛细半径，而不是真实几何半径。同样，如果把毛细力、静电和动态效应都并入 vdW 公式反推 A，得到的是 upper bound。二者只能用于判断物理量级，而不能作为唯一微观机制证明。")
    w()
    w("![approach_theory](approach_theory_comparison.pdf)")
    w("*图 2: JJS approach/loading 吸引力与 vdW + capillary 理论量级对比。*")
    w()

    w("## 4. Retract 粘附力与界面滞后")
    w()
    w("### 4.1 pull-off force 的定义")
    w("pull-off force 是 unloading 曲线中最强负力，代表探针从已形成接触或液桥状态中脱离薄膜所需克服的最大粘附力。它反映的是接触后界面脱粘，而不是 approach 阶段的远程吸引力。")
    w()
    w("### 4.2 JJS retract 粘附力统计")
    w(f"JJS 的 retract/unloading pull-off 中位数为 **{tables['jjs_retract']} nN**，四分位范围为 {tables['jjs_retract_iqr']} nN。该值远高于其 approach 吸引力，说明强信号主要发生在接触形成后的回撤阶段。")
    w()
    w("### 4.3 extend attraction 与 retract adhesion 的不对称性")
    w(f"JJS pull-off/snap-in 比值中位数为 **{tables['jjs_ratio']}** 倍。linker 系列和 k80 系列也表现出不同程度的加载/卸载不对称，说明薄膜界面不仅有可逆表面力，还有接触线钉扎、液桥拉伸、局部脱粘和耗散过程。")
    w()
    w("### 4.4 滞后功计算")
    w("对成对加载/卸载曲线，滞后功定义为加载面积与卸载面积之差。实际比较中使用 |W_hys| 表示耗散量级。")
    w()
    w("### 4.5 水桥拉伸、钉扎、延迟断裂与能量耗散机制")
    w("最合理的物理图像是：接近时形成水桥或局部接触；回撤时水桥被拉伸，三相接触线在亲水/粗糙/缺陷位点上钉扎，导致负压、延迟断裂和明显能量耗散。当前数据支持限域水桥作为候选机制，但不能单独分离 solvation force、静电力和真实水桥几何。")
    w()
    w("![branch_comparison](branch_force_comparison.pdf)")
    w("*图 3: extend snap-in 与 retract pull-off 对比。纵轴为 log scale。*")
    w()
    w("![hysteresis](hysteresis_ratio_work.pdf)")
    w("*图 4: pull-off/extend ratio 与 hysteresis work 分布。*")
    w()

    w("## 5. 样品间粘附差异")
    w()
    w("### 5.1 JJS 与 linker 系列粘附行为对比")
    w("JJS 的回撤粘附显著强于其接近段吸引力，也强于多数 linker 系列。linker 系列中，PAA 相关样品通常具有更高 pull-off，提示亲水/带电界面对液桥稳定性和接触线钉扎具有增强作用。")
    w()
    w("### 5.2 粘附信号的可靠性与限制")
    w("pull-off force 是本数据中较稳健的实验量，因为它来自回撤分支的清晰负力极值。限制在于它不是单一物理力：范德华、毛细、静电、局部塑性或脱粘都可能贡献。若要分离机制，需要湿度、干氮、不同探针半径和表面电势对照。")
    w()
    w("![adhesion_ranking](adhesion_ranking.pdf)")
    w("*图 5: 不同样品/处理组的 adhesion ranking。柱高为 retract pull-off 中位数。*")
    w()
    w("### 粘附力统计表")
    w()
    w("| 组别 | 曲线对数 | approach 吸引力 / nN | retract 粘附力 / nN | pull-off/snap-in |")
    w("|------|---------|---------------------|--------------------|--------------------|")
    w(f"| {tables['adhesion_table'].replace(chr(92)+chr(92), ' | ')} |")  # won't work — need raw table
    w()
    # Replace the broken table line with proper format
    lines[-1] = build_adhesion_md_table(pair)
    w()

    w("## 6. 深压入曲线与滑脱拼接")
    w()
    w("### 6.1 深压入曲线筛选标准")
    w("薄膜力学性能只从深压入正力 loading 段提取。候选曲线需要具有足够 post-contact 正力点、最大压入深度和最大排斥力达到深压入阈值。JJS 主要用于粘附/滞后分析，不作为 intrinsic mechanics 的主要来源。")
    w()
    w("### 6.2 recoverable slip 与 terminal cliff 的分类")
    w("recoverable slip 表现为力突然下降后，后续曲线重新回到上升趋势；terminal cliff 表现为末端大幅掉落且不恢复，通常对应破膜、脱粘或不可逆接触变化。前者可用于连续 loading 重构，后者只保留 cliff 前数据。")
    w()
    w("### 6.3 垂直 force-offset stitching 方法")
    w("对 recoverable slip 之后的整段曲线施加累计垂直 force offset，使 post-slip 段接到 pre-slip 趋势上。原始力值保留为 raw force；stitched force 只作为拟合视图。该方法不引入随机抖动，也不改变压入深度。")
    w()
    w("### 6.4 拼接方法的物理边界")
    w("拼接不代表真实实验曲线被改写，也不能用于断裂强度分析。它只适合在 recoverable slip 明确、曲线仍保持整体 loading 趋势时使用；若出现不可恢复 cliff，则不对 cliff 之后做任何修复。")
    w()
    w("![stitch](stitch_raw_vs_stitched_examples.pdf)")
    w("*图 6: 深压入曲线拼接前后对比。灰色为原始 loading 点，红色为 stitched loading 视图。*")
    w()
    w("![slip_map](slip_event_map.pdf)")
    w("*图 7: 滑脱事件分布图。点大小随 recoverable slip 数量增加；红色表示 terminal cliff 标记。*")
    w()

    w("## 7. 薄膜力学模型")
    w()
    w("### 7.1 apparent low-force stiffness 与 high-force stiffness")
    w("深压入段首先给出经验刚度。k_low 对接触点、预张力和局部顺应性敏感；k_high 更接近大压入下的承载能力。二者比值描述 strain-stiffening 或 loading 非线性。")
    w()
    w("### 7.2 幂律模型")
    w("F = A·δ^n。指数 n 可作为经验指标：n 接近 1 表示近似线性刚度；较高 n 表示大变形膜拉伸、几何非线性或接触面积变化增强。")
    w()
    w("### 7.3 clamped circular membrane 模型")
    w("主报告采用夹持圆形悬膜的 AFM 压入模型 [Lee 2008, Bertolazzi 2011]：")
    w()
    w("$$F = k_1\\delta + k_3\\delta^3$$")
    w()
    w("线性项 k₁δ 合并了预张力、边界顺应性和低压入接触刚度；三次项 k₃δ³ 反映大变形膜拉伸主导的非线性承载。")
    w()
    w("### 7.4 model-dependent apparent Young's modulus")
    w()
    w("$$k_3 = \\frac{E_{app} \\cdot t \\cdot q^3}{a^2}, \\quad q = \\frac{1}{1.05 - 0.15\\nu - 0.16\\nu^2}$$")
    w()
    w("$$E_{app} = \\frac{k_3 a^2}{q^3 t}$$")
    w()
    w("单位换算：若 k₃ 由 nN/nm³ 拟合得到，则 k₃[N/m³] = 10¹⁸ × k₃[nN/nm³]。")
    w()
    w("### 7.5 膜厚、孔径和泊松比的参数敏感性")
    w("默认孔半径 a = 10 μm、泊松比 ν = 0.30、主膜厚 t = 50 nm，并给出 t = 80 nm 的敏感性估计。由于 E_app ∝ a²/t，孔径误差会平方放大，膜厚误差会线性传递。")
    w()
    w("### 7.6 为什么结果应解释为 apparent modulus")
    w("E_app 不是严格本征 Young's modulus，因为 AFM 探针几何、薄膜缺陷、厚度不均、边界夹持顺应性和可恢复滑脱都会进入拟合参数。它最适合用于同一探针、同一批次、同一模型下的相对力学排序。")
    w()
    w("![model_fits](membrane_model_fit_examples.pdf)")
    w("*图 8: 代表性膜模型拟合曲线。*")
    w()
    w("![thickness](thickness_sensitivity.pdf)")
    w("*图 9: 膜厚敏感性分析。由于 E_app ∝ 1/t，80 nm 假设下的模量低于 50 nm 主值。*")
    w()

    w("## 8. 表面活性剂对薄膜力学性能的影响")
    w()
    w("### 8.1 k80-linker1-paa 力学表现")
    w("在同一 k80 系列内部，PAA 处理组的 apparent modulus 和高力区刚度最高。PAA 组中位 E_app 为几十 MPa，且部分曲线达到更高承载力。")
    w()
    w("### 8.2 k80-linker1-PFNA 力学表现")
    w("PFNA 组的 E_app 比 PAA 明显降低，处于低 MPa 量级。该结果提示 PFNA 处理可能产生较弱的有效承载路径、更多局部软化区域或较低界面结合。")
    w()
    w("### 8.3 k80-linker1-SDBS 力学表现")
    w("SDBS 组有效曲线数较少，现有有效曲线显示亚 MPa 到低 MPa 的 apparent modulus，整体低于 PAA 和 PFNA。该组应标注 low-N 风险。")
    w()
    w("### 8.4 linker2-paa 的有效曲线数量与可靠性")
    w("linker2-PAA 在其测试条件下表现出更高且更稳定的 GPa 级 apparent modulus，有效曲线数为 15，膜模型 R² 中位数接近 0.99。")
    w()
    w("### 8.5 apparent modulus ranking")
    w("同一 k80 系列内部排序：**PAA > PFNA > SDBS**。linker2-PAA 显示高可重复性，但因探针半径和测试条件不同，不宜直接与 k80 系列做绝对优劣判断。")
    w()
    w("### 8.6 表面形貌、缺陷密度与膜连续性的结构-性能关系")
    w("表面活性剂可能通过改变晶粒融合、片层堆积、残留相分离、孔洞和界面脱粘位置来改变薄膜力学表现。PAA 更高的刚度和模量提示更连续的承载网络；PFNA/SDBS 的低模量则更符合缺陷密度更高的情形。该因果链仍需形貌和膜厚证据闭合。")
    w()
    w("![modulus_ranking](apparent_modulus_ranking.pdf)")
    w("*图 10: 不同表面活性剂 E_app 散点图。黑点和误差棒表示中位数与 IQR。*")
    w()
    w("![stiffness_vs_modulus](stiffness_vs_modulus.pdf)")
    w("*图 11: apparent stiffness vs apparent modulus。高力区刚度和三次项模量相关。*")
    w()

    # Mechanics table
    w("### 表观模量统计表")
    w()
    w("| 日期 | 组别 | 有效曲线 | E_app 50nm / MPa | E_app 80nm / MPa | k_high / N/m | R² |")
    w("|------|------|---------|------------------|------------------|-------------|-----|")
    w(f"| {tables['mechanics_table'].replace(chr(92)+chr(92), ' | ')} |")
    lines[-1] = build_mechanics_md_table(data["mod_group"])
    w()

    w("## 9. 误差棒与统计表达")
    w()
    w("### 9.1 曲线间变异：median 与 IQR")
    w("本报告以每条有效曲线为统计单元，中心值使用 median，误差棒使用 interquartile range。该表达直接反映样品内部不均一性和缺陷导致的曲线间变异。")
    w()
    w("### 9.2 模型拟合误差：R²、残差与 confidence interval")
    w("膜模型拟合质量用 R² 和残差趋势评估。R² 高说明 k₁δ + k₃δ³ 能描述 stitched loading 包络，但不代表模型假设完全真实。")
    w()
    w("### 9.3 膜厚不确定性：50-80 nm 敏感性范围")
    w("由于 E_app ∝ 1/t，膜厚从 50 nm 增至 80 nm 会使 apparent modulus 乘以 50/80 = 0.625。因此图表同时给出 50 nm 主值和 80 nm 敏感性值。")
    w()
    w("### 9.4 low-N 数据的标注方式")
    w("有效曲线数 N < 5 的组只做趋势性讨论，不作为强统计结论。SDBS 和 k80-linker2-PAA 等低 N 或无有效模型组需要在图注和表格中明确标注。")
    w()
    w("### 9.5 推荐图示：单曲线散点 + median + IQR")
    w("推荐所有组间力学图采用单曲线散点叠加 median+IQR，而不是只画均值柱状图。这样能同时展示中心趋势、离散度和异常高/低曲线。")
    w()
    w("![errorbars](median_iqr_errorbars.pdf)")
    w("*图 12: 带原始散点、median 和 IQR 的力学性能图。*")
    w()

    w("## 10. 与其他薄膜材料的量级比较")
    w()
    w("### 10.1 软聚合物薄膜")
    w("PDMS 类软弹性体常见 Young's modulus 约为 1-3 MPa [Liu 2023]。k80-PFNA 和 k80-SDBS 接近这一软材料区间，而 k80-PAA 明显更硬。")
    w()
    w("### 10.2 水凝胶/软界面薄膜")
    w("水凝胶通常处于 kPa 到低 MPa 区间 [Jagiełło 2024, Su 2016]。本体系中较软的表面活性剂组接近软凝胶/弹性体边界。")
    w()
    w("### 10.3 超薄无机/有机复合膜")
    w("linker2-PAA 的 GPa 量级 apparent modulus 接近刚性聚合物薄膜或部分多孔有机薄膜，但仍低于高度取向、缺陷极少的二维晶体材料。")
    w()
    w("### 10.4 本体系 apparent modulus 的合理性与特殊性")
    w("当前薄膜的力学量级位于软凝胶/弹性体与高模量二维晶体之间。核心发现不是达到无缺陷二维晶体极限，而是表面化学使实际承载路径跨越多个数量级。")
    w()
    w("### 10.5 对表面活性剂调控缺陷和力学性能的启示")
    w("表面活性剂 → 形貌和缺陷 → 有效承载网络 → AFM 深压入力学响应。")
    w()
    w("![literature](literature_modulus_context.pdf)")
    w("*图 13: 本体系 apparent modulus 与文献中典型薄膜材料模量范围对比。*")
    w()

    w("## 11. 可提取物理量与科学结论")
    w()
    w("| 类别 | 物理量 | 解释边界 |")
    w("|------|--------|---------|")
    w("| 可稳健提取 | approach attraction scale | 远程吸引力加动态 snap-in 的量级 |")
    w("| 可稳健提取 | retract pull-off adhesion | 接触后脱粘/液桥断裂强度 |")
    w("| 可稳健提取 | hysteresis work | 加载/卸载耗散量级 |")
    w("| 可稳健提取 | apparent modulus ranking | 同模型下相对薄膜承载能力 |")
    w("| 半定量 | effective capillary radius | 吸收润湿、粗糙和水桥几何的有效参数 |")
    w("| 半定量 | effective Hamaker upper bound | 会混入毛细和静电贡献 |")
    w("| 不可靠单独提取 | solvation force / true bridge geometry | 需要湿度、干氮、KPFM 或探针半径系列 |")
    w("| 不可靠单独提取 | intrinsic Young's modulus | 需要独立膜厚、边界和接触模型验证 |")
    w()

    w("## 12. 总结与文章主线")
    w()
    w("### 12.1 AFM 力学测试揭示的二维聚合物薄膜界面粘附行为")
    w("接近段吸引力处于范德华力加毛细力的合理量级；真正显著的界面非对称性出现在回撤粘附和滞后中。JJS 的强 pull-off 支持液桥拉伸、界面钉扎和延迟断裂的物理图像。")
    w()
    w("### 12.2 表面活性剂改变薄膜缺陷与形貌，从而改变 apparent mechanics")
    w("深压入结果说明表面活性剂和后处理会显著改变悬膜有效承载网络。PAA 相关样品通常表现出更强承载能力；PFNA 和 SDBS 则显示更软的 apparent mechanics。")
    w()
    w("### 12.3 深压入数据支持的相对力学排序")
    w("同一 k80 系列内部最可靠的排序为：**PAA > PFNA > SDBS**。linker2-PAA 在自身测试条件下显示最高可重复性和 GPa 级 apparent modulus，但不与 k80 系列做绝对优劣比较。")
    w()
    w("### 12.4 后续实验建议")
    w("后续应补充：膜厚统计（SEM截面/椭偏仪）、AFM height/phase 或 SEM/TEM 形貌、湿度/干氮对照、不同探针半径测试和更大样本量。")
    w()

    w("---")
    w()
    w("## 附录")
    w()
    w("### A. 公式推导")
    w("从夹持圆膜大变形压入模型出发：F = k₁δ + k₃δ³。若二维模量 E₂D = E·t，圆膜半径为 a，泊松比修正因子为 q，则 k₃ = E_app·t·q³/a²。整理得到 E_app = k₃a²/(q³t)。")
    w()
    w("### B. 曲线处理与拼接算法")
    w("拼接算法只检测 post-contact 正力 loading 段中的可恢复负向突跳。对每个 recoverable slip，计算跳落前趋势和跳落后恢复段之间的力差，并对后续整段施加累计垂直 offset。terminal cliff 后数据被截断，不参与拟合。")
    w()
    w("### C. 图表生成参数")
    w("所有图为 A4 报告重新生成。力单位为 nN，长度单位为 nm，apparent modulus 主值使用 a = 10 μm、t = 50 nm、ν = 0.30，并给出 t = 80 nm 敏感性。")
    w()
    w("### D. 参考文献")
    w()
    w("1. Butt, H.-J.; Cappella, B.; Kappl, M. *Surface Science Reports* **2005**, 59, 1-152. https://doi.org/10.1016/j.surfrep.2005.08.003")
    w("2. Israelachvili, J. N. *Intermolecular and Surface Forces*, 3rd ed.; Academic Press, 2011.")
    w("3. Lee, C.; Wei, X.; Kysar, J. W.; Hone, J. *Science* **2008**, 321, 385-388.")
    w("4. Bertolazzi, S.; Brivio, J.; Kis, A. *ACS Nano* **2011**, 5, 9703-9709.")
    w("5. Jagiełło, J.; et al. *Gels* **2024**. https://pmc.ncbi.nlm.nih.gov/articles/PMC11944691/")
    w("6. Su, T.; et al. *ACS Macro Letters* **2016**, 5, 1217-1221.")
    w("7. Liu, M.; et al. *Advanced Science* **2023**. https://pmc.ncbi.nlm.nih.gov/articles/PMC10700310/")
    w("8. Xiong, L.; et al. *Chemical Science* **2025**, 16, 15913-15925. https://doi.org/10.1039/D5SC02180D")
    w()

    report_path = REPORT_MD
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def build_adhesion_md_table(pair):
    lines = []
    lines.append("| 组别 | 曲线对数 | approach 吸引力 / nN | retract 粘附力 / nN | pull-off/snap-in |")
    lines.append("|------|---------|---------------------|--------------------|--------------------|")
    groups = ["JJS", "linker1-PFPE-OH", "linker1-nls", "linker1-paa", "linker2-paa"]
    for g in groups:
        sub = pair[pair["group"] == g]
        if sub.empty:
            continue
        n = len(sub)
        ext = quantile_text(sub["abs_extend_snap_nN"], 2)
        ret = quantile_text(sub["abs_retract_pull_off_nN"], 2)
        ratio = quantile_text(sub["pull_to_snap_ratio"], 2)
        lines.append(f"| {g} | {n} | {ext} | {ret} | {ratio} |")
    return "\n".join(lines)


def build_mechanics_md_table(mod_group):
    lines = []
    lines.append("| 日期 | 组别 | 有效曲线 | E_app 50nm / MPa | E_app 80nm / MPa | k_high / N/m | R² |")
    lines.append("|------|------|---------|------------------|------------------|-------------|-----|")
    groups = ["linker2-paa", "k80-linker1-paa", "k80-linker1-PFNA", "k80-linker1-SDBS", "k80-linker2-paa"]
    for g in groups:
        sub = mod_group[mod_group["group"] == g]
        if sub.empty:
            continue
        row = sub.iloc[0]
        date = int(row["date"])
        label = display_group(g)
        n = int(row["n_valid_model"])
        e50 = f"{fmt(row['E_app_50nm_MPa_median'], 3)} [{fmt(row['E_app_50nm_MPa_q1'], 3)}, {fmt(row['E_app_50nm_MPa_q3'], 3)}]"
        e80 = fmt(row['E_app_80nm_MPa_median'], 3)
        khigh = fmt(row['high_stiffness_N_m_median'], 3)
        r2 = fmt(row['membrane_r2_median'], 3)
        lines.append(f"| {date} | {label} | {n} | {e50} | {e80} | {khigh} | {r2} |")
    return "\n".join(lines)


def append_progress_md(data, tables):
    """Append a timestamped section to progress.md at repo root."""
    pair = data["pair"]
    assert isinstance(pair, pd.DataFrame)

    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M")
    ts_compact = now.strftime("%Y%m%d-%H%M")

    lines = []
    def w(s=""):
        lines.append(s)

    if not PROGRESS_MD.exists():
        w("# AFM 二维聚合物薄膜力学分析 — 进度记录")
        w()
        w("> 自动生成的分析日志。每次运行追加新章节。")
        w()
        w("## 项目概览")
        w()
        w("- **样品**: JJS (<10nm 非晶COF薄膜, SiN孔), linker系列 (50-80nm 结晶COF, 铜网), k80系列 (50-80nm, 铜网)")
        w("- **探针**: RTESPA-150 (R=8nm, k=7N/m), DDESP-V2 (R=100nm, k=89N/m)")
        w("- **关键修正**: extend=approach/loading, retract=unloading/pull-off (2026-04-25 RealRaw 分支分离)")
        w(f"- **核心发现**: JJS retract pull-off ~{tables['jjs_retract']} nN >> extend snap-in ~{tables['jjs_extend']} nN (~{tables['jjs_ratio']}x), 液桥-膜顺应性耦合放大")
        w()
        w("---")
        w()

    w(f"## 运行记录")
    w()
    w(f"### {timestamp} — 自动分析 #{ts_compact}")
    w()
    w(f"**数据**: RealRaw/20260409 (JJS, 11 pairs), RealRaw/20260415 (linker, 69 pairs), RealRaw/20260416 (k80, 49 pairs)")
    w()
    w("**关键结果**:")
    w()
    w(f"- JJS extend snap-in: **{tables['jjs_extend']} nN** [{tables['jjs_extend_iqr']} nN]")
    w(f"- JJS retract pull-off: **{tables['jjs_retract']} nN** [{tables['jjs_retract_iqr']} nN]")
    w(f"- pull-off/snap-in ratio: **{tables['jjs_ratio']}x**")
    w(f"- 理论参考 vdW+capillary (R=8nm): **{tables['theory_sum']} nN**")
    w(f"- extend/理论比值: **{float(tables['jjs_extend'])/float(tables['theory_sum']):.1f}x** — 同量级")
    w()
    w("**apparent modulus ranking (k80 系列)**: PAA > PFNA > SDBS")
    w()
    w("**讨论**:")
    w()
    w("- JJS 接近段吸引力 (~17 nN) 只需略大的有效润湿半径或亲水界面即可解释，不需要 40x Hamaker 增强")
    w("- 真正的强信号是 retract pull-off (~116 nN)，属于接触后液桥拉伸/接触线钉扎导致的粘附滞后")
    w("- 当前数据支持限域水桥作为候选机制，但不能独立分离 solvation force 和静电力")
    w("- 缺少湿度控制和悬浮/支撑对比实验，无法证伪替代解释")
    w("- k80 系列的 SDBS 组 N=3，统计意义极弱，只能做趋势讨论")
    w()
    w("**文献参考**:")
    w()
    w("- Butt, Cappella, Kappl. *Surface Science Reports* 2005 — AFM 力测量综述")
    w("- Israelachvili. *Intermolecular and Surface Forces* 2011 — 毛细力/液桥经典")
    w("- Lee et al. *Science* 2008 — 石墨烯 AFM 压入力学")
    w("- Xiong et al. *Chemical Science* 2025 — 2D COF 本征力学性能")
    w()
    w("**完整报告**: [afm_scientific_report.md](JJS_project/reports/realraw/scientific_report/afm_scientific_report.md)")
    w()
    w("**关键图表**:")
    w()
    rel = "JJS_project/reports/realraw/scientific_report"
    w(f"![approach_theory]({rel}/approach_theory_comparison.png)")
    w(f"![branch_comparison]({rel}/branch_force_comparison.png)")
    w(f"![hysteresis]({rel}/hysteresis_ratio_work.png)")
    w(f"![modulus_ranking]({rel}/apparent_modulus_ranking.png)")
    w()

    # Write to progress.md
    content = "\n".join(lines)
    if PROGRESS_MD.exists():
        existing = PROGRESS_MD.read_text(encoding="utf-8")
        # Extract only the new run entry (skip header + project overview if already exists)
        run_section_start = content.find(f"### {timestamp}")
        if run_section_start > 0:
            new_entry = content[run_section_start:]
            PROGRESS_MD.write_text(existing.rstrip() + "\n\n" + new_entry + "\n", encoding="utf-8")
        else:
            PROGRESS_MD.write_text(existing.rstrip() + "\n\n" + content + "\n", encoding="utf-8")
    else:
        PROGRESS_MD.write_text(content, encoding="utf-8")
    return PROGRESS_MD



def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    setup_style()
    data = read_data()
    pair = data["pair"]
    points = data["points"]
    mod_curves = data["mod_curves"]
    mod_group = data["mod_group"]
    metrics = data["metrics"]
    assert isinstance(pair, pd.DataFrame)
    assert isinstance(points, pd.DataFrame)
    assert isinstance(mod_curves, pd.DataFrame)
    assert isinstance(mod_group, pd.DataFrame)
    assert isinstance(metrics, dict)

    plot_workflow()
    plot_approach_theory(metrics)
    plot_branch_comparison(pair)
    plot_adhesion_hysteresis(pair)
    plot_hysteresis_ratio_work(pair)
    plot_adhesion_ranking(pair)
    plot_stitch_examples(points, mod_curves)
    plot_slip_event_map(mod_curves)
    plot_model_fits(points, mod_curves)
    plot_modulus_ranking(mod_curves, mod_group)
    plot_stiffness_vs_modulus(mod_curves)
    plot_errorbar_statistics(mod_curves)
    plot_literature_comparison(metrics)

    tables = build_summary_tables(data)
    md_path = generate_markdown_report(data, tables)
    progress_path = append_progress_md(data, tables)

    print(f"Markdown report: {md_path}")
    print(f"Progress log:   {progress_path}")


if __name__ == "__main__":
    main()
