# AFM Force-Distance Analysis Workflow

> **For:** Kimi Code CLI agents and human collaborators  
> **Purpose:** Parameterized, reproducible analysis pipeline for any Bruker NanoScope AFM dataset.

---

## 1. Architecture Overview

```
scripts/
├── cleaning.py            # Shared: parse → baseline → segment → validate
├── dataset_registry.py    # Central config for all datasets
└── run_analysis.py        # CLI entry point

reports/
├── JJS_analysis.py        # Parameterized notebook template (Jupytext Percent)
├── jjs_analysis.ipynb     # Generated for dataset 20260409
├── jjs_analysis.py        # Synced .py for Git
├── k80_analysis.ipynb     # Generated for dataset 20260416
└── k80_analysis.py        # Synced .py for Git
```

**Design principle:** One template (`JJS_analysis.py`) + one registry (`dataset_registry.py`) = any dataset.

---

## 2. Quick Start

### 2.1 List available datasets

```bash
python scripts/run_analysis.py --list
```

### 2.2 Run analysis on a dataset

```bash
# Default output prefix (from registry)
python scripts/run_analysis.py --dataset 20260409

# Custom output prefix
python scripts/run_analysis.py --dataset 20260416原始数据 --output-prefix k80

# Dry run (print parameters, do not execute)
python scripts/run_analysis.py --dataset 20260415原始数据 --dry-run
```

**Output:**
- `reports/{prefix}_analysis.ipynb` — executed notebook with outputs
- `reports/{prefix}_analysis.py` — synced Percent-Format source for Git

---

## 3. Adding a New Dataset

### Step 1: Place raw `.txt` files

Create a new directory at project root, e.g.:

```
20260420原始数据/
├── sample-A-1000nm-10nN - NanoScope Analysis.txt
├── sample-A-2000nm-10nN - NanoScope Analysis.txt
└── ...
```

### Step 2: Register in `scripts/dataset_registry.py`

```python
"20260420原始数据": {
    "sample_name": "sampleA",
    "description": "New sample on substrate X, Probe Y",
    "film_thickness_nm": 10,
    "pore_diameter_um": 20,
    "probe_radius_nm": 8.0,
    "cantilever_stiffness_N_m": 5.0,
    "pattern": "sample-A*.txt",   # glob pattern to match files
    "force_unit": "nN",           # "nN", "uN", or "pN"
    "z_unit": "nm",               # "nm" or "um"
    "environment": "Air ambient",
    "output_prefix": "sampleA",
    "has_snap_in": True,          # optional hint for agents
},
```

### Step 3: Run

```bash
python scripts/run_analysis.py --dataset 20260420原始数据
```

**No notebook code changes required.**

---

## 4. Parameterized Notebook (`reports/JJS_analysis.py`)

### 4.1 Papermill Parameters Cell

Cell 3 (tagged `parameters`) defines all tunable variables:

| Parameter | Default | Meaning |
|-----------|---------|---------|
| `DATASET_DIR` | `"20260409"` | Raw data directory |
| `SAMPLE_NAME` | `"JJS"` | Sample identifier |
| `FILM_THICKNESS_NM` | `10` | Film thickness |
| `PORE_DIAMETER_UM` | `20` | Pore diameter |
| `PROBE_RADIUS_NM` | `8.0` | AFM tip radius |
| `CANTILEVER_STIFFNESS_N_M` | `5.0` | k_c |
| `FILE_PATTERN` | `"*.txt"` | File glob pattern |
| `OUTPUT_PREFIX` | `"jjs"` | Output filename prefix |
| `ENVIRONMENT` | `"Air ambient, RH > 60 %"` | Measurement conditions |

These are **injected at runtime** by `run_analysis.py` via Papermill.

### 4.2 Notebook Structure

| Cell | Content | Self-contained? |
|------|---------|-----------------|
| 1 | Metadata markdown | — |
| 2 | Global imports + root detection | — |
| 3 | **Papermill parameters** (injected) | — |
| 4 | Raw data loading + cleaning | ✅ |
| A | Raw Data Overview (all curves) | ✅ |
| B | Baseline Correction (all curves) | ✅ |
| C | Data Cleaning & Validation (all curves) | ✅ |
| 1–8 | Physical analysis units | ✅ |

> **Rule:** Every analysis unit (Markdown → Code pair) is copy-pasteable and does not depend on code from other units, only on the global `data` list loaded in Cell 4.

---

## 5. Cleaning Module (`scripts/cleaning.py`)

