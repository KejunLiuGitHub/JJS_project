# -*- coding: utf-8 -*-
"""
QC Filter — load manual QC decisions and filter file lists.

Usage:
    from qc_filter import load_qc_decisions, get_discarded_set, filter_files

    discarded = get_discarded_set()          # set of discarded filenames
    kept = filter_files(file_list)           # keep only non-discarded
"""
import json
from pathlib import Path

DEFAULT_QC_PATH = Path(__file__).parent.parent / "results" / "qc_decisions.json"


def load_qc_decisions(qc_path=None):
    """Load qc_decisions.json, return dict of {filename: decision}."""
    path = Path(qc_path) if qc_path else DEFAULT_QC_PATH
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("decisions", {})


def get_discarded_set(qc_path=None):
    """Return a set of discarded filenames (basename only)."""
    decisions = load_qc_decisions(qc_path)
    return {fname for fname, decision in decisions.items() if decision == "discard"}


def get_kept_set(qc_path=None):
    """Return a set of kept filenames (basename only)."""
    decisions = load_qc_decisions(qc_path)
    return {fname for fname, decision in decisions.items() if decision == "keep"}


def filter_files(file_list, qc_path=None):
    """Filter a list of Path objects, keeping only non-discarded files."""
    discarded = get_discarded_set(qc_path)
    kept = [fp for fp in file_list if fp.name not in discarded]
    return kept


def summarize(qc_path=None):
    """Print QC summary."""
    decisions = load_qc_decisions(qc_path)
    stats = {"keep": 0, "discard": 0, "pending": 0}
    for v in decisions.values():
        stats[v] = stats.get(v, 0) + 1
    print(f"[QC] Total decisions: {len(decisions)}")
    print(f"     Keep: {stats['keep']}  |  Discard: {stats['discard']}  |  Pending: {stats['pending']}")
    return stats


if __name__ == "__main__":
    summarize()
