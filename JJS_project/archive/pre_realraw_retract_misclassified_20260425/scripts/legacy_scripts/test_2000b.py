# -*- coding: utf-8 -*-
"""
Build JJS_analysis.py with raw data pipeline.
This script reads the existing notebook and inserts new cells for raw data ingestion and cleaning.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).parent.parent
src_path = ROOT / "reports" / "JJS_analysis.py"

# Read existing notebook
with open(src_path, "r", encoding="utf-8") as f:
    content = f.read()

# Find insertion point
marker = 'print("Global configuration loaded. Data:", len(data), "curves.")'
insert_pos = content.find(marker)
if insert_pos == -1:
    print("ERROR: Marker not found")
    sys.exit(1)
insert_pos += len(marker)

# New cell: raw data helper functions
new_cells = '''

# %% [markdown]
r"""
## Raw Data Ingestion

The raw data are Bruker NanoScope Analysis `.txt` files exported from PeakForce QNM mode.
Each file contains 512 data points with 2 Chinese header lines.
"""

# %%
def read_raw_forcecurve(filepath):
    """Read a Bruker NanoScope txt file (latin-1 encoded)."""
    with open(filepath, "r", encoding="latin-1") as f:
        lines = f.readlines()
    header = lines[0].strip()
    data_lines = lines[2:]  # skip 2 Chinese header lines
    z_vals, f_vals = [], []
    for line in data_lines:
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) >= 2:
            z_vals.append(float(parts[0]))
            f_vals.append(float(parts[1]))
    return np.array(z_vals), np.array(f_vals)

def clean_forcecurve(z_raw, f_raw):
    """Reverse Z, apply far-field baseline correction, detect snap-in."""
    z = z_raw[::-1].copy()
    f = f_raw[::-1].copy()
    # Baseline correction using far-field [0, 100] nm
    mask_far = (z >= 0) & (z <= 100)
    a, b = np.polyfit(z[mask_far], f[mask_far], 1)
    f_corr = f - (a * z + b)
    snap_idx = int(np.argmin(f_corr))
    # Start index: last point before snap-in with F > -2 nN
    start_idx = snap_idx
    while start_idx > 0 and f_corr[start_idx] > -2.0:
        start_idx -= 1
    while start_idx < snap_idx and f_corr[start_idx] <= -2.0:
        start_idx += 1
    if start_idx >= snap_idx:
        start_idx = max(0, snap_idx - 5)
    # Contact index: first point after snap-in with F >= 0
    contact_idx = snap_idx
    while contact_idx < len(f_corr) - 1 and f_corr[contact_idx] < 0:
        contact_idx += 1
    # Segments
    drop_z = z[start_idx:snap_idx+1]
    drop_f = f_corr[start_idx:snap_idx+1]
    rise_z = z[snap_idx:contact_idx+1]
    rise_f = f_corr[snap_idx:contact_idx+1]
    return {
        "z": z, "f_corr": f_corr,
        "snap_idx": snap_idx, "start_idx": start_idx, "contact_idx": contact_idx,
        "snap_f": float(f_corr[snap_idx]), "snap_z": float(z[snap_idx]),
        "contact_z": float(z[contact_idx]),
        "n_before": len(drop_z), "n_after": len(rise_z),
        "drop_z": drop_z.tolist(), "drop_f": drop_f.tolist(),
        "rise_z": rise_z.tolist(), "rise_f": rise_f.tolist(),
        "max_drop_slope": float(np.min(np.diff(drop_f))) if len(drop_f) > 1 else None,
        "avg_drop_slope": float((drop_f[-1] - drop_f[0]) / (drop_z[-1] - drop_z[0])) if len(drop_z) > 1 else None,
        "max_rise_slope": float(np.max(np.diff(rise_f))) if len(rise_f) > 1 else None,
        "avg_rise_slope": float((rise_f[-1] - rise_f[0]) / (rise_z[-1] - rise_z[0])) if len(rise_z) > 1 else None,
        "asymmetry_ratio": None,
        "drop_area": None,
        "energy_dissipated": None,
        "recovery": None,
        "vdW_check": None,
    }
'''

print("Script ready")
