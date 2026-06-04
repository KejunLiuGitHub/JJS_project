# JJS AFM Force-Distance Analysis — Complete Handoff

> **For:** macOS continuation  
> **From:** Windows development session  
> **Date:** 2026-04-22  
> **Status:** Raw-data pipeline design approved; implementation blocked on Windows PowerShell string-escaping issues. Ready to execute on macOS.

---

## 1. Scientific Background

### 1.1 Sample
- **JJS**: 10 nm thick 2D COF (covalent organic framework) film
- **Suspended over**: 20 μm diameter SiN (silicon nitride) pore
- **Substrate**: SiN membrane with etched pores

### 1.2 Instrument & Conditions
- **AFM**: Bruker, PeakForce QNM mode
- **Probe**: RTESPA-150
  - Nominal radius R = 8 nm
  - Stiffness k_c ≈ 5 N/m
- **Environment**: Air ambient, RH > 60%
- **Acquisition**: 512 points per force-distance curve
- **PeakForce frequency**: ~2 kHz
- **Estimated tip velocity**: 0.1–1 m/s

### 1.3 The Central Anomaly
Measured snap-in forces range from **99 to 151 nN** (mean ~120.7 nN), while classical theory predicts:
- Non-retarded vdW (DMT): ~3.7 nN
- Capillary force (complete wetting): ~7.2 nN
- Casimir-Polder (retarded vdW): ~0.5 nN
- Total classic: ~10.9 nN

**The measured forces are 1–2 orders of magnitude larger than theory.** This notebook investigates why.

### 1.4 Possible Mechanisms Under Investigation
1. **Dynamic effects**: High tip velocity (0.1–1 m/s) may cause viscoelastic/impact enhancement
2. **Capillary neck formation**: High humidity (>60%) allows water meniscus to form before contact
3. **Film indentation geometry**: The suspended COF film may deform, creating a larger effective contact area
4. **Electrostatic forces**: Contact potential difference (CPD) between tip and sample
5. **Surface contamination / adsorbates**: Unknown surface layers may alter Hamaker constant

---

## 2. Data Format & Structure

### 2.1 File Format (Bruker NanoScope Analysis Export)
Each `.txt` file contains:
```
Line 1: Chinese header (experiment description)
Line 2: Chinese header (parameter description)
Line 3+: Z_position(nm)   Force(nN)
```

**Critical:** Files are **NOT utf-8**. They use `latin-1` (or `gb2312` / `cp936`) encoding due to Chinese characters. Opening with `utf-8` will raise `UnicodeDecodeError`.

### 2.2 Data Characteristics
- **Points**: Exactly 512 per file (standard PeakForce acquisition)
- **Z direction**: Decreases monotonically from set displacement toward ~0
  - Example: 1000 nm → 0 nm in 512 steps
  - Step size: ~1.953 nm (varies slightly with set displacement)
- **Force baseline**: Raw force has a positive offset (~12–16 nN) due to optical lever calibration drift
- **Snap-in location**: Always in the first ~30 points (Z ≈ 940–1000 nm region)

> ⚠️ **CRITICAL CAVEAT — Manual Retract Distance (2026-04-23 discovery)**
> 
> The student manually adjusts the probe **retract distance** between measurements. This means:
> - **The absolute Z position of snap-in has NO physical meaning** across different curves.
> - Differences in snap Z (e.g., 221 nm vs 461 nm) do NOT indicate membrane movement, drift, or damage.
> - **Only relative quantities are physically meaningful:**
>   - `contact_z - snap_z` (distance from snap-in to mechanical contact)
>   - Indentation depth `δ = z - contact_z` (post-contact deformation)
>   - Force values (independent of Z zero)
> - Curves with "late" snap (close to max displacement) simply had a larger manual retract, leaving less room for indentation. They are NOT failed measurements.
> 
> **Analysis implication:** Always analyze post-contact behavior (F vs δ), never compare absolute snap Z positions across curves.

> 🗑️ **DISCARDED DATA — linker1-PFPE-OH low-displacement curves (2026-04-23)**
>
> The following PFPE-OH curves are **permanently discarded** from all analysis:
> - `linker1-PFPE-OH-1900nm.spm` (×2 files)
> - `linker1-PFPE-OH-2000nm.spm`
> - `linker1-PFPE-OH-2200nm.spm`
> - `linker1-PFPE-OH-2400nm.spm`
> - `linker1-PFPE-OH-2600nm.spm`
> - `linker1-PFPE-OH-2800nm.spm`
> - `linker1-PFPE-OH-3000nm.spm`
>
> **Reason:** Displacement ≤ 3000 nm is insufficient to reach the high-stiffness tension-dominated regime. These curves show inconsistent, low-k mechanical response (toe-only behavior) and cannot be used for intrinsic membrane property extraction. Only curves with displacement ≥ 3500 nm are retained for PFPE-OH mechanical analysis.

