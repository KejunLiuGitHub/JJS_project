#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automatic stitching of recoverable slip events in deep-indentation AFM curves.

The stitched curve is an analysis product: raw points are preserved, recoverable
stick-slip drops are vertically offset for continuous loading fits, and terminal
cliff/rupture events are truncated rather than repaired.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from scipy.signal import medfilt, savgol_filter
from scipy.stats import median_abs_deviation

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from cleaning import load_raw  # noqa: E402
from run_realraw_analysis import _baseline_for_branch, segment_curve  # noqa: E402


RESULTS_DIR = ROOT / "results" / "realraw"
REPORT_DIR = ROOT / "reports" / "realraw" / "deep_stitched"
CURVE_CSV = RESULTS_DIR / "curve_features.csv"

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


@dataclass
class StitchParams:
    force_abs_min_20260415: float = 2.0
    force_abs_min_20260416: float = 50.0
    local_fraction: float = 0.08
    noise_multiplier: float = 5.0
    recovery_fraction: float = 0.70
    recovery_window: int = 18
    pre_window: int = 5
    post_window: int = 5
    terminal_tail_fraction: float = 0.12
    deep_indent_threshold_nm: float = 50.0
    deep_force_threshold_nN: float = 10.0


def label_group(row: pd.Series) -> str:
    if row["sample"] == "JJS":
        return "JJS"
    parts = [x for x in (row["sample"], row["linker"], row["surfactant"]) if isinstance(x, str) and x != "nan"]
    if len(parts) >= 3 and parts[0] == parts[1]:
        parts = [parts[0], parts[2]]
    return "-".join(parts) if parts else "unknown"


def smooth_force(force: np.ndarray) -> np.ndarray:
    n = len(force)
    if n < 7:
        return force.copy()
    kernel = min(9, n if n % 2 == 1 else n - 1)
    if kernel >= 5:
        try:
            return savgol_filter(force, window_length=kernel, polyorder=2, mode="interp")
        except ValueError:
            pass
    kernel = max(3, min(7, n if n % 2 == 1 else n - 1))
    return medfilt(force, kernel_size=kernel)


def load_post_contact_curve(row: pd.Series) -> dict | None:
    fp = Path(row["source_path"])
    raw = load_raw(fp, branch="extend")
    z = np.asarray(raw["z_nm"], dtype=float)
    f = np.asarray(raw["force_nN"], dtype=float)
    f_corr, *_ = _baseline_for_branch(z, f, "extend")
    if f_corr is None or not np.all(np.isfinite(f_corr)):
        return None
    seg = segment_curve(z, f_corr)
    contact_idx = int(seg["contact_idx"])
    if contact_idx >= len(z) - 3:
        return None
    z_post = z[contact_idx:].astype(float)
    f_post = f_corr[contact_idx:].astype(float)
    k_c = float(row["cantilever_stiffness_N_m"])
    delta = (z_post - z_post[0]) - f_post / (k_c * 1000.0)
    order = np.argsort(delta)
    delta = delta[order]
    f_post = f_post[order]
    keep = np.isfinite(delta) & np.isfinite(f_post)
    delta = delta[keep]
    f_post = f_post[keep]
    if len(delta) < 5:
        return None
    # Remove tiny non-monotonic duplicates caused by cantilever correction.
    unique_delta, unique_idx = np.unique(delta, return_index=True)
    return {
        "delta_nm": unique_delta,
        "force_nN": f_post[unique_idx],
        "contact_idx": contact_idx,
        "raw_z_nm": z,
        "raw_force_corr_nN": f_corr,
        "seg": seg,
    }


def estimate_noise(force: np.ndarray) -> float:
    diff = np.diff(smooth_force(force))
    if len(diff) == 0:
        return 0.0
    mad = median_abs_deviation(diff, scale="normal", nan_policy="omit")
    if not np.isfinite(mad) or mad == 0:
        mad = np.nanstd(diff)
    return float(mad) if np.isfinite(mad) else 0.0


