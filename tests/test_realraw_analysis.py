import sys
from pathlib import Path
import json

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from cleaning import load_raw
from dataset_registry import get_config
from run_realraw_analysis import analyze_curve, pair_files
from realraw_scientific_reinterpretation import theory_for_radius
from stitch_deep_indentation import (
    StitchParams,
    analyze_row as analyze_stitched_row,
    detect_slip_events,
    fit_mechanics,
    stitch_curve,
)
from compute_apparent_modulus import (
    apparent_modulus_mpa,
    build_curve_table,
    filter_analysis_rows,
    fit_membrane_terms,
    k3_from_apparent_modulus_mpa,
    k3_nN_nm3_to_N_m3,
)


def test_extend_preserves_increasing_time_order():
    fp = ROOT / "RealRaw/20260415/extend/linker1-PFPE-OH-1000nm.spm - NanoScope Analysis.txt"
    raw = load_raw(fp, branch="extend")
    assert raw["branch"] == "extend"
    assert raw["direction"] == "inc"
    assert np.all(np.diff(raw["z_nm"]) > 0)
    assert raw["z_nm"][0] == raw["z_time"][0]


def test_retract_preserves_unloading_direction():
    fp = ROOT / "RealRaw/20260415/retract/linker1-PFPE-OH-1000nm.spm - NanoScope Analysis.txt"
    raw = load_raw(fp, branch="retract")
    assert raw["branch"] == "retract"
    assert raw["direction"] == "dec"
    assert np.all(np.diff(raw["z_nm"]) < 0)


def test_20260415_pairs_same_named_extend_retract():
    pairs = pair_files(ROOT / "RealRaw", dates=["20260415"])
    key = ("20260415", "linker1-PFPE-OH-1000nm.spm - NanoScope Analysis.txt")
    assert key in pairs
    assert pairs[key]["extend"] is not None
    assert pairs[key]["retract"] is not None


def test_jjs_snap_comes_from_extend_branch():
    cfg = get_config("RealRaw/20260409")
    fp = ROOT / "RealRaw/20260409/extend/JJS-50nm-1000nm-10nN - NanoScope Analysis.txt"
    row, _ = analyze_curve(fp, "20260409", "extend", cfg)
    assert row["branch"] == "extend"
    assert row["direction"] == "inc"
    assert row["snap_z_nm"] > 900
    assert row["snap_f_nN"] < 0


def test_20260416_un_units_are_converted_to_nn():
    fp = ROOT / "RealRaw/20260416/extend/k80-linker1-paa-50nm-500nm-3uN - NanoScope Analysis.txt"
    raw = load_raw(fp, branch="extend")
    assert raw["force_nN"][0] > 5000
    cfg = get_config("RealRaw/20260416")
    row, _ = analyze_curve(fp, "20260416", "extend", cfg)
    assert row["max_force_nN"] > 100


def test_curve_output_has_required_columns():
    cfg = get_config("RealRaw/20260415")
    fp = ROOT / "RealRaw/20260415/extend/linker1-PFPE-OH-1000nm.spm - NanoScope Analysis.txt"
    row, _ = analyze_curve(fp, "20260415", "extend", cfg)
    required = {
        "date",
        "branch",
        "sample",
        "displacement_nm",
        "setpoint",
        "snap_f_nN",
        "pull_off_f_nN",
        "baseline_status",
        "warnings",
    }
    assert required.issubset(row.keys())


def test_reinterpreted_jjs_scientific_numbers_are_branch_separated():
    metrics_path = ROOT / "results/realraw/scientific_reinterpretation_metrics.json"
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    jjs = metrics["jjs"]
    assert 16.0 < jjs["extend_snap_median_nN"] < 18.5
    assert 110.0 < jjs["retract_pull_off_median_nN"] < 121.0
    assert 6.0 < jjs["pull_to_snap_ratio_median"] < 8.0
    assert jjs["retract_pull_off_median_nN"] > 5 * jjs["extend_snap_median_nN"]


def test_classic_theory_scale_matches_revised_extend_claim():
    theory = theory_for_radius(8.0)
    assert 2.5 < theory["F_vdW_nN"] < 3.5
    assert 6.5 < theory["F_capillary_nN"] < 8.0
    assert 9.5 < theory["F_vdW_plus_capillary_nN"] < 11.0
    summary = pd.read_csv(ROOT / "results/realraw/scientific_reinterpretation_summary.csv")
    jjs = summary[(summary["date"] == 20260409) & (summary["group"] == "JJS")].iloc[0]
    assert jjs["extend_snap_median_nN"] / theory["F_vdW_plus_capillary_nN"] < 2.0


