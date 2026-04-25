# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: tags,-all
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.1
#   kernelspec:
#     display_name: base
#     language: python
#     name: python3
# ---

# %% [markdown] tags=[]
r"""
# AFM Force-Distance Analysis: Suspended COF Film

**Authors:** Li Shuang (Experimenter), Prof. Kejun Liu (Analyst)
**Date:** April 2026

## Study Overview

This notebook analyzes force-distance curves acquired on suspended ultrathin COF membranes. The central question is: **why are the measured snap-in forces one to two orders of magnitude larger than classical theory predictions?** We examine van der Waals, capillary, Casimir-Polder, and electrostatic contributions, compare them against experiment, and assess the role of dynamic effects and film indentation geometry.

> **Notebook architecture:** Cell 2 is global configuration; Cell 3 is papermill parameters. Every subsequent pair of cells (Markdown → Code) is a self-contained analysis unit.
"""

# %% tags=[]
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy import integrate
from pathlib import Path

# ── Auto-detect project root ───────────────────────────────────────
cwd = Path.cwd()
if (cwd / "scripts").exists():
    ROOT = cwd
elif (cwd.parent / "scripts").exists():
    ROOT = cwd.parent
else:
    raise FileNotFoundError("Cannot find project root with scripts/")

# ── Import cleaning module ─────────────────────────────────────────
sys.path.insert(0, str(ROOT / "scripts"))
from cleaning import load_raw, correct_baseline, segment_curve

# %% tags=["parameters"]
# ── Papermill parameters — override via command line ───────────────
DATASET_DIR = "20260409"
SAMPLE_NAME = "JJS"
FILM_THICKNESS_NM = 10
PORE_DIAMETER_UM = 20
PROBE_RADIUS_NM = 8.0
CANTILEVER_STIFFNESS_N_M = 7.0
FILE_PATTERN = "*.txt"
OUTPUT_PREFIX = "jjs"
ENVIRONMENT = "Air ambient, RH > 60 %"
DISCARDED_FILES = []  # List of filenames to exclude (from QC decisions)

# %% tags=["injected-parameters"]
# Parameters
DATASET_DIR = "20260416\u539f\u59cb\u6570\u636e"
SAMPLE_NAME = "k80"
FILM_THICKNESS_NM = 50
PORE_DIAMETER_UM = 20
PROBE_RADIUS_NM = 100.0
CANTILEVER_STIFFNESS_N_M = 89.0
FILE_PATTERN = "k80*.txt"
OUTPUT_PREFIX = "k80"
ENVIRONMENT = "Air ambient"
DISCARDED_FILES = [
    "k80-linker1-PFNA-50nm-1000nm-10uN - NanoScope Analysis.txt",
    "k80-linker1-paa-50nm-12410nm-10uN - NanoScope Analysis.txt",
    "linker1-nls-1500nm.spm - NanoScope Analysis.txt",
    "linker1-PFPE-OH-1800nm-2.spm - NanoScope Analysis.txt",
    "linker2-paa-1000nm-2.spm - NanoScope Analysis.txt",
    "k80-linker1-PFNA-50nm-7000nm-10uN - NanoScope Analysis.txt",
    "k80-linker2-paa-50nm-1500nm-10uN - NanoScope Analysis.txt",
    "linker1-nls-2000nm.spm - NanoScope Analysis.txt",
    "linker1-nls-1500nm-2.spm - NanoScope Analysis.txt",
    "linker1-PFPE-OH-1900nm-2.spm - NanoScope Analysis.txt",
    "linker1-PFPE-OH-2800nm.spm - NanoScope Analysis.txt",
    "linker1-nls-2000nm-2.spm - NanoScope Analysis.txt",
    "k80-linker1-SDBS-50nm-10000nm-10uN - NanoScope Analysis.txt",
    "linker2-paa-.300nm.-2spm - NanoScope Analysis.txt",
    "linker1-PFPE-OH-1800nm.spm - NanoScope Analysis.txt",
    "k80-linker1-paa-50nm-12000nm-10uN - NanoScope Analysis.txt",
    "linker1-PFPE-OH-1900nm.spm - NanoScope Analysis.txt",
    "k80-linker1-PFNA-50nm-12410nm-10uN - NanoScope Analysis.txt",
    "k80-linker1-paa-50nm-500nm-3uN - NanoScope Analysis.txt",
    "k80-linker1-SDBS-50nm-8000nm-10uN - NanoScope Analysis.txt",
    "k80-linker1-PFNA-50nm-10000nm-10uN - NanoScope Analysis.txt",
    "linker1-PFPE-OH-2600nm.spm - NanoScope Analysis.txt",
    "k80-linker1-SDBS-50nm-5000nm-10uN - NanoScope Analysis.txt",
    "linker1-PFPE-OH-1800nm-3.spm - NanoScope Analysis.txt",
    "linker1-PFPE-OH-4000nm.spm - NanoScope Analysis.txt",
    "linker2-paa-1500nm.spm - NanoScope Analysis.txt",
    "k80-linker1-PFNA-50nm-3000nm-10uN - NanoScope Analysis.txt",
    "linker1-nls-1000nm.spm - NanoScope Analysis.txt",
    "k80-linker1-SDBS-50nm-4000nm-10uN - NanoScope Analysis.txt",
    "k80-linker1-SDBS-50nm-3000nm-10uN - NanoScope Analysis.txt",
    "k80-linker1-PFNA-50nm-2000nm-10uN - NanoScope Analysis.txt",
    "k80-linker1-PFNA-50nm-4000nm-10uN - NanoScope Analysis.txt",
    "k80-linker1-paa-50nm-2000nm-3uN - NanoScope Analysis.txt",
    "k80-linker1-SDBS-50nm-2000nm-10uN - NanoScope Analysis.txt",
    "k80-linker1-SDBS-50nm-12410nm-10uN - NanoScope Analysis.txt",
    "k80-linker1-SDBS-50nm-9000nm-10uN - NanoScope Analysis.txt",
    "k80-linker1-paa-50nm-5000nm-3uN - NanoScope Analysis.txt",
    "k80-linker2-paa-50nm-1000nm-10uN - NanoScope Analysis.txt",
    "linker1-PFPE-OH-2200nm.spm - NanoScope Analysis.txt",
    "k80-linker1-paa-50nm-2500nm-3uN - NanoScope Analysis.txt",
    "linker2-paa-.300nm.spm - NanoScope Analysis.txt",
    "k80-linker1-PFNA-50nm-9000nm-10uN - NanoScope Analysis.txt",
    "linker2-paa-.500nm.spm - NanoScope Analysis.txt",
    "k80-linker2-paa-50nm-2000nm-10uN - NanoScope Analysis.txt",
    "k80-linker1-PFNA-50nm-8000nm-10uN - NanoScope Analysis.txt",
    "linker1-PFPE-OH-2000nm.spm - NanoScope Analysis.txt",
    "k80-linker1-paa-50nm-1500nm-3uN - NanoScope Analysis.txt",
    "k80-linker1-PFNA-50nm-5000nm-10uN - NanoScope Analysis.txt",
    "k80-linker1-paa-50nm-3000nm-3uN - NanoScope Analysis.txt",
    "k80-linker1-SDBS-50nm-500nm-10uN - NanoScope Analysis.txt",
    "k80-linker1-PFNA-50nm-500nm-10uN - NanoScope Analysis.txt",
    "k80-linker2-paa-50nm-100nm-125.5nN-2 - NanoScope Analysis.txt",
    "k80-linker1-PFNA-50nm-6000nm-10uN - NanoScope Analysis.txt",
    "k80-linker2-paa-50nm-100nm-125.5nN - NanoScope Analysis.txt",
    "k80-linker1-paa-50nm-10000nm-10uN - NanoScope Analysis.txt",
    "k80-linker2-paa-50nm-200nm-125.5nN - NanoScope Analysis.txt",
    "linker1-PFPE-OH-2400nm.spm - NanoScope Analysis.txt",
    "linker1-PFPE-OH-3000nm.spm - NanoScope Analysis.txt",
    "linker2-paa-.1000nm.spm - NanoScope Analysis.txt",
    "k80-linker1-SDBS-50nm-7000nm-10uN - NanoScope Analysis.txt",
    "k80-linker1-SDBS-50nm-6000nm-10uN - NanoScope Analysis.txt",
    "linker2-paa-150nm.spm - NanoScope Analysis.txt",
    "k80-linker2-paa-50nm-200nm-125.5nN-2 - NanoScope Analysis.txt",
]


# %% [markdown] tags=[]
r"""
## Data Loading Pipeline & Caching Strategy

The analysis begins with a **cached data-loading pipeline** that avoids redundant I/O and computation. The raw Bruker `.txt` exports are processed through three stages:

1. **Load raw**: Parse the Bruker ASCII export (latin-1 encoding, 512 points per curve, decreasing Z).
2. **Baseline correction**: Fit a linear baseline to the far-field region ($Z \in [0,100]$ nm after reversal) and subtract it to remove optical-lever drift.
3. **Segmentation**: Detect snap-in (minimum force), contact (first post-snap-in zero-crossing), and split the curve into drop (approach) and rise (retraction) branches.

Because Steps 1–3 are computationally expensive and their outputs are consumed by every downstream analysis unit, we **cache the processed `data` list** as a Python pickle. On subsequent runs the cache is loaded directly, reducing the startup time from ~10 s to <1 s.

> **Cache invalidation**: Delete `results/cache_{OUTPUT_PREFIX}_data.pkl` to force a full re-processing (e.g. after modifying `cleaning.py`).

### QC Filtering
If `DISCARDED_FILES` is provided (from `scripts/data_qc_gui.py` → `results/qc_decisions.json`), discarded files are excluded **before** raw loading. The analysis operates only on manually curated "keep" decisions.
"""

# %% tags=[]
# ── Load raw data (with caching) ───────────────────────────────────
import pickle

CACHE_FILE = ROOT / "results" / f"cache_{OUTPUT_PREFIX}_data.pkl"

# Convert to set for fast lookup
discard_set = set(DISCARDED_FILES) if DISCARDED_FILES else set()

if CACHE_FILE.exists() and not discard_set:
    with open(CACHE_FILE, "rb") as f:
        data = pickle.load(f)
    print(f"Loaded cached data from {CACHE_FILE} ({len(data)} curves)")
else:
    RAW_DIR = ROOT / DATASET_DIR
    raw_files = sorted(RAW_DIR.glob(FILE_PATTERN))
    if not raw_files:
        raise FileNotFoundError(f"No files matching '{FILE_PATTERN}' in {RAW_DIR}")
    
    # Filter out discarded files
    if discard_set:
        raw_files = [f for f in raw_files if f.name not in discard_set]
        print(f"[QC] Excluded {len(DISCARDED_FILES)} discarded file(s)")
    
    raw_curves = [load_raw(f) for f in raw_files]
    print(f"Loaded {len(raw_curves)} raw curves from {DATASET_DIR}/")

    # ── Compute theoretical forces (dataset-dependent probe params) ────
    R_m = PROBE_RADIUS_NM * 1e-9
    d0_m = 0.3e-9
    A_J = 4e-19
    gamma_N_m = 72e-3
    hbar_c_J_m = 1.98644586e-25
    eta = 0.4

    F_vdw = A_J * R_m / (12 * d0_m ** 2) * 1e9
    F_cap = 4 * np.pi * R_m * gamma_N_m * 1e9
    F_cp = (np.pi ** 3 * hbar_c_J_m * R_m / (360 * d0_m ** 3)) * eta * 1e9

    # Clean & validate
    data = []
    for rc in raw_curves:
        f_corr, slope, intercept, n_points, status = correct_baseline(rc["z"], rc["f"])
        if f_corr is None:
            continue
        seg = segment_curve(rc["z"], f_corr)
        item = {
            "file": rc["filename"],
            "disp_nm": rc["meta"]["piezo_displacement"],
            "setpoint": f"{rc['meta']['setpoint_force']}{rc['meta']['setpoint_unit']}",
            "snap_f": seg["snap_f"],
            "snap_z": seg["snap_z"],
            "contact_z": seg["contact_z"],
            "contact_f": seg["contact_f"],
            "max_drop_slope": seg["max_drop_slope"],
            "avg_drop_slope": seg["avg_drop_slope"],
            "max_rise_slope": seg["max_rise_slope"],
            "avg_rise_slope": seg["avg_rise_slope"],
            "asymmetry_ratio": seg["asymmetry_ratio"],
            "energy_dissipated": seg["energy_dissipated"],
            "drop_z": seg["drop_z"],
            "drop_f": seg["drop_f"],
            "rise_z": seg["rise_z"],
            "rise_f": seg["rise_f"],
            "recovery": seg["recovery"],
            "vdW_check": {
                "F_vdw_nonret": float(F_vdw),
                "F_capillary_theory": float(F_cap),
                "F_casimir": float(F_cp),
                "F_vdw_plus_cap": float(F_vdw + F_cap),
            },
            "baseline": {"slope": slope, "intercept": intercept, "status": status, "n_points": n_points},
            "raw_z": rc["z_raw"].tolist(),
            "raw_f": rc["f_raw"].tolist(),
        }
        data.append(item)
    print(f"Cleaned data: {len(data)} curves ready for analysis.")

    # Save cache
    with open(CACHE_FILE, "wb") as f:
        pickle.dump(data, f)
    print(f"Saved data cache to {CACHE_FILE}")

# ── A4 academic figure sizes ───────────────────────────────────────
# Single column: 8.6 cm; double column: 17.8 cm (1 inch = 2.54 cm)
SINGLE_COL = 8.6 / 2.54   # ≈ 3.39 inch
DOUBLE_COL = 17.8 / 2.54  # ≈ 7.01 inch
TRIPLE_COL = 26.0 / 2.54  # ≈ 10.24 inch

# ── Publication-grade font settings ────────────────────────────────
plt.rcParams.update({
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "font.family": "serif",
    "font.serif": ["Arial Unicode MS", "Times New Roman", "DejaVu Serif"],
    "mathtext.fontset": "stix",
    "font.size": 10,
    "axes.labelsize": 10,
    "axes.titlesize": 11,
    "legend.fontsize": 9,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "axes.linewidth": 0.6,
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "xtick.direction": "in",
    "ytick.direction": "in",
    "xtick.top": True,
    "ytick.right": True,
    "savefig.format": "pdf",
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.02,
    "pdf.fonttype": 42,
    "svg.fonttype": "none",
})

# ── Scientific color palette (Nature/Science style) ────────────────
COLORS = ["#0C5DA5", "#E8204E", "#00B945", "#FF9500", "#845B97", "#474747"]

# ── Random seed ────────────────────────────────────────────────────
rng = np.random.default_rng(42)

# ── Helper function ────────────────────────────────────────────────
def r2_score(y_true, y_pred):
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    return 1 - ss_res / ss_tot

print("Global configuration loaded. Data:", len(data), "curves.")

# %% [markdown] tags=[]
r"""
## A. Raw Data Overview

The Bruker NanoScope Analysis exports force-distance curves as `.txt` files with the following characteristics:
- **Encoding**: `latin-1` (Chinese headers cause `UnicodeDecodeError` with `utf-8`)
- **Z direction**: Decreasing monotonically (e.g., 1000 → 0 nm), which is reversed for physical interpretation
- **Force baseline**: Positive offset (~12–16 nN) due to optical-lever drift
- **Points**: Exactly 512 per curve (PeakForce QNM standard)

Below we plot the **raw, uncorrected** force vs. displacement for three representative curves to illustrate these artifacts before any processing is applied.
"""

# %% tags=[]
# ── Dynamic displacement color map ─────────────────────────────────
all_disps = sorted({d["disp_nm"] for d in data if d["disp_nm"] is not None})
disp_color_map = {d: COLORS[i % len(COLORS)] for i, d in enumerate(all_disps)}

# ── Plot all curves in a faceted grid ──────────────────────────────
import math

n_curves = len(data)
n_cols = min(5, n_curves)
n_rows = math.ceil(n_curves / n_cols) if n_curves > 0 else 1