### 2.3 File Naming Convention
```
JJS-50nm-{DISPLACEMENT}nm-{SETPOINT}nN - NanoScope Analysis.txt
```
Examples:
- `JJS-50nm-1000nm-10nN` — 1000 nm displacement, 10 nN setpoint
- `JJS-50nm-454nm-8.862nN` — 454 nm displacement, 8.862 nN setpoint

### 2.4 Current Dataset (11 curves)
| Displacement | Setpoints | Count |
|-------------|-----------|-------|
| 454 nm | 8.862 nN | 1 |
| 500 nm | 8.862, 10 nN | 2 |
| 1000 nm | 8, 8.862, 10, 50 nN | 4 |
| 1500 nm | 8, 9, 10 nN | 4 |

**Note:** All curves show clear snap-in (negative force spike). No positive-only curves in this dataset.

---

## 3. Data Cleaning Pipeline (Scientific Rationale)

### 3.1 Why Cleaning is Necessary
The raw instrument output contains three artifacts that must be removed before analysis:

1. **Direction reversal**: Bruker exports Z as decreasing. For physical interpretation, Z should increase (probe approaches from far to near).
2. **Baseline offset**: Thermal drift and optical-lever calibration cause a non-zero far-field force (~12–16 nN). This must be subtracted so that F = 0 when probe and sample are well separated.
3. **Segmentation**: The curve must be split into:
   - **Approach (drop)**: From start to snap-in — reveals attractive forces
   - **Retraction (rise)**: From snap-in to contact — reveals recovery behavior and energy dissipation

### 3.2 Baseline Correction Method
**Region**: Z ∈ [0, 100] nm (far field, well before snap-in)
**Model**: Linear baseline F_bl(Z) = a·Z + b
**Fit**: `np.polyfit(z[mask_far], f[mask_far], 1)`
**Subtraction**: F_corr = F_raw - F_bl(Z)

**Rationale**: The far-field region contains only background (thermal drift, lever offset). There is no tip-sample interaction at Z > 100 nm for a 10 nm film on a 20 μm pore. A linear fit captures slow drift; a simple mean would miss tilted baselines.

### 3.3 Snap-in Detection
**Algorithm**: `snap_idx = np.argmin(f_corr)`
**Physical meaning**: Point of maximum attractive force during approach.

**Validation check**: If `snap_f >= 0`, the curve has no attractive regime and should be **rejected**.

### 3.4 Contact Detection
**Algorithm**: First post-snap-in point where `f_corr >= 0`
**Physical meaning**: Tip has reached mechanical contact with the sample; repulsive forces begin.

**Edge case**: If no `F >= 0` point exists after snap-in, use the last point of the array (curve may not have reached full contact within the acquisition window).

### 3.5 Start Index (Drop Region Boundary)
**Algorithm**: Last pre-snap-in point where `f_corr > -2.0 nN`
**Rationale**: The drop region should start from the last point before the attractive force becomes significant. -2 nN is chosen as a threshold above noise but below the snap-in magnitude (typically -100 nN).

**Edge case**: If no `F > -2` point exists before snap-in, use `max(0, snap_idx - 5)` as fallback.

### 3.6 Rejection Criteria
A curve should be rejected (`clean_and_validate` returns `None`) if:
1. No negative snap-in detected (`snap_f >= 0`)
2. Drop segment has fewer than 3 points
3. Rise segment has fewer than 2 points

**Current dataset**: All 11 curves pass these criteria. Future datasets (20260415, 20260416) may have rejects.

---

## 4. Theoretical Models

### 4.1 Non-Retarded van der Waals (DMT)
For a sphere of radius R at distance d from a plane:
```
F_vdW = A·R / (12·d₀²)
```
- A = 4×10⁻¹⁹ J (Hamaker constant, typical for polymer/SiN)
- d₀ = 0.3 nm (cutoff distance)
- R = 8 nm

**Prediction**: ~3.7 nN

### 4.2 Capillary Force (Complete Wetting)
```
F_cap = 4π·R·γ
```
- γ = 72 mN/m (water surface tension at 25°C)

**Prediction**: ~7.2 nN

### 4.3 Casimir-Polder (Retarded vdW)
At large separations (d ≫ λ₀):
```
F_CP = (π³·ℏ·c·R / (360·d₀³)) · η
```
- η ≈ 0.4 (reduction factor for polymer/SiN)

