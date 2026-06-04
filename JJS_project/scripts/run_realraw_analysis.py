#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Branch-aware RealRaw AFM reanalysis.

This pipeline treats RealRaw/*/extend as approach/loading and RealRaw/*/retract
as unloading. Outputs are isolated under results/realraw and reports/realraw.
"""

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from cleaning import correct_baseline, load_raw, segment_curve  # noqa: E402
from dataset_registry import get_config  # noqa: E402


RESULTS_DIR = ROOT / "results" / "realraw"
REPORTS_DIR = ROOT / "reports" / "realraw"
NANOSCOPE_SUFFIX = " - NanoScope Analysis.txt"


def parse_filename(name):
    """Extract sample/linker/surfactant/displacement/setpoint from common filenames."""
    base = name.replace(NANOSCOPE_SUFFIX, "").replace(".spm", "")
    parts = [p for p in base.split("-") if p != ""]
    out = {
        "base_name": base,
        "sample": None,
        "linker": None,
        "surfactant": None,
        "scan_size_nm": None,
        "displacement_nm": None,
        "setpoint": None,
        "parse_warnings": [],
    }

    nm_vals = [float(x) for x in re.findall(r"(?<![A-Za-z])(\d+(?:\.\d+)?)nm", base)]
    force_m = re.search(r"(\d+(?:\.\d+)?)(nN|uN|μN|pN)(?:-\d+)?$", base)

    if nm_vals:
        out["displacement_nm"] = nm_vals[-1]
        if len(nm_vals) >= 2:
            out["scan_size_nm"] = nm_vals[-2]
    else:
        out["parse_warnings"].append("missing_displacement")

    if force_m:
        out["setpoint"] = f"{force_m.group(1)}{force_m.group(2)}"
    else:
        out["parse_warnings"].append("missing_setpoint")

    lower_parts = [p.lower() for p in parts]
    if parts and lower_parts[0] == "jjs":
        out["sample"] = "JJS"
        out["surfactant"] = "JJS"
    elif parts and lower_parts[0].startswith("k80"):
        out["sample"] = "k80"
        out["linker"] = parts[1] if len(parts) > 1 else None
        out["surfactant"] = parts[2] if len(parts) > 2 else None
    elif parts and lower_parts[0].startswith("linker"):
        out["sample"] = parts[0]
        out["linker"] = parts[0]
        surf_tokens = []
        for token in parts[1:]:
            if re.search(r"\d+(?:\.\d+)?(nm|nN|uN|μN|pN)", token):
                break
            surf_tokens.append(token)
        out["surfactant"] = "-".join(surf_tokens) if surf_tokens else None
    else:
        out["sample"] = parts[0] if parts else base
        out["parse_warnings"].append("unrecognized_name_shape")

    return out


def list_dates(realraw_dir):
    return sorted(p.name for p in realraw_dir.iterdir() if p.is_dir())


def pair_files(realraw_dir, dates=None, sample_filter=None):
    """Return paired RealRaw file records keyed by date and filename."""
    pairs = {}
    selected_dates = dates or list_dates(realraw_dir)
    for date in selected_dates:
        date_dir = realraw_dir / date
        for branch in ("extend", "retract"):
            branch_dir = date_dir / branch
            if not branch_dir.exists():
                continue
            for fp in sorted(branch_dir.glob("*.txt")):
                if "NanoScope Analysis" not in fp.name:
                    continue
                parsed = parse_filename(fp.name)
                sample_text = " ".join(
                    str(parsed.get(k) or "") for k in ("sample", "linker", "surfactant", "base_name")
                ).lower()
                if sample_filter and sample_filter.lower() not in sample_text:
                    continue
                key = (date, fp.name)
                pairs.setdefault(key, {"date": date, "file": fp.name, "extend": None, "retract": None})
                pairs[key][branch] = fp
    return pairs


def _baseline_for_branch(z, f, branch):
    """Prefer far-field low-Z baseline; fall back to first/last 15% if needed."""
    f_corr, slope, intercept, n_points, status = correct_baseline(z, f)
    if f_corr is not None:
        return f_corr, slope, intercept, n_points, status

    n = len(z)
    if n < 3:
        return None, 0.0, 0.0, n, "discarded: points < 3"

    window = max(3, int(round(n * 0.15)))
    idx = np.arange(window) if branch == "extend" else np.arange(n - window, n)
    if len(idx) >= 5:
        slope, intercept = np.polyfit(z[idx], f[idx], 1)
        status = f"OK_{branch}_edge"
    else:
        slope, intercept = 0.0, float(np.mean(f[idx]))
        status = f"OK_{branch}_edge_const"
    return f - (slope * z + intercept), float(slope), float(intercept), int(len(idx)), status


def _post_contact_features(z, f_corr, contact_idx, k_cantilever):
    if contact_idx is None or contact_idx >= len(z):
        return 0, np.nan, np.nan, np.nan
    mask = np.arange(len(z)) >= contact_idx
    mask &= f_corr >= 0
    n_rep = int(np.sum(mask))
    if n_rep < 2:
        return n_rep, np.nan, np.nan, float(np.nanmax(f_corr)) if len(f_corr) else np.nan
    z_rep = z[mask]
    f_rep = f_corr[mask]
    delta_raw = z_rep - z_rep[0]
    deflection_nm = f_rep / (k_cantilever * 1000.0) if k_cantilever else 0.0
    delta = delta_raw - deflection_nm
    stiffness = float(np.polyfit(delta, f_rep, 1)[0]) if len(delta) >= 3 and np.ptp(delta) > 0 else np.nan
    return n_rep, float(np.nanmax(delta)), float(stiffness), float(np.nanmax(f_rep))


def analyze_curve(fp, date, branch, cfg):
    raw = load_raw(fp, branch=branch)
    z = np.asarray(raw["z_nm"], dtype=float)
    f = np.asarray(raw["force_nN"], dtype=float)
    parsed = parse_filename(fp.name)
    warnings = list(parsed["parse_warnings"])

    f_corr, slope, intercept, n_base, baseline_status = _baseline_for_branch(z, f, branch)
    if f_corr is None:
        warnings.append(baseline_status)
        f_corr = np.full_like(f, np.nan)
    elif baseline_status.startswith("discarded"):
        warnings.append(baseline_status)

    row = {
        "date": date,
        "branch": branch,
        "file": fp.name,
        "source_path": str(fp),
        "direction": raw["direction"],
        "time_direction": raw["time_direction"],
        "n_points": int(len(z)),
        "sample": parsed["sample"],
        "linker": parsed["linker"],
        "surfactant": parsed["surfactant"],
        "scan_size_nm": parsed["scan_size_nm"],
        "displacement_nm": parsed["displacement_nm"] or raw["meta"].get("piezo_displacement"),
        "setpoint": parsed["setpoint"]
        or (
            f"{raw['meta']['setpoint_force']}{raw['meta']['setpoint_unit']}"
            if raw["meta"].get("setpoint_force")
            else None
        ),
        "probe_model": cfg["probe_model"],
        "probe_radius_nm": cfg["probe_radius_nm"],
        "cantilever_stiffness_N_m": cfg["cantilever_stiffness_N_m"],
        "baseline_slope": slope,
        "baseline_intercept": intercept,
        "baseline_points": n_base,
        "baseline_status": baseline_status,
        "min_force_nN": float(np.nanmin(f_corr)) if len(f_corr) else np.nan,
        "max_force_nN": float(np.nanmax(f_corr)) if len(f_corr) else np.nan,
        "snap_f_nN": np.nan,
        "snap_z_nm": np.nan,
        "contact_z_nm": np.nan,
        "contact_f_nN": np.nan,
        "pull_off_f_nN": np.nan,
        "pull_off_z_nm": np.nan,
        "repulsive_points": 0,
        "max_indentation_nm": np.nan,
        "loading_stiffness_nN_per_nm": np.nan,
        "max_repulsive_force_nN": np.nan,
        "work_area_nN_nm": float(np.trapezoid(f_corr, z)) if len(z) >= 2 and np.all(np.isfinite(f_corr)) else np.nan,
        "warnings": "",
        "valid": True,
    }

    if not np.all(np.isfinite(f_corr)):
        row["valid"] = False
        row["warnings"] = ";".join(warnings)
        return row, {"z": z, "f_corr": f_corr, "raw": raw}

    if branch == "extend":
        seg = segment_curve(z, f_corr)
        n_rep, max_delta, stiffness, max_rep = _post_contact_features(
            z, f_corr, seg["contact_idx"], cfg["cantilever_stiffness_N_m"]
        )
        row.update(
            {
                "snap_f_nN": seg["snap_f"],
                "snap_z_nm": seg["snap_z"],
                "contact_z_nm": seg["contact_z"],
                "contact_f_nN": seg["contact_f"],
                "repulsive_points": n_rep,
                "max_indentation_nm": max_delta,
                "loading_stiffness_nN_per_nm": stiffness,
                "max_repulsive_force_nN": max_rep,
            }
        )
        if seg["snap_f"] >= 0:
            warnings.append("no_negative_snapin")
        if row["direction"] != "inc":
            warnings.append("extend_not_increasing_z")
    else:
        pull_idx = int(np.nanargmin(f_corr))
        row.update(
            {
                "pull_off_f_nN": float(f_corr[pull_idx]),
                "pull_off_z_nm": float(z[pull_idx]),
            }
        )
        if row["direction"] != "dec":
            warnings.append("retract_not_decreasing_z")

    row["warnings"] = ";".join(warnings)
    row["valid"] = len([w for w in warnings if w.startswith("discarded")]) == 0
    return row, {"z": z, "f_corr": f_corr, "raw": raw}


def analyze_pair(record, cfg):
    pair_status = "paired"
    if record["extend"] is None:
        pair_status = "missing_extend"
    elif record["retract"] is None:
        pair_status = "missing_retract"

    curve_rows = []
    curve_data = {}
    for branch in ("extend", "retract"):
        fp = record[branch]
        if fp is None:
            continue
        row, data = analyze_curve(fp, record["date"], branch, cfg)
        curve_rows.append(row)
        curve_data[branch] = data

    ext = next((r for r in curve_rows if r["branch"] == "extend"), None)
    ret = next((r for r in curve_rows if r["branch"] == "retract"), None)
    parsed = parse_filename(record["file"])
    pair_row = {
        "date": record["date"],
        "file": record["file"],
        "pair_status": pair_status,
        "sample": parsed["sample"],
        "linker": parsed["linker"],
        "surfactant": parsed["surfactant"],
        "displacement_nm": parsed["displacement_nm"],
        "setpoint": parsed["setpoint"],
        "extend_snap_f_nN": ext["snap_f_nN"] if ext else np.nan,
        "extend_snap_z_nm": ext["snap_z_nm"] if ext else np.nan,
        "extend_contact_z_nm": ext["contact_z_nm"] if ext else np.nan,
        "extend_max_force_nN": ext["max_force_nN"] if ext else np.nan,
        "retract_pull_off_f_nN": ret["pull_off_f_nN"] if ret else np.nan,
        "retract_pull_off_z_nm": ret["pull_off_z_nm"] if ret else np.nan,
        "retract_min_force_nN": ret["min_force_nN"] if ret else np.nan,
        "force_min_delta_nN": np.nan,
        "work_extend_nN_nm": ext["work_area_nN_nm"] if ext else np.nan,
        "work_retract_nN_nm": ret["work_area_nN_nm"] if ret else np.nan,
        "hysteresis_work_nN_nm": np.nan,
        "warnings": "",
    }
    if ext and ret:
        pair_row["force_min_delta_nN"] = ext["min_force_nN"] - ret["min_force_nN"]
        pair_row["hysteresis_work_nN_nm"] = ext["work_area_nN_nm"] - ret["work_area_nN_nm"]
    warnings = []
    if ext and ext["warnings"]:
        warnings.append("extend:" + ext["warnings"])
    if ret and ret["warnings"]:
        warnings.append("retract:" + ret["warnings"])
    pair_row["warnings"] = "|".join(warnings)
    return curve_rows, pair_row, curve_data


def plot_overview(curve_df, curves_by_key, outpath, title):
    fig, ax = plt.subplots(figsize=(8.0, 5.0))
    colors = {"extend": "#0C5DA5", "retract": "#E8204E"}
    plotted = set()
    for _, row in curve_df.iterrows():
        key = (row["date"], row["file"], row["branch"])
        data = curves_by_key.get(key)
        if data is None:
            continue
        label = row["branch"] if row["branch"] not in plotted else None
        plotted.add(row["branch"])
        ax.plot(data["z"], data["f_corr"], color=colors.get(row["branch"], "0.4"), alpha=0.35, lw=0.8, label=label)
    ax.axhline(0, color="black", lw=0.7, ls="--")
    ax.set_xlabel("Z (nm)")
    ax.set_ylabel("Baseline-corrected force (nN)")
    ax.set_title(title)
    if plotted:
        ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(outpath)
    plt.close(fig)


def plot_paired_overlay(pair_df, curves_by_key, outpath, title, max_pairs=24):
    paired = pair_df[pair_df["pair_status"] == "paired"].head(max_pairs)
    if paired.empty:
        return
    n_cols = 3
    n_rows = int(np.ceil(len(paired) / n_cols))
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(10.5, max(3.2, 2.8 * n_rows)), squeeze=False)
    axes = axes.ravel()
    for ax, (_, row) in zip(axes, paired.iterrows()):
        for branch, color in (("extend", "#0C5DA5"), ("retract", "#E8204E")):
            data = curves_by_key.get((row["date"], row["file"], branch))
            if data is not None:
                ax.plot(data["z"], data["f_corr"], color=color, lw=1.0, label=branch)
        ax.axhline(0, color="black", lw=0.5, ls="--")
        ax.set_title(str(row["file"]).replace(NANOSCOPE_SUFFIX, "")[:38], fontsize=7)
        ax.tick_params(labelsize=7)
    for ax in axes[len(paired) :]:
        ax.axis("off")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper right", frameon=False)
    fig.suptitle(title)
    fig.tight_layout(rect=[0, 0, 0.98, 0.96])
    fig.savefig(outpath)
    plt.close(fig)


def plot_mechanics_summary(pair_df, outpath, title):
    if pair_df.empty:
        return
    fig, axes = plt.subplots(1, 3, figsize=(11.0, 3.6))
    df = pair_df.copy()
    df["label"] = df["file"].str.replace(NANOSCOPE_SUFFIX, "", regex=False).str.replace(".spm", "", regex=False)
    df = df.sort_values(["sample", "displacement_nm", "setpoint"], na_position="last")
    x = np.arange(len(df))
    axes[0].bar(x, df["extend_snap_f_nN"].abs(), color="#0C5DA5")
    axes[0].set_ylabel("|extend snap| (nN)")
    axes[1].bar(x, df["retract_pull_off_f_nN"].abs(), color="#E8204E")
    axes[1].set_ylabel("|retract pull-off| (nN)")
    axes[2].bar(x, df["hysteresis_work_nN_nm"], color="#00B945")
    axes[2].set_ylabel("Work difference (nN nm)")
    for ax in axes:
        ax.set_xticks(x)
        ax.set_xticklabels(df["label"], rotation=90, fontsize=5)
        ax.tick_params(axis="y", labelsize=8)
    fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(outpath)
    plt.close(fig)


def write_outputs(curve_rows, pair_rows, curves_by_key, manifest, dry_run=False):
    curve_df = pd.DataFrame(curve_rows)
    pair_df = pd.DataFrame(pair_rows)

    if dry_run:
        print(f"[Dry run] Would write {len(curve_df)} curve rows and {len(pair_df)} pair rows.")
        return curve_df, pair_df

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    curve_df.to_csv(RESULTS_DIR / "curve_features.csv", index=False)
    pair_df.to_csv(RESULTS_DIR / "pair_features.csv", index=False)

    qc_rows = []
    if not curve_df.empty:
        for (date, branch), grp in curve_df.groupby(["date", "branch"]):
            qc_rows.append(
                {
                    "date": date,
                    "branch": branch,
                    "curves": len(grp),
                    "valid": int(grp["valid"].sum()),
                    "warnings": int(grp["warnings"].astype(bool).sum()),
                    "directions": json.dumps(dict(Counter(grp["direction"])), ensure_ascii=False),
                }
            )
    if not pair_df.empty:
        for date, grp in pair_df.groupby("date"):
            qc_rows.append(
                {
                    "date": date,
                    "branch": "pairs",
                    "curves": len(grp),
                    "valid": int((grp["pair_status"] == "paired").sum()),
                    "warnings": int(grp["warnings"].astype(bool).sum()),
                    "directions": json.dumps(dict(Counter(grp["pair_status"])), ensure_ascii=False),
                }
            )
    pd.DataFrame(qc_rows).to_csv(RESULTS_DIR / "qc_summary.csv", index=False)

    manifest_path = RESULTS_DIR / "analysis_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    for date in sorted(curve_df["date"].dropna().unique()):
        cdf = curve_df[curve_df["date"] == date]
        pdf = pair_df[pair_df["date"] == date]
        plot_overview(cdf, curves_by_key, REPORTS_DIR / f"{date}_overview.pdf", f"RealRaw {date} overview")
        plot_paired_overlay(pdf, curves_by_key, REPORTS_DIR / f"{date}_paired_overlay.pdf", f"RealRaw {date} paired curves")
        plot_mechanics_summary(pdf, REPORTS_DIR / f"{date}_mechanics_summary.pdf", f"RealRaw {date} summary")

    print(f"Wrote {RESULTS_DIR / 'curve_features.csv'}")
    print(f"Wrote {RESULTS_DIR / 'pair_features.csv'}")
    print(f"Wrote {RESULTS_DIR / 'qc_summary.csv'}")
    print(f"Wrote {manifest_path}")
    print(f"Wrote PDF reports in {REPORTS_DIR}")
    return curve_df, pair_df


def config_for_date(date):
    key = f"RealRaw/{date}"
    try:
        return get_config(key)
    except KeyError:
        if date == "20260416":
            return get_config("20260416原始数据")
        if date == "20260415":
            return get_config("20260415原始数据")
        return get_config("20260409")


def run(args):
    realraw_dir = ROOT / "RealRaw"
    if not realraw_dir.exists():
        raise FileNotFoundError(f"Missing RealRaw directory: {realraw_dir}")

    dates = None
    if args.date:
        dates = args.date
    elif not args.all:
        dates = list_dates(realraw_dir)

    pairs = pair_files(realraw_dir, dates=dates, sample_filter=args.sample)
    print(f"Matched {len(pairs)} file pair records.")
    if args.dry_run:
        status = Counter(
            "paired" if r["extend"] and r["retract"] else "missing_extend" if not r["extend"] else "missing_retract"
            for r in pairs.values()
        )
        print("Pair status:", dict(status))

    curve_rows = []
    pair_rows = []
    curves_by_key = {}
    for record in sorted(pairs.values(), key=lambda r: (r["date"], r["file"])):
        cfg = config_for_date(record["date"])
        c_rows, p_row, c_data = analyze_pair(record, cfg)
        curve_rows.extend(c_rows)
        pair_rows.append(p_row)
        for branch, data in c_data.items():
            curves_by_key[(record["date"], record["file"], branch)] = data

    manifest = {
        "realraw_dir": str(realraw_dir),
        "dates": sorted({r["date"] for r in pairs.values()}),
        "sample_filter": args.sample,
        "pair_records": len(pair_rows),
        "curve_records": len(curve_rows),
        "assumptions": {
            "extend": "approach/loading primary analysis branch",
            "retract": "unloading branch for adhesion hysteresis and recovery",
            "outputs": "isolated under results/realraw and reports/realraw",
        },
    }
    return write_outputs(curve_rows, pair_rows, curves_by_key, manifest, dry_run=args.dry_run)


def main():
    parser = argparse.ArgumentParser(description="Branch-aware RealRaw AFM reanalysis")
    parser.add_argument("--date", action="append", help="Analyze one date, e.g. 20260415. Can be repeated.")
    parser.add_argument("--sample", help="Filter by sample/linker/surfactant text, e.g. k80 or PFPE.")
    parser.add_argument("--all", action="store_true", help="Analyze all RealRaw dates.")
    parser.add_argument("--dry-run", action="store_true", help="Analyze in memory but do not write outputs.")
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