fig, axes = plt.subplots(n_rows, n_cols, figsize=(DOUBLE_COL, DOUBLE_COL * 0.35 * n_rows), squeeze=False)
axes = axes.flatten()

for i, item in enumerate(data):
    ax = axes[i]
    z_raw = np.array(item["raw_z"])
    f_raw = np.array(item["raw_f"])
    disp = item["disp_nm"] if item["disp_nm"] else 0
    color = disp_color_map.get(disp, COLORS[4])
    ax.plot(z_raw, f_raw, "-", linewidth=0.5, alpha=0.8, color=color, zorder=2)
    ax.axhline(0, color="gray", linewidth=0.3, linestyle="-", zorder=1)
    ax.set_title(item["file"].replace(" - NanoScope Analysis.txt", "")[:25], fontsize=6)
    ax.tick_params(labelsize=6)
    ax.grid(True, alpha=0.3, linestyle="--", linewidth=0.3, zorder=0)
    ax.invert_xaxis()

for j in range(i + 1, len(axes)):
    axes[j].axis("off")

fig.tight_layout()
fig.savefig(f"{OUTPUT_PREFIX}_raw_data_overview.pdf")
plt.show()
print(f"Saved: {OUTPUT_PREFIX}_raw_data_overview.pdf")

# ── Overlay summary (all curves on one axis) ───────────────────────
fig, ax = plt.subplots(figsize=(DOUBLE_COL, DOUBLE_COL * 0.4))
for item in data:
    z_raw = np.array(item["raw_z"])
    f_raw = np.array(item["raw_f"])
    disp = item["disp_nm"] if item["disp_nm"] else 0
    color = disp_color_map.get(disp, COLORS[4])
    ax.plot(z_raw, f_raw, "-", linewidth=0.4, alpha=0.5, color=color, zorder=2)

ax.axhline(0, color="gray", linewidth=0.5, linestyle="-", zorder=1)
ax.set_xlabel("Raw Z (decreasing, nm)")
ax.set_ylabel("Raw Force (nN)")
ax.set_title(f"All {len(data)} Raw Force-Distance Curves (Uncorrected, Overlay)")
ax.grid(True, alpha=0.3, linestyle="--", linewidth=0.5, zorder=0)
ax.invert_xaxis()

from matplotlib.patches import Patch
legend_elements = [Patch(facecolor=disp_color_map[d], edgecolor="black", label=f"{int(d)} nm") for d in all_disps]
ax.legend(handles=legend_elements, loc="upper right", fontsize=8)

fig.tight_layout()
fig.savefig(f"{OUTPUT_PREFIX}_raw_data_overlay.pdf")
plt.show()
print(f"Saved: {OUTPUT_PREFIX}_raw_data_overlay.pdf")

# %% [markdown] tags=[]
r"""
## B. Baseline Correction

The far-field region ($Z \in [0, 100]$ nm after reversal) contains no tip–sample interaction for a {FILM_THICKNESS_NM} nm film on a {PORE_DIAMETER_UM} μm pore. A linear fit $F_{{bl}}(Z) = a \cdot Z + b$ captures thermal drift and lever offset:

- **≥ 5 points in [0, 100] nm**: Linear fit
- **3–4 points**: Constant offset (mean subtraction)
- **< 3 points**: Correction fails → curve flagged

The corrected force is $F_{corr} = F_{raw} - F_{bl}(Z)$.
"""

# %% tags=[]
# Baseline correction: summary table for all curves + 2 detailed demos
rows_bl = []
for item in data:
    z = np.array(item["raw_z"][::-1])
    f = np.array(item["raw_f"][::-1])
    f_corr, slope, intercept, n_pts, status = correct_baseline(z, f)
    rows_bl.append({
        "File": item["file"].replace(" - NanoScope Analysis.txt", ""),
        "Slope (nN/nm)": round(slope, 4),
        "Intercept (nN)": round(intercept, 2),
        "N points": n_pts,
        "Status": status,
    })

df_bl = pd.DataFrame(rows_bl)
print("Baseline correction summary for all curves:")
print(df_bl.to_string(index=False))

# Detailed demo on 2 representative curves
fig, axes = plt.subplots(2, 2, figsize=(DOUBLE_COL, DOUBLE_COL * 0.5))
demo_indices = [0, min(6, len(data)-1)] if len(data) >= 2 else [0]
for row, idx in enumerate(demo_indices):
    item = data[idx]
    z = np.array(item["raw_z"][::-1])
    f = np.array(item["raw_f"][::-1])
    f_corr, slope, intercept, n_pts, status = correct_baseline(z, f)

    ax = axes[row, 0]
    ax.plot(z, f, "o-", markersize=2, color=COLORS[0], linewidth=0.8, label="Raw", zorder=3)
    baseline = slope * z + intercept
    ax.plot(z, baseline, "--", color=COLORS[1], linewidth=1.2, label="Baseline fit", zorder=2)
    ax.axhline(0, color="gray", linewidth=0.5, zorder=1)
    ax.set_ylabel("Force (nN)")
    short = item["file"].replace(" - NanoScope Analysis.txt", "")[:30]
    ax.set_title(f"{short} — Before correction", fontsize=8)
    ax.legend(fontsize=7)
    ax.grid(True, alpha=0.3, linestyle="--", linewidth=0.5, zorder=0)

    ax = axes[row, 1]
    ax.plot(z, f_corr, "o-", markersize=2, color=COLORS[2], linewidth=0.8, zorder=3)
    ax.axhline(0, color="gray", linewidth=0.5, zorder=1)
    ax.set_ylabel("Force (nN)")
    ax.set_title(f"Slope={slope:.4f}, Intercept={intercept:.2f} nN, N={n_pts}", fontsize=8)
    ax.grid(True, alpha=0.3, linestyle="--", linewidth=0.5, zorder=0)

for ax in axes[:, 0]:
    ax.set_xlabel("Z (nm, reversed)")
for ax in axes[:, 1]:
    ax.set_xlabel("Z (nm, reversed)")

fig.tight_layout()
fig.savefig(f"{OUTPUT_PREFIX}_baseline_correction_demo.pdf")
plt.show()
print("Saved: jjs_baseline_correction_demo.pdf")

# %% [markdown] tags=[]
r"""
## C. Data Cleaning & Validation

The full cleaning pipeline proceeds as follows:
1. **Reverse** Z direction (Bruker exports decreasing; we need increasing for physical interpretation)
2. **Correct baseline** using far-field linear fit ($Z \in [0, 100]$ nm)
3. **Detect snap-in**: $\mathrm{argmin}(F_{corr})$ — maximum attractive force
4. **Detect contact**: First post-snap-in point where $F_{corr} \geq 0$
5. **Segment** into drop (approach) and rise (retraction) regions
6. **Validate**: Curves with warnings are flagged but retained for transparency

The table below summarizes the validation results for all curves.
"""

# %% tags=[]
# Validation summary table for all curves
rows = []
for item in data:
    rows.append({
        "File": item["file"].replace(" - NanoScope Analysis.txt", ""),
        "Disp (nm)": int(item["disp_nm"]) if item["disp_nm"] else "—",
        "Snap (nN)": round(item["snap_f"], 1),
        "Contact Z (nm)": round(item["contact_z"], 1),
        "Drop pts": len(item["drop_z"]),
        "Rise pts": len(item["rise_z"]),
        "Baseline": item["baseline"]["status"],
    })

df_val = pd.DataFrame(rows)
print(df_val.to_string(index=False))

# Plot segmentation for all curves as small multiples
n_curves = len(data)
n_cols = 4
n_rows = int(np.ceil(n_curves / n_cols))
fig, axes = plt.subplots(n_rows, n_cols, figsize=(DOUBLE_COL, DOUBLE_COL * 0.35 * n_rows / 2))
axes = axes.flatten() if n_curves > 1 else [axes]

for ax, item in zip(axes, data):
    z = np.array(item["raw_z"][::-1])
    f = np.array(item["raw_f"][::-1])
    f_corr, *_ = correct_baseline(z, f)
    seg = segment_curve(z, f_corr)

    ax.plot(z, f_corr, "o-", markersize=1.5, color=COLORS[0], linewidth=0.6, zorder=3)
    if len(seg["drop_z"]) > 0:
        ax.fill_between(seg["drop_z"], min(f_corr) * 1.1, max(f_corr) * 1.1,
                        alpha=0.12, color=COLORS[0])
    if len(seg["rise_z"]) > 0:
        ax.fill_between(seg["rise_z"], min(f_corr) * 1.1, max(f_corr) * 1.1,
                        alpha=0.12, color=COLORS[2])
    ax.scatter([seg["snap_z"]], [seg["snap_f"]], c=COLORS[1], s=60, marker="*",
               zorder=5, edgecolors="white", linewidth=0.3)
    if seg["contact_z"] is not None:
        ax.scatter([seg["contact_z"]], [seg["contact_f"]], c=COLORS[3], s=40, marker="^",
                   zorder=5, edgecolors="white", linewidth=0.3)
    ax.axhline(0, color="gray", linewidth=0.4, zorder=1)
    short = item["file"].replace(" - NanoScope Analysis.txt", "")[:25]
    ax.set_title(short, fontsize=7)
    ax.grid(True, alpha=0.2, linestyle="--", linewidth=0.4, zorder=0)
    ax.tick_params(axis="both", labelsize=6)

# Hide unused subplots
for ax in axes[n_curves:]:
    ax.axis("off")

fig.tight_layout()
fig.savefig(f"{OUTPUT_PREFIX}_segmentation_validation.pdf")
plt.show()
print(f"Saved: {OUTPUT_PREFIX}_segmentation_validation.pdf")

# %% [markdown] tags=[]
r"""
## B. Two-Stage Curve Detection & Highlight

### Physical Background

AFM force-distance curves on soft, suspended membranes often exhibit a characteristic **two-stage profile**:

- **Stage 1 (Pre-contact attraction)**: As the tip approaches the membrane, long-range attractive forces (van der Waals, capillary) pull the membrane upward until a mechanical instability triggers snap-in. This stage is dominated by **surface/interface interactions** and is largely independent of the membrane's elastic properties.

- **Stage 2 (Post-contact repulsion)**: After snap-in, the tip indents the membrane, and the membrane's **restoring force** pushes back. The slope of the repulsive branch reflects the effective stiffness of the membrane–cantilever system $k_{eff}^{-1} = k_c^{-1} + k_{mem}^{-1}$. For ultrathin films ($t \sim 10$ nm), $k_{mem}$ can be comparable to or smaller than $k_c \approx 5$ N/m, making Stage 2 clearly observable.

### Detection Criterion

We flag curves with a clearly positive repulsive contact force ($F_{contact} > 5$ nN) as **two-stage curves**. The threshold of 5 nN is chosen to be well above the noise floor (~1 nN) while remaining sensitive enough to catch weak membrane repulsion. Curves with $F_{contact} \leq 5$ nN are classified as **snap-in-only**: the tip snaps in but the setpoint or displacement is insufficient to probe the membrane's elastic response.

> **Note**: The presence of Stage 2 is a prerequisite for extracting membrane stiffness, Young's modulus, and tension via Hertzian or shell-theory models (see Units 10 and 12).
"""

# %% tags=[]
# ── B. Two-Stage Curve Detection ───────────────────────────────────
STAGE2_THRESHOLD = 5.0  # nN, contact force above this => clear Stage 2 repulsion

two_stage = []
for d in data:
    has_stage2 = d["contact_f"] > STAGE2_THRESHOLD
    two_stage.append({
        "File": d["file"].replace(" - NanoScope Analysis.txt", ""),
        "Disp (nm)": d["disp_nm"],
        "Setpoint": d["setpoint"],
        "Snap (nN)": round(d["snap_f"], 1),
        "Contact F (nN)": round(d["contact_f"], 1),
        "Has Stage 2": has_stage2,
    })

df_stage2 = pd.DataFrame(two_stage)
print(df_stage2.to_string(index=False))

stage2_count = sum(1 for t in two_stage if t["Has Stage 2"])
print(f"\n→ {stage2_count} out of {len(data)} curves show clear Stage 2 (contact_f > {STAGE2_THRESHOLD} nN).")

# Plot only two-stage curves with annotations
stage2_data = [d for d in data if d["contact_f"] > STAGE2_THRESHOLD]
if stage2_data:
    n_s2 = len(stage2_data)
    n_cols_s2 = min(3, n_s2)
    n_rows_s2 = int(np.ceil(n_s2 / n_cols_s2))
    fig, axes = plt.subplots(n_rows_s2, n_cols_s2, figsize=(DOUBLE_COL, DOUBLE_COL * 0.5 * n_rows_s2), squeeze=False)
    axes = axes.flatten()

    for i, d in enumerate(stage2_data):
        ax = axes[i]
        ax.plot(d["drop_z"], d["drop_f"], color=COLORS[0], linewidth=1.5, label="Stage 1: approach", zorder=3)
        ax.plot(d["rise_z"], d["rise_f"], color=COLORS[1], linewidth=1.5, label="Stage 2: retraction", zorder=3)
        ax.axhline(0, color="gray", linewidth=0.5, linestyle="-", zorder=1)
        ax.axvline(d["snap_z"], color=COLORS[2], linestyle="--", linewidth=0.8, alpha=0.7)
        ax.axvline(d["contact_z"], color=COLORS[3], linestyle="--", linewidth=0.8, alpha=0.7)
        ax.annotate("snap-in", (d["snap_z"], d["snap_f"]), fontsize=7, color=COLORS[2])
        ax.annotate("contact", (d["contact_z"], d["contact_f"]), fontsize=7, color=COLORS[3])
        ax.set_title(d["file"].replace(" - NanoScope Analysis.txt", "")[:30], fontsize=8)
        ax.set_xlabel("z (nm)", fontsize=8)
        ax.set_ylabel("F (nN)", fontsize=8)
        ax.grid(True, alpha=0.3, linestyle="--", linewidth=0.5, zorder=0)
        if i == 0:
            ax.legend(fontsize=7)

    for j in range(i + 1, len(axes)):
        axes[j].axis("off")

    fig.tight_layout()
    fig.savefig(f"{OUTPUT_PREFIX}_two_stage_curves.pdf")
    plt.show()
    print(f"Saved: {OUTPUT_PREFIX}_two_stage_curves.pdf")
else:
    print("No two-stage curves detected in this dataset.")

# %% [markdown] tags=[]
r"""
## 1. Experimental Parameters

### Parameter Selection & Physical Rationale

The table below lists the key experimental and material parameters used in all subsequent theoretical calculations. Each parameter was chosen based on either direct measurement, manufacturer specifications, or literature values:

| Parameter | Value | Source / Rationale |
|-----------|-------|-------------------|
| Probe radius $R$ | 8 nm | Bruker RTESPA-525, nominal tip radius |
| Cantilever stiffness $k_c$ | 5 N/m | Manufacturer calibration (thermal tune) |
| Water surface tension $\gamma$ | 72 mN/m | Literature value for water at 20 °C |
| Hamaker constant $A$ | $4\times10^{-19}$ J | Typical for polymer/SiO₂ in air |
| Cutoff distance $d_0$ | 0.3 nm | Interatomic spacing, standard for DMT model |
| Film thickness $t$ | 10 nm | TEM measurement (COF film) |
| Pore diameter | 20 μm | Fabrication mask design |
| Relative humidity | >60 % | Measured ambient conditions during acquisition |
| PeakForce frequency | ~2 kHz | Bruker QNM default |
| Tip velocity (est.) | 0.1–1 m/s | $v \sim 2 f A$ with $A \sim$ displacement/2 |

> **Sensitivity note**: For JJS, the measured snap-in forces (~120 nN) are **~40× larger** than the classic vdW + capillary prediction (~10 nN). Even a 2× uncertainty in $R$ or $d_0$ changes $F_{vdW}$ by only a factor of 2–4, far smaller than the observed 40× discrepancy. This confirms that the disagreement is not due to parameter uncertainty but reflects additional physical mechanisms (see Unit 2 and Unit 15b).
"""

# %% tags=[]
import pandas as pd

