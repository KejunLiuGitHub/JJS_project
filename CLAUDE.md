# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**⚖️ 本项目的宪法文件: `.claude/constitution.md`。任何操作前必须先理解宪法规则。**
**⚖️ 宪法优先级高于本文件。与本文件冲突时以宪法为准。**

## Project Overview

AFM force-distance curve analysis for 2D COF (covalent organic framework) thin films. Raw data comes from Bruker NanoScope PeakForce QNM mode. The main analysis codebase is in `JJS_project/`; `1umSquare/` contains a separate set of raw Bruker data for NLS/linker experiments.

## Constitutional Rules (摘要 — 完整版见 .claude/constitution.md)

1. **progress.md 中心地位**: 每次运行追加 14 章节完整条目。**只增不改**——学生可以追加 `> **学生注**` 讨论段，但不能删除或修改自动生成的历史条目。结论有错时，在新条目中追加更正并显式引用原位置（协议 1.6）。所有 progress.md 修改通过 git diff 在 PR 中暴露。
2. **文献引用必须有本地文件 + 行号**: 引用前必须先 Read `literature/*.md`，标注行号范围。没有本地文献文件 → 不得引用。
3. **代码纪律**: scripts/ 中只有能跑通的代码。不能跑的移入 archive/。
4. **Git 分支**: 学生不直接 push main。在 `student/<name>/<topic>` 分支工作，通过 PR 由教师审查合并。
5. **学生可改**: RealRaw/数据, dataset_registry.py, progress.md (追加模式), literature/（新文献）。**不可改**: 其他 scripts/、CLAUDE.md、constitution.md、README.md、.gitignore。

## Key Commands

```bash
# One command — run the full analysis pipeline end-to-end
python scripts/run_full_pipeline.py              # run all 5 steps (skip cached)
python scripts/run_full_pipeline.py --force      # re-run everything
python scripts/run_full_pipeline.py --dry-run    # print what would run
python scripts/run_full_pipeline.py --skip-figures  # skip report generation

# Individual steps (when you only need one):
python scripts/run_realraw_analysis.py --all                    # Step 1: branch-aware curve analysis
python scripts/realraw_scientific_reinterpretation.py           # Step 2: scientific interpretation
python scripts/stitch_deep_indentation.py                       # Step 3: slip-event stitching
python scripts/compute_apparent_modulus.py --all                # Step 4: apparent modulus fitting
python scripts/generate_scientific_report.py                    # Step 5: figures + MD report + progress.md

# Legacy Jupytext+Papermill analysis (old workflow, being phased out)
python scripts/run_analysis.py --list
python scripts/run_analysis.py --dataset 20260409

# Interactive QC (Stage 1, before batch analysis)
python scripts/data_qc_gui.py --dataset <DIR>

# Run tests
python -m pytest tests/ -v
```

Dependencies: `numpy scipy matplotlib pandas pyyaml pytest`

## Architecture

### Automated pipeline (`run_full_pipeline.py` → Markdown report)

The primary workflow is fully automated. A single command runs 5 steps:

1. **`run_realraw_analysis.py --all`** → `results/realraw/curve_features.csv`, `pair_features.csv`, `qc_summary.csv`
2. **`realraw_scientific_reinterpretation.py`** → `results/realraw/scientific_reinterpretation_metrics.json`
3. **`stitch_deep_indentation.py`** → `results/realraw/deep_stitched_points.csv`, `deep_stitched_mechanics.csv`
4. **`compute_apparent_modulus.py --all`** → `results/realraw/apparent_modulus_curves.csv`, `apparent_modulus_group_summary.csv`
5. **`generate_scientific_report.py`** → 13 figures (PDF+PNG), `reports/realraw/scientific_report/afm_scientific_report.md` (standalone Markdown report with embedded figures), and appends a new timestamped entry to `../../progress.md` (repo root)

Each step checks for cached outputs and skips if present (unless `--force`). The `progress.md` at repo root is a living auto-analysis log — each run appends a new section with key results, discussion, and literature references.

### Core modules

