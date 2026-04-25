import json, numpy as np

data = json.load(open('results/extracted_features.json','r',encoding='utf-8'))

print("="*60)
print("SNAP-IN STATISTICS")
print("="*60)

def group_stats(name, items):
    snaps = [r['snap_in_force_nN'] for r in items if r['snap_in_force_nN'] is not None]
    if not snaps:
        print(f"\n{name}: no snap-in data")
        return
    print(f"\n{name}: n={len(snaps)}")
    print(f"  mean={np.mean(snaps):.2f}, std={np.std(snaps):.2f}")
    print(f"  min={np.min(snaps):.2f}, max={np.max(snaps):.2f}")
    print(f"  median={np.median(snaps):.2f}")
    for r in sorted(items, key=lambda x: x['snap_in_force_nN'] if x['snap_in_force_nN'] is not None else 0):
        if r['snap_in_force_nN'] is not None:
            print(f"    {r['snap_in_force_nN']:>8.2f} nN  disp={r['displacement_nm']}  {r['file'].split('\\')[-1]}")

jjs = [r for r in data if 'JJS' in r['file']]
linker1 = [r for r in data if 'linker1' in r['file'] and 'k80' not in r['file']]
linker2 = [r for r in data if 'linker2' in r['file'] and 'k80' not in r['file']]
k80_l1 = [r for r in data if 'k80-linker1' in r['file']]
k80_l2 = [r for r in data if 'k80-linker2' in r['file']]

group_stats("JJS (suspended)", jjs)
group_stats("linker1 (Cu grid)", linker1)
group_stats("linker2 (Cu grid)", linker2)
group_stats("k80-linker1 (Cu grid)", k80_l1)
group_stats("k80-linker2 (Cu grid)", k80_l2)

print("\n" + "="*60)
print("REPULSIVE SLOPE STATISTICS (nN/nm)")
print("="*60)

def slope_stats(name, items):
    slopes = [r['repulsive_slope_nN_per_nm'] for r in items if r['repulsive_slope_nN_per_nm'] is not None]
    if not slopes:
        print(f"\n{name}: no slope data")
        return
    print(f"\n{name}: n={len(slopes)}")
    print(f"  mean={np.mean(slopes):.4f}, std={np.std(slopes):.4f}")
    print(f"  min={np.min(slopes):.4f}, max={np.max(slopes):.4f}")

slope_stats("JJS", jjs)
slope_stats("linker1", linker1)
slope_stats("linker2", linker2)
slope_stats("k80-linker1-paa", [r for r in k80_l1 if 'paa' in r['file']])
slope_stats("k80-linker1-PFNA", [r for r in k80_l1 if 'PFNA' in r['file']])
slope_stats("k80-linker1-SDBS", [r for r in k80_l1 if 'SDBS' in r['file']])