def force_abs_min_for_date(date: int, params: StitchParams) -> float:
    if int(date) == 20260416:
        return params.force_abs_min_20260416
    return params.force_abs_min_20260415


def detect_slip_events(delta: np.ndarray, force: np.ndarray, date: int, params: StitchParams) -> list[dict]:
    sm = smooth_force(force)
    diff = np.diff(sm)
    noise = estimate_noise(force)
    abs_min = force_abs_min_for_date(date, params)
    events = []
    i = 0
    n = len(force)
    while i < len(diff):
        local_force = max(float(np.nanmedian(sm[max(0, i - params.pre_window) : i + 1])), 0.0)
        threshold = max(params.noise_multiplier * noise, params.local_fraction * local_force, abs_min)
        if diff[i] < -threshold:
            start = i
            # Merge adjacent negative jumps into one event.
            end = i
            while end + 1 < len(diff) and diff[end + 1] < -0.35 * threshold:
                end += 1
            pre_slice = slice(max(0, start - params.pre_window + 1), start + 1)
            post_slice = slice(end + 1, min(n, end + 1 + params.post_window))
            pre_level = float(np.nanmedian(sm[pre_slice]))
            post_level = float(np.nanmedian(sm[post_slice])) if post_slice.start < post_slice.stop else float(sm[end + 1])
            drop = pre_level - post_level
            tail_start = end + 1
            tail = sm[tail_start:]
            recovery_level = params.recovery_fraction * max(pre_level, 0.0)
            recovered = bool(len(tail) and np.nanmax(tail) >= recovery_level)
            terminal_zone = tail_start >= int((1.0 - params.terminal_tail_fraction) * n)
            tail_low = bool(len(tail) and np.nanmedian(tail[-max(3, min(10, len(tail))) :]) < recovery_level)
            event_type = "recoverable_slip" if recovered and not terminal_zone else "terminal_cliff"
            if not recovered and tail_low:
                event_type = "terminal_cliff"
            events.append(
                {
                    "event_index": len(events),
                    "start_idx": int(start),
                    "end_idx": int(end + 1),
                    "delta_nm": float(delta[end + 1]),
                    "pre_level_nN": pre_level,
                    "post_level_nN": post_level,
                    "drop_nN": float(drop),
                    "threshold_nN": float(threshold),
                    "noise_nN": float(noise),
                    "event_type": event_type,
                    "recovered": recovered,
                }
            )
            i = end + 2
        else:
            i += 1
    return events


def stitch_curve(delta: np.ndarray, force: np.ndarray, events: list[dict]) -> tuple[pd.DataFrame, int | None]:
    n = len(force)
    cumulative = np.zeros(n, dtype=float)
    segment_id = np.zeros(n, dtype=int)
    offset = 0.0
    current_segment = 0
    rupture_idx = None
    recoverable = sorted([e for e in events if e["event_type"] == "recoverable_slip"], key=lambda e: e["end_idx"])
    terminal = [e for e in events if e["event_type"] == "terminal_cliff"]
    if terminal:
        rupture_idx = min(int(e["start_idx"]) for e in terminal)
    for e in recoverable:
        idx = int(e["end_idx"])
        if rupture_idx is not None and idx >= rupture_idx:
            continue
        offset += max(float(e["drop_nN"]), 0.0)
        current_segment += 1
        cumulative[idx:] += max(float(e["drop_nN"]), 0.0)
        segment_id[idx:] = current_segment
    keep = np.arange(n) if rupture_idx is None else np.arange(max(1, rupture_idx + 1))
    stitched = force + cumulative
    df = pd.DataFrame(
        {
            "point_idx": keep,
            "delta_nm": delta[keep],
            "raw_force_nN": force[keep],
            "stitched_force_nN": stitched[keep],
            "segment_id": segment_id[keep],
            "cumulative_offset_nN": cumulative[keep],
            "used_for_fit": stitched[keep] > 0,
        }
    )
    return df, rupture_idx


