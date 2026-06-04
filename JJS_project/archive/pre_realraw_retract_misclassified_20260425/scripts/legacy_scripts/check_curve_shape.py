import sys, numpy as np
sys.path.insert(0, 'scripts')
from parser import AFMForceCurve

for name in [
    '20260416原始数据/k80-linker1-paa-50nm-500nm-3uN - NanoScope Analysis.txt',
    '20260416原始数据/k80-linker1-paa-50nm-4000nm-3uN - NanoScope Analysis.txt',
    '20260409/JJS-50nm-500nm-10nN - NanoScope Analysis.txt',
]:
    c = AFMForceCurve(name)
    z = np.array(c.z)
    f = np.array(c.force)
    if c.z_unit in ('um','μm'):
        z = z * 1000
    if c.force_unit in ('uN','μN'):
        f = f * 1000
    print(f"\n{name.split('/')[-1]}")
    print(f"  z_unit={c.z_unit}, force_unit={c.force_unit}")
    print(f"  z range: {z.min():.1f} - {z.max():.1f} nm")
    print(f"  f range: {f.min():.2f} - {f.max():.2f} nN")
    print(f"  first 5 (z,f): {list(zip(z[:5], f[:5]))}")
    print(f"  last 5 (z,f): {list(zip(z[-5:], f[-5:]))}")
    # check if force ever goes negative
    neg = f[f < 0]
    print(f"  negative force count: {len(neg)}, min: {neg.min() if len(neg)>0 else 'N/A'}")
