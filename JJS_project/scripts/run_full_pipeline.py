#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Master entry point: one command runs the full AFM analysis pipeline.

Usage:
    python scripts/run_full_pipeline.py          # run all steps
    python scripts/run_full_pipeline.py --force  # re-run all steps (ignore caches)
    python scripts/run_full_pipeline.py --dry-run  # print what would run

Steps:
    1. run_realraw_analysis.py --all        → results/realraw/*.csv
    2. realraw_scientific_reinterpretation.py → results/realraw/scientific_reinterpretation_metrics.json
    3. stitch_deep_indentation.py            → results/realraw/deep_stitched_*.csv
    4. compute_apparent_modulus.py --all     → results/realraw/apparent_modulus_*.csv
    5. generate_scientific_report.py         → figures + markdown + progress.md
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
RESULTS_DIR = ROOT / "results" / "realraw"


def output_exists(*paths):
    return all(Path(p).exists() for p in paths)


def run_step(name, cmd, *check_outputs, force=False):
    """Run a pipeline step. Skip if all check_outputs exist (unless force=True)."""
    if not force and output_exists(*check_outputs):
        print(f"[SKIP] {name} — outputs already exist")
        for p in check_outputs:
            print(f"       {p}")
        return True

    print(f"[RUN]  {name}")
    print(f"       {' '.join(str(c) for c in cmd)}")
    t0 = time.time()
    result = subprocess.run(cmd, cwd=str(ROOT))
    elapsed = time.time() - t0
    if result.returncode != 0:
        print(f"[FAIL] {name} — exit code {result.returncode} ({elapsed:.1f}s)")
        return False
    print(f"[OK]   {name} ({elapsed:.1f}s)")
    return True


def main():
    parser = argparse.ArgumentParser(description="Run full AFM analysis pipeline")
    parser.add_argument("--force", action="store_true", help="Re-run all steps (ignore cached outputs)")
    parser.add_argument("--dry-run", action="store_true", help="Print steps without executing")
    parser.add_argument("--skip-figures", action="store_true", help="Skip the figure-generation + report step")
    args = parser.parse_args()

    steps = [
        (
            "Step 1/5: RealRaw branch-aware analysis",
            ["python", "scripts/run_realraw_analysis.py", "--all"],
            RESULTS_DIR / "curve_features.csv",
            RESULTS_DIR / "pair_features.csv",
            RESULTS_DIR / "qc_summary.csv",
        ),
        (
            "Step 2/5: Scientific reinterpretation",
            ["python", "scripts/realraw_scientific_reinterpretation.py"],
            RESULTS_DIR / "scientific_reinterpretation_metrics.json",
            RESULTS_DIR / "scientific_reinterpretation_summary.csv",
        ),
        (
            "Step 3/5: Deep indentation stitching",
            ["python", "scripts/stitch_deep_indentation.py"],
            RESULTS_DIR / "deep_stitched_points.csv",
            RESULTS_DIR / "deep_stitched_mechanics.csv",
        ),
        (
            "Step 4/5: Apparent modulus analysis",
            ["python", "scripts/compute_apparent_modulus.py", "--all"],
            RESULTS_DIR / "apparent_modulus_curves.csv",
            RESULTS_DIR / "apparent_modulus_group_summary.csv",
        ),
    ]

    if not args.skip_figures:
        steps.append(
            (
                "Step 5/5: Figures + Markdown report + progress.md",
                ["python", "scripts/generate_scientific_report.py"],
                ROOT / "reports" / "realraw" / "scientific_report" / "afm_scientific_report.md",
            )
        )

    if args.dry_run:
        print("[DRY RUN] Would execute:")
        for name, cmd, *_ in steps:
            print(f"  {name}: {' '.join(cmd)}")
        return

    print("=" * 60)
    print("AFM Full Analysis Pipeline")
    print(f"Root: {ROOT}")
    print(f"Force: {args.force}")
    print("=" * 60)
    print()

    failed = []
    for name, cmd, *check_outputs in steps:
        ok = run_step(name, cmd, *check_outputs, force=args.force)
        if not ok:
            failed.append(name)
        print()

    print("=" * 60)
    if failed:
        print(f"FAILED: {len(failed)} step(s)")
        for f in failed:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print("All steps completed successfully.")
        print(f"Markdown report: {ROOT / 'reports' / 'realraw' / 'scientific_report' / 'afm_scientific_report.md'}")
        print(f"Progress log:    {ROOT.parent / 'progress.md'}")


if __name__ == "__main__":
    main()
