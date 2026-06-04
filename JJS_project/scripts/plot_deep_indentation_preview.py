#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate visual previews for deep-indentation RealRaw curves."""

from pathlib import Path
import sys

import numpy as np
import pandas as pd

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from cleaning import load_raw  # noqa: E402
from run_realraw_analysis import _baseline_for_branch, segment_curve  # noqa: E402


OUTDIR = ROOT / "reports" / "realraw" / "deep_indentation_preview"
CURVE_CSV = ROOT / "results" / "realraw" / "curve_features.csv"

COLORS = {
    "JJS": "#474747",
    "linker1-PFPE-OH": "#0C5DA5",
    "linker1-nls": "#845B97",
    "linker1-paa": "#FF9500",
    "linker2-paa": "#00B945",
    "k80-linker1-PFNA": "#0C5DA5",
    "k80-linker1-SDBS": "#845B97",
    "k80-linker1-paa": "#E8204E",
    "k80-linker2-paa": "#00B945",
}


def label_group(row):
    if row["sample"] == "JJS":
        return "JJS"
    parts = [x for x in (row["sample"], row["linker"], row["surfactant"]) if isinstance(x, str) and x != "nan"]
    if len(parts) >= 3 and parts[0] == parts[1]:
        parts = [parts[0], parts[2]]
    return "-".join(parts)


def smooth(y, window=7):
    if len(y) < window:
        return y
    kernel = np.ones(window) / window
    return np.convolve(y, kernel, mode="same")


def load_processed_curve(row):
    fp = Path(row["source_path"])
    raw = load_raw(fp, branch="extend")
    z = np.asarray(raw["z_nm"], dtype=float)
    f = np.asarray(raw["force_nN"], dtype=float)
    f_corr, *_ = _baseline_for_branch(z, f, "extend")
    if f_corr is None:
        return None
    seg = segment_curve(z, f_corr)
    contact_idx = seg["contact_idx"]
    if contact_idx >= len(z) - 2:
        return None
    z_post = z[contact_idx:]
    f_post = f_corr[contact_idx:]
    k = float(row["cantilever_stiffness_N_m"])
    delta = (z_post - z_post[0]) - f_post / (k * 1000.0)
    return delta, f_post, z, f_corr, seg


def plot_candidate_map(df):
    fig, ax = plt.subplots(figsize=(7.0, 4.8))
    valid = df[df["valid"] == True].copy()  # noqa: E712
    valid = valid[np.isfinite(valid["max_indentation_nm"]) & np.isfinite(valid["max_repulsive_force_nN"])]
    for group, grp in valid.groupby("group"):
        ax.scatter(
            grp["max_indentation_nm"],
            grp["max_repulsive_force_nN"],
            s=38,
            alpha=0.75,
            color=COLORS.get(group, "#555555"),
            label=group,
            edgecolor="white",
            linewidth=0.4,
        )
    ax.set_xscale("symlog", linthresh=10)
    ax.set_yscale("symlog", linthresh=1)
    ax.axvline(50, color="black", lw=1, ls="--", alpha=0.6)
    ax.axhline(50, color="black", lw=1, ls=":", alpha=0.6)
    ax.text(55, 0.7, "deep indentation threshold ~50 nm", fontsize=8)
    ax.set_xlabel("Max indentation after contact (nm)")
    ax.set_ylabel("Max repulsive force (nN)")
    ax.set_title("Deep-indentation candidates across RealRaw extend curves")
    ax.legend(fontsize=7, frameon=False, ncol=2)
    fig.tight_layout()
    fig.savefig(OUTDIR / "deep_indentation_candidate_map.png", dpi=220)
    plt.close(fig)


def plot_k80_representatives(df):
    fig, axes = plt.subplots(1, 2, figsize=(10.0, 4.2))
    valid = df[(df["date"] == 20260416) & (df["valid"] == True)].copy()  # noqa: E712
    selected = []
    for group in ["k80-linker1-paa", "k80-linker1-PFNA", "k80-linker1-SDBS"]:
        grp = valid[valid["group"] == group].sort_values("max_repulsive_force_nN", ascending=False).head(4)
        selected.append(grp)
    selected = pd.concat(selected, ignore_index=True)
    for _, row in selected.iterrows():
        processed = load_processed_curve(row)
        if processed is None:
            continue
        delta, force, *_ = processed
        group = row["group"]
        label = f"{group} {int(row['displacement_nm'])}nm"
        axes[0].plot(delta, smooth(force), color=COLORS.get(group), alpha=0.8, lw=1.2, label=label)
        zoom = delta <= 2500
        axes[1].plot(delta[zoom], smooth(force[zoom]), color=COLORS.get(group), alpha=0.8, lw=1.2)
    for ax in axes:
        ax.axhline(0, color="black", lw=0.7, ls="--")
        ax.set_xlabel("Cantilever-corrected indentation (nm)")
        ax.set_ylabel("Force (nN)")
        ax.grid(alpha=0.2)
    axes[0].set_title("k80 deep indentation: full post-contact branch")
    axes[1].set_title("k80 zoom: first 2.5 um after contact")
    axes[0].legend(fontsize=6, frameon=False)
    fig.tight_layout()
    fig.savefig(OUTDIR / "k80_deep_indentation_representatives.png", dpi=220)
    plt.close(fig)


