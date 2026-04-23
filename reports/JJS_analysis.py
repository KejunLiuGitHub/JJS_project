# %% [markdown]
r"""
# AFM Force-Distance Analysis: JJS Suspended COF Film

**Authors:** Li Shuang (Experimenter), Prof. Kejun Liu (Analyst)
**Date:** April 2026
**Sample:** JJS — 10 nm 2D COF film suspended over 20 μm SiN pore
**Instrument:** Bruker AFM, PeakForce QNM mode, RTESPA-150 probe
**Environment:** Air ambient, RH > 60 %

## Study Overview

This notebook analyzes 11 force-distance curves acquired on a suspended ultrathin COF membrane. The central question is: **why are the measured snap-in forces (99–151 nN) one to two orders of magnitude larger than classical theory predictions (~10 nN)?** We examine van der Waals, capillary, Casimir-Polder, and electrostatic contributions, compare them against experiment, and assess the role of dynamic effects and film indentation geometry.

> **Notebook architecture:** Only Cell 2 is global configuration; every subsequent pair of cells (Markdown → Code) is a self-contained, copy-pasteable analysis unit.
"""

# %%
import json
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from pathlib import Path

# ── Load data (auto-detect project root) ───────────────────────────
cwd = Path.cwd()
if (cwd / "results" / "jjs_transition_deep_analysis.json").exists():
    ROOT = cwd
elif (cwd.parent / "results" / "jjs_transition_deep_analysis.json").exists():
    ROOT = cwd.parent
else:
    raise FileNotFoundError("Cannot find results/jjs_transition_deep_analysis.json")
JSON_PATH = ROOT / "results" / "jjs_transition_deep_analysis.json"
with open(JSON_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

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

# %% [markdown]
r"""
## 1. Experimental Parameters

The JJS sample is a 10 nm thick 2D COF film suspended over a 20 μm diameter SiN pore. Measurements were performed in ambient air (RH > 60 %) using a Bruker AFM in PeakForce QNM mode. The probe is RTESPA-150 with nominal radius $R = 8$ nm and stiffness $k_c \approx 5$ N/m.

Key parameters used throughout this notebook are listed below. No theoretical formulas are introduced here; they appear in the subsequent analysis units.
"""

# %%
import pandas as pd

params = [
    ("Probe radius $R$", "8", "nm"),
    ("Cantilever stiffness $k_c$", "5.0", "N/m"),
    (r"Water surface tension $\gamma$", "72", "mN/m"),
    ("Hamaker constant $A$", r"$4\times10^{-19}$", "J"),
    ("Cutoff distance $d_0$", "0.3", "nm"),
    ("Film thickness $t$", "10", "nm"),
    ("Pore diameter", "20", r"$\mu$m"),
    ("Relative humidity", ">60", "%"),
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
fig.savefig("jjs_experimental_parameters.pdf")
plt.show()
print("Saved: jjs_experimental_parameters.pdf")

# %% [markdown]
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

# %%
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
F_measured_all = [abs(d["snap_f_nN"]) for d in data]
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
ax.set_ylim(1e-2, 300)
ax.grid(True, alpha=0.3, linestyle="--", linewidth=0.5, zorder=0)
ax.tick_params(axis="x", rotation=15)

fig.savefig("jjs_theory_vs_experiment_bar.pdf")
plt.show()
print("Saved: jjs_theory_vs_experiment_bar.pdf")

# %% [markdown]
r"""
## 3. Snap-in Force Statistics (All 11 Curves)

The snap-in force $F_{snap}$ is the maximum attractive (negative) force recorded during probe approach. For each of the 11 valid curves, we extract $F_{snap}$, the snap depth $\Delta z = z_{contact} - z_{snap}$, the maximum drop slope (approach), and the maximum rise slope (retraction).

The mean snap-in force across all curves is $\bar{F}_{snap} = 120.7$ nN, with a range of 99.0–150.6 nN. No anomalous positive-only curves were observed, confirming the reliability of the snap-in data for mechanism analysis.
"""

# %%
rows = []
for d in data:
    rows.append({
        "File": d["file"].replace(" - NanoScope Analysis.txt", ""),
        "Disp (nm)": d["disp_nm"],
        "Setpoint": d["setpoint"],
        "Snap (nN)": round(d["snap_f_nN"], 1),
        "Depth (nm)": round(d["contact_z_nm"] - d["snap_z_nm"], 1),
        "Drop (N/m)": round(d["max_drop_slope"], 1),
        "Rise (N/m)": round(d["max_rise_slope"], 1),
    })

df_snap = pd.DataFrame(rows)
print(df_snap.to_string(index=False))

# ── Bar chart: snap-in force magnitude by file ─────────────────────
fig, ax = plt.subplots(figsize=(DOUBLE_COL, DOUBLE_COL * 0.35))

files_short = [r["File"].replace("JJS-50nm-", "").replace("- NanoScope Analysis.txt", "") for r in rows]
snap_vals = [abs(r["Snap (nN)"]) for r in rows]
disp_colors = [
    COLORS[0] if r["Disp (nm)"] == 454 else
    COLORS[1] if r["Disp (nm)"] == 500 else
    COLORS[2] if r["Disp (nm)"] == 1000 else
    COLORS[3] for r in rows
]

bars = ax.bar(range(len(files_short)), snap_vals, color=disp_colors, edgecolor="black", linewidth=0.3, zorder=3)
ax.set_xticks(range(len(files_short)))
ax.set_xticklabels(files_short, rotation=45, ha="right", fontsize=7)
ax.set_ylabel(r"$|F_{snap}|$ (nN)")
ax.set_title("Snap-in Force Magnitude (All 11 Curves)")
ax.axhline(np.mean(snap_vals), color="black", linestyle="--", linewidth=0.8, label=f"Mean = {np.mean(snap_vals):.1f} nN")
ax.grid(True, alpha=0.3, linestyle="--", linewidth=0.5, axis="y", zorder=0)

from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor=COLORS[0], edgecolor="black", label="454 nm"),
    Patch(facecolor=COLORS[1], edgecolor="black", label="500 nm"),
    Patch(facecolor=COLORS[2], edgecolor="black", label="1000 nm"),
    Patch(facecolor=COLORS[3], edgecolor="black", label="1500 nm"),
]
ax.legend(handles=legend_elements, loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0)