def test_reinterpretation_report_contains_erratum_language():
    report = ROOT / "reports/realraw/scientific_reinterpretation/realraw_scientific_reinterpretation.md"
    text = report.read_text(encoding="utf-8")
    assert "retract phenomenon" in text
    assert "not as intrinsic film pre-tension" in text
    assert "does not require a 40x Hamaker enhancement" in text


def test_recoverable_slips_are_stitched_to_continuous_loading():
    delta = np.arange(0, 220, dtype=float)
    force = 0.8 * delta
    force[70:] -= 45.0
    force[145:] -= 60.0
    force += 0.8 * np.sin(delta / 13.0)
    params = StitchParams(force_abs_min_20260415=10.0, recovery_fraction=0.55)
    events = detect_slip_events(delta, force, 20260415, params)
    recoverable = [e for e in events if e["event_type"] == "recoverable_slip"]
    assert len(recoverable) >= 2
    points, rupture_idx = stitch_curve(delta, force, events)
    assert rupture_idx is None
    assert points["cumulative_offset_nN"].max() > 90
    mech = fit_mechanics(points)
    assert mech["fit_points"] > 100
    assert mech["high_stiffness_N_m"] > 0.5


def test_terminal_cliff_is_truncated_not_stitched():
    delta = np.arange(0, 180, dtype=float)
    force = 1.2 * delta
    force[125:] -= 135.0
    force[130:] = np.linspace(15.0, 5.0, len(force[130:]))
    params = StitchParams(force_abs_min_20260415=15.0, recovery_fraction=0.70)
    events = detect_slip_events(delta, force, 20260415, params)
    assert any(e["event_type"] == "terminal_cliff" for e in events)
    points, rupture_idx = stitch_curve(delta, force, events)
    assert rupture_idx is not None
    assert points["point_idx"].max() <= rupture_idx
    assert points["cumulative_offset_nN"].max() == 0


def test_real_k80_stitched_smoke_outputs_fit_metrics():
    curve = pd.read_csv(ROOT / "results/realraw/curve_features.csv")
    row = curve[
        (curve["branch"] == "extend")
        & (curve["date"] == 20260416)
        & (curve["file"] == "k80-linker1-paa-50nm-8000nm-10uN - NanoScope Analysis.txt")
    ].iloc[0]
    row = row.copy()
    row["group"] = "k80-linker1-paa"
    points, events, mechanics = analyze_stitched_row(row, StitchParams())
    assert points is not None
    assert mechanics is not None
    assert len(points) > 100
    assert mechanics["fit_points"] > 100
    assert mechanics["max_cumulative_offset_nN"] >= 0
    assert "high_stiffness_N_m" in mechanics


def test_k3_unit_conversion_to_si():
    assert k3_nN_nm3_to_N_m3(1.0) == 1e18
    vals = k3_nN_nm3_to_N_m3(np.array([1e-18, 2e-18]))
    assert np.allclose(vals, [1.0, 2.0])


def test_synthetic_membrane_fit_recovers_apparent_modulus():
    target_e_mpa = 25.0
    k3 = k3_from_apparent_modulus_mpa(target_e_mpa, thickness_nm=50.0)
    delta = np.linspace(10.0, 500.0, 80)
    force = 0.08 * delta + k3 * delta**3
    fit = fit_membrane_terms(delta, force)
    recovered = apparent_modulus_mpa(fit["k3_nN_per_nm3"], thickness_nm=50.0)
    assert fit["r2"] > 0.999999
    assert np.isclose(recovered, target_e_mpa, rtol=1e-6)


def test_apparent_modulus_scales_inverse_with_thickness():
    k3 = k3_from_apparent_modulus_mpa(10.0, thickness_nm=50.0)
    e50 = apparent_modulus_mpa(k3, thickness_nm=50.0)
    e80 = apparent_modulus_mpa(k3, thickness_nm=80.0)
    assert np.isclose(e80 / e50, 50.0 / 80.0)


def test_apparent_modulus_default_excludes_jjs():
    mechanics = pd.DataFrame(
        [
            {
                "date": 20260409,
                "group": "JJS",
                "membrane_k3_nN_per_nm3": 1e-9,
                "membrane_k1_N_m": 0.1,
                "membrane_r2": 0.99,
                "fit_points": 20,
            },
            {
                "date": 20260416,
                "group": "k80-linker1-paa",
                "membrane_k3_nN_per_nm3": 1e-9,
                "membrane_k1_N_m": 0.1,
                "membrane_r2": 0.99,
                "fit_points": 20,
            },
        ]
    )
    filtered = filter_analysis_rows(mechanics)
    assert set(filtered["date"]) == {20260416}
    curves = build_curve_table(mechanics)
    assert "JJS" not in set(curves["group"])
    assert curves["valid_model"].all()