### 5.1 Public API

```python
load_raw(filepath) → dict          # Parse single Bruker txt
correct_baseline(z, f) → tuple     # Far-field linear fit
segment_curve(z, f_corr) → dict    # Snap-in / contact / drop / rise
clean_and_validate(filepath) → dict|None  # Full pipeline
load_all_cleaned(data_dir) → list  # Batch load
```

### 5.2 Auto-detection Features

- **Encoding:** Tries `utf-8` first, falls back to `latin-1`
- **Units:** Detects `nm/um` and `nN/uN/pN` from column header line
- **Direction:** Automatically reverses Bruker's decreasing Z

### 5.3 Baseline Correction Strategy

| Far-field points | Method |
|------------------|--------|
| ≥ 5 | Linear fit `F = a·Z + b` |
| 3–4 | Constant offset (mean) |
| < 3 | Fails → curve flagged |

### 5.4 Validation

Curves are **never rejected** (backward compatibility). Instead, `warnings` list flags issues:
- `no_negative_snapin`
- `short_drop:N`
- `short_rise:N`

---

## 6. Git + Jupytext Workflow

### 6.1 Source of Truth

| File | Role | Git |
|------|------|-----|
| `reports/JJS_analysis.py` | **Template source** | ✅ Yes |
| `reports/*_analysis.py` | Generated per-dataset | ✅ Yes |
| `reports/*_analysis.ipynb` | Executed output | ⚠️ Stripped by nbstripout |
| `reports/*.pdf` | Figures | ✅ LFS tracked |

### 6.2 Two-way Sync

```bash
# .py → .ipynb (after editing template)
jupytext --to notebook --execute reports/JJS_analysis.py --output reports/JJS_analysis.ipynb

# .ipynb → .py (after interactive Jupyter edits)
jupytext --to py reports/JJS_analysis.ipynb --output reports/JJS_analysis.py

# run_analysis.py does both automatically:
#   1. jupytext --to notebook (temp)
#   2. papermill execute (parameterized)
#   3. jupytext --to py (sync back)
```

---

## 7. Troubleshooting

### Issue: `UnicodeDecodeError` on new dataset
**Fix:** `cleaning.py` already tries `utf-8` → `latin-1`. If both fail, inspect file with `file -I` and add encoding to `load_raw()`.

### Issue: `FILE_PATTERN` matches zero files
**Fix:** Check `dataset_registry.py` pattern. Use `ls {DATASET_DIR}/` to verify filenames. Patterns use `pathlib.Path.glob()` syntax.

### Issue: Notebook cell fails with `NoneType` slope
**Fix:** `cleaning.py` now returns `0.0` for missing slopes instead of `None`. If issue persists, check `warnings` field in cleaned data.

### Issue: Papermill not installed
**Fix:** `pip install papermill jupytext pyyaml`

---

## 8. Extending the Analysis

To add a new analysis unit (e.g., "Humidity Dependence"):

1. **Edit `reports/JJS_analysis.py`** — insert a new Markdown + Code pair
2. **Use only `data` list** — assume `data` is already loaded and cleaned
3. **Keep self-contained** — no hidden state from previous cells
4. **Save figures as PDF** — `fig.savefig(f"{OUTPUT_PREFIX}_humidity.pdf")`
5. **Test** — `python scripts/run_analysis.py --dataset 20260409 --dry-run`
6. **Commit** — `git add reports/JJS_analysis.py`

---

## 9. Command Reference

```bash
# Run full pipeline
python scripts/run_analysis.py --dataset <DIR> [--output-prefix <NAME>] [--dry-run]

# Manual jupytext conversion
jupytext --to notebook template.py --output out.ipynb
jupytext --to py notebook.ipynb --output out.py

# Manual papermill execution
papermill input.ipynb output.ipynb -p DATASET_DIR "20260409" -p SAMPLE_NAME "JJS"

# Check nbstripout status
nbstripout --status
```

---

## 10. Checklist for New Agent

- [ ] `pip install papermill jupytext pyyaml` (first time only)
- [ ] Raw `.txt` files placed in `YYYYMMDDX/` directory
- [ ] `dataset_registry.py` updated with new entry
- [ ] `python scripts/run_analysis.py --dataset <DIR> --dry-run` succeeds
- [ ] `python scripts/run_analysis.py --dataset <DIR>` executes without error
- [ ] Generated `.ipynb` and `.py` files committed to Git
- [ ] `WORKFLOW.md` updated if workflow itself changes
