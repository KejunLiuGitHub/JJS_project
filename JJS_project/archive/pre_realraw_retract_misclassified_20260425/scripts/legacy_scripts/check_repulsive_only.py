import sys, numpy as np
sys.path.insert(0, 'scripts')
from parser import AFMForceCurve, load_all_curves

root = '.'
curves = load_all_curves(root)

print("Files with NO negative force (repulsive only):")
count = 0
for rel, c in sorted(curves.items()):
    f = np.array(c.force)
    if c.force_unit in ('uN','μN'):
        f = f * 1000
    neg = f[f < 0]
    if len(neg) == 0:
        count += 1
        print(f"  {rel}: f_min={f.min():.2f} {c.force_unit} -> {f.min()*1000 if c.force_unit in ('uN','μN') else f.min():.2f} nN, disp={c.piezo_displacement}{c.z_unit}")

print(f"\nTotal repulsive-only: {count}")