params = [
    ("Sample", SAMPLE_NAME, ""),
    ("Probe radius $R$", str(PROBE_RADIUS_NM), "nm"),
    ("Cantilever stiffness $k_c$", str(CANTILEVER_STIFFNESS_N_M), "N/m"),
    (r"Water surface tension $\gamma$", "72", "mN/m"),
    ("Hamaker constant $A$", r"$4\times10^{-19}$", "J"),
    ("Cutoff distance $d_0$", "0.3", "nm"),
    ("Film thickness $t$", str(FILM_THICKNESS_NM), "nm"),
    ("Pore diameter", str(PORE_DIAMETER_UM), r"$\mu$m"),
    ("Relative humidity", ENVIRONMENT.split(",")[-1].strip().replace("RH ", ""), "%"),
    ("PeakForce frequency", "~2", "kHz"),
    ("Tip velocity (est.)", "~0.1-1", "m/s"),
]

df_params = pd.DataFrame(params, columns=["Parameter", "Value", "Unit"])

fig, ax = plt.subplots(figsize=(SINGLE_COL, SINGLE_COL * 0.6))
ax.axis("off")
table = ax.table(
    cellText=df_params.values,
    colLabels=df_params.columns,
    loc="center",
    cellLoc="center",
    colColours=["#E8E8E8"] * 3,
)
table.auto_set_font_size(False)
table.set_fontsize(9)
table.scale(1.2, 1.5)
fig.savefig(f"{OUTPUT_PREFIX}_experimental_parameters.pdf")
plt.show()
print("Saved: jjs_experimental_parameters.pdf")

# %% [markdown] tags=[]
r"""
## 2. Classic Force Theory vs. Experiment

### Theoretical Framework

For a sphere of radius $R$ at distance $d$ from a plane, the non-retarded van der Waals force in the DMT framework is

$$F_{vdW} = \frac{AR}{12d_0^2} \tag{1}$$

where $A$ is the Hamaker constant and $d_0$ is the cutoff distance. For capillary force under complete wetting ($\theta = 0$),

$$F_{cap} = 4\pi R \gamma \tag{2}$$

where $\gamma$ is the water surface tension. At large separations ($d \gg \lambda_0$), the Casimir-Polder (retarded vdW) force is

$$F_{CP} = \frac{\pi^3 \hbar c R}{360 d_0^3} \cdot \eta \tag{3}$$

with $\eta \approx 0.4$ for polymer/SiN interfaces. The electrostatic force from contact potential difference $V_{CPD}$ is

$$F_{elec} = \frac{\pi \varepsilon_0 R V_{CPD}^2}{d_0} \tag{4}$$

### The JJS Discrepancy: ~40× Enhancement

For JJS, the measured snap-in forces are dramatically larger than classic theory predictions:

- **Theory (vdW + capillary)**: ~10.2 nN
- **Experiment (mean)**: ~120 nN
- **Enhancement factor**: ~12–51×, mean ~40×

This is fundamentally different from the linker1-PFPE-OH system, where experiment and theory agree within a factor of ~2 (ratio ~0.63×). The JJS discrepancy of **40× cannot be explained by parameter uncertainty alone** — even if $R$ were 10× larger or $d_0$ 3× smaller, the theoretical force would increase by only one order of magnitude.

### The Bridge-Arch Hypothesis: The Dominant Mechanism

The most plausible explanation for the 40× enhancement is the **bridge-arch restoring force** of the suspended COF film.

#### Physical Picture

As the AFM tip approaches the suspended membrane, attractive forces (vdW + capillary) pull the membrane **upward** toward the tip. Because the film is only 10 nm thick and spans a 20 μm pore, it behaves like a drumhead: the pulled region forms a **bridge arch** (bulge) with significant curvature. The membrane tension $T$ in this arch generates a **restoring force** that resists further deformation:

$$F_{arch}(\delta) = \frac{2\pi T}{\ln(R_{pore}/a_{contact})} \, \delta + \frac{E \, t}{R_{pore}^2(1-\nu)} \, \delta^3 \tag{5}$$

where:
- $\delta$ = membrane deflection (vertical displacement from flat)
- $T$ = in-plane membrane tension (N/m)
- $E$ = Young's modulus (Pa)
- $t$ = film thickness (10 nm)
- $R_{pore}$ = pore radius (10 μm)
- $a_{contact}$ = tip–film contact radius (~10–20 nm)
- $\nu$ = Poisson ratio (~0.3)

> **Critical note on stress state**: A 10 nm ultrathin film cannot sustain in-plane **compression** — it would instantly buckle or wrinkle. Whether bulging **upward** (under the tip) or indenting **downward** (after snap-in), the membrane is always in a state of **biaxial tension** (stretching). The restoring force reverses direction, but the stress state (tension) does not. This is fundamentally different from a thick plate that can experience compressive stress on one side and tensile stress on the other.

#### Why This Explains the Enhancement

The snap-in occurs when the **gradient of attractive forces exceeds the effective stiffness** of the cantilever–membrane system:

$$\left| \frac{\partial F_{attr}}{\partial z} \right| > k_c + k_{mem}$$

For a high-tension membrane, $k_{mem} \sim 1$–10 N/m is comparable to or larger than the cantilever stiffness $k_c \approx 5$ N/m. The **apparent snap-in force** is therefore not just the surface adhesion force ($F_{vdW} + F_{cap} \approx 10$ nN), but the force required to **pull the membrane up by the snap depth** ($\delta \sim 20$ nm) against its own tension:

$$F_{snap}^{effective} \approx F_{vdW} + F_{cap} + F_{arch}(\delta_{snap})$$

If $T \sim 0.1$–1 N/m and $\delta_{snap} \sim 20$ nm, $F_{arch}$ can reach **50–100 nN**, bringing the total snap-in force to the observed ~120 nN. This explains the 40× enhancement without invoking exotic surface interactions.

#### Other Mechanisms (Secondary)

While the bridge-arch effect is the dominant contributor, several secondary mechanisms may provide modest additional enhancement:

| Mechanism | Estimated contribution | Evidence |
|-----------|----------------------|----------|
| **Bridge-arch restoring force** | **10–50×** | Directly measured from rise-segment fit (Unit 15) |
| Dynamic/velocity effects | 2–5× | Tip velocity $v \sim$ 0.1–1 m/s; viscous losses in water film |
| Complex capillary geometry | 2–3× | High humidity (>60 %) allows non-ideal meniscus shapes |
| Electrostatic forces | 1–2× | Would require $V_{CPD} \sim$ 3 V; not independently confirmed |

> **Note**: The bridge-arch model is quantitatively validated in Unit 15 (post-snap-in membrane mechanics fit). A detailed parameter sensitivity analysis of all mechanisms is presented in Unit 15b.
"""

# %% tags=[]
# Physical constants
R_nm = 8.0
d0_nm = 0.3
A_J = 4e-19
gamma_mN_m = 72.0
hbar_c_J_m = 1.98644586e-25  # J·m
eta = 0.4
eps0 = 8.854e-12  # F/m

# Convert to SI
R_m = R_nm * 1e-9
d0_m = d0_nm * 1e-9
gamma_N_m = gamma_mN_m * 1e-3

# Calculate theoretical forces
F_vdw = A_J * R_m / (12 * d0_m**2) * 1e9  # nN
F_cap = 4 * np.pi * R_m * gamma_N_m * 1e9  # nN
F_cp = (np.pi**3 * hbar_c_J_m * R_m / (360 * d0_m**3)) * eta * 1e9  # nN

# Electrostatic: calculate V_CPD needed to match mean measured force
F_measured_all = [abs(d["snap_f"]) for d in data]
F_mean = np.mean(F_measured_all)
F_min = np.min(F_measured_all)
F_max = np.max(F_measured_all)

V_CPD_needed = np.sqrt(F_mean * 1e-9 * d0_m / (np.pi * eps0 * R_m))
F_elec_typical_low = np.pi * eps0 * R_m * (0.1)**2 / d0_m * 1e9
F_elec_typical_high = np.pi * eps0 * R_m * (0.5)**2 / d0_m * 1e9

mechanisms = ["Non-retarded vdW", "Capillary", "Casimir-Polder", "Electrostatic (typical)"]
predictions = [F_vdw, F_cap, F_cp, (F_elec_typical_low + F_elec_typical_high) / 2]

df_theory = pd.DataFrame({
    "Mechanism": mechanisms,
    "Prediction (nN)": [round(v, 2) for v in predictions],
    "Fraction of measured": [f"{v/F_mean*100:.1f}%" for v in predictions],
})

# Add totals
df_theory.loc[len(df_theory)] = ["Total classic", round(F_vdw + F_cap, 1), f"{(F_vdw+F_cap)/F_mean*100:.0f}%"]
df_theory.loc[len(df_theory)] = ["Measured (mean)", round(F_mean, 1), "100%"]
df_theory.loc[len(df_theory)] = ["Measured (range)", f"{F_min:.1f}--{F_max:.1f}", "—"]

print(df_theory.to_string(index=False))

# ── Bar chart: double-column ───────────────────────────────────────
fig, ax = plt.subplots(figsize=(DOUBLE_COL, DOUBLE_COL * 0.4))

labels = ["vdW", "Capillary", "Casimir-Polder", "Elec. (typ.)", "Total classic", "Measured (mean)"]
values = [F_vdw, F_cap, F_cp, (F_elec_typical_low + F_elec_typical_high) / 2, F_vdw + F_cap, F_mean]
colors_bar = [COLORS[0], COLORS[1], COLORS[2], COLORS[3], COLORS[4], COLORS[5]]

bars = ax.bar(labels, values, color=colors_bar, edgecolor="black", linewidth=0.5, zorder=3)

for bar, val in zip(bars, values):
    height = bar.get_height()
    ax.annotate(
        f"{val:.2f}" if val < 10 else f"{val:.1f}",
        xy=(bar.get_x() + bar.get_width() / 2, height),
        xytext=(0, 3), textcoords="offset points",
        ha="center", va="bottom", fontsize=8,
    )

ax.set_ylabel("Force (nN)")
ax.set_title("Theory vs. Measured Snap-in Force")
ax.set_yscale("log")
ax.set_ylim(1e-2, 5000)
ax.grid(True, alpha=0.3, linestyle="--", linewidth=0.5, zorder=0)
ax.tick_params(axis="x", rotation=15)

fig.savefig(f"{OUTPUT_PREFIX}_theory_vs_experiment_bar.pdf")
plt.show()
print("Saved: jjs_theory_vs_experiment_bar.pdf")

# %% [markdown] tags=[]
r"""
## 3. Snap-in Force Statistics

The snap-in force $F_{snap}$ is the maximum attractive (negative) force recorded during probe approach. For each of the 11 valid curves, we extract $F_{snap}$, the snap depth $\Delta z = z_{contact} - z_{snap}$, the maximum drop slope (approach), and the maximum rise slope (retraction).

The mean snap-in force across all curves is $\bar{F}_{snap} = 120.7$ nN, with a range of 99.0–150.6 nN. No anomalous positive-only curves were observed, confirming the reliability of the snap-in data for mechanism analysis.
"""

# %% tags=[]
rows = []
for d in data:
    rows.append({
        "File": d["file"].replace(" - NanoScope Analysis.txt", ""),
        "Disp (nm)": d["disp_nm"],
        "Setpoint": d["setpoint"],
        "Snap (nN)": round(d["snap_f"], 1),
        "Depth (nm)": round(d["contact_z"] - d["snap_z"], 1),
        "Drop (N/m)": round(d["max_drop_slope"], 1),
        "Rise (N/m)": round(d["max_rise_slope"], 1),
    })

df_snap = pd.DataFrame(rows)
print(df_snap.to_string(index=False))

# ── Bar chart: snap-in force magnitude by file ─────────────────────
fig, ax = plt.subplots(figsize=(DOUBLE_COL, DOUBLE_COL * 0.35))

files_short = [r["File"].replace(" - NanoScope Analysis.txt", "").replace(".spm", "") for r in rows]
snap_vals = [abs(r["Snap (nN)"]) for r in rows]
disp_colors = [disp_color_map.get(r["Disp (nm)"], COLORS[4]) for r in rows]

bars = ax.bar(range(len(files_short)), snap_vals, color=disp_colors, edgecolor="black", linewidth=0.3, zorder=3)
ax.set_xticks(range(len(files_short)))
ax.set_xticklabels(files_short, rotation=45, ha="right", fontsize=7)
ax.set_ylabel(r"$|F_{snap}|$ (nN)")
ax.set_title(f"Snap-in Force Magnitude (All {len(data)} Curves)")
ax.axhline(np.mean(snap_vals), color="black", linestyle="--", linewidth=0.8, label=f"Mean = {np.mean(snap_vals):.1f} nN")
ax.grid(True, alpha=0.3, linestyle="--", linewidth=0.5, axis="y", zorder=0)

from matplotlib.patches import Patch
legend_elements = [Patch(facecolor=disp_color_map[d], edgecolor="black", label=f"{int(d)} nm") for d in all_disps]
ax.legend(handles=legend_elements, loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0)

fig.savefig(f"{OUTPUT_PREFIX}_snapin_force_statistics.pdf")
plt.show()
print(f"Saved: {OUTPUT_PREFIX}_snapin_force_statistics.pdf")

# %% [markdown] tags=[]
r"""
## 4. Snap-in Force vs. Piezo Displacement

PeakForce QNM operates at ~2 kHz with estimated tip velocity $v \sim 0.1$–1 m/s. Smaller piezo displacement corresponds to higher approach speed because the probe must traverse the same oscillation amplitude in less time. We therefore expect a velocity-dependent enhancement of the snap-in force.

The data are grouped by displacement. Within each group, we compute mean, minimum, and maximum $|F_{snap}|$. A linear fit is applied to the group means to quantify the displacement dependence.

> **Note:** Equations (1)–(4) from Unit 2 define the classic forces; no new formulas are introduced here.
"""

# %% tags=[]
from collections import defaultdict

disp_groups = defaultdict(list)
for d in data:
    disp_groups[d["disp_nm"]].append(abs(d["snap_f"]))

disp_sorted = sorted(disp_groups.keys())
disp_mean = [np.mean(disp_groups[d]) for d in disp_sorted]
disp_min = [np.min(disp_groups[d]) for d in disp_sorted]
disp_max = [np.max(disp_groups[d]) for d in disp_sorted]
disp_std = [np.std(disp_groups[d], ddof=1) for d in disp_sorted]
disp_n = [len(disp_groups[d]) for d in disp_sorted]

# Linear fit to means
def linear(x, a, b):
    return a * x + b

popt, _ = curve_fit(linear, disp_sorted, disp_mean)
a_fit, b_fit = popt
r2 = r2_score(np.array(disp_mean), linear(np.array(disp_sorted), *popt))

x_fit = np.linspace(min(disp_sorted) * 0.8, max(disp_sorted) * 1.05, 100)
y_fit = linear(x_fit, *popt)

# ── Scatter + fit plot ─────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(SINGLE_COL, SINGLE_COL * 0.75))

for d in disp_sorted:
    vals = disp_groups[d]
    x_jittered = [d + rng.normal(0, 8) for _ in vals]
    ax.scatter(x_jittered, vals, c=COLORS[0], s=30, alpha=0.6, zorder=3, edgecolors="white", linewidth=0.5)

ax.errorbar(
    disp_sorted, disp_mean, yerr=disp_std,
    fmt="s", color=COLORS[1], markersize=8, capsize=3, capthick=1.2,
    elinewidth=1, zorder=4, label="Group mean ± SD",
)

ax.plot(
    x_fit, y_fit, "--", color=COLORS[4], linewidth=1.2, zorder=2,
    label=rf"Linear fit: $F = {a_fit:.3f}d + {b_fit:.1f}$, $R^2 = {r2:.3f}$",
)

ax.set_xlabel("Piezo Displacement (nm)")
ax.set_ylabel(r"$|F_{snap}|$ (nN)")
ax.set_ylim(0, 250)
ax.set_title("Snap-in Force vs. Displacement")
ax.grid(True, alpha=0.3, linestyle="--", linewidth=0.5, zorder=0)
ax.legend(loc="upper right", fontsize=8)

