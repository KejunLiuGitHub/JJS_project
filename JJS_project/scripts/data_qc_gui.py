#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interactive AFM Data QC GUI
===========================
Manual review of AFM force curves file by file.
First round: keep / pending / discard. Second round: pending files must be resolved.

Usage:
    python scripts/data_qc_gui.py --dataset 20260416原始数据
    python scripts/data_qc_gui.py --dataset 20260416原始数据 --pattern "k80*.txt"

Shortcuts:
    Y / →  : Keep
    N      : Discard
    S      : Save progress
    Q / Esc: Quit
"""

import sys
import json
import argparse
import tkinter as tk
from tkinter import filedialog
from pathlib import Path
from datetime import datetime
from glob import glob

import numpy as np
import matplotlib
matplotlib.use('TkAgg')  # Use TkAgg backend to avoid conflicts with tkinter on macOS
import matplotlib.pyplot as plt
from matplotlib.widgets import Button

# ── Font config ───────────────────────────────────────────────────
matplotlib.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans', 'sans-serif']
matplotlib.rcParams['axes.unicode_minus'] = False

# ── Import project modules ────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))
from cleaning import load_raw, correct_baseline, segment_curve

# ── Config ────────────────────────────────────────────────────────
RESULTS_DIR = Path("/Users/kejunliu/Desktop/Research_Data/AFM/JJS_project/results")
COLORS = {
    "keep": "#2ecc71",      # Green
    "pending": "#f1c40f",   # Yellow
    "discard": "#e74c3c",   # Red
    "none": "#3498db",      # Blue (undecided)
}

# UI labels
LABELS = {
    "keep": "Keep (Y)",
    "pending": "Pending (P)",
    "discard": "Discard (N)",
}

STATUS_TEXT = {
    "keep": "[KEPT]",
    "pending": "[PENDING]",
    "discard": "[DISCARDED]",
    "none": "[UNDECIDED]",
}


class AFMQC_GUI:
    def __init__(self, dataset_dir, pattern="*.txt", resume=True):
        self.dataset_dir = Path(dataset_dir)
        self.pattern = pattern
        
        # Collect file list
        self.files = sorted(self.dataset_dir.glob(pattern))
        if not self.files:
            raise FileNotFoundError(f"No files matching '{pattern}' in directory {dataset_dir}")
        
        self.total = len(self.files)
        self.current_idx = 0
        self.phase2_mode = False  # Phase 2: resolve pending files only
        
        # Decision storage
        self.decisions = {}  # filename -> "keep"/"pending"/"discard"
        
        # Progress files
        self.progress_file = RESULTS_DIR / "qc_progress.json"
        self.output_file = RESULTS_DIR / "qc_decisions.json"
        
        if resume and self.progress_file.exists():
            self._load_progress()
        
        # Create figure
        self._setup_figure()
        
    def _load_existing_decisions(self):
        """Load decisions from qc_decisions.json (merge across datasets)"""
        existing = {}
        if self.output_file.exists():
            try:
                with open(self.output_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    if "decisions" in data:
                        existing = data["decisions"]
                    else:
                        existing = data  # old flat format
            except Exception:
                pass
        return existing

    def _load_progress(self):
        """Resume from progress file"""
        try:
            # Load any existing cross-dataset decisions first
            existing = self._load_existing_decisions()
            self.decisions = dict(existing)
            
            with open(self.progress_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Only resume progress if dataset matches
            saved_dataset = data.get("dataset", "")
            current_dataset = str(self.dataset_dir)
            if saved_dataset and Path(saved_dataset).resolve() != Path(current_dataset).resolve():
                print(f"[Resume skipped] Progress file is for '{saved_dataset}', not '{current_dataset}'")
                print(f"[Info] Starting fresh for current dataset. Previous decisions are preserved in qc_decisions.json")
                return
            
            # Merge progress decisions for matching dataset
            progress_decisions = data.get("decisions", {})
            self.decisions.update(progress_decisions)
            
            # Resume position to first unreviewed file in current dataset
            reviewed = set(self.decisions.keys())
            for i, fpath in enumerate(self.files):
                if fpath.name not in reviewed:
                    self.current_idx = i
                    break
            else:
                self.current_idx = 0
            n_reviewed_current = sum(1 for f in self.files if f.name in reviewed)
            print(f"[Resume] Reviewed {n_reviewed_current}/{self.total} files in current dataset")
        except Exception as e:
            print(f"[Resume failed] {e}")
    
    def _save_progress(self):
        """Save progress"""
        data = {
            "dataset": str(self.dataset_dir),
            "pattern": self.pattern,
            "timestamp": datetime.now().isoformat(),
            "current_idx": self.current_idx,
            "decisions": self.decisions,
            "stats": self._get_stats(),
        }
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        with open(self.progress_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[Saved] {self.progress_file}")
    
    def _export_final(self):
        """Export final results (keep/discard only, merge across datasets)"""
        # Load existing cross-dataset decisions
        existing = self._load_existing_decisions()
        
        # Merge with current session decisions
        current_final = {k: v for k, v in self.decisions.items() if v in ("keep", "discard")}
        merged = {**existing, **current_final}
        
        data = {
            "dataset": str(self.dataset_dir),
            "pattern": self.pattern,
            "timestamp": datetime.now().isoformat(),
            "decisions": merged,
            "stats": self._get_stats(),
        }
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[Exported] {self.output_file} ({len(merged)} total decisions)")
    
    def _get_stats(self):
        """Statistics"""
        stats = {"keep": 0, "pending": 0, "discard": 0, "none": 0}
        for fname in [f.name for f in self.files]:
            d = self.decisions.get(fname, "none")
            stats[d] = stats.get(d, 0) + 1
        stats["total"] = self.total
        stats["reviewed"] = len(self.decisions)
        return stats
    
    def _setup_figure(self):
        """Initialize matplotlib figure and buttons"""
        self.fig, self.ax = plt.subplots(figsize=(12, 7))
        plt.subplots_adjust(bottom=0.18)
        
        # Labels
        self.ax.set_xlabel("Piezo displacement Z (nm)", fontsize=12)
        self.ax.set_ylabel("Force F (nN)", fontsize=12)
        
        # Create buttons
        ax_keep = plt.axes([0.20, 0.05, 0.15, 0.06])
        ax_pending = plt.axes([0.425, 0.05, 0.15, 0.06])
        ax_discard = plt.axes([0.65, 0.05, 0.15, 0.06])
        
        self.btn_keep = Button(ax_keep, LABELS["keep"], color=COLORS["keep"], hovercolor="0.9")
        self.btn_pending = Button(ax_pending, LABELS["pending"], color=COLORS["pending"], hovercolor="0.9")
        self.btn_discard = Button(ax_discard, LABELS["discard"], color=COLORS["discard"], hovercolor="0.9")
        
        self.btn_keep.on_clicked(lambda e: self._on_decision("keep"))
        self.btn_pending.on_clicked(lambda e: self._on_decision("pending"))
        self.btn_discard.on_clicked(lambda e: self._on_decision("discard"))
        
        # Keyboard events
        self.fig.canvas.mpl_connect("key_press_event", self._on_key)
        
        # Progress text
        self.text_progress = self.fig.text(0.5, 0.95, "", ha="center", fontsize=11, fontweight="bold")
        self.text_meta = self.fig.text(0.5, 0.01, "", ha="center", fontsize=9, style="italic")
        
        # Show first file
        self._show_current()
    
    def _load_and_process(self, fpath):
        """Load and process a single file"""
        try:
            rc = load_raw(str(fpath))
            z, f = rc["z"], rc["f"]
            
            # Baseline correction
            baseline_result = correct_baseline(z, f)
            f_corr = baseline_result[0] if baseline_result[0] is not None else f
            
            # Segment
            seg = segment_curve(z, f_corr)
            
            # Find stable contact (3 consecutive F>=0)
            snap_z = seg["snap_z"]
            post_snap = z >= snap_z
            z_post = z[post_snap]
            f_post = f_corr[post_snap]
            
            z_cp = None
            for i in range(len(f_post) - 3 + 1):
                if np.all(f_post[i:i+3] >= 0):
                    z_cp = z_post[i]
                    break
            
            meta = {
                "z_range": (float(min(z)), float(max(z))),
                "f_range": (float(min(f_corr)), float(max(f_corr))),
                "snap_z": float(snap_z),
                "snap_f": float(seg["snap_f"]),
                "z_cp": float(z_cp) if z_cp else None,
                "n_points": len(z),
            }
            return z, f_corr, seg, meta
        except Exception as e:
            return None, None, None, {"error": str(e)}
    
    def _show_current(self):
        """Show current file"""
        if self.current_idx >= len(self._current_file_list()):
            if self.phase2_mode:
                # Phase 2 complete
                self._finish_phase2()
            else:
                self._start_phase2_or_finish()
            return
        
        fpath = self._current_file_list()[self.current_idx]
        fname = fpath.name
        decision = self.decisions.get(fname, "none")
        
        # Load data
        z, f_corr, seg, meta = self._load_and_process(fpath)
        
        # Clear and redraw
        self.ax.clear()
        
        if z is not None:
            # Plot scatter-line
            self.ax.plot(z, f_corr, "bo-", markersize=3, linewidth=0.8, alpha=0.7, label="Force curve")
            
            # Mark snap-in
            if seg:
                snap_z, snap_f = seg["snap_z"], seg["snap_f"]
                self.ax.plot(snap_z, snap_f, "ro", markersize=10, zorder=5, label=f"Snap-in ({snap_f:.1f} nN)")
            
            # Mark contact point
            if meta.get("z_cp"):
                z_cp = meta["z_cp"]
                self.ax.axvline(z_cp, color="g", linestyle="--", alpha=0.5, label=f"Contact Z={z_cp:.0f} nm")
            
            # F=0 line
            self.ax.axhline(0, color="k", linestyle="-", linewidth=0.5, alpha=0.5)
            
            self.ax.legend(loc="upper left", fontsize=9)
        else:
            self.ax.text(0.5, 0.5, f"Load failed:\n{meta.get('error', 'Unknown error')}", 
                        transform=self.ax.transAxes, ha="center", va="center", fontsize=12, color="red")
        
        # Border color indicates decision status
        color = COLORS.get(decision, COLORS["none"])
        for spine in self.ax.spines.values():
            spine.set_color(color)
            spine.set_linewidth(4)
        
        # Update title and progress
        status = STATUS_TEXT.get(decision, "⏳ Undecided")
        phase_label = " [Phase 2 - Must decide]" if self.phase2_mode else ""
        
        self.ax.set_title(fname[:55] + ("..." if len(fname) > 55 else "") + phase_label, fontsize=10)
        
        progress = f"{self.current_idx + 1} / {len(self._current_file_list())}  |  {status}"
        if self.phase2_mode:
            progress += "  |  Phase 2"
        self.text_progress.set_text(progress)
        self.text_progress.set_color(color)
        
        # Metadata text
        if meta.get("z_range"):
            meta_str = f"Z range: {meta['z_range'][0]:.0f} ~ {meta['z_range'][1]:.0f} nm  |  "
            meta_str += f"F range: {meta['f_range'][0]:.1f} ~ {meta['f_range'][1]:.1f} nN  |  "
            meta_str += f"Snap: {meta['snap_f']:.1f} nN"
            if meta.get("z_cp"):
                meta_str += f"  |  Contact: {meta['z_cp']:.0f} nm"
        else:
            meta_str = f"Error: {meta.get('error', 'Unknown error')}"
        
        self.text_meta.set_text(meta_str)
        
        self.fig.canvas.draw_idle()
    
    def _current_file_list(self):
        """Current phase file list"""
        if self.phase2_mode:
            # Return only pending files
            return [f for f in self.files if self.decisions.get(f.name) == "pending"]
        return self.files
    
    def _on_decision(self, decision):
        """Handle button click"""
        fname = self._current_file_list()[self.current_idx].name
        self.decisions[fname] = decision
        print(f"  [{decision.upper()}] {fname}")
        
        # Auto-save
        self._save_progress()
        
        # Next file
        self.current_idx += 1
        self._show_current()
    
    def _on_key(self, event):
        """Handle keyboard events"""
        key = event.key.lower()
        
        if key in ("y", "right"):
            self._on_decision("keep")
        elif key in ("n", "delete"):
            self._on_decision("discard")
        elif key == "p" and not self.phase2_mode:
            self._on_decision("pending")
        elif key == "s":
            self._save_progress()
        elif key in ("q", "escape"):
            self._quit()
    
    def _start_phase2_or_finish(self):
        """Check if phase 2 is needed, or finish"""
        pending_files = [f for f in self.files if self.decisions.get(f.name) == "pending"]
        n_pending = len(pending_files)
        
        if n_pending > 0:
            # Enter phase 2
            self.phase2_mode = True
            self.current_idx = 0
            print(f"\n[Phase 2] {n_pending} pending files remain. Must choose keep or discard.\n")
            
            # Hide Pending button
            self.btn_pending.ax.set_visible(False)
            self.fig.canvas.draw_idle()
            
            self._show_current()
        else:
            self._finish()
    
    def _finish_phase2(self):
        """Phase 2 complete"""
        self._finish()
    
    def _finish(self):
        """Review complete"""
        self._export_final()
        stats = self._get_stats()
        
        # Clear canvas, show final results
        self.ax.clear()
        self.ax.set_visible(False)
        
        # Statistics text
        result_text = (
            f"Review Complete!\n\n"
            f"Total: {stats['total']}\n"
            f"  Kept: {stats['keep']}\n"
            f"  Discarded: {stats['discard']}\n"
            f"  Pending: {stats['pending']}\n"
            f"  Unreviewed: {stats['none']}\n\n"
            f"Results saved to:\n{self.output_file}"
        )
        self.fig.text(0.5, 0.5, result_text, ha="center", va="center", fontsize=14, 
                     family="monospace", bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5))
        
        self.text_progress.set_text("Review Complete")
        self.text_progress.set_color("green")
        self.text_meta.set_text("")
        
        self.fig.canvas.draw_idle()
        plt.pause(3)
        plt.close()
    
    def _quit(self):
        """Quit"""
        self._save_progress()
        
        # If pending files exist, notify user
        pending_files = [f for f in self.files if self.decisions.get(f.name) == "pending"]
        if pending_files and not self.phase2_mode:
            print(f"\n[Note] {len(pending_files)} pending files remain")
            print("Re-run the script to resolve them, or export results as-is")
        
        self._export_final()
        stats = self._get_stats()
        print(f"\n{'='*50}")
        print(f"Review Statistics")
        print(f"{'='*50}")
        print(f"  Total:       {stats['total']}")
        print(f"  Kept:       {stats['keep']}")
        print(f"  Discarded:  {stats['discard']}")
        print(f"  Pending:    {stats['pending']}")
        print(f"  Unreviewed: {stats['none']}")
        print(f"{'='*50}")
        plt.close()
    
    def run(self):
        """Launch GUI"""
        print(f"\n{'='*60}")
        print(f"AFM Data QC GUI")
        print(f"Dataset: {self.dataset_dir}")
        print(f"Files: {self.total}")
        print(f"{'='*60}")
        print("Shortcuts: Y=Keep, N=Discard, P=Pending (round 1 only), S=Save, Q=Quit")
        print("Use mouse or keyboard to review...\n")
        plt.show()


def select_dataset():
    """Open a folder picker dialog to select dataset directory."""
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    root.attributes('-topmost', True)  # Bring dialog to front
    
    dataset = filedialog.askdirectory(
        title="Select Dataset Folder",
        initialdir=str(Path.cwd()),
    )
    root.destroy()
    
    if not dataset:
        print("No folder selected. Exiting.")
        sys.exit(0)
    
    return dataset

def main():
    parser = argparse.ArgumentParser(description="Interactive AFM Data QC GUI")
    parser.add_argument("--dataset", default=None, help="Dataset directory (optional; will prompt if not provided)")
    parser.add_argument("--pattern", default="*.txt", help="File glob pattern")
    parser.add_argument("--no-resume", action="store_true", help="Do not resume previous progress")
    args = parser.parse_args()
    
    dataset = args.dataset
    if dataset is None:
        dataset = select_dataset()
    
    dataset_path = Path(dataset)
    if not dataset_path.exists() or not dataset_path.is_dir():
        print(f"Dataset directory not found: {dataset}")
        print("Opening folder picker...")
        dataset = select_dataset()
    
    gui = AFMQC_GUI(
        dataset_dir=dataset,
        pattern=args.pattern,
        resume=not args.no_resume,
    )
    gui.run()


if __name__ == "__main__":
    main()