fig.savefig("jjs_snapin_force_statistics.pdf")
plt.show()
print("Saved: jjs_snapin_force_statistics.pdf")

# %% [markdown]
r"""
## 4. Snap-in Force vs. Piezo Displacement

PeakForce QNM operates at ~2 kHz with estimated tip velocity $v \sim 0.1$–1 m/s. Smaller piezo displacement corresponds to higher approach speed because the probe must traverse the same oscillation amplitude in less time. We therefore expect a velocity-dependent enhancement of the snap-in force.

The data are grouped by displacement (454, 500, 1000, 1500 nm). Within each group, we compute mean, minimum, and maximum $|F_{snap}|$. A linear fit is applied to the group means to quantify the displacement dependence.

> **Note:** Equations (1)–(4) from Unit 2 define the classic forces; no new formulas are introduced here.
"""

# %%
from collections import defaultdict

disp_groups = defaultdict(list)
for d in data:
    disp_groups[d["disp_nm"]].append(abs(d["snap_f_nN"]))

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
ax.set_title("Snap-in Force vs. Displacement")
ax.grid(True, alpha=0.3, linestyle="--", linewidth=0.5, zorder=0)
ax.legend(loc="upper right", fontsize=8)

fig.savefig("jjs_snapin_vs_displacement.pdf")
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

# %% [markdown]
r"""
## 5. Drop vs. Rise Slope Asymmetry

The drop slope characterizes the approach (snap-in) dynamics, while the rise slope characterizes the retraction (recovery). For a quasi-static process, these should be symmetric. The asymmetry ratio

$$\mathcal{A} = \frac{|k_{rise}|}{|k_{drop}|} \tag{5}$$

quantifies this deviation. Observed values $\mathcal{A} = 0.06$–0.31 indicate strong mechanical instability (jump-to-contact) rather than a reversible, equilibrium approach.

> **Note:** The force expressions (1)–(4) appear in Unit 2; Equation (5) is introduced here for the first time.
"""

# %%
files_short = [d["file"].replace("JJS-50nm-", "").replace(" - NanoScope Analysis.txt", "") for d in data]
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

fig.savefig("jjs_drop_rise_asymmetry.pdf")
plt.show()
print("Saved: jjs_drop_rise_asymmetry.pdf")

print(f"\nDrop slopes: {min(drop_slopes):.1f} – {max(drop_slopes):.1f} N/m")
print(f"Rise slopes: {min(rise_slopes):.1f} – {max(rise_slopes):.1f} N/m")
print(f"Asymmetry ratio: {min(asym_ratios):.2f} – {max(asym_ratios):.2f}")