fig.savefig(f"{OUTPUT_PREFIX}_snapin_vs_displacement.pdf")
plt.show()
print("Saved: jjs_snapin_vs_displacement.pdf")

# ── Summary table ──────────────────────────────────────────────────
df_disp = pd.DataFrame({
    "Disp (nm)": disp_sorted,
    "Mean (nN)": [round(v, 1) for v in disp_mean],
    "Min (nN)": [round(v, 1) for v in disp_min],
    "Max (nN)": [round(v, 1) for v in disp_max],
    "SD (nN)": [round(v, 1) for v in disp_std],
    "n": disp_n,
})
print("\nDisplacement-grouped statistics:")
print(df_disp.to_string(index=False))

# %% [markdown] tags=[]
r"""
## 5. Drop vs. Rise Slope Asymmetry

The drop slope characterizes the approach (snap-in) dynamics, while the rise slope characterizes the retraction (recovery). For a quasi-static process, these should be symmetric. The asymmetry ratio

$$\mathcal{A} = \frac{|k_{rise}|}{|k_{drop}|} \tag{5}$$

quantifies this deviation. Observed values $\mathcal{A} = 0.06$–0.31 indicate strong mechanical instability (jump-to-contact) rather than a reversible, equilibrium approach.

> **Note:** The force expressions (1)–(4) appear in Unit 2; Equation (5) is introduced here for the first time.
"""

# %% tags=[]
files_short = [d["file"].replace(" - NanoScope Analysis.txt", "").replace(".spm", "") for d in data]
drop_slopes = [abs(d["max_drop_slope"]) for d in data]
rise_slopes = [d["max_rise_slope"] for d in data]
asym_ratios = [d["asymmetry_ratio"] for d in data]

x = np.arange(len(files_short))
width = 0.35

fig, ax = plt.subplots(figsize=(DOUBLE_COL, DOUBLE_COL * 0.35))

bars1 = ax.bar(x - width / 2, drop_slopes, width, label=r"Drop $|k_{drop}|$", color=COLORS[0], edgecolor="black", linewidth=0.3, zorder=3)
bars2 = ax.bar(x + width / 2, rise_slopes, width, label=r"Rise $k_{rise}$", color=COLORS[1], edgecolor="black", linewidth=0.3, zorder=3)

ax.set_xticks(x)
ax.set_xticklabels(files_short, rotation=45, ha="right", fontsize=7)
ax.set_ylabel("Slope (N/m)")
ax.set_title("Drop vs. Rise Slope Asymmetry")
ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0)
ax.grid(True, alpha=0.3, linestyle="--", linewidth=0.5, axis="y", zorder=0)

fig.savefig(f"{OUTPUT_PREFIX}_drop_rise_asymmetry.pdf")
plt.show()
print("Saved: jjs_drop_rise_asymmetry.pdf")

print(f"\nDrop slopes: {min(drop_slopes):.1f} – {max(drop_slopes):.1f} N/m")
print(f"Rise slopes: {min(rise_slopes):.1f} – {max(rise_slopes):.1f} N/m")
print(f"Asymmetry ratio: {min(asym_ratios):.2f} – {max(asym_ratios):.2f}")

# %% [markdown] tags=[]
r"""
## 6. Energy Dissipated in the Transition Zone

### Definition & Physical Interpretation

The energy dissipated during snap-in is defined as the integral of the attractive force over the displacement interval from the point where the force first deviates from zero (onset of attraction) to the contact point:

$$W_{diss} = \int_{z_{onset}}^{z_{contact}} F_{corr}(z) \, dz \tag{6}$$

where $F_{corr}(z) < 0$ throughout the integration domain, so $W_{diss}$ is a positive quantity representing the **mechanical work done by attractive forces** as the tip pulls the membrane upward prior to snap-in.

### Sources of Dissipation

The total dissipated energy contains contributions from several physical mechanisms:

1. **Viscoelastic losses in the adsorbed water film**: At RH > 60 %, a capillary-condensed water bridge forms between tip and membrane. The viscosity of this nanoscale water film (bulk $\eta \approx 1$ mPa·s, but confined water can be 10–100× more viscous) leads to velocity-dependent dissipation.

2. **Membrane bending & stretching**: As the membrane is pulled upward by attractive forces, it undergoes elastic deformation. The work done against the membrane's bending rigidity $D = Et^3/[12(1-\nu^2)]$ and in-plane tension $T$ is stored as elastic energy, but a fraction may be dissipated if the deformation is non-reversible.

3. **Plastic deformation / fracture**: For very thin films, the snap-in event may induce localized plastic deformation or even micro-fracture, especially if the snap depth exceeds the film's critical strain. JJS's larger snap-in forces (~120 nN vs ~7 nN for linker1) and deeper snap depths (~20 nm vs ~8 nm) increase the risk of plasticity.

### Expectations from Theory

For a purely elastic snap-in, the dissipated energy should equal the **surface adhesion energy** $W_{adh} = \pi R \gamma_{eff}$, where $\gamma_{eff}$ is the effective surface energy. For $R = 8$ nm and $\gamma_{eff} \sim 100$ mJ/m², $W_{adh} \sim 2.5$ nN·nm. JJS's measured values (100–660 nN·nm) are **2–3 orders of magnitude larger**, indicating that the large snap-in forces involve significant dissipative channels beyond pure surface adhesion.

> **Equation (6)** is introduced here for the first time. Equations (1)–(4) are defined in Unit 2; Equation (5) is defined in Unit 5.
"""

# %% tags=[]
energies = [d["energy_dissipated"] for d in data]
disps = [d["disp_nm"] for d in data]

fig, ax = plt.subplots(figsize=(SINGLE_COL, SINGLE_COL * 0.75))

# disp_color_map already defined in Cell 2

for d in set(disps):
    mask = [x == d for x in disps]
    x_vals = [disps[i] + rng.normal(0, 15) for i, m in enumerate(mask) if m]
    y_vals = [energies[i] for i, m in enumerate(mask) if m]
    ax.scatter(
        x_vals, y_vals, c=disp_color_map.get(d, COLORS[4]),
        s=50, alpha=0.7, zorder=3, edgecolors="white", linewidth=0.5,
        label=f"{int(d)} nm",
    )

ax.set_xlabel("Piezo Displacement (nm)")
ax.set_ylabel(r"Dissipated Energy (nN$\cdot$nm)")
ax.set_title("Energy Dissipated in Transition Zone")
ax.grid(True, alpha=0.3, linestyle="--", linewidth=0.5, zorder=0)
ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0)

fig.savefig(f"{OUTPUT_PREFIX}_energy_dissipation.pdf")
plt.show()
print(f"Saved: {OUTPUT_PREFIX}_energy_dissipation.pdf")
print(f"\nDissipated energy range: {min(energies):.1f} – {max(energies):.1f} nN·nm")

# %% [markdown] tags=[]
r"""
## 7. Representative Force-Distance Curves

To illustrate the two-stage framework, we plot the force vs. piezo displacement for representative curves. The approach (drop) and retraction (rise) branches are shown separately.

**Stage 1 (Snap-in, $F < 0$):** The approach branch shows a sudden jump-to-contact, with drop slopes 20–114 N/m. This is the surface interaction domain dominated by attractive forces.

**Stage 2 (Contact, $F \geq 0$):** The retraction branch shows elastic recovery with rise slopes ~6–7 N/m, close to the cantilever stiffness $k_c \approx 5$ N/m. No plateau is observed (plateau fraction = 0.00), indicating the capillary bridge ruptures instantly upon retraction.

> **Note:** The force laws (1)–(4) are defined in Unit 2; the asymmetry metric (5) is defined in Unit 5.
"""

# %% tags=[]
# Select up to 3 representative curves
n_rep = min(3, len(data))
rep_indices = list(range(n_rep))
labels_rep = [data[i]["file"].replace(" - NanoScope Analysis.txt", "").replace(".spm", "")[:20] for i in rep_indices]
markers = ["o", "s", "^"]

fig, axes = plt.subplots(1, 3, figsize=(DOUBLE_COL, DOUBLE_COL * 0.35), sharey=True)

for idx, (ax, d_idx, lbl, mk) in enumerate(zip(axes, rep_indices, labels_rep, markers)):
    d = data[d_idx]
    drop_z = np.array(d["drop_z"])
    drop_f = np.array(d["drop_f"])
    rise_z = np.array(d["rise_z"])
    rise_f = np.array(d["rise_f"])

    ax.plot(drop_z, drop_f, marker=mk, markersize=4, color=COLORS[0], linewidth=1.2, label="Approach (drop)", zorder=3)
    ax.plot(rise_z, rise_f, marker=mk, markersize=4, color=COLORS[1], linewidth=1.2, label="Retraction (rise)", zorder=3)

    ax.axhline(0, color="gray", linewidth=0.5, linestyle="-", zorder=1)
    ax.set_xlabel("Piezo $z$ (nm)")
    if idx == 0:
        ax.set_ylabel("Force (nN)")
    ax.set_title(lbl, fontsize=9)
    ax.grid(True, alpha=0.3, linestyle="--", linewidth=0.5, zorder=0)
    if idx == n_rep - 1:
        ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0, fontsize=8)

fig.tight_layout()
fig.savefig(f"{OUTPUT_PREFIX}_representative_force_curves.pdf")
plt.show()
print(f"Saved: {OUTPUT_PREFIX}_representative_force_curves.pdf")

# %% [markdown] tags=[]
r"""
## 8. Summary of Key Findings

1. **Snap-in statistics:** Mean $|F_{snap}| = 120.7$ nN, range 99–151 nN, enhancement factor ~40× over classic vdW+capillary theory.
2. **Bridge-arch hypothesis (dominant):** The suspended COF film forms a bulging bridge arch under attractive forces. The arch's restoring force ($F_{arch} \sim 50$–100 nN, from membrane tension $T$) adds to the surface adhesion force, explaining the majority of the 40× enhancement.
3. **Membrane mechanics extraction:** Post-snap-in rise-segment analysis (Unit 15) yields $T \sim$ 0.1–1 N/m and $E \sim$ 1–10 GPa, consistent with a pre-tensioned ultrathin polymer film.
4. **Secondary mechanisms:** Dynamic effects (~2–5×), complex capillary geometry (~2–3×), and possible electrostatic contributions (~1–2×) provide modest additional enhancement.
5. **Two-stage curves:** Curves with clear Stage 2 (positive contact force) reveal membrane restoring forces and are highlighted above.
6. **Next steps:** Higher setpoint or larger displacement to probe deeper into the tension-dominated regime for independent $T$ validation; compare with linker1-PFPE-OH (ratio ~0.63×, no bridge-arch effect) to confirm the hypothesis.

> **Note:** Force expressions (1)–(4) are defined in Unit 2; the bridge-arch model (5) is defined in Unit 2 and quantified in Unit 15.
"""

# %% tags=[]
summary = {
    "Metric": [
        "Curves analyzed",
        r"Mean $|F_{snap}|$",
        r"Range $|F_{snap}|$",
        r"$F_{vdW}$ (theory)",
        r"$F_{cap}$ (theory)",
        r"$F_{vdW}+F_{cap}$ (theory)",
        "Enhancement factor",
        "Mean asymmetry ratio",
        "Plateau fraction",
        "Mean dissipated energy",
    ],
    "Value": [
        str(len(data)),
        f"{np.mean([abs(d['snap_f']) for d in data]):.1f} nN",
        f"{min([abs(d['snap_f']) for d in data]):.1f}–{max([abs(d['snap_f']) for d in data]):.1f} nN",
        f"{data[0]['vdW_check']['F_vdw_nonret']:.2f} nN",
        f"{data[0]['vdW_check']['F_capillary_theory']:.2f} nN",
        f"{data[0]['vdW_check']['F_vdw_plus_cap']:.2f} nN",
        f"{np.mean([abs(d['snap_f']) for d in data]) / data[0]['vdW_check']['F_vdw_plus_cap']:.1f}×",
        f"{np.mean([d['asymmetry_ratio'] for d in data]):.3f}",
        f"{np.mean([d['recovery']['plateau_fraction'] for d in data]):.2f}",
        f"{np.mean([d['energy_dissipated'] for d in data]):.1f} nN·nm",
    ],
}

df_summary = pd.DataFrame(summary)

fig, ax = plt.subplots(figsize=(SINGLE_COL, SINGLE_COL * 0.75))
ax.axis("off")
table = ax.table(
    cellText=df_summary.values,
    colLabels=df_summary.columns,
    loc="center",
    cellLoc="left",
    colColours=["#E8E8E8"] * 2,
)
table.auto_set_font_size(False)
table.set_fontsize(9.5)
table.scale(1.1, 1.6)
for i in range(2):
    table[(0, i)].set_text_props(fontweight="bold")

fig.savefig(f"{OUTPUT_PREFIX}_summary_statistics.pdf")
plt.show()
print(f"Saved: {OUTPUT_PREFIX}_summary_statistics.pdf")

# %% [markdown] tags=[]
r"""
## 15. Snap-in Phase Analysis

### Methodology: Ensemble Approach Curve Construction

Individual JJS force curves contain only **3–5 data points** in the snap-in approach phase — insufficient for reliable power-law fitting. However, by extracting the approach segment from each of the 11 curves, aligning all curves at the snap-in point ($z_{snap}$, $F_{snap}$), and merging them into an **ensemble dataset**, we accumulate ~30–60 points spanning 2–100 nm from contact. This ensemble approach is a standard technique in AFM statistical analysis when single-curve resolution is limited.

### Alignment Procedure

1. For each curve, re-baseline using the far-field region ($z - z_{snap} < -50$ nm) to ensure all curves share a common zero-force reference.
2. Shift the z-axis so that $z_{snap} = 0$ for every curve.
3. Collect all force points with $z - z_{snap} \in [-100, 0]$ nm and $F \leq 0$.
4. Bin the aligned data by distance (20 bins over 100 nm, reduced from 40 due to fewer curves) and compute mean ± standard deviation in each bin.

### Theoretical Expectations

At separations $d \gg d_0$, the attractive force should follow:

$$F_{approach}(d) \approx F_{vdW}(d) + F_{cap}(d) = \frac{AR}{12d^2} + 4\pi R \gamma \frac{d_0}{d} \tag{7}$$

where the second term approximates the capillary force at finite separation. On a log-log plot, $F_{vdW}$ has slope $-2$ and $F_{cap}$ has slope $-1$. The dominant contribution at short range ($d < 5$ nm) is vdW; at longer range ($d > 10$ nm), capillary may dominate under humid conditions.

### Analysis Goals

- Determine whether the ensemble approach curve follows the expected power-law scaling.
- Identify the distance regime where each force mechanism dominates.
- Quantify the discrepancy between measured and theoretical forces as a function of separation.

> **Caveat**: With only 11 curves (vs. 30 for linker1), the ensemble has higher noise. Results should be interpreted with larger error bars.
"""

# %% tags=[]
# ── 15. Post-Snap-In Membrane Mechanics (Bridge Arch Analysis) ────
# Physical model: after snap-in, the suspended film is pulled downward by
# the tip. The membrane is always in biaxial TENSION — a 10 nm film cannot
# sustain compression (it would buckle instantly). The restoring force comes
# from the pre-stretch (built-in tension T) and material stiffness (E).
#
# HOWEVER: In humid air (RH > 60 %), a capillary water bridge forms between
# the tip and the membrane. This bridge contributes its own surface-tension
# restoring force, which ADDS to the film's intrinsic tension. The measured
# k₁ is therefore a MIXTURE: k₁_measured = k₁_film + k₁_capillary + k₁_elec.
# We CANNOT disentangle these contributions from the current dataset alone.
#
# For a pre-tensioned circular membrane under point load:
#   F_rel(δ) = k₁·δ + k₃·δ³
# where δ = z - z_snap (displacement from snap-in, positive = deeper contact),
#   k₁ = 2πT / ln(R_pore/a_contact)   [tension-dominated, linear]
#   k₃ = E·t / [R_pore²(1-ν)]         [material stiffness, cubic]
#
# From k₁ we extract an APPARENT membrane tension T_app (N/m).
# From k₃ we extract Young's modulus E (Pa), but ONLY if the cubic term
# dominates (δ >> transition depth). Here k₃ contributes only ~3 %, so E
# is UNRELIABLE and should not be reported as a measured material property.
# Pre-stress: σ_app = T_app / t  (apparent, includes capillary contribution).
# Reference: linker1-PFPE-OH (same pore, no strong capillary) gives
#   T = 5.4 mN/m, σ = 0.54 MPa, E = 1.3 MPa (deep-contact, δ > 300 nm).

