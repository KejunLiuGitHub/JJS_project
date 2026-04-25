import json
with open('results/jjs_transition_deep_analysis.json', encoding='utf-8') as f:
    data = json.load(f)

print('=== Module 4: vdW Check ===')
for r in data:
    vc = r['vdW_check']
    print(f"{r['file'][:22]:22s}  F_meas={vc['F_measured_nN']:6.1f}nN  "
          f"F_vdw={vc['F_vdw_nonret_nN']:.2f}  F_cap={vc['F_capillary_theory_nN']:.2f}  "
          f"A_req={vc['A_required_vs_typical']:.0f}x_typical")

print('\n=== Module 3: Recovery ===')
for r in data:
    rec = r.get('recovery', {})
    if rec:
        print(f"{r['file'][:22]:22s}  plateau_frac={rec.get('plateau_fraction', 0):.2f}  "
              f"max_jump={rec.get('max_slope_jump', 0):.2f}  max_curv={rec.get('max_curvature', 0):.2f}")
    else:
        print(f"{r['file'][:22]:22s}  no recovery data")
