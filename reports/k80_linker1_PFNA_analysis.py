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
CANTILEVER_STIFFNESS_N_M = 5.0
FILE_PATTERN = "*.txt"
OUTPUT_PREFIX = "jjs"
ENVIRONMENT = "Air ambient, RH > 60 %"

# %% tags=["injected-parameters"]
# Parameters
DATASET_DIR = "20260416\u539f\u59cb\u6570\u636e"
SAMPLE_NAME = "k80-linker1-PFNA"
FILM_THICKNESS_NM = 50
PORE_DIAMETER_UM = 20
PROBE_RADIUS_NM = 8.0
CANTILEVER_STIFFNESS_N_M = 5.0
FILE_PATTERN = "k80-linker1-PFNA-*.txt"
OUTPUT_PREFIX = "k80_linker1_PFNA"
ENVIRONMENT = "Air ambient"


# %% tags=[]
# ── Load raw data ──────────────────────────────────────────────────
RAW_DIR = ROOT / DATASET_DIR
raw_files = sorted(RAW_DIR.glob(FILE_PATTERN))
if not raw_files:
    raise FileNotFoundError(f"No files matching '{FILE_PATTERN}' in {RAW_DIR}")
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

# ── A4 academic figure sizes ───────────────────────────────────────
# Single column: 8.6 cm; double column: 17.8 cm (1 inch = 2.54 cm)
SINGLE_COL = 8.6 / 2.54   # ≈ 3.39 inch
DOUBLE_COL = 17.8 / 2.54  # ≈ 7.01 inch

# ── Publication-grade font settings ────────────────────────────────
plt.rcParams.update({
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif"],
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
demo_indices = [0, 6]
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

Some curves exhibit **both Stage 1 (pre-contact attraction / snap-in) and Stage 2 (post-contact membrane repulsion)**. Stage 2 is dominated by the membrane's own restoring force pushing back against the tip. We flag curves with a clearly positive repulsive contact force ($F_{contact} > 5$ nN) as **two-stage curves** and highlight them for in-depth analysis.
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

Key parameters used throughout this notebook are listed below. No theoretical formulas are introduced here; they appear in the subsequent analysis units.
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

For a sphere of radius $R$ at distance $d$ from a plane, the non-retarded van der Waals force in the DMT framework is

$$F_{vdW} = \frac{AR}{12d_0^2} \tag{1}$$

where $A$ is the Hamaker constant and $d_0$ is the cutoff distance. For capillary force under complete wetting ($\theta = 0$),

$$F_{cap} = 4\pi R \gamma \tag{2}$$

where $\gamma$ is the water surface tension. At large separations ($d \gg \lambda_0$), the Casimir-Polder (retarded vdW) force is

$$F_{CP} = \frac{\pi^3 \hbar c R}{360 d_0^3} \cdot \eta \tag{3}$$

with $\eta \approx 0.4$ for polymer/SiN interfaces. The electrostatic force from contact potential difference $V_{CPD}$ is

$$F_{elec} = \frac{\pi \varepsilon_0 R V_{CPD}^2}{d_0} \tag{4}$$

The table and bar chart below compare these theoretical predictions with the experimentally measured snap-in forces.
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

The energy dissipated during snap-in is computed as the area under the force-distance curve in the transition region (approach branch from zero force to contact). This represents viscoelastic losses in the adsorbed water film plus any plastic deformation of the suspended membrane.

No new formulas are required here; the energy is obtained by numerical integration of the experimental $F(z)$ data.
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

1. **Snap-in statistics:** See table below for mean, range, and theoretical comparison.
2. **Classic theory discrepancy:** vdW + capillary predictions are typically 1–2 orders of magnitude below measured snap-in forces.
3. **Dynamic effects:** Displacement-dependent trends (if present) suggest velocity-enhanced snap-in.
4. **Two-stage curves:** Curves with clear Stage 2 (positive contact force) reveal membrane restoring forces and are highlighted above.
5. **Next steps:** Higher setpoint or larger displacement may be needed to probe deeper into Stage 2 for stiffness extraction.

> **Note:** All force expressions (1)–(4) are defined in Unit 2; the asymmetry ratio (5) is defined in Unit 5.
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
print("Saved: jjs_summary_statistics.pdf")