def plot_20260415_representatives(df):
    fig, axes = plt.subplots(1, 2, figsize=(10.0, 4.2))
    valid = df[(df["date"] == 20260415) & (df["valid"] == True)].copy()  # noqa: E712
    selected = []
    for group in ["linker2-paa", "linker1-PFPE-OH", "linker1-paa"]:
        grp = valid[valid["group"] == group].sort_values("max_indentation_nm", ascending=False).head(4)
        selected.append(grp)
    selected = pd.concat(selected, ignore_index=True)
    for _, row in selected.iterrows():
        processed = load_processed_curve(row)
        if processed is None:
            continue
        delta, force, *_ = processed
        group = row["group"]
        axes[0].plot(delta, smooth(force), color=COLORS.get(group), alpha=0.85, lw=1.2, label=f"{group} {int(row['displacement_nm'])}nm")
        zoom = delta <= 1200
        axes[1].plot(delta[zoom], smooth(force[zoom]), color=COLORS.get(group), alpha=0.85, lw=1.2)
    for ax in axes:
        ax.axhline(0, color="black", lw=0.7, ls="--")
        ax.set_xlabel("Cantilever-corrected indentation (nm)")
        ax.set_ylabel("Force (nN)")
        ax.grid(alpha=0.2)
    axes[0].set_title("20260415 thick-film deep/toe indentation")
    axes[1].set_title("20260415 zoom: first 1.2 um")
    axes[0].legend(fontsize=6, frameon=False)
    fig.tight_layout()
    fig.savefig(OUTDIR / "linker_20260415_deep_indentation_representatives.png", dpi=220)
    plt.close(fig)


def plot_stiffness_summary(df):
    fig, ax = plt.subplots(figsize=(7.0, 4.4))
    valid = df[(df["valid"] == True) & np.isfinite(df["loading_stiffness_nN_per_nm"])].copy()  # noqa: E712
    order = (
        valid.groupby("group")["loading_stiffness_nN_per_nm"]
        .median()
        .sort_values()
        .index.tolist()
    )
    y = np.arange(len(order))
    med = [valid[valid["group"] == g]["loading_stiffness_nN_per_nm"].median() for g in order]
    q25 = [valid[valid["group"] == g]["loading_stiffness_nN_per_nm"].quantile(0.25) for g in order]
    q75 = [valid[valid["group"] == g]["loading_stiffness_nN_per_nm"].quantile(0.75) for g in order]
    ax.barh(y, med, color=[COLORS.get(g, "#555555") for g in order], alpha=0.85)
    for yi, lo, hi in zip(y, q25, q75):
        ax.hlines(yi, lo, hi, color="black", lw=1)
    ax.set_xscale("symlog", linthresh=0.01)
    ax.set_yticks(y)
    ax.set_yticklabels(order)
    ax.set_xlabel("Post-contact loading stiffness (nN/nm = N/m), median with IQR")
    ax.set_title("Apparent stiffness from deep/toe indentation")
    fig.tight_layout()
    fig.savefig(OUTDIR / "deep_indentation_stiffness_summary.png", dpi=220)
    plt.close(fig)


def write_summary(df):
    valid = df[df["valid"] == True].copy()  # noqa: E712
    summary = (
        valid.groupby(["date", "group"])
        .agg(
            n=("file", "count"),
            median_indent_nm=("max_indentation_nm", "median"),
            max_indent_nm=("max_indentation_nm", "max"),
            median_force_nN=("max_repulsive_force_nN", "median"),
            max_force_nN=("max_repulsive_force_nN", "max"),
            median_stiffness_N_m=("loading_stiffness_nN_per_nm", "median"),
            max_stiffness_N_m=("loading_stiffness_nN_per_nm", "max"),
        )
        .reset_index()
    )
    summary.to_csv(OUTDIR / "deep_indentation_summary.csv", index=False)
    top = valid.sort_values(["max_repulsive_force_nN", "max_indentation_nm"], ascending=False).head(30)
    top.to_csv(OUTDIR / "deep_indentation_top_curves.csv", index=False)


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(CURVE_CSV)
    df = df[df["branch"] == "extend"].copy()
    df["group"] = df.apply(label_group, axis=1)
    plot_candidate_map(df)
    plot_k80_representatives(df)
    plot_20260415_representatives(df)
    plot_stiffness_summary(df)
    write_summary(df)
    print(f"Wrote previews to {OUTDIR}")


if __name__ == "__main__":
    main()