- **`scripts/cleaning.py`** — Stateless shared module. `load_raw()` parses Bruker .txt (auto-detects utf-8/latin-1 encoding, nm/um/nN/uN/pN units). `correct_baseline()` does far-field linear fit (Z ∈ [0,100] nm). `segment_curve()` detects snap-in (argmin of corrected force), contact point (first post-snap F≥0), and splits into drop/rise segments. `clean_and_validate()` runs the full pipeline; returns `None` on failure, otherwise a dict with keys: `file, snap_f, snap_z, contact_z, contact_f, drop_z, drop_f, rise_z, rise_f, warnings, valid`.
- **`scripts/dataset_registry.py`** — Central config dictionary `DATASETS` with 6 entries: `20260409`, `20260415原始数据`, `20260416原始数据`, `RealRaw/20260409`, `RealRaw/20260415`, `RealRaw/20260416`. Each entry has probe parameters, file glob pattern, units, and sample metadata. Use `get_config(key)` to retrieve.
- **`scripts/run_realraw_analysis.py`** — Branch-aware pipeline for RealRaw data. Treats `extend/` as approach/loading, `retract/` as unloading. Pairs same-named files across branches, runs curve-level analysis, outputs `results/realraw/curve_features.csv`, `pair_features.csv`, `qc_summary.csv`, and PDF overview plots.
- **`scripts/stitch_deep_indentation.py`** — Detects recoverable slip events in deep-indentation loading curves and stitches them into continuous loading envelopes for mechanics fitting.
- **`scripts/compute_apparent_modulus.py`** — Fits membrane mechanics model `F = k1*δ + k3*δ³` to stitched curves, computes model-dependent apparent modulus for relative comparisons. Intentionally does NOT produce intrinsic Young's modulus.
- **`scripts/generate_scientific_report.py`** — Output-only module. Generates all 13 figures, writes a standalone 12-section Markdown report (`afm_scientific_report.md`) with embedded figures and tables, and appends a timestamped entry to `progress.md`. No LaTeX dependency.

### Data directories

- `20260409/` — JJS dataset: 11 curves, <10nm amorphous film on SiN pore, RTESPA-150 probe (k=7 N/m, R=8 nm)
- `20260415原始数据/` — linker1 dataset: 56 curves, 50-80nm crystalline film on copper mesh, RTESPA-150 (k=7 N/m, R=8 nm)
- `20260416原始数据/` — k80 dataset: 49 curves, 50-80nm crystalline film on copper mesh, DDESP-V2 probe (k=89 N/m, R=100 nm)
- `RealRaw/<date>/extend/` and `RealRaw/<date>/retract/` — Branch-separated raw data. **extend = approach/loading, retract = unloading/pull-off adhesion.** These are the current ground truth.
- `archive/pre_realraw_retract_misclassified_20260425/` — Archived pre-RealRaw analysis (retract was misclassified as approach). Historical reference only, not for current conclusions.

### Output directories

- `results/` — JSON/CSV analysis outputs
- `results/realraw/` — RealRaw pipeline outputs
- `reports/realraw/` — PDF figures from RealRaw analysis
- `reports/realraw/scientific_report/` — Standalone Markdown report (`afm_scientific_report.md`) + all figures (PDF+PNG)
- `reports/realraw/scientific_reinterpretation/` — Corrected scientific narrative
- `reports/realraw/apparent_modulus/` — Apparent modulus figures
- `progress.md` (repo root) — Living auto-analysis log, appended on each pipeline run

## Critical Scientific Context

The original analysis mistakenly reported ~120 nN "approach snap-in" forces. **This was wrong.** The retract branch had been merged/confused with extend. After branch separation:

- **extend snap-in**: median ~17 nN (JJS), consistent with classical vdW + capillary (~10 nN for R=8 nm)
- **retract pull-off**: median ~116 nN (JJS), ~7× larger than extend — attributed to water bridge / confined water / contact-line pinning coupled with compliant suspended membrane

**Always confirm branch (extend vs retract), probe radius, cantilever stiffness, and whether cantilever correction is needed** before interpreting any AFM result.

The central scientific question is: does the suspended ultra-thin COF membrane amplify water-bridge adhesion hysteresis? Key missing controls: humidity dependence, suspended vs supported comparison, velocity dependence.

## Conventions

- **Constitution first**: Before any action, understand `.claude/constitution.md`. Key rules: progress.md is sacred (append-only, 14-section entries), all citations must reference `literature/*.md` with line numbers, students work on branches.
- **Markdown-first reports**: `generate_scientific_report.py` outputs standalone `.md` files with embedded figures — no LaTeX/PDF dependency. The `progress.md` at repo root is append-only; each run adds a new timestamped 14-section entry.
- **Literature citations**: All scientific citations MUST reference a local file in `literature/` with specific line numbers. Format: `[AuthorYear](literature/File.md#Lxxx-Lxxx)`. Read the file before citing. No local file = no citation allowed.
- **Figure specs**: PDF vector output, `plt.rcParams['pdf.fonttype'] = 42`, single-col 3.39 inch, double-col 7.01 inch. Color palette: `['#0C5DA5', '#E8204E', '#00B945', '#FF9500', '#845B97', '#474747']`.
- **Force sign**: negative = attractive (tip pulled toward sample), positive = repulsive.
- **Encoding**: Bruker .txt files use utf-8 or latin-1. `cleaning.py` auto-detects.
- **Z direction**: Bruker exports Z decreasing. `cleaning.py` reverses it so Z increases for analysis, unless `branch="extend"` or `branch="retract"` is explicitly passed (RealRaw data is already in branch order).
- **Git**: Commit messages in English. Do not delete old results or data. Students push to `student/<name>/<topic>` branches, not main.
