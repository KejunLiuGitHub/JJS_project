# Note: Approach + Withdraw Data Integration

**Recorded:** 2026-04-21  
**Source:** User feedback from experimental collaborator

---

## Key Finding

The Bruker NanoScope `.txt` exports for this batch of data contain **both approach and withdraw (retraction) segments**, not just approach as previously assumed.

## Current State

- `scripts/cleaning.py` currently only processes the **approach** segment:
  - `drop_z / drop_f`: from `drop_start_idx` to `snap_idx`
  - `rise_z / rise_f`: from `snap_idx` to `contact_idx`
- The withdraw/retraction segment (post-contact return) is **not extracted**.

## Required Update

When the student testing the data provides feedback, update the pipeline to:

1. **Parse both approach and withdraw** from the raw Bruker export
2. **Stitch them together** into a single continuous force-distance curve
3. **Analyze the full cycle**:
   - Approach: far-field → snap-in → contact → indentation
   - Withdraw: retraction → adhesion pull-off → far-field recovery
4. **Compare approach vs. withdraw hysteresis** for energy dissipation and adhesion work

## Files to Modify (future task)

- `scripts/cleaning.py`: `load_raw()` and `segment_curve()` to extract withdraw segment
- `scripts/cleaning.py`: `correct_baseline()` to handle full-cycle baseline
- `reports/JJS_analysis.py`: Add withdraw analysis unit
- `scripts/data_qc_gui.py`: Update to show both approach and withdraw for QC

## Blocker

Waiting for student test feedback before implementing.

---

**Status:** Deferred until student feedback received.