# %% [markdown]
r"""
## 6. Energy Dissipated in the Transition Zone

The energy dissipated during snap-in is computed as the area under the force-distance curve in the transition region (approach branch from zero force to contact). This represents viscoelastic losses in the adsorbed water film plus any plastic deformation of the suspended membrane.

No new formulas are required here; the energy is obtained by numerical integration of the experimental $F(z)$ data.
"""

# %%
energies = [d["energy_dissipated_nN_nm"] for d in data]
disps = [d["disp_nm"] for d in data]

fig, ax = plt.subplots(figsize=(SINGLE_COL, SINGLE_COL * 0.75))

disp_color_map = {454.0: COLORS[0], 500.0: COLORS[1], 1000.0: COLORS[2], 1500.0: COLORS[3]}

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

fig.savefig("jjs_energy_dissipation.pdf")
plt.show()
print("Saved: jjs_energy_dissipation.pdf")
print(f"\nDissipated energy range: {min(energies):.1f} – {max(energies):.1f} nN·nm")

# %% [markdown]
r"""
## 7. Representative Force-Distance Curves

To illustrate the two-stage framework, we plot the force vs. piezo displacement for representative curves. The approach (drop) and retraction (rise) branches are shown separately.

**Stage 1 (Snap-in, $F < 0$):** The approach branch shows a sudden jump-to-contact, with drop slopes 20–114 N/m. This is the surface interaction domain dominated by attractive forces.

**Stage 2 (Contact, $F \geq 0$):** The retraction branch shows elastic recovery with rise slopes ~6–7 N/m, close to the cantilever stiffness $k_c \approx 5$ N/m. No plateau is observed (plateau fraction = 0.00), indicating the capillary bridge ruptures instantly upon retraction.

> **Note:** The force laws (1)–(4) are defined in Unit 2; the asymmetry metric (5) is defined in Unit 5.
"""

# %%
# Select 3 representative curves: one from each displacement group
rep_indices = [0, 7, 4]  # 1000nm-10nN, 454nm-8.862nN, 1500nm-10nN
labels_rep = ["1000 nm / 10 nN", "454 nm / 8.862 nN", "1500 nm / 10 nN"]
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
    if idx == 2:
        ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0, fontsize=8)

fig.tight_layout()
fig.savefig("jjs_representative_force_curves.pdf")
plt.show()
print("Saved: jjs_representative_force_curves.pdf")

# %% [markdown]
r"""
## 8. Summary of Key Findings

1. **Snap-in is reliable and reproducible:** All 11 JJS curves show systematic negative force ($-99$ to $-151$ nN).

2. **Classic theory cannot explain the magnitude:** vdW + capillary predict $\sim$10 nN; measured is 10–15$\times$ larger.

3. **Dynamic effects matter:** Smaller displacement (higher speed) $\rightarrow$ stronger snap-in, consistent with viscoelastic enhancement.

4. **Film suspension is key:** Copper mesh suppresses snap-in by 20–300$\times$, proving geometry and substrate screening dominate.

5. **Repulsive data are insufficient:** PeakForce setpoint too low (8–50 nN) to extract membrane stiffness or prestress.

> **Note:** All force expressions (1)–(4) are defined in Unit 2; the asymmetry ratio (5) is defined in Unit 5.
"""

# %%
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
        f"{np.mean([abs(d['snap_f_nN']) for d in data]):.1f} nN",
        f"{min([abs(d['snap_f_nN']) for d in data]):.1f}–{max([abs(d['snap_f_nN']) for d in data]):.1f} nN",
        f"{data[0]['vdW_check']['F_vdw_nonret_nN']:.2f} nN",
        f"{data[0]['vdW_check']['F_capillary_theory_nN']:.2f} nN",
        f"{data[0]['vdW_check']['F_vdw_plus_cap_nN']:.2f} nN",
        f"{np.mean([abs(d['snap_f_nN']) for d in data]) / data[0]['vdW_check']['F_vdw_plus_cap_nN']:.1f}×",
        f"{np.mean([d['asymmetry_ratio'] for d in data]):.3f}",
        f"{np.mean([d['recovery']['plateau_fraction'] for d in data]):.2f}",
        f"{np.mean([d['energy_dissipated_nN_nm'] for d in data]):.1f} nN·nm",
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

fig.savefig("jjs_summary_statistics.pdf")
plt.show()
print("Saved: jjs_summary_statistics.pdf")
