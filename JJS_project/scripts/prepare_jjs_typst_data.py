# -*- coding: utf-8 -*-
"""
Prepare clean CSV data for Typst beamer report.
Reads jjs_transition_deep_analysis.json and exports minimal CSV files.
"""
import json, csv
from pathlib import Path
import numpy as np

ROOT = Path(__file__).parent.parent
JSON_PATH = ROOT / "results" / "jjs_transition_deep_analysis.json"
OUT_DIR = ROOT / "results" / "jjs_report_data"
OUT_DIR.mkdir(exist_ok=True)

with open(JSON_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

# ── 1. Main summary table ─────────────────────────────────────────
rows = []
for d in data:
    rows.append({
        "file": d["file"].replace(" - NanoScope Analysis.txt", ""),
        "disp_nm": round(d["disp_nm"], 1),
        "setpoint": d["setpoint"],
        "snap_f_nN": round(d["snap_f_nN"], 1),
        "snap_depth_nm": round(d["contact_z_nm"] - d["snap_z_nm"], 1),
        "max_drop_slope": round(d["max_drop_slope"], 1),
        "max_rise_slope": round(d["max_rise_slope"], 1),
        "asymmetry_ratio": round(d["asymmetry_ratio"], 3),
        "energy_nN_nm": round(d["energy_dissipated_nN_nm"], 1),
        "F_measured_nN": round(d["vdW_check"]["F_measured_nN"], 1),
        "F_vdw_nN": round(d["vdW_check"]["F_vdw_nonret_nN"], 2),
        "F_cap_nN": round(d["vdW_check"]["F_capillary_theory_nN"], 2),
        "A_mult": round(d["vdW_check"]["A_required_vs_typical"], 1),
    })

with open(OUT_DIR / "summary.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

# ── 2. Displacement-dependence series ─────────────────────────────
disp_groups = {}
for d in data:
    disp = d["disp_nm"]
    if disp not in disp_groups:
        disp_groups[disp] = []
    disp_groups[disp].append(abs(d["snap_f_nN"]))

disp_rows = []
for disp in sorted(disp_groups):
    vals = disp_groups[disp]
    disp_rows.append({
        "disp_nm": disp,
        "mean_snap_nN": round(np.mean(vals), 1),
        "min_snap_nN": round(np.min(vals), 1),
        "max_snap_nN": round(np.max(vals), 1),
        "n": len(vals),
    })

with open(OUT_DIR / "displacement.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=disp_rows[0].keys())
    writer.writeheader()
    writer.writerows(disp_rows)

# ── 3. Theory comparison (single representative row) ──────────────
theory_row = {
    "F_vdw_nN": round(data[0]["vdW_check"]["F_vdw_nonret_nN"], 2),
    "F_cap_nN": round(data[0]["vdW_check"]["F_capillary_theory_nN"], 2),
    "F_sum_nN": round(data[0]["vdW_check"]["F_vdw_plus_cap_nN"], 2),
    "F_measured_min": round(min(abs(d["snap_f_nN"]) for d in data), 1),
    "F_measured_max": round(max(abs(d["snap_f_nN"]) for d in data), 1),
    "F_measured_mean": round(np.mean([abs(d["snap_f_nN"]) for d in data]), 1),
    "ratio_min": round(min(abs(d["snap_f_nN"]) / d["vdW_check"]["F_vdw_plus_cap_nN"] for d in data), 1),
    "ratio_max": round(max(abs(d["snap_f_nN"]) / d["vdW_check"]["F_vdw_plus_cap_nN"] for d in data), 1),
}

with open(OUT_DIR / "theory.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=theory_row.keys())
    writer.writeheader()
    writer.writerow(theory_row)

# ── 4. Asymmetry data (for plotting) ──────────────────────────────
asym_rows = []
for d in data:
    asym_rows.append({
        "file": d["file"].replace(" - NanoScope Analysis.txt", ""),
        "drop_slope": round(abs(d["max_drop_slope"]), 1),
        "rise_slope": round(d["max_rise_slope"], 1),
        "ratio": round(d["asymmetry_ratio"], 3),
        "disp_nm": d["disp_nm"],
    })

with open(OUT_DIR / "asymmetry.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=asym_rows[0].keys())
    writer.writeheader()
    writer.writerows(asym_rows)

# ── 5. Energy dissipation ─────────────────────────────────────────
energy_rows = []
for d in data:
    energy_rows.append({
        "file": d["file"].replace(" - NanoScope Analysis.txt", ""),
        "disp_nm": d["disp_nm"],
        "energy_nN_nm": round(d["energy_dissipated_nN_nm"], 1),
    })

with open(OUT_DIR / "energy.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=energy_rows[0].keys())
    writer.writeheader()
    writer.writerows(energy_rows)

# ── 6. Physical constants ─────────────────────────────────────────
const_rows = [
    {"parameter": "Probe radius R", "value": "8", "unit": "nm"},
    {"parameter": "Cantilever stiffness k_c", "value": "5.0", "unit": "N/m"},
    {"parameter": "Water surface tension γ", "value": "72", "unit": "mN/m"},
    {"parameter": "Hamaker constant A", "value": "4×10⁻¹⁹", "unit": "J"},
    {"parameter": "Cutoff distance d₀", "value": "0.3", "unit": "nm"},
    {"parameter": "Film thickness t", "value": "10", "unit": "nm"},
    {"parameter": "Pore diameter", "value": "20", "unit": "μm"},
    {"parameter": "Relative humidity", "value": ">60", "unit": "%"},
    {"parameter": "PeakForce frequency", "value": "~2", "unit": "kHz"},
    {"parameter": "Tip velocity (est.)", "value": "~0.1–1", "unit": "m/s"},
]

with open(OUT_DIR / "constants.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=const_rows[0].keys())
    writer.writeheader()
    writer.writerows(const_rows)

print(f"Saved {len(rows)} rows to {OUT_DIR}/summary.csv")
print(f"Saved {len(disp_rows)} rows to {OUT_DIR}/displacement.csv")
print(f"Saved theory comparison to {OUT_DIR}/theory.csv")
print(f"Saved {len(asym_rows)} rows to {OUT_DIR}/asymmetry.csv")
print(f"Saved {len(energy_rows)} rows to {OUT_DIR}/energy.csv")
print(f"Saved {len(const_rows)} constants to {OUT_DIR}/constants.csv")
