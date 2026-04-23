# %% [markdown]
r"""
## Raw Data Ingestion

The raw data are Bruker NanoScope Analysis `.txt` files exported from PeakForce QNM mode. Each file contains:
- **512 data points** (standard PeakForce acquisition)
- **2 Chinese header lines** describing experiment parameters
- **2 numeric columns**: piezo position $Z$ (nm) and cantilever deflection force $F$ (nN)

In the raw export, $Z$ decreases monotonically from the set displacement toward 0 as the probe approaches the sample. The snap-in event appears as a sharp negative spike in the first ~30 points.

Below we read one representative file directly to inspect the uncorrected instrument output.
"""

# %%
# -- Read and plot one representative RAW curve --------------------
RAW_DIR = ROOT / "20260409"
rep_file = sorted(RAW_DIR.glob("JJS*.txt"))[0]

# Read raw txt (latin-1 encoding for Chinese headers)
with open(rep_file, "r", encoding="latin-1") as f:
    raw_lines = f.readlines()
header = raw_lines[0].strip()
z_vals, f_vals = [], []
for line in raw_lines[2:]:
    line = line.strip()
    if not line:
        continue
    parts = line.split()
    if len(parts) >= 2:
        z_vals.append(float(parts[0]))
        f_vals.append(float(parts[1]))
z_raw = np.array(z_vals)
f_raw = np.array(f_vals)

fig, ax = plt.subplots(figsize=(SINGLE_COL, SINGLE_COL * 0.75))
ax.plot(z_raw, f_raw, "o-", markersize=2, linewidth=0.5, color=COLORS[0], label="Raw instrument output")
ax.set_xlabel("Piezo $Z$ (nm)")
ax.set_ylabel("Force (nN)")
ax.set_title(f"Raw Force-Distance Curve\\n{rep_file.name[:35]}")
ax.grid(True, alpha=0.3, linestyle="--", linewidth=0.5, zorder=0)
ax.legend(loc="upper right")
fig.savefig("jjs_raw_forcecurve_representative.pdf")
plt.show()
print("Saved: jjs_raw_forcecurve_representative.pdf")
print(f"Raw points: {len(z_raw)}, Z range: {z_raw.min():.1f} to {z_raw.max():.1f} nm")
print(f"Force range: {f_raw.min():.1f} to {f_raw.max():.1f} nN")