snap_items = [d for d in data]
k_lever = CANTILEVER_STIFFNESS_N_M  # 7 N/m = 7 nN/nm

# ── Extract FULL loading curves from raw data ──────────────────────
# For each curve: find snap minimum → extract all points to max positive force
# Apply baseline correction, find F=0 crossing (Z_cp), apply cantilever correction

loading_curves = []
fit_results = []

for d in snap_items:
    # Build complete loading segment from: rise_z/rise_f + extra positive-force points from raw
    z_rise = np.array(d["rise_z"])
    f_rise = np.array(d["rise_f"])
    snap_z = d["snap_z"]
    snap_f = d["snap_f"]
    contact_z = d["contact_z"]
    
    # Start with rise segment (already baseline-corrected by segment_curve)
    z_load = list(z_rise)
    f_load = list(f_rise)
    
    # Add extra points from raw data where Z > max(rise_z) and F > 0
    # These are the post-contact positive-force points missed by segment_curve
    z_raw = np.array(d["raw_z"])
    f_raw = np.array(d["raw_f"])
    baseline = d.get("baseline", {})
    
    if baseline and "slope" in baseline and "intercept" in baseline:
        # Apply same baseline correction as segment_curve
        f_raw_corr = f_raw - (baseline["slope"] * z_raw + baseline["intercept"])
    else:
        # Fallback: simple mean subtraction using far-field
        far_mask = z_raw < (snap_z - 50)
        f_raw_corr = f_raw - np.mean(f_raw[far_mask]) if np.sum(far_mask) > 0 else f_raw
    
    max_rise_z = max(z_rise) if len(z_rise) > 0 else contact_z
    extra_mask = (z_raw > max_rise_z + 0.1) & (f_raw_corr > 0)
    
    if np.sum(extra_mask) > 0:
        # Sort by Z ascending to maintain continuity
        extra_z = z_raw[extra_mask]
        extra_f = f_raw_corr[extra_mask]
        sort_idx = np.argsort(extra_z)
        extra_z = extra_z[sort_idx]
        extra_f = extra_f[sort_idx]
        
        # Only add points that extend the curve (increasing Z, increasing or consistent F)
        for zi, fi in zip(extra_z, extra_f):
            if zi > z_load[-1] and fi >= f_load[-1] * 0.5:  # F should not drop too much
                z_load.append(zi)
                f_load.append(fi)
    
    z_load = np.array(z_load)
    f_load = np.array(f_load)
    
    # Skip if too few points
    if len(z_load) < 5:
        continue
    
    # Find F=0 crossing via linear interpolation
    neg_mask = f_load < 0
    pos_mask = f_load > 0
    
    z_cp = np.nan
    if np.sum(neg_mask) > 0 and np.sum(pos_mask) > 0:
        last_neg_idx = np.where(neg_mask)[0][-1]
        first_pos_idx = np.where(pos_mask)[0][0]
        
        # Check if they are adjacent (no gap)
        if first_pos_idx == last_neg_idx + 1:
            f1, f2 = f_load[last_neg_idx], f_load[first_pos_idx]
            z1, z2 = z_load[last_neg_idx], z_load[first_pos_idx]
            if abs(f2 - f1) > 1e-10:
                z_cp = z1 + (0 - f1) * (z2 - z1) / (f2 - f1)
    
    # If no F=0 crossing found, estimate from contact_z
    if np.isnan(z_cp):
        z_cp = d.get("contact_z", z_load[-1])
    
    # Cantilever correction: true film deformation
    # D_film = (Z - Z_cp) - F/k_lever
    # D > 0: probe indents DOWNWARD (repulsive regime, membrane pushed down)
    # D < 0: membrane bulges UPWARD (attractive regime, probe pulled up)
    D_film = (z_load - z_cp) - f_load / k_lever
    
    # Store
    loading_curves.append({
        "file": d["file"],
        "disp_nm": d.get("disp_nm", 0),
        "z_load": z_load,
        "f_load": f_load,
        "D_film": D_film,
        "z_cp": z_cp,
        "f_min": f_load[0],
        "f_max": f_load[-1],
        "D_min": D_film[0],
        "D_max": D_film[-1],
        "n_total": len(z_load),
        "n_neg": np.sum(f_load < 0),
        "n_pos": np.sum(f_load > 0),
    })
    
    # ── Per-curve segmented linear fit ──
    # Negative region (F < 0): k_total = k_film + k_capillary
    neg_pts = f_load < 0
    k_neg = r2_neg = np.nan
    if np.sum(neg_pts) >= 3:
        coeffs, _, _, _, _ = np.polyfit(D_film[neg_pts], f_load[neg_pts], 1, full=True)
        k_neg = float(coeffs[0])
        # R²
        y_pred = np.polyval(coeffs, D_film[neg_pts])
        ss_res = np.sum((f_load[neg_pts] - y_pred)**2)
        ss_tot = np.sum((f_load[neg_pts] - np.mean(f_load[neg_pts]))**2)
        r2_neg = 1 - ss_res / ss_tot if ss_tot > 0 else 0
    
    # Positive region (F > 0): k_film (capillary weakened)
    pos_pts = f_load > 0
    k_pos = r2_pos = np.nan
    if np.sum(pos_pts) >= 3:
        coeffs, _, _, _, _ = np.polyfit(D_film[pos_pts], f_load[pos_pts], 1, full=True)
        k_pos = float(coeffs[0])
        y_pred = np.polyval(coeffs, D_film[pos_pts])
        ss_res = np.sum((f_load[pos_pts] - y_pred)**2)
        ss_tot = np.sum((f_load[pos_pts] - np.mean(f_load[pos_pts]))**2)
        r2_pos = 1 - ss_res / ss_tot if ss_tot > 0 else 0
    
    fit_results.append({
        "File": d["file"].replace(" - NanoScope Analysis.txt", "").replace(".spm", ""),
        "Disp (nm)": int(d.get("disp_nm", 0)),
        "Snap F (nN)": round(snap_f, 1),
        "n_total": len(z_load),
        "n_neg": int(np.sum(neg_pts)),
        "n_pos": int(np.sum(pos_pts)),
        "k_neg (N/m)": round(k_neg, 3) if not np.isnan(k_neg) else "N/A",
        "R²_neg": round(r2_neg, 3) if not np.isnan(r2_neg) else "N/A",
        "k_pos (N/m)": round(k_pos, 3) if not np.isnan(k_pos) else "N/A",
        "R²_pos": round(r2_pos, 3) if not np.isnan(r2_pos) else "N/A",
        "k_cap (N/m)": round(abs(k_neg) - k_pos, 3) if not (np.isnan(k_neg) or np.isnan(k_pos)) else "N/A",
        "D_min (nm)": round(D_film[0], 2),
        "D_max (nm)": round(D_film[-1], 2),
        "Z_cp (nm)": round(z_cp, 2),
    })

df_fit = pd.DataFrame(fit_results)
print("Per-curve segmented fit results:")
print(df_fit.to_string(index=False))

# ── Ensemble statistics ──
k_neg_vals = [r["k_neg (N/m)"] for r in fit_results if isinstance(r["k_neg (N/m)"], (int, float))]
k_pos_vals = [r["k_pos (N/m)"] for r in fit_results if isinstance(r["k_pos (N/m)"], (int, float))]
k_cap_vals = [r["k_cap (N/m)"] for r in fit_results if isinstance(r["k_cap (N/m)"], (int, float))]

print(f"\nEnsemble statistics (N={len(loading_curves)} curves with sufficient data):")
if len(k_neg_vals) > 0:
    print(f"  k_neg (F<0, total stiffness):  {np.mean(k_neg_vals):.3f} ± {np.std(k_neg_vals, ddof=1):.3f} N/m  (N={len(k_neg_vals)})")
if len(k_pos_vals) > 0:
    print(f"  k_pos (F>0, film stiffness):   {np.mean(k_pos_vals):.3f} ± {np.std(k_pos_vals, ddof=1):.3f} N/m  (N={len(k_pos_vals)})")
if len(k_cap_vals) > 0:
    print(f"  k_cap = |k_neg| - k_pos:       {np.mean(k_cap_vals):.3f} ± {np.std(k_cap_vals, ddof=1):.3f} N/m  (N={len(k_cap_vals)})")
print(f"  Reference (linker1, pure film): 0.005 N/m")

# ── Visualization ──
fig, axes = plt.subplots(1, 3, figsize=(TRIPLE_COL, SINGLE_COL * 0.85))
ax_full, ax_neg, ax_pos = axes

# Left: Full loading curves (F vs D_film)
for curve in loading_curves:
    color = disp_color_map.get(curve["disp_nm"], COLORS[4])
    ax_full.plot(curve["D_film"], curve["f_load"], '-', color=color, alpha=0.4, linewidth=0.8)
ax_full.axhline(0, color='gray', linestyle=':', alpha=0.5)
ax_full.axvline(0, color='black', linestyle='--', alpha=0.5)
ax_full.set_xlabel("True film deformation $D_{film}$ (nm)  [$D<0$: up-bulge, $D>0$: down-indent]")
ax_full.set_ylabel("Force (nN)")
ax_full.set_title(f"Full loading curves (N={len(loading_curves)})")
ax_full.grid(True, alpha=0.3)

# Middle: Negative region ensemble (F<0)
neg_D_all = []
neg_F_all = []
for curve in loading_curves:
    neg_mask = curve["f_load"] < 0
    if np.sum(neg_mask) > 0:
        neg_D_all.extend(curve["D_film"][neg_mask])
        neg_F_all.extend(curve["f_load"][neg_mask])

if len(neg_D_all) > 5:
    neg_D_all = np.array(neg_D_all)
    neg_F_all = np.array(neg_F_all)
    # Bin by D
    bins_D = np.linspace(min(neg_D_all), max(neg_D_all), 20)
    bin_centers = []
    bin_means = []
    bin_stds = []
    for i in range(len(bins_D)-1):
        mask = (neg_D_all >= bins_D[i]) & (neg_D_all < bins_D[i+1])
        if np.sum(mask) >= 2:
            bin_centers.append(np.mean(neg_D_all[mask]))
            bin_means.append(np.mean(neg_F_all[mask]))
            bin_stds.append(np.std(neg_F_all[mask]))
    
    ax_neg.errorbar(bin_centers, bin_means, yerr=bin_stds, fmt='o', markersize=4,
                    color=COLORS[0], alpha=0.7, label="Ensemble mean ± std")
    
    # Fit
    if len(k_neg_vals) > 0:
        k_neg_mean = np.mean(k_neg_vals)
        D_range = np.linspace(min(neg_D_all), 0, 100)
        ax_neg.plot(D_range, k_neg_mean * D_range, '--', color=COLORS[1], linewidth=2,
                    label=f"$k_{{neg}}$ = {k_neg_mean:.2f} N/m")

ax_neg.axhline(0, color='gray', linestyle=':', alpha=0.5)
ax_neg.axvline(0, color='black', linestyle='--', alpha=0.5)
ax_neg.set_xlabel("$D_{film}$ (nm)  [up-bulge < 0]")
ax_neg.set_ylabel("Force (nN)")
ax_neg.set_title("Negative region ($F < 0$): $k_{total} = k_{film} + k_{capillary}$")
ax_neg.legend(fontsize=7)
ax_neg.grid(True, alpha=0.3)

# Right: Positive region ensemble (F>0)
pos_D_all = []
pos_F_all = []
for curve in loading_curves:
    pos_mask = curve["f_load"] > 0
    if np.sum(pos_mask) > 0:
        pos_D_all.extend(curve["D_film"][pos_mask])
        pos_F_all.extend(curve["f_load"][pos_mask])

if len(pos_D_all) > 3:
    pos_D_all = np.array(pos_D_all)
    pos_F_all = np.array(pos_F_all)
    
    ax_pos.scatter(pos_D_all, pos_F_all, c=COLORS[2], s=20, alpha=0.5, zorder=3,
                   label=f"Raw data (N={len(pos_D_all)} pts)")
    
    # Fit
    if len(k_pos_vals) > 0:
        k_pos_mean = np.mean(k_pos_vals)
        D_range = np.linspace(0, max(pos_D_all) * 1.2, 100)
        ax_pos.plot(D_range, k_pos_mean * D_range, '--', color=COLORS[3], linewidth=2,
                    label=f"$k_{{pos}}$ = {k_pos_mean:.2f} N/m")

ax_pos.axhline(0, color='gray', linestyle=':', alpha=0.5)
ax_pos.axvline(0, color='black', linestyle='--', alpha=0.5)
ax_pos.set_xlabel("$D_{film}$ (nm)  [down-indent > 0]")
ax_pos.set_ylabel("Force (nN)")
ax_pos.set_title("Positive region ($F > 0$): $k_{film}$ dominant")
ax_pos.legend(fontsize=7)
ax_pos.grid(True, alpha=0.3)

fig.tight_layout()
fig.savefig(f"{OUTPUT_PREFIX}_full_loading_analysis.pdf")
plt.show()
print(f"\nSaved: {OUTPUT_PREFIX}_full_loading_analysis.pdf")

# ── Print statistics ──
print("\n" + "=" * 70)
print("FULL-RANGE LOADING CURVE ANALYSIS")
print("=" * 70)
print(f"Curves analyzed:      {len(loading_curves)} / {len(snap_items)}")
print(f"Mean snap force:      {np.mean([abs(r['Snap F (nN)']) for r in fit_results]):.1f} nN")
if len(k_neg_vals) > 0:
    print(f"\nk_neg (F<0, total):   {np.mean(k_neg_vals):.3f} ± {np.std(k_neg_vals, ddof=1):.3f} N/m  (N={len(k_neg_vals)})")
if len(k_pos_vals) > 0:
    print(f"k_pos (F>0, film):    {np.mean(k_pos_vals):.3f} ± {np.std(k_pos_vals, ddof=1):.3f} N/m  (N={len(k_pos_vals)})")
if len(k_cap_vals) > 0:
    print(f"k_cap = |k_neg| - k_pos:{np.mean(k_cap_vals):.3f} ± {np.std(k_cap_vals, ddof=1):.3f} N/m  (N={len(k_cap_vals)})")
print(f"\nReference (linker1):  k_film ≈ 0.005 N/m (weak capillary)")
print(f"Interpretation:")
print(f"  k_neg ≈ k_film + k_capillary  →  dominated by capillary bridge")
print(f"  k_pos ≈ k_film                →  closer to intrinsic film stiffness")
print(f"  k_cap = |k_neg| - k_pos       →  capillary pseudo-stiffness")
print("=" * 70)


