import sys, numpy as np
sys.path.insert(0, 'scripts')
from parser import AFMForceCurve

for name in [
    '20260416原始数据/k80-linker1-paa-50nm-500nm-3uN - NanoScope Analysis.txt',
    '20260416原始数据/k80-linker1-paa-50nm-4000nm-3uN - NanoScope Analysis.txt',
]:
    c = AFMForceCurve(name)
    z = np.array(c.z)
    f = np.array(c.force)
    if c.z_unit in ('um','μm'):
        z = z * 1000
    if c.force_unit in ('uN','μN'):
        f = f * 1000
    
    # 全段线性拟合
    coeffs = np.polyfit(z, f, 1)
    print(f"\n{name.split('/')[-1]}")
    print(f"  z range: {z.min():.1f} - {z.max():.1f} nm")
    print(f"  f range: {f.min():.1f} - {f.max():.1f} nN")
    print(f"  full slope: {coeffs[0]:.4f} nN/nm")
    print(f"  intercept: {coeffs[1]:.2f} nN")
    
    # 分段拟合（前一半 vs 后一半）
    mid = len(z) // 2
    s1 = np.polyfit(z[:mid], f[:mid], 1)[0]
    s2 = np.polyfit(z[mid:], f[mid:], 1)[0]
    print(f"  first half slope: {s1:.4f} nN/nm")
    print(f"  second half slope: {s2:.4f} nN/nm")
