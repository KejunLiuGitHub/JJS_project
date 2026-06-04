#!/usr/bin/env python3
"""
Auto QC based on extracted features + manual review for borderline cases.
"""
import json, os, glob

def load_features():
    with open('results/extracted_features.json') as f:
        return json.load(f)

def load_discarded():
    try:
        with open('results/discarded_files.json') as f:
            return json.load(f)
    except:
        return []

def auto_qc(features, discarded):
    decisions = {}
    pending = []
    
    # Build discarded set
    discarded_files = set()
    for d in discarded:
        if isinstance(d, dict):
            discarded_files.add(os.path.basename(d.get('file', '')))
    
    for feat in features:
        fname = os.path.basename(feat['file'])
        
        # Already discarded by pipeline
        if fname in discarded_files:
            decisions[fname] = {'decision': 'discard', 'reason': 'pipeline_discarded', 'auto': True}
            continue
        
        # Criteria for auto-discard
        reasons = []
        
        if feat.get('baseline_status') != 'OK':
            reasons.append(f"baseline_{feat.get('baseline_status')}")
        
        if feat.get('far_end_points', 0) < 3:
            reasons.append(f"far_end_points_{feat.get('far_end_points')}")
        
        intercept = feat.get('baseline_intercept_nN', 0)
        if abs(intercept) > 200:
            reasons.append(f"intercept_{intercept:.1f}")
        
        slope = feat.get('baseline_slope_nN_per_nm', 0)
        if abs(slope) > 0.1:
            reasons.append(f"slope_{slope:.4f}")
        
        rep_slope = feat.get('repulsive_slope_nN_per_nm', 0)
        if rep_slope is not None and rep_slope <= 0:
            reasons.append(f"repulsive_slope_{rep_slope:.4f}")
        
        # Contact mechanics sanity check
        max_f = feat.get('max_force_nN', 0)
        min_f = feat.get('min_force_nN', 0)
        if max_f < 0:
            reasons.append(f"max_force_negative_{max_f:.2f}")
        
        # Displacement check for linker1/linker2 on 20260415 (need > 3000 nm for meaningful data)
        disp = feat.get('displacement_nm', 0)
        if 'linker1-PFPE-OH' in fname and disp <= 3000:
            reasons.append(f"insufficient_disp_{disp:.0f}nm")
        
        if reasons:
            decisions[fname] = {'decision': 'discard', 'reason': ','.join(reasons), 'auto': True}
        else:
            # Auto-keep: looks clean
            decisions[fname] = {'decision': 'keep', 'reason': 'clean', 'auto': True}
    
    return decisions

def main():
    features = load_features()
    discarded = load_discarded()
    
    decisions = auto_qc(features, discarded)
    
    keep = [k for k, v in decisions.items() if v['decision'] == 'keep']
    discard = [k for k, v in decisions.items() if v['decision'] == 'discard']
    
    print(f"Total files with features: {len(features)}")
    print(f"  Auto-keep:   {len(keep)}")
    print(f"  Auto-discard: {len(discard)}")
    print()
    
    # Show auto-discard reasons summary
    from collections import Counter
    reason_counts = Counter()
    for k, v in decisions.items():
        if v['decision'] == 'discard':
            reason_counts[v['reason']] += 1
    
    print("Auto-discard reasons:")
    for reason, count in reason_counts.most_common():
        print(f"  {count:3d}: {reason}")
    print()
    
    # Save decisions
    os.makedirs('results', exist_ok=True)
    with open('results/auto_qc_decisions.json', 'w') as f:
        json.dump(decisions, f, indent=2)
    
    print("Saved to results/auto_qc_decisions.json")
    
    # Also update qc_decisions.json with auto decisions
    try:
        with open('results/qc_decisions.json') as f:
            existing = json.load(f)
    except:
        existing = {}
    
    # Merge: existing manual decisions override auto
    merged = dict(decisions)
    for k, v in existing.items():
        merged[k] = {'decision': v, 'reason': 'manual_override', 'auto': False}
    
    with open('results/qc_decisions.json', 'w') as f:
        json.dump({k: v['decision'] for k, v in merged.items()}, f, indent=2)
    
    print(f"Updated results/qc_decisions.json: {len(merged)} total decisions")

if __name__ == '__main__':
    main()
