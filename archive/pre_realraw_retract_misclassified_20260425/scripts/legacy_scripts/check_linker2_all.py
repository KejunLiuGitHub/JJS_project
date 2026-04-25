import sys, numpy as np
sys.path.insert(0, 'scripts')
from parser import AFMForceCurve, load_all_curves

curves = load_all_curves('.')
print("=== linker2-paa with negative force ===")
for rel, c in sorted(curves.items()):
    if 'linker2-paa' not in rel:
        continue
    f = np.array(c.force)
    if c.force_unit in ('uN','μN'):
        f = f * 1000
    neg = f[f < 0]
    if len(neg) > 0:
        print(f"  {rel}: min={neg.min():.2f} nN, max_neg={neg.max():.2f} nN")