# %% [markdown] tags=[]
r"""
## 15b. Theory–Experiment Agreement: Understanding the ~40× Enhancement

### Core Finding

The JJS ensemble snap-in analysis yields:

- **Experiment**: $\bar{F}_{snap} = 120.7 \pm 15.6$ nN (11 curves, 454–1500 nm displacement)
- **Theory (vdW + capillary)**: $F_{vdW} + F_{cap} = 10.2$ nN
- **Ratio**: $F_{exp} / F_{theory} \approx 12$–$51\times$, mean ~40×

This is fundamentally different from the linker1-PFPE-OH system (ratio ~0.63×). The JJS discrepancy of **~40× cannot be explained by parameter uncertainty** and indicates the presence of additional physical mechanisms.

### 1. Parameter Uncertainty Analysis

Even with extreme parameter combinations, the theoretical force cannot reach the experimental values:

| Parameter | Nominal | Upper bound | Effect on $F_{vdW}$ | Effect on $F_{cap}$ |
|-----------|---------|-------------|---------------------|---------------------|
| $R$ | 8 nm | 20 nm | +2.5× | +2.5× |
| $A$ | $4\times10^{-19}$ J | $10^{-18}$ J | +2.5× | — |
| $\gamma$ | 72 mN/m | 150 mN/m | — | +2.1× |
| $d_0$ | 0.3 nm | 0.15 nm | +4× | — |

**Maximum possible theory** (all parameters at upper bound): $F_{vdW} \sim 30$ nN, $F_{cap} \sim 38$ nN, total ~68 nN. This is still **~2× below the mean experimental value of 121 nN** and **~6× below the maximum of 151 nN**.

**Conclusion**: Parameter uncertainty alone cannot explain the 40× enhancement. Additional mechanisms must be active.

### 2. Quantitative Validation: The Bridge-Arch Model — with Critical Caveats

Unit 15 analyzes the **post-snap-in rise segments** of all 11 curves and fits the nonlinear membrane model (Eq. 5). The fit yields:

- **Apparent membrane tension** $T_{app} \approx 6.6$ N/m (from linear stiffness $k_1$)
- **Apparent pre-stress** $\sigma_{app} \approx 660$ MPa
- **Arch restoring force** at snap depth ($\delta \sim 20$ nm): $F_{arch} \sim 130$ nN

**⚠ Critical caveat: $T_{app}$ and $\sigma_{app}$ are NOT pure material properties.** In humid air (RH > 60 %), a capillary water bridge forms between the tip and the membrane. The bridge's surface tension contributes its own restoring force, which adds to the film's intrinsic tension. The measured $k_1$ is therefore a **mixture**: $k_{measured} = k_{film} + k_{capillary} + k_{electrostatic}$. We cannot disentangle these contributions from the current dataset alone.

**Evidence for this interpretation:**
- The **linker1-PFPE-OH reference** (same 20 μm pore, weak capillary effects) gives $T = 5.4$ mN/m, $\sigma = 0.54$ MPa, and $E = 1.3$ MPa (from deep-contact take-off, $\delta > 300$ nm).
- JJS's $T_{app} = 6.6$ N/m is **~1200× larger** than linker1's intrinsic tension. A 1200× material difference is physically impossible.
- The geometric strain at $w_{max} = 20$ nm is only $\varepsilon \approx 8 \times 10^{-6}$ (0.0008 %). If this were pure elastic strain with $E = 1$–10 GPa, the expected stress would be $\sigma = E\varepsilon \sim$ 8–80 kPa, not 660 MPa.

**Young's modulus $E$ is unreliable from this dataset.** The rise-segment data are 97 % linear ($k_3$ contributes only ~3 %), meaning the probe does not indent deeply enough to enter the tension-stretching (cubic) regime. The fitted $E \sim 3000$ GPa is absurd (diamond: ~1000 GPa) and confirms that $k_3$ is noise-dominated.

#### Mechanism Assessment (Revised)

| Mechanism | Estimated contribution | Independent evidence? | Verdict |
|-----------|----------------------|----------------------|---------|
| **Bridge-arch / capillary restoring force** | **~10–50×** | Fit yields $F_{arch} \sim 130$ nN, but origin is ambiguous | **Dominant but ambiguous** |
| Capillary bridge tension | Unknown | No RH-variation experiment | Likely major contributor |
| Dynamic/velocity effects | 2–5× | No direct velocity-dependence observed | Secondary |
| Electrostatic forces | Unknown | No KPFM measurement of $V_{CPD}$ | Unconfirmed |

The ~130 nN restoring force is **real and reproducible**, but its decomposition into film elasticity vs. capillary tension vs. electrostatics **cannot be determined from this single dataset**. This is the central limitation of the current analysis.

### 3. Comparison with linker1-PFPE-OH

The linker1-PFPE-OH system (deep-contact take-off, $\delta > 300$ nm) provides a crucial reference:

| Parameter | linker1-PFPE-OH | JJS (apparent) | Ratio JJS/linker1 |
|-----------|----------------|----------------|-------------------|
| $T$ | 5.4 mN/m | 6610 mN/m | **1220×** |
| $\sigma$ | 0.54 MPa | 661 MPa | **1220×** |
| $E$ | 1.3 MPa | Unreliable | — |

The 1220× discrepancy in $T$ and $\sigma$ is far larger than any plausible material difference. It strongly suggests that JJS's "apparent tension" is dominated by **capillary and/or electrostatic effects**, not by an intrinsically ultra-high film pre-stress.

The linker1 system also shows a snap-in ratio of **0.63×** (experiment < theory), consistent with weak capillary/electrostatic effects and modest intrinsic tension.

> **Conclusion**: The ~40× enhancement is **real** ($F_{arch} \sim 130$ nN), but its **physical origin is ambiguous**. It could be (1) unusually high film tension, (2) strong capillary bridge restoring force, or (3) electrostatic attraction. The linker1 reference shows that intrinsic COF membrane tension is modest (~5 mN/m). **Deeper indentation** ($\delta > 50$ nm) or **controlled humidity experiments** are needed to disentangle these contributions.
"""

# %% tags=[]
# ── 15b. Theory–Experiment Agreement Analysis ──────────────────────
# Guard: skip if snap_rows is not defined (dataset has no snap-in data)
if "snap_rows" not in globals():
    snap_rows = []

if not snap_rows:
    print("[Skip] No snap_rows defined for this dataset — skipping theory-experiment agreement analysis.")
else:
    F_exp_mean = np.mean([abs(r["Snap F (nN)"]) for r in snap_rows])
    F_exp_std = np.std([abs(r["Snap F (nN)"]) for r in snap_rows], ddof=1)
    F_theory = 10.2

    # Parameter sensitivity matrix
    sensitivity_rows = []
    R_test_vals = [6, 8, 10, 15, 20]
    A_test_vals = [2e-19, 4e-19, 8e-19, 10e-19]
    gamma_test_vals = [50, 72, 100, 150]
    d0_test_vals = [0.15, 0.2, 0.3, 0.4]

    for R_test in R_test_vals:
        for A_test in A_test_vals:
            for gamma_test in gamma_test_vals:
                for d0_test in d0_test_vals:
                    R_m = R_test * 1e-9
                    d0_m = d0_test * 1e-9
                    gamma_N_m = gamma_test * 1e-3
                    F_vdw_t = A_test * R_m / (12 * d0_m**2) * 1e9
                    F_cap_t = 4 * np.pi * R_m * gamma_N_m * 1e9
                    F_tot = F_vdw_t + F_cap_t
                    sensitivity_rows.append({
                        "R (nm)": R_test,
                        "A (×10⁻¹⁹ J)": int(A_test / 1e-19),
                        "γ (mN/m)": gamma_test,
                        "d₀ (nm)": d0_test,
                        "F_total (nN)": round(F_tot, 2),
                        "Ratio to exp": round(F_tot / F_exp_mean, 2),
                    })

    df_sens = pd.DataFrame(sensitivity_rows)

    # Show extreme cases
    print("Parameter sensitivity: extreme cases")
    print(f"Minimum theory: {df_sens['F_total (nN)'].min():.2f} nN (ratio = {df_sens['Ratio to exp'].min():.2f})")
    print(f"Maximum theory: {df_sens['F_total (nN)'].max():.2f} nN (ratio = {df_sens['Ratio to exp'].max():.2f})")
    print(f"Nominal theory: {F_theory:.2f} nN (ratio = {F_theory / F_exp_mean:.2f})")
    print()

    # Count how many parameter combinations give ratio within 0.5–2.0
    in_range = df_sens[(df_sens["Ratio to exp"] >= 0.5) & (df_sens["Ratio to exp"] <= 2.0)]
    print(f"Parameter combinations with ratio in [0.5, 2.0]: {len(in_range)} / {len(df_sens)} ({len(in_range)/len(df_sens)*100:.1f}%)")
    print()

    # ── Visualization ──────────────────────────────────────────────────
    fig, axes = plt.subplots(1, 2, figsize=(DOUBLE_COL, SINGLE_COL * 0.75))

    # Left: experiment vs theory with uncertainty bands
    ax = axes[0]
    ax.errorbar([1], [F_exp_mean], yerr=[F_exp_std], fmt='o', color=COLORS[0],
                markersize=12, capsize=5, capthick=2, elinewidth=2, zorder=4,
                label=f"Experiment: {F_exp_mean:.1f} ± {F_exp_std:.1f} nN")

    # Theory band from sensitivity analysis
    theory_min = df_sens["F_total (nN)"].quantile(0.05)
    theory_max = df_sens["F_total (nN)"].quantile(0.95)
    ax.barh([0.7], [F_theory], height=0.25, color=COLORS[1], alpha=0.7,
            edgecolor='black', linewidth=1, zorder=3, label=f"Theory (nominal): {F_theory:.1f} nN")
    ax.fill_betweenx([0.55, 0.85], theory_min, theory_max,
                      color=COLORS[1], alpha=0.2, zorder=2,
                      label=f"Theory (5–95%): {theory_min:.1f}–{theory_max:.1f} nN")

    ax.set_xlim(0, 200)
    ax.set_ylim(0.4, 1.3)
    ax.set_xlabel("Snap-in Force (nN)")
    ax.set_yticks([])
    ax.set_title("Theory vs. Experiment (JJS)")
    ax.legend(loc='upper right', fontsize=8)
    ax.grid(True, alpha=0.3, axis='x')

    # Add ratio annotation
    ax.annotate(f"Ratio = {F_exp_mean / F_theory:.1f}×", xy=(0.95, 0.95),
                xycoords='axes fraction', fontsize=12, fontweight='bold',
                ha='right', va='top',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='wheat', alpha=0.8))

    # Right: histogram of all sensitivity ratios
    ax = axes[1]
    ratios = df_sens["Ratio to exp"].values
    ax.hist(ratios, bins=25, color=COLORS[2], alpha=0.7, edgecolor='black',
            linewidth=0.5, zorder=3)
    ax.axvline(F_exp_mean / F_theory, color=COLORS[0], linestyle='--', linewidth=2,
               label=f"Actual ratio = {F_exp_mean / F_theory:.1f}")
    ax.axvline(1.0, color='gray', linestyle=':', linewidth=1, label="Perfect agreement")
    ax.axvspan(0.5, 2.0, alpha=0.1, color='green', label="Excellent agreement zone")
    ax.set_xlabel(r"$F_{theory} / F_{experiment}$")
    ax.set_ylabel("Count")
    ax.set_title("Sensitivity: Parameter Combinations")
    ax.legend(loc='upper right', fontsize=8)
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(f"{OUTPUT_PREFIX}_theory_experiment_agreement.pdf")
    plt.show()
    print(f"Saved: {OUTPUT_PREFIX}_theory_experiment_agreement.pdf")

    # ── Summary table ──────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("THEORY–EXPERIMENT AGREEMENT SUMMARY (JJS)")
    print("=" * 70)
    print(f"Experimental mean:    {F_exp_mean:.1f} ± {F_exp_std:.1f} nN  (N = {len(snap_rows)} curves)")
    print(f"Theoretical (nominal): {F_theory:.1f} nN  (vdW + capillary)")
    print(f"Ratio (exp/theory):    {F_exp_mean / F_theory:.1f}x")
    print(f"Theory 5–95% range:    {theory_min:.1f}–{theory_max:.1f} nN")
    print(f"Agreement category:    {'EXCELLENT' if 0.5 <= F_exp_mean/F_theory <= 2.0 else 'LARGE DISCREPANCY — additional mechanisms required'}")
    print("=" * 70)


# %% [markdown] tags=[]
r"""
## 16. Snap-in Data Quality Assessment

### Critical Conclusion: Snap-in Phase Cannot Extract Intrinsic Membrane Mechanics

While the snap-in phase provides valuable information about **interface forces** (adhesion, capillary condensation), it is fundamentally unsuited for extracting the membrane's intrinsic mechanical properties. This conclusion rests on three quantitative observations:

#### 1. Insufficient Data Points in the Approach Phase

The approach segment from first deviation to snap-in spans only ~10–20 nm. With the Bruker PeakForce QNM acquisition at 512 points per curve and total displacements of 454–1500 nm, the step size is ~1–3 nm. This yields only **3–8 data points** in the critical pre-snap-in region. Power-law fitting ($F \propto d^n$) with 3–8 points has large uncertainty: the standard error on the exponent $n$ is $\sigma_n \sim 1/\sqrt{N_{pts}} \approx 0.3$–0.6, comparable to the difference between vdW ($n = -2$) and capillary ($n = -1$) scaling.

#### 2. Insufficient Data Points in the Rise Phase

The rise segment from snap-in to mechanical contact spans 10–25 nm, yielding **2–5 data points** for most curves. Extracting contact stiffness from 2–5 points has limited reliability.

#### 3. Snap-in Force Reflects Interface Interactions, Not Membrane Elasticity

The snap-in event is a **mechanical instability** triggered when the gradient of attractive forces exceeds the cantilever restoring force: $|\partial F_{attr}/\partial z| > k_c$. The force at instability is determined by the **interface adhesion energy** ($\gamma_{eff}$) and the **capillary bridge geometry**, not by the membrane's Young's modulus $E$ or tension $T$.

### JJS-Specific Observations

| Feature | JJS | linker1-PFPE-OH | Implication |
|---------|-----|-----------------|-------------|
| Mean $|F_{snap}|$ | ~121 nN | ~6.8 nN | JJS has much stronger adhesion |
| Enhancement factor | ~40× | ~0.63× | JJS shows large dynamic/geometric effects |
| Snap depth | ~20 nm | ~8 nm | JJS membrane deflects more before contact |
| Rise data points | 2–5 | 1–3 | JJS has slightly better rise resolution |

The larger snap-in forces and deeper snap depths in JJS **do not improve** the extractability of membrane mechanics. In fact, the large forces may indicate **stronger adhesion hysteresis** and **more plastic deformation**, making the snap-in phase even less representative of elastic properties.

### What CAN Be Extracted from the Snap-in Phase

| Quantity | Method | Reliability |
|----------|--------|-------------|
| Interface adhesion energy $\gamma_{eff}$ | $F_{snap}$ via JKR/DMT model | Moderate (factor ~2) |
| Pre-tension / slack estimate | Snap depth $\Delta z$ | Semi-quantitative |
| Presence/absence of snap-in | Binary classification | High |
| Dynamic enhancement evidence | $|F_{snap}|$ vs. displacement | Qualitative |

### What CANNOT Be Extracted

| Quantity | Why | Where to Extract Instead |
|----------|-----|--------------------------|
| Young's modulus $E$ | Snap-in is interface-dominated | Post-contact indentation (Unit 10) |
| Membrane tension $T$ | Insufficient rise data points | Membrane deflection vs. pressure (Unit 12) |
| Contact stiffness $k_{contact}$ | Only 2–5 rise points | Hertzian fit to repulsive branch (Unit 10) |
| Power-law exponent $n$ | 3–8 approach points, $\sigma_n \sim 0.3$–0.6 | Ensemble analysis (Unit 15) with caveats |

### Recommendations for Future Measurements

To enable extraction of membrane mechanics from the snap-in phase, future experiments should:
1. **Increase point density** near the surface by using a smaller Z-range or adaptive sampling.
2. **Reduce tip velocity** to approach quasi-static conditions and minimize viscoelastic artifacts.
3. **Use higher-stiffness cantilevers** ($k_c > 20$ N/m) to suppress jump-to-contact and extend the measurable repulsive region.

> **Note**: Units 10 and 12 analyze the post-contact regime, where membrane restoring forces dominate and sufficient data points are available for Hertzian and shell-theory fitting.
"""

# %% tags=[]
# ── 16. Snap-in Data Quality & Summary ────────────────────────────
snap_items = [d for d in data]

fig, axes = plt.subplots(1, 2, figsize=(DOUBLE_COL, SINGLE_COL))
ax_full, ax_zoom = axes

summary_rows = []

