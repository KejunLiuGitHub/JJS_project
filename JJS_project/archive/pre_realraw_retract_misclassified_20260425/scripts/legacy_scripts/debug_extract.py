import sys, numpy as np
sys.path.insert(0, 'scripts')
from parser import AFMForceCurve

for name in [
    '20260415原始数据/linker1-PFPE-OH-10000nm.spm - NanoScope Analysis.txt',
    '20260416原始数据/k80-linker1-PFNA-50nm-10000nm-10uN - NanoScope Analysis.txt',
]:
    c = AFMForceCurve(name)
    z = np.array(c.z)
    f = np.array(c.force)
    if c.z_unit in ('um','μm'):
        z = z * 1000
    if c.force_unit in ('uN','μN'):
        f = f * 1000
    print(f"\n{name.split('/')[-1]}")
    print(f"  has_attraction={np.any(f < 0)}, f_min={f.min():.2f}, f_max={f.max():.2f}")
    print(f"  z_min={z.min():.2f}, z_max={z.max():.2f}")
    print(f"  points in [0,100]nm: {np.sum((z>=0)&(z<=100))}")