def linear_fit(x: np.ndarray, y: np.ndarray) -> tuple[float, float, float]:
    if len(x) < 3 or np.ptp(x) <= 0:
        return np.nan, np.nan, np.nan
    slope, intercept = np.polyfit(x, y, 1)
    pred = slope * x + intercept
    ss_res = np.sum((y - pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else np.nan
    return float(slope), float(intercept), float(r2)


def membrane_model(delta_nm: np.ndarray, k1: float, k3: float) -> np.ndarray:
    return k1 * delta_nm + k3 * delta_nm**3


def fit_mechanics(points: pd.DataFrame) -> dict:
    fit = points[(points["used_for_fit"]) & (points["delta_nm"] > 0) & (points["stitched_force_nN"] > 0)].copy()
    if len(fit) < 6:
        return {
            "fit_points": int(len(fit)),
            "low_stiffness_N_m": np.nan,
            "high_stiffness_N_m": np.nan,
            "stiffening_ratio": np.nan,
            "power_law_A": np.nan,
            "power_law_n": np.nan,
            "power_law_r2": np.nan,
            "membrane_k1_N_m": np.nan,
            "membrane_k3_nN_per_nm3": np.nan,
            "membrane_r2": np.nan,
        }
    x = fit["delta_nm"].to_numpy(float)
    y = fit["stitched_force_nN"].to_numpy(float)
    max_delta = float(np.max(x))
    low = fit[x <= np.quantile(x, 0.35)]
    high = fit[x >= np.quantile(x, 0.65)]
    low_slope, _, low_r2 = linear_fit(low["delta_nm"].to_numpy(float), low["stitched_force_nN"].to_numpy(float))
    high_slope, _, high_r2 = linear_fit(high["delta_nm"].to_numpy(float), high["stitched_force_nN"].to_numpy(float))
    # Robust-ish log power law: trim extreme residual leverage by fitting central positive span.
    pos = (x > 0) & (y > 0)
    logx = np.log(x[pos])
    logy = np.log(y[pos])
    if len(logx) >= 6 and np.ptp(logx) > 0:
        n_val, log_a = np.polyfit(logx, logy, 1)
        pred_log = n_val * logx + log_a
        ss_res = np.sum((logy - pred_log) ** 2)
        ss_tot = np.sum((logy - np.mean(logy)) ** 2)
        power_r2 = 1 - ss_res / ss_tot if ss_tot > 0 else np.nan
        power_a = float(np.exp(log_a))
    else:
        n_val = power_a = power_r2 = np.nan
    try:
        popt, _ = curve_fit(membrane_model, x, y, p0=[max(low_slope, 1e-6) if np.isfinite(low_slope) else 0.1, 1e-9], maxfev=20000)
        pred = membrane_model(x, *popt)
        ss_res = np.sum((y - pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        membrane_r2 = 1 - ss_res / ss_tot if ss_tot > 0 else np.nan
        k1, k3 = float(popt[0]), float(popt[1])
    except Exception:
        k1 = k3 = membrane_r2 = np.nan
    return {
        "fit_points": int(len(fit)),
        "fit_delta_max_nm": max_delta,
        "fit_force_max_nN": float(np.max(y)),
        "low_stiffness_N_m": low_slope,
        "low_stiffness_r2": low_r2,
        "high_stiffness_N_m": high_slope,
        "high_stiffness_r2": high_r2,
        "stiffening_ratio": float(high_slope / low_slope) if np.isfinite(high_slope) and np.isfinite(low_slope) and abs(low_slope) > 1e-12 else np.nan,
        "power_law_A": power_a,
        "power_law_n": float(n_val) if np.isfinite(n_val) else np.nan,
        "power_law_r2": float(power_r2) if np.isfinite(power_r2) else np.nan,
        "membrane_k1_N_m": k1,
        "membrane_k3_nN_per_nm3": k3,
        "membrane_r2": float(membrane_r2) if np.isfinite(membrane_r2) else np.nan,
    }


def candidate_rows(curve_df: pd.DataFrame, params: StitchParams) -> pd.DataFrame:
    df = curve_df[curve_df["branch"] == "extend"].copy()
    df["group"] = df.apply(label_group, axis=1)
    mask = (
        (df["valid"] == True)  # noqa: E712
        & (df["max_indentation_nm"] > params.deep_indent_threshold_nm)
        & (df["max_repulsive_force_nN"] > params.deep_force_threshold_nN)
    )
    return df[mask].sort_values(["date", "group", "max_repulsive_force_nN"], ascending=[True, True, False])


def analyze_row(row: pd.Series, params: StitchParams) -> tuple[pd.DataFrame | None, list[dict], dict | None]:
    loaded = load_post_contact_curve(row)
    if loaded is None:
        return None, [], None
    delta = loaded["delta_nm"]
    force = loaded["force_nN"]
    events = detect_slip_events(delta, force, int(row["date"]), params)
    points, rupture_idx = stitch_curve(delta, force, events)
    mechanics = fit_mechanics(points)
    curve_id = f"{int(row['date'])}::{row['file']}"
    for col in ["date", "file", "group", "sample", "linker", "surfactant", "displacement_nm", "setpoint"]:
        points[col] = row[col] if col in row else np.nan
    points["curve_id"] = curve_id
    points["rupture_idx"] = rupture_idx if rupture_idx is not None else np.nan
    event_rows = []
    for event in events:
        e = dict(event)
        e.update(
            {
                "curve_id": curve_id,
                "date": int(row["date"]),
                "file": row["file"],
                "group": row["group"],
                "displacement_nm": row["displacement_nm"],
                "setpoint": row["setpoint"],
            }
        )
        event_rows.append(e)
    mechanics.update(
        {
            "curve_id": curve_id,
            "date": int(row["date"]),
            "file": row["file"],
            "group": row["group"],
            "sample": row["sample"],
            "linker": row["linker"],
            "surfactant": row["surfactant"],
            "displacement_nm": row["displacement_nm"],
            "setpoint": row["setpoint"],
            "raw_max_indentation_nm": row["max_indentation_nm"],
            "raw_max_force_nN": row["max_repulsive_force_nN"],
            "n_slip_events": int(sum(e["event_type"] == "recoverable_slip" for e in events)),
            "n_terminal_cliffs": int(sum(e["event_type"] == "terminal_cliff" for e in events)),
            "rupture_idx": rupture_idx if rupture_idx is not None else np.nan,
            "max_cumulative_offset_nN": float(points["cumulative_offset_nN"].max()) if len(points) else 0.0,
            "model_scope": "apparent/comparative; DDESP-V2 k80 uses blunt-tip geometry",
        }
    )
    return points, event_rows, mechanics


def plot_raw_vs_stitched(points_df: pd.DataFrame, mechanics_df: pd.DataFrame, outpath: Path) -> None:
    examples = mechanics_df.sort_values(["n_slip_events", "raw_max_force_nN"], ascending=False).head(6)
    if examples.empty:
        examples = mechanics_df.sort_values("raw_max_force_nN", ascending=False).head(6)
    n = len(examples)
    if n == 0:
        return
    fig, axes = plt.subplots(int(np.ceil(n / 2)), 2, figsize=(10, 3.0 * int(np.ceil(n / 2))), squeeze=False)
    axes = axes.ravel()
    for ax, (_, row) in zip(axes, examples.iterrows()):
        pts = points_df[points_df["curve_id"] == row["curve_id"]]
        ax.plot(pts["delta_nm"], pts["raw_force_nN"], color="#999999", lw=1, alpha=0.7, label="raw")
        ax.plot(pts["delta_nm"], pts["stitched_force_nN"], color=COLORS.get(row["group"], "#E8204E"), lw=1.2, label="stitched")
        ax.set_title(f"{row['group']} {row['displacement_nm']:.0f}nm slips={row['n_slip_events']}", fontsize=8)
        ax.set_xlabel("Indentation (nm)")
        ax.set_ylabel("Force (nN)")
        ax.grid(alpha=0.2)
    for ax in axes[n:]:
        ax.axis("off")
    axes[0].legend(frameon=False, fontsize=7)
    fig.tight_layout()
    fig.savefig(outpath, dpi=220)
    plt.close(fig)


def plot_group_mechanics(points_df: pd.DataFrame, mechanics_df: pd.DataFrame, date: int, outpath: Path, title: str) -> None:
    df = mechanics_df[mechanics_df["date"] == date].copy()
    if df.empty:
        return
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2))
    for _, row in df.sort_values("raw_max_force_nN", ascending=False).head(18).iterrows():
        pts = points_df[(points_df["curve_id"] == row["curve_id"]) & (points_df["used_for_fit"])]
        if pts.empty:
            continue
        jitter = (hash(row["curve_id"]) % 17 - 8) * 0.2
        axes[0].plot(
            pts["delta_nm"] + jitter,
            pts["stitched_force_nN"],
            color=COLORS.get(row["group"], "#555555"),
            lw=1,
            alpha=0.75,
            label=row["group"],
        )
    handles, labels = axes[0].get_legend_handles_labels()
    uniq = dict(zip(labels, handles))
    axes[0].legend(uniq.values(), uniq.keys(), frameon=False, fontsize=7)
    axes[0].set_xlabel("Indentation (nm)")
    axes[0].set_ylabel("Stitched force (nN)")
    axes[0].set_title(title)
    axes[0].grid(alpha=0.2)
    groups = df.groupby("group")["high_stiffness_N_m"].median().sort_values()
    axes[1].barh(groups.index, groups.values, color=[COLORS.get(g, "#555555") for g in groups.index])
    axes[1].set_xlabel("High-force apparent stiffness (N/m)")
    axes[1].set_title("Median high-force stiffness")
    fig.tight_layout()
    fig.savefig(outpath, dpi=220)
    plt.close(fig)


def plot_ranking(mechanics_df: pd.DataFrame, outpath: Path) -> None:
    df = mechanics_df.copy()
    if df.empty:
        return
    fig, axes = plt.subplots(1, 3, figsize=(12, 4.2))
    for ax, col, label in [
        (axes[0], "high_stiffness_N_m", "High-force stiffness (N/m)"),
        (axes[1], "power_law_n", "Power-law exponent n"),
        (axes[2], "stiffening_ratio", "Stiffening ratio"),
    ]:
        vals = df.groupby("group")[col].median().replace([np.inf, -np.inf], np.nan).dropna().sort_values()
        ax.barh(vals.index, vals.values, color=[COLORS.get(g, "#555555") for g in vals.index])
        ax.set_xlabel(label)
        ax.grid(axis="x", alpha=0.2)
    fig.tight_layout()
    fig.savefig(outpath, dpi=220)
    plt.close(fig)


def plot_slip_event_map(events_df: pd.DataFrame, outpath: Path) -> None:
    if events_df.empty:
        return
    fig, ax = plt.subplots(figsize=(7.2, 4.5))
    colors = {"recoverable_slip": COLORS["linker1-paa"], "terminal_cliff": "#222222"}
    for typ, grp in events_df.groupby("event_type"):
        ax.scatter(grp["delta_nm"], grp["drop_nN"], s=42, alpha=0.75, color=colors.get(typ, "#555555"), label=typ)
    ax.set_xscale("symlog", linthresh=10)
    ax.set_yscale("symlog", linthresh=2)
    ax.set_xlabel("Slip/cliff indentation (nm)")
    ax.set_ylabel("Force drop magnitude (nN)")
    ax.set_title("Detected slip and terminal cliff events")
    ax.legend(frameon=False)
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(outpath, dpi=220)
    plt.close(fig)


def write_outputs(points_rows: list[pd.DataFrame], event_rows: list[dict], mechanics_rows: list[dict]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    points_df = pd.concat(points_rows, ignore_index=True) if points_rows else pd.DataFrame()
    events_df = pd.DataFrame(event_rows)
    mechanics_df = pd.DataFrame(mechanics_rows)
    points_df.to_csv(RESULTS_DIR / "deep_stitched_points.csv", index=False)
    events_df.to_csv(RESULTS_DIR / "deep_slip_events.csv", index=False)
    mechanics_df.to_csv(RESULTS_DIR / "deep_stitched_mechanics.csv", index=False)
    if not points_df.empty and not mechanics_df.empty:
        plot_raw_vs_stitched(points_df, mechanics_df, REPORT_DIR / "raw_vs_stitched_examples.png")
        plot_group_mechanics(points_df, mechanics_df, 20260416, REPORT_DIR / "k80_stitched_mechanics.png", "k80 stitched deep-indentation curves")
        plot_group_mechanics(points_df, mechanics_df, 20260415, REPORT_DIR / "linker_20260415_stitched_mechanics.png", "20260415 stitched thick-film curves")
        plot_ranking(mechanics_df, REPORT_DIR / "mechanics_ranking.png")
    plot_slip_event_map(events_df, REPORT_DIR / "slip_event_map.png")
    manifest = {
        "points": len(points_df),
        "events": len(events_df),
        "curves": len(mechanics_df),
        "recoverable_slips": int((events_df["event_type"] == "recoverable_slip").sum()) if not events_df.empty else 0,
        "terminal_cliffs": int((events_df["event_type"] == "terminal_cliff").sum()) if not events_df.empty else 0,
        "note": "Stitched forces are analysis products; raw_force_nN is preserved.",
    }
    (RESULTS_DIR / "deep_stitched_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return points_df, events_df, mechanics_df


def run(args: argparse.Namespace) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    params = StitchParams(
        deep_indent_threshold_nm=args.min_indent,
        deep_force_threshold_nN=args.min_force,
        force_abs_min_20260415=args.force_abs_min_20260415,
        force_abs_min_20260416=args.force_abs_min_20260416,
    )
    curve_df = pd.read_csv(CURVE_CSV)
    candidates = candidate_rows(curve_df, params)
    if args.sample:
        candidates = candidates[candidates["group"].str.contains(args.sample, case=False, na=False)]
    points_rows: list[pd.DataFrame] = []
    event_rows: list[dict] = []
    mechanics_rows: list[dict] = []
    for _, row in candidates.iterrows():
        points, events, mechanics = analyze_row(row, params)
        if points is None or mechanics is None:
            continue
        points_rows.append(points)
        event_rows.extend(events)
        mechanics_rows.append(mechanics)
    points_df, events_df, mechanics_df = write_outputs(points_rows, event_rows, mechanics_rows)
    print(f"Analyzed {len(mechanics_df)} deep-indentation curves")
    print(f"Wrote {RESULTS_DIR / 'deep_stitched_points.csv'}")
    print(f"Wrote {RESULTS_DIR / 'deep_slip_events.csv'}")
    print(f"Wrote {RESULTS_DIR / 'deep_stitched_mechanics.csv'}")
    print(f"Wrote figures to {REPORT_DIR}")
    return points_df, events_df, mechanics_df


def main() -> None:
    parser = argparse.ArgumentParser(description="Stitch recoverable slip events in deep indentation curves.")
    parser.add_argument("--min-indent", type=float, default=50.0)
    parser.add_argument("--min-force", type=float, default=10.0)
    parser.add_argument("--force-abs-min-20260415", type=float, default=2.0)
    parser.add_argument("--force-abs-min-20260416", type=float, default=50.0)
    parser.add_argument("--sample", help="Optional group substring filter, e.g. k80-linker1-paa")
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