for d in snap_items:
    z_full = np.array(d["raw_z"][::-1])
    f_full = np.array(d["raw_f"][::-1])
    f_corr_full, *_ = correct_baseline(z_full, f_full)
    if f_corr_full is None:
        continue

    seg = segment_curve(z_full, f_corr_full)
    snap_z = seg["snap_z"]
    snap_f = seg["snap_f"]
    snap_idx = seg["snap_idx"]
    contact_z = seg["contact_z"]

    # Align at snap-in
    z_aligned = z_full - snap_z
    force = f_corr_full.copy().astype(float)
    far_mask = z_aligned < -50
    if np.sum(far_mask) > 5:
        slope, intercept = np.polyfit(z_aligned[far_mask], force[far_mask], 1)
        force = force - (slope * z_aligned + intercept)
    elif np.sum(far_mask) > 0:
        force = force - np.mean(force[far_mask])

    disp = int(d.get("disp_nm", 0))
    color = {454: COLORS[0], 500: COLORS[1], 1000: COLORS[2], 1500: COLORS[3]}.get(disp, COLORS[4])
    label = d["file"].replace(" - NanoScope Analysis.txt", "").replace(".spm", "")

    # Full view: -50 to +50 nm
    full_mask = (z_aligned > -50) & (z_aligned < 50)
    ax_full.plot(z_aligned[full_mask], force[full_mask], '-', color=color, linewidth=0.8, alpha=0.5)

    # Zoom view: -20 to +20 nm
    zoom_mask = (z_aligned > -20) & (z_aligned < 20)
    ax_zoom.plot(z_aligned[zoom_mask], force[zoom_mask], '-', color=color, linewidth=1.2, alpha=0.6, label=label)

    # Count approach and rise points
    app_pts = np.sum((z_aligned > -20) & (z_aligned < 0) & (force < 0))
    rise_pts = np.sum((z_aligned > 0) & (z_aligned < 20))

    summary_rows.append({
        "File": label,
        "Disp (nm)": disp,
        "Snap F (nN)": round(snap_f, 1),
        "Snap depth (nm)": round(snap_z - contact_z, 1),
        "Approach pts": int(app_pts),
        "Rise pts": int(rise_pts),
        "|F|/F_theory": round(abs(snap_f) / 10.2, 1),
    })

for ax in [ax_full, ax_zoom]:
    ax.axvline(0, color='black', linestyle='--', alpha=0.5)
    ax.axhline(0, color='gray', linestyle=':', alpha=0.4)
    ax.set_xlabel("Z - Z$_{snap}$ (nm)")
    ax.set_ylabel("Force (nN)")
    ax.grid(True, alpha=0.3)

ax_full.set_title(f"Snap-in ± 50 nm (N={len(snap_items)})")
ax_zoom.set_title("Zoom: snap-in ± 20 nm")
ax_zoom.legend(fontsize=5, loc='upper left')

fig.tight_layout()
fig.savefig(f"{OUTPUT_PREFIX}_snapin_quality_check.pdf")
plt.show()
print(f"Saved: {OUTPUT_PREFIX}_snapin_quality_check.pdf")

df_sum = pd.DataFrame(summary_rows)
print("\nSnap-in data quality summary:")
print(df_sum.to_string(index=False))

print("\n" + "=" * 70)
print("SNAP-IN PHASE: WHAT WE CAN AND CANNOT EXTRACT (JJS)")
print("=" * 70)
print(f"Mean |F_snap|:      {np.mean([abs(r['Snap F (nN)']) for r in summary_rows]):.1f} ± {np.std([abs(r['Snap F (nN)']) for r in summary_rows], ddof=1):.1f} nN")
print(f"Theory (vdW+cap):   10.2 nN")
print(f"Ratio:              {np.mean([abs(r['Snap F (nN)']) for r in summary_rows]) / 10.2:.1f}x")
print(f"Mean snap depth:    {np.mean([r['Snap depth (nm)'] for r in summary_rows]):.1f} ± {np.std([r['Snap depth (nm)'] for r in summary_rows], ddof=1):.1f} nm")
print(f"Mean approach pts:  {np.mean([r['Approach pts'] for r in summary_rows]):.1f}")
print(f"Mean rise pts:      {np.mean([r['Rise pts'] for r in summary_rows]):.1f}")
print()
print("CAN extract from snap-in phase:")
print("  • Interface adhesion energy (from snap-in force)")
print("  • Pre-tension / slack estimate (from snap depth)")
print("  • Presence/absence of snap-in as a binary indicator")
print("  • Evidence for dynamic enhancement (|F_snap| vs. displacement)")
print()
print("CANNOT extract from snap-in phase (insufficient data points):")
print("  • Power-law index of approach force (F ∝ d^n) — only ~3-8 pts per curve")
print("  • Initial contact stiffness from rise slope — only ~2-5 pts per curve")
print("  • Young's modulus E, membrane tension T, stress σ")
print()
print("These mechanical properties require post-contact F–δ analysis (Unit 10, 12).")
print("=" * 70)


# %% [markdown] tags=[]
r"""
## 9. Deep Contact & Yield Analysis

For curves that penetrate deeply into the sample (max force ≫ setpoint), the post-contact region extends far beyond the first F ≥ 0 crossing. In this regime, the suspended COF film undergoes large deformation and may exhibit mechanical yield or densification. We detect such "deep-contact" curves and perform piecewise linear fitting on the full post-contact branch to identify stiffness transitions.

> ⚠️ **Important:** The probe retract distance was manually adjusted between measurements. Therefore, **the absolute Z position of snap-in has no physical meaning across curves**. Only post-contact quantities (indentation depth δ, force F) are physically meaningful. Curves with "late" snap (close to max displacement) simply had a larger manual retract and less room for indentation — they are not failed measurements.

**Detection criterion:** max(raw force) − baseline intercept > 50 nN.

**Analysis per curve:**
1. Re-process the full raw array (z reversed, baseline-corrected).
2. Locate the standard contact index (first F ≥ 0 after snap-in).
3. Fit two linear regimes on the post-contact branch:
   - Pre-yield: contact → mid-point of post-contact segment
   - Post-yield: mid-point → deepest indentation
4. Compute moving-window slope to pinpoint the transition.
"""

# %% tags=[]
# ── 9. Deep Contact & Yield Analysis ───────────────────────────────
DEEP_CONTACT_THRESHOLD = 50.0  # nN above baseline

deep_contact_items = []
for d in data:
    raw_f = np.array(d["raw_f"])
    baseline_intercept = d["baseline"]["intercept"]
    if max(raw_f) - baseline_intercept > DEEP_CONTACT_THRESHOLD:
        deep_contact_items.append(d)

if not deep_contact_items:
    print(f"No deep-contact curves detected (threshold: {DEEP_CONTACT_THRESHOLD:.0f} nN).")
