# Legacy Archive: Pre-RealRaw Retract-Misclassified Analysis

This directory archives AFM analyses generated before the RealRaw branch
separation was confirmed on 2026-04-25.

## Critical Correction

The archived analyses were built on the mistaken assumption that the available
curves represented complete approach/loading behavior. The RealRaw data later
showed that the previously analyzed curves were retract/unloading curves or
otherwise not branch-separated. As a result, old conclusions such as:

- "120 nN approach snap-in anomaly"
- "extreme approach vdW/capillary enhancement"
- intrinsic membrane mechanics inferred from snap/pull-off phases

must not be used as current scientific evidence.

## What Is Archived Here

- `root_outputs/`: legacy PDF/PNG figures that were left in the project root.
- `reports/`: legacy notebooks, report scripts, and generated figures from the
  pre-RealRaw analysis flow.
- `scripts/legacy_scripts/`: old single-branch parser/check/debug/report scripts.
- `reports/legacy_report_scripts/`: old report generator scripts previously kept
  under `archive/reports`.

These files are preserved for provenance only. They are not deleted, but they
are no longer part of the active analysis workflow.

## Current Analysis To Use Instead

Use the branch-aware RealRaw pipeline:

```bash
python scripts/run_realraw_analysis.py --all
python scripts/realraw_scientific_reinterpretation.py
python scripts/stitch_deep_indentation.py
python scripts/compute_apparent_modulus.py --all
python -m pytest tests/test_realraw_analysis.py
```

Current outputs live under:

- `results/realraw/`
- `reports/realraw/`

Current scientific interpretation:

- `extend` = approach/loading.
- `retract` = unloading/pull-off.
- JJS strong signal is retract adhesion/hysteresis, not a 120 nN approach
  snap-in.
- Thin-film mechanics should be extracted only from stitched deep-loading
  curves as model-dependent apparent mechanics.