**Prediction**: ~0.5 nN

### 4.4 Electrostatic Force
```
F_elec = π·ε₀·R·V_CPD² / d₀
```
- V_CPD: contact potential difference (typically 0.1–0.5 V)

**Typical prediction**: 0.3–7.5 nN (depends strongly on V_CPD)

### 4.5 Total Classic Prediction
```
F_total_classic = F_vdW + F_cap ≈ 10.9 nN
```

**vs. measured mean of 120.7 nN: discrepancy factor ~11×**

---

## 5. Key Implementation Details

### 5.1 Encoding
```python
# CORRECT
with open(filepath, 'r', encoding='latin-1') as f:
    lines = f.readlines()

# WRONG — will crash
with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()
```

### 5.2 Z Direction Handling
```python
# Raw: Z decreases (e.g., 1000 → 0)
z_raw = np.array([...])  # decreasing

# Corrected: Z increases (0 → 1000)
z = z_raw[::-1].copy()
f = f_raw[::-1].copy()
```

**Common mistake**: Forgetting to reverse BOTH Z and F arrays.

### 5.3 Baseline Region
After reversal, the far field is at the **beginning** of the array (Z ≈ 0–100 nm), NOT the end.

```python
mask_far = (z >= 0) & (z <= 100)  # First ~51 points
```

### 5.4 Force Sign Convention
- **Negative force** = attractive (tip pulled toward sample)
- **Positive force** = repulsive (tip pushed away)
- Snap-in force is the **most negative** value: `snap_f = min(f_corr)`
- Reported as magnitude: `|snap_f| = -snap_f` (since snap_f < 0)

### 5.5 Figure Specifications
```python
SINGLE_COL = 8.6 / 2.54   # ≈ 3.39 inch (single-column journal)
DOUBLE_COL = 17.8 / 2.54  # ≈ 7.01 inch (double-column)

COLORS = ['#0C5DA5', '#E8204E', '#00B945', '#FF9500', '#845B97', '#474747']
# Nature/Science style palette
```

Matplotlib rcParams:
- Font: Times New Roman, 10 pt
- DPI: 300 (both figure and savefig)
- Math font: STIX
- Ticks: inward, on all four sides
- Output format: PDF (vector)

---

## 6. Notebook Architecture

### Current Structure (8 units, reads JSON)
```
Cell 1: Metadata markdown
Cell 2: Global config + JSON load
Unit 1: Experimental Parameters
Unit 2: Theory vs Experiment
Unit 3: Snap-in Force Statistics
Unit 4: Snap-in vs Displacement
Unit 5: Drop/Rise Asymmetry
Unit 6: Energy Dissipation
Unit 7: Representative Curves
Unit 8: Summary
```

### Target Structure (11 units, reads raw txt)
```
Cell 1: Metadata markdown
Cell 2: Global config + raw data load
Unit A: Raw Data Overview          ← NEW
Unit B: Baseline Correction        ← NEW
Unit C: Data Cleaning & Validation ← NEW
Unit 1: Experimental Parameters
Unit 2: Theory vs Experiment
Unit 3: Snap-in Force Statistics
Unit 4: Snap-in vs Displacement
Unit 5: Drop/Rise Asymmetry
Unit 6: Energy Dissipation
Unit 7: Representative Curves
Unit 8: Summary
```

### Key Refactor for Downstream Units
Replace JSON key access:
```python
# OLD (JSON)
d["snap_f_nN"], d["contact_z_nm"], d["drop_z"]

# NEW (clean_and_validate output)
d["snap_f"], d["contact_z"], d["drop_z"]
```

The JSON used keys like `snap_f_nN`, `contact_z_nm` with units in the name. The `clean_and_validate` dict uses shorter keys (`snap_f`, `contact_z`) since the units are documented and consistent (nN, nm).

---

## 7. Files to Create on macOS

### New Files
| File | Purpose | Size (est.) |
|------|---------|-------------|
| `scripts/cleaning.py` | Shared cleaning module | ~150 lines |
| `scripts/qc_filter.py` | QC decision loader (reads qc_decisions.json) | ~30 lines |
| `scripts/notebook_cells/cell_a_raw_overview.py` | Raw data inspection cell | ~80 lines |
| `scripts/notebook_cells/cell_b_baseline_correction.py` | Baseline demo cell | ~100 lines |
| `scripts/notebook_cells/cell_c_data_cleaning.py` | Cleaning & validation cell | ~120 lines |
| `scripts/assemble_notebook.py` | Notebook assembly script | ~50 lines |