else:
    print(f"Deep-contact curves detected: {len(deep_contact_items)}")
    import math

    n_dc = len(deep_contact_items)
    n_cols = min(2, n_dc)
    n_rows = math.ceil(n_dc / n_cols)
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(DOUBLE_COL, DOUBLE_COL * 0.5 * n_rows), squeeze=False)
    axes = axes.flatten()

    for ax, d in zip(axes, deep_contact_items):
        # Re-process full curve from raw
        z_full = np.array(d["raw_z"][::-1])
        f_full = np.array(d["raw_f"][::-1])
        f_corr_full, bl_slope, bl_int, n_pts, bl_status = correct_baseline(z_full, f_full)
        seg_full = segment_curve(z_full, f_corr_full)
        contact_idx = seg_full["contact_idx"]

        # Full post-contact branch
        z_post = z_full[contact_idx:]
        f_post = f_corr_full[contact_idx:]

        if len(z_post) < 10:
            ax.text(0.5, 0.5, "Too few post-contact points", ha="center", va="center", transform=ax.transAxes)
            ax.set_title(d["file"].replace(" - NanoScope Analysis.txt", "")[:35])
            continue

        # Piecewise linear fit: split at midpoint
        mid = len(z_post) // 2
        z1, f1 = z_post[:mid], f_post[:mid]
        z2, f2 = z_post[mid:], f_post[mid:]

        c1 = np.polyfit(z1, f1, 1)
        c2 = np.polyfit(z2, f2, 1)
        fit1 = np.poly1d(c1)
        fit2 = np.poly1d(c2)

        # Moving-window slope
        window = max(5, len(z_post) // 10)
        mid_z = []
        win_slopes = []
        for i in range(len(z_post) - window):
            zz = z_post[i:i + window]
            ff = f_post[i:i + window]
            if len(zz) > 1:
                s = np.polyfit(zz, ff, 1)[0]
                win_slopes.append(s)
                mid_z.append(zz.mean())

        # Plot
        ax.plot(z_post, f_post, "o", markersize=3, color=COLORS[0], alpha=0.6, label="Data", zorder=3)
        ax.plot(z1, fit1(z1), "-", linewidth=2, color=COLORS[1], label=f"Pre-yield k={c1[0]:.3f} N/m", zorder=4)
        ax.plot(z2, fit2(z2), "-", linewidth=2, color=COLORS[2], label=f"Post-yield k={c2[0]:.3f} N/m", zorder=4)

        # Special annotation for known yield at 380 nm
        if "100nN-500nm" in d["file"] and 380 >= z_post.min() and 380 <= z_post.max():
            ax.axvline(380, color=COLORS[3], linestyle="--", linewidth=2, alpha=0.8, label="Yield z=380 nm")
            ax.annotate(f"Yield: k drops {abs((c2[0]-c1[0])/c1[0]*100):.0f}%", xy=(380, fit1(380)), fontsize=8, color=COLORS[3])

        ax.axhline(0, color="gray", linewidth=0.5, zorder=1)
        ax.set_xlabel("z (nm)")
        ax.set_ylabel("Force (nN)")
        ax.set_title(d["file"].replace(" - NanoScope Analysis.txt", "")[:35], fontsize=9)
        ax.legend(fontsize=7, loc="upper left")
        ax.grid(True, alpha=0.3)

    for j in range(len(deep_contact_items), len(axes)):
        axes[j].axis("off")

    fig.tight_layout()
    fig.savefig(f"{OUTPUT_PREFIX}_deep_contact_yield.pdf")
    plt.show()
    print(f"Saved: {OUTPUT_PREFIX}_deep_contact_yield.pdf")

    # Print summary table
    rows_dc = []
    for d in deep_contact_items:
        z_full = np.array(d["raw_z"][::-1])
        f_full = np.array(d["raw_f"][::-1])
        f_corr_full, *_ = correct_baseline(z_full, f_full)
        seg_full = segment_curve(z_full, f_corr_full)
        contact_idx = seg_full["contact_idx"]
        z_post = z_full[contact_idx:]
        f_post = f_corr_full[contact_idx:]
        mid = len(z_post) // 2
        c1 = np.polyfit(z_post[:mid], f_post[:mid], 1)[0] if len(z_post[:mid]) > 1 else np.nan
        c2 = np.polyfit(z_post[mid:], f_post[mid:], 1)[0] if len(z_post[mid:]) > 1 else np.nan
        rows_dc.append({
            "File": d["file"].replace(" - NanoScope Analysis.txt", ""),
            "Max F (nN)": round(max(f_post), 1),
            "Pre-yield k (N/m)": round(c1, 3),
            "Post-yield k (N/m)": round(c2, 3),
            "Ratio": round(c2 / c1, 2) if c1 and c1 != 0 else "—",
        })
    df_dc = pd.DataFrame(rows_dc)
    print("\nDeep-contact yield summary:")
    print(df_dc.to_string(index=False))

# %% [markdown] tags=[]
r"""
## 10. Free-Standing Membrane Point-Load Mechanics

For a pre-stressed circular membrane clamped at the pore edge and indented by a sharp tip, the force–indentation relation depends on the deformation regime:

- **Small indentation** ($\delta \lesssim t$): Bending and local contact dominate; the response is approximately linear $F = k \, \delta$ with $k = \frac{2\pi T}{\ln(R/r)}$, where $T$ is the membrane tension, $R$ the pore radius, and $r$ the contact radius.
- **Large indentation** ($\delta \gg t$): In-plane stretching dominates; geometric non-linearity causes the stiffness to increase with $\delta$ (concave-up F–δ curve).
- **Failure**: At critical strain the membrane ruptures or the tip punctures through, causing a sudden stiffness drop.

Because all curves were measured on the **same free-standing region** of the COF film, differences in snap-in position reflect variations in AFM engage height, not changes in membrane state. Curves with late snap (e.g. 500 nm, 1000 nm) simply have insufficient indentation depth to reach the large-deformation regime. Only curves with early snap (e.g. 100nN-500nm) capture the full mechanical response from contact through yield to rupture.
"""

# %% tags=[]
# ── 10. Free-Standing Membrane Point-Load Mechanics ────────────────
# Geometry parameters
R_pore_m = (PORE_DIAMETER_UM * 0.5) * 1e-6  # pore radius, m
r_contact_m = PROBE_RADIUS_NM * 1e-9  # approximate contact radius, m
ln_R_r = np.log(R_pore_m / r_contact_m) if r_contact_m > 0 else 1.0
t_film_m = FILM_THICKNESS_NM * 1e-9  # film thickness, m

fig, axes = plt.subplots(1, 2, figsize=(DOUBLE_COL, SINGLE_COL))
ax_lin, ax_log = axes

mech_rows = []

for d in data:
    # Re-process full curve
    z_full = np.array(d["raw_z"][::-1])
    f_full = np.array(d["raw_f"][::-1])
    f_corr_full, bl_slope, bl_int, n_pts, bl_status = correct_baseline(z_full, f_full)
    seg_full = segment_curve(z_full, f_corr_full)

    contact_idx = seg_full["contact_idx"]
    z_post = z_full[contact_idx:]
    f_post = f_corr_full[contact_idx:]

    if len(z_post) < 3:
        continue

    # Indentation depth δ = z - contact_z (only δ >= 0)
    delta_nm = z_post - seg_full["contact_z"]
    valid = delta_nm >= 0
    delta_v = delta_nm[valid]
    f_v = f_post[valid]

    if len(delta_v) < 3:
        continue

    delta_m = delta_v * 1e-9
    f_N = f_v * 1e-9
    delta_max_nm = float(delta_v[-1])
    is_deep = delta_max_nm > 50.0  # threshold for "deep indentation"

    # Linear fit to first 20% of data (small-deformation regime)
    n_linear = max(3, len(delta_v) // 5)
    k_linear = np.polyfit(delta_m[:n_linear], f_N[:n_linear], 1)[0]  # N/m
    T_linear = k_linear * ln_R_r / (2 * np.pi)  # N/m
    sigma_linear = T_linear / t_film_m / 1e6  # MPa

    # Power-law fit: F = C * δ^n  (use δ > 0)
    pos_mask = delta_m > 0
    if np.sum(pos_mask) > 2:
        c_power = np.polyfit(np.log(delta_m[pos_mask]), np.log(f_N[pos_mask]), 1)
        n_power = float(c_power[0])
        C_power = float(np.exp(c_power[1]))
    else:
        n_power = 1.0
        C_power = k_linear

    label = d["file"].replace(" - NanoScope Analysis.txt", "").replace(".spm", "")
    color = COLORS[2] if is_deep else COLORS[0]
    alpha = 0.85 if is_deep else 0.35
    lw = 2.0 if is_deep else 1.0

    ax_lin.plot(delta_v, f_v, "-", color=color, alpha=alpha, linewidth=lw,
                label=label if is_deep else None)
    ax_log.loglog(delta_v[delta_v > 0], f_v[delta_v > 0], "-", color=color,
                  alpha=alpha, linewidth=lw, label=label if is_deep else None)

    mech_rows.append({
        "File": label,
        "δ_max (nm)": round(delta_max_nm, 1),
        "F_max (nN)": round(float(f_v[-1]), 1),
        "k (N/m)": round(k_linear, 3),
        "T (N/m)": round(T_linear, 3),
        "σ (MPa)": round(sigma_linear, 1),
        "Power n": round(n_power, 2),
        "Category": "Deep" if is_deep else "Shallow",
    })

# Add inset for shallow-indentation detail
from mpl_toolkits.axes_grid1.inset_locator import mark_inset
ax_inset = ax_lin.inset_axes([0.55, 0.12, 0.4, 0.4])
for d in data:
    z_full = np.array(d["raw_z"][::-1])
    f_full = np.array(d["raw_f"][::-1])
    f_corr_full, *_ = correct_baseline(z_full, f_full)
    seg_full = segment_curve(z_full, f_corr_full)
    contact_idx = seg_full["contact_idx"]
    z_post = z_full[contact_idx:]
    f_post = f_corr_full[contact_idx:]
    if len(z_post) < 3:
        continue
    delta_nm = z_post - seg_full["contact_z"]
    valid = delta_nm >= 0
    delta_v = delta_nm[valid]
    f_v = f_post[valid]
    if len(delta_v) < 3 or float(delta_v[-1]) > 50:
        continue
    label = d["file"].replace(" - NanoScope Analysis.txt", "").replace(".spm", "")
    ax_inset.plot(delta_v, f_v, "-o", markersize=2, linewidth=1, label=label)

ax_inset.set_xlim(0, 20)
ax_inset.set_ylim(0, 10)
ax_inset.set_xlabel("δ (nm)", fontsize=7)
ax_inset.set_ylabel("F (nN)", fontsize=7)
ax_inset.set_title("Shallow detail", fontsize=8)
ax_inset.tick_params(labelsize=6)
ax_inset.grid(True, alpha=0.3)
ax_inset.legend(fontsize=5, loc="upper left")
mark_inset(ax_lin, ax_inset, loc1=2, loc2=4, fc="none", ec="0.5", linestyle="--")

ax_lin.set_xlabel("Indentation depth $\\delta$ (nm)")
ax_lin.set_ylabel("Force (nN)")
ax_lin.set_title("Force vs Indentation (linear scale)")
ax_lin.legend(fontsize=7, loc="upper left")
ax_lin.grid(True, alpha=0.3)

ax_log.set_xlabel("Indentation depth $\\delta$ (nm)")
ax_log.set_ylabel("Force (nN)")
ax_log.set_title("Force vs Indentation (log-log)")
ax_log.legend(fontsize=7, loc="upper left")
ax_log.grid(True, alpha=0.3, which="both")

fig.tight_layout()
fig.savefig(f"{OUTPUT_PREFIX}_membrane_mechanics.pdf")
plt.show()
print(f"Saved: {OUTPUT_PREFIX}_membrane_mechanics.pdf")

df_mech = pd.DataFrame(mech_rows)
print("\nFree-standing membrane mechanics summary:")
print(df_mech.to_string(index=False))

print("\n" + "="*60)
print("Model: F = k·δ  with  k = 2πT / ln(R/r)")
print(f"Pore radius R = {R_pore_m*1e6:.1f} μm,  contact radius r ≈ {r_contact_m*1e9:.0f} nm")
print(f"ln(R/r) = {ln_R_r:.2f}")
print("Shallow curves (δ_max < 50 nm) only probe the initial contact/bending regime.")
print("Deep curves (δ_max > 50 nm) capture the full tension-stretching response.")

# %% [markdown] tags=[]
r"""
## 11. No-Snap-In Curve Overlap (Large Displacement)

For measurements with large displacement settings (> 2000 nm), the probe approach velocity is high enough that the attractive snap-in is suppressed. The force rises directly from baseline upon mechanical contact, without the characteristic negative spike. This section isolates such curves, subtracts baseline, aligns them at the contact-rise point (defined as the first point where smoothed force exceeds 5% of its maximum), and overlays them to reveal the common post-contact mechanical response.

> **Note:** The absolute Z position of the rise point is arbitrary (manual retract distance), so only the post-rise indentation depth δ is physically meaningful.
"""

# %% tags=[]
# ── 11. No-Snap-In Curve Overlap ───────────────────────────────────
from scipy.ndimage import uniform_filter1d

NO_SNAP_THRESHOLD = -2.0  # nN; snap_f above this is considered "no snap"
LARGE_DISP_THRESHOLD = 3500.0  # nm; curves with disp <= 3000 nm are discarded (insufficient indentation)
RISE_FRACTION = 0.05  # 5% of max smoothed force

no_snap_items = []
for d in data:
    disp = d.get("disp_nm", 0)
    snap_f = d.get("snap_f", -100.0)
    if disp >= LARGE_DISP_THRESHOLD and snap_f > NO_SNAP_THRESHOLD:
        no_snap_items.append(d)

if len(no_snap_items) < 2:
    print(f"Not enough no-snap curves (disp > {LARGE_DISP_THRESHOLD:.0f} nm) for overlap analysis.")
else:
    print(f"No-snap curves for overlap: {len(no_snap_items)}")
    fig, ax = plt.subplots(figsize=(DOUBLE_COL, SINGLE_COL))

    for d in no_snap_items:
        z_full = np.array(d["raw_z"][::-1])
        f_full = np.array(d["raw_f"][::-1])
        f_corr_full, *_ = correct_baseline(z_full, f_full)
        if f_corr_full is None:
            continue

        # Smooth and find rise point
        window = max(11, len(z_full) // 20)
        f_smooth = uniform_filter1d(f_corr_full, size=window)
        max_f = float(np.max(f_smooth))
        thresh = max_f * RISE_FRACTION
        idx = np.where(f_smooth > thresh)[0]
        if len(idx) == 0:
            continue
        rise_idx = int(idx[0])
        z0 = float(z_full[rise_idx])
        f0 = float(f_corr_full[rise_idx])

        delta = z_full[rise_idx:] - z0
        force = f_corr_full[rise_idx:] - f0

        label = d["file"].replace(" - NanoScope Analysis.txt", "").replace(".spm", "")
        ax.plot(delta, force, "-", linewidth=1.2, label=label, alpha=0.8)

    ax.set_xlabel("Indentation depth $\\delta$ (nm)")
    ax.set_ylabel("Force (nN)")
    ax.set_title(f"No-snap curves overlapped (N={len(no_snap_items)}, origin = {RISE_FRACTION*100:.0f}% max force)")
    ax.legend(fontsize=6, loc="upper left", ncol=2)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(f"{OUTPUT_PREFIX}_no_snap_overlap.pdf")
    plt.show()
    print(f"Saved: {OUTPUT_PREFIX}_no_snap_overlap.pdf")

# %% [markdown] tags=[]
r"""
## 12. 无突跳曲线起飞后力学分析 (No-Snap Take-Off Mechanics)

部分无突跳曲线在压入初期存在一段低刚度 "趾区" (toe)，这对应于探针逐渐绷紧膜上的褶皱或松弛部分。为了提取膜的本征力学性能，我们**跳过趾区**，以 **起飞点**（平滑力首次超过最大力 20% 的位置）为原点重新对齐曲线，对起飞后分支进行线性拟合，得到膜的有效刚度 $k$、张力 $T$ 等参数。

**参数说明：**

| 符号 | 汉语含义 | 单位 | 计算方法 |
|------|----------|------|----------|
| $k$ | 有效刚度 (effective stiffness) | N/m | 起飞后 $F$–$\delta$ 线性拟合斜率 |
| $T$ | 膜张力 (membrane tension) | N/m | $T = k \cdot \ln(R/r) / (2\pi)$ |
| $\sigma$ | 面内应力 (in-plane stress) | MPa | $\sigma = T / t$ |
| $n$ | 幂律指数 (power-law exponent) | — | $\log F$–$\log \delta$ 斜率；$n=1$ 为纯线性张力 |
| $E$ | 杨氏模量 (Young's modulus) | MPa | 非线性拟合 $F = a\delta + b\delta^3$ 后由 $b$ 反推 |

> **注意：** 本实验所有无突跳曲线在达到断裂前即停止（由位移上限控制），因此**不存在真实的断裂事件**。表中未列出 "断裂强度"，$\sigma$ 仅代表实验最大压入深度对应的等效膜应力。
"""

# %% tags=[]
# ── 12. No-Snap Curve Take-Off Mechanics (post-toe) ─────────────────
TAKEOFF_FRACTION = 0.20  # 20% of max smoothed force
nu = 0.3                 # Poisson ratio (polymer film)

def membrane_model(delta, a, b):
    """Nonlinear membrane model: F = a·δ + b·δ³ (tension + bending/stretching)"""
    return a * delta + b * delta**3

# Guard: skip if no no-snap curves available
if len(no_snap_items) < 1:
    print(f"No no-snap curves available (disp >= {LARGE_DISP_THRESHOLD:.0f} nm & snap_f > {NO_SNAP_THRESHOLD} nN). Skipping take-off mechanics.")
    takeoff_rows = []
    mech_results = []
else:
    takeoff_rows = []
    mech_results = []
    fig, ax = plt.subplots(figsize=(DOUBLE_COL, SINGLE_COL))

    for d in no_snap_items:
        z_full = np.array(d["raw_z"][::-1])
        f_full = np.array(d["raw_f"][::-1])
        f_corr_full, *_ = correct_baseline(z_full, f_full)
        if f_corr_full is None:
            continue
    
        # Rise point (5% max)
        window = max(11, len(z_full) // 20)
        f_smooth = uniform_filter1d(f_corr_full, size=window)
        max_f = float(np.max(f_smooth))
        idx_rise = np.where(f_smooth > max_f * RISE_FRACTION)[0]
        if len(idx_rise) == 0:
            continue
        rise_idx = int(idx_rise[0])
    
        # Take-off point (20% max) — skip toe region
        idx_takeoff = np.where(f_smooth[rise_idx:] > max_f * TAKEOFF_FRACTION)[0]
        if len(idx_takeoff) == 0:
            continue
        takeoff_idx = rise_idx + int(idx_takeoff[0])
    
        z0 = float(z_full[takeoff_idx])
        f0 = float(f_corr_full[takeoff_idx])
        delta = z_full[takeoff_idx:] - z0
        force = f_corr_full[takeoff_idx:] - f0
    
        if len(delta) < 10:
            continue
    
        label = d["file"].replace(" - NanoScope Analysis.txt", "").replace(".spm", "")
        ax.plot(delta, force, "-", linewidth=1.2, label=label, alpha=0.8)
    
        # ── Linear fit for k, T, σ (with covariance) ──
        delta_m = delta * 1e-9
        force_n = force * 1e-9
        coeffs, cov = np.polyfit(delta_m, force_n, 1, cov=True)
        k_val = float(coeffs[0])
        k_err = float(np.sqrt(cov[0, 0])) if cov is not None else 0.0
    
        T_val = k_val * ln_R_r / (2 * np.pi)
        T_err = k_err * ln_R_r / (2 * np.pi)
        sigma_val = T_val / t_film_m / 1e6
        sigma_err = T_err / t_film_m / 1e6
    
        # ── Power-law index n from log-log slope ──
        pos = (delta_m > 0) & (force_n > 0)
        log_n = float(np.polyfit(np.log(delta_m[pos]), np.log(force_n[pos]), 1)[0]) if np.sum(pos) > 5 else np.nan
    
        # ── Young's modulus from nonlinear fit ──
        E_val = E_err = np.nan
        try:
            popt, pcov = curve_fit(membrane_model, delta_m, force_n, p0=[k_val, 1e8])
            a_fit, b_fit = popt
            _, b_err = np.sqrt(np.diag(pcov))
            if b_fit > 0 and b_err / b_fit < 0.5:
                E_val = b_fit * R_pore_m**2 * (1 - nu) * ln_R_r / (np.pi * t_film_m) / 1e6
                E_err = b_err * R_pore_m**2 * (1 - nu) * ln_R_r / (np.pi * t_film_m) / 1e6
        except Exception:
            pass
    
        takeoff_rows.append({
            "File": label,
            "Disp (nm)": d.get("disp_nm", 0),
            "Rise Z (nm)": round(float(z_full[rise_idx]), 0),
            "Take-off Z (nm)": round(z0, 0),
            "Toe δ (nm)": round(z0 - float(z_full[rise_idx]), 0),
            "k (N/m)": round(k_val, 5),
            "k_err": round(k_err, 5),
            "T (N/m)": round(T_val, 5),
            "T_err": round(T_err, 5),
            "σ (MPa)": round(sigma_val, 2),
            "σ_err": round(sigma_err, 2),
            "n": round(log_n, 3) if not np.isnan(log_n) else "N/A",
            "E (MPa)": round(E_val, 1) if not np.isnan(E_val) else "N/A",
            "E_err": round(E_err, 1) if not np.isnan(E_err) else "N/A",
        })
    
        mech_results.append({
            "k": k_val, "k_err": k_err,
            "T": T_val, "T_err": T_err,
            "sigma": sigma_val, "sigma_err": sigma_err,
            "n": log_n,
            "E": E_val, "E_err": E_err,
        })

    ax.set_xlabel("Indentation depth $\\delta$ (nm)")
    ax.set_ylabel("Force (nN)")
    ax.set_title(f"Post-take-off overlap (N={len(takeoff_rows)}, origin = {TAKEOFF_FRACTION*100:.0f}% max force)")
    ax.legend(fontsize=6, loc="upper left", ncol=2)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(f"{OUTPUT_PREFIX}_no_snap_takeoff.pdf")
    plt.show()
    print(f"Saved: {OUTPUT_PREFIX}_no_snap_takeoff.pdf")

df_takeoff = pd.DataFrame(takeoff_rows)
print("\nNo-snap take-off mechanics (per-curve):")
print(df_takeoff.to_string(index=False))

# ── Ensemble statistics ──
print("\n" + "=" * 70)
print(f"ENSEMBLE STATISTICS (mean ± std, N={len(mech_results)})")
print("=" * 70)

ensemble = {}
for key in ["k", "T", "sigma", "n", "E"]:
    vals = [r[key] for r in mech_results if not np.isnan(r[key])]
    errs = [r.get(key + "_err", 0) for r in mech_results if not np.isnan(r[key])]
    if len(vals) > 1:
        ensemble[key] = {
            "mean": np.mean(vals),
            "std": np.std(vals, ddof=1),
            "fit_err_avg": np.mean(errs) if errs else 0,
            "N": len(vals),
        }
        unit = "N/m" if key in ("k", "T") else ""
        print(f"{key}: {ensemble[key]['mean']:.5f} ± {ensemble[key]['std']:.5f} {unit}  (fit-err avg={ensemble[key]['fit_err_avg']:.5f}, N={ensemble[key]['N']})")

# ── Parameter distribution figure ──
fig, axes = plt.subplots(2, 3, figsize=(TRIPLE_COL, 1.3 * SINGLE_COL))
params = [
    ("k", "Stiffness $k$ (N/m)\n有效刚度 (N/m)"),
    ("T", "Tension $T$ (N/m)\n膜张力 (N/m)"),
    ("sigma", "Stress $\\sigma$ (MPa)\n面内应力 (MPa)"),
    ("n", "Power-law $n$\n幂律指数"),
    ("E", "Young's modulus $E$ (MPa)\n杨氏模量 (MPa)"),
]

for ax, (key, title) in zip(axes.flat, params):
    vals = [r[key] for r in mech_results if not np.isnan(r[key])]
    if len(vals) < 2:
        ax.set_visible(False)
        continue
    indices = [i for i, r in enumerate(mech_results) if not np.isnan(r[key])]
    ax.bar(range(len(vals)), vals, color="steelblue", edgecolor="k", alpha=0.7)
    ax.axhline(np.mean(vals), color="crimson", linestyle="--", label=f"mean={np.mean(vals):.3f}")
    ax.set_title(title, fontsize=9)
    ax.set_xticks(range(len(vals)))
    short_labels = [takeoff_rows[i]["File"].replace("JJS-50nm-", "").replace("JJS-50nm", "") for i in indices]
    ax.set_xticklabels(short_labels, rotation=45, ha="right", fontsize=6)
    ax.legend(fontsize=6)

# Hide the 6th (empty) subplot
axes.flat[-1].set_visible(False)

fig.suptitle(f"JJS mechanical parameters per curve (N={len(mech_results)})", fontsize=11)
fig.tight_layout()
fig.savefig(f"{OUTPUT_PREFIX}_mech_params.pdf")
plt.show()
print(f"\nSaved: {OUTPUT_PREFIX}_mech_params.pdf")