### Modified Files
| File | Changes |
|------|---------|
| `reports/JJS_analysis.py` | Remove JSON load, insert 3 new units, refactor 8 existing units, add DISCARDED_FILES parameter |
| `scripts/run_analysis.py` | Auto-load qc_decisions.json, pass discard list to notebook |
| `scripts/cleaning.py` | Add optional `discard_set` parameter to `load_all_cleaned()` |

### Deprecated (moved to `archive/`)
| File | Status |
|------|--------|
| `results/jjs_transition_deep_analysis.json` | No longer read by notebook |
| `scripts/test_*.py`, `scripts/debug_*.py`, `scripts/check_*.py` | Archived debug/one-off scripts |
| `reports/linker1_*.py`, `reports/k80_*.py` (old versions) | Archived duplicate analysis scripts |

---

## 8. Open Questions / Future Work

1. **20260415 dataset (linker1-PFPE-OH)**: 56 files, different linker chemistry. Does the snap-in anomaly persist?
2. **20260416 dataset (k80-linker1-PFNA)**: 49 files, fluorinated linker. How does fluorination affect adhesion?
3. **Velocity dependence**: JJS data has 4 displacement settings (454, 500, 1000, 1500 nm). Is the observed displacement dependence actually a velocity effect (v = f·amplitude)?
4. **Film mechanics**: The 10 nm COF film may indent under load. Should the analysis include membrane bending/tension models?
5. **Humidity control**: Current data at RH > 60%. Would snap-in forces decrease in dry N₂?
6. **Tip wear**: RTESPA-150 tips may blunt during measurement. Is the effective R larger than 8 nm?

---

## 9. Quick Start (macOS)

```bash
# 1. Unzip
cd ~/Projects
unzip JJS_project.zip -d JJS_AFM

# 2. Setup environment
cd JJS_AFM
python3 -m venv .venv
source .venv/bin/activate
pip install numpy matplotlib scipy pandas jupytext

# 3. Verify data
ls 20260409/ | wc -l   # Should print 11

# 4. Launch Kimi Code CLI
kimi

# 5. Tell Kimi: "已在 macOS，继续执行计划"
```

---

## 10. Troubleshooting

### Issue: `UnicodeDecodeError` when reading txt files
**Solution**: Always use `encoding='latin-1'` or `encoding='gb2312'`. Never `utf-8`.

### Issue: Baseline correction produces NaN
**Cause**: Far-field region has fewer than 3 points (very short displacement).  
**Solution**: Fall back to mean offset instead of linear fit.

### Issue: Snap-in not detected
**Cause**: Curve is positive-only (no attractive regime).  
**Solution**: Reject curve via `clean_and_validate` returning `None`.

### Issue: Figures look different on macOS
**Cause**: macOS may not have Times New Roman.  
**Solution**: Matplotlib falls back to DejaVu Serif (already in rcParams). Install Times New Roman if exact font matching is required.

---

## 11. Kimi CLI + VS Code Workflow

### Real-time File Sync
When Kimi CLI modifies `.py` files on disk, VS Code may not auto-refresh. Two solutions:

**A. Auto-save + Revert keybinding (recommended)**
- `.vscode/settings.json` is already configured with `files.autoSave: afterDelay` (500 ms)
- Press `Ctrl+Alt+R` (or `Cmd+Shift+P` → `File: Revert File`) to instantly reload from disk
- This is faster than closing/reopening the tab

**B. One-key refresh without keybinding**
- `Cmd+Shift+P` → type `File: Revert File` → Enter
- The file reloads from disk immediately

### Why This Happens
VS Code locks the file tab when it detects unsaved edits (dirty state). Kimi CLI writes to disk, but VS Code refuses to overwrite your unsaved changes. Auto-save prevents dirty state; `Revert File` forces reload.

### Recommended Layout
```
┌─────────────────┬─────────────────┐
│                 │  Interactive    │
│   .py Editor    │    Window       │
│   (left 50%)    │  (right 40%)    │
│                 │                 │
├─────────────────┴─────────────────┤
│        Terminal (Kimi CLI)        │
│             (bottom 25%)          │
└───────────────────────────────────┘
```

- **Editor**: Read-only reference; refresh with `Ctrl+Alt+R` after Kimi edits
- **Interactive Window**: Execute cells, inspect variables
- **Terminal**: Run Kimi CLI commands

### Workflow
1. Edit/request in terminal → Kimi writes to disk
2. Editor auto-saves or press `Ctrl+Alt+R` to see changes
3. Jump to cell in editor → `Shift+Enter` → runs in Interactive Window
4. Iterate
